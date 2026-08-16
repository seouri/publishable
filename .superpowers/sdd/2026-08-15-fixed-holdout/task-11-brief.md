## Task 11: Construction 2 — whole clusters, strata, and the relation between the two constructions

**Files:** Modify `src/publishable/units.py`. Modify (append) `tests/test_units.py`.

**Interfaces:**
- Consumes: `units._assign_whole_clusters_by_ratio(units, weights, rng, clusters) -> list[list[Unit]]`; `units._stratum_groups(units, names, axis, resolved=None) -> dict[tuple[str, ...], list[Unit]]`; `units.holdout_sizes`; `units.holdout_for` from task 10.
- Produces: the clustered and stratified branches of `holdout_for`, `HoldoutPlan.strata` populated, and — the reason this is its own task — a test that **distinguishes the two constructions from each other**. Also changes `_stratum_groups`' third parameter from `axis: str` to `declaration: str`, carrying the full dotted path.

**Why this is a second task and not a branch inside task 10.** `_assign_whole_clusters_by_ratio` takes a **non-optional** `Mapping` and indexes it directly — unlike its sibling `_assign_whole_clusters`, whose docstring argues at length that `clusters is None` is "a cluster of one per unit, not another path". The ratio primitive has no such branch and no such argument, so the unclustered holdout genuinely **cannot** go through it. These are two constructions with a relation between them, not one call with a flag.

**The relation, stated so a fixture can be built to see it.** With one cluster per unit, the two constructions produce the **same sizes** and, in general, **different membership**. The unclustered path shuffles *unit keys* and cuts two consecutive slices. The clustered path shuffles *cluster names*, sorts largest-first (stable, so with equal sizes the shuffled order survives), then deals each cluster to the bucket with the smallest `counts[i] / weights[i]` — which **interleaves** by ratio rather than slicing. So a singleton-cluster draw and an unclustered draw from the same seed over the same roster are **not** bit-identical, and a fixture that cannot tell them apart proves nothing about either. `CLAUDE.md` records exactly this trap: a cluster fixture where correct and buggy cluster counts were both 3.

**The `_stratum_groups` message is wrong for this caller, and the scoping is wrong that it is harmless.** `_stratum_groups` raises `NotImplementedError` interpolating `data.units.assign.{axis}.stratify_by`. A holdout caller passing `axis="holdout"` would print `data.units.assign.holdout.stratify_by` — a path no config can hold. Fix it by changing the parameter to a **full dotted path** and passing `f"data.units.assign.{axis}.stratify_by"` at the three existing sites and `"data.units.holdout.stratify_by"` here. **Before editing, run `grep -rn "stratify_by. names\|E-DATA-ASSIGN-STRATIFY-FORWARD" tests/ src/`** — a test pinning the old wording must move with it.

**`resolved` is not passed by this caller.** A holdout's `stratify_by` admits only a **unit attribute**, never a `sweep.groups` axis — § Validation's *Stratification attribute exists* says so, and task 8 refuses a holdout beside a group axis anyway. So the argument stays at its default and a name that is not an attribute raises, which is correct: `validate` refused it first as `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`.

**Coverage is checked over the MERGED draw, never per stratum** — `assignment_for`'s stated rule for the identical composition: a side a small stratum apportioned nothing is fine while another stratum covered it, and only a side empty across every stratum is refused.

- [ ] **Step 1: Write the failing test** — append to `tests/test_units.py`:

```python
def test_a_clustered_holdout_keeps_every_cluster_whole():
    """`reference.md` § Clustered units: "core computed the partition, so core
    keeps it indivisible." A holdout that trains on one cell of an animal and
    tests on another leaks just as thoroughly for happening only once.

    Twelve units in six clusters of two, so both a correct draw and a
    unit-level one give the same SIZES — the cluster-integrity assertion is the
    only thing that separates them, which is why the fixture is built this way
    rather than with clusters of one."""
    roster = _roster(12, animal=lambda i: f"a{i // 2}")
    clusters = {f"u{i}": f"a{i // 2}" for i in range(12)}
    plan = holdout_for(
        roster, {"method": "random", "frac": 0.5}, seed=99, clusters=clusters
    )
    train, test = set(plan.train), set(plan.test)
    assert train | test == {f"u{i}" for i in range(12)}
    assert not train & test
    for cluster in {f"a{i}" for i in range(6)}:
        members = {k for k, c in clusters.items() if c == cluster}
        assert members <= train or members <= test, (cluster, plan)
    # A positive companion for the integrity assertion above, which a draw
    # putting EVERY unit on one side would also satisfy.
    assert train and test


def test_the_clustered_and_unclustered_constructions_are_not_the_same_draw():
    """The relation between the two constructions, pinned — H3c-2's own
    experience is that a fixture cannot tell them apart unless it is built to.

    With one cluster per unit the two agree on SIZES and differ on MEMBERSHIP:
    the unclustered path shuffles unit keys and cuts two consecutive slices,
    while the clustered path shuffles cluster names, sorts largest-first, and
    deals each to the bucket furthest below its own target share — which
    interleaves by ratio rather than slicing. A fixture asserting only the
    sizes would pass under either construction for either call."""
    roster = _roster(10, animal=lambda i: f"u{i}")
    singleton = {f"u{i}": f"u{i}" for i in range(10)}
    plain = holdout_for(roster, {"method": "random", "frac": 0.4}, seed=5)
    clustered = holdout_for(
        roster, {"method": "random", "frac": 0.4}, seed=5, clusters=singleton
    )
    assert len(plain.test) == len(clustered.test) == 4
    assert set(plain.test) != set(clustered.test)


def test_a_stratified_holdout_splits_within_each_stratum():
    """`stratify_by` balances the split inside each stratum rather than only
    over the roster. Three UNEQUAL strata — 8, 4 and 2 units — so an
    unstratified draw, a correct stratified one, and one that weighted the
    strata equally each produce a different per-stratum test count.

    At `frac: 0.5` the correct per-stratum test counts are 4, 2 and 1; an
    unstratified draw of the same roster gives 7 test units spread by chance,
    which this asserts against directly."""
    sizes = {"big": 8, "mid": 4, "small": 2}
    labels = ["big"] * 8 + ["mid"] * 4 + ["small"] * 2
    roster = _roster(14, band=lambda i: labels[i])
    plan = holdout_for(
        roster, {"method": "random", "frac": 0.5, "stratify_by": ["band"]}, seed=17
    )
    assert plan.strata == ("band",)
    per_stratum = {}
    for name, count in sizes.items():
        members = {f"u{i}" for i, lab in enumerate(labels) if lab == name}
        per_stratum[name] = len(members & set(plan.test))
    assert per_stratum == {"big": 4, "mid": 2, "small": 1}
    # Membership too, not only counts: the counts are FORCED by the
    # apportionment, so no count assertion can see a change in how the
    # generator is carried across strata — the same dimension-no-assertion-
    # can-see shape that let a deleted shuffle pass an earlier slice's suite.
    # PINNED LITERAL — replace with what the implementation actually returns.
    assert set(plan.test) == {"REPLACE"}


def test_a_stratified_clustered_holdout_composes_both_rules():
    """The composition: strata outside, whole clusters inside — the same
    arrangement `assignment_for` uses, and sound only while
    `E-DATA-HOLDOUT-STRATIFY-VARIES` refuses a cluster carrying two stratum
    values, since such a cluster would belong to two groups and be divided.

    Every cluster whole AND every stratum represented on both sides."""
    labels = ["x"] * 8 + ["y"] * 8
    roster = _roster(16, animal=lambda i: f"a{i // 2}", band=lambda i: labels[i])
    clusters = {f"u{i}": f"a{i // 2}" for i in range(16)}
    plan = holdout_for(
        roster,
        {"method": "random", "frac": 0.5, "stratify_by": ["band"]},
        seed=23,
        clusters=clusters,
    )
    train, test = set(plan.train), set(plan.test)
    for cluster in {f"a{i}" for i in range(8)}:
        members = {k for k, c in clusters.items() if c == cluster}
        assert members <= train or members <= test, cluster
    for band in ("x", "y"):
        members = {f"u{i}" for i, lab in enumerate(labels) if lab == band}
        assert members & train and members & test, band


def test_a_stratified_holdout_that_leaves_a_side_empty_across_every_stratum_raises():
    """Coverage over the MERGED draw, `assignment_for`'s rule for the identical
    composition: a side a small stratum apportioned nothing is fine while
    another stratum covered it, and only a side empty everywhere is refused.

    Two strata of one unit each at `frac: 0.2` apportion `(1, 0)` in both, so
    the test side is empty across the whole draw."""
    roster = _roster(2, band=lambda i: f"b{i}")
    with pytest.raises(ContractError) as exc:
        holdout_for(
            roster, {"method": "random", "frac": 0.2, "stratify_by": ["band"]}, seed=1
        )
    assert exc.value.code == "E-DATA-HOLDOUT-EMPTY"


def test_a_thin_stratum_alone_does_not_raise():
    """The positive companion for the rule above, produced by the code under
    test: one stratum apportioning the test side nothing is accepted while
    another covers it. Without this the refusal above is indistinguishable from
    a per-stratum coverage rule."""
    labels = ["big"] * 9 + ["tiny"]
    roster = _roster(10, band=lambda i: labels[i])
    plan = holdout_for(
        roster, {"method": "random", "frac": 0.2, "stratify_by": ["band"]}, seed=3
    )
    assert plan.test and plan.train
    tiny = {"u9"}
    assert tiny <= set(plan.train)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_units.py -k "clustered_holdout or constructions_are_not or stratified_holdout or stratified_clustered or thin_stratum" -x`. All fail with `NotImplementedError` from task 10's guard. Before implementing, **verify the per-stratum expectations by hand**: `holdout_sizes(8, 0.5) == (4, 4)`, `holdout_sizes(4, 0.5) == (2, 2)`, `holdout_sizes(2, 0.5) == (1, 1)` and `holdout_sizes(1, 0.2) == (1, 0)`. If any differs, fix the test's literals to the arithmetic rather than the other way round.

