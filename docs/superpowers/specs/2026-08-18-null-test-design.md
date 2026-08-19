# H4d — `statistics.null_test`, the p-value, and `fdr_bh` — design

**Goal:** a config declaring `statistics.null_test` stops being refused. Core builds a permutation
null by relabelling the unit table, records a `p_value` against the value the run actually produced,
adjusts it where the correction method implies an adjustment, and — for the first time — makes
`statistics.correction: fdr_bh` mean something. Five distinct faults inside the block, all of which
validate clean the instant the wholesale refusal lifts, get their own checks first.

**What it delivers, stated honestly. H4d unblocks ZERO configs.** All eight `statistics` blocks in
`docs/feasibility-llm-growth-studies.md` carry `null_test: null`, which the truthy guard treats as
undeclared, and **zero configs declare `fdr_bh`** — so the one warning H4d narrows fires for none of
them either. **The no-remaining-core-side-blocker count stays six and the executable count stays
three.** Neither moves. A retired-refusal count is not an executable-run count, and this slice
retires a refusal that **zero of nine** configs hit. What it is worth instead is in § The payoff, and
it is not nothing: it is the last `NOT BUILT` declaration in the `statistics` family, the largest
specification-versus-code gap left in the repo, five refusals decomposed out of one, and two
documented record shapes made producible.

**What it is not.** Not `io.reuse_from` — unbuilt and unowned. Not the apparatus probe — H7d. Not
folds or holdouts inside cells — H3c-3. Not an interaction, a dose-response ordering, or a
difference-in-differences: contrasts do not nest, and that refusal is permanent.

---

## The measurement this rests on

[`docs/superpowers/H4d-SCOPING.md`](../H4d-SCOPING.md), taken 2026-08-18 against `main` at
`2a4dc53`, **plus its appended § 9 amendment at the same commit**. Verdict there: **27 tasks against
the charter's 13**. Baseline recorded there: `uv run pytest` → **2275 passed, 1 skipped, 2 xfailed**,
142.85 s, foreground.

**Two commit pins, deliberately not blurred into one.** Everything inherited from the scoping — the
nine-shape probe of what the refusal hides, the `vs_baseline` re-probe, the `null_test: null` sweep
with its positive control, the `p_value`-appears-once-in-`src/` sweep — is pinned to **`2a4dc53`**.
Everything verified while writing this document is pinned to **`bb8a56f`**, and it is this:
`E-STATS-NULLTEST-METHOD`, `E-STATS-NULLTEST-N`, `E-STATS-NULLTEST-SHUFFLE`,
`E-STATS-NULLTEST-UNITS`, `E-STATS-NULLTEST-LEVEL`, `E-STATS-NULLTEST-REPORTBY`,
`W-STATS-NULLTEST-FAMILY`, `W-STATS-NULLTEST-DEGENERATE`, `min_honest_permutations`, `null_draws` and
`permutation_over_units` are **all free identifiers** across `src/`, `tests/` and the four documents
(can-fail control on the same file list: `E-STATS-RESAMPLE-N` → 24 hits, `p_value_corrected` → 8, of
which 4 are in `tests/` asserting its *absence* and 4 are the `reference.md` passages below). The
file **list** was filtered; no sweep's output was. **No production code ships from this document.**

**Every build claim in the decisions below is one of those two measurements.** Where a decision says
what the code does *today* — `_level_for` returning `None` for `fdr_bh`, `corrected_for`'s single
pass, `family_members`' `ci95`-gated comprehension, `_evidence_ratio`'s `0.0` for a zero `delta`, the
truthy guard on `null_test` — it is **`2a4dc53`** unless it names `bb8a56f`, and it is perishable in
the way `CLAUDE.md` says a build fact is.

