# H4b-2 scoping — clusters through contrasts, and retiring `E-DATA-CLUSTER-CONTRAST`

Read-only measurement against `main` at `001ed9f`, on 2026-08-17. This re-measures the cluster half of
`docs/superpowers/H4b-SCOPING.md`, taken at `b65ab91` — **before H4b-1 merged**, and H4b-1 changed the
exact functions this slice must touch. Every identifier below was grepped, read or probed at `001ed9f`;
nothing is carried. Where this document contradicts its predecessor it says so and shows the command;
where it confirms one, it says that too.

**Verdict: 18 tasks**, against the charter's **7**. The direction is the repo's usual one — up — but
**one item moved down**, and that is the first time a re-scope here has recorded a decrease.

**Baseline at `001ed9f`:** `uv run pytest -q` → **2159 passed, 1 skipped, 2 xfailed**, 135 s, run in the
foreground. Identical to the figure `.superpowers/sdd/2026-08-17-weighted-contrasts/progress.md` closes on.

**The payoff, stated plainly and without hedging: H4b-2 unblocks ZERO configs.** Confirmed below (§ 4).

---

## 0. Executive summary — the five things that change what H4b-2 is

1. **Retiring the refusal today routes a declared cluster to a construction that ignores it.** This is
   the headline and it is not what the charter describes. `_comparison_step_blocks` takes `weights`,
   `strata` and `weighted_by` and **no membership parameter at all**; its `method` selection branches
   only on `weights is None` and `resample_columns`. So the moment `E-DATA-CLUSTER-CONTRAST` is deleted,
   a clustered contrast silently takes the **unclustered** path and publishes
   `method: paired_t_over_units` — or, under a weight, `weighted_paired_t_over_units` — beside
   per-condition values that *are* `t_over_units_clustered` / `weighted_t_over_units_clustered`, with
   nothing in the record saying which is which. That is H4b-1's own decision 4 one axis over: a raw
   interval whose counterpart was computed on different evidence, **and every existing test passes.**
   The retirement is therefore last, not first, and it is gated on the composition decision in § 3. § 1, § 3.
2. **H4b-1 left the weight × cluster combination unrefused, against its own scoping's instruction.**
   `H4b-SCOPING` § 10 assigned that combination to H4b-1 **by name** — "not to *whichever ships
   first*" — recommending a narrower code on the `E-DATA-WEIGHT-CONTRAST` / `E-DATA-CLUSTER-DERIVED`
   precedent. Measured: `grep -rn 'E-DATA-WEIGHT-CONTRAST' src/ docs/reference.md` → **exit 1**, and no
   replacement code was minted (`git diff b65ab91..001ed9f -- src/` adds no new `E-` identifier).
   Probed: a `weight_by` + `cluster_by` config with a baseline earns **`E-DATA-CLUSTER-CONTRAST` alone.**
   So H4b-2 inherits the combination, and `reference.md` § Statistical reporting's *"The `_clustered`
   suffix does not compose with either weighted form in this build"* — a **build-hedged sentence in the
   specification** — is now H4b-2's to resolve in one direction or the other. § 3.
3. **The charter's hardest document task is already discharged, by a better move than the one it
   proposed.** `H4b-SCOPING` § 5 ruled that `E-DATA-CLUSTER-CONTRAST`'s *"none of those five
   constructions exists"* could not be walked to zero and **had** to become an enumeration — converting a
   self-maintaining claim into a maintenance obligation, which it conceded `CLAUDE.md` § Habits warns
   against. H4b-1's fix round (`efa13bc`) instead narrowed the quantifier's **scope**: the row now reads
   "each **unweighted** contrast construction" and "**none of those** exists in this build". No count, no
   enumeration, still self-maintaining. **The charter's task 18 clause is gone.** § 2.
4. **The same fix stopped one file short — and the consequence is a warning about task 14, not a task of
   its own.** The "five" claim survives at **two live ends** the document fix did not reach:
   `validate.py`'s guard comment and `tests/test_validate.py`'s section header. **Both sit inside blocks
   task 14 deletes**, so H4b-2 owes them no repair — checked rather than assumed (§ 2). What it owes is
   the **surviving** citations, which are a different and larger set: four in `src/`, two in
   `reference.md`, and a group of `tests/` assertions that pin `E-DATA-CLUSTER-CONTRAST` and
   `E-DATA-ALLOCATION-CONTRAST` **co-reporting**, which is behaviour rather than wording. That H4b-1's
   enumeration missed two ends is the evidence that task 14's enumeration must be complete. § 2.
