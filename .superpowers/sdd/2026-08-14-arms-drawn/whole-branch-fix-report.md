# Whole-branch review: closing the five findings on `h3c2-arms-drawn`

All five landed. `uv run pytest` 1632 passed / 2 xfailed, `ruff check .` and `mypy` clean.
`ruff format .` was not run.

## 1 — the clustered drawn allocation, asserted end to end (Important)

`tests/test_cli.py::test_a_clustered_drawn_axis_keeps_every_cluster_whole_end_to_end`.
24 units in 4 equal clusters of 6, `cluster_by: site`, `assign.arm.method: random` with a
pinned seed, run through a real `command_run`, asserting `allocation.json`'s arms leave
every cluster whole.

What it asserts, and why in that form:

- **Wholeness, not identity.** No site is asserted to draw a named arm — that is
  `units.assignment_for`'s to pin, and an arm-label assertion here would move with any
  unrelated change to the design digest. The discriminating assertion is "no site carries
  two arms".
- **Non-vacuity.** Both arms are asserted at 12 units, so an allocation that put everything
  on one side cannot satisfy the wholeness check trivially.
- **A size assertion alone proves nothing here**, which is why the cluster sizes are equal:
  whole-cluster apportionment and a per-unit shuffle both give 12/12 over this roster.
- `random`, not `blocked`: `E-DATA-ASSIGN-BLOCKED-CLUSTER` refuses `blocked` beside any
  `cluster_by`, so `random` is the only drawn method that reaches this path.

**Mutation (applied, not reasoned about):** `clusters` → `None` at `cli.command_run`'s
`_resolved_group_axes` call. Test FAILED, reporting all four sites as
`['control', 'treatment']`. `__pycache__` cleared, reverted, test PASSES — verified by
re-running, not by `git status`.

The two normative claims this now wires: `experimental-designs.md` § Mistakes core prevents
("a declared `cluster_by` makes clusters indivisible in every partition core computes") and
`reference.md` § Clustered units ("core computed the partition, so core keeps it indivisible").

## 2 — the stale unreachability claim (Important)

`units._assign_constant_columns`. The gate is unchanged; its justification is. It claimed
every config reaching `run` has `method: by_attribute` "since `random`/`blocked` … are
refused at `validate` first — so this gate loses no coverage a shipped run could reach",
which was true at the fork point and false after the retirement. The replacement states the
inversion: the gate went from redundant to load-bearing, because every drawn design now
reaches this function, and this gate is the only thing between such a design and an
`E-DATA-ASSIGN-VARIES` over a column its declaration never named and its draw never reads.

## 3 — the docstring citing a deleted § Validation row (Important)

`validate._check_assign`'s `by_attribute` paragraph cited *Assignment method isn't drawn*,
which was `E-DATA-ASSIGN-DRAWN`'s row and is gone. Rewritten to what the `elif` chain
actually is now: a partition of which of a block's fields mean what, not a refusal.
**`from` is the only field a draw does not read** — a first draft of this rewrite put
`levels` beside it, which is false: `levels` is read under a draw by *Ratio names levels*,
by *Every arm draws units*, and by `assignment_for`'s own `zip(levels, sizes)`. It means
*the set of arms the apportionment fills* there and *the set the column's values must
equal* under `by_attribute` — a different meaning, not an absence, which is what the
original text got right. `ratio` and `stratify_by` are likewise read under a draw, by that
branch's own rows. The second half (absent/out-of-enum method → *Assignment names a
method*) is unchanged, still true. The retirement itself is not restated: the same docstring already covers it where the
drawn branch is introduced.

`grep -rn "isn't drawn" docs/ src/ tests/` now matches only two historical files under
`docs/superpowers/` (the slice plan and its design spec), which record what the plan said
rather than making a live claim.

## 4 — a wrongly-typed `assign.<axis>.seed` (Important)

**Minted `E-DATA-ASSIGN-SEED`.** The argument for minting rather than broadening: every code
in this family owns exactly one field's value space — `E-DATA-ASSIGN-RATIO` owns `ratio`'s,
`E-DATA-ASSIGN-BLOCK-SIZE` owns `block_size`'s, the `STRATIFY-*` trio own `stratify_by`'s,
`E-DATA-ASSIGN-UNKNOWN` owns `from`'s name and type — and `seed` was the one field of a drawn
block with no code at all. Broadening `E-DATA-ASSIGN-NO-DRAW` would be the wrong home twice
over: that code is about fields that mean *nothing* under `by_attribute`, and a `seed` under
a drawn method means a great deal. `E-SWEEP-SAMPLE-INVALID`'s refusal of the sibling
`sweep.sample.seed` is the precedent for refusing at all, not for reusing a neighbour's code.

Documents first, then the check:

