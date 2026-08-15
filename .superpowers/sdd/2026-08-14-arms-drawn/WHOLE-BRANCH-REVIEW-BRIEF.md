# H3c-2 whole-branch review — arms drawn

Branch `h3c2-arms-drawn`, 32 commits over `39c6667` (the H3c-1 merge). 11 files, +5144/−280.

**Goal:** `assign.method: random` and `blocked` **draw** the arm assignment — honouring `ratio`,
`block_size` and `stratify_by`, keeping whole clusters on one side, seeded from `assign.seed` —
recorded in `allocation.json` under `provenance.allocation_hash`. Before this branch, only
`by_attribute` executed: the arm was *read* from a column, and both drawn methods were refused by value.

## The property to attack

**A drawn assignment is a partition of the roster into the declared levels, reproducible from
`(digest, axis, roster, seed)` alone, recorded in `allocation.json`, and identical between the plan
`validate` computes and the one the runner executes.**

`units.assignment_for` is the **single authority** — a pure function callable from `validate` and from
`cli.command_run` alike, an **allowlist** where `by_attribute` reads a column and everything else must
be explicitly implemented or raise. `units.arms_of`'s docstring calls a second notion of arm membership
*"the validate-clean-then-disagree gap in a new shape"*. **Look for a second producer.**

## Where this branch's defects lived — hunt these first

**Nine mutations survived a full suite during execution**, every one caught by a reviewer rather than by
the implementer that wrote the code. The diagnoses generalize, and are the best guide to what to try:

1. **A fixture whose numbers agree with the bug.** Twice: an "undeclared level" ratio fixture that was
   *also* partial, so neither direction was isolated; and a 13-unit apportionment fixture that agreed
   with a reverse-order mutant by coincidence.
2. **A dimension no assertion can see.** Per-stratum arm counts are *forced* by `_apportion`, so **no
   count assertion can detect an RNG mutation on the stratified path** — deleting the shuffle, or
   replacing the seeded generator with `Random(0)`, both left 1594 tests green. The second is worse: the
   seed is ignored while `ArmPlan.seed` still **records** it, a false record of the draw.
3. **A parametrized test asserting a *failure* for both arms**, which proves nothing about either arm's
   *success* path — `blocked`'s forward-only stratification was fully threaded and never exercised.
4. **A behaviour documented in a registry row and an eight-line comment, asserted nowhere** — twice, and
   both times removing the guard raised an uncaught exception **out of `validate`**, a module contracted
   never to raise.
5. **Testing the refusal but never the honouring** — `validate` refused bad `block_size` values while
   nothing checked the draw *used* a good one, so ignoring an explicit `block_size` entirely passed all
   1563 tests.

**Also recurring: a comment or document claiming a guarantee the code does not provide.** At least six
instances, including a docstring that explicitly promised "any other `method` string takes the
`by_attribute` path" — the fail-open defect written down as if intended — and three overreaching claims
inside a single commit that was itself fixing overreaching claims.

**And seven positional table-row phrases**, wrong on at least two occasions, once in a row no diff
touched.

## Known and deliberately left

- **Three classes of starving draw validate clean and raise at the run**: clustered, attribute-stratified,
  and axis-stratified. Recorded at five sites. The widening was declined with a stated reason — admitting
  attribute strata means either swallowing a `NotImplementedError` or **copying `_stratum_groups`'
  precedence rule into `validate`**, a second copy of the rule the single-producer seam exists to prevent.
- **`resume` still does not exist**, and its "read rather than re-drawn" rule stopped being harmless: under
  `by_attribute` a re-derivation re-read a column and agreed; under a draw a second draw is a second
  allocation.
- `limits.min_units_per_cell` remains unowned and hedged (a limits deliverable, not a drawing one).
- A single `by_attribute` axis whose column varies within a cluster splits that cluster with no finding —
  pre-existing, and defensible: § Clustered units promises indivisibility for a partition *core computed*.

## What no task-scoped review could see

- whether the 32 commits **together** leave the single-authority property true
- whether the retirement of `E-DATA-ASSIGN-DRAWN` left any claim, comment, test or document stale
- whether the eleven codes this branch touched overlap or leave a gap between them
- whether a drawn allocation is genuinely reproducible — same inputs, same arms, across processes
- whether the worked example moved: 240/228/12; r = 0.581 / 0.607 / 0.412; delta 0.026 ci95
  [−0.007, 0.059]; kendall −0.169 [−0.213, −0.125]; `repeat_spread` std 0.014; hashes
  `8e21`/`1a2b`/`3d8a`/`6b1f`; README demo `2f5c8d0`
