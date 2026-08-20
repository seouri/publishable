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

## Fix round 1

Review at `.superpowers/sdd/2026-08-19-apparatus-part-b/task-b2-review.md`, reviewed at `bfe1818`.
Verdicts: spec compliance PASS; task quality PASS WITH FINDINGS, conditional on Major 1 closing
before task 4 wires the gate. Fix commit: **`abb04a9`**.

### Corrected disagreement count

The batch report's original count ("none found... one clarification") does not hold. The honest
count is **two disagreements**, per the reviewer's own framing:

1. **Task 2's brief step 1 claim that the missing-first-answered branch is "invisible to every
   fixture, because no fixture can reach it" is false** — verified by the reviewer running a bare
   `changed()` call with no prior `record()`, which reaches and fires the assert in one line. The
   implementer's narrowing of the assert (to fire only when the incoming value is non-`None`) is the
   **correct correction** of that brief claim, not a reading of it against the surrounding decision
   as the original report characterized it. Widening the assert to `assert False` (the brief's
   literal reading) fails `test_changed_null_to_value_passes_and_becomes_first_answered`, confirming
   the narrowing is necessary, not just defensible.
2. **Plan correction 4's premise, carried into `STOP_CODES`' docstring, was false by grep** —
   `APPARATUS_CODES`'s docstring does not itself claim "every member is pinned" in a way `STOP_CODES`
   could honestly echo with named fixtures that do not exist (Major 2, below).

Both are now recorded as disagreements, not as "one clarification and nothing else." This is the
fifth time on this project a "zero disagreements" report turned out to have one sitting in prose the
brief supplied — logged per `CLAUDE.md`'s standing instruction to grep the brief before repeating it.

### Major 1 — `nan` reflexivity, closed

`Observations.changed` used a bare `incoming != first`. `coerce_scalars` admits non-finite floats
(`reference.md`'s `E-APPARATUS-FACT-TYPE` row names `float` unqualified, with no `isnan`/`isfinite`
check anywhere in its body), and `float('nan') != float('nan')` is `True` in Python — so a probe
returning a constant-`nan` fact would report a change against **itself** on its first observation,
which is exactly this batch's named risk (a run stopping when it should not) the moment task 4 wires
the gate. It would also have falsified Decision 11 (the run-start round cannot trip the gate)
directly, since the false stop fires on the very first call.

**Changed:** added a module-level `_unchanged(incoming, first)` helper in
`src/publishable/apparatus.py` — `nan`-vs-`nan` reads as unchanged; every other pair, including a
`nan` against a genuinely different value, falls through to ordinary `==`. `changed()` now calls
`_unchanged` instead of `!=`.

**Pinned by:** `test_changed_is_reflexivity_safe_for_a_constant_nan_fact` — records a `nan`-valued
fact, asserts a repeat `nan` observation reads as unchanged, then asserts a later **different**
value (`1.5`) against the same fact still fails, with the triple's first element read back as `nan`
via `math.isnan`.

**Mutation, run against the full, unfiltered suite (not just the file), reverted by hand:** reverted
`_unchanged(incoming, first)` back to a bare `incoming != first`. Result:

```
FAILED tests/test_apparatus.py::test_changed_is_reflexivity_safe_for_a_constant_nan_fact
AssertionError: assert ('drift', nan, nan) is None
1 failed, 2435 passed, 1 skipped, 2 xfailed in 157.65s
```

Exactly one failure, on an assertion (not a crash), and it is the new nan test — every other test,
including the batch's five-reading fixture, is unaffected by the mutant. Reverted by editing the
file back from a saved pre-mutation copy; `diff` against that copy came back empty; reran the full
suite to confirm **2436 passed, 1 skipped, 2 xfailed** again before committing.

### Major 2 — `STOP_CODES`' false fixture claim, closed

Deleted the clause "each pinned by its own fixture — `E-APPARATUS-RAISED` by Fixture U,
`E-APPARATUS-CHANGED` by Fixture G1 — rather than one shared assertion" from `STOP_CODES`'
docstring (`grep -rn 'Fixture U\|Fixture G1' tests/` returns nothing; both are owed by tasks 5 and
7). Replaced it with a statement of what is actually true at this commit: the only pin is one shared
set-equality assertion (`test_stop_codes_holds_exactly_the_two_codes_execute_plan_breaks_on`), with
each member's absence independently checkable by deleting it and rerunning that one test — the
inverted comparison (that `APPARATUS_CODES` is the set with genuine per-member pins) is preserved,
since the reviewer confirmed that premise sound by deleting `E-APPARATUS-FACT-MISSING` and watching
`test_E_APPARATUS_FACT_MISSING_is_individually_pinned_through_the_wrapper` fail. No new test added —
this is a claim correction, not a behavior change, per *prefer deleting a claim to rewriting it*.

