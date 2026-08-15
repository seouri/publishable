# H4a scoping — `statistics.resample` honoured

**Measured on 2026-08-15 against `main` at `eaf3605`, read-only.** Suite green at that commit:
`uv run pytest` → 1689 passed, 2 xfailed, 85 s.

This re-measures `docs/superpowers/H4-SCOPING.md`, which was taken at `cb96c7d` and has since had
H3c-1, H3c-2 and H7a land underneath it. **Every claim below was checked against the code rather
than against that document.** Where the old scoping is right it says *verified* and moves on; where
it is stale or wrong it says so and gives the current fact.

**Headline: the charter's 15 becomes 19.** The three largest reasons: `resample.stratify_by` is a
construction rather than wiring and is the common case in the feasibility configs (§ 5 task 8); a
column contrast's percentile interval needs its own `Member` handling that no existing test would
catch getting wrong (§ 1, § 5 task 14); and `resample` declared with no `data.units` becomes a live
silent no-op the moment the refusal is retired (§ 5 task 6). Two of the old scoping's conclusions do
not survive: its § 5 trap 1's validate-time family-size bound **cannot exist as specified** (§ 4),
and `W-STATS-REPORTBY-THIN` should be **declined with a named owner** rather than claimed (§ 7).
Neither H4a's split nor its position in the order changes.

---

## 0. What the diff licenses carrying forward

`git diff --stat cb96c7d..eaf3605 -- src/` — **`stats.py` and `correction.py` do not appear.** They
are byte-identical to the commit `H4-SCOPING.md` measured at. That licenses carrying forward, without
re-grepping each line:

- § 1.1's nine-built / seven-named-and-absent / two-built-and-unwired table — **verified unchanged**.
- § 1.2's claim that `percentile_over_units` and `percentile_over_units_clustered` both already take
  `weights: Sequence[Any] | None` — **verified unchanged** (signatures at `stats.py:488` and `:552`).
- The paired estimators' shapes (`paired_t_over_units(diffs, confidence)`,
  `paired_delta_of_derived`, `paired_percentile_of_derived`) — **verified unchanged**.

What did move, and is therefore where all drift can live: `validate.py` (+1798), `units.py` (+1207),
`cli.py` (+603), `sweep.py` (+356), `templates/discovery.py` (new, +400).

---

## 1. The load-bearing claims, each re-verified

| # | Claim from `H4-SCOPING.md` | Verdict | How verified |
|---|---|---|---|
| 1 | `percentile_over_units` / `_clustered` fully written, tested, **zero production callers** | **Verified. No caller appeared.** | `grep -rn percentile_over_units src/` returns only `stats.py`'s two `def` lines plus docstring prose, and two `validate.py` *comment* lines (4213, 4264) about the absent `unpaired_` sibling. No call site anywhere. `tests/test_stats.py` exercises both directly (~20 tests, 1868–2240) |
| 2 | `E-STATS-RESAMPLE-UNSUPPORTED` emitted at `validate._check_unimplemented` on truthy `statistics.resample` | **Verified, unchanged by H7a.** | `validate.py:3138–3158`, a two-entry loop over `("resample", …)` / `("null_test", …)`, guarded `if statistics.get(field)`. `git diff cb96c7d..eaf3605 -- src/publishable/validate.py` contains **no** `±` line touching `_check_unimplemented`, `RESAMPLE` or `NULLTEST` |
| 3 | `limits.min_clusters` materialized, typed, read by nothing; docstring miscites it as `statistics.min_clusters` | **Verified.** | `materialize.py:156` writes `"  min_clusters: 10"`; `envelope.py:100` types `"limits.min_clusters": int`; `grep -c min_clusters src/publishable/validate.py` → **0**. `stats.py:617` says `statistics.min_clusters`. `reference.md:169` puts it under `limits`, and `:249` carries the § Validation row *Clusters enough to resample* |
| 4 | Derived metrics resample at a hard-coded `derived_metric_draws = 2000` in `cli.command_run`, emitting `method: percentile_over_units`, `resample_draws: 2000` | **Verified.** | Constant at `cli.py:1507`, read at `:1681`, `:1760`, `:1766`, `:1990`, `:2055`, `:2067`. Method string set in `stats.summarize_step`'s derived branch from `percentile_of_derived`'s return |
| 5 | `p_value` appears nowhere in `src/` | **Verified.** | `grep -rn p_value src/` → zero matches. H4a is bounded away from H4d |
| 6 | `min_honest_draws`: 80 / 400 / 800 / 1601 | **Verified, recomputed from the functions** | See § 4 — the 1601 is a real float artifact, not a typo |
| 7 | Six refusals in § 2 emitted where claimed | **Verified for all six**, none disturbed by H4a — see § 3 | grep of each code in `src/` |

