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