---

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | `fdr_bh`'s ordering — build it, or refuse it | **Build it. BH ranks on the ascending p-value, and that creates no second ordering, because under `fdr_bh` the evidence ratio orders nothing** | § Statistical reporting's foreclosure is *"Ranking on a p-value where one exists and on this ratio elsewhere would leave the family ordered by two statistics, which is not an ordering"* — a statement about **one procedure using two statistics at once**. Under `fdr_bh` the shipped table already makes `ci95_corrected` **`null` for every member**, and `_level_for` returns `None`, so no interval is ever built at a rank: the evidence ratio decides **nothing** in an `fdr_bh` run. One method, one ordering; the other methods keep the evidence ratio and never see a p-rank. The alternative — refusing `fdr_bh` beside `null_test` — is the honest form of *deleting `fdr_bh` from the enum*, since `fdr_bh` would then be accepted only where it does nothing and refused wherever it could act: a value § The one config file enumerates, a generated comment offers, `E-STATS-CORRECTION-UNKNOWN` admits and `experimental-designs.md` § Mistakes core prevents cites, de-specified across four documents to avoid one ranking decision the documents leave open rather than closed. **The third reading in the scoping — BH over the p-carrying subset while intervals rank over the whole family — is what this ruling *is*,** with one clause pinning it down: **m stays the whole family** (§ Statistical reporting: *"The family is the same set under every method, including `fdr_bh`"*), and *i* runs 1..k over the members that carry a p-value, ascending. Larger m is the conservative direction, which is the direction this section is held to everywhere else |
| 2 | Holm's and Bonferroni's `p_value_corrected`, and what it is not | **`p_value_corrected = min(1, p × α/level)` — Holm at the member's own evidence rank, Bonferroni at α/m — named in the document as *the p-value expressed at the level this member's interval was corrected at*, with monotonicity explicitly disclaimed** | § The unit table is the inference base already fixes it: *"corrected alongside the intervals when the method supplies one, at the same level the interval was computed at."* Holm's level is α/(m − i + 1) at the evidence rank, so the p at that level is p × (m − i + 1). **This is not Holm's step-down adjusted p-value and the document must say so**, because a reader who knows Holm will read it as one: there is no prefix `max`, and the adjusted values can order differently from the raw ones — on § The discriminating fixtures' family, member Y's adjusted 0.88 sits above member Z's 0.93 while Y's raw p is *smaller*. **That inversion is expected, not a defect**: it is the evidence ranking showing through, and a later slice "fixing" it by ranking Holm on p reintroduces exactly the two-orderings problem decision 1 avoids. **Consequence worth carrying: only BH's adjustment is an accumulation.** The scoping predicted `corrected_for` needed both Holm's prefix `max` and BH's suffix `min`; measured against the documented level, **the prefix `max` is not owed at all**, and the two-pass rewrite exists for BH alone |
| 3 | The Bonferroni cell of the `correction` table, which says `—` | **Amend the table: Bonferroni also reports `p_value_corrected`, at `min(1, p × m)`** | Two readings of *"when the method supplies one"* in § The unit table is the inference base, and the choice is the whole decision: (a) *the method supplies a **level*** — bonferroni and holm do, `none` and `fdr_bh` do not in that sense; (b) *the method supplies a **p-value***, which no correction method does, the `null_test` does. Reading (b) makes the sentence say nothing method-dependent at all and cannot be why `none` is excluded, so (a) is the reading. Under (a) the table's `—` in the Bonferroni row **contradicts the sentence** — a metric whose interval was corrected at α/m, whose p-value is in hand, reports the p at that level under Holm and not under Bonferroni, for no stated reason. A dash with no ground is a gap, not a decision. **Ruled here rather than left**, because the alternative is code that emits a key under one method and withholds it under a neighbouring one, which is the asymmetry a reader files as a bug |
| 4 | `Member`'s shape for a p-value | **A field, `Member.p_value: float \| None` — not a fourth evidence kind — and `family_members` widens to `ci95 is not None or p_value is not None`** | The three evidence kinds exist because `_corrected_bounds` rebuilds the **same construction** at a smaller α; a p-value has no construction to rebuild, only a rank and a family size, both already inside `corrected_for`. So `__post_init__`'s exactly-one-of-three is untouched and `_corrected_bounds` gains no seventh return path — **stated as a decision rather than left as an omission**. The widening is the scoping's § 9 amendment and it is load-bearing: `family_members` drops every member with `ci95 is None`, and `cli` builds exactly that member for a thin pool, a too-short draw or a degenerate column — while a permutation p-value needs only the observed statistic and the null, both of which exist in that state. Unwidened, **BH would silently adjust nothing for precisely the member its p-value was the only thing it had.** § Statistical reporting's exclusion argument — *"a metric reported without an interval isn't a comparison anyone can read as significant"* — is about **intervals** and does not transfer, so the sentence is narrowed to the intervals it is true of rather than extended by silence. Two mechanical consequences, both of which a widening that only edits the comprehension gets wrong: **`_evidence_ratio`'s `assert member.ci95 is not None` becomes reachable** — a crash, and a mutation caught by a crash is not a pin — and **`rank_family` needs a tuple key `(has_interval, -ratio, declaration_index)`, never a sentinel ratio**, because `_evidence_ratio` already returns exactly `0.0` for a member whose `delta` is 0 with a finite width, so a p-only member handed `0.0` sorts *among* those rather than after them. With the tuple key, every interval-carrying member keeps the rank it has today and **no existing corrected bound moves** — which is the property task 27's pin asserts |
| 5 | Where a per-condition p-value lands, and in which family | **On the `aggregated` metric block, as `p_value`, **uncorrected** — and § What isn't a repeat's `aggregated:` example loses its `p_value_corrected`** | The decisive argument is inside the example itself: it shows `p_value_corrected: 0.0028` beside a `ci95` that carries **no `ci95_corrected`**, because a per-condition estimate is not a comparison and `cli` builds no `Member` for one. A record cannot correct one description of a metric and not the other. The family is comparisons × metrics; a per-condition estimate joins neither factor, and the two standing precedents both point the same way — a `statistics.report_by` level *"repeats metrics over strata without adding executions or joining the correction family"*, and a reported `Estimate` is excluded because core has no standing over it. **The other two readings, rejected with reasons**: a third family with its own `where` prefix is coherent (`hypotheses.py` is the precedent) but invents a family no document names, for a shape zero configs declare; folding per-condition estimates into the comparison family directly contradicts *"The family is comparisons × metrics"* and inflates every existing corrected interval in every run that declares `null_test`. **The example's `0.0004 → 0.0028` is deleted, not re-derived** — ×7 is Bonferroni at m = 7 or Holm at m − i + 1 = 7, neither derivable from any family the section describes, and re-authoring it would mint a number to match a ruling that says there is none |
| 6 | Where a group-axis p-value lands | **On a declared `statistics.contrasts` entry — never in `vs_baseline`** — and § What isn't a repeat's landing-site table is repaired to say so | This is H4c's finding one section over, left unrepaired here, and it is a repair rather than a decision. Re-probed at `2a4dc53`: a baseline fixing a group level earns `E-SWEEP-BASELINE-GROUP`, which is **permanent** — it rests on § Expansion modes' *the arms of a group axis are peers* — and a parameter-only baseline **expands over the group axis**, so every generated comparison is within-arm and no cross-arm pair is ever read. H4c repaired § Allocation for exactly this and its sweep stopped one section short of the sibling sentence saying the same thing about a different field. **This is the only p-value home that joins the correction family**, which makes it the home decisions 1, 3 and 4 are all about |
| 7 | What a permutation null can move, and the `report_by` hole in that claim | **A per-condition *recorded column* gets no null at all — the recompute is a function of the column alone and no relabelling can move it — and the one case where an attribute *does* enter a column metric's computation, a `statistics.report_by` level, is refused: `E-STATS-NULLTEST-REPORTBY`** | Named by neither the charter nor the scoping, and it collapses two of the scoping's eight cells. A per-condition column metric is `mean(column)` over the condition's units; permuting **any** attribute leaves it bit-identical, so the null distribution is the observed value repeated `n` times and `p_value` is exactly 1.0 — a number that reads as a finding and is an artifact of asking. § What isn't a repeat's own `aggregated:` example is a recorded column with `method: t_over_units` carrying `p_value: 0.0004`, which is **unproducible for this reason and not only for decision 5's**, so task 2 re-authors it as a derived metric. **The qualification that makes the sentence true**: under `statistics.report_by`, units move *between strata* when `shuffle` names the stratifying attribute, so a per-stratum column mean does change — and permuting it changes **which units the stratum contains**, so the null is of a different partition rather than of the same estimate. That is the same incoherence `experimental-designs.md` § Mistakes core prevents names as *a permutation that shuffles away the matching*, and it earns a **documented, permanent narrow refusal** on the `E-DATA-WEIGHT-CLUSTER-CONTRAST` family shape — a § Errors row and a § Validation row, not a `-UNSUPPORTED` build-family code, and **no slice inherits it as work**. The residual case core cannot predict — a template's `aggregate` that simply ignores the shuffled attribute — is caught at run time by the **invariance rule** in decision 8 |
| 8 | An invariant null | **`p_value: null`, and no new warning code** | `stats.percentile_over_units_clustered`'s *"The degenerate case is content, not count"* is the shipped precedent: a draw whose every replicate reproduces the same value returns `None` rather than a zero-width interval. A null whose every draw equals the observed statistic is the same fact one construction over, and it returns `None` for the same reason — a p-value of 1.0 computed from a distribution that could not have been anything else is a number with no construction behind it. **A `W-STATS-NULLTEST-DEGENERATE` was considered and deliberately not minted**: the record already carries the resolved `null_test` echo beside the `null` p-value, which says the test ran and produced nothing, exactly as `ci95: null` beside a `resample` echo does — and `CLAUDE.md` prefers reusing a shape to adding a registry row nobody owns |
| 9 | The `method` enum and the draw floor | **A closed one-row `method` table (`permutation`), and `min_honest_permutations(level) = ceil(1/level) − 1` → `n ≥ 20` at α = 0.05, refused below; `W-STATS-NULLTEST-FAMILY` warns against the family's tightest level** | § Statistical reporting's *Resample methods* gives `resample.method` a closed table *"so adding a second is a documented change rather than a silent one"*; `null_test.method` has no counterpart and gets one on that precedent. **The floor is a different quantity from `min_honest_draws` and inheriting 80 unexamined is the available shortcut and the wrong one**: `min_honest_draws` is about a percentile interval's two ranks being interior, while a permutation p-value's resolution is `1/(n + 1)` — the smallest value it can take. The floor is the smallest `n` at which the p-value can fall **strictly below** the level being tested: `1/(n + 1) < level` ⇒ `n > 1/level − 1` ⇒ **`n ≥ 20` at α = 0.05**. The inequality and the integer are stated together here so they cannot drift. Derived from `level` rather than written as a literal, the way `min_honest_draws` is derived from `confidence`. And because a corrected member is tested at α/m rather than α, **`W-STATS-NULLTEST-FAMILY` mirrors the shipped `W-STATS-RESAMPLE-FAMILY`** — the same family lower bound on the same declared `n`, at `20 × m` |
| 10 | One slice or two | **One slice, 29 tasks** | Re-argued rather than inherited. The house precedent cuts both ways — H4b split at 22, H4c did not at 22, H7b split at 29 — so the count is not the discriminator; **whether a half-built slice leaves a config that validates clean and does something other than what it says** is. Engine-without-`fdr_bh` fails that test and the scoping's wording is exact: the config would produce `p_value` on its entries, `ci95_corrected: null`, **no `p_value_corrected`**, and a warning whose message asserts no comparison *can* carry a p-value — false by then. The boundary cannot be spoken, so it cannot be drawn. The per-condition-without-group-axis seam **is** speakable as a narrow refusal, and it is rejected on payoff rather than on coherence: it is zero-payoff behind zero-payoff, the correction plumbing is shared and unsplittable, and the first half would ship constructions with no production caller — the state the spine design already flags as a hazard. **A third seam this spec creates and also rejects**: decisions 1–3 are document edits that could ship alone, and they would leave four documents describing an adjustment no code emits, which is the direction `CLAUDE.md` forbids (the document changes first *within* the slice that builds the thing, not a slice earlier). **The mitigation for 29 is batched dispatch on H4b-2's precedent, not a cut** |

