# H4c scoping — the unpaired contrast forms, and retiring `E-DATA-ALLOCATION-CONTRAST`

Read-only measurement against `main` at `051600c`, on 2026-08-18. This re-scopes the H4c row of
`docs/superpowers/H4-SCOPING.md`, written at a commit **before H4a, H4b-1 and H4b-2 existed**, and
those three slices changed every function H4c must touch. Every identifier below was grepped, read or
probed at `051600c`; nothing is carried. Where this document contradicts a predecessor it says so and
shows the command.

**Verdict: 22 tasks**, against the charter's **12**. The direction is the repo's usual one — up — and
every bucket measured is larger than the charter's row, none smaller.

**Baseline at `051600c`:** `uv run pytest -q` → **2200 passed, 1 skipped, 2 xfailed**, 113.77 s, run in
the foreground.

**The payoff, stated plainly and without hedging: H4c unblocks ZERO configs**, and it does not move
either count H4b-1 and H4b-2 left — six with no remaining core-side blocker, three executable.
Measured in § 5, with a control that can fail. What H4c is worth instead is stated there too, and it is
not nothing: it is the gate five `spec-defects.md` filings are queued behind, and it is the slice that
makes `reference.md`'s own documented unpaired record producible — or proves it cannot be.

---

## 0. Executive summary — the five things that change what H4c is

1. **`Member` has no shape for an unpaired contrast, and the fix is a third evidence *kind*, not a
   fourth modifier.** `correction.Member` is `pool` XOR `diffs`, enforced in `__post_init__`, with
   `weights` and `clusters` as modifiers **keyed on `diffs`** — both raise when `diffs is None`. A
   Welch interval has no differences at all: its evidence is two per-side value vectors. So H4c breaks
   the exactly-one rule, both modifier length checks, and `_corrected_bounds`' three-way branch — and
   `correction.py` is a **second production call site for the contrast constructions** that the charter
   names nowhere. The H4b-1 ledger predicted "a fourth evidence dialect in `Member` that H4b-2 and H4c
   both have to widen"; what H4b-2 added was a dialect, and what H4c needs is a new kind. § 3.
2. **Retiring `E-DATA-ALLOCATION-CONTRAST` makes the plain, the weighted *and* the clustered unpaired
   shapes reachable in one stroke.** Probed: each of the three earns
   `E-DATA-ALLOCATION-CONTRAST` **alone** — no second refusal stands behind it for the weighted or the
   clustered form. So the "build the pair, refuse the composition" arrangement H4b-2 could make is not
   available here: **six unpaired constructions**, not two, in the same slice as the retirement. The one
   thing H4c genuinely inherits as a refusal rather than as work is weight × cluster, and that saves it
   nothing it would otherwise build. § 2, § 3.
3. **The four documents give a weighted unpaired contrast no `method` string at all** — verbatim the
   H4b-1 finding one axis over, and unrepaired since. An alternation grep for both stems over `src/`,
   `docs/` and `tests/` returned **zero hits** at `051600c`, before this document existed and
   introduced the first four. § Statistical reporting names two unpaired spellings, implies two more
   through the `_clustered` suffix rule, and names the last two nowhere. § 2.
4. **The only documented unpaired record in the four documents sits in a `vs_baseline` block that core
   permanently refuses, and H4c does not lift that refusal.** § Allocation's YAML shows
   `paired: false, confounded: true, method: unpaired_percentile_over_units` under
   `vs_baseline: # 03_arm=treatment__method=spearman` — a shape reachable only from a baseline fixing a
   group level, which `E-SWEEP-BASELINE-GROUP` refuses on the *peers* rule, permanently and for its own
   reason. Probed both ways. So H4c's whole reachable surface is the **declared contrast**, and the
   record shape it must design has no licence in any document it can honour as written. § 4.
5. **`n_paired` is not a key with a gap beside it — it is a key whose definition does not apply.**
   § Contrasts defines it as *the intersection*, says it "has to be recorded", and both scalar siblings
   H4b-1 and H4b-2 minted (`n_paired_effective`, `n_paired_clusters`) rest on that same argument. An
   unpaired contrast's intersection is **empty by construction**, so `n_paired: 0` is a true number and
   a false description, and `W-STATS-CONTRAST-THIN` plus `limits.min_reported_n` both key on it. The
   charter calls this "the `n_paired` spec gap", one row of twelve; measured, it is a record-shape design
   task with three keys and a warning hanging off it. § 4.

---

## 1. Every site of `E-DATA-ALLOCATION-CONTRAST`, enumerated by reading then confirmed by grep

`validate._check_sweep` was read in full first, then confirmed by grep. `reference.md` § Errors carries
one row per code covering **every** emit site, so the unit of work is every site that raises *or*
reports it — the discipline a task once scoped by a helper's single call site got wrong.

