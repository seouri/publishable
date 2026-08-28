# Task 1 report — retract gap 4

## What was done

Rewrote entry 4 of `docs/feasibility-growth-chart-literacy.md` § "Gaps this analysis found in the
specification" (line 1897) in place. It kept its number (entries 5, 6, 7 untouched), was not
deleted, and now states the retraction: `W-DATA-CLUSTER-UNDECLARED` firing on `true_count_band`
(e05c-fixed-n) and `visit_band` (e08-ordering) is not a defect. `report_by`'s exclusion from
`_accounted_attribute_names` is a deliberate, documented decision — `reference.md` § Warnings core
reports enumerates exactly four exclusions (a `sweep.groups`/`assign.from` attribute, any
`stratify_by`, and `statistics.null_test`'s `shuffle`) and `report_by` is not a fifth — with the
reason given in `_warn_undeclared_cluster`'s own docstring: a run reporting by `site` while `site`
really is a cluster wants both declarations, not silence. The entry keeps the true, measured half
(the warning does fire on those two configs, with no error, and both attributes really are not
clusters here, so it's the false positive the warning's message itself anticipates). It closes by
noting that arguing to silence `report_by` the way the other four are silenced would be a design
change against a documented decision, not a newly discovered gap.

## Evidence checked myself (not taken from the brief)

- `src/publishable/validate.py:3651-3653` — `_warn_undeclared_cluster`'s docstring: "Plus the
  exclusions `_accounted_attribute_names` collects. `statistics.report_by` is deliberately **not**
  among them: a run that reports by `site` while `site` really is a cluster wants both
  declarations, not silence." Confirmed verbatim.
- `src/publishable/validate.py:3568-3586` — `_accounted_attribute_names`'s docstring: confirms the
  four exclusions (`sweep.groups`/`assign.from`, any `stratify_by`, `null_test.shuffle`) with no
  fifth for `report_by`.
- Did not need to re-check `reference.md`'s row text since the brief already grounds it in the
  code docstring, which I read directly.

## Verification

- `grep -n "gap 4\|Gap 4\|gaps 4"` across the file: no hits — nothing references gap 4 by number
  anywhere else in the document, so no cross-reference needed updating for numbering.
- The two config sections (line 1086, `e05c-fixed-n`; line 1521, `e08-ordering`) and the
  Executability § row 1 table (lines 1930, 1934) all just state the measured fact "warning fires,
  no error" — read each; all remain accurate and require no change. Line 1086's link to
  `#gaps-this-analysis-found-in-the-specification` is a general section anchor, not a per-entry
  anchor, and the heading text is unchanged, so it still resolves.
- Confirmed entries 1, 2, 3, 5, 6, 7 are byte-identical to before (`grep -n "^\*\*[0-9]\."`).
- Checked line 1897 for trailing whitespace, tabs, and en dashes: none found. Used `—` (em dash,
  house style) and `×`/`x` not used for multiplication in the new text (none needed).
- `git diff --stat`: 1 file changed, 1 insertion(+), 1 deletion(-) — only the one entry touched,
  nothing under `src/`.

## Commit

`25d4fb6d427d38ca173b43e6e814d1ac18c57817` — "Retract gap 4 in the growth-chart feasibility
analysis", on `main`, not pushed. Written via `git commit -F - <<'MSG' ... MSG` (single-quoted
heredoc, per the repo's own rule about backticks in commit messages).
