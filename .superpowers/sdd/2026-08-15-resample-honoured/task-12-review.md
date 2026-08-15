# Task 12 review — retire `E-STATS-RESAMPLE-UNSUPPORTED` (`30e8d03..ef8880f`)

**Spec compliance: ✅**
**Task quality: findings — 1 Important, 3 Minor.**

## What was verified, and how

| Check | Result |
|---|---|
| `uv run pytest` | 1767 passed, 2 xfailed — matches the report |
| `uv run ruff check .` / `uv run mypy` | both clean |
| Sweep, **file list filtered**, scope `src/ tests/ docs/` (tracked files) | only `docs/superpowers/**` (gitignored), `tests/test_validate.py` (the acceptance test's own assertions), and one dated historical mention in `docs/feasibility-llm-growth-studies.md`. No `src/` hit. Sweep proven able to fire against a known-present string |
| Inverse sweep — prose still calling a declared `resample` refused | none in the four documents |
| `NOT BUILT` count phrase | exactly three markers remain (`{resolver:}` line 79, `holdout` line 91, `null_test` line 151); § The one config file now says "**Three** declarations". The neighbouring "four optional `statistics` sub-blocks" counts sub-blocks, not build state, and is still right |
| No "retired" row added to § Errors `validate` reports | confirmed — the `-UNSUPPORTED` family stays out of the registry |
| "unblocks 8 of the nine" | absent; the honest phrasing (one refusal retired that 8 of 9 hit, zero experiments newly executing) is what the section carries |
| Mechanical pass on both edited `*.md` | duplicate anchors, broken links/anchors, table column counts, trailing whitespace, tabs, invisible unicode — all clean. The three apparent column mismatches are escaped `\|` inside cells, pre-existing and untouched |
| Feasibility configs re-checked against the now-real checks | every declared block is `method: bootstrap`, `n: 2000`, and each `stratify_by` name (`truth`; `consensus_label`, `count_stratum`) is in that config's `data.units.attributes` — so no config earns a *new* finding from the retirement. The table needed no new row, which is the thing that could have gone wrong silently |

**Mutations** (`__pycache__` cleared each time, reverted by editing in place, verified byte-identical to a pre-mutation copy and by re-running):

1. Re-added the `resample` tuple → `test_a_declared_resample_is_no_longer_refused_wholesale` FAILS (plus two more). Reverted, green.
2. Deleted the whole `null_test` check → `test_a_declared_null_test_is_still_refused_h4a` FAILS. **`E-STATS-NULLTEST-UNSUPPORTED` genuinely survives** and is genuinely pinned.
3. (Extra) `return` inserted after the `method` check → the two `method`-side repairs FAIL, confirming their new companions are load-bearing.
4. (Extra) `return` inserted after the `n` check → **all four repaired tests still pass** — see Minor 1.
5. (Extra) removed the `isinstance(n, int) and not isinstance(n, bool)` guard → both `n` tests FAIL, so their primary assertions are still mutation-sensitive.

## 1. The two-task window: **silent, not wrong**

`statistics.resample` is read at exactly one place in `src/` — `validate.py:5026`. `cli.py:1502` still hardcodes `derived_metric_draws = 2000` and reads nothing from the declaration. Nothing else at run time consults the block.

So during the window nothing in the record makes a false statement: `resample_draws` reports the draws actually taken, and the emitted method strings (`t_over_units`, `percentile_over_units`, …) name the constructions actually used. No field echoes the *declared* method, `n` or `stratify_by`, so nothing claims the declaration was honoured. The six validate-time checks bound the declaration's *shape*, not its honouring — a config passing all six is simply not acted on.

The honest caveat, and what makes the window bounded rather than dangerous: `run.yaml` embeds the config verbatim, so a declared `n: 5000` sits beside `resample_draws: 2000` in the same file. The disagreement is **detectable by a reader**, not hidden. Tasks 13–14 close it.

## Findings

### Important

**I1 — A false claim about `validate`'s check ordering, introduced by this commit in the dated section.**
`docs/feasibility-llm-growth-studies.md` § Executability on this build now says: "all nine still declare a resolver and stop at `E-DATA-RESOLVER-UNSUPPORTED` — **the plugin registry gates every one of them before any other check runs**."

`validate` is a collector, not a short-circuiter. Probed directly with a config declaring a resolver, a `holdout`, and a faulty `resample`:

```
['E-DATA-HOLDOUT-UNSUPPORTED', 'E-DATA-RESOLVER-UNSUPPORTED',
 'E-STATS-RESAMPLE-METHOD', 'E-STATS-RESAMPLE-N']
```

All four are reported together; the resolver finding gates nothing. `_check_resample`'s own comment ("No `return` here, matching the `E-REPL-FOLD-NO-UNITS` twin") says the same from the other end. This is the repo's 12+-instance defect class — a prose claim about a guarantee the code does not provide — and it lands in the one section whose justification is that it was "re-derived from `validate.py`'s emit sites". The rest of the sentence is correct and load-bearing; only the ordering clause is false.
*Fix:* cut the clause, or reword to "each of the nine still carries at least one refusal from an unbuilt slice, and every one of those refusals is still reported."

### Minor

**M1 — Two of the four repaired tests claim a proof their companion cannot give.**
`test_a_resample_n_of_the_wrong_type_is_a_type_fault_not_a_traceback` and `test_a_resample_n_of_bool_type_is_a_type_fault_not_a_floor_violation` gained `method: "bootstap"` as their companion, with a docstring and an inline comment saying it proves "validation continued past the bad leaf". The `method` check runs **before** the `n` check: with a `return` inserted immediately after the `n` check, both tests stay green (mutation 4). So the companion proves only that validation reached a point upstream of the leaf in question. The two `method`-side repairs do not have this problem (mutation 3 kills them), and both `n` tests still fail under their real mutation (mutation 5), which is why this is Minor rather than a broken test.
*Fix:* move the companion downstream of the `n` check — an undeclared `stratify_by` name — or reword the comment to claim only that `validate` did not crash.

**M2 — The prescribed `null_test` control is a near-duplicate; the requirement was already met.**
Mutation 2 failed **four** tests, including the pre-existing `test_a_declared_null_test_is_refused`. The sibling was already load-bearing before this task, so `test_a_declared_null_test_is_still_refused_h4a` adds a second name for a property already pinned. Harmless, and the brief asked for it — noted so the duplication is deliberate rather than forgotten.

**M3 — Unresolvable relative build claims left in docstrings.**
`_check_resample`'s new docstring says resampling "is not honored by `cli.command_run` yet **at that same commit**" while naming no commit; the same window is described in `cli.py`, `stats.py` and `units.py`. All four go stale the moment tasks 13–14 land. The implementer flagged this in the report — logging it so 13/14 actually clear it, and so no "at that commit" survives without a sha.

*(Sub-minor, not counted: `test_a_declared_resample_is_no_longer_refused_wholesale`'s second assertion — a prefix filter over `found` — would pass vacuously if the config failed early for an unrelated reason. Covered in practice by `test_a_resample_with_no_unit_roster_is_refused`, which asserts `== set()` on the identical config.)*

## The two brief defects the implementer reported — both confirmed

- **(a) True.** `git show d5a3a19` (task 2) changed `# NOT BUILT; {method: …}` to `# NOT BUILT; bootstrap` — it deliberately **kept** the marker, contradicting step 3(b)'s "Task 2 already removed `NOT BUILT;`" and agreeing with the brief's own top matter. Dropping the marker here, together with the coupled count, was the right resolution and leaves the list self-consistent.
- **(b) True.** The prescribed docstring ("`cli.command_run` resolves the block and threads it into every interval construction, so a declared resample changes the record") is false at this commit — `cli.py` hardcodes 2000 and reads nothing. Writing it would have been the exact defect class this repo has hit 12+ times. The substituted text across five files is accurate at `ef8880f`, subject to M3.

## The dated claim

The split into two commits is correct reasoning, not bookkeeping: `9fa2366` dates the section against `2fdc957`, the tree where the refusal is actually absent, rather than against a parent that still carries it. Today's date matches. The section states plainly that the table is re-derived from `validate.py`'s emit sites rather than from a run, and why (the nine configs are YAML in the analysis, not files in the repo) — which is the honest disclosure the procedure asks for. Subject to I1, the section is accurate.

## Tree state

Clean at `ef8880f`; `git status` shows only the user's uncommitted `progress.md`. 1767 passed + 2 xfailed, `ruff check` and `mypy` clean, re-verified after every mutation was reverted.
