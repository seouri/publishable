# SDD ledger — plan: docs/superpowers/plans/2026-08-18-unpaired-contrasts.md

**Spec:** `docs/superpowers/specs/2026-08-18-unpaired-contrasts-design.md`, plus its
**§ Corrections against the code** appended during planning — **twelve of them, the most any plan
author here has found.** **Scoping:** `docs/superpowers/H4c-SCOPING.md`, dated 2026-08-18 and pinned
to `051600c` — **22 tasks against the charter's 12**, the sixth consecutive re-scope to move up.

**Branch:** `h4c-unpaired-contrasts`, from `main` at `e40a219`.
**Baseline, measured in the foreground at `c0849a1`:** 2200 passed, 1 skipped, 2 xfailed; `ruff
check`, `ruff format --check` (80 files), `mypy` (45 source files) all clean.

**Execution order, from the plan:** 1 → 2 → 3 → **21** → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 →
13 (+17a) → 14 → 16 → **15 + 17b + 18 as one commit** → 19 → 20 → 22. **22 tasks, 20 commits** —
task 17 has none of its own. The order is **not numeric** and every departure is argued in the plan.

## What this slice is worth, stated before it starts

**Zero configs unblocked.** An unpaired contrast requires a declared `sweep.groups` axis, and the
nine configs' two shared roster blocks declare `allocation: within` with `groups: []` — verified by
sweep with a can-fail control. **No-remaining-core-side-blocker stays six** and **executable stays
three**, measured 2026-08-18 against `051600c`.

What it buys instead: **specification integrity** — § Statistical reporting names unpaired
constructions in the present tense that do not exist, and the `_clustered` suffix rule specifies two
more; the **gate five `spec-defects.md` filings are queued behind**; and the removal of **the last
hard-coded claim in the contrast record**, `"paired": True` written unconditionally at both branches.

Recording it first because H4b-1's retirement commit rounded a refusal-count into an execution-count
and **failed both review verdicts**, and on H4b-2 a *correction* to a report inverted the same two
numbers **and** named a retired refusal as live. The numbers do not move. Nothing here may say they do.

## Pre-flight conflict scan

### Shared files, by task, in execution order

| File | Tasks |
|---|---|
| `docs/reference.md` | 1, 2, 3, 9, 16, 19 |
| `src/publishable/stats.py` | 4, 5, 6, 7, 8, 19 |
| `src/publishable/cli.py` | 10, 13, 14, 15, 19 |
| `src/publishable/correction.py` | 11, 12, 19 |
| `src/publishable/validate.py` | 9, 16, 18, 19 |
| `tests/test_stats.py` | 4, 5, 6, 7, 8 |
| `tests/test_cli.py` | 3, 21, 10, 13, 14, 16, 18 |
| `tests/test_correction.py` | 11, 12 |
| `tests/test_validate.py` | 9, 16, 18 |
| `docs/superpowers/spec-defects.md` | 20 |
| `docs/feasibility-llm-growth-studies.md` | 22 |

No two tasks create the same file. Every shared file is modify-after-modify, serialized by the
per-task commit boundary and sequential dispatch.

### Pairwise: what one produces against what the next consumes

| Pair | Produced → consumed | Found |
|---|---|---|
| 1, 2 → 4-8, 10, 14 | the four `method` spellings and the record shape → the code that emits them | **Two of the four spellings exist nowhere in the four documents today.** A record key code writes and no document names is the pair `CLAUDE.md` says to grep for, and H4b-1 had to mint a whole vocabulary for exactly this reason |
| 21 → 4-20 | the regression literals → every task that can move a *paired* contrast | **The reason 21 runs fourth rather than last.** Its literals were captured at `e40a219` and written into the brief, so the pin **guards** the slice instead of reporting on it. Deriving `paired` is precisely the change that can silently move every existing paired contrast |
| 4 → 7 | `_sample_variance` → the CR1 variance extracted from `t_over_units_clustered` | Spec correction 2: `welch_t_over_units_clustered` **cannot "follow"** its sibling, which returns an `Interval`; a Welch form needs each side's variance *and* cluster count, so the machinery is **extracted** rather than called |
| 9 → 13 | the shared pairing predicate → its second caller | Spec correction 5: decision 7's predicate was **assigned to no task**, and 13 needs it before it exists. Task 9 mints it |
| 11 → 12 | `Member.sides` → `_corrected_bounds`' arms | **Five *t* arms plus the unchanged `pool` arm — six return paths**, counted rather than carried. `correction.py` is a **second production call site for the contrast *t* family that no charter named** |
| 10, 13 → 15+17b+18 | the unpaired key path and the derived `paired` → the retirement | The refusal cannot retire until every cell it stood in for exists, or a cell publishes a number from a construction nobody wrote |
| 2 → 13 | `n_paired` **absent, not null** → absence-tolerance in the readers | **The first conditional write of `n_paired` in the codebase.** `0` already means *pairing failed* and is live-pinned, so absence is the only free encoding |
| all → 15+17b+18 | every test asserting **alongside** `E-DATA-ALLOCATION-CONTRAST` | Makes the retirement a one-line deletion per test. If a test resists, something was built wrong |