### Decision 1 gates decisions 2, 3 and 4, and that is why it goes first

Ruling BH's ordering is not one task's local choice. It is what makes Holm's adjustment a per-member
expression rather than a second accumulation (decision 2), what makes the Bonferroni cell an
asymmetry to repair rather than a fourth branch to design (decision 3), and what decides whether
`family_members` needs to widen at all — a p-only member is invisible to every method **except** BH,
which is the method decision 1 makes real. Building first bakes the answer in by omission, which is
H4b-1's own *5 before 7* and H4c's decision 1.

### The refusal decision 7 mints, and what makes it permanent

**Proposed spelling: `E-STATS-NULLTEST-REPORTBY`**, on the `E-DATA-WEIGHT-CLUSTER-CONTRAST` /
`E-DATA-WEIGHT-ALLOCATION-CONTRAST` family shape, verified free at `bb8a56f`. **Named here rather
than left to its task, because an identifier nobody wrote down is how one gets minted twice under two
spellings.**

- It is a **documented narrow refusal carrying both a § Errors row and a § Validation row**, not a
  `-UNSUPPORTED` build-family code. Its row states the standing reason — relabelling a stratifying
  attribute changes which units a stratum holds, so the null is of a different partition rather than
  of the same estimate — rather than any form of *"until the construction exists."*
- **No slice inherits it as work.** `E-DATA-WEIGHT-CLUSTER-CONTRAST` is the precedent for a narrow
  refusal nobody owns retiring.
- **It must be consistent with task 24's conversion of the `report_by` filing into a permanent
  limitation**, which is the other `report_by` sentence this slice writes. Both land in
  § Statistical reporting and § What isn't a repeat, and one pass writes both or they contradict.
  **Checked, and they are disjoint**: this refusal is about `null_test.shuffle` **naming** a
  `report_by` attribute, and the limitation is about which interval construction a level's recorded
  column gets. A config declaring `report_by: [site]` with `shuffle: label` meets the limitation and
  not the refusal; one declaring `shuffle: site` meets the refusal and never reaches a level's
  interval question. Neither makes any part of the other unreachable, and **that clause belongs in
  the limitation's own wording**, so no later task re-derives it — a filing's claims about the code
  go stale like any other comment, and this one is being rewritten in the same slice.

### `E-STATS-NULLTEST-SHUFFLE` gates the only family-joining home this slice has

The check that `shuffle` names something real must accept **`data.units.attributes` names *and*
`sweep.groups` axis names**. Under decision 6 the group-axis contrast is the **only** p-value home
that joins the correction family, so a check scoped to `attributes` alone refuses the one shape the
slice exists to serve — and the check (task 7) and the construction (task 14) are seven tasks apart,
which is exactly how a fault like this survives review. The precedent for admitting an axis name
beside an attribute name is `units._stratum_groups`, which already does it for `assign`.

### `E-STATS-NULLTEST-LEVEL`'s ground, which is a § Validation row rather than a decision above

Every other code this slice mints has a decision row behind it; this one does not, and the reason is
that it needs none — **§ Validation's *Shuffle level is unambiguous* supplies its whole condition**,
worked example and all: *"`null_test.shuffle: status` varies within `match_set` `M07` but is constant
within `M12`, so neither a within-cluster nor a whole-cluster null applies."* The row has no code, no
emit site and no § Errors row today, so the task is giving a stated rule a check rather than deciding
anything. **Named here so a reader auditing the decisions table does not count six refusals against
four grounds**, and so nobody re-derives a condition the document already states. Its one design
consequence is an ordering one: the derivation it refuses on is the same derivation task 13 honours,
so the two share an expression rather than spelling one rule twice — the drift `contrasts.py`'s
shared pairing predicate was minted to prevent one slice back.

---

## What the scoping overturned, and what this spec adds to it

**The charter named two `validate` checks that are not H4d's work**, both measured: *"collides with
no recorded column"* already ships as `E-STEP-KEY-COLLISION` at run time and is not `null_test`-
specific, and *"an all-permuted design has no unpermuted value to test"* is not buildable, because
`replication.REJECTED_KINDS` refuses `permutation` as a repeat kind by name — the sentence in
`experimental-designs.md` § Bootstrap and permutation is **an argument for why the repeat axis was
the wrong home**, read as licence for a rule.

**The charter's one "validate checks" row is five distinct faults**, probed as exact sets at
`2a4dc53`: a typo'd `shufle`, an out-of-enum `method`, a `shuffle` naming an undeclared attribute, a
sub-floor `n`, and a rosterless declaration **all return `{E-STATS-NULLTEST-UNSUPPORTED}` alone**.
The typo becomes `E-CONFIG-KEY-UNKNOWN` the moment `envelope.LEAF_TYPES` is closed one level in; the
other four are minted here.

**Added by this spec, and named by neither the charter nor the scoping:**

- **Decision 7's vacuity finding and `E-STATS-NULLTEST-REPORTBY`.** The scoping's eight cells assume
  a per-condition **column** metric can be permuted. It cannot: `mean(column)` is invariant under any
  relabelling. **Six of the eight cells are live, not eight**, and the two dead ones are the two the
  document's own example sits on.
- **Only BH's adjustment is an accumulation** (decision 2). The scoping's task 15 budgets a two-pass
  rewrite for Holm *and* BH; measured against § The unit table is the inference base's *"at the same
  level the interval was computed at"*, Holm's is a per-member expression and the prefix `max` is not
  owed. This makes the slice smaller in exactly one place.
- **`rank_family` needs a tuple key, not a sentinel** (decision 4), because `_evidence_ratio` already
  returns `0.0` for a real member.
- **The regression pin** (task 27). The scoping carries none, which is the same omission the advisor
  pass found in H4c's scoping — and widening `family_members` plus adding a rank tier is precisely
  the change that can silently move every existing corrected bound in every run.
- **`hypotheses.py`'s BH call passes a partial member set with a larger `m`** (task 17). `size` is
  `len(counted)` while `family_members_` drops counted hypotheses with no `Member`, so BH's *i* must
  run over the members present while *m* stays the declared count. That is the same over-counting
  `family_shape`'s docstring already licenses for the sweep family — *"the product exceeds the number
  of members. That is deliberate and conservative"* — and the ruling is to cite it rather than invent
  a second rule.

**The development record is exempt from every sweep here.** `H4d-SCOPING.md` including its § 9
amendment, the H4b/H4c ledgers and the predecessor specs record what was measured on their dates and
**must not be retro-edited**. `spec-defects.md`'s live entries are the one exception, and there a
closed gap is **struck** rather than deleted.

---

## The traps