**On claim 1, going further than the old scoping did.** Zero production callers also means *never
production-shaped input*. What `summarize_step`'s recorded-column branch (`stats.py:1340–1390`) builds
and hands `t_over_units` today is `values: list[float]`, `column_keys: list[str]`, and, when weighted,
`column_weights`. `percentile_over_units(values, seed, draws, confidence, weights)` accepts exactly
that plus a `seed`, and `resample_seed_value` is **already computed in `cli.command_run`** and already
passed to `summarize_step` as `seed=`. The gap list is genuinely short, and it is:

| Gap | Consequence for the wiring task |
|---|---|
| `t_over_units` returns `None` below **2** units; `percentile_over_units` returns `None` below 2 units **and** below `min_honest_draws(confidence)` **draws** | A declared `resample: {n: 50}` nulls `ci95` on **every column in the run**, silently. This is why § 5 task 3's `n >= 80` floor is mandatory, not optional |
| `percentile_over_units` returns a bare `Interval` — **no `draws_used`**, unlike `percentile_of_derived` (`→ (Interval, int)`) and `paired_percentile_of_derived` (`→ PairedResample`) | A column metric under `resample` must still record `resample_draws` (`reference.md:1920`). For a column the mean of a non-empty draw is always defined, so `draws_used == n` always — but that has to be a stated decision, not an omission. Own task |
| The correction pool, and **`diffs` wins the tie** | `correction._corrected_bounds` (`correction.py:158–163`) tests `member.diffs is not None` **first** and only falls through to `member.pool`. `cli._entry_for` sets `diffs=None if is_derived else tuple(diffs)`, so a column contrast **always** carries diffs today. The natural implementation — add `pool=`, leave `diffs=` alone because `cohens_dz(diffs)` still needs them — silently yields `ci95` from a percentile and `ci95_corrected` from `paired_t_over_units` **on the same row**. Nothing raises and no existing test sees it. So: under a declared `resample`, a column contrast's `Member` must carry the **pool** and must set **`diffs=None`**, while `cohens_dz` keeps computing from the local `diffs` list. The `Member` docstring's own "exactly one of `pool`/`diffs`" is the rule being honoured. Own task, § 5 item 14 |
| `weights` when `weight_by` is absent | `None`, exactly as the `t_over_units` branch passes nothing. No gap |
| Clustered | `percentile_over_units_clustered(values, keys, membership, seed, …)` takes precisely the `column_keys` + `clusters` mapping the `t_over_units_clustered` branch already builds. No gap |

So *"the unclustered column half is wiring, not construction"* — **verified, and the wiring is small.**
What is **not** wiring is `stratify_by` (§ 2) and the contrast pool (§ 5 item 14).

---

## 2. What the documents specify, kept apart from build facts

**Spec claims (the four documents, present tense, no expiry).**

- `reference.md` § The one config file, line 147:
  `resample: null                         # NOT BUILT; {method: bootstrap, n: 2000, stratify_by: []}`
  — **that is the whole inline comment.** It names one method value, `bootstrap`, in an *example
  expansion*, not as an enum. There is no `# a | b | c` enum comment for it.
- **The schema is not closed and no table enumerates it — verified.** `grep -n resample docs/*.md`
  over the four documents produces no table of legal `resample.method` values. § Statistical
  reporting's construction table (`reference.md:2304–2319`) enumerates *method strings core emits*
  (`percentile_over_units`, `paired_percentile_over_units`, …) — which are outputs, not inputs, and
  must not be confused for the enum. `envelope.py:87` types `"statistics.resample": dict` and closes
  nothing beneath it. So `CLAUDE.md`'s enum-comment rule bites in the direction the old scoping
  said: **H4a must mint the table first, then the comment.** (`assign.<axis>` is the precedent for
  closing one level in — `ASSIGN_AXIS_KEYS` at `envelope.py:193`.)
