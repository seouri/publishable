## Task 25: dispatch in `resolve_units`

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`,
`src/publishable/cli.py`, `src/publishable/sweep.py`, `docs/reference.md`, `tests/test_units.py`,
`tests/test_cli.py`.

**Interfaces:**
- Consumes: `units.resolve_units(units_decl: dict, input_dir: Path) -> tuple[UnitList, dict[str, float] | None, frozenset[str]]`
  and its two branches `_from_table`/`_from_glob`, read in `src/publishable/units.py`;
  `artifacts.ResolverIO(input_dir)` from task 23; `units._resolver_for(name)` from task 24;
  `runner.resolve_wide_cfg(base: dict, swept_paths: set[str]) -> Config` and
  `cli._wide_swept_paths(sweep_block: dict) -> set[str]`, read in `src/publishable/runner.py` and
  `src/publishable/cli.py`.
- Produces: `resolve_units(units_decl, input_dir, *, cfg: Config | None = None, resolver_io: ResolverIO | None = None)`
  — same three-element return; `units._from_resolver(decl, name, input_dir, cfg, resolver_io) -> tuple[list[Unit], frozenset[str]]`;
  `sweep.wide_swept_paths` (moved from `cli._wide_swept_paths`); `E-RESOLVER-YIELD` and
  `E-RUN-RESOLVER-UNCONFIGURED` emitted; both `resolve_units` production call sites thread `cfg`.

**Two defaulted keywords, not two required parameters — decision 6, measured.**
`grep -c 'resolve_units(' tests/test_units.py` → 56 and `tests/test_cli.py` → 4, plus the two
production sites in `validate.py` and `cli.py`. A required parameter is a 60-site edit with no
behavioural content. The price is named rather than discovered: **a resolver source reached with
`cfg=None` must refuse rather than crash**, under `E-RUN-RESOLVER-UNCONFIGURED`, which joins
§ Errors core raises' existing *core's plan disagreeing with the state core resolved beside it* row.
`resolver_io` defaults the same way and for a narrower reason: only `cli.command_run` needs the
object back afterwards (task 31 reads `read_paths` off it), and `validate` builds no manifest.

**Yield order is preserved and is not cosmetic.** § Where units come from: *"The resolved list keeps
the order it was resolved in — table row order, resolver yield order, or lexicographic path order
for a `glob`"*, and `assign.method: blocked` reads that order as data while
`provenance.units_hash` covers the list in it. So `_from_resolver` appends in iteration order and
does nothing else to it.

**`validate` → `runner` is acyclic, so nobody needs to re-derive it.** Read both import blocks:
`runner.py` imports `artifacts`, `coercion`, `config`, `errors`, `replication`, `scope`, `secrets`,
`stats`, `sweep`, `units` — never `validate`. The only module in `src/publishable/` importing
`validate` is `cli.py`. `units` → `plugins` → `artifacts` is acyclic too: `artifacts` imports
`units` only under `TYPE_CHECKING`.

**`_wide_swept_paths` moves to `sweep.py` and is pinned by name.** `tests/test_cli.py` imports it
from `publishable.cli` and asserts its exact returned set; update that import **in the same
commit**. It moves because `validate` now needs it and `validate` importing `cli` would be the
cycle `cli` → `validate` already occupies.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_units.py`:

```python
def _install_resolver(installed, tmp_path, module: str, body: str):
    """One installed distribution whose `publishable.resolvers` entry point points
    at a module this writes. Returns nothing: every caller pops `module` from
    `sys.modules` in its own `finally`, because a real import leaks and Part A's
    fixtures deliberately could not import at all."""
    site = installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": f"{module}:resolve"}})
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
    roster, _technical_n, columns = resolve_units({"from": "index.csv", "key": "patient_id"}, tmp_path)
    assert [u.key for u in roster] == ["p1", "p2"]
    assert columns == frozenset({"patient_id"})
```

      and in `tests/test_cli.py`, update the import of `_wide_swept_paths` to
      `from publishable.sweep import wide_swept_paths` and rename its three uses in
      `test_a_group_path_gets_no_swept_away_marker`.

