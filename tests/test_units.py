# tests/test_units.py
from pathlib import Path

import pytest

from publishable import ContractError
from publishable.units import (
    Unit,
    UnitList,
    apply_rule,
    cluster_count,
    clusters_of,
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
    units, _, _ = resolve_units({"from": "index.csv", "key": "patient_id", "attributes": ["label"]},
                             input_dir)
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
    assert len(list(units)) == 3          # iterate, repeatably
    assert len(list(units)) == 3
    assert len(units) == 3                # len
    assert units[1].key == "p1"           # index
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
    assert collapsed[0].depth == 15.0        # mean of 10 and 20
    assert collapsed[0].site == "A"          # non-numeric, constant: carried
    assert "read_id" not in collapsed[0].attributes   # the measurement axis is consumed


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
    assert apply_rule("sum", [1, 2]) == 3          # already covered above; kept for contrast
    assert apply_rule("mean", [5, 5]) == 5         # mean over constant numeric: still a mean
    assert apply_rule("mean", ["A", "A"]) == "A"   # round-1 behaviour, must survive


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
    collapsed, counts = collapse_measurements(
        units, by="read_id", collapse={"depth": "mean"}
    )
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
    roster = UnitList(
        [Unit(key=f"u{i}", paths=(), attributes={"site": "S1"}) for i in range(4)]
    )
    assert cluster_count(roster, "site") == 1
    with pytest.raises(ContractError):
        cluster_count(UnitList([Unit(key="u0", paths=(), attributes={})]), "site")


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
    # The control: the same declarations over rows that agree resolve cleanly.
    _write_reads(
        input_dir,
        "patient_id,read_id,site,w\np1,r1,S1,2\np1,r2,S1,2\np2,r3,S3,3\n",
    )
    roster, technical_n, _ = resolve_units(decl, input_dir)
    assert clusters_of(roster, "site") == {"p1": "S1", "p2": "S3"}
    assert technical_n == {"min": 1, "max": 2, "median": 1.5}


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
