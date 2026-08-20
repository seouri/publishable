# H7d Part A — Batch 2 report (tasks 4–8)

**Status: complete.** Every check and the ledger, no call site touched. `uv run ruff check .`,
`uv run ruff format --check .`, and `uv run mypy` (46 source files) are clean after every task.

## Commits

| Task | SHA | Subject |
|---|---|---|
| 4 | `c330c67` | probe invocation and the contained raise |
| 5 | `899f657` | the `apparatus_facts` projection, and its first reader |
| 6 | `5e45ca4` | a returned credential fails the command rather than being redacted into the record |
| 7 | `48b50c8` | null semantics, the unobserved counts, and the unanswered warning |
| 8 | `f1be329` | the append-only probe ledger |

## Test summary

Full-suite deltas, each measured by running `uv run pytest` directly and reading the tail:

| After task | Passed | Skipped | xfailed |
|---|---|---|---|
| baseline (batch 1) | 2371 | 1 | 2 |
| 4 | 2374 | 1 | 2 |
| 5 | 2381 | 1 | 2 |
| 6 | 2384 | 1 | 2 |
| 7 | 2388 | 1 | 2 |
| 8 (final) | 2392 | 1 | 2 |

Net: **+21 passed**, 0 skipped/xfailed change. `tests/test_apparatus.py` alone: 6 (batch 1) → 27.

Every mutation below was applied to the working file, confirmed to make the named test FAIL, then
reverted **by editing the file back** (never `git checkout --`), and confirmed green again by
re-running the file's tests. `find . -name __pycache__ ... -exec rm -rf {} +` ran between every
mutate/revert step.

| Task | Mutation | Assertion it breaks | Outcome |
|---|---|---|---|
| 4a | `except BaseException` → `except Exception` | `test_a_probe_calling_sys_exit_is_contained_too` | FAIL (SystemExit propagates instead of `ContractError`) → revert → PASS |
| 4b | `raise KeyboardInterrupt from None` → bare `raise` | `test_a_keyboard_interrupt_is_re_raised_fresh_and_argument_less` | FAIL (`str(exc) == "secret-token-abc123"` not `""`) → revert → PASS |
| 5a | delete the declared-key loop | `test_a_declared_fact_the_probe_omitted_is_E_APPARATUS_FACT_MISSING` | FAIL (`DID NOT RAISE`) → revert → PASS |
| 5b | project onto `declared` instead of keeping every key | `test_an_undeclared_fact_the_probe_returned_is_kept` | FAIL (key set drops `extra_diagnostic`) → revert → PASS |
| 5c | re-raise `coerce_scalars`' `ContractError` unchanged | `test_a_structural_fact_value_is_E_APPARATUS_FACT_TYPE_...` | FAIL (`E-STEP-RETURN-TYPE` vs `E-APPARATUS-FACT-TYPE`) → revert → PASS |
| 6 | equality → heuristic (see note below) | `test_a_fact_equal_to_a_declared_credential_value_is_refused` | FAIL (`DID NOT RAISE`) → revert → PASS |
| 7a | keep last observation, not first-answered | `test_the_first_answered_observation_wins_...` | FAIL (`'r2' == 'r1'`) → revert → PASS |
| 7b | derive warning from `facts_document()` nulls | `test_the_warning_is_one_finding_per_condition_and_fact_...` | FAIL, **1 finding against 3** — matches the design's own prediction | revert → PASS |
| 7c | emit once per null observation instead of once per pair | same test | FAIL, **4 findings against 3** (this fixture's own arithmetic — the brief's stated "8" is Fixture N's, not this test's fixture) → revert → PASS |
| 8 | ledger opened with `"w"` instead of `"a"` | `test_a_second_append_adds_a_line_and_rewrites_nothing` | FAIL (1 line on disk against 2) → revert → PASS |

