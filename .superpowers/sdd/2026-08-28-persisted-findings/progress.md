# SDD ledger — plan: docs/superpowers/plans/2026-08-28-persisted-findings.md

Pre-flight scan. Seven tasks, one file each except Task 2 (diagnostics.py + cli.py) and Task 6
(documents). Cross-task couplings checked:
- T1 changes a message; T2 persists messages. **T1 must precede T2**, and the plan orders it so —
  otherwise an intermediate commit writes a host path into a record.
- T2 produces the list; T3 consumes it. T3 cannot land first.
- T4 (report) reads the block T3 writes. T4 after T3.
- T5 (oracle) is downstream of T3 by construction: the literal cannot move until the block exists.
- T6 documents what T1-T5 built; T7 verifies the whole.
No task contradicts another and none mandates something the review rubric treats as a defect.
Ruling: work proceeds directly on `main` with commit and push per task, as G1 and G2 did on the
same instruction. Cost if wrong: history on main rather than a branch, which this project has
accepted twice before.

Task 1: implemented (commit 76aa752). Suite 3556 passed / 1 skipped / 2 xfailed (+2 new tests);
ruff, format and mypy clean. Both mutations reported with output: restoring the interpolation fails
the message test, and adding an offending interpolation fails the source sweep.
Ruling: the agent STALLED mid-task waiting on a monitor it had scheduled, and returned without
running its gate or committing. Resumed with an instruction to run the four commands in the
foreground with long timeouts. Recorded because it is a dispatch defect rather than an implementer
one — a brief that says "gate before committing" should also say how long the gate takes. Cost if
wrong: none; the work was correct once it ran.
Note for later tasks: T1 found the old message pinned in TWO places the brief did not name — a
whole-stdout literal in `tests/test_cli.py` and README's demo transcript. A message this project
prints is quoted in more places than a grep of `src/` shows. Later tasks changing printed output
must sweep `tests/` and the four documents before believing they are done.
Task 1 review: PASS on both verdicts, one Moderate. The reviewer reproduced both mutations
independently, read `verify_manifest` to confirm `E-INPUT-CHANGED` carries relative paths and is
correctly unflagged, and checked the two collateral edits were faithful rather than loosened.
Ruling: the Moderate is REAL and I fixed it myself rather than opening a fix round. The whole-stdout
guard pin's docstring read `SOLE AUTHORIZED EDITOR: NONE` and had just been edited — a docstring
contradicting what happened to it, which is this repo's most-repeated defect. Re-authorized in the
convention the file already uses at its H9b pin, naming the slice, the task, the reason, and what
the task was permitted to change. A one-line docstring correction does not need a fresh implementer.
Cost if wrong: a docstring, revertible.
Ruling: the sweep's known gap is ACCEPTED, not widened. It matches a `.warn(`/`.error(` message
interpolating `repo_root`/`input_dir`/`output_dir`/`Path(...)` by NAME, and misses a path assigned to
an intermediate variable first. Widening it needs dataflow analysis inside a test; the runtime
alternative — comparing every message against a list of host paths — is exactly the redaction pass
Decision 4 refused in favour of prevention. Every message in the two functions today is written the
literal way, so the sweep covers the whole live surface and the gap is about a shape nothing uses.
Cost if wrong: a future message could carry a path through a renamed variable and the sweep stays
green; the reviewer of that task would have to catch it.

Task 2: implemented (commits b9938c7, 9212a4a). All 12 print sites replaced — 5 in `_prepare_run`,
7 in `_execute_prepared`. Suite 3560 passed / 1 skipped / 2 xfailed (+4); ruff, format, mypy clean.
Source pin proven: reverting one real site to a bare print fails it with a message naming the
function; restored from a cp backup and re-run green.
The implementer disclosed one incidental fixup: a test pinned `len(dataclasses.fields(Prepared)) == 37`
and `findings` makes it 38, with the docstring counts moved to match. That is a field-count pin
doing its job, not a loosening — the review is checking it as such.
Review dispatched with `streams` as its first question. Several of the 12 sites printed to stderr,
and a silent move to stdout is invisible to every assertion about the record — the exact shape this
slice is otherwise built to prevent.
Task 2 review: PASS on both verdicts, no findings. The reviewer checked all 12 stream assignments
individually (5 stderr, 7 stdout, none crossed), confirmed no out-of-scope command's rendering was
touched, traced the list from construction through `Prepared` to extension without reassignment or
sort, and — the part that mattered — mutated a site in `_execute_prepared`, which the implementer's
own report never exercised, proving the pin covers both functions rather than only the one mutated.
Task 2: complete (commits b9938c7, 9212a4a).

