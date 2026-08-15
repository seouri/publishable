# H4a `statistics.resample` honoured — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A config that declares `statistics.resample` gets the method, draw count and strata it asked for — on column metrics, on column contrasts, on clusters and on reporting strata — while a config that declares nothing produces byte-identical output to today, retiring `E-STATS-RESAMPLE-UNSUPPORTED`.

**Architecture:** `validate` gains `_check_resample`, which closes the block's key set in `envelope.py` and refuses a bad `method`, an `n` below the 80-draw honesty floor, a `stratify_by` naming an undeclared attribute, and a `resample` with no roster — all of it landing *before* any code honours the declaration. `stats.percentile_over_units` and `percentile_over_units_clustered` gain a `strata` argument (draw within a stratum; a cluster is the draw and its stratum must be constant within it), and `summarize_step` gains `resample_columns` and `strata` so a recorded column takes a percentile interval instead of `t_over_units`. `cli.command_run` resolves the block once, replacing the hard-coded `derived_metric_draws = 2000`, and threads it through all seven read sites plus `_comparison_step_blocks`, where a column contrast under `resample` takes `paired_percentile_of_derived` over `col_keys` and carries a **pool** rather than **diffs** into the correction family.

**Spec:** docs/superpowers/specs/2026-08-15-resample-honoured-design.md

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced because an implementer sees only its own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`. Types `uv run mypy`. All four must pass before a commit.

**Exact values used across this slice.**

- The honesty floor: `stats.min_honest_draws(confidence) = math.ceil(2.0 / ((1.0 - confidence) / 2.0))`. At 0.95 it is **80**. At 0.975 it is **160**. At 0.99 it is **400**. At 0.9975 it is **1601** (a genuine float artifact — `1.0 - 0.9975` lands just above `0.0025`; do not "fix" it to 1600).
- `correction.ALPHA = 0.05`. Holm's level at rank 1 of a family of `m` is `0.05 / m`. Bonferroni's is `0.05 / m` for every member.
- The default draw count is **2000** and the default method is **`bootstrap`**, both documented at `reference.md` § Statistical reporting.
- `cli.command_run` reads `correction_method = (doc.get("statistics") or {}).get("correction") or "holm"` — an unset correction is **holm**, not none.
- The `resample.method` enum is closed at exactly one value: `("bootstrap",)`.
- New identifiers minted by this slice: `E-STATS-RESAMPLE-METHOD`, `E-STATS-RESAMPLE-N`, `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`, `E-STATS-RESAMPLE-STRATIFY-VARIES`, `E-STATS-RESAMPLE-UNITS`, `W-STATS-RESAMPLE-FAMILY`, `W-STATS-RESAMPLE-CLUSTERS`.
- Retired by this slice: `E-STATS-RESAMPLE-UNSUPPORTED`. `E-STATS-NULLTEST-UNSUPPORTED` stays.

**Boundaries this slice does not cross.**

- `_comparison_step_blocks`'s `"paired": True` (cli.py:808 and :830) **stays hard-coded**. Its docstring says it expires with `E-DATA-ALLOCATION-CONTRAST`, which is H4c, not H4a.
- `cohens_d` stays `null` for every derived metric and for every derived contrast. `r` is computed by `aggregate`, so there is no per-unit value to difference. Do not reintroduce one.
- Nothing `p_value`-shaped. `grep -rn p_value src/` returns zero matches today and must still return zero after this slice.
- A `summary`-step `Estimate` is `reported: true`, sits outside the correction family, and is **never recomputed**. It reaches `run.yaml` through `run_record.summary_values`, never through `summarize_step`.
- `E-DATA-CLUSTER-DERIVED` (stats.py:1429) stays: under `cluster_by`, derived metrics are still dropped while recorded columns take clustered intervals.

**Mutation discipline, every task.** Apply the named mutation to the file it names. Run the named test. Confirm it **FAILS**. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert **by editing the file back in place** — never `git checkout -- <file>`, which destroys uncommitted work and has been mistaken for a revert twice in this repo. Confirm the test **PASSES** again. Verify the revert by behaviour (the test passes), never by `git status`.

**Test-design rules this repo enforces.** Sixteen checks across two earlier slices could not fail. Before believing any test here:

- A control that asserts only an absence passes identically if nothing ran. Every such assertion needs a positive companion **in the same test**.
- Size a statistical fixture so each candidate wrong answer produces a **different** observable. Two equal strata distinguish nothing; three unequal strata with disjoint value bands distinguish unstratified draws, correct stratified draws, and equal-weighting-of-stratum-means.
- Never filter the output of a grep whose job is to find a string — filter the file list.

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen, never an en dash, in anything that becomes an anchor. Cite by section (`reference.md` § "Statistical reporting"), never by line number. After any `*.md` edit run the mechanical pass: every relative link and `#anchor` resolves, no two headings in a file share an anchor, every table row matches its header's column count, no trailing whitespace or tabs, skipping fenced code blocks. Any inline `# a | b | c` enum comment must list every value its table defines.

---

## Task 1: The regression pin — the undeclared-`resample` shape, `null` and absent separately

**Files:** Modify (append) `tests/test_cli.py`. No `src/` change.

**Interfaces:**
- Consumes: `run_a_project(tmp_path, *, capsys=None, aggregate_returns=None, units=10, sweep=..., statistics=..., **overrides)` from `tests/test_cli.py`; `_named_contrast(run, label, metric)` at `tests/test_cli.py:3122`; `_first_metric(run, name)` at `tests/test_cli.py:2218`.
- Produces: `test_the_undeclared_resample_shape_is_pinned_absent_key` and `test_the_undeclared_resample_shape_is_pinned_explicit_null` — the only baseline any later task can be compared against.

**Why first.** Once `percentile_over_units` is wired into `summarize_step` there is nothing left to compare against. The live hazard is Task 13, where the literal `derived_metric_draws = 2000` becomes a resolved value: that is where an undeclared config silently acquires a different draw count. `materialize.py` writes **neither** `resample` key, so the absent-key case and the explicit-`null` case must be pinned separately — `_check_unimplemented`'s `if statistics.get(field)` is false for both, but they are different documents.

**Trap this task must avoid.** `run_a_project` merges overrides with `doc.update(overrides)` — a **top-level replace**. Passing `statistics={"resample": None}` would delete the `correction: holm` `materialize.py` writes, moving `correction_level` and `family_size` and pinning a baseline the test itself changed. The explicit-`null` test therefore passes `statistics={"correction": "holm", "resample": None}`, and **both** tests assert `correction_level` and `family_size` so a future accidental replacement is caught.

**The second trap, and it is the one that would have made this pin worthless.** `tests/test_cli.py`'s existing `_AGGREGATE_STEP` records `pred = float(i)` with **no reference to `cfg`**, so the column is byte-identical under every condition — the derived-contrast test at `tests/test_cli.py:3138` says so in its own docstring, and works only because `aggregate` is monkeypatched to vary by `cfg`. A recorded column has no such patch. So under a baseline sweep the per-unit differences are **all zero**, and verified against the build: `paired_t_over_units([0.0] * 40)` returns `Interval(0.0, 0.0)` and **`cohens_dz([0.0] * 40)` returns `None`**. A pin asserting `cohens_d is not None` would fail, and every later width comparison would be `0 > 0`. This task therefore introduces `_CONDITION_SCALED_STEP`, a step whose recorded column varies with the swept axis, and Task 16 reuses it.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
_CONDITION_SCALED_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # The recorded column VARIES with the swept axis. `_AGGREGATE_STEP`
        # records `float(i)` regardless of `cfg`, which makes every per-unit
        # difference zero: `paired_t_over_units` then returns a zero-width
        # interval and `cohens_dz` returns `None`, so a contrast pin over it
        # asserts nothing and every width comparison is `0 > 0`. Scaled by
        # `analysis.method` so both the differences and the draw pool have real
        # dispersion under every comparison this file builds.
        scale = {{"pearson": 1.0, "spearman": 2.0, "kendall": 3.0}}[
            cfg.parameters.analysis.method
        ]
        units = list(io.units)
        for i, unit in enumerate(units):
            io.record(unit.key, {{"pred": float(i) * scale}})
        return {{"n_units": len(units)}}
