# Task 6 report

**Status:** complete.

**What changed.** `src/publishable/hypotheses.py`'s `corrected_unavailable` `elif` branch (line
414) needed no logic change: Task 5's `cli.py` member-building already made `key not in by_key`
true only for the two genuinely-nothing-to-correct cases, since the branch is reached only when the
`if corrected is not None` arm above it did not fire. Rewrote the branch's comment, which still
described the pre-Task-5 world ("core builds one for every `vs_baseline`/contrast comparison but
none for a constant reference"), to name the two residual cases: a metric with no raw interval at
all, and a recorded column carried under both `weight_by` and `cluster_by` (no paired construction
of that shape, no `Member` field for both modifiers, `Member.__post_init__` refuses one that
carries both).

**Documents corrected.**
- `docs/superpowers/spec-defects.md`: amended (not removed) the `{to: constant}` entry — title and
  body narrowed to the weighted+clustered residual, with an "AMENDED" section explaining the three
  closed rows and why the fourth stays open. The brief's "stays open for the `t` case" was stale per
  the controller's ruling; corrected as instructed.
- `docs/superpowers/specs/2026-08-28-correctable-condition-metric-design.md`: appended an
  amendment to Decision 5 naming the Holm-rank-shift exception ("nothing else may move" now has one
  named exception) and why it's kept — the family already counted the constant hypothesis, Task 5
  only gave it a rank to sort into.
- `docs/reference.md` § Pre-registration / § What a hypothesis is tested against: fixed four stale
  passages (and one example comment) claiming core builds no `Member` for a constant-referenced
  hypothesis at all; each now names the weighted+clustered combination as the sole exception.
- `docs/feasibility-growth-chart-literacy.md`: corrected finding #2 (E2 declares neither `weight_by`
  nor `cluster_by`, so its `{to: constant}` claim on `auroc` is no longer limited) and finding #7
  for internal consistency, both without touching § Executability.

**Mutation evidence** (both run against production code, reverted, diffed clean after):
1. Forced the `elif` to never fire (`... and False`) → `test_a_condition_metric_with_no_raw_interval_still_gets_no_member` and `test_a_weighted_clustered_condition_metric_gets_no_member` FAILED (2 failed, 3 passed); the three "now correctable" tests stayed green.
2. Disabled `cli.py`'s `condition_members.append(...)` (`if False:` guard, simulating pre-Task-5) → `test_an_unresampled_condition_metric_corrects_off_its_own_per_unit_values`, `test_a_resampled_condition_metric_corrects_off_its_own_draw_pool`, `test_a_derived_condition_metric_corrects_off_its_own_draw_pool` FAILED (3 failed, 2 passed); the two residual tests stayed green.

Both reverts verified byte-identical via `diff` against a pre-mutation backup, then full 5/5 green.

**Verification:** the 5 relevant end-to-end tests pass; `test_task1_bit_stability_oracle_over_the_correction_machinery` passes with its golden literal untouched; `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all clean.

**Concerns:** none — no behavior changed beyond the comment; no run declaring no constant hypothesis is affected.

## Fix round 1

**Finding 1 (spec compliance failure, `docs/reference.md`).** Swept the whole file for the "sole
exception" framing rather than trusting the three locations named. Found **four** homes carrying the
false claim, not three: the § Pre-registration passage at the `family implies` sentence (already
correctly scoped — "wherever the metric's own raw interval exists" — left as-is), the `supported`
`null` passage naming "three unrelated reasons" (now four, with the no-raw-interval case named
explicitly), and both § What a hypothesis is tested against passages ("except for a recorded
column…", "The standing exception is…"). All three rewritten to name both cases: no raw interval at
all, and weighted+clustered. Also fixed `docs/feasibility-growth-chart-literacy.md` finding #7's
matching "one standing exception" framing and its undated "as of a later slice" clause (ride-along),
and added the `metric_key == "by"` skip as a third named path in `hypotheses.py`'s comment
(ride-along).

**Finding 2 (mutation didn't test the claim).** Added
`tests/test_hypotheses.py::test_the_by_key_conjunct_is_what_keeps_a_family_dropped_member_off_the_honest_gap`,
a direct unit test of `evaluate()` with a `Member` present in `by_key` (`ci95=None`, `p_value=None`,
the pre-existing "dropped by `_family`" case the coordinator ruled out of scope) beside a `hyp` that
is counted. This is exactly the input shape where `key not in by_key` is `False` and therefore the
only conjunct that can make the `elif` not fire — `corrected` is already `None` from the `if` branch
above regardless of this conjunct, since the dropped member is absent from `corrected_for`'s output
too.

Mutation: deleted `and key not in by_key` from the `elif` (kept `_is_counted(...) and method !=
"none"`). Before: `1 passed, 50 deselected`. After: `FAILED
tests/test_hypotheses.py::test_the_by_key_conjunct_is_what_keeps_a_family_dropped_member_off_the_honest_gap`
— `AssertionError: assert 'ci95_corrected' not in {'value': 0.62, 'ci95': [0.55, 0.69],
'ci95_corrected': None}` (`1 failed, 50 deselected`). Restored via `cp` from a pre-mutation backup,
`diff` byte-identical, re-ran green: `51 passed` (full `test_hypotheses.py`).

**Verification re-run:** targeted tests (18 passed), the 5 end-to-end tests (5 passed), Task 1 oracle
(1 passed, golden untouched), `ruff check` clean, `ruff format --check` clean (101 files), `mypy`
clean (56 files). Mechanical pass re-run on all four touched `*.md` files: no trailing whitespace, no
tabs, no new broken anchors (pre-existing slugger false-positives in `reference.md` for `.json`
headings are unrelated to this edit).
