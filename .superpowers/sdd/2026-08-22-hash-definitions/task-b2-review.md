# Batch 2 review — tasks 3, 4

**Commits reviewed:** task 3 `84a7393`, task 4 `3baaa46`, report `10f5fe0`.
**Verdicts: task 3 PASS (one Major, disclosed and adjudicated below). task 4 PASS.**

## The forced pin-arm edits — adjudication

**Verified by diff** (`git show 84a7393 -- tests/test_cli.py tests/test_hashes.py`): every touch to
arms A, B, D, E is exactly a `, None` appended to an existing `code_hash(...)` call, plus added
docstring prose. No `assert` line, no digest literal, no comparison target moved in any of the four.

**Verified by mutation** (batch 1's own two production mutations, re-run against the current tree):

- `hashes.py`'s fold separator doubled (`b"\n"` → `b"\n\n"`): arms A, B, C, D all failed on digest
  mismatch; arm E (empty-tree case) unaffected — reproduced batch 1's result exactly. Reverted by
  editing back; `diff` against the saved copy was byte-identical; all five re-ran green.
- `diff.py`'s `_render_row` comparison inverted (`==` → `!=`): both arm N tests failed. Reverted the
  same way; both green again.

So the mechanism still catches what it caught. The question is whether it should have needed touching
at all.

**Structural finding (Major, process rather than correctness).** `docs/superpowers/specs/2026-08-22-
hash-definitions-design.md` Decision 4 explicitly considered and rejected a defaulted `include`
parameter (mutation-table row 1, "Alternatives rejected... A default of `None` — rejected above",
anti-fail-open grounds) — **at commit `f8450f9`, 18:09:34.** The guard pin (task 2, commit `ad59bdd`,
19:10:52 — **an hour later**) then captured arms A, B, D using the *old* one-argument
`code_hash(tree)` call, despite the required-two-argument signature already being final, written
design. Task 2's own brief for task 3 anticipated exactly one mechanical touch (arm E, "13 mechanical
edits in the pins," matching the pre-batch-1 count) — it did not anticipate arms A, B, D because they
did not exist yet when that count was taken. Task 3's own brief is explicit: **"Guard-pin arms this
task may edit: E, and only by adding `None`."** Task 3 edited A, B, D as well, which its own brief did
not authorize by name.

Given a defaulted parameter *was* an available alternative and was rejected for reasons unrelated to
the guard pin (an anti-fail-open argument, made before the pin existed in its final form) — the
mechanism, not the diff, is where this sits: the root cause is a **sequencing gap in task 2**, which
captured new pin arms against a signature Decision 4 had already superseded, one hour after that
decision was written down. Task 3 inherited an import-breaking situation with no clean way to satisfy
"only arm E" and "the suite must import." Its response — the same class of edit already blessed for
arm E, applied uniformly, fully disclosed in the report's own "Concerns for the reviewer" section and
in each arm's docstring — is the least-damaging fix available in-batch, and it is verified (above) to
have moved nothing a mutation can see. It is nonetheless a literal breach of arms A's and D's own text
("no task in H6a is authorized to change one character of this test," "NO AUTHORIZED EDITOR — a
passing arm IS the proof") and of task 3's own brief's named scope. **Adjudication: accept the edits as
correct and harmless in substance (diff- and mutation-verified), but record the Major against
process** — an implementer should not self-authorize touching a device whose entire value is that no
implementer can, even when the touch is provably inert; this called for a controller ruling before the
edit, not after. The fix for next time is upstream: task 2 (or whichever task next captures pin arms
against a signature already decided in that slice's design) must write the calls in the post-decision
shape from the start.

## No pinned hash literal moved

Verified by running, not by reading: every one of `_H6A_BASE_DIGEST`, `_H6A_BASE_WITH_ENV_DIGEST`,
`_H6A_RUN_DIGEST`, `_H6A_RUN_WITH_ENV_DIGEST`, `_H6A_TRACKED_PYD_DIGEST`, `_H6A_EMPTY_DIGEST`, and arm
C's seven other figures are unchanged text (`git show 84a7393` / `3baaa46` — no line touching a literal
digest anywhere), and the full suite reproduces every one of them (`2945 passed`, see below). PASS.

## `check-ignore`'s tri-state returncode — all three branches proven, not just present

Mutated each branch independently against `src/publishable/provenance.py`:

- **rc not in (0, 1) → always pass through (never raise):** `if False:` in place of the returncode
  check. Caught: `test_h6a_fixture_i_a_submodule_refuses_rather_than_reading_empty_stdout` — `Failed:
  DID NOT RAISE ContractError`.
- **rc 1 folded into the error branch (`if result.returncode not in (0,):`)**: caught
  `test_nothing_excluded_returns_every_candidate_unchanged` — raises where it must return the full set.
- **rc 0's exclusion computation broken (`excluded = set()` unconditionally)**: caught both
  `test_the_ascii_control_subtracts_exactly_the_excluded_path` and
  `test_h6a_fixture_f_the_z_claim_on_excluded_non_ascii_paths`.

All three reverted by editing back, `diff` against saved copies byte-identical, full
`tests/test_provenance.py` (15 tests) green after each revert. No branch is unpinned. PASS.

## Ruling F — global/system config neutralized on every invocation

`grep -rn "check-ignore" src/ tests/ docs/*.md` → exactly one real invocation
(`provenance.py:70`), which passes `env=dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null",
GIT_CONFIG_SYSTEM="/dev/null")` and `-c core.excludesFile=`. No second, un-neutralized call exists.
PASS — no Major here.

## Ruling H — `E-CODE-FILE-LIST` keeps one emit site

`grep -rn "E-CODE-FILE-LIST" src/ tests/ docs/*.md` → one `raise` (`provenance.py:81`), one assertion
on `.code` (`test_provenance.py:244`). Re-derived independently, matches the report.

**§ Errors row check.** `docs/reference.md` carries no row for `E-CODE-FILE-LIST` yet — this is
correct, not a gap: the plan (`docs/superpowers/plans/2026-08-22-hash-definitions.md`, task 8, steps
7–8) explicitly assigns both new § Errors rows (`E-CODE-EMPTY` and `E-CODE-FILE-LIST`) to task 8,
"two batches after `E-CODE-FILE-LIST`'s code lands," specifically so both new rows are written by one
task with one shape. Batch 2 is not that task. PASS.

## The proxy question — three states built and checked against what shipped

- **A tracked file deleted from the working tree:** built a repo where `src/pkg/step.py` is committed
  then `rm`'d. `hashed_files` walks the filesystem (`base.rglob("*")`), never `git ls-files`, so a
  deleted-but-tracked file is simply absent from the candidate list — never listed, never attempted to
  be read. Confirmed by running `hashed_files(root, include)` on that tree: only `templates/t.py`
  came back, no crash.
- **A tracked file inside `__pycache__`:** same tree carried a tracked `src/pkg/__pycache__/x.pyc`.
  The fixed skip set (`_SKIP_DIRS`) drops it before `include` is ever called, so git is never asked
  about it — confirmed present in this same run (absent from the result, no subprocess call needed for
  it).
- **A submodule silently dropping content:** covered by the shipped `test_h6a_fixture_i_...`, which
  this review independently re-verified above (mutation 6 fails it). `check-ignore` on a submodule path
  exits 128, and the shipped code raises rather than reading the empty stdout as "nothing excluded."

All three answer correctly against what shipped. PASS.

## The docstring carry-forward

`hashes.py:78`, "Read from the working tree, not from git" — checked both call paths.
`grep -n "code_hash(repo_root" src/publishable/cli.py` → `cli.py:2347: ch = code_hash(repo_root,
None)`, still the mechanical `None` task 3 put there; the real git-backed predicate built in task 4
(`provenance.unignored_under_hashed_trees`) is not wired at that call site yet — that is task 5's.
`hashes.py` itself imports nothing from `provenance` or `subprocess`. The sentence stays true in
substance as well as in code, for now. PASS — correctly deferred to task 5, as batch 1's review ruled.

## Mutations the report claims — re-run

- **Mutation 1** (defaulted `include`, `uv run mypy` against a synthetic in-tree caller omitting it):
  reproduced — `error: Missing positional argument "include" in call to "code_hash"  [call-arg]`.
- **Mutation 3** (drop `-z` on both ends, split on newlines): reproduced —
  `test_h6a_fixture_f_the_z_claim_on_excluded_non_ascii_paths` fails, both non-ASCII files leak into the
  kept set exactly as the report describes.
- **Mutation 6** (route through `_git`): reproduced — `test_h6a_fixture_i_...` fails with `DID NOT
  RAISE ContractError`.
- **The empty-candidate-list short circuit control**: read rather than re-mutated (the test itself
  monkeypatches `subprocess.run` to raise `AssertionError` if called, and is built and run before the
  patch is applied — read directly, this ordering is correct and is what makes the control meaningful).

All reverted by editing back; each revert verified by re-running, not by `git status`.

## Grepped, not assumed — independently re-checked

- `grep -c "code_hash(" tests/test_hashes.py` at the state right after batch 1 (`4c9e6da`) returns 19
  raw lines, of which 2 are docstring prose (`code_hash(tmp_path /` inside a sentence, and "the 13
  `code_hash(` call sites" as a quoted phrase) — 17 real call sites, matching the report's "17"
  exactly. Same check on `tests/test_cli.py` at that commit: 4, matching. The report's corrected count
  is accurate, independently re-derived rather than trusted.
- `grep -rn "E-CODE-EMPTY" src/ tests/"` → one docstring mention in `test_hashes.py`, no code, matching
  the report's claim that task 4 does not touch task 8's surface.
- `grep -n "code_hash(" src/publishable/*.py` → exactly `hashes.py`'s definition and `cli.py`'s one
  call. The "one production caller" claim holds.

No disagreement found with anything the report claims about other tests, other rows, or other code.

## Undisclosed drops

Diffed both briefs (`task-3-brief.md`, `task-4-brief.md`) against what shipped. Task 3: all of steps
1–7 present (required parameter, `code_hash_of` extraction, identity test on both a bare and a
narrowing `include`, all 14 named call sites plus the four extra pin-arm sites, arm E's mechanical-only
touch, mutation 1 named as partly blind, the reading-obligation for step 7). Task 4: all of steps 1–9
present except the § Errors row addition — but that step ("§ Errors row / emit-site count" wording in
this task's own brief refers only to the emit-site grep, not a new row; the row itself is task 1's
step-6-style mechanical pass applied by task 8, per the plan) — nothing dropped that this task owned.
No undisclosed gap found in either.

## Gates

- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **93 files already formatted**
- `uv run mypy` → **Success: no issues found in 52 source files**
- `uv run pytest -q` (foreground, after clearing `pytest-of-joon` and `__pycache__`) →
  **2945 passed, 1 skipped, 2 xfailed** — reconciles exactly with the claimed baseline
  2939 + 1 (task 3) + 5 (task 4) = 2945.

## Summary

| Task | Verdict |
|---|---|
| 3 | PASS — one Major (process): pin arms A, B, D edited outside task 3's own named authorization (arm E only), root-caused to a sequencing gap in task 2 capturing new arms against a signature Decision 4 had already superseded an hour earlier. Substance verified inert by diff and by re-running batch 1's mutations. |
| 4 | PASS — no findings. |

Findings below, most-severe first.
