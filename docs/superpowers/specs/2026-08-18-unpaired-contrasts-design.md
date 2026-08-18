# H4c — the unpaired contrast forms — design

**Goal:** a comparison whose two conditions differ on a declared `sweep.groups` axis stops being
refused. The delta and its interval are computed by a construction that assumes neither shared units
nor equal variances, the `method` says which, `paired: false` is derived rather than hard-coded, and
the record stops describing an intersection that does not exist.

**What it delivers, stated honestly. H4c unblocks ZERO configs.** No config in
`docs/feasibility-llm-growth-studies.md` declares a `sweep.groups` axis — all nine declare
`allocation: within` and `groups: []` — so **the no-remaining-core-side-blocker count stays six and
the executable count stays three.** Neither moves. A retired refusal is not an execution, and this
slice retires a refusal that **zero of nine** configs hit. What it is worth instead is stated in
§ The payoff, and it is not nothing: it is the gate five `spec-defects.md` filings are queued behind,
it closes the largest standing specification-versus-code gap in the statistics family, and it removes
the last hard-coded claim in the contrast record.

**What it is not.** Not the weighted unpaired forms — refused here by name, under decision 1. Not
`statistics.null_test` — H4d. Not `io.reuse_from` — unbuilt and unowned. Not `E-SWEEP-BASELINE-GROUP`,
which refuses a declaration on the peers rule and is permanent.

---

## The measurement this rests on

`docs/superpowers/H4c-SCOPING.md`, taken 2026-08-18 against `main` at `051600c`, after H4b-2 merged.
**Verdict: 22 tasks against the charter's 12.** It re-scopes the H4c row of
`docs/superpowers/H4-SCOPING.md`, written at a commit *before* H4a, H4b-1 and H4b-2 existed, and those
three slices changed every function this slice must touch. Baseline recorded there: `uv run pytest -q`
→ **2200 passed, 1 skipped, 2 xfailed**, foreground.

**Two commit pins, deliberately not blurred into one.** Everything inherited from the scoping is
pinned to **`051600c`**. Four things were verified while writing this spec and are pinned to
**`6a1ece1`**: that `E-DATA-WEIGHT-ALLOCATION-CONTRAST`, `welch_t_over_units_clustered`,
`unpaired_percentile_over_units_clustered`, `cohens_ds`, `n_of:`, `n_against`, `n_clusters_of` and
`n_clusters_against` are all **free identifiers** across `src/`, the four documents and `tests/`
(can-fail control on the same file list: `E-DATA-WEIGHT-CLUSTER-CONTRAST` → 22 hits, `n_paired:` → 8);
that `correction._corrected_bounds` branches on `member.clusters` → `member.weights` → plain over
`member.diffs`, with `pool` reached only after; that `cli._comparison_step_blocks` writes
`"paired": True` as a literal at both metric branches; and every half-width in
§ The discriminating fixtures, computed against the shipped `stats._t_critical`. **No production code
ships from this document.**

**One item moves DOWN against the scoping, and one moves UP**, and they cancel. Decision 1 merges the
scoping's tasks 9 and 10 into a single mint. The advisor pass on this spec found the scoping carries
**no regression-pin task at all**, where H4b-2 had one by name — so one is added. **The count is 22
either way, and the agreement is a coincidence of two independent moves rather than a confirmation.**

