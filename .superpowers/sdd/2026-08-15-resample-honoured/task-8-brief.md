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