| Site | Kind |
|---|---|
| `validate.py`, in `_check_sweep`, the `for comp in resolved_contrasts` loop | **The one emit.** Guard: the axes `differing_axes` returns, intersected with either side's `selectors`, non-empty — read per resolved comparison, not once for the family |
| `validate.py`, the same guard's 40-line comment block | States the per-comparison reading, the empty-pairing consequence, and "H4 Statistics owns the unpaired estimator family and lifts this the moment it exists" |
| `validate.py`, `_check_assign`'s docstring | Cites it as the precedent for refusing a combination while honouring both declarations |
| `validate.py`, `_check_unimplemented`'s comment | Cites `_check_sweep` as the owner of the cross-arm contrast refusal |
| `validate.py`, `E-SWEEP-BASELINE-GROUP`'s guard comment **and its emitted message** | The message says the delta is refused "until the unpaired estimators exist" — **inside a permanent refusal's text**, so this is a re-wording H4c owes and cannot discharge by deleting a row (§ 4) |
| `cli.py`, `_comparison_step_blocks`' docstring | Two paragraphs: the `paired: true` justification, and "**That claim expires with `E-DATA-ALLOCATION-CONTRAST`**", naming the derivation H4c must write |
| `contrasts.py`, `differing_axes`' docstring | Names its two callers, one of them "the (temporarily) hard-coded `paired`" |
| `reference.md` § Validation, *Allocation deltas aren't computed* | Its § Validation row |
| `reference.md` § Errors `validate` reports | Its § Errors row — the long one, which already states the `E-SWEEP-BASELINE-GROUP` interaction § 4 measures |
| `reference.md` § Allocation, the peers paragraph | "**This build refuses to compute that delta** (`E-DATA-ALLOCATION-CONTRAST`, temporary)" |
| `experimental-designs.md` § Mistakes core prevents | *Two identical measurements reported as two arms* names it |
| `feasibility-llm-growth-studies.md` § What core refuses / § Executability | One refusal row, and one table row — **re-dated rather than edited**, per the development-record rule |
| `tests/test_validate.py` | **17 lines** by a sweep for the code *or* the word "unpaired", of which **14** name the code: filtered finding-set assertions, two exact-set assertions, and comment or docstring claims |
| `tests/test_cli.py` | **6 lines** by the same sweep, of which **3** name the code; one is a pin's docstring (§ 6) |

**Can-fail control on the same file list:** `grep -rn 'E-DATA-CLUSTER-CONTRAST' src/ docs/reference.md`
→ **exit 1**, on files where `E-DATA-ALLOCATION-CONTRAST` returns hits. A different answer from the same
sweep shape is what says the sweep can fail. The file **list** was filtered, never the output.

### What else stands between a config and an unpaired contrast

Probed rather than reasoned about, because `validate` collects rather than aborting and a refusal
elsewhere never makes a later check unreachable. Five shapes, each a real config through
`validate_config`, error codes as an exact set:

| Shape | Exact error set at `051600c` |
|---|---|
| `between` + `assign` + `groups` + declared cross-arm contrast | `{E-DATA-ALLOCATION-CONTRAST}` |
| the same + `weight_by` | `{E-DATA-ALLOCATION-CONTRAST}` |
| the same + `cluster_by` | `{E-DATA-ALLOCATION-CONTRAST}` |
| the same + `weight_by` + `cluster_by` | `{E-DATA-ALLOCATION-CONTRAST, E-DATA-WEIGHT-CLUSTER-CONTRAST}` |
| the same with no contrast at all — the can-fail control | `{}` (clean) |

Three readings follow, and the third is the one that resizes the slice. `E-DATA-ALLOCATION-CONTRAST`
is the **sole** blocker for the plain, weighted and clustered unpaired shapes alike. The clean control
proves the sweep can fail and that the combination itself is legal — only a comparison beside it is
refused. And `E-DATA-WEIGHT-CLUSTER-CONTRAST` **does** fire on an unpaired comparison, which is the
composition H4b-2 said H4c inherits: it is inherited as a *standing refusal*, not as work, and it
removes no construction from H4c's list (§ 3).

`allocation: within` beside a `groups` axis earns `E-DATA-ALLOCATION-WITHIN-ARMS`, and a `groups` axis
with no `assign` earns `E-DATA-ALLOCATION-NO-ARMS`. Neither is H4c's: they refuse a *declaration* a
correct unpaired config does not make. They are named here because a fixture that forgets them
attributes its refusal to the wrong code, which is the "a refusal that happens to fire must be
attributed before it is counted" trap.

### What the message claims, and how much of that is H4c's

The emit's own text, at three points: *"no construction in this build computes an unpaired interval"*;
*"there is no `welch_t_over_units` or `unpaired_percentile_over_units` to call"*; *"This will be honored
once the unpaired estimators exist."* All three are H4c's in full — unlike H4b-2, which owned only the
paired half of its predecessor's message. There is no fourth slice behind this one to route a clause to.

But the message **under-names what it is waiting on**. It names two constructions; § 3 measures six.
Rewriting it is not on the list, because H4c deletes it; what is on the list is not building toward the
two it names and calling the family done — the same failure H4b-2 avoided by counting cells rather
than reading the message.