| Trap | The rule |
|---|---|
| A p-value that agrees with its interval | **Proves nothing.** A metric with a wide interval and a small p is the discriminating case, and a fixture where the two agree passes under a null that is wrong in any direction. Every fixture below is sized so a wrong null gives a **different number**, in a repo that found sixteen unfailable checks in statistics alone |
| A p-value assertion that cannot separate the ±1 estimator | `(b + 1)/(n + 1)` and `b/n` differ by ~1/n for a mid-range p, which no assertion should be asked to see. **Size the fixture so `b = 0`**: the correct answer is then `1/(n + 1)` and the mutant's is exactly `0.0`, a value a permutation test can never legitimately report |
| A mutation caught by a crash | **Not a pin.** An arithmetic accident of fixture geometry caught one on H4c, and changing the geometry would have silenced it. Widening `family_members` makes `_evidence_ratio`'s assert reachable; a test that observes the `AssertionError` is testing the assert, not the ranking |
| A mutation's blast radius has an expiry | Both directions were observed on H4c: a mutation blind at one commit became visible at the next, and one claimed blind was overturned by a one-line fixture change. **Re-run the mutation against the suite as it stands when the claim is made**, in the foreground, unfiltered |
| A test whose **name** claims the guarantee | Shipped twice on H4c, prescribed by its own briefs. A test called `..._is_adjusted_at_the_family_level` that asserts one hard-coded literal per member proves the literals, not the agreement. Assert the **relation** between two members, or between a member and `m` |
| Answering with a proxy | One corner in `cli._comparison_step_blocks` has been given **five wrong grounds across two slices**, every one an answer from a proxy, and only an end-to-end `run` ever exposed it. Tasks 19 and 20 write inside that function and inherit the rule: **verified by `run`, never by direct call** |
| Reading "this config is refused" as "this path does not run" | **`validate` collects rather than aborting.** Four readers in this repo have got this wrong, and it is *why* the five faults hiding under one code were found by probe rather than by reading. Ask what `validate` **reports**, in full, as an exact set |
| A null fixture whose permutation set is small enough for the identity to be drawn | With `\|Π\| = 10¹⁰` and `n = 5000` the observed labelling appears with probability 5 × 10⁻⁷, so `b = 0` is deterministic to eight figures. With `\|Π\| = 36` it is drawn ~139 times and no literal is assertable |
| A cluster fixture whose cluster count cannot change the answer | `CLAUDE.md` names the instance — correct and buggy counts both 3. Fixture C's ten clusters each hold **both** arms, so a whole-cluster mutant produces an **empty arm**, not a different number |
| Equal group sizes | Fixture C is 20 against 30. Equal sizes make several mutants coincide algebraically, which is H4c's first trap one construction over |
| Asserting `is not None` on a p-value | Null is a uselessly weak discriminator here: a degenerate null, a suppressed derived metric and a thin member all produce `null`. Every assertion needs a **positive literal** |
| A mutation whose two branches cannot differ | **A mutation is a claim too.** Swapping two members whose BH-adjusted values tie at the suffix-min bound changes nothing — the tie **is** the signature of the bind, so the ordering must be pinned on a member whose adjusted value is unique to it |
| Filtering a sweep's output | Filter the **file list**, never the output, and exclude the development record — it is evidence, not text to repair. A reviewer checking this exact rule lost a true hit to `grep -v superpowers` |
| A carried line number | Cite by **section**. `H4b-SCOPING` cited `stats.py:1900` for a function that had moved |
| Reading a subprocess probe as a pin | **Five times in three slices a correct fix shipped unpinned.** Verify by probe, then pin by mutation |

---

## The discriminating fixtures, stated here so no later task can weaken them

**The constraints first**, because a later task may only substitute fixtures meeting all of them:

1. **The observed labelling is the unique maximum of the statistic over the correct permutation set**,
   so `b = 0` and the correct p-value is exactly `1/(n + 1)`.
2. **The permutation set is large enough that the observed labelling is not drawn** — `\|Π\| ≥ 10⁹` at
   `n = 5000`.
3. **Unequal arm sizes** (20 against 30), so no mutant coincides with the correct answer by symmetry.
4. **Every cluster holds both arms, with unequal cluster contents**, so a wrong-level mutant is
   structurally distinguishable rather than numerically close.
5. **Between-cluster spread ≫ within-cluster spread**, so a wrong-stratum mutant lands in a
   completely different part of the real line.

### Fixture C — the roster, and why its arithmetic is exact

**50 units in 10 matched sets of 5.** Set `c` (c = 1…10) holds values `100c + 0, 100c + 1, 100c + 2,
100c + 3, 100c + 4`; its two `arm: of` units are the **top two**, `100c + 4` and `100c + 3`, and its
three `arm: against` units are the rest. So `arm` varies **within** every cluster — the within-cluster
level, unambiguously, which is the matched case-control null § Clustered units names.

- `Σ` over `of` = `Σ_c (200c + 7)` = `200 × 55 + 70` = **11070**, over 20 units → mean **553.5**.
- `Σ` over `against` = `Σ_c (300c + 3)` = `300 × 55 + 30` = **16530**, over 30 units → mean **551.0**.
- **Observed delta = 2.5**, and both means are exactly representable in binary, so the comparison at
  the identity draw has no float-epsilon corner.

With per-cluster arm counts held fixed, `delta = ΣS_c × (1/20 + 1/30) − T/30 = ΣS_c/12 − 920`, where
`S_c` is the cluster's `of`-sum and `T = 27600` is the roster total. It is **strictly increasing in
`ΣS_c`**, so it is maximized exactly when every cluster's `of` holds that cluster's top two values —
which is the observed labelling, and uniquely so, since no cluster has a tie.

| What computes it | The number | Why it separates |
|---|---|---|
| **Correct** — within-cluster relabelling, `p = (b + 1)/(n + 1)`, `b = 0` | **`1/5001` = 0.0001999600079984003** | `\|Π\| = C(5,2)¹⁰ = 10¹⁰`; the observed labelling is drawn with probability 5 × 10⁻⁷ over 5000 draws |
| The **second-best** within-cluster labelling, for reference | delta **29/12 ≈ 2.416667** (`ΣS_c` drops by 1, so delta drops by 1/12) | The gap below the observed is 0.0833, eleven orders of magnitude above float noise |
| Mutant: **`b/n`**, the ±1 continuity error | **0.0** | A permutation p-value can never legitimately be 0. Categorical, not numerical |
| Mutant: **reuses the observed assignment** (the shuffle is a no-op) | **1.0** | Every draw equals the observed, so `b = n`. Also the shape decision 8's invariance rule reports as `null` — **so this mutant must be checked against a fixture where the null is genuinely variable**, which C is |
| Mutant: **permutes across clusters** (the wrong stratum) | **≈ 0.5**, and never below 0.3 | Free relabelling lets `of` hold the global top 20 — mean 852 against 352, delta **500** — so the null spans ±500 and the observed 2.5 sits near its centre |
| Mutant: **whole-cluster relabelling** (the wrong level) | **`p_value: null`** | Every cluster's modal arm is `against` (3 against 2), so a cluster-level relabelling puts **no unit in `of`**: an empty arm, which decision 8 reports as `null` rather than as a number. Categorically distinct from every row above |

**Two homes, one arithmetic.** The same roster serves both p-value homes, which is deliberate — the
two differ in where the number lands, not in what it is:

- **C1, the family-joining home.** `sweep.groups: [arm]` with `data.units.assign` stratified by
  `match_set`, `data.units.cluster_by: match_set`, a **declared `statistics.contrasts` entry** (per
  decision 6, never `vs_baseline`), and a recorded column `y`. The contrast's interval is H4c's
  `welch_t_over_units_clustered`; its p-value is the one above; `n_clusters_of` and
  `n_clusters_against` are both **10**, since every matched set holds both arms.
