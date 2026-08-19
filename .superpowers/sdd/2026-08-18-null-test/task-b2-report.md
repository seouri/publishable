# Batch report: tasks 5+24, 6, 7, 8, 9

**Status: complete.** All tasks done, in the prescribed order (5+24 → 6 → 7 → 8 → 9), tasks 5+24 in
one commit as required, the rest each their own commit. Gates clean at HEAD.

## Commits

| Task | SHA | Subject |
|---|---|---|
| 5+24 | `5473585` | H4d tasks 5+24: E-STATS-NULLTEST-REPORTBY, and the report_by asymmetry converted to a limitation |
| 6 | `7aac5ad` | H4d task 6: statistics.null_test closed one level in, before its refusal retires |
| 7 | `4fcc89f` | H4d task 7: _check_null_test — the enum, the floor, and a shuffle over attributes union group axes |
| 8 | `610c9e5` | H4d task 8: E-STATS-NULLTEST-UNITS, claimed from its filing |
| 9 | `acc50cb` | H4d task 9: the derived shuffle level, its ambiguity refusal, and the report_by guard |

## Test summary

Baseline before this batch: 2280 passed, 1 skipped, 2 xfailed. Task 5+24 (docs only): unchanged.
Task 6: +3 → 2283. Task 7: +6 → 2289. Task 8: +1 → 2290. Task 9: +7 → 2297. **Final: 2297 passed,
1 skipped, 2 xfailed.** `ruff check .`, `ruff format --check .` (80 files, 0 to reformat), and
`mypy` (45 source files) all clean at HEAD.

Every prescribed mutation was run against the full, unfiltered suite and reverted by editing the
source back (never `git checkout --`), confirmed green by re-running afterward:

- **Task 6, step 5** (delete `"statistics.null_test.shuffle": str` from `LEAF_TYPES`): **BLIND**
  exactly as the brief predicted — full suite stayed at 2283/1/2, nothing failed. I then added the
  brief's own prescribed discriminating fixture (`{"shuffle": 5}` as a second case inside
  `test_a_wrong_typed_null_test_child_is_reported_by_the_envelope`) **permanently**, re-applied the
  mutation, and confirmed that new case failed (`E-CONFIG-KEY-UNKNOWN` instead of `E-CONFIG-TYPE`,
  1 failed/2282 passed). Reverted the envelope entry; re-ran, confirmed 2283/1/2. I read this as the
  brief instructing me to leave the discriminating case in place going forward — noted as a judgment
  call since the brief's literal step 5 wording could also be read as a throwaway probe.
- **Task 7, step 6** (`shuffle not in (declared | axes)` → `shuffle not in declared`): FAILED
  `test_a_shuffle_naming_a_group_axis_is_accepted` exactly as prescribed (1 failed/2288 passed).
  Reverted; re-ran, confirmed 2289/1/2.
- **Task 8, step 6** (add `return` after the `E-STATS-NULLTEST-UNITS` call): FAILED the fixture's
  `E-STATS-NULLTEST-N` assertion exactly as prescribed (1 failed/2289 passed). Reverted; re-ran,
  confirmed 2290/1/2.
- **Task 9, step 6(a)** (`if varying and constant:` → `if varying and not constant:`): failed the
  two tests the brief named — `test_the_null_test_level_is_ambiguous_when_some_clusters_vary_and_others_do_not`
  and `test_an_ambiguous_shuffle_level_is_refused` — **plus two more via `IndexError`**
  (`test_the_null_test_level_is_within_cluster...` and `test_a_unit_carrying_no_value_for...`, both
  crashing at `constant[0]` on an empty list). 4 failed/2293 passed. Per CLAUDE.md's "a mutation
  caught only by a crash is not a pin": here the two brief-named tests fail on real assertion
  mismatches, not crashes, so the discriminating pin holds independent of the bonus crashes — the
  crashes are collateral evidence, not the only proof. Reverted; re-ran, confirmed 2297/1/2.
- **Task 9, step 6(b)** (`return ("within_cluster" if varying else "whole_cluster"), None` →
  `return "within_cluster", None`): FAILED
  `test_the_null_test_level_is_whole_cluster_when_the_label_is_constant_inside_every_one` exactly as
  prescribed (1 failed/2296 passed). Reverted; re-ran, confirmed 2297/1/2.

## Ruling for task 6: the closed schema

`statistics.null_test` keeps its `"statistics.null_test": dict` `LEAF_TYPES` entry **and** gains
three children (`method: str`, `n: int`, `shuffle: str`) — the same both-a-leaf-and-a-container shape
`statistics.resample` already has, per the brief's own late-found trap and § Corrections' precedent.
`level` is deliberately absent from the envelope: it's derived from the roster and recorded, never
declared, so naming it in a config would be a config asserting a value core computes. Confirmed the
module comment (naming which blocks are "declared at their own key with the one outer type") no
longer lists `.null_test` there, and the sentence naming `resample` as closed-one-level-in now also
names `null_test` beside it — re-read the whole comment after editing, not just the touched
sentence, per CLAUDE.md's own instruction.

## Ruling for task 9: the closed schema's third check, and `null_test_level`'s three states