---

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | One slice or two, and which of the six constructions get built | **One slice, 22 tasks. Build the plain and clustered unpaired pairs; mint a narrow refusal for the weighted unpaired pair** | **The seam is a document asymmetry, not a task count.** § Statistical reporting's `_clustered` suffix rule specifies both unpaired clustered forms in the present tense — *"over the differenced values when paired and over the arm-level ones when not"*, *"jointly across both sides when paired"* — and § Clustered units makes one of them load-bearing for a named design: *"The contrast stays unpaired, since no unit appears in both arms, but its interval is cluster-robust on the matched set — so the effective `n` is the number of sets rather than the number of subjects, which is the accounting a matched design needs."* Refusing that pair would **de-specify a shipped rule** H4b-2 gave code to one axis over, and strand `experimental-designs.md` § Matched case-control. The weighted unpaired pair has the opposite standing: an alternation grep for both stems over `src/`, `docs/` and `tests/` returned **zero** at `051600c`, so refusing it removes nothing and mints over vapour. That is H4b-2's decision 3 applied where its precondition actually holds. **Against the split**, argued rather than assumed: H4b split at exactly 22, but it split **on the payoff line** — H4b-1 retired a refusal three configs hit and H4b-2 one that zero hit — and that seam does not exist here, where the payoff is zero for every task. Any cut must leave the retirement in the second half (the ordering constraint below), so the first half would ship **four constructions with no production caller** — the state the spine design already flags as a hazard ("two percentile constructions built with zero production callers") — and change no observable behaviour at all. The mitigation for 22 is **batched dispatch** on H4b-2's precedent, not a cut. **The count is stated as what it is: 22, two above this repo's observed band** (H3c-1 20, H7b Part A 20, H3d 19, H4b-2 18, H4b-1 15) |
| 2 | `Member`'s evidence model | **A third evidence *kind*, carried in one new field of a new frozen type — and only the *t* forms need it** | An unpaired percentile's evidence is a **pool of resampled differences**, structurally identical to a paired one's, so `interval_at` already serves it and `pool` needs no change. Only `welch_t_over_units` and `welch_t_over_units_clustered` have evidence that is neither a pool nor differences: **two per-side value vectors**, plus two per-side label vectors when clustered. So `Member` gains **one** field, `sides: UnpairedEvidence \| None`, where `UnpairedEvidence` is a frozen dataclass holding `of`, `against` and an optional per-side `clusters` pair, validating its own internal alignment in its own `__post_init__`. **One field, not four**, because only a single field can enter the exactly-one rule cleanly, and because a modifier's length invariant belongs to the object that defines the vectors it aligns against — a flat `clusters` beside `sides` would be one field with two admissible shapes, which is the misaligned-vector class that *"produces a plausible number rather than an error"*. `__post_init__`'s exactly-one becomes **exactly one of `pool`/`diffs`/`sides`, counted over the three** rather than extended from today's `(pool is None) == (diffs is None)` equality: that equality does not generalize, and a later reader adding a second equality would silently admit two-set members. Both existing modifier checks gain **"never beside `sides`"** — `weights` because decision 1 refuses the weighted unpaired composition, so a member carrying both is `cli`'s bookkeeping error exactly as `E-DATA-WEIGHT-CLUSTER-CONTRAST` makes the other pair's; `clusters` because unpaired membership is per side and lives inside `sides`. **`correction.py` is a second production call site the charter names nowhere**, so each new *t* form needs a caller there as well as in `cli.py`, and `_corrected_bounds` goes from three arms to **five** — two under `sides`, three under `diffs` — **five, counted rather than carried**: an implementer writing six from the scoping's "six-way" leaves an arm no input reaches, and one writing four leaves a cell falling through to a wrong construction, which is H4b-2's decision 2 |
| 3 | The `method` vocabulary, and where it is minted | **Four spellings, `reference.md` first, and no new table rows** | `welch_t_over_units` and `unpaired_percentile_over_units` **already have § Statistical reporting rows**. `welch_t_over_units_clustered` and `unpaired_percentile_over_units_clustered` are **licensed by the suffix rule** and get **no rows of their own** — H4b-2's decision 5 verbatim: adding rows converts a self-maintaining rule into a maintenance obligation nobody owns, and `efa13bc` repaired the opposite mistake by narrowing a quantifier rather than enumerating. **Ruled explicitly, in writing, because without it a later task will helpfully enumerate them.** The weighted pair gets **no spelling at all** — decision 1 refuses it — and the two `weighted_paired_*` rows gain the narrowing that makes them true of the paired case only. **One clause is added**, and its scope is the whole point of adding it: the suffix rule does not say how two per-side dfs combine for an unpaired clustered *t*, and code cannot emit a df a document does not license, so the sentence gains that rule — **scoped to the *t* forms alone**, because a df provenance generalized over the percentile form is the exact false claim H4b-2's batch-1 Major 1 deleted and its batch-3 Major 1 then re-seeded at three more sites. **And `unpaired_percentile_over_units` may not reuse `paired_percentile_of_derived`**: that function's construction is *one* draw applied to both sides, argued at length in its docstring — *"would resample the two conditions apart and destroy the pairing"* — and § Statistical reporting defines the unpaired form as *"resampling within each side independently"*, which is precisely the arrangement that docstring exists to refuse. The three-`method`-strings-one-function economy H4b-1 and H4b-2 built **does not extend here**; the percentile side is a new construction, and it serves its own two spellings through its own `method=` parameter |
| 4 | The df of an unpaired clustered *t* | **Welch-Satterthwaite over the two cluster-robust per-side variances, each side contributing df = `G_s` − 1** | The four documents under-specify this and code must emit something. `welch_t_over_units`' own row says *"df from Welch-Satterthwaite"*, and the suffix rule says the cluster replaces the unit **as the draw** — so the substitution happens **inside each side's variance and its own df**, and Welch-Satterthwaite combines them exactly as it does for the IID form. The two rejected readings, named so nobody re-derives them: `min(G_of, G_against) − 1` discards a side's information and contradicts "df = clusters − 1" on the side it discards; `G_total − 2` is the **pooled** reading the `welch_t_over_units` row refuses by construction. Fixture B separates all three by more than 4 % (§ The discriminating fixtures) |
| 5 | The record shape where `n_paired` does not apply | **`n_paired` absent — not null — and replaced by the scalar siblings `n_of` / `n_against`; `n_paired_clusters` by `n_clusters_of` / `n_clusters_against`** | § Contrasts defines `n_paired` as *the intersection*, and an unpaired contrast's intersection is **empty by construction**. `n_paired: 0` is arithmetically true and descriptively false, and it is worse than merely imprecise: § Contrasts already spends `0` on a different meaning — *"A contrast whose intersection is empty is reported as such rather than as a delta of zero"* — so writing it here would make one number mean both *a pairing that failed* (a defect to report) and *a design where pairing is not the concept* (nothing wrong at all). **Absent, not null**, is the shape `weighted_by`, `n_paired_effective` and `n_paired_clusters` already use, and it keeps `n_paired` meaning exactly one thing wherever a reader meets it. **Two scalar siblings, never an `n` mapping**, on the standing argument § Contrasts makes twice: *"this record deliberately has no `n` mapping to join"*. `n_of`/`n_against` mirror the entry's own `of:`/`against:` keys. `n_paired_effective` has **no unpaired counterpart to design**, because decision 1 refuses the only composition that would produce one — a record-shape problem that ruling removes rather than defers. The § Contrasts sentence *"`n_paired` is the intersection, and it has to be recorded"* is **narrowed to paired contrasts**, the same quantifier-narrowing H4b-2's batch-1 review applied to *"Every clustered contrast…"* rather than the enumeration it could have been. **This is the first conditional write of `n_paired` in the codebase, and the spec says so rather than presenting the ruling as pure precedent-following.** `cli._comparison_step_blocks` writes it **unconditionally at both metric branches** today, and H4b-2's batch-4 fix round upheld that shape on the ground that it is *an intersection-fact rather than a construction-fact* — verified there by a direct call showing it written beside a null `method`/`ci95`. Measured at `6a1ece1`: the readers are those two writes and `tests/` alone — nothing in `attrition`, `_entry_for` or the hypothesis `observed` path reads it — so **task 13 owns making the entry tolerate its absence**, and the ruling costs no reader outside the tests. The pin that must survive unchanged is `test_a_derived_contrast_over_an_empty_stratum_reports_no_delta`, which asserts `n_paired == 0` beside a null delta for a *paired* contrast whose stratum matched nobody: it is the live proof that `0` already means **pairing failed**, which is the whole reason an unpaired contrast may not spend it. Without this clause an implementer adds `n_of` and leaves `n_paired: 0` beside it — the worst-of-both this decision rejects, and nothing else in the slice enforces the rejection. **`reference.md` § Contrasts names all four keys before any code writes one** — a record key code writes and no document names is the pair `CLAUDE.md` says to grep for, and H4b-1 had to mint a whole `method` vocabulary for exactly this reason |
| 6 | `W-STATS-CONTRAST-THIN` and `limits.min_reported_n` with no `n_paired` to read | **Both apply per side, and fire when *either* side is below the limit** | § Validation's row reads *"the comparison's realized `n_paired` is below it"*, and § Contrasts grounds it in *"a stratified paired comparison is where a small denominator is easiest to miss and most disclosive"*. The disclosive quantity is a **thin denominator anywhere**, not a thin intersection specifically: a five-unit arm compared against a five-hundred-unit one is exactly the disclosure the limit exists to catch, and any rule reading only one side or only a total would pass it. Firing on either side is the reading that preserves the row's own reason. The row and the § Contrasts sentence are both narrowed in task 2, before task 16 reads them |
| 7 | Where the retirement sits, and what derives `paired` | **Last, after every construction, `method` string and record key — and the pairing predicate is ONE expression with two callers** | `_comparison_step_blocks` writes `"paired": True` as a **literal at both metric branches**. Delete `E-DATA-ALLOCATION-CONTRAST` before the constructions exist and a declared cross-arm comparison routes to a *paired* construction over an **empty** intersection, publishing `delta: null, paired: true, n_paired: 0` with `validate` reporting **zero errors** — H4b-2's decision 2 one axis over, and it hit that class for real. Separately: `paired` must be derived from `differing_axes(of, against)` intersected with the group axes' selectors — **the same test the refusal runs today** — and that predicate acquires a **second** live caller in decision 1's new refusal, which must fire only on a cross-arm comparison. So it is **one named function in `contrasts.py` beside `differing_axes`**, called by `cli`'s derivation and by `validate`'s new guard. Two spellings of one rule drifting apart is a defect this codebase has already shipped, and here the drift would be `validate` refusing a shape `cli` records as paired |
| 8 | The derived-metric unpaired case, and the suppression guard | **Suppress, on a guard that reads the pairing derivation's own answer — and state the branch's two grounds as one guard, never as two accreted checks** | **No per-side derived draw exists among the four constructions built here**, so an unpaired **derived** contrast has nothing to compute: `delta`/`method`/`ci95` all `null`, with `n_of`/`n_against` (and the cluster counts when declared) beside them — the shape `E-DATA-CLUSTER-DERIVED` already uses, and the shape § Contrasts already licenses on the grounds that a count is a fact about the sides rather than about whether a construction ran. **The guard reads the derived `paired` answer, not an empty `base_keys`.** An empty `base_keys` is a **proxy**: it is also empty when two genuinely paired conditions share no completed units, which is a defect to report rather than a design to honour — the substitution `CLAUDE.md` § Answering a question with a proxy is about, one axis over. After this slice the derived branch carries **two independent suppression conditions**, a declared cluster and an unpaired comparison, and they are written as **one guard naming both grounds**: a later reader taking one as covering the other is the *fourth* wrong ground this corner was already given — *"the same clusters-guarded suppression `E-DATA-CLUSTER-DERIVED` states for the recorded-column path applies to the contrast over that key too"*, disproved by running. **Verified by an end-to-end `run`, never by direct call**: every direct-call probe of this corner hand-built the maps and so never reached it |

