# Task 19 — controller additions

These are requirements, with the same force as the brief file they accompany.

**This task is tests only, and it is the one that catches what no single task owned.** Every defect this
project has shipped lived in a combination: `measurements` × `weight_by`, `measurements` × `cluster_by`,
the `k: all` budget, and — found at task 12's review — two derivations of "which group axes exist"
disagreeing, which handed both conditions the whole roster. Write these as if you expect to find one.

## Step 2 is a decision, not an observation — and here is the ruling

A `groups` axis whose name collides with a parameter path. `expand` produces both a selector and a
parameter path of the same name, and `Condition.selectors` (task 3) is what distinguishes them.

**Refuse it at `validate`.** A name that is both a unit selector and a parameter path makes
`Condition.values[name]` ambiguous at seven reader sites, and the whole point of task 3's `selectors`
marking was that the distinction is carried *on the condition* rather than re-derived per reader — a
name in both sets defeats that by construction. Mint `E-SWEEP-GROUPS-PARAMETER` and say in the message
that a group axis names a set of units while a parameter path names a value, so one name cannot be both;
rename the axis, or sweep the parameter under a different path.

If you find the collision is already refused by something else, say which code and drop the new one —
do not add a second reporter for one fault.

## Step 3's fixture, restated because it is the easy one to get wrong

Cells and clusters must **not** be the same partition, or arm-aware and cluster-aware behaviour are
indistinguishable and the test proves nothing. The existing cluster harness in `tests/test_runner.py` is
5 units over 3 clusters; task 12's arm fixture is 12 units in arms of 7 and 5. **State the two partitions
explicitly in the docstring and show they cross** — some cluster spanning both arms, some arm containing
units of two clusters. A reader must be able to check the discrimination without running anything.

Note what `reference.md` § Clustered units already settles, so your test pins the documented behaviour
rather than inventing one: under `method: by_attribute` **the arm is read rather than drawn, and a
cluster may span both arms** — in a matched case-control design it always does. So a cluster straddling
two arms is *correct here*, not a fault, and the contrast stays unpaired with a cluster-robust interval.
Do not write a test asserting clusters are kept whole across arms; that rule belongs to `random`/
`blocked`, which this build refuses.

## Step 1's arithmetic

`ablate × groups` gives `(1 + n)` conditions per group level, per § Expansion modes. With 2 levels and
3 ablatable components that is 2 × 4 = 8 — **assert the number and the labels**, not just the count, and
pick counts where `(1 + n) × levels` cannot be confused with `n × levels` or with either factor alone.
2 × 4 = 8 works; 2 × 2 = 4 does not, since 4 is also 2 + 2 and 2².

## Step 4 end to end

`groups × measurements` closes the loop task 11 opened: the constancy check refuses a varying arm, but
nothing yet proves a **constant** arm survives collapse and reaches the right condition. Assert the
resolved unit's arm attribute, the `technical_n` showing the rows actually collapsed, **and** which
condition's roster the unit landed in. The third is the one that makes it end to end rather than two
earlier tests run together.

## Fixtures and mutation

Every fixture states why its numbers discriminate. Every new test must be shown to fail against a
mutation of the behaviour it claims to test — a combination test that passes under every mutation is
testing that the two features do not crash, which is not what this task is for. Delete `__pycache__`
between mutation and revert; verify reverts by running tests, never by `git status`.


## Corrections from the pre-flight audit — these override what is written above

**1. Step 2's collision is already refused. Do not mint `E-SWEEP-GROUPS-PARAMETER`.** Task 5 closed it:
`validate.py` emits **`E-SWEEP-PATH-DUPLICATE`**, and § Validation carries the row verbatim — *"…or a
`sweep.groups` axis's `by` names a path one of those three writes, which is the worse version of the
same collision — a group cell is a set of units, so every condition marks that path a selector and no
scope plants the parameter."* My ruling was stated first and in bold and it was wrong; **step 2 is
"pin the existing refusal", exactly as the ledger recorded it.** What remains genuinely open, and is
correctly yours: a `by` naming a parameter that is **declared but not swept**.

