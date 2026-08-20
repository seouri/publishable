# H7d Part B batch 3 review — tasks 4 and 13

Reviewed at `5e29991` on branch `h7d-apparatus-part-b`. Every claim below says whether it was
**verified by running** or **read**. Gates, run in the foreground at HEAD before and after every
mutation: `ruff check .` clean, `ruff format --check .` 82 files, `mypy` 46 source files,
`uv run pytest` **2439 passed, 1 skipped, 2 xfailed** (twice — baseline and after all reverts).
**The tree is clean**; every mutation was applied to a saved copy and reverted by writing the copy
back, and `git status --porcelain` is empty. Three temporary test files the reviewer wrote were
deleted; `git checkout --` was never used.

## Verdicts

**Spec compliance: PASS.** Decision 3's order is exactly as ruled and every clause of it is
observable at `run` level; all five of Decision 1's transitions plus per-condition scope behave as
ruled in end-to-end runs the reviewer built independently of the shipped fixtures; Decision 11's
claim is a test rather than a comment and that test **discriminates**; Decision 2's message shape
holds; plan correction 4's exclusion of `E-APPARATUS-CHANGED` from `APPARATUS_CODES` is honoured and
its stated cost is the shape actually measured. No sentence anywhere in the diff claims this slice
unblocks a config, and no count (zero / six / three) is asserted or moved — verified by grep over
every added line.

**Task quality: PASS, conditional on Major 1 and Major 2 closing before task 5 commits.** Both
Majors are in surfaces task 5 touches, and both are the shapes `CLAUDE.md` names by hand: a
credential-carrying value reaching an un-redacted printer, and a test whose docstring claims a
guarantee no assertion in it makes. The five Minors are all prose, four of them false or stale
claims in docstrings this batch edited or created.

---

## Findings

### Major 1 — task 4's wiring made a named credential residual live, and its stated mitigation does not exist at this commit

`src/publishable/apparatus.py:406` (the `E-APPARATUS-CHANGED` raise), reached from
`src/publishable/apparatus.py:613` (`_observe_one`'s new last statement); printed by
`src/publishable/cli.py:3732`.

**Verified by running.** A scaffolded project with `required_env = ["PUBLISHABLE_TEST_TOKEN"]`, an
`.env` supplying `PUBLISHABLE_TEST_TOKEN=13579`, and a probe returning `{"serial": 13579}` (an
`int`) on its first two calls and `{"serial": 999}` afterwards prints, to stderr, exit 1:

```
  error   E-APPARATUS-CHANGED  condition `00`'s fact `serial` changed: 13579 → 999
```

The credential's value core itself read from the environment reaches the operator's terminal
verbatim. `check_facts`'s containment check **skips any non-`str` value** by its own deliberate
carve-out (`apparatus.py:181`), and `E-APPARATUS-CHANGED` is deliberately not in `APPARATUS_CODES`,
so the raise passes `command_run`'s redacting containment site (`cli.py:2476`) and lands in `main`'s
bare `print(f"  error   {exc.code:<20} {exc}")`. **Before task 4 this path had no call site**, so the
residual was inert; the wiring is what made it live.

**The value is already on disk regardless, and that half is pre-existing — verified by running.**
The same run writes `{"serial": 13579}` into `apparatus/probes.jsonl` on two lines, because
`check_facts`'s non-`str` carve-out lets it through the credential check entirely. So what task 4
newly created is the **terminal** exposure, not the disk exposure; the disk half belongs to whoever
owns that carve-out. Checked against `docs/superpowers/spec-defects.md`: the closed entry there
covers a `str` fact value reaching `probes.jsonl` (closed by Part A task 9, Fixture K), and the open
entry covers a credential-valued fact **key** — **the non-`str` value carve-out is filed nowhere**,
and should be, owned by the fact-contract carve-out rather than by this batch. That same open entry
already predicts this batch's half in as many words: *"a future code added outside that set (or a
future call site printing the raw exception rather than a `Collector`) would reopen the leak."*
`E-APPARATUS-CHANGED` is exactly a code outside that set, so this is the predicted reopening rather
than a new class.