5. **The record-shape task moved DOWN, and it is the only item that did.** `H4b-SCOPING` § 3 ruled that a
   contrast entry had "nowhere to put `effective` or `clusters`" and that H4b-1's task 3 must *design and
   document* a shape no document licensed. H4b-1 did: it minted **`n_paired_effective`**, a scalar sibling
   of `n_paired`. So `n_paired_clusters` is a **precedent-following extension**, not a design from
   scratch — and `cli.py`'s own comment already records the other half of the answer, that `clusters`
   travels in `attrition`'s counts because "nothing in the documents shows a `clustered_by` sibling of
   `weighted_by`". § 3.

---

## 1. Every site of `E-DATA-CLUSTER-CONTRAST`, enumerated by reading then confirmed by grep

Read `validate._check_sweep` in full first, then confirmed. `§ Errors carries one row per code, not per
emit site` — so the unit of work is every site that raises *or* reports it.

| Site | Kind |
|---|---|
| `validate.py`, in `_check_sweep` | **The one emit.** Guard: `comparisons > 0 and isinstance(cluster_by, str) and cluster_by` |
| `validate.py`, `_check_unimplemented`'s docstring | Names it in the combination-refusal family |
| `validate.py`, the `_check_assign` comment | Cites `_check_sweep` as refusing that combination |
| `validate.py`, `E-DATA-ALLOCATION-CONTRAST`'s guard comment | Contrasts its own per-comparison reading against this one's per-family reading. **Must be re-worded, not deleted** |
| `stats.py`, `summarize_step`'s docstring | Names it as "the same missing construction one level over" from `E-DATA-CLUSTER-DERIVED` |
| `reference.md` § Errors `validate` reports | **Its § Errors row** — the one line whose final cell is the code itself |
| `reference.md` § Validation, *Clustered deltas aren't computed* | **Its § Validation row.** Located by reading the table; the row names no identifier |
| `reference.md` § Validation, *Allocation deltas aren't computed* | Cites *Clustered deltas aren't computed* **by name** to state its own per-comparison reading against it. **This citation is the one H4b-1's task-9-12 review installed deliberately so it would survive `E-DATA-WEIGHT-CONTRAST`'s deletion — and H4b-2's task 14 is what breaks it.** The ledger records the repair as chosen because "a filing that says *task 13 will handle it* is the maintenance obligation nobody owns"; the identical reasoning now points at this slice |
| `reference.md` § Errors core raises, `E-DATA-CLUSTER-DERIVED`'s row | "Temporary, alongside `E-DATA-CLUSTER-CONTRAST`" |
| `reference.md` § Statistical reporting | The suffix paragraph, and the `_clustered`-does-not-compose sentence, which links to the code |
| `feasibility-llm-growth-studies.md` § Executability on this build | One table row, **re-dated rather than edited** |
| `tests/test_validate.py`, `tests/test_cli.py` | Six assertions plus four comment blocks |

Can-fail control on the same file list: `grep -rn 'E-DATA-WEIGHT-CONTRAST' src/ docs/reference.md` →
**exit 1** on files where `E-DATA-CLUSTER-CONTRAST` returns hits — a different answer from the same
sweep shape, which is what says the sweep can fail.

### What the message claims, and how much is H4b-2's

The emit's closing clause: *"The combination will be honored once the paired **and unpaired** estimators
take clusters."* The § Errors row's parallel: *"there is no unpaired form at all."*

**H4b-2 owns the paired half only.** The unpaired clustered forms — `welch_t_over_units_clustered`,
`unpaired_percentile_over_units_clustered` — are H4c's, and `H4b-SCOPING` § 5's finding on that ownership
is **CONFIRMED at `001ed9f`**: `grep -rn 'paired.*_clustered\|_clustered.*paired' src/publishable/` →
**exit 1**, and neither unpaired stem exists in `src/` at all.

**But the count question the charter agonized over does not arise, and the reason is measurable.**
`_comparison_step_blocks` writes `"paired": True` **unconditionally, at both metric branches** — there is
no code path producing an unpaired contrast entry today. Every comparison that survives
`E-DATA-ALLOCATION-CONTRAST` is paired. So **two paired clustered constructions are sufficient to retire
`E-DATA-CLUSTER-CONTRAST`**, and the message's "and unpaired" clause is a promise about a code path that
does not exist rather than a construction the refusal is waiting on. Rewrite it to name the paired forms;
do not build toward it.

**The sequencing constraint that makes this true, which no charter row states.** Sufficiency holds
**only while `E-DATA-ALLOCATION-CONTRAST` stands**. If H4c lands first or concurrently, `paired` stops
being unconditional and the unpaired clustered forms become reachable with nothing built — the exact
mirror of the gap H4b-1 left this slice (§ 0.2). State it in the design and pin it with a test that
fails if `paired` is ever written `False` while no clustered unpaired construction exists.

---