- § Statistical reporting (`:2325`): *"A derived metric is resampled whether or not you declare
  `statistics.resample`."* Declaring it *"changes the method or the count rather than switching the
  behaviour on, and the resolved values are recorded in `run.yaml` beside the interval."*
- § Weighted samples (`:1330`): *"`resample.stratify_by` says what an independent draw is, resampling
  within each stratum so a bootstrap can't return a replicate whose stratum composition the design
  ruled out."* § Validation carries the row *Resample strata exist* (`:319`) — **with no error
  identifier**; the registered `E-STATS-*` set is `CONTRAST-{NESTED,SAME-SIDES,SHAPE,UNKNOWN,WITHIN}`,
  `CORRECTION-UNKNOWN`, `REPORTBY-UNKNOWN`. H4a mints one. *(Old scoping's spec gap 1 — verified still
  open.)*
- § Clustered units (`:1361`): a draw is **rows** by default, **clusters** under `cluster_by`, and the
  interval's effective `n` is the cluster count, which joins the three-part `n`.
- `limits.min_clusters` (`:169`): *"`validate` warns when `resample` would draw fewer than this."*

**Build facts (dated 2026-08-15, `eaf3605`).**

- `resample.method`, `resample.n`, `resample.stratify_by` are read by nothing. `null_test` is read by
  nothing. `p_value` does not exist.
- `derived_metric_draws = 2000` is unconditional and is the only place the documented default is a
  real passed value (`cli.py:1502–1507` says so in its own comment, and names
  `E-STATS-RESAMPLE-UNSUPPORTED` as the reason it can be a constant).
- Column metrics get `t_over_units` / `_clustered` / `weighted_*`; derived metrics get
  `percentile_over_units` at 2000 draws; column contrasts get `paired_t_over_units`; derived contrasts
  get `paired_percentile_over_units` at 2000 draws.

---

## 3. The six refusals — does H4a disturb any of them?

All six re-verified as emitted at the sites the old scoping names. The H4a-specific question — *does
retiring `E-STATS-RESAMPLE-UNSUPPORTED` open a new route to any of the other five?* — answers **no**
for all five:

| Code | Site | Opened by H4a? |
|---|---|---|
| `E-STATS-NULLTEST-UNSUPPORTED` | `validate.py:3147`, same loop | No. Independent key |
| `E-DATA-WEIGHT-CONTRAST` | `validate.py:4138`, `_check_sweep` | No. Reads `weight_by` × resolved comparisons; `resample` is not in the guard |
| `E-DATA-CLUSTER-CONTRAST` | `validate.py:4190` | No. Same shape |
| `E-DATA-CLUSTER-DERIVED` | `stats.py:1441`, **run time** | **Already fully reachable without `resample`** — `cli.py:1507` sets `derived_metric_draws = 2000` unconditionally, so the gate `clusters is not None and seed is not None and any resample callable` fires today on a bare `cluster_by`. H4a adds no route. It does create a *new coherent state*: under `cluster_by` + declared `resample`, columns take `percentile_over_units_clustered` while derived metrics are still dropped. That is exactly what § Statistical reporting `:2325` specifies, but it wants a test |
| `E-DATA-ALLOCATION-CONTRAST` | `validate.py:4256`, per comparison | No |

**One thing H4a must not do**: `cli._entry_for`'s `paired: True` is hard-coded and its docstring
(`cli.py:~730`) says the hard-coding *"expires with `E-DATA-ALLOCATION-CONTRAST`"* — i.e. with **H4c**,
not H4a. H4a touches the same metric-block builder to add the percentile branch. Leaving `paired`
alone there is correct; a helpful "while I'm here" derivation would land H4c's task in H4a with none
of H4c's estimators behind it.

---

## 4. Trap 1's arithmetic — recomputed, and then the conclusion it does not support

**The numbers are right.** Recomputed by calling the real functions:

```
ALPHA = 0.05                       (correction.py)
min_honest_draws(c) = ceil(2 / ((1-c)/2))   (stats.py:468)
_level_for("holm", m, 1) = ALPHA / m        (rank 1 is the tightest)

family  1 → level 0.05    → conf 0.95   →   80
family  5 → level 0.01    → conf 0.99   →  400
family 10 → level 0.005   → conf 0.995  →  800
family 20 → level 0.0025  → conf 0.9975 → 1601
```

The **1601** is a genuine float artifact, not a typo: `1.0 - 0.9975` evaluates just above `0.0025`
after rounding, so `2.0/tail` lands fractionally over 1600 and `math.ceil` takes it to 1601. Worth
knowing before someone "fixes" it to 1600 in a test.

### But the conclusion — *"`validate` must bound `n` against family size (comparisons × metrics)"* — cannot be built as stated

`correction.family_shape` (`correction.py:82–100`) computes

```
comparisons = len({m.where for m in members})
metrics     = len({(m.step, m.metric) for m in members})
```

from `Member`s, and `cli` builds a `Member` per metric per comparison in `_entry_for` — **after every
execution has run**, from (a) recorded columns, which come from `io.record` calls inside user step
code, and (b) `aggregate`'s returned keys, which come from user template code. Neither is declared
anywhere in the config: `envelope.py`'s `LEAF_TYPES` has no `metrics` path, `parameter_spec` declares
*parameters*, and `hypotheses` names metrics only for the ones a user chose to pre-register.
`CLAUDE.md`'s greenfield invariant closes the door: core *"never inspects the body of user Python."*

**So the metric count is unknowable at `validate` time, by design.** What that changes:

1. A **full** `n` vs. `comparisons × metrics` bound is impossible as a § Validation row. Do not write it.
2. A **lower-bound** check is possible and worth having, because `comparisons` *is* resolvable at
   validate time — `contrasts.resolve_contrasts` already runs there, and `E-DATA-WEIGHT-CONTRAST`
   already reads the resolved comparison count. So `validate` can say: *with `k` comparisons and at
   least one metric each, Holm's tightest level needs `min_honest_draws(1 − α/k)` draws, and your
   declared `n` is below it* — a warning that is always true when it fires and silent when it might
   not be. That is one task, not the task the old scoping described.
3. The residue — that a config with many metrics can still null every `ci95_corrected` with only
   `W-STATS-CORRECTED-THIN` to show for it — is a **run-time** disclosure that already exists
   (`cli.py:2095`) and a **spec defect to file**, not a check to build.

This is the single largest reshaping in this document. Flagging it now rather than four tasks in, as
asked.

---

## 5. Decomposition: **19 tasks**

Derived by enumeration, not by adjusting 15. Grouped for review only; the ordering inside a group is
free except where noted.

**Schema and validation (7)**

1. **Mint the `resample.method` table** in `reference.md` § Statistical reporting, and fix the § The
   one config file inline comment to the `# a | b | c` form `CLAUDE.md` requires. Also decide whether
   `bootstrap` is the whole enum today — if it is, say so, because a one-value enum is a legitimate
   answer and an unstated one is not. Cross-document pass required (this edit touches a fenced schema
   example, so § Config completeness and § Enum comments both apply).
2. **Close the block one level in**, `assign.<axis>` style: `statistics.resample.{method,n,stratify_by}`
   in `envelope.py`'s `LEAF_TYPES` (`str`, `int`, `(str, list)`) plus a closed key set so
   `stratifyy_by` reports `E-CONFIG-KEY-UNKNOWN` rather than being ignored.
