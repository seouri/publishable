# tests/test_units.py
import importlib
import sys
from collections import Counter
from pathlib import Path

import pytest

from publishable import ContractError
from publishable.units import (
    DRAWN_ASSIGN_METHODS,
    HOLDOUT_METHODS_REALIZED,
    ArmPlan,
    HoldoutPlan,
    Unit,
    UnitList,
    _apportion,
    _assign_constant_columns,
    _holdout_constant_column,
    _seed_from,
    apply_rule,
    arm_members,
    arms_of,
    assign_seed_for,
    assignment_for,
    cluster_count,
    clusters_of,
    collapse_measurements,
    fold_basis,
    holdout_for,
    holdout_seed_for,
    holdout_sizes,
    holdout_values_fault,
    partition_units,
    resolve_units,
    stratum_varies_within_cluster,
    units_hash,
)


@pytest.fixture
def input_dir(tmp_path: Path) -> Path:
    d = tmp_path / "in"
    (d / "scans").mkdir(parents=True)
    (d / "index.csv").write_text("patient_id,label,site\np3,1,a\np1,0,b\np2,1,a\n")
    for name in ("b.dcm", "a.dcm"):
        (d / "scans" / name).write_bytes(b"\x00")
    (d / "top.dcm").write_bytes(b"\x00")
    return d


def test_a_table_resolves_in_row_order_not_sorted(input_dir: Path):
    units, _, _ = resolve_units(
        {"from": "index.csv", "key": "patient_id", "attributes": ["label", "site"]}, input_dir
    )
    assert [u.key for u in units] == ["p3", "p1", "p2"], "row order is data, not cosmetic"
    assert len(units) == 3
    assert units[0].key == "p3"


def test_declared_attributes_are_readable_directly(input_dir: Path):
    units, _, _ = resolve_units(
        {"from": "index.csv", "key": "patient_id", "attributes": ["label", "site"]}, input_dir
    )
    assert units[0].site == "a"
    assert units[0].attributes["label"] == "1"


def test_an_undeclared_column_is_not_an_attribute(input_dir: Path):
    units, _, _ = resolve_units(
        {"from": "index.csv", "key": "patient_id", "attributes": ["label"]}, input_dir
    )
    assert "site" not in units[0].attributes
    with pytest.raises(AttributeError):
        _ = units[0].site


def test_a_glob_resolves_lexicographically_with_the_path_as_key(input_dir: Path):
    units, _, _ = resolve_units({"from": {"glob": "**/*.dcm"}, "key": "path"}, input_dir)
    assert [u.key for u in units] == ["scans/a.dcm", "scans/b.dcm", "top.dcm"]
    assert units[0].paths == ("scans/a.dcm",)


def test_a_non_recursive_glob_does_not_descend(input_dir: Path):
    units, _, _ = resolve_units({"from": {"glob": "*.dcm"}, "key": "path"}, input_dir)
    assert [u.key for u in units] == ["top.dcm"]


def test_a_missing_key_column_is_refused(input_dir: Path):
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "index.csv", "key": "subject_id"}, input_dir)
    assert e.value.code == "E-UNITS-KEY-MISSING"
    assert "subject_id" in str(e.value)


def test_a_missing_attribute_column_is_refused(input_dir: Path):
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "index.csv", "key": "patient_id", "attributes": ["age"]}, input_dir)
    assert e.value.code == "E-UNITS-ATTR-MISSING"


def test_a_glob_matching_nothing_is_refused(input_dir: Path):
    with pytest.raises(ContractError) as e:
        resolve_units({"from": {"glob": "**/*.nonexistent"}, "key": "path"}, input_dir)
    assert e.value.code == "E-UNITS-EMPTY"
    assert "*.nonexistent" in str(e.value)


def test_a_header_only_table_is_refused_as_empty_not_key_missing(input_dir: Path):
    (input_dir / "empty.csv").write_text("patient_id,label\n")
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "empty.csv", "key": "patient_id"}, input_dir)
    assert e.value.code == "E-UNITS-EMPTY"


def test_a_genuinely_missing_key_column_with_real_rows_still_reports_key_missing(
    input_dir: Path,
):
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "index.csv", "key": "subject_id"}, input_dir)
    assert e.value.code == "E-UNITS-KEY-MISSING"


def test_a_one_unit_roster_still_resolves(input_dir: Path):
    (input_dir / "single.csv").write_text("patient_id\np1\n")
    units, _, _ = resolve_units({"from": "single.csv", "key": "patient_id"}, input_dir)
    assert len(units) == 1
    assert units[0].key == "p1"


def test_a_missing_table_is_refused(input_dir: Path):
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "absent.csv", "key": "patient_id"}, input_dir)
    assert e.value.code == "E-UNITS-SOURCE-MISSING"


def test_a_wrong_typed_source_names_both_alternatives_without_doubled_braces(input_dir: Path):
    """`data.units.from` that is neither a string nor a `glob`/`resolver` mapping
    must render both alternatives as single braces — the continuation is an
    f-string specifically so `{{resolver: ...}}` unescapes to `{resolver: ...}`,
    matching `{glob: ...}` in the same sentence rather than rendering literal
    doubled braces."""
    with pytest.raises(ContractError) as e:
        resolve_units({"from": 42, "key": "patient_id"}, input_dir)
    assert e.value.code == "E-UNITS-SOURCE-MISSING"
    assert str(e.value) == (
        "`data.units.from` is 42; expected a table name, {glob: ...}, or {resolver: ...}"
    )


def test_duplicate_keys_are_refused_naming_the_offender(input_dir: Path):
    (input_dir / "dup.csv").write_text("patient_id\np1\np2\np1\n")
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "dup.csv", "key": "patient_id"}, input_dir)
    assert e.value.code == "E-UNITS-KEY-DUPLICATE"
    assert "p1" in str(e.value)


@pytest.mark.parametrize("reserved", ["key", "paths", "attributes"])
def test_reserved_attribute_names_are_refused(input_dir: Path, reserved: str):
    (input_dir / "r.csv").write_text(f"patient_id,{reserved}\np1,x\n")
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "r.csv", "key": "patient_id", "attributes": [reserved]}, input_dir)
    assert e.value.code == "E-UNITS-ATTR-RESERVED"


def test_a_unit_is_frozen_and_hashable_by_key():
    u = Unit(key="p1", paths=(), attributes={"label": "1"})
    with pytest.raises(Exception):  # noqa: B017 — frozen dataclass raises FrozenInstanceError
        u.key = "p2"  # type: ignore[misc]
    assert hash(u) == hash(Unit(key="p1", paths=(), attributes={"label": "0"}))


def test_attributes_cannot_be_mutated_in_place():
    u = Unit(key="p1", paths=(), attributes={"label": "1"})
    with pytest.raises(ContractError) as exc:
        u.attributes["x"] = 1  # type: ignore[index]
    assert exc.value.code == "E-UNIT-IMMUTABLE"
    assert u.attributes["label"] == "1"
    assert u.label == "1"


def test_mutating_the_original_dict_after_construction_does_not_leak_in():
    original = {"label": "1"}
    u = Unit(key="p1", paths=(), attributes=original)
    original["label"] = "tampered"
    original["extra"] = "new"
    assert u.attributes["label"] == "1"
    assert "extra" not in u.attributes


def test_the_unit_list_is_exactly_four_operations(input_dir: Path):
    units, _, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert len(list(units)) == 3  # iterate, repeatably
    assert len(list(units)) == 3
    assert len(units) == 3  # len
    assert units[1].key == "p1"  # index
    for absent in ("append", "index", "count", "sort", "__contains__"):
        assert not hasattr(units, absent), f"{absent} would make this a list"


def test_slicing_is_rejected_not_silently_returning_a_list(input_dir: Path):
    units, _, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    with pytest.raises(ContractError) as e:
        _ = units[0:2]
    assert e.value.code == "E-STEP-UNITS-CONTRACT"
    assert units[0].key == "p3"  # integer indexing still works


def test_a_string_index_is_rejected(input_dir: Path):
    units, _, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    with pytest.raises(ContractError) as e:
        _ = units["p1"]  # type: ignore[call-overload]
    assert e.value.code == "E-STEP-UNITS-CONTRACT"


def test_membership_and_reversed_are_deliberately_permitted(input_dir: Path):
    # Not part of the promised three operations, but both derive entirely from
    # `__iter__` (membership) and `len` + integer indexing (`reversed`), so any
    # backing that satisfies the contract satisfies these for free — unlike
    # slicing, which would return a foreign type. See spec-defects.md.
    units, _, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    first = units[0]
    assert first in units
    assert [u.key for u in reversed(units)] == ["p2", "p1", "p3"]


def test_train_raises_when_no_partition_is_declared(input_dir: Path):
    units, _, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    with pytest.raises(ContractError) as e:
        _ = units.train
    assert e.value.code == "E-STEP-UNITS-UNAVAILABLE"


def test_units_hash_follows_order_and_content(input_dir: Path):
    a, _, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    b, _, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert units_hash(a) == units_hash(b)
    assert units_hash(a).startswith("sha256:")
    (input_dir / "index.csv").write_text("patient_id,label,site\np1,0,b\np3,1,a\np2,1,a\n")
    reordered, _, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert units_hash(reordered) != units_hash(a), "order is part of the identity"


def _roster(n: int) -> UnitList:
    return UnitList([Unit(key=f"u{i:03d}", paths=(), attributes={}) for i in range(n)])


def test_a_pinned_assign_seed_is_returned_literally():
    """§ What `auto` derives from: 'pinning an integer is the deliberate act,
    and the one to take for anything you intend to cite', so a pinned seed must
    survive a roster change. Same block, two different rosters, same answer."""
    block = {"method": "blocked", "seed": 42}
    assert assign_seed_for(block, "arm", "sha256:d", _roster(10)) == 42
    assert assign_seed_for(block, "arm", "sha256:d", _roster(11)) == 42


def test_a_boolean_seed_is_not_a_pin_and_derives():
    """`bool` is a subclass of `int`, so `seed: true` would otherwise pin every
    drawn axis to `1` and `seed: false` to `0` — a number nobody wrote, recorded
    in `allocation.json` as the axis's own seed. `assign_seed_for` excludes it
    explicitly, and this is what pins that exclusion: dropping the
    `not isinstance(seed, bool)` guard makes both assertions below read `1`/`0`.

    `validate` refuses the declaration outright (`E-DATA-ASSIGN-SEED`), so this
    is the second line rather than the only one — but a raise-free fallback in
    the function `validate` itself calls is worth keeping honest."""
    roster = _roster(10)
    derived = assign_seed_for({"method": "random"}, "arm", "sha256:d", roster)
    for pinned in (True, False):
        block = {"method": "random", "seed": pinned}
        assert assign_seed_for(block, "arm", "sha256:d", roster) == derived
    assert derived not in (0, 1)


def test_the_derived_seed_moves_with_the_roster():
    """'the roster changes, or any axis is added or edited'. Two rosters
    differing by one unit -> different seeds. THE CONTROL: the same roster in a
    different ORDER must also differ, because `units_hash` covers order and
    § Where units come from says two runs that resolved the same units in a
    different sequence did not allocate the same trial."""
    block = {"method": "blocked"}
    base = assign_seed_for(block, "arm", "sha256:d", _roster(10))

    grown = _roster(11)
    assert assign_seed_for(block, "arm", "sha256:d", grown) != base

    reordered = UnitList(list(reversed(list(_roster(10)))))
    assert assign_seed_for(block, "arm", "sha256:d", reordered) != base


def test_the_derived_seed_moves_with_the_axis_name():
    """Two axes over one roster and one digest draw differently, or a crossed
    design assigns both axes identically."""
    block = {"method": "blocked"}
    roster = _roster(10)
    arm_seed = assign_seed_for(block, "arm", "sha256:d", roster)
    sex_seed = assign_seed_for(block, "sex", "sha256:d", roster)
    assert arm_seed != sex_seed


def test_the_derived_seed_moves_with_the_digest():
    block = {"method": "blocked"}
    roster = _roster(10)
    one = assign_seed_for(block, "arm", "sha256:d", roster)
    other = assign_seed_for(block, "arm", "sha256:e", roster)
    assert one != other


def test_every_unit_appears_in_exactly_one_partition():
    parts = partition_units(_roster(240), 10, "d")
    seen = [u.key for p in parts for u in p]
    assert len(seen) == 240
    assert len(set(seen)) == 240


def test_partitions_cover_the_roster():
    parts = partition_units(_roster(240), 10, "d")
    assert {u.key for p in parts for u in p} == {f"u{i:03d}" for i in range(240)}


def test_partition_sizes_differ_by_at_most_one():
    parts = partition_units(_roster(241), 10, "d")
    sizes = sorted(len(p) for p in parts)
    assert sizes[-1] - sizes[0] <= 1
    assert len(parts) == 10


def test_k_equal_to_n_yields_one_unit_each():
    parts = partition_units(_roster(7), 7, "d")
    assert [len(p) for p in parts] == [1] * 7


def test_the_same_digest_reproduces_the_same_split():
    a = partition_units(_roster(50), 5, "d")
    b = partition_units(_roster(50), 5, "d")
    assert [[u.key for u in p] for p in a] == [[u.key for u in p] for p in b]


def test_a_different_digest_gives_a_different_split():
    a = partition_units(_roster(50), 5, "d")
    b = partition_units(_roster(50), 5, "other")
    assert [[u.key for u in p] for p in a] != [[u.key for u in p] for p in b]


def test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite():
    """The literal split HEAD produced before `clusters` existed, pinned as bytes.

    The other unclustered tests pin reproducibility and shape — the same digest
    twice, sizes within one — which a rewritten unclustered path would still
    satisfy while allocating different units to different folds. `cohort-pilot`
    and every other unclustered design rests on this draw being the same one.
    """
    parts = partition_units(_roster(50), 5, "d")
    assert [[u.key for u in p] for p in parts] == [
        ["u018", "u019", "u034", "u029", "u025", "u023", "u007", "u016", "u013", "u035"],
        ["u036", "u000", "u043", "u040", "u026", "u032", "u003", "u031", "u022", "u041"],
        ["u020", "u046", "u004", "u001", "u038", "u049", "u017", "u030", "u012", "u033"],
        ["u039", "u021", "u028", "u010", "u045", "u048", "u009", "u024", "u014", "u042"],
        ["u011", "u006", "u002", "u005", "u015", "u037", "u027", "u008", "u047", "u044"],
    ]


def _clustered(sizes: dict[str, int]) -> tuple[UnitList, dict[str, str]]:
    units, clusters = [], {}
    for site, n in sizes.items():
        for i in range(n):
            key = f"{site}_{i}"
            units.append(Unit(key=key, paths=(), attributes={"site": site}))
            clusters[key] = site
    return UnitList(units), clusters


def test_no_cluster_is_split_across_folds():
    """Cluster sizes 7/3/3/1/1 over k=2. Deliberately uneven: with equal-sized or
    singleton clusters the clustered and unclustered partitioners agree, so a test
    over those could not see this rewrite at all.

    The `{8, 7}` assertion discriminates twice over. Assigning units rather than
    whole clusters splits a cluster and trips the `seen` check; balancing cluster
    count rather than unit count puts 7+3 against 3+1+1 and gives `{10, 5}`; and
    under this digest the shuffle draws the size-7 cluster **last**, so dropping
    the largest-first sort also gives `{10, 5}` rather than coinciding with the
    sorted answer as it does for shuffles that draw it early.
    """
    roster, clusters = _clustered({"S1": 7, "S2": 3, "S3": 3, "S4": 1, "S5": 1})
    folds = partition_units(roster, k=2, digest="sha256:abc", clusters=clusters)
    seen: dict[str, int] = {}
    for f, fold in enumerate(folds):
        for u in fold:
            assert seen.setdefault(clusters[u.key], f) == f, "a cluster spans two folds"
    assert sum(len(f) for f in folds) == 15  # every unit lands
    assert len({u.key for f in folds for u in f}) == 15  # and lands exactly once
    assert {len(f) for f in folds} == {8, 7}  # balanced by UNIT count


def test_the_clustered_draw_follows_the_digest():
    """Six clusters of 3 over k=3, where the largest-first sort is a no-op and the
    shuffle is the only thing deciding which cluster lands where.

    Membership, not sizes: with equal clusters every fold holds 6 units whatever
    the order, so a size assertion here is a check that could not fail. Dropping
    the shuffle makes the assignment a function of the sizes alone and this test
    is what reports it.
    """
    roster, clusters = _clustered({f"C{i}": 3 for i in range(6)})
    a = partition_units(roster, k=3, digest="sha256:0000", clusters=clusters)
    b = partition_units(roster, k=3, digest="sha256:0001", clusters=clusters)
    as_sites = [sorted({clusters[u.key] for u in fold}) for fold in a]
    bs_sites = [sorted({clusters[u.key] for u in fold}) for fold in b]
    assert as_sites != bs_sites, "the clustered draw must be a function of the digest"
    assert [len(f) for f in a] == [6, 6, 6]
    assert [len(f) for f in b] == [6, 6, 6]


def test_the_same_digest_reproduces_the_same_clustered_split():
    roster, clusters = _clustered({"S1": 7, "S2": 3, "S3": 3, "S4": 1, "S5": 1})
    a = partition_units(roster, k=2, digest="sha256:abc", clusters=clusters)
    b = partition_units(roster, k=2, digest="sha256:abc", clusters=clusters)
    assert [[u.key for u in p] for p in a] == [[u.key for u in p] for p in b]


def test_more_folds_than_clusters_leaves_folds_empty_rather_than_raising():
    """`k` past the cluster count is refused at `validate`
    (`E-REPL-FOLD-K-TOO-LARGE`, bounded by `fold_basis`), so a caller reaching here
    with such a `k` is one that skipped that check. The partitioner stays total and
    empty-handed rather than dividing a cluster to fill a fold — an empty fold is a
    visibly useless split, a divided cluster is a leaky one that looks fine."""
    roster, clusters = _clustered({"S1": 2, "S2": 2})
    folds = partition_units(roster, k=4, digest="sha256:abc", clusters=clusters)
    assert sorted(len(f) for f in folds) == [0, 0, 2, 2]


def _by_stratum(sizes: dict[str, int]) -> tuple[UnitList, dict[str, str]]:
    """One unit per member, `label` carrying the stratum and no clustering."""
    units, strata = [], {}
    for label, n in sizes.items():
        for i in range(n):
            key = f"{label}_{i}"
            units.append(Unit(key=key, paths=(), attributes={"label": label}))
            strata[key] = label
    return UnitList(units), strata


def _clustered_by_stratum(
    spec: dict[str, list[int]],
) -> tuple[UnitList, dict[str, str], dict[str, str]]:
    """Clusters of the given sizes, every cluster wholly inside one stratum — which
    is what `units.stratum_varies_within_cluster` guarantees a validated config is."""
    units, clusters, strata = [], {}, {}
    for label, sizes in spec.items():
        for c, n in enumerate(sizes):
            cluster = f"{label}c{c}"
            for i in range(n):
                key = f"{cluster}_{i}"
                units.append(Unit(key=key, paths=(), attributes={"label": label, "site": cluster}))
                clusters[key], strata[key] = cluster, label
    return UnitList(units), clusters, strata


def test_each_fold_gets_a_proportional_share_of_each_stratum():
    """12 units, 8 `label=0` and 4 `label=1`, at k=2, so each fold must hold 4 and 2.

    Deliberately asymmetric, and deliberately under digest `sha256:0000`. An 8/4
    roster is not enough on its own: under `sha256:abc` and under `"d"` the
    *unstratified* draw already lands 4/2 in both folds, so this assertion would pass
    against a partitioner that ignored `strata` entirely. Under `sha256:0000` it does
    not — `test_an_unstratified_draw_of_the_same_stratum_fixture_is_lopsided` pins the
    3/3 and 5/1 it gives instead, and is this test's control.
    """
    roster, strata = _by_stratum({"0": 8, "1": 4})
    folds = partition_units(roster, k=2, digest="sha256:0000", strata=strata)
    assert [len(f) for f in folds] == [6, 6]
    for fold in folds:
        counts = Counter(u.label for u in fold)
        assert counts["0"] == 4
        assert counts["1"] == 2


def test_an_unstratified_draw_of_the_same_stratum_fixture_is_lopsided():
    """The control that must report: the same roster and digest with no `strata`
    splits the small stratum 3/1, not 2/2. Named with `stratum` so `pytest -k
    stratum` runs it beside the probe rather than leaving the probe unaccompanied."""
    roster, _ = _by_stratum({"0": 8, "1": 4})
    folds = partition_units(roster, k=2, digest="sha256:0000")
    assert [dict(Counter(u.label for u in f)) for f in folds] == [
        {"0": 3, "1": 3},
        {"0": 5, "1": 1},
    ]


def test_one_stratum_over_the_whole_roster_is_the_unstratified_draw():
    """A single stratum has nothing to balance, so it must reproduce the draw exactly
    — the same units in the same folds in the same order, not merely the same sizes.
    This is what pins the stratified path onto the one assignment rule: a second rule
    for the stratified case would be free to differ here."""
    roster, strata = _by_stratum({"only": 50})
    stratified = partition_units(roster, k=5, digest="d", strata=strata)
    plain = partition_units(roster, k=5, digest="d")
    assert [[u.key for u in f] for f in stratified] == [[u.key for u in f] for f in plain]


def test_no_cluster_is_split_across_a_stratified_fold():
    """Stratification must not reintroduce the leak. Clusters 7/3/3/1/1, each wholly
    inside one stratum (`A` holds 7+3, `B` holds 3+1+1), at k=2.

    Task 4's `test_no_cluster_is_split_across_folds` cannot see this: it passes no
    `strata`, so a stratifier that partitioned units instead of clusters — or that
    ignored `clusters` once `strata` arrived — would leave it green. The uneven sizes
    are what make the leak visible; with singleton clusters every assignment keeps
    them whole trivially.
    """
    roster, clusters, strata = _clustered_by_stratum({"A": [7, 3], "B": [3, 1, 1]})
    folds = partition_units(roster, k=2, digest="sha256:0000", clusters=clusters, strata=strata)
    seen: dict[str, int] = {}
    for f, fold in enumerate(folds):
        for u in fold:
            assert seen.setdefault(clusters[u.key], f) == f, "a cluster spans two folds"
    assert sum(len(f) for f in folds) == 15
    assert len({u.key for f in folds for u in f}) == 15
    assert [dict(Counter(u.label for u in f)) for f in folds] == [
        {"A": 7, "B": 3},
        {"A": 3, "B": 2},
    ]