## 2. The two stale-claim shapes, swept by claim over a named file list

**The sweep filtered the file list, never the output**, per `CLAUDE.md` § Two mechanical traps.

| Claim | Where it survives at `001ed9f` | Survives task 14? | Shape |
|---|---|---|---|
| "none of those **five** constructions exists" | `validate.py`'s guard comment; `tests/test_validate.py`'s section header | **No.** Both sit inside blocks task 14 deletes | **A fix that stopped one file short.** `efa13bc` repaired `reference.md`'s row alone. `CLAUDE.md` § Habits: *"Sweep for the claim, not for the file the claim was first noticed in"* — three sweeps in one slice stopped one file short, and this is the fourth |
| "once the paired **and unpaired** estimators take clusters" | The emit message; the § Errors row's "no unpaired form at all" | **No.** Task 14 deletes both | **A promise H4b-2 cannot keep.** True today, and it makes the row un-retirable *as written* — a different defect from a wrong count, and it dies with the row rather than needing a rewrite |
| "Temporary, alongside `E-DATA-CLUSTER-CONTRAST`" | `E-DATA-CLUSTER-DERIVED`'s § Errors row; `stats.summarize_step`'s docstring | **Yes** | **A dangling justification.** Task 4's decision governs it |
| "`_clustered` does not compose with either weighted form **in this build**" | `reference.md` § Statistical reporting, linking to the code | **Yes** | Task 1's decision governs it (§ 3) |
| "Unlike `E-DATA-CLUSTER-CONTRAST` above, this guard does not fire on `comparisons > 0`" | `E-DATA-ALLOCATION-CONTRAST`'s guard comment; `_check_unimplemented`'s docstring; `_check_assign`'s comment | **Yes** | Three `src/` sites that name a code about to stop existing |
| A config drawing `E-DATA-CLUSTER-CONTRAST` **and** `E-DATA-ALLOCATION-CONTRAST` together | `tests/test_validate.py`, `tests/test_cli.py` | **Yes** | **Behaviour, not wording.** These pin `validate`'s collect-don't-abort property across the two codes; after task 14 they must assert the allocation code alone, and deleting them instead would drop the pin |

**Checked, not assumed.** Whether a citation survives the retirement decides whether it is work. The
first two rows are the finding about H4b-1; the last four are the finding about H4b-2, and they are what
task 15 actually is.

**The development record is exempt.** `H4b-SCOPING.md`, `spec-defects.md`'s dated entries and the H4b-1
spec all carry "five" and **must not be retro-edited** — they record what was measured on their date.
`CLAUDE.md`: *"retro-editing either destroys the evidence they exist to hold."*

**What the charter got right and what it got wrong here.** `H4b-SCOPING` § 5's *analysis* was correct —
the five could not be walked to zero — and its *remedy* was worse than the one that shipped. Narrowing
the quantifier to "each **unweighted** contrast construction" makes the sentence true today, keeps it
self-maintaining, and lets H4b-2 retire the row by **deletion** rather than by rewriting it into an
enumeration nobody owns. Record the trade as **resolved in H4b-1's favour**, not as owed.

---

## 3. What H4b-1 changed underneath H4b-2 — smaller, larger, or differently shaped

Each row answers the brief's question directly. **Three of six make H4b-2 larger, one smaller, two
differently shaped.**

