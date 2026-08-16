# SDD ledger — plan: docs/superpowers/plans/2026-08-16-credentials-and-secrets.md

Spec: docs/superpowers/specs/2026-08-16-credentials-and-secrets-design.md
Branch: h7c-credentials, from main at d86290c. Baseline: 1957 passed + 2 xfailed; ruff check, ruff
format --check (74 already formatted, 0 to reformat) and mypy all clean.

Standing authorization from the user, recorded because it changes what I stop for: subagent-driven
execution, and **merge without stopping to ask**. After merging, update CLAUDE.md,
docs/superpowers/spec-defects.md and docs/feasibility-llm-growth-studies.md. Push is NOT covered by
that authorization and is asked once at the end.

## Pre-flight conflict scan

Run before task 1, against the plan as committed at 878a862. Rows are pairs sharing a file or an
interface, plus one row per task for self-consistency.

| Tasks | Shared | What I checked | Finding |
|---|---|---|---|
| 1, 2, 5, 6, 12 | `docs/reference.md` | Whether an insertion by one moves a row or a count phrase another depends on | **Clean, and non-obviously so.** Task 2 owns two count phrases ("Five faults", "two today") and its Step 1 RE-READS and re-counts both rather than trusting them. Its ruling that both stay unchanged is correct: this slice's new codes are `validate` reports, not early-return load faults, so the enumeration task 1 adds to is a different one |
| 8, 9, 10 | `src/publishable/validate.py` | Whether two tasks write the same emit site or reorder findings | Clean. 9 produces `_check_required_env`, 10 produces `_check_requires_env` — separate functions, separate call sites. 8 adds a load site and touches neither |
| 8, 11 | `tests/test_validate.py` | Helper collisions | Clean, verified by name rather than by reading: all six helpers the plan defines (`_check_required_env`, `_check_requires_env`, `_files_under`, `_findings_of`, `_joined`, `_union_project`) return zero hits in `src/` and `tests/`, with a control (`messages_by_code`) that does fire. This is the trap that authored a name collision in the previous slice's plan |
| 3, 4 | `src/publishable/param.py` | Ordering | Clean. 3 adds the keyword-only argument, 4 renders it. `requires_env` is keyword-only so no positional contract moves |
| each task | itself | Tests specified against code specified; files created before touched | Clean. `Condition(index, label, values, is_baseline, selectors)` confirmed at `sweep.py:44-49` exactly as task 10 and 11 state it |

**No conflict required a ruling.** Recorded rather than omitted, because "the scan is clean" without
the rows is not a scan that was run.

## Rulings made before execution

Ruling: the plan's finding 2 was wrong and I measured it before dispatching. It reported ONE
exception-text construction site from `grep -rn "\.error\b"` — a grep that finds assignments to an
attribute, not constructions. `grep -rn 'type(exc).__name__' src/publishable/*.py` returns FIVE. Three
are `W-STATS-AGGREGATE-FAILED` warnings that never reach `run.yaml` (`run_record.py` mentions
diagnostics zero times, checked) but ARE in scope, because task 12's leak sweep covers stdout and
stderr. Redaction moved from a construction site to the two SERIALIZATION BOUNDARIES, so a sixth
construction cannot diverge from the policy. Cost if wrong: one more edit site than strictly needed
today.
Ruling: my own correction named the boundary `Diagnostic.render()`. It is `Collector.render()` —
`Diagnostic` is a frozen four-field dataclass with no methods. I misjoined a class list and a method
line read from the same file in two separate greps. The plan author read `diagnostics.py` and caught
it, and the ruling is strengthened by the correction: redacting per-`Diagnostic` would need the values
at construction, which is what the ruling exists to avoid. Both the spec and the plan carry the
correction rather than a silent fix.

Task 1: dispatched — mint `E-CRED-MISSING` and `E-CRED-PARAM-MISSING`, and record that the
  `requires_env` totality check mints nothing. Document-only, and the brief says honestly that no
  mutation reaches it; the dispatch turned that into a positive obligation instead — re-read each row
  against the code tasks 9 and 10 will build, and say what it was checked against.
