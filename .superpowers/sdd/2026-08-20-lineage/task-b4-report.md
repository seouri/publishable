# Task 12 (batch 4) — `_contained` wired into `read_upstream` and `read_condition`

Dated 2026-08-20, against branch `h8a-lineage` at `39256e3` (batch 3 closed).

## What changed

`src/publishable/artifacts.py`: `read_upstream` and `read_condition` each computed a `step_dir`
and then ended in a bare `self._read(step_dir / name)`. Both now route through the shared
`StepIO._contained(base, name, code=)` helper task 5 built for `reuse_from` — unchanged in this
task — passing `code="E-ARTIFACT-NAME"`, the code `_resolve` already raises for `write`/`path`/
`exists`/`append`. No other line in either function moved; the base computation (scope routing,
condition nesting, `_nest_repeat`) is exactly what it was.

`tests/test_artifacts.py`: four new tests, placed immediately after the existing `read_upstream`/
`read_condition` block (before `_mixed_arm_roster`) —
`test_read_upstream_name_containment_refuses_traversal_absolute_path_and_symlink_escape`,
`test_read_upstream_positive_control_a_forward_separator_and_an_interior_dot_still_read`, and the
`read_condition` equivalents (`summary` scope, `conditions=[(0, "baseline")]`,
`step_scopes={"fit": "condition"}` — the shape
`test_read_condition_resolves_a_non_repeat_scoped_step_without_a_repeat` already uses).

## Suite delta, and why it is attributable to this task alone

Full, unfiltered `uv run pytest -q`: **2503 passed, 1 skipped, 2 xfailed**, twice (before and after
the mutation round, byte-identical). Baseline per `CLAUDE.md` and `progress.md`'s batch-3 close was
**2499 passed, 1 skipped, 2 xfailed**. Delta: **+4, zero pre-existing tests moved.** The four are
exactly the four new tests above — no shipped test failed, changed outcome, or needed touching.
`ruff check .`, `ruff format --check .` and `mypy` are all clean at the stated baseline (47/84).

**This also confirms the design's measured claim held**: nothing in `tests/`, the four documents,
or `src/publishable/templates/` reads through a `..` segment. Had it, this task would have broken
a pre-existing test, which did not happen. No finding to report on that front.

## The three refusals, and the fixture that discriminates each

Both readers get the same three arms as `reuse_from`'s own Fixture N (batch 3), each targeting a
file that **exists** and holds distinguishable content, so an unenforced check returns it rather
than failing for an unrelated reason:

1. **`..` traversal** — `secret.json` written *outside* the run tree entirely (`tmp_path/secret.json`
   for `read_upstream`, same for `read_condition`), reached via `os.path.relpath(secret, step_dir)`
   from inside the step directory. Refused by the `startswith(resolved_base)` half of `_contained`.
2. **Absolute path, outside the base** — the same secret file, named by its absolute path. Also
   refused by the `startswith` half — this arm alone does not discriminate the absolute-path
   clause, per batch 3's finding about the identical `reuse_from` arm.
3. **Absolute path, *inside* the base** — `step_dir / "ok.json"`, holding distinguishable content,
   named by its absolute path. This is the one arm refused **only** by `Path(name).is_absolute()`:
   its target sits inside `resolved_base`, so `startswith` alone would return it. This is the
   discriminating case named in the brief and in batch 3's Minor 1 (an absolute name pointing
   *inside* the step dir), applied here to both new readers.

A fourth arm (symlink escape — `step_dir/escape_dir` symlinked to an outside directory holding
`leak.json`) is also present for both readers, matching `reuse_from`'s Fixture N shape, though the
brief's own table names only three refusals; carrying it costs nothing and matches the shipped
`reuse_from` test it was copied from.

**Positive control, both readers**: `programs/a.json` (the documented worked example, a forward
separator) and `programs/gpt-4.1__seed29.json` (an interior dot that must still dispatch as
`.json`) both still read.

## Mutations run, against the full, unfiltered suite

All four reverted by editing the file back to the exact prior text (no `git checkout`), verified
by re-running. A diff against a pre-edit copy of `artifacts.py` after the last revert showed only
the two intended lines changed (see below).

