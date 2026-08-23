# H6a batch 4 review — tasks 8 and 9

Reviewed at `c09e937` (task 9, head). Commits: `758f8a7` (task 8), `c09e937` (task 9 + report).

## Verdicts

- **Task 8 (`E-CODE-EMPTY`, its § Errors row, and `E-CODE-FILE-LIST`'s): PASS**
- **Task 9 (the stale owner corrected, zero-file blast radius): PASS**

## The report's three concerns, adjudicated

1. **The `E-CODE-EMPTY` row's table placement: right table.** The design
   (`docs/superpowers/specs/2026-08-22-hash-definitions-design.md` § The § Errors and § Warnings
   work) explicitly directs `E-CODE-EMPTY` to "new row in § Errors core raises" — not to § Errors
   `validate` reports, which is scoped to the `validate` command specifically. `E-CODE-DIRTY`
   (the sibling using the same `Collector` mechanism) has no row *anywhere*, is named in the same
   design table as "not H6a's… H6b task 17 owns that," and is correctly left untouched here. The
   parenthetical `*(no exception; a Collector diagnostic)*` in the `Type · code` column is an
   honest cell value — verified by reading `docs/reference.md:1101`'s header (`Raised by | Type ·
   code`) and by grep (`E-CODE-EMPTY` has exactly one emit site, `cli.py:2380`, and it is
   genuinely never raised, confirmed by reading the diff). Read, not behaviour — a table-placement
   question has no runtime test — but grounded directly against the design document's own
   instruction, which the report did not cite. No fix needed.
2. **`_h6a_t8_project` duplicating `_h6a_t5_project`: real, disclosed, avoidable duplication —
   Minor.** `_h6a_t5_project` always writes `src/pkg/step.py` and hardcodes its `.gitignore` text;
   `_h6a_t8_project` differs only in taking `gitignore` and `write_step` as parameters. Nothing
   structural stops `_h6a_t5_project` from gaining `gitignore: str = "..."` and `write_step: bool =
   True` defaults and serving both call sites — the two helpers are otherwise byte-for-byte the
   same shape (same tmp dirs, same roster CSV, same outside-package entrypoint route, same
   config-templating, same git init/add/commit). Not a Critical or Major: it is disclosed
   plainly in concern 2 of the report, it does not touch a guard-pin arm, and the "sibling that
   already got it right" trap this repo has hit before is about *silently* reinventing a walk
   that already existed correctly — here the reinvention is named at the point of use.
3. **Fixtures G/H reusing `configs/t5/`: matches an existing, disclosed pattern.** Confirmed
   `_H6A_T5_CONFIG` fixes `metadata.name: t5`, so `E-NAME-DIR` forces the directory name; the same
   coupling was already accepted for arm/fixture C. Disclosed in a comment at the call site. Not a
   finding.

## Both directions of the refusal — verified by mutation

- **Fires when it should (mutation 8 — delete the guard):** re-ran with the guard block removed.
  `test_h6a_fixture_g_a_wholly_empty_src_refuses_e_code_empty` and
  `test_h6a_fixture_h_a_wholly_ignored_src_refuses_e_code_empty` both failed, `main(["run", …])`
  returning `0` instead of `EXIT_WRONG`, with the printed `run.yaml` path ending `_e3b0c44` (the
  empty digest) — exactly the pre-slice behaviour. Reverted by editing back; diffed byte-identical
  against a saved copy; re-ran: 2 passed.
- **Honours the ordinary path / leaves no directory (mutation 9 — move the guard after
  `allocate_run_dir`):** re-ran with the guard moved past the `run_dir = allocate_run_dir(...)`
  call. Both fixtures failed specifically on `assert not list(results_dir.glob("*"))` — a run
  directory existed even though the run still refused with `E-CODE-EMPTY` — a different failure
  from mutation 8's, confirming the two mutations catch different properties. Reverted, diffed
  byte-identical, re-ran: 2 passed.
- **Mutation P1 (comparison against the empty digest, named blind in advance):** replaced
  `if not hashed:` with `if code_hash_of(hashed) == "sha256:e3b0c442…":` (verified the literal is
  the true empty-list sha256 by computing it directly). Both fixtures still passed — confirmed
  blind, as the brief predicted. Reverted, diffed byte-identical, re-ran: 2 passed.

## The guard's location — verified by moving it into `hashes.py` in a scratch copy

`test_code_hash_skip_list_matches_relative_path_not_absolute` and
`test_code_hash_handles_a_dot_git_intermediate_path_component` (both in `tests/test_hashes.py`,
calling `code_hash(tmp_path / "nonexistent_empty_repo", None)` directly) currently pass. Edited a
scratch copy of `code_hash` in `hashes.py` to raise when `hashed_files(...)` is empty: both named
tests then failed with the injected `ValueError`, at the `empty_digest = code_hash(...)` call line
— confirming by behaviour, not by reading, that the guard belongs at the caller and would break
these two negative controls if pushed into the pure hashing module. Reverted, diffed
byte-identical against the saved original, re-ran: 28/28 in `test_hashes.py` pass.

## Disclosure and ownership

- **§ Errors row for `E-CODE-EMPTY`:** one row, § Errors core raises, one emit site
  (`grep -n "E-CODE-EMPTY" src/publishable/*.py` → `cli.py` lines 2361/2373/2380, all inside/about
  the single guard, one `error(...)` call). Names both reachable situations (nothing under either
  tree; everything git-excluded) in the one row, as required.
- **§ Errors row for `E-CODE-FILE-LIST`:** `grep -n "E-CODE-FILE-LIST" src/publishable/*.py` →
  one hit, `provenance.py:81`. One row, correctly retroactively documenting task 4's code.
- **Four-document sweep:** `grep -rn "E-CODE-EMPTY|E-CODE-FILE-LIST" README.md
  docs/design-principles.md docs/experimental-designs.md docs/reference.md
  docs/feasibility-llm-growth-studies.md CLAUDE.md` → only the two new `reference.md` rows match;
  reproduced exactly as the report claims.
- **Mechanical pass, re-run:** both new rows are 4 pipe-delimited fields (`awk -F'|' '{print NF}'`
  → 4, 4); no trailing whitespace/tabs (`grep -nP '[ \t]$'` on both lines → no hits); both anchors
  (`#how-the-three-are-computed`, `#the-apparatus-core-can-only-observe`) resolve to real
  `###` headings (`### How the three are computed` at line 3096, `### The apparatus core can only
  observe` at line 3164).
- **The re-owned filing (`spec-defects.md`):** the correction is appended
  (`RE-OWNED 2026-08-22 (H6a task 9)`), the prior `AMENDED 2026-08-11` paragraph is untouched, and
  its claims reproduce: both negative-control tests are named correctly and still call
  `code_hash(tmp_path / "nonexistent_empty_repo", None)` for the empty digest; the new owner
  (H6a task 8) is a landed fact, not a placeholder; `validate` genuinely does not check this
  (confirmed by the design's own Decision 15/H6b-task-18 cross-reference, present in both the
  design doc and the plan). H1 Validation is confirmed stale as an owner — it shipped
  2026-08-11 and the code_hash-empty entry was never touched by it.

## Guard-pin arms — none moved

`git show --stat 758f8a7` touches only `docs/reference.md`, `src/publishable/cli.py`,
`tests/test_cli.py`, with **zero deletions** in `tests/test_cli.py` (129 insertions, 0 deletions)
and **no lines at all** in `tests/test_hashes.py`. `c09e937` touches only
`docs/superpowers/spec-defects.md` and the batch report. Arms A, C, D (no authorized editor), and
arm N (in `tests/test_diff.py`, untouched by either commit) are provably unedited by the diff
shape alone; arms B, E, F belong to other tasks and are likewise absent from the diff.

Re-ran batch 1's pin logic rather than assuming it still holds: arm E
(`test_h6a_arm_e_code_hash_of_a_directory_that_does_not_exist_is_the_empty_digest`) passes
standalone. Spot-checked arm A can still fail: temporarily corrupted `_H6A_RUN_DIGEST`'s literal
in a saved-and-restored copy of `tests/test_cli.py`; `test_h6a_arm_a_the_ordinary_path_does_not_move`
failed on the expected assertion; reverted and re-ran: passes. Did not re-run every pin mutation
for every arm (time-boxed); the diff-shape argument (zero deletions/modifications to any file
holding an arm) is the stronger evidence here since it rules out an edit to an arm by
construction, not just by spot check.

## Suite and gates

- `uv run pytest -q`: **2953 passed, 1 skipped, 2 xfailed** (matches the report's claimed count;
  baseline was 2951/1/2, task 8's stated `+2 tests`, task 9's stated `0 tests` — reconciled).
- `uv run ruff check .`: all checks passed.
- `uv run ruff format --check .`: 93 files already formatted.
- `uv run mypy`: Success, no issues in 52 source files.
- `git status` after every revert: clean working tree (all mutations reverted by editing back and
  verified byte-identical against saved copies before re-running).

## What was verified by behaviour vs. by reading

**By behaviour (ran or mutated and re-ran):** the full suite count; mutation 8 (guard deletion);
mutation 9 (guard moved past `allocate_run_dir`); mutation P1 (digest-comparison proxy); the
guard-in-`hashes.py` scratch relocation against the two negative controls; arm E re-run; arm A
mutation/revert spot check; `ruff check`, `ruff format --check`, `mypy`.

**By reading (grep/diff, not executed as a behavioural test):** § Errors row placement against
the design document's own table; one-emit-site claims for both new codes; the four-document
sweep for the two new codes; mechanical column-count/whitespace/anchor checks; the `spec-defects.md`
re-owning text against the design's Decision 15/H6b-task-18 cross-reference; the diff-shape
argument that no guard-pin arm's file was touched; the `git diff --stat` line count for
`tests/test_hashes.py` (393/21/414, matching the report) and that every changed line in the two
negative-control tests is a call rather than an assert (confirmed by reading the isolated diff
hunks, each showing `code_hash(...)` gaining `, None` with the `assert` keyword and compared
values unchanged).

## Findings

None survived verification. No Critical, Major, or Minor beyond concern 2 above (duplication,
already disclosed by the report, priced here as Minor and not requiring a fix on this pass).