| What H4b-1 changed | Effect on H4b-2 | Why |
|---|---|---|
| `weighted_paired_t_over_units` and `weighted_paired_percentile_over_units` exist, on the corrected and general paths | **LARGER — this is the headline** | The `_clustered` suffix now has **four** unclustered forms to compose with, not two. § Statistical reporting says the suffix "does not compose with either weighted form **in this build**" — a build-hedged sentence, and `E-DATA-CLUSTER-CONTRAST` is the only thing enforcing it. H4b-2 must either build the two weighted clustered forms or mint the narrower refusal H4b-1's own scoping told H4b-1 to mint |
| `Member` carries `weights` as a **modifier on `diffs`**, not a third evidence kind | **LARGER, and predicted** | The H4b-1 ledger's task-4 ruling names its own cost: *"a fourth evidence dialect in `Member` that H4b-2 and H4c both have to widen."* `clusters` is that widening. And `correction.py` is a **second production call site** for both paired *t* forms — `_corrected_bounds` calls `paired_t_over_units` and `weighted_paired_t_over_units` directly — so it is `paired_t_over_units_clustered`'s **first caller**, exactly as H4b-1's spec correction 2 found for the weighted form. The charter names `correction.py` nowhere |
| `paired_percentile_of_derived` takes `strata` and **enforces** a sorted-`keys` contract | **DIFFERENTLY SHAPED** | The clustered percentile form must now compose with stratification: § Validation's *`E-STATS-RESAMPLE-STRATIFY-VARIES`* already specifies "a resample draws whole clusters, so a cluster carrying two stratum values can be dealt to neither", and `percentile_over_units_clustered` already implements that equality **per condition**. So the paired clustered draw is *cluster within stratum*, and the rule it must satisfy is written down and has a working sibling to mirror — not a new decision, but a composition the charter never named |
| `_compute_vs_baseline`, `_compute_declared_contrasts` and `_comparison_step_blocks` thread `weights` and `strata` | **SMALLER than the equivalent H4b-1 task** | The keyword-only pattern is established and the membership mapping **already exists at the right scope**: `command_run` builds `clusters = clusters_of(roster, cluster_by)` from the single authority and hands it to `summarize_step`. H4b-2 threads an existing mapping down three signatures; H4b-1 had to build one |
| `n_paired_effective` minted as a scalar sibling of `n_paired` | **SMALLER — the one item that moved down** | § 0.5. The charter's "design and document a shape no document licenses" is discharged; `n_paired_clusters` follows the precedent. `cli.py` also records why `clusters` travels in `attrition` per condition — "nothing in the documents shows a `clustered_by` sibling of `weighted_by`" — which is the argument H4b-2 must either extend or distinguish, not invent |
| The `method`-selection branch now reads `weights is None` and `resample_columns` | **DIFFERENTLY SHAPED, and it is the retirement's gate** | A two-way branch becomes four-way (or six-way, per the composition decision). Today it has **no `clusters` argument to branch on**, which is § 0.1 |

### The composition decision, stated as the decision it is

Two defensible answers, and H4b-2 owns choosing before anything is built:

- **Build the composition** — `weighted_paired_t_over_units_clustered` and
  `weighted_paired_percentile_over_units_clustered`, deleting the "does not compose in this build"
  sentence. Four new constructions, and the weighted clustered *t*'s df question is already answered per
  condition: `weighted_t_over_units_clustered` uses "df = clusters − 1, **not** Kish's effective size,
  since `cluster_by` is what decides the draw", so the paired form inherits it rather than re-litigating.
- **Mint the narrower refusal** — keep the sentence, refuse `weight_by` × `cluster_by` × a comparison
  under a new code, on the precedent H3a used minting `E-DATA-WEIGHT-CONTRAST` and H3b
  `E-DATA-CLUSTER-DERIVED`. Two new constructions, one new code, one new § Errors row and § Validation
  row, and a deferral H4c inherits.

**The trap either way:** the "does not compose" sentence is hedged *in this build*, so leaving it
standing while deleting the refusal that enforces it makes the specification describe a behaviour core no
longer has. **A sentence and a guard are one claim seen from two ends** — the rule H4b-1's own review
applied to the § Validation / § Errors pair.

---

## 4. The payoff — zero, and what H4b-2 is worth instead

**Measured 2026-08-17 against `001ed9f`: no config in `docs/feasibility-llm-growth-studies.md` declares
`cluster_by`.** `grep -n 'cluster_by' docs/feasibility-llm-growth-studies.md` → **two hits, both
`cluster_by: null`**, plus one prose sentence saying so in its own words. Can-fail control on the same
file: `grep -c 'weight_by'` → **10**, a field that *is* declared. The analysis's § Executability prose
already states it: `cluster_by` is among the fields "no config in this analysis declares".

**So: H4b-2 unblocks zero configs, retires no refusal any experiment hits, and moves neither the
no-remaining-core-side-blocker count (six) nor the executable count (three).** Both numbers stand
unchanged at 2026-08-17 / `001ed9f`. Do not write a sentence that implies otherwise; `CLAUDE.md`'s
feasibility procedure step 10 exists because a refusal count has been read as an execution count, and
every slice since H4a has had to correct one.

**What it is worth instead — four things, each dated to 2026-08-17 / `001ed9f`:**

| Worth | What it is |
|---|---|
| **A live defect closed** | The zero-width stratified paired draw, filed **by H4b-1 task 5** and owned by **H4b-2 by name**: `paired_percentile_of_derived` is the only one of four percentile constructions with **no content-based degenerate refusal**, and task 5's `strata` parameter made it reachable — a near-unique `stratify_by` publishes `ci95: [x, x]`, a zero-width 95 % interval § Statistical reporting refuses in those terms, indistinguishable from a genuine one. **This did not exist when the charter was written** |
| **A documented rule given code** | § Statistical reporting's `_clustered` suffix rule is specification with **no construction behind it** — `grep -rn 'paired.*_clustered' src/` → exit 1. This is `CLAUDE.md` § Misreadings' *"a documented rule with no code"* shape, of which five § Validation rows were once instances |
| **Two refusals narrowed** | `E-DATA-CLUSTER-CONTRAST` retired; `E-DATA-CLUSTER-DERIVED` either retired or re-owned by name (§ 5) |
| **A specification sentence resolved** | The `_clustered`-does-not-compose hedge (§ 3), and the weight × cluster combination H4b-1 left unrefused (§ 0.2) — the one thing H4b-SCOPING said the split "does not cleanly cut" |