| # | Mutation (exact) | Result | Assertion that caught it |
|---|---|---|---|
| 1 | `read_upstream`'s last line changed from `return self._read(self._contained(step_dir, name, code="E-ARTIFACT-NAME"))` to `return self._read(step_dir / name)` | **FAIL** — `test_read_upstream_name_containment_refuses_traversal_absolute_path_and_symlink_escape` (`DID NOT RAISE ArtifactError` on the `..` arm); 1 failed / 118 passed in `tests/test_artifacts.py`, confirming `read_condition`'s arms stayed green | Fixture N's `read_upstream` arms |
| 2 | `read_condition`'s last line changed the same way | **FAIL** — `test_read_condition_name_containment_refuses_traversal_absolute_path_and_symlink_escape` (`DID NOT RAISE ArtifactError`); 1 failed / 118 passed, confirming `read_upstream`'s arms stayed green | Fixture N's `read_condition` arms |
| 3 | Wire it into only one of the two | **Already demonstrated by 1 and 2**: each mutation left the *other* reader's arms — and both positive controls — passing, so the two call sites are independently covered; no separate run needed |
| 4 | Widen `_contained` to refuse any separator (`"/" in name or Path(name).is_absolute() or ...`) | **FAIL on all three positive controls** — `test_read_upstream_positive_control_…`, `test_read_condition_positive_control_…`, and the pre-existing `test_reuse_from_positive_control_…` all failed with `ArtifactError` on `programs/a.json` | the positive control, for both new readers **and** the shipped `reuse_from` one |

Each mutation's body was read before trusting the failure (not run against a proxy): mutation 1
and 2 each touch only the named function's final line; mutation 4 touches only `_contained`'s
condition, shared by all three call sites, which is why it failed three tests at once rather than
one.

## The § Errors row this task names for task 9

`docs/reference.md` § Errors core raises (line 1026), the row at line 1040 beginning *"A `name`
that escapes the step's directory, an `io.append` onto anything but `.jsonl`, or an extension no
writer claims handed an object that isn't `bytes` or `str`"* → `E-ARTIFACT-NAME`, `E-ARTIFACT-
APPEND`, `E-ARTIFACT-UNWRITABLE`. This row's own wording does not restrict `E-ARTIFACT-NAME` to
the write direction, but it was written when `write`/`path`/`exists`/`append` were its only emit
sites; `read_upstream` and `read_condition` are now two more, and § Errors carries one row per
code rather than per site (`CLAUDE.md`'s own naming of this exact shape). Task 9 owns updating it.

## Docstrings and comments re-read (Step 2) — nothing false found

Read `read_upstream` (no docstring, only inline comments), `read_condition`'s docstring,
`_nest_repeat`'s docstring, and `_contained`'s own docstring in full. None of them claimed that
`read_upstream` or `read_condition` enforced (or lacked) a name rule — they describe scope
resolution and base computation, which this task left untouched. `_contained`'s docstring already
reads correctly post-change: it already said "the readers that use it each resolve against a
different one" (plural) before this task, anticipating exactly this wiring, and its warning that
"this is not a boundary … a step can `open()` any file on the machine regardless" already covers
the new call sites without edit. No claim needed deleting or rewriting.

## Disagreements between the brief/design/plan and the code, checked by grepping what each asserts

- **Design doc's task table (line 659) attributes this wiring to "Task 5"**, and its filings table
  (line 702) says *"The `..`/absolute escape in `read_upstream` and `read_condition` | Closed by
  task 5, not filed."* Grepped the actual code and `progress.md`'s batch-3 entry: task 5 (batch 3,
  commit `e21d795`) built `_contained` and wired it into `reuse_from` **only** — confirmed by
  reading `artifacts.py` before this task's edit, where `read_upstream`/`read_condition` still
  ended in a bare `self._read(... / name)`. The plan's own task 12 (`docs/superpowers/plans/
  2026-08-20-lineage.md` lines 887–946) is the corrected version — it explicitly re-measures "the
  two that ship enforce neither" and assigns the wiring to task 12 — so the plan already carries
  the correction; only the design doc's task-5 row and its filings-table entry are now stale
  against the shipped code and belong to whichever task does the design/filings-table sweep (task
  9's consistency pass, per its own remit).
- No other disagreement found. Grepped the brief's own claims (probe outputs, § Errors row
  ownership, the three-refusal table, the CLAUDE.md batch note "2499 passed… before your tests")
  against the measured suite and code; all held.

## Commits

- `406a86a` — code + tests: `_contained` wired into `read_upstream` and `read_condition`,
  Fixture N arms and positive controls for both readers
- this report, committed separately

## Concerns

None outstanding. The change is exactly the isolated, narrow wiring the brief scoped: no other
behaviour moved, the overshoot mutation is caught, and the full suite shows a clean +4 delta.
