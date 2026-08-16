## Task 16: `W-STATS-RESAMPLE-CLUSTERS` against the test partition

**Files:** Modify `src/publishable/validate.py`. Modify (append) `tests/test_validate.py`.

**Interfaces:**
- Consumes: `units.holdout_for`, `units.holdout_seed_for`, `units.clusters_of`, `hashes.design_digest`, `units.fold_basis`.
- Produces: `_check_resample(doc, roster, c, holdout_test: UnitList | None = None)` — one new keyword parameter — and a `_holdout_test_roster(doc, units_decl, roster, cluster_by) -> UnitList | None` helper in `validate.py`, called once in `validate_config` and threaded in.

**The defect, in the direction of not firing.** `_check_resample` computes `groups = fold_basis(roster, cluster_by)` over the **whole roster** and compares it to `limits.min_clusters`. Under a `frac: 0.2` holdout the percentile interval actually rests on roughly a fifth of that many clusters: a run with 50 clusters and `min_clusters: 20` passes silently while its intervals rest on ~10 draws. H4a shipped it, and only a task scoped past `holdout` alone would notice.

**Why the fix is the realized draw and not `fold_basis × frac`.** Under `by_attribute` there is **no `frac`** — the realized proportion is whatever the column says. And under `cluster_by` the split moves whole clusters, so the realized cluster count is not any arithmetic on the unit count. `holdout_for` is a pure function precisely so `validate` can ask it, which is `assignment_for`'s own argument.

**Only the clusters warning moves.** `E-STATS-RESAMPLE-STRATIFY-VARIES` keeps reading the **whole** roster: within-cluster constancy over the test partition is implied by constancy over the whole roster, so refusing on the wider set is stricter and correct, and refusing on the narrower one would let a config validate whose *training* half is incoherent. Say this in the code.

**`tests/test_validate.py` does not import `_check_resample`** — verified at `78bb794`, it appears only in docstrings there — so this signature change costs nothing outside `validate.py`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
_FIFTY_CLUSTERS = "patient_id,animal_id,label\n" + "".join(
    f"p{i},a{i // 2},x\n" for i in range(100)
)


def test_the_resample_cluster_warning_counts_the_holdout_s_test_partition(
    write_config, tmp_path
):
    """The warning is about how many INDEPENDENT DRAWS a percentile interval
    rests on, and under a holdout the draw runs over the test partition alone.
    50 clusters × `frac: 0.2` is ~10, so `min_clusters: 20` must warn — and at
    `78bb794` it does not, because the count is taken over the whole roster.

    Two configs differing ONLY in whether a holdout is declared, so the
    warning's presence is attributable to the holdout rather than to the
    roster."""
    (tmp_path / "input" / "index.csv").write_text(_FIFTY_CLUSTERS)
    common = {
        "from": "index.csv", "key": "patient_id",
        "attributes": ["animal_id", "label"], "cluster_by": "animal_id",
    }
    resample = {"resample": {"method": "bootstrap", "n": 2000}}

    without = codes(write_config({
        "data.units": dict(common),
        "limits": {"min_clusters": 20},
        "statistics": resample,
    }))
    # The control, and it must be silent: 50 clusters is above 20.
    assert "W-STATS-RESAMPLE-CLUSTERS" not in without

    with_holdout = codes(write_config({
        "data.units": dict(common, holdout={"method": "random", "frac": 0.2}),
        "limits": {"min_clusters": 20},
        "statistics": resample,
    }))
    assert "W-STATS-RESAMPLE-CLUSTERS" in with_holdout
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in with_holdout