### Decision 1 gates decisions 2, 3 and 5, and that is why it goes first

Refusing the weighted unpaired pair is not one task's local choice. It is what makes `Member`'s
`weights` modifier a *"never beside `sides`"* assertion rather than a fourth construction to align
(decision 2), what keeps the § Statistical reporting weighted rows narrowable rather than doubled
(decision 3), and what leaves `n_paired_effective` with no unpaired counterpart to invent (decision 5).
**Building first bakes the answer in by omission** — H4b-1's own *5 before 7*, one axis over.

### The refusal decision 1 mints, and what makes it permanent rather than build-hedged

**Proposed spelling: `E-DATA-WEIGHT-ALLOCATION-CONTRAST`**, on the
`E-DATA-WEIGHT-CONTRAST` / `E-DATA-CLUSTER-CONTRAST` / `E-DATA-WEIGHT-CLUSTER-CONTRAST` family shape,
verified free at `6a1ece1`. **Named here rather than left to its task, because an identifier nobody
wrote down is how one gets minted twice under two spellings.**

Two constraints on the mint, both from H4b-2's decision 3:

- It is a **documented narrow refusal carrying both a § Errors row and a § Validation row**, not a
  `-UNSUPPORTED` build-family code. `CLAUDE.md` § Misreadings draws that distinction and it decides
  whether the code outlives this slice. **It is written to outlive it**, and its row states the
  standing reason — a Welch *t* on two weighted means needs Kish's effective size **per side**, two df
  inputs where the paired form needed one, on the dimension where a wrong choice hides best — rather
  than any form of *"until the estimators exist"*.
- **No slice inherits it as work.** `E-DATA-WEIGHT-CLUSTER-CONTRAST` is the precedent: a narrow
  refusal nobody owns retiring. Writing it as a deferral instead is how an entry comes to read as live
  work nobody holds.

