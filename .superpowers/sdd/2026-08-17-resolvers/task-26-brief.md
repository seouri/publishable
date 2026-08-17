## Task 26: retire `E-DATA-RESOLVER-UNSUPPORTED` and the `_check_units` skip, in one change

**Files:** Modify `src/publishable/validate.py`, `src/publishable/materialize.py`,
`docs/reference.md`, `tests/test_validate.py`, `tests/test_materialize.py`.

**Interfaces:**
- Consumes: `validate._check_unimplemented(doc, c)`'s resolver branch — **the one emit site**, found
  by reading that function in full and then confirming with `grep -rn "RESOLVER" src/`, in that
  order; `validate._check_units`'s early return for a `{resolver: ...}` source and the docstring
  bullet justifying it; `materialize.py`'s literal `"| {resolver: <name>} (NOT BUILT)"`.
- Produces: the code gone from `src/`, the skip gone, four document sites moved.

**Read the whole function, then grep.** `E-DATA-RESOLVER-UNSUPPORTED` appears at **four** sites in
`validate.py` and **only one of them emits**: the emit in `_check_unimplemented`, the early return in
`_check_units` (not an emit — the blast radius), `_check_units`'s docstring bullet justifying the
skip, and `_check_unimplemented`'s closing comments. Enumerating by grep alone is the substitution
that shipped a credential leak two slices ago.

**Delete the message, do not edit it.** Part A already rewrote this message once, because the old
wording claimed the registry was unimplemented and Part A implemented it. The current wording
(*"a resolver cannot be dispatched in this build; resolvers will be honored in a later slice"*) is
true today and false the moment this task lands. Deleting is what Part A's decision 7 bought by
requiring every test to assert the refusal **alongside** its own finding.

**`statistics.null_test` stays.** `_check_unimplemented`'s loop keeps its other member — retiring
one must not retire the loop — and § The one config file's *"**Two** declarations above are not yet
built"* count goes to **one**, not to zero.

- [ ] **Step 1: Write the failing test.** In `tests/test_validate.py`:

```python
def test_a_resolver_source_is_no_longer_refused_wholesale(installed, registries, write_config, tmp_path):
    """The retirement, asserted against behaviour rather than against a grep. The
    control is the second half: an UNREGISTERED name still earns
    `E-RESOLVER-UNKNOWN`, so this is not a check that stopped reporting anything."""
    from publishable.units import RESOLVER_GROUP

    site = installed("dist-one", "1.0", {RESOLVER_GROUP: {"plate_wells": "retire_r26:resolve"}})
    (site / "retire_r26.py").write_text(
        "from publishable import Unit, register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n"
        "    yield Unit(key='p1')\n"
    )
    importlib.invalidate_caches()
    units = {"from": {"resolver": "plate_wells"}, "key": "well"}
    try:
        found = codes(write_config({"data.units": units}))
        unknown = codes(write_config({"data.units": {**units, "from": {"resolver": "nope"}}}))
    finally:
        sys.modules.pop("retire_r26", None)

    assert found == set()
    assert "E-RESOLVER-UNKNOWN" in unknown


def test_the_unsupported_family_is_down_to_null_test(write_config):
    """`E-DATA-RESOLVER-UNSUPPORTED` is gone from every surface, and the family it
    left is not empty — a sweep asserting only an absence would pass identically if
    the whole family had been deleted."""
    found = messages_by_code(
        write_config({"statistics": {"null_test": {"method": "permutation", "n": 5000}}})
    )
    unsupported = {code for code in found if code.endswith("-UNSUPPORTED")}
    assert unsupported == {"E-STATS-NULLTEST-UNSUPPORTED"}
```

      and **delete one line from each** of the tests that were written to make this a deletion —
      find them by name, not by line number:

      - `tests/test_validate.py::test_a_resolver_source_is_refused_until_plugins_exist` — delete the
        whole test; it is the refusal itself.
      - `tests/test_validate.py::test_every_unsupported_message_defers_rather_than_scolds` — delete
        the resolver row from its `@pytest.mark.parametrize` list and the sentence in its docstring
        naming `E-DATA-RESOLVER-UNSUPPORTED` as what remains of the family.
      - `tests/test_validate.py::test_a_resolver_source_does_not_also_raise_source_missing` — delete
        the `assert "E-DATA-RESOLVER-UNSUPPORTED" in found` line. The remaining assertion
        (`E-UNITS-SOURCE-MISSING` not in `found`) is still a real claim: `resolve_units`' `else`
        branch must not describe a resolver as a missing file.
      - `tests/test_validate.py::test_two_installed_distributions_claiming_one_resolver_name_are_reported`
        — delete the `assert "E-DATA-RESOLVER-UNSUPPORTED" in both` line and the comment above it.
      - the `E-UNITS-SOURCE-AMBIGUOUS` test — delete its two
        `assert "E-DATA-RESOLVER-UNSUPPORTED" in ...` lines.
      - `tests/test_materialize.py::test_the_from_enum_s_not_built_marking_is_honoured_by_core` —
        this whole test is about a marker that no longer exists; delete it, and delete the
        `(NOT BUILT)` sentence from its docstring's sibling explanation if that sentence stands
        alone elsewhere in the file.

      Confirm the list is complete before starting, by sweeping the **file list**:
      `grep -rn "E-DATA-RESOLVER-UNSUPPORTED" src/ tests/ docs/reference.md docs/design-principles.md docs/experimental-designs.md README.md CLAUDE.md`
      → after the task, empty except `docs/superpowers/**` and
      `docs/feasibility-llm-growth-studies.md`, which are the development record and a dated
      measurement respectively and are **never** retro-edited. Can-fail control on the same list:
      `grep -rn "E-STATS-NULLTEST-UNSUPPORTED" src/ docs/reference.md` → non-empty.

