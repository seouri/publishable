## Task 11 report — close the branch

**Status:** Complete.

**Commit:** `0553056` (branch tip before it was `6bac09a`)

**Whole-branch re-run.** `uv run pytest -q`: 3524 passed, 1 skipped, 2 xfailed (up 39 passed from the
3485-baseline before the slice; no failures). `uv run ruff check .`: all checks passed. `uv run ruff
format --check .`: 101 files already formatted. `uv run mypy`: no issues found in 56 source files.

**Consistency passes.** Mechanical (custom GitHub-slug checker over README, design-principles,
experimental-designs, reference.md, feasibility-growth-chart-literacy): no duplicate-anchor headings,
no broken relative/anchor links, no trailing whitespace/tabs/invisible unicode. One pre-existing,
unrelated table cell (`feasibility-growth-chart-literacy.md`'s cost-summary **Total** row, predating
this slice) trips a naive "no empty cell" rule but is a legitimate n/a total — left untouched.
Cross-document: the two new codes (`E-TEMPLATE-PARAM-PATH`, `W-SWEEP-CONDITION-DUPLICATE`) and the
third `compare` form (`to: constant`) each have § Errors/§ Warnings rows, consistent § Templates/§
Sweeps-and-repeats/§ Pre-registration prose, and a consistent fenced example comment.

**`spec-defects.md`.** Removed (not struck — per the file's own 2026-08-28 convention that a closed
entry is removed) the `parameter_spec` two-segment entry and the `sweep.baseline`/`grid`
duplicate-condition entry, both closed by code this slice. Amended the cross-run correction-family
entry in place (kept, not removed) with a dated note that it closed as a documented limitation (the
new § Studies subsection) rather than by the mechanism it proposed — no `study.yaml` block, no
computed cross-run level. Updated the preamble's recount (152/62 → 151/61 open) with a dated addendum
rather than silently changing the original count.

**Feasibility gaps 1–7.** Gap 1: corrected — was stale (claimed unhandled traceback, no `E-` code);
now states `E-TEMPLATE-PARAM-PATH` closes it. Gap 2: corrected to describe the documented-limitation
closure. Gap 3: corrected — `validate` now reports `W-SWEEP-CONDITION-DUPLICATE`. Gap 4: already
retracted (untouched). Gap 5: corrected — § Repeat kinds now states the `fold` `stratify_by` type.
Gap 6: corrected — documentation half fixed; resolver-incompatibility half was never itself a gap and
is noted as such. Gap 7: corrected — `compare: {to: constant, value: N}` now exists.

**Fifteen-config re-validation.** Ran `python3 tools/make_fixtures.py ../2026-08-28-gcl-measurement-data`
and `uv sync` in `2026-08-28-gcl-measurement/`, then `publishable validate` on all fifteen `config.yaml`s
at commit `6bac09a`. Result: thirteen `✓ valid`, two carrying exactly one `W-DATA-CLUSTER-UNDECLARED`
each (`e05c-fixed-n` on `true_count_band`, `e08-ordering` on `visit_band`) — identical to the first
measurement, as gap 4's retraction predicts. **No sixteenth warning appeared.** Appended a new dated
`### Re-measured on 2026-08-28 against commit `6bac09a`` subsection under § Executability (never
edited the original `b0a6c9e` entry).

**Concerns:** none. All four command results are green, both consistency passes are clean, and the
fifteen-config re-validation matches the brief's stated expectation exactly.