---

## 5. The constructions — what exists, what is called, what is documented with no code

| Construction | In `stats.py` | Production callers | Documented |
|---|---|---|---|
| `t_over_units_clustered` | Yes | 1, `summarize_step` | § Statistical reporting row |
| `weighted_t_over_units_clustered` | Yes | 1, `summarize_step` | § Statistical reporting row |
| `percentile_over_units_clustered` | Yes | 1, `summarize_step` | § Statistical reporting row |
| `paired_t_over_units` | Yes | 2 — `cli.py` **and `correction.py`** | § Statistical reporting row |
| `weighted_paired_t_over_units` | Yes (H4b-1) | 2 — `cli.py` **and `correction.py`** | § Statistical reporting row (H4b-1) |
| `paired_percentile_of_derived` | Yes | 2, both in `cli.py` | Two rows, under two `method` names |
| `paired_t_over_units_clustered` | **No** | — | **Derived from the suffix rule; named nowhere.** Confirmed at `001ed9f` |
| `paired_percentile_over_units_clustered` | **No** | — | **Same.** The charter listed both as though they were named surfaces |
| The weighted clustered pair | **No** | — | **Explicitly excluded** by the "does not compose in this build" sentence |
| `welch_t_over_units_clustered`, `unpaired_percentile_over_units_clustered` | **No — and unreachable** | — | **H4c's.** `E-DATA-ALLOCATION-CONTRAST` refuses every unpaired comparison, and `paired` is written unconditionally `True` |
| A clustered draw for a **derived** metric | **No** | — | `E-DATA-CLUSTER-DERIVED`, raised in `stats.summarize_step` — **run time and per condition**, not a contrast at all |

**`E-DATA-CLUSTER-DERIVED` must be assigned by name, and this slice is where.** `H4b-SCOPING` § 5
recommended the cluster half "because the construction it needs is the same membership-aware derived
draw". Re-checked at `001ed9f`: it is emitted once, from `summarize_step`, and its § Errors row says
"Temporary, alongside `E-DATA-CLUSTER-CONTRAST`" — so **retiring only the contrast refusal leaves that
row's own justification dangling**, which is the two-ended-check rule again. H4b-2 either builds the
clustered derived draw or re-words the row and re-owns the code explicitly. Silence is how a deferral
ends up owned by nobody.

---

## 6. The filings that name H4b-2 — every one, and what each costs

`grep -n 'H4b-2' docs/superpowers/spec-defects.md` → hits in **five** entries; reading each places them.
Two more name **H4 Statistics** in terms that resolve here.

| Entry | Owner as filed | What it costs H4b-2 |
|---|---|---|
| **"a stratified paired draw can publish a zero-width contrast interval"** | "**Owner: H4b-2 — clusters through contrasts**, by name and not *whichever slice ships next*" | **A real defect, filed by H4b-1 itself.** "H4b-2 is the half that adds the remaining paired percentile construction, so it is where the degenerate sweep belongs for all of them at once." One task, built **with** the new construction, not after |
| **"A column resample is only ever defined given finite inputs"** | "**Owner re-assigned to H4b-2**" | Two `*_is_a_known_unfixed_gap` tests that must move **with** the entry. The entry's own reasoning: H4b-2 "is the next place a whole weight vector or value column is drawn as a unit". Its proposed resolution explicitly says it "likely also affects the unweighted and **clustered** percentile constructions" |
| **"The contrast path discloses nothing about its resample…"** | Findings 1 and 3 "stay with **H4b-2** as the nearer of the two contrast-family slices" | A contrast-scope thin finding needing a `where` and a registry row, and a contrast entry carrying no resolved-`resample` echo. Finding 2 was closed by H4b-1 task 5 |
| **`paired_percentile_of_derived`'s sorted-pool precondition unasserted** | "**H4b-2** — H4b-1 task 5 gave the function a `strata` parameter…" | **The entry's claim about the code is stale and must be re-stated or struck, not implemented as filed.** Read at `001ed9f`: *both* return paths sort the returned pool (`pool=sorted(values)` and `values.sort()` before `pool=values`). The amendment's "second route to an unsorted-pool input" is about the **stratum key pools**, a different object from `PairedResample.pool`. `CLAUDE.md`: *"when you change code a `spec-defects.md` entry describes, re-read the entry."* The row's original condition — "a **new** percentile construction returning an unsorted pool" — is exactly what this slice adds, so the *obligation* is real and the *diagnosis* is not. **Recommended direction: restore the entry to its original condition and strike the 2026-08-17 amendment's stratum-pool reasoning**, rather than implementing the amendment as filed |
| **§ *How a metric becomes a number* is cited across the repo and does not exist** | "**unassigned**, and explicitly declined once more… **H4b-2** is next to touch that material" | Claim it or decline it **in writing**. Declined twice now; a third silent pass is how it goes stale. Note `paired_t_over_units`' docstring cites it, and H4b-2 edits that function's neighbourhood |
| **"`report_by` … a level's recorded-column interval stays `t_over_units`"** | "**H4 Statistics**" | Live on C1–C3, **not** created or touched by clusters. Recommend H4b-2 **declines it explicitly** and re-owns it to H4c — it is a `report_by` gap, and folding it in is what `H4b-SCOPING` § 12 warned against for its sibling |
| **`correction.corrected_fields` dedupe unpinned** | "**H4 Statistics** — the slice that would build `Member` lists from somewhere other than `cli._comparison_step_blocks`" | H4b-2 does **not** meet that condition — it widens `Member`, it does not build lists elsewhere. Record as **not H4b-2's**, so it is not re-scoped as owed |