def test_the_clustered_stratified_split_pins_which_fold_each_cluster_lands_in():
    """Stratum `A` in clusters 3/2/2/2 and `B` in 5/1/1/1/1, at k=3 — the shape where
    the per-stratum fold sizes are *not* in descending order (`A` gives 3/4/2), so
    merging the strata index-wise and merging them sorted by size differ.

    Pinned as membership because that difference is an arrangement, not an imbalance:
    sorting cannot change any stratum's multiset of piece sizes, and on this very
    fixture it lands marginally *closer* to the roster's 1:1 mix (4/9 and 3/5 against
    3/8 and 4/6). There is therefore no proportional assertion that could justly
    condemn it, and this test condemns it on the contract instead — which fold a unit
    lands in is a function of the digest, and `partition_units` says so.
    """
    roster, clusters, strata = _clustered_by_stratum({"A": [3, 2, 2, 2], "B": [5, 1, 1, 1, 1]})
    folds = partition_units(roster, k=3, digest="sha256:0000", clusters=clusters, strata=strata)
    assert [sorted({u.site for u in f}) for f in folds] == [
        ["Ac0", "Bc0"],
        ["Ac1", "Ac2", "Bc1", "Bc3"],
        ["Ac3", "Bc2", "Bc4"],
    ]
    assert [dict(Counter(u.label for u in f)) for f in folds] == [
        {"A": 3, "B": 5},
        {"A": 4, "B": 2},
        {"A": 2, "B": 2},
    ]


def test_stratified_fold_sizes_can_differ_by_more_than_one():
    """Three strata of three units at k=2 give 6 and 3, not 5 and 4: with equal-sized
    things to deal out, each stratum's fold list is non-increasing and fold 0 takes
    every stratum's ceiling. Pinned because it contradicts
    `test_partition_sizes_differ_by_at_most_one`, which holds for an unstratified
    split only — evening the totals out is what would divide a stratum's share
    unevenly, and that is the thing being declared away.

    The bound is the stratum count here and *nothing* once clusters are uneven:
    `test_no_cluster_is_split_across_a_stratified_fold` is two strata at k=2 with
    sizes 10 and 5, because the one-large-cluster floor applies per stratum and the
    floors add.
    """
    roster, strata = _by_stratum({"a": 3, "b": 3, "c": 3})
    folds = partition_units(roster, k=2, digest="sha256:0000", strata=strata)
    assert [len(f) for f in folds] == [6, 3]
    assert [dict(Counter(u.label for u in f)) for f in folds] == [
        {"a": 2, "b": 2, "c": 2},
        {"a": 1, "b": 1, "c": 1},
    ]


def test_a_k_past_a_single_stratum_leaves_a_fold_holding_none_of_it():
    """`validate` bounds `k` by `fold_basis` over the **whole roster**, which
    stratification turns into a per-stratum question nothing checks: 6 clusters here,
    so k=3 validates cleanly, but stratum `B` has only 2 clusters and reaches only 2
    folds — the third holds no `B` at all, while § Repeat kinds still calls the fold
    stratified.

    Pinned as behaviour, not fixed: the partitioner stays total and visibly short of a
    stratum rather than dividing a cluster to fill the fold, which is the same stance
    `test_more_folds_than_clusters_leaves_folds_empty_rather_than_raising` takes. The
    missing per-stratum bound is a `validate` gap, recorded rather than closed here.
    """
    roster, clusters, strata = _clustered_by_stratum({"A": [2, 2, 2, 2], "B": [2, 2]})
    assert fold_basis(roster, "site") == 6, "so k=3 is well inside what validate allows"
    folds = partition_units(roster, k=3, digest="sha256:0000", clusters=clusters, strata=strata)
    assert [dict(Counter(u.label for u in f)) for f in folds] == [
        {"A": 4, "B": 2},
        {"A": 2, "B": 2},
        {"A": 2},
    ]


def test_the_same_digest_reproduces_the_same_stratified_split():
    roster, strata = _by_stratum({"0": 8, "1": 4})
    a = partition_units(roster, k=2, digest="sha256:0000", strata=strata)
    b = partition_units(roster, k=2, digest="sha256:0000", strata=strata)
    assert [[u.key for u in f] for f in a] == [[u.key for u in f] for f in b]


def test_a_unit_missing_from_the_stratum_mapping_is_a_core_defect():
    """Total over the roster or not at all, the rule `clusters` already follows: a
    `.get` default would give the unit a stratum of its own and balance the split
    around a value nobody declared."""
    roster, strata = _by_stratum({"0": 4, "1": 2})
    del strata["1_0"]
    with pytest.raises(KeyError):
        partition_units(roster, k=2, digest="sha256:0000", strata=strata)


def test_writing_a_unit_field_raises_the_documented_code() -> None:
    unit = Unit(key="u1")

    with pytest.raises(ContractError) as exc:
        unit.key = "u2"  # type: ignore[misc]

    assert exc.value.code == "E-UNIT-IMMUTABLE"


def test_writing_through_a_units_attributes_raises_the_documented_code() -> None:
    """`reference.md` names this exact expression: a roster is shared across
    conditions, so this write would change what the next condition measures."""
    unit = Unit(key="u1", attributes={"site": "A"})

    with pytest.raises(ContractError) as exc:
        unit.attributes["scored"] = True  # type: ignore[index]

    assert exc.value.code == "E-UNIT-IMMUTABLE"


def test_deleting_a_units_attribute_raises_the_documented_code() -> None:
    unit = Unit(key="u1", attributes={"site": "A"})

    with pytest.raises(ContractError) as exc:
        del unit.attributes["site"]  # type: ignore[misc]

    assert exc.value.code == "E-UNIT-IMMUTABLE"


def test_a_unit_still_reads_normally() -> None:
    unit = Unit(key="u1", paths=("a.csv",), attributes={"site": "A"})

    assert unit.key == "u1"
    assert unit.paths == ("a.csv",)
    assert unit.attributes["site"] == "A"
    assert unit.site == "A"
    assert len(unit.attributes) == 1
    assert dict(unit.attributes) == {"site": "A"}
    assert {unit} == {Unit(key="u1")}  # hashable by key


def test_a_units_attributes_copy_the_input_mapping() -> None:
    """`_FrozenAttributes.__init__` must copy rather than alias its argument: if it
    stored the caller's dict directly, mutating that dict after construction would
    silently change what the unit reports, defeating the immutability this task adds."""
    source = {"site": "A"}
    unit = Unit(key="u1", attributes=source)

    source["site"] = "B"
    source["extra"] = "new"

    assert unit.attributes["site"] == "A"
    assert "extra" not in unit.attributes


def test_a_glob_source_cannot_supply_a_declared_attribute(input_dir: Path):
    """`reference.md` § Validation's "Attributes have a source" row uses this exact
    case: `data.units.attributes` names `label` under `from: {glob: "*.dcm"}`,
    which yields a key and a path and nothing else. `_from_glob` built every unit
    with `attributes={}` without reading the declaration, so the config validated
    clean and every `unit.label` raised at run time instead."""
    with pytest.raises(ContractError) as e:
        resolve_units(
            {"from": {"glob": "*.dcm"}, "key": "path", "attributes": ["label"]}, input_dir
        )
    assert e.value.code == "E-UNITS-ATTR-MISSING"
    assert "label" in str(e.value)


def test_a_glob_source_reports_a_reserved_attribute_name_as_reserved(input_dir: Path):
    """Ordered as `_from_table` orders it, so one declaration draws one code
    whichever source it sits under: `key`, `paths` and `attributes` are refused as
    reserved rather than as unsourced."""
    with pytest.raises(ContractError) as e:
        resolve_units(
            {"from": {"glob": "*.dcm"}, "key": "path", "attributes": ["paths"]}, input_dir
        )
    assert e.value.code == "E-UNITS-ATTR-RESERVED"


def test_a_glob_source_with_no_declared_attributes_still_resolves(input_dir: Path):
    units, _, _ = resolve_units(
        {"from": {"glob": "*.dcm"}, "key": "path", "attributes": []}, input_dir
    )
    assert [u.key for u in units] == ["top.dcm"]


def test_rows_sharing_a_key_collapse_to_one_unit():
    """`collapse="mean"` here applies to every column, including the non-numeric
    `site` — a config shape task 2's row-243 check refuses at `validate` time
    (`collapse: mean` over a non-numeric column). It is legal input to this
    *function*, which must stay total over the constant case regardless of what
    `validate` will later reject, so `site` collapsing cleanly via the
    "constant needs no rule" path is not evidence the config itself is legal."""
    units = [
        Unit(key="p1", paths=(), attributes={"read_id": "r1", "depth": 10, "site": "A"}),
        Unit(key="p1", paths=(), attributes={"read_id": "r2", "depth": 20, "site": "A"}),
        Unit(key="p2", paths=(), attributes={"read_id": "r3", "depth": 30, "site": "B"}),
    ]
    collapsed, counts = collapse_measurements(units, by="read_id", collapse="mean")
    assert [u.key for u in collapsed] == ["p1", "p2"]
    assert counts == [2, 1]
    assert collapsed[0].depth == 15.0  # mean of 10 and 20
    assert collapsed[0].site == "A"  # non-numeric, constant: carried
    assert "read_id" not in collapsed[0].attributes  # the measurement axis is consumed


def test_mean_over_three_measurements_is_a_mean_and_not_a_median():
    """Every other `mean` case here collapses two symmetric values (10 and 20 →
    15 under either rule), so none of them can tell `mean` from `median`. Three
    asymmetric values can, which is what makes this the input-path half of the
    pair that pins the step path and this one to one shared `apply_rule`."""
    units = [
        Unit(key="p1", paths=(), attributes={"read_id": "r1", "depth": 10}),
        Unit(key="p1", paths=(), attributes={"read_id": "r2", "depth": 20}),
        Unit(key="p1", paths=(), attributes={"read_id": "r3", "depth": 60}),
    ]
    collapsed, _ = collapse_measurements(units, by="read_id", collapse="mean")
    assert collapsed[0].depth == 30.0


def test_median_and_sum_are_collapse_rules():
    units = [
        Unit(key="p1", paths=(), attributes={"read_id": "r1", "depth": 10}),
        Unit(key="p1", paths=(), attributes={"read_id": "r2", "depth": 20}),
        Unit(key="p1", paths=(), attributes={"read_id": "r3", "depth": 60}),
    ]
    median_collapsed, _ = collapse_measurements(units, by="read_id", collapse="median")
    assert median_collapsed[0].depth == 20
    sum_collapsed, _ = collapse_measurements(units, by="read_id", collapse="sum")
    assert sum_collapsed[0].depth == 90


def test_mode_breaks_a_genuine_tie_by_whichever_value_appeared_first():
    """`reference.md` § What isn't a repeat pins the tie-break: `mode` breaks a
    tie "by whichever tied value appeared first" — resolution order, not an
    incidental property of `Counter.most_common`. `"b"` and `"a"` each appear
    twice; `"b"` is first in resolution order, so it must win."""
    units = [
        Unit(key="p1", paths=(), attributes={"read_id": "r1", "label": "b"}),
        Unit(key="p1", paths=(), attributes={"read_id": "r2", "label": "a"}),
        Unit(key="p1", paths=(), attributes={"read_id": "r3", "label": "a"}),
        Unit(key="p1", paths=(), attributes={"read_id": "r4", "label": "b"}),
    ]
    collapsed, _ = collapse_measurements(units, by="read_id", collapse="mode")
    assert collapsed[0].label == "b"


def test_the_constant_shortcut_does_not_corrupt_a_numeric_aggregation():
    """The "constant needs no rule" shortcut exists to let a non-numeric rule
    survive constant values it can't operate on (`mean` over a constant `site`
    string). It must not also swallow a genuine numeric aggregation: `sum` over
    two constant depths is still a sum, not a no-op — `sum([5, 5])` is `10`,
    not `5`, even though the two reads agree."""
    assert apply_rule("sum", [5, 5]) == 10
    assert apply_rule("sum", [1000, 1000]) == 2000
    assert apply_rule("sum", [1, 2]) == 3  # already covered above; kept for contrast
    assert apply_rule("mean", [5, 5]) == 5  # mean over constant numeric: still a mean
    assert apply_rule("mean", ["A", "A"]) == "A"  # round-1 behaviour, must survive


def test_a_bogus_rule_raises_even_over_a_single_trivially_constant_value():
    """The rule-name check runs before the constant shortcut, so a bogus rule
    still raises even where the shortcut's own condition (`values` all equal)
    is trivially true for a single-member group — the common case for an
    unmeasured unit that never repeats."""
    with pytest.raises(ContractError) as e:
        apply_rule("bogus", ["A"])
    assert e.value.code == "E-UNITS-COLLAPSE-RULE"


def test_a_constant_boolean_column_carries_rather_than_summing():
    """`bool` is deliberately outside the numeric gate, so the constant shortcut
    still fires for it. `isinstance(True, int)` is True in Python, and without
    the explicit exclusion a constant boolean column would be summed — a
    different intent than summing depths.

    Pinning it because the exclusion was a claim in a comment that nothing
    provided: including `bool` as numeric left every test in this file passing.

    The asymmetry this leaves — `sum([True, False])` is `1`, an int — is real and
    is deliberately not fixed here: `sum` over a boolean column is incoherent
    whichever branch it takes, and refusing it belongs to the validate-time
    collapse-rule/column-type check rather than to this function."""
    assert apply_rule("sum", [True, True]) is True
    assert apply_rule("sum", [False, False]) is False


def test_a_column_absent_from_the_collapse_map_falls_back_to_first():
    """`collapse` may be a per-column map; a column it does not name falls back
    to `first` rather than being averaged. `batch` differs across the two rows,
    so this is the case `collapse_measurements`'s blanket `"mean"` test above
    cannot reach: it exercises `apply_rule`'s `first` branch on values that are not
    already constant."""
    units = [
        Unit(key="p1", paths=(), attributes={"read_id": "r1", "depth": 10, "batch": "b1"}),
        Unit(key="p1", paths=(), attributes={"read_id": "r2", "depth": 20, "batch": "b2"}),
    ]
    collapsed, counts = collapse_measurements(units, by="read_id", collapse={"depth": "mean"})
    assert counts == [2]
    assert collapsed[0].depth == 15.0
    assert collapsed[0].batch == "b1"


def _write_reads(input_dir: Path, body: str, name: str = "reads.csv") -> Path:
    """A table whose rows are measurements of a unit, not units.

    Written as text rather than through a row-builder because what these tests
    are about is exactly what `csv.DictReader` hands back — every value a `str`,
    a short row's missing column a `None` — and a builder that took Python values
    would hide the property under test.
    """
    (input_dir / name).write_text(body)
    return input_dir / name


_MEASURED = {
    "from": "reads.csv",
    "key": "patient_id",
    "attributes": ["depth", "read_id"],
    "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
}


def test_duplicate_keys_collapse_when_measurements_is_declared(input_dir: Path):
    _write_reads(
        input_dir,
        "patient_id,read_id,depth\np1,r1,10\np1,r2,20\np2,r3,30\n",
    )
    roster, technical_n, _ = resolve_units(dict(_MEASURED), input_dir)
    assert len(roster) == 2
    assert [u.key for u in roster] == ["p1", "p2"]
    assert technical_n == {"min": 1, "max": 2, "median": 1.5}


def test_a_csv_sourced_numeric_column_collapses_to_a_number(input_dir: Path):
    """The headline: `validate` accepts `mean` over a numeric-looking column
    (`is_measurement_numeric("10")` is `True`), so resolution has to be able to
    compute it. `csv.DictReader` yields `"10"`/`"20"`, and without the coercion
    this is a `TypeError` for `sum`/`median` and a *string* for `mean` over a
    constant column. `15.0` and not `15`: the gate is `float`'s own grammar,
    which is what keeps the predicate and the conversion from parting ways —
    narrowing back to `int` is the tidy-up that would break that."""
    _write_reads(input_dir, "patient_id,read_id,depth\np1,r1,10\np1,r2,20\n")
    roster, _, _ = resolve_units(dict(_MEASURED), input_dir)
    assert roster[0].depth == 15.0
    assert isinstance(roster[0].depth, float)


def test_a_constant_numeric_string_column_collapses_to_a_number_too(input_dir: Path):
    """`apply_rule("mean", ["10", "10"])` returns the *string* `"10"` — its
    constant-column shortcut fires because the strings fail its own isinstance
    gate. Coercing before `apply_rule` sees them is what makes the shortcut's
    numeric-rule exclusion reachable, so this answers `10.0`."""
    _write_reads(input_dir, "patient_id,read_id,depth\np1,r1,10\np1,r2,10\n")
    roster, _, _ = resolve_units(dict(_MEASURED), input_dir)
    assert roster[0].depth == 10.0
    assert not isinstance(roster[0].depth, str)


def test_a_sum_over_csv_strings_is_a_sum_and_not_a_type_error(input_dir: Path):
    """`sum(["10", "20"])` is a bare `TypeError` — no `.code`, and not caught by
    `validate`'s `except ContractError`. Pinned separately from `mean` because
    `sum` reaches a different branch of `apply_rule`."""
    _write_reads(input_dir, "patient_id,read_id,depth\np1,r1,10\np1,r2,20\n")
    decl = dict(_MEASURED, measurements={"by": "read_id", "collapse": {"depth": "sum"}})
    roster, _, _ = resolve_units(decl, input_dir)
    assert roster[0].depth == 30.0


@pytest.mark.parametrize(
    "body",
    [
        "patient_id,read_id,depth\np1,r1,10\np1,r2,north\n",  # a mixed group
        "patient_id,read_id,depth\np1,r1,10\np1,r2,\n",  # an empty cell
        "patient_id,read_id,depth\np1,r1,10\np1,r2\n",  # a short row: depth is None
    ],
    ids=["mixed", "empty-cell", "short-row"],
)
def test_a_numeric_rule_over_a_value_it_cannot_compute_is_refused(input_dir: Path, body: str):
    """Every one of these is arithmetic `apply_rule` cannot do, and every one would
    otherwise leave `resolve_units` as a bare `TypeError` — which escapes
    `validate` itself, since it resolves the roster inside `except ContractError`.
    The identifier is `validate`'s own collapse-type code, not a second one for
    the run-time half of one fault."""
    _write_reads(input_dir, body)
    with pytest.raises(ContractError) as e:
        resolve_units(dict(_MEASURED), input_dir)
    assert e.value.code == "E-DATA-MEASUREMENTS-COLLAPSE-TYPE"


def test_a_column_one_row_lacks_collapses_over_the_rows_that_have_it(input_dir: Path):
    """The short row again, under a rule that *can* answer it: the group is the
    members carrying the column, never an empty list — which is what keeps
    `apply_rule`'s `values[0]` in reach of a value."""
    _write_reads(input_dir, "patient_id,read_id,depth\np1,r1,10\np1,r2\n")
    decl = dict(_MEASURED, measurements={"by": "read_id", "collapse": {"depth": "first"}})
    roster, technical_n, _ = resolve_units(decl, input_dir)
    assert roster[0].depth == "10"
    assert technical_n == {"min": 2, "max": 2, "median": 2}


def test_a_single_member_group_keeps_the_constant_shortcut(input_dir: Path):
    """A non-numeric column under a numeric rule is refused by `validate` (row
    243) whether or not the data happens to be constant — but this function must
    stay total over what `apply_rule` documents as the constant case, or a
    one-measurement-per-unit roster would raise here before `validate` could
    report the real finding with the column's name on it."""
    _write_reads(input_dir, "patient_id,read_id,site\np1,r1,north\np2,r2,south\n")
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["site", "read_id"],
        "measurements": {"by": "read_id", "collapse": {"site": "mean"}},
    }
    roster, technical_n, _ = resolve_units(decl, input_dir)
    assert roster[0].site == "north"
    assert technical_n == {"min": 1, "max": 1, "median": 1}


def test_the_measurement_axis_is_consumed_by_the_collapse(input_dir: Path):
    _write_reads(input_dir, "patient_id,read_id,depth\np1,r1,10\np1,r2,20\n")
    roster, _, _ = resolve_units(dict(_MEASURED), input_dir)
    assert "read_id" not in roster[0].attributes


@pytest.mark.parametrize(
    "measurements",
    [{"collapse": "mean"}, {"by": "", "collapse": "mean"}, {"by": ["read_id"]}, "yes"],
    ids=["no-by", "empty-by", "non-string-by", "not-a-mapping"],
)
def test_a_malformed_measurements_block_is_a_contract_error_not_a_crash(
    input_dir: Path, measurements: object
):
    """`validate._check_units` resolves the roster *before* `_check_measurements`
    reports shape faults, so a malformed block reaches resolution first. A
    `KeyError` or an `AttributeError` here would escape `validate`, which collects
    findings and never raises — and the code is the one `_check_measurements`
    reports for the same shapes."""
    _write_reads(input_dir, "patient_id,read_id,depth\np1,r1,10\np1,r2,20\n")
    with pytest.raises(ContractError) as e:
        resolve_units(dict(_MEASURED, measurements=measurements), input_dir)
    assert e.value.code == "E-DATA-MEASUREMENTS-INVALID"


def test_an_unknown_collapse_rule_is_refused_at_resolution(input_dir: Path):
    _write_reads(input_dir, "patient_id,read_id,depth\np1,r1,10\np1,r2,20\n")
    with pytest.raises(ContractError) as e:
        resolve_units(
            dict(_MEASURED, measurements={"by": "read_id", "collapse": "bogus"}), input_dir
        )
    assert e.value.code == "E-UNITS-COLLAPSE-RULE"


def test_nothing_but_a_contract_error_escapes_resolve_units(input_dir: Path):
    """The adversarial sweep, as one claim: whatever the declaration and whatever
    the table, resolution either answers or raises a `ContractError` carrying a
    code. Anything else escapes `validate`."""
    bodies = [
        "patient_id,read_id,depth\np1,r1,10\np1,r2,north\n",
        "patient_id,read_id,depth\np1,r1,nan\np1,r2,10\n",
        "patient_id,read_id,depth\np1,r1,\np1,r2,\n",
        "patient_id,read_id,depth\np1,r1,10\n",
        "patient_id,read_id,depth\np1,r1,10,extra\np1,r2,20\n",
    ]
    declarations = [
        dict(_MEASURED),
        dict(_MEASURED, measurements={"by": "read_id", "collapse": "sum"}),
        dict(_MEASURED, measurements={"by": "read_id", "collapse": "median"}),
        dict(_MEASURED, measurements={"by": "read_id", "collapse": "mode"}),
        dict(_MEASURED, measurements={"by": "depth", "collapse": "first"}),
        dict(_MEASURED, measurements={"by": "read_id"}),
    ]
    for body in bodies:
        _write_reads(input_dir, body)
        for decl in declarations:
            try:
                resolve_units(dict(decl), input_dir)
            except ContractError as exc:
                assert exc.code.startswith("E-")


def test_the_unit_list_gains_no_new_operation(input_dir: Path):
    """The contract is exactly three operations plus `.train`
    (`reference.md` § The unit list is three operations). `technical_n` is a
    second return value precisely so it cannot become a fourth."""
    _write_reads(input_dir, "patient_id,read_id,depth\np1,r1,10\np1,r2,20\n")
    roster, _, _ = resolve_units(dict(_MEASURED), input_dir)
    assert not hasattr(roster, "technical_n")
    assert not any("technical" in name for name in vars(roster))


def test_duplicate_keys_still_raise_without_measurements(input_dir: Path):
    """The collapse is what makes a repeated key legal. Without the declaration
    it is the duplicate it always was."""
    _write_reads(input_dir, "patient_id,read_id,depth\np1,r1,10\np1,r2,20\n")
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "reads.csv", "key": "patient_id"}, input_dir)
    assert e.value.code == "E-UNITS-KEY-DUPLICATE"