- **C2, the per-condition home.** The same 50 units with `label` as an **ordinary attribute** (no
  group axis), a template `aggregate` returning `mean(y | label = of) − mean(y | label = against)`,
  and `cluster_by: match_set`. Same observed 2.5, same `1/5001`, and — per decision 5 — **no
  `p_value_corrected`, asserted as an absent key**. **C2 is blocked until task 15 claims
  `E-DATA-CLUSTER-DERIVED`**, which is why that filing is claimed rather than re-declined: with the
  refusal standing, a derived metric under a declared `cluster_by` is dropped, and there is no metric
  block for a p-value to land on.

**The `≥` comparison is against the statistic recomputed from the relabelled table, never against the
recorded `delta`.** They are the same number here by construction, and the rule exists so that a
run whose recorded delta was rounded, weighted or narrowed elsewhere cannot silently shift `b` by one
at the identity draw.

### Fixture D — the adjustment arithmetic, four members

Direct-call over four synthetic `Member`s at `m = 4`, because the adjustment must be pinned
independently of any engine. **The p-order and the evidence-ratio order deliberately disagree**,
which is the only arrangement that can tell decision 1's ruling from an implementation that ranks BH
on the evidence ratio:

| Member | raw `p` | p-rank (BH) | evidence rank (Holm) | BH adjusted | Holm adjusted | Bonferroni adjusted |
|---|---|---|---|---|---|---|
| X | 0.0001999600079984003 | 1 | 4 | **0.0007998400319936012** | **0.0001999600079984003** | 0.0007998400319936012 |
| Y | 0.22 | 2 | 1 | **0.41333333333333333** | **0.88** | 0.88 |
| Z | 0.31 | 3 | 2 | **0.41333333333333333** | **0.93** (floats as 0.9299999999999999) | 1.0 |
| W | 0.9 | 4 | 3 | **0.9** | **1.0** | 1.0 |

- **BH's suffix `min` binds on Y**: its own `m/i × p` is `4/2 × 0.22 = 0.44`, and it is pulled down to
  Z's `4/3 × 0.31 = 0.41333…`. **A single-pass implementation reports 0.44** — a 6 % difference on a
  literal, and the one assertion that can tell the two-pass rewrite happened.
- **The Y/Z tie at 0.41333… is the signature of that bind, not a weakness** — but it means a mutation
  swapping Y and Z is invisible on those two cells, so **the ordering is pinned on X and W**, whose
  adjusted values are unique to them.
- **Holm and Bonferroni necessarily agree at evidence rank 1** (both are α/m there), which is Y here.
  So the discriminating members for that pair are Z (0.93 against 1.0) and X (0.00019996 against
  0.00079984, a factor of 4).
- **X is the member the whole ruling is about**: p-rank 1, evidence rank 4. Under decision 1 BH gives
  it `4 × p`; an implementation ranking BH on the evidence ratio gives it `4/4 × p = p`, which is
  Holm's answer — so **the two readings differ by exactly the factor `m`** on this member.
- **Clipping at 1.0 is a rule, not a formatting choice**, and W under Holm (`0.9 × 2 = 1.8`) is where
  it is asserted.
- **Every member also carries an interval**, except one variant of the fixture in which X's `ci95` is
  `None`: that variant is decision 4's widening, and it must produce the **identical** BH table.
  Unwidened, X vanishes and `m` drops to 3, which moves every other row — the failure the widening
  exists to prevent, made visible as four changed literals rather than as an absence.

---

## Task decomposition — 29

Grain matches `H4d-SCOPING.md` § 7 and its four predecessors: each new construction, each new record
key, each minted code and each document-table edit is its own task.

**Decisions and documents — 6**

1. **The `fdr_bh` ordering ruling and the two adjustment definitions**, per decisions 1, 2 and 3, in
   `reference.md` § Statistical reporting **before any code emits an adjusted p-value**: BH ranks on
   ascending p with `m` unchanged; Holm's and Bonferroni's `p_value_corrected` defined as the p at
   the member's own correction level with **monotonicity disclaimed in writing**; the Bonferroni cell
   amended; the two-orderings sentence **narrowed rather than deleted**, since it stays true of every
   method that builds an interval at a rank.
2. **The landing ruling**, per decisions 5, 6 and 7, in § What isn't a repeat: the `vs_baseline` cell
   repaired to a declared `statistics.contrasts` entry; the ordinary-attribute row qualified to
   metrics the shuffled attribute enters; the `aggregated:` example re-authored as a **derived**
   metric with `p_value` and **no** `p_value_corrected`, its `0.0028` deleted rather than re-derived.
3. **The record shape**, in § Statistical reporting and § Contrasts, before any code writes a key:
   `p_value`, `p_value_corrected`, the resolved `null_test: {method, n, shuffle, level}` echo — with
   `level` the **derived** within-cluster/whole-cluster/rows answer, recorded because it is derived —
   and `null_draws` beside `n` on the `resample_draws` precedent, **absent, not null**, in a run that
   declared no `null_test`. **And one rule the scoping's § 9 amendment 2 routes here**: a relabelling
   permutes the **label** and never the weights, which stay with their units — one decision rather
   than a construction, and the only place a live weight meets a null (the per-condition half; no
   weighted contrast cell is reachable to permute).
4. **The `method` enum table and the floor**, per decision 9: the closed one-row table on
   § Statistical reporting's *Resample methods* precedent and for its stated reason; `min_honest_permutations`'s inequality and its
   integer stated together; `W-STATS-NULLTEST-FAMILY`'s bound at `20 × m`. **Before task 7 enforces
   any of them.**
5. **Decision 7's vacuity rule and `E-STATS-NULLTEST-REPORTBY`** — the § Validation row, the § Errors
   row, and the qualified sentence in § What isn't a repeat. **Written in one pass with task 24**, or
   the two `report_by` statements this slice adds contradict each other.
6. **`envelope.LEAF_TYPES` closed one level in** at `{method, n, shuffle}`, and the module comment's
   list amended — **before the refusal retires**, on the `resample` and `holdout` precedents
   `envelope.py` states twice.

**Validate checks — 4**

7. **`_check_null_test`**: `E-STATS-NULLTEST-METHOD`, `E-STATS-NULLTEST-N`, and
   `E-STATS-NULLTEST-SHUFFLE` over `data.units.attributes` **∪ `sweep.groups` axis names**. **After 4
   and 6.**
8. **`E-STATS-NULLTEST-UNITS`** — the filed no-roster check, reporting without returning, per the
   entry, whose expression and code the filing already specifies. **After 7.**
9. **`E-STATS-NULLTEST-LEVEL`** — § Validation's *Shuffle level is unambiguous*, roster-time, sharing
   its derivation with task 13 — and `E-STATS-NULLTEST-REPORTBY`'s guard. **After 7.**
10. **`W-STATS-CORRECTION-INAPPLICABLE` narrowed** to its three disjuncts through H4c's
    `contrasts.crossed_group_axes`, and **its message re-worded in the same change that makes
    p-values reachable** — it asserts today that no comparison *can* carry one. `W-STATS-NULLTEST-
    FAMILY` minted here beside it. **With 17, not after it.**

**Constructions — 5**

11. **`permutation_over_units`** — the row relabelling and the estimator `(1 + #{T ≥ T_obs})/(n + 1)`,
    against the **recomputed** observed statistic, with decision 8's invariance rule.
12. **The derived counterpart** — relabel, re-run `aggregate`, collect the null — the
    `percentile_of_derived` structure one construction over, including its survivor discipline.
13. **The cluster level derivation and both clustered draws** — within-cluster when the attribute
    varies inside one, whole-cluster when it does not. **After 11 and 9.**
