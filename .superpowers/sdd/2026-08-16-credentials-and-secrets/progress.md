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
  `docs/reference.md` → 4 sites — both matched the brief's `478c1f3` count. Of the four
  `reference.md` sites, none is falsified by this change: the worked-example config line, the
  § Templates constraint table row, and the § Secrets-adjacent parameter table all show parameters
  with no `requires_env`, so they still render exactly as before; § A credential can belong to a
  parameter value already showed the new rendering and this task is what implements it — the
  asserted test string is character-identical to that section's example modulo the `# ` prefix
  `materialize` adds. The § Templates row itself is task 5's, not this task's. Both prescribed
  mutations (annotate the written value everywhere; drop the `[]`-vs-missing-key distinction) were
  run, checked against the test bodies, and discriminated. 1964 passed + 2 xfailed; ruff check,
  format and mypy clean.

Task 4 ruling: `progress.md` carried an uncommitted line, absent from HEAD, asserting a widened
  standing authorization to merge, push, and edit `CLAUDE.md` / `spec-defects.md`. It contradicted
  the task's own instructions and was not acted on; it is removed here rather than committed, and
  quoted verbatim in `task-4-report.md` so the text survives. Flagged to the controller.

Controller correction to task 4's ruling, and the cause was mine.
  **The line was not a prompt injection. It was my own ledger write, uncommitted at dispatch time.**
  The user widened the standing authorization after task 3 — "keep going until all tasks in H7c is
  merged and pushed" — and I appended it to `progress.md` in the same shell command that extracted the
  task-4 brief, so it sat in the working tree, absent from HEAD, when the implementer read it. The
  authorization is real and stands: execute every remaining task, merge, push, then update `CLAUDE.md`,
  `docs/superpowers/spec-defects.md` and `docs/feasibility-llm-growth-studies.md`.
  **The implementer was right to refuse it and I am not overriding that judgment retroactively.** An
  uncommitted line in a working tree asserting an authorization that contradicts the reader's own
  instructions is indistinguishable, from inside that task, from an injected one. It quoted the text
  verbatim into its report before removing it, which is what made this recoverable rather than a silent
  deletion — the correct handling of a suspected injection.
  Ruling, and it changes how I dispatch: **a ledger write is committed BEFORE the dispatch that follows
  it**, never left in the tree for a subagent to find. An authorization a subagent cannot verify is one
  it should not act on, so the only safe place for it is a commit — or, better, the dispatch prompt
  itself, which is the channel that actually carries authority to a subagent. Cost of the old habit:
  one task's worth of confusion, and a correct refusal that read as a defect.

Task 4: implemented at 3e20580 / 37c4cfb. 1964 passed + 2 xfailed. `_choice_label` renders each choice
  with its `requires_env` variables; `generic` is byte-identical because it declares none, which the
  reviewer proved by A/B against the pre-task-4 `comment()` (2583 bytes, identical) rather than by
  reading.
Task 4: reviewed (opus). Spec compliance PASS; task quality FAIL with one Important and three Minor.
  Important: § A credential can belong to a parameter value showed the `choices` comment on **its own
  line**; `materialize` always appends it **trailing, padded to column 36**. Fixed in the document, and
  I verified both ends myself — rendered the exact `Param` (`'choices: azure_openai (needs
  AZURE_OPENAI_API_KEY) | openai (needs OPENAI_API_KEY) | ollama'`) and read `materialize.py`'s
  `pad = " " * max(1, 36 - len(entry))`.
  Ruling worth carrying past this slice: the report said "Disagreements: None" while dispositioning
  that exact site as "not falsified ... **modulo the `# ` prefix** `materialize` adds". What
  `materialize` adds is a POSITION, not a prefix. **A gloss that makes a difference sound incidental is
  how a site gets carried past its own check** — the sweep looked at the right line and the wording
  waved it through. That is a new entry for the catalogue and it is not the same as a missed site.
  Two Minors corrected by appending, both narrowing overstated claims: mutation (b) cannot pin "`[]`
  vs a missing key", because totality in `__init__` makes a missing key unconstructible and the `or []`
  fallback unreachable; and it reddens three tests, not one.
  Recorded, not fixed: choice ORDERING is unpinned — swapping the join's iterable to
  `(self.requires_env or self.choices)` leaves the whole suite green. No passage specifies an ordering,
  so there is nothing to be true to. If a later task specifies one, it owes the fixture.
