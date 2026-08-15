# Task 10 report: `blocked`, `block_size`, and the whole-multiple rule

## What was built

`units.assignment_for` now realizes `method: blocked`, alongside `random`. The resolved
roster is cut into consecutive chunks of `assign.<axis>.block_size` units (`"auto"`, or any
declared value that isn't a plain `int`, resolves to twice `ratio`'s sum — `2 * len(levels)`
when `ratio` is `{}`). Each chunk — including a final one shorter than `block_size` when the
roster doesn't divide evenly — is apportioned by the existing `_apportion` Hamilton rule,
turned into a label list, shuffled in place with one `random.Random(assign_seed_for(...))`
instance whose state carries from block to block, then zipped onto the chunk's units in
roster order. Coverage/non-emptiness is checked over the *whole* roster (a level empty in one
block but present in another is fine); a level empty across every block raises
`E-DATA-ASSIGN-LEVELS`, the same code and construction `random`'s zero-size arm uses.
`blocked` beside a declared `cluster_by` raises `NotImplementedError` (task 11 owns the real
`E-DATA-ASSIGN-BLOCKED-CLUSTER` validate-time refusal; this build does not implement the
combination at all), and a non-empty `stratify_by` raises the same way `random`'s does
(task 12).

`validate._check_assign` gained the whole-multiple refusal, *Block size fills the arms*: for
`method: blocked` with a declared `block_size` other than the literal `"auto"`, `ratio`'s sum
(falling back to the level count for an absent/empty/malformed `ratio` — that shape fault is
`E-DATA-ASSIGN-RATIO`'s to report, not re-derived here) must divide `block_size` evenly
(`math.isclose` rather than a bare `%`, since `ratio` values may be `float`). The same code
also refuses a `block_size` that is not a positive `int` at all (`0`, negative, `2.5`,
`"four"`, `null`) — added after the initial pass, once review surfaced that `units.py`'s
`range(0, len(keys), block_size)` would otherwise crash on `0` or silently produce no blocks
on a negative value with no diagnostic. Mints `E-DATA-ASSIGN-BLOCK-SIZE`, reported beside
`E-DATA-ASSIGN-DRAWN` (both still fire for `blocked` until task 14 retires the latter).
Registered in `docs/reference.md` § Errors `validate` reports, inserted alphabetically before
`E-DATA-ASSIGN-DRAWN`. § Validation's *Block size fills the arms* row already existed
(pre-written by an earlier task) and needed no change.

`units.DRAWN_ASSIGN_METHODS`'s own branch inside `assignment_for`'s generic fallback was dead
code after this change (both its members are now handled in earlier branches, so nothing ever
reaches it already knowing which drawn method it is) — removed, along with the docstring
claims that depended on it, rather than left as untested unreachable code.

## Tests

`tests/test_units.py`:
- `test_a_blocked_draw_balances_within_every_whole_block` — 14 units, ratio `{}`, `block_size`
  auto = 4 (three whole blocks of 4 + a trailing 2, deliberately not a multiple of 4 — the
  fixture trap named in the brief, since `random` gives the identical 7/7 total over this same
  roster). Asserts exact membership plus explicit per-block 2/2 composition for every whole
  block and the trailing partial block's actual composition.
- `test_blocked_reads_the_roster_order_as_data` — same 14 units, only `u00` and `u05` swapped.
  Control: `random` at the same pinned seed gives the identical per-unit assignment for *this
  specific* swap (chosen so both units' positions land in `random`'s same arm-slice under its
  one whole-roster shuffle — `random` is not order-blind in general, only for a swap confined
  to one arm-slice's positions, which is what makes the control meaningful rather than trivial).
  `blocked` gives a different assignment: the swap moves each unit into a different block, so
  the two trade arms while every other unit is unmoved.
- `test_auto_block_size_is_twice_the_ratio_sum` — two fixtures (`{control:1,treatment:2}` over
  6 units, and `ratio: {}` over 4), each a roster exactly one `auto`-block long, chosen because
  a mutant `auto = sum` produces the *same total counts* as the real formula at that roster
  size (apportionment over an exact multiple is additive) — only exact per-unit membership,
  which depends on whether the seeded shuffle consumes one block or two, distinguishes them.

`tests/test_validate.py`:
- `test_an_explicit_block_size_must_be_a_whole_multiple_of_the_ratio_sum` — `block_size: 3`
  with `ratio` summing to 2 is refused; the control, `block_size: 4`, is not (only
  `E-DATA-ASSIGN-DRAWN` fires). Both the `write_config`/`_error_codes` path and a direct
  `_check_assign` call are exercised.
- `test_an_auto_block_size_is_never_refused_for_not_dividing_the_ratio_sum` (extra, not in the
  brief's four) — `block_size: "auto"` never reaches the whole-multiple arithmetic.

Two pre-existing tests were removed because their premise — "`blocked` still raises
`NotImplementedError`" — is now false: `test_assignment_for_refuses_a_drawn_method_rather_than_reading_a_column`
in `tests/test_units.py` (parametrized only over `DRAWN_ASSIGN_METHODS` minus `random`, which
was `blocked` alone) and
`test_resolved_group_axes_raises_rather_than_reading_a_column_under_a_drawn_method` in
`tests/test_cli.py` (same premise, same method). Both docstrings already anticipated this,
saying `blocked` was "what remains — still task 10's."

## Mutation-proving

Applied, ran the discriminating test(s), confirmed FAIL, reverted (from a clean backup copy,
`__pycache__` deleted between steps), confirmed PASS — for all three prescribed mutations, plus
one on the validate-side check:

1. **Balance overall rather than per block** (one block covering the whole roster) — failed
   `test_a_blocked_draw_balances_within_every_whole_block` (per-block 2/2 assertions).
2. **Shuffle the roster before blocking** — failed all three `units.py` blocked tests
   (`balances_within_every_whole_block`, `reads_the_roster_order_as_data`,
   `auto_block_size_is_twice_the_ratio_sum`).
3. **`auto` as the ratio sum rather than twice it** — failed the same three tests.
4. (Not prescribed, done anyway) Disabling the `validate` whole-multiple comparison —
   failed `test_an_explicit_block_size_must_be_a_whole_multiple_of_the_ratio_sum`.

Full suite (`uv run pytest`), `uv run ruff check .`, and `uv run mypy` are green after every
revert and at the end.

## One thing to report, per the brief

**Appending a unit re-blocks rather than redraws — but the brief's own phrasing of the
mechanism ("block boundaries move relative to every earlier unit") is imprecise for an
append specifically, and I want to correct it rather than repeat it.** Verified against the
real implementation, pinned seed, 14 units grown to 15: the three whole blocks (positions
0-3, 4-7, 8-11) are position-identical between the two runs, consume the same number of
`rng.shuffle` calls over same-length label lists, and land on **identical** labels — only the
final partial block (12-13 growing to 12-14) re-draws, and it is the *only* unit whose arm
changes (`u12`, verified: `u00`, `u01`, ..., `u11` are unchanged; `u13` is unchanged too,
since it stays in the same, merely-longer, trailing block; only the newly-drawn `u12`-through-
new-unit block differs from before). So for a **pinned** seed, appending at the end leaves
every whole block's membership and labels untouched, and only the trailing partial block
re-draws — a narrower and more precise claim than "every earlier unit can change." It is
*insertion or reordering in the middle* of the roster, not appending at the end, that shifts
which units share which block for units that never moved rows. Separately, under the
*derived* (`"auto"`) seed — what most runs carry — appending changes `units_hash(roster)`,
which changes the seed itself (§ Allocation already says a changed roster re-randomizes), so
in that common case *every* block re-permutes and any unit can change arms, regardless of
this position argument. I did not write a test asserting "adding a unit changes only that
unit's arm" — under the derived seed it's false outright, and even under a pinned seed the
narrower true claim ("only the trailing partial block") is not what the brief's directive
was guarding against, so I left it as prose here rather than as an assertion.

## Concerns

- **The brief's control premise is only true for a hand-picked swap, and I want to flag that
  explicitly rather than let it stand as a general claim.** § Where units come from calls
  `blocked` "the one declaration that reads the order as data," implying by contrast that
  `random` does not. As implemented (and as it was already implemented before this task —
  `random`'s algorithm is untouched), `random` shuffles a list built from the roster's own
  order and slices it, so it *is* order-sensitive in general: a full reversal of the 14-unit
  fixture at the same pinned seed moves several units across arms (verified). The control in
  `test_blocked_reads_the_roster_order_as_data` holds only because the swapped pair (`u00`,
  `u05`) was chosen so both units' *original positions* land in the same arm-slice under that
  seed's shuffle permutation — a swap confined to one slice doesn't change which positions
  feed that slice's content, so the set of units in each arm is unaffected (only their
  position *within* the tuple would move, which the test compares against with a `dict`, not
  a tuple, for exactly this reason). A swap crossing the slice boundary would move `random`'s
  membership too. Under the *derived* seed, `random` is order-sensitive a second way,
  independent of the shuffle: `assign_seed_for`'s `"auto"` path mixes in `units_hash(roster)`,
  which covers the roster in resolved order, so a reordered roster draws with a different seed
  outright. None of this is a code defect — `random`'s behavior is task 8/9's, unchanged here
  — but the document's phrasing reads as though `random` ignores order unconditionally, which
  it does not; worth a look for `docs/superpowers/spec-defects.md` rather than something I
  changed in this task.
- I minted the error code name `E-DATA-ASSIGN-BLOCK-SIZE` myself; neither the task brief nor
  the plan/design-spec docs name it explicitly, though the § Validation row *Block size fills
  the arms* (pre-existing) made the check's existence unambiguous. Followed the project's
  existing `E-DATA-ASSIGN-<SUFFIX>` convention and the table's alphabetical-within-family sort.
- `assignment_for`'s `blocked` branch does not itself re-validate `block_size` at all — it
  trusts `validate`. Caught in review before this report was finalized: an un-validated
  `block_size` of `0` reaches `range(0, len(keys), 0)` and raises a bare `ValueError` (not a
  `PublishableError`), and a negative one silently produces zero blocks (every arm ends up
  empty, refused as `E-DATA-ASSIGN-LEVELS` — the right code by accident, not by design, and
  with a message that describes the wrong fault). I closed this at the `validate` layer instead
  of guarding `units.py`: `E-DATA-ASSIGN-BLOCK-SIZE` now also refuses a non-positive or
  non-`int`, non-`"auto"` `block_size` (folded into the same code, mirroring how
  `E-DATA-ASSIGN-RATIO` absorbs `ratio`'s non-mapping and non-positive shapes), with a
  parametrized mutation-proved test (`test_a_non_positive_or_non_int_block_size_is_refused`,
  `[0, -2, 2.5, "four", None, True]`; `True` is deliberate — `True != "auto"` and
  `isinstance(True, int)` both hold, so the guard excludes `bool` explicitly, and a second
  test, `test_a_bool_block_size_is_refused_even_when_its_int_value_would_divide_evenly`, uses
  a `ratio` summing to 1 so `int(True) == 1` *would* be a legal whole multiple, isolating that
  exclusion from "1 doesn't divide 2 either"). The type/positivity check is ordered *before*
  the whole-multiple arithmetic and its `ratio_sum` — a first pass had it nested inside
  `if ratio_sum > 0:`, which is always true on every reachable path (`_usable_ratio_share`
  requires a positive share, `_declared_levels` a non-empty level list) and so was a dead
  gate that read as live; reordering removes the ambiguity rather than leaving a condition
  whose truth nothing states. `units.py` itself is still reachable directly with a bad
  `block_size` bypassing `validate` — the same reachability gap already documented and
  accepted for `random`+`ratio` (task 8's report), not a new one, and not fixed here for the
  same reason task 8 didn't fix its sibling: `validate` is the gate `run` actually goes
  through.
- `tests/test_cli.py` has no CLI-level (`_resolved_group_axes`/`build_allocation_document`)
  coverage of `method: random` either — the seam I removed a test from was already the *only*
  CLI-level assign-drawing test in that file, and it tested the obsolete "still raises" premise
  rather than a real draw. I did not add a `blocked`-drawing CLI test to replace it: the task
  brief scopes tests to `tests/test_units.py`/`tests/test_validate.py`, and adding one for
  `blocked` alone without a symmetric one for `random` would leave the asymmetry rather than
  close it. Flagging it rather than silently doing nothing. **Coordinator review ruled the seam
  matters more than the symmetry — addressed, see below.**

## Review fix round (coordinator's four items)

**Adjudication 1 (order test tested the wrong property) — fixed.** Verified empirically: at a
pinned seed, `random` and `blocked` are *both* pure functions of position → arm (200 random
reorderings leave each method's own position→arm vector bit-identical; each is invariant under
exactly 42 of the 91 pairwise position swaps over the 14-unit fixture) — equally
order-sensitive mechanically, only the *map* differs. Rewrote
`test_blocked_reads_the_roster_order_as_data`'s docstring to say that plainly, credit
`test_a_blocked_draw_balances_within_every_whole_block` as the real demonstration of the
property specific to `blocked` (local balance in every consecutive window), and narrow the
mutation claim (see Minor, below). No `spec-defects.md` entry, per the ruling: the false
mechanism claim was the brief's, already corrected in-thread, and `reference.md`'s own next
sentence already concedes general order-sensitivity.

**Adjudication 2 (append mechanism) — no code or doc change needed**, the report's existing
correction already matched what review confirmed independently (five appends, pinned seed,
only the trailing-partial-block unit ever changes).

**Important 1 (two mutations survived) — both fixed, both mutation-proved.**
- Added `test_a_declared_block_size_is_honoured_rather_than_ignored_for_auto`: 12 units, `ratio:
  {}` (`auto` = 4), explicit `block_size: 6` — both legal whole multiples of the ratio sum (2),
  drawing against genuinely different block boundaries. Mutation (`block_size = 2 * ratio_sum`
  unconditionally, discarding the declared value) fails this test and only this test; reverted,
  confirmed green.
- Added `test_a_blocked_level_empty_in_one_block_is_fine_if_another_block_covers_it`: 7 units,
  3 levels, equal ratio (`auto` = 6) — one full block of 6 (`_apportion` gives exact 2/2/2) plus
  a trailing block of 1, whose three-way tie always breaks to the first-declared level
  (`_apportion`'s own declared-order tie-break), so the trailing block deterministically
  apportions `[1, 0, 0]` every seed: two levels are empty *in that block* but non-empty overall.
  Mutation (raise per-block rather than over the whole roster) fails this test and only this
  test; reverted, confirmed green.

**Important 2 (registry row's skip clause overclaims) — fixed.** The type/positivity half of
the check is unconditional (checked before `_declared_levels` runs at all), and only the
whole-multiple-arithmetic half is skipped when `levels` don't resolve. Rewrote the
`E-DATA-ASSIGN-BLOCK-SIZE` registry row in two explicit parts so the skip clause now scopes to
the second part only, matching the code exactly.

**Important 3 (tighten to per-level shares) — implemented and mutation-proved, then corrected
again in a second review pass (see below) after an initial "subsumes" claim turned out to be
false.** Replaced the sum-divisibility check with a per-level one: for each declared level,
`block_size × that level's share of ratio` must be a whole number. Refuses `ratio: {a: 0.5, b:
0.5}` at `block_size: 1` (sum divides evenly; each level's own share, 0.5, does not) and `{a:
1.5, b: 2.5}` at `block_size: 4` (same shape). Added
`test_the_whole_multiple_rule_checks_each_levels_own_share_not_just_the_sum`, parametrized over
both examples; mutation (reverting to the sum-only check) fails both parametrizations, reverted,
confirmed green. Updated `docs/reference.md` § Allocation's prose and § Validation's *Block
size fills the arms* row to state the per-level rule rather than the sum rule. Also caught in
the same pass and fixed: the type/positivity check had been nested inside `if ratio_sum > 0:`, a
gate that is always true on every reachable path and so was dead but read as live — moved the
check above the whole-multiple arithmetic entirely. Replaced
`test_a_bool_block_size_is_refused_even_when_its_int_value_would_divide_evenly` (whose isolating
fixture became impossible to construct once the per-level rule closed the loophole it relied
on — no two-level, both-positive ratio ever makes `block_size: 1` legal) with
`test_a_bool_block_size_is_refused_by_the_type_check_not_by_coincidence`, which isolates the
`bool` exclusion by asserting on which branch's message text fired rather than by constructing
an artificial "would-be-legal" ratio; mutation (removing the explicit `bool` check) fails this
test with the share-check's message instead, reverted, confirmed green.

**Important 4 (restore CLI seam) — added `test_resolved_group_axes_draws_a_blocked_allocation`**
in `tests/test_cli.py`: a `blocked` draw through `_resolved_group_axes`, reusing the same
14-unit, pinned-seed fixture as `test_a_blocked_draw_balances_within_every_whole_block` so a
result differing between the two call sites would surface as a real divergence rather than a
second independent computation.

**Minor (order test's mutation claim overclaimed) — fixed.** Verified: the order test fails
against a mutant that shuffles the whole roster with the *same*, continuing `rng` before
blocking, but **survives** a mutant that shuffles with a **separate**, freshly-seeded
`random.Random(seed)` first while leaving the block-drawing `rng` untouched (confirmed
empirically — `u00`/`u05` land in the same post-shuffle grouping under that variant).
`test_a_blocked_draw_balances_within_every_whole_block` catches both variants. Narrowed the
order test's docstring to say precisely this rather than claim it catches "a mutant that
shuffled the whole roster before blocking" unconditionally.

Full suite (`uv run pytest`), `uv run ruff check .`, and `uv run mypy` are green after every
mutation/revert in this round and at the end: 1568 passed, 2 xfailed.

## Second review pass (advisor caught two blockers in the first fix round's own new code/prose)

**Blocker 1 — `auto`'s `2 * ratio_sum` crashes for a fractional `ratio`, with no `block_size`
declared at all.** `ratio: {control: 0.5, treatment: 0.5}` makes `ratio_sum = 1.0` (a `float`,
since `_usable_ratio_share` accepts any finite positive float), so `auto` resolved to `2.0`,
and `range(0, len(keys), 2.0)` raises a bare `TypeError`, not a `PublishableError` — reachable
by a config that validates completely clean, since `validate`'s new check returns immediately
on `block_size == "auto"` and never inspects what `auto` will actually resolve to. Fixed:
`else max(1, round(2 * ratio_sum))` in `units.py`, always a positive `int`. `max(1, ...)` is a
defensive floor for a pathological `ratio_sum` under 0.5, not expected in practice. This does
**not** make `auto` satisfy the per-level whole-share rule for every `ratio` — no finite
`block_size` can, for shares that aren't commensurate rationals (`{a: 0.25, b: 0.75}` is a
counterexample even after the fix: `auto` is 2, and neither level's own share, 0.5 or 1.5, is
whole) — so `auto` remains an unchecked convenience default, and the per-block draw tolerates
the shortfall the same way `_apportion`'s largest-remainder rule already tolerates one for an
unclustered `random` draw whose `ratio` doesn't divide the roster evenly, rather than raising.
**This "unchecked" characterization is superseded in the third pass below**, which extends the
whole-share check to the `auto`-resolved value too rather than leaving it exempt — recorded
here rather than edited away, so the report reads in the order the work actually happened.
Added `test_auto_block_size_is_a_valid_int_even_for_a_fractional_ratio` (asserts no raise and
full roster coverage); mutation (reverting to the bare `2 * ratio_sum`) reproduces the exact
`TypeError` and fails only this test, reverted, confirmed green.

**Blocker 2 — three prose claims I wrote in the first fix round asserting an ordering between
the sum check and the per-level check were false in both directions.** `ratio: {a: 2, b: 2}`
(sum 4) with `block_size: 2`: the sum does *not* divide `block_size` evenly (the old check
would have refused it), yet each level's own per-block share, `2 × 2 / 4 = 1`, is whole and
`_apportion(2, [2, 2]) == [1, 1]` fills it exactly — so the per-level check is not merely a
tightening of the sum check; it accepts things the sum check would have refused, as well as
refusing things the sum check would have accepted. Corrected everywhere this claim appeared:
`validate.py`'s inline comment (was "subsumes ... for integer ratios," which `{2, 2}` itself
refutes — the true coincidence condition is `ratio: {}` or every weight exactly `1`, not merely
"integer"), `reference.md` § Allocation ("a stricter requirement" → "a **different**
requirement ... neither implies the other," with both counterexamples), `reference.md`'s
registry row (same correction, plus the false "necessary for but not sufficient" wording), and
the error message's remedy clause (was "a whole multiple of `{ratio_sum}` *and* of every
level's own share of it" — the first half isn't required at all). Added
`test_a_block_size_the_sum_rule_would_wrongly_refuse_is_accepted` (the missing direction: a
case the sum rule refuses and the per-level rule accepts) beside the existing
`test_the_whole_multiple_rule_checks_each_levels_own_share_not_just_the_sum`, whose docstring
now names both directions explicitly. Mutation (reinstating the sum-only check) fails all
three of these tests together — the accept-side one and both parametrizations of the
refusal-side one — confirming neither direction was accidentally still covered by only one
test; reverted, confirmed green.

Also corrected in the same pass: the registry row's and § Allocation's claim that `auto`
"gives every level a whole share by construction" — false for the `{a: 0.25, b: 0.75}` case
above, corrected to state `auto` is exempt from the check rather than guaranteed to pass it.

Full suite, `ruff check .`, and `mypy` green after this pass too: 1570 passed, 2 xfailed.

## Third review pass (advisor caught two more, both in this round's own new prose)

**Blocker 1 — "the two checks coincide only where `ratio` is `{}`" was itself false.** `ratio:
{a: 1, b: 2}` (sum 3, the docs' own unequal example and this task's own
`test_auto_block_size_is_twice_the_ratio_sum` fixture) accepts the identical `block_size` set —
multiples of 3 — under both the sum rule and the per-level rule, and so does `{1, 1}`. The real
coincidence set is "every weight a whole number with no common factor," not `{}` alone, and
stating that precisely gains nothing a reader needs beyond the two counterexamples already
present. Dropped the "coincide only where…" clause everywhere it appeared —
`validate.py`'s comment, `reference.md` § Allocation, and the registry row — keeping only the
two verified counterexamples (`{2, 2}`/`block_size: 2` accepted despite failing the sum rule;
`{0.5, 0.5}`/`block_size: 1` refused despite passing it). Third round in a row this exact class
of sentence needed correcting; recorded so the pattern is visible rather than repeated a fourth
time.

**Blocker 2 — `auto` was declared "tolerant of a shortfall" that is total, not partial, for a
plausible ratio.** `ratio: {a: 0.33, b: 0.33, c: 0.34}` — an ordinary percentage split — makes
resolved `auto` equal to 2, and `_apportion(2, [0.33, 0.33, 0.34])` gives `[1, 0, 1]`: level `b`
gets zero units in *every* block, so it's zero overall, and `units.assignment_for` raises
`E-DATA-ASSIGN-LEVELS` on a config that validated completely clean — exactly the
validate-clean-then-fail shape Important 3 ruled must be closed, reached through the derived
value rather than a declared one. Chose the first of the advisor's two defensible options:
**extended the per-level whole-share check to the resolved `"auto"` value**, not just to an
explicit declaration. `validate._check_assign` now resolves `block_size` — the declared `int`
after its own type/positivity check, or `max(1, round(2 * ratio_sum))` for `"auto"`, mirroring
`units.py`'s own formula — once, and runs the identical per-level check against whichever it
is. The type/positivity half stays exclusive to a declared, non-`"auto"` value, since `"auto"`
is a positive `int` by construction. Replaced the two tests that had asserted `"auto"` was
exempt from the whole-share arithmetic
(`test_an_auto_block_size_is_never_refused_for_not_dividing_the_ratio_sum`, renamed to
`test_an_auto_block_size_is_not_exempt_from_the_type_check_but_usually_passes_the_share_one`
and rewritten to say what's actually true) with that test plus a new sibling,
`test_an_auto_block_size_can_still_be_refused_for_a_percentage_ratio`, which pins the
`{0.33, 0.33, 0.34}` case exactly. Mutation (reverting the extension so only an explicit value
is checked) fails the new sibling test specifically; reverted, confirmed green. Updated
`docs/reference.md` § Allocation and the registry row to match: `auto` is "checked the same way
an explicit value is, not exempted," and the registry row's two-part split now reads as
"type/positivity, declared-only" and "whole-share, declared-or-`auto`" rather than
"declared-only" and "exempt for `auto`." Also updated `units.py`'s own comment on the `auto`
formula, which had independently claimed `_apportion`'s tolerance covers this — true only for a
caller that bypasses `validate` entirely (still possible, and still relies on the same
largest-remainder tolerance and the same `E-DATA-ASSIGN-LEVELS` raise rather than a silent
misallocation), not true for the path `run` actually takes, which now stops at `validate` first.

Full suite, `ruff check .`, and `mypy` green after this pass too: 1571 passed, 2 xfailed.

## Fourth review pass (advisor caught a two-sources-of-truth defect, plus two cheap items)

**Blocker — `auto`'s formula existed independently in `units.py` and `validate.py`, pinned in
agreement by nothing.** The exact shape task 7's controller ruling already named for
`DRAWN_ASSIGN_METHODS` in this same slice: two copies of a value validate approves and the draw
uses, with nothing forcing them to agree. My own comment claimed the copy was deliberate
("`validate` does not depend on the draw"), which was simply false — `validate.py` already
imports several names from `units.py` (`DRAWN_ASSIGN_METHODS` among them), so the dependency
edge the comment denied already exists in the file. Extracted `units.auto_block_size(weights)
-> int` (`max(1, round(2 * sum(weights)))`, with the crash-guard and rounding from the previous
pass, now stated once) and imported it into `validate.py` rather than keeping a second literal.
Divergence is now inexpressible rather than merely untested: verified by temporarily changing
the formula's multiplier in `units.py` alone (3× instead of 2×) and confirming `validate.py`'s
own `block_size`/`whole_multiple_rule` tests still passed with no edit on that side — the two
sides moved together because there is only one side. Reverted. All pre-existing `auto` tests
(`test_auto_block_size_is_twice_the_ratio_sum`,
`test_auto_block_size_is_a_valid_int_even_for_a_fractional_ratio`,
`test_an_auto_block_size_can_still_be_refused_for_a_percentage_ratio`) still pass unchanged.

Also removed the `assert resolved_block_size is not None` mypy-narrowing hint the third pass
had added (flagged as a lesser, non-blocking concern, given the same pattern already exists
once in `correction.py`) — the extraction gave a cleaner way to reach the same type without a
runtime assertion: `block_size = resolved_block_size if resolved_block_size is not None else
auto_block_size(weights_for_block_size)`, a ternary rather than a statement that disappears
under `python -O`, covering the one remaining case (`declared_block_size == "auto"`) the outer
`if` doesn't already guarantee.

**Cheap item 1 — the report's second-pass Blocker 1 paragraph was left asserting something the
third pass had already reversed** ("`auto` remains an unchecked convenience default"). Added a
forward-pointing sentence rather than editing the earlier paragraph, so the report still reads
in the order the work happened.

**Cheap item 2 — the two inline schema comments** (`docs/reference.md` lines ~100 and ~1196,
`block_size: auto # blocked only; twice the ratio's sum, or twice the level count when ratio is
{}`) said nothing about the rounding or the fact that `auto` is checked like any other value,
where § Allocation's prose now says both. Appended `(rounded)` and `; checked like any
block_size` to both — the two inline comments were already near-duplicates of each other, kept
that way rather than diverging.

Full suite (1571 passed, 2 xfailed), `ruff check .`, and `mypy` green after this pass.

**Noted rather than fixed, per the advisor's own review of this pass**: the formula is now
single-sourced, but its *input* still isn't — `validate` builds `weights_for_block_size` via
`usable_ratio` (falling back to an equal-share list when the ratio's keys or values don't check
out) while `units.assignment_for` builds `weights` as `[ratio[level] for level in levels] if
isinstance(ratio, dict) and ratio` (no value check at all). For a `ratio` that is a non-empty
dict with matching keys but an unusable value (`{control: -1, treatment: 2}`), the two sides
would feed `auto_block_size` different weights. Every such `ratio` is already refused by
`E-DATA-ASSIGN-RATIO` before a run reaches `assignment_for`, so this is bounded-latent — the
same class, and symmetric with, the pre-existing `ratio[level]` `KeyError` gap task 8's report
already flagged for the `random` branch — not fixed here for the same reason that one wasn't.