'''


def _assert_undeclared_resample_shape(run: dict[str, Any]) -> None:
    """The full shape an undeclared `statistics.resample` produces, which H4a
    must not move. Shared by the absent-key and the explicit-`null` pins because
    the two configs are different documents that must produce one shape:
    `materialize.py` writes neither key, and `_check_unimplemented`'s
    `if statistics.get(field)` is false for both — so a resolution step that read
    `.get("resample", DEFAULT)` instead of `.get("resample") or DEFAULT` would
    separate them, and nothing else in the suite would notice."""
    assert run["status"] == "completed"
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    # A recorded column: the t-interval, and NO `resample_draws` key at all.
    column = aggregated["pred"]
    assert column["basis"] == "units"
    assert column["method"] == "t_over_units"
    assert column["ci95"] is not None
    assert "resample_draws" not in column
    # A derived metric: resampled whether or not `resample` is declared, at the
    # documented default of 2000 draws, and never carrying an effect size.
    derived = aggregated["mean_pred"]
    assert derived["basis"] == "units"
    assert derived["method"] == "percentile_over_units"
    assert derived["resample_draws"] == 2000
    assert derived["cohens_d"] is None
    assert derived["ci95"] is not None
    # A column contrast: Student's t on the per-unit differences, with Cohen's dz.
    col_contrast = _named_contrast(run, "method=spearman", "pred")
    assert col_contrast is not None
    assert col_contrast["method"] == "paired_t_over_units"
    assert col_contrast["cohens_d"] is not None
    assert "resample_draws" not in col_contrast
    # A derived contrast: the joint percentile, and no effect size.
    derived_contrast = _named_contrast(run, "method=spearman", "mean_pred")
    assert derived_contrast is not None
    assert derived_contrast["method"] == "paired_percentile_over_units"
    assert derived_contrast["cohens_d"] is None
    # The correction family, which a replaced `statistics` block would move:
    # two metrics over one comparison is a family of 2, and holm's rank-1 level
    # is ALPHA/2. Asserted on both pins so an override that dropped
    # `correction: holm` cannot pass.
    assert col_contrast["family"] == {"comparisons": 1, "metrics": 2}
    assert col_contrast["family_size"] == 2
    assert col_contrast["correction"] == "holm"
    assert col_contrast["correction_level"] in (
        pytest.approx(0.05 / 2), pytest.approx(0.05 / 1)
    )
    # Holm ranks on the point estimate over HALF THE RAW ci95 WIDTH, never on a
    # p-value — the family often carries none. Both members' levels come from
    # that ranking, so the two distinct levels must both be present exactly once.
    levels = sorted(
        m["correction_level"]
        for m in (col_contrast, derived_contrast)
    )
    assert levels == [pytest.approx(0.025), pytest.approx(0.05)]


_PIN_SWEEP = {
    "baseline": {"analysis.method": "pearson"},
    "grid": {"analysis.method": ["spearman"]},
}


def _pinned_run(tmp_path, capsys, monkeypatch, **overrides):
    """One run carrying both a recorded column and a derived metric under one
    baseline comparison. `_starter_step` rather than `aggregate_returns`,
    because that shorthand's step records `float(i)` regardless of `cfg` and a
    contrast over it is degenerate."""
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(
        GenericTemplate,
        "aggregate",
        lambda self, units, cfg: {"mean_pred": sum(units.pred) / len(units)},
    )
    return run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep=_PIN_SWEEP,
        _starter_step=_CONDITION_SCALED_STEP,
        **overrides,
    )


def test_the_undeclared_resample_shape_is_pinned_absent_key(tmp_path, capsys, monkeypatch):
    """`materialize.py` writes no `resample` key at all, so this is the shape a
    generated config actually produces. Pinned before H4a wires
    `percentile_over_units` into `summarize_step`, because after that there is
    nothing left to compare against."""
    doc = _pinned_run(tmp_path, capsys, monkeypatch)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert "resample" not in (run["config"].get("statistics") or {})
    _assert_undeclared_resample_shape(run)


def test_the_undeclared_resample_shape_is_pinned_explicit_null(tmp_path, capsys, monkeypatch):
    """`resample: null` is a DIFFERENT document from the absent key and must
    produce the identical shape. `correction: holm` is restated here because
    `run_a_project` merges overrides with `doc.update`, a top-level replace: a
    bare `statistics={"resample": None}` would delete the correction
    `materialize.py` writes and move every `correction_level` below."""
    doc = _pinned_run(
        tmp_path, capsys, monkeypatch,
        statistics={"correction": "holm", "resample": None},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["config"]["statistics"]["resample"] is None
    _assert_undeclared_resample_shape(run)
```

`run_a_project` has no `_starter_step` parameter today. **Add one in this task**, and Tasks 15 and 16 reuse it: a keyword that `monkeypatch`es `publishable.generators.experiment.STARTER_STEP` inside the existing `pytest.MonkeyPatch.context()` block, exactly the way `aggregate_returns` already does, and document it in `run_a_project`'s docstring beside `extra_step_source`. Duplicating the scaffold-and-commit dance instead is what that helper exists to prevent.

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k undeclared_resample_shape -x`. Both tests fail first on the unknown `_starter_step` keyword; once that parameter is added, **this is a characterization pin, so both must PASS immediately.** If either then fails, the assertion is wrong, not the code — fix the assertion to what the run actually produces and record the difference in the commit message. Two verified facts to check the assertions against before changing anything: `paired_t_over_units([0.0] * 40)` returns `Interval(0.0, 0.0)` and `cohens_dz([0.0] * 40)` returns `None`, which is why `_CONDITION_SCALED_STEP` exists.

- [ ] **Step 3: Implement** — the `_starter_step` parameter on `run_a_project`, and nothing else. The pin itself is the deliverable. `_PIN_SWEEP` gives exactly one baseline comparison, `_CONDITION_SCALED_STEP` gives a column that differs between the two sides, and the monkeypatched `aggregate` gives the derived metric.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_cli.py -k undeclared_resample_shape`, then the whole suite: `uv run pytest`.

- [ ] **Step 5: Mutate** — in `src/publishable/cli.py`, change `derived_metric_draws = 2000` to `derived_metric_draws = 500`. Run `uv run pytest tests/test_cli.py -k undeclared_resample_shape`. Both tests must FAIL on `derived["resample_draws"] == 2000`. Delete `__pycache__`. Edit the line back to `2000` in place. Re-run; both pass. Then a second mutation, because the first only proves the draw count is pinned: in `src/publishable/stats.py`'s `summarize_step`, change the unweighted unclustered column branch `interval = t_over_units(values)` to `interval = percentile_over_units(values, 1, draws=2000)`. Both tests must FAIL on `column["method"] == "t_over_units"`. Revert in place the same way.

- [ ] **Step 6: Commit** — `test: pin the undeclared-resample shape, absent key and explicit null separately`.

---

## Task 2: Mint the `resample.method` table and fix the inline enum comment

**Files:** Modify `docs/reference.md`. No code, no test file.

**Interfaces:**
- Consumes: nothing.
- Produces: the normative statement that `resample.method`'s enum is exactly `bootstrap`, which Task 4's `E-STATS-RESAMPLE-METHOD` check enforces.

**The decision being written down (spec decision 1).** `bootstrap` is the **whole** enum — a closed, one-value enum. It is the only value the schema shows, the only construction that exists, and § Statistical reporting's existing construction table (`percentile_over_units`, `paired_percentile_over_units`, …) lists method strings core **emits**, not inputs a config may name. A one-value enum is a legitimate answer and an unstated one is not: closing it makes adding a second value a documented change rather than a silent one, and makes `method: bootstap` a diagnostic rather than a shrug.

- [ ] **Step 1: Write the failing test** — the test here is a mechanical grep, written as a throwaway and run in Step 2, not kept:

```bash
# Every value the new table defines must appear in the inline comment, and vice
# versa. Filter the FILE LIST, never the output of a sweep whose job is to find
# a string (a matching line can itself contain the excluded path).
cd /Users/joon/src/tries/publishable
grep -n 'resample:.*# ' docs/reference.md          # the inline comment, `# a | b | c` form
grep -n 'Resample methods' -A 6 docs/reference.md  # the new table
```

- [ ] **Step 2: Run it, confirm it fails** — today `grep -n 'Resample methods' docs/reference.md` returns nothing, and the inline comment at § The one config file reads `resample: null                         # NOT BUILT; {method: bootstrap, n: 2000, stratify_by: []}` — an *example expansion*, not an enum comment. Both greps failing is the confirmation.

- [ ] **Step 3: Implement** — two edits to `docs/reference.md`.

  (a) In § Statistical reporting, immediately after the paragraph beginning "**A derived metric is resampled whether or not you declare `statistics.resample`.**", add:

```markdown
**Resample methods.** `statistics.resample.method` names how the draws are taken, and the vocabulary is closed:

| `method` | What one draw is |
|---|---|
| `bootstrap` | Units drawn with replacement to the original count, or whole [clusters](#clustered-units) when `cluster_by` is declared, or within each [stratum](#weighted-samples) when `stratify_by` is — the statistic recomputed on each draw |

One value is the whole enum today. It is stated as an enum rather than left implicit so that adding a second is a documented change rather than a silent one, and so `method: bootstap` is refused (`E-STATS-RESAMPLE-METHOD`) rather than ignored. The method strings in the two construction tables above — `percentile_over_units`, `paired_percentile_over_units` and their `_clustered` forms — are what core **emits** into `run.yaml`, not values a config may name here.
```

  (b) In § The one config file, replace the `resample:` line with:

```yaml
  resample: null                         # bootstrap
                                         #   {method: bootstrap, n: 2000, stratify_by: []}
```

  Keep the two following comment lines (`# ... metrics resample either way`) exactly as they are, and delete `NOT BUILT;` from this line only — the rest of Task 12 handles the `NOT BUILT` prose in the § The one config file paragraph.

- [ ] **Step 4: Run, confirm it passes** — re-run both greps from Step 1; both now return their lines. Then the full mechanical pass: check that no heading added here duplicates an existing anchor (`grep -n '^#' docs/reference.md | sort` — the new block adds no heading, so this must be unchanged), that the new table's every row has 2 columns matching its header, that no added line has trailing whitespace (`grep -n ' $' docs/reference.md`), and that no `x` was used for multiplication in the added text. Then `uv run pytest` — the docs are read by `tests/test_materialize.py`, which pins the generated config's comment text, so confirm whether that test covers this line and update `materialize.py` if and only if it does (it writes no `resample` key, so it should not).

- [ ] **Step 5: Mutate** — change `bootstrap` to `boostrap` in the new table's first column only. Re-run `grep -n 'Resample methods' -A 6 docs/reference.md` and confirm the table row and the inline comment now disagree — this is the § Enum comments consistency class, caught by reading the two together, which is why both greps are in Step 1. Revert in place by editing the word back.

- [ ] **Step 6: Commit** — `docs: close resample.method at one value, and give it the enum comment CLAUDE.md requires`.

---

## Task 3: Close `statistics.resample` one level in

**Files:** Modify `src/publishable/envelope.py`. Test `tests/test_envelope.py`.

**Interfaces:**
- Consumes: `envelope.LEAF_TYPES`, `envelope._known_containers()`, `envelope._check_unknown_keys`.
- Produces: `statistics.resample.method` (`str`), `statistics.resample.n` (`int`), `statistics.resample.stratify_by` (`(str, list)`) as `LEAF_TYPES` entries — which Tasks 4 and 5 rely on for their `E-CONFIG-TYPE` backstop.

**The precedent is `data.units.measurements`, not `assign.<axis>`.** The spec and the scoping both say "`assign.<axis>` style … `LEAF_TYPES` plus a closed key set". A closed key set is **not needed here**, and building one would be a second authority over the same three names. `_known_containers()` derives every dotted prefix a `LEAF_TYPES` path implies, and `_check_unknown_keys` checks **containers before leaves** ("Containers before leaves: `data.units.measurements` is both — typed a mapping by the loop in `check_envelope`, and descended into here"). So adding the three child paths makes `statistics.resample` simultaneously a leaf (still typed `dict`) and a container (descended into), and `stratifyy_by` reports `E-CONFIG-KEY-UNKNOWN` with a difflib hint for free. `_check_assign_axis_keys` exists only because an `assign` **axis name** is user-chosen and no fixed dotted path reaches it; `resample`'s three keys are fixed.

**`stratify_by` is `(str, list)`** because `units.stratum_names` — the single authority `validate._check_assign` already imports — reads presence and shape structurally: a bare `stratify_by: site` names one stratum exactly as `[site]` does. Typing it `list` alone would make the bare form an `E-CONFIG-TYPE` while `stratum_names` accepts it, which is the two-readings-of-one-declaration shape that docstring exists to prevent.

- [ ] **Step 1: Write the failing test** — append to `tests/test_envelope.py`:

```python
def test_a_misspelled_resample_key_is_reported_rather_than_ignored():
    """`statistics.resample` is now both a leaf and a container, the same
    arrangement `data.units.measurements` has: typed a mapping by the loop in
    `check_envelope`, and descended into by `_check_unknown_keys`, which checks
    containers before leaves. Without the three child paths the closure stops at
    the leaf and `stratifyy_by` is reached by no check in this build."""
    findings = check_envelope(
        {"statistics": {"resample": {"method": "bootstrap", "n": 2000, "stratifyy_by": ["a"]}}}
    )
    by_code = [(code, path) for code, path, _ in findings]
    assert ("E-CONFIG-KEY-UNKNOWN", "statistics.resample.stratifyy_by") in by_code
    # The positive companion: the three real keys are NOT reported, so the test
    # cannot pass by the closure rejecting everything under the block.
    assert not any(
        path.startswith("statistics.resample.") and path.endswith(("method", "n", "stratify_by"))
        for _, path in by_code
    )


def test_the_three_resample_leaves_are_typed():
    """A wrong-typed child now has an `E-CONFIG-TYPE` backstop, which is what
    lets `_check_resample` read each value without its own isinstance ladder."""
    findings = check_envelope(
        {"statistics": {"resample": {"method": 3, "n": "many", "stratify_by": 7}}}
    )
    paths = {path for code, path, _ in findings if code == "E-CONFIG-TYPE"}
    assert paths == {
        "statistics.resample.method",
        "statistics.resample.n",
        "statistics.resample.stratify_by",
    }


def test_a_bare_string_stratify_by_is_accepted_by_the_envelope():
    """`units.stratum_names` reads a bare `stratify_by: site` as one name, the
    same as `[site]`. Typing this `list` alone would make the two readings
    disagree — `E-CONFIG-TYPE` here while the draw balances on it there."""
    findings = check_envelope({"statistics": {"resample": {"stratify_by": "site"}}})
    assert not [f for f in findings if f[1].startswith("statistics.resample")]
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_envelope.py -k resample -x`. Expect `test_a_misspelled_resample_key_is_reported_rather_than_ignored` to fail with an empty `by_code` for that path (the closure stops at the leaf), and `test_the_three_resample_leaves_are_typed` to fail with `paths == set()`.

- [ ] **Step 3: Implement** — in `src/publishable/envelope.py`, in `LEAF_TYPES`, immediately after `"statistics.resample": dict,`:

```python
    "statistics.resample": dict,
    # Closed one level in, the arrangement `data.units.measurements` above has
    # and for its reason: these three names are fixed, the block is no longer
    # refused wholesale, and leaving it whole would make a `stratifyy_by` typo
    # unreachable by any check the moment the wholesale refusal retired — a
    # latent gap turning live. `assign`'s separate `_check_assign_axis_keys` is
    # not the precedent: it exists because an axis NAME is user-chosen and no
    # fixed dotted path reaches it. `stratify_by` is `(str, list)` because
    # `units.stratum_names` — the single authority the draw balances on — reads
    # a bare `stratify_by: site` as one name exactly as `[site]` is; typing it
    # `list` alone would make the envelope and the draw disagree about the same
    # declaration.
    "statistics.resample.method": str,
    "statistics.resample.n": int,
    "statistics.resample.stratify_by": (str, list),
```

  Then update the module docstring's list of blocks "declared at their own key with the one outer type that section gives them" — it currently names `statistics.contrasts` / `.resample` / `.null_test` / `.report_by`; remove `.resample` from that list and add a sentence saying it is now closed one level in like `measurements`.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_envelope.py`, then `uv run pytest`, then `uv run mypy` and `uv run ruff check .`.

- [ ] **Step 5: Mutate** — in `envelope.py`, delete the line `"statistics.resample.stratify_by": (str, list),`. Run `uv run pytest tests/test_envelope.py -k resample`. `test_the_three_resample_leaves_are_typed` must FAIL (the path set shrinks to two) and `test_a_misspelled_resample_key_is_reported_rather_than_ignored` must still pass — proving the closure survives on the other two children, which is the fact that makes this a three-line change rather than a new function. Delete `__pycache__`, edit the line back in place, re-run.

- [ ] **Step 6: Commit** — `feat: close statistics.resample one level in, the way measurements already is`.

---

## Task 4: `_check_resample` — the `method` enum, and the `n >= 80` floor

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `envelope.LEAF_TYPES`'s three `statistics.resample.*` entries (Task 3); `stats.min_honest_draws`; `diagnostics.Collector` (`.error(code, path, message)` / `.warn(...)`).
- Produces: `validate._check_resample(doc, roster, c)` — the one function Tasks 5, 6, 7 and 8 extend. Its call site in `validate_config` is fixed here.

**Where it sits, and why (spec decision 5).** `validate_config`'s sequence today is `… _check_fold_stratify_by → _check_replication → _check_unimplemented → _check_sweep → _check_contrasts → _check_hypotheses → _check_report_by`. `_check_resample` goes **immediately after `_check_sweep`**, before `_check_contrasts`. It needs the resolved roster (Task 5's declared-attribute test and Task 8's cluster count) and, for Task 6, the resolved comparison family that `_check_sweep` also computes. This is the one ordering question H4a inherits from H7a's `validate_config` reshuffle.

**The floor is mandatory, and it must land before anything honours `n`.** `stats.t_over_units` returns `None` below 2 units. `stats.percentile_over_units` returns `None` below 2 units **and** below `min_honest_draws(confidence)` draws. So once Task 14 wires the column branch, a `resample: {n: 50}` nulls `ci95` on **every column in the run**, silently. `min_honest_draws(0.95)` is exactly **80**.

**Signature.** `def _check_resample(doc: dict[str, Any], roster: "UnitList | None", c: Collector) -> None`. `roster` is the same value `_check_units` returned and `_check_report_by` already takes.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
_RESAMPLE_UNITS = {"from": "index.csv", "key": "patient_id", "attributes": ["cohort"]}


def test_an_unknown_resample_method_is_refused(write_config):
    """`bootstrap` is the whole enum. An unstated one-value enum makes
    `method: bootstap` a shrug; a stated one makes it a diagnostic."""
    found = codes(
        write_config(
            {
                "data.units": _RESAMPLE_UNITS,
                "statistics": {"resample": {"method": "bootstap", "n": 2000}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-METHOD" in found
    # The positive companion, in the same test: the legal spelling is NOT
    # refused, so this cannot pass by the check rejecting every method string.
    assert "E-STATS-RESAMPLE-METHOD" not in codes(
        write_config(
            {
                "data.units": _RESAMPLE_UNITS,
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        )
    )


@pytest.mark.parametrize("n", [0, -1, 79])
def test_a_resample_n_below_the_honest_floor_is_refused(write_config, n):
    """`percentile_over_units` returns `None` below `min_honest_draws(0.95)` = 80
    draws, so a declared `n: 50` would null `ci95` on EVERY column in the run
    with no diagnostic. The floor is what makes that impossible, and it lands
    before any code honours `n` — validate-before-honour, inside the slice.

    Three values, not one: `0` and `-1` are the not-a-positive-count fault and
    `79` is the floor itself, and a check written as `n < 1` passes the first two
    while letting the third through. `79`/`80` is the boundary pair, so an
    off-by-one (`n <= 80`) fails the companion below rather than passing."""
    found = codes(
        write_config(
            {
                "data.units": _RESAMPLE_UNITS,
                "statistics": {"resample": {"method": "bootstrap", "n": n}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-N" in found


def test_a_resample_n_at_the_floor_is_accepted(write_config):
    """The positive companion `79` above needs: exactly 80 is honest, so an
    off-by-one in either direction fails one of the two."""
    found = codes(
        write_config(
            {
                "data.units": _RESAMPLE_UNITS,
                "statistics": {"resample": {"method": "bootstrap", "n": 80}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-N" not in found


def test_the_resample_floor_message_names_the_number_and_the_consequence(write_config):
    messages = messages_by_code(
        write_config(
            {
                "data.units": _RESAMPLE_UNITS,
                "statistics": {"resample": {"method": "bootstrap", "n": 50}},
            }
        )
    )
    message = messages["E-STATS-RESAMPLE-N"]
    assert "80" in message
    assert "no interval" in message
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k resample_method or resample_n -x`. Expect `KeyError`/`assert ... in found` failures: neither code exists.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`.

  (a) Add to the imports from `publishable.stats`: `min_honest_draws`.

  (b) Add the call, immediately after `_check_sweep(doc, template, c, fold_basis=basis)`:

```python
    _check_sweep(doc, template, c, fold_basis=basis)
    # After `_check_sweep`, not before it, and this is the one ordering question
    # H4a inherits from H7a's prologue reshuffle: the strata check needs the
    # resolved roster and the declared attributes, and the `n` bound needs the
    # resolved comparison family, which `_check_sweep` is the first thing to
    # compute. Before `_check_contrasts`, which reports the shape faults in a
    # `statistics.contrasts` block this one only counts.
    _check_resample(doc, roster, c)
    _check_contrasts(doc, c, roster)
```

  (c) Add the function. Put it immediately before `_check_report_by`, which it most resembles:

```python
RESAMPLE_METHODS = ("bootstrap",)
"""Every value `statistics.resample.method` may take — `reference.md`
§ Statistical reporting's *Resample methods* table, which is the enum this
tuple enforces.

**A closed, one-value enum on purpose.** `bootstrap` is the only value the
schema shows and the only construction `stats.py` has, and § Statistical
reporting's construction tables enumerate the method strings core *emits*
(`percentile_over_units`, `paired_percentile_over_units`) — outputs, not inputs
a config may name. Stating the enum is what makes `method: bootstap` a
diagnostic rather than a shrug, and what makes adding a second value a
documented change rather than a silent one."""


def _check_resample(doc: dict[str, Any], roster: "UnitList | None", c: Collector) -> None:
    """`statistics.resample`, once it is honored rather than refused.

    Every check here presupposes the declaration is a mapping; a scalar or a
    list is `check_envelope`'s `E-CONFIG-TYPE` (`statistics.resample` is typed
    `dict`), and a wrong-typed child is the same, because Task 3 closed the
    block one level in. So this reads values rather than re-testing types, the
    same division `_check_report_by` keeps with the envelope.

    **The `n` floor is the load-bearing one.** `stats.percentile_over_units`
    returns `None` below `min_honest_draws(confidence)` draws — 80 at 95 % — so
    a declared `n: 50` would null `ci95` on every recorded column in the run,
    silently and with nothing in the record saying why. Refusing it here is why
    `validate` learns about `n` in the same slice that teaches `summarize_step`
    to honor it, rather than a slice later.
    """
    statistics = doc.get("statistics") or {}
    resample = statistics.get("resample")
    if not isinstance(resample, dict) or not resample:
        return
    method = resample.get("method")
    # `None`/absent means the documented default, `bootstrap` — § Statistical
    # reporting: declaring `resample` "changes the method or the count rather
    # than switching the behaviour on". Only a value actually named is checked.
    if method is not None and (not isinstance(method, str) or method not in RESAMPLE_METHODS):
        shown = f"`{method}`" if isinstance(method, str) else type(method).__name__
        c.error(
            "E-STATS-RESAMPLE-METHOD",
            "statistics.resample.method",
            f"is {shown}, not one of {', '.join(f'`{m}`' for m in RESAMPLE_METHODS)}",
        )
    n = resample.get("n")
    floor = min_honest_draws()
    # `bool` excluded explicitly: `isinstance(True, int)` is `True` in Python,
    # and `resample: {n: true}` is already `E-CONFIG-TYPE` from the envelope —
    # a value flagged wrong-typed there must not also drive this check.
    if n is not None and isinstance(n, int) and not isinstance(n, bool) and n < floor:
        c.error(
            "E-STATS-RESAMPLE-N",
            "statistics.resample.n",
            f"is {n}; a percentile interval needs at least {floor} draws before both "
            "of its ranks are interior, so below that the lower endpoint IS the "
            "smallest draw while the upper keeps shrinking — low-biased and "
            f"systematically too narrow. Under {floor} core reports no interval at "
            "all, so this would null `ci95` on every metric in the run rather than "
            "narrowing one",
        )
```

  (d) Register both codes in `docs/reference.md` § Errors `validate` reports, beside `E-STATS-REPORTBY-UNKNOWN`:

```markdown
| `statistics.resample.method` names a value other than `bootstrap` — the whole enum, [§ Statistical reporting](#statistical-reporting)'s *Resample methods*. Unset (`null`) is accepted and takes the documented default | `E-STATS-RESAMPLE-METHOD` |
| `statistics.resample.n` is below 80, the fewest draws both percentile ranks are interior at. Refused rather than warned because under it core reports no interval at all, so a declared `n: 50` would null `ci95` on every metric in the run rather than narrowing one | `E-STATS-RESAMPLE-N` |
```

  And add the § Validation row, beside *Clusters enough to resample*:

```markdown
| Resample draws are honest | `statistics.resample: {n: 50}` — below 80 draws a percentile interval's lower endpoint is the sample minimum, so core reports none and every metric in the run loses its `ci95` |
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k resample`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`. Then the doc mechanical pass: table rows match column counts, no trailing whitespace, `#statistical-reporting` resolves.

- [ ] **Step 5: Mutate** — in `validate.py`, change `if n is not None and isinstance(n, int) and not isinstance(n, bool) and n < floor:` to `... and n < 1:`. Run `uv run pytest tests/test_validate.py -k resample_n`. `test_a_resample_n_below_the_honest_floor_is_refused[79]` must FAIL while `[0]` and `[-1]` still pass — which is exactly why three values are parametrized and not one. Delete `__pycache__`, edit `n < 1` back to `n < floor` in place, re-run. Then a second mutation: change `floor = min_honest_draws()` to `floor = 81`; `test_a_resample_n_at_the_floor_is_accepted` must FAIL. Revert in place.

- [ ] **Step 6: Commit** — `feat: E-STATS-RESAMPLE-METHOD and the 80-draw floor, before anything honours n`.

---

## Task 5: `resample.stratify_by` names declared attributes

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_resample(doc, roster, c)` (Task 4); `units.stratum_names(stratify_by) -> tuple[str, ...]` (`src/publishable/units.py:1117`), already imported by `validate._check_assign`.
- Produces: `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`, which mints the identifier § Validation's *Resample strata exist* row has never had.

**Reuse `_check_report_by`'s shape, not `units._stratum_groups`.** The reference set is `data.units.attributes` — the declared set, exactly as `_check_report_by` reads it — because a stratum is read per unit when the draw is taken, so it has to survive resolution as an attribute. `units._stratum_groups` is `assign`-specific: it also admits a `sweep.groups` axis name as a legal target and raises `E-DATA-ASSIGN-STRATIFY-UNKNOWN`, neither of which applies to a resample.

**Read the declaration through `units.stratum_names`.** A bare `stratify_by: site` names one stratum exactly as `[site]` does — the same normalization the draw (Task 9) will balance on. Two independent readings of one declaration is the validate-clean-then-disagree shape `stratum_names`' own docstring exists to prevent. **Resample takes several names**, and the stratum is their cross: `stratify_by: [dx_status, count_stratum]` is `reference.md` § Weighted samples' own example.

**One finding per offending name**, so a declaration naming two undeclared attributes earns two findings rather than one that names only the first — the rule `E-DATA-ASSIGN-STRATIFY-UNKNOWN` already follows.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
def test_a_resample_stratum_must_be_a_declared_attribute(write_config):
    """§ Validation's *Resample strata exist* row has never had an identifier.
    The reference set is `data.units.attributes`, the declared one — the same set
    `_check_report_by` reads, and for its reason: a stratum is read per unit when
    the draw is taken, so it has to survive resolution as an attribute."""
    found = codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv",
                    "key": "patient_id",
                    "attributes": ["cohort"],
                },
                "statistics": {
                    "resample": {"method": "bootstrap", "n": 2000,
                                 "stratify_by": ["count_stratum"]}
                },
            }
        )
    )
    assert "E-STATS-RESAMPLE-STRATIFY-UNKNOWN" in found
    # Positive companion, same test: a DECLARED name is not refused, so this
    # cannot pass by the check refusing every stratum it is handed.
    assert "E-STATS-RESAMPLE-STRATIFY-UNKNOWN" not in codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv",
                    "key": "patient_id",
                    "attributes": ["cohort"],
                },
                "statistics": {
                    "resample": {"method": "bootstrap", "n": 2000, "stratify_by": ["cohort"]}
                },
            }
        )
    )


def test_a_resample_declaration_earns_one_finding_per_offending_stratum(write_config):
    """Two undeclared names, two findings — not one naming only the first. The
    count is the assertion: a check that `break`s after the first offender passes
    a membership test and fails this."""
    c = Collector()
    validate_config(
        write_config(
            {
                "data.units": {
                    "from": "index.csv",
                    "key": "patient_id",
                    "attributes": ["cohort"],
                },
                "statistics": {
                    "resample": {
                        "method": "bootstrap",
                        "n": 2000,
                        "stratify_by": ["dx_status", "count_stratum", "cohort"],
                    }
                },
            }
        ),
        c,
    )
    offenders = [f for f in c.findings if f.code == "E-STATS-RESAMPLE-STRATIFY-UNKNOWN"]
    assert len(offenders) == 2
    named = " ".join(f.message for f in offenders)
    assert "dx_status" in named and "count_stratum" in named
    # `cohort` IS declared and must not be among them — three names, two
    # offenders, so a check that reported all three would also fail the count.
    assert "cohort" not in named


def test_a_bare_string_resample_stratum_is_read_as_one_name(write_config):
    """`units.stratum_names` reads `stratify_by: site` as one name exactly as
    `[site]` is — the same normalization the draw balances on. Read as a
    sequence of characters instead, this would report four findings (`s`, `i`,
    `t`, `e`) rather than one, which is what the count catches."""
    c = Collector()
    validate_config(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id",
                               "attributes": ["cohort"]},
                "statistics": {"resample": {"method": "bootstrap", "n": 2000,
                                            "stratify_by": "site"}},
            }
        ),
        c,
    )
    offenders = [f for f in c.findings if f.code == "E-STATS-RESAMPLE-STRATIFY-UNKNOWN"]
    assert len(offenders) == 1
    assert "site" in offenders[0].message


def test_an_empty_resample_stratify_by_is_not_refused(write_config):
    """`stratify_by: []` is what a full expansion shows and what most designs
    carry; it names no stratum and sends the draw down its unstratified path.
    `stratum_names` returns `()` for it, so there is nothing to refuse."""
    found = codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "statistics": {"resample": {"method": "bootstrap", "n": 2000,
                                            "stratify_by": []}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-STRATIFY-UNKNOWN" not in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k resample_stratum or resample_declaration_earns -x`. Expect all four to fail on the missing code (the first three) and the last to pass vacuously (note it: a test that passes before the feature exists is a control, and its value comes from the three beside it).

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`, add `stratum_names` to the existing `from publishable.units import (...)` block, and append inside `_check_resample`, after the `n` check:

```python
    # The declared set, `data.units.attributes` — the same reference
    # `_check_report_by` reads, and for its reason: `strata.levels_for` and the
    # draw both read the attribute per unit, so a typo and an attribute no unit
    # carries are indistinguishable downstream. NOT `units._stratum_groups`,
    # which is `assign`-specific: it admits a `sweep.groups` axis name as a
    # legal target and raises `E-DATA-ASSIGN-STRATIFY-UNKNOWN`, and a resample
    # draws from the roster rather than from an allocation, so neither applies.
    #
    # Read through `units.stratum_names`, the same normalization the draw
    # balances on: a bare `stratify_by: site` is one name to both. Two
    # independent readings of one declaration is the validate-clean-then-
    # disagree shape that function's own docstring exists to prevent.
    #
    # Filtered to strings the same way `_check_report_by` filters `attributes`:
    # a non-string item there is `_check_units`' own finding (`E-UNITS-ATTR-
    # MISSING`), and `set(...)` over the raw list would raise on an unhashable
    # one before that finding is ever reached.
    declared = {
        a
        for a in (((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
        if isinstance(a, str)
    }
    for name in stratum_names(resample.get("stratify_by")):
        # One finding per offending name, not one naming only the first: the
        # declaration is a list and each entry is separately fixable, the same
        # rule `E-DATA-ASSIGN-STRATIFY-UNKNOWN` follows. A non-string entry is
        # absorbed here rather than left silent — it names no attribute either,
        # and `stratify_by`'s LEAF type is the container's, not each item's.
        if not isinstance(name, str) or name not in declared:
            c.error(
                "E-STATS-RESAMPLE-STRATIFY-UNKNOWN",
                "statistics.resample.stratify_by",
                f"names `{name}`, which is not a unit attribute — a stratum is read "
                "per unit when the draw is taken, so it has to be one. "
                f"`data.units.attributes` declares {', '.join(sorted(declared)) or 'none'}",
            )
```

  (b) `docs/reference.md`: give the existing § Validation row *Resample strata exist* its identifier by adding a registry row in § Errors `validate` reports:

```markdown
| `statistics.resample.stratify_by` names a value `data.units.attributes` does not declare, or is not a name at all. `data.units.attributes`, not the source's columns, for the same reason `E-DATA-CLUSTER-UNKNOWN` reads that set: a stratum is read per unit when the draw is taken, so it has to survive resolution as an attribute. Read through the same normalization the draw balances on, so a bare `stratify_by: site` is one name to both. One finding per offending name. Unlike `assign.<axis>.stratify_by`, a [`sweep.groups`](#expansion-modes) axis name is **not** a legal target here — a resample draws from the roster, not from an allocation | `E-STATS-RESAMPLE-STRATIFY-UNKNOWN` |
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k resample`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`, then the doc mechanical pass.

- [ ] **Step 5: Mutate** — in `validate.py`, add `break` as the last statement of the `for name in stratum_names(...)` loop body's `if` branch. Run `uv run pytest tests/test_validate.py -k earns_one_finding_per_offending_stratum`. It must FAIL on `len(offenders) == 2` (getting 1) while `test_a_resample_stratum_must_be_a_declared_attribute` still passes — which is why the count assertion exists and a membership assertion alone would not have caught it. Delete `__pycache__`, remove the `break` in place, re-run. Then a second mutation: replace `stratum_names(resample.get("stratify_by"))` with `resample.get("stratify_by") or []`; `test_a_bare_string_resample_stratum_is_read_as_one_name` must FAIL with 4 offenders. Revert in place.

- [ ] **Step 6: Commit** — `feat: E-STATS-RESAMPLE-STRATIFY-UNKNOWN, the identifier the Resample strata exist row never had`.

---

## Task 6: The comparisons-only lower bound on `n`, and the filed residue

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`, `docs/superpowers/spec-defects.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_resample(doc, roster, c)` (Tasks 4–5); `sweep.expand(doc) -> list[Condition]`; `contrasts.resolve_contrasts(doc, conditions)`; `stats.min_honest_draws(confidence)`; `correction.ALPHA`.
- Produces: `W-STATS-RESAMPLE-FAMILY`.

**What cannot be built, and why the plan says so rather than deferring it.** The old scoping wanted `validate` to bound `n` against the family size, which `correction.family_shape` computes as `comparisons × metrics`. **`metrics` is unknowable at validate time by design.** It is `len({(m.step, m.metric) for m in members})`, and `cli` builds a `Member` per metric per comparison *after every execution has run*, from (a) recorded columns, which come from `io.record` calls inside user step code, and (b) `aggregate`'s returned keys, which come from user template code. Neither is declared anywhere in the config: `envelope.LEAF_TYPES` has no `metrics` path, `parameter_spec` declares parameters, and `hypotheses` names only the metrics a user chose to pre-register. Core "never inspects the body of user Python" (CLAUDE.md, greenfield only). So the full bound needs a capability core refuses to have.

**What can be built.** `comparisons` *is* resolvable — `contrasts.resolve_contrasts` already runs at validate time, and `E-DATA-WEIGHT-CONTRAST` already reads the resolved count. With `k` comparisons and at least one metric each, Holm's tightest level is `ALPHA / k` and the corrected interval needs `min_honest_draws(1 - ALPHA/k)` draws. A warning at that bound is **always true when it fires and silent when it might not be**. Exact values: `k=1 → 80`, `k=2 → 160`, `k=3 → 240`, `k=4 → 321`, `k=5 → 400`.

**Gate on the correction method.** `fdr_bh` implies no per-comparison level at all (`correction._level_for` returns `None`), and `none` corrects nothing; under either, `ci95_corrected` is null regardless of `n` and this warning would be a false positive. `cli` treats an unset `statistics.correction` as **holm**, so unset is in scope.

**Re-derive `conditions`, do not hoist.** `_check_sweep`, `_check_contrasts` and `_check_hypotheses` each call `expand(doc)` behind their own `try/except Exception: conditions = []` guard — three existing precedents. The `fold_basis` hoist in `validate_config` exists because `_check_replication` bounds `k` against a number and `_check_sweep` sizes a budget from the same number, and "a `k` checked against one number while the budget counts another is the drift a single derivation removes". Nothing here is bounded against `comparisons`; it only sets a warning threshold. Re-derivation with the same guard is the smaller change and matches three siblings.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
def _resample_family_config(write_config, *, n, correction, levels):
    return write_config(
        {
            "data.units": {"from": "index.csv", "key": "patient_id"},
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": levels},
            },
            "statistics": {"correction": correction,
                           "resample": {"method": "bootstrap", "n": n}},
        }
    )


def test_a_resample_n_too_small_for_the_comparison_family_warns(write_config):
    """Three comparisons put Holm's tightest level at ALPHA/3, whose interval
    needs `min_honest_draws(1 - 0.05/3)` = 240 draws. `n: 200` clears the 80-draw
    floor and still cannot support the corrected interval, which is the whole
    gap this warning covers.

    The metric count is deliberately NOT in the bound: `correction.family_shape`
    derives it from `Member`s built after the run out of `io.record` keys and
    `aggregate`'s return, neither of which the config declares, and core never
    inspects the body of user Python. So this is a LOWER bound — always true when
    it fires."""
    found = codes(
        _resample_family_config(
            write_config, n=200, correction="holm", levels=["spearman", "kendall", "theil"]
        )
    )
    assert "W-STATS-RESAMPLE-FAMILY" in found
    assert "E-STATS-RESAMPLE-N" not in found  # 200 is above the 80 floor


def test_the_family_bound_is_silent_when_n_clears_it(write_config):
    """The positive companion to the test above, and the one that makes the
    threshold real rather than a warning that always fires: the same three
    comparisons with `n: 240` — exactly `min_honest_draws(1 - 0.05/3)` — are
    silent. 239 and 240 is the boundary pair."""
    assert "W-STATS-RESAMPLE-FAMILY" in codes(
        _resample_family_config(
            write_config, n=239, correction="holm", levels=["spearman", "kendall", "theil"]
        )
    )
    assert "W-STATS-RESAMPLE-FAMILY" not in codes(
        _resample_family_config(
            write_config, n=240, correction="holm", levels=["spearman", "kendall", "theil"]
        )
    )


def test_the_family_bound_scales_with_the_comparison_count(write_config):
    """One comparison needs 80 draws and three need 240, so an `n: 100` that is
    fine under one is not under three. A bound that read a constant rather than
    the resolved family passes one of these and fails the other."""
    assert "W-STATS-RESAMPLE-FAMILY" not in codes(
        _resample_family_config(write_config, n=100, correction="holm", levels=["spearman"])
    )
    assert "W-STATS-RESAMPLE-FAMILY" in codes(
        _resample_family_config(
            write_config, n=100, correction="holm", levels=["spearman", "kendall", "theil"]
        )
    )


@pytest.mark.parametrize("correction", ["none", "fdr_bh"])
def test_the_family_bound_is_not_reported_where_no_level_exists(write_config, correction):
    """`fdr_bh` implies no per-comparison level (`correction._level_for` returns
    `None`) and `none` corrects nothing, so under either `ci95_corrected` is null
    whatever `n` is and this warning would be a false positive."""
    assert "W-STATS-RESAMPLE-FAMILY" not in codes(
        _resample_family_config(
            write_config, n=100, correction=correction,
            levels=["spearman", "kendall", "theil"],
        )
    )


def test_the_family_bound_applies_when_correction_is_unset(write_config):
    """`cli` reads `(statistics.correction) or "holm"`, so an unset correction is
    holm and its family is corrected. A check gated on the key being present
    would leave every generated-but-edited config unwarned."""
    path = write_config(
        {
            "data.units": {"from": "index.csv", "key": "patient_id"},
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman", "kendall", "theil"]},
            },
            "statistics": {"resample": {"method": "bootstrap", "n": 100}},
        }
    )
    assert "W-STATS-RESAMPLE-FAMILY" in codes(path)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k family_bound or too_small_for_the_comparison -x`. Expect the four positive assertions to fail on the missing code; the two negative-assertion tests pass vacuously and are controls whose value comes from their positive siblings.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`, append to `_check_resample` (after the `stratify_by` loop), and add `from publishable.correction import ALPHA` to the imports:

```python
    # The comparisons-only lower bound. Holm's tightest level is `ALPHA / m` at
    # rank 1, and a corrected interval is read off the SAME pool the raw one was
    # (`correction.interval_at`), so a pool below `min_honest_draws(1 - level)`
    # yields `ci95_corrected: null` with only `W-STATS-CORRECTED-THIN` at run
    # time to say why. `m` is `comparisons × metrics` and the metric count is
    # unknowable here BY DESIGN — `correction.family_shape` derives it from
    # `Member`s built after the run, out of `io.record` keys and `aggregate`'s
    # return, and core never inspects the body of user Python. So this bounds
    # against `comparisons` alone: always true when it fires, silent when it
    # might not be. The residue — a config with many metrics that still nulls
    # every corrected bound — is filed in `spec-defects.md` as a run-time
    # disclosure that already exists, not a check to build.
    #
    # `expand(doc)` re-derived behind the same guard `_check_sweep`,
    # `_check_contrasts` and `_check_hypotheses` each use, rather than hoisted
    # into `validate_config` the way `fold_basis` is: that hoist exists because
    # two checks BOUND declarations against one number and must not disagree,
    # where this only sets a warning threshold.
    correction_method = statistics.get("correction") or "holm"
    # `fdr_bh` implies no per-comparison level at all and `none` corrects
    # nothing, so under either `ci95_corrected` is null whatever `n` is and this
    # would be a false positive. Unset is `holm`, the same default `cli` applies.
    if correction_method not in ("holm", "bonferroni"):
        return
    if not isinstance(n, int) or isinstance(n, bool) or n < floor:
        return  # already refused above, or defaulted; nothing to bound
    try:
        conditions = expand(doc)
    except Exception:
        conditions = []
    try:
        comparisons = len(resolve_contrasts(doc, conditions))
    except (TypeError, KeyError, AttributeError, ValueError):
        comparisons = 0
    if comparisons < 1:
        return
    needed = min_honest_draws(1.0 - ALPHA / comparisons)
    if n < needed:
        plural = "" if comparisons == 1 else "s"
        c.warn(
            "W-STATS-RESAMPLE-FAMILY",
            "statistics.resample.n",
            f"is {n}, and this design resolves to {comparisons} comparison{plural}, so "
            f"`{correction_method}` puts the tightest corrected level at "
            f"{ALPHA / comparisons:.5f} — an interval at that level needs at least "
            f"{needed} draws, so `ci95_corrected` would be null rather than reported "
            "too narrow. This is a lower bound: the family is comparisons × metrics "
            "and the metric count is not knowable before the run, so the real "
            "requirement is at least this",
        )
```

  `expand` and `resolve_contrasts` are already imported at the top of `validate.py` (used by `_check_sweep`); confirm with `grep -n "^from publishable.sweep import\|^from publishable.contrasts import" src/publishable/validate.py` and add only what is missing.

  (b) `docs/reference.md` § Warnings core reports:

```markdown
| `statistics.resample.n` is below the draw count the resolved comparison family's tightest corrected level needs, under `holm` or `bonferroni` — a **lower** bound, since the family is comparisons × metrics and the metric count is not knowable before the run | `W-STATS-RESAMPLE-FAMILY` |
```

  And a § Validation row beside *Resample draws are honest*:

```markdown
| Resample draws fit the family | `statistics.resample: {n: 200}` over 3 comparisons under `holm` — the tightest corrected level is 0.01667 and needs 240 draws, so `ci95_corrected` would be null (warning) |
```

  (c) `docs/superpowers/spec-defects.md` — append a new section:

```markdown
## A validate-time `comparisons × metrics` bound on `resample.n` cannot be built

Found while scoping H4a (2026-08-15, `eaf3605`). `H4-SCOPING.md`'s trap 1 asked `validate` to
bound `statistics.resample.n` against the correction family, which `correction.family_shape`
computes as `comparisons × metrics`.

**The metric count is unknowable at `validate` time by design.** `family_shape` reads
`len({(m.step, m.metric) for m in members})` from `Member`s `cli._comparison_step_blocks` builds
*after every execution has run*, out of (a) recorded columns, which come from `io.record` calls
inside user step code, and (b) `aggregate`'s returned keys, which come from user template code.
Neither is declared anywhere in the config — `envelope.LEAF_TYPES` has no `metrics` path,
`parameter_spec` declares parameters, and `hypotheses` names metrics only for the ones a user
pre-registered. `CLAUDE.md`'s greenfield invariant closes the door: core "never inspects the body
of user Python."

**What H4a built instead:** `W-STATS-RESAMPLE-FAMILY`, a comparisons-only lower bound — with `k`
comparisons and at least one metric each, `holm`'s tightest level is `ALPHA / k` and needs
`min_honest_draws(1 − ALPHA/k)` draws. Always true when it fires, silent when it might not be.

**The residue, accepted rather than fixed:** a config with many metrics can still null every
`ci95_corrected` while clearing this bound. That is already disclosed at run time by
`W-STATS-CORRECTED-THIN`, which names the realized `family_size` and `correction_level`. Proposed
resolution: none — a validate-time check that reported the real requirement would have to know
what user code returns, and the run-time disclosure is the honest surface for it. Recorded so the
absence is a decision rather than a gap nobody noticed.
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k resample`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`, then the doc mechanical pass on both `reference.md` and `spec-defects.md`.

- [ ] **Step 5: Mutate** — in `validate.py`, change `needed = min_honest_draws(1.0 - ALPHA / comparisons)` to `needed = min_honest_draws()`. Run `uv run pytest tests/test_validate.py -k family_bound`. `test_the_family_bound_scales_with_the_comparison_count` must FAIL on its second assertion (100 ≥ 80, so no warning at three comparisons) and `test_the_family_bound_is_silent_when_n_clears_it` must FAIL on its 239 assertion — two tests, which is why the scaling test exists beside the boundary test. Delete `__pycache__`, edit the expression back in place, re-run. Second mutation: delete the `if correction_method not in ("holm", "bonferroni"): return` guard; `test_the_family_bound_is_not_reported_where_no_level_exists` must FAIL for both parameters. Revert in place.

- [ ] **Step 6: Commit** — `feat: W-STATS-RESAMPLE-FAMILY, the comparisons-only bound; file the metric-count residue`.

---

## Task 7: `resample` declared with no `data.units`

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_resample(doc, roster, c)` (Tasks 4–6).
- Produces: `E-STATS-RESAMPLE-UNITS`.

**Why this is a task and not a footnote.** Today `E-STATS-RESAMPLE-UNSUPPORTED` covers this shape wholesale. Retire it (Task 12) and a bare `resample: {method: bootstrap, n: 2000}` with **no roster** validates clean and does nothing — literally the failure `_check_unimplemented`'s own comment records for `E-SWEEP-SAMPLE-BASELINE`: *"Retiring it made the shape reachable without implementing them."* Tasks 4, 5 and 6 all presuppose a roster and none covers its absence.

`reference.md` marks the `units:` block "required by fold, resample, null_test" and says of a unit-less design that `fold`, `statistics.resample` and `statistics.null_test` "then aren't available, which is correct, since there'd be nothing to partition or resample". The precedent shape is `_check_replication`'s fold-without-basis check, which reports `E-REPL-FOLD-K` when `fold_basis` is `None` for the same reason.

**Gate on the declaration, not on `roster is None`.** `roster` is also `None` when `data.units` *is* declared but failed to resolve — a table that does not exist, a `key` column absent — and that fault already has its own finding from `_check_units`. Reporting a second, derived fault on top of the one the reader has to fix anyway is what the `usable_cluster` guard in `validate_config` avoids by the same reasoning.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
def test_a_resample_with_no_unit_roster_is_refused(write_config):
    """`reference.md` marks `data.units` "required by fold, resample,
    null_test". Once `E-STATS-RESAMPLE-UNSUPPORTED` retires, this shape would
    otherwise validate clean and do nothing — the exact failure
    `_check_unimplemented`'s own `E-SWEEP-SAMPLE-BASELINE` comment records."""
    found = codes(
        write_config({"statistics": {"resample": {"method": "bootstrap", "n": 2000}}})
    )
    assert "E-STATS-RESAMPLE-UNITS" in found
    # Positive companion in the same test: the identical declaration WITH a
    # roster is not refused, so this cannot pass by refusing every resample.
    assert "E-STATS-RESAMPLE-UNITS" not in codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        )
    )


def test_an_unresolvable_roster_does_not_earn_a_second_resample_finding(write_config):
    """`roster` is `None` for a declared-but-unresolvable `data.units` too, and
    that fault already has `_check_units`' own finding. Gating on the DECLARATION
    rather than on `roster is None` is what keeps this from reporting a derived
    fault on top of the one the reader has to fix anyway."""
    c = Collector()
    validate_config(
        write_config(
            {
                "data.units": {"from": "nope.csv", "key": "patient_id"},
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        ),
        c,
    )
    found = {f.code for f in c.findings}
    assert "E-STATS-RESAMPLE-UNITS" not in found
    # The positive half: the real fault IS reported, so the test cannot pass by
    # the config being clean.
    assert any(code.startswith("E-UNITS-") or code.startswith("E-DATA-") for code in found)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k no_unit_roster or unresolvable_roster -x`. The first fails on the missing code; the second passes vacuously and is the control for the gating decision.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`, at the **top** of `_check_resample`, immediately after the `if not isinstance(resample, dict) or not resample: return` guard:

```python
    # No roster at all, which is a different fault from every check below and
    # the one they all presuppose away. `reference.md` § The one config file
    # marks `units:` "required by fold, resample, null_test", and § Where units
    # come from says resample "isn't available" without one. The precedent is
    # `_check_replication`'s fold-without-basis check (`E-REPL-FOLD-K`), for the
    # same reason: a declaration that cannot operate on anything is refused
    # rather than accepted and silently skipped.
    #
    # Read from the DECLARATION, not from `roster is None`: the roster is also
    # `None` when `data.units` is declared and failed to resolve, and that fault
    # already has `_check_units`' own finding. A second, derived fault on top of
    # the one the reader has to fix anyway is what `validate_config`'s
    # `usable_cluster` guard avoids by the same argument. Every later check in
    # this function returns after this one, since each of them presupposes a
    # roster it would have nothing to read.
    units_declared = ((doc.get("data") or {}).get("units")) or {}
    if not units_declared:
        c.error(
            "E-STATS-RESAMPLE-UNITS",
            "statistics.resample",
            "is declared and `data.units` is not, so there is no unit table to draw "
            "from and no metric core could recompute on a draw — a declaration that "
            "changes no behavior. Declare `data.units`, or drop `resample` and report "
            "over repeats, which is honest for a design whose executions are the "
            "observations",
        )
        return
```

  (b) `docs/reference.md` § Errors `validate` reports:

```markdown
| `statistics.resample` is declared and `data.units` is not — there is no unit table to draw from, so the declaration would change no behavior. Read from the declaration, not from whether a roster resolved: a declared-but-unresolvable `data.units` already has its own finding | `E-STATS-RESAMPLE-UNITS` |
```

  And a § Validation row:

```markdown
| Resample has a roster | `statistics.resample` is declared with no `data.units` — nothing to resample, and the declaration would run nothing |
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k resample`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`, then the doc mechanical pass.

- [ ] **Step 5: Mutate** — in `validate.py`, change the gate to `if roster is None:`. Run `uv run pytest tests/test_validate.py -k unresolvable_roster`. `test_an_unresolvable_roster_does_not_earn_a_second_resample_finding` must FAIL (the derived finding now appears) while `test_a_resample_with_no_unit_roster_is_refused` still passes — which is the whole point of writing both. Delete `__pycache__`, edit the gate back to `if not units_declared:` in place, re-run.

- [ ] **Step 6: Commit** — `feat: E-STATS-RESAMPLE-UNITS, so retiring the refusal cannot open a silent no-op`.

---

## Task 8: `limits.min_clusters` made real

**Files:** Modify `src/publishable/validate.py`, `src/publishable/stats.py` (docstring only), `docs/reference.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_resample(doc, roster, c)` (Tasks 4–7); `units.fold_basis(roster, cluster_by) -> int`, already imported by `validate`.
- Produces: `W-STATS-RESAMPLE-CLUSTERS`.

**The state today.** `materialize.py` writes `  min_clusters: 10` into every generated config, `envelope.py` types `"limits.min_clusters": int`, and **`grep -c min_clusters src/publishable/validate.py` returns 0** — the value is materialized, typed, and read by nothing. `reference.md` puts it under `limits` and says "`validate` warns when `resample` would draw fewer than this", and carries the § Validation row *Clusters enough to resample*: "`statistics.resample` with `cluster_by: animal_id` over 4 animals bootstraps 4 draws; below `limits.min_clusters` (warning)". This is the fifth documented-row-with-no-emit-site of the kind CLAUDE.md warns about — grep for the code before building on the row.

**The one-line docstring fix.** `stats.percentile_over_units_clustered`'s docstring says the judgment that a cluster count is too few "belongs to `statistics.min_clusters`". There is no such path. It is `limits.min_clusters`. Fix the citation in the same commit as the check, because a comment claiming a guarantee the code does not provide is this repo's single most repeated defect.

**Count clusters through `units.fold_basis`**, which is the same single counting expression `_check_replication` and `_check_sweep` already share and which resolves to the cluster count when `cluster_by` is a non-empty string. Two counting expressions for "how many clusters are there" is the drift a shared derivation removes.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
_FOUR_ANIMALS = "patient_id,animal_id\n" + "".join(
    f"p{i},a{i % 4}\n" for i in range(12)
)


def test_a_clustered_resample_below_min_clusters_warns(write_config, tmp_path):
    """§ Validation's *Clusters enough to resample* row, which has had no emit
    site since it was written: 12 units in 4 animals bootstraps 4 draws, and
    `limits.min_clusters` is 10 in every generated config."""
    (tmp_path / "input" / "index.csv").write_text(_FOUR_ANIMALS)
    found = codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv",
                    "key": "patient_id",
                    "attributes": ["animal_id"],
                    "cluster_by": "animal_id",
                },
                "limits.min_clusters": 10,
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        )
    )
    assert "W-STATS-RESAMPLE-CLUSTERS" in found


def test_the_cluster_warning_counts_clusters_not_units(write_config, tmp_path):
    """12 units and 4 clusters: a check reading `len(roster)` sees 12, clears a
    floor of 10, and is silent. The fixture is sized so unit count and cluster
    count fall on OPPOSITE sides of the same threshold, which a 12-unit /
    12-cluster fixture could not distinguish."""
    (tmp_path / "input" / "index.csv").write_text(_FOUR_ANIMALS)
    found = codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv", "key": "patient_id",
                    "attributes": ["animal_id"], "cluster_by": "animal_id",
                },
                "limits.min_clusters": 10,
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        )
    )
    assert "W-STATS-RESAMPLE-CLUSTERS" in found
    messages = messages_by_code(
        write_config(
            {
                "data.units": {
                    "from": "index.csv", "key": "patient_id",
                    "attributes": ["animal_id"], "cluster_by": "animal_id",
                },
                "limits.min_clusters": 10,
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        )
    )
    assert "4" in messages["W-STATS-RESAMPLE-CLUSTERS"]
    assert "12" not in messages["W-STATS-RESAMPLE-CLUSTERS"]


def test_the_cluster_warning_is_silent_above_the_floor(write_config, tmp_path):
    """The positive companion: the same roster with `min_clusters: 3` is silent,
    so the warning reads the declared floor rather than firing on any cluster
    count at all."""
    (tmp_path / "input" / "index.csv").write_text(_FOUR_ANIMALS)
    found = codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv", "key": "patient_id",
                    "attributes": ["animal_id"], "cluster_by": "animal_id",
                },
                "limits.min_clusters": 3,
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        )
    )
    assert "W-STATS-RESAMPLE-CLUSTERS" not in found


def test_no_cluster_warning_without_a_declared_resample(write_config, tmp_path):
    """`cluster_by` alone decides each condition's own interval and draws
    nothing; the row scopes the warning to `resample` with `cluster_by`."""
    (tmp_path / "input" / "index.csv").write_text(_FOUR_ANIMALS)
    found = codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv", "key": "patient_id",
                    "attributes": ["animal_id"], "cluster_by": "animal_id",
                },
                "limits.min_clusters": 10,
            }
        )
    )
    assert "W-STATS-RESAMPLE-CLUSTERS" not in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k cluster_warning or below_min_clusters -x`. Confirm the missing code first, and separately confirm the row has no emit site today: `grep -c min_clusters src/publishable/validate.py` must print `0`.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`, append to `_check_resample` (before the family bound's early `return`s, or after the `stratify_by` loop and before the `correction_method` block — order inside the function is free, but it must not sit after a `return`):

```python
    # `limits.min_clusters`: materialized in every generated config, typed by
    # `envelope.py`, and — until this slice — read by nothing. § Validation's
    # *Clusters enough to resample*: "`statistics.resample` with `cluster_by:
    # animal_id` over 4 animals bootstraps 4 draws; below `limits.min_clusters`
    # (warning)". Scoped to `resample` WITH `cluster_by`, because `cluster_by`
    # alone decides each condition's own interval and draws nothing.
    #
    # Counted through `units.fold_basis`, the single counting expression
    # `_check_replication` and `_check_sweep` already share: it resolves to the
    # cluster count when `cluster_by` is a non-empty string. A second expression
    # for "how many clusters are there" is the drift one derivation removes, and
    # the number a reader compares against `n.clusters` in `run.yaml` has to be
    # the same number.
    cluster_by = units_declared.get("cluster_by")
    min_clusters = (doc.get("limits") or {}).get("min_clusters")
    if (
        roster is not None
        and isinstance(cluster_by, str)
        and cluster_by
        and isinstance(min_clusters, int)
        and not isinstance(min_clusters, bool)
    ):
        try:
            groups = fold_basis(roster, cluster_by)
        except ContractError:
            # A unit carrying no value for the cluster attribute
            # (`E-DATA-CLUSTER-UNKNOWN`), already reported beside this by
            # `_check_cluster_by` or by the resolution `_check_units` performed.
            # This module collects rather than raises.
            groups = None
        if groups is not None and groups < min_clusters:
            c.warn(
                "W-STATS-RESAMPLE-CLUSTERS",
                "limits.min_clusters",
                f"is {min_clusters}, and `data.units.cluster_by: {cluster_by}` puts this "
                f"roster in {groups} clusters — `resample` draws whole clusters, so the "
                f"percentile interval rests on {groups} independent draws however many "
                "units they hold",
            )
```

  (b) `src/publishable/stats.py`, in `percentile_over_units_clustered`'s docstring, change:

```
    `statistics.min_clusters` — `reference.md` § The one config file:
```

  to:

```
    `limits.min_clusters` — `reference.md` § The one config file:
```

  There is no `statistics.min_clusters` path in `envelope.LEAF_TYPES` and never was; the miscitation named a guarantee under a name nothing reads.

  (c) `docs/reference.md` § Warnings core reports:

```markdown
| `statistics.resample` is declared beside `data.units.cluster_by` and the roster falls in fewer clusters than `limits.min_clusters` — a resample draws whole clusters, so the interval rests on that many independent draws however many units they hold | `W-STATS-RESAMPLE-CLUSTERS` |
```

  The § Validation row *Clusters enough to resample* already exists and needs no edit.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k cluster`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`, then the doc mechanical pass. Also re-run `grep -n "statistics.min_clusters" src/ docs/ -r` and confirm zero matches.

- [ ] **Step 5: Mutate** — in `validate.py`, change `groups = fold_basis(roster, cluster_by)` to `groups = len(roster)`. Run `uv run pytest tests/test_validate.py -k counts_clusters_not_units`. It must FAIL — 12 units clears a floor of 10 where 4 clusters does not, which is why the fixture puts the two counts on opposite sides of one threshold. Delete `__pycache__`, edit the line back in place, re-run. Second mutation: change `groups < min_clusters` to `groups <= min_clusters`; `test_the_cluster_warning_is_silent_above_the_floor` still passes (4 > 3), so add nothing — instead change it to `groups < 10`, and `test_the_cluster_warning_is_silent_above_the_floor` must FAIL, proving the declared floor is read rather than a constant. Revert in place.

- [ ] **Step 6: Commit** — `feat: W-STATS-RESAMPLE-CLUSTERS, and fix the docstring citing limits.min_clusters as statistics.min_clusters`.

---

## Task 9: The stratified draw — construction, not wiring

**Files:** Modify `src/publishable/stats.py`. Test `tests/test_stats.py`.

**Interfaces:**
- Consumes: `stats.percentile_over_units(values, seed, draws=2000, confidence=0.95, weights=None)` as it stands at `src/publishable/stats.py:488`; `stats.checked_weights`; `stats._weighted_mean`; `stats._percentile_ranks`; `stats.min_honest_draws`.
- Produces: `percentile_over_units(values, seed, draws=2000, confidence=0.95, weights=None, strata=None) -> Interval | None`, where `strata` is a sequence aligned positionally to `values`. Task 14 passes it; Task 15 builds it.

**This is construction, not wiring.** Nothing in `stats.py` draws within a stratum, and `units._stratum_groups` is not reusable — it takes a `UnitList`, and `stats.py` is deliberately import-free of `units` beyond `cluster_count_of`/`checked_weights`. **Six of the seven non-null `resample:` declarations in `docs/feasibility-llm-growth-studies.md` carry a `stratify_by`**, so this is the common case, not the exotic one.

**What the document specifies.** `reference.md` § Weighted samples: "`resample.stratify_by` says what an independent draw is, resampling within each stratum so a bootstrap can't return a replicate whose stratum composition the design ruled out." So each draw preserves **each stratum's own size** and draws with replacement **within** it.

**Row-order invariance is preserved the same way the existing branches preserve it.** `percentile_over_units` sorts its pool because with a fixed seed `rng.randrange(n)` draws the same sequence of *indices* whatever the input order is, so the multiset of values must be all that matters. Under strata: group first (carrying each value's weight with it), sort within each stratum, then order the strata **by their own sorted contents** rather than by label — which is what makes a relabelled stratum give the identical interval, exactly as `percentile_over_units_clustered` orders its cluster pools.

**Fixture sizing — this is where a fixture agrees with the bug.** Use three strata with **unequal sizes and disjoint value bands**: 20 values in `[0, 1)`, 8 in `[10, 11)`, 2 in `[100, 101)`. Then the three candidate answers are all different numbers:
- correct stratified mean ≈ `(20·0.5 + 8·10.5 + 2·100.5) / 30` ≈ **9.83**, with a *narrow* interval because the 2-value stratum contributes exactly 2 rows to every draw;
- unstratified draw: same expectation, but the 2-value stratum's contribution varies from 0 to many, so the interval is **several times wider**;
- averaging the strata's own means: `(0.5 + 10.5 + 100.5) / 3` ≈ **37.17**, nowhere near either.

Two equal strata distinguish none of these.

- [ ] **Step 1: Write the failing test** — append to `tests/test_stats.py`:

```python
def _banded_strata() -> tuple[list[float], list[str]]:
    """Three strata, unequal sizes, disjoint value bands. Sized so that the
    three candidate constructions produce three DIFFERENT numbers:

      correct stratified mean  (20·0.5 + 8·10.5 + 2·100.5) / 30  ≈  9.83
      unstratified             same centre, several times wider
      mean of stratum means    (0.5 + 10.5 + 100.5) / 3          ≈ 37.17

    Two equal strata distinguish none of them, which is the fixture-sizing rule
    this repo wrote into CLAUDE.md after an apportionment test matched a
    reverse-order mutant by coincidence."""
    values = (
        [i / 20.0 for i in range(20)]
        + [10.0 + i / 8.0 for i in range(8)]
        + [100.0 + i / 2.0 for i in range(2)]
    )
    strata = ["low"] * 20 + ["mid"] * 8 + ["high"] * 2
    return values, strata


def test_a_stratified_draw_preserves_each_stratum_size():
    """§ Weighted samples: resampling within each stratum "so a bootstrap can't
    return a replicate whose stratum composition the design ruled out". The
    two-value stratum contributes exactly 2 rows to every draw, which pins the
    interval near 9.83 and makes it much narrower than the unstratified one."""
    values, strata = _banded_strata()
    stratified = percentile_over_units(values, seed=7, draws=2000, strata=strata)
    plain = percentile_over_units(values, seed=7, draws=2000)
    assert stratified is not None and plain is not None
    expected = sum(values) / len(values)  # 9.83…
    assert stratified.low < expected < stratified.high
    stratified_width = stratified.high - stratified.low
    plain_width = plain.high - plain.low
    # Narrower, and by a lot: the whole point of the declaration is that the
    # 2-unit stratum's contribution stops varying.
    assert stratified_width < plain_width / 2.0
    # And NOT the mean-of-stratum-means answer, which is 37.17 — a construction
    # that gave each stratum equal say would put the interval there instead.
    assert stratified.high < 20.0


def test_a_stratified_draw_is_invariant_to_row_order():
    """A fixed seed draws a fixed sequence of indices, so the multiset of
    (value, stratum) pairs must be all that matters — the same invariance the
    unstratified branch gets from sorting its pool, and the same one
    `percentile_over_units_clustered` gets from ordering its pools by contents."""
    values, strata = _banded_strata()
    pairs = list(zip(values, strata, strict=True))
    shuffled = pairs[7:] + pairs[:7]
    a = percentile_over_units(values, seed=11, draws=2000, strata=strata)
    b = percentile_over_units(
        [v for v, _ in shuffled], seed=11, draws=2000, strata=[s for _, s in shuffled]
    )
    assert a == b


def test_a_stratified_draw_is_invariant_to_stratum_labels():
    """Strata ordered by their own sorted contents, not by label — so renaming
    `low`/`mid`/`high` to `z`/`a`/`m` gives the identical interval."""
    values, strata = _banded_strata()
    renamed = {"low": "z", "mid": "a", "high": "m"}
    a = percentile_over_units(values, seed=3, draws=2000, strata=strata)
    b = percentile_over_units(
        values, seed=3, draws=2000, strata=[renamed[s] for s in strata]
    )
    assert a == b


def test_one_stratum_reproduces_the_unstratified_interval_digit_for_digit():
    """The degenerate case is not a special case: with every unit in one
    stratum, the stratified path draws n indices from one sorted pool, which is
    exactly what the unstratified path does."""
    values, _ = _banded_strata()
    a = percentile_over_units(values, seed=5, draws=2000)
    b = percentile_over_units(values, seed=5, draws=2000, strata=["only"] * len(values))
    assert a == b


def test_a_stratified_weighted_draw_keeps_each_value_with_its_weight():
    """Weights travel with values through the grouping AND the sort. Sorting the
    two sequences separately would preserve every invariance above and silently
    re-pair them — a mistake equal weights cannot see, which is why the weights
    here are as banded as the values."""
    values, strata = _banded_strata()
    weights = [1.0] * 20 + [5.0] * 8 + [50.0] * 2
    got = percentile_over_units(values, seed=9, draws=2000, weights=weights, strata=strata)
    assert got is not None
    expected = sum(v * w for v, w in zip(values, weights, strict=True)) / sum(weights)
    assert got.low < expected < got.high
    # The weighted centre (≈ 39.5) is far from the unweighted one (≈ 9.83), so a
    # re-pairing or a dropped weight lands outside this interval rather than
    # inside it.
    assert got.low > 20.0


def test_a_stratified_draw_refuses_a_misaligned_stratum_vector():
    """A length mismatch is a misaligned vector, and would produce a plausible
    number rather than an error — the same reason `strict=True` guards the
    clustered zip."""
    values, strata = _banded_strata()
    with pytest.raises(ValueError):
        percentile_over_units(values, seed=1, draws=2000, strata=strata[:-1])
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_stats.py -k stratified -x`. Every one fails with `TypeError: percentile_over_units() got an unexpected keyword argument 'strata'`.

- [ ] **Step 3: Implement** — in `src/publishable/stats.py`, replace `percentile_over_units`'s signature and body:

```python
def percentile_over_units(
    values: Sequence[float],
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    weights: Sequence[Any] | None = None,
    strata: Sequence[Any] | None = None,
) -> Interval | None:
```

  Append to its docstring, after the `weights` paragraphs:

```
    With `strata`, each draw preserves **each stratum's own size** and draws with
    replacement *within* it — `reference.md` § Weighted samples:
    "`resample.stratify_by` says what an independent draw is, resampling within
    each stratum so a bootstrap can't return a replicate whose stratum
    composition the design ruled out." The two ways to get this wrong both
    produce a plausible number: drawing `n` units and repairing the composition
    afterwards is the unstratified interval however carefully the counts are
    matched, and averaging the strata's own means gives every stratum equal say,
    which is a different estimator entirely (for 20/8/2 units in three bands it
    reports 37.2 where the sample mean is 9.8).

    `strata` is aligned positionally to `values`, the same contract `weights`
    has, and `strict=True` on the zip for the same reason: a length mismatch is
    a misaligned vector and would produce a number rather than an error.

    **Grouping happens before any sort and carries the pairs**, so each value
    keeps its stratum and its weight; the strata are then ordered by their own
    sorted contents rather than by label, which is what makes a relabelled
    stratum give the identical interval and what makes the one-stratum case
    reproduce the unstratified path digit for digit. Sorting values and stratum
    labels as separate sequences would preserve every invariance and silently
    re-pair them — the mistake equal-sized strata cannot see.
```

  Body — replace everything from `rng = random.Random(seed)` to the `return`:

```python
    if len(values) < 2:
        return None
    if draws < min_honest_draws(confidence):
        return None
    # One weight vector for every branch below, so a value and its weight are
    # paired once. `checked_weights` gates before any draw rather than producing
    # `draws` worth of `nan`, and it is the one authority `validate` and
    # `kish_effective_n` also read.
    carried = None if weights is None else checked_weights(weights)
    rng = random.Random(seed)
    if strata is not None:
        # Grouped BEFORE any sort, carrying (value, weight) pairs, then each
        # group sorted and the groups ordered by their own sorted contents —
        # so the interval depends on the multiset of (value, weight, stratum)
        # triples and on nothing else, not on row order and not on the labels.
        pools: dict[Any, list[tuple[float, float]]] = {}
        pairs_in = zip(
            values,
            strata,
            [1.0] * len(values) if carried is None else carried,
            strict=True,
        )
        for value, stratum, weight in pairs_in:
            pools.setdefault(stratum, []).append((float(value), weight))
        ordered = sorted(sorted(pool) for pool in pools.values())
        means: list[float] = []
        for _ in range(draws):
            # Each stratum contributes exactly as many rows as it holds: that
            # is the composition the design ruled the alternatives out of.
            drawn = [
                pool[rng.randrange(len(pool))] for pool in ordered for _ in range(len(pool))
            ]
            if carried is None:
                means.append(sum(v for v, _ in drawn) / len(drawn))
            else:
                means.append(_weighted_mean([w for _, w in drawn], [v for v, _ in drawn]))
        means.sort()
    elif carried is not None:
        pairs = sorted(zip(values, carried, strict=True))
        n = len(pairs)
        drawn_means = []
        for _ in range(draws):
            drawn = [pairs[rng.randrange(n)] for _ in range(n)]
            drawn_means.append(_weighted_mean([w for _, w in drawn], [v for v, _ in drawn]))
        means = sorted(drawn_means)
    else:
        # Sorted, not just `list(values)`: with a fixed seed, `rng.randrange(n)`
        # draws the same sequence of *indices* regardless of input order, so
        # drawing from an unsorted pool would make the resample depend on row
        # order — the multiset of values must be all that matters.
        pool_flat = sorted(values)
        n = len(pool_flat)
        means = sorted(
            sum(pool_flat[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws)
        )
    lo, hi = _percentile_ranks(draws, confidence)
    return Interval(low=means[lo], high=means[hi], method="percentile_over_units")
```

  Note the one-stratum equality this preserves: with a single stratum, `ordered` holds one sorted pool of length `n` and the loop draws `n` indices from it in the same order the unweighted branch does, so `test_one_stratum_reproduces_the_unstratified_interval_digit_for_digit` holds by construction rather than by luck.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_stats.py -k stratified or percentile_over_units`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`. The ~20 existing `percentile_over_units` tests must be untouched — none passes `strata`, and the default is `None`.

- [ ] **Step 5: Mutate** — in `stats.py`, change the draw line to ignore the stratum sizes:

```python
            drawn = [
                pool[rng.randrange(len(pool))] for pool in ordered for _ in range(1)
            ]
```

  Run `uv run pytest tests/test_stats.py -k preserves_each_stratum_size`. It must FAIL: each stratum then contributes one row, so the mean lands near the mean-of-stratum-means 37.17 and the `stratified.high < 20.0` assertion breaks — which is exactly the third candidate the banded fixture exists to separate. Delete `__pycache__`, edit `range(1)` back to `range(len(pool))` in place, re-run. Second mutation: change `ordered = sorted(sorted(pool) for pool in pools.values())` to `ordered = [sorted(pools[k]) for k in sorted(pools)]`; `test_a_stratified_draw_is_invariant_to_stratum_labels` must FAIL. Revert in place.

- [ ] **Step 6: Commit** — `feat: percentile_over_units draws within a stratum, preserving its size`.

---

## Task 10: The stratified × clustered composition rule

**Files:** Modify `src/publishable/stats.py`, `src/publishable/validate.py`, `docs/reference.md`. Test `tests/test_stats.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `stats.percentile_over_units_clustered(values, keys, membership, seed, draws=2000, confidence=0.95, weights=None)` at `src/publishable/stats.py:552`; `units.stratum_varies_within_cluster(roster, cluster_by, stratify_by) -> tuple[str, list[str]] | None` at `src/publishable/units.py:1817`, already imported by `validate`; `units.cluster_count_of`; `validate._check_resample` (Tasks 4–8).
- Produces: `percentile_over_units_clustered(..., strata: Sequence[Any] | None = None)`, and `E-STATS-RESAMPLE-STRATIFY-VARIES`.

**The rule, stated (spec decision 3).** `stratify_by` says what an independent draw is; `cluster_by` says the draw **is** a cluster. Composed: **a stratum must be constant within a cluster, and the draw is a cluster drawn within its stratum.** § Clustered units already requires exactly this constancy for `fold`, `holdout` and `assign` — resample takes the same rule rather than a second one, and `units.stratum_varies_within_cluster` is the check that already exists. A cluster carrying two stratum values cannot be dealt to either, being indivisible.

**Dual-listed, like `E-DATA-WEIGHT-INVALID`.** `validate` reports it from the declaration plus the roster; `stats` raises the same code at run time, because `stats.py` is a public surface that will be handed a stratum vector and a membership map and cannot silently pick one.

- [ ] **Step 1: Write the failing test** — append to `tests/test_stats.py`:

```python
def _clustered_banded() -> tuple[list[float], list[str], dict[str, str], list[str]]:
    """Six clusters of unequal size across three strata, with disjoint value
    bands per stratum — so a cluster draw ignoring the strata, a correct
    stratified cluster draw, and a row-level draw all give different intervals.

    Stratum `low`  : clusters c0 (4 units), c1 (3) — values in [0, 1)
    Stratum `mid`  : clusters c2 (3), c3 (2)       — values in [10, 11)
    Stratum `high` : clusters c4 (2), c5 (1)       — values in [100, 101)
    """
    values: list[float] = []
    keys: list[str] = []
    membership: dict[str, str] = {}
    strata: list[str] = []
    plan = [
        ("c0", "low", 4, 0.0), ("c1", "low", 3, 0.5),
        ("c2", "mid", 3, 10.0), ("c3", "mid", 2, 10.5),
        ("c4", "high", 2, 100.0), ("c5", "high", 1, 100.5),
    ]
    for cluster, stratum, size, base in plan:
        for i in range(size):
            key = f"{cluster}_u{i}"
            values.append(base + i / 100.0)
            keys.append(key)
            membership[key] = cluster
            strata.append(stratum)
    return values, keys, membership, strata


def test_a_clustered_stratified_draw_takes_clusters_within_strata():
    """`stratify_by` says what an independent draw is; `cluster_by` says the
    draw IS a cluster. Composed: two clusters are drawn from each stratum
    (each stratum holds two), so every replicate carries all three bands and the
    interval is far narrower than the unstratified cluster draw, where a single
    replicate can hold six `high` clusters."""
    values, keys, membership, strata = _clustered_banded()
    stratified = percentile_over_units_clustered(
        values, keys, membership, seed=13, draws=2000, strata=strata
    )
    plain = percentile_over_units_clustered(values, keys, membership, seed=13, draws=2000)
    assert stratified is not None and plain is not None
    assert (stratified.high - stratified.low) < (plain.high - plain.low) / 2.0
    assert stratified.method == "percentile_over_units_clustered"


def test_a_clustered_stratified_draw_refuses_a_stratum_that_varies_within_a_cluster():
    """A cluster is indivisible, so it cannot be dealt to two strata. The same
    rule § Clustered units already imposes on `fold`, `holdout` and `assign`,
    reported under this construction's own code because `stats.py` is handed the
    two vectors directly and cannot pick one."""
    values, keys, membership, strata = _clustered_banded()
    strata[0] = "mid"  # c0_u0 now disagrees with the rest of c0
    with pytest.raises(ContractError) as exc:
        percentile_over_units_clustered(
            values, keys, membership, seed=13, draws=2000, strata=strata
        )
    assert exc.value.code == "E-STATS-RESAMPLE-STRATIFY-VARIES"
    assert "c0" in str(exc.value)
    # Positive companion: the UNMUTATED vector does not raise, so this cannot
    # pass by the construction refusing every stratified clustered draw.
    _, _, _, clean = _clustered_banded()
    assert percentile_over_units_clustered(
        values, keys, membership, seed=13, draws=2000, strata=clean
    ) is not None
```

  And append to `tests/test_validate.py`:

```python
_VARYING_STRATUM = (
    "patient_id,animal_id,label\n"
    "p0,a0,x\np1,a0,y\n"          # animal a0 carries two labels
    + "".join(f"p{i},a{i},x\n" for i in range(2, 14))
)


def test_a_resample_stratum_varying_within_a_cluster_is_refused(write_config, tmp_path):
    """The composition rule, checked from the declaration plus the roster the
    way *Fold strata survive clustering* already is — `validate` reuses
    `units.stratum_varies_within_cluster` rather than minting a second notion of
    constancy."""
    (tmp_path / "input" / "index.csv").write_text(_VARYING_STRATUM)
    found = codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv", "key": "patient_id",
                    "attributes": ["animal_id", "label"], "cluster_by": "animal_id",
                },
                "limits.min_clusters": 2,
                "statistics": {"resample": {"method": "bootstrap", "n": 2000,
                                            "stratify_by": ["label"]}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-STRATIFY-VARIES" in found


def test_a_constant_stratum_within_clusters_is_accepted(write_config, tmp_path):
    """Positive companion: the same declaration over a roster where `label` IS
    constant within each animal is clean, so the check reads the roster rather
    than refusing the combination."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,animal_id,label\n" + "".join(f"p{i},a{i // 2},x\n" for i in range(28))
    )
    found = codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv", "key": "patient_id",
                    "attributes": ["animal_id", "label"], "cluster_by": "animal_id",
                },
                "limits.min_clusters": 2,
                "statistics": {"resample": {"method": "bootstrap", "n": 2000,
                                            "stratify_by": ["label"]}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-STRATIFY-VARIES" not in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_stats.py -k clustered_stratified tests/test_validate.py -k varying_within_a_cluster -x`. The stats tests fail on the unexpected `strata` keyword; the validate test fails on the missing code.

- [ ] **Step 3: Implement** —

  (a) `src/publishable/stats.py`, `percentile_over_units_clustered`: add `strata: Sequence[Any] | None = None` as the last parameter, and insert after the `groups < 2` guard:

```python
    # A stratum must be CONSTANT within a cluster, and this is a composition of
    # two declarations rather than a third rule: `stratify_by` says what an
    # independent draw is, `cluster_by` says the draw IS a cluster, and a cluster
    # carrying two stratum values cannot be dealt to either, being indivisible.
    # § Clustered units already imposes exactly this on `fold`, `holdout` and
    # `assign`; `validate` reports it from the declaration through
    # `units.stratum_varies_within_cluster`, and this is the run-time half of the
    # same dual listing `E-DATA-WEIGHT-INVALID` has — a public function handed
    # both vectors directly cannot silently pick one of them.
    cluster_stratum: dict[str, Any] = {}
    if strata is not None:
        for key, stratum in zip(keys, strata, strict=True):
            cluster = membership[key]
            if cluster in cluster_stratum and cluster_stratum[cluster] != stratum:
                raise ContractError(
                    f"cluster {cluster!r} carries stratum values "
                    f"{cluster_stratum[cluster]!r} and {stratum!r}. A resample draws "
                    "whole clusters, so a cluster cannot be drawn within one stratum "
                    "while carrying two; stratify on an attribute that is constant "
                    "within a cluster, or drop `cluster_by` if the units really are "
                    "independent",
                    code="E-STATS-RESAMPLE-STRATIFY-VARIES",
                )
            cluster_stratum[cluster] = stratum
```

  Then replace the draw loop so that, when `strata` is given, the cluster pools are grouped by stratum and each stratum's own cluster count is drawn:

```python
    ordered = sorted(sorted(pool) for pool in pools.values())
    rng = random.Random(seed)
    if strata is None:
        stratum_pools = [ordered]
    else:
        # Cluster pools grouped by the stratum their cluster carries, then each
        # group ordered by its own sorted contents — the same label-independence
        # the unstratified `ordered` gets, one level up.
        by_stratum: dict[Any, list[list[tuple[float, float]]]] = {}
        for cluster, pool in pools.items():
            by_stratum.setdefault(cluster_stratum[cluster], []).append(sorted(pool))
        stratum_pools = [sorted(group) for group in by_stratum.values()]
        stratum_pools.sort()
    means: list[float] = []
    for _ in range(draws):
        # Each stratum contributes exactly as many CLUSTERS as it holds — the
        # composition of "the draw is a cluster" with "each stratum keeps its
        # size". With no strata this is one group holding every cluster, which
        # is the unstratified draw digit for digit.
        drawn = [
            pair
            for group in stratum_pools
            for _ in range(len(group))
            for pair in group[rng.randrange(len(group))]
        ]
        if weights is None:
            means.append(sum(v for v, _ in drawn) / len(drawn))
        else:
            means.append(_weighted_mean([w for _, w in drawn], [v for v, _ in drawn]))
    means.sort()
```

  Append to the docstring a paragraph stating the composition rule verbatim from the § Clustered units sentence, and naming `E-STATS-RESAMPLE-STRATIFY-VARIES` as its refusal.

  (b) `src/publishable/validate.py`, in `_check_resample`, after the `stratify_by` declared-name loop:

```python
    # The composition rule, from the declarations plus the roster — the same
    # shape *Fold strata survive clustering* and *Holdout strata survive
    # clustering* already have, and reusing `units.stratum_varies_within_cluster`
    # rather than minting a second notion of constancy is the point: a resample
    # draws whole clusters, so it inherits the rule rather than inventing one.
    if roster is not None and isinstance(cluster_by, str) and cluster_by:
        for name in stratum_names(resample.get("stratify_by")):
            if not isinstance(name, str) or name not in declared:
                continue  # already refused above
            try:
                offender = stratum_varies_within_cluster(roster, cluster_by, name)
            except ContractError:
                # A unit with no cluster value (`E-DATA-CLUSTER-UNKNOWN`),
                # already reported beside this. This module collects.
                break
            if offender is not None:
                cluster, seen = offender
                c.error(
                    "E-STATS-RESAMPLE-STRATIFY-VARIES",
                    "statistics.resample.stratify_by",
                    f"names `{name}`, which varies within `{cluster_by}` {cluster} — it "
                    f"carries {', '.join(seen)}. A resample draws whole clusters, so a "
                    "cluster cannot be drawn within one stratum while carrying two; "
                    "stratify on an attribute constant within a cluster",
                )
```

  `cluster_by` is the local Task 8 already binds; make sure this block sits after it.

  (c) `docs/reference.md`: a § Validation row beside *Fold strata survive clustering*:

```markdown
| Resample strata survive clustering | `statistics.resample: {stratify_by: [label]}` with `cluster_by: animal_id`, but `label` varies within animal `A3` — a resample draws whole clusters, so a cluster carrying two stratum values can be drawn within neither |
```

  a § Errors `validate` reports row, and a § Errors core raises row noting it is raised at run time too under the same code, the arrangement `E-DATA-WEIGHT-INVALID` has.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_stats.py -k clustered`, `uv run pytest tests/test_validate.py -k cluster`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`, then the doc mechanical pass.

- [ ] **Step 5: Mutate** — in `stats.py`, change the drawn-cluster count to a constant: `for _ in range(len(group))` → `for _ in range(1)`. Run `uv run pytest tests/test_stats.py -k takes_clusters_within_strata`. It must FAIL — one cluster per stratum makes every replicate three clusters instead of six, and the interval stops being narrower than half the unstratified one only if the fixture's cluster sizes are unequal, which is why the plan sizes them 4/3, 3/2, 2/1. Delete `__pycache__`, revert in place. Second mutation: in `validate.py`, replace `stratum_varies_within_cluster(roster, cluster_by, name)` with `None`; `test_a_resample_stratum_varying_within_a_cluster_is_refused` must FAIL while `test_a_constant_stratum_within_clusters_is_accepted` still passes. Revert in place.

- [ ] **Step 6: Commit** — `feat: a stratum is constant within a cluster, and the draw is a cluster within its stratum`.

---

## Task 11: `resample_draws` for a column metric — verify the invariant decision 2 rests on

**Files:** Modify `src/publishable/stats.py` (docstring), `docs/superpowers/spec-defects.md`. Test `tests/test_stats.py`.

**Interfaces:**
- Consumes: `stats.percentile_over_units(values, seed, draws, confidence, weights, strata)` (Tasks 9–10); `stats.checked_weights`; `units.usable_weight`.
- Produces: the stated guarantee Task 14 relies on — a column metric records `resample_draws` = **the requested `n`**, and `percentile_over_units` keeps returning a bare `Interval`.

**The decision (spec decision 2), and the verification it demands.** `percentile_of_derived` returns `(Interval, int)` because a derived metric's `compute` can fail on a degenerate draw — `nan`, `None`, or a raise — so the survivor count is a real fact. A **column** metric's draw statistic is a mean over a non-empty sample, which is always defined, so `draws_used == n` always and the return type need not change (~20 existing tests read it). **The spec says: "The implementer must verify that invariant before relying on it; if a degenerate column draw is reachable, take `(Interval, int)` instead and say so."** This task is that verification.

**The verification argument, which the test must exercise rather than assert.** The unweighted branch computes `sum(pool[...]) / n` with `n = len(values) >= 2`, so no division by zero. The weighted branch computes `_weighted_mean` over a drawn subset, and `checked_weights` — reading `units.usable_weight`, which requires `math.isfinite(number) and number > 0` — raises `E-DATA-WEIGHT-INVALID` **before any draw** for a zero, negative, non-finite or non-numeric weight. So Σw over any non-empty drawn subset is strictly positive and the weighted mean is defined. The stratified branch draws `len(pool) >= 1` rows from each non-empty pool, so its `drawn` is non-empty too. There is no reachable degenerate column draw.

- [ ] **Step 1: Write the failing test** — append to `tests/test_stats.py`:

```python
@pytest.mark.parametrize(
    "bad", [0, 0.0, -1.0, float("nan"), float("inf"), "heavy", None, True]
)
def test_a_column_resample_refuses_a_bad_weight_before_any_draw(bad):
    """The invariant decision 2 rests on: a column metric's draw statistic is a
    mean over a non-empty sample, so it is ALWAYS defined and
    `resample_draws == n` always. What could break that is a weight of zero
    making Σw zero on some draw — so the check is that `checked_weights`
    (reading `units.usable_weight`, which requires a finite positive number)
    refuses every such weight before a single draw is taken."""
    values = [1.0, 2.0, 3.0, 4.0]
    weights = [1.0, 1.0, 1.0, bad]
    with pytest.raises(ContractError) as exc:
        percentile_over_units(values, seed=1, draws=100, weights=weights)
    assert exc.value.code == "E-DATA-WEIGHT-INVALID"


def test_a_column_resample_is_never_degenerate_across_adversarial_columns():
    """The positive half, and the one that would catch a `(Interval, int)`
    requirement appearing: over columns chosen to be as degenerate as a column
    can be — zero variance, a single repeated value, extreme weight spread,
    a one-unit stratum — the interval is always produced, so no survivor count
    ever differs from the requested draws."""
    cases: list[tuple[list[float], dict]] = [
        ([5.0, 5.0, 5.0, 5.0], {}),                                  # zero variance
        ([0.0, 0.0, 0.0, 1e-12], {}),                                # near-zero spread
        ([1.0, 2.0, 3.0, 4.0], {"weights": [1e-9, 1e-9, 1e-9, 1e9]}),  # extreme spread
        ([1.0, 2.0, 3.0], {"strata": ["a", "b", "b"]}),               # one-unit stratum
        ([1.0, 2.0, 3.0, 4.0], {"strata": ["a", "a", "b", "b"],
                                "weights": [1.0, 2.0, 3.0, 4.0]}),
    ]
    for values, kwargs in cases:
        got = percentile_over_units(values, seed=2, draws=100, **kwargs)
        assert got is not None, (values, kwargs)
        assert got.method == "percentile_over_units"
        assert got.low <= got.high


def test_percentile_over_units_still_returns_a_bare_interval():
    """Pinned deliberately: ~20 tests read this return, and decision 2 is that
    it does NOT become `(Interval, int)`. A slice that changed it would have to
    change this test, which is where the decision gets re-argued rather than
    drifted past."""
    got = percentile_over_units([1.0, 2.0, 3.0, 4.0], seed=1, draws=100)
    assert isinstance(got, Interval)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_stats.py -k column_resample or bare_interval -x`. All three should **pass immediately** — this is a verification task, and a pass here is the evidence decision 2 asked for. If `test_a_column_resample_refuses_a_bad_weight_before_any_draw` fails for any parameter, the invariant is **false**: stop, take `(Interval, int)` from `percentile_over_units` instead, and record the change in `docs/superpowers/spec-defects.md` naming the parameter that broke it.

- [ ] **Step 3: Implement** — in `src/publishable/stats.py`, append to `percentile_over_units`'s docstring:

```
    **This returns a bare `Interval`, with no survivor count, and that is a
    decision rather than an omission.** `percentile_of_derived` returns
    `(Interval, int)` because a derived metric's `compute` can fail on a
    degenerate draw — `nan`, `None`, or a raise — so how many draws survived is
    a real fact about the interval. A column metric's draw statistic is a mean
    over a non-empty sample, which is always defined: the unweighted branch
    divides by `n >= 2`, the weighted branch's Σw is strictly positive because
    `checked_weights` refuses a zero, negative, non-finite or non-numeric weight
    before any draw is taken, and the stratified branch draws `len(pool) >= 1`
    rows from each non-empty pool. So a column's `resample_draws` is the
    REQUESTED `n` and is recorded as such by `summarize_step`; the invariant is
    pinned by `test_a_column_resample_is_never_degenerate_across_adversarial_columns`
    rather than asserted here.
```

  And add to `docs/superpowers/spec-defects.md`:

```markdown
## A column metric's `resample_draws` records the requested `n`, not a survivor count

Decided in H4a (2026-08-15). `stats.percentile_over_units` returns a bare `Interval` where
`percentile_of_derived` returns `(Interval, int)`, so a recorded column under a declared
`statistics.resample` has no survivor count to record beside its interval.

**Ruling: record the requested `n`.** A column's draw statistic is a mean over a non-empty
sample and is always defined — the unweighted branch divides by `n >= 2`, `checked_weights`
refuses a non-positive or non-finite weight before any draw, and a stratified pool is non-empty
by construction — so `draws_used == n` always and the return type need not change (~20 existing
tests read it). Verified rather than assumed, by
`tests/test_stats.py::test_a_column_resample_is_never_degenerate_across_adversarial_columns`
and the parametrized weight refusal beside it.

**Consequence to keep in view:** `W-STATS-RESAMPLE-THIN` fires on `used < requested`, so it can
never fire for a column. That is correct — the warning exists for a template's `aggregate`
producing nothing on some draws — but it means the two metric kinds carry the same field with
subtly different provenance, which `reference.md` § Statistical reporting states.
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_stats.py`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`, then the doc mechanical pass on `spec-defects.md`.

- [ ] **Step 5: Mutate** — in `src/publishable/units.py`, change `usable_weight`'s guard from `if not math.isfinite(number) or number <= 0:` to `if not math.isfinite(number) or number < 0:` — admitting a weight of zero. Run `uv run pytest tests/test_stats.py -k refuses_a_bad_weight`. The `0` and `0.0` parameters must FAIL, which is the proof that the invariant rests on that guard and not on luck. Delete `__pycache__`, edit `number < 0` back to `number <= 0` in place, re-run.

- [ ] **Step 6: Commit** — `test: verify a column draw is never degenerate, so resample_draws records the requested n`.

---

## Task 12: Retire `E-STATS-RESAMPLE-UNSUPPORTED`

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`, `docs/feasibility-llm-growth-studies.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_unimplemented(doc, c)` at `src/publishable/validate.py:2931`, whose two-entry loop over `("resample", …)` / `("null_test", …)` sits at `:3138–3158`.
- Produces: a config declaring `statistics.resample` that reaches `command_run` at all. **Every later task's end-to-end test depends on this**, because `cli` always validates before running and an error exits before a run directory exists.

**Why it lands here and not later.** Tasks 4–11 built the validate-time refusals and the constructions; nothing yet honours the declaration, so retiring the blanket refusal opens a **two-task window** (this task through Task 14) in which a declared `resample` validates clean and changes only the derived draw count. That window is closed by Task 14 and is the smallest one available: retiring any earlier would make the window five tasks wide, and retiring any later would make Tasks 13–14 untestable end to end. `E-STATS-RESAMPLE-UNITS`, `E-STATS-RESAMPLE-METHOD`, `E-STATS-RESAMPLE-N`, `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`, `E-STATS-RESAMPLE-STRATIFY-VARIES`, `W-STATS-RESAMPLE-FAMILY` and `W-STATS-RESAMPLE-CLUSTERS` are all already in place, so the shape is checked before it is honoured.

**`E-STATS-NULLTEST-UNSUPPORTED` stays.** It is an independent key in the same loop, owned by H4d, and `p_value` appears nowhere in `src/`.

**A `-UNSUPPORTED` code is retired wholesale and is absent from the registry.** Do not add a "retired" row to § Errors `validate` reports — that family is deliberately outside that table, and § The one config file's `NOT BUILT` list is where a refused block is named. Retiring means the name disappears from `src/` and from `docs/` except where a historical record deliberately keeps it.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
def test_a_declared_resample_is_no_longer_refused_wholesale(write_config):
    """H4a implements it, so the blanket refusal retires with the slice — the
    same way `E-STATS-CONTRASTS-UNSUPPORTED` and `E-STATS-REPORTBY-UNSUPPORTED`
    retired with theirs."""
    found = codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-UNSUPPORTED" not in found
    # The positive companion, in the same test: the config is now CLEAN of every
    # resample finding, so this cannot pass by the refusal having been renamed.
    assert not [code for code in found if code.startswith("E-STATS-RESAMPLE")]


def test_a_declared_null_test_is_still_refused(write_config):
    """The sibling entry in the same loop is H4d's and does not retire here. A
    single-key retirement that deleted the loop would pass the test above and
    fail this one."""
    assert "E-STATS-NULLTEST-UNSUPPORTED" in codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "statistics": {"null_test": {"method": "permutation", "n": 5000,
                                             "shuffle": "cohort"}},
            }
        )
    )


def test_the_retired_resample_code_appears_nowhere_in_src():
    """A retired `-UNSUPPORTED` code is retired wholesale. Filtering the FILE
    LIST rather than the sweep's output, because a matching line can itself
    contain whatever you would have excluded."""
    import pathlib

    hits = [
        path
        for path in pathlib.Path("src").rglob("*.py")
        if "E-STATS-RESAMPLE-UNSUPPORTED" in path.read_text()
    ]
    assert hits == []
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k no_longer_refused_wholesale or retired_resample_code -x`. Both fail; `test_a_declared_null_test_is_still_refused` passes and is the control that keeps the sibling alive.

- [ ] **Step 3: Implement** —

  (a) `src/publishable/validate.py`, `_check_unimplemented`: delete the `("resample", "E-STATS-RESAMPLE-UNSUPPORTED", "no resampling scheme runs")` tuple from the loop, leaving `null_test` as the only entry. Rewrite the loop as a single guarded check if `ruff` objects to a one-entry loop; keep the message text for `null_test` byte-identical.

  Then edit the docstring paragraph that reads "`statistics.resample` and `.null_test`, and a top-level `hypotheses` block, are refused the same way — a declared 2000-draw bootstrap or a pre-registered hypothesis that runs and reports success while honoring neither is the same silent-no-op class." Replace with:

```
    `statistics.resample` is no longer in this family: `_check_resample` checks
    the declaration for real — the method enum, the 80-draw floor, the strata
    against `data.units.attributes`, the roster's absence, and the cluster count
    — and `cli.command_run` resolves the block and threads it into every
    interval construction, so a declared resample changes the record. That is
    the test this family applies. `.null_test` is still refused the same way: a
    declared 5000-draw permutation that runs and reports nothing is the
    silent-no-op class, and `p_value` exists nowhere in this build.
```

  Also update the comment at `:3134–3138` that reads "`materialize.py` writes only two of these keys into a generated config … so `resample` and `null_test` are simply absent there" — it now names one key.

  (b) `docs/reference.md`:
  - § The one config file's paragraph currently says "**Four declarations above are not yet built**: `data.units.holdout`, the `{resolver: <name>}` form of `data.units.from`, and `statistics.resample` and `statistics.null_test`." Change *Four* to **Three** and drop `statistics.resample` from the list. **Check every count phrase near it** — this repo has been wrong twice on a count near an edited row.
  - Task 2 already removed `NOT BUILT;` from the `resample:` line. Verify with `grep -n 'NOT BUILT' docs/reference.md` that exactly the three remaining declarations carry a marker.
  - § How a metric becomes a number / § Statistical reporting: remove any sentence saying a declared `resample` is refused in this build. Grep for the code: `grep -rln 'E-STATS-RESAMPLE-UNSUPPORTED' docs/` and fix each file the **list** names.

  (c) `docs/feasibility-llm-growth-studies.md` § Executability on this build — **re-date it, do not edit it in place.** It currently opens "Measured on 2026-08-14 against commit `cb96c7d`". A dated build claim is re-measured or it is not changed. Concretely: re-run `uv run publishable validate` against the section's own configs (or, if they are not materialized in the repo, state that the refusal table is re-derived from `validate.py`'s emit sites rather than from a run, and say so in the section), then rewrite the opening as "Measured on <today's date> against commit `<sha of this commit's parent>`", delete the `E-STATS-RESAMPLE-UNSUPPORTED` row from the refusal table, and rewrite the "**Six of the nine are one slice-set away**" paragraph — the remaining blockers are the plugin registry (9 of 9) and `data.units.holdout` (6 of 9), with `E-DATA-WEIGHT-CONTRAST` on C1–C3. **Do not write "unblocks 8 of the nine" anywhere.** The honest statement is: one refusal retired that 8 of 9 configs hit, a regression preserved, and **zero experiments newly executing** — E1–E6 still declare `holdout`, C1–C3 still declare `weight_by` beside a baseline, and all nine declare a resolver.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k resample or null_test`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`. Then: `grep -rln 'E-STATS-RESAMPLE-UNSUPPORTED' src/ docs/ tests/` — the only permitted hits are `docs/superpowers/**` (gitignored) and the new test asserting its absence. Then the doc mechanical pass on `reference.md` **and** `feasibility-llm-growth-studies.md` (the latter is exempt from the cross-document pass, not from the mechanical one).

- [ ] **Step 5: Mutate** — in `validate.py`, re-add the `resample` tuple to `_check_unimplemented`'s loop. Run `uv run pytest tests/test_validate.py -k no_longer_refused_wholesale`. It must FAIL. Delete `__pycache__`, remove the tuple in place, re-run. Second mutation: delete the **whole** loop rather than the one entry; `test_a_declared_null_test_is_still_refused` must FAIL, proving the sibling is genuinely load-bearing here and not incidentally surviving. Revert in place.

- [ ] **Step 6: Commit** — `feat: retire E-STATS-RESAMPLE-UNSUPPORTED; re-date the feasibility build section`.

---

## Task 13: Resolve the block once in `cli.command_run` and thread it

**Files:** Modify `src/publishable/cli.py`. Test `tests/test_cli.py`.

**Interfaces:**
- Consumes: `cli.command_run`'s `derived_metric_draws = 2000` literal at `src/publishable/cli.py:1507`, read at `:1681`, `:1760`, `:1766`, `:1990`, `:2055`, `:2067`; `validate.RESAMPLE_METHODS` (Task 4).
- Produces: `cli._resolved_resample(doc) -> dict[str, Any]` returning `{"method": str, "n": int, "stratify_by": tuple[str, ...], "declared": bool}`, and a local `resample_spec` in `command_run`. Tasks 14, 15, 16 and 17 all read it.

**This is the live regression hazard.** Task 1's pin exists for this task. Replacing the literal `2000` with a resolved value is where an undeclared config silently acquires a different draw count. The resolution must read `.get("resample") or {}` — **not** `.get("resample", DEFAULT)` — because `materialize.py` writes no key at all and a config may write `resample: null`, and the two must produce one answer.

**`declared` is a separate field from `n`.** A config declaring `resample: {n: 2000}` and a config declaring nothing both resolve to 2000 draws, but only the first turns a recorded column into a percentile. `declared` is what Task 14 gates on; `n` is what every existing read site uses. Conflating them is how "a derived metric is resampled whether or not you declare `statistics.resample`" would stop being true.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
def test_a_declared_resample_n_changes_the_derived_draw_count(tmp_path, capsys):
    """The threading, end to end: the literal 2000 becomes the resolved `n`.
    `500` rather than `100` because `W-STATS-RESAMPLE-THIN` fires on
    `used < requested` and a small count makes degenerate draws likely — the
    assertion here is about the requested count, not about survivors."""
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        aggregate_returns="mean_pred",
        units=40,
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 500}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    metric = _first_metric(run, "mean_pred")
    assert metric["resample_draws"] == 500
    assert metric["ci95"] is not None  # 500 clears the 80-draw floor


def test_an_undeclared_resample_still_draws_two_thousand(tmp_path, capsys):
    """The regression Task 1 pinned, restated at the point it can break: the
    resolution must read `.get("resample") or {}`, never
    `.get("resample", DEFAULT)`, because `materialize.py` writes no key at all
    and a hand-written config may write `resample: null` — one answer for two
    different documents."""
    for statistics in ({}, {"correction": "holm", "resample": None}):
        doc = run_a_project(
            tmp_path / f"case{len(statistics)}",
            capsys=capsys,
            aggregate_returns="mean_pred",
            units=40,
            **({"statistics": statistics} if statistics else {}),
        )
        run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
        metric = _first_metric(run, "mean_pred")
        assert metric["resample_draws"] == 2000
        # Positive companion: the column is still a t-interval, so this cannot
        # pass by nothing having been resampled at all.
        column = run["results"]["conditions"][0]["aggregated"][
            "step01_summarize_units"]["pred"]
        assert column["method"] == "t_over_units"


def test_the_resample_block_is_resolved_once():
    """A unit test on the resolver itself, because the end-to-end tests above
    cannot distinguish 'resolved once and threaded' from 'read seven times'.
    Every field has a documented default and `declared` is separate from `n`:
    a config asking for exactly 2000 draws is still a DECLARED resample, which
    is what turns a recorded column into a percentile."""
    from publishable.cli import _resolved_resample

    assert _resolved_resample({}) == {
        "method": "bootstrap", "n": 2000, "stratify_by": (), "declared": False,
    }
    assert _resolved_resample({"statistics": {"resample": None}}) == {
        "method": "bootstrap", "n": 2000, "stratify_by": (), "declared": False,
    }
    assert _resolved_resample({"statistics": {"resample": {"n": 2000}}}) == {
        "method": "bootstrap", "n": 2000, "stratify_by": (), "declared": True,
    }
    assert _resolved_resample(
        {"statistics": {"resample": {"method": "bootstrap", "n": 500,
                                     "stratify_by": "site"}}}
    ) == {"method": "bootstrap", "n": 500, "stratify_by": ("site",), "declared": True}
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k resample_n_changes or resolved_once or still_draws_two_thousand -x`. The first fails with `resample_draws == 2000`; the third fails on the missing import.

- [ ] **Step 3: Implement** — in `src/publishable/cli.py`.

  (a) Add the resolver near `_entry_for`:

```python
def _resolved_resample(doc: dict[str, Any]) -> dict[str, Any]:
    """`statistics.resample` with every default filled in, resolved once.

    `reference.md` § Statistical reporting: "A derived metric is resampled
    whether or not you declare `statistics.resample`" — declaring it "changes
    the method or the count rather than switching the behaviour on, and the
    resolved values are recorded in `run.yaml` beside the interval". So the
    defaults are real values here rather than `summarize_step`'s own defaults
    taking effect unseen at a call site that forgot them.

    **`declared` is separate from `n` on purpose.** A config asking for exactly
    2000 draws and a config asking for nothing both resolve to 2000, but only
    the first turns a RECORDED COLUMN into a percentile interval — a column has
    a t-interval available, so resampling it is a choice and `resample` is what
    makes it, while a derived metric has no such fallback. Reading `declared`
    off `n != 2000` would silently make that sentence false.

    **`.get("resample") or {}`, never `.get("resample", …)`**: `materialize.py`
    writes no `resample` key at all and a hand-written config may write
    `resample: null`, and the two are different documents that must resolve to
    one answer.

    `stratify_by` goes through `units.stratum_names`, the same normalization the
    draw balances on and `validate._check_resample` checks names against, so a
    bare `stratify_by: site` is one name to all three.
    """
    declared = ((doc.get("statistics") or {}).get("resample")) or {}
    if not isinstance(declared, dict):
        declared = {}
    n = declared.get("n")
    return {
        "method": declared.get("method") or "bootstrap",
        "n": n if isinstance(n, int) and not isinstance(n, bool) else 2000,
        "stratify_by": stratum_names(declared.get("stratify_by")),
        "declared": bool(declared),
    }
```

  Import `stratum_names` from `publishable.units` in `cli.py` if it is not already imported.

  (b) Replace the literal at `cli.py:1502–1507`:

```python
            # `statistics.resample` is honored as of H4a: the block is resolved
            # ONCE here and threaded to every read site, rather than each site
            # reading the config for itself. `reference.md` § Statistical
            # reporting requires the resolved values be recorded beside the
            # interval, and two sites resolving the same declaration
            # independently is how the record and the arithmetic disagree.
            resample_spec = _resolved_resample(doc)
            derived_metric_draws = resample_spec["n"]
```

  Leave every one of the six read sites of `derived_metric_draws` unchanged in this task — they now read the resolved value. Verify all six with `grep -n derived_metric_draws src/publishable/cli.py`.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_cli.py -k resample or undeclared_resample_shape` (Task 1's pin **must still pass**, and it is the point of this step), then `uv run pytest`, `uv run mypy`, `uv run ruff check .`.

- [ ] **Step 5: Mutate** — in `cli.py`, change the resolver's first line to `declared = (doc.get("statistics") or {}).get("resample", {"n": 500})`. Run `uv run pytest tests/test_cli.py -k still_draws_two_thousand or undeclared_resample_shape`. `test_an_undeclared_resample_still_draws_two_thousand` must FAIL on the absent-key case while passing on the explicit-`null` case — which is exactly why the two are separate cases and why Task 1's pin has two tests. Delete `__pycache__`, edit the line back in place, re-run. Second mutation: change `"declared": bool(declared)` to `"declared": n != 2000`; `test_the_resample_block_is_resolved_once` must FAIL on the `{"n": 2000}` case. Revert in place.

- [ ] **Step 6: Commit** — `feat: resolve statistics.resample once in command_run and thread it`.

---

## Task 14: A column metric's percentile interval in `summarize_step`

**Files:** Modify `src/publishable/stats.py`, `src/publishable/cli.py`. Test `tests/test_stats.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `stats.summarize_step(collapsed, counts, derived=None, seed=None, resample=None, draws=2000, beside_n=None, weights=None, clusters=None)` at `src/publishable/stats.py:1156`, whose recorded-column branch is `:1340–1393`; `stats.percentile_over_units(values, seed, draws, confidence, weights, strata)` (Tasks 9–11); `stats.percentile_over_units_clustered(values, keys, membership, seed, draws, confidence, weights, strata)` (Task 10); `cli._resolved_resample` and the local `resample_spec` (Task 13).
- Produces: `summarize_step(..., resample_columns: bool = False)`, and a recorded column carrying `method: percentile_over_units` (or `_clustered`) with `resample_draws: <n>` under a declared resample.

**The four combinations, all of which must land together.** Unclustered/unweighted → `percentile_over_units(values, seed, draws=draws)`. Unclustered/weighted → the same with `weights=column_weights`. Clustered/unweighted → `percentile_over_units_clustered(values, column_keys, clusters, seed, draws=draws)`. Clustered/weighted → the same with `weights=column_weights`. In every case the **value** stays what it already is (the mean, or the weighted mean) — only the interval's construction changes. `n.effective` stays Kish's size under a weight, and `n.clusters` stays the cluster count under a cluster: § Weighted samples says the weights are "in the estimate rather than in the drawing", and § Clustered units says the interval's effective `n` is the cluster count.

**`resample_draws` on a column records the requested `n`** (Task 11's verified invariant). It must be **absent** when no resample is declared — Task 1's pin asserts `"resample_draws" not in column`, and an explicit `null` there would claim resampling was attempted and produced nothing, which is the exact ambiguity the `null`-versus-`0` distinction exists to remove.

**A trap this task introduces into an existing loop.** `cli.py:1755–1770` iterates **every** metric in `step_summary` reading `resample_draws`. Today columns have no such key, so `used is None` skips them. After this task they will have one. `used == 0` emits `W-STATS-AGGREGATE-FAILED` naming `<template>.aggregate` — **a lie for a recorded column**, which `aggregate` never touched. A column's `used` is always the requested `n` and `n >= 80`, so neither branch can fire; the brief requires an **assertion** that it does not, because "cannot fire" is a claim about Task 11's invariant and this is where it is consumed.

**A `summary`-step `Estimate` is not reached by this pass.** It lands in `results.summary` through `run_record.summary_values`, never through `summarize_step`. Task 18 owns the assertion.

- [ ] **Step 1: Write the failing test** — append to `tests/test_stats.py`:

```python
def _ragged_collapsed(n: int = 40) -> dict[str, dict[str, float]]:
    return {f"u{i}": {"pred": float(i)} for i in range(n)}


def test_a_recorded_column_takes_a_percentile_interval_under_resample():
    """§ Statistical reporting: a column metric has a t-interval available, so
    resampling it is a CHOICE and `resample` is what makes it. The value is
    unchanged — the draw changes the interval, not the estimate."""
    collapsed = _ragged_collapsed()
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    plain = summarize_step(collapsed, counts, seed=5, draws=2000)
    drawn = summarize_step(collapsed, counts, seed=5, draws=2000, resample_columns=True)
    assert plain["pred"]["method"] == "t_over_units"
    assert "resample_draws" not in plain["pred"]
    assert drawn["pred"]["method"] == "percentile_over_units"
    assert drawn["pred"]["resample_draws"] == 2000
    assert drawn["pred"]["value"] == plain["pred"]["value"]
    assert drawn["pred"]["ci95"] is not None
    low, high = drawn["pred"]["ci95"]
    assert low < drawn["pred"]["value"] < high


def test_a_clustered_column_takes_the_clustered_percentile_under_resample():
    """`cluster_by` decides the draw when both are declared, so the construction
    is the `_clustered` one and `n.clusters` still reports the cluster count."""
    collapsed = _ragged_collapsed(40)
    clusters = {f"u{i}": f"c{i % 8}" for i in range(40)}
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    drawn = summarize_step(
        collapsed, counts, seed=5, draws=2000, clusters=clusters, resample_columns=True
    )
    assert drawn["pred"]["method"] == "percentile_over_units_clustered"
    assert drawn["pred"]["n"]["clusters"] == 8
    assert drawn["pred"]["resample_draws"] == 2000


def test_a_weighted_column_keeps_its_weighted_value_and_kish_size_under_resample():
    """Three things move together or the declaration is half-delivered: the
    value stays the WEIGHTED mean, `n.effective` stays Kish's size, and only the
    interval becomes a percentile. § Weighted samples puts the weights "in the
    estimate rather than in the drawing"."""
    collapsed = _ragged_collapsed(40)
    weights = {f"u{i}": 1.0 + (i % 4) for i in range(40)}
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    plain = summarize_step(collapsed, counts, seed=5, draws=2000, weights=weights)
    drawn = summarize_step(
        collapsed, counts, seed=5, draws=2000, weights=weights, resample_columns=True
    )
    assert plain["pred"]["method"] == "weighted_t_over_units"
    assert drawn["pred"]["method"] == "percentile_over_units"
    assert drawn["pred"]["value"] == plain["pred"]["value"]
    assert drawn["pred"]["n"]["effective"] == plain["pred"]["n"]["effective"]
    # And the weighted centre differs from the unweighted one on this fixture,
    # so a dropped `weights=` lands outside the interval rather than inside it.
    unweighted = summarize_step(collapsed, counts, seed=5, draws=2000)
    assert drawn["pred"]["value"] != unweighted["pred"]["value"]


def test_a_column_below_two_units_reports_no_interval_under_resample():
    """`percentile_over_units` returns `None` below two units exactly as
    `t_over_units` does, so the degenerate case does not change shape — but
    `resample_draws` must still be present, saying which count was requested."""
    counts = {"resolved": 1, "completed": 1, "failed": 0}
    got = summarize_step({"u0": {"pred": 1.0}}, counts, seed=5, draws=2000,
                         resample_columns=True)
    assert got["pred"]["ci95"] is None
    assert got["pred"]["method"] is None
    assert got["pred"]["resample_draws"] == 2000
```

  And append to `tests/test_cli.py`:

```python
def test_a_declared_resample_gives_every_column_a_percentile_interval(tmp_path, capsys):
    """End to end, and the assertion the `resample_draws` warning loop needs:
    `cli`'s loop over `step_summary` reads `resample_draws` on EVERY metric, and
    a column's is now present. `used == 0` would emit
    `W-STATS-AGGREGATE-FAILED` naming the template's `aggregate`, which never
    touched a recorded column — a lie. A column's `used` is the requested `n`
    and `n >= 80`, so neither branch can fire, and this pins it."""
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        aggregate_returns="mean_pred",
        units=40,
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 500}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    assert aggregated["pred"]["method"] == "percentile_over_units"
    assert aggregated["pred"]["resample_draws"] == 500
    assert aggregated["pred"]["ci95"] is not None
    # The derived metric still resamples, at the same resolved count.
    assert aggregated["mean_pred"]["method"] == "percentile_over_units"
    assert aggregated["mean_pred"]["resample_draws"] == 500
    # Neither warning fires for the column.
    assert "W-STATS-AGGREGATE-FAILED" not in doc["stdout"]
    assert "W-STATS-RESAMPLE-THIN" not in doc["stdout"]
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_stats.py -k percentile_interval_under_resample or clustered_column or weighted_column_keeps -x`. All fail with `TypeError: summarize_step() got an unexpected keyword argument 'resample_columns'`.

- [ ] **Step 3: Implement** —

  (a) `src/publishable/stats.py`, `summarize_step`: add `resample_columns: bool = False` as the last parameter, and replace the interval selection at `:1361–1380`:

```python
        interval: Interval | None
        value: float | None
        column_weights: list[Any] | None = None
        if weights is None:
            value = mean_of(values)
        else:
            column_weights = [weights[key] for key, _ in carried]
            value = weighted_mean_of(values, column_weights)
            n_block["effective"] = kish_effective_n(column_weights)
        # A recorded column has a t-interval available, so resampling it is a
        # CHOICE and `statistics.resample` is what makes it — § Statistical
        # reporting's asymmetry between the two `basis: units` rows. A derived
        # metric has no such fallback and is resampled either way, below.
        #
        # The VALUE is unchanged in every branch: § Weighted samples puts the
        # weights "in the estimate rather than in the drawing", and § Clustered
        # units makes the cluster the draw while `n.clusters` still reports the
        # count. Only the construction moves.
        if resample_columns and seed is not None:
            interval = (
                percentile_over_units(
                    values, seed, draws=draws, weights=column_weights
                )
                if clusters is None
                else percentile_over_units_clustered(
                    values, column_keys, clusters, seed, draws=draws,
                    weights=column_weights,
                )
            )
        elif weights is None:
            interval = (
                t_over_units(values)
                if clusters is None
                else t_over_units_clustered(values, column_keys, clusters)
            )
        else:
            interval = (
                weighted_t_over_units(values, column_weights)
                if clusters is None
                else weighted_t_over_units_clustered(
                    values, column_keys, clusters, column_weights
                )
            )
```

  and add the field to the emitted block, **absent** rather than null when no resample is declared:

```python
        out[column] = {
            **(beside_n or {}),
            "value": value,
            "basis": "units",
            "n": n_block,
            "ci95": [interval.low, interval.high] if interval else None,
            "method": interval.method if interval else None,
            "correction": None,
            # Present only under a declared resample, and holding the REQUESTED
            # count: a column's draw statistic is a mean over a non-empty sample
            # and is therefore always defined, so there is no survivor count to
            # differ from it (`percentile_over_units`' own docstring gives the
            # three-branch argument). ABSENT rather than `null` where no
            # resample is declared — `null` already means "resampling was
            # attempted and produced nothing", and reusing it here would
            # reintroduce the ambiguity `resample_draws`' null-versus-0
            # distinction exists to remove.
            **({"resample_draws": draws} if resample_columns and seed is not None else {}),
        }
```

  Append a paragraph to `summarize_step`'s docstring naming `resample_columns`, stating the asymmetry (a column may be resampled; a derived metric always is), and noting that `resample_draws` is absent rather than null when it is `False`.

  (b) `src/publishable/cli.py`: pass `resample_columns=resample_spec["declared"]` at the `summarize_step` call at `:1675`. **Not** at the retry call at `:1703` — that call passes no `derived`, `seed` or `draws` either, and its job is to reproduce the recorded columns unchanged after a derived-key fault; adding a resample there would change a column's construction on the containment path only. Add a comment saying so. Task 15 handles the `report_by` call at `:1984`.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_stats.py -k resample`, `uv run pytest tests/test_cli.py -k percentile_interval or undeclared_resample_shape` (Task 1's pin must still pass), then `uv run pytest`, `uv run mypy`, `uv run ruff check .`.

- [ ] **Step 5: Mutate** — in `stats.py`, change `weights=column_weights` to `weights=None` in the unclustered percentile call. Run `uv run pytest tests/test_stats.py -k weighted_column_keeps_its_weighted_value`. It must FAIL on the interval no longer bracketing the weighted value — which is why that test asserts the weighted and unweighted centres differ on its fixture. Delete `__pycache__`, revert in place. Second mutation: change the emitted field to `"resample_draws": draws` unconditionally (no `**({...})`); Task 1's `test_the_undeclared_resample_shape_is_pinned_absent_key` must FAIL on `"resample_draws" not in column`, and `test_a_recorded_column_takes_a_percentile_interval_under_resample` must FAIL on `"resample_draws" not in plain["pred"]`. Revert in place.

- [ ] **Step 6: Commit** — `feat: a recorded column takes a percentile interval under a declared resample`.

---

## Task 15: Stratum membership from `cli` into `summarize_step`

**Files:** Modify `src/publishable/stats.py`, `src/publishable/cli.py`. Test `tests/test_stats.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `summarize_step(..., resample_columns: bool = False)` (Task 14); `percentile_over_units(..., strata=...)` (Task 9); `percentile_over_units_clustered(..., strata=...)` (Task 10); `cli.command_run`'s `unit_attributes: dict[str, dict[str, Any]]` (built at `cli.py:~1498` as `{u.key: dict(u.attributes) for u in roster if u.attributes}`); `resample_spec["stratify_by"]` (Task 13).
- Produces: `summarize_step(..., strata: dict[str, str] | None = None)` — unit key → that unit's stratum label — threaded from `cli`, and passed through to the `report_by` call site at `cli.py:1984`.

**Aligned to the column's own keys, in one pass.** `summarize_step`'s docstring gives the reason twice, for `weights` and again for `clusters`: "a vector filtered differently weights the wrong unit and produces a plausible number rather than an error", and "the keys the clusters are looked up by are the column's own, taken in the same pass as its values". The stratum vector follows the identical discipline — built as a roster-wide mapping in `cli`, looked up per key from `column_keys` inside `summarize_step`, indexed rather than `.get`-ed so a key the roster does not hold is a core defect rather than a silent extra stratum.

**Several names compose into one label.** `stratify_by: [dx_status, count_stratum]` means the stratum is the **cross**, exactly as `reference.md` § Weighted samples' own example shows. Compose in `cli`, where the attributes live, into a single hashable label; `stats.py` sees one label per unit and never learns how many attributes made it.

**A unit missing one of the attributes.** `strata.levels_for` puts a unit whose attribute is absent or `None` in **no** level, because "there is no honest level for 'we don't know'". A resample cannot drop a unit — the draw is over the completed table and dropping changes `n` silently. So such a unit joins a stratum of its own, labelled from the absence: compose with a sentinel and say so in the code. Assert it, because a fixture with every attribute present cannot see it.

- [ ] **Step 1: Write the failing test** — append to `tests/test_stats.py`:

```python
def test_summarize_step_draws_within_the_strata_it_is_given():
    """The stratified column interval, end of the thread. The fixture is the
    banded one: 20 units in [0,1), 8 in [10,11), 2 in [100,101), so the
    stratified interval is far narrower than the unstratified one and nowhere
    near the mean-of-stratum-means answer."""
    values = (
        [i / 20.0 for i in range(20)]
        + [10.0 + i / 8.0 for i in range(8)]
        + [100.0 + i / 2.0 for i in range(2)]
    )
    collapsed = {f"u{i}": {"pred": v} for i, v in enumerate(values)}
    strata = {f"u{i}": ("low" if i < 20 else "mid" if i < 28 else "high") for i in range(30)}
    counts = {"resolved": 30, "completed": 30, "failed": 0}
    plain = summarize_step(collapsed, counts, seed=7, draws=2000, resample_columns=True)
    drawn = summarize_step(
        collapsed, counts, seed=7, draws=2000, resample_columns=True, strata=strata
    )
    plain_low, plain_high = plain["pred"]["ci95"]
    low, high = drawn["pred"]["ci95"]
    assert (high - low) < (plain_high - plain_low) / 2.0
    assert low < drawn["pred"]["value"] < high
    assert high < 20.0  # not the 37.17 of equal-weighted stratum means


def test_the_stratum_vector_is_aligned_to_the_columns_own_keys():
    """A RAGGED column: only some units carry `late`, and its stratum vector
    must be the subset those units carry, not the whole table's. A vector
    filtered differently draws the wrong composition and produces a plausible
    number rather than an error — the same reason `weights` and `clusters` are
    both looked up per column key."""
    collapsed: dict[str, dict[str, float]] = {}
    for i in range(30):
        row: dict[str, float] = {"early": float(i)}
        if i >= 20:  # only the `high`/`mid` tail carries `late`
            row["late"] = 100.0 + float(i)
        collapsed[f"u{i}"] = row
    strata = {f"u{i}": ("low" if i < 20 else "mid" if i < 28 else "high") for i in range(30)}
    counts = {"resolved": 30, "completed": 30, "failed": 0}
    got = summarize_step(
        collapsed, counts, seed=7, draws=2000, resample_columns=True, strata=strata
    )
    # The ragged column's own `n.completed` is 10, and its interval exists —
    # a whole-table stratum vector would zip against 30 labels and raise.
    assert got["late"]["n"]["completed"] == 10
    assert got["late"]["ci95"] is not None
    assert got["late"]["method"] == "percentile_over_units"
    # The full column is unaffected, so this cannot pass by both being broken.
    assert got["early"]["n"]["completed"] == 30
    assert got["early"]["ci95"] is not None
```

  And append to `tests/test_cli.py`:

```python
def test_a_declared_stratify_by_reaches_the_column_interval(tmp_path, capsys):
    """The thread from `statistics.resample.stratify_by` through
    `unit_attributes` to the draw. `cohort` alternates a/b across 40 units, and
    the step records a `pred` that is banded by cohort, so the stratified
    interval is measurably narrower than the unstratified one — a fixture where
    the two cohorts held the same values could not tell them apart."""
    doc_plain = run_a_project(
        tmp_path / "plain", capsys=capsys, units=40, unit_attributes=["cohort"],
        _starter_step=_COHORT_BANDED_STEP,
        statistics={"correction": "holm", "resample": {"method": "bootstrap", "n": 2000}},
    )
    doc_strat = run_a_project(
        tmp_path / "strat", capsys=capsys, units=40, unit_attributes=["cohort"],
        _starter_step=_COHORT_BANDED_STEP,
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 2000,
                                 "stratify_by": ["cohort"]}},
    )
    def width(doc):
        run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
        metric = run["results"]["conditions"][0]["aggregated"][
            "step01_summarize_units"]["pred"]
        assert metric["method"] == "percentile_over_units"
        low, high = metric["ci95"]
        return high - low
    assert width(doc_strat) < width(doc_plain)


def test_a_unit_missing_a_stratum_attribute_joins_a_stratum_of_its_own(
    tmp_path, capsys
):
    """`strata.levels_for` drops such a unit from every reporting level, because
    "there is no honest level for 'we don't know'". A DRAW cannot drop it — that
    would change `n` silently — so it joins a stratum labelled from the absence.
    Asserted because a fixture with every attribute present cannot see it."""
    roster = "patient_id,cohort,arm\n" + "".join(
        f"p{i}," + ("" if i % 10 == 0 else "a" if i % 2 else "b") + ",x\n"
        for i in range(40)
    )
    doc = run_a_project(
        tmp_path, capsys=capsys, units=40, unit_attributes=["cohort"],
        roster_csv=roster,
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 2000,
                                 "stratify_by": ["cohort"]}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    metric = run["results"]["conditions"][0]["aggregated"][
        "step01_summarize_units"]["pred"]
    # Every completed unit is still in `n` — the draw dropped nobody.
    assert metric["n"]["completed"] == 40
    assert metric["ci95"] is not None
```

  `_COHORT_BANDED_STEP` is a new module-level constant beside `_AGGREGATE_STEP`: a `repeat`-scoped step recording `pred = i / 40` for cohort `a` and `100.0 + i / 40` for cohort `b`, read from `unit.attributes["cohort"]`. It goes through `_starter_step` (added in Task 1), **not** `extra_step_source`, which overrides the source of the *extra* steps `extra_steps` names and leaves the scaffold's own step alone. The two bands must be disjoint, or the stratified and unstratified intervals have the same width and the comparison proves nothing.

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_stats.py -k within_the_strata or aligned_to_the_columns_own_keys -x`. Both fail on the unexpected `strata` keyword.

- [ ] **Step 3: Implement** —

  (a) `src/publishable/stats.py`, `summarize_step`: add `strata: dict[str, str] | None = None`, build the column's own vector inside the per-column pass, and pass it to both percentile constructions:

```python
        # The column's OWN keys, the same one-pass discipline `weights` and
        # `clusters` already follow and for the identical reason the docstring
        # gives twice: a vector filtered or ordered differently draws the wrong
        # composition and produces a plausible number rather than an error.
        # Indexed rather than `.get`-ed — every key in the collapsed table came
        # from the roster the caller built this mapping from, so a default would
        # quietly invent a stratum instead of failing.
        column_strata = None if strata is None else [strata[key] for key, _ in carried]
```

  and thread `strata=column_strata` into both `percentile_over_units` and `percentile_over_units_clustered` calls from Task 14.

  (b) `src/publishable/cli.py`, beside `unit_attributes`:

```python
            # One stratum LABEL per unit, composed once for the run: several
            # declared names mean the stratum is their cross — `reference.md`
            # § Weighted samples' own `stratify_by: [dx_status, count_stratum]`
            # — so the composition happens here, where the attributes live, and
            # `stats.py` sees one label per unit and never learns how many
            # attributes made it.
            #
            # A unit carrying no value for one of the names joins a stratum of
            # its own rather than being dropped. `strata.levels_for` drops such
            # a unit from every REPORTING level, because there is no honest
            # level for "we don't know" — but a DRAW cannot drop it: the draw is
            # over the completed table, and dropping would change `n` silently
            # beneath an interval that claimed the full count. The sentinel is
            # printable rather than a control character: nothing emits a stratum
            # LABEL into `run.yaml` today (Task 17 records the attribute names),
            # but a NUL byte in a string PyYAML is later asked to emit raises,
            # and a printable one costs nothing to choose now.
            resample_strata: dict[str, str] | None = None
            if resample_spec["stratify_by"]:
                resample_strata = {
                    u.key: "|".join(
                        "<absent>" if u.attributes.get(name) is None
                        else str(u.attributes.get(name))
                        for name in resample_spec["stratify_by"]
                    )
                    for u in roster
                }
```

  Pass `strata=resample_strata` at the `summarize_step` call at `:1675` **and** at the `report_by` level call at `:1984`. A level's own table filters the same roster-wide mapping exactly as `weights` and `clusters` already are there — the comment beside those two says why, and the stratum joins them.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_stats.py -k strata`, `uv run pytest tests/test_cli.py -k stratify_by or stratum_attribute`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`.

- [ ] **Step 5: Mutate** — in `stats.py`, change `column_strata` to be built from the whole table rather than the column: `None if strata is None else list(strata.values())`. Run `uv run pytest tests/test_stats.py -k aligned_to_the_columns_own_keys`. It must FAIL — the ragged `late` column has 10 values and would zip against 30 labels, raising `ValueError` from `strict=True`. This is why the fixture is ragged and why a 40-unit fixture where every unit carries the column could not have seen it. Delete `__pycache__`, revert in place. Second mutation: in `cli.py`, change the composition to **drop** units missing a value — `for u in roster if all(u.attributes.get(n) is not None for n in resample_spec["stratify_by"])`. `test_a_unit_missing_a_stratum_attribute_joins_a_stratum_of_its_own` must FAIL with a `KeyError` from `strata[key]` inside `summarize_step`, which is the indexed-rather-than-`.get`-ed guarantee doing its job. Revert in place.

- [ ] **Step 6: Commit** — `feat: thread resample strata from the roster into every column interval`.

---

## Task 16: A column contrast's paired percentile, and the correction pool

**Files:** Modify `src/publishable/cli.py`, `src/publishable/correction.py` (docstrings). Test `tests/test_cli.py`.

**Interfaces:**
- Consumes: `cli._comparison_step_blocks(comp, *, roster, aggregated, collapsed_by_key, derived_by_key, resample_fns_by_key, seed, draws, min_reported_n, findings, where, where_id, conditions_by_index)` at `src/publishable/cli.py:653`, whose column branch is `:816–834` and whose `Member` construction is `:848–866`; `stats.paired_percentile_of_derived(of, against, keys, compute_of, compute_against, seed, draws, confidence) -> PairedResample` at `src/publishable/stats.py:822`; `stats.cohens_dz(diffs)`; `correction.Member`; `correction._corrected_bounds`; `cli._resolved_resample` (Task 13).
- Produces: a column contrast under a declared `resample` carrying `method: paired_percentile_over_units`, `cohens_d: <dz>`, a `Member` with `pool=` and `diffs=None`, and a `ci95_corrected` read off that pool.

**This is the one place H4a can produce a wrong number with a green suite. Two independent ways.**

**(1) The correction pool.** `correction._corrected_bounds` (`src/publishable/correction.py:158`) tests `if member.diffs is not None:` **first**, and only then falls through to `member.pool`. `cli.py:856` sets `diffs=None if is_derived else tuple(diffs)`, so a column contrast **always** carries diffs today. The failure mode is **not** "set both" — `Member.__post_init__` raises `ValueError` for that, loudly and catastrophically (`_compute_vs_baseline` sits outside the `try/except ContractError` around `summarize_step`, so the run would lose `run.yaml` after every execution was spent). The genuinely silent failure is **forgetting the `Member` entirely**: wire the percentile into the interval and leave lines 855–856 alone. The column contrast then carries `diffs` alone, nothing raises, and `ci95` comes from a percentile while `ci95_corrected` comes from `paired_t_over_units` **on the same row**. The rule: under a declared `resample`, a column contrast's `Member` carries the **pool** and sets **`diffs=None`**, while `cohens_dz` keeps computing from the local `diffs` list. `Member`'s own docstring — "exactly one of `pool`/`diffs`" — is what is being **honoured**, not broken.

**The family must be bigger than one or the assertion cannot fail.** At `family_size` 1, holm's level is `0.05` → confidence `0.95` → `interval_at(pool, 0.95)` reads the *same* ranks as the raw interval, so `ci95_corrected == ci95` and a `paired_t_over_units` corrected bound would be indistinguishable from a percentile one only by luck. Size the fixture to **2 comparisons × 1 metric = family 2**, rank 1 → level `0.025` → confidence `0.975` → `min_honest_draws(0.975) = 160`, which `n: 2000` clears. Then assert, **in the same test**: `ci95_corrected` strictly contains `ci95`, **and** does not equal `paired_t_over_units(diffs, confidence=0.975)` recomputed in the test from the deterministic column the step records. That second assertion is the one the mutation kills.

**(2) `col_keys`, not `base_keys`.** The column branch narrows `base_keys → col_keys` on `metric_key in of_collapsed[k] and metric_key in against_collapsed[k]`; the derived branch does not, because a derived metric has no column to be ragged about. `paired_percentile_of_derived` builds its `UnitTable`s from **whole rows**, so handing it `base_keys` for a column metric feeds `compute` rows missing that column. `UnitTable.__getattr__` returns `[row.get(name) for row in rows]` — full length, `None` where absent — so the failure depends entirely on the closure body. **State the closure exactly, then size the fixture against it.** With the body below (`sum(...) / len(...)` over the column), a `None` raises `TypeError`, which `paired_percentile_of_derived` catches as a degenerate draw and drops. **Fixture sizing:** with 1 of 40 units missing the column, ~36 % of draws survive → ~720 ≥ 160 → the interval exists and the test **passes with the bug**. Make roughly a **quarter** of the roster miss it: survival is then ~1e-5 and the interval is `None`. `n_paired` stays `len(col_keys)` and **does not discriminate** — it is already `len(col_keys)` today.

**Three docstring edits this task owes**, because `_corrected_bounds`' own docstring states a guarantee this task falsifies. It currently opens: *"A recorded column re-runs `paired_t_over_units` over the stored per-unit differences — exact at any α."* Under a declared `resample` that stops being true. Leaving it is this repo's single most repeated defect — a comment claiming a guarantee the code does not provide, twelve-plus instances — sitting in the one function whose correctness this task turns on.
1. `_corrected_bounds`: re-scope to say what now decides — a column contrast re-runs the *t* construction **when it carries diffs** and reads the pool **when it carries one**, with the declared `resample` being what puts it in the second case.
2. The paragraph after it. **Keep the "Neither redraws" sentence if it survives** — its reason is good and still holds, and a corrected interval narrower than its raw one is exactly the number this slice must not produce.
3. `Member`'s own docstring ("exactly one of `pool`/`diffs`"): say explicitly that a column contrast under `resample` carries the pool, so a reader meeting `diffs=None` on a column contrast for the first time knows it was deliberate.

**The fixture must vary the column across conditions, or every assertion here is vacuous.** `tests/test_cli.py`'s `_AGGREGATE_STEP` records `pred = float(i)` with no reference to `cfg`, so the per-unit differences are all zero: verified against the build, `paired_t_over_units([0.0] * 40)` returns `Interval(0.0, 0.0)` and `cohens_dz([0.0] * 40)` returns `None`. With an all-zero pool `interval_at` returns `(0.0, 0.0)` at every α, so "corrected is wider than raw" is `0 > 0` — **it fails under the correct implementation and passes under neither**, and the "not the *t* bound" assertion compares two zero-width intervals. This task therefore uses **`_CONDITION_SCALED_STEP`** (introduced in Task 1: `pred = float(i) * {pearson: 1.0, spearman: 2.0, kendall: 3.0}[cfg.parameters.analysis.method]`), which gives both comparisons a nonzero delta and real dispersion in both the diffs and the pool. Check in Step 4 that the family still reads `{comparisons: 2, metrics: 1}` — a comparison whose interval came back `None` is dropped by `family_members` and would shrink it.

**Out of scope, again.** `"paired": True` **stays hard-coded** at both `:808` and `:830`. `cohens_d` stays `null` on the derived branch.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
_RAGGED_COLUMN_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # Scaled by the swept axis for the reason `_CONDITION_SCALED_STEP` is:
        # an identical column under both conditions makes every per-unit
        # difference zero, and a zero-variance contrast asserts nothing.
        scale = {{"pearson": 1.0, "spearman": 2.0, "kendall": 3.0}}[
            cfg.parameters.analysis.method
        ]
        units = list(io.units)
        for i, unit in enumerate(units):
            values = {{"always": float(i) * scale}}
            # A QUARTER of the roster does not carry `sometimes`. Sized that way
            # deliberately: with one unit missing, ~36 % of draws still survive
            # and a `base_keys` bug would produce an interval anyway; at a
            # quarter, survival is ~1e-5 and the interval is null.
            if i % 4 != 0:
                values["sometimes"] = float(i) * 2.0 * scale
            io.record(unit.key, values)
        return {{"n_units": len(units)}}
'''


