## Task 33: the owned prose sweep, and the reader-facing half

**Files:** Modify `docs/reference.md`, `docs/feasibility-llm-growth-studies.md`, `CLAUDE.md`,
`docs/superpowers/spec-defects.md`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: the whole slice. `docs/feasibility-llm-growth-studies.md` § Executability on this build,
  whose subsections are each headed *"Measured on \<date\> against commit \<sha\>"*;
  `CLAUDE.md` § Misreadings' *unbuilt reader of a shipped surface* row, whose example is
  `BaseTemplate.required_env`.
- Produces: the newly-live roster-check family exercised end-to-end against a resolver-produced
  roster; a **new, dated** § Executability subsection carrying the three-of-nine count with its
  qualifications; two filings.

**The tests here are the ones tasks 25–29 could not write**, because `_check_units` skipped
resolution until task 26. **A check written where the roster is not proves nothing:** the checks
that survive under a resolver *today* are the declaration-against-declaration ones, so a test
mutating `cluster_by` proves nothing — it fires with the refusal in place. **The discriminating
fixtures are the ones that were lost**: a bad `key`, a bad attribute, `fold k=99`, a duplicate key.
And per the traps: **vary the resolver's yield, not the config shape.** Nineteen adversary configs
over one roster once made every refusal roster-incidental.

- [ ] **Step 1: Write the failing test.** In `tests/test_validate.py`, one parametrized test whose
      parameter is the **resolver body**, all against one config:

```python
_ROSTER_FAULTS = {
    "duplicate keys": ("yield Unit(key='a1')\n    yield Unit(key='a1')\n", "E-UNITS-KEY-DUPLICATE"),
    "no units at all": ("return\n    yield\n", "E-UNITS-EMPTY"),
    "swept parameter": ("yield Unit(key=cfg.parameters.analysis.method)\n", "E-RESOLVER-SWEPT-PARAM"),
    "undeclared attribute": ("yield Unit(key='a1')\n", "E-UNITS-ATTR-MISSING"),
}


@pytest.mark.parametrize("body,expected", list(_ROSTER_FAULTS.values()), ids=list(_ROSTER_FAULTS))
def test_the_roster_checks_are_real_against_a_resolver_produced_roster(
    installed, registries, write_config, body, expected
):
    """The kept/lost matrix, closed. Every one of these was UNREACHABLE under a
    resolver until this slice — the config's shape is identical across all four
    rows and only the resolver's YIELD varies, so no refusal here can be
    config-incidental. The control is the clean body: the same config with a
    well-formed resolver validates with no findings at all."""
```

      plus the clean-body control in the same test module, and a run-level test asserting
      `provenance.units_hash` is stable across two runs of one resolver and differs when the
      resolver yields a different order.

- [ ] **Step 2: Run and see it fail.** Write one row's fixture wrong on purpose first — a body that
      yields a well-formed roster under the "duplicate keys" id — and confirm the test fails.
      Then fix it. This is the can-fail proof for a parametrized test whose rows all assert a
      **failure**: a parametrization asserting a refusal for every arm proves nothing about the
      success path, which is why the clean-body control is not optional.

- [ ] **Step 3: Implement.** No `src/` change is expected. If a row fails for a reason other than
      the expected code, **that is a finding, not a test to adjust** — record it and stop.

      In `docs/feasibility-llm-growth-studies.md`, append a new subsection to § Executability on
      this build, headed *"Measured on \<date\> against commit \<sha\>"* with the real sha of the
      merge, carrying the honest form and its three qualifications verbatim in shape:

      > H7b Part B retires **one refusal that 9 of 9 configs hit** (`E-DATA-RESOLVER-UNSUPPORTED`),
      > and **three experiments — E1, E2, E5 — have no remaining core-side blocker.** That is the
      > first non-zero executable count this project has produced. It is conditional on the plugin
      > being written and installed (`plugin new` scaffolds it; a hand-written package works), and
      > on accepting that a declared apparatus probe is neither executed nor recorded. Six stay
      > blocked, on two causes neither of which is H7b's: `io.reuse_from` (unbuilt, **unowned**) and
      > `E-DATA-WEIGHT-CONTRAST` (H4b).

      **Append; never retro-edit the earlier dated subsections** — they record what was measured on
      their dates, and this file is exempt from the cross-document pass but not from the mechanical
      one. **Every cell must be re-measured, not carried**: run each of the nine `data`/`statistics`
      blocks and record the codes, with a can-fail control (`holdout.frac: 0` on E1, which the
      analysis itself prescribes).

      In `CLAUDE.md`, update § Misreadings' *unbuilt reader of a shipped surface* row if its example
      moved, and add the slice to the § Repository status paragraph naming the remaining order —
      **dated and pinned to a commit**, since it is a build fact.

      In `docs/superpowers/spec-defects.md`, file two things this slice makes reachable and does not
      own:

      - **`cli.py` writes `"apparatus": None` unconditionally**, and § The apparatus core can only
        observe defines `apparatus: null` as *"no probe declared"*. After this slice a run whose
        template **does** declare an installed probe records a false `apparatus: null`. **Owner:
        H7d.** File it; do not fix it — a reader for it is `Apparatus`, facts, the ledger and the
        change gate, all H7d's.
      - **`io.reuse_from` is unbuilt and unowned**, and is now the sole remaining core-side blocker
        for E3, E4 and E6. The existing entry already says so; **amend it with an owner request**
        rather than opening a second, since `CLAUDE.md` names *"a ledger line saying 'filed' is not
        a filing"* and a duplicate entry is the same failure in the other direction.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2097 + 6 = 2103 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/validate.py`, change `_check_units`'s
      `cfg=resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {}))` to
      `cfg=resolve_wide_cfg(doc, set())` — the mutation task 29 named and could not catch.
      The `"swept parameter"` row of
      `test_the_roster_checks_are_real_against_a_resolver_produced_roster` must **FAIL**: with no
      markers planted, `cfg.parameters.analysis.method` resolves to the base value and the resolver
      succeeds. **Checked against the test body:** that row's config declares
      `sweep.grid: {analysis.method: [...]}` and its resolver reads exactly that path, so the two
      branches genuinely differ — this is the seam task 29 named and this test instantiates.

      Second mutation: in `units.resolve_units`, delete the `E-UNITS-KEY-DUPLICATE` loop. The
      `"duplicate keys"` row must **FAIL**. **Checked:** that row's resolver yields the same key
      twice with no `measurements` declaration, so no collapse intervenes.

      **What no mutation here reaches:** the § Executability subsection and the two filings. Prose
      and a ledger are verified by the sweep in Step 6, not by a test.