Task 1: implemented at 5f416c1. 1957 passed + 2 xfailed, unmoved, as a document-only task must be.
Task 1: reviewed (opus). Spec compliance PASS; task quality FAIL with three Important, **all three in
  text my own plan supplied rather than in the implementer's execution.** Recorded that way round
  deliberately: the brief is mine, and a review finding against brief-supplied text is a finding
  against me.
  The substantive one: `E-CRED-PARAM-MISSING`'s row claimed THE MESSAGE names the parameter. It does
  not — task 10's message names the value, the condition and the variable, and the parameter arrives in
  the finding's `path` field, which `Collector.render()` prints on its own line. The plan's own test
  comment concedes this ("the parameter (via `path` above)"), so the plan disagreed with itself and the
  document took the wrong half. Reworded to say the FINDING carries the parameter while the MESSAGE
  names the value and the condition. Decision 1's grounds are untouched — they rest on the two messages
  being unshareable, which value-and-condition alone already establishes.
  Both rows also located their sibling by POSITION, the habit CLAUDE.md bans and which the brief itself
  invoked one step earlier when it forbade positional description of the insertion point. A brief can
  contain the defect it warns against. Both now name the sibling code, and the file carries zero
  "row above/below" references.
  Ruling on the third: the implementer justified its insertion point by the table being strictly
  alphabetical. The reviewer extracted all 119 codes and found SEVEN out of order — the table is not.
  The PLACEMENT is right, because the local `E-CONFIG-*` -> `E-CRED-*` -> `E-DATA-*` run is
  alphabetical and that is the run these rows join. Only the reason was wrong. Corrected by appending
  to the report rather than editing it, because a wrong reason for a right answer is what sends the
  next reader looking for an ordering that is not there. Cost if wrong: nothing today; a future
  inserter who trusts "strictly alphabetical" picks a slot that is not the run.
  Verified by the reviewer and worth keeping: decision 2 traced end to end in code — `param.py`'s
  `ValueError` -> `discovery.py`'s broad catch -> `E-TEMPLATE-LOAD` — rather than taken from the spec.
  One emit site per code, so neither needs a second row. Task 2's two count phrases are unaffected.
Task 1: complete. 1957 passed + 2 xfailed; ruff check, format and mypy clean. BASE for task 2 is below.

Task 2: dispatched — the two load-refusal count phrases. The dispatch made the point that the brief's
  prediction (both counts hold) was a PREDICTION and Step 1 was the measurement, with an explicit
  instruction not to adjust a count to match the prediction.
Task 2: implemented at af84611 / 10b488d. 1957 passed + 2 xfailed. Both counts measured by enumeration
  and both held. It also checked, unprompted, that task 1's two new rows do not cover the
  `requires_env`-totality fault — confirming the new sentence complements those rows rather than
  conflicting with them.
