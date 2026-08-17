## Task 29: condition-independence — `E-RESOLVER-SWEPT-PARAM`

**Files:** Modify `src/publishable/units.py`, `docs/reference.md`, `tests/test_units.py`.

**Interfaces:**
- Consumes: `config.SweptAway(path)` and `config.Node.__getattr__`, which raises `ContractError` ·
  `E-STEP-SWEPT-PARAM` on resolving one — read in `src/publishable/config.py`;
  `runner.resolve_wide_cfg(base, swept_paths) -> Config`, which plants a marker at every swept path
  under `parameters`, walking with `setdefault`; `sweep.wide_swept_paths` (moved in task 25), whose
  union is `_swept_paths` ∪ `ablated_paths` ∪ `baseline` keys, minus `selector_paths`.
- Produces: `_from_resolver` translating an `E-STEP-SWEPT-PARAM` raised inside the resolver into
  `ContractError` · `E-RESOLVER-SWEPT-PARAM`; § Errors' `Not yet emitted:` clause struck.

**The mechanism is shared and the fault is not.** Part A's `E-RESOLVER-SWEPT-PARAM` row settles the
reuse-or-mint question and this task honours it rather than re-making it: *"that identifier is a
step's, reached at run time from `"run"` or `"summary"` scope, and a reader holding it is sent to a
section describing a different fault at a different time. Sharing the mechanism — a sentinel
substituted for a swept path, raising on the read — is not sharing the fault, the same way a coded
`ContractError` from a local template's top level is reported as `E-TEMPLATE-LOAD` rather than under
the code it carried."*

**Translate only `E-STEP-SWEPT-PARAM`, and let every other coded raise through.** A resolver that
raises `ContractError` · `E-UNITS-SOURCE-MISSING` from `io.read_input` must keep that code — the
scoping's probe A shows it arriving at `validate` under its own identifier, redacted. Only the
sentinel read is re-coded.

**No document change beyond the marker.** § Where units come from already states the rule and its
reason: *"a resolver that reads a parameter the sweep varies is rejected by `validate`. The unit
table is one table for the whole run, so conditions that resolved different units couldn't be paired
and `n` would mean something different in each. Parameters the sweep leaves alone are fair game."*

- [ ] **Step 1: Write the failing test.** Append to `tests/test_units.py`:

```python
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
            resolve_units(
                {"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path, cfg=cfg
            )
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


def test_a_resolvers_own_coded_refusal_keeps_its_own_identifier(
    installed, registries, tmp_path
):
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
```

- [ ] **Step 2: Run and see it fail.** The first test fails on `excinfo.value.code ==
      "E-RESOLVER-SWEPT-PARAM"` — it is `E-STEP-SWEPT-PARAM` today.

- [ ] **Step 3: Implement.** In `src/publishable/units.py`, wrap `_from_resolver`'s iteration:

```python
    try:
        for item in resolve(io, cfg):
            ...
    except ContractError as exc:
        if exc.code != "E-STEP-SWEPT-PARAM":
            raise
        # The mechanism is shared and the fault is not. `config.Node` raises the
        # step's identifier because that is what it raises for every reader of a
        # `SweptAway` marker; a reader holding it here would be sent to § Step
        # scope, which describes a different fault at a different time. Re-coded
        # rather than re-raised, on `discover_local`'s precedent for a coded
        # `ContractError` out of user code.
        raise ContractError(
            f"resolver `{name}` reads {exc}. The unit table is one table for the whole run, "
            "so conditions that resolved different units could not be paired and `n` would "
            "mean something different in each. Read a parameter the sweep leaves alone",
            code="E-RESOLVER-SWEPT-PARAM",
        ) from exc
```

      **The message interpolates `exc`, which already names the swept path**
      (`config.Node.__getattr__` builds *"`parameters.analysis.method` is varied by `sweep`…"`*), so
      the path is not re-derived here — a second derivation is how the two would come to disagree
      about which path was read.

      In `docs/reference.md`, strike `E-RESOLVER-SWEPT-PARAM`'s **`Not yet emitted:`** clause whole.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2085 + 3 = 2088 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/units.py`, change `if exc.code != "E-STEP-SWEPT-PARAM":
      raise` to `if False: raise` — i.e. re-code every `ContractError` the resolver raises.
      `tests/test_units.py::test_a_resolvers_own_coded_refusal_keeps_its_own_identifier` must
      **FAIL**: its resolver raises `E-UNITS-EMPTY`, which would come back as
      `E-RESOLVER-SWEPT-PARAM`. **Checked against the test body:** the fixture raises a code that is
      neither of the two involved, so the two branches genuinely differ — a fixture raising
      `E-STEP-SWEPT-PARAM` itself could not have told the readings apart.

      Second mutation, for the honouring: in `src/publishable/validate.py`, change `_check_units`'s
      `cfg=resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {}))` to
      `cfg=resolve_wide_cfg(doc, set())` — a config with no markers planted at all. **This does not
      fail any test in this task**, because all three call `resolve_units` directly with a cfg they
      built themselves. It is task 33's `validate`-level test that catches it, and task 33's brief
      says so. Recorded here rather than left silent: **a mutation's silence is evidence about the
      tests**, and the test that would catch this one is scheduled rather than missing.

- [ ] **Step 6: Commit.** `units: a resolver reading a swept parameter is refused under its own code`

---