- [ ] **Step 6: Sweep, then commit.** Prove each sweep can fail by running it first against a string
      known to be present, and **filter the file list, never the output**:

      - `grep -rn "E-DATA-RESOLVER-UNSUPPORTED\|(NOT BUILT)" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md CLAUDE.md src/`
        → the code must be absent; `(NOT BUILT)` must appear only where a genuinely unbuilt thing is
        marked. Can-fail control on the same list: `grep -rn "NOT BUILT" docs/reference.md` →
        non-empty.
      - `grep -rn "Not yet emitted" docs/reference.md` → **empty**; the three markers are struck by
        tasks 24, 28 and 29. Can-fail control: `grep -c "E-RESOLVER" docs/reference.md` → non-zero.
      - `grep -rn "against commit .deaed2b." docs/reference.md src/` → empty.
      - `grep -rn "cannot be dispatched\|will be honored in a later slice" src/ docs/reference.md`
        → empty.

      Mechanical pass on every `*.md` touched by the slice: links and anchors resolve, no duplicate
      anchors, table rows match their headers, no trailing whitespace or tab or invisible unicode,
      `×` not `x`, hyphen not en dash in anything that becomes an anchor — skipping fenced blocks.
      Cross-document pass on the four documents only.
      Commit: `docs: resolvers land — three of nine have no remaining core-side blocker`

---

## Self-review

Run before declaring the plan finished; findings fixed inline rather than appended.

**Spec coverage — a task per decision, and a task per scoping row.**

| Spec decision | Task | Scoping § 10 row | Task |
|---|---|---|---|
| 1 — `validate` imports a plugin to run a resolver | 22 | 21 `plugin new` | 21 |
| 2 — the credential-leak fix, both halves | 32 | 22 the decision | 22 |
| 3 — a non-`PublishableError` from a resolver | 32 | 23 read-only `io` | 23 |
| 4 — `check_registration` at `validate` | 24 | 24 name resolution and load | 24 |
| 5 — `hash_index`, table case and resolver case | 31 | 25 dispatch | 25 |
| 6 — `cfg` as a defaulted keyword | 25 | 26 retire the refusal | 26 |
| 7 — the payoff figure, with its qualifications | 33 | 27 attribute projection | 27 |
| | | 28 measurement field | 28 |
| | | 29 condition-independence | 29 |
| | | 30 `plugin_versions` + dated notes | 30 |
| | | 31 `hash_index` | 31 |
| | | 32 the credential leak | 32 |
| | | 33 prose sweep + re-dated count | 33 |

Thirteen tasks, thirteen rows, seven decisions, each landed. The four surfaces `spec-defects.md`
names Part B as owner of — `RESOLVERS`, `load_entry_point`, `check_registration`, `declared_names` —
get their first production caller in task 24, and task 30 amends the filing; the
`E-PLUGIN-COLLISION`/`E-PLUGIN-LOAD` hazard filed against Part B is decided and struck in task 24.

**Placeholder scan.** Every code step carries real code, with two deliberate exceptions, both in
tests and both marked with `...`: task 30's and task 32's `tests/test_cli.py` additions, whose
setup is *"build the config with the file's existing run helper"*. `tests/test_cli.py` is 9178
lines and its `command_run` helpers are what those tests must reuse rather than duplicate; naming a
helper this plan has not read would be the *helper that shadows an existing name* defect this repo
has already shipped. The assertions — which are the load-bearing half — are written out in full.

**Type consistency.** `resolve_units` keeps its three-element return, so no call site's unpacking
changes; the two new parameters are keyword-only with defaults. `Config | None` is quoted in
`units.py` (the import is real, not `TYPE_CHECKING`, so the quotes are stylistic consistency with
the file's existing `"UnitList | None"` forward references — drop them if `mypy` prefers).
`index_names` takes `UnitList | None` and a `tuple[str, ...]`, and returns `set[str]`, which is
exactly what `build_manifest`'s `index_names: set[str] | None` accepts. `versions_for` returns
`dict[str, str]`, matching `run.yaml`'s `plugin_versions` shape.
`ResolverIO.read_paths` is a `tuple[str, ...]` property over a private list, so a resolver cannot
edit the record of what it read.
