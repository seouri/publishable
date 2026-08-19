# H4d scoping — `statistics.null_test`, and retiring `E-STATS-NULLTEST-UNSUPPORTED`

Read-only measurement against `main` at `2a4dc53`, on 2026-08-18. This re-scopes the H4d row of
`docs/superpowers/H4-SCOPING.md`, written at a commit **before H4a, H4b-1, H4b-2 and H4c existed**,
and four slices have since rebuilt every surface H4d must touch — the contrast record, `Member`,
`_corrected_bounds`, and the correction family itself. Every identifier below was grepped, read or
probed at `2a4dc53`; nothing is carried. Where this document contradicts a predecessor it says so and
shows the command.

**Verdict: 27 tasks**, against the charter's **13**. The direction is the repo's usual one — up. Two of
the charter's three named `validate` checks are **not H4d's work at all** (one already ships, one
refuses a shape the schema cannot express), and the buckets that replace them are larger than the row
they came from.

**Baseline at `2a4dc53`:** `uv run pytest` → **2275 passed, 1 skipped, 2 xfailed**, 142.85 s, run in
the foreground.

**The payoff, stated plainly and without hedging: H4d unblocks ZERO configs**, and it moves neither
count H4b-1, H4b-2 and H4c left — **six with no remaining core-side blocker, three executable**.
Measured in § 5, with a control that can fail. What H4d is worth instead is stated there, and it is
the largest specification-versus-code gap left in the repo: the permutation engine, the p-value, and
`fdr_bh` are **all three entirely unbuilt**, while the four documents describe all three in the
present tense across nine sections.

---

## 0. Executive summary — the six things that change what H4d is

1. **`fdr_bh` cannot be made real without deciding an ordering `reference.md` refuses to supply, and
   the fix converts a per-member loop into a two-pass procedure.** `correction._level_for` returns
   `None` for `fdr_bh` today, so BH corrects nothing. Benjamini-Hochberg's *i* is definitionally the
   rank in ascending **p-value**; `rank_family` ranks on `_evidence_ratio` (|delta| over half the raw
   width), and § Statistical reporting explicitly forecloses mixing the two — *"Ranking on a p-value
   where one exists and on this ratio elsewhere would leave the family ordered by two statistics,
   which is not an ordering."* **`fdr_bh`'s own *i* is named nowhere in the four documents**
   (`grep -n 'fdr_bh\|Benjamini' docs/reference.md` → nine hits, read in full, none states it). And
   both Holm's step-down and BH's step-up enforce monotonicity **across** the ranked family, where
   `corrected_for` computes each member's level independently in one pass. § 2.
2. **A p-value needs a `Member` *field*, not a fourth evidence kind — and that is the small half of
   the finding.** The three kinds exist because `_corrected_bounds` must rebuild the *same
   construction* at a smaller α. A p-value needs no evidence rebuilt: only a rank and a family size,
   both already inside `corrected_for`. So `Member.p_value: float | None` plus a `p_value_corrected`
   output key is the shape, and the exactly-one rule is untouched. The cost is entirely in § 0.1's
   loop structure, not in the dataclass. § 2, § 4.
3. **The p-value's two documented landing sites are both unproducible as written, for two different
   reasons.** § What isn't a repeat's table says a group-axis shuffle's p-value lands *"On the
   contrast, in `vs_baseline`"* — the claim H4c proved false one section over and repaired in
   § Allocation, **left unrepaired here**. Re-probed at this commit: a baseline fixing a group level
   earns `E-SWEEP-BASELINE-GROUP` (permanent), and a parameter-only baseline expands over the group
   axis so no cross-arm comparison is generated at all. And the same section's `aggregated:` example
   shows `p_value: 0.0004, p_value_corrected: 0.0028` on a **per-condition** metric block — a shape
   with no correction plumbing anywhere: `cli.py` builds a `Member` at exactly one site, inside
   `_comparison_step_blocks`, and `_entry_for` resolves only `cond:` and `contrast:` addresses.
   § 3, § 4.
4. **`statistics.null_test` is a whole leaf in `envelope.LEAF_TYPES`, and both precedents say to close
   it *before* the refusal retires.** `resample` and `holdout` were each closed one level in ahead of
   their own wholesale refusal lifting, on the validate-before-honour ground `envelope.py` states
   twice. `null_test` is still `dict`, so a `shufle` typo is unreachable by any check the instant the
   refusal goes. **Probed: it is unreachable today too** — a typo'd subkey earns
   `E-STATS-NULLTEST-UNSUPPORTED` and nothing else. § 1.
5. **`E-STATS-NULLTEST-UNSUPPORTED` is the sole blocker for *five* distinct fault shapes, not one.**
   Probed as exact code sets: a typo'd subkey, an out-of-enum `method`, a `shuffle` naming an
   undeclared attribute, an `n` below any floor, and a declaration with no `data.units` — **every one
   returns `{E-STATS-NULLTEST-UNSUPPORTED}` alone**. The moment it retires, all five validate clean.
   Two of them are § Validation rows with no code behind them today. § 1.
6. **H4c built the predicate the narrowed `W-STATS-CORRECTION-INAPPLICABLE` needs, which makes one
   task smaller.** The § Validation row's condition is a three-way disjunction the check tests none
   of; `contrasts.crossed_group_axes(of, against)` — minted by H4c as the single expression for
   "does this comparison cross a group axis" — answers the load-bearing disjunct per comparison.
   § 4.

---

## 1. Every site of the refusal, and everything else standing between a config and a permutation test

`validate._check_unimplemented` was read in full first, then confirmed by grep. `reference.md`
§ Errors carries one row per code covering **every** emit site, so the unit of work is every site that
raises *or* reports it — the discipline a task once scoped by a helper's single call site got wrong.

