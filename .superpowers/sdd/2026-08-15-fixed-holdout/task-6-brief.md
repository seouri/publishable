## Task 6: `_check_holdout`, declaration half B — `stratify_by` existence, and `holdout` × `fold`

**Files:** Modify `src/publishable/validate.py`. Modify (append) `tests/test_validate.py`.

**Interfaces:**
- Consumes: `_check_holdout(doc, units, roster, cluster_by, c)` from task 5; `units.stratum_names(stratify_by: Any) -> tuple[str, ...]`, already imported in `validate.py`.
- Produces: two more findings inside the same function — `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` and `E-DATA-HOLDOUT-FOLD` — and the docstring's enumeration grown from five to seven.

**Why these two are one task and not two halves of task 5.** Different failure reason: the first discharges the `holdout` half of § Validation's shared *Stratification attribute exists* row, which `validate.py`'s `_check_fold_stratify_by` docstring explicitly says "belongs to the slice that builds that block"; the second reads a **different block** (`replication`) and is the only check in `_check_holdout` that does.

**Read through `units.stratum_names`, not with a hand-rolled `isinstance` chain.** It is the single authority the draw balances on, and it reads a bare `stratify_by: label` as one name exactly as `[label]` is. Two independent readings of one declaration pinned in agreement by nothing is the validate-clean-then-disagree shape this repo refuses; `_check_resample` reads it the same way and its own comment says why.