**If H4b-2 ships without discharging or re-owning each, the filing count goes up rather than down.**

---

## 7. Traps specific to this slice

**The retirement that publishes an unclustered number.** § 0.1. Deleting the emit before membership
reaches `_comparison_step_blocks` produces a clustered run whose per-condition intervals are
cluster-robust and whose deltas are not, with a `method` string that names neither state. **Every
existing test passes**, because the combination is refused today and no fixture exercises it. Delete the
emit **last**, after every construction, `method` string and record key lands — the discipline H7b Part A
bought and H4b-1's task 13 kept.

**A cluster fixture whose cluster count cannot change the answer.** `CLAUDE.md` § Writing checks that can
fail names this exact instance: *"a cluster fixture where correct and buggy cluster counts were both 3"*.
And the df is the discriminating dimension — § Statistical reporting: "10 animals give 9, not 299". Size
the fixture so the clustered and unclustered intervals differ by a margin no rounding can produce, and
**compute both by hand before asserting**, exactly as H4b-1's controller did for 6.0 versus 8.0.

**A singleton-cluster fixture.** One unit per cluster makes `clusters − 1` equal `n_paired − 1`, so the
clustered and unclustered *t* forms coincide **exactly** and every assertion passes under a mutant that
ignores membership entirely. This is the *fixture whose numbers agree with the bug* shape.

**A mutation applied to the per-condition clustered form.** `t_over_units_clustered` is shipped, tested
and correct; breaking it proves nothing about the paired form. The discriminating mutation is on the new
construction and on the `method`-selection branch — **a mutation is a claim too**, and both branches must
be able to produce different results.

**Reading "this config is refused" as "this path does not run."** `CLAUDE.md` names it, and H4b-1's
task-6-8 review recorded the **fourth** reader making it — then its task-13-15 review recorded a fifth,
where a mutation was declared blind on the strength of **one self-chosen test**. `validate` collects. Run
every mutation against the **full, unfiltered** suite in the **foreground**; H4b-1's ledger records a
re-reviewer who backgrounded a run and stopped with a mutation possibly still applied.

**A test asserting only that `n_paired_clusters` is present.** H4b-1 pinned the three-way obligation for
weights — value, interval and size move together — and the reviewer had to force it once already, after
`weighted_by`'s value passed under a hardcoded constant. A clustered entry has the same obligation.

**Kish and clusters in the same entry.** Under the *build the composition* branch, an entry can carry
`n_paired`, `n_paired_effective` **and** `n_paired_clusters`, and the df comes from the **cluster count**,
not from Kish — § Statistical reporting settles that per condition and the paired form inherits it. A
fixture where the two happen to coincide cannot see a construction that took the wrong one.

**A carried line number.** `H4b-SCOPING` cited `stats.py:1900` for `E-DATA-CLUSTER-DERIVED`; it is
elsewhere at `001ed9f`. **Cite by name.** This document cites no line numbers for that reason.

---

## 8. Decomposition — 18 tasks, against the charter's 7

Grain matches `H4b-SCOPING.md`, `H7b-PartB-SCOPING.md` and `H3d-SCOPING-2.md`: each new construction,
each new record key, and each document-table edit is its own task. 18 sits inside this repo's band
(H3c-1 20, H7b Part A 20, H3d 19, H4b-1 15, H7c 14, H7b Part B 13).

**Six ordering constraints, five of which the charter does not state.**