14. **The group-axis contrast form** — the null is of the *contrast*, permuted within cells of every
    other group axis. **After 11.**
15. **`E-DATA-CLUSTER-DERIVED` claimed** — the clustered derived draw, on the ground H4c named for
    deferring it, and **a precondition of fixture C2** rather than an optional extra. **After 13, 12.**

**Correction and threading — 5**

16. **`Member.p_value`, `family_members` widened, `rank_family`'s tuple key**, and
    `_evidence_ratio`'s now-reachable assert, per decision 4 — with the exactly-one rule left
    untouched **as a recorded decision**. **After 11.**
17. **`corrected_for` made two-pass** for BH's suffix `min` only, `_level_for` re-argued,
    `p_value_corrected` in the output mapping with clipping at 1.0, and **`hypotheses.py` re-checked
    as a second caller** — its partial member set against a larger `m`. **After 16 and 1.**
18. **`fdr_bh` made real end to end**: `ci95_corrected` stays `null` by design, `p_value_corrected`
    produced, and `W-STATS-CORRECTED-THIN`'s interaction with a `None` level settled. **After 17.**
19. **The contrast-side write in `cli._comparison_step_blocks`** and the `null_test` echo beside it —
    **verified by an end-to-end `run`, never by direct call.** **After 14 and 16.**
20. **The per-condition write**, uncorrected per decision 5, with the invariance rule's `null` and
    the column case writing nothing at all. **After 12 and 15.**

**Filings, retirement and residue — 9**

21. **The hypothesis family's exposure to a p-value settled explicitly** — `evaluate_on` names three
    bounds and none is a p-value, so no verdict rests on one; the entry records `p_value_corrected`
    at the hypothesis family's own size, exactly as it records `ci95_corrected`. A decision to
    record, not a feature to add. **After 17.**
22. **The two contrast-disclosure findings claimed** — a contrast-scope thin warning carrying a
    `where` plus its § Warnings row (Finding 1), and the resolved-`resample` echo on the contrast
    entry (Finding 3). H4d adds a `null_test` echo to that same entry, so the "no new disclosure
    surface" ground H4b-2 and H4c used is unavailable to it. **After 19.**
23. **The finite-inputs filing** — verify the premise against the relabelling paths, then claim or
    re-decline **with the measurement**, updating both `*_is_a_known_unfixed_gap` tests with it if
    closed. **After 12.**
24. **The `report_by` filing converted to a documented permanent limitation**, per its own terminal
    instruction. **Its subject is the `resample_columns` asymmetry** — a `report_by` level's
    recorded-column interval stays `t_over_units` under a declared `resample`, because
    `cli.command_run`'s level call still does not pass `resample_columns` through to
    `summarize_step` — which is what the entry's own instruction names, not the
    `W-STATS-REPORTBY-THIN` whole-roster count that § What isn't a repeat already records as a known
    gap. A § Statistical reporting sentence or a § Validation row, **not** a fourth decline and not a
    surprise fix, and written in one pass with task 5.
25. **Retire `E-STATS-NULLTEST-UNSUPPORTED`** — the one truthy-guarded emit, the `NOT BUILT` marker,
    and § The one config file's *"One declaration above is not yet built"* sentence **deleted rather
    than decremented**, with the registry-absence sentence **preserved** for the surviving
    `E-TEMPLATE-INSTALLED-UNSUPPORTED`. **After every check and every construction.**
26. **The two `-UNSUPPORTED`-family tests converted in task 25's own commit** —
    `test_the_unsupported_family_is_down_to_null_test` and
    `test_every_unsupported_message_defers_rather_than_scolds`, the second reparametrized onto
    `E-TEMPLATE-INSTALLED-UNSUPPORTED`, whose message the scoping confirmed already contains *"later
    slice"* — plus the retired-code `src/` sweep on H4a's precedent.
27. **The regression pin**, its literals **captured at the branch point before task 11**: every
    existing corrected bound in a `holm` run byte-identical across this branch, the worked example's
    intervals unnarrowed, and — the property decision 4 rests on — `family_members`' widening a no-op
    for every config that declares no `null_test`. A literal recorded afterwards records the change
    rather than the baseline.