**One finding per offending name.** A `stratify_by: [site, sex]` naming two undeclared attributes earns two findings, not one naming only the first — `E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s stated rule, and the reason the fixture below declares two.

**Where the exclusion is sited, and why not in `resolve_repeats`.** In `_check_holdout`, reading `replication.repeats` from the doc. `replication.REPL_DECLARATION_CODES` stays exactly as it is: a fold level is a perfectly well-formed *repeat*, and what is refused is the **combination** with a declaration in another block, which `resolve_repeats` cannot see. Siting it here is also what lets task 18 retire the wholesale refusal without touching `replication.py`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
_HOLDOUT_STRATA_ROSTER = "patient_id,label,site\n" + "".join(
    f"p{i},{'x' if i % 2 else 'y'},s{i % 3}\n" for i in range(12)
)


def test_a_holdout_stratum_naming_no_declared_attribute_is_refused(write_config, tmp_path):
    """§ Validation *Stratification attribute exists*, the `holdout` half —
    `_check_fold_stratify_by`'s docstring names this as belonging to the slice
    that builds the block, and this is that slice.

    TWO undeclared names, because the rule is one finding per offending name
    and a one-element fixture cannot tell that from one finding per
    declaration."""
    (tmp_path / "input" / "index.csv").write_text(_HOLDOUT_STRATA_ROSTER)
    c = Collector()
    validate_config(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": ["sex", "cohort"]},
                attributes=["label", "site"],
            )
        ),
        c,
    )
    unknown = [f for f in c.findings if f.code == "E-DATA-HOLDOUT-STRATIFY-UNKNOWN"]
    assert len(unknown) == 2, [f.message for f in unknown]
    # Both names, not the same name twice: a loop reporting `strata[0]` each
    # time would give a count of 2 and be wrong about which attributes failed.
    joined = " ".join(f.message for f in unknown)
    assert "'sex'" in joined and "'cohort'" in joined, joined
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in {f.code for f in c.findings}


def test_a_bare_string_holdout_stratum_is_read_as_one_name(write_config, tmp_path):
    """`units.stratum_names` reads `stratify_by: label` as one name exactly as
    `[label]` is. Read as a sequence of characters instead, an undeclared bare
    string would report one finding per LETTER — five for `sexes` — so the
    count is what distinguishes the two readings, and the fixture's name is
    five letters long for exactly that reason."""
    (tmp_path / "input" / "index.csv").write_text(_HOLDOUT_STRATA_ROSTER)
    c = Collector()
    validate_config(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": "sexes"},
                attributes=["label", "site"],
            )
        ),
        c,
    )
    assert len([f for f in c.findings if f.code == "E-DATA-HOLDOUT-STRATIFY-UNKNOWN"]) == 1


@pytest.mark.parametrize("declared", ["", [], 7, [3]])
def test_a_holdout_stratum_that_names_no_attribute_at_all_is_refused(
    write_config, tmp_path, declared
):
    """A non-string, an empty string, and an empty list each name no attribute.
    `data.units.holdout.stratify_by` IS an `envelope.LEAF_TYPES` leaf as of task
    3, so `7` also earns `E-CONFIG-TYPE` — absorbed here as well because a bare
    type finding does not say what a stratum has to be."""
    (tmp_path / "input" / "index.csv").write_text(_HOLDOUT_STRATA_ROSTER)
    found = codes(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": declared},
                attributes=["label", "site"],
            )
        )
    )
    assert "E-DATA-HOLDOUT-STRATIFY-UNKNOWN" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_holdout_stratum_naming_the_measurement_axis_is_refused(write_config, tmp_path):
    """The measurement axis is consumed when a unit's rows collapse, so no
    resolved unit carries it — the same fault and the same code as an
    undeclared name, for `_check_fold_stratify_by`'s stated reason one
    declaration over."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,read_id,label\n" + "".join(f"p{i // 2},r{i},x\n" for i in range(12))
    )
    found = codes(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": ["read_id"]},
                attributes=["read_id", "label"],
                measurements={"by": "read_id", "collapse": "mean"},
            )
        )
    )
    assert "E-DATA-HOLDOUT-STRATIFY-UNKNOWN" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_declared_holdout_stratum_is_accepted(write_config, tmp_path):
    """The positive companion, produced by the code under test: the same
    declaration over a name `data.units.attributes` DOES declare reports
    nothing, so the check reads the declaration rather than refusing every
    `stratify_by`."""
    (tmp_path / "input" / "index.csv").write_text(_HOLDOUT_STRATA_ROSTER)
    found = codes(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": ["label", "site"]},
                attributes=["label", "site"],
            )
        )
    )
    assert "E-DATA-HOLDOUT-STRATIFY-UNKNOWN" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_holdout_beside_a_fold_repeat_is_refused(write_config):
    """§ A fixed holdout split: two answers to one question — how the data is
    divided for evaluation — leaving "which units is this metric over?" with
    none. Probed at `78bb794`: this config reports ONLY
    `E-DATA-HOLDOUT-UNSUPPORTED` today, with no exclusion check at all."""
    overrides = _holdout({"method": "random", "frac": 0.2})
    overrides["replication"] = {
        "repeats": [{"kind": "fold", "k": 5}], "order": "as_declared"
    }
    found = codes(write_config(overrides))
    assert "E-DATA-HOLDOUT-FOLD" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_holdout_beside_a_seed_repeat_is_not_refused(write_config):
    """The control, and it must report something: a `seed` repeat divides
    nothing, so the exclusion is about `fold` specifically rather than about
    `replication` being declared at all. Without the second assertion this
    passes identically if the check is dead."""
    found = codes(write_config(_holdout({"method": "random", "frac": 0.2})))
    assert "E-DATA-HOLDOUT-FOLD" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k "holdout_stratum or holdout_beside" -x`. Every test asserting a new code fails; the two controls pass already, which is why each carries the wholesale-refusal companion. `Collector` and `validate_config` are already imported at the top of `tests/test_validate.py`.

- [ ] **Step 3: Implement** — extend `_check_holdout` in `src/publishable/validate.py`. First grow the docstring's enumeration to seven, inserting after the `E-DATA-HOLDOUT-SEED` bullet:

```python
    - `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` — a `stratify_by` name that is not a
      declared unit attribute, names `data.units.measurements.by`, or is not
      the name of an attribute at all.
    - `E-DATA-HOLDOUT-FOLD` — a `{kind: fold}` repeat declared beside this
      block. The only check here that reads a block other than `data.units`.
```

  Then append to the function body, after the seed pin:

```python
    # `stratify_by`, through `units.stratum_names` — the single authority the
    # draw balances on, which reads a bare `stratify_by: label` as one name
    # exactly as `[label]` is. Re-deriving that reading here with an
    # `isinstance` chain would pin two independent readings of one declaration
    # in agreement by nothing, which is what `_check_resample` reads it this
    # way to avoid.
    #
    # **`data.units.attributes` is the reference set**, not the source's
    # columns, the side of the line `_check_cluster_by`, `_check_weight_by` and
    # `_check_fold_stratify_by` all read: a stratum is read per unit when the
    # split is drawn, so it has to survive resolution as an attribute rather
    # than merely be a column of the source. Checked from the declaration
    # alone, so it reports whether or not a roster resolved.
    #
    # One finding per offending name, `E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s rule:
    # a declaration naming two undeclared attributes earns two, rather than one
    # naming only the first.
    attrs = units.get("attributes") or []
    declared_names = (
        sorted({a for a in attrs if isinstance(a, str)}) if isinstance(attrs, list) else []
    )
    measurements = units.get("measurements")
    measurement_axis = measurements.get("by") if isinstance(measurements, dict) else None
    raw_strata = holdout.get("stratify_by")
    strata = stratum_names(raw_strata)
    if raw_strata is not None and not strata:
        # An empty string or an empty list: present, and naming nothing. Left
        # silent it would be a declaration that changes no behaviour, which is
        # exactly what a truthy read of it hides.
        c.error(
            "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
            "data.units.holdout.stratify_by",
            "is empty, which names no attribute to balance the split on and changes "
            "no behavior. Name the attribute, or remove the key",
        )
    for name in strata:
        if not isinstance(name, str) or not name:
            c.error(
                "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
                "data.units.holdout.stratify_by",
                f"names {name!r}, which is not the name of a unit attribute — a split "
                "is balanced on attributes named as strings",
            )
            continue
        if name not in declared_names:
            c.error(
                "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
                "data.units.holdout.stratify_by",
                f"names {name!r}, which is not a unit attribute — a stratum is read "
                "per unit when the split is drawn, so it has to be one. "
                f"`data.units.attributes` declares "
                f"{', '.join(declared_names) or 'none'}",
            )
            continue
        if isinstance(measurement_axis, str) and measurement_axis == name:
            c.error(
                "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
                "data.units.holdout.stratify_by",
                f"names {name!r}, which `data.units.measurements.by` also names — the "
                "measurement axis is consumed when a unit's rows collapse and is not "
                "an attribute of the resolved unit, so there is nothing left to "
                "balance the split on. Stratify on an attribute that survives the "
                "collapse",
            )

    # The one check here that reads a block other than `data.units`. Sited in
    # `validate` rather than in `resolve_repeats` because a `fold` level is a
    # perfectly well-formed *repeat*: what is refused is the COMBINATION with a
    # declaration in another block, which `resolve_repeats` never sees. That is
    # also why `replication.REPL_DECLARATION_CODES` is unchanged by this.
    repeats = (doc.get("replication") or {}).get("repeats")
    if isinstance(repeats, list) and any(
        isinstance(level, dict) and level.get("kind") == "fold" for level in repeats
    ):
        c.error(
            "E-DATA-HOLDOUT-FOLD",
            "data.units.holdout",
            "is declared beside a `{kind: fold}` repeat level, and the two are "
            "mutually exclusive — each divides the units for evaluation, so together "
            "they leave `which units is this metric over?` with no single answer. To "
            "hold out a final test set AND cross-validate for model selection, declare "
            "the holdout and do the inner search inside the step over `io.units.train`",
        )
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k "holdout_stratum or holdout_beside"`, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — two.

  (a) In `src/publishable/validate.py`, change `strata = stratum_names(raw_strata)` to `strata = (raw_strata,) if isinstance(raw_strata, str) else tuple(raw_strata or ())` — a re-derivation that agrees with `stratum_names` on every shape this fixture set covers except none, so **check the two branches can differ before trusting it**: they cannot, and this mutation is therefore *rejected*. Use this one instead: change it to `strata = tuple(raw_strata) if isinstance(raw_strata, list) else ()`. Run `uv run pytest tests/test_validate.py -k bare_string_holdout_stratum`. It must **FAIL** — a bare `"sexes"` now yields zero names, so no finding is reported. Revert in place; re-run.

  (b) Change the fold exclusion's `level.get("kind") == "fold"` to `level.get("kind") == "batch"`. `test_a_holdout_beside_a_fold_repeat_is_refused` must **FAIL**. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: refuse an unknown holdout stratum and a holdout beside a fold`.

---

