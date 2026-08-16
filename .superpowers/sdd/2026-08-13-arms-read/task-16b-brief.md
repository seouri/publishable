## Task 16b: A contrast whose two sides share no units is refused

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`; Test `tests/test_validate.py`

**Found by a pre-flight audit of tasks 13–20, and settled by the user: refuse, do not build.**

`cli._vs_baseline_block` hard-codes `"paired": True`. Its own docstring says why that is safe today —
the unpaired case *"needs a group axis or `allocation: between`, both refused
(`E-SWEEP-GROUPS-UNSUPPORTED`, `E-DATA-ALLOCATION-UNSUPPORTED`), so it is unreachable in this build"* —
and **task 17 retires exactly those two codes**. `grep -rn 'unpaired_\|welch_' src/` returns one hit,
that same docstring line. No construction exists.

Probed, not reasoned: a `groups` axis with `baseline: {arm: control}` yields 2 comparisons; the arms
are disjoint, so `paired_keys` returns `[]` and every downstream statistic returns `None`. After task 17
such a run would write, per metric, `{"delta": null, "basis": "units", "paired": true, "n_paired": 0,
"ci95": null, "cohens_d": null}` — **silently**, no raise and no warning. That falsifies
`experimental-designs.md` § Mistakes core prevents' *"Paired analysis of an unpaired design"* in the
same slice that makes the design legal.

**This task must land before task 17.** A refusal minted after the retirement is a refusal that shipped
too late.

- [ ] **Step 1: Failing test.** A `groups` axis with a declared baseline draws the new code; a declared
  `statistics.contrasts` entry across arms draws it too. **The control is a `groups` axis with no
  baseline and no contrasts** — that config has no comparison at all and must draw nothing new, and it
  is the config tasks 12 and 19 already use, so it must keep passing.
- [ ] **Step 2: A second control that must report** — `allocation: within` with a parameter axis and a
  baseline, whose contrast *is* paired, must be unaffected. Assert the exact finding set on both.
- [ ] **Step 3: Implement** as a check on the **combination**, beside `E-DATA-WEIGHT-CONTRAST` and
  `E-DATA-CLUSTER-CONTRAST` in `_check_sweep` — the two existing refusals of exactly this shape, a
  comparison core can count but cannot construct. Read both before writing yours. **Not** in the
  five-field loop, which refuses declarations rather than combinations.
- [ ] **Step 4: The message** says a contrast between conditions on a group axis compares two disjoint
  sets of units, that core has no unpaired construction to give it an interval, and that the honest
  routes are a `summary`-step `Estimate` or two separate runs joined in a `study`. Temporary — say so in
  the same words the sibling refusals use, without naming an internal slice.
- [ ] **Step 5: Mutate** each half separately: the baseline-generated comparison and the declared
  contrast must each die to their own branch.
- [ ] **Step 6: Registry row** in § Errors `validate` reports, sorted. **Then fix the docstring that
  motivated this task** — `cli._vs_baseline_block`'s "unreachable in this build" claim names the two
  codes task 17 removes, and must name this one instead. Commit.
