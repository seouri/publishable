# Task 17 report

Status: COMPLETE.

Commit: `7160e16` (branch `h4a-resample-honoured`).

Tests: `uv run pytest` — 1797 passed + 2 xfailed (baseline 1795 + 2, two new tests added). `uv run mypy`
and `uv run ruff check .` clean. Both new tests confirmed FAIL before implementation, then PASS after.
Both named mutations (Step 5) applied, confirmed FAIL, `__pycache__` cleared, reverted in place,
confirmed PASS.

## What changed

- `src/publishable/cli.py`: right after `resample_spec = _resolved_resample(doc)` is resolved (once per
  run), builds `resample_beside` — `{"resample": {"method", "n", "stratify_by": list(...)}}` when
  `resample_spec["declared"]`, else `{}` — and merges it into `weighted_beside` (`.update`, run-wide, so
  the `report_by` level call at the existing `beside_n=weighted_beside` site carries it too) and into
  `cond_beside_n` (`{**_condition_beside_n(...), **resample_beside}`, per condition, feeding both
  `beside_n=cond_beside_n` sites). Both are the exact `beside_n` carriers `summarize_step` copies
  verbatim into every metric block, the same route `weighted_by` already takes — no new mechanism added.
- Updated the stale comment beside `resample_strata`'s sentinel choice, which said "nothing emits a
  stratum LABEL into `run.yaml` today (a future task records the attribute names)". That "future task"
  is this one, but it records the attribute *names* (`resample.stratify_by`), a coarser fact than the
  composed `|`-joined per-unit label the sentinel actually guards — reworded to say so rather than
  leaving it pointing at an already-passed future.
- `docs/reference.md` § Statistical reporting: extended the sentence the whole slice deferred to ("the
  resolved values are recorded in `run.yaml` beside the interval") with what it now means concretely —
  the `resample:` sibling's shape, the absent-not-null rule, and `resample.n` vs. `resample_draws` as two
  different facts. Added a second, clearly-labelled `mean_pred` example carrying a `resample:` sibling,
  placed after the shared worked example's own `r:` block rather than inside it, so that block's numbers
  (`ci95: [0.517, 0.683]`, `repeat_spread: {std: 0.014, ...}`, etc.) are untouched — verified by
  `grep -n '0.517, 0.683|−0.007, 0.059|0.014' docs/reference.md README.md docs/design-principles.md`
  returning the same lines as before the edit.
- `tests/test_cli.py`: the two tests from the brief, appended verbatim.

## The undeclared-case decision

Chose **absent, not null**, for an undeclared `resample` — matching task 1's existing pin exactly.
`resample_spec["declared"]` is `False` for an undeclared config, so `resample_beside` is `{}` and no
`resample` key reaches the record; task 1's pin test
(`test_the_undeclared_resample_shape_is_pinned_absent_key` and its `_explicit_null` sibling) needed no
amendment and passed unmodified. This is the reading that keeps a reader from being told anything about
an undeclared run's resolution, at the cost of not being able to distinguish "2000 was a default" from
"2000 was chosen" for such a run — the same trade the brief laid out as the second reading. Flagging this
explicitly per the brief's instruction, since it's a deliberate choice rather than the pin's greenness
being incidental: no amendment to task 1's pin was made or needed.

## Where the resolved values live

Chose per-metric (`beside_n`/`weighted_beside`, beside every `ci95`), not a run-level block. Reasons:
`summarize_step`'s own carrier rule (a key that sits beside `n` travels in `beside_n`) already covers
this shape, `weighted_by` is the direct precedent for "a key that names a declaration rather than
reporting a figure," and — the deciding argument — the run-level alternative can't distinguish a metric
core actually resampled with the declared method from one it didn't reach at all (a `basis: repeats`
metric, or one dropped by `E-DATA-CLUSTER-DERIVED`). A per-metric echo makes that distinction free: the
key is present exactly where a resample ran under the declaration, and absent everywhere else, so its
presence can never be misread as implying a value varied across metrics when it didn't — it's the same
constant three values repeated, once per metric that used them.

## Concerns

None outstanding. No brief/code disagreement found for this task (checked the exact locals named in the
brief — `resample_spec`, `cond_beside_n`, `weighted_beside` — against current `cli.py`; the only
wrinkle is that `resample_spec` is resolved later in the function than `weighted_beside`'s initial
declaration, so the merge into `weighted_beside` has to happen via `.update()` after `resample_spec`
exists rather than at its original declaration site — a placement detail, not a semantic disagreement,
and covered by the passing tests and both mutations).
