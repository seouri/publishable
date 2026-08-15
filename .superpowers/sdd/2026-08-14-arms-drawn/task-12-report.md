# Task 12 report — `assign.stratify_by` in the draw

Commits: `ef46038` (the feature), `986370f` (two doc statements and one test-claim fix from
review), `a600358` (the review's Important plus its two Minors — see § Review round 2 at the
end). `uv run pytest` 1594 passed / 2 xfailed; `ruff check` and `mypy` clean. `ruff format`
not run. This report is under `.superpowers/sdd/.gitignore` and is deliberately untracked.

## What was built

**`units.assignment_for` draws stratified, under both drawing methods.** The refusal task 8 left
inside the `random` branch is gone, and so is the matching one in the `blocked` branch — that
second raise was validate-clean-then-crash: § Validation's *Allocation strata exist* and the
`E-DATA-ASSIGN-STRATIFY-UNKNOWN` registry row both gate on "random **or** blocked", so a
well-formed `stratify_by` under `blocked` validates clean and would have reached a
`NotImplementedError`. Nothing in the documents refuses the pair (decision 1 refuses `blocked` ×
`cluster_by`, not × `stratify_by`), and stratified permuted blocks are the composition the
existing block loop already supports.

- `units.stratum_names` (public) is the one reading of the declaration — imported by
  `validate._check_assign` rather than re-read there, `auto_block_size`'s own argument: a bare
  `stratify_by: site` cannot be one name to the draw and a character sequence to the check.
- `units._stratum_groups` splits the roster into one group per *combination* of the declared
  values, in roster order, and `_blocked_draw` is the block loop extracted so the stratified path
  is that same loop once per stratum rather than a second blocking rule.
- Unstratified draws are unchanged bit for bit: an empty declaration is `()` and leaves both
  branches on their previous code path, including the fresh `random.Random(seed)` the unclustered
  `random` draw uses.
- `ArmPlan.strata` now carries the realized declaration; its docstring, `assignment_for`'s two
  refusal paragraphs, and `_check_assign`'s `arms_of` paragraph were rewritten rather than left
  claiming what this branch no longer does.

**`validate` gained two rows.** *Allocation strata exist* reports
`E-DATA-ASSIGN-STRATIFY-UNKNOWN`, one finding per offending name, existence only — a declared
attribute and a `sweep.groups` axis are both legal targets, and order stays task 13's.
*Allocation strata survive clustering* is **newly minted** as `E-DATA-ASSIGN-STRATIFY-VARIES`
(§ Validation row + registry row in `reference.md`, alphabetical slot `STRATIFY-UNKNOWN` <
`STRATIFY-VARIES` < `UNKNOWN` < `VARIES`): the constancy refusal had no code, and both
alternatives were closed — `STRATIFY-UNKNOWN` is narrowed to existence, and
`E-REPL-FOLD-STRATIFY-VARIES`'s row says "A `fold` level's". It reuses
`units.stratum_varies_within_cluster`, is skipped for a name the existence row already reported,
and is not reached under `blocked`, whose pairing with any `cluster_by` is already refused.

**`_check_assign` now calls `assignment_for`, not `arms_of`** (addendum item 2). The block is
passed whole so `from` resolution is that function's single copy too; the digest is the literal
`"validate"`, `_check_replication`'s own placeholder convention, and the call sits strictly
inside the `by_attribute` branch where the parameter is provably unread — with a comment saying
why a future hoist above the method dispatch must confront the value.

**Step 5 (exclusion):** `_accounted_attribute_names` walks the `data` block for any `stratify_by`
key and handles both the string and list forms, so `assign.<axis>.stratify_by` is already
excluded from `W-DATA-CLUSTER-UNDECLARED` with no `assign.from` in sight. Test added either way,
with the no-`stratify_by` control that must warn.

**Step 6 (record, do not fix):** `reference.md` § Allocation, in the paragraph that already
argues `assign.<axis>.from` must not vary across measurement rows, now records that
`stratify_by` carries no such refusal, what it costs, and that closing it means joining the same
constant-column family under `E-DATA-ASSIGN-VARIES`. Not written to the gitignored
`spec-defects.md`.

## The fixture, and why its numbers discriminate

12 units, `site` A×6/B×4/C×2, **interleaved** in roster order so `blocked`'s blocks do not
coincide with stratum boundaries. Seed 11 was chosen by running the *unstratified* draw over
candidate seeds, and that choice is written down as a test rather than left in a scratch script:
`test_an_unstratified_arm_draw_of_the_same_fixture_is_lopsided` pins `random` at A 5/1, B 1/3,
C 0/2 and `blocked` at B 3/1, C 0/2 for the same roster and seed. Every one of those differs from
the stratified answer (A 3/3, B 2/2, C 1/1) that the two stratified tests assert exactly, so the
"ignore `stratify_by`" mutation fails them deterministically rather than for a fraction of seeds
— the failure mode the addendum cites five surviving mutations for. Totals are 6/6 either way,
which is why no whole-roster size assertion is made.

## Mutations — applied, run, reverted, re-run (never reasoned about)

`__pycache__` deleted between mutation and revert; every revert verified by re-running the test.
All ten mutated runs FAILED and all ten reverted runs PASSED.