3. **`_check_resample`: value checks.** `method` against the enum from task 1 (new code); `n` positive
   int; **`n >= min_honest_draws(0.95)` = 80**, without which a declared `resample` nulls every
   interval in the run silently (§ 1's gap table).
4. **`resample.stratify_by` names declared attributes.** Mints the identifier § Validation's *Resample
   strata exist* row has never had; register it in § Errors `validate` reports. Reuse
   `_check_report_by`'s shape — the `data.units.attributes` declared-set test — not `units._stratum_groups`,
   which is `assign`-specific and raises `E-DATA-ASSIGN-STRATIFY-UNKNOWN`.
5. **The comparisons-only lower-bound warning on `n`** (§ 4 item 2), plus the `spec-defects.md` entry
   for the metric-count residue (§ 4 item 3).
6. **`resample` declared with no `data.units`.** `reference.md:78` marks the `units:` block *"required
   by fold, resample, null_test"* and `:1388` says resample *"isn't available"* without one. Today
   `E-STATS-RESAMPLE-UNSUPPORTED` covers that shape wholesale; retire it and a bare
   `resample: {method: bootstrap, n: 2000}` with no roster **validates clean and does nothing** —
   exactly the failure `_check_unimplemented`'s own `E-SWEEP-SAMPLE-BASELINE` comment records
   (*"Retiring it made the shape reachable without implementing them"*). Tasks 3–5 all presuppose a
   roster and none covers its absence. Copy `_check_replication`'s fold-without-basis shape, which
   reports `E-REPL-FOLD-K` when `fold_basis` is `None` for the same reason.
7. **`limits.min_clusters` made real** — the § Validation row *Clusters enough to resample* as a
   warning under `cluster_by` + `resample`, and the one-line fix to
   `stats.percentile_over_units_clustered`'s docstring, which cites it as `statistics.min_clusters`.

**Construction (3)**

8. **Stratified draw.** `percentile_over_units` gains a stratified path: draw with replacement *within*
   each stratum, preserving stratum sizes. **This is construction, not wiring** — nothing in `stats.py`
   does it, and `units._stratum_groups` is not reusable (it takes a `UnitList`, and `stats.py` is
   deliberately import-free). **Six of the seven non-null `resample:` declarations shown in the
   feasibility analysis carry a `stratify_by`** (`[truth]`, or `[consensus_label, count_stratum]`;
   only the one at line 396 omits it) — so it is the common case, not the exotic one, and not
   deferrable out of H4a.
9. **Stratified × clustered composition rule**, stated then implemented: `stratify_by` says what an
   independent draw is, `cluster_by` says the draw is a cluster. § Clustered units already requires a
   stratum be constant within a cluster for `fold`/`holdout`/`assign`; resample needs the same rule
   written down or the two declarations disagree about what one draw is. *(Old scoping trap 5 —
   verified still unowned.)*
10. **`resample_draws` for a column metric.** `percentile_over_units` returns a bare `Interval` with no
   survivor count, unlike both derived constructions. Decide and implement: return `(Interval, int)`,
   or record the requested `n` on the grounds that a column mean is never degenerate. Either is
   defensible; silence is not.

**Wiring (5)**

11. **Resolve the block once in `cli.command_run`** and thread it: `derived_metric_draws = 2000`
    becomes the resolved `resample.n` with 2000 as the documented default, and `method` /
    `stratify_by` travel beside it. Every one of the seven read sites (§ 1 claim 4) is in scope.
12. **Column-metric percentile in `summarize_step`** — unclustered and clustered, weighted and not.
    The two functions and the seed are already in hand; this is the wiring the 15-task estimate rests
    on and it is genuinely small.
13. **Stratum membership from `cli` into `summarize_step`**, aligned to *the column's own keys* — the
    same one-pass discipline the `weights` and `clusters` mappings already follow, for the reason
    `summarize_step`'s docstring gives twice ("a vector filtered differently weights the wrong unit").
14. **A column contrast's paired percentile under `resample`.** Verified empirically that
    `paired_percentile_of_derived` serves it with `compute = mean of the column` on both sides: on a
    120-unit synthetic pair it returned `[0.2242, 0.2958]` against `paired_t_over_units`'
    `[0.2230, 0.2950]` — agreeing, and returning a **pool**, which is what `correction._corrected_bounds`
    needs (§ 1's gap table). Three things the brief must carry:
    - **Set `diffs=None` on the `Member`** and let the pool answer, per § 1's gap table. This is the
      one place H4a can produce a wrong number with a green suite.
    - **Draw from `col_keys`, not `base_keys`.** The column branch narrows
      `base_keys → col_keys` on `metric_key in of_collapsed[k] and metric_key in against_collapsed[k]`;
      the derived branch does not, because a derived metric has no column to be ragged about.
      `paired_percentile_of_derived` builds its `UnitTable`s from whole rows, so handing it `base_keys`
      for a column metric feeds `compute` rows missing that column — loud if the compute indexes,
      **silent if it `.get`s**. `n_paired` stays `len(col_keys)`. *(My verification probe used 120
      units all carrying the column, so it could not have seen this.)*
    - **It rebuilds two `UnitTable`s of *n* rows per draw**, currently paid by 1–2 derived metrics and
      about to be paid by every recorded column × every comparison. Measure it, and if it is bad write
      the cheap direct construction instead — drawing index vectors once and taking column means.
15. **Echo the resolved `method`/`n`/`stratify_by` into `run.yaml`**, as § Statistical reporting
    requires (*"the resolved values are recorded in `run.yaml` beside the interval"*), including the
    `run.yaml` example in `reference.md`.

**Retirement, regression, residue (4)**

16. **Retire `E-STATS-RESAMPLE-UNSUPPORTED`** — the `_check_unimplemented` loop entry and its
    docstring paragraph, `reference.md` § The one config file's `NOT BUILT` list and line 147's
    marker, and the feasibility doc's § Executability on this build (which is dated and must be
    re-dated, not edited in place).
17. **The regression pin** (§ 6).
18. **`report_by` levels resample without minting `Member`s** — verify-and-pin rather than build; see
    § 7.
19. **The `init`-materializes-optional-blocks residual** that `spec-defects.md` routes to H4 by name.

### Should H4a be split or resequenced?

**No split.** Tasks 8–9 (the stratified draw) are the only candidate for deferral and they are the
one part 8 of 9 feasibility configs actually declare — deferring them would leave H4a honouring a
declaration two-thirds of the way, which is the exact failure `_check_unimplemented` exists to
prevent.

**One resequencing note.** Task 3's `n >= 80` floor and task 11's threading must land **before** task
12, or the first person to declare `resample: {n: 50}` gets a run whose every interval is `null` with
no diagnostic. Build validate-before-honour within the slice.

---

## 6. Trap 2 — the regression guarantee, concretely enough to pin

An undeclared-`resample` config must produce byte-identical output after H4a. **The baseline is
already partly pinned by existing tests**, which changes task 17's shape from *write a pin* to
*extend a pin*. What exists at `eaf3605`:

| Fact | Pinned at |
|---|---|
| derived metric → `method: "percentile_over_units"` | `tests/test_cli.py:2171`, `:2236`, `:6180` |
| derived metric → `resample_draws: 2000` | `tests/test_cli.py:2467`, `:4124`, `:6181` |
| derived contrast → `method: "paired_percentile_over_units"` | `tests/test_cli.py:3180`, `:3859`, `:3920` |
| column contrast → `paired_t_over_units` (or the percentile, in a parametrized pair) | `tests/test_cli.py:2631` |
| `resample_draws` `0` vs `null` vs partial (`100`, `2`) | `tests/test_cli.py:2195`, `:2335`, `:2360`, `:2403–2433` |

**The full shape H4a must not move**, for the worked example's config (undeclared `resample`, no
`cluster_by`, no `weight_by`):

