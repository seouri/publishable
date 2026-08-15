# `spec-defects.md` staleness audit

**Measured on 2026-08-15 against commit `5578988`** (`main`, after H7a project-local templates and
H4a `statistics.resample` honoured both merged). No code touched; `uv run pytest` is
**1801 passed, 2 xfailed**, unmoved.

Ten entries amended, each by an appended `**AMENDED 2026-08-15 (spec-defects staleness audit at
`5578988`):**` paragraph. Nothing was rewritten, struck, or deleted.

## Amended

| Entry (by name) | What was stale | What the amendment says |
|---|---|---|
| New error identifiers: `E-STATS-CONTRASTS-UNSUPPORTED`, `E-STATS-RESAMPLE-UNSUPPORTED`, … | "The two that remain … are still live refusals"; "retire with H4 Statistics" | `-RESAMPLE-` retired with H4a, zero occurrences in `src/` and none in the four documents; two deliberate non-uses named (the `tests/test_validate.py` negative guard + sweep, the dated feasibility-analysis mention). `-NULLTEST-` still live, owner narrowed to **H4d** |
| `resample_draws: null` and `resample_draws: 0` were the same fact until this fix | "(`statistics.resample` still isn't honored, so there is nothing else to pass)" | `cli.py` now sets `derived_metric_draws = resample_spec["n"]` from a declared block, 2000 only as fallback |
| `percentile_over_units` is unguarded and currently unreachable | The 2026-08-11 amendment's "nothing in production calls it — **still true**, because `statistics.resample` is refused" | False at HEAD: `summarize_step`'s recorded-column branch calls it under `resample_columns`, and it arrives guarded. One copy of the correction, explicitly also governing the "RESOLVED in S4c Task 9" entry's "still unreachable in production" |
| `limits.max_ineligible_fraction` moves from S4b to S4c | "`min_clusters` and `min_units_per_cell` … remain unread behind refused features" | `min_clusters` is read (11 sites in `validate.py`, emits `W-STATS-RESAMPLE-CLUSTERS`); `min_units_per_cell` is the only one left and is tracked by its own live entry. The S4a carry table's duplicate cell deliberately left as filed |
| The importable surface names five things `publishable/__init__.py` does not export | "**Zero** of the four registries exist … still true"; six absent names; residual owned by "H7" | One registry exists: `register_template` in `templates/discovery.py`, exported, `__all__` now **eleven** names; `reference.md` marks that row `built`, so document and code agree. **Five** absent names; residual re-owned by sub-slice to **H7b/H7d** (`BaseReport` still shared with H8) |
| `register_template` appears outside § The importable surface — checked, not a defect | Tail clause "none of the four is exported, and the table now marks them `not yet built`" | Disposition stands; that clause is false for `register_template` |
| Row 211 "Template is installed" | Locator — H7a renamed the § Validation row | Row is **"Template resolves"**. Finding and reason survive (`generic` is no longer the only *resolvable* template but is still the only *installed* one). Owner stays H7, now **H7b** |
| Row 212 "Template version moved", first half | Justification "behaviourally inert while `generic` is the only installed template" | Inertness now rests on H7a's ruling that a project-local template writes no `template_version` and is never version-checked (`materialize.py` omits it, `_check_versions` skips it). Gap untouched; row not renamed; owner **H7b** |
| AMENDED 2026-08-11 (task 12, second follow-up): the gap is **four** blocks | Enumeration row verdicting `measurements`/`holdout`/`assign`/`resample`/`null_test`/`sweep.*` "unreachable; refused by the `-UNSUPPORTED` family" | Only `holdout`, `null_test`, `sweep.groups` are still behind one. `resample` is reachable **and** closed one level in (`envelope.LEAF_TYPES` types its three keys), the closure having landed before the refusal retired |
| A column metric's `resample_draws` records the requested `n`, not a survivor count | Owner "whichever slice (task 12/14) wires column resample into `summarize_step`" — that slice was H4a; and "`E-STATS-RESAMPLE-UNSUPPORTED` still refuses a declared `resample` end to end" | Debt **paid**: `reference.md` § Statistical reporting carries the column-provenance paragraph (absent / `null` / requested `n`, finiteness caveat, two-vs-three-valued asymmetry). Nothing re-owned because nothing is owing. The finiteness gap keeps its separate entry and its H4b owner |

