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

---

## Fix round 1

Reviewed at `5223383`; review at `.superpowers/sdd/2026-08-20-diff-freeze/task-b1-review.md`.
Both verdicts were PASS (one Major, seven Minors). Per this repo's convention of appending a
correction rather than retro-editing a record, the section above is left as originally written;
this section says what changed and what replaces it.

**MAJOR 1(a) — Arm F's coverage claim was false.** `tests/test_cli.py`'s
`test_h8b_arm_f_the_embedded_config_is_the_file` claimed *"No existing test asserts this equality
directly … never a whole-mapping comparison against the file on disk."* False:
`tests/test_acceptance.py::test_scaffold_then_run_produces_a_real_record` makes exactly that
comparison for the unswept case. **Changed:** the docstring now names that test as the real
neighbour and narrows the claim to what the arm actually adds — the *swept* case. **Verified by
running:** the unnarrowed `{**config, "sweep": None}` mutation in `run_record.py` fails both arm F
and the acceptance test; narrowed to fire only when `config["sweep"]["grid"]` is truthy, it fails
**only** arm F and `test_h8b_arm_g_parameters_hash_agrees_with_run_yamls_embedded_config` across
the full suite — `2 failed, 2520 passed, 1 skipped, 2 xfailed`, reproduced myself before writing
the correction. Reverted; `diff` against a pre-mutation copy of `run_record.py` byte-identical.
**What the arm genuinely adds:** the only place in the suite that would catch a *swept* run's
embedded config diverging from the file on disk — the unswept case is already covered by
`test_scaffold_then_run_produces_a_real_record`.

**MAJOR 1(b) — Arm E's coverage claim was half false.** The same test's docstring claimed *"No
existing test asserts `sweep.yaml`'s top-level key list or that no condition entry carries
`selectors`."* The second half is false: `tests/test_sweep.py`'s
`test_the_sweep_document_records_the_resolved_plan` asserts `doc["conditions"] == [...]` by full
dict equality, which already pins the entry key set — including `selectors`'s absence — exactly.
**Changed:** the docstring now separates the two halves, marks the `selectors` half as already
covered by that shipped test (named), and keeps only the top-level-key-list half as the arm's own
new-coverage claim. **Verified by running:** adding `"selectors": {}` to each condition entry in
`sweep.py`'s `sweep_document` fails arm E **and**
`test_sweep.py::test_the_sweep_document_records_the_resolved_plan` — `2 failed, 2520 passed, 1
skipped, 2 xfailed`, reproduced myself. Reverted; `diff` against a pre-mutation copy of `sweep.py`
byte-identical. **What the arm genuinely adds:** the top-level key list only — no shipped test
reads `sweep.yaml` as a file for its shape at all.

**The consequence, and the lesson.** Both false claims falsified the § Brief/design/plan vs. code
and § Concerns sections above ("None" / "None outstanding" were both wrong), which is now the
sixth consecutive report on this project to make that claim and be wrong. **The mechanical check
that would have caught it: before writing "no existing test asserts X," grep for X** — a
one-command check, run against the actual suite, not against memory of what the suite probably
covers. Doing that now for every "new coverage" / "not new coverage" claim in the original report
(arms A, B, D, G-1, G-3 as new; arm C, G-2 as not-new) reproduces the review's own attack-1 table:
all five "new" claims and both "not new" claims hold. Arms E and F did not, because their
docstrings named "the nearest neighbour" from reasoning about what a pin like this would probably
need, rather than from a grep run before the sentence was written.

**MINOR 1 — Arm A's `lock`-absence line is implied by the line above it.** If `lock` existed,
`iterdir()` would list it and the sorted-list equality would fail first, so the `lock` assertion
can never fail on its own — `CLAUDE.md`'s own "assertion implied by another in the same test"
shape. **Changed:** Arm A's docstring now says so explicitly, and says the list assertion is what
actually delivers it. Kept the line itself, since the brief prescribed it verbatim. **Verified by
construction** (as the review did): no reachable state fails the `lock` line while the list
assertion passes, so no mutation was run for this one — there is no branch for a mutation to
isolate.