def test_technical_n_is_absent_when_measurements_is_undeclared(input_dir: Path):
    """A design that never measures twice must read exactly as it did before."""
    roster, technical_n, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert len(roster) == 3
    assert technical_n is None


# --- cluster membership, one authority --------------------------------------


def test_clusters_group_units_by_their_declared_attribute():
    """`reference.md` § Clustered units: `cluster_by` names a declared attribute,
    and the mapping it produces is what the partition, the checks and the
    cluster-robust intervals all read. Deliberately uneven — 3 clusters over 5
    units — because equal cluster sizes make a per-unit mapping and a per-cluster
    one indistinguishable."""
    units = [
        Unit(key=f"u{i}", paths=(), attributes={"site": s})
        for i, s in enumerate(["S1", "S1", "S1", "S2", "S3"])
    ]
    roster = UnitList(units)
    assert clusters_of(roster, "site") == {
        "u0": "S1",
        "u1": "S1",
        "u2": "S1",
        "u3": "S2",
        "u4": "S3",
    }
    assert cluster_count(roster, "site") == 3


def test_cluster_membership_is_in_roster_order():
    """Insertion order is roster order, which is what lets a caller needing the
    ordered cluster list derive it here rather than walking the roster again."""
    roster = UnitList(
        [
            Unit(key="u0", paths=(), attributes={"site": "S2"}),
            Unit(key="u1", paths=(), attributes={"site": "S1"}),
            Unit(key="u2", paths=(), attributes={"site": "S2"}),
        ]
    )
    assert list(clusters_of(roster, "site").values()) == ["S2", "S1", "S2"]


def test_a_unit_carrying_no_cluster_value_is_refused():
    """A singleton cluster invented for a unit with no value would make that unit
    its own inferential draw. `reference.md` § Errors validate reports gives this
    the same code `validate` reports for a `cluster_by` naming no attribute."""
    roster = UnitList(
        [
            Unit(key="u0", paths=(), attributes={"site": "S1"}),
            Unit(key="u1", paths=(), attributes={}),
        ]
    )
    with pytest.raises(ContractError) as e:
        clusters_of(roster, "site")
    assert e.value.code == "E-DATA-CLUSTER-UNKNOWN"
    assert "u1" in str(e.value)


def test_cluster_count_reads_the_same_authority():
    """The count is derived from the membership rather than counted separately:
    a count above the number of groups the partitioner can produce is a `k` that
    cannot be satisfied."""
    roster = UnitList([Unit(key=f"u{i}", paths=(), attributes={"site": "S1"}) for i in range(4)])
    assert cluster_count(roster, "site") == 1
    with pytest.raises(ContractError):
        cluster_count(UnitList([Unit(key="u0", paths=(), attributes={})]), "site")


def test_arms_partition_units_by_declared_level_in_roster_order():
    """`reference.md` § Allocation: `from` names "a unit attribute whose values are
    exactly the declared levels". Uneven on purpose — 2 units in `control`, 1 in
    `treatment` — so a caller reading `partition["control"]` back gets a list, not
    a single unit, and roster order survives inside each bucket (`u2` before `u0`
    within `control`, matching insertion order rather than being resorted)."""
    roster = UnitList(
        [
            Unit(key="u2", paths=(), attributes={"arm": "control"}),
            Unit(key="u1", paths=(), attributes={"arm": "treatment"}),
            Unit(key="u0", paths=(), attributes={"arm": "control"}),
        ]
    )
    partition = arms_of(roster, "arm", ["control", "treatment"])
    assert [u.key for u in partition["control"]] == ["u2", "u0"]
    assert [u.key for u in partition["treatment"]] == ["u1"]
    # Every unit in the roster appears in exactly one bucket.
    assert sum(len(units) for units in partition.values()) == len(roster)


def test_arms_stringify_values_before_comparison():
    """`clusters_of`'s own reason: a table yields `str` for every column, but a
    hand-built roster need not, and an arm id is a label rather than a quantity.
    `{'arm': 1}` (an `int`) has to resolve against levels declared as strings."""
    roster = UnitList(
        [
            Unit(key="u0", paths=(), attributes={"arm": 1}),
            Unit(key="u1", paths=(), attributes={"arm": 2}),
        ]
    )
    partition = arms_of(roster, "arm", ["1", "2"])
    assert [u.key for u in partition["1"]] == ["u0"]
    assert [u.key for u in partition["2"]] == ["u1"]


def test_arms_refuse_a_value_naming_no_declared_level():
    """§ Allocation opens `between` with "each unit belongs to exactly one arm" —
    a value naming none of the declared levels leaves that unit in none."""
    roster = UnitList(
        [
            Unit(key="u0", paths=(), attributes={"arm": "control"}),
            Unit(key="u1", paths=(), attributes={"arm": "unknown_arm"}),
        ]
    )
    with pytest.raises(ContractError) as e:
        arms_of(roster, "arm", ["control", "treatment"])
    assert e.value.code == "E-DATA-ASSIGN-LEVELS"
    assert "u1" in str(e.value)
    assert "unknown_arm" in str(e.value)


def test_arms_refuse_a_unit_with_no_value_at_all():
    """The same violation `clusters_of` recognizes for a unit missing its
    attribute entirely — folded into the same code and message as a value naming
    the wrong level, rather than a distinct fault."""
    roster = UnitList(
        [
            Unit(key="u0", paths=(), attributes={"arm": "control"}),
            Unit(key="u1", paths=(), attributes={}),
        ]
    )
    with pytest.raises(ContractError) as e:
        arms_of(roster, "arm", ["control", "treatment"])
    assert e.value.code == "E-DATA-ASSIGN-LEVELS"
    assert "u1" in str(e.value)
    assert "carries no value" in str(e.value)


def test_arms_refuse_a_declared_level_with_no_unit():
    """The other direction of set equality: every unit resolves to a declared
    level, but `treatment` holds none of them, so that arm's condition would
    resolve zero units."""
    roster = UnitList(
        [
            Unit(key="u0", paths=(), attributes={"arm": "control"}),
            Unit(key="u1", paths=(), attributes={"arm": "control"}),
        ]
    )
    with pytest.raises(ContractError) as e:
        arms_of(roster, "arm", ["control", "treatment"])
    assert e.value.code == "E-DATA-ASSIGN-LEVELS"
    assert "treatment" in str(e.value)


def _arm_roster12():
    """12 units, 7 `control` and 5 `treatment` — `tests/test_runner.py`'s
    `_arm_roster12`, restated here so this module's arm tests run against the
    same uneven split: neither half is 6, so an arm cannot be confused with
    the other arm, with half the roster, or with the whole roster by size
    alone."""
    return UnitList(
        [Unit(key=f"c{i}", attributes={"arm": "control"}) for i in range(7)]
        + [Unit(key=f"t{i}", attributes={"arm": "treatment"}) for i in range(5)]
    )


def _arm_plans(roster):
    return {"arm": assignment_for(roster, "arm", None, ["control", "treatment"], "digest")}


def test_assignment_for_by_attribute_realizes_arms_of_with_no_seed_and_no_strata():
    """Step 1 of the seam: `by_attribute` through `ArmPlan` gives exactly what
    `arms_of` gives, and says so about the two fields a draw would fill.

    Both arms' keys are written out literally rather than re-derived from the
    fixture's own `arm` attribute: a test that rebuilds the expectation by
    re-running the membership rule cannot tell a correct partition from a
    wrongly recomputed one, since the same rule produces both.

    `seed is None` and `strata == ()` are the load-bearing halves, not
    decoration — `by_attribute` reads an arm a trial system already assigned,
    so a realized seed here would be a false record of a draw that never
    happened, and `artifacts.build_allocation_document` writes exactly what
    these two fields say."""
    roster = _arm_roster12()
    plan = assignment_for(roster, "arm", {"method": "by_attribute"}, ["control", "treatment"], "d")

    assert plan.levels == ("control", "treatment")
    assert plan.members["control"] == ("c0", "c1", "c2", "c3", "c4", "c5", "c6")
    assert plan.members["treatment"] == ("t0", "t1", "t2", "t3", "t4")
    assert set(plan.members) == {"control", "treatment"}
    assert plan.seed is None
    assert plan.strata == ()

    # The same partition `arms_of` returns, restated as keys — the plan is
    # `arms_of`'s answer carried in a shape a draw can also fill, not a
    # second reading of the column.
    partition = arms_of(roster, "arm", ["control", "treatment"])
    assert plan.members == {
        level: tuple(u.key for u in units) for level, units in partition.items()
    }


def test_assignment_for_resolves_from_against_the_axis_name_and_reads_no_other_column():
    """The `from`-or-axis-name default now lives in `assignment_for` alone —
    `cli._resolved_group_axes` used to resolve it too, and two resolutions of
    one declaration is the defect class this slice closes. A declared `from`
    naming a column that is NOT the axis name is what discriminates: the
    fixture's units carry `arm_column`, and nothing at all under `arm`, so a
    resolution that fell back to the axis name would raise
    `E-DATA-ASSIGN-LEVELS` instead of partitioning."""
    roster = UnitList(
        [
            Unit(key="u0", attributes={"arm_column": "control"}),
            Unit(key="u1", attributes={"arm_column": "treatment"}),
        ]
    )
    block = {"method": "by_attribute", "from": "arm_column"}
    plan = assignment_for(roster, "arm", block, ["control", "treatment"], "digest")
    assert plan.members == {"control": ("u0",), "treatment": ("u1",)}

    # The control that must report: with no `from`, the axis name is the
    # column, and this fixture has no `arm` attribute to read.
    with pytest.raises(ContractError) as e:
        assignment_for(roster, "arm", None, ["control", "treatment"], "digest")
    assert e.value.code == "E-DATA-ASSIGN-LEVELS"


def test_assignment_for_refuses_a_method_it_has_never_heard_of():
    """**Fail-closed, and this is the regression it prevents.** `assignment_for`
    allows `by_attribute` and refuses everything else, rather than denying the
    methods that happen to draw today. A fourth method added to
    `validate.ASSIGN_METHODS` — and to nothing else — would otherwise validate
    clean and then be silently partitioned by a column read, which is the
    fallback the whole guard exists to prevent. `adaptive` stands in for that
    method here: it is in no enum, and the fixture's units DO carry `arm`, so a
    denylist would have returned a plausible-looking partition instead of
    raising.

    Reachable only through a core defect: `validate` refuses an out-of-enum
    method as `E-DATA-ASSIGN-METHOD` and returns before `run` reaches this."""
    roster = _arm_roster12()
    with pytest.raises(NotImplementedError) as e:
        assignment_for(roster, "arm", {"method": "adaptive"}, ["control", "treatment"], "d")
    assert "adaptive" in str(e.value)
    assert "by_attribute" in str(e.value)
    assert "adaptive" not in DRAWN_ASSIGN_METHODS


def test_assignment_for_takes_the_by_attribute_path_for_an_unnamed_method():
    """An absent block, a non-mapping one, and a block with no `method` all
    take the `by_attribute` path — the same default `validate._check_assign`
    falls back to. Only `random` and `blocked` divert, so no method that
    *draws* can reach a column read by falling through."""
    roster = _arm_roster12()
    expected = ("c0", "c1", "c2", "c3", "c4", "c5", "c6")
    for block in (None, {}, {"from": "arm"}):
        plan = assignment_for(roster, "arm", block, ["control", "treatment"], "digest")
        assert plan.members["control"] == expected
        assert plan.seed is None


def _random_roster(n: int) -> UnitList:
    """`n` units with no attributes at all — a drawn axis has no column to
    read, so unlike `_arm_roster12` these carry nothing an `arm`-style
    attribute could leak membership from."""
    return UnitList([Unit(key=f"u{i:02d}", paths=(), attributes={}) for i in range(n)])


def test_a_random_draw_honours_an_unequal_ratio():
    """12 units, `ratio: {control: 1, treatment: 2}` -> 4 and 8. Deliberately
    unequal AND not a half: 4/8 cannot be confused with 6/6, with 12, or with
    each other — the fixture trap the plan's Global Constraints name, restated
    for a draw rather than a read. Exact membership under a pinned seed is
    asserted literally, not re-derived from the apportionment rule under
    test."""
    roster = _random_roster(12)
    block = {"method": "random", "ratio": {"control": 1, "treatment": 2}, "seed": 7}
    plan = assignment_for(roster, "arm", block, ["control", "treatment"], "digest")

    assert plan.seed == 7
    assert len(plan.members["control"]) == 4
    assert len(plan.members["treatment"]) == 8
    assert plan.members["control"] == ("u07", "u11", "u03", "u10")
    assert plan.members["treatment"] == (
        "u08",
        "u04",
        "u09",
        "u01",
        "u00",
        "u06",
        "u02",
        "u05",
    )


def test_a_random_draw_is_a_partition():
    """Every unit in exactly one arm — the coverage half of the property
    `arms_of` guarantees for a read assignment, which a draw must too. Reuses
    the 12-unit, `{control: 1, treatment: 2}` fixture from the ratio test
    above: an equal split over a roster divisible by the arm count would make
    a coverage bug (a duplicate, or a dropped unit) invisible by size alone.

    The *non-emptiness* half is not asserted here and deliberately so: 12
    units at 1:2 cannot floor either level to zero, so an assertion of it
    against this fixture could never fail — it would document the property
    rather than sense it.
    `test_a_drawn_arm_the_ratio_apportions_no_unit_to_is_refused` below owns
    that half, against a fixture where a size of 0 is reachable."""
    roster = _random_roster(12)
    block = {"method": "random", "ratio": {"control": 1, "treatment": 2}, "seed": 7}
    plan = assignment_for(roster, "arm", block, ["control", "treatment"], "digest")

    seen = plan.members["control"] + plan.members["treatment"]
    assert len(seen) == len(set(seen)) == len(roster)
    assert set(seen) == {unit.key for unit in roster}


def test_the_same_seed_draws_the_same_arms():
    """Two calls with the same pinned seed draw the same arms.

    **The control**: a different pinned seed draws different arms. Without
    it, an implementation that ignored the seed entirely — always shuffling
    from an unseeded, or a constant, RNG state — would still pass the first
    half by accident."""
    roster = _random_roster(12)
    levels = ["control", "treatment"]
    first = assignment_for(roster, "arm", {"method": "random", "seed": 1}, levels, "digest")
    again = assignment_for(roster, "arm", {"method": "random", "seed": 1}, levels, "digest")
    assert first.members == again.members

    different = assignment_for(roster, "arm", {"method": "random", "seed": 2}, levels, "digest")
    assert different.members != first.members


def test_a_ratio_that_does_not_divide_the_roster_is_reported_not_rounded_away():
    """13 units at `ratio: {a: 1, b: 2}` — sum 3 does not divide 13, so there is
    no exact solution. `_apportion` floors each level's exact share (4.333 ->
    4, 8.667 -> 8, 12 of the 13 accounted for) and hands the 13th, leftover
    unit to the largest fractional part rather than the largest level by
    name: `b`'s 0.667 beats `a`'s 0.333, so that 13th unit — the last element
    of `b`'s slice of the seed-3 shuffle — lands in `b`, giving 4 and 9. The
    realized sizes are stated exactly rather than a false "even enough"
    claim.

    Membership is asserted literally beside the sizes, not sizes alone: this
    is the one roster in this file whose remainder unit is *distributed* by
    `_apportion` rather than falling out of an exact division, so it is the
    one place a slicing bug that keeps the sizes right while cutting the
    shuffle at the wrong offsets would show."""
    roster = _random_roster(13)
    block = {"method": "random", "ratio": {"a": 1, "b": 2}, "seed": 3}
    plan = assignment_for(roster, "arm", block, ["a", "b"], "digest")

    assert len(plan.members["a"]) == 4
    assert len(plan.members["b"]) == 9
    assert len(plan.members["a"]) + len(plan.members["b"]) == 13
    assert plan.members["a"] == ("u12", "u11", "u01", "u06")
    assert plan.members["b"] == (
        "u00",
        "u04",
        "u10",
        "u07",
        "u05",
        "u02",
        "u08",
        "u09",
        "u03",
    )


def test_apportion_hands_the_remainder_to_the_largest_fraction():
    """**`_apportion`'s rule, pinned directly.** Every fixture drawn through
    `assignment_for` above happens to agree with the mutant that gives the
    remainder to the *last* entries in reverse order — 13 units at 1:2 puts the
    leftover in `b` either way — so the whole of Hamilton's rule was enforced
    by nothing. These two cases each kill a different wrong rule:

    - `(10, [1, 1, 1])` -> `[4, 3, 3]`. Every fraction is equal (0.333), so
      this is the *tie-break* alone: declared order wins, and the reverse-order
      mutant gives `[3, 3, 4]`.
    - `(10, [3, 3, 1])` -> `[4, 4, 2]`. Here the largest fraction (0.429)
      belongs to the *smallest* weight, so it discriminates "largest fractional
      part" from every weight-magnitude heuristic at once: giving the remainder
      to the largest weight, or to the first entry, both give `[5, 4, 1]`.

    `(10, [1, 2, 4])` would have been the natural third case and is left out on
    purpose — it coincides with the reverse-order mutant, the same accident that
    let the mutant survive the suite in the first place."""
    assert _apportion(10, [1, 1, 1]) == [4, 3, 3]
    assert _apportion(10, [3, 3, 1]) == [4, 4, 2]
    # The floors themselves, so a mutation that distributed the whole of `n`
    # by fractions alone is not mistaken for the rule above.
    assert _apportion(12, [1, 2]) == [4, 8]


@pytest.mark.parametrize(
    ("n", "ratio", "levels", "expected_empty"),
    [
        (10, {"a": 1, "b": 1000}, ["a", "b"], "a"),
        (2, None, ["a", "b", "c"], "c"),
    ],
    ids=["skewed-ratio", "fewer-units-than-levels"],
)
def test_a_drawn_arm_the_ratio_apportions_no_unit_to_is_refused(n, ratio, levels, expected_empty):
    """A drawn arm with no units is the same fault as a read one, and carries
    the same code. `arms_of` refuses "a declared level no unit's value names —
    that arm's condition would resolve zero units" as `E-DATA-ASSIGN-LEVELS`,
    and `reference.md` § Allocation states it method-agnostically ("An arm no
    unit resolves to is already refused, as `E-DATA-ASSIGN-LEVELS`") in the
    very sentence that contrasts it with the thin-but-nonzero cell
    `limits.min_units_per_cell` does not yet warn about. A hard refusal routed
    into that warning-shaped gap is what this test exists to prevent.

    Two routes to a size of 0, so no single wrong guard covers both:

    - `{a: 1, b: 1000}` over 10 units floors `a` to 0 while `b` takes all ten.
      **`validate` approves this ratio** — the keys are exactly the levels and
      both values are finite positives — so it is the validate-clean-then-
      disagree shape, caught only at the draw.
    - 2 units over 3 levels leaves `c` empty under equal allocation, with no
      `ratio` declared at all: a guard written as a check on the declared
      ratio rather than on the realized sizes would miss it entirely.

    The message names the empty level, so a raise that reported the wrong one
    (or all of them) is not mistaken for this one."""
    roster = _random_roster(n)
    block = {"method": "random", "seed": 5}
    if ratio is not None:
        block["ratio"] = ratio
    with pytest.raises(ContractError) as e:
        assignment_for(roster, "arm", block, levels, "digest")
    assert e.value.code == "E-DATA-ASSIGN-LEVELS"
    assert expected_empty in str(e.value)
    assert "resolves zero of them" in str(e.value)


def test_a_drawn_arm_of_one_unit_is_not_refused():
    """**The control the refusal above needs.** 3 units over 3 levels gives
    every arm exactly one unit — the thinnest partition that is still a
    partition — and must draw, not raise. A guard written against "an arm
    smaller than the others" or "an arm below some floor" rather than against
    an arm of *zero* would fail here, and `reference.md` § Allocation is
    explicit that a single-unit arm "is not the uncovered case either"."""
    roster = _random_roster(3)
    plan = assignment_for(roster, "arm", {"method": "random", "seed": 5}, ["a", "b", "c"], "d")
    assert [len(plan.members[level]) for level in ("a", "b", "c")] == [1, 1, 1]
    assert sorted(k for arm in plan.members.values() for k in arm) == ["u00", "u01", "u02"]


_STRATUM_SITES = ["A", "B", "A", "C", "A", "B", "A", "B", "A", "C", "A", "B"]
"""12 units over three strata of DIFFERENT sizes — `site` A×6, B×4, C×2 — so an
equal two-arm draw that balanced only overall (6/6) is not forced to leave any
one stratum even, and C, at two units, is the stratum a whole-roster cut splits
lopsidedly most easily. Interleaved rather than grouped by site so `blocked`'s
own blocks, which read roster order, do not coincide with the strata: a fixture
whose block boundaries fell on stratum boundaries would make an unstratified
`blocked` draw stratified by accident."""


def _stratum_roster() -> UnitList:
    return UnitList(
        [
            Unit(key=f"u{i:02d}", paths=(), attributes={"site": site})
            for i, site in enumerate(_STRATUM_SITES)
        ]
    )


def _per_stratum(plan, levels: tuple[str, str]) -> dict[str, tuple[int, int]]:
    """Each site's per-arm counts, `{site: (level0 count, level1 count)}`."""
    counts = {site: [0, 0] for site in set(_STRATUM_SITES)}
    for i, level in enumerate(levels):
        for key in plan.members[level]:
            counts[_STRATUM_SITES[int(key[1:])]][i] += 1
    return {site: (pair[0], pair[1]) for site, pair in counts.items()}


def test_an_unstratified_arm_draw_of_the_same_fixture_is_lopsided():
    """**The oracle the two stratified tests below rest on, and the reason the
    seed is 11 rather than any pinned number.** The mutation those tests exist to
    catch is "ignore `stratify_by`, draw over the whole roster" — and against a
    fixture whose strata happen to come out even under the unstratified draw,
    that mutation passes them. It does not here: at seed 11 the unstratified
    `random` draw gives A 5/1, B 1/3 and C 0/2, and the unstratified `blocked`
    draw gives B 3/1 and C 0/2. Every one of those differs from the stratified
    answer asserted below, so dropping stratification fails both tests rather
    than a fraction of the time.

    The seed was chosen by running exactly this draw over candidate seeds, not
    by assuming a lopsided one; this test is that choice, written down and
    re-checked on every run rather than left in a scratch script."""
    roster = _stratum_roster()
    levels = ("control", "treatment")

    unstratified = assignment_for(roster, "arm", {"method": "random", "seed": 11}, levels, "d")
    assert _per_stratum(unstratified, levels) == {"A": (5, 1), "B": (1, 3), "C": (0, 2)}

    blocked = assignment_for(roster, "arm", {"method": "blocked", "seed": 11}, levels, "d")
    assert _per_stratum(blocked, levels) == {"A": (3, 3), "B": (3, 1), "C": (0, 2)}


