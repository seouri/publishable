# H4a whole-branch fix report

Closing the findings of `whole-branch-review.md` (verdict: findings, no Critical — 3 Important,
4 Minor). Branch `h4a-resample-honoured`, reviewed at `d59316d`. All seven taken; one new finding
was turned up while closing M4 and is filed rather than fixed.

`uv run pytest` → **1801 passed, 2 xfailed** (baseline 1800 + 2; the one new test is I1's pin).
`uv run ruff check .` clean. `uv run mypy` clean, 42 files. `ruff format --check`'s 62 files
untouched, per instruction.

---

## Important 1 — the record claimed a resample that did not happen

**Fixed in code, not filed.** `cli.command_run`'s retry after a `ContractError` from
`summarize_step` now passes `seed`, `draws`, `resample_columns` and `strata`, so a contained
`aggregate` fault (`E-DATA-CLUSTER-DERIVED`, `E-STEP-KEY-COLLISION`) costs the derived mapping and
nothing else — which is what the retry's own `weights` argument, four lines above the disputed
comment, was already there to guarantee.

**Why honour the resample rather than suppress the echo.** The file's own principle decides it: the
comment beside `weights` says "the collision costs the `derived` mapping and nothing else, so the
recorded columns must come back with the same arithmetic they had on the first call", and a
column's interval construction is that same arithmetic. Suppressing the echo would additionally
contradict `reference.md` § Statistical reporting, which has the resolved block recorded "so the
number is never the result of an undocumented default" — it would make the record say less than the
run did, and it would need a document amendment to be legal. Fixing it by *providing* the guarantee
the comment claimed is the cheaper and the more honest of the two.

**`draws` travels with the gate.** At `summarize_step`'s 2000 default a config declaring `n: 500`
would have resampled the column 2000 times beside an echo saying 500 — the same defect class one
field over. The four arguments are passed together for that reason.

**The crash risk was checked, not assumed.** `stats.py`'s `E-STEP-KEY-COLLISION` comment states as
an invariant that the retry must not re-raise. The only `ContractError` the column loop can raise on
this path is the run-time `E-STATS-RESAMPLE-STRATIFY-VARIES` from
`percentile_over_units_clustered`. Verified by probe that it fires from the **column** loop, ahead
of the derived block — so the *first* call raises it before the fault this `except` contains, and
the `except` is never entered for it. `validate` refuses the same composition from the roster
(`units.stratum_varies_within_cluster`, per declared name) and `command_run` returns `EXIT_WRONG`
on any validate error, so a run that starts cannot reach it. That argument depends on the run-time
check being no *stricter* than the validate-time one: it is looser, because `cli.resample_strata`
joins the declared names into one label and a label collision can only merge two strata, never
split one. The dependency, and the already-filed gap it rests on
(`cli.resample_strata`'s composed label), are named in the new comment as a dependency rather than
as coverage.

**The retry-site comment is rewritten** and no longer claims reproduction it does not perform.

**Pinned** by `tests/test_cli.py::test_a_contained_aggregate_fault_does_not_downgrade_a_declared_column_resample`
— declared `n: 500` (not the 2000 default), `cluster_by`, a template deriving a metric, asserting
`percentile_over_units_clustered`, `resample_draws: 500`, the echo, `E-DATA-CLUSTER-DERIVED`
disclosed and `status: completed`. **Two mutations, each confirmed FAIL then reverted by editing in
place and re-confirmed PASS:** dropping `resample_columns=` from the retry (→
`t_over_units_clustered`) and dropping `draws=` (→ 2000 beside an echo of 500).

**The undeclared path is unchanged, proved not argued.** The review's shape (b) — undeclared
`resample` + `cluster_by` + `weight_by` + a derived metric, which fires `E-DATA-CLUSTER-DERIVED` and
so runs this exact retry — was run end to end: `weighted_t_over_units_clustered`, **no**
`resample_draws` key, **no** `resample` echo, i.e. byte-for-byte the `eaf3605` shape. The existing
`test_a_clustered_derived_metric_is_refused_rather_than_drawn` pins the unweighted twin and still
passes untouched. Task 1's pin is green.

`report_by`'s level call was **not** touched — its asymmetry is filed with a live owner and this fix
does not widen it.

## Important 2 — `_check_resample`'s docstring undercounted and misattributed

**Fixed.** The docstring now enumerates **all seven** findings by identifier in declaration order
(`E-STATS-RESAMPLE-UNITS`, `-METHOD`, `-N`, `-STRATIFY-UNKNOWN`, `W-STATS-RESAMPLE-CLUSTERS`,
`E-STATS-RESAMPLE-STRATIFY-VARIES`, `W-STATS-RESAMPLE-FAMILY` — counted against the `c.error(`/
`c.warn(` sites in the function body, not from the old prose), marks the **two** that read the
roster, and says that each carries its own `roster is not None` guard — verified at both sites
rather than repeated from the old sentence. The inline comment at the no-`return` gate is corrected
in the same pass and now points at the docstring's list instead of naming "the one exception".

The enumeration makes a claim about this function only ("a check added here must state which side of
that line it is on"), not a guarantee about anything downstream — deliberately, since I2 and I1 are
both the overreaching-comment class and the fix must not mint a third.

## Important 3 — two deferrals not durably filed

**(a) Non-finite column values.** `spec-defects.md`'s entry is amended: **owner re-assigned to H4b**
("weights and clusters through the contrast family", `H4-SCOPING.md` § Decomposition), with the
record stating that the previous owner *was* H4a, that both tasks landed, and that **task 14's
decline was deliberate** — with the disclosure it took instead named at both live sites
(`stats.summarize_step`'s docstring and `reference.md` § Statistical reporting, both verified
present). The two `*_is_a_known_unfixed_gap` tests are untouched.

**(b) Contrast entries get no resolved-values echo.** **Now filed**, as Finding 3 appended to the
existing task-16 entry — the entry the ledger falsely claimed already carried it, so the repair
lands where the next reader looks. Dated and pinned to `d59316d`. Re-confirmed at the construction
site as well as by the review's run: `_comparison_step_blocks` builds each entry as a literal
`{delta, n_paired, method, ci95, cohens_d, correction}` mapping and takes no `beside_n` parameter at
all, so there is no route by which the echo could reach a contrast.

The other three deferrals were **not** re-opened.

## Minors

- **M1.** The task-16 entry's "its three siblings now have" sentence now carries an explicit scope
  paragraph: each of those refusals is on its stratified or clustered branch; an **unstratified**
  constant pool still publishes `Interval(5, 5)` from `percentile_over_units` and
  `(Interval(5, 5), 200)` from `percentile_of_derived`, which is not a regression (`t_over_units`
  does the same) and is defensible, but is not the general guarantee a reader might infer.
- **M2.** Both deferrals now name **H4b** with its charter title and the file to look it up in,
  replacing "H4's contrast-side hardening"; the old description is recorded as what it was, so the
  ledger's wording still leads somewhere.
- **M3.** The perishable build claim ("Check `cli.command_run`'s `derived_metric_draws` directly for
  whether that gap is still open") is retired: the docstring now says tasks 13–15 closed the window
  and states what `command_run` does today, with no errand for the reader.
- **M4.** `reference.md` § The one config file: `measurements` is now "the one *built* block `init`
  **materializes** as a `null`", with a clause saying `statistics.resample` is *shown* that way too
  since H4a but is written by `init` not at all — and why that difference is load-bearing rather
  than incidental. **Every count phrase in the paragraph was re-checked**, not only the two the
  review named: "four optional `statistics` sub-blocks" (contrasts/resample/null_test/report_by ✓),
  "Three declarations above are not yet built" (three `NOT BUILT` markers in the fenced block ✓),
  "Its two sub-fields, `by` and `collapse`" (✓ against the inline comment), and the six-key closed
  set `{method, from, ratio, block_size, stratify_by, seed}` (✓ against `envelope.ASSIGN_AXIS_KEYS`).

## New finding, filed not fixed

**`reference.md` § *How a metric becomes a number* is cited across the repo and does not exist.**
Found while writing M4's cross-reference and checking that the anchor resolved. No heading of that
name exists in any of the four documents, and no commit in this repo's history removed one — yet
**eighteen files name it**: five sites in `src/` (four `stats.py`, one `validate.py`), both scoping
documents, four plans, four specs, five development-record files, and `spec-defects.md` itself,
whose `W-STATS-AGGREGATE-FAILED` entry proposes to "add `resample_draws` to the § How a metric
becomes a number derived-metric shape once that section next changes".

The sweep behind that count was run **filtering the file list, never the output** — the first
attempt used `grep -v superpowers` and lost every hit inside `spec-defects.md`, which is the trap
`CLAUDE.md` § Two mechanical traps describes verbatim; caught and re-run before the entry was
written, and the re-run is what turned up the prior mentions.

The quotations were located rather than assumed: `stats.py`'s "can do only for a metric it knows how
to compute" is under `#### What isn't a repeat`; the `resample_draws` scheme and the
recorded-column paragraph are under `### Statistical reporting` → `#### The unit table is the
inference base`. The phantom name spans at least two real sections, so it is not a `sed`. Filed with
**both readings stated** — the citations are misaddressed, or the document genuinely owes the
section that uniform usage implies — because nothing in the record settles which, and the second
reading is a documentation change of real size. Owner unassigned. Two instances written by this pass
(one in `spec-defects.md`, one in the new test's docstring) were corrected before landing; the entry
does **not** claim the name was "invented", which the record does not support.

## Mechanical pass

Both edited `*.md` files: no trailing whitespace, no tabs, no invisible unicode (the only non-ASCII
characters added are `—` and `§`), every added link resolves (`#statistical-reporting`, one
heading), no table touched, no heading added or moved so no anchor changed and no count phrase
elsewhere shifted.