**Note on task 6's mutation.** The brief's literal heuristic —
`len(value) >= 20 or any(c.isdigit() for c in value) and value.isalnum()` — was tried first and did
**not** fail the test: `"lab7"` contains a digit and is alphanumeric, so that exact formula flags it
too, and the mutation's two branches could not be told apart (the class of proposed-mutation-that-
cannot-differ CLAUDE.md warns about). The brief itself permits "or any entropy rule you like," so the
mutation actually run was a length-only heuristic (`len(value) >= 20`), which does not flag `"lab7"`
and genuinely diverges from the equality check — confirmed FAIL, then reverted.

## What was built (task by task)

- **Task 4** — `apparatus.observe_once(probe, cfg, *, probe_name)`. Calls the probe once;
  `KeyboardInterrupt` re-raised fresh and argument-less (`from None`); any other `BaseException`
  becomes `ContractError(code="E-APPARATUS-RAISED")` carrying the probe's own message. No redaction
  here — that is the call site's job (tasks 9/10), so this function and its tests only assert the
  message is carried, never removed.
- **Task 5** — `apparatus.check_facts(returned, declared, *, probe_name, credentials)`, giving
  `apparatus_facts` its first reader. Four ordered checks: shape (`E-APPARATUS-RETURN`, minted here
  per the plan's correction 4 — the design named only four codes), credentials (step 2, left as a
  single-line comment for task 6), the scalar walk (re-coded from `coerce_scalars`'s
  `E-STEP-RETURN-TYPE` into `E-APPARATUS-FACT-TYPE`, called with no `scope` so an `Estimate` falls
  through to the same refusal), and the declared-key check (`E-APPARATUS-FACT-MISSING`, last, so a
  credential-carrying payload is refused for the credential rather than for a missing key). An
  undeclared fact is kept, never dropped — the documented difference from a resolver's attribute
  projection.
- **Task 6** — filled step 2 of `check_facts`: every returned value compared by exact equality
  against every value in `credentials`; a match raises `E-APPARATUS-FACT-CREDENTIAL` naming the
  fact's key and the credential's variable name, never the value.
- **Task 7** — `apparatus.Observations`, an accumulator over per-(condition, fact) null/total
  counts. `facts_document()` returns the first-answered value per (condition, fact), `null` if never
  answered; `unobserved(declared)` sums those counts over every condition, keyed by declared facts
  only; `warn_unanswered(c)` emits `W-APPARATUS-UNANSWERED` once per (condition, fact) pair with at
  least one null, reading the counts rather than `facts_document()` — the only construction that can
  see the flaky case (answered on some calls, null on others) that neither published mapping alone
  can show.
- **Task 8** — `apparatus.condition_key(index, label)` (imports `sweep.condition_dir_name` rather
  than reformatting; a `None` label — the no-`sweep` case — renders `f"{index:02d}"`) and
  `apparatus.append_observation(run_dir, *, phase, condition, probe, facts)`, which appends one JSON
  line (`at`, `phase`, `condition`, `probe`, `facts`) to `run_dir/apparatus/probes.jsonl`, creating
  the directory as needed, append-only. `docs/reference.md` § How artifacts are organized gained a
  tree row for `apparatus/probes.jsonl`, located beside the `executions.jsonl` row it was described
  against; no other row's position or count phrase was disturbed by the insertion.

## Disagreements with the brief, design, or plan found while executing

1. **Task 6's exact mutation formula does not fail the test it names** (detailed above under "Note
   on task 6's mutation"). The brief's own literal heuristic —
   `len(value) >= 20 or any(c.isdigit() for c in value) and value.isalnum()` — flags `"lab7"` (a
   digit is present and the whole string is alphanumeric), so it does **not** distinguish from the
   equality check for this fixture, contradicting the brief's claim that "`lab7` is four characters
   of ordinary lowercase-plus-digit text that no heuristic flags." The brief explicitly allows
   substituting "any entropy rule you like," so a length-only heuristic was used instead, and it does
   genuinely diverge. No code was changed on the strength of the brief's own formula — this is a
   mutation-design defect in the brief text, not a defect in `check_facts`.