@pytest.mark.parametrize("stratify_by", [["site"], "site"], ids=["list", "bare-string"])
def test_a_stratified_draw_balances_arms_within_every_stratum(stratify_by):
    """`reference.md` § Allocation's own example — `stratify_by: [site]`,
    "balance arms on these" — over 12 units in sites A(6)/B(4)/C(2) at two equal
    arms. Each stratum's own per-arm counts are asserted exactly: A 3/3, B 2/2,
    C 1/1.

    **Why these numbers discriminate**, rather than agreeing with the bug they
    exist to catch: the sibling test above pins what the *same* roster and the
    *same* seed give with no stratification — A 5/1, B 1/3, C 0/2 — so a draw
    that ignored `stratify_by` and cut the shuffled roster 6/6 fails all three
    assertions here, not just the small stratum's. The totals are 6/6 either
    way, which is exactly why a whole-roster size assertion would prove nothing
    and is not what this test makes.

    A bare `stratify_by: site` balances the same way a list does: presence and
    shape are read structurally, `validate`'s own convention for the field, so a
    draw written against `isinstance(x, list)` would silently ignore the bare
    form while `validate` reports it as non-empty."""
    levels = ("control", "treatment")
    plan = assignment_for(
        _stratum_roster(),
        "arm",
        {"method": "random", "seed": 11, "stratify_by": stratify_by},
        levels,
        "digest",
    )
    assert _per_stratum(plan, levels) == {"A": (3, 3), "B": (2, 2), "C": (1, 1)}
    assert plan.seed == 11
    assert plan.strata == ("site",)
    assert sorted(k for arm in plan.members.values() for k in arm) == [
        f"u{i:02d}" for i in range(12)
    ]

    # **Membership, not only counts — and this is the half no count assertion
    # can carry.** `_apportion` FORCES the counts above: each stratum's split is
    # decided by its size and the ratio before any number is drawn, so a draw
    # that never shuffled at all (arms decided by roster order) or that ignored
    # the seed entirely would produce the identical 3/3, 2/2, 1/1 and pass every
    # count assertion in this file. Exact keys at a pinned seed are what makes
    # the shuffle and the seed load-bearing, and the seed-12 half below is what
    # makes the SEED load-bearing rather than just some fixed permutation.
    assert plan.members["control"] == ("u04", "u00", "u02", "u01", "u11", "u09")
    assert plan.members["treatment"] == ("u10", "u08", "u06", "u07", "u05", "u03")

    other = assignment_for(
        _stratum_roster(),
        "arm",
        {"method": "random", "seed": 12, "stratify_by": stratify_by},
        levels,
        "digest",
    )
    assert _per_stratum(other, levels) == {"A": (3, 3), "B": (2, 2), "C": (1, 1)}
    assert set(other.members["control"]) != set(plan.members["control"])


def test_a_stratified_blocked_draw_balances_arms_within_every_stratum():
    """The same balance under `blocked`, which is a stratified permuted-block
    design: the block loop runs inside each stratum, over that stratum's units in
    roster order, rather than over the whole roster.

    A(6) at `block_size` 4 (`auto` over two equal levels) is one whole block and
    a trailing 2, so 3/3; B(4) is one whole block, 2/2; C(2) is one trailing
    block, 1/1. **Those counts are forced by the blocking rule rather than by the
    seed**, which is the point — and the sibling test above is what keeps this
    from being vacuous, pinning the unstratified `blocked` draw at the same seed
    as B 3/1 and C 0/2. A mutant that cut the whole roster into blocks and
    ignored the strata fails here on both.

    The strata are interleaved in the roster, so a mutant that blocked the whole
    roster does not reproduce the per-stratum blocks by accident: its first block
    holds A, B, A, C."""
    levels = ("control", "treatment")
    plan = assignment_for(
        _stratum_roster(),
        "arm",
        {"method": "blocked", "seed": 11, "stratify_by": ["site"]},
        levels,
        "digest",
    )
    assert _per_stratum(plan, levels) == {"A": (3, 3), "B": (2, 2), "C": (1, 1)}
    assert plan.strata == ("site",)