| Site | Kind |
|---|---|
| `validate.py`, `_check_unimplemented`, `if statistics.get("null_test")` | **The one emit.** Truthy-guarded, so `null_test: {}` and `null_test: null` are not declarations — probed, both clean |
| `validate.py`, the 30-line comment above it | Names `null_test` as the last member of the silent-no-op family and states `resample`/`contrasts`/`report_by`/`hypotheses`/`correction` each left it |
| `validate.py`, `_check_sweep`'s `W-STATS-CORRECTION-INAPPLICABLE` comment | *"narrowed by whichever slice implements `null_test`"* — the refinement § 4 measures |
| `validate.py`, `_check_resample`'s no-roster comment | Cites § The one config file's *"required by fold, resample, null_test"* line for a check `null_test` does not have |
| `validate.py`, `_accounted_attribute_names` | **A live reader of the unbuilt block.** `null_test.shuffle` suppresses `W-DATA-CLUSTER-UNDECLARED` for that attribute *today*, because `validate` collects rather than aborting |
| `envelope.py`, `"statistics.null_test": dict` and the module comment above `LEAF_TYPES` | The whole-leaf entry, and the comment listing `.null_test` among blocks "declared at their own key with the one outer type" — § 0.4 |
| `units.py` and `design-principles.md` § The shape your input must have is derived | `null_test.shuffle` named as one of eight parallel field-namers; both stay true after H4d |
| `replication.py`, `REJECTED_KINDS` | `"permutation": "declare `statistics.null_test` instead"` — the pointer the retirement makes honest |
| `reference.md` § The one config file | The `NOT BUILT` marker, **and** the sentence *"One declaration above is not yet built"* — § 6 |
| `reference.md` § Validation, two rows | *Null test coherence* and *Shuffle level is unambiguous* — **neither has any code, any emit site, or any § Errors row** |
| `reference.md` § Statistical reporting, four passages | The `correction` table's two `p_value_corrected` cells; the ranking-statistic paragraph; the `fdr_bh` paragraph; the *"does not add a place in the family"* paragraph |
| `reference.md` § What isn't a repeat | The two YAML blocks, the landing-site table, the parameter-axis exclusion, and the `null_test` row of *What each declaration replaces* |
| `reference.md` § Clustered units, § Where units come from, § How artifacts are organized | The permutation level rule; the "isn't available without a roster" sentence; `units.parquet`'s *"`resample`/`null_test` rebuild it"* |
| `experimental-designs.md` § Bootstrap and permutation, § Matched case-control, § Allocation, § Mistakes core prevents | Four sites, one of them a **prevented-mistake row** — *A permutation that shuffles away the matching* — whose guarantee is delivered today by the wholesale refusal alone |
| `tests/test_validate.py` | **7 lines** naming the code, including two exact-set assertions and the `-UNSUPPORTED`-family parametrize (§ 6) |
| `feasibility-llm-growth-studies.md` § Executability on this build | One table row, to be **re-dated rather than edited**, per the development-record rule |

**Can-fail control on the same file list:** `grep -rn 'E-STATS-RESAMPLE-UNSUPPORTED' src/ docs/reference.md`
→ **exit 1** (the code is retired), on files where `E-STATS-NULLTEST-UNSUPPORTED` returns hits.
A different answer from the same sweep shape is what says the sweep can fail. The file **list** was
filtered, never the output.

### What the refusal is hiding — probed, not reasoned about

`validate` collects rather than aborting, so a refusal elsewhere never makes a later check
unreachable; the only honest way to know what a config earns is to run it. Nine shapes through
`validate_config`, error codes as exact sets:

| Shape | Exact set at `2a4dc53` |
|---|---|
| `null_test: {method: permutation, n: 5000, shuffle: label}` | `{E-STATS-NULLTEST-UNSUPPORTED}` |
| the same with `shufle:` for `shuffle:` | `{E-STATS-NULLTEST-UNSUPPORTED}` |
| the same with `method: bootsrap` | `{E-STATS-NULLTEST-UNSUPPORTED}` |
| the same with `shuffle: nope_not_an_attr` | `{E-STATS-NULLTEST-UNSUPPORTED}` |
| the same with `n: 3` | `{E-STATS-NULLTEST-UNSUPPORTED}` |
| the same with the whole `data.units` block removed | `{E-STATS-NULLTEST-UNSUPPORTED}` |
| `null_test: {}` — the can-fail control | `{}` (clean) |
| `null_test: null` — the second control | `{}` (clean) |
| no `null_test` key at all — the third control | `{}` (clean) |

**Five real faults, one code, nothing underneath it.** Two of the five are § Validation rows
(*Null test coherence*, *Shuffle level is unambiguous*); one is the filed
`E-STATS-NULLTEST-UNITS` gap; one is the closed-schema gap § 0.4 measures; and one — the `method`
enum — has **no table anywhere**, where `resample.method`'s enum was written down by H4a precisely so
"adding a second is a documented change rather than a silent one".

Two further probes with a sweep declared, since the correction warning is guarded on
`comparisons > 0` and a base config generates none:

| Shape | Exact set at `2a4dc53` |
|---|---|
| `grid` + `baseline` + `correction: fdr_bh`, no `null_test` | `{W-STATS-CORRECTION-INAPPLICABLE}` |
| the same **plus** `null_test` | `{E-STATS-NULLTEST-UNSUPPORTED, W-STATS-CORRECTION-INAPPLICABLE}` |
| the same with `correction: holm` — the control | `{E-STATS-NULLTEST-UNSUPPORTED}` |

The second row is the one to carry: the two fire **together**, exactly as `spec-defects.md` records,
and the warning's message — *"no comparison in this family can carry one in this build"* — becomes
**false** the instant the engine lands. That is the narrowing H4d owes, and it is owed in the *same
change* that makes p-values reachable, not a change later.

---

## 2. What exists, what is named, and what is vapour

Read `stats.py`'s definition list in full (43 module-level functions), then grepped.

**Nothing exists. Not one line of it.**

| Sweep | Result at `2a4dc53` |
|---|---|
| `grep -rn 'p_value' src/` | **1 hit** — and it is a comment in `validate.py` saying *"`p_value` exists nowhere in this build"* |
| `grep -rn 'ci95_corrected' src/` — the can-fail control | **20 hits**, over the same file list |
| `grep -rn 'permutation' src/publishable/stats.py` | **0 hits** |
| `grep -rho 'E-STATS-NULLTEST[A-Z-]*' src/ docs/ tests/` | `E-STATS-NULLTEST-UNSUPPORTED` ×42, `E-STATS-NULLTEST-UNITS` ×1 — and the second is the *proposal* text inside `spec-defects.md`, not a code |