- **Registry row** — `reference.md` § Errors `validate` reports, inserted in the table's
  alphabetical position between `E-DATA-ASSIGN-RATIO` and `E-DATA-ASSIGN-STRATIFY-FORWARD`.
- **§ Validation row** — *Assignment seed is auto or pinned*, after *Blocked draw excludes
  clustering*.
- **§ What `auto` derives from** gained the converse of "an omitted `seed` is `auto`, not an
  error": a *present* seed must be `auto` or an integer, with both codes named.

The check sits in the drawn branch **before** *Every arm draws units*, so it falls inside
`findings_before_block`'s gate — a block reported here is not then drawn from the seed just
refused. An absent key and an explicit `null` are both `auto`, the module's convention;
`bool` is refused, matching `assign_seed_for`'s own exclusion.

Tests: `tests/test_validate.py` refuses `"1234"`, `1.5`, `True`, `False`, `[11]`, `{n: 11}`
under `random` and under `blocked`, with an exact-set assertion and a path/message check; the
can-fail control accepts absent / `auto` / `null` / `11` / `0` (a falsy but legal pin, which
a truthiness read would wrongly reject).

**The `bool` exclusion is now asserted**: `tests/test_units.py::test_a_boolean_seed_is_not_a_pin_and_derives`.
**Mutation (applied):** removing `not isinstance(seed, bool)` from `assign_seed_for` — test
FAILED (`seed: True` returned `1`); `__pycache__` cleared, reverted, PASSES.

**Adjacent gap seen and deliberately left:** `seed` is in `envelope.ASSIGN_AXIS_KEYS`, so a
`seed` declared beside `method: by_attribute` earns no finding at all — it is accepted and
ignored. Extending *Ratio and strata need a draw* to cover it is a separate decision (and
one to weigh against what § The one config file's expansion shows), pinned as scope by
`test_a_wrongly_typed_seed_under_by_attribute_is_not_this_row`.

## 5 — the comment describing a consequence that no longer happens (Minor)

`validate.py`'s duplicate-level discussion. Fixed the comment, not the code — the shape is
unreachable through a config, `E-SWEEP-LEVEL-DUPLICATE` refuses it. The comment now names
**both** outcomes rather than swapping one wrong claim for another, because `by_attribute`'s
is still the original one: `arms_of` hands both conditions the same units (`{control} ==
{control}`) and two condition directories come out byte-identical. Under a draw there is no
column to agree with itself — `assignment_for` keys `members` by level, so the second
`control` slice lands on the first key rather than beside it.

**Both drawn methods were run rather than reasoned about**, on a 12-unit roster with
`levels: [control, treatment, control]` and a pinned seed:

| Path | `members` | Total |
|---|---|---|
| `random`, unclustered | `control: 4`, `treatment: 4` | 8 of 12 — units vanish |
| `random`, clustered | `control: 3`, `treatment: 3` | 6 of 12 — the whole-cluster buckets zip into the same duplicate key |
| `blocked` | `control: 8`, `treatment: 4` | 12 — `_blocked_draw` extends per-level lists, so nothing vanishes and `control` is drawn twice the ratio it declared |

The comment names all three. An earlier draft said only "overwrites (`random`) or extends
(`blocked`)", which understated the clustered loss and left `blocked`'s oversized arm
unnamed.

## Row-insertion sweep

Two 2-column tables gained one row each. Checked, not assumed:

- `_check_assign`'s docstring says *Allocation strata survive clustering* is "one of the two
  rows here needing a roster" and *Every arm draws units* is "the other roster-needing row"
  and "the last thing the drawn branch does". The new row is declaration-only and is checked
  before the draw, so all three phrases stay true.
- "`method: by_attribute`'s three rows" is unaffected — the insertion is in the drawn branch.
- No count phrase anywhere counts either table's rows — swept across all four documents and
  `CLAUDE.md` for "N checks/rows/codes" and for a § Validation/§ Errors mention within 80
  characters of one of those nouns; nothing matched. The § Validation table's rows are
  referenced by name, never by position.
- Mechanical pass over `reference.md`: every `#anchor` resolves, no duplicate heading anchor,
  every table row matches its header's column count, no trailing whitespace, tab, or
  invisible unicode (fenced blocks skipped throughout).

## Concerns

- **What the new end-to-end test cannot see.** It reads `allocation.json`, not what each
  condition's execution actually received. A break that wrote a correct allocation and then
  narrowed the per-condition rosters wrongly would survive it. `command_run` realizes the
  plan once and hands the same object to both consumers
  (`test_one_plan_per_axis_is_realized_once_and_both_consumers_get_that_same_plan` pins that
  seam), which is why the two agree today — but the agreement is pinned at the seam, not at
  the clustered draw's own output.
- The `by_attribute` seed gap named under item 4 is open by choice, not oversight.
