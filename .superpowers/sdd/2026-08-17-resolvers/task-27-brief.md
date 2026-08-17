## Task 27: attribute projection, and `E-UNITS-ATTR-MISSING` generalized past a table

**Files:** Modify `src/publishable/units.py`, `docs/reference.md`, `tests/test_units.py`.

**Interfaces:**
- Consumes: `units._from_table`'s attribute loop — `RESERVED_FIELDS` first, then
  `name not in columns` → `ContractError` · `E-UNITS-ATTR-MISSING`, then
  `Unit(key=row[key_col], paths=(), attributes={a: row[a] for a in attrs})` — read in
  `src/publishable/units.py`; `_from_glob`'s same-ordered loop and its `from: {glob: ...}`-worded
  message; `units._from_resolver` from task 25.
- Produces: `_from_resolver` projecting each yielded unit's attributes onto `data.units.attributes`,
  with `E-UNITS-ATTR-RESERVED` and a resolver-worded `E-UNITS-ATTR-MISSING`; § Errors'
  `E-UNITS-ATTR-MISSING` row widened past *"the source table has no column for"*.

**Projection, not pass-through, and it is what makes the rest of core indifferent to the source.**
§ Where units come from: *"What it returns is a unit table with the columns a CSV would have
supplied … `attributes`, the mapping `data.units.attributes` draws from … Everything downstream is
then indifferent to which form `from` took: `stratify_by`, `assign.from`, `cluster_by`, and
`null_test.shuffle` all name attributes."* `_from_table` builds `Unit.attributes` from the declared
list and nothing else; a resolver's units must end up the same shape, or `clusters_of`,
`arms_of`, `usable_weight` and the fold's `stratify_by` subscript would see a name `validate` never
approved. Two consequences the plan states rather than leaves to be discovered: an attribute the
resolver yields and the config does not declare is **dropped**, exactly as an undeclared CSV column
is; and `measurements.by` is dropped by the same projection, which is correct, because
`collapse_measurements` groups on `key` and reads `by` only to exclude it from the merged names —
the pre-projection column set task 25 returns is what task 28 checks `by` against.

**Ordering: reserved before missing**, matching `_from_table` and `_from_glob`, so one declaration
draws one code whichever source it sits under. Report the **first** such name and stop, the
convention both existing branches use.

**A declared name is missing when no yielded unit carries it** — the union, not the intersection.
That is a table header's question ("does this column exist") rather than a per-row one, and it
matches `collapse_measurements`'s reading that a name only some rows carry is no disagreement.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_units.py`:

```python
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


def test_a_reserved_attribute_name_is_refused_before_a_missing_one(
    installed, registries, tmp_path
):
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
```

- [ ] **Step 2: Run and see it fail.** The projection test fails on the yielded `plate`/`scratch`
      surviving; the missing-attribute test fails with "DID NOT RAISE".

- [ ] **Step 3: Implement.** In `src/publishable/units.py`, `_from_resolver`, after the yield loop
      and before the empty check:

```python
    attrs = list(decl.get("attributes") or [])
    for attribute in attrs:
        if attribute in RESERVED_FIELDS:
            raise ContractError(
                f"`data.units.attributes` names {attribute!r}, which is a field of `Unit` "
                f"itself; {', '.join(RESERVED_FIELDS)} cannot also be attributes",
                code="E-UNITS-ATTR-RESERVED",
            )
        if attribute not in yielded:
            raise ContractError(
                f"`data.units.attributes` names {attribute!r}, which resolver `{name}` yields "
                "no unit carrying — a resolver has no columns beyond the attributes it yields, "
                "so the field a table would simply have carried has to be yielded",
                code="E-UNITS-ATTR-MISSING",
            )
    # Projected onto the declared list exactly as `_from_table` projects a CSV row,
    # which is what makes everything downstream indifferent to which form `from`
    # took: `cluster_by`, `weight_by`, `assign.<axis>.from`, `holdout.from` and a
    # `fold`'s `stratify_by` all read `Unit.attributes` and were approved by
    # `validate` against `data.units.attributes` alone. An attribute the resolver
    # yields and the config does not declare is dropped, the way an undeclared
    # column is.
    units = [
        Unit(
            key=unit.key,
            paths=unit.paths,
            attributes={a: unit.attributes[a] for a in attrs if a in unit.attributes},
        )
        for unit in units
    ]
```

      **The reserved/missing loop runs over the declaration, before the projection**, so the two
      cannot disagree about which names survive. Move the empty-roster check *above* this block, so
      a resolver yielding nothing reports `E-UNITS-EMPTY` rather than an attribute fault about a
      roster that does not exist.

      In `docs/reference.md`, § Errors `validate` reports' `E-UNITS-ATTR-MISSING` row: widen its
      opening from *"names a value the source table has no column for, or names any value at all
      under a `{glob: ...}` source"* to name the third source — *"or a value no unit a
      [resolver](#where-units-come-from) yielded carries"* — keeping the rest of the row, including
      its `measurements.by` clause, untouched.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2078 + 4 = 2082 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/units.py`, change the projection comprehension's
      `attributes={a: unit.attributes[a] for a in attrs if a in unit.attributes}` to
      `attributes=unit.attributes`.
      `tests/test_units.py::test_a_resolver_roster_is_projected_onto_the_declared_attributes` must
      **FAIL** — the first unit comes back carrying `plate` and `scratch`. **Checked against the
      test body:** the assertion is on the exact `dict(u.attributes)` of both units, and the fixture
      yields an attribute (`scratch`) that the declaration omits, so pass-through and projection
      genuinely differ. A fixture yielding only declared attributes would have made this blind.

      Second mutation: change `if attribute not in yielded:` to
      `if all(attribute not in u.attributes for u in units):`, i.e. the intersection reading
      inverted to a stricter one — no: that is the same predicate. **The mutation that discriminates
      union from intersection** is `if any(attribute not in u.attributes for u in units):`.
      `test_a_name_only_some_units_yield_is_not_missing` must **FAIL** with an
      `E-UNITS-ATTR-MISSING` raise for `scratch`, which one of the two units carries and the other
      does not. **Checked against the test body:** the fixture's two units differ in exactly that
      attribute, which is the seam this mutation exists to instantiate — naming the seam is not
      testing it, and this fixture is what separates the readings.

      **What no mutation here reaches:** the ordering of `_from_resolver`'s three refusals relative
      to `resolve_units`' later `E-UNITS-KEY-DUPLICATE` loop. No fixture yields both a duplicate key
      and a missing attribute. Named, not covered.

- [ ] **Step 6: Commit.** `units: project a resolver roster onto the declared attributes`

---