So unlike H4c — which inherited a complete, symmetric paired half to derive its counterparts from —
**H4d has no neighbouring construction to copy.** The charter's own ordering note said this and it is
still true: H4d *"is the only sub-slice with no existing code to build on."*

### The vocabulary the documents already name, and what backs each

| Named in the four documents | Backed by |
|---|---|
| `p_value` on a metric block | Nothing |
| `p_value_corrected` on a metric block | Nothing |
| `null_test: {method, n, shuffle}` echoed beside a metric | Nothing — and the resolved-values echo rule, which `resample` follows, is not stated for it either |
| `method: permutation` | Nothing, **and no enum table** — § Resample methods gives `resample.method` a closed one-row table and says why; `null_test.method` has no counterpart |
| The within-cluster / whole-cluster level derivation | Nothing |
| The group-axis "permuted within cells of every *other* group axis" rule | Nothing |
| `fdr_bh` producing an adjusted p-value | Nothing — `_level_for` returns `None` and `corrected_for` writes `ci95_corrected: None` |

**`fdr_bh` is the sharpest instance in this table, because it is not merely unbuilt — it is
under-specified in a way a slice cannot resolve by reading.** § Statistical reporting says three
things that together do not close:

- BH *"needs p-values"* and reports *"`p_value_corrected`, Benjamini-Hochberg adjusted"*;
- the family's ranking statistic is the evidence ratio, chosen *because* the family "often carries no
  p-values at all";
- and ranking on two statistics "is not an ordering."

BH's adjustment is *defined* over the p-value ordering. Under the evidence-ratio rank it is not
Benjamini-Hochberg; under a p-value rank the family carries two orderings. **The decision is H4d's,
it has grounds available on both sides, and by `CLAUDE.md`'s rule and H4b-1's precedent the four
documents change before any code emits an adjusted p-value.** A third reading is available and should
be argued explicitly rather than assumed away: BH may rank *within the p-value-carrying subset* while
the interval ranks over the whole family, which is two procedures over two families rather than two
orderings over one — that is a coherent position, and it is not what any document currently says.

**And the loop is one pass.** `corrected_for` iterates `rank_family(family)` computing
`_level_for(method, family_size, rank)` per member independently. Holm's *p*-adjustment is
`max` over the prefix, BH's is `min` over the suffix; neither is expressible as a per-member function
of `(m, i)` alone. Making `fdr_bh` real is therefore a change to the **shape** of `corrected_for`,
shared with `hypotheses.py`, which calls the same function for its own family — a second caller no
charter names, on the H4c precedent where `correction.py` turned out to be a second production call
site nobody had listed.

---

## 3. Where a p-value lands, and why neither documented home works today

`cli.py` constructs `Member` at exactly **one** site — inside `_comparison_step_blocks`, the function
that builds a comparison's metric block. `_entry_for` resolves a corrected field onto a record entry
addressed `cond:<index>` (a `vs_baseline` block) or `contrast:<id>` (a declared entry) and nothing
else. Every `ci95_corrected` in `reference.md` sits on one of those two shapes. **A per-condition
`aggregated` metric block has no `Member`, no `where`, and no correction fields at all.**

Against that, § What isn't a repeat's landing-site table:

| `shuffle` names | Documented home | Measured status at `2a4dc53` |
|---|---|---|
| An ordinary unit attribute | *"One per condition, beside that condition's estimate"* | **No plumbing exists, and the family definition excludes it.** The family is comparisons × metrics and a per-condition estimate is not a comparison. The section's own YAML shows `p_value_corrected: 0.0028` there anyway |
| A `groups` axis attribute | *"On the contrast, in `vs_baseline`"* | **Unreachable, and the claim is the one H4c retired one section over** |

### The `vs_baseline` claim, re-probed rather than carried

`H4c-SCOPING` § 4 established this and H4c repaired § Allocation for it (commit `24a6241`, which moved
the unpaired example into a `results.contrasts` block, and `6b9bf11`, the citation sweep). Re-probed
here at `2a4dc53`, because a scoping expires:

| Shape | Exact set at `2a4dc53` |
|---|---|
| `groups` + `assign` + `grid`, baseline fixing `arm: control` | `{E-SWEEP-BASELINE-GROUP}` |
| the same, baseline fixing the parameter axis only | `{}` — clean, and **no cross-arm comparison is generated at all**, the baseline expanding over the group axis |
| the same with neither — the control | `{}` |

`E-SWEEP-BASELINE-GROUP` is permanent: it rests on § Expansion modes' *the arms of a group axis are
peers* and on `experimental-designs.md` § Mistakes core prevents' *two identical measurements reported
as two arms*, a structural impossibility rather than a temporary gap. **So a group-axis p-value's only
reachable home is a declared `statistics.contrasts` entry, exactly as an unpaired delta's is.** The
§ What isn't a repeat row is a stale claim H4d inherits, and it is a textbook instance of
`CLAUDE.md`'s *sweep for the claim, not for the file the claim was first noticed in* — H4c's sweep
covered § Allocation and its citations and stopped one section short of the sibling sentence saying
the same thing about a different field.

### The per-condition home is the harder half, and it is a design decision

This is the same class as H4c's unreachable `vs_baseline` example — **the only place the shape is
written down is a config no run can produce** — but it is worse, because the ordinary-attribute row is
the *first* row of the table and the common case. Three readings, and H4d must choose one on grounds
and change the document first:

- **The p-value travels uncorrected on the `aggregated` block.** Cheapest; contradicts the § What
  isn't a repeat YAML, which shows `p_value_corrected` there.
- **Per-condition p-values form their own family**, corrected at their own size, the way
  `hypotheses.py` already does. Coherent with the two-family precedent; requires a third family and a
  third `where` prefix, and § Statistical reporting's *"does not add a place in the family"* sentence
  has to be re-read as scoped to the comparison family (which is what it says, on its own terms).
- **Per-condition estimates join the comparison family when they carry a p-value.** Directly
  contradicts *"The family is comparisons × metrics"* and *"a metric reported without an interval
  isn't a comparison anyone can read as significant"*, and inflates every existing corrected interval
  in every run that declares `null_test`. Named here so it is rejected with a reason rather than
  never considered.

