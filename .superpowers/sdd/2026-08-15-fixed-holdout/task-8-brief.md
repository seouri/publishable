## Task 8: The shared cells refusal — one check site, two codes, and H3c-3 named as its owner

**Files:** Modify `src/publishable/validate.py`, `docs/experimental-designs.md`, `docs/reference.md`, `docs/superpowers/spec-defects.md`. Modify (append) `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate_config`'s `doc` and `units_decl`.
- Produces:

```python
def _check_evaluation_split_cells(doc: dict[str, Any], units: dict[str, Any], c: Collector) -> None:
```

  called from `validate_config` immediately after `_check_holdout`. Reports `E-DATA-HOLDOUT-CELLS` and/or `E-REPL-FOLD-CELLS`.

**This is H3c-3's own 3-task refusal and H3d's, merged into one.** The two faults are one fault — *a roster-wide evaluation split beside a cell structure* — both knowable from the declarations alone, both live at `78bb794`. Probed at 15 units split 12/3 by arm: `fold_basis` answers **15** over the whole roster, so `k: 5` is permitted and arm `b` gets **two empty folds**; a roster-wide `frac: 0.2` gives arm `b` **zero test units**. `groups` + `between` + `fold k=5` **validates clean today**.

**Refuse, not disclose.** The disclosure route is `allocation.json` recording a truthful `train`/`test` membership that a reader would have to cross against the arms list by hand to see the imbalance — the silently-wrong class. The repo's precedent is to refuse the *combination* while honouring both *declarations*: `E-DATA-WEIGHT-CONTRAST`, `E-DATA-CLUSTER-CONTRAST`, `E-DATA-ALLOCATION-CONTRAST`, `E-DATA-ASSIGN-BLOCKED-CLUSTER`.

**One check site is not negotiable.** Two codes for the two split kinds is defensible; a second *site* is how the two answers come to disagree.

**Cost against the outside evidence: zero, re-verified.** All nine configs in `docs/feasibility-llm-growth-studies.md` declare one roster, `allocation: within`, no `sweep.groups`, and `seed` or `batch` repeats. And no section of `experimental-designs.md` declares `allocation: between` **and** a `fold` repeat: it declares `between` in three sections and a `fold` in two, with no overlap.

**Two false present-tense claims this task marks honestly rather than adding a third to.** `experimental-designs.md`'s "folds and holdouts are drawn *within* each cell" is false for `fold` at `78bb794` and would become false for `holdout` the moment this slice lands. `reference.md` § Cross-validation's "Under `allocation: between`, folds are drawn within each cell" is the same sentence one file over. (§ A fixed holdout split's own fourth interaction was already rewritten in task 2 — do not rewrite it again; **read it first** and make these two agree with what it now says.)

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
_CELL_ROSTER = "patient_id,arm\n" + "".join(
    f"p{i},{'b' if i >= 12 else 'a'}\n" for i in range(15)
)
_ARM_GROUP_AXIS = [{"by": "arm", "levels": ["a", "b"]}]


def _cells(units_extra: dict, *, fold: bool) -> dict:
    """A `between` design with an `arm` group axis, plus whichever evaluation
    split the caller asked for. 15 units, 12 in arm `a` and 3 in arm `b` — the
    exact shape both defects were reproduced at."""
    units = {
        "from": "index.csv", "key": "patient_id", "attributes": ["arm"],
        "allocation": "between", "assign": {"arm": {"method": "by_attribute"}},
        **units_extra,
    }
    out: dict = {"data.units": units, "sweep": {"groups": _ARM_GROUP_AXIS}}
    if fold:
        out["replication"] = {
            "repeats": [{"kind": "fold", "k": 5}], "order": "as_declared"
        }
    return out


def test_a_fold_beside_a_cell_structure_is_refused(write_config, tmp_path):
    """A LIVE defect at `78bb794`: this config validates clean, and `k: 5` is
    permitted because `fold_basis` answers 15 over the whole roster while arm
    `b` holds 3 — so arm `b` gets two folds holding none of its units.

    Refused rather than disclosed: `sweep.yaml`'s partitions would record the
    membership truthfully and no reader crosses it against the arms list by
    hand."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    found = codes(write_config(_cells({}, fold=True)))
    assert "E-REPL-FOLD-CELLS" in found


def test_a_holdout_beside_a_cell_structure_is_refused(write_config, tmp_path):
    """The same fault, the same check site, the other split kind: a roster-wide
    `frac: 0.2` over 15 units gives arm `b` zero test units."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    found = codes(
        write_config(_cells({"holdout": {"method": "random", "frac": 0.2}}, fold=False))
    )
    assert "E-DATA-HOLDOUT-CELLS" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_both_split_kinds_beside_a_cell_structure_report_both_codes(
    write_config, tmp_path
):
    """One check site, two codes — asserted together because a site that
    returned after the first finding would pass both tests above and still
    hide half the fault. `E-DATA-HOLDOUT-FOLD` rides along, which is correct:
    the two declarations are also mutually exclusive with each other."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    found = codes(
        write_config(_cells({"holdout": {"method": "random", "frac": 0.2}}, fold=True))
    )
    assert "E-DATA-HOLDOUT-CELLS" in found
    assert "E-REPL-FOLD-CELLS" in found


def test_allocation_between_alone_triggers_the_refusal_without_a_group_axis(
    write_config, tmp_path
):
    """`allocation: between` and a non-empty `sweep.groups` are two spellings
    of the same cell structure, and EITHER is enough. Without this row a check
    reading only `sweep.groups` passes every test above.

    The message is asserted, not just the code: `where` is a two-branch
    ternary and BOTH branches emit the same code at the same path, so a
    code-only assertion here and in its sibling below passes identically if
    the ternary is collapsed to either branch."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    overrides = _cells({"holdout": {"method": "random", "frac": 0.2}}, fold=False)
    overrides["sweep"] = {}
    path = write_config(overrides)
    assert "E-DATA-HOLDOUT-CELLS" in codes(path)
    assert "`data.units.allocation: between`" in (
        messages_by_code(path)["E-DATA-HOLDOUT-CELLS"]
    )


