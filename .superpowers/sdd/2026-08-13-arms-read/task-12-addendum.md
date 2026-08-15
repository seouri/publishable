# Task 12 — controller additions

These are requirements, with the same force as the brief file they accompany.

## The narrowing predicate falls out of the data — do not write a scope allowlist

Verified in `src/publishable/scope.py`'s plan builder: `run` and `summary` executions are appended with
`condition_index = None`; only `condition` and `repeat` executions carry an index. So the rule is

> **narrow the roster to the arm exactly when `execution.condition_index is not None`**

and that is structural rather than a list of scope names someone can get wrong later. A `run`-scope step
runs once for the whole run and a `summary`-scope step runs once after every condition — neither belongs
to an arm, and the worked example's `step04_compare_methods` is `summary` scope, so this is reachable
rather than theoretical.

**It needs the test that discriminates.** With 12 units in arms of 7 and 5: a `summary`-scope step and a
`run`-scope step must each receive **12**. Without that pair, an implementation that narrows at all four
scopes passes every test the brief currently specifies.

## Ordering against the fold narrowing is the load-bearing detail

`runner.py`'s repeat branch builds

```python
step_units = UnitList(
    [u for u in units if u.key in handed],
    train=UnitList([u for u in units if u.key not in handed]),
)
```

If the arm narrowing is applied to `step_units` *after* that branch, `train` silently keeps units of the
**other arm** — a training set leaking across arms, the same class of fault as the cluster leak
`partition_units` exists to prevent, and one no size assertion on `io.units` would catch.

**Narrow `units` to the arm before the fold branch reads it**, so both `handed` and its complement are
computed within the arm. Then assert it: **`.train` must contain no unit of the other arm.** That is the
assertion a plausible implementation fails, and it is the reason this ordering is written down rather
than left to fall out.

## `groups` + `fold` is not refused, and this is a ruling

The composition above is well-defined: each unit is still in exactly one fold, and cross-validation
happens within the arm. What is missing is only the **bound on `k`** — a small arm can yield an empty
fold. The spec's out-of-scope table already assigns H3c-3 "`k` bounded per cell, and the empty-fold-
per-arm case", which is a bound, not a construction. **Do not mint a refusal for the combination**; that
would narrow what this slice ships on account of a gap the design routed elsewhere. Build the
composition, test it, and leave the bound alone. The controller records the gap under task 18.

## The two mutations the brief names, and what each must kill

- hand every condition the whole roster → the **size** assertion fails (`sizes == {7, 5}`, `12 not in sizes`)
- re-resolve units per condition → the **`units_hash`** assertion fails

Neither may kill the other's test; if one mutation kills both, the tests are not separating "which units"
from "how they were obtained". Delete `__pycache__` between mutation and revert; verify the revert by
running the tests, never by `git status`.

## The fixture's numbers, and why 7 and 5

7 and 5 are deliberately uneven and neither is 6, so an arm cannot be confused with the other arm, with
half the roster, or with the whole roster by size alone. **Do not "tidy" them to 6 and 6.** State that
reasoning in the test's docstring, as every fixture in this plan must.

Per the global constraints, this fixture must not double as a cluster fixture: give it no `cluster_by`,
or one on a column whose partition is genuinely different from the arm partition, and say which in a
comment. If arms and clusters were the same partition, arm-aware and cluster-aware behaviour would be
indistinguishable.

## *Arms need allocation* — consume the single authority, do not re-derive

`units.arms_of(roster, column, levels)` was added by task 10 and **is the single authority for arm
membership**, read by `validate` already. The subset view reads it too — the fifth instance of the
pattern behind `usable_weight`, `is_measurement_numeric`, `clusters_of`, `fold_basis`, and the property
that makes "a config that validates cannot crash the runner" true. **Do not derive membership from the
roster a second time here.** If `arms_of` does not give you what the runner needs, change `arms_of` and
say so — a second derivation is the defect this pattern exists to prevent.

For the `allocation: within` half, note that `E-DATA-ASSIGN-*` codes are `_check_assign`'s and are gated
on the `assign` block; *Arms need allocation* is a check on the **pair** `sweep.groups` + `allocation`,
like `E-DATA-ALLOCATION-NO-ARMS`, which is its exact mirror (arms declared with no allocation vs.
allocation with no arms). Put it where its mirror lives and name the mirror in the message.

## Documentation

**Never write a phrase locating a table row by position** ("the row above", "immediately below",
"further up"). Tasks 9, 10 and 11 did it five times between them and were wrong twice — once in a row the
diff did not touch, falsified by an insertion that moved it. Name what a sibling row *does*. When you
insert a row, check every row your insertion **moved**, not only the ones you edited.

The registry table § Errors `validate` reports is sorted; one pre-existing violation
(`E-SWEEP-ABLATE-BASELINE-GROUP` after `E-SWEEP-ABLATE-CROSSED`) belongs to task 20 — leave it.
