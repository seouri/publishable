# SDD ledger — plan: docs/superpowers/plans/2026-08-17-weighted-contrasts.md

Spec: docs/superpowers/specs/2026-08-17-weighted-contrasts-design.md
Branch: h4b-weighted-contrasts, from main at d11f40a. Baseline: 2118 passed, 1 skipped, 2 xfailed;
ruff check, ruff format --check (80 files, 0 to reformat) and mypy (45 source files) all clean.

Standing authorization: re-scope, spec, plan, execute, merge AND push without stopping, reporting once
after the push. Committed before the first dispatch — an implementer two slices ago correctly refused an
uncommitted authorization line in this file as a possible injection, and from inside a task it is
indistinguishable from one.

**What this slice moves.** `E-DATA-WEIGHT-CONTRAST` retired, and the count of experiments with **no
remaining core-side blocker** goes three -> six. **The EXECUTABLE count stays at three** — C1-C3 also
depend on `io.reuse_from`, unbuilt and unowned, which no config or grep can settle.

## Pre-flight conflict scan

| File | Tasks | Finding |
|---|---|---|
| `tests/test_cli.py` | 2, 3, 6, 7, 10, 11, 12 | Seven tasks append. Clean by inspection, but **each must re-read the file s existing names before adding a helper** — a plan two slices back authored a helper that would have shadowed one used by a dozen tests. The plan also states once that tasks 6-12 test by DIRECT CALL, because `command_run` returns `EXIT_WRONG` on any error and the refusal is one until task 13 |
| `docs/reference.md` | 1, 2, 3, 11, 13, 14 | Six tasks. **Ruling: tasks 2 and 3 must precede 7-10** — a `method` string and a record key must exist in a document before code emits them, and the four documents give a weighted contrast NO method string today. Task 13 strikes the § Validation row together with the § Errors row it pairs with, which is why spec correction 3 moved it there: striking one alone would have the document deny a live refusal for two commits |
| `src/publishable/cli.py` | 6, 7, 8, 10 | **The payoff chain, and the ordering is the whole point.** 6 threads `weights`, 7 builds the weighted closure, 8 writes the record, 10 wires the general construction. **5 before 7** (spec decision 5): a stratified draw lives INSIDE the weighted closure, so building the closure first bakes the answer in by omission — which is exactly how `resample.stratify_by` got dropped on this path originally |
| `src/publishable/stats.py` | 5, 8, 9 | Clean and ordered: 5 gives the paired percentile construction a `strata` parameter it is the only one of four to lack, 8 adds Kish and the weighted effect size, 9 builds `weighted_paired_t_over_units`. **Spec correction 2: that construction is built at 9, not 10** — `correction._corrected_bounds` diffs branch is its FIRST caller, so the spec s original ordering inverted the dependency |
| `src/publishable/validate.py` | 1, 13 | Clean. 1 narrows the published refusal s over-broad claim; 13 deletes its single emit site. **The emit is ONE site** — my scoping brief said five, which was a `grep -c` over a docstring line and three comments |
| `src/publishable/correction.py` | 4, 9 | **The pair that can diverge silently.** 4 decides whether `Member` carries weights or the corrected path is forced onto the pool, argued against `__post_init__`s exactly-one invariant; 9 builds it. Until 9, `Member.weights` is written and read by nothing — the plan names that gap in-task rather than leaving it to be found |

**Three conflicts required a ruling and all three are recorded above** — `reference.md` s 2-and-3-before-
7-10, `cli.py` s 5-before-7, and `stats.py` s construction-at-9. The rest are clean, and the rows are
here because "the scan is clean" without them is not a scan that was run.

**The fixture the whole slice rests on, arithmetic checked by me rather than carried:** six units, column
`m` at 1, 2, 3, 9, 10, 11 against a zero baseline, weights 1, 1, 1, 3, 3, 3. Unweighted delta 36/6 = 6.0;
weighted delta 96/12 = 8.0; Kish effective size 144/30 = 4.8 against a raw 6. **Three distinct answers,
so a wrong weighting cannot pass** — which is the trap statistics tasks in this repo keep falling into,
sixteen unfailable checks in two slices.