### `validate` gates `run`, so the threading tasks cannot be tested through `run`

H4b-1's planning correction 1 and H4b-2's restatement of it apply here verbatim, and it is stated in
the spec rather than left for planning because H4b-1 paid a round discovering it. `cli.command_run`
calls `validate_config` and returns `EXIT_WRONG` on any error, and `E-DATA-ALLOCATION-CONTRAST` is one
— so **no unpaired contrast reaches `_comparison_step_blocks` through `run` until task 18 retires the
refusal.** Tasks 10–16 test by direct call; **task 18 carries the `validate`-clean and `run`-through
halves**, and **task 15's guard lands IN task 18's commit**, not merely after it — see the constraint below.

---

## What the scoping overturned, and what this spec adds to it

**The charter named the wrong function.** *"`paired` derived in `cli._entry_for`"* — `_entry_for` maps
a corrected field onto whichever record shape holds it and never touches `paired`. Both literals are
in `_comparison_step_blocks`, whose `conditions_by_index` and `differing_axes` are already parameters
and imports, so the derivation is local.

**The charter's "their clustered and weighted counterparts" reads as two forms beside two; measured,
it is four beside two.** Decision 1 builds two of the four and refuses two.

**The charter's "the `n_paired` spec gap" is not one key's gap** — a definition that does not apply,
two missing per-side counts, two scalar siblings inheriting the problem, and a warning keyed on it.

**The only documented unpaired record in the four documents sits in a config shape core permanently
refuses**, and that is a repair rather than a decision: a parameter-only baseline beside a `groups`
axis **expands over the group axis**, giving each arm its own reference, so every generated comparison
is within-arm and no cross-arm pair is ever read; and the baseline that *does* fix a group level earns
`E-SWEEP-BASELINE-GROUP`, which H4c does not lift. So **`vs_baseline` is never H4c's surface — a
declared `statistics.contrasts` entry is** — and § Allocation's fenced example plus the two prose
sentences deriving from it are repaired at **three enumerated sites** (task 3).

**Added by this spec, and named by neither the charter nor the scoping:** the **regression pin**
(task 21) — the scoping carries none, where H4b-2 had one by name, and deriving `paired` at both
branches is precisely the change that can silently move every existing *paired* contrast while
`_corrected_bounds` growing two arms is precisely the change that can silently move every existing
corrected bound; the **shared pairing predicate** (decision 7); the **df-combination rule** (decision
4); and the **`n_of` substring hazard** below.

**A sweep for `n_of` cannot be a bare-word sweep.** `grep -rn 'n_of' src/ docs/ tests/` returns **40
hits at `6a1ece1`, none of them a bare `n_of`** — they are `n_of_m`, `n_off` and test-name fragments.
`grep -rn 'n_of:'` returns **0**, against a can-fail control of `n_paired:` → 8. The greppable form is
the one with the colon, and it is recorded here because a later task sweeping for the bare word will
drown and conclude the key is taken.

**The development record is exempt from every sweep here.** `H4c-SCOPING.md`, the H4b ledgers and both
predecessor specs record what was measured on their dates and **must not be retro-edited**.
`spec-defects.md`'s live entries are the one exception, and there a closed gap is **struck** rather
than deleted.

---

## The traps

| Trap | The rule |
|---|---|
| A Welch interval that coincides with a pooled one | Equal per-side sizes make the pooled and Welch standard errors **algebraically identical**, and near-equal variances make them agree to several digits whatever the sizes. **Unequal `n` and unequal variance together are what make them separable**, and the fixture below is sized so no candidate lands within 4 % of another. Sixteen unfailable checks were found across the two H3c slices, in statistics alone |
| A Welch df that coincides with a side's own df | Welch-Satterthwaite's df is bounded below by `min(df_of, df_against)`, so a fixture where one side dominates the variance drives it **onto** that bound and a `min(n) − 1` mutant becomes invisible. The first draft of fixture A did exactly this: correct 17.2405 against the mutant's 17.2614, **0.1 % apart**. Both sides must contribute comparably to the variance |
| A cluster fixture whose cluster count cannot change the answer | `CLAUDE.md` § Writing checks that can fail names the instance — *"a cluster fixture where correct and buggy cluster counts were both 3"*. Here the two sides carry **3 and 4** clusters, so a mutant reading one side's count writes a wrong **integer** into the record |
| A singleton-cluster fixture | One unit per cluster makes `G − 1` equal `n − 1`, so the clustered and IID forms coincide exactly and every assertion passes under a mutant ignoring membership |
| Equal cluster sizes in the percentile fixture | Makes "a replicate's pooled row count varies" invisible; a mutant drawing **units** instead of clusters returns a fixed row count and is never seen |
| Asserting `is not None` on anything unpaired | **Null is a uselessly weak discriminator on this slice.** A joint-draw mutant routed through `paired_percentile_of_derived` returns `None` over disjoint arms — but so does a suppressed derived contrast, a thin side, and a degenerate draw. Every unpaired assertion needs a **positive literal or an integer count** |
| A mutation whose two branches cannot differ | **A mutation is a claim too.** Swapping the two sides of fixture A flips `delta`'s sign but leaves the half-width **bit-identical**, so it is blind to every interval assertion and caught only by the `delta` one. Named here so nobody prescribes it as an interval mutation later. Five mutations were claimed blind on H4b-2; **one was overturned by a one-line fixture change** |
| Reading a mutation's silence as confirmation | A mutation that changes nothing is evidence about the **tests**, not about the code |
| A mutation run against a self-chosen subset | H4b-1 produced a **false blind-spot claim** exactly this way. Every mutation runs against the **full, unfiltered** suite in the **foreground**; a backgrounded run is how a re-reviewer stopped with a mutation possibly still applied, twice on H4b-2 |
| A mutation applied to a proxy | `t_over_units_clustered` and `paired_t_over_units_clustered` are shipped and correct; breaking either proves nothing about the unpaired forms. The discriminating mutation is on the **new** construction and on the `method`-selection branch |
| Reading "this config is refused" as "this path does not run" | **`validate` collects rather than aborting.** Four readers in this repo have got this wrong. Ask what `validate` *reports*, in full, as an exact set |
| Answering with a proxy | One corner on H4b-2 was given **four wrong grounds in four commits** — `aggregated`, then `resample_fns_by_key`, then a sibling path's behaviour, then a citation of a row rewritten in the same breath — and **only an end-to-end `run` exposed it**. Decision 8 is that corner's neighbour and inherits the discipline |
| A test asserting only that a per-side key is present | H4b-1 pinned the three-way obligation after `weighted_by`'s value passed under a hardcoded constant. An unpaired entry carries it too: value, interval and the two counts move together |
| A refusal that happens to fire, counted without attribution | `allocation: within` beside a `groups` axis earns `E-DATA-ALLOCATION-WITHIN-ARMS`, and a `groups` axis with no `assign` earns `E-DATA-ALLOCATION-NO-ARMS`. A fixture forgetting either attributes its refusal to the wrong code |
| A carried line number | Cite by **name**. `H4b-SCOPING` cited `stats.py:1900` for a function that had moved |
| Filtering a sweep's output | Filter the **file list**, never the output — and exclude the development record, which is evidence rather than text to repair |