def test_a_column_contrast_takes_the_paired_percentile_under_resample(tmp_path, capsys):
    """§ Statistical reporting: `paired_percentile_over_units` is "Every derived
    metric, and a column metric under `resample`". Cohen's dz survives — it
    differences a per-unit value, which a column has.

    `_CONDITION_SCALED_STEP`, not `aggregate_returns`: an identical column under
    both conditions gives zero differences, and `cohens_dz` of those is `None`,
    so `cohens_d is not None` would fail under the correct implementation."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=40,
        _starter_step=_CONDITION_SCALED_STEP,
        sweep={"baseline": {"analysis.method": "pearson"},
               "grid": {"analysis.method": ["spearman"]}},
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 2000}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _named_contrast(run, "method=spearman", "pred")
    assert entry is not None
    assert entry["method"] == "paired_percentile_over_units"
    assert entry["cohens_d"] is not None      # a column HAS a per-unit value
    assert entry["paired"] is True            # still hard-coded; H4c owns it
    assert entry["ci95"] is not None


def test_a_column_contrast_corrects_off_its_own_pool_not_a_t_interval(
    tmp_path, capsys
):
    """THE test this task exists for. `_corrected_bounds` tests
    `member.diffs is not None` FIRST, so a `Member` still carrying diffs yields
    `ci95` from a percentile and `ci95_corrected` from `paired_t_over_units` on
    the same row — nothing raises, and no other test sees it.

    Two comparisons, so `family_size` is 2 × 1 = 2 and holm's rank-1 level is
    0.025 → confidence 0.975 → 160 draws needed, which 2000 clears. At
    `family_size` 1 the level is 0.05, `interval_at` reads the SAME ranks as the
    raw interval, and this assertion could not fail."""
    import math

    from publishable.stats import paired_t_over_units

    doc = run_a_project(
        tmp_path, capsys=capsys, units=40,
        _starter_step=_CONDITION_SCALED_STEP,
        sweep={"baseline": {"analysis.method": "pearson"},
               "grid": {"analysis.method": ["spearman", "kendall"]}},
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 2000}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _named_contrast(run, "method=spearman", "pred")
    assert entry is not None
    # Both comparisons carry an interval — `family_members` drops one with
    # `ci95: None`, which would shrink this to 1 and quietly weaken every
    # assertion below by loosening the corrected level from 0.025 to 0.05.
    assert entry["family_size"] == 2
    assert entry["family"] == {"comparisons": 2, "metrics": 1}
    assert entry["method"] == "paired_percentile_over_units"
    raw_low, raw_high = entry["ci95"]
    corr_low, corr_high = entry["ci95_corrected"]
    # A corrected interval is at a SMALLER alpha off the same evidence, so it
    # contains the raw one. Never narrower — that is the number a reader cannot
    # tell is wrong. Strictly wider is assertable only because
    # `_CONDITION_SCALED_STEP` gives the pool real dispersion: over an
    # all-zero pool `interval_at` returns (0.0, 0.0) at every alpha and this
    # would be `0 > 0`, failing under the CORRECT implementation.
    assert corr_low <= raw_low and corr_high >= raw_high
    assert (corr_high - corr_low) > (raw_high - raw_low)
    # And it is NOT the t-interval. Recompute the bound the buggy path would
    # have produced, from the same per-unit differences the step's own scaling
    # determines — `pred` is `float(i)` at pearson and `2 * float(i)` at
    # spearman, so the difference for unit `i` is exactly `float(i)`.
    level = 0.05 / entry["family_size"]
    diffs = [float(i) for i in range(40)]
    t_bound = paired_t_over_units(diffs, confidence=1.0 - level)
    assert t_bound is not None      # non-degenerate, unlike an all-zero column
    assert not (
        math.isclose(corr_low, t_bound.low) and math.isclose(corr_high, t_bound.high)
    )


def test_a_column_contrast_draws_from_the_columns_own_keys(tmp_path, capsys):
    """`paired_percentile_of_derived` builds its `UnitTable`s from WHOLE ROWS, so
    `base_keys` feeds `compute` rows missing the column — `UnitTable.__getattr__`
    pads with `None`, and the closure's `sum(...)` raises `TypeError`, which the
    construction catches as a degenerate draw and drops. A quarter of the roster
    missing makes survival ~1e-5, so the interval is null under the bug and real
    under the fix. One unit missing would leave ~720 survivors and pass either
    way."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=40,
        sweep={"baseline": {"analysis.method": "pearson"},
               "grid": {"analysis.method": ["spearman"]}},
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 2000}},
        _starter_step=_RAGGED_COLUMN_STEP,
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    ragged = _named_contrast(run, "method=spearman", "sometimes")
    assert ragged is not None
    assert ragged["method"] == "paired_percentile_over_units"
    assert ragged["ci95"] is not None
    assert ragged["n_paired"] == 30           # 40 units, every 4th missing
    # The full column is unaffected, so this cannot pass by both being broken.
    full = _named_contrast(run, "method=spearman", "always")
    assert full is not None
    assert full["ci95"] is not None
    assert full["n_paired"] == 40