`check_changed`'s own docstring names this residual and names Decision 14's redacting `Collector` as
the mitigation — **which is task 5/7's and is not in the tree**. Reading `secrets.redact`'s
containment behaviour, that `Collector` should indeed redact `13579` from the rendered message, so
the residual really does close at task 5 — but at this commit it is live, unmitigated and unpinned.
**Close it in task 5** (Decision 14's fresh redacting `Collector` on the stop path) **and pin exactly
this shape**: a non-`str` fact equal to a declared credential's value that then moves. A reviewer
could reasonably rank this Critical given that Part A's only Critical was the same class; it is
ranked Major here only because it needs an all-numeric credential value *and* a moving fact.

### Major 2 — the count discriminator task 4 exists to establish cannot be reached by any ordering mutation, and its docstring claims otherwise

`tests/test_apparatus.py:790` (the test) and `:847` (the assertion); the tripwire is
`src/publishable/apparatus.py:303`.

**Verified by running, and the implementer's finding is confirmed and extended.** With the gate moved
above `self.observations.record`, both the direct-call test and the end-to-end test fail with
`AssertionError` from `apparatus.py:303` — `record() runs before changed() …` — and the named
assertion `unobserved(["pinned"])["pinned"]["total_probes"] == 4` is never evaluated.

**No fixture can change that**, and this is the part the report stopped short of: the assert fires
whenever `first is None and incoming is not None`, which is the **first answering observation of any
fact**. Under a gate-before-`record` ordering that condition holds on the very first non-null
observation, and a fact that later *moves* must have first-answered somewhere. So the assert is a
strictly earlier tripwire on the same ordering for every possible fixture. `CLAUDE.md`: *a mutation
caught by a crash is not a pin* — so **the record-before-gate ordering has no test-level pin at all**,
while the test's docstring asserts the count "is the only assertion that can see this ordering" and
the report repeats it. That is the *a test whose name claims the guarantee* shape.

**First, what is NOT claimed: the ordering is not unguarded.** The assert fires loudly, at every
apparatus fixture, the instant `_observe_one`'s order is reversed — a reorder cannot ship silently.
What is missing is a *test-level* witness, and the overclaiming docstring is the actual defect.

**Three actions, in ascending cost; the first is the minimum and closes the finding.**

1. **Delete the count test's "the only assertion that can see this ordering" clause** (and the
   report's repetition of it). Prefer deleting the claim to rewriting it; describe the count for what
   it is — a census assertion, true under the surviving ordering, not a discriminator.
2. **Pin the claim `Observations.changed`'s docstring makes and nothing asserts**: a direct call to
   `changed()` **without** `record()` first, asserting the `AssertionError`. Verified by grep that no
   test in `tests/test_apparatus.py` asserts it. **Note precisely what this does and does not pin**:
   it witnesses that `changed` *requires* record-first, **not** that `_observe_one` *satisfies* it —
   add it after a reorder and it still passes.
3. **The only legible witness of `_observe_one`'s order** is an observation of the call sequence —
   spy or wrap `Observations.record` and `check_changed` and assert record-then-gate — because every
   value assertion is equal under both orderings and every count assertion sits behind the assert.

**The append discriminator, by contrast, is real — verified by running.** The brief's mutation (a) is
realizable in an assert-safe form the report did not try: move `append_observation` **below**
`check_changed`, leaving `record` where it is. Under that ordering
`test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end` fails on **its own**
`assert len(ledger) == 4` with `assert 3 == 4`, and the direct-call count test **passes** — exactly
the brief's prediction that "the recomputed `unobserved` is *equal* under this mutation". So the
brief's (a) is sound as a claim and only its literal wording (which also crosses `record`) produces
the crash the report reported. **The run-level append pin holds; the direct-call record pin does
not.**

### Minor 1 — `check_changed`'s docstring says "there is no call site yet" in the commit that gave it one

`src/publishable/apparatus.py:389`. Read, and contradicted by `:613` and by the same docstring's next
paragraph ("Task 4 wires this into `Observer._observe_one`"), which task 4 rewrote while leaving this
clause. It is also the sentence carrying Major 1's excuse. **Delete the clause** rather than rewriting
it (`CLAUDE.md`: prefer deleting a claim).

### Minor 2 — `STOP_CODES`' docstring is wrong about a fixture this batch created

`src/publishable/apparatus.py:511`: "Fixture U and Fixture G1 … are owed by tasks 5 and 7 and **do
not exist here**." Task 4 shipped Fixture G1 — `_APPARATUS_G1_TEMPLATE` and
`test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end` (`tests/test_cli.py:14363`), whose
own docstring calls it "Fixture G1's ledger" — and did not update this sentence. This is the same
shape batch 2 was found on (a docstring wrong about which fixtures exist), one commit later. Delete
the "do not exist here" clause and the task attribution rather than restating them.

### Minor 3 — a mis-citation of the plan

`tests/test_apparatus.py:798`: "the plan's own **correction** and Fixture G1 both name this as the
discriminator". Verified by grep: `total_probes` appears in the plan's Fixture G1 expectations, in
its mutation table and in task 4's step 2, and **nowhere in § Corrections against the code**. Name
the mutation table or delete the citation.

### Minor 4 — the docstring names task 5 where the brief prescribed task 7, unrecorded as a divergence

`tests/test_cli.py:14372`. The brief's step 3 required the text to say "this expectation is **task
7's** to change"; the shipped docstring says task 5's. The substitution is very likely the correct
one — task 5's `break` is what stops the raise from escaping, so the exit code changes there, not at
7 — but the report's own disagreements section records two smaller brief-vs-code notes and not this
one. Keep the docstring; record the substitution so task 5's implementer knows the test is theirs.

### Minor 5 — a positional locator in a new docstring

`tests/test_cli.py:14444`: "(`_SWEPT_FACT_PROBE_MODULE`/`_APPARATUS_ASSAY_TEMPLATE` **above**)". The
constants are named, so "above" is deletable; `CLAUDE.md` forbids positional locators and has been
burned by them seven times. **The weakest finding here** — the rule targets positional *table row*
references and the constants are named, so "above" is redundant rather than wrong.

### Minor 6 — Decision 11's cost-if-wrong sentence names a test that would not fail, and its own mutation table has the right answer

`docs/superpowers/specs/2026-08-19-apparatus-part-b-design.md` § Decision 11: *"If a future round ever
probes one condition twice before the first execution, the gate would fire during setup and **the test
above is what would fail**."* It would not. Determined from the fixture: G3's probe returns the swept
value, constant within a condition, so a duplicated run-start round observes the same value twice and
nothing is compared as changed — the test passes. The design's own mutation table has the correct
guard for that case (*"Probe once at run start instead of once per condition | Part A's shipped
call-count contract"*), so the decision contradicts its own table. This disturbs neither verdict —
the pin task 13 was asked for exists and discriminates against the reading it was built for — but per
`CLAUDE.md` the correction is appended to the design rather than retro-edited into Decision 11, and
task 11 is the natural place to record it. Not mutated in this review: Part A's
`test_a_declared_probe_is_called_once_per_condition_at_run_start`, which is the guard that would
actually have to fail.

---

## The two brief-vs-code notes, adjudicated

**They are one issue, not two, and it is already owned.** `run_a_project`'s `run_dir` contract is
keyed on `expect_exit` rather than on whether a run directory exists: plan correction 3 records the
non-`EXIT_WRONG` face (the helper globs and reads `executions.jsonl`, crashing when neither exists),
and the implementer's note records the `EXIT_WRONG` face (it returns `run_dir: None` where a run
directory and a ledger do exist). **Task 7 step 2 already owns the widening** — "`run_dir` is not
`None` exactly when there is a ledger to read" — which fixes both faces. The test's inline comment
plus its own glob is the right disposition at this commit; **no new filing is owed.**

**The `parameters={}` note is a test-helper artifact, not a spec defect — verified by reading the
production path.** `run_a_project` calls `generate_experiment(..., template_name="generic")` and then
swaps `experiment_type` in the generated YAML, so `parameters.analysis.*` is `generic`'s own
`parameter_spec` materialized by `materialize.py`'s `_parameters_block(template.parameter_spec)`. That
*is* the invariant (`parameter_spec` is the single source of truth for what `init` writes); production
`init` against a custom template materializes that template's spec. **No filing owed**, and the note
is correct as written.

---

## What was verified by running, in full

**Attack 2 — firing when it should not. Zero false stops; no Critical.** Six end-to-end runs the
reviewer wrote from scratch (`installed` + `registries` + `run_a_project`, own distribution, module,
probe and template names per Fixture P's warning), all exit 0, `status: completed`, and
`E-APPARATUS-CHANGED` absent from stdout and stderr, each paired with something that must report:

| Case | What must report | Result |
|---|---|---|
| A constant fact across **6** executions | 7 ledger lines, 6 results | pass |
| `null → value` | 5 ledger lines, `facts["00"]["cal"] == "C1"` | pass |
| `value → null` | 5 ledger lines, the first answered value stands | pass |
| An **undeclared** key present on call 1 only | present in ledger line 1, absent from line 2 | pass |
| A constant **`nan`** fact | 5 ledger lines, `provenance.apparatus.hash` written | pass |
| **Three** conditions × 2 repeats, three distinct values of one fact | `{m1, m2, m3}` recorded, 6 results, 9 ledger lines | pass |

The `nan` row is the one nothing had previously checked end to end: batch 2's fix was verified by
direct call on `Observations` only, and this run puts a `nan` through `append_observation`'s JSON
write, the apparatus fingerprint and `run.yaml`'s YAML round-trip. **It survived the wiring** — no
stop, no serialization failure.

**Attack 3 — the sentinel, reproduced.** Mutated `Observations.changed` to fail on `null → value`
using an independently constructed counts-based detector (`null_probes > 0` and
`total_probes == null_probes + 1`; a bare `first != incoming` cannot see this transition at all,
since `record` precedes `changed`). Confirmed non-degenerate first: of the reviewer's six false-stop
runs it fired on exactly the `null → value` one. Full, unfiltered suite under the mutation gave
**exactly the report's five failures**, including Fixture N's
`test_a_declared_probe_records_the_five_sub_keys_per_condition`. **The sentinel is real**, and the
report's measurement is confirmed rather than taken on trust.

**Decision 11's own pin discriminates.** A genuine cross-condition mutation (the earliest
`_first_answered` entry for that fact overriding the pair's own) makes
`test_g3_run_start_round_never_trips_the_gate_across_conditions` fail on `run_a_project`'s
`assert main([...]) == expect_exit` — `assert 1 == 0` — with stderr reading ``condition
`01_model=m2`'s fact `model_revision` changed: m1 → m2``: the **second run-start call**, exactly as
the design predicts. Recorded for the next reviewer: the first mutation attempted was **blind** —
falling back to another condition's value only when the pair's own is missing, which never happens,
because `record` runs before `changed`. A mutation is a claim too.

**Attack 4 — the ordering chain, on the reviewer's own schedule.** A 6-execution plan with the fact
moving on call 5: ledger holds **5** lines with the moving observation last, `executions.jsonl` holds
**3** `completed`, no `run.yaml`, no `latest`, and the diagnostic names `pinned` and `r1 → r2`. So the
shipped 4-vs-3 discriminator is **mechanism, not fixture coincidence** — the ledger length tracks the
probe calls including the moving one at any plan length — and it fails on its own assertion under the
assert-safe append mutation (Major 2). The record loss (`run.yaml` and `latest` absent) is this
commit's expected shape and is tasks 5–7's to close.

**Attack 5 — the batch-1 guard pin is green and unedited.** `git diff c33f061 HEAD -- tests/` has
**zero** deleted lines. `test_max_failed_fraction_is_measured_against_the_test_partition`'s body,
docstring included, is sha256 `61e63bc5dc75…` (2327 bytes) at `2a10c3a`, `7d907b2` **and** HEAD —
byte-identical, expectation and argument both. Arm B
(`test_an_all_completed_truncation_stays_completed_at_exit_0`) is identical at `ffd1d8499690…`; arm C
(`test_a_mixed_truncation_is_partial_at_exit_3`) is byte-identical for its whole length, followed
only by task 4's new section.

**Attack 8 — no count claim.** Grep over every added line for `unblock`, `executable`, `six`,
`three`, `zero configs`: no hits anywhere in the diff.

## What could not be checked

- **Whether Decision 14's `Collector` actually redacts Major 1's message.** `secrets.redact` matches
  by containment over the same value set, and the rendered message contains the value, so it should —
  but that is **read**, not run, and only becomes runnable once task 5/7 land the collector.
- **Fixture G1's final-state expectations** — `run.yaml`, `status: failed`, exit 4, three `unobserved`
  entries, `W-APPARATUS-UNANSWERED` exactly twice — are tasks 5–7's and are unassessed here.
- **Whether a smaller fixture than G1 separates its readings** (the design's own unmeasured item 6)
  was not searched for.
