## Task 12: The consistency passes and the exit criterion

**Files:** whichever of the four documents the passes find defects in.

- [ ] **Step 0: H3a's four § Validation rows, by title not number.** `docs/superpowers/H3-SCOPING.md` names them as rows 243, 291, 292, 293 — **those numbers are already stale**: the first is now 244 and the weight rows are at 292–294, because the table grew above them during this slice. Verify by **row title**, which is stable: *"Collapse rule fits the column"* (task 2), *"Weight attribute exists"*, *"Weights are usable"*, *"Weighting looks undeclared"* (task 7). Each must have an implemented check emitting the identifier its row implies, and a test producing it. This is `CLAUDE.md`'s own "cite by section, never by line number" rule arriving as a concrete failure — do not re-cite the numbers.

- [ ] **Step 1: Both retirements, both directions.** `E-DATA-MEASUREMENTS-UNSUPPORTED` and `E-DATA-WEIGHT-UNSUPPORTED` must be absent from `src/**/*.py` **and** from every tracked `*.md`. The second direction is the one `comm -23` cannot see — a surviving row for a retired code is the mirror of an undocumented code. **State the command and prove it can fail.** Exclude `__pycache__` with `--include='*.py'`; stale bytecode has produced a false positive on this exact check before.

- [ ] **Step 2: The `NOT BUILT` count is nine**, and exactly `measurements` and `weight_by` left the list. This is a number in prose that no mechanical check catches.

- [ ] **Step 3: Registry counts.** § Errors `validate` reports 65 → 69, § Warnings core reports 18 → 19, and every new row's condition read from its emit site rather than from this plan. Both directions: every code `src/` emits is documented or is a surviving `-UNSUPPORTED`; every documented code is still emitted.

- [ ] **Step 4: `partition_units` is untouched.** `git diff main..HEAD -- src/publishable/units.py` must show no change inside it. **This is H3a's own claim to being first in H3, and H3b and H3c both rely on it.**

- [ ] **Step 5: The worked example did not move.** `cohort-pilot` declares neither field. Verify with a **real temporary commit** — a working-tree edit is invisible to a two-dot diff, which is how this check silently passes.

- [ ] **Step 6: The mechanical pass**, then the **cross-document pass** over `CLAUDE.md`'s seven drift classes. The ones this slice most plausibly disturbed: **config completeness** (two fields changed meaning), **enum comments** (`collapse` must list what the code accepts), **schema fields in prose**, and **declared vs. derived** (`technical_n` and `effective` are derived — no passage may show either as a settable input).

- [ ] **Step 7: Fix what the passes find; commit only if something changed.** A clean result is a real result — do not create an empty commit.

---

## Sequencing

1 → 12 in order. Tasks 1–6 are `measurements`, 7–11 are `weight_by`, and **the two halves share nothing**: if the slice runs long it splits cleanly at the 6/7 boundary. Task 1 is what tasks 3 and 5 both call; task 4 must precede task 5; tasks 6 and 11 retire their refusals only after the behaviour behind them works, so that no check lands as dead code behind a refusal. Task 12 runs last, over a settled tree.