def test_a_stratified_draw_balances_within_each_combination_of_two_attributes():
    """Two names in `stratify_by` are one stratum per *combination* of their
    values, not one per name: 12 units crossing `site` A/B with `sex` f/m into
    four groups of 3, drawn 2/1 by an unequal ratio inside each.

    A draw that stratified on only the first name would give the four cells
    counts summing correctly per site but free within it — 3/0 in one cell and
    0/3 in another are both reachable — so asserting every cell at (2, 1) is
    what distinguishes the composite key from either name alone."""
    roster = UnitList(
        [
            Unit(
                key=f"u{i:02d}",
                paths=(),
                attributes={"site": "AB"[i % 2], "sex": "fm"[(i // 2) % 2]},
            )
            for i in range(12)
        ]
    )
    levels = ("control", "treatment")
    plan = assignment_for(
        roster,
        "arm",
        {
            "method": "random",
            "seed": 3,
            "stratify_by": ["site", "sex"],
            "ratio": {"control": 2, "treatment": 1},
        },
        levels,
        "digest",
    )
    assert plan.strata == ("site", "sex")
    cells: dict[tuple[str, str], list[int]] = {}
    by_key = {unit.key: unit for unit in roster}
    for i, level in enumerate(levels):
        for key in plan.members[level]:
            unit = by_key[key]
            cells.setdefault((unit.attributes["site"], unit.attributes["sex"]), [0, 0])[i] += 1
    assert sorted(cells) == [("A", "f"), ("A", "m"), ("B", "f"), ("B", "m")]
    assert all(counts == [2, 1] for counts in cells.values())


def test_a_stratum_no_resolved_unit_carries_is_not_drawn_as_one_stratum():
    """A `stratify_by` naming a `sweep.groups` axis is legal against § Validation's
    *Allocation strata exist* — the row admits an axis name — but an axis's
    membership is *realized* by an earlier draw rather than carried as a column,
    so it can only be read out of that axis's plan. With no such plan in
    `resolved`, drawing it as a single "no value" stratum would be an
    unstratified draw wearing a stratified record: every unit in one group,
    `strata` recording a balance that never happened.

    So the assertion is the raise, and the message names the two declarations
    that reach it by their codes — a later axis
    (`E-DATA-ASSIGN-STRATIFY-FORWARD`) and a name nothing declares
    (`E-DATA-ASSIGN-STRATIFY-UNKNOWN`) — because the raise cannot tell them
    apart from its own arguments. Both empty and non-empty `resolved` are
    exercised: an axis this draw comes *before* is absent from the snapshot it
    is handed, which is the whole of what "forward-only" means at this level.
    The control that this is not simply "any name raises" is every stratified
    test above, whose `site` draws, and
    `test_an_axis_may_stratify_on_an_earlier_axis` below, whose `sex` does."""
    roster = _stratum_roster()
    later = assignment_for(roster, "sex", {"method": "random", "seed": 3}, ["f", "m"], "d")
    for method in ("random", "blocked"):
        for resolved in (None, {}, {"cohort": later}):
            with pytest.raises(NotImplementedError) as e:
                assignment_for(
                    roster,
                    "arm",
                    {"method": method, "seed": 11, "stratify_by": ["sex"]},
                    ["control", "treatment"],
                    "digest",
                    None,
                    resolved,
                )
            assert "'sex'" in str(e.value)
            assert "E-DATA-ASSIGN-STRATIFY-FORWARD" in str(e.value)
            assert "E-DATA-ASSIGN-STRATIFY-UNKNOWN" in str(e.value)


def _sex_plan() -> ArmPlan:
    """The earlier axis, drawn — six `f` and six `m` over the 12-unit fixture,
    with no `sex` column anywhere in the roster. That absence is the point: a
    drawn axis leaves nothing to read, so a second axis stratifying on it has
    only this plan to balance within."""
    return assignment_for(
        _stratum_roster(), "sex", {"method": "random", "seed": 7}, ["f", "m"], "digest"
    )


def test_an_axis_may_stratify_on_an_earlier_axis():
    """`experimental-designs.md` § Between-subjects factorial: "Axes resolve in
    declaration order and `stratify_by` may name an earlier axis" — the both-
    randomized row of `reference.md` § Expansion modes' table, two `random` axes
    with the second stratifying on the first.

    **`arm` is balanced WITHIN each `sex` arm**, and neither `sex` nor any
    stand-in for it is a unit attribute here, so the balance can only have come
    from the earlier plan's realized membership. A draw that ignored `resolved`
    would raise (the test above); one that read a column would find none.

    **Membership at a pinned seed, not only counts**, for the reason task 12's
    surviving mutation established: `_apportion` FORCES 3/3 inside each stratum
    of six, so every count assertion here is satisfied by a draw that never
    shuffled, ignored its seed, or split the strata the wrong way round. The
    exact keys, and the seed-12 half that must differ from them, are what make
    the RNG load-bearing on this path specifically."""
    sex = _sex_plan()
    levels = ("control", "treatment")
    plan = assignment_for(
        _stratum_roster(),
        "arm",
        {"method": "random", "seed": 11, "stratify_by": ["sex"]},
        levels,
        "digest",
        None,
        {"sex": sex},
    )
    assert plan.strata == ("sex",)

    for arm in sex.members.values():
        # Six units in each `sex` arm, apportioned 3/3 within it — the balance
        # `stratify_by` declares. Asserted per `sex` arm rather than over the
        # roster, whose 6/6 total an unstratified draw also produces.
        assert len(set(arm) & set(plan.members["control"])) == 3
        assert len(set(arm) & set(plan.members["treatment"])) == 3

    assert plan.members["control"] == ("u02", "u00", "u01", "u11", "u03", "u07")
    assert plan.members["treatment"] == ("u09", "u06", "u05", "u08", "u10", "u04")

    other = assignment_for(
        _stratum_roster(),
        "arm",
        {"method": "random", "seed": 12, "stratify_by": ["sex"]},
        levels,
        "digest",
        None,
        {"sex": sex},
    )
    assert set(other.members["control"]) != set(plan.members["control"])


def test_a_blocked_axis_may_stratify_on_an_earlier_axis():
    """**`blocked`'s own success path on an axis-name stratum**, which nothing
    else in this suite reaches.

    `test_a_stratum_no_resolved_unit_carries_is_not_drawn_as_one_stratum` loops
    both methods but asserts a **raise** for each, so it passes whether or not
    `blocked` can read a plan at all: a parametrized test asserting a failure for
    both arms proves nothing about either arm's success path. Reverting only the
    `blocked` branch's `_stratum_groups` call sites to the pre-`resolved`
    signature left the whole suite green because of that gap.

    The block loop runs inside each `sex` arm, from the one carried generator, so
    each arm is filled 3/3 — and the pinned membership differs from the
    UNSTRATIFIED `blocked` draw of the same roster at the same seed
    (`('u00', 'u01', 'u04', 'u05', 'u08', 'u11')`), which is what makes
    "`stratify_by` was ignored" a failure here rather than a coincidence."""
    sex = _sex_plan()
    levels = ("control", "treatment")
    plan = assignment_for(
        _stratum_roster(),
        "arm",
        {"method": "blocked", "seed": 11, "stratify_by": ["sex"]},
        levels,
        "digest",
        None,
        {"sex": sex},
    )
    assert plan.strata == ("sex",)
    for sex_arm in sex.members.values():
        assert len(set(sex_arm) & set(plan.members["control"])) == 3
        assert len(set(sex_arm) & set(plan.members["treatment"])) == 3

    assert plan.members["control"] == ("u00", "u01", "u06", "u07", "u08", "u11")
    assert plan.members["treatment"] == ("u02", "u05", "u09", "u03", "u04", "u10")

    other = assignment_for(
        _stratum_roster(),
        "arm",
        {"method": "blocked", "seed": 12, "stratify_by": ["sex"]},
        levels,
        "digest",
        None,
        {"sex": sex},
    )
    assert set(other.members["control"]) != set(plan.members["control"])


def test_a_blocked_draw_on_an_axis_stratum_names_the_strata_when_an_arm_is_empty():
    """**The `E-DATA-ASSIGN-LEVELS` message under an axis-name stratum**, and the
    reason it needs its own test: `blocked`'s refusal builds its "within each of
    the N strata" clause by calling `_stratum_groups` a second time, from inside
    the message construction. A call site left on the pre-`resolved` signature
    there raises `NotImplementedError` **while formatting a diagnostic** — the
    worse half of the same mutation, since it turns a clean refusal into a
    traceback.

    Four units, an earlier axis splitting them 2/2, three equal arms: each
    stratum is one partial block apportioned `[1, 1, 0]`, so `c` is empty across
    every block of every stratum — the merged-coverage rule, reached through a
    stratum no unit carries as a column."""
    roster = UnitList([Unit(key=f"u{i:02d}", paths=(), attributes={}) for i in range(4)])
    earlier = assignment_for(roster, "sex", {"method": "random", "seed": 3}, ["f", "m"], "d")
    with pytest.raises(ContractError) as e:
        assignment_for(
            roster,
            "arm",
            {"method": "blocked", "seed": 11, "stratify_by": ["sex"]},
            ["a", "b", "c"],
            "digest",
            None,
            {"sex": earlier},
        )
    assert e.value.code == "E-DATA-ASSIGN-LEVELS"
    assert "no unit in c" in str(e.value)
    assert "within each of the 2 strata of sex" in str(e.value)


def test_a_stratum_the_roster_carries_is_an_attribute_before_it_is_an_axis():
    """**The precedence, pinned in the one place it can diverge.** `validate`
    exempts a `stratify_by` name found in `data.units.attributes` before it asks
    whether the name is a group axis; this function decides the same order from
    the other side, off the resolved units. So a name that is both — `site`,
    carried by every unit here AND handed in as a drawn axis — must balance on
    the column, or the two sides would answer differently for one declaration
    and no forward-only finding would correspond to what the draw did.

    The two answers are made distinguishable on purpose: the `site` plan handed
    in is a two-level 6/6 split that cuts ACROSS the three sites, so balancing
    on it gives A 3/3, B 2/2, C 1/1 only if the column won. The membership pin
    is `test_a_stratified_draw_balances_arms_within_every_stratum`'s own,
    unchanged — the same declaration with no `resolved` at all — so this test
    asserts bit-identity with the column draw rather than merely a plausible
    balance."""
    crossing = assignment_for(
        _stratum_roster(), "site", {"method": "random", "seed": 5}, ["f", "m"], "digest"
    )
    levels = ("control", "treatment")
    plan = assignment_for(
        _stratum_roster(),
        "arm",
        {"method": "random", "seed": 11, "stratify_by": ["site"]},
        levels,
        "digest",
        None,
        {"site": crossing},
    )
    assert _per_stratum(plan, levels) == {"A": (3, 3), "B": (2, 2), "C": (1, 1)}
    assert plan.members["control"] == ("u04", "u00", "u02", "u01", "u11", "u09")


def test_a_unit_carrying_no_value_for_the_stratum_is_its_own_stratum():
    """A name *some* units carry is a stratum; the units carrying none are
    balanced together as `no value`, `stratum_varies_within_cluster`'s own
    rendering of the same absence — so the two agree about what a missing value
    is rather than one treating it as a stratum and the other as a fault. Only a
    name **no** unit carries is the raise above.

    Six units carry `site: A` and six carry nothing, two equal arms: both groups
    come out 3/3, which a draw that raised on the first missing value could not
    produce and a draw that lumped every unit into one group would not be forced
    to."""
    roster = UnitList(
        [
            Unit(key=f"u{i:02d}", paths=(), attributes={"site": "A"} if i < 6 else {})
            for i in range(12)
        ]
    )
    plan = assignment_for(
        roster,
        "arm",
        {"method": "random", "seed": 11, "stratify_by": ["site"]},
        ["control", "treatment"],
        "digest",
    )
    carried = {f"u{i:02d}" for i in range(6)}
    assert len(carried & set(plan.members["control"])) == 3
    assert len(carried & set(plan.members["treatment"])) == 3
    assert len(plan.members["control"]) == 6


def test_a_level_empty_in_one_stratum_is_fine_if_another_stratum_covers_it():
    """Coverage is checked over the MERGED draw, never per stratum — `blocked`'s
    own rule for the same question one construction over. Three arms over strata
    of 6 and 2: the two-unit stratum apportions `[1, 1, 0]`, giving the third arm
    nothing, and the six-unit one gives it 2. A check written per stratum would
    refuse this legal design.

    Its mirror, `test_a_stratified_draw_leaving_an_arm_empty_is_refused` below,
    is what keeps this from licensing an empty arm."""
    roster = UnitList(
        [
            Unit(key=f"u{i:02d}", paths=(), attributes={"site": "A" if i < 6 else "B"})
            for i in range(8)
        ]
    )
    plan = assignment_for(
        roster,
        "arm",
        {"method": "random", "seed": 11, "stratify_by": ["site"]},
        ["a", "b", "c"],
        "digest",
    )
    assert sorted(len(plan.members[level]) for level in ("a", "b", "c")) == [2, 3, 3]
    assert all(plan.members[level] for level in ("a", "b", "c"))


def test_a_stratified_draw_leaving_an_arm_empty_is_refused():
    """The merged-coverage check has teeth: two strata of two units over three
    equal arms apportion `[1, 1, 0]` in each, so the third arm is empty across
    every stratum — `arms_of`'s own sentence, "that arm's condition would resolve
    zero units", so `E-DATA-ASSIGN-LEVELS`, the same code both unstratified
    draws refuse the same fault with.

    The message names the strata rather than only the roster, since a reader
    whose arms are empty *because* the strata are small needs to know that is
    what happened."""
    roster = UnitList(
        [
            Unit(key=f"u{i:02d}", paths=(), attributes={"site": "A" if i < 2 else "B"})
            for i in range(4)
        ]
    )
    with pytest.raises(ContractError) as e:
        assignment_for(
            roster,
            "arm",
            {"method": "random", "seed": 11, "stratify_by": ["site"]},
            ["a", "b", "c"],
            "digest",
        )
    assert e.value.code == "E-DATA-ASSIGN-LEVELS"
    assert "no unit in c" in str(e.value)
    assert "2 strata" in str(e.value)


def test_a_clustered_stratified_draw_keeps_every_cluster_whole():
    """Both constructions at once, which is a cluster-randomized trial stratified
    by site: whole clusters go to one arm (§ Clustered units, "core computed the
    partition, so core keeps it indivisible") *and* each stratum is balanced.

    Eight clusters of 2, four in each site. The structural assertion is that no
    cluster straddles two arms — a size check could not see a split cluster,
    since 8/8 is reachable either way — and the per-stratum assertion is that
    each site contributes 4 units to each arm, which a draw that dealt clusters
    over the whole roster is not forced to produce.

    This composition is sound only because a cluster carries one stratum value:
    `validate` refuses the other case as `E-DATA-ASSIGN-STRATIFY-VARIES`, the
    same dependence `partition_units` has on the fold half of that rule."""
    units, clusters = [], {}
    for c in range(8):
        for m in range(2):
            key = f"c{c}_{m}"
            units.append(Unit(key=key, paths=(), attributes={"site": "A" if c < 4 else "B"}))
            clusters[key] = f"c{c}"
    roster = UnitList(units)
    plan = assignment_for(
        roster,
        "arm",
        {"method": "random", "seed": 11, "stratify_by": ["site"]},
        ["control", "treatment"],
        "digest",
        clusters,
    )
    control = set(plan.members["control"])
    for c in range(8):
        members = {f"c{c}_0", f"c{c}_1"}
        assert members <= control or not (members & control), f"c{c} straddles two arms"
    assert len({k for k in control if k.startswith(("c0", "c1", "c2", "c3"))}) == 4
    assert len(control) == 8

    # The same membership pin the unclustered stratified test carries, and for
    # the same reason: which four of each site's clusters go to `control` is the
    # only thing the RNG decides here — the counts and the wholeness are forced
    # by the ratio and by `_assign_whole_clusters_by_ratio` respectively — so a
    # clustered draw that ignored its seed would satisfy both assertions above.
    assert plan.members["control"] == (
        "c0_0",
        "c0_1",
        "c2_0",
        "c2_1",
        "c5_0",
        "c5_1",
        "c6_0",
        "c6_1",
    )
    other = assignment_for(
        roster,
        "arm",
        {"method": "random", "seed": 12, "stratify_by": ["site"]},
        ["control", "treatment"],
        "digest",
        clusters,
    )
    assert set(other.members["control"]) != set(plan.members["control"])


def test_an_empty_stratify_by_still_draws():
    """**The control** for the refusal above: `stratify_by: []` is what `init`
    writes and what most designs carry, and it declares no balance — so it
    draws. A refusal written as "the key is present" rather than "the value is
    non-empty" would refuse every generated config."""
    roster = _random_roster(12)
    block = {"method": "random", "seed": 5, "stratify_by": []}
    plan = assignment_for(roster, "arm", block, ["a", "b"], "digest")
    assert len(plan.members["a"]) == 6
    assert len(plan.members["b"]) == 6
    assert plan.strata == ()


def _five_clusters() -> tuple[UnitList, dict[str, str]]:
    """12 units in 5 clusters of 4/3/2/2/1 — `reference.md` § Clustered units'
    "core computed the partition, so core keeps it indivisible" fixture,
    shared by the two tests below. Irregular sizes on purpose: no two are
    equal except the pair of 2s, so a mutation that dealt clusters out by
    the wrong rule reaches a size combination none of the other rosters in
    this file happen to share.

    **Not a claim that a split-cluster mutation produces a size no correct
    draw could** — it can, and does: `{c0, c3}` (4+2) and `{c1, c2, c4}`
    (3+2+1) are both legitimate whole-cluster combinations summing to 6, so
    a 6/6 split proves nothing about whether a cluster was divided to reach
    it.
    `test_a_clustered_random_draw_keeps_every_cluster_whole` below asserts
    the structural property (every cluster's units land together) for
    exactly this reason — a size-based assertion could not distinguish the
    two."""
    return _clustered({"c0": 4, "c1": 3, "c2": 2, "c3": 2, "c4": 1})


def test_a_clustered_random_draw_keeps_every_cluster_whole():
    """§ Clustered units: 'core computed the partition, so core keeps it
    indivisible.' 12 units in 5 clusters of 4/3/2/2/1 drawn `random` over two
    equal-weight arms. The assertion that matters is structural — every
    cluster's units land together — because a mutation that *split* a
    cluster (moved some of its units to the other arm) would still be
    caught by no size check at all: legitimate whole-cluster combinations
    here already reach a 6/6 split (`{c0, c3}` vs `{c1, c2, c4}`), so a
    split-cluster bug could produce a same-sized, merely wrong-membership
    result. Asserting per-cluster containment is what a size-only assertion
    cannot do."""
    roster, clusters = _five_clusters()
    block = {"method": "random", "seed": 5}
    plan = assignment_for(roster, "arm", block, ["a", "b"], "digest", clusters)

    membership = {key: level for level, keys in plan.members.items() for key in keys}
    for cluster_name in set(clusters.values()):
        cluster_keys = [key for key, name in clusters.items() if name == cluster_name]
        levels_seen = {membership[key] for key in cluster_keys}
        assert len(levels_seen) == 1, f"cluster {cluster_name!r} split across arms: {levels_seen}"

    # The realized split this seed happens to draw, pinned so the structural
    # check above has a concrete shape to be checked against too.
    assert plan.members["a"] == ("c0_0", "c0_1", "c0_2", "c0_3", "c2_0", "c2_1")
    assert plan.members["b"] == ("c1_0", "c1_1", "c1_2", "c3_0", "c3_1", "c4_0")


def test_a_clustered_draw_approaches_an_unequal_ratio_as_closely_as_clusters_allow():
    """`ratio: {a: 1, b: 3}` over the same 12-unit, 5-cluster fixture targets
    3 and 9 — `_apportion(12, [1, 3]) == [3, 9]` exactly, confirmed below as
    the unclustered answer this is contrasted against. The realized sizes are
    4 and 8, not 3 and 9: `c0` (size 4) is the largest cluster and is dealt
    first — largest-first is `_assign_whole_clusters`'s own rule, inherited
    here — landing on whichever arm is furthest below its target share, which
    at the first cluster is a tie broken toward the earlier-declared level,
    `a`. That single placement already puts `a` at 4, one past its target of
    3, and every remaining cluster's smallest member is `c4` at size 1 — too
    coarse to pull `a` back down to 3 without leaving it short instead. A
    cluster is the smallest thing that can move, so one large cluster sets a
    floor no assignment can get under; `partition_units`'s docstring makes
    the identical argument for folds and refuses to claim the stronger,
    exact-ratio thing. This is that argument checked numerically rather than
    merely asserted."""
    roster, clusters = _five_clusters()
    block = {"method": "random", "seed": 5, "ratio": {"a": 1, "b": 3}}
    plan = assignment_for(roster, "arm", block, ["a", "b"], "digest", clusters)

    assert _apportion(12, [1, 3]) == [3, 9]
    assert len(plan.members["a"]) == 4
    assert len(plan.members["b"]) == 8
    assert plan.members["a"] == ("c0_0", "c0_1", "c0_2", "c0_3")
    assert plan.members["b"] == (
        "c1_0",
        "c1_1",
        "c1_2",
        "c3_0",
        "c3_1",
        "c2_0",
        "c2_1",
        "c4_0",
    )


def test_a_clustered_draw_the_ratio_apportions_no_whole_cluster_to_is_refused():
    """The same refusal `test_a_drawn_arm_the_ratio_apportions_no_unit_to_is_refused`
    pins for the unclustered path, over a fixture where a *cluster* rather
    than a unit is the thing a level can be starved of: a single 5-unit
    cluster over two arms leaves one arm no whole cluster to receive, since
    the only thing that can move is the whole cluster and it can only move
    to one side. A coarser unit of movement makes an empty arm *easier* to
    reach than in the unclustered case, not exempt from the refusal —
    `assignment_for`'s docstring states the same code applies for the
    identical reason, "a coarser unit of movement makes it easier to reach,
    not exempt from the refusal"."""
    roster, clusters = _clustered({"c0": 5})
    block = {"method": "random", "seed": 1}
    with pytest.raises(ContractError) as e:
        assignment_for(roster, "arm", block, ["a", "b"], "digest", clusters)
    assert e.value.code == "E-DATA-ASSIGN-LEVELS"
    assert "b" in str(e.value)
    assert "resolves zero of them" in str(e.value)


def test_a_clustered_draws_zero_weight_level_refuses_rather_than_dividing_by_zero():
    """`ratio: {a: 0, b: 1}` reaches `_assign_whole_clusters_by_ratio`'s
    `counts[i] / weights[i]` with a weight of 0 for `a`. `validate` refuses a
    non-positive ratio value today (`E-DATA-ASSIGN-RATIO`), but
    `assignment_for` is reachable directly — the same reachability gap task
    8's report already flagged for the unclustered path — so a defensive
    guard here is worth having regardless of that gate.

    Every cluster's priority for `a` is `inf` rather than a raw
    `ZeroDivisionError`, so `a` is never the argmin while `b`'s weight stays
    positive: `b` claims every cluster and `a` ends up an empty bucket,
    refused by the same `E-DATA-ASSIGN-LEVELS` code and "resolves zero of
    them" message a starved level always gets — a `ContractError` the
    caller asked for, not an arithmetic exception it didn't."""
    roster, clusters = _five_clusters()
    block = {"method": "random", "seed": 1, "ratio": {"a": 0, "b": 1}}
    with pytest.raises(ContractError) as e:
        assignment_for(roster, "arm", block, ["a", "b"], "digest", clusters)
    assert e.value.code == "E-DATA-ASSIGN-LEVELS"
    assert "a" in str(e.value)
    assert "resolves zero of them" in str(e.value)


def test_a_blocked_draw_balances_within_every_whole_block():
    """14 units, ratio `{}` (equal allocation), `block_size: auto` = 4. 14 is
    NOT a multiple of 4: three whole blocks of 4 and a trailing 2, so a draw
    that balanced only *overall* — 7 control / 7 treatment, exactly what
    `random` also gives this roster — would pass a size assertion on the
    whole roster and still fail this one, which checks every block on its
    own. Asserting each whole block holds exactly 2 and 2, and the trailing
    partial block's actual composition, is what a mutant that shuffled the
    full 14 and cut it into 7/7 (§ Global Constraints' 'balance overall
    rather than per block') cannot pass: nothing forces its arbitrary cut to
    land 2-2 in every four-unit window.

    A pinned seed makes the exact membership — not just the counts —
    checkable, which is what the mutation for `auto`'s formula (task's
    Global Constraints: 'auto as the ratio sum rather than twice it') needs:
    with `ratio: {}` over two levels `auto` is twice the level count, so 4
    here rather than 2, and a wrong `block_size` changes how the seeded RNG
    is consumed and so changes who lands where, verified in
    `test_auto_block_size_is_twice_the_ratio_sum` below."""
    roster = _random_roster(14)
    block = {"method": "blocked", "seed": 11}
    plan = assignment_for(roster, "arm", block, ["control", "treatment"], "digest")

    assert plan.seed == 11
    assert plan.members["control"] == ("u00", "u01", "u04", "u05", "u08", "u11", "u13")
    assert plan.members["treatment"] == ("u02", "u03", "u06", "u07", "u09", "u10", "u12")

    control = set(plan.members["control"])
    treatment = set(plan.members["treatment"])
    keys = [u.key for u in roster]
    for block_start in (0, 4, 8):
        chunk = set(keys[block_start : block_start + 4])
        assert len(chunk & control) == 2, f"block at {block_start} is not 2 control"
        assert len(chunk & treatment) == 2, f"block at {block_start} is not 2 treatment"

    # The trailing partial block (positions 12-13, only 2 units): its actual
    # composition, asserted rather than left unchecked because it is the one
    # block a "whole blocks only" check would silently skip.
    trailing = set(keys[12:14])
    assert trailing & control == {"u13"}
    assert trailing & treatment == {"u12"}


def test_blocked_reads_the_roster_order_as_data():
    """**What this test actually shows, corrected after review — not that
    `blocked` is order-sensitive and `random` isn't.** At a pinned seed, both
    `random` and `blocked` are pure functions of *position* → arm (verified:
    200 random permutations leave each one's own position→arm vector
    bit-identical across runs, and each is invariant under exactly 42 of the
    91 pairwise position swaps at this seed) — they are **equally**
    order-sensitive mechanically; only the *specific* position→arm map
    differs between the two methods. What this test demonstrates is narrower
    than the docstring this replaces claimed: `u00` and `u05` happen to sit
    in the same arm under `random`'s map at seed 1 and in different arms
    under `blocked`'s, so swapping them moves `blocked`'s output and not
    `random`'s — which shows the two maps disagree on this one pair, not
    that one method reads order and the other doesn't.

    **The real demonstration of § Where units come from's claim — the
    property specific to `blocked`, and what § Allocation's "site batches,
    plate order" rationale is actually about — is
    `test_a_blocked_draw_balances_within_every_whole_block` above**: local
    balance in every consecutive window is a property `random` has at no
    window smaller than the whole roster, and `blocked` has by construction.
    This test is kept as a secondary, narrower check on that same swap, with
    its `random` half serving as a control that must still report (both
    orderings of a roster giving `random` the identical map is not
    guaranteed for every pair — a full reversal at this seed does move units
    across arms — but holds for this hand-picked one, `u00`/`u05`, because
    both land in `random`'s same arm-slice).

    **This test's own discriminating power against 'shuffle the roster
    before blocking' is real but narrower than once claimed, too**: it fails
    against a mutant that reuses the block-drawing `rng` instance to shuffle
    the whole roster first (consuming its state before any block draw runs),
    but *survives* a mutant that shuffles with a **separate**,
    freshly-seeded `random.Random(seed)` first and leaves the block-drawing
    `rng` untouched — verified: under that variant, `u00` and `u05` still
    land in the same post-shuffle grouping and this test passes.
    `test_a_blocked_draw_balances_within_every_whole_block` catches both
    variants, which is why it, not this test, is the mutation-proved
    demonstration of 'balance within every block'."""
    roster = _random_roster(14)
    keys = [u.key for u in roster]
    swapped_keys = keys[:]
    swapped_keys[0], swapped_keys[5] = swapped_keys[5], swapped_keys[0]
    swapped = UnitList([Unit(key=k, paths=(), attributes={}) for k in swapped_keys])

    levels = ["control", "treatment"]

    random_block = {"method": "random", "seed": 1}
    random_plan = assignment_for(roster, "arm", random_block, levels, "digest")
    random_plan_swapped = assignment_for(swapped, "arm", random_block, levels, "digest")
    random_map = {k: lvl for lvl, ks in random_plan.members.items() for k in ks}
    random_map_swapped = {k: lvl for lvl, ks in random_plan_swapped.members.items() for k in ks}
    assert random_map == random_map_swapped, (
        "the control must report: random reads no order, so the same units "
        "in a different order must land in the same arms"
    )

    blocked_block = {"method": "blocked", "seed": 1}
    blocked_plan = assignment_for(roster, "arm", blocked_block, levels, "digest")
    blocked_plan_swapped = assignment_for(swapped, "arm", blocked_block, levels, "digest")
    blocked_map = {k: lvl for lvl, ks in blocked_plan.members.items() for k in ks}
    blocked_map_swapped = {k: lvl for lvl, ks in blocked_plan_swapped.members.items() for k in ks}
    assert blocked_map != blocked_map_swapped
    assert blocked_map["u00"] == "treatment"
    assert blocked_map["u05"] == "control"
    assert blocked_map_swapped["u00"] == "control"
    assert blocked_map_swapped["u05"] == "treatment"
    # Every other unit is unmoved by the swap — it is exactly this pair the
    # reorder touches, and both sit in different blocks (`u00` in the first,
    # `u05` in the second), which is why `blocked`, and only `blocked`, feels
    # the swap at all.
    for key in keys:
        if key not in ("u00", "u05"):
            assert blocked_map[key] == blocked_map_swapped[key]


def test_auto_block_size_is_twice_the_ratio_sum():
    """`{control: 1, treatment: 2}` -> sum 3 -> `auto` 6. And with `ratio: {}`
    over two levels -> `auto` 4, per § Allocation.

    Both fixtures are chosen so `auto = 2 x sum` and the mutant `auto = sum`
    disagree on *exact membership* at the same seed, not merely on size:
    over a roster exactly one `auto`-block long, `_apportion`'s per-block
    counts happen to sum to the identical totals under either reading (the
    fixture trap the plan's Global Constraints name, restated for this
    formula specifically), so only the precise unit-level draw — which
    depends on whether the seeded shuffle consumes one block of `2 x sum`
    positions or two of `sum` — tells them apart."""
    roster = _random_roster(6)
    block = {"method": "blocked", "ratio": {"control": 1, "treatment": 2}, "seed": 1}
    plan = assignment_for(roster, "arm", block, ["control", "treatment"], "digest")
    assert plan.members["control"] == ("u03", "u05")
    assert plan.members["treatment"] == ("u00", "u01", "u02", "u04")

    roster4 = _random_roster(4)
    block2 = {"method": "blocked", "seed": 2}
    plan2 = assignment_for(roster4, "arm", block2, ["a", "b"], "digest")
    assert plan2.members["a"] == ("u00", "u03")
    assert plan2.members["b"] == ("u01", "u02")


def test_a_declared_block_size_is_honoured_rather_than_ignored_for_auto():
    """**Caught by review: a mutation replacing the resolved `block_size` with
    `2 * ratio_sum` unconditionally — always drawing at `auto` and silently
    discarding whatever was declared — passed the entire suite.** Every other
    test in this file either omits `block_size` (so `auto` is also the
    correct answer) or picks a declared value that happens to equal `auto`.
    This fixture doesn't: `ratio: {}` over two levels makes `auto` 4, and the
    declared value is 6 — both are legal whole multiples of the ratio sum
    (2), so neither is refused, and they draw against genuinely different
    block boundaries (12 units: one block of 6 vs. three of 4), which the
    same pinned seed's RNG consumes differently. Exact membership, not size,
    discriminates them: `_apportion` gives 3/3 and 2/2/2 respectively, both
    summing to 6/6 overall, so a size assertion could not tell `block_size:
    6` from `auto` here either — the same fixture trap this task's brief
    names, now applied to the declared value itself rather than to `auto`'s
    formula."""
    roster = _random_roster(12)
    block = {"method": "blocked", "seed": 1, "block_size": 6}
    plan = assignment_for(roster, "arm", block, ["control", "treatment"], "digest")
    assert plan.members["control"] == ("u00", "u03", "u05", "u06", "u07", "u08")
    assert plan.members["treatment"] == ("u01", "u02", "u04", "u09", "u10", "u11")

    auto_block = {"method": "blocked", "seed": 1}
    auto_plan = assignment_for(roster, "arm", auto_block, ["control", "treatment"], "digest")
    assert auto_plan.members != plan.members, (
        "the control must report: block_size 6 and auto (4) must draw "
        "differently at this seed, or this test proves nothing"
    )


def test_auto_block_size_is_a_valid_int_even_for_a_fractional_ratio():
    """**Caught by review: `auto = 2 * ratio_sum` is a bare `2 * 0.5 = 1.0`
    for `ratio: {control: 0.5, treatment: 0.5}` — a `float` — and
    `range(0, len(keys), block_size)` in the draw below raises a bare
    `TypeError` on a `float` step. Reachable with no `block_size` declared
    at all: a fractional `ratio` alone does it, and `validate`'s
    `_usable_ratio_share` accepts any finite positive `float` share, so the
    config that reaches this validates clean.** This does not raise, and
    every unit resolves to exactly one arm — the property that matters here,
    since a resolved `auto` is checked by the same whole-share rule an
    explicit `block_size` is, and is not guaranteed to give every level a
    whole per-block share
    for an arbitrary `ratio` (§ Allocation states this explicitly): the
    draw still has to complete via `_apportion`'s largest-remainder
    tolerance rather than raise a type error root cause away."""
    roster = _random_roster(14)
    block = {"method": "blocked", "seed": 1, "ratio": {"control": 0.5, "treatment": 0.5}}
    plan = assignment_for(roster, "arm", block, ["control", "treatment"], "digest")
    assert sorted(plan.members["control"] + plan.members["treatment"]) == sorted(
        u.key for u in roster
    )


def test_a_blocked_level_empty_in_one_block_is_fine_if_another_block_covers_it():
    """**Caught by review: a mutation checking emptiness *per block* rather
    than over the whole roster passed the entire suite.** `assignment_for`'s
    own docstring commits to the opposite explicitly: "a level with at least
    one unit in some block is fine even if another block apportioned it
    none." The 14-unit, two-level fixture above can never reach this,
    because with only two levels every whole block of 4 is forced to 2/2 and
    the trailing block of 2 to 1/1 — no level is ever apportioned zero in any
    block there.

    Three levels, 7 units, equal ratio (`auto` = 6): one whole block of 6
    (`_apportion(6, [1,1,1]) == [2,2,2]`, exact) plus a trailing block of 1.
    `_apportion(1, [1,1,1])`'s three equal fractional parts tie-break to the
    first-declared level deterministically (largest-remainder ties go to
    declared order — `_apportion`'s own rule), so the trailing block always
    apportions `[1, 0, 0]`: `b` and `c` get **zero units in that block**,
    every seed, while `a` gets one. Both still resolve to a non-empty arm
    overall, because each already has 2 units from the full block — exactly
    the property a per-block check would refuse and the real, whole-roster
    check does not."""
    roster = _random_roster(7)
    block = {"method": "blocked", "seed": 1}
    plan = assignment_for(roster, "arm", block, ["a", "b", "c"], "digest")

    keys = [u.key for u in roster]
    full_block = set(keys[0:6])
    trailing_block = set(keys[6:7])
    assert trailing_block == {"u06"}

    for level in ("a", "b", "c"):
        assert len(full_block & set(plan.members[level])) == 2, (
            f"the full block of 6 must apportion {level} exactly 2 units"
        )
    # The trailing block of 1: `a` claims it, `b` and `c` are empty *in this
    # block specifically* — the situation a per-block check would refuse.
    assert trailing_block & set(plan.members["a"]) == {"u06"}
    assert trailing_block & set(plan.members["b"]) == set()
    assert trailing_block & set(plan.members["c"]) == set()
    # No raise reached this point, and every level resolves overall — `a` at
    # 3 (2 + the trailing unit), `b` and `c` at 2 each from the full block
    # alone.
    assert len(plan.members["a"]) == 3
    assert len(plan.members["b"]) == 2
    assert len(plan.members["c"]) == 2


def test_arm_members_reduces_arms_of_across_the_resolved_conditions():
    """`units.arm_members` is the reduction the runner's subset view is built
    from: one call into `arms_of` per declared axis, then a per-condition lookup
    against `.selectors`/`.values` — never a second derivation of membership.
    7 control, 5 treatment, deliberately uneven per the H3c fixture rule, plus a
    third condition selecting no axis at all, which must be absent from the
    result entirely rather than mapped to the whole roster."""
    from publishable.sweep import Condition

    roster = UnitList(
        [Unit(key=f"c{i}", attributes={"arm": "control"}) for i in range(7)]
        + [Unit(key=f"t{i}", attributes={"arm": "treatment"}) for i in range(5)]
    )
    selectors = frozenset({"arm"})
    conditions = [
        Condition(index=0, label="control", values={"arm": "control"}, selectors=selectors),
        Condition(index=1, label="treatment", values={"arm": "treatment"}, selectors=selectors),
        Condition(index=2, label="plain", values={}, selectors=frozenset()),
    ]
    result = arm_members(_arm_plans(roster), conditions)
    assert result[0] == frozenset(f"c{i}" for i in range(7))
    assert result[1] == frozenset(f"t{i}" for i in range(5))
    assert 2 not in result
    assert len(result[0]) + len(result[1]) == len(roster)


def test_arm_members_derives_no_membership_of_its_own_from_a_planted_plan():
    """The property `test_arm_members_calls_arms_of_once_per_axis_not_per_condition`
    used to pin, retargeted rather than dropped: `arm_members` no longer calls
    `arms_of` at all — it is handed plans — so "once per axis, not once per
    condition" is now `assignment_for`'s own property (pinned end-to-end in
    `test_cli.py`), and what is left to pin here is stronger. The plan handed
    in **contradicts** the roster attribute: `c0` carries `arm: control` but
    the plan puts it in `treatment`, and `t0` the reverse. `arm_members`
    must return the plan's answer, not the column's. A version that re-derived
    membership from a roster — the second producer this slice exists to make
    impossible — would return the swapped-back sets and fail both assertions."""
    from publishable.sweep import Condition

    selectors = frozenset({"arm"})
    conditions = [
        Condition(index=0, label="control", values={"arm": "control"}, selectors=selectors),
        Condition(index=1, label="treatment", values={"arm": "treatment"}, selectors=selectors),
    ]
    planted = ArmPlan(
        levels=("control", "treatment"),
        members={"control": ("t0",), "treatment": ("c0",)},
        seed=None,
        strata=(),
    )
    result = arm_members({"arm": planted}, conditions)
    assert result[0] == frozenset({"t0"})
    assert result[1] == frozenset({"c0"})


def test_arm_members_intersects_when_a_condition_selects_two_axes():
    """§ Validation's `sex × arm` cell: a condition selecting more than one axis
    gets the intersection of each axis's arm, not either one alone."""
    from publishable.sweep import Condition

    roster = UnitList(
        [
            Unit(key="u0", attributes={"arm": "control", "sex": "f"}),
            Unit(key="u1", attributes={"arm": "control", "sex": "m"}),
            Unit(key="u2", attributes={"arm": "treatment", "sex": "f"}),
        ]
    )
    conditions = [
        Condition(
            index=0,
            label="cell",
            values={"arm": "control", "sex": "f"},
            selectors=frozenset({"arm", "sex"}),
        ),
    ]
    result = arm_members(
        {
            "arm": assignment_for(roster, "arm", None, ["control", "treatment"], "digest"),
            "sex": assignment_for(roster, "sex", None, ["f", "m"], "digest"),
        },
        conditions,
    )
    assert result[0] == frozenset({"u0"})


def test_the_fold_basis_is_the_cluster_count_when_the_units_are_clustered():
    """`reference.md` § Validation, *Folds fit inside the clusters*: a cluster is
    indivisible, so what a fold may be drawn from is the cluster count.

    Sizes 7/3/3/1/1 — 5 clusters over 15 units — deliberately: with one unit per
    cluster the two numbers coincide and this assertion could not tell the cluster
    count from the roster size.
    """
    roster, _ = _clustered({"S1": 7, "S2": 3, "S3": 3, "S4": 1, "S5": 1})
    assert len(roster) == 15
    assert fold_basis(roster, "site") == 5


def test_the_fold_basis_is_the_unit_count_when_nothing_is_clustered():
    """The control that must report: with no `cluster_by`, every unit is its own
    independent draw and the basis is the roster size — the same 15-unit roster the
    clustered case counts 5 of, so the two answers cannot be confused."""
    roster, _ = _clustered({"S1": 7, "S2": 3, "S3": 3, "S4": 1, "S5": 1})
    assert fold_basis(roster, None) == 15
    assert fold_basis(roster, "") == 15


def test_the_fold_basis_refuses_a_unit_with_no_cluster():
    """`cluster_count` is the authority, so a unit carrying no value for the
    attribute raises here rather than being counted as a cluster of its own — which
    would inflate the basis and admit a `k` the partitioner cannot satisfy."""
    roster = UnitList(
        [
            Unit(key="u0", paths=(), attributes={"site": "S1"}),
            Unit(key="u1", paths=(), attributes={}),
        ]
    )
    with pytest.raises(ContractError) as e:
        fold_basis(roster, "site")
    assert e.value.code == "E-DATA-CLUSTER-UNKNOWN"


def test_cluster_ids_are_labels_whatever_the_source_supplied(input_dir: Path):
    """A table yields `str` for every column, but a hand-built roster need not,
    and a cluster id is a label rather than a quantity."""
    roster, _, _ = resolve_units(
        {"from": "index.csv", "key": "patient_id", "attributes": ["site"]}, input_dir
    )
    assert set(clusters_of(roster, "site").values()) == {"a", "b"}
    numeric = UnitList([Unit(key="u0", paths=(), attributes={"site": 7})])
    assert clusters_of(numeric, "site") == {"u0": "7"}


# --- a cluster and a weight must not vary within a unit's measurement rows ---
#
# `reference.md` § Clustered units and § Weighted samples: `measurements` collapses
# these two columns like any other attribute, so replicate rows disagreeing about
# them answer by row order. The check belongs here because `collapse_measurements`
# is the one place holding the pre-collapse values — `validate` resolves the roster
# and sees the post-collapse one, where the disagreement is already gone.


def test_a_cluster_varying_within_a_unit_is_refused():
    """A mis-collapsed cluster decides which side of a split a unit lands on."""
    units = [
        Unit(key="p1", paths=(), attributes={"read": "r1", "site": "S1"}),
        Unit(key="p1", paths=(), attributes={"read": "r2", "site": "S2"}),
    ]
    with pytest.raises(ContractError) as e:
        collapse_measurements(units, by="read", collapse="first", constant={"cluster_by": "site"})
    assert e.value.code == "E-DATA-CLUSTER-VARIES"
    assert "p1" in str(e.value) and "site" in str(e.value)


def test_a_cluster_constant_within_a_unit_is_accepted():
    """The control: same shape, agreeing rows, must NOT raise. Without it there is
    no way to tell a check from a function that refuses every input."""
    units = [
        Unit(key="p1", paths=(), attributes={"read": "r1", "site": "S1"}),
        Unit(key="p1", paths=(), attributes={"read": "r2", "site": "S1"}),
    ]
    collapsed, _ = collapse_measurements(
        units, by="read", collapse="first", constant={"cluster_by": "site"}
    )
    assert collapsed[0].site == "S1"


def test_a_weight_varying_within_a_unit_is_refused():
    """The half H3a could only state: a weight is what one unit stands for, so
    replicate rows carrying 1 and 99 would sum to a weight no row declared."""
    units = [
        Unit(key="p1", paths=(), attributes={"read": "r1", "w": "1"}),
        Unit(key="p1", paths=(), attributes={"read": "r2", "w": "99"}),
    ]
    with pytest.raises(ContractError) as e:
        collapse_measurements(units, by="read", collapse="first", constant={"weight_by": "w"})
    assert e.value.code == "E-DATA-WEIGHT-VARIES"


def test_a_weight_constant_within_a_unit_is_accepted():
    """The weight half's own control."""
    units = [
        Unit(key="p1", paths=(), attributes={"read": "r1", "w": "2.5"}),
        Unit(key="p1", paths=(), attributes={"read": "r2", "w": "2.5"}),
    ]
    collapsed, _ = collapse_measurements(
        units, by="read", collapse="first", constant={"weight_by": "w"}
    )
    assert collapsed[0].w == "2.5"


def test_the_two_codes_are_not_one_code():
    """The cluster case and the weight case say different things about what
    breaks — leakage versus a mis-sized contribution — so one identifier for both
    would send a reader to the wrong section. Pinned in one place so a later
    refactor that collapses the two tables fails here."""
    rows = [
        Unit(key="p1", paths=(), attributes={"read": "r1", "col": "a"}),
        Unit(key="p1", paths=(), attributes={"read": "r2", "col": "b"}),
    ]
    codes = set()
    for declaration in ("cluster_by", "weight_by"):
        with pytest.raises(ContractError) as e:
            collapse_measurements(rows, by="read", collapse="first", constant={declaration: "col"})
        codes.add(e.value.code)
    assert codes == {"E-DATA-CLUSTER-VARIES", "E-DATA-WEIGHT-VARIES"}


def test_no_declaration_leaves_the_collapse_exactly_as_it_was():
    """Totality over the declaration being absent entirely, which is every config
    that declares neither — including the worked example. The default must check
    nothing at all, or `measurements` would start refusing rosters it has always
    collapsed."""
    units = [
        Unit(key="p1", paths=(), attributes={"read": "r1", "site": "S1"}),
        Unit(key="p1", paths=(), attributes={"read": "r2", "site": "S2"}),
    ]
    collapsed, counts = collapse_measurements(units, by="read", collapse="first")
    assert collapsed[0].site == "S1"
    assert counts == [2]


def test_a_column_absent_from_some_rows_is_not_a_disagreement():
    """`validate` collects findings and never raises, so this function has to be
    total over a name only some members carry. The rows that carry it agree, so
    nothing about the collapsed value depends on row order — an absent cell is
    the *presence* question, which `clusters_of` raises on after resolution, not
    a disagreement between rows."""
    units = [
        Unit(key="p1", paths=(), attributes={"read": "r1", "site": "S1"}),
        Unit(key="p1", paths=(), attributes={"read": "r2"}),
    ]
    collapsed, _ = collapse_measurements(
        units, by="read", collapse="first", constant={"cluster_by": "site"}
    )
    assert collapsed[0].site == "S1"


def test_a_null_cluster_beside_a_real_one_is_a_disagreement():
    """Present-but-`None` is not absent: one row names a site and the other names
    nothing, so which value survives is again the file's row order."""
    units = [
        Unit(key="p1", paths=(), attributes={"read": "r1", "site": None}),
        Unit(key="p1", paths=(), attributes={"read": "r2", "site": "S2"}),
    ]
    with pytest.raises(ContractError) as e:
        collapse_measurements(units, by="read", collapse="first", constant={"cluster_by": "site"})
    assert e.value.code == "E-DATA-CLUSTER-VARIES"


def test_a_cluster_naming_the_measurement_axis_is_refused():
    """`cluster_by` naming the very column that distinguishes one measurement from
    another varies within every unit by construction. The check runs over the
    members directly rather than over the merge loop's column list, which excludes
    `by` — so this case is reachable at all only because of that placement."""
    units = [
        Unit(key="p1", paths=(), attributes={"read": "r1"}),
        Unit(key="p1", paths=(), attributes={"read": "r2"}),
    ]
    with pytest.raises(ContractError) as e:
        collapse_measurements(units, by="read", collapse="first", constant={"cluster_by": "read"})
    assert e.value.code == "E-DATA-CLUSTER-VARIES"


def test_the_leakage_code_wins_over_the_collapse_type_code():
    """A varying string cluster column under a blanket `mean` satisfies both this
    check and `coerce_for_rule`'s. Ordering decision, pinned: the reader needs to
    be told a unit is filed under two sites, not that `mean` doesn't fit strings —
    fixing the rule name would leave the leak in place."""
    units = [
        Unit(key="p1", paths=(), attributes={"read": "r1", "site": "S1"}),
        Unit(key="p1", paths=(), attributes={"read": "r2", "site": "S2"}),
    ]
    with pytest.raises(ContractError) as e:
        collapse_measurements(units, by="read", collapse="mean", constant={"cluster_by": "site"})
    assert e.value.code == "E-DATA-CLUSTER-VARIES"


def test_both_declarations_over_one_column_each_check_their_own(input_dir: Path):
    """The wiring, end to end through `resolve_units`, which is where the two
    names come from `units_decl` with no new plumbing."""
    _write_reads(
        input_dir,
        "patient_id,read_id,site,w\np1,r1,S1,2\np1,r2,S2,2\np2,r3,S3,3\n",
    )
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["site", "w", "read_id"],
        "cluster_by": "site",
        "weight_by": "w",
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    with pytest.raises(ContractError) as e:
        resolve_units(decl, input_dir)
    assert e.value.code == "E-DATA-CLUSTER-VARIES"
    # The other half of the same wiring: the cluster column agrees and the weight
    # column is the one that varies, so this fires the weight raise through
    # `resolve_units` rather than through a hand-built `constant`.
    _write_reads(
        input_dir,
        "patient_id,read_id,site,w\np1,r1,S1,1\np1,r2,S1,99\np2,r3,S3,3\n",
    )
    with pytest.raises(ContractError) as e:
        resolve_units(decl, input_dir)
    assert e.value.code == "E-DATA-WEIGHT-VARIES"
    # The control: the same declarations over rows that agree resolve cleanly.
    _write_reads(
        input_dir,
        "patient_id,read_id,site,w\np1,r1,S1,2\np1,r2,S1,2\np2,r3,S3,3\n",
    )
    roster, technical_n, _ = resolve_units(decl, input_dir)
    assert clusters_of(roster, "site") == {"p1": "S1", "p2": "S3"}
    assert technical_n == {"min": 1, "max": 2, "median": 1.5}


# --- an arm must not vary within a unit's measurement rows -------------------
#
# H3b named this by number: `CONSTANT_COLUMN_RULES` reached only a flat,
# string-valued key of `data.units`, and its own comment named `assign.<axis>.from`
# as one of the next two declarations that would want the rule. Worse than the
# cluster/weight pair above: a mis-collapsed arm decides which *condition* the
# unit is measured in, not merely which side of a split it lands on or how much
# it counts for. No fixture below declares `cluster_by` at all, so a varying
# `arm` cannot be mistaken for a varying cluster.


def test_an_arm_varying_within_a_units_measurement_rows_is_refused(input_dir: Path):
    """p1's replicate rows say control and treatment. Silently keeping one
    would put the unit in an arm no row declared — worse than a mis-collapsed
    cluster or weight, because it changes which condition p1 counts toward."""
    _write_reads(
        input_dir,
        "patient_id,read_id,arm\np1,r1,control\np1,r2,treatment\np2,r3,control\n",
    )
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["arm", "read_id"],
        "assign": {"arm": {"method": "by_attribute"}},
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    with pytest.raises(ContractError) as e:
        resolve_units(decl, input_dir)
    assert e.value.code == "E-DATA-ASSIGN-VARIES"
    assert "p1" in str(e.value) and "arm" in str(e.value)


def test_an_arm_constant_within_a_units_rows_is_accepted(input_dir: Path):
    """The control: same shape, agreeing rows, must NOT raise. Asserting only
    that nothing raised would also pass for a roster the collapse never
    reached, so this also asserts two positive facts about the resolved
    roster: the collapsed unit's `arm` is the value both rows agreed on, and
    `technical_n`'s `max` of 2 (over a `min` of 1) proves p1's two rows were
    actually collapsed into one unit rather than the check trivially passing
    over an unmeasured roster."""
    _write_reads(
        input_dir,
        "patient_id,read_id,arm\np1,r1,control\np1,r2,control\np2,r3,control\n",
    )
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["arm", "read_id"],
        "assign": {"arm": {"method": "by_attribute"}},
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    roster, technical_n, _ = resolve_units(decl, input_dir)
    by_key = {u.key: u for u in roster}
    assert by_key["p1"].arm == "control"
    assert technical_n == {"min": 1, "max": 2, "median": 1.5}


def test_a_constant_arm_survives_collapse_and_reaches_the_right_condition(input_dir: Path):
    """Task 19 Step 4 — the loop task 11 opened and this closes: the constancy
    check above refuses a *varying* arm, but nothing before this proved a
    *constant* one actually reaches the right condition once collapsed. Three
    assertions, not two: the resolved unit's own `arm` attribute (survived
    collapse), `technical_n` showing the rows that were actually collapsed
    (uneven — 2 for `p1`, 3 for `p2`, 2 for `p3` — so a roster collapse that
    silently used only the first row per key cannot pass by coincidence), and —
    the one that makes this end to end rather than the constancy test and
    `test_two_arms_get_different_rosters_and_neither_is_the_whole_roster`'s
    `arms_of` check run side by side — `units.arms_of` over THIS resolved
    roster, proving `p1` and `p3` (both `control`) land in the same partition
    and `p2` (`treatment`) lands in the other, using the exact roster
    `resolve_units` produced rather than a hand-built stand-in."""
    _write_reads(
        input_dir,
        "patient_id,read_id,arm,depth\n"
        "p1,r1,control,10\np1,r2,control,20\n"
        "p2,r1,treatment,30\np2,r2,treatment,40\np2,r3,treatment,90\n"
        "p3,r1,control,11\np3,r2,control,22\n",
    )
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["arm", "depth", "read_id"],
        "assign": {"arm": {"method": "by_attribute"}},
        "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
    }
    roster, technical_n, _ = resolve_units(decl, input_dir)
    by_key = {u.key: u for u in roster}
    assert by_key["p1"].arm == "control"
    assert by_key["p2"].arm == "treatment"
    assert by_key["p3"].arm == "control"
    assert technical_n == {"min": 2, "max": 3, "median": 2}

    partition = arms_of(roster, "arm", ["control", "treatment"])
    assert {u.key for u in partition["control"]} == {"p1", "p3"}
    assert {u.key for u in partition["treatment"]} == {"p2"}


def test_a_varying_arm_under_a_drawn_method_is_not_checked(input_dir: Path):
    """`_check_assign` reads `from`/`levels` only under `method: by_attribute` —
    "mean nothing" under `random`/`blocked` — so this accessor gates the same
    way. Without the gate, `arm`'s axis-name default would still resolve to a
    real column, and a `random`-method block over these same varying rows would
    raise a fault naming a `.from` path this declaration never asked to have
    read. Must NOT raise: the positive control for the gate itself, since the
    rows are exactly `test_an_arm_varying_within_a_units_measurement_rows_is_refused`'s."""
    _write_reads(
        input_dir,
        "patient_id,read_id,arm\np1,r1,control\np1,r2,treatment\np2,r3,control\n",
    )
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["arm", "read_id"],
        "assign": {"arm": {"method": "random"}},
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    roster, _, _ = resolve_units(decl, input_dir)
    assert {u.key for u in roster} == {"p1", "p2"}


def test_an_arm_varying_on_a_column_that_is_not_the_cluster_column_is_reported_as_assign(
    input_dir: Path,
):
    """`site` is declared as `cluster_by` and is constant across p1's rows;
    `arm` is the one that varies. A check that attributed the wrong code here
    would send a reader to fix clustering when the real fault is which
    condition p1 is measured in."""
    _write_reads(
        input_dir,
        "patient_id,read_id,site,arm\np1,r1,S1,control\np1,r2,S1,treatment\np2,r3,S1,control\n",
    )
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["site", "arm", "read_id"],
        "cluster_by": "site",
        "assign": {"arm": {"method": "by_attribute"}},
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    with pytest.raises(ContractError) as e:
        resolve_units(decl, input_dir)
    assert e.value.code == "E-DATA-ASSIGN-VARIES"


def test_the_three_codes_are_not_one_code_and_none_excludes_another():
    """The converse of the row above: one column named by all three
    declarations at once still raises each declaration's own code when that
    declaration is the one checked — `CONSTANT_COLUMN_RULES`'s docstring says a
    config naming one column under two declarations is checked once for each
    rather than one silently dropping under a precedence rule nothing in the
    documents states, and this is the proof neither the registry lookup nor the
    collapse itself builds mutual exclusion between `assign` and its siblings."""
    rows = [
        Unit(key="p1", paths=(), attributes={"read": "r1", "col": "a"}),
        Unit(key="p1", paths=(), attributes={"read": "r2", "col": "b"}),
    ]
    codes = set()
    for declaration in ("cluster_by", "weight_by", "assign.arm.from"):
        with pytest.raises(ContractError) as e:
            collapse_measurements(rows, by="read", collapse="first", constant={declaration: "col"})
        codes.add(e.value.code)
    assert codes == {"E-DATA-CLUSTER-VARIES", "E-DATA-WEIGHT-VARIES", "E-DATA-ASSIGN-VARIES"}


def test_one_column_named_by_both_cluster_and_arm_reports_exactly_one_code(input_dir: Path):
    """A brief claim checked by observation rather than trusted: a column named
    as both `cluster_by` and an axis's `assign.<axis>.from`, on a unit that
    violates both at once, does **not** raise both codes from one
    `resolve_units` call — `collapse_measurements` raises the first
    `ContractError` its per-unit loop finds and stops, so exactly one code
    comes back. It is `E-DATA-ASSIGN-VARIES`, not `E-DATA-CLUSTER-VARIES`:
    `_assign_constant_columns`'s entries are built into `constant` *before*
    the flat pair's, deliberately, so the severity order § Allocation states
    (arm worse than cluster worse than weight) is also the order
    `collapse_measurements` checks in for a unit that violates more than one.
    What survives from the brief's claim is the weaker, true half — each
    declaration considered on its own still raises: see
    `test_the_three_codes_are_not_one_code_and_none_excludes_another` above,
    which checks each declaration in a separate call rather than one config
    naming a column under two of them at once."""
    _write_reads(
        input_dir,
        "patient_id,read_id,arm\np1,r1,control\np1,r2,treatment\np2,r3,control\n",
    )
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["arm", "read_id"],
        "cluster_by": "arm",
        "assign": {"arm": {"method": "by_attribute"}},
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    with pytest.raises(ContractError) as e:
        resolve_units(decl, input_dir)
    assert e.value.code == "E-DATA-ASSIGN-VARIES"


def test_resolve_units_checks_holdout_after_assign_and_before_cluster(input_dir: Path):
    """`test_collapse_stops_at_the_first_entry_of_the_constant_mapping_it_is_given`
    (`test_units.py`, `_holdout_constant_column` fixture) pins the ordering
    against a `constant` mapping the test itself builds by hand — it proves
    `collapse_measurements` stops at whichever entry is first in the dict it
    is given, never that `resolve_units` actually builds that dict in this
    order. This is the companion that calls `resolve_units` on a real
    declaration, the way `test_one_column_named_by_both_cluster_and_arm_reports_exactly_one_code`
    above does for `assign` vs. `cluster_by` alone: one unit's rows disagree
    under `assign`, `holdout.from` and `cluster_by` at once, so only the
    `constant.update` order `resolve_units` itself builds decides which code
    comes back."""
    _write_reads(
        input_dir,
        "patient_id,read_id,arm,split,site\np1,r1,control,train,S1\np1,r2,treatment,test,S2\n",
    )
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["arm", "split", "site", "read_id"],
        "cluster_by": "site",
        "assign": {"arm": {"method": "by_attribute"}},
        "holdout": {"method": "by_attribute", "from": "split"},
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    with pytest.raises(ContractError) as e:
        resolve_units(decl, input_dir)
    assert e.value.code == "E-DATA-ASSIGN-VARIES"

    without_assign = dict(decl)
    del without_assign["assign"]
    with pytest.raises(ContractError) as e2:
        resolve_units(without_assign, input_dir)
    assert e2.value.code == "E-DATA-HOLDOUT-VARIES"


def test_a_bare_string_holdout_does_not_reach_the_registry_through_the_flat_comprehension(
    input_dir: Path,
):
    """`holdout` is a key of `CONSTANT_COLUMN_RULES`, so `resolve_units`'s flat
    comprehension — `if isinstance(units_decl.get(declaration), str) and
    units_decl[declaration]` — would otherwise admit a bare-string
    `data.units.holdout` naming a column that varies within a unit's
    measurement rows, and raise `E-DATA-HOLDOUT-VARIES` at path
    `data.units.holdout` (no `.from`) for a shape `_check_holdout` already
    refuses as `E-CONFIG-TYPE`. `holdout.from` reaches this registry only
    through `_holdout_constant_column`, so the flat comprehension excludes
    `holdout` explicitly and this declaration produces no `constant` entry at
    all — `resolve_units` completes without raising, over a roster whose
    `split` column varies exactly the way the mapping form would refuse."""
    _write_reads(
        input_dir,
        "patient_id,read_id,split\np1,r1,train\np1,r2,test\n",
    )
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["split", "read_id"],
        "holdout": "split",
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    units, _, _ = resolve_units(decl, input_dir)
    assert units[0].split == "train"


def test_roster_order_not_severity_decides_when_different_units_violate_different_declarations(
    input_dir: Path,
):
    """The qualifier the "assign checked first" claim needs: that ordering only
    ever gets tested on a unit that violates *both* declarations at once. Here
    p1 varies only in `site` (its `arm` agrees) and p2 varies only in `arm`
    (its `site` agrees) — `collapse_measurements`'s outer loop is per unit, in
    roster order, and stops at its first raise, so p1's own single violation
    (`E-DATA-CLUSTER-VARIES`) is reported before p2's is ever reached, even
    though `assign` is checked first *within* whichever unit's turn it is."""
    _write_reads(
        input_dir,
        "patient_id,read_id,site,arm\n"
        "p1,r1,S1,control\np1,r2,S2,control\n"
        "p2,r3,S3,control\np2,r4,S3,treatment\n",
    )
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["site", "arm", "read_id"],
        "cluster_by": "site",
        "assign": {"arm": {"method": "by_attribute"}},
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    with pytest.raises(ContractError) as e:
        resolve_units(decl, input_dir)
    assert e.value.code == "E-DATA-CLUSTER-VARIES"
    assert "p1" in str(e.value)


def test_a_non_string_declaration_is_left_to_the_envelope(input_dir: Path):
    """`validate` never raises, and a list-valued `cluster_by` used as a column
    name is a `TypeError` escaping it — the same class `_check_units`'s own `key`
    guard exists for. `E-CONFIG-TYPE` is the finding for a mistyped leaf; this
    function's job is to stay total."""
    _write_reads(input_dir, "patient_id,read_id,site\np1,r1,S1\np1,r2,S2\n")
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["site", "read_id"],
        "cluster_by": ["site"],
        "weight_by": "",
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    roster, _, _ = resolve_units(decl, input_dir)
    assert roster[0].site == "S1"


def test_a_column_no_row_carries_is_not_a_disagreement_either(input_dir: Path):
    """The fourth totality case: `cluster_by` naming a column absent from *every*
    row, which happens whenever it names something `data.units.attributes` does not
    declare. Resolution must complete — the finding is `E-DATA-CLUSTER-UNKNOWN`,
    made where membership is read — so the empty-group case may not raise, and may
    not be an `IndexError` either."""
    _write_reads(input_dir, "patient_id,read_id,depth\np1,r1,10\np1,r2,20\n")
    decl = {
        "from": "reads.csv",
        "key": "patient_id",
        "attributes": ["depth", "read_id"],
        "cluster_by": "site",
        "measurements": {"by": "read_id", "collapse": "first"},
    }
    roster, _, _ = resolve_units(decl, input_dir)
    with pytest.raises(ContractError) as e:
        clusters_of(roster, "site")
    assert e.value.code == "E-DATA-CLUSTER-UNKNOWN"


# --- a stratum must be constant within a cluster ------------------------------


def _strata(rows: list[tuple[str, str, str]]) -> UnitList:
    """`(key, animal, label)` rows, as a roster carrying both attributes."""
    return UnitList(
        [
            Unit(key=key, paths=(), attributes={"animal_id": animal, "label": label})
            for key, animal, label in rows
        ]
    )


_ANIMALS = {"A1": 7, "A2": 3, "A3": 3, "A4": 1, "A5": 1}
_ANIMAL_LABELS = {"A1": "tumor", "A2": "normal", "A3": "tumor", "A4": "normal", "A5": "tumor"}


def _animal_rows(varying: bool) -> list[tuple[str, str, str]]:
    """The fixture both halves share: 15 cells over 5 animals, sized 7/3/3/1/1.

    It discriminates because neither coincidence holds. Animals `A1`, `A2` and
    `A3` hold several cells each, so a stratum is not constant within a cluster
    merely for the cluster being a singleton; and `label` takes both values across
    the roster, so it is not constant globally either. `varying` flips exactly one
    cell of `A3` — a three-cell animal, so the flipped cell has siblings to
    disagree with — which is the whole difference between the probe and its
    control.
    """
    rows = []
    for animal, n in _ANIMALS.items():
        for i in range(n):
            label = _ANIMAL_LABELS[animal]
            if varying and animal == "A3" and i == 0:
                label = "normal"
            rows.append((f"{animal}_{i}", animal, label))
    return rows


def test_a_stratum_varying_inside_a_cluster_is_found():
    """`reference.md` § Clustered units: stratifying folds on an attribute that
    varies inside a cluster is unsatisfiable once the cluster is indivisible. The
    offender is named with the values it carries, so the reader knows which animal
    to look at."""
    roster = _strata(_animal_rows(varying=True))
    found = stratum_varies_within_cluster(roster, "animal_id", "label")
    assert found is not None
    cluster, values = found
    assert cluster == "A3"
    assert values == ["normal", "tumor"]


def test_a_stratum_constant_within_every_cluster_is_not_found():
    """The control that must report: the same 15 cells over the same 5 animals,
    with `label` constant within each animal and differing *across* them — a
    stratum a cluster-respecting split can balance, differing from the probe by one
    cell's label."""
    roster = _strata(_animal_rows(varying=False))
    assert stratum_varies_within_cluster(roster, "animal_id", "label") is None


def test_a_cell_carrying_no_stratum_value_varies_from_its_siblings():
    """Totality: a cell with no value for the stratum has nothing to be balanced
    on, so within a cluster whose other cells declare one it is a variation like any
    other. Two cells both carrying none agree, and a stratum no unit carries at all
    is the `-UNKNOWN` half's finding rather than this one's."""
    roster = _strata([("c0", "A1", "tumor")])
    roster = UnitList(
        [
            roster[0],
            Unit(key="c1", paths=(), attributes={"animal_id": "A1"}),
        ]
    )
    found = stratum_varies_within_cluster(roster, "animal_id", "label")
    assert found == ("A1", ["no value", "tumor"])
    both_missing = UnitList(
        [
            Unit(key="c0", paths=(), attributes={"animal_id": "A1"}),
            Unit(key="c1", paths=(), attributes={"animal_id": "A1"}),
        ]
    )
    assert stratum_varies_within_cluster(both_missing, "animal_id", "label") is None


def test_the_stratum_check_reads_cluster_membership_from_the_one_authority():
    """`clusters_of` is the single authority, so a unit carrying no cluster value
    raises `E-DATA-CLUSTER-UNKNOWN` from there rather than being grouped into a
    cluster of its own — which would make its stratum trivially constant and hide a
    real variation."""
    roster = UnitList(
        [
            Unit(key="c0", paths=(), attributes={"animal_id": "A1", "label": "tumor"}),
            Unit(key="c1", paths=(), attributes={"label": "normal"}),
        ]
    )
    with pytest.raises(ContractError) as e:
        stratum_varies_within_cluster(roster, "animal_id", "label")
    assert e.value.code == "E-DATA-CLUSTER-UNKNOWN"


def test_holdout_sizes_is_the_single_authority_for_the_split_sizes():
    """One arithmetic for the split, shared by `validate`'s refusal and the
    draw. `_apportion`'s largest-remainder rule, which `assignment_for`'s
    `random` branch already uses — so a `frac` `validate` approves is a `frac`
    the draw realizes at the same sizes.

    Each row is chosen so a DIFFERENT wrong rule gives a different answer:
    truncation, rounding, and largest-remainder disagree on at least one."""
    assert holdout_sizes(10, 0.2) == (8, 2)
    assert holdout_sizes(240, 0.2) == (192, 48)
    # 7 × 0.2 = 1.4: truncation gives 1 — this row separates largest-remainder
    # (and rounding) from truncation, not from each other.
    assert holdout_sizes(7, 0.2) == (6, 1)
    # 4 × 0.2 = 0.8: the floor is 0 and the remainder goes to the LARGEST
    # fractional part, which is the test side's 0.8 against the train side's
    # 3.2 — so largest-remainder gives 1 here where truncation gives 0.
    assert holdout_sizes(4, 0.2) == (3, 1)
    # 6 × 0.25 = 1.5: banker's-rounding `round()` rounds a .5 tie to the
    # nearest EVEN integer, giving `test = 2`; largest-remainder allots the
    # single remainder unit to the side with the larger fractional part when
    # there is one, and ties broken any other way from `round()`'s still
    # disagree here. This is the row task 7's review named as missing — a
    # rounding-based reimplementation of this function passes every other row
    # in this test (task 7 review, finding 2).
    assert holdout_sizes(6, 0.25) == (5, 1)
    # The case the refusal exists for: no rule can give the test side a unit.
    assert holdout_sizes(2, 0.2) == (2, 0)
    assert sum(holdout_sizes(13, 0.3)) == 13


def _holdout_roster(n, **attrs_by_index):
    """`n` units keyed `u0..u{n-1}`, each carrying whatever the caller maps.

    Named distinctly from the module's other `_roster(n) -> UnitList` (used
    throughout this file, keys zero-padded to 3 digits and pinned against
    exact literals at lines 296 and 333-337) rather than reusing that name:
    the two would collide as the same module-level binding, and the later
    definition would silently repoint every earlier call to a different key
    format."""
    return UnitList(
        [
            Unit(key=f"u{i}", paths=(), attributes={k: v(i) for k, v in attrs_by_index.items()})
            for i in range(n)
        ]
    )


def test_an_unclustered_holdout_cuts_the_shuffled_roster_at_the_apportioned_sizes():
    """`_apportion` + one shuffle + consecutive slices — `assignment_for`'s
    `random` branch, one declaration over. The realized membership is pinned as
    a literal derived by RUNNING this, not by predicting it: a predicted
    membership that happened to match a wrong construction is how a 13-unit
    apportionment matched a reverse-order mutant by coincidence in an earlier
    slice."""
    plan = holdout_for(_holdout_roster(10), {"method": "random", "frac": 0.2}, seed=1234)
    assert len(plan.train) == 8 and len(plan.test) == 2
    assert set(plan.train) | set(plan.test) == {f"u{i}" for i in range(10)}
    assert not set(plan.train) & set(plan.test)
    assert plan.seed == 1234
    assert plan.strata == ()
    # PINNED LITERALS — derived by running the implementation (see task-10-report.md).
    assert plan.train == ("u2", "u8", "u3", "u5", "u6", "u4", "u9", "u0")
    assert plan.test == ("u1", "u7")


def test_the_same_seed_and_roster_draw_the_same_holdout_and_a_different_seed_does_not():
    """Determinism, and the positive companion that keeps it from being
    vacuous: a different seed must give a DIFFERENT partition, or a draw that
    ignored the seed entirely would pass the first assertion alone."""
    a = holdout_for(_holdout_roster(20), {"method": "random", "frac": 0.25}, seed=7)
    b = holdout_for(_holdout_roster(20), {"method": "random", "frac": 0.25}, seed=7)
    c = holdout_for(_holdout_roster(20), {"method": "random", "frac": 0.25}, seed=8)
    assert a.test == b.test
    assert a.test != c.test


def test_a_by_attribute_holdout_reads_the_column_and_records_no_draw():
    """Read through `arms_of`, the single authority for a column-read
    partition — so roster order is preserved and set equality is enforced by
    the same function an arm assignment uses. No seed and no strata are
    recorded, `ArmPlan`'s own convention: reading a partition the data holds is
    not drawing one."""
    roster = _holdout_roster(10, split=lambda i: "test" if i % 5 == 0 else "train")
    plan = holdout_for(roster, {"method": "by_attribute", "from": "split"}, seed=1234)
    assert plan.test == ("u0", "u5")
    assert plan.train == ("u1", "u2", "u3", "u4", "u6", "u7", "u8", "u9")
    assert plan.seed is None
    assert plan.strata == ()


def test_a_by_attribute_holdout_over_a_column_that_is_not_the_two_literals_raises():
    """The run-time half of `E-DATA-HOLDOUT-VALUES`, through `arms_of`'s own
    set equality. `validate` refuses this first; the draw refuses it too rather
    than partitioning on whatever it finds."""
    roster = _holdout_roster(10, split=lambda i: "A" if i % 2 else "B")
    with pytest.raises(ContractError) as exc:
        holdout_for(roster, {"method": "by_attribute", "from": "split"}, seed=1)
    assert exc.value.code == "E-DATA-HOLDOUT-VALUES"
    # Asserts the agreement `holdout_values_fault` exists to guarantee — the
    # raise's wording IS the function's answer, not an independent literal that
    # could drift from it.
    assert str(exc.value) == holdout_values_fault(roster, "split")


@pytest.mark.parametrize(
    "n,frac,empty_side",
    [(2, 0.2, "test"), (2, 0.9, "train")],
    ids=["the test side is apportioned none", "the train side is apportioned none"],
)
def test_a_holdout_that_leaves_a_side_empty_raises(n, frac, empty_side):
    """Both sides, because `validate` refuses only the test one: 2 units at
    `frac: 0.9` apportions `(0, 2)` and would fit a model on nothing.
    `assignment_for`'s posture — the draw holds the realized sizes and is the
    last place that can see them."""
    with pytest.raises(ContractError) as exc:
        holdout_for(_holdout_roster(n), {"method": "random", "frac": frac}, seed=1)
    assert exc.value.code == "E-DATA-HOLDOUT-EMPTY"
    # The invariant tail names both "the training side" and "the test side" in
    # every instance of this message, so `empty_side in str(exc.value)` alone
    # cannot discriminate which one is actually empty. `leaves the {side} side
    # empty` is the one phrase that names the computed side specifically —
    # task 11 merged this with the clustered/stratified coverage check, one
    # refusal rather than two of the same fault.
    assert f"leaves the {empty_side} side empty" in str(exc.value)


@pytest.mark.parametrize("method", ["stratified", "", None, "by_attributes"])
def test_an_unknown_holdout_method_raises_rather_than_falling_back(method):
    """An allowlist, not a denylist of the methods that happen to draw today.
    `validate` refuses an out-of-enum method first; this is what stops a THIRD
    method added to `HOLDOUT_METHODS` and to nothing else from validating clean
    and then silently partitioning on a column."""
    with pytest.raises(NotImplementedError) as exc:
        holdout_for(_holdout_roster(10), {"method": method, "frac": 0.2}, seed=1)
    assert repr(method) in str(exc.value)
    assert "random" in str(exc.value)
    assert "by_attribute" in str(exc.value)


def test_holdout_methods_realized_is_pinned_by_what_it_documents():
    """`HOLDOUT_METHODS_REALIZED` is read at exactly one place — the final
    `NotImplementedError`'s message — and pinned by nothing else, so adding a
    method to the tuple without building the branch behind it would make that
    message claim a draw this build does not perform.
    `DRAWN_ASSIGN_METHODS`'s own test is the model: every declared member must
    actually draw or read a plan, not merely fail to hit the final raise."""
    assert HOLDOUT_METHODS_REALIZED == ("random", "by_attribute")
    random_roster = _holdout_roster(10)
    attr_roster = _holdout_roster(10, split=lambda i: "test" if i % 5 == 0 else "train")
    for method, roster, block in (
        ("random", random_roster, {"method": "random", "frac": 0.2}),
        ("by_attribute", attr_roster, {"method": "by_attribute", "from": "split"}),
    ):
        assert method in HOLDOUT_METHODS_REALIZED
        plan = holdout_for(roster, block, seed=1)
        assert isinstance(plan, HoldoutPlan)


def test_a_clustered_holdout_keeps_every_cluster_whole():
    """`reference.md` § Clustered units: "core computed the partition, so core
    keeps it indivisible." A holdout that trains on one cell of an animal and
    tests on another leaks just as thoroughly for happening only once.

    Twelve units in six clusters of two, so both a correct draw and a
    unit-level one give the same SIZES — the cluster-integrity assertion is the
    only thing that separates them, which is why the fixture is built this way
    rather than with clusters of one."""
    roster = _holdout_roster(12, animal=lambda i: f"a{i // 2}")
    clusters = {f"u{i}": f"a{i // 2}" for i in range(12)}
    plan = holdout_for(roster, {"method": "random", "frac": 0.5}, seed=99, clusters=clusters)
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

    The unclustered path shuffles unit keys and cuts two consecutive slices;
    the clustered path shuffles cluster names, sorts largest-first, and deals
    each to the bucket furthest below its own target share — which
    interleaves by ratio rather than slicing. **Even with one cluster per
    unit, no agreement between the two on SIZE is promised** (a sweep found
    90 disagreements over n x frac, some outright legality disagreements —
    see `holdout_for`'s docstring); the only difference this fixture can
    assert without pinning a coincidence is MEMBERSHIP. `len(plain.test) == 4`
    is this seed's realized size, asserted as a fact, not compared against
    the clustered draw's own (possibly different) realized size."""
    roster = _holdout_roster(10, animal=lambda i: f"u{i}")
    singleton = {f"u{i}": f"u{i}" for i in range(10)}
    plain = holdout_for(roster, {"method": "random", "frac": 0.4}, seed=5)
    clustered = holdout_for(roster, {"method": "random", "frac": 0.4}, seed=5, clusters=singleton)
    assert len(plain.test) == 4
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
    roster = _holdout_roster(14, band=lambda i: labels[i])
    plan = holdout_for(roster, {"method": "random", "frac": 0.5, "stratify_by": ["band"]}, seed=17)
    assert plan.strata == ("band",)
    per_stratum = {}
    for name in sizes:
        members = {f"u{i}" for i, lab in enumerate(labels) if lab == name}
        per_stratum[name] = len(members & set(plan.test))
    assert per_stratum == {"big": 4, "mid": 2, "small": 1}
    # Membership too, not only counts: the counts are FORCED by the
    # apportionment, so no count assertion can see a change in how the
    # generator is carried across strata — the same dimension-no-assertion-
    # can-see shape that let a deleted shuffle pass an earlier slice's suite.
    # PINNED LITERAL — derived by running the implementation (see task-11-report.md).
    assert set(plan.test) == {"u2", "u5", "u6", "u7", "u8", "u11", "u13"}


def test_a_stratified_clustered_holdout_composes_both_rules():
    """The composition: strata outside, whole clusters inside — the same
    arrangement `assignment_for` uses, and sound only while
    `E-DATA-HOLDOUT-STRATIFY-VARIES` refuses a cluster carrying two stratum
    values, since such a cluster would belong to two groups and be divided.

    Every cluster whole AND every stratum represented on both sides."""
    labels = ["x"] * 8 + ["y"] * 8
    roster = _holdout_roster(16, animal=lambda i: f"a{i // 2}", band=lambda i: labels[i])
    clusters = {f"u{i}": f"a{i // 2}" for i in range(16)}
    plan = holdout_for(
        roster,
        {"method": "random", "frac": 0.5, "stratify_by": ["band"]},
        seed=23,
        clusters=clusters,
    )
    assert plan.strata == ("band",)
    train, test = set(plan.train), set(plan.test)
    for cluster in {f"a{i}" for i in range(8)}:
        members = {k for k, c in clusters.items() if c == cluster}
        assert members <= train or members <= test, cluster
    # Counts, not only "some of each" — forced by 4 whole clusters of 2 units
    # per band at equal weights, so an implementation that dropped the strata
    # entirely and dealt clusters over the whole 16-unit roster would still
    # put both bands on both sides by chance (this exact fixture does, at
    # `frac: 0.5` over two equal-sized 8-unit bands) but could not produce a
    # clean 4/4 split for BOTH bands.
    for band in ("x", "y"):
        members = {f"u{i}" for i, lab in enumerate(labels) if lab == band}
        assert len(members & test) == 4 and len(members & train) == 4, band
    # PINNED LITERAL — derived by running the implementation (see the task-11
    # fix report), catching a composition that ignores strata even when it
    # happens to produce a 4/4 count for both bands by coincidence.
    assert test == {"u4", "u5", "u6", "u7", "u12", "u13", "u14", "u15"}


def test_a_stratified_holdout_that_leaves_a_side_empty_across_every_stratum_raises():
    """Coverage over the MERGED draw, `assignment_for`'s rule for the identical
    composition: a side a small stratum apportioned nothing is fine while
    another stratum covered it, and only a side empty everywhere is refused.

    Two strata of one unit each at `frac: 0.2` apportion `(1, 0)` in both, so
    the test side is empty across the whole draw."""
    roster = _holdout_roster(2, band=lambda i: f"b{i}")
    with pytest.raises(ContractError) as exc:
        holdout_for(roster, {"method": "random", "frac": 0.2, "stratify_by": ["band"]}, seed=1)
    assert exc.value.code == "E-DATA-HOLDOUT-EMPTY"
    # The full message, not only the code — pins the `", drawn within N stratum
    # declaration(s)"` fragment, unpinned by any test before this one.
    assert "leaves the test side empty, drawn within 1 stratum declaration(s)" in str(exc.value)
    assert "over whole clusters" not in str(exc.value)


def test_a_single_cluster_holdout_leaves_the_test_side_empty_over_whole_clusters():
    """The second half of the deleted `NotImplementedError` test's coverage —
    a single cluster spanning the whole roster cannot split, so the whole
    roster is dealt to one bucket (ties break to the earlier-declared level,
    `train`) and the test side is empty. Pins the `" over whole clusters"`
    suffix, unpinned by any test until now, and is the clustered branch of
    `E-DATA-HOLDOUT-EMPTY` that no earlier test reaches."""
    roster = _holdout_roster(10)
    clusters = {f"u{i}": "c0" for i in range(10)}
    with pytest.raises(ContractError) as exc:
        holdout_for(roster, {"method": "random", "frac": 0.2}, seed=1, clusters=clusters)
    assert exc.value.code == "E-DATA-HOLDOUT-EMPTY"
    assert "leaves the test side empty" in str(exc.value)
    assert "over whole clusters" in str(exc.value)
    assert "stratum declaration" not in str(exc.value)


def test_a_holdout_stratify_by_naming_no_attribute_names_the_holdout_path():
    """The first half of the deleted `NotImplementedError` test's coverage,
    and Step 3(a)'s own deliverable: the `declaration` argument
    `holdout_for` hands `_stratum_groups` must read
    `data.units.holdout.stratify_by`, the path a holdout's config actually
    has — not an assign-shaped path built by interpolating an axis name into
    a fixed `data.units.assign.<...>` template, which would print
    `data.units.assign.holdout.stratify_by`, a path no config can hold."""
    with pytest.raises(NotImplementedError) as exc:
        holdout_for(
            _holdout_roster(10),
            {"method": "random", "frac": 0.2, "stratify_by": ["x"]},
            seed=1,
        )
    assert "`data.units.holdout.stratify_by` names 'x'" in str(exc.value)
    assert "`E-DATA-HOLDOUT-STRATIFY-UNKNOWN`" in str(exc.value)
    assert "E-DATA-ASSIGN-STRATIFY-FORWARD" not in str(exc.value)
    assert "E-DATA-ASSIGN-STRATIFY-UNKNOWN" not in str(exc.value)


def test_a_thin_stratum_alone_does_not_raise():
    """The positive companion for the rule above, produced by the code under
    test: one stratum apportioning the test side nothing is accepted while
    another covers it. Without this the refusal above is indistinguishable from
    a per-stratum coverage rule."""
    labels = ["big"] * 9 + ["tiny"]
    roster = _holdout_roster(10, band=lambda i: labels[i])
    plan = holdout_for(roster, {"method": "random", "frac": 0.2, "stratify_by": ["band"]}, seed=3)
    assert plan.test and plan.train
    tiny = {"u9"}
    # `tiny <= set(plan.train)` is forced by `holdout_sizes(1, 0.2) == (1, 0)`
    # under ANY correct per-stratum apportionment, so it cannot distinguish a
    # construction — the "big" stratum's actual membership is what can.
    # PINNED LITERAL — derived by running the implementation.
    assert tiny <= set(plan.train)
    assert set(plan.test) == {"u2", "u3"}


def test_a_by_attribute_holdout_with_no_from_raises_not_realized():
    """`method: by_attribute` naming no column is `validate`'s `E-DATA-HOLDOUT-FROM`;
    the draw refuses it too rather than reading a column that does not exist."""
    with pytest.raises(NotImplementedError) as exc:
        holdout_for(_holdout_roster(10), {"method": "by_attribute"}, seed=1)
    assert "no column" in str(exc.value)
    assert "E-DATA-HOLDOUT-FROM" in str(exc.value)


@pytest.mark.parametrize("frac", [None, "0.2", True, -0.5, 0.0, 1.0, 2.0])
def test_a_random_holdout_with_an_unusable_frac_raises_not_realized(frac):
    """Widened to refuse both an unusable TYPE (`None`, a string, a bool) and
    an out-of-range VALUE, so the docstring's "both sides are refused empty"
    guarantee holds for every `frac` rather than only the ones `validate`
    would have let through to the empty-side check."""
    with pytest.raises(NotImplementedError) as exc:
        holdout_for(_holdout_roster(10), {"method": "random", "frac": frac}, seed=1)
    assert "no usable `frac`" in str(exc.value)
    assert "E-DATA-HOLDOUT-FRAC" in str(exc.value)


_MEASUREMENT_ROWS = [
    {"patient_id": "p1", "read_id": "r1", "split": "train", "value": "1"},
    {"patient_id": "p1", "read_id": "r2", "split": "test", "value": "2"},
    {"patient_id": "p2", "read_id": "r3", "split": "test", "value": "3"},
]


def _units_from_rows(rows, attributes):
    return [
        Unit(key=r["patient_id"], paths=(), attributes={a: r[a] for a in attributes}) for r in rows
    ]


def test_a_holdout_from_column_varying_within_a_unit_is_refused():
    """A `by_attribute` holdout reading a column that disagrees between two
    rows of one unit would file that unit on whichever side the row the
    collapse kept says — a train/test membership decided by row order.

    `p1` carries `train` and `test`; `p2` carries one value, so the fixture
    also proves the check is per-unit rather than per-roster."""
    units = _units_from_rows(_MEASUREMENT_ROWS, ["read_id", "split", "value"])
    constant = _holdout_constant_column({"method": "by_attribute", "from": "split"})
    assert constant == {"holdout.from": "split"}
    with pytest.raises(ContractError) as exc:
        collapse_measurements(units, "read_id", "first", constant)
    assert exc.value.code == "E-DATA-HOLDOUT-VARIES"
    assert "split" in str(exc.value)


def test_a_constant_holdout_from_column_collapses_cleanly():
    """The positive companion, produced by the code under test: the same
    declaration over rows that AGREE collapses without raising, and the
    surviving unit keeps the value. Without this the test above passes
    identically if the rule refused every `holdout.from`."""
    rows = [dict(r, split="train") for r in _MEASUREMENT_ROWS]
    units = _units_from_rows(rows, ["read_id", "split", "value"])
    collapsed, counts = collapse_measurements(
        units,
        "read_id",
        "first",
        _holdout_constant_column({"method": "by_attribute", "from": "split"}),
    )
    assert [u.key for u in collapsed] == ["p1", "p2"]
    assert [u.attributes["split"] for u in collapsed] == ["train", "train"]
    assert counts == [2, 1]


@pytest.mark.parametrize(
    "decl",
    [
        None,
        {},
        "nonsense",
        {"method": "random", "frac": 0.2},
        {"method": "random", "frac": 0.2, "from": "split"},
        {"method": "by_attribute"},
        {"method": "by_attribute", "from": ""},
        {"method": "by_attribute", "from": 7},
    ],
    ids=[
        "absent",
        "empty",
        "not a mapping",
        "random",
        "random with a stray from",
        "by_attribute with no from",
        "empty from",
        "non-string from",
    ],
)
def test_the_holdout_accessor_resolves_no_column_for_these(decl):
    """It resolves a column or it does not; it never reports a malformed
    declaration. `E-DATA-HOLDOUT-METHOD`, `-FROM` and `-NO-DRAW` are
    `validate`'s findings to raise, not a `ContractError` from a run that
    resolution has no path to report through.

    The `random with a stray from` row is the load-bearing one: the gate is on
    the METHOD, so a drawn split whose declaration happens to carry a `from`
    still reads no column — a run that raised `E-DATA-HOLDOUT-VARIES` there
    would be refusing a config over a column its draw never reads."""
    assert _holdout_constant_column(decl) == {}


def test_collapse_stops_at_the_first_entry_of_the_constant_mapping_it_is_given():
    """`collapse_measurements` stops at the first `constant` entry whose column
    disagrees and raises that entry's code — this test builds the mapping by
    hand, so it pins only that stopping behaviour, not that `resolve_units`
    builds the mapping in any particular order. The order `resolve_units`
    itself builds — `assign` before `holdout` before the flat pair — is pinned
    by `test_resolve_units_checks_holdout_after_assign_and_before_cluster`,
    which calls `resolve_units` on a real declaration; that is where the
    ordering guarantee actually lives.

    The fixture makes ONE unit violate `assign`, `holdout` and `cluster_by`
    at once — three declarations, so the three candidate orderings each give a
    different answer, which two declarations could not distinguish."""
    rows = [
        {"patient_id": "p1", "read_id": "r1", "split": "train", "arm": "a", "site": "s1"},
        {"patient_id": "p1", "read_id": "r2", "split": "test", "arm": "b", "site": "s2"},
    ]
    units = _units_from_rows(rows, ["read_id", "split", "arm", "site"])
    constant = _assign_constant_columns({"arm": {"method": "by_attribute"}})
    constant.update(_holdout_constant_column({"method": "by_attribute", "from": "split"}))
    constant.update({"cluster_by": "site"})
    with pytest.raises(ContractError) as exc:
        collapse_measurements(units, "read_id", "first", constant)
    assert exc.value.code == "E-DATA-ASSIGN-VARIES"

    # Remove the highest-priority declaration and the NEXT one reports — which
    # is what proves the order rather than merely that `assign` reports.
    without_assign = _holdout_constant_column({"method": "by_attribute", "from": "split"})
    without_assign.update({"cluster_by": "site"})
    with pytest.raises(ContractError) as exc2:
        collapse_measurements(units, "read_id", "first", without_assign)
    assert exc2.value.code == "E-DATA-HOLDOUT-VARIES"


def test_a_pinned_holdout_seed_is_returned_literally_and_ignores_the_digest():
    """`sweep.sample_seed_for`'s load-bearing half, copied: on the pinned path
    the digest is not consulted at all, so a pinned split survives a roster
    that grows, shrinks or reorders.

    Three varying inputs against one pin, because a function that read ANY of
    them would move for at least one of these."""
    block = {"method": "random", "frac": 0.2, "seed": 4321}
    assert holdout_seed_for(block, "sha256:aaa", _roster(10)) == 4321
    assert holdout_seed_for(block, "sha256:bbb", _roster(10)) == 4321
    assert holdout_seed_for(block, "sha256:aaa", _roster(11)) == 4321


def test_a_boolean_seed_is_not_a_pin():
    """`isinstance(True, int)` is `True`, and `seed: true` is not a pin —
    `validate` refuses it as `E-DATA-HOLDOUT-SEED`, and honouring it as `1`
    here would record a derived seed under a key the config wrote
    deliberately."""
    derived = holdout_seed_for({"seed": True}, "sha256:aaa", _roster(10))
    assert derived != 1
    assert derived == holdout_seed_for({}, "sha256:aaa", _roster(10))


def test_the_derived_holdout_seed_mixes_the_digest_and_the_resolved_roster():
    """§ What `auto` derives from's new row. Each assertion changes exactly one
    input, so a derivation that ignored either would fail one of them."""
    base = holdout_seed_for({}, "sha256:aaa", _roster(10))
    assert base == holdout_seed_for({"seed": "auto"}, "sha256:aaa", _roster(10))
    assert base != holdout_seed_for({}, "sha256:bbb", _roster(10))
    assert base != holdout_seed_for({}, "sha256:aaa", _roster(11))
    # `units_hash` covers the roster IN RESOLVED ORDER, so a reordered roster
    # is a different trial and must draw a different split.
    reordered = UnitList(list(_roster(10))[::-1])
    assert base != holdout_seed_for({}, "sha256:aaa", reordered)
    assert 0 <= base < 2**32


def test_the_holdout_seed_is_not_the_fold_seed_for_the_same_digest():
    """`_seed_from` hardcodes `|folds`. The two declarations are mutually
    exclusive today (`E-DATA-HOLDOUT-FOLD`), so nothing observes a collision —
    which is the argument for the suffix rather than against it: the two stay
    independent whatever a later slice permits."""
    assert holdout_seed_for({}, "sha256:aaa", _roster(10)) != _seed_from("sha256:aaa")


def test_the_holdout_seed_is_not_an_assign_axis_seed_for_the_same_digest():
    """The other neighbour, and the one whose construction this copies: same
    digest, same roster, different suffix."""
    roster = _roster(10)
    assert holdout_seed_for({}, "sha256:aaa", roster) != assign_seed_for(
        {}, "holdout", "sha256:aaa", roster
    )


def test_an_unregistered_resolver_name_is_refused_from_metadata_alone(installed, registries):
    """`E-RESOLVER-UNKNOWN`, and the message names what it did find — the ordinary
    cause is a spelling and the ordinary remedy is reading the list."""
    from publishable.errors import ContractError
    from publishable.units import _resolver_for

    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "no_one:resolve"}})
    with pytest.raises(ContractError) as excinfo:
        _resolver_for("plate_welz")
    assert excinfo.value.code == "E-RESOLVER-UNKNOWN"
    assert "plate_welz" in str(excinfo.value)
    assert "plate_wells" in str(excinfo.value)  # the list it names