Task 2: reviewed (opus). Spec compliance PASS; task quality FAIL with one Important and three Minor.
  The reviewer rebuilt both counts from source rather than checking the implementer's arithmetic
  against the implementer's list, and returned a STRONGER result than the task had: `discovery.py`'s
  broad `except Exception` **relabels**, so even a template raising its own coded `ContractError`
  arrives as `E-TEMPLATE-LOAD`. "Two" is therefore not the current count but the ONLY count that guard
  can produce. That is the difference between enumerating today's raise sites and establishing a
  property, and it is worth carrying: the comment is now true of any future raise site too.
  Important 1, and it is the same origin as all three of task 1's: **plan-supplied text.** The
  paragraph kept "Five *faults*", then said "That is five *codes*", then "adds a *fault* to this list
  ... without a sixth to this count" — three nouns for one set, and the new sentence made the noun
  load-bearing. `validate.py`'s comment had been fixed to say "codes"; `reference.md`'s had not.
  Now "Five codes" / "five *codes*" / "adds a **shape** to `E-TEMPLATE-LOAD` ... without a sixth
  **code**", which is both internally consistent and true.
  Ruling: three of four review findings across two tasks now trace to text my plan supplied rather
  than to implementer error. That is not a complaint about the plan author — it is the expected rate
  for prose written ahead of the code, and it is exactly what the per-task review is for. Recorded so
  the pattern is visible if it continues past the document-only tasks.
  Ruling: Minor 1 corrected by appending to the report — it justified "five codes" by "five `return
  None` sites" and there are FOUR, since two codes share one return. The count is right, the
  correspondence is not one-to-one, and citing it invites the next reader to recount the wrong thing.
  OBLIGATION ON TASK 3, from Minor 2: `validate.py`'s amended comment now asserts a
  `requires_env`-totality `Param` fault, and `grep -rn "requires_env" src/publishable/` returns ONLY
  that comment at this commit. The claim is a forward reference that task 3 makes true. **Task 3's
  reviewer must confirm it became true**, or the comment is an unbuilt reader of a shipped surface —
  the defect shape this very slice exists to close elsewhere.
Task 2: complete. 1957 passed + 2 xfailed; ruff check, format and mypy clean. BASE for task 3 is below.

Task 3: dispatched — `Param(requires_env=)`, the H7b prerequisite. Pre-checked all three mutations
  against the BODIES of the tests the brief supplies. Mutation (b) is the one that matters and it is
  sound: the unknown-key fixture is `choices=["a","b"]` fully keyed PLUS `"zz"`, so `absent` is empty
  and dropping the `extra` half silences only the second block. Carried task 2's obligation explicitly.
Task 3: implemented at fbab1e8 / ceff925. 1962 passed + 2 xfailed (+5).
  **Task 2's forward reference is now true**, confirmed two ways rather than asserted: directly, and
  end to end through a real `templates/cred_assay.py` driven through `validate_config`, landing under
  `E-TEMPLATE-LOAD` and NOT under any `E-CRED-*` code — which is what decision 2 turns on.
Task 3: reviewed (opus). Spec compliance PASS; task quality FAIL with two Important and two Minor,
  and **no shipped behaviour wrong** — both Importants are false prose.
  The first is a docstring that claimed the honouring test guards against "ignoring `requires_env`
  entirely — storing it and checking nothing". Falsified by mutation: deleting the whole validation
  block while keeping the store turns BOTH refusal tests red, so that is not what this test uniquely
  guards. The sentence was transplanted from the spec, where it is about the ENVIRONMENT check that
  tasks 9-11 build and is true there. Ruling: fix the docstring, not the test — the reviewer measured
  that the test is the only one of five that goes red when `requires_env` leaks into `check()`, which
  makes it the sole guard on the closed-vocabulary invariant. It now says that.
  My first replacement named a specific value (`check("b")`) I had not verified; the leak would most
  plausibly bite on a value with a NON-empty list, so I removed the specific rather than guess. A
  correction that adds an unverified detail is how the third generation of a false claim starts.
  The second Important is a report inference: "the `TypeError` confirms the guard is correctly
  ordered" does not follow — a `TypeError` from iterating `None` proves the comprehensions RAN, which
  is what an absent guard looks like. And the report said "no disagreements found" while the brief's
  own rule ("if it is a `TypeError` the guard order was transcribed wrong") is FALSE: `DID NOT RAISE`
  is unreachable for that mutation under any correct transcription. Another brief defect that went
  unfiled. Both corrected by appending to the report.
  Ruling on mutation (c): the reviewer's verdict — **blunt, not blind** — is accepted. It reddens via
  a crash rather than an assertion, but the guard is pinned anyway by `pytest.raises(ValueError,
  match="choices")`, which the reviewer proved catches both a message missing the word and a changed
  exception type. Recorded because "the test went red" and "the test saw the difference" are not the
  same claim, and only the second justifies calling a thing pinned.
  Verified beyond the brief by the reviewer and worth keeping: the mirror mutation `if extra:` reddens
  only the FIRST block, so both totality directions are separately pinned; the end-to-end control is
  real (making the second write stay partial brings `E-TEMPLATE-LOAD` back, so no `sys.modules`
  short-circuit and no collision relabel); storage is pinned by two `AttributeError` tests.
Task 3: complete. 1962 passed + 2 xfailed; ruff check, format and mypy clean. **The H7b prerequisite
  has landed.** BASE for task 4 is below.
Task 4: complete. `Param.comment()`'s `choices` branch now renders each choice through a new
  `_choice_label` helper carrying its `requires_env` variables; `generic`'s two regression sites
  (`test_param.py`'s existing assertion, `test_materialize.py`'s generated-config line) are
  byte-identical since it declares no `requires_env`. Re-measured grep counts: `tests/` → 2 sites,
  `docs/reference.md` → 4 sites — both matched the brief's `478c1f3` count. Both prescribed mutations
  (annotate the written value everywhere; drop the `[]`-vs-missing-key distinction) were run, checked
  against the test bodies, and discriminated. 1964 passed + 2 xfailed; ruff check, format and mypy
  clean.
