# H8b batch B1 (tasks 13, 14) — report

**Status: complete.** Both tasks done, in order 13 → 14, each committed separately.

**Commits:**
- `152688f` — H8b task 13: pin the run directory, the record's figures and the recorded plan before anything moves
- `af87572` — H8b task 14: what a run-start config copy is, said before the code writes one

**Test summary:** full suite `2522 passed, 1 skipped, 2 xfailed` (baseline 2513 + 9 new arm tests; task 14 added no test, so the count held at 2522 through it). `ruff check .` clean, `ruff format --check .` → 84 files unchanged (task 13 added no file, task 14 touched only `docs/reference.md`, which the formatter does not process), `mypy` → 47 source files, unchanged.

## Task 13 — the seven arms

All seven literals were produced by driving `run_a_project` (a sweep of 2 conditions × 2 seed repeats, 8 units) and reading the artifacts back with `yaml.safe_load`, plus one direct call to `parameters_hash`/`design_digest` — never transcribed from `cli.py`. Captured via a throwaway script before writing any assertion, then re-verified by the tests themselves.

- **Arm A** (run directory root) — `['conditions', 'environment', 'executions.jsonl', 'manifest', 'run.yaml', 'sweep.yaml']`, `lock` absent. New coverage — no existing test asserts the full root list.
- **Arm B** (`environment/`'s contents) — `['pyproject.toml']`. New coverage — no existing test asserts the full list (existing tests check individual files' bytes/existence).
- **Arm C** (record's key lists, status, exit) — `run.yaml` and `provenance` key lists, `status: completed`, `draft: False`. **Not new coverage** — restates, verbatim, what `test_h8a_arm_a_...` / `test_h8a_arm_b_...` already assert; kept here so H8b's own pin is self-contained.
- **Arm D** (five figures `diff` reads) — `provenance.environment` (minus `python_version`, asserted present and non-empty) `== {'manager': 'uv', 'uv_lock': None, 'uv_lock_hash': None}`; `apparatus is None`; `upstream == []`; `code_hash`/`parameters_hash`/`input_manifest_hash` each start `sha256:`. New coverage as a group (individual figures had scattered prior coverage; this is the first place all five are pinned together as `diff`'s operand set).
- **Arm E** (`sweep.yaml`'s recorded plan) — top-level keys `['design_digest', 'conditions', 'repeats', 'labels', 'order', 'execution_order']`; every condition entry's keys `['index', 'label', 'values', 'is_baseline']`; no `selectors` in any entry; `design_digest(config) == sweep.yaml['design_digest']`. New coverage.
- **Arm F** (embedded config is the file) — `run.yaml['config'] == yaml.safe_load(cfg.read_text())`. New coverage (existing tests read sub-fields of `config`, never a whole-mapping comparison against the file on disk).
- **Arm G** (`parameters_hash` agrees with its own embedded config), in `tests/test_hashes.py`:
  - `parameters_hash(run_doc['config']) == run_doc['parameters_hash']` — driven through a real run (imports `run_a_project` from `tests.test_cli`). New coverage.
  - metadata-only edit → identical — **not new coverage**; the same claim `test_parameters_hash_excludes_metadata_and_the_two_paths` already makes, over a different literal.
  - `limits.max_failed_fraction` edit → differs — new coverage for that specific key (existing "differs" test edits `parameters.analysis.method`; none edits `limits`).

**Authorized-edit clauses:** Arm A's and Arm B's docstrings each name task 3 as sole authorized editor and state the post-edit list in advance — Arm A: append `'config.yaml'` (sorted) → `['conditions', 'config.yaml', 'environment', 'executions.jsonl', 'manifest', 'run.yaml', 'sweep.yaml']`; Arm B: append `'repo_root.txt'` (sorted) → `['pyproject.toml', 'repo_root.txt']`.

**Two mutations, both run against the full suite:**
1. Added `(run_dir / "environment" / "stray.txt").write_text("x")` beside the shipped `pyproject.toml` capture in `cli.py`. Result: Arm B **FAILED** (`environment/` list gained `'stray.txt'`), Arm A **PASSED** (root list unaffected) — 1 failed, 2521 passed.
2. Moved the write to `(run_dir / "stray.txt")` (run-directory root instead). Result: reversed exactly — Arm A **FAILED**, Arm B **PASSED** — 1 failed, 2521 passed.

Both mutations reverted by editing the line back out; `git diff` on `cli.py` empty after revert; full suite re-run green at 2522 passed both before committing.

## Task 14 — the document ruling

`docs/reference.md` changes, all additive, no behavior/verdict/status/exit-code claim touched:

1. **§ The two files** gains one paragraph after "`reproduce` accepts either …": names the run-start byte copy, states its purpose (`freeze`/future `resume` reaching the config before `run.yaml` exists), cross-references § The other files a run writes as the section that enumerates run-directory contents, and states explicitly that "the two files" counts roles (edit / report), not every file in a run directory.
2. **§ The other files a run writes** gains a new subsection, `` `config.yaml` and `environment/repo_root.txt` — what a mid-run command reads instead of `run.yaml` ``, placed as the first artifact (settled-before-first-execution kind, beside `sweep.yaml`/`allocation.json` in the intro sentence). States what reads each artifact and the remedy when absent (`E-FREEZE-NO-CONFIG` for a build predating the pair), and closes with the boundary sentence: the pair holds exactly the two facts a mid-run command cannot otherwise obtain or compute — the config as it was and the repo it came from — everything else is either computable from those two or a recorded `run.yaml` figure, and `code_hash` at run start is specifically *not* recoverable later, which is why `freeze` does not compare code.
3. **§ Run identity's tree** gains `config.yaml` as its own line after `run.yaml`, and `repo_root.txt` joins the existing `environment/{uv.lock,pyproject.toml}` brace. The tree's final `└──` marker (on `summary/...`) is unaffected — checked, since the insertion landed above it among `├──` lines.
4. **§ CLI reference's `resume` sentence** — verified rather than edited. It already reads "that run directory already contains the config it used," which was false at `0a636af` (per `H8-SCOPING.md` § 4) and becomes literally true once `config.yaml` exists at run start (task 3). No change made — editing it would have resolved the defect the wrong way per the brief's own instruction.

**Consistency passes, both run:**
- Mechanical (fenced blocks skipped): no trailing whitespace/tabs/invisible unicode in added lines (checked programmatically against the diff); no duplicate anchors after the new `###` heading (checked against a synthetic collision to prove the sweep can fail — it caught `## Foo Bar` vs `## foo-bar`); all links/anchors I added resolve (`#the-other-files-a-run-writes`, `#cli-reference`).
- Cross-document, swept over `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md` (by name), plus `CLAUDE.md` and `docs/feasibility-llm-growth-studies.md`: none of the other five files enumerates run-directory contents (`environment/{uv.lock,pyproject.toml}`, `sweep.yaml`, `manifest/input.json` — all grepped, zero hits outside `reference.md`), so none needed the new artifacts added. "The two files" as a phrase appears only in `reference.md`; the one other place a "two files" idea is implied (the TOC line `- [The two files](#the-two-files) — config.yaml and run.yaml`) still correctly names the roles and needed no edit. Sweep proven non-vacuous first by grepping `repo_root.txt`, which is present only in my own new text (six hits, all in `reference.md`) before checking the zero-hit files. `spec-defects.md` has no entry for the resume-sentence defect to strike (it lives only in the dated `H8-SCOPING.md`, which per `CLAUDE.md` is not retro-edited); task 14's file list doesn't include it and the brief doesn't ask for a strike there.

## Brief/design/plan vs. code — disagreements found

None. Every literal captured for task 13's seven arms matched the brief's stated values exactly (root list, environment list, key lists, five figures, sweep.yaml shape, embedded-config equality, hash agreement) — no reconciliation was needed. Correction 4 in the plan's own § Corrections against the code (claiming `CLAUDE.md`'s `EXIT_EXTERNAL` clause is false) is itself overruled per the progress ledger, and grepping `CLAUDE.md` confirmed the shipped text is already the past-tense, non-contradictory form the ledger describes — left untouched, as required; neither task 13 nor 14 touches `CLAUDE.md`.

## Concerns

None outstanding. Both authorized-edit clauses are in place for task 3 to consume; task 14's document changes are additive-only and match the controller's ruling; gates are clean at the expected deltas (2522 tests, 47 mypy source files, 84 formatted files).
