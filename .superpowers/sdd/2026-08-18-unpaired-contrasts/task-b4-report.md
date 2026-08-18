# Batch 4 report — tasks 14, 16, 15+17b+18, 19, 20, 22

## Status

All six tasks complete. Full suite green, ruff/mypy clean, at every commit.

## Commits

| Task | SHA | Message |
|---|---|---|
| 14 | `66b57c2` | feat: the four reachable unpaired contrast cells, their methods and cohens_ds |
| 16 | `6e45eb5` | fix: W-STATS-CONTRAST-THIN reads a comparison's own denominators, per side at both emit sites |
| 15+17b+18 | `05aeba8` | feat: E-DATA-ALLOCATION-CONTRAST retired, the derived unpaired path guarded on two named grounds, and an unpaired contrast run end to end |
| 19 | `6b9bf11` | docs: every surviving claim that core refuses a cross-arm delta, repaired by claim |
| 20 | `87d1706` | docs: H4c's five inherited filings ruled, the sorted-pool precondition claimed, and the counts re-measured unmoved |
| 22 | `ad1bb34` | review: H4c whole-branch — three corners pinned (derived-key collision, mixed-pairing correction family, report_by/Estimate boundary), all found correct |

## Test summary

`uv run pytest` progression, each run in the foreground against the full, unfiltered suite:
2252 (start) → 2260 (task 14, +8) → 2265 (task 16, +5) → 2269 (task 15+17b+18, +4 net: +5 added, −1
stale test deleted) → 2271 (task 19, +2) → 2272 (task 20, +1) → 2275 (task 22, +3, all new
whole-branch pins). **Final: 2275 passed, 1 skipped, 2 xfailed.** `ruff check`, `ruff format --check`
(80 files), and `mypy` (45 source files) clean at every commit.

## Measured figures

**Feasibility analysis executability**, measured 2026-08-18 against commit
`6b9bf119a9706aeb34be7e10a4311280e1b9e5d9` (the task 19 commit — the state task 20's own dated section
measures): **H4c unblocks ZERO configs. Six with no remaining core-side blocker, three executable —
both counts unmoved**, matching `CLAUDE.md` § Repository status exactly. `grep -c 'allocation:
within'` → 3, `grep -c 'allocation: between'` → 1 (read, confirmed to be prose naming fields no config
declares), `grep -n 'groups:'` → 2 hits, both `groups: []` — no config in the analysis declares a
group axis, so neither the retired `E-DATA-ALLOCATION-CONTRAST` nor the minted
`E-DATA-WEIGHT-ALLOCATION-CONTRAST` reaches any of the nine. Can-fail control on a minimal fixture,
cited against this repo's own tests: `test_a_contrast_beside_groups_and_cluster_by_now_validates_clean`
(exact empty set) and `test_a_weighted_cross_arm_contrast_draws_the_weight_allocation_refusal` (exact
`{E-DATA-WEIGHT-ALLOCATION-CONTRAST}`). Recorded in `docs/feasibility-llm-growth-studies.md`'s new
dated section, appended after the H4b-2 one; no earlier dated section touched.

**Task 14 mutation 3** (`cohens_dz` swapped in for `cohens_ds`): the fixture's zip-truncated 5-pair
`cohens_dz` value is **6.7082039324993685**, not the 7.0710678118654755 the brief's docstring cites (a
different quantity — that number is what standardizing by the Welch SE instead would give, not what
this mutation produces). The test still correctly FAILs; only the specific number differed from the
brief's illustrative one.

## Concerns and findings

