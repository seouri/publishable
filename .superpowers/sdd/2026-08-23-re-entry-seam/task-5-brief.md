## Task 5

`draft`'s three readers all ship and all are today testable only against **synthesized** records —
H8c Decision 7 says so in its own docstring. This task gives each a **real** draft.

Build, each through `main([...])` now that `draft` dispatches:

- **`report` refuses a real draft.** `main(["report", str(run_yaml)])` over Fixture Q's record →
  `E-REPORT-DRAFT`, exit `1`. Grep for the existing synthesized-record test first and **name it in
  your report**, so the new coverage is stated as a difference rather than as a count.
- **`study add` flags a real draft.** Bundle outside any repo (`study new`, then `study add`), then
  `report <study.yaml>` → the member's identity line carries the `**draft**` label and the render
  **succeeds**. Decision 7's asymmetry is the claim: a bundle flags, a single run refuses.
- **`diff` labels a real draft.** `main(["diff", draft_run_yaml, clean_run_yaml])` → the per-side
  header carries `draft` on one side and not the other. **Assert per side**, not as a substring of the
  whole output: `assert "draft" in out` has already passed in this repo because a member was named
  `draft_run`, and a `run` tag's pin has already passed on a bundle header's `##`.

**Each reader must be shown able to fail.** Neuter each reader's `record.get("draft") is True` test in
turn and confirm exactly the corresponding test fails.

**Must not touch:** `report.py`, `study.py`, `diff.py` — this task adds fixtures, not behaviour. If a
reader is wrong, that is a finding.

---