def test_a_holdout_wide_enough_to_keep_the_clusters_does_not_warn(
    write_config, tmp_path
):
    """The positive companion, produced by the code under test: the same
    roster and the same `min_clusters` under a `frac: 0.8` holdout keeps ~40
    clusters on the test side and stays silent. Without it, a fix that warned
    whenever a holdout was declared would pass the test above."""
    (tmp_path / "input" / "index.csv").write_text(_FIFTY_CLUSTERS)
    found = codes(write_config({
        "data.units": {
            "from": "index.csv", "key": "patient_id",
            "attributes": ["animal_id", "label"], "cluster_by": "animal_id",
            "holdout": {"method": "random", "frac": 0.8},
        },
        "limits": {"min_clusters": 20},
        "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
    }))
    assert "W-STATS-RESAMPLE-CLUSTERS" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_the_stratum_constancy_check_still_reads_the_whole_roster(
    write_config, tmp_path
):
    """`E-STATS-RESAMPLE-STRATIFY-VARIES` deliberately does NOT move: a
    stratum varying inside a cluster the holdout put on the TRAINING side is
    still an incoherent declaration, and refusing on the whole roster is the
    stricter, correct reading.

    The fixture makes only the training-side clusters vary — pinned by seed, so
    the assertion is about the check's scope rather than about luck."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,animal_id,label\n"
        + "".join(f"p{i},a{i // 2},{'x' if i % 2 else 'y'}\n" for i in range(40))
    )
    found = codes(write_config({
        "data.units": {
            "from": "index.csv", "key": "patient_id",
            "attributes": ["animal_id", "label"], "cluster_by": "animal_id",
            "holdout": {"method": "random", "frac": 0.2, "seed": 1234},
        },
        "limits": {"min_clusters": 2},
        "statistics": {
            "resample": {"method": "bootstrap", "n": 2000, "stratify_by": ["label"]}
        },
    }))
    assert "E-STATS-RESAMPLE-STRATIFY-VARIES" in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k "resample_cluster_warning or holdout_wide_enough or stratum_constancy_still" -x`. The first fails on `W-STATS-RESAMPLE-CLUSTERS in with_holdout`; the other two pass, which is why each carries a companion.

  **Verify the digest before implementing, because the task's premise rests on it.** `validate`'s realization must use the **same digest** `cli.command_run` derives the seed from, or the warning is aimed at a partition the run does not draw. Confirmed at `78bb794`: `cli.py` line 1199 is `digest = design_digest(doc)  # phase 5: pin hashes`, over the same document `validate_config` holds, and `cli.py` imports it as `from publishable.hashes import code_hash, design_digest, parameters_hash`. **Re-check both** — if `command_run`'s digest has since come from anywhere else (a `run_identity` helper, a pre-narrowed dict), the two realizations diverge and this task must derive it the way `command_run` does rather than the way this brief assumes. Also confirmed: `validate.py` imports nothing from `publishable.hashes` at `78bb794`, so the import is new; `hashes.py` imports only the standard library, so there is no cycle.

  **Verify the arithmetic against the fixture before implementing**: 100 rows in clusters of 2 is 50 clusters; a `frac: 0.2` clustered draw allocates whole clusters, so the test side holds close to 10 — print the realized count from `holdout_for` and confirm it is below 20 rather than assuming it.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`:

```python
def _holdout_test_roster(
    doc: dict[str, Any],
    units_decl: dict[str, Any],
    roster: UnitList | None,
    cluster_by: str | None,
) -> UnitList | None:
    """The holdout's realized **test** partition, or `None` when the design
    declares none or the draw cannot be performed.

    Realized through `units.holdout_for`, the same pure function
    `cli.command_run` realizes it with — which is the reason that function is
    pure at all, `assignment_for`'s own argument: `validate` has to ask "which
    units will the interval rest on" of the same declaration the run asks it
    of, so a second answer computed here would be a check aimed at a partition
    the run does not use.

    **Never raises.** `validate` collects, and this runs over configs that are
    already known bad — a malformed `frac`, an unresolvable column, an unknown
    stratum, a cluster attribute a unit does not carry. Each of those is
    reported by its own check; here they become `None`, and the check that
    reads this simply does not run rather than reporting a second, derived
    fault on top of the one the reader has to fix anyway.
    """
    if roster is None:
        return None
    block = units_decl.get("holdout")
    if not isinstance(block, dict) or not block:
        return None
    try:
        clusters = clusters_of(roster, cluster_by) if cluster_by else None
        plan = holdout_for(
            roster,
            block,
            seed=holdout_seed_for(block, design_digest(doc), roster),
            clusters=clusters,
        )
    except (ContractError, NotImplementedError, KeyError, TypeError, ValueError):
        return None
    test = set(plan.test)
    return UnitList([u for u in roster if u.key in test])
```

  Add `clusters_of`, `holdout_for` and `holdout_seed_for` to the `publishable.units` import list and `design_digest` from `publishable.hashes`. Then in `validate_config`, immediately after `basis` is resolved:

```python
    # The holdout's realized test partition, resolved once and threaded — the
    # denominator a resample's cluster count is actually over. Resolved here
    # rather than inside `_check_resample` so a future second reader gets the
    # same object rather than realizing a second draw.
    holdout_test = _holdout_test_roster(doc, units_decl, roster, usable_cluster)
```

  and change the call to `_check_resample(doc, roster, c, holdout_test=holdout_test)`.

  Then in `_check_resample`, add the parameter and use it for the cluster count only:

```python
def _check_resample(
    doc: dict[str, Any],
    roster: UnitList | None,
    c: Collector,
    holdout_test: UnitList | None = None,
) -> None:
```

  replacing

```python
            groups = fold_basis(roster, cluster_by)
```

  with

```python
            # **The test partition when a holdout is declared, not the whole
            # roster.** `statistics.resample` draws over the per-unit table,
            # which under a holdout holds only the units that recorded — so a
            # percentile interval rests on the clusters of the TEST side, and
            # counting the wider set warns against a denominator no interval
            # used. Wrong in the direction of NOT firing: 50 clusters at
            # `frac: 0.2` leaves roughly 10, and `min_clusters: 20` passed
            # silently.
            #
            # `holdout_test` is `None` whenever no holdout is declared or the
            # draw could not be performed, so this is `roster` unchanged for
            # every other design — including every config in the build before
            # a holdout existed.
            groups = fold_basis(holdout_test if holdout_test is not None else roster, cluster_by)
```

  and add to `_check_resample`'s docstring, in the `W-STATS-RESAMPLE-CLUSTERS` bullet, that it reads the test partition, plus a sentence on why `E-STATS-RESAMPLE-STRATIFY-VARIES` deliberately does not:

```python
    - `E-STATS-RESAMPLE-STRATIFY-VARIES` — **reads the WHOLE roster, on
      purpose**, even under a `data.units.holdout`. Constancy within a cluster
      over the whole roster implies it over any subset, so the wider read is
      the stricter one; the narrower would let a config validate whose training
      half is incoherent and whose test half happens not to show it.
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — two.

  (a) In `src/publishable/validate.py`, revert the `fold_basis` argument to `roster`. `test_the_resample_cluster_warning_counts_the_holdout_s_test_partition` must **FAIL**, and `test_a_holdout_wide_enough_to_keep_the_clusters_does_not_warn` must still pass. Revert in place; re-run.

  (b) Change `_holdout_test_roster`'s return to `UnitList([u for u in roster if u.key in set(plan.train)])`. `test_a_holdout_wide_enough_to_keep_the_clusters_does_not_warn` must **FAIL** (the train side at `frac: 0.8` is ~10 clusters, below 20) **and** `test_the_resample_cluster_warning_...` must **PASS** — which is exactly why the second test exists: a single-config fixture cannot tell "counts the test side" from "counts the smaller side". Revert in place; re-run.

- [ ] **Step 6: Commit** — `fix: count a resample's clusters over the holdout's test partition`.

---