### Per-task self-agreement — twelve disagreements, all appended to the spec

The plan author checked each task against the code rather than against the spec alone and found
**twelve** disagreements, appended to the spec as § Corrections against the code with its body
untouched. Three change what a task ships rather than how:

- **`W-STATS-CONTRAST-THIN` has a second emit site, at `validate`**, whose message asserts "the run
  counts `n_paired` over the two sides' completed units" — **false after decision 5**. The spec's
  decision 6 quotes only the run-side row. This is § Errors' one-row-per-code rule firing before
  execution began: a diagnostic's unit of work is every site that raises *or reports* it.
- **§ Allocation's example metric `r` is derived**, so the spec's task 3 repair as written would ship
  a record decision 8 forbids. Changed to `abs_error`.
- **`_groups_cluster_*`'s per-arm cluster counts are 3 and 3** — the "both 3" shape `CLAUDE.md` names
  as a documented unfailable fixture — and § 6's second pin uses that fixture. Task 18 builds its own
  roster at 3/4.

**Two mutations are recorded blind with grounds, not prescribed**: `_corrected_bounds`' arm **order**
is unobservable because mutual exclusion makes it so, and the discriminating fixture **cannot be
built** — its protection is the exactly-one refusal, pinned in task 11; and the degenerate-draw rule
across two independent draws was **undefined**, ruled **AND** rather than OR because one constant side
still leaves the difference varying.

**Ruling: the disposition is right.** Across the two preceding slices nine mutations were claimed
blind — **one was overturned by a reviewer with a one-line fixture change**, one was provably
unbuildable, the rest held. Naming one blind *in the plan*, with grounds and with the fixture that
would catch it, is the claim being checked before it is trusted. **Cost if wrong:** a behaviour left
unpinned that a nameable fixture could have pinned, which is why each is recorded with its fixture.

## Rulings taken before execution

**Ruling: dispatch in four batches on the plan's own seams.** 1/2/3/21 are the documents plus the
guarding regression pin; 4-8 the six constructions; 9-13 the refusal, the key path, `Member`'s third
kind and the derived `paired`; 14/16/15+17b+18/19/20/22 the selection, the thin warning, the
retirement and the residue. Each batch gets one implementer, one opus task review, and a scoped
re-review of the fixes. **Cost if wrong:** a defect crosses a batch boundary and is caught by the
whole-branch review instead of a task review — which is what the whole-branch review is for, and
which is exactly how H4b-2's Critical was found.

**Ruling: three interval literals are `CAPTURE-AND-PASTE`, and that is correct rather than a gap.**
The two unpaired percentile spellings and the unpaired clustered *t* half-width name constructions
that **do not exist** at `e40a219`, so any literal in the plan would be invented. Each carries a
capture step in the same commit and a stated constraint the captured number must satisfy. **Cost if
wrong:** a captured number records the implementation rather than the mathematics — which is why the
constraint is stated in the plan and must be checked against it, not merely recorded.

**Ruling: the two discriminating fixtures are load-bearing and may not be weakened.** The spec
records that its **first draft was unfailable** — a min-df mutant landed **0.1%** from correct because
one side dominated the Welch variance — and was rebalanced to n=5/25 with s²/n=1 each, so both
fixtures now separate every candidate by **>4%**, with the integer cluster counts (3, 4) the strongest
discriminator. The plan author reproduced **every literal in both fixtures** against the shipped
`_t_critical`. **Cost if wrong:** the whole slice is statistics, and this repo has found sixteen
checks that could not fail in statistics alone.