Ruling: **Task 5 is ABSORBED into Task 3, and this is a defect in my plan rather than in any task.**
The plan sequences the oracle update after the assembly, but the global constraint requires a clean
suite at every commit — and the moment Task 3 puts `findings:` into `run.yaml`, the bit-stability
oracle pinning the whole normalized record fails. There is no ordering in which the two are separate
commits and the suite is green in between: the block cannot exist before Task 3 and cannot be
unpinned after it. Task 3 therefore determines whether its fixture emits any finding, and updates the
oracle in the same commit if it does, reading the diff rather than regenerating the literal.
Cost if wrong: one larger commit instead of two, and the oracle's movement is reviewed with the
change that caused it rather than a task later — which is arguably where it belongs anyway.
Task 3 review (opus): PASS both verdicts, 1 Medium + 2 Low. The strongest review of the slice — it
AST-extracted each golden literal at both commits and diffed them (+4 leaves, 0 removed, 0 values
changed), enumerated all EIGHT pinning tests by name and ruled each faithful, and mutated `assemble`
to sort the findings to prove the order test discriminates.
Task 3 fix round 1: all three addressed (commit c79cc51). Suite 3564 passed / 1 skipped / 2 xfailed.
Ruling: the Medium was MY comment from the previous slice, and the sweep it triggered found THREE
live homes where I had named one — `cli.py`, `hypotheses.py`, and a `test_cli.py` fixture template.
That is the repo's own lore reproduced exactly: sweep for the claim, not for the file the claim was
first noticed in. I verified the closure independently rather than spending a re-review cycle — the
claim now has no live home in `src/`, `tests/` or the four documents, the justification is rewritten
to survive on current facts, and the new end-to-end test exists with its reason in its docstring.
Cost if wrong: a scoped re-review skipped on a three-line fix I read myself.
Task 3: complete (commits 98dff8c, c79cc51).

Task 4: implemented (commits aa12e21, 8091f32). Suite 3567 passed / 1 skipped / 2 xfailed (+3);
ruff, format, mypy clean. Absent-case mutation fails 3 tests and passes after a cp restore.
The order fixture is three entries chosen so emission order differs from BOTH a by-code and a
by-level sort — the implementer sized it by counting the orderings it had to rule out and noting
that two elements can only ever rule out one. That is the discipline stated correctly and applied
without being asked twice.
Ruling: the stall is a DISPATCH defect and now a pattern, not an implementer one. Tasks 1 and 4 both
scheduled a background wait for their own 7-minute test run and returned without gating or
committing; Task 4 had an explicit "no monitors, foreground only" line and did it anyway. The
instruction is being read too late, inside the gate section. For the remaining tasks it goes in the
FIRST line of the dispatch. Cost if wrong: a resume message per task, which is what it has cost.
Task 4 review: PASS both verdicts, no findings. The reviewer rendered a findings-free record at
BOTH commits and compared the outputs directly — byte-identical, established by construction rather
than by reading — computed the two candidate sorts over the order fixture to confirm it really
discriminates, and mutated `_finding_rows` to sort by code to prove the order test fails. It also
noticed that `fixture_r`'s real run DOES emit findings and checked why the existing pins survive
anyway (they use filtered lookups, not whole-row equality) rather than accepting "unaffected".
Task 4: complete (commits aa12e21, 8091f32).
Task 6 review: PASS both verdicts, no findings. The reviewer grepped the code behind EVERY documented
claim rather than reading the prose — `assemble_run_yaml` for the shape and absent-when-empty,
`Collector.disclosed` for the shared redaction, `_disclose`/`E-INPUT-CHANGED` for the error level,
`report._finding_rows` for the render — and settled the commands list by finding `assemble_run_yaml`'s
only call site and tracing which handlers reach it (dry-run calls `_prepare_run` alone and never
persists). It recounted spec-defects independently at 151/61, matching the preamble.
Task 6: complete (commit 32d4cac).
