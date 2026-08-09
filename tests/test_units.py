# tests/test_units.py
from pathlib import Path

import pytest

from publishable import ContractError
from publishable.units import Unit, resolve_units, units_hash


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


def test_the_unit_list_is_exactly_four_operations(input_dir: Path):
    units = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert len(list(units)) == 3          # iterate, repeatably
    assert len(list(units)) == 3
    assert len(units) == 3                # len
    assert units[1].key == "p1"           # index
    for absent in ("append", "index", "count", "sort", "__contains__"):
        assert not hasattr(units, absent), f"{absent} would make this a list"


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
