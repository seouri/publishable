# G2 whole-branch review — the single fix wave

Six findings from the final review at `whole-branch-review.md` (read it in full first).
I independently verified the three code facts below before writing this brief; they are settled,
so do not re-litigate them — build on them.

- `correction.py::_level_for` returns `None` for `fdr_bh`. So under BH there is no per-comparison
  level and therefore no corrected bound, for ANY member.
- `cli.py` ~line 1651: `corrected_from_pool = is_derived or resample_columns`. A derived metric
  carries the pool with NO declared `statistics.resample`. Derived resampling gates elsewhere on
  `compute is not None and seed is not None`.
- `pools_by_key` (`cli.py` ~4089, written ~4403) is never read. T5 used a `step_pools` local instead.

## The six

**F1 [Important] `reference.md`: `fdr_bh` is a third case, and the document contradicts itself.**
The slice's new text promises a real corrected bound "except in two cases" (no raw interval;
weighted+clustered) — but the same document still lists `fdr_bh` among the reasons a bound is null,
and BH genuinely produces none. Correct the new text so the exception set is right. Do NOT simply
append "and fdr_bh" everywhere: work out whether BH belongs in the same list at all, or whether it
is a prior condition on the whole promise (no method-level α → no bound for anyone). State it
whichever way is TRUE and self-consistent across every passage the slice touched. Re-read § Statistical
reporting, § Pre-registration, § What a hypothesis is tested against and the `compare` enum comment.

**F2 [Important] Decision 1's row 4 is false where it is quoted as live text.** Row 4 reads
"derived, no declared `resample` → no raw interval → nothing to correct". The premise is wrong: a
derived metric resamples without a declared `resample`. The row's CONCLUSION (a metric with no raw
interval has nothing to correct) is right; only its stated cause is wrong. What actually reaches the
no-interval state is a resample that yielded no usable interval — T5's own row-4 test reaches it via
all-degenerate draws. Fix the live homes: `docs/superpowers/spec-defects.md` (a live list) and the
new comment in `src/publishable/hypotheses.py`. **Do NOT retro-edit the design spec or the plan** —
`CLAUDE.md` forbids editing the development record; a spec records what was decided when written.
Instead append a correction to the ledger `progress.md` naming what it replaces. Sweep for other
live homes of the false premise before you stop.

**F3 [Important] Feasibility finding #2 names the wrong metric and contradicts the § Executability
entry appended below it.** `docs/feasibility-growth-chart-literacy.md` finding #2 says the E2 claim
can be written "directly on `step03_compare.auroc_count_only` rather than routed through a
`summary`-step `Estimate`". That metric IS the Estimate — the source config's `h1` carries no
`compare:` block at all. The condition-scoped metric that COULD carry `compare: {to: constant}` is
the template's own `auroc`. Correct finding #2 to name the right metric and to agree with the
§ Executability entry. Do not edit that dated entry; it is correct.

**F4 [Minor] Delete `pools_by_key`.** It is written and never read, and its comment claims the job
the `step_pools` local actually does. Delete the declaration and the write. Check whether the
`report_by` comment at ~4903 that references "a `pools_by_key`-shaped cache" still reads correctly
once the name is gone — reword it to describe the shape without naming a symbol that no longer exists.

**F5 [Minor] Pin the `declaration_index` offset and the co-family case.** T5 sets
`declaration_index=len(comparison_members)+i`. Mutating it to `=i` — colliding with the comparison
members' 0..n-1 — leaves `test_cli.py test_hypotheses.py test_correction.py` fully green (702 passed).
No test anywhere puts a comparison member and a condition member in the SAME family, so the Holm
re-rank that Decision 5's amendment describes is unpinned. Write that test: one family containing
both kinds, asserting the ranking and the resulting corrected bounds. Prove it fails under the `=i`
mutation and report the exact pytest output line for both arms. Keep a copy before mutating; verify
the revert by behaviour, never `git status`.

**F6 [Minor] `spec-defects.md`'s narrowed entry still carries its old present-tense "Why open"
paragraph** ("bound test is never answerable") above the amendment that corrects it. In a live list a
stale paragraph misleads. Repair it — and prefer deleting a false claim to rewriting it, per CLAUDE.md.

## Constraints
- Four documents get both consistency passes if you touch any of them.
- Full suite, ruff, ruff format, mypy must all be clean before you commit. Baseline: 3544 passed,
  1 skipped, 2 xfailed.
- Do not touch the T1 bit-stability oracle's golden literal. If it moves, something is wrong.
- Cite sections by name, never line number. `×` not `x`. Hyphens, not en dashes, in anchors.
- Commit with `git commit -F - <<'MSG'` (single-quoted heredoc). Backticks in a double-quoted commit
  message have executed the command they named in this repo. Do not push.
- Report to `.superpowers/sdd/2026-08-28-correctable-condition-metric/fix-wave-report.md`.