**What the closed schema admits and refuses (carried from task 7, extended by 8 and 9):** a mapping
`null_test` block with fixed keys `method`/`n`/`shuffle`; `method` must be `permutation`; `n` must
clear `stats.min_honest_permutations()` (20 at the default level); `shuffle` must name either a
declared `data.units.attributes` entry OR a declared `sweep.groups` axis name (the union is
load-bearing — a group-axis shuffle is the only p-value home that joins the correction family, so
scoping to attributes alone would refuse the shape the slice exists to serve); `data.units` must be
declared at all; `shuffle` must not name an attribute `statistics.report_by` also names; and, when a
`cluster_by` is declared and `shuffle` resolves to a legal attribute/axis, the roster's shuffle-level
must not be ambiguous.

**`null_test_level`'s three (four, counting `rows`) states and what each drives:**
- **`"rows"`** — no `cluster_by` declared at all. Not a third clustering answer; the absence of one.
  Drives nothing beyond itself: the level check only fires on `"ambiguous"`, so `"rows"` and the
  clustered-but-unambiguous states are both silently fine at `validate` time. (Task 13, out of this
  batch's scope, is where `"rows"` vs `"within_cluster"` vs `"whole_cluster"` drives which
  permutation construction actually runs.)
- **`"within_cluster"`** — the shuffled attribute varies inside *every* cluster (matched case-control:
  a case/control swap inside each matched set). Legal; no refusal.
- **`"whole_cluster"`** — the shuffled attribute is constant inside *every* cluster (cluster-randomized
  trial: whole clusters relabelled). Legal; no refusal.
- **`"ambiguous"`** — some clusters vary and others are constant. This is the one state
  `E-STATS-NULLTEST-LEVEL` fires on, carrying both witnesses (first varying cluster, first constant
  cluster, in roster order) so the message doesn't read as though the constant one were fine.

Per § Corrections against the code, correction 4: `units.stratum_varies_within_cluster` cannot supply
this answer — it returns *first offender or `None`*, which separates "varies somewhere" from
"constant everywhere" and cannot separate "varies everywhere" (legal within-cluster) from "varies in
some" (the ambiguity). `null_test_level` is a genuinely new function, sharing only `clusters_of` (the
single cluster-membership authority) with its cousin — matching H4c's task-9-mints-the-predicate
precedent the correction cites.

## Disagreements between the briefs/spec and the actual repo state

1. **I diverged from a literal reading of task 6 step 5's "revert" instruction.** The brief's mutation
   step describes adding the discriminating `{"shuffle": 5}` case as if to prove a fixture *could*
   distinguish the mutation, then says "Revert by editing the entry back" — referring unambiguously to
   the envelope entry, but ambiguous about whether the added test case should also be reverted (i.e.,
   removed) or kept. I kept it permanently, on the reading that a documented-blind mutation with no
   surviving discriminator would be exactly the "a mutation caught only by X" trap the house style
   warns against — leaving future readers with a mutation this repo's own ledger calls out as blind
   with nothing pinning the sibling shape. Flagging this explicitly since it's a judgment call, not a
   literal instruction-follow.
2. **No other disagreement found.** Tasks 5, 6, 7, 8, and 9's briefs matched the repo state at every
   point I checked against it directly: the § Validation rows for "Null test coherence" and "Shuffle
   level is unambiguous" already existed (from an earlier batch, confirmed by grep before writing my
   own "Shuffle respects the reporting strata" row so as not to duplicate); `E-STATS-NULLTEST-REPORTBY`
   was confirmed absent from `src/`, `tests/`, and the four documents before I minted it (task 5's own
   prescribed grep, re-run); the `spec-defects.md` entries for both the `report_by` asymmetry and the
   no-units-check gap were exactly where and in the state the briefs described; `stratum_varies_within_cluster`'s
   actual return shape (first-offender-or-`None`) matched § Corrections' correction 4 exactly, confirming
   task 9 was right to mint a new function rather than reuse it.
3. **One thing I did NOT carry over from the docstring-writing trap the CLAUDE.md misreadings table
   warns about, worth naming since it's exactly the failure mode described there:** task 7's own code
   block (as given in its brief) enumerates all six eventual checks in `_check_null_test`'s docstring,
   but task 7's own `Step 4` code only implements three of them (method/n/shuffle) — units, report_by,
   and level are tasks 8 and 9's. Writing the brief's docstring verbatim in task 7's commit would have
   shipped a docstring claiming a guarantee the code did not yet provide for two commits. I trimmed the
   docstring to describe only what each commit actually built, expanding it back to the full six-item
   enumeration only in task 9's commit once all six were real. This is not a disagreement with the
   brief's *intent* (the finished function's docstring, quoted in task 7's own brief text, is what task
   9 now carries verbatim) — it's a divergence from the brief's literal per-task code block, made to
   avoid landing a false claim mid-slice.

## Concerns

None outstanding. `E-STATS-NULLTEST-UNSUPPORTED` remains alive and is asserted alongside every new
code in every test, never on a total code set, per the binding convention — confirmed by re-reading
each new test before finishing. No sentence in this batch's doc edits states or implies this slice
unblocks any config; the counts (six no-remaining-core-side-blocker, three executable) are untouched
and unmentioned here for that reason.