---

## 2. The constructions: which exist, which are named, which are vapour

Read `src/publishable/stats.py`'s definition list in full, then grepped. **No unpaired construction
exists in `src/` at any spelling**: `grep -rn 'welch_\|unpaired_' src/` → **five hits, all prose** — two
inside `E-DATA-ALLOCATION-CONTRAST`'s own emitted message, two in the comment above it (one of which
*is* this grep, quoted), and one in `_comparison_step_blocks`' docstring. Confirms `H4b-SCOPING` § 5 and
`H4b-2-SCOPING` § 1 at this commit. A separate alternation grep for `weighted_welch` and
`weighted_unpaired` over `src/`, `docs/` and `tests/` returned **zero** — the can-fail control being the
first grep, which returns hits over the same file list. `cohens_ds` does not exist either: `stats.py`
has `cohens_dz` and `weighted_cohens_dz`, and every `pooled` in the file refers to pooling a cluster's
rows.

The paired half is complete and symmetric, which is what makes the unpaired count derivable. Modifiers
are mutually exclusive (`E-DATA-WEIGHT-CLUSTER-CONTRAST`), so the space is
**{plain, weighted, clustered} × {*t*, percentile}** — six cells per pairing:

| Cell | Paired form, at `051600c` | Unpaired counterpart | Named by a document? |
|---|---|---|---|
| plain, *t* | `paired_t_over_units` | `welch_t_over_units` | **Yes** — a § Statistical reporting table row |
| plain, percentile | `paired_percentile_over_units` (a `method` string over `paired_percentile_of_derived`) | `unpaired_percentile_over_units` | **Yes** — a § Statistical reporting table row |
| weighted, *t* | `weighted_paired_t_over_units` | — | **No. Nowhere in the four documents** |
| weighted, percentile | `weighted_paired_percentile_over_units` | — | **No. Nowhere in the four documents** |
| clustered, *t* | `paired_t_over_units_clustered` | `welch_t_over_units_clustered` | **Only by the suffix rule** — no row, no spelling written down |
| clustered, percentile | `paired_percentile_over_units_clustered` | `unpaired_percentile_over_units_clustered` | **Only by the suffix rule** |

**So: six unpaired constructions, of which two are named, two are specified only by a rule, and two are
not named at all.** Every one is vapour — zero exist, zero are called from production.

Three findings from that table, each of which costs a task the charter does not have.

**The `_clustered` suffix rule specifies constructions that never existed, and it says so in the
present tense.** § Statistical reporting: *"each of the **unweighted** forms above takes a `_clustered`
suffix and reads the cluster as the draw: the *t* forms are cluster-robust (CR1) with df = clusters − 1,
**over the differenced values when paired and over the arm-level ones when not**, and the percentile
forms resample whole clusters — jointly across both sides when paired."* The "when not" clauses are
specification for the two unpaired clustered forms, written before either the paired or the unpaired
one existed. H4b-2 recorded the identical shape one axis over and built to the rule rather than
rewriting it; H4c does the same, and must not read the rule as licence to skip a construction because
a sentence already describes it. **This is a specification, not a defect** — an unbuilt reader of an
unbuilt surface — and the present tense is correct.

**The two weighted unpaired forms have no `method` string, and minting one is a document task that goes
first.** H4b-1's own record: *"The four documents gave a weighted contrast no `method` string at all, so
the vocabulary was minted in `reference.md` before any code emitted it."* The identical situation, one
pairing over, and the identical order applies. There are two coherent choices and H4c must pick one on
grounds: **mint** `weighted_welch_t_over_units` and `weighted_unpaired_percentile_over_units` as
§ Statistical reporting rows and build both; or **mint a third narrow refusal** on
`E-DATA-WEIGHT-CLUSTER-CONTRAST`'s precedent for `weight_by` beside a cross-arm comparison. The
measured input to that choice: the composition is reachable the instant the retirement lands (§ 1's
probe), it unblocks zero configs either way, and a Welch *t* on two weighted means needs Kish's
effective size **per side** — two df inputs, where the paired form needed one. Leaving this implicit is
what H4b-1 was faulted for; the decision belongs in the design with grounds, and the four documents
change before any code emits either string.

**`unpaired_percentile_over_units` is not `paired_percentile_of_derived` with a `method` argument.**
That function's whole construction is *one* draw applied to both sides, argued for at length in its
docstring: drawing each side independently "would resample the two conditions apart and destroy the
pairing." The unpaired form's definition — § Statistical reporting, *"resampling within each side
independently"* — is exactly the arrangement that docstring exists to refuse. So the three-`method`-
strings-one-function economy H4b-1 and H4b-2 built cannot be extended here: the percentile side is a
**new construction**, twice (plain and clustered), plus the weighted decision above.

---

## 3. What H4a, H4b-1 and H4b-2 changed underneath H4c

Each row says whether it makes H4c **smaller**, **larger**, or **differently shaped**.