- [ ] **Step 2: Run and see it fail.** `TypeError: resolve_units() got an unexpected keyword
      argument 'cfg'`; the `test_cli.py` import fails with `ImportError`.

- [ ] **Step 3: Implement.** In `src/publishable/cli.py`, delete `_wide_swept_paths` and move it
      verbatim — docstring included — into `src/publishable/sweep.py` as `wide_swept_paths`,
      dropping the leading underscore because it now has readers in two modules. Import it in
      `cli.py` from `publishable.sweep` and update the one call site.

      In `src/publishable/units.py`, add `from publishable.artifacts import ResolverIO` and
      `from publishable.config import Config` to the imports, then:

```python
def _from_resolver(
    decl: dict[str, Any],
    name: str,
    input_dir: Path,
    cfg: "Config | None",
    resolver_io: ResolverIO | None,
) -> tuple[list[Unit], frozenset[str]]:
    """The units a plugin's resolver yields, and the attribute names it yielded.

    The columns come back beside the roster for the reason `_from_table`'s do: they
    are the only honest reference set for `data.units.measurements.by`, and a
    resolver has no columns beyond the attributes it yields, so the field a CSV
    would simply have carried is checked against what actually arrived. The union
    over yielded units rather than the intersection, matching a table header's
    "this column exists" rather than "every row filled it in" — the same reading
    `collapse_measurements` takes when it treats a name only some rows carry as no
    disagreement.

    Yield order is preserved and nothing re-sorts it: `reference.md` § Where units
    come from makes resolver yield order the resolved order, `assign.method:
    blocked` reads that order as data, and `provenance.units_hash` covers the list
    in it.
    """
    if cfg is None:
        raise ContractError(
            f"`data.units.from.resolver` names `{name}`, and resolution was reached with no "
            "config to hand it — a resolver sees the same `cfg` a `scope: \"run\"` step does, "
            "so core's resolved state disagrees with itself here rather than the config being "
            "wrong",
            code="E-RUN-RESOLVER-UNCONFIGURED",
        )
    resolve = _resolver_for(name)
    io = resolver_io if resolver_io is not None else ResolverIO(input_dir)
    units: list[Unit] = []
    yielded: set[str] = set()
    for item in resolve(io, cfg):
        if not isinstance(item, Unit):
            raise ContractError(
                f"resolver `{name}` yielded a {type(item).__name__} — a resolver yields "
                "`Unit`s, which is what makes its roster a unit table with the columns a "
                "CSV would have supplied",
                code="E-RESOLVER-YIELD",
            )
        units.append(item)
        yielded.update(item.attributes)
    if not units:
        raise ContractError(
            f"resolver `{name}` yielded no units; a run measuring zero units has nothing "
            "to report",
            code="E-UNITS-EMPTY",
        )
    return units, frozenset(yielded)
```

      and rewrite `resolve_units`'s signature and source branch:

```python
def resolve_units(
    units_decl: dict[str, Any],
    input_dir: Path,
    *,
    cfg: "Config | None" = None,
    resolver_io: ResolverIO | None = None,
) -> tuple[UnitList, dict[str, float] | None, frozenset[str]]:
```

```python
    source = units_decl.get("from")
    if isinstance(source, str):
        units, columns = _from_table(units_decl, input_dir, source)
    elif isinstance(source, dict) and "glob" in source:
        units, columns = _from_glob(units_decl, str(source["glob"]), input_dir)
    elif isinstance(source, dict) and "resolver" in source:
        units, columns = _from_resolver(
            units_decl, str(source["resolver"]), input_dir, cfg, resolver_io
        )
    else:
        raise ContractError(
            f"`data.units.from` is {source!r}; expected a table name, {{glob: ...}}, or "
            "{{resolver: ...}}",
            code="E-UNITS-SOURCE-MISSING",
        )