- `aggregated.<step>.<column>.method` = `t_over_units`; `ci95` from it; **no `resample_draws` key**.
- `aggregated.<step>.<derived>.method` = `percentile_over_units`, `resample_draws: 2000`,
  `cohens_d: null`.
- `vs_baseline.<cond>.<step>.<column>.method` = `paired_t_over_units`, `cohens_d` = `cohens_dz`.
- `vs_baseline.<cond>.<step>.<derived>.method` = `paired_percentile_over_units`, `cohens_d: null`.
- `correction_level`, `family_size`, `family: {comparisons, metrics}` unchanged; Holm still ranks on
  `abs(delta)` over half the raw interval width (`correction._evidence_ratio`).
- The worked example's numbers in `CLAUDE.md` § The worked example — r intervals, the delta's
  `[−0.007, 0.059]`, the `repeat_spread` std 0.014 — **must not narrow.**

**The live hazard is task 11, not task 12.** Replacing the literal `2000` with a resolved value is
where an undeclared config silently acquires a different draw count. Pin `resample: null → 2000`
explicitly, and pin the *absent-key* case separately from the *`null`* case, since `_check_unimplemented`
distinguishes them (`if statistics.get(field)` is false for both, but `materialize.py` writes
neither key at all — verified: `grep resample src/publishable/materialize.py` → no match).

