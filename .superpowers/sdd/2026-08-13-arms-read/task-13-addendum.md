# Task 13 — controller additions

These are requirements, with the same force as the brief file they accompany.

## "Implement, or confirm no change is needed" — it is not no-change, and here is where

`cli.py`'s per-condition loop calls

```python
counts = attrition(results, roster, step_name, cond.index, fold_members=..., weights=..., clusters=...)
```

passing **the whole roster** for every condition. `attrition`'s own docstring says so: *"`resolved`
counts what was handed out across this condition… without a fold that is the full roster, since every
execution receives it whole."* Under `allocation: between` that sentence is **no longer true** — the
execution received the arm — so a condition would report `resolved: 12` over an arm of 7 and derive
`failed` for five units that were never handed to it. **Do not "confirm no change needed".** If your
reading disagrees, show the number, not the reasoning.

The pattern to follow is already in the same file: the `report_by` branch builds
`level_roster = UnitList([u for u in roster if u.key in keys])` and passes **that** to `attrition`,
with a comment saying the recomputation "is what makes it carryable at all". Your case is the same
shape one level up, and it must consume `units.arms_of` — task 10's single authority for arm
membership, already read by `validate` and, after task 12, by the runner — rather than deriving
membership a third time.

**Update `attrition`'s docstring in the same commit.** It currently states the whole-roster claim as a
fact; leaving it is the stale-comment failure this project has now hit repeatedly.

## The two assertions, and what makes each able to fail

Over the 7/5 fixture task 12 established:

1. **Per condition:** `resolved == completed + ineligible + failed`, with `resolved` equal to **7** for
   one arm and **5** for the other. Assert the exact numbers. `resolved == completed + ineligible +
   failed` alone is satisfiable by `12 == 12 + 0 + 0` and by `12 == 7 + 0 + 5`, so the reconciliation
   without the exact `resolved` is a check that cannot fail — which is this project's dominant defect
   class and has appeared ten-plus times across three slices.
2. **Across conditions:** the arms' `resolved` sum to the roster (7 + 5 = 12) when every unit is
   assigned. Note this is only meaningful because set equality is enforced at validate
   (`E-DATA-ASSIGN-LEVELS`, task 10): no unit belongs to no arm, and no declared level is empty.

**Make at least one arm attrit.** Two arms that both complete cleanly give `completed == resolved` on
both sides, and then `ineligible` and `failed` are zero everywhere and no arithmetic is being tested.
Have one unit `io.skip` in one arm and one fail in the other, and state in the docstring which number
proves which part.

## The other denominators that read the roster

`resolved` is not the only figure computed against it. Check, and say in your report what you found for
each — a bare "checked" is not a finding:

- `limits.max_ineligible_fraction`, computed in the same loop as `counts["ineligible"] /
  counts["resolved"]` — a per-arm ratio over a whole-roster denominator understates attrition
- `max_failed_fraction`, which the invariants say "guards only the fourth" part of `n`
- Kish's effective size (`weights`) and the cluster count (`clusters`), both of which `attrition`
  receives as whole-roster mappings and scopes internally — confirm the scoping is by the units it
  counts and not by the mapping's extent

If any of these is wrong under arms and fixing it is out of this task's scope, **say so with the number
that shows it** and the controller will route it. Do not fix silently and do not leave it unmentioned.

## Mutation

Counting the whole roster per condition must fail **both** assertions. If it fails only one, the two
assertions are not independent and one of them is decorative — rewrite rather than reason about it.
Delete `__pycache__` between mutation and revert; verify the revert by running the tests.

## Documentation

**Never write a phrase locating a table row by position.** Tasks 9, 10 and 11 did it five times and were
wrong twice, once in a row the diff did not touch — falsified by an insertion that moved it. Name what a
sibling row *does*, and when you insert a row, check every row your insertion **moved**.

`reference.md` § The per-unit tables and the `n` discussion around the three-part count are the passages
most likely to need a sentence about arms. Check them; the documents lead the code.

## Carried from task 12's review — a live document claim the code does not satisfy

`reference.md` § What `status` means already says *"Under a group axis it's that arm's roster, ~120
rather than 240"*. Today `attrition` is arm-blind, so it would report `resolved: 240` and count the
other arm's 120 units `failed`. **The prose is right and the code is wrong** — this task is where they
meet. That sentence is also your acceptance check: after your change, the number it names must be the
number the code produces.

Task 12 made `_units_failed_anywhere` arm-aware (with a test asserting exactly `{"u4"}`) and left
`attrition` alone, by instruction. So **two notions of "did this unit fail" now differ**, and closing
that gap is yours. Check them against each other explicitly and say in your report whether they agree
after your change; if they cannot be made to agree, say why with the numbers.

`units.arm_members` is where task 12 put the per-condition membership, built on `units.arms_of`. Consume
one of those — a fourth derivation of arm membership is the defect the single-authority pattern exists
to prevent, and this file already has three readers of it.


## Corrections from the pre-flight audit — these override what is written above

**1. My "sum to the roster" assertion is decorative, and my own independence test would certify it.**
I wrote that the arms' `resolved` must sum to the roster (7 + 5 = 12) and that the whole-roster mutation
must fail *both* assertions or one is decorative. Over a fixed 12-unit fixture, `7 + 5 = 12` is
**arithmetically implied** by pinning 7 and 5 — it can only fail if one of those already failed. So both
assertions do die to the mutation *because they are dependent*, and my criterion reports "independent"
for a check that cannot fail on its own. **Replace the sum with coverage**: the union of the arms'
`resolved` key sets equals the roster's keys, and their intersection is empty. That is what
`E-DATA-ASSIGN-LEVELS`' set equality actually buys, and it fails for reasons the pinned counts do not.

**2. My section citation was wrong.** The sentence *"Under a group axis it's that arm's roster, ~120
rather than 240"* is real and word-perfect, but it is in **§ What isn't a repeat**, in the three-part `n`
discussion — not § What `status` means, which is the completed/partial/failed table and says nothing
about arms. The claim built on it stands; the pointer was wrong.

**3. Consume `units.arm_members`, not `arms_of` — my headline instruction had it backwards.** `attrition`
takes `(results, roster, step_name, condition_index, …)`; reaching `arms_of` from there would mean
threading the axes declaration down and re-reducing across axes per condition, which is a *fourth*
derivation — the thing the single-authority pattern forbids. `arm_members_map` already exists at the
call site in `cli.py`, built from the same resolved conditions the plan was built from, which is
`_arm_keys`' stated invariant. Use it.

**4. `report_by` has the same defect one level down, and no task owns it.** The branch I held up as the
pattern computes `levels_for(roster, attribute)` over the **whole roster** inside the per-condition loop,
so under arms a level's key set spans both arms and `level_roster` hands `attrition` units of the other
arm. Its own comment states the invariant it breaks: *"One key set decides BOTH the table and the counts
… a number reported against a denominator computed over other units."* **This task owns it now.** Fix it
with the same narrowing, and pin it with a test whose stratum genuinely crosses both arms — otherwise the
fix and the bug are indistinguishable.

**5. `technical_n` beside a per-arm `n` — decide and say which.** `cli.py` computes `technical_n` once
from the whole roster and passes it into every condition's metric block. This task makes the `n` beside
it per-arm. The codebase already litigated this one level down and went the other way: the `report_by`
branch **withholds** `technical_n` because it is *"a whole-roster figure that would have to be COPIED
down"*. Follow that precedent or argue against it in the docstring — but do not leave a whole-roster
`technical_n` sitting beside a per-arm `n` without saying so.