---

## The discriminating fixtures, stated here so no later task can weaken them

**The constraints first**, because a later task may only substitute fixtures meeting all of them:

1. **Unequal per-side sizes**, or pooled and Welch coincide algebraically.
2. **Unequal per-side variances**, arranged so *both* sides contribute comparably to the Welch
   variance — otherwise the Welch df collapses onto one side's own df and a `min(n) − 1` mutant hides.
3. **Non-singleton clusters, unequal in size, and differing in count between the two sides.**
4. **Values constant within a cluster**, so the within-side variance is entirely between-cluster and
   CR1 cannot approximate the IID form.

### Fixture A — the IID unpaired contrast

`of` is **5 units**, `[17, 19, 20, 21, 23]` — mean **20**, s² **5**, s²/n **1**.
`against` is **25 units**, twelve at `5`, twelve at `15`, one at `10` — mean **10**, s² **25**,
s²/n **1**. **Delta = 10.** The single unit *at* the mean is deliberate, not padding: it contributes zero to the variance, so the side's **count and its variance are independently mutable** — an off-by-one dropping it leaves s² at 25 while moving n to 24, which shifts the df and the half-width by ~0.5 %. Small, but a literal assertion still catches it, where a fixture with no such unit would let a count mutation hide inside a variance change. Welch SE = √2 = `1.4142135623730951`; Welch-Satterthwaite
df = 96/7 = `13.714285714285714`.

| What computes it | Half-width | Ratio to correct |
|---|---|---|
| **Correct** — Welch variance, Welch-Satterthwaite df | **3.039125537798091** | 1.0000 |
| Mutant: pooled variance, df = `n_of + n_against − 2` = 28 | 4.722138614325821 | 1.5538 |
| Mutant: Welch variance, df = `min(n) − 1` = 4 | 3.9264863229551143 | 1.2920 |
| Mutant: Welch variance, df = `max(n) − 1` = 24 | 2.918793337216675 | 0.9604 |
| Mutant: Welch variance, df = `n_of + n_against − 2` = 28 | 2.8968851611887434 | 0.9532 |
| `paired_t_over_units` over two disjoint arms | `None` — the intersection is empty | — |

**Five distinct numbers, the tightest 4.7 % from the correct one**, which no rounding produces. Two
qualifications, stated so nobody over-claims: the last two mutants sit **0.75 % apart from each
other**, so a literal assertion catches both but cannot say which fired; and the paired mutant returns
`None`, which per the traps table is never sufficient on its own.

**`cohens_ds` is separately assertable, and it pins a documented asymmetry nothing else does.** The
pooled sd is `4.705619740571601`, so *d*s = **2.1251185925162073**, while a mutant standardizing by
the interval's own Welch denominator (`1.4142…`) gives **7.0710678118654755** — a factor of 3.33.
§ Statistical reporting states that asymmetry deliberately — *"*d*s pools where `welch_t_over_units`
deliberately doesn't, and that isn't an inconsistency"* — and this is the assertion that makes it more
than a sentence.

### Fixture B — the clustered unpaired contrast

`of` is **9 units in 3 clusters** of sizes 2, 3, 4, constant within cluster at `0`, `15`, `30` —
mean `18.333333333333332`. `against` is **12 units in 4 clusters** of sizes 2, 3, 3, 4, constant
within cluster at `2`, `4`, `6`, `8` — mean `5.5`. **Delta = 12.833333333333332.** Per-side CR1
variances `67.07818930041152` (G = 3) and `1.5879629629629628` (G = 4), SE `8.286504224543332`,
Welch-Satterthwaite df over `G_s − 1` = `2.0950313633473936`.

| What computes it | Half-width | Ratio to correct |
|---|---|---|
| **Correct** — CR1 per side, df combined over `G_s` − 1 | **34.14810237373095** | 1.0000 |
| Mutant: `min(G) − 1` = 2, equivalently `G_of − 1` | 35.653950021811816 | 1.0441 |
| Mutant: `G_against − 1` = 3 | 26.371354753115764 | 0.7723 |
| Mutant: `G_total − 2` = 5, the pooled reading | 21.301137240534675 | 0.6238 |
| Mutant: CR1 meat, df = `n_of + n_against − 2` = 19 | 17.343852668925262 | 0.5079 |
| The IID Welch form on the identical data | 9.647234756296374 | 0.2825 |