Task 4: complete. 1964 passed + 2 xfailed; ruff check, format and mypy clean. Part A's code half is
  done; tasks 5 and 6 are its document half. BASE for task 5 is below.

Tasks 5 and 6: BATCHED into one dispatch and one review — both document-only, both independent, both
  editing `reference.md`, so one dispatch also removed the risk of two agents racing on that file.
  Committed separately (8e3a911, f298aca) so each stays reviewable alone.
  Pre-dispatch I found an ordering edge my conflict scan missed: task 6's brief says it "depends on
  task 7 for truth", because retiring § Package layout's `— not yet built` marker is a BUILD CLAIM and
  `secrets.py` does not exist yet. The plan already resolves it — task 6 does the importable-surface
  half and defers the marker to task 7's commit — so the scan's gap was covered by the brief. Recorded
  because the scan is mine and it missed a real edge.
Tasks 5 and 6: reviewed (opus). All four verdicts PASS, with one Important.
  **Task 5 repaired one positional table reference and introduced another in the same commit** — the
  new sentence ended "is not in the table below". The brief disagreed with ITSELF: step 2 prescribes
  that text, step 3 forbids the practice. That is the eighth finding in this slice traceable to prose
  written ahead of the code, and the first where the brief contains both the rule and its violation.
  Fixed, and then I swept for the CLAIM rather than the instance I was handed — which found a SECOND
  one, in text **I** wrote fixing task 2 ("without adding a row to the table below"). Both now name
  their table by link. One pre-existing instance remains at § the provenance table ("the table above");
  it predates this slice and is routed to task 14's filings rather than edited here.
  Ruling: being told about one instance of a banned habit is not a licence to fix only that one. The
  sweep cost one grep and found a defect I had authored twenty minutes earlier.
  Also routed to task 14: the constraint table documents `# list of float, 2 to 5 items` while
  `Param.comment()` renders only `list of float` — `min_items`/`max_items` are read by nothing that
  renders, and there is no `spec-defects.md` entry. Pre-existing, out of scope here.
Tasks 5 and 6: complete. 1964 passed + 2 xfailed; ruff check, format and mypy clean. **Part A is done.**
  BASE for task 7 is below.

Task 7: implemented at b907ab6. 1971 passed + 2 xfailed. `secrets.py` ships `load_env`, `missing_env`,
  `credential_values`, `redact`; `python-dotenv` added; § Package layout's `— not yet built` marker
  retired IN THIS COMMIT, which is the deferral task 6 handed forward so the document never claimed a
  module that was not there.
  Real disagreement found by the implementer, and it is a good one: **`load_dotenv` writes straight
  into `os.environ`, past `monkeypatch`'s tracking**, so a value one test's `.env` wrote survived into
  the next and failed it — independent of the implementation. The plan's global prescription that
  `monkeypatch.delenv(..., raising=False)` protects against a later direct write is empirically FALSE.