**2. Step 3's fixture cannot carry a baseline or a contrast, and the brief never says so.** My concluding
clause — "the contrast stays unpaired with a cluster-robust interval" — describes behaviour this build
both refuses and lacks: `validate` fires `E-DATA-CLUSTER-CONTRAST` whenever a comparison exists beside a
declared `cluster_by`, and no clustered contrast construction exists. A `groups` axis with the natural
`baseline: {arm: control}` yields two comparisons, so that config is refused outright. **Write the
`groups × cluster_by` test with no baseline and no `statistics.contrasts`**, and say in the docstring
that the combination is what is under test, not the comparison. After task 16b, a cross-arm contrast is
refused on its own account too — check which code fires and assert the exact set.

The rest of step 3 checks out: the cluster harness and task 12's `_arm_roster12` genuinely cross, and
§ Clustered units really does say that under `by_attribute` a cluster may span both arms.

## Step 6 (new) — the end-to-end counting test task 13 could not write

Task 13 narrowed `attrition`, `report_by`'s strata and `beside_n` to the arm, and its review found that
**the brief's own Step 5 mutation passed green at the real call sites**: reverting all three call sites
in `cli.command_run` to whole-roster behaviour killed nothing in the suite. The implementer extracted
`_condition_counts`, `_condition_report_by_levels` and `_condition_beside_n` so each is directly
mutation-tested, then disclosed honestly that the literal mutation **still** passes, because
`command_run`'s inline aggregation loop is unreachable end to end while `E-SWEEP-GROUPS-UNSUPPORTED`
stands — and it could not find the task-12-style bypass that made `execute_plan` testable.

**Task 17 removes that refusal, and you run after it.** So the route task 13 lacked exists by the time
you execute:

- a real `groups` + `allocation: between` + `assign.method: by_attribute` config that **validates clean**
- run it end to end through `command_run`
- assert the per-condition `n` in the written `run.yaml`: `resolved` equal to the arm's size, and
  `resolved == completed + ineligible + failed` per condition, with at least one arm attriting so
  `ineligible` and `failed` are not both zero
- **then run the mutation task 13 could not**: revert `command_run`'s three call sites to pass the whole
  roster, and confirm this test fails. Record the output. If it passes, the narrowing is still unpinned
  at the place that matters and that is a Critical finding, not a note.

This is the only test in the slice that proves the counting fix is *wired in* rather than merely
present. Do not skip it because task 13 is marked complete — task 13 is complete on everything it could
reach, and this is the part it could not.

## Correction to step 1's arithmetic — use the document's own example, not mine

I wrote "with 2 levels and 3 ablatable components that is 2 × 4 = 8". **Prefer the config
`reference.md` § Expansion modes already shows**, so your test pins what the document claims rather than
a shape I invented:

```yaml
sweep:
  groups:
    - {by: cohort, levels: [derivation, validation]}
  baseline: {features.labs: true, features.notes: true}
  ablate:
    from: baseline
    remove: [features.labs, features.notes]
  # 2 levels × (1 baseline + 2 ablations) = 6 conditions
```

Six is distinguishable from both factors (2 and 3), from the per-level count (3), and from either factor
alone — so it discriminates, and the section prints the expected labels
(`00_cohort=derivation__baseline`, `01_cohort=derivation__labs=false`, …
`03_cohort=validation__baseline`). **Assert the labels, not only the count** — the count alone cannot
tell a correct expansion from one that emitted the baseline once per run instead of once per level,
which is the specific thing this passage says is the honest reading.

Two nearby claims in the same section your test should not contradict, and may as well pin:

- *"the baseline becomes one condition per level rather than one per run … there is no single reference
  condition when the reference cohort differs"*
- *"`sweep.baseline` may not name the group axis for this reason — the arms are peers, and `validate`
  rejects a baseline that fixes a level while `ablate` is declared"* — that refusal is task 6's
  (`E-SWEEP-ABLATE-BASELINE-GROUP`), already built and tested; do not duplicate it, but a control
  confirming it still fires beside your composition test costs one line.