**Six distinct answers, and the correct one is not the extreme of any single dimension** — 35.65 sits
above it — so an assertion on the number discriminates every failure mode, which an assertion on "is
it wider" does not. The tightest separation is 4.4 %.

**The two integer counts are the strongest discriminator on this fixture and must be asserted
alongside the half-width.** `n_clusters_of: 3` and `n_clusters_against: 4` are integers that cannot
coincide, so a construction reading one side's count, or a pooled count of 7, writes a wrong integer
into `run.yaml` even where a float assertion might be argued about.

### The percentile forms, and the corrected bounds

**The percentile discriminator is the per-replicate draw size, and it must be asserted rather than
inferred from the interval.** An independent per-side draw takes **exactly 5 rows and exactly 25 rows,
every replicate** on fixture A — a mutant drawing once from the pooled 30 and splitting, or drawing
`min(n)` for both, returns different sizes. On fixture B the cluster sizes 2/3/4 and 2/3/3/4 make the
`of`-side row count **vary between 6 and 12 across replicates** while a unit-drawing mutant returns a
fixed 9. No percentile half-width literals are stated here: the constructions do not exist yet, so a
literal would be invented rather than computed, which is the failure `CLAUDE.md` names for regression
pins captured after the change.

**The corrected bound is pinned by its ratio at the entry's own df, not by a field being threaded.**
A corrected half-width must equal the raw one times `t(df, 1 − level) / t(df, 0.95)` **at the same
df** — so at Bonferroni over a family of 2 that ratio is `1.1706821500146336` on fixture A (df
13.714286) and `1.4227764722656022` on fixture B (df 2.095031). **The two differ by 21 %, which is the
point**: a corrected bound built at an unpaired-IID df, at a paired df, or at the unclustered df
produces a visibly different ratio. H4b-2's whole-branch review confirmed its own bound exactly this
way and found the *t* ratio at df = clusters − 1; H4c owes the same at both dfs.

---

## Task decomposition — 22

Grain matches `H4c-SCOPING.md` and its three predecessors: each new construction, each new record key
and each document-table edit is its own task.

**Decisions and documents — 3**

1. **The vocabulary, the refusal and the df-combination rule** per decisions 1, 3 and 4: confirm the
   two existing § Statistical reporting rows, rule **no new rows** for the clustered pair in writing,
   narrow the two `weighted_paired_*` rows to the paired case, and add the df-combination clause
   **scoped to the *t* forms alone**. **The clause needs a tripwire, because this is the sentence whose removal cost H4b-2 two review rounds**: batch 1 deleted a df-provenance clause from this exact region as false of the percentile form, and batch 3 re-seeded it at three more sites — one of them a paraphrase no literal grep could find. So task 22's sweep **re-reads** the percentile forms' comments and docstrings for the same claim rather than grepping for this clause's wording.
2. **The record shape** per decisions 5 and 6, in `reference.md` § Contrasts and § Validation, **before
   any code writes a key**: `n_of`/`n_against`, `n_clusters_of`/`n_clusters_against`, `n_paired`'s
   quantifier narrowed to paired contrasts, and `limits.min_reported_n` / `W-STATS-CONTRAST-THIN`
   restated as per-side.
3. **§ Allocation's unreachable `vs_baseline` example** re-authored as a `results.contrasts` entry
   carrying task 2's keys, with the two prose sentences that derive from it. **Three sites**, and the
   enumeration is the task: the fenced block including its `# 03_arm=treatment__method=spearman`
   comment, *"Each contrast records its own `paired: true|false` in `vs_baseline`"*, and *"Fixing a
   value on every axis is the other coherent choice, and it's the one that produces contrasts like the
   above"* — which produces `E-SWEEP-BASELINE-GROUP`. **After task 2.**

**Constructions and the refusal — 6**

4. **`welch_t_over_units`** — Welch's *t* on two independent condition means, Welch-Satterthwaite df.
5. **`cohens_ds`** — pooled within-condition sd, the denominator § Statistical reporting names,
   deliberately **not** the interval's.