def test_a_group_axis_alone_triggers_the_refusal_without_between(
    write_config, tmp_path
):
    """The other half of the same pair: without this row a check reading only
    `allocation` passes every test above. The message is asserted for the
    reason its sibling above states."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    overrides = _cells({"holdout": {"method": "random", "frac": 0.2}}, fold=False)
    overrides["data.units"]["allocation"] = "within"
    path = write_config(overrides)
    assert "E-DATA-HOLDOUT-CELLS" in codes(path)
    assert "a non-empty `sweep.groups`" in (
        messages_by_code(path)["E-DATA-HOLDOUT-CELLS"]
    )


def test_an_evaluation_split_without_a_cell_structure_is_not_refused(
    write_config, tmp_path
):
    """The control. `allocation: within`, no `sweep.groups` — the shape all
    nine feasibility configs declare, and the shape this refusal must leave
    alone.

    **`E-DATA-HOLDOUT-UNSUPPORTED` below is NOT positive attribution.** It is
    emitted by `_check_unimplemented`, a different function, so it would appear
    unchanged if this check never ran — task 7's review found three controls
    resting on exactly that mistake. It is asserted here only so the row
    survives task 18's retirement as a one-line deletion. A control over a
    check that correctly reports nothing cannot prove itself; what proves this
    one is the pair of trigger tests above, which differ from it only in the
    cell structure."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    found = codes(
        write_config(
            _holdout({"method": "random", "frac": 0.2}, attributes=["arm"])
        )
    )
    assert "E-DATA-HOLDOUT-CELLS" not in found
    assert "E-REPL-FOLD-CELLS" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k "cell_structure or triggers_the_refusal or without_a_cell" -x`. Every test asserting a new code fails; the control passes with its companion. **Before implementing, confirm the live defect by hand**: run the fold config through `validate_config` and check it reports no error at all today — that is the defect this task closes, and seeing it is what stops the refusal being written against a fault that was never there.

- [ ] **Step 3: Implement** —

  (a) In `src/publishable/validate.py`, add after `_check_holdout`:

```python
def _check_evaluation_split_cells(
    doc: dict[str, Any], units: dict[str, Any], c: Collector
) -> None:
    """A roster-wide evaluation split beside a cell structure — refused, for
    both split kinds, from one site.

    **The two faults are one fault**, which is why they share a site: a
    `data.units.holdout` and a `{kind: fold}` level each partition the WHOLE
    roster once, and `data.units.allocation: between` or a non-empty
    `sweep.groups` divides that same roster into cells. A partition drawn
    across the cells rather than within them gives them unequal test sizes and,
    once the split is fine enough, a cell holding none of its own units at all
    — a cell-level metric computed from nothing.

    **Two codes, one site.** `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS`
    send a reader to the declaration they actually wrote; a single code would
    name one of the two and be wrong for the other. A second check *site* is
    what this deliberately does not have — that is how two answers to one
    question come to disagree.

    **Refused rather than disclosed.** The disclosure route would be
    `allocation.json` and `sweep.yaml` recording a truthful membership whose
    imbalance is visible only to a reader who crosses it against the arms list
    by hand — the silently-wrong class. The repo's own precedent is to refuse
    the COMBINATION while honouring both DECLARATIONS, and to route it:
    `E-DATA-WEIGHT-CONTRAST`, `E-DATA-CLUSTER-CONTRAST`,
    `E-DATA-ALLOCATION-CONTRAST`, `E-DATA-ASSIGN-BLOCKED-CLUSTER`.

    **The `fold` half closes a defect that is live at this commit**, not a
    hypothetical: `replication._fold_k` bounds `k` against `units.fold_basis`
    over the WHOLE roster, so 15 units split 12/3 by arm permit `k: 5` and
    leave the 3-unit arm with two empty folds. Nothing else scheduled closes
    it sooner, which is why it ships here rather than with the slice that owns
    cells.

    **The route is a design that draws within each cell**, which this build
    does not have. `docs/superpowers/spec-defects.md` carries the entry and
    names **H3c-3** as the owner of this refusal's retirement.

    Knowable from the declarations alone — no roster, no resolution — so this
    takes neither.
    """
    allocation = units.get("allocation")
    groups = (doc.get("sweep") or {}).get("groups")
    cells = allocation == "between" or bool(isinstance(groups, list) and groups)
    if not cells:
        return
    where = (
        "`data.units.allocation: between`"
        if allocation == "between"
        else "a non-empty `sweep.groups`"
    )
    reason = (
        f"is declared beside {where}, which divides the roster into cells. One "
        "roster-wide split across those cells gives them unequal test sizes and, "
        "once it is fine enough, a cell holding none of its own units — a "
        "cell-level metric computed from nothing. Drawing the split within each "
        "cell is the design that lifts this, and it is not built: declare one or "
        "the other, or run each arm as its own run and join them in a `study`"
    )
    if units.get("holdout"):
        c.error("E-DATA-HOLDOUT-CELLS", "data.units.holdout", reason)
    repeats = (doc.get("replication") or {}).get("repeats")
    if isinstance(repeats, list) and any(
        isinstance(level, dict) and level.get("kind") == "fold" for level in repeats
    ):
        c.error("E-REPL-FOLD-CELLS", "replication.repeats", f"declares a `fold` level, which {reason}")