| What changed | Direction | Measured |
|---|---|---|
| `Member` carries `weights` **and** `clusters` as mutually-exclusive modifiers on `diffs` | **LARGER, and the headline** | Both modifier checks raise when `diffs is None`, and `__post_init__` enforces `pool` XOR `diffs` whenever `ci95` is not `None`. A Welch interval's evidence is two per-side value vectors, so it is neither a pool nor differences: H4c adds a **third kind**, re-states the exactly-one rule as exactly-one-of-three, and re-argues both modifier checks against a vector that no longer has a `diffs` to be the same length as. `_corrected_bounds`' three-way branch (`clusters` → `weights` → plain) becomes six-way, since a corrected bound must be the same construction at a smaller α or it is a counterpart in name only |
| `correction.py` imports `paired_t_over_units`, `weighted_paired_t_over_units`, `paired_t_over_units_clustered` directly | **LARGER, and unnamed by any charter** | It is a **second production call site** for the contrast *t* family, so each of H4c's three unpaired *t* forms needs a caller there as well as in `cli.py`. `H4b-2-SCOPING` § 3 found the same thing for the clustered form and recorded that "the charter names `correction.py` nowhere" — still true of H4c's row |
| `paired_percentile_of_derived` takes `strata` **and** `clusters`, one `method` string per declaration, and returns a sorted pool | **Differently shaped, and smaller in one place only** | The `strata` × `clusters` composition rule, the relabelling invariance, and the degenerate-draw refusal are all solved and can be **copied** into the two unpaired percentile constructions. What cannot be copied is the draw itself (§ 2). Net: the hard reasoning is done, the code is not |
| `paired_t_over_units_clustered` exists | **Smaller** | `welch_t_over_units_clustered` can follow it into `t_over_units_clustered`'s CR1 machinery rather than deriving a cluster-robust variance from scratch. The one genuinely new part is that df = clusters − 1 must be computed **per side and combined**, where the paired form has one cluster set |
| `E-DATA-WEIGHT-CLUSTER-CONTRAST` refuses weight × cluster | **Neither larger nor smaller — and the charter's arithmetic was wrong about why** | Probed on an *unpaired* comparison: it fires (§ 1). So H4c does not build a weighted clustered unpaired form. But this removes **zero** cells from § 2's six, because weight and cluster were already mutually exclusive there; the refusal is what makes the space 3 × 2 instead of 4 × 2. The charter's "their clustered and weighted counterparts" reads as two extra forms beside two; measured, it is **four** extra forms beside two |
| `_comparison_step_blocks` has a six-cell `method` branch across two sites, plus a clusters-guarded suppression on the derived branch | **LARGER** | The six cells are `{clustered, weighted, plain} × {resample, t}` and every one asserts a *paired* construction. Deriving `paired` doubles that to twelve across the same two sites. The clusters-guarded suppression needs its unpaired analogue asked about explicitly: the derived-key-collision corner it closes was given **four wrong grounds in four commits**, every one an answer from a proxy, and the only thing that ever exposed it was an end-to-end `run` |
| `paired_keys` is the intersection, sorted | **Differently shaped** | It is the wrong function for an unpaired contrast and the charter says so ("`paired_keys` no longer applies"). What the charter does not say: `n_paired`, `n_paired_effective` and `n_paired_clusters` are **all three** computed from `base_keys`/`col_keys` in `_comparison_step_blocks`, so the key path and the record shape are one task's two halves, not two tasks (§ 4) |
| H4a wired `resample_columns`, so a declared `resample` routes every column contrast through the percentile branch | **LARGER, and it decides which construction matters** | H4b-1's lesson verbatim: all three C configs declare `resample`, so the *t* form its charter named was never the payoff path. For H4c the same check must be run before ordering the constructions — and unlike H4b-1 there is no config to run it against (§ 5), which means the ordering argument has to come from the documents instead |

---

## 4. Two things nothing between the code and the documents can currently produce

### The only documented unpaired record is in a block core permanently refuses

`reference.md` § Allocation, immediately after the pairing table, shows the one unpaired record in the
four documents:

```yaml
vs_baseline:                                   # 03_arm=treatment__method=spearman
  step03_analyze:
    r: {delta: 0.041, basis: units, paired: false, confounded: true,
        method: unpaired_percentile_over_units,
        differs_on: [arm, analysis.method],
        ci95: [0.012, 0.070]}
```

A `vs_baseline` entry crossing a group axis requires a baseline that **fixes a group level**, which is
the only way the expansion produces one baseline row for two arms to be compared against. Probed, both
branches, exact error sets:

| Shape | Exact error set at `051600c` |
|---|---|
| `groups` axis + `grid` + baseline fixing `arm: control` | `{E-DATA-ALLOCATION-CONTRAST, E-DATA-ALLOCATION-WITHIN-ARMS, E-SWEEP-BASELINE-GROUP}` |
| `groups` axis + `grid` + baseline fixing `analysis.method` only | `{E-DATA-ALLOCATION-WITHIN-ARMS}` — **no cross-arm comparison exists at all** |

