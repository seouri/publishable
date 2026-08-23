## Task 4

**Pointer: Ruling V binds this task. It is the batch's real-command review target.**

Task 3 wrote the artifact; this task **measures that nothing else moved**, and it is the disclosure's
evidence rather than its assertion.

Build two editable installs — one on a `main` worktree, one on the branch — with a positive control
printing a distinct `publishable.__file__` per side. Run **one** config through the real console
script on each and compare:

- `run.yaml` **leaf by leaf, in order**;
- the run directory tree **path by path, by kind, size and sha256** — `identity.json` is the one
  expected addition and it is on the normalization list as an addition, named in advance;
- `sweep.yaml`, `executions.jsonl` **key by key**, stdout, stderr, the exit code;
- **`dry-run`'s transcript line by line** — the `7` → `8` change and one new line are the two expected
  differences, named in advance.

**Write the normalization list into your report BEFORE running the comparison.** Every remaining
difference must be attributed individually; an unattributed difference is a finding, not noise. **Green
tests are not the evidence.**

**Must not touch:** anything. This task writes a report and, if it finds a difference, files it.

---