---

## 7. `report_by` — verified, and a recommendation the old scoping did not reach

**How a `report_by` level's interval is built today** (`cli.py:1823–2000`): for each declared
attribute, `_condition_report_by_levels` narrows the roster to the condition's own arm first, then to
the level; `level_counts` is recomputed by `attrition` over the level's own units; `level_derived` is
recomputed per level through the *same* resample closure the parent used; then one
`summarize_step(level_collapsed, level_counts, derived=level_derived, seed=resample_seed_value,
resample=strata_resample, draws=derived_metric_draws, …)` call.

**Does a level's result reach `family_members`?** **No — verified from the call site, not the
docstring.** `Member`s are constructed in exactly one place, `cli._entry_for`'s per-metric loop
(`cli.py:~845`), which iterates `sorted((set(of_summary) & set(against_summary)) - {"by"})` — the
`by` key, which is where the whole `report_by` block lives, is **explicitly excluded**, with a comment
saying why. The `report_by` block above never constructs a `Member` at all. So *"`report_by` levels
resample without minting `Member`s"* is a **property that already holds**, and H4a's task 18 is to
add the assertion that keeps it holding once levels start carrying percentile intervals — one test,
not a build.

Note that task 11 already reaches this code: `draws=derived_metric_draws` at `cli.py:1990` is one of
the seven read sites. So H4a touches `report_by` whether or not it claims anything there.

### `W-STATS-REPORTBY-THIN`'s whole-roster-vs-arm gap: **decline it, and here is the measured cost**

Still live — `validate.py:5027` counts `levels_for(roster, name)` over the **whole roster**, and
`reference.md:1899` and `:377` both record the gap as reachable since `sweep.groups` landed.

**Cost of claiming it, measured:** `validate` would have to know arm membership, and arm membership
comes from `units.assignment_for` → `ArmPlan` → `units.arm_members` (`units.py:1285`, `:1705`). Under
`assign.method: by_attribute` that is derivable from the declaration plus the roster. Under `random`
and `blocked` — the two methods H3c-2 built — **it requires performing the draw**: apportionment,
seeded shuffle, forward-only stratification on an earlier axis's *realized* membership
(`units.py:1496–1697`). `validate` currently performs no draw; `cli` realizes the plan once per run
and calls it out as such (`cli.py:350`, *"Realized **once per run**"*).

So claiming it means either (a) making `validate` realize the allocation — new: whether a validate-time
draw is legitimate at all, whether it must agree byte-for-byte with the run's, and what happens when
`assign.seed` is absent; or (b) narrowing the warning to `by_attribute` only, which is a partial fix
that needs its own message wording so a reader is not told a `random` design was checked. **Estimate:
3–5 tasks, and (a) touches `provenance.allocation_hash`'s determinism story.** That is 20–25 % of H4a
for a warning's precision, in a slice whose deliverable is a retired refusal.

**Recommendation: decline explicitly, with a named owner.** The natural owner is **H4c**, which
already has to derive `paired` from `differing_axes ∩ selectors` and is therefore the slice that
already has to reason about arm membership at comparison time. Record the decline in
`spec-defects.md` under the existing entry so the silence the old § 7 warned about does not recur.

---

## 8. Evidence payoff — the three figures reconciled, and the honest number

Three figures are in circulation and they disagree because they count three different things:

| Figure | Where | What it actually counts |
|---|---|---|
| H4a "unblocks 8 of the nine" | spine design line 163–164, and its refusal table line 113 | **Refusal-gated count**: `E-STATS-RESAMPLE-UNSUPPORTED` is the refusal 8 of the 9 configs hit. **Partly verified**: `grep -n "resample:" docs/feasibility-llm-growth-studies.md` shows eight declarations, seven non-null and one explicit `resample: null` (line 433). E1 is shown in full and the rest show only differing blocks, so which config inherits which block is not recoverable by grep — the 8/9 figure is the spine design's and I did not re-derive it |
| H4a → **0** | spine design slice table, line 193 (*"After it, of the nine"*) | **Cumulative end-to-end executable** |
| "H4a and H3d then unblock six" | `CLAUDE.md` § Repository status | **Cumulative executable, for configs sourcing their roster from a table** — the six screening runs E1–E6, which are blocked additionally by `holdout` (H3d). The last three, C1–C3, need H4b's weighted contrasts |

