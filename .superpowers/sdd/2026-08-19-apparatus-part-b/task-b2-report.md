# Task batch 2 report — tasks 2 and 3

**Status: both tasks complete, committed, gates clean.**

**Commits:**
- `c46e07d` — task 2: `Observations.changed`
- `a384dbd` — task 3: `E-APPARATUS-CHANGED` and `STOP_CODES`

**Test summary:** full suite `uv run pytest` → **2435 passed, 1 skipped, 2 xfailed** (was 2426
passed at batch start; +6 for task 2, +3 for task 3, matching both briefs' stated deltas). `uv run
ruff check .`, `uv run ruff format --check .`, `uv run mypy` (46 source files) all clean.

## Task 2 — `Observations.changed`, direct call

Built on the shipped `_first_answered` mapping exactly as ruled — no second mapping, no new
mechanism. `changed(condition_key, facts)` iterates the **incoming** mapping, compares each fact
against `_first_answered.get((condition_key, fact))`, and returns the first `(fact, first,
incoming)` triple that disagrees, or `None`.

The `assert` in step 1 is narrower than "no branch for a missing first-answered value" read
literally: it fires only when the **incoming value is non-`None`** and no first-answered entry
exists for that pair — which cannot happen once `record` has already run against the same `facts`,
per Decision 3's ordering. A `None` incoming value with no first-answered entry is not a violation
of that invariant; it is the ordinary "never yet answered" state (`null → value`'s first half), so
it is skipped rather than asserted about. Writing the assert any wider would make it fire on every
legitimate `null`-first fact — a live discriminator, not the dead branch the brief describes, so
narrowing it was necessary to keep the assert true rather than decorative.

**The fixture, and the reading each observation separates** (one condition, `"00"`, unless noted):

| # | Call sequence | Observation | What it separates |
|---|---|---|---|
| 1 | `record("00", {pinned: "r1"})` → `changed("00", {pinned: "r1"})` → `None` | establishes first-answered | baseline: a fact's own first call never contradicts itself |
| 2 | `record("00", {pinned: "r2"})` → `changed(...)` → `("pinned", "r1", "r2")` | **fails** | reading 1, value → different value |
| 3 | `record("00", {appears: None})` → `changed(...)` → `None`; then `record("00", {appears: "A1"})` → `changed(...)` → `None` | passes both calls | reading 2, null → value; the value becomes first-answered (`facts_document()["00"]["appears"] == "A1"`) |
| 4 | `record("00", {vanishes: "L1"})` → `None`; then `record("00", {vanishes: None})` → `None` | passes both calls | reading 3, value → null; `facts_document()["00"]["vanishes"] == "L1"` stands |
| 5 | `record("00", {pinned: "r1", sometimes: "S1"})` → `None`; then `record("00", {pinned: "r1"})` (`sometimes` **absent**) → `None` | passes | reading 4, absent key never compared — `changed` only iterates `facts.items()`, so `sometimes` is never visited |
| 6 | `record("00", {flip: "v1"})` → `None`; `record("00", {flip: None})` → `None`; `record("00", {flip: "v2"})` → `("flip", "v1", "v2")` | **fails on the third call** | reading 5, value → null → different value — fails against the **first** answered (`v1`), not the intervening `null`. A two-observation fixture cannot show this: the middle `null` call is what a most-recent comparison would (wrongly) treat as resetting the baseline |
| 7 | Two conditions, `record("00_a", {model_revision: "rev-a"})` → `None`; `record("01_b", {model_revision: "rev-b"})` → `None` | passes both | per-condition scope — `01_b`'s own first observation is never compared against `00_a`'s differing value |

**Three mutations, run and reverted by editing the file back (verified `diff` against a saved copy
== empty after each revert, then reran the file's suite to confirm 39/39 passing again each time):**

| Mutation | Mechanism (since the shipped code has no second mapping to swap in, one was added for the mutation only) | Result |
|---|---|---|
| (a) compare against most-recent instead of first-answered | Added a parallel `_MUTATION_most_recent` dict, updated in `record` for every non-`None` value (mirroring `_first_answered`'s own update timing), and pointed `changed`'s lookup at it instead | **FAILs** reading 6's test: `record` writes `v2` into the most-recent map *before* `changed` reads it on the same call, so the comparison becomes `v2` vs `v2` and returns `None` where the correct code returns `("flip", "v1", "v2")` — `AssertionError: assert None == ('flip', 'v1', 'v2')`. Reading 2's test also failed the same way, for the same reason (`r2` vs `r2`) — a stronger discriminator than the brief requires, not a weaker one, since it shows both branches diverge from the shipped code rather than merely from each other |
| (b) drop the `incoming is None` guard | Removed the `if incoming is None: continue` line | **FAILs** the value→null test (reading 4): `changed` returns `("vanishes", "L1", None)` where the correct code returns `None` — `AssertionError: assert ('flip', 'v1', None) is None` on the reading-6 test and the reading-4 test both fail |
| (c) iterate `_first_answered`'s keys instead of `facts`, using a `_MISSING` sentinel so absence is distinguishable from an explicit `null` | Rewrote the loop to iterate `self._first_answered` and look up `facts.get(fact, _MISSING)` | **FAILs** the absent-key test (reading 5): `sometimes`'s absence now reads as `_MISSING != "S1"` and raises a spurious change — confirmed the test failed, along with readings 3 and 6 (both also touch the sentinel path) |

Each mutation's two branches were checked to produce different, non-crash results before trusting
the pin — none of the three is a bare substring match or a crash-only catch.

## Task 3 — `E-APPARATUS-CHANGED` and `STOP_CODES`

`check_changed(observations, condition_key_value, facts)` is the new module-level "gate's
caller-facing helper" (`check_facts`/`observe_once`'s own naming convention — no name was mandated
by the brief or plan). It calls `Observations.changed` and raises `ContractError` coded
`E-APPARATUS-CHANGED` with message `` condition `{condition_key}`'s fact `{fact}` changed: {first} →
{incoming} `` — condition key, fact name, both values, `→` not `->` — or returns `None` silently.
Not wired anywhere yet; task 4 (design's numbering) wires it into `Observer._observe_one` on
Decision 3's `check_facts → append_observation → record → compare` order.

**`STOP_CODES = frozenset({"E-APPARATUS-RAISED", "E-APPARATUS-CHANGED"})`**, minted per plan
correction 4, kept deliberately separate from `APPARATUS_CODES`. Verified by a direct membership
test (`E-APPARATUS-CHANGED not in APPARATUS_CODES`, `E-APPARATUS-RAISED in APPARATUS_CODES`). The
docstring states the reasoning (why admitting it to `APPARATUS_CODES` would add an unpinned member)
without asserting run-start unreachability as a settled fact — that claim is explicitly left to
task 13's fixture, per the brief's own instruction not to repeat Part A's Critical-producing
pattern.

**Credential ordering — measured, not assumed.** A dedicated test
(`test_a_credential_carrying_value_cannot_reach_check_changed_because_check_facts_runs_first`)
calls `check_facts` on an `Apparatus` whose one fact value equals a declared credential, in the same
try block that would go on to call `check_changed` if `check_facts` did not raise first. The test
asserts the caught exception's code is `E-APPARATUS-FACT-CREDENTIAL` — **never**
`E-APPARATUS-CHANGED` — confirming that a credential-carrying value cannot reach
`check_changed`/`Observations.changed`/`Observations.record` at all, because `check_facts` (Part A,
unmodified in this batch) refuses it first, before any value is recorded. No credential can reach
`E-APPARATUS-CHANGED`'s message. This is a Pass, not a Critical.

**The prescribed mutation** — reduce the message to the fact name alone (`f"fact \`{fact}\`
changed"`) — was applied, run, and reverted by editing the file back. It **FAILs** on the missing
`r1 → r2` phrase (`AssertionError: assert 'r1 → r2' in 'fact \`pinned\` changed'`), confirming the
message test asserts the whole arrow phrase including both values, not a substring either branch
would satisfy. Reverted; `diff` against the pre-mutation copy came back empty; reran to confirm
42/42 passing again.

## Disagreements found — after grepping what each brief and the design/plan actually assert

- **None found in either brief's stated mechanics.** Grepped both briefs, the design's Decision 1
  and Decision 2 sections, and plan correction 4 against the code and tests built: the signature,
  the five/four-transition table, the "no branch for a missing first-answered pair" step, the
  message shape, the `STOP_CODES`/`APPARATUS_CODES` exclusion, and the credential-ordering claim all
  matched what was buildable and testable without contradiction.
- **One clarification, not a disagreement:** the brief's step 1 wording ("do not write a branch for
  a pair with no first answered value... a bare `self._first_answered.get(pair)` whose `None`
  result silently `continue`s would be a dead branch") is true only for **non-`None` incoming
  values** — the code narrows the assert to that case rather than applying it to every `get(pair) is
  None` outcome, because a `None` incoming value legitimately has no first-answered entry on its own
  first call (reading 2's opening half). This is stated in the design's own table (`null → value`
  passes) and in Decision 1's grounds, so it is a reading of the brief's prose against the
  surrounding decision, not a contradiction of either. Recorded here per CLAUDE.md's "grep what the
  brief asserts before repeating it," since four prior "zero disagreements" reports hid exactly this
  shape of thing in prose supplied by the brief.
- **No sentence in this report claims a config is unblocked.** Neither task retires a refusal or
  changes what `validate_config` reports for any of the nine configs; the zero/six/three figures are
  untouched.

## Concerns

None outstanding. `check_changed` and `STOP_CODES` are unwired — by design, task 4 in the design's
numbering — so no run-level behavior has changed yet; a spurious gate cannot reach a run at this
commit, consistent with the batch's stated boundary.
