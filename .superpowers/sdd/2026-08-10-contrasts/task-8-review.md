# Task 8 review — the acceptance test

**Reviewer:** the controller, directly. The 200-subagent session limit was reached before this
review could be dispatched. **This is self-review and is weaker than the independent pass every
other task in this slice received** — I wrote the briefs that produced most of this slice's
defects, so I am the worst-placed reader for them. Treat these findings as a floor, not a
ceiling, and let the whole-branch review re-cover this task.

**Spec compliance:** ✅
**Task quality:** findings — 2 Important, both inherited from the brief rather than introduced
by the implementer.

## What checks out

- The diff touches **only** `tests/test_cli.py`, +61 lines. Zero `src/` changes, so the claim
  that every earlier task's piece was already reachable from `main(["run", ...])` holds.
- Both tests drive `run_a_project`, which calls the real CLI entry point, rather than reaching
  into internals.
- `_METHOD_VARYING_STEP` is used, so the metric genuinely differs across conditions — a fixture
  recording identical values would let `delta` and `cohens_d` pass at `0.0`/`None` regardless of
  correctness.
- The hand run in the report is real evidence: per-condition widths ≈12.577 and ≈12.574 against
  a paired delta width of ≈0.181.

## Important 1 — `assert width < per_condition` is far weaker than the measured reality

`tests/test_cli.py`, `test_a_paired_delta_is_narrower_than_the_conditions_it_compares`.

The hand run measured 0.181 against 12.577 — roughly 70×. The assertion passes at 12.5 against
12.577. So an implementation that lost almost all of the pairing benefit would still be green,
and the hand run is doing work the suite is not.

Task 5's unit test already uses a ratio (`< independent_width / 4`) for exactly this reason. The
acceptance test should too. This assertion came from the plan's Task 8 text, not from the
implementer.

## Important 2 — `assert hi > lo` does not test what its docstring claims

Same file, `test_the_delta_half_width_is_not_implausibly_narrow`.

The docstring cites `CLAUDE.md`'s ≈0.033 floor for a linear-versus-rank contrast, but the
assertion only rejects a zero-width interval. Those are not the same claim, and the gap between
them is most of the test's stated purpose.

It also cannot simply be tightened to "non-degenerate": Task 5 established that a zero-width
interval is **legitimate** for a point-mass bootstrap, where a difference genuinely has no
sampling variability. So strengthening this needs a fixture whose difference does vary, and an
assertion keyed to that fixture — not a bare floor constant lifted from a different *n*.

Also from the plan's text.

## Minor

- Both tests repeat the same `monkeypatch` + `run_a_project` setup verbatim; a fixture would
  carry it.
- Neither asserts `correction is None` nor the absence of `ci95_corrected`. That is covered by
  Task 7's tests, so it is not a gap in the slice — only in this task's independence.

## Cross-task note

Task 7's review (independent, and it did run) found that **no test produces a derived contrast
through `main(["run", ...])`, and none declares a `statistics.contrasts` entry end to end**.
That is properly an acceptance-test gap, and this task is where it should have been closed. The
consequence is stated in that review: both of this slice's Criticals can be reverted invisibly,
because the unit tests guard `stats.py` rather than the call site in `cli.py`.

Fixing Important 1 and 2 without also closing that gap would leave the slice's two worst defects
unguarded at the integration level.