The second row is the load-bearing one and it is not obvious: a parameter-only baseline **expands over
the group axis**, giving each arm its own reference, so every generated comparison is within-arm and
`E-DATA-ALLOCATION-CONTRAST` never reads a cross-arm pair. The first row is the only generated route to
one, and it also earns `E-SWEEP-BASELINE-GROUP` — a refusal H4c does not lift, grounded in
§ Expansion modes' *the arms of a group axis are peers* and in `experimental-designs.md` § Mistakes core
prevents' *two identical measurements reported as two arms*, which is a structural impossibility rather
than a temporary gap.

**So after H4c, `vs_baseline` still never carries an unpaired entry, and the whole reachable surface is
a declared `statistics.contrasts` entry.** The § Errors row already states this correctly — *"a
`vs_baseline` comparison ... crosses a group axis only where the baseline fixes a group level, which
`E-SWEEP-BASELINE-GROUP` ... refuse outright — that route still reports here, always beside one of
them"* — so the row is right and **the § Allocation example contradicts it**, showing a `vs_baseline`
unpaired entry that no config can produce. The surrounding prose compounds it twice: *"Each contrast
records its own `paired: true|false` in `vs_baseline`"*, and *"Fixing a value on every axis is the other
coherent choice, and it's the one that produces contrasts like the above."*

**This is a repair, not a decision, and the measurement is what closes the second branch.** The only
other reading would be to lift `E-SWEEP-BASELINE-GROUP`, which refuses a *declaration* on the peers rule
and routes to `experimental-designs.md` § Mistakes core prevents' *two identical measurements reported as
two arms* — structurally impossible by design, not a temporary gap, and a change to it is an argument
against `design-principles.md` rather than a slice's work. So the example moves to a `results.contrasts`
entry, which is where the record can actually appear. It is the sharpest instance of the class
`CLAUDE.md` warns about — an example read as a definition — because the example is *also* the only place
the unpaired record's shape is written down.

**The repair is three sites, not one**, and the enumeration matters because a sweep that stops at the
fenced block is the "sweep for the claim, not the file the claim was first noticed in" failure:

| Site | What goes stale |
|---|---|
| § Allocation, the fenced `vs_baseline:` example | The block itself, including its `# 03_arm=treatment__method=spearman` comment, which is what makes it a `vs_baseline` record |
| § Allocation, the paragraph above it | *"Each contrast records its own `paired: true\|false` in `vs_baseline`"* — true of the boolean, false of the block that can hold `false` |
| § Allocation, the paragraph below it | *"Fixing a value on every axis is the other coherent choice, and it's the one that produces contrasts like the above"* — it produces `E-SWEEP-BASELINE-GROUP`, measured above |

### `n_paired` is a definition that does not apply, not a key with a gap beside it

§ Contrasts: *"**`n_paired` is the intersection, and it has to be recorded.**"* Both scalar siblings rest
on that: `n_paired_effective` is "a fact about the intersection `n_paired` counts", and
`n_paired_clusters` is "the number of distinct clusters the paired intersection falls in ... on the same
argument `n_paired_effective` rests on". An unpaired contrast's intersection is **empty by
construction** — that is what "disjoint arms" means, and it is the reason `E-DATA-ALLOCATION-CONTRAST`'s
own message gives for refusing. So:

- `n_paired: 0` is arithmetically true and descriptively false, and it is what today's code would
  write, since `n_paired = len(col_keys)` unconditionally.
- No per-side count key exists in any document. The unpaired *t* needs two, because Welch's df is
  computed from both sides' sizes and variances.
- `n_paired_effective` and `n_paired_clusters` inherit the problem: Kish's size and the cluster count
  are both **per side** for an unpaired contrast, and both are documented as scalars.
- `W-STATS-CONTRAST-THIN` and `limits.min_reported_n` key on `n_paired` — § Validation's row is *"the
  comparison's realized `n_paired` is below it"* — so the disclosure warning has nothing to read on an
  unpaired contrast unless the record shape says what it reads instead.

H4b-1's precedent is the route: it minted `n_paired_effective` as a documented scalar sibling before any
code wrote it. H4c mints whatever replaces `n_paired` here the same way — in `reference.md` § Contrasts
first, then in code — and it is one design task with four keys and a warning hanging off it, not the
charter's single row.

---

## 5. The payoff, dated and pinned

### Measured on 2026-08-18 against commit `051600c`

**No config in `docs/feasibility-llm-growth-studies.md` needs an unpaired contrast, and none is
unblocked by H4c.** Both counts stay exactly where H4b-1 and H4b-2 left them: **six with no remaining
core-side blocker, three executable.**

Measured directly on the nine configs' own declarations rather than derived from a claim in the
analysis's prose:

