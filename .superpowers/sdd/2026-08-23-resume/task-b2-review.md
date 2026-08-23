# H9b batches 3-4 — tasks 5, 6, 7, 8, 9 — review

**Reviewed 2026-08-23** at `b465a3a`, branch `h9b-resume`, in a worktree of my own.

## 0. The normalization list, committed BEFORE the comparison is run

This section is committed on its own, before any two-sided run, so that its content cannot
be shaped by what the comparison found. Batch 1 established the method and this repeats it.

**The batch changes a shipped artifact for the second time in one slice** (`executions.jsonl`
gains `recorded_columns` and `returned`), so the evidence is a real `run` on a `main` worktree
against a real `run` on this branch, not a green suite.

**Two sides.** A `git worktree` at `main` with its own `uv sync` venv, and this branch's
worktree. A positive control first: each side's `publishable.__file__` must resolve inside
its own worktree, or it is one build run twice.

**One project per side**, scaffolded and executed only through the console script
(`publishable new`, `generate experiment`, `run`, `dry-run`), **outside this repository**.
`index.csv` is copied with `cp -p` **before** both runs, so `st_mtime_ns` cannot move the
input manifest — batch 1 measured that as the one path-independent input that can.

**Normalizing exactly these, and nothing else:**

- any key or line component named `at`, `started_at`, `wall_seconds`;
- `run_id` and everything derived from it (the run directory's own name);
- absolute paths, on either side, including each side's own project directory and worktree;
- `hostname`;
- `code_hash`, `parameters_hash`, `uv_lock_hash` and `input_manifest_hash`, and the run
  directory name's 7-hex `code_hash` prefix — two worktrees are two `src/` trees;
- `attempts`.

**What is compared, and the bar for each.**

| Comparison | The bar |
|---|---|
| Run-directory tree, path by path | Differences must be **added paths only**, each attributed to a named task |
| `run.yaml`, leaf by leaf in order, after normalization | **Zero differing leaves**, and identical leaf order |
| Every shared path's size and sha256 | Every difference on the list above |
| `executions.jsonl`, **key by key, line by line** | Differences must be **added keys only**: `recorded_columns` and `returned`, in that position, on every line. Any removed key, reordered key, or changed value outside the list is a finding |
| `sweep.yaml`, `manifest/input.json` | Byte-identical |
| `run` stdout / stderr / exit | Identical after path normalization |

**`main` vs HEAD conflates batch 2's `identity.json`**, which is already reviewed and PASSed;
that one added path is attributed to batch 2 rather than counted against this one. The
isolation of batches 3-4's own artifact change is `git diff 635b3a9..b465a3a -- src/`, read
for every write site.