- [ ] **Step 2: Run and see it fail.** The new tests fail on `found == set()` (the wholesale refusal
      is still reported) and on the `unsupported == {...}` equality.

- [ ] **Step 3: Implement.** In `src/publishable/validate.py`:

      - delete `_check_unimplemented`'s `if isinstance(source, dict) and "resolver" in source:`
        block **and** the two lines above it that fetch `units`/`source`, if nothing else in the
        function reads them — read the function to check rather than assuming;
      - delete `_check_units`'s early return for a resolver source, its two-line comment, and the
        `data.units.from.resolver` bullet in its docstring — the bullet **justifies the skip by the
        refusal**, so the two die together;
      - rewrite `_check_unimplemented`'s closing comments: delete the sentence *"One `data.units`
        sub-field remains read by nothing: a `resolver` source"* and its parenthetical, and the
        clause *"It resolves a unit roster, but one `data.units` sub-field — a `resolver` source —
        is still read by nothing"* in the docstring. **Prefer deleting to rewriting**: there is now
        no `data.units` sub-field read by nothing, so the honest edit is that the sentence goes.

      In `src/publishable/materialize.py`, change the two-part literal to a single line reading
      `'    from: index.csv                # index.csv | {glob: "*.dcm"} | {resolver: <name>}'`.

      In `docs/reference.md`:

      - § The one config file's fenced `from:` line — strike `(NOT BUILT)`;
      - § The one config file's prose — *"**Two** declarations above are not yet built"* becomes
        **one**, naming `statistics.null_test` alone, and the resolver clause is deleted from the
        sentence listing them. Append the same shape the `resample`/`holdout` retirements already
        use: what now checks it for real (`units._from_resolver` dispatches it, `_check_units`
        resolves it, `provenance.plugin_versions` records the plugin), so the declaration changes
        the record;
      - § Where units come from's second `from` enum comment — strike `(NOT BUILT)` there too, so
        the generated config and the document do not disagree about build state.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2078 + 2 − 2 (deleted tests) = 2078
      passed**, 1 skipped, 2 xfailed. Restate the arithmetic in the commit message from the actual
      run, not from this line.

- [ ] **Step 5: Mutate.** In `src/publishable/validate.py`, restore `_check_units`'s early return
      for a resolver source (`return None, None, frozenset()` under the `resolver` test).
      `tests/test_validate.py::test_a_resolver_source_is_no_longer_refused_wholesale` must **FAIL**
      on `"E-RESOLVER-UNKNOWN" in unknown` — with the skip restored, the misspelled name never
      reaches `_resolver_for`. **Checked against the test body:** the first assertion
      (`found == set()`) would still *pass* under the restored skip, since skipping produces no
      finding either; it is the second, positive half that discriminates. That asymmetry is the
      reason the control is in the test at all.

      Second mutation: in `materialize.py`, put `(NOT BUILT)` back on the `from:` line.
      **This one now fails nothing**, because the test that pinned it was deleted in Step 1 — and
      that is correct rather than a gap: the marker was a claim about build state, and the build
      state it claimed is gone. The test that *would* catch a marker resurfacing is
      `tests/test_materialize.py`'s `_MARKED_LATER_SLICE` sweep, which reads the generated config
      for `(x: later slice)` markers; it does not match the `(NOT BUILT)` spelling, which is exactly
      why the deleted test existed. Record this in the commit message rather than adding a test for
      a string nobody writes any more.

- [ ] **Step 6: Commit.** `validate: retire E-DATA-RESOLVER-UNSUPPORTED and the roster skip together`

---