```

  `_starter_step` and `_CONDITION_SCALED_STEP` both come from Task 1 and need no new work here.

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k column_contrast -x`. All three fail: the method is `paired_t_over_units` today and there is no pool for `_corrected_bounds` to read.

- [ ] **Step 3: Implement** —

  (a) `src/publishable/cli.py`, `_comparison_step_blocks`: add a `resample_columns: bool` keyword parameter (passed by `_compute_vs_baseline` and `_compute_declared_contrasts`, which each gain the same parameter, from `command_run`'s `resample_spec["declared"]`). Replace the column branch at `:816–834`:

```python
            else:
                col_keys = [
                    k
                    for k in base_keys
                    if metric_key in of_collapsed[k] and metric_key in against_collapsed[k]
                ]
                diffs = [
                    of_collapsed[k][metric_key] - against_collapsed[k][metric_key]
                    for k in col_keys
                ]
                n_paired = len(col_keys)
                resampled = None
                if resample_columns and n_paired >= 2:
                    # `col_keys`, NOT `base_keys`. The derived branch above uses
                    # `base_keys` because a derived metric has no column to be
                    # ragged about; a recorded column does.
                    # `paired_percentile_of_derived` builds its `UnitTable`s from
                    # whole rows, so `base_keys` here would feed `compute` rows
                    # missing this column — `UnitTable.__getattr__` pads with
                    # `None` and the mean below raises, which the construction
                    # catches as a degenerate draw and silently drops. A quarter
                    # of a roster missing the column nulls the interval; one unit
                    # missing leaves it looking fine, which is why this is a
                    # correctness rule and not a tidiness one.
                    #
                    # The same callable twice: both sides compute the mean of the
                    # same column, which is a normal call rather than the
                    # shared-closure cancellation `paired_percentile_of_derived`
                    # warns about — that one is about a SWEPT AXIS changing which
                    # formula `aggregate` runs, and a column mean is one formula.
                    def _column_mean(table: UnitTable, _name: str = metric_key) -> float:
                        column = getattr(table, _name)
                        return sum(column) / len(column)

                    resampled = paired_percentile_of_derived(
                        of_collapsed,
                        against_collapsed,
                        col_keys,
                        _column_mean,
                        _column_mean,
                        seed,
                        draws=draws,
                    )
                    interval = resampled.interval
                else:
                    interval = paired_t_over_units(diffs)
                metric_block[metric_key] = {
                    # The mean of the per-unit differences over `col_keys` — the
                    # same unit set the interval is drawn from, and identical to
                    # the difference of the two column means over that set, so
                    # the point estimate and the pool cannot drift onto
                    # different rosters.
                    "delta": mean_of(diffs),
                    "basis": "units",
                    "paired": True,
                    "method": interval.method if interval else None,
                    "n_paired": n_paired,
                    "ci95": [interval.low, interval.high] if interval else None,
                    # Cohen's dz survives the switch: it differences a PER-UNIT
                    # value, which a column has and a derived metric does not,
                    # and it is computed from the local `diffs` list rather than
                    # from anything the `Member` carries.
                    "cohens_d": cohens_dz(diffs),
                    "correction": None,
                }
```

  and the `Member` construction at `:848–866`:

```python
            # `Member` requires exactly one of `pool`/`diffs` wherever there is
            # an interval to correct: the draws a percentile interval was read
            # off, or the per-unit differences a *t* interval was computed from.
            #
            # **A column contrast under a declared `resample` carries the POOL
            # and sets `diffs=None`.** `_corrected_bounds` tests `diffs` FIRST
            # and only then falls through to `pool`, so leaving `diffs` set here
            # — the natural thing to do, since `cohens_dz` still needs them —
            # would give this row a `ci95` from a percentile and a
            # `ci95_corrected` from `paired_t_over_units`. Nothing raises and no
            # reader can tell. `cohens_dz` is computed above from the local list,
            # which is why the `Member` does not need it.
            corrected_from_pool = is_derived or resample_columns
            members.append(
                Member(
                    where=where_id,
                    step=step_name,
                    metric=metric_key,
                    delta=metric_block[metric_key]["delta"] or 0.0,
                    ci95=(interval.low, interval.high) if interval else None,
                    pool=tuple(resampled.pool) if corrected_from_pool and resampled else None,
                    diffs=None if corrected_from_pool else tuple(diffs),
                    declaration_index=0,
                )
            )
```

  Note that `resampled` is now assigned in **both** branches of `is_derived`, so the "reset per metric" comment at `:781–787` still applies and must be kept — it is what stops a later metric inheriting an earlier one's pool.

  (b) `src/publishable/correction.py`, `_corrected_bounds`'s docstring — replace the first paragraph:

```
    """The interval at `level`, from the same evidence as the raw one.

    **What decides the construction is which field the member carries, not what
    kind of metric it is.** A member carrying per-unit differences re-runs
    `paired_t_over_units` over them — exact at any α. A member carrying a draw
    pool reads a second rank pair off it. A derived metric always carries a
    pool; a recorded column carries differences by default and **carries a pool
    instead under a declared `statistics.resample`**, because its raw interval
    was then a percentile and a *t* corrected bound would be its counterpart in
    name only — narrower or wider than the truth by construction rather than by
    evidence. `Member.__post_init__` enforces exactly one of the two, so this
    order is a preference among impossible-to-have-both fields rather than a
    tie-break.

    Neither redraws: a fresh resample at the corrected level could land *inside*
    the raw interval, and a corrected interval narrower than its raw one is
    precisely the number a reader cannot tell is wrong.
    """
```

  (c) `src/publishable/correction.py`, `Member`'s docstring — extend the "Exactly one of them is set" sentence:

```
    `pool` and `diffs` are how the corrected interval is built from the *same*
    evidence as the raw one — the stored draws for a percentile interval, the
    stored per-unit differences for a *t* one. Exactly one of them is set.
    **A recorded column carries `diffs` by default and `pool` under a declared
    `statistics.resample`**, which is what makes a percentile raw interval and a
    percentile corrected one the same construction; a reader meeting
    `diffs=None` on a column contrast is meeting that, not an omission. Cohen's
    *dz* is computed at the call site from its own list and does not travel here.
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_cli.py -k column_contrast or undeclared_resample_shape`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`. Then **measure the rebuild cost**, which the scoping asks for: `paired_percentile_of_derived` builds two `UnitTable`s of *n* rows **per draw**, currently paid by one or two derived metrics and now by every recorded column × every comparison. Run a throwaway timing probe in the scratchpad:

```python
import time
from publishable.stats import paired_percentile_of_derived
of = {f"u{i}": {"m": float(i)} for i in range(240)}
against = {f"u{i}": {"m": float(i) * 1.1} for i in range(240)}
keys = list(of)
def mean_m(t): return sum(t.m) / len(t)
start = time.perf_counter()
paired_percentile_of_derived(of, against, keys, mean_m, mean_m, 1, draws=2000)
print(f"{time.perf_counter() - start:.2f}s per column-comparison at n=240, 2000 draws")
```

  Record the number in the commit message. If it exceeds ~2 s per column-comparison, write the cheap direct construction instead — draw index vectors once and take column means, skipping `UnitTable` entirely — and say so; the pool it returns must still be the sorted list of differences `interval_at` reads ranks off.

- [ ] **Step 5: Mutate** — the mutation is **forgetting the `Member`**, which is the silent failure and not the loud one. In `cli.py`, change `corrected_from_pool = is_derived or resample_columns` back to `corrected_from_pool = is_derived`. Run `uv run pytest tests/test_cli.py -k corrects_off_its_own_pool`. It must FAIL — the row keeps `diffs`, `_corrected_bounds` takes the *t* branch, and both the containment assertion and the not-equal-to-the-t-bound assertion break. Do **not** mutate by setting both fields: `Member.__post_init__` raises `ValueError` for that, the run loses `run.yaml`, and the test fails for a reason that proves nothing about the assertion. Delete `__pycache__`, edit the line back in place, re-run. Second mutation: change `col_keys` to `base_keys` in the `paired_percentile_of_derived` call. `test_a_column_contrast_draws_from_the_columns_own_keys` must FAIL on `ragged["ci95"] is not None` while `full` still passes — which is the whole reason the fixture carries both a full and a quarter-missing column. Revert in place.

- [ ] **Step 6: Commit** — `feat: a column contrast resamples over its own keys and corrects off its own pool` (include the timing figure).

---

## Task 17: Echo the resolved `method`/`n`/`stratify_by` into `run.yaml`

**Files:** Modify `src/publishable/cli.py`, `docs/reference.md`. Test `tests/test_cli.py`.

**Interfaces:**
- Consumes: `cli.command_run`'s `resample_spec` (Task 13); the `beside_n` parameter of `stats.summarize_step`, documented at `src/publishable/stats.py:1220` as "core-supplied context copied verbatim into every metric block"; the locals `cond_beside_n` and `weighted_beside` in `command_run`.
- Produces: a `resample: {method, n, stratify_by}` sibling of `n` in every metric block of a run that declared one.

**Why `beside_n` is the right carrier and not a new one.** `summarize_step`'s docstring states the rule: a key that **joins** `n` travels in `counts` (`clusters`, `effective`, `ineligible`); a key that **sits beside** `n` travels in `beside_n`, and § Weighted samples' `weighted_by` is the precedent — a key that names a declaration rather than reporting a figure. `reference.md` § Statistical reporting requires "the resolved values are recorded in `run.yaml` beside the interval so the number is never the result of an undocumented default", which is the same position. Adding a second mechanism for the same sentence is how two spellings of one construction drift apart.

**`resample.n` is what was requested; `resample_draws` is what the interval rests on.** For a column they are equal by Task 11's invariant. For a derived metric they differ whenever a draw was degenerate, and that difference is exactly what `W-STATS-RESAMPLE-THIN` reports. Both keys are therefore meaningful and neither replaces the other.

**Absent, not null, when nothing was declared.** Task 1's pin asserts the undeclared shape, and an explicit `resample: null` in a metric block would claim a resolution was performed.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
def test_the_resolved_resample_is_recorded_beside_every_interval(tmp_path, capsys):
    """§ Statistical reporting: "the resolved values are recorded in `run.yaml`
    beside the interval so the number is never the result of an undocumented
    default". Carried on `beside_n`, the documented route for a key that sits
    beside `n` rather than joining it — the same position `weighted_by` takes."""
    doc = run_a_project(
        tmp_path, capsys=capsys, aggregate_returns="mean_pred", units=40,
        unit_attributes=["cohort"],
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 500,
                                 "stratify_by": ["cohort"]}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    for name in ("pred", "mean_pred"):
        assert aggregated[name]["resample"] == {
            "method": "bootstrap", "n": 500, "stratify_by": ["cohort"]
        }
    # `n` is what was REQUESTED; `resample_draws` is what the interval rests on.
    # Equal for a column by construction, and equal here for the derived metric
    # because no draw was degenerate — but they are different facts and both are
    # recorded.
    assert aggregated["pred"]["resample_draws"] == 500
    assert aggregated["mean_pred"]["resample_draws"] == 500


def test_no_resample_block_is_recorded_when_none_was_declared(tmp_path, capsys):
    """Absent, not null: an explicit null would claim a resolution was performed.
    Paired with a positive assertion in the same test so it cannot pass by
    nothing having run."""
    doc = run_a_project(
        tmp_path, capsys=capsys, aggregate_returns="mean_pred", units=40
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    assert "resample" not in aggregated["pred"]
    assert "resample" not in aggregated["mean_pred"]
    # The positive companion: the derived metric IS still resampled at the
    # documented default, so the block really did run.
    assert aggregated["mean_pred"]["resample_draws"] == 2000
    assert aggregated["mean_pred"]["method"] == "percentile_over_units"
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k resolved_resample_is_recorded -x`. Fails on the missing `resample` key; the second test passes and is the control.

- [ ] **Step 3: Implement** — in `src/publishable/cli.py`, where `cond_beside_n` and `weighted_beside` are built, merge in:

```python
            # The resolved block, beside the interval rather than joining `n` —
            # `summarize_step`'s own rule for which carrier a fact takes, and
            # `weighted_by` is the precedent: a key that names a declaration
            # rather than reporting a figure. § Statistical reporting requires
            # it be recorded "so the number is never the result of an
            # undocumented default".
            #
            # ABSENT when nothing was declared, not null: a null would claim a
            # resolution was performed. `stratify_by` is materialized as a list
            # even where the config wrote a bare string, because the record
            # resolves what the config abbreviates — the same rule `of`/`against`
            # follow in `results.contrasts`.
            #
            # `n` here is what was REQUESTED; `resample_draws` beside it is what
            # the interval rests on. Equal for a column by construction and
            # different for a derived metric whenever a draw was degenerate,
            # which is what `W-STATS-RESAMPLE-THIN` reports.
            resample_beside = (
                {
                    "resample": {
                        "method": resample_spec["method"],
                        "n": resample_spec["n"],
                        "stratify_by": list(resample_spec["stratify_by"]),
                    }
                }
                if resample_spec["declared"]
                else {}
            )
```

  and add `**resample_beside` to both `cond_beside_n` and `weighted_beside`. `weighted_beside` is what the `report_by` level call uses, so a level block carries the declaration too — correct, because the declaration is true of the run either way, the same argument the code already makes for `weighted_by` there.

  (b) `docs/reference.md`: extend the `run.yaml` metric-block example in § What isn't a repeat (the one carrying `resample_draws: 2000`) with the sibling, and say in § Statistical reporting which key is which:

```yaml
r:
  value: 0.607
  basis: units                                 # what the interval is over
  n: {resolved: 240, completed: 228, failed: 12}
  technical_n: {min: 2, max: 3, median: 3}     # collapsed, shown for transparency
  repeat_spread: {std: 0.014, n: 5, kind: seed}   # how much the pipeline moved
  ci95: [0.517, 0.683]
  method: percentile_over_units
  resample_draws: 2000                         # how many draws the interval rests on
```

  **Do not change any number in that block** — it is the shared worked example, and `CLAUDE.md` § The worked example says those intervals were checked numerically against a synthetic 228-unit table and must not be narrowed. Add the `resample:` sibling only in a **second**, clearly-labelled example showing a declared resample, so the worked example's config (which declares none) stays consistent with it.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_cli.py -k resample`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`. Then the cross-document pass: § Config completeness (no new config field was added, so nothing moves), § Schema fields in prose (the new `resample` record key must appear in a `run.yaml` example and in prose), and the worked example's numbers unchanged — `grep -n '0.517, 0.683\|−0.007, 0.059\|0.014' docs/reference.md README.md docs/design-principles.md` must return what it returned before.

- [ ] **Step 5: Mutate** — in `cli.py`, drop the `if resample_spec["declared"]` guard so the block is emitted unconditionally. Run `uv run pytest tests/test_cli.py -k no_resample_block_is_recorded`. It must FAIL. Delete `__pycache__`, restore the guard in place, re-run. Second mutation: change `"stratify_by": list(resample_spec["stratify_by"])` to `"stratify_by": []`; `test_the_resolved_resample_is_recorded_beside_every_interval` must FAIL. Revert in place.

- [ ] **Step 6: Commit** — `feat: record the resolved resample beside every interval`.

---

## Task 18: `report_by` levels resample without minting `Member`s, and a `summary` `Estimate` is never recomputed

**Files:** Test only — `tests/test_cli.py`. No `src/` change expected.

**Interfaces:**
- Consumes: `cli.command_run`'s `report_by` block at `src/publishable/cli.py:1832–2000`, whose `summarize_step` call is at `:1984`; `cli._comparison_step_blocks`'s per-metric loop at `:766`, which iterates `sorted((set(of_summary) & set(against_summary)) - {"by"})`; `run_record.summary_values` at `src/publishable/run_record.py:58`.
- Produces: two assertions that keep two properties holding once levels start carrying percentile intervals. **Verify-and-pin, not a build.**

**Property 1, already true.** `Member`s are constructed in exactly one place — `_comparison_step_blocks`' per-metric loop — which explicitly excludes the `by` key, where the whole `report_by` block lives, with a comment saying why. So a `report_by` level never constructs a `Member` and never joins the correction family. Task 15 threads `strata` into that call site and Task 17 threads the declaration, so H4a touches this code whether or not it claims anything here.

**Property 2, a boundary this slice owes rather than merely respects.** A `summary`-step `Estimate` is `reported: true`, sits outside the correction family, and is never recomputed. Task 14's pass walks every metric block, so the test is owed. It is **structural**: an `Estimate` reaches `run.yaml` through `run_record.summary_values` into `results.summary`, never through `summarize_step`.

**Both are absence assertions and both need positive companions in the same test.** "A `report_by` level mints no `Member`s" and "an `Estimate` is never recomputed" pass identically if nothing ran. The companions: the level **did** produce a percentile interval; the `Estimate` **is** still present with its `ci95` and `method` unchanged, beside a column in the same run that **did** take `method: percentile_over_units`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
def test_a_report_by_level_resamples_without_joining_the_correction_family(
    tmp_path, capsys
):
    """`Member`s are built in one place, `_comparison_step_blocks`' per-metric
    loop, which excludes the `by` key the whole strata block lives under. That
    property already holds; this keeps it holding now that levels carry
    percentile intervals.

    The absence assertion has a positive companion IN THE SAME TEST: the level
    genuinely produced an interval, so the test cannot pass by nothing having
    been stratified. And `family` is asserted to the exact shape a
    strata-free run would have, so a level joining the family shows up as an
    inflated metric count rather than as a silence."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=40, unit_attributes=["cohort"],
        sweep={"baseline": {"analysis.method": "pearson"},
               "grid": {"analysis.method": ["spearman"]}},
        statistics={"correction": "holm", "report_by": ["cohort"],
                    "resample": {"method": "bootstrap", "n": 2000}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    # Positive companion: the level exists and carries a real percentile
    # interval, drawn over its own units.
    level = aggregated["by"]["cohort"]["a"]["pred"]
    assert level["method"] == "percentile_over_units"
    assert level["ci95"] is not None
    assert level["n"]["completed"] < aggregated["pred"]["n"]["completed"]
    # The absence: one comparison, one metric — `pred`. The `by` key is not a
    # metric and neither are its levels, so the family stays 1 × 1.
    entry = _named_contrast(run, "method=spearman", "pred")
    assert entry["family"] == {"comparisons": 1, "metrics": 1}
    assert entry["family_size"] == 1
    # And there is no contrast entry for `by` at all.
    for condition in run["results"]["conditions"]:
        for step_block in condition.get("vs_baseline", {}).values():
            assert "by" not in step_block


_SUMMARY_ESTIMATE_STEP = '''\
# src/{pkg}/steps/{step_name}.py — generated, and runnable as-is
from publishable import BaseStep, Estimate


class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        return {{
            "site_adjusted_delta": Estimate(
                value=0.041, ci95=[0.012, 0.070], n=228, method="mixed_model"
            ),
            "converged": True,
        }}
'''


def test_a_summary_estimate_is_not_recomputed_by_the_resample_pass(tmp_path, capsys):
    """A `summary`-step `Estimate` is `reported: true`, outside the correction
    family, and never recomputed — and H4a's column pass walks every metric
    block, so this is a boundary the slice OWES a test for rather than one it
    merely respects. Structural: an `Estimate` reaches `results.summary` through
    `run_record.summary_values`, never through `summarize_step`.

    The positive companion is in the same test: a recorded column in the same
    run DID take a percentile interval, so this cannot pass by the resample
    having done nothing at all."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=40,
        extra_steps=["step02_report"],
        extra_step_source=_SUMMARY_ESTIMATE_STEP,
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 2000}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    estimate = run["results"]["summary"]["step02_report"]["site_adjusted_delta"]
    assert estimate == {
        "value": 0.041,
        "reported": True,
        "ci95": [0.012, 0.070],
        "n": 228,
        "method": "mixed_model",
    }
    # Nothing the resample pass writes has been added to it.
    assert "resample_draws" not in estimate
    assert "resample" not in estimate
    assert "basis" not in estimate
    assert "correction" not in estimate
    # The non-Estimate return is untouched too.
    assert run["results"]["summary"]["step02_report"]["converged"] is True
    # Positive companion: a column in the same run IS resampled.
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    assert aggregated["pred"]["method"] == "percentile_over_units"
    assert aggregated["pred"]["resample"]["n"] == 2000
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k report_by_level_resamples or summary_estimate_is_not_recomputed -x`. Both are expected to **pass immediately**: they pin properties that already hold. If either fails, a preceding task broke a boundary — stop and fix the task that did, not the test.

- [ ] **Step 3: Implement** — no `src/` change. If `test_a_report_by_level_resamples_without_joining_the_correction_family` fails on the level's `method`, Task 15 did not thread `resample_columns`/`strata` into the `:1984` call site; fix it there.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_cli.py -k report_by or summary_estimate`, then `uv run pytest`.