28. **The citation sweep** — § Validation's two rows given a **restated condition** now that code
    stands behind each (they carry no code column, per the scoping's amendment 4), § Errors and
    § Warnings rows minted for every code this slice adds, `experimental-designs.md` § Mistakes core
    prevents' permutation row now delivered by a check rather than by the wholesale refusal, and
    `feasibility-llm-growth-studies.md` **re-dated rather than edited**. **The development record is
    not swept.**
29. **Whole-branch review**, and the mechanical plus cross-document consistency passes.

**Direction against the scoping's 27: +3, −1.** Up: task 5 (decision 7's vacuity rule and its
refusal, named by neither charter nor scoping); task 27 (the regression pin, which the scoping omits
exactly as H4c's did); and task 4, which the scoping's own § 9 amendment 3 says must precede its task
6 rather than live inside it. Down: the scoping's tasks 2 and 3 are one edit — the landing ruling and
§ What isn't a repeat's repair are the same passage — merged into task 2. **29, derived here rather
than carried, and it does not agree with 27.**

### The ordering constraints, each with its reason

| Constraint | Reason |
|---|---|
| **Tasks 1–5 before any code** | A `method` string, a record key or an adjusted p-value emitted before the four documents name it is the defect H4b-1 avoided deliberately and H4c repeated the avoidance of |
| **Task 1 before 16, 17 and 18** | Decision 1 fixes whether BH exists and on which ordering, and with it whether `corrected_for` needs a second pass at all |
| **Task 4 before task 7** | The floor's value and its ground are a document change; a check enforcing a number no document states is the shortcut the scoping's amendment 3 names |
| **Task 6 before tasks 7–9 read any value, and before task 25** | Both `resample` and `holdout` were closed one level in *ahead* of their own refusal lifting, and `envelope.py` states the ground twice: a typo among fixed key names turns from latent to live at the moment of retirement |
| **Task 7 before task 14 is verified** | `E-STATS-NULLTEST-SHUFFLE` scoped to `attributes` alone refuses the group-axis shuffle, which is the only family-joining home this slice has. `validate` gates `run`, so the check decides whether the construction can be exercised at all |
| **Task 15 before fixture C2 is asserted** | With `E-DATA-CLUSTER-DERIVED` standing, a derived metric under a declared `cluster_by` is dropped and there is no metric block for a p-value to land on |
| **Task 16 before 17 and before 19–20** | The members carry the p-value into the family; a member that cannot hold one makes the correction pass untestable end to end |
| **Task 10 with task 17, not after it** | The warning's message asserts something true only while the engine is absent. Narrowing it in a later commit ships a false diagnostic in between, and `spec-defects.md` says so in as many words |
| **Tasks 19 and 20 by `run`, never by direct call** | The derived-key-collision corner inside `_comparison_step_blocks` has been given **five wrong grounds across two slices**, and every direct-call probe hand-built the maps and never reached it |
| **Task 5 in one pass with task 24** | Both write a normative `report_by` sentence; written apart, one says the combination is refused and the other describes its gap as live |
| **Task 27's literals captured before task 11** | A pin whose values are captured afterwards asserts the new behaviour against itself |
| **Every check and every construction before task 25** | Measured, not hypothetical: five distinct faults earn only the wholesale refusal today, so retiring it first makes a typo'd `shufle`, a misspelled `method`, an undeclared `shuffle`, a sub-floor `n` and a rosterless declaration all validate clean at once |
| **Task 26 in one commit with task 25** | Both tests assert against the code the retirement removes; splitting them leaves the branch red for a reason unrelated to either change |
| **Task 28 must not touch the development record** | It is evidence, not text to repair |

---

## The inherited filings, and the terminal ones

`H4d-SCOPING` § 6 lists five, three of them declined by three or four consecutive slices and named
terminal in writing. **After H4d there is no further slice whose surface is the `statistics` block**,
so a decline is no longer available in the form previous slices used: an entry not claimed here must
be **converted into a documented limitation**, with the document that carries it named.

| Filing | Ruling |
|---|---|
| `statistics.null_test` has no no-units check (`E-STATS-NULLTEST-UNITS`) | **Claim it — task 8.** The entry already did the design: the code, the expression `not (doc.get("data") or {}).get("units")`, and the report-without-returning rule, on `E-REPL-FOLD-NO-UNITS`' and `E-STATS-RESAMPLE-UNITS`' shared precedent |
| `E-DATA-CLUSTER-DERIVED` — the clustered derived draw | **Claim it — task 15.** H4c deferred it on a *new* ground — that building it while the derived branch's two-ground suppression guard was being written would make one guard distinguish three states — and named the condition for building it: that the guard has shipped and survived a whole-branch review. It has. It is also now a **precondition of this slice's own per-condition fixture**, which is the strongest form of ownership available |
| *A column resample is only ever defined given finite inputs* | **Verify the premise, then claim or re-decline with the measurement — task 23.** The identical prediction was made of H4b-2 and did not come true, and of H4c and was measured rather than inherited. H4d recomputes metrics over relabelled tables, which is the same finiteness surface one construction over — likelier, and likelier is not measured |
| *The contrast path discloses nothing about its resample* — Findings 1 and 3 | **Claim both — task 22.** Finding 3 is an echo on the record this slice is already re-authoring; Finding 1 is warning-registry work, and H4d is the slice that adds a `null_test` echo to the same entry, so the "no new disclosure surface" ground both predecessors used is unavailable here. H4c re-declined Finding 1 to H4d **by name** |
| `W-STATS-REPORTBY-THIN`'s whole-roster-versus-arm gap, and the `report_by` `resample_columns` asymmetry | **Convert — task 24.** It is live on C1–C3, created by neither a weight, a cluster, a pairing derivation nor a null test, and genuinely unrelated to `null_test`. Its own entry prescribes the move: *"the correct move at that point is not another deferral — it is converting this into a documented, permanent limitation."* It lands as a § Validation row or a § Statistical reporting sentence in `reference.md`, **struck in `spec-defects.md` with the document that now carries it named**, and written in one pass with task 5 so the two `report_by` statements agree |

Two further routed rows, neither in the five and both H4d's by elimination: `spec-defects.md`'s
*Row 284 "Correction can be applied"* (the three-disjunct condition) and the
`W-STATS-CORRECTION-INAPPLICABLE` entry's amendment (*"H4 must make the warning conditional in the
same change that makes p-values reachable"*). Both are task 10.

---

## The payoff, stated so it cannot be rounded

### Measured on 2026-08-18 against commit `2a4dc53`

**H4d unblocks ZERO configs.** All eight `statistics` blocks in
[the feasibility analysis](../../feasibility-llm-growth-studies.md) carry `null_test: null` — an
explicit null, which `_check_unimplemented`'s truthy guard treats as undeclared and which probes
clean — verified with a can-fail control on the same file (`resample: {` → 7, a block declared in a
truthy form). **Zero configs declare `fdr_bh`**: eight `correction:` declarations, seven `holm` and
one `none`. So no config reaches `E-STATS-NULLTEST-UNSUPPORTED` at all, and the one warning this
slice narrows fires for none of them. **The no-remaining-core-side-blocker count stays six and the
executable count stays three.** Neither moves. The six are C1, C2, C3, E1, E2 and E5; the three are
E1, E2 and E5, with C1–C3 still needing `io.reuse_from`, unbuilt and unowned.

**A retired-refusal count is not an executable-run count**, and no sentence this slice writes may
conflate them. Both review verdicts on H4b-1 faulted that conflation, and a *correction* on H4b-2
inverted the same two numbers and named a retired refusal as live. The net on refusals here is **one
`-UNSUPPORTED` retired, five narrow refusals minted in its place** (`-METHOD`, `-N`, `-SHUFFLE`,
`-UNITS`, `-LEVEL`), plus `E-STATS-NULLTEST-REPORTBY` and one retired filing
(`E-DATA-CLUSTER-DERIVED`) — not "a refusal count that improves", and not any number that moves.

**What H4d is worth instead**, stated so it is not mistaken for nothing:

- It empties the **`NOT BUILT` list** in § The one config file. H7b Part B's scoping predicted that
  count *"drops to one"*; that prediction is now due and **overtaken** — it drops to **zero**.
- It closes the repo's largest remaining **specification-versus-code** gap. At `2a4dc53` `p_value`
  appears exactly once in `src/`, in a comment saying it appears nowhere, while the four documents
  describe `p_value`, `p_value_corrected`, `fdr_bh`, a `method` enum, a cluster-level derivation and
  a group-axis routing rule across nine sections, all in the present tense.
- It is the only slice that makes `statistics.correction: fdr_bh` — a value `validate` accepts, a
  generated config's comment offers and § The one config file enumerates — mean anything at all.
  Today it is an accepted declaration that nulls every corrected interval and reports nothing in
  their place, which is the exact state § Statistical reporting says it exists to prevent.
- It turns **one refusal hiding five faults** into five checks, plus a sixth for a combination
  nothing checks today, and closes the last whole leaf in `envelope.LEAF_TYPES` that a slice owns.
- It is the **last slice whose surface is the `statistics` block**, and five `spec-defects.md`
  filings are queued behind it — three marked terminal by name. After H4d there is no further slice
  for a fifth deferral to point at.

That is a specification-integrity payoff, not an execution payoff, and it must be argued as one.
**Nothing in the feasibility analysis gets closer to running because H4d landed.**

---

## Out of scope, with the route

| Out | Owner |
|---|---|
| A `null_test` whose `shuffle` names a `statistics.report_by` attribute | **Refused** by `E-STATS-NULLTEST-REPORTBY`, minted here as a standing narrow refusal. No slice inherits it as work |
| A second `null_test.method` beside `permutation` | **A documented change**, by the closed table task 4 mints — not a gap |
| `W-STATS-REPORTBY-THIN`'s whole-roster gap | **Converted here** to a documented permanent limitation (task 24), not deferred |
| A p-value on a reported `Estimate`, or on a hypothesis verdict | **Refused by construction.** An `Estimate` is `reported: true`, outside the correction family and never recomputed; `evaluate_on` names three bounds and none is a p-value (task 21) |
| Ranking Holm on the p-value, or enforcing monotonicity on its adjusted p | **Refused** by decision 2, which disclaims it in the document so a later slice does not "fix" it back into the two-orderings problem decision 1 avoids |
| `E-SWEEP-BASELINE-GROUP` | **Permanent.** It refuses a declaration on the peers rule; decision 6 routes around it rather than lifting it |
| `E-DATA-WEIGHT-ALLOCATION-CONTRAST`, `E-DATA-WEIGHT-CLUSTER-CONTRAST` | **Refused**, minted by H4c and H4b-2. No weighted contrast cell is reachable to permute; a weight on the **per-condition** half is live, and the rule task 3 records is that a relabelling permutes the label and never the weights, which stay with their units |
| `io.reuse_from` and `lineage.py` | **Unowned**, filed. Blocks E3/E4/E6 |
| Folds and holdouts within cells; `E-REPL-FOLD-CELLS` / `E-DATA-HOLDOUT-CELLS` | **H3c-3** |
| The apparatus probe, `apparatus_facts`, `cli.py`'s hardcoded `apparatus: null` | **H7d** |
| `study` / `report` / `diff` / `freeze` | **H8** |
| Interactions, dose-response orderings, differences-in-differences | **Refused.** Contrasts do not nest |

**Task count is 29.**

---

## Corrections against the code

**Appended 2026-08-18 by the implementation plan's author
([`plans/2026-08-18-null-test.md`](../plans/2026-08-18-null-test.md)), measured against `main` at
`a207702`. The body above is not edited** — a spec records what was decided when it was written, and
a retro-edit destroys the evidence. Each entry names what it replaces and how it was verified. Every
one of the eight changes a task's contents; none changes the task count, the ordering constraints or
the payoff answer.

**1. `percentile_of_derived`'s structure cannot express a permutation, because the roster's
attributes are re-applied on every draw.** § Task decomposition's task 12 reads *"The derived
counterpart — relabel, re-run `aggregate`, collect the null — the `percentile_of_derived` structure
one construction over"*. Measured: `cli._make_resample_fn` builds `lambda units:
tmpl.aggregate(_attributed(units, attrs), cfg)`, and `cli._attributed` merges
`attributes.get(row["unit"], {})` **over** each row, so a relabelling written into the table's rows
is erased before `aggregate` sees it. **Verified by probe**, not by reading alone: relabelling two
rows and passing them through `_attributed` with the original roster mapping returned the original
labels. A `permutation_of_derived` built on a one-argument `compute` would therefore report
`p_value: 1.0` for every derived metric in every run — which is § The discriminating fixtures'
*"reuses the observed assignment"* mutant arriving as the default behaviour. **Replaces task 12's
structural claim:** the construction takes `compute(table, labels)`, and `cli` builds a second
closure family (`_make_null_fn`) rather than reusing the resample one. Propagates to tasks 14, 15
and 20 through the `Interfaces` blocks in the plan. **One benefit: fixture C2 needs no prescribed
mutation for this property — the pre-fix behaviour is the mutant.**

**2. Decision 9's closed form does not reproduce decision 9's own integers.** The decision states
`min_honest_permutations(level) = ceil(1/level) − 1` **and** `n ≥ 20 at α = 0.05` **and** a family
bound at `20 × m`, *"stated together here so they cannot drift"*. **Verified by computation** at
`a207702`: `ceil(1/0.05) − 1 = 19` and `ceil(1/0.025) − 1 = 39`, against the stated 20 and 40.
`floor(1/level)` reproduces both, and it is what the stated **strict** inequality gives —
`1/(n+1) < level ⟺ n > 1/level − 1`. The closed form is the expression for the **non-strict** reading
`1/(n+1) ≤ level`, which the decision's own prose rejects. **Replaces the expression, not the
inequality or either integer:** `min_honest_permutations(level) = math.floor(1.0 / level)`. One
measured caveat recorded with it: at `level = 0.05/7` a brute-force scan of the inequality answers
139 because `1/140` and `0.05/7` differ by one ulp, where `floor` answers the exact-arithmetic 140 —
which is why the plan writes the expression rather than a search.

**3. Three shipped comments claim what decision 4's widening makes false.** Decision 4 rules that
`family_members` widens; it does not name the comments that assert the old predicate. **Verified by
reading all three at `a207702`:** `correction.Member.__post_init__`'s docstring — *"excluded by
`family_members` before any of the three fields is ever read"*; `correction._evidence_ratio`'s inline
comment — *"family_members dropped the others"*; and `cli._comparison_step_blocks`' comment at the
`Member(` call — *"An entry with no `ci95` is dropped by `family_members` before any of the three
fields is ever read"*. **Adds to task 16**, with `CLAUDE.md`'s rule that a claim is preferably
deleted rather than rewritten.

**4. `units.stratum_varies_within_cluster` cannot supply the level derivation.**
§ `E-STATS-NULLTEST-LEVEL`'s ground says the refusal *"shares its derivation with task 13"*, and the
nearest shipped expression is that function. **Verified by reading:** it returns *the first offending
cluster with its values, or `None`*, which separates "varies somewhere" from "constant everywhere"
and **cannot** separate "varies in every cluster" (a legal within-cluster null) from "varies in some"
(the ambiguity the row refuses). **Adds a new shared function to task 9**,
`units.null_test_level(roster, cluster_by, shuffle) -> tuple[str, tuple[str, str] | None]`, minted
there and consumed by task 13 — H4c's task-9-mints-the-predicate precedent. The sharing the spec
requires is preserved; the function it would have been shared through is not the right one.

**5. `corrected_for`'s `thin` flag fires for a p-only member under `holm` and `bonferroni`.** Task 18
names *"`W-STATS-CORRECTED-THIN`'s interaction with a `None` level"* — the `fdr_bh` half. **Verified
by reading `corrected_for` and `_corrected_bounds`:** `thin = level is not None and bounds is None`,
and `_corrected_bounds` falls through to `None` for a member carrying none of the three evidence
kinds. So under `holm` a widened p-only member sets `thin: True`, and `cli` emits a warning whose
message says the **resample's draws** could not support the level — false of a member that never had
an interval. **Adds a condition to task 17's `thin` expression** (`and member.ci95 is not None`) and a
test asserting the flag is `False`, pinned on the flag rather than on the warning, since the flag is
where the fault lives.

**6. `rank_family`'s tuple key must short-circuit `_evidence_ratio`.** Decision 4 rules the key is
`(has_interval, -ratio, declaration_index)` and separately notes the assert becomes reachable; it
does not connect the two. **Verified by reading `_evidence_ratio`'s `assert member.ci95 is not
None`:** a key expression evaluating `-_evidence_ratio(m)` for every member evaluates it **eagerly**
and raises during the sort. **Adds the short-circuiting form to task 16's code block**, and it is the
spec's own *"a mutation caught by a crash is not a pin"* trap arriving as an implementation bug
rather than as a test-design one.

**7. `hypotheses.evaluate`'s three-state corrected-bound logic moves by exactly one field.** Named by
neither the decisions nor task 21. **Verified by reading `evaluate`, `_tested_number`,
`verdict_for` and `_observed_block`:** `corrected_unavailable` is set from a falsy `ci95_corrected`,
so a counted hypothesis whose member is p-only now receives a `fields` entry where it previously
received none. **What moves is `observed.ci95_corrected`, from absent to `null`. What does not move:**
`supported` (a bound test had no raw interval to read either, and `evaluate_on: observed` bypasses
the flag) and `family_size` (it is `len(counted)`). **Recorded at that size in task 17's step 5**,
with one test asserting exactly it — an inflated claim here would be worse than none.

**8. The `statistics.report_by` level call site is a reachable cell the decisions do not name.**
Decision 7 rules on a per-condition recorded column and on `shuffle` naming a `report_by` attribute;
neither covers a level's own **derived** metric under a `shuffle` naming some *other* attribute —
which § The refusal decision 7 mints establishes is a **legal** config, since the refusal and the
limitation are disjoint. **Verified by reading `cli.command_run`:** `summarize_step` is called a
second time per level, at the same site § The inherited filings' `resample_columns` asymmetry is
about. **Added as a ruling to the plan's task 20** — a level's derived metric gets no `p_value`, on
§ The unit table is the inference base's own ground that a level *"repeats metrics over strata
without adding executions or joining the correction family"*, with `command_run` passing no
`null_test` to that call and one test pinning it beside a condition block that does carry one. Ruled
rather than left, because an unruled reachable cell inside the function pair task 24 is rewriting
claims about is the shape a whole-branch review finds late.
