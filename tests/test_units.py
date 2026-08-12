# tests/test_units.py
from pathlib import Path

import pytest

from publishable import ContractError
from publishable.units import (
    Unit,
    UnitList,
    _apply,
    collapse_measurements,
    partition_units,
    resolve_units,
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
    units = resolve_units(
        {"from": "index.csv", "key": "patient_id", "attributes": ["label", "site"]}, input_dir
    )
    assert [u.key for u in units] == ["p3", "p1", "p2"], "row order is data, not cosmetic"
    assert len(units) == 3
    assert units[0].key == "p3"


def test_declared_attributes_are_readable_directly(input_dir: Path):
    units = resolve_units(
        {"from": "index.csv", "key": "patient_id", "attributes": ["label", "site"]}, input_dir
    )
    assert units[0].site == "a"
    assert units[0].attributes["label"] == "1"


def test_an_undeclared_column_is_not_an_attribute(input_dir: Path):
    units = resolve_units({"from": "index.csv", "key": "patient_id", "attributes": ["label"]},
                          input_dir)
    assert "site" not in units[0].attributes
    with pytest.raises(AttributeError):
        _ = units[0].site


def test_a_glob_resolves_lexicographically_with_the_path_as_key(input_dir: Path):
    units = resolve_units({"from": {"glob": "**/*.dcm"}, "key": "path"}, input_dir)
    assert [u.key for u in units] == ["scans/a.dcm", "scans/b.dcm", "top.dcm"]
    assert units[0].paths == ("scans/a.dcm",)


def test_a_non_recursive_glob_does_not_descend(input_dir: Path):
    units = resolve_units({"from": {"glob": "*.dcm"}, "key": "path"}, input_dir)
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
    units = resolve_units({"from": "single.csv", "key": "patient_id"}, input_dir)
    assert len(units) == 1
    assert units[0].key == "p1"


def test_a_missing_table_is_refused(input_dir: Path):
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "absent.csv", "key": "patient_id"}, input_dir)
    assert e.value.code == "E-UNITS-SOURCE-MISSING"


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
    units = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert len(list(units)) == 3          # iterate, repeatably
    assert len(list(units)) == 3
    assert len(units) == 3                # len
    assert units[1].key == "p1"           # index
    for absent in ("append", "index", "count", "sort", "__contains__"):
        assert not hasattr(units, absent), f"{absent} would make this a list"


def test_slicing_is_rejected_not_silently_returning_a_list(input_dir: Path):
    units = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    with pytest.raises(ContractError) as e:
        _ = units[0:2]
    assert e.value.code == "E-STEP-UNITS-CONTRACT"
    assert units[0].key == "p3"  # integer indexing still works


def test_a_string_index_is_rejected(input_dir: Path):
    units = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    with pytest.raises(ContractError) as e:
        _ = units["p1"]  # type: ignore[call-overload]
    assert e.value.code == "E-STEP-UNITS-CONTRACT"


def test_membership_and_reversed_are_deliberately_permitted(input_dir: Path):
    # Not part of the promised three operations, but both derive entirely from
    # `__iter__` (membership) and `len` + integer indexing (`reversed`), so any
    # backing that satisfies the contract satisfies these for free — unlike
    # slicing, which would return a foreign type. See spec-defects.md.
    units = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    first = units[0]
    assert first in units
    assert [u.key for u in reversed(units)] == ["p2", "p1", "p3"]


def test_train_raises_when_no_partition_is_declared(input_dir: Path):
    units = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    with pytest.raises(ContractError) as e:
        _ = units.train
    assert e.value.code == "E-STEP-UNITS-UNAVAILABLE"


def test_units_hash_follows_order_and_content(input_dir: Path):
    a = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    b = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert units_hash(a) == units_hash(b)
    assert units_hash(a).startswith("sha256:")
    (input_dir / "index.csv").write_text("patient_id,label,site\np1,0,b\np3,1,a\np2,1,a\n")
    reordered = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert units_hash(reordered) != units_hash(a), "order is part of the identity"


def _roster(n: int) -> UnitList:
    return UnitList([Unit(key=f"u{i:03d}", paths=(), attributes={}) for i in range(n)])


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
    assert {unit} == {Unit(key="u1")}          # hashable by key


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
    units = resolve_units({"from": {"glob": "*.dcm"}, "key": "path", "attributes": []}, input_dir)
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
    assert collapsed[0].depth == 15.0        # mean of 10 and 20
    assert collapsed[0].site == "A"          # non-numeric, constant: carried
    assert "read_id" not in collapsed[0].attributes   # the measurement axis is consumed


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
    assert _apply("sum", [5, 5]) == 10
    assert _apply("sum", [1000, 1000]) == 2000
    assert _apply("sum", [1, 2]) == 3          # already covered above; kept for contrast
    assert _apply("mean", [5, 5]) == 5         # mean over constant numeric: still a mean
    assert _apply("mean", ["A", "A"]) == "A"   # round-1 behaviour, must survive


def test_a_bogus_rule_raises_even_over_a_single_trivially_constant_value():
    """The rule-name check runs before the constant shortcut, so a bogus rule
    still raises even where the shortcut's own condition (`values` all equal)
    is trivially true for a single-member group — the common case for an
    unmeasured unit that never repeats."""
    with pytest.raises(ContractError) as e:
        _apply("bogus", ["A"])
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
    assert _apply("sum", [True, True]) is True
    assert _apply("sum", [False, False]) is False


def test_a_column_absent_from_the_collapse_map_falls_back_to_first():
    """`collapse` may be a per-column map; a column it does not name falls back
    to `first` rather than being averaged. `batch` differs across the two rows,
    so this is the case `collapse_measurements`'s blanket `"mean"` test above
    cannot reach: it exercises `_apply`'s `first` branch on values that are not
    already constant."""
    units = [
        Unit(key="p1", paths=(), attributes={"read_id": "r1", "depth": 10, "batch": "b1"}),
        Unit(key="p1", paths=(), attributes={"read_id": "r2", "depth": 20, "batch": "b2"}),
    ]
    collapsed, counts = collapse_measurements(
        units, by="read_id", collapse={"depth": "mean"}
    )
    assert counts == [2]
    assert collapsed[0].depth == 15.0
    assert collapsed[0].batch == "b1"