2. **Task 7's mutation (c) count does not match the brief's "eight findings against three."** That
   figure is Fixture N's (task 11's, not built in this batch — this batch's pin is direct-call only).
   The task 7 tests in this batch build their own smaller fixture (2 conditions × 3 facts over 4
   observations) to stay self-contained at the direct-call surface; under that fixture, mutation (c)
   (emit once per null observation rather than once per (condition, fact) pair) produces **4 findings
   against 3**, not 8. Both counts demonstrate the same thing — the mutation's two branches produce
   different, wrong counts — so the mutation still catches the same defect; only the specific numbers
   differ from the brief's Fixture-N-derived figure, which is why they are reported explicitly rather
   than silently reconciled.

No other disagreement was found: task 4's docstring, task 5's `check_facts` ordering and re-coding,
task 6's exact-value match, task 7's per-(condition, fact) accumulator, and task 8's `condition_key`/
`append_observation` split were all buildable exactly as briefed, and every literal (`00`, `00_baseline`,
the `unobserved` sums, the ledger key set) was computed by the test from what it itself recorded, per
the plan's mutation-discipline and no-guessed-literals rules.

## Concerns for review

- `check_facts`'s credential loop is O(facts × credentials); fine at today's scale, worth a glance if
  a future template declares many facts and many credentials.
- `observe_once`'s return type is annotated `Apparatus` and the body returns `cast("Apparatus", returned)`
  to satisfy `mypy`'s `no-any-return` — the runtime value is genuinely unchecked until `check_facts`
  (task 5) is called on it, which is the design's own ruling (Decision 5 / plan correction 11): the
  contract is enforced at core's boundary, not here.

---

## Fix round 1 (review at `task-b2-review.md`, reviewed at `6df82fe`)

Commit: `c04d12d`. Full suite before this round: 2392 passed, 1 skipped, 2 xfailed (matches the
review's own run). After: **2395 passed, 1 skipped, 2 xfailed** (+3: the Major 1 discriminating
fixture, the Major 3 third-cell test, and a Major 2 regression test). Four gates clean
(`ruff check`, `ruff format --check`, `mypy` — 46 source files) after the round.

### Major 1 — `warn_unanswered` fired for an undeclared `null` fact

**Changed:** `Observations.warn_unanswered` now takes `declared: Sequence[str]` and skips any
`(condition, fact)` pair whose fact is not in it — the same list `unobserved` already takes.
Updated its docstring to state the narrowing and why (Decision 8's opening clause, Decision 4's
fourth row). Updated the one existing caller in the test file
(`test_the_warning_is_one_finding_per_condition_and_fact_including_the_flaky_pair`) to pass
`["fact_a", "fact_b", "fact_c"]`.

**New fixture:** `test_an_undeclared_facts_null_warns_of_nothing_beside_a_declared_null_that_must` —
one `record` call carrying both a declared and an undeclared fact, both `null`. Asserts exactly one
finding, that it names the declared fact, and that no finding mentions the undeclared one — a control
beside a positive, not an absence-only assertion.