**MINOR 2 — the authorized-editor clause was missing its auditable half.** The brief's step 3
required both docstrings to state *"task 3's report must show the diff is exactly one entry per
arm with nothing reordered."* **Changed:** added that sentence to both Arm A's and Arm B's
docstrings, immediately after each post-edit list. **Verified by reading:** `grep -n "task 3's
report"` now hits both docstrings; nothing else in the clause needed changing (sole-editor naming
and post-edit lists were already correct per the review's own read).

**MINOR 3 — the cross-document sweep was run for three spellings, not for the claim.** The
original sweep grepped `environment/{uv.lock,pyproject.toml}`, `sweep.yaml` and
`manifest/input.json` — none of which can match `README.md`'s own abbreviated run-directory tree
(`~/results/cohort-pilot/` → `run.yaml`, `conditions/`, `summary/`), so the sweep never looked at
the one place the claim ("no other document enumerates run-directory contents") was actually at
risk. **Changed:** re-ran the sweep over the four documents named individually plus `CLAUDE.md`
and `docs/feasibility-llm-growth-studies.md`, using `run.yaml` as a proven-to-fire positive
control and `environment/` as the actual claim. **Verified:** `run.yaml` hits — README 8,
design-principles 5, experimental-designs 1, reference 75, CLAUDE.md 4, feasibility 3 (control
fires everywhere, so the sweep can see); `environment/` hits — zero outside `reference.md`. Read
README's tree directly: it already omits `environment/`, `manifest/`, `sweep.yaml` and
`executions.jsonl`, by deliberate abbreviation, so it owes nothing and the conclusion is unchanged
— but this time the method looked. The report's earlier sweep description (above, unedited per
this repo's append-don't-retro-edit convention) is superseded by this paragraph.

**MINOR 4 — recorded, no action.** `E-FREEZE-NO-CONFIG` sits in `reference.md` prose with no
§ Errors row and no emit site. Task 12 owns § Errors rows; the reviewer measured six codes already
prose-only in `reference.md` with no table row anywhere (`E-EXPERIMENT-EXISTS`, `E-IO-FAILED`,
`E-PROJECT-EXISTS`, `E-STEP-EXISTS`, `E-TEMPLATE-EXISTS`, `E-TEMPLATE-INSTALLED-UNSUPPORTED`), so
this is precedented and not a rule breach. No document or code change made.

**MINOR 5 — a positional locator in new text.** `tests/test_hashes.py`'s
`test_h8b_arm_g_parameters_hash_agrees_with_run_yamls_embedded_config` said "the two below."
**Changed:** names the two tests (`test_h8b_arm_g_metadata_only_change_is_identical`,
`test_h8b_arm_g_max_failed_fraction_change_differs`) instead of locating them by position.
**Verified by reading** — the two named tests are exactly the two that followed positionally.

**MINOR 6 — three citations to a git-ignored brief, in a tracked report.** The plan
(`docs/superpowers/plans/2026-08-20-diff-freeze.md`, tracked) holds the identical content to the
brief at its own § Task 13 and § Task 14. This section replaces the earlier § Brief/design/plan
vs. code and § Concerns wording rather than editing it in place (see the note at the top of this
Fix round): where this Fix round cites source material, it cites the plan's task sections, not
"the brief."

**MINOR 7 — two wording slips in § The two files' new paragraph.** `docs/reference.md` read
"never modified since" (no referent for "since") and argued "naming it here would…" while the
sentence itself names the file. **Changed:** "since" removed (now "written at run start and never
modified"); the sentence restructured so it states the two true properties directly — not a third
thing to edit, and the section is not renamed on the file's account — without the
self-contradicting "naming it here would" framing. **Verified by reading** the corrected sentence
against Minor 7's own diagnosis; no other instance of either phrasing exists elsewhere in the diff
(grepped).

**Corrected § Brief/design/plan vs. code — disagreements found, restated for this round.** Two:
Arm F's and Arm E's own coverage claims, both above. Both are claims about the shipped test suite
that the task made without grepping for the string in the claim first, which is exactly the
category that section exists to hold, and both were closed in this round rather than carried
forward.

**Corrected § Concerns, restated for this round.** None outstanding after this round's fixes.
Minor 4 is recorded, not fixed, by design (task 12's). Minor 1 has no code action available — it
documents an assertion that cannot fail on its own rather than removing it, per the brief's
verbatim prescription.

**Gates after all fixes, on the reverted tree:** `ruff format .` run before committing;
`ruff check .` clean; `ruff format --check .` → 84 files unchanged; `mypy` → 47 source files, no
issues; `pytest` → full suite, unfiltered.