```

  and wire it in `validate_config`, immediately after the `_check_holdout` call:

```python
    _check_holdout(doc, units_decl, roster, usable_cluster, c)
    # One site for both split kinds, deliberately: see this function's own
    # docstring for why a second site is the thing being avoided rather than a
    # cost being paid.
    _check_evaluation_split_cells(doc, units_decl, c)
```

  (b) In `docs/experimental-designs.md`, replace the clause "**folds and holdouts are drawn *within* each cell**" in the paragraph beginning "Every cell is a condition" with:

```markdown
Every cell is a condition, so cells get their own `values` and their own labels — but **not their own evaluation split**: core refuses a `fold` repeat or a [`data.units.holdout`](reference.md#a-fixed-holdout-split) declared beside a cell structure (`E-REPL-FOLD-CELLS`, `E-DATA-HOLDOUT-CELLS`) rather than drawing one roster-wide partition across the cells, which would give them unequal test sizes and, once the split is fine enough, a cell holding none of its own units. Drawing within each cell is the design that lifts the refusal, and it is not built. `limits.min_units_per_cell` is checked per cell, which is where a 2×2 over a fixed roster starts to bite.
```

  (c) In `docs/reference.md` § Cross-validation, replace the paragraph beginning "**Under `allocation: between`, folds are drawn within each cell**" with:

```markdown
**Under `allocation: between`, a `fold` repeat is refused**, not drawn — `E-REPL-FOLD-CELLS`, the same refusal and the same reason [a holdout](#a-fixed-holdout-split) earns under `E-DATA-HOLDOUT-CELLS`. One roster-wide partition would give the cells unequal test sizes and, once `k` approaches the smallest cell's size, a fold holding none of that cell's units at all, which is a cell-level metric computed from nothing. Drawing within each cell is the design that lifts both refusals: `k` would then be bounded by the *smallest* cell's unit count — or its cluster count, when `cluster_by` is declared — and it is not built. Without a cell structure nothing changes: the boundaries are derived once from the design digest, and every condition sees the same ones, which is exactly what paired contrasts need.
```

  (d) In `docs/superpowers/spec-defects.md`, append:

```markdown
## OPEN — an evaluation split cannot be drawn within a cell

`data.units.holdout` and a `{kind: fold}` repeat both partition the whole roster once, and
`data.units.allocation: between` / a non-empty `sweep.groups` divides that same roster into
cells. `reference.md` § A fixed holdout split and `experimental-designs.md` both prescribe
drawing the split **within** each cell. **No build draws one.**

H3d refuses the combination instead, at one site under two codes — `E-DATA-HOLDOUT-CELLS`
and `E-REPL-FOLD-CELLS` — because the `fold` half was a live defect: `replication._fold_k`
bounds `k` against `units.fold_basis` over the whole roster, so 15 units split 12/3 by arm
permitted `k: 5` and left the 3-unit arm with two empty folds, and the config validated
clean. Refusing rather than disclosing follows `E-DATA-ASSIGN-BLOCKED-CLUSTER`'s precedent:
a truthful record of an imbalance no reader crosses by hand is the silently-wrong class.

**Owner of the retirement: H3c-3**, the slice that builds folds and holdouts inside cells.
Re-owner this entry if that slice's scope changes, rather than leaving it pointing at a
closed one.

**Found by:** H3d, Task 8. **Severity:** Was Major for `fold` while open — a validated
config produced empty folds per arm — and is now closed as a refusal rather than as a
capability.
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then the **documents sweep, by claim not by file**: `grep -rn "within each cell" docs/reference.md docs/experimental-designs.md docs/design-principles.md README.md` — every remaining hit must be a statement this build actually honours, or must name the refusal. Prove the sweep can fail by running it against `each cell`, which returns more. Then the mechanical pass on both edited documents (trailing whitespace, tabs, anchors resolve, `×` not `x`, table rows match headers) and the cross-document pass: check § Mistakes core prevents in `experimental-designs.md` still lists nothing these edits make merely-discouraged rather than structurally impossible.

- [ ] **Step 5: Mutate** — four.

  (a) In `src/publishable/validate.py`, change `cells = allocation == "between" or bool(...)` to `cells = allocation == "between"`. `test_a_group_axis_alone_triggers_the_refusal_without_between` must **FAIL**. Revert in place; re-run.

  (b) Change it to `cells = bool(isinstance(groups, list) and groups)`. `test_allocation_between_alone_triggers_the_refusal_without_a_group_axis` must **FAIL**. Revert in place; re-run.

  (c) Add `return` immediately after the `E-DATA-HOLDOUT-CELLS` `c.error(...)` call. `test_both_split_kinds_beside_a_cell_structure_report_both_codes` must **FAIL** on `E-REPL-FOLD-CELLS`, and `test_a_fold_beside_a_cell_structure_is_refused` must still pass — which is the point: an early `return` is invisible to every single-declaration test, and only the both-declared fixture separates the two readings. Revert in place; re-run.

  (d) Collapse `where`'s ternary to its second branch — delete the
  `"`data.units.allocation: between`" if allocation == "between" else` half so
  `where` is always ``"a non-empty `sweep.groups`"``.
  `test_allocation_between_alone_triggers_the_refusal_without_a_group_axis`
  must **FAIL** on its message assertion, and every code-only assertion in this
  task must still pass — which is the point: both branches emit the same code
  at the same path, so only the message separates them. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: refuse a roster-wide evaluation split beside a cell structure`.

---