def test_a_registered_resolver_name_loads_the_object_behind_it(installed, registries, tmp_path):
    """THE HONOURING. Without this, a `_resolver_for` returning `None` for every
    name would pass every refusal test above and below it."""
    from publishable.units import _resolver_for

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "loadable_r24:resolve"}}
    )
    (site / "loadable_r24.py").write_text(
        "from publishable import register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n    return ['loaded']\n"
    )
    importlib.invalidate_caches()
    try:
        assert _resolver_for("plate_wells")(None, None) == ["loaded"]
    finally:
        sys.modules.pop("loadable_r24", None)


def test_a_resolver_whose_module_raises_is_contained_as_a_plugin_load(installed, registries):
    """`E-PLUGIN-LOAD`'s first production caller. The distribution is named rather
    than the module, since a distribution is what a reader uninstalls or pins."""
    from publishable.errors import ContractError
    from publishable.units import _resolver_for

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "broken_r24:resolve"}}
    )
    (site / "broken_r24.py").write_text("raise RuntimeError('module scope blew up')\n")
    importlib.invalidate_caches()
    try:
        with pytest.raises(ContractError) as excinfo:
            _resolver_for("plate_wells")
    finally:
        sys.modules.pop("broken_r24", None)
    assert excinfo.value.code == "E-PLUGIN-LOAD"
    assert "dist-one 1.0" in str(excinfo.value)