**Note the arithmetic in the document's own example**, because it is evidence about which reading was
intended and it does not settle it: `0.0004 → 0.0028` is ×7, which is Bonferroni at `m = 7` or Holm at
`m − i + 1 = 7`. Neither is derivable from the surrounding text, which describes no family that
example belongs to. Treat it as a number to be **re-derived and re-authored**, not as a constraint.

---

## 4. What H4a, H4b-1, H4b-2 and H4c changed underneath H4d

Each row says whether it makes H4d **smaller**, **larger**, or **differently shaped**.

| What changed | Direction | Measured |
|---|---|---|
| `Member` gained a third evidence *kind* (`sides`) and two mutually-exclusive modifiers, with the exactly-one rule counted over three | **Neither — and this is the finding that keeps H4d small in one place** | A p-value is not evidence: `_corrected_bounds` rebuilds a construction, and a p-value has no construction to rebuild at a smaller α. So H4d adds a **field** (`Member.p_value`) and an output key, and touches neither `__post_init__`'s count nor any of `_corrected_bounds`' six return paths. Verified by reading all three: every branch consumes `sides`/`diffs`/`pool` to call a *t* or read ranks off a pool, and none reads a scalar |
| `_corrected_bounds` has six return paths after H4c | **Neither** | Same reason. H4d adds no seventh |
| `corrected_for` is a single-pass per-member loop | **LARGER, and named by no charter** | Holm's and BH's p-adjustments are prefix/suffix accumulations across the ranked family. Making either real changes the loop's shape, and `hypotheses.py` is a second caller of the same function |
| H4c minted `contrasts.crossed_group_axes` as the one expression for "does this comparison cross a group axis" | **SMALLER** | `W-STATS-CORRECTION-INAPPLICABLE`'s three-disjunct condition needs exactly that predicate per comparison, and `_check_sweep` already imports and loops over `resolved_contrasts` with `conditions_by_index` in scope — the same loop `E-DATA-WEIGHT-ALLOCATION-CONTRAST` fires from. The narrowing is local |
| `paired` is now derived, and a comparison's `method` selection is a twelve-cell branch across two sites | **Differently shaped** | A p-value attaches per comparison regardless of pairing, so H4d adds one conditional key rather than a thirteenth cell. But the **derived-key-collision corner** those two sites contain has now been given **five wrong grounds across two slices**, every one an answer from a proxy, and only an end-to-end `run` ever exposed it. Any H4d change inside `_comparison_step_blocks` inherits that verification rule |
| H4c repaired § Allocation's unreachable `vs_baseline` record and swept its citations | **LARGER by omission** | The sweep stopped one section short: § What isn't a repeat still routes a group-axis p-value to `vs_baseline` (§ 3) |
| H4b-2 minted the degenerate-draw refusal; H4c minted `E-DATA-WEIGHT-ALLOCATION-CONTRAST`; `E-DATA-WEIGHT-CLUSTER-CONTRAST` stands | **SMALLER, measurably** | A permutation null recomputes a metric under a relabelling, and it does so **once per metric**, not once per contrast cell. The paired/unpaired × plain/weighted/clustered space H4b-1 through H4c had to fill six-fold does **not** replicate here: the null distribution is built over the unit table, and the weighted and clustered forms differ only in *what one draw is* — the same two-way choice `resample` already makes. **H4d builds two draw shapes (rows, clusters), not six** |
| H4a wired `resample_columns`, so a declared `resample` routes column contrasts through the percentile branch | **Differently shaped** | A p-value is orthogonal to which interval construction was used, which is precisely why the ranking statistic is not a p-value. No interaction, checked by reading `_corrected_bounds` and `rank_family` |

### How many cells a `null_test` must actually serve

Asked explicitly, because H4b-1's charter mis-sized itself by assuming a construction family
replicates across the modifier axes. **It does not replicate here**, and the reason is structural: a
permutation null is built by relabelling the unit table and recomputing, so the modifiers change the
*draw*, not the *estimator*. The real cells are:

| Axis | Values | Why |
|---|---|---|
| What one draw is | **2** — rows, or whole/within clusters | § Clustered units, the same rule `resample` follows |
| What is recomputed | **2** — a recorded column, or a template's `aggregate` | `stats.percentile_over_units` versus `percentile_of_derived`, the existing split |
| What the null is *of* | **2** — one condition's estimate, or a cross-arm contrast | § What isn't a repeat's landing-site table |

**Eight cells, of which the cluster axis collapses to a level derivation rather than a second
construction**, and of which the contrast half is reachable only through a declared
`statistics.contrasts` entry (§ 3). That is smaller than H4c's six unpaired constructions in
construction count and larger in *decision* count, which is the honest way to state it.

---

## 5. The payoff, dated and pinned

### Measured on 2026-08-18 against commit `2a4dc53`

**No config in `docs/feasibility-llm-growth-studies.md` declares `statistics.null_test`, and none is
unblocked by H4d.** Both counts stay exactly where H4b-1 left them and H4b-2 and H4c did not move:
**six with no remaining core-side blocker, three executable.** The six are C1, C2, C3, E1, E2 and E5;
the three are E1, E2 and E5, C1–C3 still needing `io.reuse_from`, which is unbuilt and unowned.

Measured on the nine configs' own declarations rather than derived from the analysis's prose:

| Sweep | Result |
|---|---|
| `grep -n 'null_test' docs/feasibility-llm-growth-studies.md` | **8 hits, every one `null_test: null`** — an explicit null, which `_check_unimplemented`'s truthy guard treats as undeclared, probed clean in § 1 |
| `grep -c 'resample: {' …` — the positive control | **7**, on the same file, for a block that *is* declared in a truthy form. The same sweep shape returns a different answer for a string present as a real declaration, which is what says it can fail |
| `grep -n 'correction:' …` | **8 hits — seven `holm`, one `none`. Zero `fdr_bh`** |