- [ ] **Step 3: Implement** —

  (a) In `src/publishable/units.py`, change `_stratum_groups`' third parameter from `axis: str` to `declaration: str` and interpolate it whole in the `NotImplementedError`, replacing

```python
            f"`data.units.assign.{axis}.stratify_by` names {name!r}, which no resolved "
```

  with

```python
            f"`{declaration}` names {name!r}, which no resolved "
```

  and adding to that function's docstring:

```python
    **`declaration` is the full dotted path of the declaration being served**,
    not an axis name: this function has more than one caller and the message it
    raises names the config path a reader has to go and fix. An axis name
    interpolated into a fixed `data.units.assign.<...>` template would print
    `data.units.assign.holdout.stratify_by` for a holdout — a path no config
    can hold.
```

  Update the three call sites in `assignment_for` to pass `f"data.units.assign.{axis}.stratify_by"`, and sweep: `grep -rn "assign.*stratify_by. names" src/ tests/` must show every message and every test pinning it agreeing.

  (b) Replace task 10's combined `if strata or clusters is not None: raise NotImplementedError(...)` guard with the two realized branches. Inside the `random` branch, after the `frac` guard and **in place of** the unclustered shuffle-and-slice, put:

```python
        weights = [1.0 - float(frac), float(frac)]
        rng = random.Random(seed)
        train_keys: list[str] = []
        test_keys: list[str] = []
        if strata:
            # One generator across every stratum, `assignment_for`'s own
            # convention: the strata are drawn in roster order from one carried
            # state, so the seed determines the whole split together rather
            # than each stratum in isolation. `_stratum_groups` is handed no
            # `resolved`: a holdout's `stratify_by` admits only a unit
            # attribute, never a `sweep.groups` axis (§ Validation,
            # *Stratification attribute exists*), and a holdout beside a group
            # axis is refused outright as `E-DATA-HOLDOUT-CELLS`.
            groups = _stratum_groups(
                list(roster), strata, "data.units.holdout.stratify_by"
            )
            for stratum_units in groups.values():
                if clusters is not None:
                    # Whole clusters inside each stratum — sound only while
                    # `E-DATA-HOLDOUT-STRATIFY-VARIES` refuses a cluster
                    # carrying two stratum values, which would belong to two of
                    # these groups and be divided here. The identical argument
                    # `assignment_for` makes for the identical composition.
                    train_bucket, test_bucket = _assign_whole_clusters_by_ratio(
                        stratum_units, weights, rng, clusters
                    )
                    train_keys.extend(u.key for u in train_bucket)
                    test_keys.extend(u.key for u in test_bucket)
                else:
                    keys = [u.key for u in stratum_units]
                    rng.shuffle(keys)
                    cut, _rest = holdout_sizes(len(stratum_units), float(frac))
                    train_keys.extend(keys[:cut])
                    test_keys.extend(keys[cut:])
        elif clusters is not None:
            train_bucket, test_bucket = _assign_whole_clusters_by_ratio(
                list(roster), weights, rng, clusters
            )
            train_keys.extend(u.key for u in train_bucket)
            test_keys.extend(u.key for u in test_bucket)
        else:
            train_size, test_size = holdout_sizes(len(roster), float(frac))
            keys = [unit.key for unit in roster]
            rng.shuffle(keys)
            train_keys.extend(keys[:train_size])
            test_keys.extend(keys[train_size:])
        # Coverage over the MERGED draw, never per stratum — `assignment_for`'s
        # rule for the identical composition: a side a small stratum
        # apportioned nothing is fine while another stratum covered it, and
        # only a side empty across the whole draw leaves one half of the split
        # with no units. Also the one refusal the unclustered and clustered
        # paths share: a cluster is the smallest thing that can move, so a
        # clustered draw reaches an empty side more easily rather than being
        # exempt from the refusal.
        if not train_keys or not test_keys:
            side = "train" if not train_keys else "test"
            raise ContractError(
                f"`data.units.holdout.frac: {frac}` over {len(roster)} resolved units "
                f"leaves the {side} side empty"
                + (f", drawn within {len(strata)} stratum declaration(s)" if strata else "")
                + (" over whole clusters" if clusters is not None else "")
                + ". Every split needs both sides — the training side has nothing to fit "
                "on, or the test side has nothing to report over; widen or narrow "
                "`frac`, stratify on fewer attributes, or resolve a larger roster",
                code="E-DATA-HOLDOUT-EMPTY",
            )
        return HoldoutPlan(
            train=tuple(train_keys), test=tuple(test_keys), seed=seed, strata=strata
        )
```

  Delete task 10's separate `train_size == 0 or test_size == 0` pre-check — the merged coverage check above subsumes it, and two refusals of one fault is what the single check avoids. **Keep task 10's tests passing**: re-run them and confirm the message still names the empty side, which both of that task's parametrized rows assert on.

  (c) Update `holdout_for`'s docstring: replace the "not realized at this commit" paragraph with the composition rules — whole clusters through `_assign_whole_clusters_by_ratio` at `[1 - frac, frac]`, strata outside either draw through `_stratum_groups`, one generator across every stratum, and **the relation between the two constructions stated**:

```python
    **The two constructions are deliberately not one, and are not
    bit-identical.** The unclustered draw shuffles unit keys and cuts two
    consecutive slices; the clustered draw shuffles cluster names, sorts
    largest-first and deals each cluster to the bucket furthest below its own
    target share. With one cluster per unit the two agree on the SIZES and
    differ on the MEMBERSHIP — the second interleaves by ratio where the first
    slices — so a fixture that cannot tell them apart proves nothing about
    either. `_assign_whole_clusters_by_ratio` takes a non-optional `Mapping`
    and indexes it, unlike `_assign_whole_clusters`, which is why this is two
    paths rather than one with a `clusters or singletons` default.
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then the task 10 tests (`uv run pytest tests/test_units.py -k holdout`), then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/units.py`, replace the unclustered `else:` branch with a call to `_assign_whole_clusters_by_ratio(list(roster), weights, rng, {u.key: u.key for u in roster})` — the "singleton clusters are the same path" reading this task exists to refuse. Run `uv run pytest tests/test_units.py -k "constructions_are_not or holdout_cuts"`. `test_the_clustered_and_unclustered_constructions_are_not_the_same_draw` must **FAIL** on `set(plain.test) != set(clustered.test)`, and task 10's `holdout_cuts` must **FAIL** on its pinned literals. Revert in place; re-run.

  (b) Move `rng = random.Random(seed)` **inside** the stratum loop. Run `uv run pytest tests/test_units.py -k stratified_holdout`. `test_a_stratified_holdout_splits_within_each_stratum` must **FAIL on its membership assertion and only on that one**: with one generator the strata are drawn from a carried state and with one per stratum each restarts, so the per-stratum *counts* are unchanged — which is exactly why that test carries the pinned `set(plan.test)` literal beside the counts, and why this mutation would be blind without it. Revert in place; re-run.

  (c) In the stratified branch, change `cut, _rest = holdout_sizes(len(stratum_units), float(frac))` to `cut, _rest = holdout_sizes(len(roster), float(frac))` — apportioning the whole roster's sizes inside each stratum. `test_a_stratified_holdout_splits_within_each_stratum` must **FAIL** on `per_stratum == {"big": 4, "mid": 2, "small": 1}`. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: the clustered and stratified holdout draws, and the relation between them`.

---