- [ ] **Step 5: Mutate** — in `src/publishable/cli.py`, remove `- {"by"}` from `_comparison_step_blocks`' metric loop, so it reads `sorted(set(of_summary) & set(against_summary))`. Run `uv run pytest tests/test_cli.py -k report_by_level_resamples`. It must FAIL on `entry["family"] == {"comparisons": 1, "metrics": 1}` — the metric count becomes 2 — which is why the family shape is asserted to an exact value rather than merely checked non-empty. Delete `__pycache__`, restore `- {"by"}` in place, re-run. Second mutation: in `src/publishable/run_record.py`, add `"basis": "units"` to the dict `summary_values` builds for an `Estimate`. `test_a_summary_estimate_is_not_recomputed_by_the_resample_pass` must FAIL on the exact-equality assertion. Revert in place.

- [ ] **Step 6: Commit** — `test: pin that strata mint no Members and a summary Estimate is never recomputed`.

---

## Task 19: The `init`-materializes-optional-blocks residual

**Files:** Modify `docs/superpowers/spec-defects.md`. Possibly `src/publishable/materialize.py` and `docs/reference.md` — see the ruling below.

**Interfaces:**
- Consumes: the open entry in `docs/superpowers/spec-defects.md` under *"The generated config calls itself 'the complete parameter set' before it is one"*, whose **Open residual, routed** paragraph reads: "whether `init` should materialize the optional `statistics` sub-blocks at all is a design decision, not a reconciliation, and is left open. **Owner: H4 Statistics** (it owns `resample` and `null_test`, the last two that are refused; whatever it decides for those settles the shape for `contrasts` and `report_by` too)."
- Produces: a **closed** entry — a ruling with its grounds, so the residue is a decision rather than a silence.