Three readings follow. No config reaches `E-STATS-NULLTEST-UNSUPPORTED` at all, so retiring it
executes nothing. No config declares `fdr_bh`, so the one warning H4d narrows fires for none of them
either. And eight `statistics` blocks cover nine configs because E1–E6 and C1–C3 share blocks — the
count is of blocks, and it was read rather than assumed.

**A retired-refusal count is not an executable-run count.** Both review verdicts on H4b-1 faulted that
conflation, and a *correction* on H4b-2 inverted the same two numbers and named a retired refusal as
live. H4d retires one refusal that **zero of nine** configs hit, closes no live defect for any of
them, and leaves three executable.

**What H4d is worth instead**, stated so it is not mistaken for nothing:

- It is the **last slice in the charter whose surface is the `statistics` block**, and five
  `spec-defects.md` filings are queued behind it — three of them declined by three or four consecutive
  slices and marked **terminal** by name (§ 6). After H4d there is no further slice for a fifth
  deferral to point at.
- It closes the repo's largest remaining **specification-versus-code** gap. `p_value` appears once in
  `src/`, in a comment saying it appears nowhere; the four documents describe it, `p_value_corrected`,
  `fdr_bh`, a `method` enum, a cluster-level derivation and a group-axis routing rule, across nine
  sections, all in the present tense.
- It is the only slice that makes `statistics.correction: fdr_bh` — a value `validate` accepts, a
  generated config's comment offers, and § The one config file enumerates — mean anything at all.
  Today it is an accepted declaration that nulls every corrected interval and reports nothing in their
  place, which is the exact state § Statistical reporting says that section exists to prevent.
- It empties the `NOT BUILT` list in § The one config file. H7b Part B's scoping predicted that count
  *"drops to one"*; that prediction is now due and **overtaken** — it drops to **zero**.

That is a specification-integrity payoff, not an execution payoff, and it should be argued as one.
The measured consequence, and the whole of it: **nothing in the feasibility analysis gets closer to
running because H4d landed.**

---

## 6. The pins H4d must satisfy, and the filings it inherits

### Two tests that go vacuous or red the moment the code retires

| Pin | What it asserts | What H4d must do to it |
|---|---|---|
| `tests/test_validate.py::test_the_unsupported_family_is_down_to_null_test` | The **exact set** `{"E-STATS-NULLTEST-UNSUPPORTED"}` for a config declaring one, with a docstring saying "the family it left is not empty — a sweep asserting only an absence would pass identically if the whole family had been deleted" | **Convert, not delete.** The set becomes `{}` and the test goes red — the tripwire working. Its replacement must keep the docstring's own argument alive against the code that survives (below) |
| `tests/test_validate.py::test_every_unsupported_message_defers_rather_than_scolds` | Parametrized over **one** remaining row, asserting the finding set is non-empty *and* that every message says "later slice" | **Convert, not delete.** Removing the row leaves an empty parametrize; keeping it leaves a red assertion. Either way the test stops testing, which is the "a control asserting only absences" shape one axis over |

**The `-UNSUPPORTED` family does not empty, and saying it does would be wrong.**
`grep -rho 'E-[A-Z0-9-]*-UNSUPPORTED' src/` returns six codes, of which four are mentions in comments
about retired codes and **two are live emits**: `E-STATS-NULLTEST-UNSUPPORTED` and
`E-TEMPLATE-INSTALLED-UNSUPPORTED` (two emits, in `validate.py` and `generators/experiment.py`, plus
a docstring mention in `templates/registry.py`). § The one config file already distinguishes them — the installed-template
refusal *"is not a declaration at all and so is marked nowhere above"*. So the **declaration** half of
the family empties; the family survives, and the sentence *"That whole family is deliberately absent
from the validate-time registry"* must **survive with it**. Per `CLAUDE.md`, prefer deleting the count
claim to rewriting it: *"One declaration above is not yet built"* is a self-maintaining sentence only
while there is one, and an enumeration replacing it is a second source of truth nobody owns.

A third pin is available as a precedent rather than an obligation:
`test_the_retired_resample_code_appears_nowhere_in_src` sweeps every `src/**/*.py` for the retired
string, filtering the **file list** and guarding against a vacuous scan. H4d should add its
counterpart, since that is how H4a's retirement was made durable rather than momentary.

### Five filings, three of them declined by three or four slices and marked terminal

Each must be claimed or re-declined **in writing**, and for the terminal ones a decline is no longer
available in the form previous slices used.

| Filing | Why it is H4d's | Measured status at `2a4dc53` |
|---|---|---|
| `statistics.null_test` has no no-units check | Filed by H4a task 7's review naming *"whichever slice retires `E-STATS-NULLTEST-UNSUPPORTED` (H4d)"*, with the code (`E-STATS-NULLTEST-UNITS`), the expression (`not (doc.get("data") or {}).get("units")`) and the report-without-returning rule all specified | **Live, and confirmed by probe** (§ 1): a `null_test` with the whole `data.units` block removed earns only the wholesale refusal. Claim it — the entry has already done the design |
| *A column resample is only ever defined given finite inputs* | Re-declined by H4c task 20 with a measured ruling — "the premise is confirmed likelier but the fix is a task, not a line" — and **Owner: H4d**, on the terminal reasoning | **Live.** H4d recomputes metrics over relabelled tables, which is the same finiteness surface one construction over. Two `*_is_a_known_unfixed_gap` tests pin it and must be updated *with* this entry if closed |
| `W-STATS-REPORTBY-THIN`'s whole-roster-versus-arm gap, and the `report_by` `resample_columns` asymmetry | Declined by H4a, H4b-2 and H4c in turn. **Owner: H4d, and the entry names H4d as terminal in writing**: *"If H4d does not close it, the correct move at that point is not another deferral — it is converting this into a documented, permanent limitation"* | **Live on C1–C3**, created by neither a weight, a cluster, nor a pairing derivation, and **genuinely unrelated to `null_test`**. So the honest H4d task is the conversion the entry prescribes — a § Statistical reporting sentence or a § Validation row — not a fourth decline and not a surprise fix |
| *The contrast path discloses nothing about its resample* — Findings 1 and 3 | Re-declined by H4b-2 and by H4c task 20; **Owner: H4d** | **Live.** Finding 1 needs a contrast-scope `where`-carrying thin warning and a § Warnings registry row; Finding 3 needs a resolved-`resample` echo on the contrast entry. H4d adds a `null_test` echo to the same entries (§ 2), so the "no new disclosure surface" ground is unavailable to it as it was to H4c |
| `E-DATA-CLUSTER-DERIVED` — the clustered derived draw | Re-declined by H4c task 20 **on a new ground**: H4c gave the derived branch a second suppression condition, and building the clustered derived draw inside it would have made one guard distinguish three states. **Owner: H4d** | **Live, and now the nearest neighbour of H4d's own work**: a clustered permutation of a *derived* metric is the same recompute-over-a-clustered-draw construction. The two-ground guard has now shipped and survived a whole-branch review, which is the condition H4c named for building it |