def test_a_decorator_argument_disagreeing_with_the_entry_point_key_is_refused(
    installed, registries
):
    """`E-PLUGIN-DECORATOR`'s first production caller, and decision 4's siting:
    the object is in hand at `validate`, so the disagreement is knowable there."""
    from publishable.errors import ContractError
    from publishable.units import _resolver_for

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "misnamed_r24:resolve"}}
    )
    (site / "misnamed_r24.py").write_text(
        "from publishable import register_resolver\n\n\n"
        '@register_resolver("plate_positions")\n'
        "def resolve(io, cfg):\n    return []\n"
    )
    importlib.invalidate_caches()
    try:
        with pytest.raises(ContractError) as excinfo:
            _resolver_for("plate_wells")
    finally:
        sys.modules.pop("misnamed_r24", None)
    assert excinfo.value.code == "E-PLUGIN-DECORATOR"
    assert "plate_wells" in str(excinfo.value)
    assert "plate_positions" in str(excinfo.value)


def test_a_core_suffix_claim_at_import_time_is_recoded_as_plugin_load(installed, registries):
    """Pins `spec-defects.md`'s CLOSED entry on the `E-PLUGIN-COLLISION` ->
    `E-PLUGIN-LOAD` substitution: `register_writer`/`register_reader` raise
    `E-PLUGIN-COLLISION` directly, but reached from inside a module
    `load_entry_point` is importing, its own broad `except Exception` catches
    that `ContractError` like any other failure and re-reports it as
    `E-PLUGIN-LOAD` — the same substitution `E-TEMPLATE-LOAD` already makes for
    a coded error from a local template's top level. Without this test, that
    substitution was accurate but asserted by nothing."""
    from publishable.errors import ContractError
    from publishable.units import _resolver_for

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "collides_r24:resolve"}}
    )
    (site / "collides_r24.py").write_text(
        "from publishable import register_writer\n\n\n"
        '@register_writer(".csv")\n'
        "def write(obj):\n    return b''\n"
    )
    importlib.invalidate_caches()
    try:
        with pytest.raises(ContractError) as excinfo:
            _resolver_for("plate_wells")
    finally:
        sys.modules.pop("collides_r24", None)
    assert excinfo.value.code == "E-PLUGIN-LOAD"
    assert ".csv" in str(excinfo.value)


