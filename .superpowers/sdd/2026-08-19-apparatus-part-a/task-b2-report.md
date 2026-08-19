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