1. **Task 15's mutations 1 and 2, as literally prescribed, are blind on their own fixtures — measured,
   not assumed.** `test_the_derived_suppression_reads_the_pairing_answer_not_an_empty_intersection`
   (the brief's own verbatim test) and the run-through test both stayed GREEN when `and is_paired` was
   deleted from the derived-branch guard, and again when it was replaced with `and bool(base_keys)`.
   Root cause: a real unpaired comparison's two arms are disjoint by construction under `allocation:
   between`, so `base_keys` is empty regardless of whether the guard's `is_paired` clause fires, and
   `paired_delta_of_derived`'s own `if not keys: return None` floor produces the identical three nulls
   either way. I built an additional direct-call test,
   `test_the_derived_suppression_fires_even_when_the_intersection_is_not_empty`, with a **fabricated**
   fixture (two conditions declared unpaired but hand-built with overlapping collapsed-table keys —
   unreachable through any real `validate`-passing config, only reachable by direct call) that
   genuinely discriminates both mutations. Ran and confirmed: mutation 1 → `delta` leaks to `10.0`
   instead of `None`; mutation 2 → identical leak. Reverted both; full suite green after each revert.
   This is reported rather than silently patched over, per the standing rule about a prescribed
   mutation that turns out blind.

2. **Task 22's own corner-(a) end-to-end test inherits the same blindness, for the same reason** —
   `test_an_unpaired_derived_key_collision_end_to_end` (the real-run reproduction of H4b-2's Critical,
   one axis over) also stays green under the guard's `is_paired` clause removed, checked directly. Its
   docstring says so explicitly and points to the direct-call test above as the one that actually pins
   the guard. The end-to-end test's real job — confirmed correct — is the record shape: three nulls,
   two side counts, and the recorded column's own per-condition interval untouched.

3. **Task 18's Step 5 conversion table missed one site**: `test_the_validation_rows_own_reading_names_
   no_row_task_13_deletes` asserted on § Validation's *"Allocation deltas aren't computed"* row, which
   task 18's own Step 3 deletes. Not named in the brief's table. Deleted the test (its subject row no
   longer exists; nothing to convert) rather than leave it failing. The brief said +4; the delta was
   +4; it arrived as +5 added and −1 deleted, the deletion being a site the brief's own table did not
   carry — reconciled against the brief's arithmetic as `CLAUDE.md`'s own "a test-count absolute cannot
   be stated per task" note anticipates.

4. **Two tests in `test_validate.py` needed `E-DATA-ALLOCATION-WITHIN-ARMS` added to their exact
   sets** after the retirement (`test_a_generated_cross_arm_comparison_now_validates_clean`,
   `test_a_declared_contrast_across_arms_now_validates_clean`) — their fixtures declare no
   `allocation`, which defaults to `within` and earns that code alongside a declared `groups` axis
   regardless of the cross-arm question. The third renamed test in the same conversion,
   `test_a_contrast_beside_groups_and_cluster_by_now_validates_clean`, declares `allocation: between`
   and asserts the true exact-empty set. Caught by running rather than assuming the exact set. A stale
   docstring citation inside that third test — naming the first two tests by their pre-rename
   names — was also found and corrected in the same pass.

5. **Task 20's Finding-3 disposition ("CLAIM")**: the brief's ruling table says "CLAIM Finding 3" for
   the contrast-entry resample echo, but no numbered step in task 20 builds code for it. Ruled as
   "confirmed still real and unambiguously scoped to H4c's own record shape, owner H4d" rather than
   inventing an unscoped fix — flagged here since "claim" could be read as "close," and it is not
   closed.

6. **Disk exhaustion mid-review** (task 22): `/System/Volumes/Data` hit 100% (147Mi, then effectively
   0) during a `grep`, which is an unrelated system condition, not a mutation artifact. Checked the
   guard's state via `Read` before doing anything else (intact, no live mutation), then cleared
   `pytest-of-joon`'s stale temp dirs (186M) to recover headroom before re-running the suite. The one
   pytest run that executed while disk was critically low logged 65 `OSError` "could not create
   numbered dir" collection errors on unrelated tests — a disk artifact, not a regression; the
   immediately following clean run passed those same tests.

No other disagreements between brief/spec and code found in this batch beyond items 1–5 above.
