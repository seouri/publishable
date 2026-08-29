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