## Verified and deliberately left alone

- **The phantom, `reference.md` § *How a metric becomes a number*** (last entry, unassigned). Accurate
  and its count is right: no such heading in any of the four documents; **5 `src/` sites** (4 in
  `stats.py`, 1 in `validate.py`); 2 scoping documents + 4 plans + 4 specs + this file + 5
  development-record files = the **eighteen** it claims. `#### What isn't a repeat` and
  `#### The unit table is the inference base`, the two real sections it says the citations lean on,
  both exist. Unchanged, including its unassigned owner.
- **The five H4a deferrals** (non-finite column values and overflowing weight sums; the `report_by`
  level's unresampled column; the refused-interval column `resample_draws`; the contrast path's
  missing resample disclosure and `paired_percentile_of_derived`'s zero-width sweep). Each still
  states something true and each names a live owner (H4b, or H4 for the `report_by` half). Not
  re-opened, not amended.
- `limits.min_units_per_cell` is still declared, typed, and read by nothing — re-checked, still true.
- **The two code-registry entries**, both downstream of any slice that mints codes: "Validate-time
  `E-` identifiers have no registry, where `W-` ones now do" (CLOSED by H1) and "Nine undocumented
  run-time and creation-command `E-` codes". Neither asserts a count that H7a or H4a moved, and
  every code the two slices minted already has a `reference.md` row — checked one by one:
  `E-TEMPLATE-LOAD`, `E-TEMPLATE-COLLISION`, `E-TEMPLATE-EXISTS`, `E-STATS-RESAMPLE-METHOD`/`-N`/
  `-UNITS`/`-STRATIFY`, `E-DATA-CLUSTER-DERIVED`, `W-STATS-RESAMPLE-CLUSTERS`/`-FAMILY`/`-THIN`. The
  nine-code table's members are untouched by either slice. No amendment needed.
- **`runner.py` is missing from § Package layout** (CLOSED). H7a added `templates/discovery.py` and
  `generate template`; `reference.md` § Package layout already shows
  `templates/{base.py,registry.py,discovery.py,builtin/generic.py}`, so the entry's closure holds.
- Entries about slices that have not run (H5/H6/H8/H9 debts, `seeds`, Row 284's `null_test`
  condition) — untouched.

## Could not settle

1. **`sweep.paired` / `sweep.ablate` / `sweep.sample` key closure.** All three became reachable with
   H2's expansion-modes work and are still typed as whole `dict`s in `envelope.LEAF_TYPES`, so the
   task-12 enumeration's "unreachable" verdict no longer explains their silence — but whether an
   additive junk key inside one is now reported by that mode's own checker was not verified. Named as
   an open question inside the amendment rather than asserted either way. Probable H2.
2. **`E-STATS-CONTRASTS-UNSUPPORTED` still matches a `src/` grep.** Only in explanatory comments
   (`cli.py`, `validate.py`); it is raised nowhere, so its retirement is intact. It does sit slightly
   against the retirement entry's own invariant ("a retired code is gone from `src/`, `tests/` and
   the four documents"), which reads as being about emit sites. Recorded in the amendment; whether
   the invariant should be reworded to say "raised nowhere" is left to whoever next mints or retires
   a code.
3. The `reference.md` § Validation row numbers this file cites (211, 212, 225, 244, 284) were left
   unremeasured. They are recorded as "line numbers as of this task" and the rows are located by
   name; re-measuring them would create a second dated set that goes stale the same way.