**The ruling this plan makes, and the argument for it.** `init` should **not** materialize `statistics.resample`. Grounds, in the order they bind:

1. **`parameter_spec` is the single source of truth for what `init` writes**, and `resample` is not a parameter — it is a `statistics` block, and `materialize.py` writes exactly two `statistics`-adjacent keys today (`correction: holm` and a top-level `hypotheses: []`).
2. **The two documents already disagree in this direction and `reference.md` resolves it**: § The one config file says its fenced example is "the complete config *schema*, which is a wider thing than the literal output of `init`; a materialized file that does not carry them is not an incomplete config", and that for `contrasts` and `report_by` "declaring one by hand is how a run asks for it, and `validate` accepts the key whether or not `init` wrote it". `resample` inherits that sentence.
3. **Writing it would change behaviour, not just text.** A materialized `resample: {method: bootstrap, n: 2000}` is a **declared** resample under Task 13's `declared` flag, so every generated project would turn every recorded column into a percentile interval by default — reversing § Statistical reporting's stated asymmetry ("a column metric has a t-interval available, so resampling it is a *choice*, and `resample` is what makes it"). A materialized `resample: null` would be inert but would then need its own inline comment and would tempt the `.get("resample", DEFAULT)` reading Task 13 forbids.

So: **no `materialize.py` change, no `reference.md` change**, and the entry closes on the third argument, which is the one only this slice could make.