| Mutation | Test that failed |
|---|---|
| `random` ignores the strata | `test_a_stratified_draw_balances_arms_within_every_stratum` |
| `blocked` ignores the strata | `test_a_stratified_blocked_draw_balances_arms_within_every_stratum` |
| Coverage checked per stratum | `test_a_level_empty_in_one_stratum_is_fine_if_another_stratum_covers_it` |
| A bare `stratify_by` read as characters | `test_a_stratified_draw_balances_arms_within_every_stratum` |
| A name no unit carries drawn as one stratum | `test_a_stratum_no_resolved_unit_carries_is_not_drawn_as_one_stratum` |
| Existence check drops the attribute allowlist | `test_a_declared_stratum_attribute_is_not_refused` |
| Existence check drops the axis exemption | `test_an_unknown_stratum_attribute_is_refused` |
| Constancy check never reports | `test_a_stratum_that_varies_within_a_cluster_is_refused` |
| Constancy check runs under `blocked` too | `test_a_varying_stratum_is_not_reported_a_second_time_under_blocked` |
| Exclusion stops walking for `stratify_by` | `test_an_assign_stratum_is_excluded_from_the_undeclared_cluster_warning` |

## Concerns

1. **Can a stratified draw produce an empty arm? No.** Per-stratum zero is legal — `blocked`'s
   own per-block rule, one construction over — and the coverage check runs over the **merged**
   draw, raising `E-DATA-ASSIGN-LEVELS` for a level empty across every stratum. Both the legal
   case and the refusal are tested.
2. **One producer, both sides.** The runner reaches membership through `cli._resolved_group_axes`
   → `assignment_for`, and `validate` now reaches it through `assignment_for` too. `arms_of`
   survives as the column-read partition *inside* that function and has no other caller in `src/`.
3. **A stratum naming a group axis validates clean and raises at the draw** —
   `NotImplementedError`, naming task 13, which the task-13 addendum claims (axis 2's draw
   consuming axis 1's realized membership). Deliberate, but it is a live validate-clean-then-raise
   window until task 13 lands.
4. **The `_declared_levels` / `_resolved_group_axes` first-versus-last asymmetry** carried in the
   addendum is untouched and still unreachable (`E-SWEEP-PATH-DUPLICATE`).
5. **Stratified arm sizes can differ by more than one, biased toward the first-declared level.**
   `_apportion` runs per stratum and the floors add: three strata of five at an equal two-arm
   ratio give 9/6 where the unstratified draw gives 8/7. Stated in `assignment_for`'s docstring,
   the same statement `partition_units` carries for stratified folds; it also makes
   `E-DATA-ASSIGN-LEVELS` more reachable (three strata of one unit over two arms apportion
   `[1, 0]` everywhere and are refused), which the message's "stratify on fewer attributes"
   remedy names. Recorded, not fixed — balancing totals across strata unbalances the strata.
6. **`artifacts.build_allocation_document`'s docstring still says `seed`/`strata` are empty "in
   this build", correctly**: it grounds that on `E-DATA-ASSIGN-DRAWN` still refusing both drawn
   methods at `validate`, so no drawn plan reaches it through `command_run`. Task 14 retires that
   refusal and owns that paragraph; the code there already reads `plan.strata` and needs no change.
7. **The `arms_of` → `assignment_for` swap is not mutation-testable**: both resolve the same
   partition for `by_attribute`, so no test distinguishes them. It is a structural guarantee, and
   the docstring is where it is argued.

## Review round 2 — `a600358`

**Important: two RNG mutations survived the full suite, and the reason generalizes.** Per-stratum
arm counts are *forced* by `_apportion` — each stratum's split follows from its size and the ratio
before any number is drawn — so **no count assertion can detect an RNG mutation on the stratified
path**. Every stratified test I wrote asserted counts or structure (cluster wholeness, per-site
totals), both forced, so my ten mutations sampled that class exclusively and could not have found
these:

- deleting `stratified_rng.shuffle(stratum_keys)` — arms decided by roster order, not drawn;
- `random.Random(seed)` → `random.Random(0)` — the seed ignored while `ArmPlan.seed` still records
  it, which is a false record of the draw, the fault `ArmPlan`'s docstring argues against for
  `strata`.

Fixed by pinning `plan.members` exactly at seed 11 and asserting seed 12 gives different
membership, for the unclustered **and** clustered stratified paths (the clustered path draws from
the same generator, so both mutations are covered there too). Both mutations re-run: each now
FAILS `tests/test_units.py`, and each reverted run passes. The docstrings say why the pin exists
rather than leaving it as a magic tuple.

**Minor 1** — `E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s row said the absorption is the one
`E-DATA-ASSIGN-NO-DRAW` performs "one row up"; it is two, with `E-DATA-ASSIGN-RATIO` between. Now
names what the sibling row *does* ("for the same two fields under `by_attribute`"), per the
standing rule against locating a row by position.

**Minor 2** — the apportionment consequence now appears in `reference.md` § Allocation, beside
the `stratify_by` and `ratio` a user is reading, not only in `assignment_for`'s docstring: totals
may not honour the ratio, deviation bounded by the stratum count rather than by one unit, surplus
to the first-declared level, and `E-DATA-ASSIGN-LEVELS` made easier to reach. § Clustered units'
identical non-promise for the stratified fold is the precedent cited.

**Also** — `_check_assign`'s docstring said "thirteen § Validation rows" while implementing
fourteen; it omitted *Block size fills the arms*, and was already one short at "eleven" before
this slice. Corrected, with the pre-existing miscount named so it is not re-derived.

**Calibration accepted:** neither the `blocked` × `stratify_by` gap nor a group-axis stratum is
reachable through a command today — `E-DATA-ASSIGN-DRAWN` still refuses both drawn methods at
`validate`, so those paths are direct-API only until task 14. The "validate-clean-then-crash"
framing in this report is one slice ahead of the build; the fixes stand regardless.
