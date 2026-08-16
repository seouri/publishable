## Task 11: `assign.<axis>.from` joins the constancy check

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`, `tests/test_validate.py`

**H3b predicted this task by name.** `CONSTANT_COLUMN_RULES` reaches flat string-valued keys of `data.units` only; its comment says adding a nested name **no-ops silently**, and names `assign.<axis>.from` as one of the next two that will want the rule.

Without it a `measurements` collapse **invents an arm membership** — H3a's defect a third time, and worse: a mis-collapsed arm changes *which condition a unit is measured in*, not how much it counts for.

- [ ] **Step 1: Write the failing test with its control**

```python
def test_an_arm_varying_within_a_units_measurement_rows_is_refused():
    """p1's replicate rows say control and treatment. Silently keeping one
    would put the unit in an arm no row declared."""
    ...
def test_an_arm_constant_within_a_units_rows_is_accepted():
    """The control: same shape, agreeing rows, must NOT raise."""
```

- [ ] **Step 2: Confirm the naive fix no-ops.** Add `"assign"` to the registry and show the test **still fails** — that is the constraint H3b documented, and seeing it is what stops the accessor being skipped.
- [ ] **Step 3: Implement the accessor** for nested keys, and register `assign.<axis>.from` for every declared axis.
- [ ] **Step 4–6:** Pass; mutate (drop the accessor → the test fails); registry row, dual-listed as its siblings are; commit.

---

## Controller additions — these are requirements, same force as the brief above

**The identifier is `E-DATA-ASSIGN-VARIES`**, matching `E-DATA-CLUSTER-VARIES` and
`E-DATA-WEIGHT-VARIES`. Read `CONSTANT_COLUMN_RULES`'s docstring in `src/publishable/units.py` before
writing the message: it argues **two codes rather than one** on the grounds that the sections say
different things about what breaks. Yours must say the third thing, and it is the worst of the three —
a mis-collapsed cluster decides which side of a split a unit lands on, a mis-collapsed weight mis-sizes
what one unit stands for, and a mis-collapsed **arm decides which condition the unit is measured in**,
so the order the file happens to be in would be silently deciding it. Say that, not a paraphrase.

**"Dual-listed as its siblings are" means both tables.** `E-DATA-CLUSTER-VARIES` has a row in
`reference.md` § Errors `validate` reports *and* one in § Errors core raises — `validate` resolves the
roster, so it reports the same fault the run-time collapse raises. Read both cluster rows and write both
of yours. § Validation's *Arm is constant within a unit* row already exists; do not duplicate it, but
check it still says what you implement.

**The registry's shape is the real design question, and the brief does not settle it.**
`CONSTANT_COLUMN_RULES` is keyed by *declaration* and maps to `(code, message)`; `resolve_units` builds
`constant` as `{declaration: column}` and `collapse_measurements` looks the declaration back up in the
registry. `assign` is the first declaration yielding **more than one column** — one per group axis — so
a single flat key cannot carry it. Two shapes are available:

- expand to one entry per axis (`assign.arm.from`, `assign.sex.from`) and teach the lookup to find the
  rule for a key not literally in the registry, or
- carry the code and message *in the `constant` mapping itself*, making the registry the source of the
  rule and `constant` the source of the expansion.

**Pick one and say in the docstring why the other was rejected.** Whichever you pick, the invariant the
existing comment states must survive in a form a reader can still check: `holdout.from` is the next
declaration that will want this rule, and the comment must tell that reader truthfully whether it now
works or still no-ops. **If your change makes `holdout.from` reachable, say so; if not, say why.** Do
not leave the comment describing the old shape — a stale comment here is what H3b deliberately left
behind, and this task exists because that comment was accurate.

**Step 2 is not optional, and it is the step most likely to be skipped.** The brief asks you to add
`"assign"` to the registry and *show the test still fails*. That demonstration is the whole reason this
is not a one-line change: the `isinstance(units_decl.get(declaration), str)` filter drops it, because
`data.units.assign` is a mapping. Record the actual failure output in your report. Skipping to the
accessor and asserting the naive fix "would have" no-opped is reasoning about a mutation, which the
global constraints forbid.

**The control must be able to fail.** A test asserting agreeing rows "do not raise" passes for a config
that never reached the collapse at all — because `measurements` was absent, because the axis had no
`from`, because the fixture's rows did not share a key. So the accepting control must **also assert
something positive about the resolved roster**: that the unit's arm attribute is the value both rows
agreed on, and that `technical_n` shows the rows were actually collapsed (`min`/`max`/`median` over a
count above 1). State in the docstring which number proves the collapse happened.

**The fixture must not double as a cluster fixture.** Per the global constraints, no arm fixture may
share a boundary with a cluster fixture — if the varying column is also the `cluster_by` column, an
`E-DATA-CLUSTER-VARIES` would be indistinguishable from yours. Give the fixture no `cluster_by`, or one
on a column that genuinely does not vary, and say which in a comment.

**Mutation:** dropping the accessor must fail the refusal test and **not** the control (a control that
also dies to that mutation was never testing the collapse). Also: a varying arm **on a column that is
not the cluster column** must report `E-DATA-ASSIGN-VARIES` and not `E-DATA-CLUSTER-VARIES`. Note the
converse — one column named as *both* the arm attribute and `cluster_by` **should** draw both codes,
which is exactly what `CONSTANT_COLUMN_RULES`' docstring means by keying on the declaration so a config
"is checked once for each rather than silently dropping one under a precedence rule nothing in the
documents states". **Do not build mutual exclusion between the two.**

**Never write a phrase locating a table row by position** ("the row above", "immediately below",
"further up"). Tasks 9 and 10 did it four times between them and were wrong twice — once in a row the
diff did not even touch, falsified by an insertion that moved it. Name what a sibling row *does*. When
you insert a row, check every row your insertion **moved**, not only the ones you edited.

**What tasks 9 and 10 actually landed** — read the code, not this summary, but so you are not surprised:
`_check_assign` now takes `(doc, units, roster, c)` and emits `E-DATA-ALLOCATION-NO-ARMS`,
`E-DATA-ASSIGN-MISSING`, `E-DATA-ASSIGN-METHOD`, `E-DATA-ASSIGN-DRAWN` (refuses `random`/`blocked` by
value), `E-DATA-ASSIGN-UNKNOWN` (the `from` name half, defaulting to the axis name, and absorbing a
non-`str` `from` because no `E-CONFIG-TYPE` backstop can exist for a dynamic axis key), and
`E-DATA-ASSIGN-LEVELS` (set equality in both directions). **`units.arms_of(roster, column, levels)` is
the single authority for arm membership** and raises `ContractError` that `_check_assign` catches. Your
constancy check runs *before* any of that — at collapse time inside `resolve_units`, which `validate`
calls to get the roster in the first place. **Do not touch `E-DATA-ASSIGN-UNSUPPORTED`**; task 17
retires it, and in this build a config exercising your check reports it too, correctly.