**Verified by:** reverting the `if fact not in declared: continue` line (deleting the filter) and
re-running the full test file. `test_an_undeclared_facts_null_warns_of_nothing_...` **FAILED**
(`assert 2 == 1` — the undeclared fact's `null` produced a second finding). Reverted by editing the
file back; confirmed 30/30 passing again.

**Plan defect recorded, not fixed in the plan itself** (per CLAUDE.md, a plan is not retro-edited):
task 7's brief prescribed `warn_unanswered(self, c: Collector) -> None`, giving the implementer no
parameter to filter by. The review attributes this correctly as a plan defect rather than an
implementer error, and this report records the same attribution rather than disputing it.

### Major 2 — a NumPy-shaped fact value escaped as an uncoded `ValueError`, conditionally on a declared credential

**Changed:** `check_facts`'s credential loop now guards with `if not isinstance(value, str): continue`
before comparing to any credential value. A credential value is always a `str`
(`secrets.credential_values`'s return type), so nothing the check is meant to catch is skipped —
behaviour-preserving for Decision 6's stated property.

**New regression test:**
`test_a_fact_value_with_elementwise_eq_is_E_APPARATUS_FACT_TYPE_even_beside_a_credential` — a fact
value `numpy.array([1, 2])`, alongside a non-empty `credentials` mapping. Asserts
`E-APPARATUS-FACT-TYPE`, not a crash.

**Verified by:** reverting the guard (removing the `isinstance` check and its comment) and
re-running. Reproduced the exact escape the review reported:
`ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or
a.all()`, raised from `apparatus.py:166` inside the new test. Reverted by editing the file back;
confirmed the test passes again with `E-APPARATUS-FACT-TYPE`.

### Major 3 — the credential check had no test distinguishing exact-value matching from a pattern heuristic

**Changed:** nothing in `check_facts` itself — Major 3 was a missing test, not a code defect (the
review's own adjudication of report disagreement 1 already established the shipped code is correct
exact-value matching).

**New test:** `test_a_credential_shaped_value_that_is_not_a_declared_credential_is_kept` — a
**non-empty** `credentials` mapping (`{"INSTRUMENT_API_TOKEN": "lab7"}`) beside a fact value that is
long, mixed alphanumeric, credential-shaped (`"gpt-5.5-2026-06-11x9f3a2b8c"`) but not equal to the
declared value. Asserts the fact is kept, unchanged. This exercises the missing third cell the review
named: the two existing tests only covered *value equals a declared credential* and *`credentials` is
empty entirely* (whose loop body never runs).

**Verified two ways:**
1. Direct call: applied the review's exact heuristic mutation —
   `if len(value) >= 20 or (any(c.isdigit() for c in value) and value.isalnum()):` in place of
   `value == cred_value` — and re-ran the new test alone. **FAILED**: the credential-shaped value was
   wrongly refused (`ContractError ... E-APPARATUS-FACT-CREDENTIAL`) where the real code keeps it.
2. Full suite under the same mutation: **1 failed** (the new test), **2394 passed**, 1 skipped, 2
   xfailed — where before this round the identical mutation left the full suite at 2392 passed with
   zero failures. This is the concrete fix for "the highest-stakes check in the batch is pinned by a
   test whose loop body never runs."

Reverted the mutation by editing the file back; confirmed 30/30 passing (this round's file total)
and the full suite green again (2395/1/2).

### Major 4 — two test docstrings asserted claims the implementer's own report contradicted

**Changed by deletion/rewrite, per CLAUDE.md's "prefer deleting a claim to rewriting it":**
- `test_a_fact_equal_to_a_declared_credential_value_is_refused`'s docstring no longer claims a
  heuristic "agrees" with the equality check or that "the mutation below would have two branches that
  cannot differ" — both false, per Major 3's own finding that the brief's literal heuristic *does*
  flag `"lab7"`. Replaced with a statement of what is actually true: `"lab7"` is chosen so the
  exact-value check catches it regardless of appearance, which a heuristic cannot be relied on for.
- `test_the_warning_is_one_finding_per_condition_and_fact_including_the_flaky_pair`'s docstring no
  longer says "six observations," "eight," or "Fixture N." It now says what the fixture actually is:
  four `record` calls, not the plan's Fixture N (a separate, six-line `run`-level fixture owned by
  task 11), with this fixture's own four null observations — so a per-null-observation emission would
  produce four, not eight, matching this report's original disagreement 2 exactly.

**Verified by:** re-reading both docstrings against the fixtures they describe (the fixture code
itself was not changed for this docstring, only the earlier `Fixture N`/"eight" test whose
`warn_unanswered` call also needed the new `declared` argument for Major 1). No mutation applies to
prose; verification here is textual — the docstring's claims are checked against the literal fixture
code beside them, which is the same standard the review applied.

### Minor 1 — the `condition_dir_name` import cannot be pinned

**Changed:** `condition_key`'s docstring now states plainly that the import itself is not
behaviourally pinnable — `condition_dir_name` is exactly `f"{index:02d}_{label}"` with no
sanitisation, so inlining that f-string instead of importing it would produce an identical result for
every input. Also updated `test_the_condition_key_is_the_nn_label_form_and_a_labelless_condition_is_nn`
to assert `condition_key(0, "baseline") == condition_dir_name(0, "baseline")` (computed from the
import) before the pre-existing hard-coded-literal assertion, and its docstring says explicitly that
the hard-coded form pins a value, not the import.

**Verified by:** reading `sweep.condition_dir_name`'s body (`f"{index:02d}_{label}"`, confirmed by
`grep`) and confirming no mutation could be constructed that both (a) calls the import differently and
(b) changes any test's outcome — this is a claim, not a code change, so it was verified by reading
rather than by running a mutation that cannot exist.

### Minor 2 — a false "fewer than three observations" claim

**Changed:** deleted the clause "A build that kept the LAST observation instead cannot be told apart
from this one by any fixture with fewer than three observations" from `record`'s inline comment. The
true, remaining sentence ("The FIRST answered observation wins...") needed no rewrite.

**Verified by:** construction, as the review did — two observations `r1` then `r2` already distinguish
first-answered (`r1`) from last-seen (`r2`); no running needed since this was a prose deletion, not a
behavior change (the existing three-observation fixture and mutation (a) are untouched and still pass
and still fail correctly under the "keep last" mutation, confirmed by re-running that mutation:
`assert 'r2' == 'r1'` still fails as before).

### Minor 3 — a cited ground the cited code qualifies

**Changed:** `append_observation`'s docstring now admits `runner.execute_plan`'s `max_failed_fraction`
early stop alongside the `except Exception` comment, and states explicitly that the qualification
does not change the ordering argument (an after-the-execution append would still have recorded that
stop correctly; what it loses is a run that dies inside the execution itself or between executions
before the next scheduled append).

**Verified by:** reading `runner.py:741–745`'s `max_failed_fraction` break, as the review did; no
behavior changed, so no mutation applies.

### Minor 4 — no ruled ordering between `append_observation` and `check_facts`

**Changed:** `append_observation`'s docstring now states the gap directly — it writes `facts`
verbatim with no check of its own, no decision in the design orders it against `check_facts`, and
batch 3 (the first call site) must either sequence the calls correctly or the gap is
`spec-defects.md`'s. Also filed as its own entry in `docs/superpowers/spec-defects.md`
("`append_observation` writes `facts` verbatim with no ordering ruled against `check_facts`"), owner
H7d batch 3, satisfying the review's "either/or" with both.

**Verified by:** grep for "check_facts" and "append_observation" across `apparatus.py` — confirmed no
call site in this batch calls either from the other, so the gap is real and unaddressed by any
existing code path, exactly as the review found.

### Minor 5 — a fact key equal to a credential value is not checked, and is interpolated by `coerce_scalars`

**Not fixed — filed instead, per the review's explicit recommendation** ("Recommend a
`spec-defects.md` filing rather than a code change here — changing it silently would put a second
answer beside Decision 6's stated set"). Filed as
"a fact key equal to a credential value is not checked, and reaches a diagnostic via
`coerce_scalars`'s `{key!r}`" in `docs/superpowers/spec-defects.md`, owner unassigned — this is a real
narrowing question (does Decision 6's "fact value" extend to fact keys?) that this batch should not
resolve unilaterally.

### Findings not closed, and why

- **Minor 5** is filed, not fixed, on the review's own recommendation — closing it would add an
  unruled second answer beside Decision 6's stated scope ("a fact value").
- **Minor 4** is hand-forwarded to batch 3 via docstring + a `spec-defects.md` filing rather than
  closed by adding a check inside `append_observation` itself — adding one there would duplicate
  `check_facts`'s job and risks a second, possibly diverging, credential check. Batch 3 is better
  placed to decide whether to sequence the two calls or build something else, since it is the batch
  that first calls both.

All five tasks' original mutations (task 4's two, task 5's three, task 6's one, task 7's three, task
8's one) were re-verified unaffected by this round's changes by the full-suite run reported above;
none of this round's edits touch the code those mutations exercise except `warn_unanswered` (task 7)
and the credential loop (task 6), both of which were re-mutated and re-verified in this round as
described.
