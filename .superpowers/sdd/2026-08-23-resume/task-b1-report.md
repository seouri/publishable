# H9b batch 1+2 — tasks 1, 2, 3 and 4

**Written 2026-08-23** on branch `h9b-resume`, from `main` at `f2e545d`. Every figure below was
read off a run of the command it describes; nothing is carried from the plan or the design without
re-checking, and where the code disagreed with them the disagreement is named rather than smoothed.

## Task 4's normalization list — WRITTEN BEFORE THE COMPARISON WAS RUN

Recorded here first, and this section is timestamped by the commit that carries it. A normalization
decided after seeing a diff is a normalization chosen to hide it.

**Two sides.** A `main` worktree and the branch worktree, each with its own venv and its own
`uv pip install -e`, and a positive control asserting each side's `publishable.__file__` resolves
inside its own worktree — so a comparison that accidentally ran one build twice is caught rather
than reported as agreement.

**`run.yaml`, leaf by leaf, in order.** Normalized: any leaf whose own key is `at`, `started_at`,
`wall_seconds`, `run_id`, or `hostname`; `provenance.git.commit` (a fresh commit's SHA is
committer-timestamp-sensitive); and any string leaf containing either side's own base directory
(`config.data.input_dir`, `output_dir`, `provenance.git.repo_root`). **The three hashes are NOT
normalized**: the two projects are byte-identical apart from those paths, and `code_hash` covers
`src/**`+`templates/**` while `parameters_hash` and `input_manifest_hash` cover content, so all
three must be EQUAL across sides. A difference in any is a finding, not noise.

**The run-directory tree, path by path, by kind, size and sha256.** The expected difference, named
in advance: **`identity.json` exists on the branch side and not on `main`'s — one added file, and
nothing else added, removed or moved.** Every file whose bytes legitimately carry a path or a
timestamp is expected to differ in size/sha256 and is enumerated in advance: `config.yaml` and
`environment/repo_root.txt` and `manifest/input.json` (absolute paths), `run.yaml` and
`executions.jsonl` (timestamps and durations), `units.parquet` (a container whose bytes are not a
promise). Anything else differing is a finding.

**`sweep.yaml`** — compared as parsed documents, leaf by leaf, with no normalization at all: it
holds no path, no timestamp and no hash.

**`executions.jsonl`** — key by key per line, and the ordered `(step, condition, repeat, status)`
tuples. Values of `started_at`/`wall_seconds` normalized; every other value compared.

**stdout, stderr, exit code** — line by line, with each side's own absolute paths normalized.

**`dry-run`'s transcript, line by line.** Two expected differences, named in advance: the header
`and 7 fixed files in that directory:` becomes `and 8 …`, and one new line, `  identity.json`,
appears in the fixed-file list. Every other line must match after path normalization.
