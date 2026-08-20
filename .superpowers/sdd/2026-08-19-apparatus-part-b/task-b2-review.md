# Batch 2 review — tasks 2 and 3 (`Observations.changed`, `E-APPARATUS-CHANGED`, `STOP_CODES`)

**Reviewed at `bfe1818` on branch `h7d-apparatus-part-b`.** Every claim below marked *verified by
running* was produced by executing something in this working tree; claims marked *read* were not.

## Verdicts

**Spec compliance: PASS.** All five of Decision 1's readings and the per-condition scope behave as
ruled — verified by running my own sequences against `Observations`, independent of the shipped
fixture. Decision 2's message names the condition key, the fact and both values with `→`. Plan
correction 4 is honoured: `E-APPARATUS-CHANGED` is absent from `APPARATUS_CODES` and `STOP_CODES` is
minted separately, with both members individually pinned (verified by deleting each). **Nothing is
wired** — `grep -rn 'check_changed\|STOP_CODES\|\.changed(' src/` returns only the definitions and
`check_changed`'s own internal call, so a spurious gate cannot reach a run at this commit. No
sentence in the code, the tests or the report claims a config is unblocked; the zero/six/three
figures are untouched. Gates clean: `ruff check`, `ruff format --check` (82 files), `mypy` (46 source
files), `pytest` **2435 passed, 1 skipped, 2 xfailed** — the expected count.

**Task quality: PASS WITH FINDINGS, and the pass is conditional on Major 1 closing before task 4
wires the gate.** The shipped fixture does separate first-answered from most-recent — but **not for
the reason the report gives**, and the report's own mutation (a) was degenerate. One real defect in
the comparison (`!=` on a non-reflexive value) is invisible to every fixture in this batch and to
every fixture the design prescribes. Two docstring claims are false in the present tense.

**And the report's disagreement count does not hold.** "None found in either brief's stated
mechanics" is wrong: task 2's brief step 1 asserts of the missing-first-answered branch that "no
fixture can reach it", and I **verified by running** that a bare `changed()` call reaches it in one
line (Minor 4). The implementer's narrowing of the assert is a *correction* of that brief claim, not
a reading of it against the surrounding decision — and it was the right correction, which I also
verified by running. Plan correction 4's claim that `APPARATUS_CODES`'s docstring "states that every
member is pinned" is likewise false by grep (Major 2). So the honest count for this batch is **one
correction of the brief and one false locator carried into a new docstring**, not "one clarification
and no disagreements" — the fifth report on this project to record zero disagreements while the
disagreement sat in prose the brief supplied.

---

## Findings

### Major 1 — `changed` reports a change against a value equal to itself when the value is `float('nan')`
**`src/publishable/apparatus.py:281`** (`if incoming != first:`)

`coerce_scalars` admits non-finite floats — no `isnan`/`isfinite` anywhere in its body — so a probe
may legitimately return `Apparatus(facts={"drift": float("nan")})`. Verified by running:

```
coerce nan: {'f': nan}
 nan 1st: ('f', nan, nan)
 nan 2nd: ('f', nan, nan)
 nan msg: E-APPARATUS-CHANGED condition `00`'s fact `f` changed: nan → nan
```

The triple is returned on the **first** observation, immediately after `record` — i.e. on the
run-start round. Once task 4 wires `check_changed` into `_observe_one`, a probe whose fact value is a
constant `nan` stops the run at the very first probe call, which is *a run that stops when it should
not* — this batch's whole named risk — and it falsifies Decision 11's ruling that the run-start round
cannot trip the gate. **Not reachable at this commit** (no call site), which is why this is Major and
not Critical.

**The owner is this task, determined rather than guessed.** `reference.md` § Errors core raises'
`E-APPARATUS-FACT-TYPE` row admits a fact value that is "`bool`, `int`, `float`, `str`, `None`, or
what core coerces to one" — `float` **without qualification**, so a non-finite float is legal declared
input and `coerce_scalars` is enforcing the documented rule correctly. The defect is therefore in this
batch's comparison operator, and the remedy is a reflexivity-safe comparison here rather than a new
refusal upstream. (Separately and not this slice's: `json.dumps({'f': float('nan')})` emits
`{"f": NaN}`, which is not valid JSON, so a `nan` fact also corrupts `apparatus/probes.jsonl` — a Part
A gap I could find no filing for. Naming it here so it is not lost, not as a route for this finding.)

**Timing: this must be closed before or inside task 4.** Task 4 is precisely the commit that makes it
reachable, no fixture the design prescribes can see it, and the failure mode it produces is the one
this slice's whole risk statement names. "PASS WITH FINDINGS" is not clearance for batch 3 to wire
the gate over it.

### Major 2 — `STOP_CODES`'s docstring claims per-member fixture pins that do not exist, and denies the one pin that does
**`src/publishable/apparatus.py:472-476`**