def _install_resolver(installed, tmp_path, module: str, body: str):
    """One installed distribution whose `publishable.resolvers` entry point points
    at a module this writes. Returns nothing: every caller pops `module` from
    `sys.modules` in its own `finally`, because a real import leaks and Part A's
    fixtures deliberately could not import at all."""
    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": f"{module}:resolve"}}
    )
    (site / f"{module}.py").write_text(body)
    importlib.invalidate_caches()


_YIELDS_TWO = """\
from publishable import Unit, register_resolver


@register_resolver("plate_wells")
def resolve(io, cfg):
    for row in io.read_input("layout.csv"):
        yield Unit(
            key=row["barcode"] + ":" + row["well"],
            paths=(row["read"],),
            attributes={"operator": row["operator"]},
        )
"""


def test_a_resolver_source_yields_the_roster_in_yield_order(installed, registries, tmp_path):
    """THE HONOURING, and the property `units_hash` and `assign.method: blocked`
    both rest on: yield order is the resolved order. The fixture's rows are
    deliberately NOT in sorted key order, so a dispatch that sorted — the way
    `_from_glob` must — comes out different rather than identical."""
    from publishable.artifacts import ResolverIO
    from publishable.config import Config
    from publishable.units import resolve_units

    (tmp_path / "layout.csv").write_text(
        "barcode,well,read,operator\nB9,h3,reads/b9.fq,mo\nA1,c2,reads/a1.fq,kj\n"
    )
    _install_resolver(installed, tmp_path, "yielding_r25", _YIELDS_TWO)
    try:
        roster, technical_n, columns = resolve_units(
            {"from": {"resolver": "plate_wells"}, "key": "well", "attributes": ["operator"]},
            tmp_path,
            cfg=Config({}),
            resolver_io=ResolverIO(tmp_path),
        )
    finally:
        sys.modules.pop("yielding_r25", None)

    assert [u.key for u in roster] == ["B9:h3", "A1:c2"]
    assert [u.paths for u in roster] == [("reads/b9.fq",), ("reads/a1.fq",)]
    assert technical_n is None
    assert columns == frozenset({"operator"})


def test_a_resolver_yielding_something_that_is_not_a_unit_is_refused(
    installed, registries, tmp_path
):
    """`E-RESOLVER-YIELD`. A resolver is the second place user code runs inside
    resolution, and `validate` is contracted never to raise — without this a
    yielded mapping reaches `u.key` as an `AttributeError` escaping `validate`."""
    from publishable.config import Config
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(
        installed,
        tmp_path,
        "wrongyield_r25",
        "from publishable import register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n    yield {'key': 'a1'}\n",
    )
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units(
                {"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path, cfg=Config({})
            )
    finally:
        sys.modules.pop("wrongyield_r25", None)
    assert excinfo.value.code == "E-RESOLVER-YIELD"
    assert "dict" in str(excinfo.value)


def test_a_resolver_source_reached_with_no_cfg_refuses_rather_than_crashing(
    installed, registries, tmp_path
):
    """Decision 6's named price. `cfg` is a defaulted keyword so ~60 existing call
    sites keep compiling, which makes `cfg=None` a reachable state rather than a
    hypothetical — core's resolved state disagreeing with itself, reported under
    the row that family already has."""
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "nocfg_r25", _YIELDS_TWO)
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units({"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path)
    finally:
        sys.modules.pop("nocfg_r25", None)
    assert excinfo.value.code == "E-RUN-RESOLVER-UNCONFIGURED"


def test_a_table_source_still_resolves_with_no_cfg(tmp_path):
    """THE CONTROL for the refusal above: the defaulted keyword must not have
    turned every existing caller into a refusal. Without this, a `cfg is None`
    guard placed one branch too high would pass every test in this file that
    passes a `cfg` and break every one that does not."""
    from publishable.units import resolve_units

    (tmp_path / "index.csv").write_text("patient_id\np1\np2\n")
    roster, _technical_n, columns = resolve_units(
        {"from": "index.csv", "key": "patient_id"}, tmp_path
    )
    assert [u.key for u in roster] == ["p1", "p2"]
    assert columns == frozenset({"patient_id"})


_YIELDS_PARTIAL = """\
from publishable import Unit, register_resolver


@register_resolver("plate_wells")
def resolve(io, cfg):
    yield Unit(key="a1", attributes={"operator": "kj", "plate": "P1", "scratch": "x"})
    yield Unit(key="b9", attributes={"operator": "mo", "plate": "P1"})
"""


def test_a_resolver_roster_is_projected_onto_the_declared_attributes(
    installed, registries, tmp_path
):
    """Everything downstream is indifferent to which form `from` took, and this is
    what makes it so: an undeclared attribute is dropped exactly as an undeclared
    CSV column is. `scratch` is yielded and not declared; asserting only that
    `operator` survives would pass on a pass-through implementation."""
    from publishable.config import Config
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "project_r27", _YIELDS_PARTIAL)
    try:
        roster, _n, columns = resolve_units(
            {"from": {"resolver": "plate_wells"}, "key": "well", "attributes": ["operator"]},
            tmp_path,
            cfg=Config({}),
        )
    finally:
        sys.modules.pop("project_r27", None)

    assert [dict(u.attributes) for u in roster] == [{"operator": "kj"}, {"operator": "mo"}]
    assert columns == frozenset({"operator", "plate", "scratch"})  # pre-projection, for task 28


def test_a_declared_attribute_no_unit_yields_is_refused_naming_the_resolver(
    installed, registries, tmp_path
):
    """`E-UNITS-ATTR-MISSING`, generalized past "which index.csv does not have".
    The message must name the resolver, or a reader is sent looking for a column
    in a file that has nothing to do with the fault."""
    from publishable.config import Config
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "missing_r27", _YIELDS_PARTIAL)
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units(
                {
                    "from": {"resolver": "plate_wells"},
                    "key": "well",
                    "attributes": ["operator", "site"],
                },
                tmp_path,
                cfg=Config({}),
            )
    finally:
        sys.modules.pop("missing_r27", None)
    assert excinfo.value.code == "E-UNITS-ATTR-MISSING"
    assert "'site'" in str(excinfo.value)
    assert "plate_wells" in str(excinfo.value)
    assert "index.csv" not in str(excinfo.value)


def test_a_name_only_some_units_yield_is_not_missing(installed, registries, tmp_path):
    """THE DISCRIMINATOR between the union and the intersection. `scratch` is
    carried by one of the two units; declaring it must resolve, with the unit that
    lacks it simply carrying no value — a table column that some rows leave blank
    behaves the same way. Without this fixture, union and intersection are the
    same answer and the choice is untested."""
    from publishable.config import Config
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "sparse_r27", _YIELDS_PARTIAL)
    try:
        roster, _n, _columns = resolve_units(
            {"from": {"resolver": "plate_wells"}, "key": "well", "attributes": ["scratch"]},
            tmp_path,
            cfg=Config({}),
        )
    finally:
        sys.modules.pop("sparse_r27", None)
    assert [dict(u.attributes) for u in roster] == [{"scratch": "x"}, {}]


def test_a_reserved_attribute_name_is_refused_before_a_missing_one(installed, registries, tmp_path):
    """One declaration, one code, whichever source it sits under: `_from_table` and
    `_from_glob` both check reserved before unsourced, and a resolver must not
    invert that. `paths` is reserved AND unyielded, so a wrong order gives
    `E-UNITS-ATTR-MISSING` instead."""
    from publishable.config import Config
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "reserved_r27", _YIELDS_PARTIAL)
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units(
                {"from": {"resolver": "plate_wells"}, "key": "well", "attributes": ["paths"]},
                tmp_path,
                cfg=Config({}),
            )
    finally:
        sys.modules.pop("reserved_r27", None)
    assert excinfo.value.code == "E-UNITS-ATTR-RESERVED"


def test_a_non_string_attribute_under_a_resolver_is_refused_not_a_crash(
    installed, registries, tmp_path
):
    """`resolve_units` is contracted never to escape with a bare `TypeError`.
    An unhashable declared attribute (a `dict`) would hit `attribute not in
    yielded`, which hashes it against a `set`, if the type guard were removed —
    reported as `E-UNITS-ATTR-MISSING` instead, the same identifier the table
    source's own non-string-item guard uses."""
    from publishable.config import Config
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "unhashable_r27", _YIELDS_PARTIAL)
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units(
                {
                    "from": {"resolver": "plate_wells"},
                    "key": "well",
                    "attributes": [{"operator": 1}],
                },
                tmp_path,
                cfg=Config({}),
            )
    finally:
        sys.modules.pop("unhashable_r27", None)
    assert excinfo.value.code == "E-UNITS-ATTR-MISSING"


_READS_A_PARAM = """\
from publishable import Unit, register_resolver


@register_resolver("plate_wells")
def resolve(io, cfg):
    yield Unit(key=str(cfg.parameters.analysis.method))
"""


def test_a_resolver_reading_a_swept_parameter_is_refused_under_its_own_code(
    installed, registries, tmp_path
):
    """`E-RESOLVER-SWEPT-PARAM`, not `E-STEP-SWEPT-PARAM`: the mechanism is shared
    and the fault is not — a reader holding the step's identifier is sent to a
    section describing a different fault at a different time."""
    from publishable.errors import ContractError
    from publishable.runner import resolve_wide_cfg
    from publishable.sweep import wide_swept_paths
    from publishable.units import resolve_units

    doc = {
        "parameters": {"analysis": {"method": "pearson"}},
        "sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}},
    }
    cfg = resolve_wide_cfg(doc, wide_swept_paths(doc["sweep"]))
    _install_resolver(installed, tmp_path, "swept_r29", _READS_A_PARAM)
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units({"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path, cfg=cfg)
    finally:
        sys.modules.pop("swept_r29", None)
    assert excinfo.value.code == "E-RESOLVER-SWEPT-PARAM"
    assert "plate_wells" in str(excinfo.value)
    assert "analysis.method" in str(excinfo.value)


def test_a_resolver_reading_a_parameter_the_sweep_leaves_alone_resolves(
    installed, registries, tmp_path
):
    """THE CONTROL, and § Where units come from's own sentence: "Parameters the
    sweep leaves alone are fair game, which is how a resolver is told which assay,
    panel, or shard to include." Without it, a refusal that fired for every `cfg`
    read would pass the test above."""
    from publishable.runner import resolve_wide_cfg
    from publishable.sweep import wide_swept_paths
    from publishable.units import resolve_units

    doc = {
        "parameters": {"analysis": {"method": "pearson"}},
        "sweep": {"grid": {"analysis.min_samples": [10, 20]}},
    }
    cfg = resolve_wide_cfg(doc, wide_swept_paths(doc["sweep"]))
    _install_resolver(installed, tmp_path, "unswept_r29", _READS_A_PARAM)
    try:
        roster, _n, _columns = resolve_units(
            {"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path, cfg=cfg
        )
    finally:
        sys.modules.pop("unswept_r29", None)
    assert [u.key for u in roster] == ["pearson"]


def test_a_resolvers_own_coded_refusal_keeps_its_own_identifier(installed, registries, tmp_path):
    """Only the sentinel read is re-coded. A resolver reading a file that is not
    there gets `E-UNITS-SOURCE-MISSING`'s cousin from `io`, and re-coding
    everything would tell a reader their sweep was at fault."""
    from publishable.config import Config
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(
        installed,
        tmp_path,
        "coded_r29",
        "from publishable import ContractError, Unit, register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n"
        "    raise ContractError('nope', code='E-UNITS-EMPTY')\n"
        "    yield Unit(key='a1')\n",
    )
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units(
                {"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path, cfg=Config({})
            )
    finally:
        sys.modules.pop("coded_r29", None)
    assert excinfo.value.code == "E-UNITS-EMPTY"


def test_index_names_covers_every_source_shape(tmp_path):
    """One expression, three sources: the source's own file where it names one,
    plus every path its units name. A table names its index and no paths; a glob
    names no index and one path per unit; a resolver names what it read and
    whatever its units carry. Asserted together, because shipping two of the three
    is how the glob case would be left at `sha256: None` silently."""
    from publishable.units import Unit, UnitList, index_names

    table = UnitList([Unit(key="p1"), Unit(key="p2")])
    globbed = UnitList([Unit(key="a.dcm", paths=("a.dcm",)), Unit(key="b.dcm", paths=("b.dcm",))])
    resolved = UnitList([Unit(key="a1", paths=("reads/a1.fq",))])

    assert index_names({"from": "index.csv"}, table) == {"index.csv"}
    assert index_names({"from": {"glob": "*.dcm"}}, globbed) == {"a.dcm", "b.dcm"}
    assert index_names({"from": {"resolver": "plate_wells"}}, resolved, ("layout.csv",)) == {
        "layout.csv",
        "reads/a1.fq",
    }
    assert index_names({"from": "index.csv"}, None) == {"index.csv"}  # no roster, still the index
