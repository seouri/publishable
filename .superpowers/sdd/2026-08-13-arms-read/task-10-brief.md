## Task 10: `assign.<axis>.from` resolves, and defaults to the axis name

**Files:** Modify `src/publishable/validate.py`; Test `tests/test_validate.py`

§ The one config file: `from` is `by_attribute` only, and **defaults to the axis name**. So a `groups` axis named `arm` with no `from` reads the `arm` attribute.

- [ ] **Step 1: Failing tests** — `from` naming an undeclared attribute is refused; **the default is exercised** (no `from`, axis named `arm`, attribute `arm`); and the levels the attribute holds match the axis's declared levels.
- [ ] **Step 2–6:** Implement, mutate (drop the default → the no-`from` test fails), registry rows, commit.

---

## Controller additions — these are requirements, same force as the brief above

**Two identifiers, following the sibling convention exactly.** `weight_by` and `cluster_by` each use
`E-DATA-<X>-UNKNOWN` for *the name does not resolve*; the value half gets its own. So:

| Fault | Code | The § Validation row |
|---|---|---|
| `from` — declared, or defaulted from the axis name — is not in `data.units.attributes` | `E-DATA-ASSIGN-UNKNOWN` | **has no row yet; write one**, phrased as *Weight attribute exists* is |
| The attribute's values, over the resolved roster, are not the axis's declared levels | `E-DATA-ASSIGN-LEVELS` | *Attribute assignment resolves* — already there, unimplemented |

**Read `_check_weight_by` in `src/publishable/validate.py` before writing either.** It is the model,
and its docstring already argues every question you are about to ask: why `data.units.attributes` is
the reference set rather than the roster's realized names (so the name half runs with **no roster at
all**), why a non-`str` declaration returns silently (`check_envelope` owns `E-CONFIG-TYPE`, and
reporting it again would describe `3` as "empty"), why an absent `attributes` is an empty list rather
than a skip, and why skipping the *value* half without a roster is not the silent skip H1 removed.
Every one of those applies here unchanged. Where your answer differs, say why in the docstring — a
silent divergence between two checks of the same shape is the defect the H3a review found twice.

**`_check_assign` currently takes `(doc, units, c)` and has no roster.** The levels half needs one:
change the signature to match `_check_weight_by`'s — `roster: UnitList | None` — and update the call
site, which sits beside `_check_weight_by(units_decl, roster, c)` and already holds the roster.

**The default is the whole point of this task, and it is the easiest thing here to test vacuously.**
A test that omits `from`, names the axis `arm`, declares attribute `arm`, and asserts *no finding*
passes just as well if the default were never implemented and the check simply never ran. **It must be
paired with a case where the default is what makes the difference**: same config, axis named `arm`,
attribute list **not** containing `arm` → `E-DATA-ASSIGN-UNKNOWN` naming `'arm'` in its message. That
pair discriminates; neither half alone does. Assert the message names the attribute it resolved,
because that string is the only observable evidence of *which* name the default produced.

**Mutation, and it must be the real one.** Dropping the default (`from` read with no fallback to the
axis name) must fail the paired test above. If it fails nothing, the default is unreachable or the
tests do not exercise it — rewrite them, do not reason about it. Mutate the two halves separately as
well: each code's test must die to its own branch and no other.

**The levels half is set equality, and this is a ruling, not your choice.** `reference.md`
§ Allocation settles it twice and the controller has checked both: the `by_attribute` example annotates
`from` as *"a unit attribute whose values are **exactly** the declared levels"*, and `allocation:
between` opens *"each unit belongs to **exactly one** arm"*. So:

- an attribute value naming no declared level → **refused**; that unit would belong to no arm, and
  there is no fourth part of `n` for it
- a declared level no unit holds → **refused**; that arm's condition would resolve zero units

One code, `E-DATA-ASSIGN-LEVELS`, for both directions, with a message that says which one occurred and
names the offending values. Do **not** implement subset-tolerance and do not leave the question open in
a docstring: three later tasks depend on the answer, which is why it is settled here. § Validation's
*Attribute assignment resolves* row does not currently say this — its example is disjoint, a fault
under either reading, so the row reads settled and is not. **Amend that row to state set equality in
both directions**, in the same commit.

### Produces: the single authority for the arm partition

Tasks 12 and 13 must not re-derive arm membership from the roster — that is this project's second named
defect class, a defect living in a combination no single task owns, and the answer here is the one
already used four times: `units.usable_weight`, `units.is_measurement_numeric`, `units.clusters_of`,
`units.fold_basis` — each read by **both** `validate` and its consumer, so a config that validates
cannot crash downstream.

**You are the first reader, so you write the accessor.** Put it in `src/publishable/units.py` beside
`clusters_of`, whose shape and docstring are your model. Something of the form

```python
def arms_of(roster: UnitList, column: str, levels: Sequence[str]) -> dict[str, list[Unit]]
```

returning the partition keyed by level — and, since set equality is the rule, a caller may rely on
every unit appearing in exactly one bucket and every declared level being a non-empty key. `validate`
calls it and turns a violation into `E-DATA-ASSIGN-LEVELS`; task 12 calls it for the subset view; task
13 counts it. Match `clusters_of`'s conventions for the no-roster case and for a unit missing the
attribute entirely, and state in the docstring that both `validate` and the runner read it — that
shared reading is the property which makes the invariant hold.

**Do not touch `E-DATA-ASSIGN-UNSUPPORTED`** — task 17 retires it. In this build a config exercising
your checks reports it too, and that is correct.

**Registry:** § Errors `validate` reports is sorted; `E-DATA-ASSIGN-DRAWN` < `E-DATA-ASSIGN-LEVELS` <
`E-DATA-ASSIGN-METHOD` < `E-DATA-ASSIGN-MISSING` < `E-DATA-ASSIGN-UNKNOWN`. One pre-existing violation
in that table (`E-SWEEP-ABLATE-BASELINE-GROUP` after `E-SWEEP-ABLATE-CROSSED`) belongs to task 20 —
leave it. **Never write a phrase locating a row relative to a position** ("the two rows above", "further
up"): task 9 did it twice and was wrong both times, once in the fix for the first. Name what a sibling
row *does*, not where it sits.