```

      **`glob` is still tested before `resolver`**, deliberately: a `from` declaring both is refused
      by `validate._check_from_source_exclusivity` as `E-UNITS-SOURCE-AMBIGUOUS`, and keeping this
      order means the two modules cannot come to read one declaration two ways in the window before
      that check runs. Extend `resolve_units`'s docstring to say the columns are a table's header,
      a glob's empty set, or a resolver's yielded attribute names.

      Thread `cfg` at both production call sites. In `src/publishable/validate.py`, add
      `from publishable.runner import resolve_wide_cfg` and `wide_swept_paths` to the `sweep`
      import, then in `_check_units` replace the `resolve_units(units_decl, path)` call with:

```python
        # The same `cfg` a `scope: "run"` step sees, so a resolver reading a swept
        # parameter meets a `SweptAway` marker rather than a value no condition
        # used. Built here rather than threaded from `validate_config` because
        # every other check in this module re-derives from `doc` locally.
        roster, technical_n, columns = resolve_units(
            units_decl,
            path,
            cfg=resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {})),
        )
```

      In `src/publishable/cli.py`, `command_run`'s phase-5 roster call becomes:

```python
    resolver_io = ResolverIO(input_dir)
    roster, technical_n, _columns = (
        resolve_units(
            units_decl,
            input_dir,
            cfg=resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {})),
            resolver_io=resolver_io,
        )
        if units_decl
        else (None, None, frozenset())
    )
```

      In `docs/reference.md` § Errors `validate` reports, `E-UNITS-SOURCE-MISSING`'s row says `from`
      *"is neither a table name nor a `{glob: ...}` mapping"* — a third form is legal now, so widen
      that clause to name all three. **This row appears in neither the scoping's § 6 nor its § 13;
      it is found by reading the row, not by grepping for `NOT BUILT`.**

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2074 + 4 = 2078 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/units.py`, change `_from_resolver`'s
      `units.append(item)` loop to `units = sorted(units, key=lambda u: u.key)` before the return.
      `tests/test_units.py::test_a_resolver_source_yields_the_roster_in_yield_order` must **FAIL**.
      **Checked against the test body:** the fixture's two rows are `B9,h3` then `A1,c2`, so sorted
      order (`A1:c2`, `B9:h3`) differs from yield order — a fixture whose rows happened to be sorted
      would have made this mutation blind, which is why the CSV is written that way.

      Second mutation: in `resolve_units`, move the `elif isinstance(source, dict) and "resolver"
      in source` branch **above** the `glob` branch. **This one cannot fail, and it is recorded
      rather than prescribed:** no fixture declares both keys, because
      `_check_from_source_exclusivity` refuses that shape and no test in `tests/test_units.py`
      builds it. The mutation that *can* discriminate the ordering is a direct call to
      `resolve_units` with `{"from": {"glob": "*.csv", "resolver": "plate_wells"}}` — and the reason
      not to add one is that it would pin resolution behaviour for a declaration `validate` refuses,
      making a future removal of that refusal look like a regression. **What no mutation reaches**:
      the branch order between `glob` and `resolver`. Named, not covered.

      Third mutation, for the `cfg` guard: change `if cfg is None:` to `if False:`.
      `test_a_resolver_source_reached_with_no_cfg_refuses_rather_than_crashing` must **FAIL** — with
      `cfg=None` reaching `resolve(io, cfg)`, the fixture resolver reads `io.read_input` fine and
      never touches `cfg`, so the failure is "DID NOT RAISE" rather than a crash. That is exactly
      the fail-open the guard exists for, and it is why the guard is a raise rather than a comment.

- [ ] **Step 6: Commit.** `units: dispatch a resolver source, yield order preserved`

---