| Constraint | Reason |
|---|---|
| **Task 1 before 6–9 and 11** | The composition decision fixes how many constructions exist and what `method` each writes. Building first bakes the answer in by omission — H4b-1's own *5 before 7* ruling, one axis over |
| **Task 3 before 7** | A degenerate-draw refusal lives **inside** the percentile construction. Same shape, same reason |
| **Task 2 before 13** | A record key must exist in a document before code writes it — H4b-1's *2 and 3 before 7–10* |
| **Task 6 before 12** | `correction._corrected_bounds` is `paired_t_over_units_clustered`'s **first caller**, exactly as H4b-1's spec correction 2 found for the weighted form |
| **Task 14 last** | A refusal is deleted only after everything it stood in for exists (§ 7) |
| **Task 15 must not touch the development record** | § 2. `H4b-SCOPING`, `spec-defects.md`'s dated entries and H4b-1's spec are evidence, not text to repair |

**Decisions and documents (5)**

| # | Task | Against the charter |
|---|---|---|
| 1 | **Decide the weight × cluster composition** (§ 3): build the two weighted clustered forms, or mint the narrower refusal. Argued against `reference.md` § Statistical reporting's build-hedged "does not compose" sentence and H4b-1's decision-4 precedent | **NEW.** The charter assigned this to H4b-1 by name; H4b-1 did not do it |
| 2 | **Document the clustered contrast record key** — `n_paired_clusters` beside `n_paired_effective`, on H4b-1's own precedent, and distinguish or extend `cli.py`'s "no `clustered_by` sibling" argument | **SMALLER.** The charter's "design a shape no document licenses" is discharged |
| 3 | **Decide the degenerate-draw refusal** for the paired percentile family — the filed zero-width defect, and the content-based refusal its three siblings each carry | **NEW.** Filed by H4b-1 after the charter was written |
| 4 | **Decide `E-DATA-CLUSTER-DERIVED`'s fate** (§ 5): build the clustered derived draw, or re-word its row and re-own the code by name | Charter task 17 assumed *build*; the decision is the task |
| 5 | **Record the `E-DATA-ALLOCATION-CONTRAST` sequencing dependency** in writing, with the `paired`-is-unconditionally-`True` measurement that makes two constructions sufficient (§ 1) | **NEW as a task.** The charter's § 5 named the dependency and gave it no owner |

**Task 5's pin, stated precisely so it is not written as an unfailable one.** `paired` is a **literal
`True`** at both branches, so there is no runtime state to assert against and "a test that fails if
`paired` is ever `False`" would be a mutation whose two branches cannot differ — the trap § 7 names.
What can be pinned is the literal: assert both sites write `True` unconditionally, so the test fails the
moment H4c makes either conditional and forces whoever does that to confront the clustered unpaired gap.

**Constructions (4)**

| # | Task |
|---|---|
| 6 | **`paired_t_over_units_clustered`** — CR1 over the differenced values, df = clusters − 1, mirroring `t_over_units_clustered` rather than hand-rolling a variance |
| 7 | **`paired_percentile_over_units_clustered`** — whole clusters, one joint draw for both sides, **composing with `strata`**: a cluster drawn within its stratum, mirroring `percentile_over_units_clustered`'s existing equality (§ 3) |
| 8 | **The weighted clustered pair, or the refusal** — per task 1 |
| 9 | **The content-based degenerate refusal** built into the paired percentile family — per task 3 |

**Threading and record (4)**

| # | Task |
|---|---|
| 10 | **Thread `clusters` into `_compute_vs_baseline`, `_compute_declared_contrasts` and `_comparison_step_blocks`** — the mapping already exists at `command_run`; none of the three takes it |
| 11 | **The `method`-selection branch**: four-way (or six-way) on `weights` × `clusters` × `resample_columns`, and the `method` string each writes |
| 12 | **`Member.clusters` and the corrected bound** — `correction.py`, the call site the charter names nowhere, and the second widening H4b-1's task-4 ruling predicted |
| 13 | **`n_paired_clusters` on every affected entry**, with H4b-1's three-way move-together obligation pinned |

**Retirement, residue and regression (5)**