- [ ] **Step 1: Write the failing test** — the check is a grep and an existing test, run in Step 2:

```bash
cd /Users/joon/src/tries/publishable
grep -n 'resample\|null_test' src/publishable/materialize.py   # must print nothing
uv run pytest tests/test_materialize.py -q
```

- [ ] **Step 2: Run it, confirm it fails** — the grep prints nothing today, which is the state the ruling preserves; `tests/test_materialize.py` passes. **This task's deliverable is the written ruling, not a behaviour change** — so "confirm it fails" here means confirming that the `spec-defects.md` entry is still open and still says "left open. Owner: H4 Statistics": `grep -n 'Owner: H4 Statistics' docs/superpowers/spec-defects.md`.

- [ ] **Step 3: Implement** — in `docs/superpowers/spec-defects.md`, replace the **Open residual, routed** paragraph under *"The generated config calls itself 'the complete parameter set' before it is one"* with:

```markdown
**Residual — CLOSED by H4a (2026-08-15).** Whether `init` should materialize the optional
`statistics` sub-blocks: **no.** Three grounds, in the order they bind.

1. `parameter_spec` is the single source of truth for what `init` writes, and none of these is a
   parameter. `materialize.py` writes `statistics.correction` and a top-level `hypotheses: []`
   and nothing else under `statistics`.
2. `reference.md` § The one config file already resolves it for `contrasts` and `report_by` —
   its fenced example is "the complete config *schema*, which is a wider thing than the literal
   output of `init`; a materialized file that does not carry them is not an incomplete config" —
   and `resample` and `null_test` inherit that sentence rather than needing their own.
3. **The argument only this slice could make:** now that `resample` is honored, a materialized
   `resample: {method: bootstrap, n: 2000}` would be a *declared* resample, so every generated
   project would give every recorded column a percentile interval by default — reversing
   § Statistical reporting's asymmetry, which is that a column has a t-interval available so
   resampling it is a **choice** and `resample` is what makes it. A materialized `resample: null`
   would be inert but would need its own inline comment and would invite the
   `.get("resample", DEFAULT)` reading that separates the absent key from the explicit null.

No `materialize.py` change and no `reference.md` change. Recorded so the absence is a decision.
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest`, then re-run both greps from Step 1 and confirm `grep -n 'left open' docs/superpowers/spec-defects.md` no longer matches this entry. Then the mechanical pass on `spec-defects.md`: no trailing whitespace, no tab, table rows intact, every `#anchor` resolvable.