### Minor 1 — corrected: the shipped fixture is sound, but the report's mutation (a) was degenerate

The original report's most-recent shim updated its parallel map **inside `record`**, before
`changed` ran against the same `facts` — so the comparison became `x vs x` for every transition, a
mutant that can never detect anything, not the most-recent rule Decision 1 rules out. Reading that
result as "a stronger discriminator" was wrong; a mutation whose two branches cannot differ proves
nothing (`CLAUDE.md`: *a mutation is a claim too*).

Rebuilt the non-degenerate shim this round: two dicts, `_MUTATION_last` (the literal value from the
call just processed, null or not) and `_MUTATION_prev` (what `_MUTATION_last` held **before** this
call), with `changed` comparing against `_MUTATION_prev` — a `sentinel`-vs-`None` distinction so "no
prior call at all" and "the prior call was null" are told apart. Ran against the file's suite:

```
FAILED tests/test_apparatus.py::test_changed_value_null_different_value_fails_against_first_not_most_recent
AssertionError: assert None == ('flip', 'v1', 'v2')
1 failed, 42 passed
```

Exactly the reading-5 test fails, on an assertion, while `test_changed_value_to_different_value_fails`
(reading 1) passes — matching the reviewer's own measurement precisely. **The shipped fixture is
sound**; only the account of why (in the original report's table) was wrong. Reverted by hand;
`diff` against a pre-mutation copy came back empty; reran to confirm 43/43 passing again. This
mutation was exploratory (correcting the record), not a new pin — the batch's actual pin remains
`test_changed_value_null_different_value_fails_against_first_not_most_recent` itself, unchanged.

### Minor 2 — credential-safety docstring narrowed

`check_facts` skips its containment check for any non-`str` fact value (a deliberate Part A
carve-out), so a non-`str` fact equal to a declared credential's value is not caught by the
mechanism the original docstring cited unconditionally. Narrowed `check_changed`'s docstring to
state the protection only for `str` fact values, and named the residual (a non-`str` credential-equal
value reaching the message) with its actual mitigation — Decision 14's redacting `Collector`, not yet
wired — as a note for whoever wires the diagnostic in task 4, rather than a claim this function makes
good on by itself.

### Minor 3 — wrong task number corrected

`check_changed`'s docstring said "task 5 wires this into `Observer._observe_one`"; the design's
§ Task decomposition gives that wiring to **task 4** (task 5 is `StopSignal` and the `execute_plan`
`break`). Corrected to "task 4."

### Minor 4 — docstring wording corrected to match Minor 4's finding

`Observations.changed`'s docstring described the missing-first-answered branch as "invisible to
every fixture, because no fixture can reach it while the ordering holds." The reviewer showed this
false by running a bare `changed()` call with no prior `record()`. Reworded to state the branch is
reachable by a direct call that skips `record` first (verified by review; no shipped test calls it
that way), and is not reached by any fixture that keeps the ordering — matching what was actually
measured rather than the brief's stronger, false claim.

### Minor 5 — full-suite evidence for this round's mutations

Both of this round's mutations (Major 1's revert-to-`!=`, and Minor 1's rebuilt non-degenerate
shim) were run — Major 1's against the **full, unfiltered suite** (`2436` baseline → `1 failed, 2435
passed` under the mutant → `2436 passed` again after revert), and Minor 1's at file level since it
is a correction of the existing report's account rather than a new pin (the batch's actual pin for
that reading was already covered by Major 1's full-suite run, which exercises the same test file).

### Verification after all fixes

`uv run ruff check .`, `uv run ruff format --check .` (82 files), `uv run mypy` (46 source files) —
all clean. `uv run pytest` — **2436 passed, 1 skipped, 2 xfailed** (2435 baseline + 1 for the nan
fixture). `git status --porcelain` empty before and after every mutation revert in this round; no
`git checkout -- <file>` was used.