**Confirmed, as you expected: H4a on its own makes zero new experiments execute end-to-end.** Verified
directly against `docs/feasibility-llm-growth-studies.md`:

- E1–E6 declare `holdout:` (line 139 and the shared-roster block) → `E-DATA-HOLDOUT-UNSUPPORTED`,
  which the doc's own table at line 958 scores 6 of 9. **H3d.**
- C1–C3 declare `weight_by: sampling_weight` (line 507) beside a baseline → `E-DATA-WEIGHT-CONTRAST`.
  **H4b.**
- And **all nine** declare `from: {resolver: patient_trajectory}` → `E-DATA-RESOLVER-UNSUPPORTED`, so
  *as the analysis writes them* none executes until H7b regardless. The 6/3/9 figures all assume the
  table-roster substitution.

**Write H4a's justification as: one refusal retired that 8 of 9 configs hit, a regression preserved,
and zero experiments newly executing.** That is defensible and it is true. "Unblocks 8 of the nine"
is true only of the refusal count and will read as the executable count a month later — which is
precisely the undated-build-claim failure `CLAUDE.md`'s feasibility procedure step 10 exists to
prevent.

---

## 9. What H7a changed underfoot

`validate_config`'s prologue was reordered (`15ee377`, "Hoist `find_repo_root` above the template check")
and now runs: `load_document` → `_check_shape` (early return) → `find_repo_root` → `resolve_template`
(early return on `E-TEMPLATE-LOAD` / `E-TEMPLATE-COLLISION`, early return on `E-TEMPLATE-UNKNOWN`) →
entrypoint import → the `_check_*` sequence. Within that sequence `_check_unimplemented`
(`validate.py:625`) still sits **after** everything that resolves the roster (`_check_units`,
`_check_measurements`, `_check_weight_by`, `_check_cluster_by`, `_check_assign`,
`_check_fold_stratify_by`, `_check_replication`) and **before** `_check_sweep`, `_check_contrasts`,
`_check_hypotheses` and `_check_report_by` — the same relative position it held at `cb96c7d`.

**Collision with H4a: none, with one caveat.** `_check_unimplemented`'s body is untouched by the H7a
range. But three of H4a's new checks (tasks 3, 4, 5) belong *after* `_check_units` (they need the
resolved roster and the declared attributes) and task 5 needs the resolved comparison family, which
`_check_sweep` computes at position nine. **The new `_check_resample` therefore sits between
`_check_unimplemented` and `_check_contrasts`, or after `_check_sweep`** — deciding which is part of
task 3, and it is the one ordering question H4a inherits from H7a's reshuffle.

Also relevant: `resolve_template` now returns early on three template faults. A config that both names
an unknown template *and* declares a bad `resample.method` reports only the first — correct, and the
same treatment every other check gets, but it constrains how H4a's tests are fixtured (a local
`templates/` fixture is now the cheap way to get past that gate; `tests/test_templates.py` grew 968
lines of them).

---

## 10. What is NOT in H4a

Unchanged from `H4-SCOPING.md` § 7 and re-verified: `null_test` and everything `p_value`-shaped
(H4d); the weighted and clustered contrast families (H4b); the unpaired family and `paired` becoming
derived (H4c); `data.units.holdout` (H3d); the plugin registry and `{resolver: …}` (H7b); folds
within cells (H3c-3); `study`/`report`/`diff`/`freeze` (H8); a `summary`-step `Estimate`, which is
`reported: true` and never recomputed — **a resample pass that walks every metric block must skip
it**, and H4a's task 12 is exactly such a pass, so this is a test H4a owes rather than a boundary it
merely respects.

Newly added to this list by this measurement: **`W-STATS-REPORTBY-THIN`'s whole-roster gap**, declined
with a named owner (§ 7), and **a validate-time family-size bound on `resample.n`**, which § 4 shows
cannot be built.