Two further routed rows, neither in the five: `spec-defects.md`'s *Row 284 "Correction can be
applied"* (the three-disjunct condition, routed to "H4 Statistics") and the
`W-STATS-CORRECTION-INAPPLICABLE` entry's amendment (*"H4 must make the warning conditional in the
same change that makes p-values reachable, or the warning becomes false the moment `null_test`
works"*). Both are H4d's by elimination and are § 7's task 9.

---

## 7. Decomposition: 27 tasks, against the charter's 13

The charter's H4d row reads: *"the permutation engine; `p_value` / `p_value_corrected` plumbing;
attribute-shuffle vs. group-axis-shuffle routing; cluster-level permutation; `fdr_bh` made real for
the first time; `W-STATS-CORRECTION-INAPPLICABLE` narrowed; validate checks (`shuffle` names an
attribute, collides with no recorded column, an all-permuted design has no unpermuted value) — 13."*

| # | Task | Depends on |
|---|---|---|
| 1 | **The `fdr_bh` ordering decision** (§ 2): which *i* BH adjusts on, argued against § Statistical reporting's two-orderings sentence, in `reference.md` before any code emits an adjusted p-value | — |
| 2 | **The p-value landing decision** (§ 3): where a per-condition p-value is recorded and in which family, if any, it is corrected — the three readings named and one chosen on grounds, in `reference.md` § Statistical reporting and § What isn't a repeat | — |
| 3 | § What isn't a repeat's `vs_baseline` routing repaired to `results.contrasts`, and the `aggregated:` example re-authored against task 2's ruling — its `p_value_corrected: 0.0028` re-derived rather than carried | 2 |
| 4 | `null_test.method`'s closed enum table in § Statistical reporting, on § Resample methods' precedent and for its stated reason, plus the `p_value`/`p_value_corrected`/`null_test`-echo record shape (absent-versus-null, per the `resample` sibling rule) | 2 |
| 5 | **`envelope.LEAF_TYPES` closed one level in** at `{method, n, shuffle}`, and the module comment's list amended — **before** the refusal retires, on the `resample` and `holdout` precedents `envelope.py` states twice | 4 |
| 6 | `_check_null_test`: the `method` enum (`E-STATS-NULLTEST-METHOD`), the draw floor (`E-STATS-NULLTEST-N`), and `shuffle` naming a declared attribute (`E-STATS-NULLTEST-SHUFFLE`, § Validation's *Null test coherence*) | 5 |
| 7 | `E-STATS-NULLTEST-UNITS`, the filed no-roster check — reporting without returning, per the entry | 6 |
| 8 | The **shuffle-level-unambiguous** check against the resolved roster (§ Validation's *Shuffle level is unambiguous*, the `M07`/`M12` row) — roster-time, and the derivation it shares with task 12 | 6 |
| 9 | `W-STATS-CORRECTION-INAPPLICABLE` narrowed to its three disjuncts, through `crossed_group_axes` (§ 4), and its message re-worded — **in the same change that makes p-values reachable** | 6, 15 |
| 10 | `permutation_over_units` — the unclustered row relabelling, over a recorded column | 6 |
| 11 | The derived counterpart: relabel, re-run `aggregate`, collect the null — the `percentile_of_derived` structure one construction over, including its degenerate-draw and survivor-count discipline | 10 |
| 12 | The **cluster level derivation** — within-cluster when the attribute varies inside one, whole-cluster when it doesn't — and both clustered draws | 10, 8 |
| 13 | The group-axis form: the null is the *contrast*, permuted within cells of every other group axis | 10 |
| 14 | `Member.p_value`, and the exactly-one rule left untouched with that stated as a decision rather than an omission (§ 4) | 10 |
| 15 | **`corrected_for` made two-pass**: Holm's prefix `max` and BH's suffix `min`, `_level_for` re-argued, `p_value_corrected` in the output mapping — and `hypotheses.py`'s call re-checked as a second caller | 14, 1 |
| 16 | `fdr_bh` made real: `ci95_corrected` stays `null` by design, `p_value_corrected` produced, and `W-STATS-CORRECTED-THIN`'s interaction with a `None` level settled | 15 |
| 17 | The comparison-side write in `_comparison_step_blocks`, and the `null_test` resolved-values echo beside it — **verified by an end-to-end `run`, never a direct call** (§ 4) | 13, 14 |
| 18 | The per-condition write, wherever task 2 put it, and its family plumbing if task 2 gave it one | 2, 11, 15 |
| 19 | A hypothesis family's exposure to a p-value settled explicitly — `evaluate_on` names three bounds and none is a p-value, so this is a decision to record, not a feature to add | 15 |
| 20 | `E-DATA-CLUSTER-DERIVED` claimed: the clustered derived draw, on the ground H4c named for deferring it (§ 6) | 12, 11 |
| 21 | The two contrast-disclosure findings claimed: a contrast-scope thin warning with a `where` and a registry row, and the resolved-resample echo (§ 6) | 17 |
| 22 | The finite-inputs filing claimed or re-declined in writing, with its two pinning tests updated together if closed (§ 6) | 11 |
| 23 | The `report_by` filing **converted to a documented limitation**, per its own terminal instruction (§ 6) | — |
| 24 | **Retire `E-STATS-NULLTEST-UNSUPPORTED`**: the guard, the `NOT BUILT` marker, and § The one config file's count sentence — deleted rather than decremented, with the registry-absence sentence preserved for `E-TEMPLATE-INSTALLED-UNSUPPORTED` (§ 6) | every construction, 6, 7, 8 |
| 25 | The two `-UNSUPPORTED`-family tests converted **in the same commit as task 24**, plus the retired-code `src/` sweep on H4a's precedent | 24 |
| 26 | The citation sweep: § Validation's two rows given codes, § Errors rows minted for the new codes, `experimental-designs.md` § Mistakes core prevents' permutation row now delivered by code rather than by the refusal, and `feasibility-*` **re-dated rather than edited** | 24 |
| 27 | Whole-branch review, and the mechanical plus cross-document consistency passes | all |

**Direction against the charter: up, 13 → 27.** Where it moved, and why each is real rather than
padding: the two document-first decisions (tasks 1 and 2) are H4b-1's and H4c's own precedent and
neither is in the charter; the closed schema (task 5) is a precedent-bound ordering task the charter
names nowhere; the charter's "validate checks" is one row where the probe found **five** distinct
faults with nothing behind them (§ 1); `corrected_for`'s two-pass shape (task 15) is named nowhere;
and five inherited filings (tasks 20–23) did not exist when the charter was written.

### Should H4d be split? No — and the discriminator is the boundary's silence, not the count

H4c was 22 and was not split; H7b was 29 and was. The rule that separates them is whether a
half-built slice leaves a config that validates clean and does something other than what it says.
Two candidate seams, measured against that:

- **Engine without `fdr_bh`.** Illegitimate. A config declaring `null_test` + `fdr_bh` would produce
  `p_value` on its entries, `ci95_corrected: null`, and **no `p_value_corrected`** — the exact
  silent-correction-not-applied state § Statistical reporting says it exists to prevent — while
  `W-STATS-CORRECTION-INAPPLICABLE` asserts in its message that no comparison *can* carry a p-value,
  which would by then be false. The boundary cannot be spoken, so it cannot be drawn.
- **Per-condition form without the group-axis contrast form.** *Legitimate* — the boundary is
  speakable as a narrow refusal on `shuffle` naming a `groups` axis, on
  `E-DATA-WEIGHT-ALLOCATION-CONTRAST`'s precedent. But it buys little: the group-axis half is tasks
  13 and 17 plus part of 9, the correction plumbing is shared and unsplittable, and **no config in
  the feasibility analysis declares a group axis at all**, so the second half would be a zero-payoff
  slice behind a zero-payoff slice. Named here so a later decision to split has grounds rather than
  having to re-derive them.

**The ordering constraints, each with its reason:**

- **Documents before code for tasks 1, 2, 3 and 4.** A `method` string or a record key emitted before
  the four documents name it is the defect H4b-1 avoided deliberately and H4c repeated the avoidance
  of. `CLAUDE.md`'s rule is that the document changes first.
- **Task 5 before task 24, and before tasks 6–8 read any value.** Both `resample` and `holdout` were
  closed one level in *ahead* of their own wholesale refusal lifting, and `envelope.py` states the
  ground twice: the slice that honours a block needs the shape checked before it can read the values,
  or a typo among fixed key names turns from latent to live at the moment of retirement.
- **Every check and every construction before task 24.** Measured, not hypothetical: the probe in § 1
  shows five distinct faults earning only the wholesale refusal, so retiring it first makes a typo'd
  `shufle`, a misspelled `method`, an undeclared `shuffle` attribute, a sub-floor `n` and a rosterless
  declaration all validate clean at once.
- **Task 9 with task 15, not after it.** The warning's message currently asserts something true only
  while the engine is absent. A slice that lands p-values and narrows the warning in a later commit
  ships a false diagnostic in between, and `spec-defects.md` says so in as many words.
- **Task 14 before task 15 and before tasks 17–18.** The members carry the p-value into the family;
  a member that cannot hold one makes the correction pass untestable end to end.
- **Task 17 by `run`, never by direct call.** The derived-key-collision corner inside
  `_comparison_step_blocks` has been given **five wrong grounds across two slices**, every one an
  answer from a proxy, and every direct-call probe hand-built the maps and never reached it.
- **Task 25 in one commit with task 24.** Both tests assert against the code the retirement removes;
  splitting them leaves the branch red for a reason unrelated to either change.

---

## 8. What the charters name that no longer exists, and what is real that they never named

Both have been found on every re-scope in this repo, and both are here.

| The charter says | Measured at `2a4dc53` |
|---|---|
| a `validate` check that a shuffled attribute "collides with no recorded column" | **Already built, and not `null_test`-specific.** `artifacts.py`'s `io.record` refuses any recorded column shadowing *any* declared unit attribute, under `E-STEP-KEY-COLLISION`, at run time — and `null_test.shuffle` must name a declared attribute, so the row is covered by the broader rule. § Validation's row uses `null_test.shuffle` as its *example*, which is the "treating a row's example as its definition" trap read from the other end |
| a `validate` check that "an all-permuted design has no unpermuted value to test" | **Not a check, and not buildable.** `replication.REJECTED_KINDS` refuses `permutation` as a repeat kind by name, so no config can express an all-permuted design. The sentence in `experimental-designs.md` § Bootstrap and permutation is an **argument for why the repeat axis was the wrong home** — a sentence whose job is to contrast, read as licence for a rule |
| "`p_value` / `p_value_corrected` plumbing" | One row; measured, it is a record-shape decision with two unproducible documented homes (§ 3), a `Member` field, a two-pass rewrite of `corrected_for`, and two write sites |
| "`fdr_bh` made real for the first time" | One row; measured, it needs an ordering decision the four documents foreclose two answers to and supply none (§ 2) |
| `H4-SCOPING` § 6: "H4d last on its own merits — it is the only sub-slice with no existing code to build on" | **Still exactly true**, and the one charter claim that survived four slices unchanged. `p_value` has one occurrence in `src/`, and it is a comment saying it has none |
| The spine design: "H4d `null_test` (13)" | 27 (§ 7) |

| Real, and named by no charter | Where |
|---|---|
| `corrected_for` is a single-pass per-member loop, and neither Holm's nor BH's p-adjustment fits that shape; `hypotheses.py` is a second caller | § 2, § 4 |
| `statistics.null_test` is a whole leaf in `envelope.LEAF_TYPES`, where `resample` and `holdout` were both closed one level in *before* their refusals retired | § 0.4, § 1 |
| `null_test.method` has no closed enum table, where `resample.method`'s exists and states why it exists | § 2 |
| `validate._accounted_attribute_names` **already reads `null_test.shuffle`** — a live reader of an unbuilt block, suppressing `W-DATA-CLUSTER-UNDECLARED` today for a config that is refused | § 1 |
| § What isn't a repeat still routes a group-axis p-value to `vs_baseline`, the claim H4c retired one section over | § 0.3, § 3 |
| The `aggregated:` p-value example sits on a record shape with no `Member`, no `where`, and no correction fields — and the family definition excludes it | § 0.3, § 3 |
| `experimental-designs.md` § Mistakes core prevents carries a `null_test` row whose guarantee is delivered today by the wholesale refusal alone, which the cross-document invariant does not permit after retirement | § 1 |
| A permutation null does **not** replicate across the paired/weighted/clustered axes the last three slices each filled six-fold — the modifiers change the draw, not the estimator | § 4 |
| The `-UNSUPPORTED` family does **not** empty: `E-TEMPLATE-INSTALLED-UNSUPPORTED` survives at two emit sites, so the registry-absence sentence must survive with it | § 6 |

---

## 9. Amendment, 2026-08-18, same commit `2a4dc53` — five corrections to the body above

Appended rather than folded in, per the development-record rule: a scoping records what was measured,
and a retro-edit destroys the evidence. Each entry names what it replaces. **None changes the task
count, the no-split ruling, or the payoff answer.**

**1. A p-value on a member with no interval is reachable, and § 4's "a field, not a kind" row
under-states its cost.** That row says `Member.p_value` touches neither `__post_init__`'s count nor
`_corrected_bounds`' six return paths, verified by reading all three. That much stands. What it did
not check is `family_members`, which is `[e for e in entries if e.ci95 is not None]` — and
`_comparison_step_blocks` builds `ci95=(interval.low, interval.high) if interval else None`, so a
member whose interval came back `None` (a thin pool, a too-short draw, a degenerate column) is
constructed and then **dropped before ranking**. A permutation p-value needs only the observed
statistic and the null distribution, both of which exist in exactly that state. So a metric can
legitimately carry a p-value and no interval, and today's family would silently omit it — leaving
`fdr_bh` adjusting nothing for the member whose p-value was the only thing it had to adjust.

The exclusion argument § Statistical reporting gives — *"a metric reported without an interval isn't a
comparison anyone can read as significant"* — is about **intervals** and does not transfer to
p-values on its face. **This is a ruling task 15 owes and task 2 should decide:** either
`family_members` widens to `ci95 is not None or p_value is not None` (which changes `family_shape`'s
metric count, and therefore every existing corrected level in any run that declares `null_test`), or
the exclusion is re-argued for p-values explicitly and the omission documented. Named here so it is
decided rather than discovered.

**2. § 4's eight cells, with the standing refusals applied.** The body gives the space as
2 (draw: rows | clusters) × 2 (recompute: column | derived) × 2 (null of: one condition | a contrast)
and stops there. Reduced against what `validate` already refuses:

| Cell | Status at `2a4dc53` | H4d |
|---|---|---|
| rows × column × condition | Live | **Builds** — task 10 |
| rows × derived × condition | Live | **Builds** — task 11 |
| clusters × column × condition | Live | **Builds** — task 12 |
| clusters × derived × condition | The resample counterpart is refused by `E-DATA-CLUSTER-DERIVED` | **Builds, having claimed that filing** — task 20 |
| rows × column × contrast | Live, and reachable **only** through a declared `statistics.contrasts` entry (§ 3) | **Builds** — task 13 |
| rows × derived × contrast | Same reachability | **Builds** — task 13 |
| clusters × column × contrast | Same reachability | **Builds** — tasks 12, 13 |
| clusters × derived × contrast | Behind `E-DATA-CLUSTER-DERIVED` as well | **Builds** — tasks 20, 13 |

**Weights multiply none of these on the contrast half**, and that is the whole contribution of the
two standing weight refusals: `E-DATA-WEIGHT-ALLOCATION-CONTRAST` refuses a weighted cross-arm
comparison and `E-DATA-WEIGHT-CLUSTER-CONTRAST` refuses weight × cluster, so no weighted contrast cell
is reachable to permute. **On the per-condition half a weight *is* live** — H4b-1 gave every
`basis: units` column a weighted value and interval — so a permutation null over a weighted estimate
is reachable and needs a ruling: whether a relabelling permutes the weights with the labels or holds
them fixed with the units. That is one decision, not a construction, and it belongs in task 2.

**3. `E-STATS-NULLTEST-N`'s floor is a document change, and § 7 put it in the wrong place.** Task 6
mints a draw floor. No § Validation row states one, and § Statistical reporting's draw-count
paragraphs are about *interval* endpoints — `min_honest_draws`, whose argument is that below 80 draws
a percentile interval's lower endpoint is the sample minimum. A permutation p-value's resolution is
`1/(n+1)`, a different quantity with a different threshold. **The floor's value and its ground go
with tasks 1–4, before task 6 enforces it**, by the same rule those tasks exist to honour. Inheriting
`resample`'s floor unexamined is the available shortcut and it is the wrong one: the two numbers
answer different questions.

**4. § 7 task 26 is wrong about § Validation's shape.** It reads "§ Validation's two rows given
codes"; § Validation is a two-column table and carries no code column at all. What the two rows need
is their **condition restated** once a check exists behind each, and the new codes need rows in
§ Errors `validate` reports. Corrected here because a task brief inherits a sentence like that and
executes it literally.

**5. Task 25's conversion is a row swap, confirmed rather than assumed.**
`test_every_unsupported_message_defers_rather_than_scolds` asserts every `-UNSUPPORTED` message
contains `"later slice"`. Checked: `templates/registry.installed_template_message` contains that
exact phrase, so reparametrizing the test with a config drawing `E-TEMPLATE-INSTALLED-UNSUPPORTED`
preserves the test's premise instead of rewriting it. Task 25 costs what § 7 says it costs.