| Sweep | Result |
|---|---|
| `grep -n 'allocation:' docs/feasibility-llm-growth-studies.md` | Two config-block hits, both `allocation: within` — the shared roster block E1–E6 share, and the shared block C1–C3 share. Two further hits are prose |
| `grep -n 'groups:' …` | Two hits, both `groups: []` |
| `grep -c 'allocation: within' …` — the positive control | **3** (two blocks plus one prose sentence) |
| `grep -c 'allocation: between' …` — the negative arm | **1**, and reading it shows a prose sentence listing `allocation: between` among fields *no config declares* |

The control is what makes this a measurement: the same sweep shape returns a different answer for a
string that is present, and the one `between` hit was **read** rather than counted, which is how a
prose mention would otherwise have inverted the finding. An unpaired contrast requires a declared
`sweep.groups` axis (§ 1's probes); no config declares one; therefore none reaches
`E-DATA-ALLOCATION-CONTRAST` at all. This confirms `H4-SCOPING` § 6's "unpaired contrasts unblock **0**"
at a commit three slices later.

**A retired-refusal count is not an executable-run count**, and the two must not be conflated: both
review verdicts on H4b-1 faulted that conflation, and a *correction* on H4b-2 inverted the same two
numbers. H4c retires one refusal that **zero of nine** configs hit — a weaker position than H4b-2's,
which at least retired a refusal that zero configs hit while closing a live defect for every config.

**What H4c is worth instead**, stated so it is not mistaken for nothing:

- It is the **gate five `spec-defects.md` filings are queued behind**, four of them re-ownered to H4c
  by name on 2026-08-18 (§ 6). A filing whose owner never runs is the shape `CLAUDE.md` calls "a ledger
  line saying filed is not a filing".
- It closes the repo's largest standing **specification-versus-code** gap in the statistics family: six
  named-or-implied constructions with nothing behind them, one `method` vocabulary that does not exist,
  and one documented record shape that is unreachable (§ 4). Five § Validation rows once described
  checks with no emit site; this is the same class at construction scale.
- It removes the last hard-coded claim in the contrast record. `paired: true` is true today *because*
  `validate` refuses everything else — a true claim resting on a guard, which is exactly the kind that
  goes silently false.
- It is the only slice that makes `groups × grid` — "each arm analyzed three ways", a design
  `reference.md` walks through twice — analyzable end to end rather than half-refused.

That is a specification-integrity payoff, not an execution payoff, and it should be argued as one. The
measured consequence, and the whole of it: **nothing in the feasibility analysis gets closer to running
because H4c landed.**

---

## 6. The two pins H4c must satisfy, and the filings it inherits

H4b-2's task 5 pinned its own sufficiency argument **two ways on purpose**, because the obvious pin —
"fail if `paired` is ever `False`" — is a mutation whose two branches cannot differ: `paired` is a
literal, so there is no runtime state to assert against. Both pins were located by reading
`spec-defects.md`'s "RULED by H4b-2 task 5" entry and then grepped in `tests/`.

| Pin | What it asserts | What H4c must do to it |
|---|---|---|
| `tests/test_cli.py::test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch` | `inspect.getsource(_comparison_step_blocks)` contains `'"paired": True'` exactly **2** times **and** `'"paired":'` exactly **2** times. Both counts, deliberately: the first alone passes under a third branch writing `"paired": is_paired`, the second alone under two sites that both became conditional | **Replace, not delete.** It fails on both assertions the moment either site becomes conditional, which is precisely the change H4c makes. Its replacement is the behavioural pin it could not be: a real declared cross-arm contrast recording `paired: false` beside a `welch_*`/`unpaired_*` `method`, **and** a within-arm comparison in the same run still recording `true`. Its own docstring records the scope gap to carry forward — it reads one function's source text, so it is defeated by extracting either write into a helper |
| `tests/test_validate.py::test_a_contrast_beside_groups_and_cluster_by_draws_the_allocation_refusal` | The **exact set** `_error_codes(...) == {"E-DATA-ALLOCATION-CONTRAST"}` for a declared cross-arm contrast beside `cluster_by` | **Convert, not delete.** Retiring the code makes the set `{}`, so the assertion fails — and that failure is the tripwire working: this fixture is a *clustered* cross-arm contrast, so the conversion is only honest once `welch_t_over_units_clustered` and `unpaired_percentile_over_units_clustered` exist. It becomes the clean-composition control beside `test_groups_and_cluster_by_compose_with_no_comparison`, and the run-side assertion that the entry's `method` carries `_clustered` |

Deleting either pin is the one move H4c may not make: they exist to force the clustered unpaired
constructions into the same slice as the retirement, which is H4b-2's decision 2 read forward.

**Five filings, four of them re-ownered to H4c by name on 2026-08-18.** Each must be claimed or
re-declined **in writing**, because a silent inherit is how an entry comes to read as live work nobody
holds:

| Filing | Why it is H4c's | Measured status |
|---|---|---|
| `paired_percentile_of_derived`'s sorted-pool precondition unasserted | Re-ownered 2026-08-18: "H4c is now the nearer of the remaining paired-construction slices" | **Live, and H4c makes it worse before better**: `interval_at` reads fixed ranks off an unsorted pool silently, and H4c writes two new percentile constructions that must each return a sorted pool. Claim it — the cost is one assertion at one seam H4c is opening anyway |
| *A column resample is only ever defined given finite inputs* | Re-owned to H4c as "the next slice past this one to touch `summarize_step`'s column path" | **Check the premise before accepting it.** The identical prediction was made of H4b-2 and **did not come true** — that is recorded in the entry itself. H4c's unpaired *t* forms **do** sum per-side value columns and compute per-side variances, so the premise is likelier here than it was there; verify rather than inherit |
| *The contrast path discloses nothing about its resample* — Findings 1 and 3 | Re-ownered 2026-08-18, declined by H4b-2 in writing | Finding 1 needs a contrast-scope `where` and a warning registry row; Finding 3 needs a resolved-`resample` echo on the contrast entry. H4c adds **six** `method` spellings to the contrast entry and a new record shape (§ 4), which is more new disclosure surface than H4b-2 added, so the "no new surface" ground H4b-2 declined on does not transfer |
| `W-STATS-REPORTBY-THIN`'s whole-roster-versus-arm gap, and the `report_by` level's `resample_columns` asymmetry | Declined by H4a with a measured 3–5 task cost, re-declined by H4b-2, re-owned to H4c by name | **Live on C1–C3**, created by neither weights, clusters nor pairing. It has now been declined by three consecutive slices. H4c is the last slice whose charter names it, and it is the **only one of the five that is genuinely unrelated to unpaired constructions** — a fourth decline needs a named owner that is not a description, or it becomes work nobody holds |
| `E-DATA-CLUSTER-DERIVED` — the clustered derived draw | Re-owned by H4b-2 task 4 "on the construction-family argument": it is a per-condition percentile draw over clusters for a recomputed metric, "the same family as the unpaired clustered percentile form H4c already owns" | **Live.** The family argument is sound and H4c is building the neighbouring construction. Its § Errors row's justification — *"Temporary, alongside `E-DATA-CLUSTER-CONTRAST`"* — was repaired by H4b-2 task 15, so re-read the entry rather than trusting this row |

---

## 7. Decomposition: 22 tasks, against the charter's 12

The charter's H4c row reads: *"`welch_t_over_units`, `unpaired_percentile_over_units`, their clustered
and weighted counterparts; `paired` derived in `cli._entry_for`; `cohens_d` *d*s/*d*z branch; the
unpaired point-estimate path (`paired_keys` no longer applies); the `n_paired` spec gap — 12."*

| # | Task | Depends on |
|---|---|---|
| 1 | The weighted-unpaired vocabulary decision (§ 2): mint two `method` strings in `reference.md` § Statistical reporting, or mint a third narrow refusal, **with grounds** | — |
| 2 | The unpaired record-shape decision (§ 4): what replaces `n_paired`, the two per-side counts, `n_paired_effective`/`n_paired_clusters` per side, documented in § Contrasts before any code writes a key | — |
| 3 | § Allocation's unreachable `vs_baseline` example re-authored as a `results.contrasts` entry, with the two prose sentences that derive from it (§ 4's three-site table) | — |
| 4 | `welch_t_over_units` | 2 |
| 5 | `cohens_ds`, and its weighted counterpart if task 1 mints one | 1 |
| 6 | `unpaired_percentile_over_units` — a new draw, independent per side | 2 |
| 7 | `welch_t_over_units_clustered` — df from each side's own cluster count | 4 |
| 8 | `unpaired_percentile_over_units_clustered` | 6 |
| 9 | `weighted_welch_t_over_units`, or the refusal task 1 chose instead | 1, 4 |
| 10 | `weighted_unpaired_percentile_over_units`, or the same refusal | 1, 6 |
| 11 | The unpaired key path: `paired_keys`' unpaired counterpart, per-side completed sets narrowed by `within`, and the point estimate as a difference of two side means | 2 |
| 12 | `Member`'s third evidence kind, and `__post_init__` re-argued (§ 3) | 4, 6 |
| 13 | `_corrected_bounds` gains an unpaired arm per unpaired *t* form built, and `family_members` widens with it — **one arm per construction task 1 licenses**, three if it mints the weighted pair and two if it mints the refusal, beside today's three paired arms | 12, 7, 9 |
| 14 | `paired` derived at **both** `_comparison_step_blocks` branches, from `differing_axes ∩ selectors` — the same test the refusal runs | 11 |
| 15 | The `method` selection: six cells → twelve, at both sites | 14, and every construction |
| 16 | The derived-metric unpaired case, and the clusters-guarded suppression's unpaired analogue asked about explicitly — **verified by an end-to-end `run`, never a direct call** | 15 |
| 17 | `W-STATS-CONTRAST-THIN` and `limits.min_reported_n` under an unpaired contrast | 2, 14 |
| 18 | The two pins replaced and converted (§ 6) | 14 for the first, 19 for the second |
| 19 | **Retire `E-DATA-ALLOCATION-CONTRAST`**: the guard, its § Errors row, its § Validation row | every construction, 14, 15 |
| 20 | The citation sweep (§ 1's 14 sites), including `E-SWEEP-BASELINE-GROUP`'s emitted message, and `feasibility-*` **re-dated rather than edited** | 19 |
| 21 | The five inherited filings claimed or re-declined in writing (§ 6), and § Executability on this build re-dated with the unmoved counts | 19 |
| 22 | Whole-branch review, and the mechanical plus cross-document consistency passes | all |

**Direction against the charter: up, 12 → 22.** Where it moved, and why each is real rather than
padding: the construction count is **6, not 4** (§ 2 — "their clustered and weighted counterparts"
reads as two beside two); `Member` and `_corrected_bounds` are **two tasks the charter names nowhere**
(§ 3); the two document-first decisions (tasks 1 and 2) are H4b-1's own precedent and neither is in the
charter; § Allocation's unreachable example (task 3) was found here; and the pins (task 18) did not
exist when the charter was written.

**The ordering constraints, each with its reason:**

- **Every construction before the retirement** (19 after 4–10). This is H4b-2's decision 2 read
  forward and its cost is measured, not hypothetical: retiring the guard while a construction is
  missing routes a declared cross-arm comparison to a *paired* construction over an empty intersection,
  publishing `delta: null, paired: true, n_paired: 0` with `validate` reporting zero errors. H4b-2 hit
  the same class one axis over and only an end-to-end `run` found it.
- **All three unpaired shapes' constructions in the same slice as the retirement** (§ 1's probe). There
  is no "build the pair, refuse the composition" option: plain, weighted and clustered all become
  reachable at one stroke, so partial delivery is silent mis-attribution rather than a smaller slice.
- **Documents before code for tasks 1, 2 and 3.** A `method` string or a record key emitted before the
  four documents name it is the defect H4b-1 avoided deliberately, and `CLAUDE.md`'s rule is that the
  document changes first.
- **Task 12 before task 13 and before task 15.** `_comparison_step_blocks` builds the `Member`s, so a
  `Member` that cannot represent an unpaired interval makes the dispatch untestable end to end.
- **Task 18's second pin with task 19, in one commit.** It asserts an exact code set that the
  retirement empties; splitting them leaves the branch red for a reason unrelated to either change.
- **Task 16 by `run`, never by direct call.** Every direct-call probe of the derived-key corner
  hand-built the maps and so never reached the bug; that corner was given four wrong grounds in four
  commits, each an answer from a proxy.

---

## 8. What the charters name that no longer exists, and what is real that they never named

Both have been found on every re-scope in this repo, and both are here.

| The charter says | Measured at `051600c` |
|---|---|
| "`paired` derived in **`cli._entry_for`**" | **Wrong function.** `_entry_for` maps a corrected field onto whichever record shape holds it and never touches `paired`. Both literals are in `_comparison_step_blocks`. Good news for scope: `conditions_by_index` and `differing_axes` are already parameters and imports of that function, so the derivation is local — a few lines, not a threading task |
| "their clustered and **weighted** counterparts" | Reads as two forms beside two; measured, **four beside two**, and two of the four have no `method` string in any document (§ 2) |
| "the `n_paired` spec gap" | Not one key's gap: a definition that does not apply, two missing per-side counts, two scalar siblings inheriting the problem, and a warning keyed on it (§ 4) |
| `H4-SCOPING` § 6: "the cluster half can ride with H4c, which is the same construction work one level over" | Already answered against by `H4b-SCOPING` § 5 and by events — H4b-2 built the paired clustered pair. What survives is the *unpaired* clustered pair, and it is H4c's whether or not anything rides with it |
| The spine design: "H4c unpaired (12)" | 22 (§ 7) |

| Real, and named by no charter | Where |
|---|---|
| `Member`'s evidence model has no unpaired shape, and `correction.py` is a second production call site | § 0.1, § 3 |
| § Allocation's only unpaired record example is in a permanently-refused config shape | § 0.4, § 4 |
| A parameter-only baseline beside a `groups` axis produces **no cross-arm comparison at all** — so `vs_baseline` is not H4c's surface; a declared contrast is | § 4 |
| The weighted unpaired `method` vocabulary does not exist in the four documents | § 0.3, § 2 |
| `E-SWEEP-BASELINE-GROUP`'s **emitted message** promises the delta "until the unpaired estimators exist" — a temporary clause inside a permanent refusal | § 1, task 20 |
| `cohens_ds` does not exist in `stats.py` at any spelling; only `cohens_dz` and `weighted_cohens_dz` | § 2 |
| `unpaired_percentile_over_units` cannot reuse `paired_percentile_of_derived` — its definition is the arrangement that function's docstring exists to refuse | § 2 |
| `E-DATA-WEIGHT-CLUSTER-CONTRAST` fires on an *unpaired* comparison too, so the inherited composition is a standing refusal rather than work — and it removes zero cells from the six | § 1, § 3 |