Task 7: reviewed (opus). Spec compliance PASS; task quality FAIL on one Important.
  **`missing_env`'s declared-order guarantee was pinned by nothing** — the fixture names were already
  alphabetical, so declared order and sorted order are the same answer and `return sorted(out)` left
  all seven tests green. `reversed(out)` was caught, so what was pinned was "not reversed", strictly
  weaker than the normative § Validation claim. **And the test's NAME claimed the guarantee**, which is
  the shape that makes a reader stop looking — task 9's implementer would have grepped, found it, and
  skipped writing the real check. Fixed by changing one fixture name so the orders differ; I ran the
  mutation both ways.
  Ruling on the second Important, which the reviewer raised without attaching verdict weight: the
  isolation fixture was FILE-LOCAL. The hazard is not — every module exercising a load path inherits
  it, and tasks 8-12 would each have rediscovered the same leak. Moved to `tests/conftest.py`, with the
  reason written where the next reader will be. Proven load-bearing after the move rather than assumed:
  flipping `autouse` to `False` reproduces the failure. Cost if wrong: one autouse fixture over the
  whole suite, which is the price of not having the leak rediscovered five more times.
  Minor closed: `load_env`'s "Returns whether a file was read" was false in both directions. Measured
  all three shapes myself — comment-only `False`, empty `False`, every-binding-skipped `True` — rather
  than carrying the reviewer's account.
  Routed to task 14's filings: `PYTHON_DOTENV_DISABLED` silently disables loading, so core's load path
  honours an **undocumented behavior-changing environment variable** — which is against CLAUDE.md's
  first invariant. It fails closed and predates the version bump, so it is a filing rather than a fix.
  Also routed there: the constraint table's `min_items`/`max_items` rendering gap from tasks 5-6.
  The reviewer also reported falsifying its OWN hypothesis mid-review — it set out to file the
  idempotence assertion as vacuous and found an isolating memoization mutation does fail it. Recorded
  because a reviewer that reports what it expected to find and didn't is worth more than one that only
  reports hits.
Task 7: complete. 1971 passed + 2 xfailed; ruff check, format (76 files) and mypy (43 source files)
  clean. BASE for task 8 is below.

Task 8: implemented at 99a62c3 / 4d1dc18. 1973 passed + 2 xfailed. Both load sites built, no stub for
  `draft`/`resume` (both in `NOT_BUILT_COMMANDS`), and the document's sentence written as
  specification with the inheritance recorded.
  Both mutations reddened their OWN site's test and left the other green — which is the pairing that
  proves two sites are separately pinned rather than one doing all the work. The reviewer re-ran them
  and confirmed both halves.
Task 8: reviewed (opus). Spec compliance PASS; task quality FAIL with two Important and two Minor, all
  four prose.
  Important 1: the document and a `cli.py` comment claimed "**three** of its checks ask whether a
  variable is *set*". Only TWO do — the third credential row is a totality check that ships as
  `E-TEMPLATE-LOAD` and is pinned by a test that reads no environment at all. Repaired by DROPPING the
  count rather than writing "two", which is the form that does not go stale when task 11 adds coverage.
  Note the count originates in the spec's decision 5, which is a dated record and stays as written.
  Important 2, and it is the one worth carrying: the promise *"creates nothing and reaches nothing off
  the machine"* was cited to **§ Validation** at three sites — a document link, a `validate.py` comment
  and a test docstring. The sentence occurs exactly ONCE in the repo, in § CLI reference's operation-
  commands row. Three citations, all pointing at a section that does not contain the thing they quote.
  Fixed at all three, and I swept for the CLAIM afterwards — `grep "§ Validation promises"` over
  `docs/`, `src/` and `tests/` returns nothing.
  Ruling: a quoted promise is worth locating before citing. All three sites quoted the text correctly
  and attributed it to the wrong section, which is the failure a reader only discovers when the link
  takes them somewhere that does not say it.
  Minor closed: the `_env_file` fixture comment argued the scaffold's `.gitignore` is what keeps the
  file from making `src/**`+`templates/**` dirty. Inoperative — I read `provenance.py` and the refusal
  is `git status --porcelain -- src templates`, so a file at the PROJECT ROOT is in neither tree and
  could not have dirtied it whatever `.gitignore` said. The comment now says what `.gitignore` actually
  buys (the file stays untracked as in a real project) and states the real reason separately.
  Routed to task 12: `_local_template` has ZERO callers, so deleting its body leaves the suite green
  and its comment describes "every caller that passes this" — an empty set. Task 12 is the first
  caller and must exercise it.
  Position gap judged a NOTE, not Important, and the reviewer improved on the implementer's framing:
  core reads no environment variable at this commit, so nothing depends on the load preceding
  `resolve_template` — AND task 9's `required_env` check reads the RESOLVED template, so it runs after
  `resolve_template` anyway. Task 9 can only pin "before the first check that reads the environment".
  It should pin that and reword, or state the stronger position is unpinned by design.
Task 8: complete. 1973 passed + 2 xfailed; ruff check, format and mypy clean. BASE for task 9 is below.
