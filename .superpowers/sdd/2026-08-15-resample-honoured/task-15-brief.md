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