6. **`unpaired_percentile_over_units`** — a **new construction**, drawing each side independently, per
   decision 3. Returns a **sorted** pool (see task 20's first filing).
7. **`welch_t_over_units_clustered`** — CR1 per side, df combined per decision 4. **After 4.**
8. **`unpaired_percentile_over_units_clustered`** — whole clusters within each side, its own `method=`
   spelling on task 6's construction. **After 6.**
9. **Mint `E-DATA-WEIGHT-ALLOCATION-CONTRAST`** — the guard (through decision 7's shared predicate),
   its § Errors row and its § Validation row, bundled as one task on H4b-1's task-11 precedent.
   **After 1**, and **before 18**, or the combination falls through to an unweighted number silently.

**Threading, `Member` and the record — 7**

10. **The unpaired key path** — the per-side completed sets narrowed by `within`, and the point
    estimate as a difference of two side means. `paired_keys` does not apply. **After 2.**
11. **`Member`'s third evidence kind** — `UnpairedEvidence`, the exactly-one rule counted over three,
    and both modifier checks re-argued, per decision 2. **After 4 and 6.**
12. **`_corrected_bounds`' two unpaired arms and `family_members`** — five arms, counted rather than
    carried. `correction.py` is the second production call site. **After 11 and 7.**
13. **`paired` derived at both `_comparison_step_blocks` branches**, through decision 7's shared
    predicate. **Carries task 17's first pin in its own commit.** **It also owns `differing_axes`' docstring**, which task 19's sweep deliberately does not: that docstring *names its two callers*, one of them *"the (temporarily) hard-coded `paired`"*, and this slice replaces both — the new predicate becomes its caller here, and task 18 deletes `_check_sweep`'s guard entirely. That is a claim about the **call graph**, falsified by tasks 13 and 18 together rather than by any wording a citation sweep would match — the shape `CLAUDE.md` names as rewriting a sentence when a row was the thing that was wrong. **After 10.**
14. **The `method` selection** — the reachable cells across both sites, the *t* arm's string coming
    from the construction and the percentile arm's from a `method=` argument, as H4b-2's correction 2
    established. **After 13 and every construction.**
15. **The derived-metric unpaired case and the two-ground suppression guard**, per decision 8 —
    **verified by an end-to-end `run`, never by direct call**. **Its guard lands in task 18's own commit.** Task 18 is the commit that *removes the thing making this corner unreachable*, so any gap between them is a window in which a derived unpaired contrast publishes a number from nothing with `validate` reporting zero errors. On H4b-2 the retirement commit was exactly that commit, and the re-check routed to it was silently dropped and found only by the whole-branch review.
16. **`W-STATS-CONTRAST-THIN` and `limits.min_reported_n` per side.** **After 2 and 13.**

**Retirement, residue and regression — 6**

17. **The two pins**, per the scoping's § 6. The first —
    `test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch`, which asserts
    `inspect.getsource` counts — is **replaced, not deleted**, by the behavioural pin it could not be:
    one `run` in which a declared cross-arm contrast records `paired: false` beside a `welch_*` or
    `unpaired_*` `method` **and** a within-arm comparison in the same run still records `true`. Its own
    docstring names the scope gap the replacement closes: it reads one function's source text and is
    defeated by extracting either write into a helper. The second —
    `test_a_contrast_beside_groups_and_cluster_by_draws_the_allocation_refusal`, an **exact set** — is
    **converted, not deleted**, into the clean-composition control plus a run-side assertion that the
    entry's `method` carries `_clustered`; **its fixture is clustered, which is what forces the
    clustered unpaired forms into this slice.** **The two halves land in two commits by constraint:
    the first with task 13, the second with task 18**, because each fails the moment its own change
    lands and splitting either leaves the branch red for an unrelated reason.
18. **Retire `E-DATA-ALLOCATION-CONTRAST`** — its one emit in `_check_sweep`, its § Validation row
    *Allocation deltas aren't computed*, and its § Errors row. **Last among the code tasks**, and it
    alone carries the `validate`-clean and `run`-through halves.
19. **The surviving-citation sweep** — every one of the scoping's 14 sites that task 18 does not
    delete, by **claim** over a named file list: `_check_assign`'s docstring, `_check_unimplemented`'s
    comment, `_comparison_step_blocks`' docstring (whose *"That claim expires with
    `E-DATA-ALLOCATION-CONTRAST`"* names the derivation task 13 wrote),
    `experimental-designs.md` § Mistakes core prevents, and — the one that is a re-wording rather than
    a deletion — **`E-SWEEP-BASELINE-GROUP`'s guard comment and its emitted message**, which promise
    the delta *"until the unpaired estimators exist"*: a temporary clause inside a **permanent**
    refusal, which must be restated on the peers ground it actually rests on.
    `feasibility-llm-growth-studies.md` is **re-dated rather than edited**.
20. **The five inherited filings, each claimed or re-declined in writing**, per § The inherited
    filings below.
21. **The regression pin** — a within-arm paired contrast **byte-identical** across this branch
    (`paired_t_over_units`, `paired_percentile_over_units`, the weighted and clustered forms), and the
    worked example's intervals, which `CLAUDE.md` § The worked example says **must not be narrowed
    back**. **Literals captured at the branch point, before any behaviour changes**: a literal recorded
    afterwards records the change rather than the baseline. Plus the boundary this slice owes rather
    than merely respects — an unpaired pass walking every metric block **must skip** a `summary`-step
    `Estimate`, which is `reported: true`, outside the correction family and never recomputed.
22. **Whole-branch review**, and the mechanical plus cross-document consistency passes.

### The ordering constraints, each with its reason

| Constraint | Reason |
|---|---|
| **Task 1 before 4–12** | Decision 1 fixes whether four constructions exist or six, and with it how many arms tasks 12 and 14 have. Building first bakes the answer in by omission |
| **Tasks 2 and 3 before any code writes a key** | A record key emitted before a document names it is the pair `CLAUDE.md` says to grep for, and H4b-1's own precedent |
| **Task 2 before task 3** | § Allocation's repaired example must carry the keys task 2 mints, or the repair ships a second unreachable record |
| **Task 11 before 12 and before 14** | `_comparison_step_blocks` builds the `Member`s, so a `Member` that cannot represent an unpaired interval makes the dispatch untestable end to end |
| **Task 9 before task 18** | The weighted unpaired combination must land somewhere before the refusal currently catching it is deleted |
| **Every construction before task 18** | Retiring the guard while a construction is missing routes a declared cross-arm comparison to a *paired* construction over an empty intersection, publishing `delta: null, paired: true, n_paired: 0` with `validate` reporting zero errors. H4b-2 hit this class for real and only an end-to-end `run` found it |
| **Task 17's first half in task 13's commit, its second in task 18's** | Each pin fails the moment its own change lands; splitting either leaves the branch red for a reason unrelated to both |
| **Task 15's guard in task 18's commit** | `validate` gates `run` until 18, so 15 cannot be verified earlier — and landing it later leaves the retirement commit shipping an unguarded derived unpaired path. One commit, or the branch has a window |
| **Task 21's literals captured before task 4** | A pin whose values are captured afterwards asserts the new behaviour against itself |
| **Task 19 must not touch the development record** | It is evidence, not text to repair |

---

## The inherited filings, and the two that need a named owner rather than a fourth pass

| Filing | Ruling |
|---|---|
| `paired_percentile_of_derived`'s sorted-pool precondition unasserted | **Claim it.** `interval_at` reads fixed ranks off an unsorted pool silently, and task 6 adds a **new** percentile construction returning a pool — which is the entry's own original condition, restored by H4b-2. The cost is one assertion at a seam this slice is opening anyway |
| *A column resample is only ever defined given finite inputs* | **Verify the premise, do not inherit it.** The identical prediction was made of H4b-2 and **did not come true**, which the entry itself records. H4c's unpaired *t* forms **do** sum per-side value columns and compute per-side variances, so the premise is likelier here — but likelier is not measured. Check, then claim or re-decline with the measurement |
| *The contrast path discloses nothing about its resample* — Findings 1 and 3 | **Claim Finding 3; re-decline Finding 1 with a named owner.** H4b-2 declined both on a "no new disclosure surface" ground that **does not transfer**: H4c adds four `method` spellings and a new record shape. Finding 3 — a resolved-`resample` echo on the contrast entry — is the same record this slice is already re-authoring. Finding 1 needs a contrast-scope `where` and a warning-registry row, which is warning-registry work; **owner: H4d** |
| `W-STATS-REPORTBY-THIN`'s whole-roster-versus-arm gap, and `report_by`'s `resample_columns` asymmetry | **Re-decline, and name a slice.** It is live on C1–C3, created by neither weights, clusters nor pairing, and it is **the only one of the five genuinely unrelated to unpaired constructions**. Declined by three consecutive slices, so a fourth decline needs an owner that is not a description: **H4d**, the last remaining slice whose surface is the `statistics` block. **H4d is terminal for it** — after H4d there is no statistics slice, so a fifth decline must convert it into a documented limitation with a permanent § Errors or § Validation row, not pass it on again |
| `E-DATA-CLUSTER-DERIVED` — the clustered derived draw | **Re-decline, on a new ground, owner H4d.** The old ground was cost and reachability, and H4b-2 used it up; the family argument that re-owned it here does point at this slice. The new ground is decision 8: H4c is the slice that gives the derived branch a **second** suppression condition, and building the clustered derived draw inside it would require that same guard to distinguish three states rather than two — compounding, in one commit, the exact corner that has already been given four wrong grounds in four commits. Building it after the guard is stable is strictly safer than building it while the guard is being written |

---

## The payoff, stated so it cannot be rounded

### Measured on 2026-08-18 against commit `051600c`

**H4c unblocks ZERO configs.** An unpaired contrast requires a declared `sweep.groups` axis; the nine
configs in `docs/feasibility-llm-growth-studies.md` declare `allocation: within` and `groups: []`, so
none reaches `E-DATA-ALLOCATION-CONTRAST` at all. Verified by grep with a can-fail control on the same
file — `allocation: within` → 3 (two config blocks plus one prose sentence), `allocation: between` →
1, **read** rather than counted and found to be a prose sentence listing fields *no config declares*.
**The no-remaining-core-side-blocker count stays six and the executable count stays three.** Neither
moves.

**A retired-refusal count is not an executable-run count**, and the two must not be conflated in any
sentence this slice writes. Both review verdicts on H4b-1 faulted that conflation, and a *correction*
on H4b-2 inverted the same two numbers and named a **retired** refusal as live. The net on refusals
here is **one retired, one minted** — not "a refusal narrowed", and not any number that moves.

**What H4c is worth instead**, stated so it is not mistaken for nothing:

- It is the **gate five `spec-defects.md` filings are queued behind**, four re-ownered to it by name on
  2026-08-18. A filing whose owner never runs is what `CLAUDE.md` calls "a ledger line saying filed is
  not a filing".
- It closes the largest standing **specification-versus-code** gap in the statistics family: six
  named-or-implied constructions with nothing behind them, and one documented record shape that no
  config can produce.
- It **removes the last hard-coded claim in the contrast record.** `paired: true` is true today
  *because* `validate` refuses everything else — a true claim resting on a guard, which is exactly the
  kind that goes silently false.
- It is the only slice that makes `groups × grid` — "each arm analyzed three ways", a design
  `reference.md` walks through twice — analyzable end to end rather than half-refused.

That is a specification-integrity payoff, not an execution payoff, and it must be argued as one.
**Nothing in the feasibility analysis gets closer to running because H4c landed.**

---

## Out of scope, with the route

| Out | Owner |
|---|---|
| `weighted_welch_t_over_units` and `weighted_unpaired_percentile_over_units` | **Refused** by `E-DATA-WEIGHT-ALLOCATION-CONTRAST`, minted here as a standing narrow refusal. No slice inherits it as work |
| The weight × cluster composition | **Refused** by `E-DATA-WEIGHT-CLUSTER-CONTRAST`, minted by H4b-2 and confirmed here to fire on an unpaired comparison too |
| `E-SWEEP-BASELINE-GROUP` and `E-SWEEP-ABLATE-BASELINE-GROUP` | **Permanent.** They refuse a declaration on the peers rule, grounded in § Expansion modes and in `experimental-designs.md` § Mistakes core prevents. H4c re-words their message, never their behaviour |
| `E-DATA-CLUSTER-DERIVED`, `W-STATS-REPORTBY-THIN`'s gap, and contrast-disclosure Finding 1 | **H4d**, by name and terminally |
| `statistics.null_test`, `p_value`, `fdr_bh` made real | **H4d** |
| `io.reuse_from` and `lineage.py` | **Unowned**, filed. Blocks E3/E4/E6 |
| Folds and holdouts within cells; `E-REPL-FOLD-CELLS` / `E-DATA-HOLDOUT-CELLS` | **H3c-3** |
| The apparatus probe, `apparatus_facts`, `cli.py`'s hardcoded `apparatus: null` | **H7d** |
| `study` / `report` / `diff` / `freeze` | **H8** |
| Interactions, dose-response orderings, differences-in-differences | **Refused.** Contrasts do not nest |

**Task count is 22.**