- [ ] **Step 5: Mutate** — add `"  resample: {method: bootstrap, n: 2000}",` to `materialize.py`'s `statistics:` block. Run `uv run pytest tests/test_cli.py -k undeclared_resample_shape`. **Both of Task 1's pins must FAIL** — every generated project now declares a resample, so `column["method"]` becomes `percentile_over_units` and `"resample_draws" not in column` breaks. That is the empirical demonstration of ground 3, and it is why this task's ruling is a behaviour argument rather than a stylistic one. Note the failure in the commit message. Delete `__pycache__`, remove the line in place, re-run.

- [ ] **Step 6: Commit** — `docs: close the init-materializes-optional-blocks residual — no, and here is the behaviour argument`.

---

## Sequencing

Execute in the order above. The order is not free — four constraints bind it, and three of them are not in the spec's own sequencing note.

1. **Task 1 first, absolutely.** It is the only baseline anything later can be compared against. Once Task 14 wires `percentile_over_units` into `summarize_step`'s column branch there is nothing left to compare against, and once Task 13 replaces the literal `2000` there is nothing left to detect a silently changed draw count.
2. **Tasks 4–8 (every `validate` refusal) before Task 12 (the retirement), and Task 12 before Task 13.** Validate-before-honour, inside the slice: the `n >= 80` floor and the no-roster refusal must exist before a declared `resample` can reach a run, or the first `resample: {n: 50}` gets a run whose every interval is `null` with no diagnostic, and a `resample` with no roster validates clean and does nothing.
3. **Task 12 before Tasks 13–18** — a constraint the spec's task list does not state. `cli` always validates before running, and an error exits before a run directory exists, so **every end-to-end test from Task 13 onward is impossible while `E-STATS-RESAMPLE-UNSUPPORTED` still fires.** Placing the retirement at 12 makes the silent-no-op window exactly two tasks wide (12→14, during which a declared resample changes only the derived draw count) — the narrowest available, since retiring earlier widens it to five and retiring later makes Tasks 13–14 untestable.
4. **Tasks 9–11 (the `stats.py` constructions) before Tasks 14–16 (the wiring).** They are pure and unit-testable with no run behind them, so they can land inside the pre-retirement window and shorten it.

Task 3 must precede Tasks 4–8 (they read values whose type the envelope now backstops). Task 2 must precede Task 4 (the enum it enforces is minted there). Task 15 must precede Task 16 only in that both touch `cli.command_run`'s locals; they are otherwise independent. Task 17 must follow Task 13 (it reads `resample_spec`) and Task 15 (it merges into the same `beside_n` locals). Task 18 must be **last but one**, because it pins properties every earlier task could have broken. Task 19 is documentation and may land any time after Task 13, whose `declared` flag its argument rests on.

**After the final task**, re-run the full suite plus every check: `uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy`, then `grep -rln 'E-STATS-RESAMPLE-UNSUPPORTED' src/ docs/ tests/` (only the absence test may match), then `grep -rn p_value src/` (must be empty), then the worked example's numbers: `grep -n '0.488, 0.661\|0.517, 0.683\|0.347, 0.477\|−0.007, 0.059\|−0.213, −0.125\|0.014' docs/reference.md README.md docs/design-principles.md` must return exactly what it returned at `eaf3605`.

## Where this slice will be attacked

**The acceptance property: a config that declares nothing produces byte-identical output to a run at `eaf3605`, and a config that declares `statistics.resample` gets the method, the count and the strata it asked for — on every recorded column, every column contrast, every cluster, and every reporting stratum — with the corrected interval read off the same evidence as the raw one.**

The four places a reviewer will press, in the order they are likely to find something:

1. **The corrected interval of a column contrast under `resample`.** Task 16. `_corrected_bounds` tests `diffs` first; a `Member` that keeps them yields `ci95` from a percentile and `ci95_corrected` from `paired_t_over_units` on the same row, and nothing raises. The defence is the family-of-2 fixture (level 0.025, 160 draws needed, 2000 supplied) with both a containment assertion **and** an assertion the corrected bound is not the *t* bound — because at family size 1 the two coincide and the test could not fail. A reviewer should apply the mutation `corrected_from_pool = is_derived` and confirm the test dies.

2. **The key set a column contrast resamples over.** Task 16. `base_keys` for a ragged column feeds `compute` rows the column is missing from, and `UnitTable.__getattr__` pads with `None` rather than raising, so whether the bug is loud depends on the closure body. The defence is a fixture where a **quarter** of the roster misses the column — at one unit missing, ~720 of 2000 draws survive and the bug produces a plausible interval.

3. **The undeclared path.** Tasks 1 and 13. The absent `resample` key and an explicit `resample: null` are different documents that must resolve to one answer, and `run_a_project`'s `doc.update` makes it easy to pin a baseline the test itself changed by dropping `correction: holm`. The defence is two separate pins, each asserting `correction_level`, `family_size` and `family`.

4. **The stratified draw's arithmetic.** Tasks 9, 10 and 15. Three constructions produce three plausible numbers — the correct within-stratum draw, an unstratified draw, and an equal-weighting of stratum means — and a fixture with two equal strata separates none of them. The defence is the banded fixture (20/8/2 units in `[0,1)`, `[10,11)`, `[100,101)`; clusters 4/3, 3/2, 2/1) sized so that each wrong answer lands in a different place, plus the label-invariance and row-order-invariance pins that catch a draw depending on anything but the multiset.

**Two lower-probability but higher-cost attacks.** `W-STATS-AGGREGATE-FAILED` naming a template's `aggregate` for a recorded column that `aggregate` never touched — prevented by Task 11's invariant and asserted in Task 14. And a `summary`-step `Estimate` acquiring a field from the pass that walks every metric block — prevented structurally (`summary_values`, not `summarize_step`) and asserted in Task 18 with an exact-equality check rather than a set of absences.
