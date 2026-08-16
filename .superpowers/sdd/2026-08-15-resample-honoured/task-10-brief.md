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

