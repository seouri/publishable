# Task 6 report

**Status:** done
**Commits:**
- `5c744bd` — feat: W-STATS-RESAMPLE-FAMILY, the comparisons-only bound; file the metric-count residue
- `8a973f1` — fix: address task-6 review — precedent count, cross-doc distinction, sizing rule, default-n and floor coverage, valid-choice fixture

**Tests:** `uv run pytest` — 1719 passed, 2 xfailed (baseline 1711 + 8 new). `uv run ruff check .` and `uv run mypy` both clean. All four mutations applied/reverted in place (never `git checkout`), each confirmed FAIL before revert, PASS after.

## Review response

**1 (Important) — wrong precedent count.** Fixed the comment: only `_check_sweep` and `_check_contrasts` call `expand(doc)` directly with this guard; `_check_hypotheses` goes through `_condition_labels`, a different call site. Comment now names exactly those two and says why `_check_hypotheses` isn't a third.

**2 (Important) — cross-document consistency.** `reference.md`'s "Six things deliberately absent from that table" paragraph (§ CLI reference, line 336) claimed a corrected interval's draw floor is reported only once a run has executions to count from — true of `W-STATS-CORRECTED-THIN` but no longer complete once `W-STATS-RESAMPLE-FAMILY` exists as its validate-time counterpart. Added a distinguishing clause parallel to the existing "distinct from the row above" one; the "Six things" count is unchanged (a clause, not a seventh thing).

**3 — the sizing rule.** Added two sentences to § Statistical reporting, immediately after the correction-level table and before the Holm paragraph: `resample.n` should be sized against `comparisons × metrics` (≈ 80·m draws), not the 80-draw floor alone, and a hypothesis family is corrected separately at its own count. Framed as a present-tense spec claim, not a build claim.

**Minors — all taken:**
- Added a test (`test_the_family_bound_is_silent_once_n_is_already_refused`) and confirmed by mutation that removing the `n < floor` early return makes it fail — the clause was previously untested.
- Fixed the default-`n` silence: an absent `n` now uses `cli.py`'s actual hardcoded default (2000) as the effective value for the bound, rather than treating "unset" as "nothing to check." Comment corrected accordingly. Added `test_the_family_bound_applies_to_an_unset_n_too` (26-comparison family warns at the 2000 default; 1-comparison family stays silent) — mutation-confirmed.
- `spec-defects.md`'s residue section now names the second family explicitly: `hypotheses.py` corrects at `ALPHA / H` where `H` is the *computed* confirmatory count, not the declared one (exploratory and summary-`Estimate` hypotheses are named but excluded), so it has the same one-step-removed unboundability as the metric count, just thinner.
- Softened "read off the SAME pool" to note it's true of pool-backed members only, not a universal guarantee ahead of later tasks.
- `_check_resample`'s docstring now says "method enum, its n floor, the comparison-family lower bound on that same n, and its stratify_by names" (four checks, not three).
- Fixed the scaling-test fixture: it swept `analysis.method` including the invalid choice `"theil"` (`GenericTemplate.parameter_spec` closes `method` to `{pearson, spearman, kendall}`), producing incidental `E-PARAM-VALUE` noise. Switched the shared `_resample_family_config` helper and all call sites to sweep `analysis.min_samples` (unconstrained int, `ge=2`) instead, sized directly to whatever comparison count each test needs. No behavioral change to what's being tested, just removes the noise.

No further disagreements found between the review and the code; all six points were real and are now addressed with their own tests, each mutation-verified.
