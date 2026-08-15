# Task 13 report — forward-only stratification

**Status: COMPLETE.** Commit `d4aa70a`. 1602 passed + 2 xfailed; `ruff check` and `mypy` green.
(`ruff format` deliberately not run.)

## What landed

**`units.assignment_for(..., resolved=None)`** — the plans of the axes *already drawn*, keyed by
axis name. `units._stratum_groups` takes the same argument and, for a `stratify_by` name that is
one of those axes, reads each unit's stratum out of the plan's **realized membership** (the level
whose `members` hold the unit's key). A drawn axis leaves no column, so this is the only place the
value can come from.

**`cli._resolved_group_axes`** walks the declared `sweep.groups` in order and passes `dict(axes)` —
a snapshot of the plans drawn so far — into each draw.

**`E-DATA-ASSIGN-STRATIFY-FORWARD`**, minted in `validate._check_assign`: a `stratify_by` naming a
group axis this one is drawn *before*, or naming this axis itself. Order comes from
`sweep.selector_paths`, the same declaration order the draw loop walks. A name resolving to a
declared attribute is exempt **before** the order question is asked, matching
`_stratum_groups`' own precedence.

**Task 12's live window is closed.** The `NotImplementedError` naming "task 13" is gone; the raise
now fires only for a name that is neither carried by a resolved unit nor an already-drawn axis, and
its message names both remaining declarations *by code* (`-FORWARD` for a later axis, `-UNKNOWN`
for a name nothing declares).

## Is the draw order a contract, or still an accident?

**It is a contract, and one thing pins it: the raise.** Each axis is drawn against a snapshot of
the axes drawn *before* it, so an axis whose stratum is not in that snapshot **cannot be drawn at
all** — `_stratum_groups` raises. A refactor that reordered the loop, or that drew every axis
against the finished set, fails `test_the_draw_order_is_the_declaration_order_by_contract` rather
than silently drawing a different allocation.

**What does *not* pin it, and why no test claims otherwise:** `units.assign_seed_for` keys on the
axis *name*, not on position, so two axes neither of which stratifies on the other draw
bit-identical plans in either order. Reordering is observable **only** through a stratifying axis.
`assert list(plans) == ["sex", "arm"]` is in the test as a cheap extra; it proves insertion order,
not draw order, and the docstring says so.

## Mutations (applied, run, confirmed FAIL, reverted, confirmed PASS; `__pycache__` deleted each way)

| # | Mutation | Result |
|---|---|---|
| 1 | **The decisive one** — reverse the draw order in `_resolved_group_axes` | `test_the_draw_order_...` FAILS: `arm` is drawn before `sex` exists and raises. Axis 2 *is* consuming axis 1's membership; the feature is not decorative |
| 2 | `dict(axes)` → `{}` (resolved never passed) | same test FAILS |
| 3 | `source.get(unit.key, ...)` → `"no value"` (realized membership ignored, one stratum) | `test_an_axis_may_stratify_on_an_earlier_axis` and the cli test FAIL |
| 4 | Precedence swapped: axis branch before attribute branch | `test_a_stratum_the_roster_carries_is_an_attribute_before_it_is_an_axis` FAILS |
| 5 | `axes.index(name) < axes.index(axis)` → `<=` | `test_stratifying_on_a_later_axis_is_refused[itself]` FAILS |
| 6 | Stratum groups returned sorted rather than in roster order | Only the **new** earlier-axis test FAILS — the pre-existing `site` fixture is already in sorted order, so this dimension had no coverage before |

The dimension the count assertions cannot see (task 12's diagnosis) is handled the way that fix
prescribed: exact membership pinned at seed 11, asserted different at seed 12, on the
earlier-axis path specifically. Mutation 3 is the new-path analogue — per-`sex`-arm counts of 3/3
are forced by `_apportion` once the strata exist, so only membership discriminates.

## Docs

- New registry row in `reference.md` § Errors `validate` reports, alphabetically **before**
  `E-DATA-ASSIGN-STRATIFY-UNKNOWN` (that table sorts by code). No count phrase and no
  positional phrase locates any row the insertion moved; verified by grep over the four documents
  for `the row above/below`, `That last row`, `N codes`.
- `E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s row now names the code its "different fault instead" clause
  previously pointed at anonymously, and states the attribute exemption.
- Neither new row nor either existing one is located by position; both cross-reference by code name.
- § Validation's *Stratification is forward-only* row needed no edit — it already stated the rule
  and its example (`assign.sex.stratify_by: [arm]`) is now the parametrized `later-axis` test.
- § Expansion modes' "forward-only stratification makes a cycle unrepresentable rather than
  something `validate` has to detect" **survives and was examined**: the order is a total one the
  config already states, so what landed is one index comparison, not cycle detection. The new
  registry row says so explicitly.

## Concerns

0. **NEW GAP, MEASURED, ROUTED TO TASK 14 — a cluster can straddle both arms.** An axis-name
   stratum never reaches *Allocation strata survive clustering* (`E-DATA-ASSIGN-STRATIFY-VARIES`),
   whose loop reads only strata that resolved to **declared attributes**. When the earlier axis
   **draws**, that is harmless: it allocated whole clusters, so its realized membership is constant
   within every cluster. When the earlier axis is `by_attribute` with a `from` naming a column that
   varies within a cluster, `arms_of` splits that cluster between the earlier axis's own arms, the
   halves land in different strata here, and `_assign_whole_clusters_by_ratio` allocates each
   independently. **Measured, not reasoned about:** `cluster_by: family_id`,
   `sex: {by_attribute, from: patient_sex}` then `arm: {random, stratify_by: [sex]}`, one family
   whose two members differ in `patient_sex` — the family straddles both `arm` levels at **17 of 30
   seeds**. This contradicts `reference.md` § Clustered units' "core computed the partition, so core
   keeps it indivisible". Unreachable in this build (`E-DATA-ASSIGN-DRAWN` still refuses `arm`'s
   `random`) and it needs `from` ≠ the axis name; with the default the stratum resolves as a
   declared attribute on both sides and the existing check covers it. I did **not** extend the
   VARIES check — that is a new rule with no § Validation row, the controller's to decide, and the
   same shape as the hazards tasks 8 and 10 routed to task 14. Recorded in
   `units.assignment_for`'s and `validate._check_assign`'s docstrings rather than left as the
   overreaching "no check is owed" claim an earlier draft carried.
1. **One shape can still reach the raise through a clean `validate`, and it is pre-existing.**
   `validate` reads the axis order from `sweep.selector_paths`, which admits an axis whose `levels`
   `_resolved_group_axes` skips (any non-`str` element, or an absent/empty `levels`). A non-`str`
   level is caught by `_check_shape` (`E-CONFIG-SHAPE`, which returns before `_check_assign` runs),
   so the reachable residue is an **absent or empty `groups[].levels`**, for which I found no
   refusal. Then `validate` sees an earlier axis that `_resolved_group_axes` never realized, and
   the draw raises. **Not closed**, deliberately: it is the same disagreement
   `_resolved_group_axes`' own docstring already routes to `arm_members`'s `KeyError` as "a caller
   bug to see", and closing it means refusing an empty/absent `groups` level list — a separate
   rule with no row today. Cited as that precedent in the docstring; recording it here as the
   candidate spec gap.
2. **The declared/realized seam in the precedence rule.** `validate` exempts a name in
   `data.units.attributes`; `_stratum_groups` exempts a name a resolved unit *carries*. They agree
   except for an attribute declared but carried by no unit — a broken roster — where units falls
   through to the axis. Stated in `_stratum_groups`' docstring; not worth a code.
3. **The latent `_declared_levels` / `_resolved_group_axes` asymmetry (first vs. last matching
   `by`) is untouched and still unreachable** (`E-SWEEP-PATH-DUPLICATE`). My forward-only check
   reads `selector_paths`, which dedupes keeping the **first** occurrence — so it now sides with
   `_declared_levels`, and `_resolved_group_axes` remains the odd one out. Third place, not second.
4. **Checked and clean, recorded so it isn't re-checked:** `allocation.json`'s `strata` key is "the
   declaration realized, in declared order" and `reference.md` § `allocation.json` constrains it no
   further, so an axis name appearing there is not a cross-document contradiction — its example
   merely happens to use attribute names. `docs/superpowers/spec-defects.md` carries no
   forward-only entry to make stale. `H3c-2-SCOPING.md`'s "row only | none" row and
   `H1-SCOPING.md:135`'s MISSING row are point-in-time scoping records of this slice's own working
   documents (task 1's ruling); left as found rather than back-dated.
5. **Process note:** I ran `git checkout src/publishable/units.py` to revert a mutation, which
   discarded the whole uncommitted implementation of that file (task 4 hit the identical trap). It
   was reconstructed and re-verified — same 1602-test count, same pinned membership tuples,
   including the one asserting bit-identity with the pre-existing column-stratified draw — before
   anything was reported or committed. Every subsequent revert was a text substitution, never git.
   (The reviewer proved the reconstruction complete a stronger way: pre-change versus HEAD
   `assignment_for` output byte-identical over n × method × seed × ratio × strata × clustered.)

## Review round — two surviving mutations closed

**Critical (seventh of the project): `blocked`'s forward-only stratification was threaded but never
exercised.** Reverting only the `blocked` branch's two `_stratum_groups` call sites to the
pre-`resolved` signature left all 1602 tests passing. The reason is worth keeping: the raise test
loops `("random", "blocked")` but asserts a **raise** for both, so it passes whether or not
`blocked` can read a plan at all — **a parametrized test asserting a failure for both arms proves
nothing about either arm's success path.** Every *successful* axis-name draw in the suite was
`random`.

Two tests added to `tests/test_units.py`:

- `test_a_blocked_axis_may_stratify_on_an_earlier_axis` — 3/3 within each `sex` arm, membership
  pinned at seed 11, different at seed 12, and the pinned tuple differs from the **unstratified**
  `blocked` draw of the same roster at the same seed, so "`stratify_by` ignored" fails rather than
  coincides.
- `test_a_blocked_draw_on_an_axis_stratum_names_the_strata_when_an_arm_is_empty` — reaches the
  second call site, which sits **inside** the `E-DATA-ASSIGN-LEVELS` message construction, so the
  mutation there raises `NotImplementedError` while formatting a diagnostic. Four units, an earlier
  axis splitting 2/2, three equal arms: `[1, 1, 0]` in each stratum leaves `c` empty everywhere.

**Important (eighth): the `axis not in axes` guard was documented and unasserted.** Dropping it
left all 1602 passing and is reachable and fatal — `assign.ghost.stratify_by: ["arm"]`, where
`ghost` is no `sweep.groups` axis, raises `ValueError: 'ghost' is not in list` out of a module
contracted never to raise. `test_a_block_whose_axis_is_not_declared_is_not_ordered_against_anything`
asserts the exact set `{"E-DATA-ASSIGN-DRAWN"}`, catching a spurious ordering finding as well as
the crash.

**Minor:** the mangled `validate._check_assign` docstring from the reconstruction ("the the", ragged
reflow) is repaired.

Mutations 7 and 8, applied / run / FAIL / reverted / PASS, `__pycache__` deleted each way:

| # | Mutation | Result |
|---|---|---|
| 7 | `blocked` branch's two call sites → 3-arg `_stratum_groups` | both new `blocked` tests FAIL |
| 7b | **only** the message-construction call site | `..._names_the_strata_when_an_arm_is_empty` FAILS alone — the two tests isolate the two sites |
| 8 | drop `axis not in axes or` | `..._is_not_ordered_against_anything` FAILS with the `ValueError` |

**Ruling accepted on `spec-defects.md`:** not written there (gitignored, does not survive the
merge). My reachability argument did double duty as "nothing ships broken" and "no record is owed",
and only the first follows. Task 14 owns the decision, with `reference.md` § Clustered units — where
a reader meets the indivisibility promise — as the place it would go.

**Final state: 1605 passed + 2 xfailed**, `ruff check` and `mypy` green.
