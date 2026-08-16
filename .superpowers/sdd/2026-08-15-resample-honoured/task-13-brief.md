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