| # | Task |
|---|---|
| 14 | **Retire `E-DATA-CLUSTER-CONTRAST`** — the one emit, its § Errors row, its § Validation row *Clustered deltas aren't computed*, the sibling row *Allocation deltas aren't computed* re-worded so it survives the deletion (§ 1), and six test assertions. **Last** |
| 15 | **The surviving-citation sweep** (§ 2) — every site naming `E-DATA-CLUSTER-CONTRAST` that task 14 does **not** delete: three `src/publishable/validate.py` comments, `stats.summarize_step`'s docstring, `E-DATA-CLUSTER-DERIVED`'s § Errors row, § Statistical reporting's compose sentence, and the `tests/` assertions pinning the two codes **co-reporting**, which are behaviour and must be narrowed rather than deleted. By claim, over a named file list, **excluding the development record**. *Not* the "five" sweep — those two ends die with task 14 |
| 16 | **The filings** (§ 6): the finiteness entry with its two `*_is_a_known_unfixed_gap` tests, contrast-disclosure findings 1 and 3, the sorted-pool row **re-stated or struck** rather than implemented as filed, § *How a metric becomes a number* claimed or declined, and `report_by` explicitly re-owned to H4c |
| 17 | **The regression pin** — an unclustered unweighted config byte-identical (`paired_t_over_units`, `paired_percentile_over_units`, the worked example's intervals, which `CLAUDE.md` § The worked example says **must not be narrowed back**), **and an unclustered weighted one**, which is H4b-1's output and must not move |
| 18 | **The dated re-measurement** in `feasibility-llm-growth-studies.md` § Executability — re-dated, not edited, stating **zero** plainly and leaving six and three unchanged (§ 4) |

---

## 9. What the charter names that no longer exists, and what is real that it never named

**Both have been found on every re-scope so far, and both are here.**

### Named by the charter, gone at `001ed9f`

| What the charter says | State |
|---|---|
| Task 18: "rewriting the *five constructions* sentence as an enumeration and arguing the trade" | **Discharged by `efa13bc`**, by a better move — narrowing the quantifier's scope, not counting (§ 2). The self-maintaining-versus-enumeration trade does not need arguing |
| Task 16: "`clusters` beside `n_paired`, **in the shape task 3 designs**" | Task 3 was H4b-1's and it shipped a different, smaller answer. The referenced shape does not exist as described (§ 0.5) |
| § 10: "H4b-2 then *retires* the new code as part of task 18" — the weight × cluster combination refusal H4b-1 was to mint | **The code was never minted.** H4b-2 has nothing to retire and a decision to make instead (§ 0.2) |
| § 12: `E-DATA-WEIGHT-CONTRAST` as a live sibling row to re-word | **Retired.** `grep -rn 'E-DATA-WEIGHT-CONTRAST' src/ docs/reference.md` → exit 1 |

### Real, and never named by the charter

| What | Why it matters |
|---|---|
| **The silent mis-routing** — `_comparison_step_blocks` has no membership parameter, so retiring the refusal publishes an unclustered delta under an unclustered `method` beside cluster-robust per-condition values | § 0.1. The headline, and it reorders the slice |
| **`correction.py` as a second call site** for both paired *t* forms | § 3. `_corrected_bounds` is the clustered form's **first** caller |
| **`strata` × clusters composition** inside the new percentile construction | § 3. `paired_percentile_of_derived` gained `strata` **after** the charter was written |
| **The zero-width stratified paired draw**, filed by H4b-1, owned by H4b-2 by name | § 6. Did not exist when the charter was written |
| **`paired` written unconditionally `True`** at both branches | § 1. The measurement that makes two paired constructions sufficient — and the thing H4c breaks |
| **The "five" claim alive at two ends** in `src/` and `tests/` | § 2 |

---

## 10. What is NOT in H4b-2

| Out | Owner |
|---|---|
| `welch_t_over_units`, `unpaired_percentile_over_units` and both clustered counterparts; `E-DATA-ALLOCATION-CONTRAST`; the `cohens_d` *d*s branch | **H4c.** Its refusal standing is what makes H4b-2's two paired constructions sufficient (§ 1) |
| `W-STATS-REPORTBY-THIN`'s whole-roster-versus-arm gap, and the `report_by` level's `resample_columns` asymmetry | **H4c.** Live on C1–C3, created by neither weights nor clusters. H4b-2 must **decline it in writing**, not fold it in |
| `statistics.null_test`, `p_value`, `fdr_bh` made real | **H4d** |
| `io.reuse_from` and `lineage.py` | **Unowned**, filed. Blocks E3/E4/E6 and unsettles C1–C3 |
| Folds and holdouts within cells; `E-REPL-FOLD-CELLS` / `E-DATA-HOLDOUT-CELLS` | **H3c-3** |
| The apparatus probe, `apparatus_facts`, `cli.py`'s hardcoded `apparatus: null` | **H7d** |
| `study` / `report` / `diff` / `freeze` | **H8** |
| An `Estimate` returned by a `summary` step | **Never recomputed.** `reported: true`, outside the correction family, and the documented route `E-DATA-CLUSTER-CONTRAST`'s own message offers. A clustered pass walking every metric block **must skip it** — a test H4b-2 owes, not a boundary it merely respects |
| Interactions, dose-response orderings, differences-in-differences | **Refused.** Contrasts do not nest |