> "each pinned by its own fixture — `E-APPARATUS-RAISED` by Fixture U, `E-APPARATUS-CHANGED` by
> Fixture G1 — rather than one shared assertion"

Verified: `grep -rn 'Fixture U\|Fixture G1' tests/` returns **nothing** — both are run-level fixtures
owed by tasks 5 and 7. The only pin at this commit is
`test_stop_codes_holds_exactly_the_two_codes_execute_plan_breaks_on`, which is **exactly one shared
set-equality assertion** — the thing the sentence says it is not. Verified by mutation that both
members *are* pinned (deleting `E-APPARATUS-RAISED` alone, and deleting `E-APPARATUS-CHANGED` alone,
each fails that one test at `tests/test_apparatus.py:755`), but by the mechanism the docstring
disclaims.

The comparison is also inverted: `APPARATUS_CODES` is the set whose members each have their own named
pin — verified by deleting `E-APPARATUS-FACT-MISSING` from it and running the **full** suite, which
failed `test_E_APPARATUS_FACT_MISSING_is_individually_pinned_through_the_wrapper`
(`tests/test_cli.py:13597`), 2434 passed / 1 failed. So Part A's Major 2 premise is materially sound;
it is `STOP_CODES` that does not yet meet it.

This is `CLAUDE.md`'s first-listed habit — *a docstring claiming a guarantee the code does not
provide* — sitting on the exact enumeration Part A's Major 2 was about. Per *prefer deleting a claim
to rewriting it*: **delete the "each pinned by its own fixture … rather than one shared assertion"
clause**. The membership reason (the paragraph below it) stands on its own and needs no claim about
how the pin is shaped.

### Minor 1 — the report's mutation (a) was degenerate, and its "stronger discriminator" reading is wrong
**`.superpowers/sdd/2026-08-19-apparatus-part-b/task-b2-report.md`, task 2 mutation table**

The report's most-recent shim updated a parallel map **inside `record`**. Because `changed` runs after
`record` for the same `facts`, that map already held the incoming value, so the comparison became
`x vs x` for *every* transition. The report observes that reading 2's test failed too and reads that
as "a stronger discriminator, not a weaker one." It is neither: it means the mutant was *a comparison
that can never detect anything*, not the most-recent rule Decision 1 rules out.

I built the non-degenerate shim (two maps, so the prior observation survives the current `record`;
`changed` reading `_prev`) and ran it. Result, verified by running:

```
FAILED tests/test_apparatus.py::test_changed_value_null_different_value_fails_against_first_not_most_recent
E  AssertionError: assert None == ('flip', 'v1', 'v2')
1 failed, 41 passed
```

Exactly one test fails, on an assertion, and it is the named reading-5 test;
`test_changed_value_to_different_value_fails` **passes** under the mutant, as it must. **The shipped
fixture genuinely separates first-answered from most-recent** — the design's constraint that a
two-observation fixture cannot do so is met by the three-call sequence. So the pin is sound and the
report's account of why is not. Worth a correction line in the ledger, since a later slice reading
that table would build the same degenerate shim.

### Minor 2 — the credential-safety docstring over-claims for non-`str` fact values
**`src/publishable/apparatus.py:352-356`**

> "`check_facts` (Part A) refuses a fact value that equals **or contains** a declared credential
> **before** anything is recorded"

Verified by running: the containment case is refused —
`check_facts(Apparatus(facts={"endpoint": "https://api.example.com/?key=lab7"}), credentials={"TOK": "lab7"})`
→ `E-APPARATUS-FACT-CREDENTIAL`. But `check_facts` step 2 skips the containment test for any non-`str`
value (`if not isinstance(value, str): continue`, a deliberate Part A carve-out with its own comment),
so:

```
non-str bypass: check_facts returned {'port': 1234}
  message: condition `00`'s fact `port` changed: 1234 → 9999
```

A declared credential whose value is `"1234"` reaches this message verbatim. Two reasons this is
Minor and not Critical, both checked: there is no call site, and Decision 14 routes the wired
diagnostic through a redacting `Collector` whose `secrets.redact` does a plain `str.replace` over the
same value set, so the rendered output would be redacted. Remedy per *prefer deleting*: narrow the
clause to "a `str` fact value", or drop the "equals or contains" parenthetical and cite `check_facts`
without restating its rule.

### Minor 3 — `check_changed`'s docstring names the wrong task for the wiring
**`src/publishable/apparatus.py:362`**: "task 5 wires this into `Observer._observe_one`". The design's
§ Task decomposition gives **task 4** the ordering chain into `_observe_one`; task 5 is `StopSignal`
and the `break` in `execute_plan`. The report gets this right ("task 4 (design's numbering)"), so
code and report disagree and the code is wrong. `STOP_CODES`'s own "(task 5)" for the loop break is
correct.

### Minor 4 — the brief's "no fixture can reach it" is false, and the assert's firing branch is unpinned
Task 2's brief step 1 says a missing-first-answered branch is "invisible to every fixture, because no
fixture can reach it". Verified by running that it is trivially reachable by direct call:

```
assert FIRED by bare changed() with no record: record() runs before changed() for the same `facts`; a non-n…
```

**The implementer's narrowing is correct**, and I verified the necessity rather than reading it:
widening the assert to `assert False` (the brief's literal reading) fails
`test_changed_null_to_value_passes_and_becomes_first_answered` — so the narrow form is the only true
one, and the narrowing is pinned in that direction by an existing test. The narrowing is also sound
for the reason the docstring gives: `record` never stores `None`, so `.get(pair) is None` is
equivalent to "pair absent" — checked by reading `record`'s `elif` and confirmed by the `value → null`
sequence. What is **not** pinned is the assert firing: no shipped test calls `changed` without
`record`. That is acceptable for an assert about core's own callers (`execute_plan`'s precedent), but
the report should say the assert is reachable-by-direct-call rather than repeat the brief's
unreachability framing.

### Minor 5 — per-mutation full-suite runs are not evidenced
§ Global Constraints requires, for each mutation: confirm the named test fails, **then run the full,
unfiltered suite in the foreground**. The report evidences file-level runs only ("39/39", "42/42")
and one full-suite count at the end. Not a defect in the code; recorded because "the mutation was run
and the suite was clean" is the claim a later reader will take from it.

---

## What I verified, and how

| Claim | How |
|---|---|
| All five of Decision 1's readings + per-condition scope | **Run**, my own sequences, no shipped fixture involved: `value→value` returns the triple; `null→value`, `value→null`, absent key all return `None`; `value→null→v2` returns `('f','v1','v2')`; two conditions with the same fact name and different values both pass, and a second condition's *own* later drift still fires |
| The fixture separates first-answered from most-recent | **Run**, non-degenerate two-map mutation; one named test fails on an assertion (Minor 1) |
| Both `STOP_CODES` members individually pinned | **Run**, two separate deletions, each failing `tests/test_apparatus.py:755` |
| `E-APPARATUS-CHANGED ∉ APPARATUS_CODES` | **Run** (the membership test) and read |
| Every `APPARATUS_CODES` member has its own pin (the brief's premise) | **Run**, full suite with one member deleted → `test_E_APPARATUS_FACT_MISSING_is_individually_pinned_through_the_wrapper` fails |
| The message's `r1 → r2` phrase is the discriminator | **Run**, message reduced to the fact name → the named test fails at `tests/test_apparatus.py:713` |
| Credential ordering: containment refused before anything is recorded | **Run**, `check_facts` on a URL embedding the credential → `E-APPARATUS-FACT-CREDENTIAL`; the containment rule itself is separately pinned by Part A's `test_a_fact_value_containing_a_declared_credential_value_is_refused`, so the new test's use of exact equality costs nothing |
| `_observe_one`'s shipped order is `check_facts → append_observation → record` | **Read** `src/publishable/apparatus.py:550-567` — `check_changed` is not in it, which is correct at this commit |
| Nothing wired | **Run** `grep -rn` over `src/` |
| A declared key's absence is `E-APPARATUS-FACT-MISSING` | **Run** |
| `E-APPARATUS-CHANGED` has no `reference.md` row yet | **Run** grep — correct, task 11 owns it; no docstring claims a row exists |
| Mechanical prose pass on the new lines | **Run** greps: no positional locators, no bare `x` for multiplication, no trailing whitespace or tabs |
| Suite delta arithmetic | **Run**: 2435 = plan baseline 2423 + batch 1's 3 + task 2's 6 + task 3's 3 |
| `review-b2.diff`'s header lists 8 files but the batch touches 3 | **Run** `git diff --stat c46e07d~1 bfe1818`. The `tests/test_cli.py`, `docs/reference.md` and `CLAUDE.md` edits in that diff came from `7d907b2` (batch 1's fix round), not from this batch — checked with `git log -S`. **Not a finding against this batch**; noted so the next reviewer does not attribute task 12's docstring edit here |

## What I could not check

- **Anything about the wired behaviour.** Fixtures G1/G2/G3/U/Z/T/K/B do not exist at this commit;
  every run-level consequence of Decision 1 — including whether Major 1's `nan` case actually stops a
  run — is owed by tasks 4, 5, 7 and 13. Major 1's severity assumes the wiring the design describes.
- **Whether `secrets.redact` in fact reaches the wired diagnostic** (Minor 2's mitigation). I read
  Decision 14 and `redact`'s body; the path does not exist yet.
- **Whether a `nan` fact is reachable through a real plugin probe.** `coerce_scalars` admits it and
  `Apparatus` does not constrain it; no shipped probe returns one.

**Tree state: clean.** Every mutation was applied by editing in place, reverted by copying back a
pre-mutation copy taken before the first edit, and each revert verified by `diff` against that copy
*and* by re-running. `git status --porcelain` is empty and the full suite is back at 2435 passed, 1
skipped, 2 xfailed. No `git checkout -- <file>` was used at any point.
