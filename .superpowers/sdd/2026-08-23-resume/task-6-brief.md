## Task 6

**Pointer: Decision 6 binds this task, and so does a standing pin you may not touch.**

`attempts` becomes a count of ledger records.

- `run_record.assemble_run_yaml` gains one optional keyword, a mapping from
  `(step, condition_index, repeat_label)` to an `int`, defaulting to `None`.
- `_execution_block` writes that count when the mapping is given and **`1` when it is not** — so the
  `None` branch is byte-identical to today.
- `runner` or `lineage` gains the reader that counts a triple's records off `executions.jsonl`.
  **Appended 2026-08-23: the grep is already done and there is no such reader** — correction 21
  attributes all seven hits, and the two ledger-reading functions that do exist
  (`apparatus.replay_ledger`, `freeze._ledger_probe_names`) read `apparatus/probes.jsonl`, a different
  file. So you build the **first** reader of this ledger, knowingly, and task 8 is its second caller;
  write it once, where both can use it, and say in your report where you put it and why. Re-run the
  grep and report it anyway — if it now finds a reader, that is a finding.

**`run_status`'s bare `assert len(results) >= planned` is NOT changed, and its docstring is not
edited.** Design Decision 6: `resume` satisfies it by construction, because task 8 reconstitutes the
skipped triples into the same `results` list and task 9 passes the **full** plan's length as `planned`.
If you find you cannot satisfy it, that is a **finding to report**, not an assertion to relax.

**H7d Part B's `max_failed_fraction` pin is left alone.** It holds that a truncated plan reports
`completed` at exit `0`, with a written justification in a shipped test's docstring, and it is filed
with its owner told to argue against that justification rather than discover it. **Editing that
assertion or its justification in this slice is indistinguishable from weakening a pin to pass.** Do
not touch it.

**Must not touch:** `run_status`'s body or docstring; the `max_failed_fraction` pin; any `*.md`.

**Mutations:** keep the `1` literal when the mapping is given (caught by a fixture whose ledger holds
two records for one triple — buildable today by appending a second line by hand, so it does not wait
for `resume`); count records for the wrong triple (caught by the same fixture's neighbour staying at
`1`, which is the assertion that makes the first non-vacuous).

---

