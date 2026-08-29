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
