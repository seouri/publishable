# H3d re-scoping — a fixed holdout split

Read-only measurement against `main` at `78bb794`, on 2026-08-15. This **replaces**
`H3d-SCOPING.md`, which was pinned to `cb96c7d`; four slices have landed since
(H3c-1, H3c-2, H7a, H4a). Every identifier below was grepped or probed, not
remembered. Spec claims and build facts are labelled separately throughout.

**Verdict: 19 tasks**, against the old scoping's 16 — and **the recommendation is to
split the slice in two**, at the seam § 8 names. The growth is the usual direction:
the old count omitted `holdout.from`'s column accessor entirely, under-counted the
owned prose sweep by a factor of three, and treated one construction as one where
the build needs two.

**Baseline at `78bb794`:** `uv run pytest -q` → **1801 passed, 2 xfailed**, 96 s. Every
probe below was run against that tree with nothing modified.

**The old scoping's structure is sound and this document keeps it.** Roughly two
thirds of its claims re-verify unchanged, and those are marked **verified** and not
re-argued. What follows concentrates on what moved.

---

## 0. Executive summary — the five things that change how H3d is built

1. **The H3c-3 refusal and H3d's own cell refusal are one refusal, not two.** Both
   faults are "a roster-wide evaluation split beside a cell structure", both are
   knowable from the declarations alone, and both are live today — I reproduced each.
   One check site, one code family, one documents pass. § 5.
2. **`E-DATA-HOLDOUT-UNSUPPORTED`'s retirement makes 13 comments in `src/` false, not
   4.** The old § 3 counted three prose blocks plus `envelope.py`'s. The sweep stops
   one file short in three directions. § 6.
3. **`holdout.from` is not reachable through `CONSTANT_COLUMN_RULES`**, and two
   comments in `units.py` say so in the present tense with H3d implicitly named. The
   old decomposition has **no task for it**. § 4.
4. **The draw is two constructions, not one.** `_assign_whole_clusters_by_ratio`
   takes a non-optional `Mapping[str, str]` and indexes it directly, so the
   *unclustered* holdout cannot go through it. The old § 1's "H3d calls the H3c-2
   primitive" is half the story. § 3.
5. **The payoff is "one refusal retired that 6 of 9 configs hit, zero experiments
   newly executing."** The charter's "unblocks 6 of 9" is a drift from the
   feasibility analysis's own words, which say *validate clean*, not *execute*. § 7.

---

## 1. Verifying the old scoping, item by item

### § 1 *What exists* — verified, with two corrections

| Old claim | Status |
|---|---|
| `_check_unimplemented`'s tuple loop holds `holdout` as its last member | **Verified.** `validate.py:3137`, still the sole remaining entry |
| The guard is `units.get(field)` truthiness, so `holdout: {}` and `holdout: null` pass | **Verified by probe** — a config with `holdout: {}` validates **clean**; `holdout: null` likewise |
| `E-DATA-HOLDOUT-UNSUPPORTED` is the only `E-DATA-HOLDOUT-*` identifier anywhere | **Verified.** `grep -o "E-DATA-HOLDOUT[A-Z-]*"` over `src/` and the four documents returns exactly five hits, all that one code (`validate.py`, `artifacts.py`, `cli.py`, `envelope.py`, `reference.md`) |
| `UnitList.train` is built and raises `E-STEP-UNITS-UNAVAILABLE` | **Verified — and it is a *populated* surface, not an unread one.** `runner.execute_plan:578` constructs `UnitList(..., train=UnitList(...))` on the fold path. This is **not** the `BaseTemplate.required_env` shape: `.train` has a reader and a writer today, and H3d adds a second writer. H3d's surface is smaller here than a shipped-but-unread promise would make it |
| `units._assign_whole_clusters_by_ratio` is the clustered holdout draw at `[1-frac, frac]` | **Verified as far as it goes — but it is only half the draw.** See § 3 |
| `units._apportion`, `_stratum_groups`, `arms_of`, `clusters_of`, `stratum_names`, `allocation_hash` reusable unchanged | **Verified.** `_stratum_groups` gained two parameters since `cb96c7d` (`axis: str`, `resolved: Mapping[str, ArmPlan] \| None = None`) — the second is defaulted and the first is a label used only in messages, so a holdout caller passes `"holdout"` and is otherwise unaffected |
| `units.stratum_varies_within_cluster` is built, and "H3d supplies the **second** caller and the second code" | **Stale.** There are **three** call sites today: `validate.py:2045` (`E-DATA-ASSIGN-STRATIFY-VARIES`, H3c-1), `:2625` (`E-REPL-FOLD-STRATIFY-VARIES`, H3b), `:5222` (`E-STATS-RESAMPLE-STRATIFY-VARIES`, H4a). H3d is the **fourth**. And the function's own docstring still names only two rows — *Fold strata survive clustering* and *Holdout strata survive clustering* — so it is a **false comment claiming a narrower scope than the code has**, owed a fix in whichever task adds the call |
| `replication.REJECTED_KINDS` already routes `{kind: holdout}`, so *Holdout isn't a repeat kind* is not one of the charter's three | **Verified by probe** — `{kind: holdout, n: 1}` reports `E-REPL-KIND` with the message *"`holdout` is not a repeat kind — declare `data.units.holdout` instead"* |
| `stats.handed_to` / `collapse_repeats` stay on their `None` paths; there is no `holdout_members` | **Verified, and now argued from the code rather than by analogy.** `attrition`'s `handed` is `keys` when `fold_members is None`, so the narrowing must happen on the roster. See § 6 trap 1 |

### § 2 *`partition_units` is not rewritten a third time* — verified

**Build fact, re-measured:** `partition_units(roster, k, digest, clusters=None, strata=None)`
is byte-identical in signature to `cb96c7d` and still builds `k` equal buckets via
`_assign_whole_clusters`, which deals to the *least-loaded* of `k` equal buckets.
H3d touches it **not at all**. Verified.

**But the old scoping's framing — "this slice exists because a spec claim and
`partition_units`'s signature differ" — is the wrong frame now.** `partition_units`
was never going to be the seam; H3c-2 built the ratio primitive under another name
and H3d's real gap is that **no function produces a two-way roster partition at all**,
plus everything downstream of one (§ 6's four denominators, the runner gate,
`allocation.json`'s fourth key). The signature gap is one line of a nineteen-line slice.

### § 2's three under-specifications — all three still open, all three still owed

Re-read against `reference.md` at `78bb794`:

**(a) Which `by_attribute` value is the test side — still unsettled.** § A fixed
holdout split's example uses `from: split` and § Validation's *Holdout is resolvable*
says "expected exactly two", but a holdout declares no `levels` and
`arms_of(roster, column, levels)` requires them. **Recommendation: fix the two
literals as `train`/`test` and refuse a `{A, B}` column**, because the alternative —
"the two values sorted, second is test" — makes the answer depend on a lexical
accident of the input, which is the class of thing this repo refuses everywhere else.

**(b) `allocation.json` has no home for a drawn holdout's seed or strata — verified.**
§ `allocation.json` (line 830 ff.) prints `"holdout": {"train": [...], "test": [...]}`
with no seed anywhere, and states in bold that `seed` and `strata` are keyed by axis.
A holdout is not an axis. The block's own `# recorded explicitly` comment on
`seed: auto` is contradicted by the printed example. Still owed.

**(c) The `auto` table has no holdout row — verified.** § What `auto` derives from's
prose names `holdout.seed` ("`sweep.sample.seed`, `assign.seed`, and `holdout.seed`
each default to the derivation above") but its table omits it, and the malformed-pin
paragraph names `E-SWEEP-SAMPLE-INVALID` and `E-DATA-ASSIGN-SEED` and nothing for
`holdout.seed`. Still owed.

**A fourth under-specification the old scoping did not have, because H4a did not exist
when it was written:** *nothing in the four documents connects `statistics.resample`
to `data.units.holdout`.* See § 6 trap 6.

---

## 2. The § Validation rows — measured, and the charter's "3 rows" is right about the count and wrong about which

`reference.md` § Validation carries **five** rows naming `holdout`. Grepped, and each
checked for an emit site:

| Row | Line | Emit site today | H3d owes |
|---|---|---|---|
| *Stratification attribute exists* | 272 | **Half built.** `_check_fold_stratify_by` covers the `fold` half under `E-REPL-FOLD-STRATIFY-UNKNOWN`. `validate.py:2520`'s own docstring says the `holdout.stratify_by` half "belongs to the slice that builds that block" | The holdout branch, its own code |
| *Holdout isn't a repeat kind* | 274 | **Built.** `replication.REJECTED_KINDS` → `E-REPL-KIND`, probe-confirmed | Nothing. Re-check the route once the field exists |
| *One evaluation split, not two* | 275 | **None.** Probe: `holdout` + `{kind: fold, k: 5}` together reports only `E-DATA-HOLDOUT-UNSUPPORTED` | The check |
| *Holdout is resolvable* | 276 | **None** | The check — three faults in one row (`frac` range, `from` required, exactly-two column) |
| *Holdout strata survive clustering* | 277 | **None.** The *computation* exists (`stratum_varies_within_cluster`); the *rule* has no caller | The fourth call site and its code |

So the charter's "3 rows" is the count of *unbuilt, holdout-only* rows — correct — but
it misses that *Stratification attribute exists* is a shared row with an unbuilt half,
which the old scoping did catch and route to its task 5. **Verified: no documented
holdout row has code behind it that the charter assumed absent, and none has code
behind it the charter assumed present.** This is the one section where `CLAUDE.md`'s
"a documented row with no emit site" warning turns up nothing new.

**None of the five rows has a minted `E-` code.** Nine or so codes are unminted, as the
old scoping said. Verified.

---

## 3. The draw is two constructions, not one — the old § 1 is half right

**Build fact.**

```python
def _assign_whole_clusters_by_ratio(
    units: list[Unit], weights: Sequence[float], rng: random.Random, clusters: Mapping[str, str]
) -> list[list[Unit]]:
    ...
    members.setdefault(clusters[unit.key], []).append(unit)
```

`clusters` is **not** `Optional` and is indexed directly — unlike its sibling
`_assign_whole_clusters`, whose docstring argues at length that `clusters is None` is
"a cluster of one per unit, not another path". The ratio primitive has no such branch
and no such argument.

**So the unclustered holdout goes through `assignment_for`'s `random` branch instead**:
`_apportion(len(roster), [1 - frac, frac])`, one `rng.shuffle` of the whole roster,
consecutive slices. Verified against that branch's docstring, which states exactly
that construction.

**What this costs the plan.** Old task 8 ("`units.holdout_for` — the single producer")
is two constructions with a **stated relation between them**, not one call. That
relation is precisely where H3c-2's own checks-that-could-not-fail were found:
`CLAUDE.md` records a cluster fixture where correct and buggy cluster counts were both
3, and a 13-unit apportionment that matched a reverse-order mutant by coincidence.
A fixture that cannot tell `_apportion`-then-slice from
`_assign_whole_clusters_by_ratio`-with-singleton-clusters proves nothing about either.
Splitting it into two tasks with a can-fail control on each is why the count moved.

---

## 4. `holdout.from` needs its own column accessor — a task the old decomposition does not have

**Build fact, two sites, both present tense:**

- `units.py:312–316` — *"`assign.<axis>.from` and `holdout.from` are the next two
  columns that want this rule, and neither is a flat string… Task 11 adds
  `_assign_constant_columns` below as `assign`'s accessor, so that one is now
  reachable; **`holdout.from` still is not** — its shape is a single key under a fixed
  mapping, not one-per-declared-axis, and needs its own accessor rather than this
  one's `axis` loop."*
- `units.py:720` — *"**`holdout.from` is not reachable through this registry today**…
  it needs its own accessor the same shape `_assign_constant_columns` is for `assign`,
  and nothing in this task builds one."*

`CONSTANT_COLUMN_RULES` is what makes `collapse_measurements` refuse a unit whose
`cluster_by` / `weight_by` / `assign.<axis>.from` value is **not constant across the
rows being collapsed into one unit**. Under `data.units.measurements`, a
`by_attribute` holdout reading a column that disagrees between two rows of the same
unit would silently take whichever row `collapse` kept — a unit assigned to train or
test by an accident of row order.

**`design-principles.md` § Core vs. plugin lists `holdout.from` beside `assign.from`
as parallel namers of an input field** (quoted at `validate.py:1034` and
`spec-defects.md:4687`), so this is not an invented requirement.

**It is a small task and a real one**: a `_holdout_constant_column(units_decl.get("holdout"))`
returning at most one entry, keyed `holdout.from` for the message, plus a
`CONSTANT_COLUMN_RULES` entry keyed `holdout` (bare, no dot — that registry's own
stated constraint), plus its place in the documented severity ordering the
`constant` dict's build order encodes. **Old § 6 has no task for it.**

Consequence for `validate.py:883`'s claim that *"`cluster_by`, `weight_by`, and
`holdout` are not read by `resolve_units` at all"*: once `holdout.from` joins the
registry, that sentence becomes false in the same way its `assign` sibling already
would have. It is on the owned-sweep list in § 6.

---

## 5. The cells question, settled now — and it is one refusal, not two

`CLAUDE.md` records two separate things and they are the **same** thing:

- H3c-3 contains a 3-task refusal closing a live defect — `groups` + `between` +
  `fold` validates clean and produces empty folds per arm, because `fold_basis`
  answers over the whole roster — and **that refusal ships with H3d**.
- H3d, shipping before the cells work, must refuse the combination it cannot honour.

### Both halves reproduce. Measured, not argued

Probe, 15 units, arm `b` holding 3 and arm `a` holding 12, `by_attribute` assignment
on the `arm` column:

```
fold_basis(whole roster): 15 -> k=5 permitted
roster-wide fold sizes:   [3, 3, 3, 3, 3]
arm a per-fold:           [3, 3, 2, 2, 2]
arm b per-fold:           [0, 0, 1, 1, 1]      ← two empty folds
apportion 15 @ (0.8,0.2): [12, 3]
arm a test units: 3 of 12
arm b test units: 0 of 3                        ← a whole arm with no test partition
```

And the config that produces the first half **validates clean today** — probed through
`validate_config` on a real git repo with a real table source:

```
--- groups+between+fold k=5:   CLEAN
--- groups+between+holdout:    ['E-DATA-HOLDOUT-UNSUPPORTED']
--- holdout + fold together:   ['E-DATA-HOLDOUT-UNSUPPORTED']   (only — no exclusion check)
--- holdout: {} (empty):       CLEAN                            (the truthiness hole)
--- holdout malformed:         ['E-DATA-HOLDOUT-UNSUPPORTED']   (only — no envelope closure)
--- {kind: holdout} repeat:    ['E-REPL-KIND']
```

### The recommendation: refuse, and refuse both under one code family

**Refuse, not disclose.** The disclosure route would be `allocation.json` recording a
truthful `train`/`test` membership that a reader would have to cross against the arms
list by hand to see the imbalance — the silently-wrong class. The repo's own
precedent (`E-DATA-WEIGHT-CONTRAST`, `E-DATA-CLUSTER-CONTRAST`,
`E-DATA-ALLOCATION-CONTRAST`, `E-DATA-ASSIGN-BLOCKED-CLUSTER`) is to refuse a
*combination* while honouring both *declarations*, and to route it.

**One refusal, because the fault is one fault.** "A roster-wide evaluation split
beside a cell structure" is knowable from `data.units.allocation` /
`sweep.groups` / `replication.repeats` / `data.units.holdout` alone, before any roster
resolves. Two codes for the two split kinds is defensible (`E-DATA-HOLDOUT-CELLS`,
`E-REPL-FOLD-CELLS`) — one check site is not negotiable, since a second site is how the
two answers come to disagree.

**H4a's ruling applies directly and is the reason to do both at once:** *"both wrong
the same way" beats "one right, one wrong, indistinguishable"*, and the test is not
whether two things differ but whether a reader can tell. H3d shipping a holdout that
refuses cells while `fold` silently mis-partitions them is exactly the
indistinguishable case.

**The two false present-tense claims, named:**

- `experimental-designs.md:123` — *"folds and holdouts are drawn **within** each cell"*.
  False for `fold` today; H3c-3-SCOPING § 3 records it as "No" for folds and
  "honestly covered" for holdouts only because the whole block is `NOT BUILT`.
  **H3d makes the holdout half false too** unless the refusal ships with it.
- `reference.md` § A fixed holdout split, fourth interaction — *"Under `allocation:
  between`, the split happens within each cell"* — same, and it names the failure it
  is preventing in its own next sentence.

**Cost of the refusal against the outside evidence: zero. Re-verified.** All nine
configs in `docs/feasibility-llm-growth-studies.md` declare one roster,
`allocation: within`, no `sweep.groups`, and `seed` or `batch` repeats — the analysis's
own § Executability says so in the sentence beginning *"The machinery built most
recently unblocks none of them"*, listing `sweep.groups`, `allocation: between`,
`assign`, `cluster_by` and `fold` as declared by none of them.

**And it makes no documented design unrunnable.** H3c-3-SCOPING checked this and I did
not re-derive it: `experimental-designs.md` declares `allocation: between` in three
sections and a `fold` repeat in two, and **no section declares both**.

### Scoping the H3c-3 refusal as part of H3d

H3c-3-SCOPING § 5 puts the refusal at "3 tasks of the 17" — its own task 1 (documents),
task 6-as-a-refusal, task 10-as-a-refusal. **Merged with H3d's own cell refusal it is
one task, not four**, because the documents pass, the check site and the
`spec-defects.md` entry naming H3c-3 as the owner of the retirement are shared. That
is task 7 below, and the saving is the single largest structural finding in this
document.

---

## 6. Traps — re-measured

### Trap 1 — the denominator. Verified, sharpened, and one worry retired

**Build fact.** `runner.attrition` computes `handed = keys` (the whole roster it was
given) when `fold_members is None`, and returns `resolved = len(handed)`,
`failed = len(handed) - len(completed) - len(ineligible)`. Under a holdout with no
narrowing, **every training unit lands in `failed`** — it is handed out, records
nothing, and is neither completed nor skipped. That is the old scoping's trap 1 and it
is exactly right.

| Site | Today | Under a holdout |
|---|---|---|
| `attrition` → `n.resolved` / `n.failed` | `len(keys)` on whatever roster `_cond_roster` resolved | Must receive the test-narrowed roster. Narrow at the call site — `_cond_roster`'s own single-authority argument, which `attrition`'s docstring restates ("does not re-derive that narrowing itself, and must not") |
| `cli`'s `W-DATA-INELIGIBLE` | `ineligible / resolved` | Follows automatically; needs a test, not a change |
| `execute_plan`'s `max_failed_fraction` | `resolved = len(units)` on the **outer, un-narrowed** `units` | **Wrong by 1/frac.** A 0.2 holdout over 240 divides at most 48 possible failures by 240 — the guard fires at five times the declared threshold, in the direction of not firing |
| `provenance.units.n`, `units_hash` | `len(roster)`, whole roster | **Stay whole-roster**, and say so in a comment. They are the roster's identity, not a metric's denominator |

**One worry the old scoping did not raise and which I checked and can retire:**
`runner._counts` computes `effective` (Kish) and `clusters` over the **completed**
units, not over the passed maps — its own docstring argues the point ("a df is over the
units the interval was computed from"). So narrowing the roster does **not** leave a
whole-roster Kish size beside a test-partition `n`. `cli`'s `resample_strata` and
`clusters` maps are likewise built key-indexed over the whole roster and consumed by
key, so surplus entries are inert. **Verified: the weighted and clustered figures are
holdout-safe by construction.**

### Trap 2 — the scope gate is the inverse of the fold rule. Verified unchanged

`runner.execute_plan:572` still reads `elif execution.scope in ("run", "condition"):
step_units = None`. A holdout must not take that branch;
`experimental-designs.md` § Cross-validation supplies the sentence
(*"Condition-scoped fitting is right for a fixed holdout and wrong for
cross-validation"*) and `reference.md:1464` supplies the other half (*"A `holdout` does
not raise, because its split is fixed for the whole run"*). Mutual exclusion makes the
fold branch unreachable under a holdout — **assert it**. Verified verbatim.

### Trap 3 — the seed. Verified, and the spec-defect entry is still open

`units._seed_from` still hardcodes `sha256(f"{digest}|folds")`. `assign_seed_for` is
still per-axis and reads `block["seed"]` under an axis name a holdout does not have.

`hashes._units_excluding_assign_seed` drops `assign.<axis>.seed` **and nothing else**,
so `design_digest` still canonicalizes `holdout.seed` — a pinned holdout seed moves
the digest every *other* auto derivation reads. `spec-defects.md:4888–4897` carries
this as an explicitly **open** half of a closed entry, naming its owner as *"the slice
that builds `data.units.holdout`"*. **Verified open at `78bb794`**, and it survived
`a2c106f`'s strike of ten falsified claims.

### Trap 4 — "read rather than re-drawn on resume" still has no reader. Verified

`OPERATION_COMMANDS` is unchanged; no `resume` command dispatches. H3d inherits the
contract paragraph and must not let the missing reader become an argument for
re-deriving.

### Trap 5 — where a zero-size test partition is refused. Verified

Mirror *Every arm draws units* exactly: reported for the unstratified, unclustered
draw only; a clustered or stratified draw is checked where the run performs it.

### Trap 6 — `resample` × `holdout`, which no charter anticipated

**The mechanics are already coherent; one validate-time warning is not, and no
document says anything at all.**

- **Does the draw see the holdout?** Yes, correctly and for free. `statistics.resample`
  draws over the collapsed per-unit table, which under a holdout holds only units that
  recorded — the test partition. `resample_strata` and `clusters` are whole-roster maps
  indexed by key, so the surplus training keys are never looked up. **No change owed.**
- **`W-STATS-RESAMPLE-CLUSTERS` is wrong in the direction of not firing.**
  `validate.py:5186` computes `groups = fold_basis(roster, cluster_by)` over the
  **whole roster** and compares it to `limits.min_clusters`. Under a `frac: 0.2`
  holdout the percentile interval actually rests on roughly a fifth of that many
  clusters. A run with 50 clusters and `min_clusters: 20` passes silently while its
  intervals rest on ~10 draws. This is the shape `CLAUDE.md` calls a check that cannot
  fail — here, one that can fail but has been aimed at the wrong denominator.
- **Nothing in the four documents connects the two.** § A fixed holdout split's
  interaction list names `fold`, `resolved`, clustering and cells, and stops.
  § Weighted samples names `fold`, `holdout` and `assign` as prior takers of
  `stratify_by` and says nothing about what a holdout does to a resample's `n`.
  **One sentence is owed**, and it belongs in task 1.

---

## 7. The payoff, stated honestly

**The charter's "unblocks 6 of 9" is a drift.** `docs/feasibility-llm-growth-studies.md`
§ Executability on this build says *"E1, E2, E3, E4, and E6 **validate completely
clean** once two things land: the plugin registry a resolver is looked up through, and
`data.units.holdout`."* Validate clean is not execute, and the two-things is not one.

**Measured on 2026-08-15 against `78bb794`:**

> H3d retires **one refusal that 6 of 9 configs hit** (`E-DATA-HOLDOUT-UNSUPPORTED`,
> E1–E6; the three shortcut configs declare `holdout: null`), and **zero experiments
> newly execute.** All nine still declare a resolver and still earn
> `E-DATA-RESOLVER-UNSUPPORTED`, which is H7b's. C1–C3 keep `E-DATA-WEIGHT-CONTRAST`
> on top of that.
>
> Under a **table-roster substitution the analysis does not itself make**: E1, E2 and
> E5 would validate clean and could run. **E3, E4 and E6 would validate clean and
> still cannot execute** — each reads its frozen compiled program through
> `io.reuse_from`, which the analysis's own § Executability records as *"no such
> method exists yet"*. So even the generous count is **three**, not six, and it rests
> on a substitution nobody has written.

**E5's "one correction of its own" is not a blocker, and I checked rather than
assumed it.** § Executability defers it to § E5 — Binary-output repeatability, whose
paragraph *"One condition is declared by leaving `sweep` out"* is the correction: a
present-but-empty `sweep` earns `E-SWEEP-EXPANDS-EMPTY`, and E5's YAML already drops
the key rather than overriding it. It is a config-level fix the analysis itself
prescribes and has already applied, not an unbuilt surface. E5's other two
requirements — `io.read_condition` at `summary` scope and an `Estimate` returned by a
`summary` step — are both built (`runner.py:504`, `artifacts.py:358`). So **three
stands.**

That is the same shape as H4a's honest number and should be written the same way, in
the feasibility analysis's dated section, with the commit pinned.

**One thing that genuinely did improve and is worth carrying:** H7a made a
**project-local template** possible, so the `llm_screen` template no longer needs an
installed plugin. The *resolver* and the *probe* still do. That narrows H7b's
remaining job for these configs to the two entry-point artifacts.

---

## 8. Decomposition — 19 tasks, and the seam to split them at

**Part A — refuse and declare. `E-DATA-HOLDOUT-UNSUPPORTED` stays alive throughout.**

| # | Task | Why separate |
|---|---|---|
| 1 | **Documents first.** Settle § 1's three under-specifications in `reference.md` — the `by_attribute` test-side literals, the `seed`/`strata` home in `allocation.json`, the holdout row in § What `auto` derives from plus its seed-refusal code. Mint every new `E-DATA-HOLDOUT-*` in § Errors. Add the two § Validation rows the five existing ones do not cover — the cells refusal and the empty-test-partition refusal. Add the **`resample` × `holdout` sentence** (§ 6 trap 6). Both consistency passes | `CLAUDE.md` requires it; five of these are things no document currently says |
| 2 | **Envelope closure one level in**: `data.units.holdout.{method, frac, from, stratify_by, seed}` in `LEAF_TYPES`, and rewrite `envelope.py`'s two `holdout`-stays-whole comments. Closes the `holdout: {}` hole as a by-product | `measurements.by`/`.collapse` and `resample.{method,n,stratify_by}` are the precedent, and `envelope.py`'s own comment argues **validate-shape-before-honour-values** as the reason `resample` was closed ahead of its refusal retiring |
| 3 | **`design_digest` excludes `holdout.seed`**, beside `_units_excluding_assign_seed`; close the open half of the `spec-defects.md` entry | One line, and it must land before any pin is reachable |
| 4 | **`_check_holdout`, declaration half A**: `method` enum, `frac` in (0, 1) under `random`, `from` required under `by_attribute`, fields meaning nothing under the other method (`E-DATA-ASSIGN-NO-DRAW`'s analogue), the seed pin | Declaration-only, reports with no roster. `_check_resample`'s docstring — which **enumerates its findings and says an eighth belongs in the list** — is the model |
| 5 | **`_check_holdout`, declaration half B**: `stratify_by` existence (the *Stratification attribute exists* holdout branch); the `holdout` × `fold` mutual exclusion | Different failure reason; the exclusion reads `replication` |
| 6 | **`_check_holdout`, roster half**: the `by_attribute` column resolving to exactly the two settled literals; *Holdout strata survive clustering* through the **fourth** `stratum_varies_within_cluster` call site — **and that function's stale two-row docstring corrected to four**; the unstratified/unclustered zero-size test partition | Needs a resolved roster; siting rule is trap 5's. Each of the three carries its own `roster is not None` guard, `_check_resample`'s stated convention |
| 7 | **The shared cells refusal**: `holdout` **or** `{kind: fold}` beside `allocation: between` / a non-empty `sweep.groups`, one check site, one code family; a `spec-defects.md` entry naming **H3c-3** as owner of the retirement; `experimental-designs.md:123` and § A fixed holdout split's fourth interaction marked honestly | § 5. **This is H3c-3's 3-task refusal and H3d's own, merged.** It is what stops H3d adding a second false present-tense cell claim, and it closes a defect that is live today |
| 8 | **`holdout.from`'s constant-column accessor**: `_holdout_constant_column`, its `CONSTANT_COLUMN_RULES` entry, its place in the documented severity ordering, and `validate.py:883`'s sentence re-checked | § 4. **Absent from the old decomposition entirely.** Two comments in `units.py` name it in the present tense |

**Part B — draw, narrow, record. The wholesale refusal retires at the end.**

| # | Task | Why separate |
|---|---|---|
| 9 | **`units.holdout_for`, construction 1 — unclustered**: `_apportion(len(roster), [1-frac, frac])` + one shuffle + consecutive slices, matching `assignment_for`'s `random` branch; `by_attribute` through `arms_of` with the two settled literals. Returns a plan object carrying `train`/`test`/`seed`/`strata` | The seam, isolated from every caller as `assignment_for` was |
| 10 | **Construction 2 — clustered**, through `_assign_whole_clusters_by_ratio` at `[1-frac, frac]`, plus `stratify_by` through `_stratum_groups` wrapped around either construction. **The bit-stability relation between 9 and 10 stated and pinned** | § 3. `_assign_whole_clusters_by_ratio` takes a non-optional `Mapping`, so this is genuinely a second path — and H3c-2's own experience is that a fixture cannot tell the two apart unless it is built to |
| 11 | **The holdout seed derivation**, its own digest suffix with the reason stated (not inherited from `_seed_from`'s `"\|folds"`); a pinned integer returned literally, `bool` excluded, matching `assign_seed_for` | A second thing to get wrong inside 9 |
| 12 | **Realize once in `cli.command_run`**; the one object handed to the runner narrowing and to `build_allocation_document`, never re-derived | `build_allocation_document`'s own docstring makes this argument for arms and it transfers verbatim |
| 13 | **Runner narrowing**: `io.units` = test, `io.units.train` = train, at run, condition, repeat and summary scope; assert the fold branch is unreachable under a holdout | Trap 2 — the inverse of a rule in the same function |
| 14 | **The denominators**: `_cond_roster`/`attrition` receive the test-narrowed roster at the call site; `max_failed_fraction` and `_units_failed_anywhere` likewise; `provenance.units.n`/`units_hash` explicitly stay whole-roster, with a comment saying why 240-here/48-there is not a bug | Trap 1, the item most likely to ship wrong |
| 15 | **`W-STATS-RESAMPLE-CLUSTERS` against the test partition**, not the whole roster | Trap 6. Under-warns by ~1/frac today, in the direction of not firing. Would be missed by any task scoped to `holdout` alone |
| 16 | **`allocation.json`**: the fourth key, the "both absent" gate (`if not group_axes: return None` → neither an assignment nor a holdout), the plan-not-roster signature, and the `seed`/`strata` home task 1 settled | § 1(b). `allocation_hash` needs no change — it canonicalizes whatever document it is handed, and its docstring already rules out a `holdout_hash` |
| 17 | **Retire `E-DATA-HOLDOUT-UNSUPPORTED`** — the loop's last entry, so the loop itself goes; re-check the `E-REPL-KIND` route now that it points at a built field; expect the finding-order flip and pin it (H3b task 8's experience). `REPL_DECLARATION_CODES` stays as it is, since task 5 sites the exclusion in `validate` rather than in `resolve_repeats` | Gated on the declaration changing the record, which 9–16 are what make true |
| 18 | **The owned prose sweep — 13 sites in `src/`, swept by claim rather than by file** (§ 9), plus `reference.md`'s `NOT BUILT` marker, its "Three declarations above are not yet built" → two, its `.holdout` inherits-the-same-treatment clause (task 2 discharges it), § E-CONFIG-KEY-UNKNOWN's "not among them only because the whole block is refused today", and `materialize.py`'s generated line gaining a shape comment the way its `measurements` sibling carries `{by: read_id, collapse: mean}` | **The old scoping's § 3 counted 4.** `CLAUDE.md`: three sweeps in one slice stopped one file short |
| 19 | **Regression and the reader-facing half**: a no-holdout run byte-identical to today (`fold_members=None`'s own oracle pattern); the six holdout-declaring feasibility configs validated under a table-roster substitution, with the honest count of § 7 written into the dated executability section; `experimental-designs.md` § Train-test holdout unblocked and § Mistakes core prevents re-checked | H3a's lesson. The reorder's claim needs re-measuring rather than restating |

### The split seam, and why it is at 8/9

**Recommend shipping Part A (tasks 1–8) and Part B (tasks 9–19) as two slices.**

- **It has direct precedent and the code states it.** `envelope.py`'s own comment
  argues that `resample` was closed one level in *before* its wholesale refusal
  retired, deliberately, "because the slice that honours a block needs the shape
  checked before it can read the values."
- **It keeps the wholesale refusal alive across the seam**, which is what avoids the
  hazard `_check_resample`'s docstring admits to: *"for two tasks a declared `resample`
  validated clean here before it changed any interval."* A `holdout` that validates
  clean and partitions nothing is a silent no-op on a declaration that changes the
  record — the exact failure `_check_unimplemented` exists to prevent.
- **It delivers the live-defect fix first.** Task 7 closes the `groups` + `between` +
  `fold` empty-fold defect, which is live today and which no other scheduled slice is
  going to close sooner.
- **Part A is 8 tasks with no runner, no `cli`, no artifact changes.** Part B is 11 and
  touches four modules. Neither half is past twenty.

**The cost of the seam, named rather than discovered.** `validate` **collects**, so
every check Part A adds — tasks 4, 5, 6, task 7's holdout half, task 8's raise — is
exercised against configs that *also* earn `E-DATA-HOLDOUT-UNSUPPORTED`, and their
tests will pin finding lists containing it. **Task 17 retires that code, so every one
of those tests changes when Part B lands.** Two consequences: task 17 is larger than
its one cell suggests, and shipping Part A alone means Part B inherits a test-revision
pass over the whole of Part A. Mitigate it by requiring **each Part A test to assert
positively that its new finding appears *alongside* the wholesale refusal, not instead
of it** — an assertion that survives the retirement as a one-line deletion rather than
a rewrite. The split is still right on its merits (live-defect-first, `envelope.py`'s
own validate-shape-before-honour-values precedent, and the refusal staying alive across
the seam); this is its price, not an argument against it.

If the slice ships whole instead, task 17 is the ordering constraint: **nothing may
retire the wholesale refusal before 9–16 land**, and tasks 1–8 must not make a
declared holdout validate clean while it is still read by nothing.

---

## 9. The owned prose sweep — 13 sites, classified

The old § 3 named "three prose blocks plus `envelope.py`'s fourth". Grepped
`holdout` across `src/` and classified every hit as *asserts the current absence*
(owned; false the moment H3d lands) or *forward reference* (fine as written).

**Owned — 13:**

| Site | The claim it makes |
|---|---|
| `validate.py:3137` | The tuple-loop entry itself |
| `validate.py:2995` | "two `data.units` sub-fields — `holdout` and a `resolver` source — are still read by nothing" → one |
| `validate.py:2520` | "`data.units.holdout.stratify_by` halves belong to the slices that build those blocks" → discharged by task 6 |
| `validate.py:883` | "`cluster_by`, `weight_by`, and `holdout` are not read by `resolve_units` at all" → false once task 8 lands |
| `artifacts.py:230–235` | "**`holdout` is never written here.**" |
| `cli.py:1509–1510` | "`holdout` is never in this build's document at all" |
| `cli.py:2501` | The `None`/`None` pairing comment at the provenance write site — the gate changes |
| `cli.py:1347` | "`holdout` and `assign` **will** each read the same attribute under their own" — future tense becomes present |
| `envelope.py:30–31` | "`holdout` stays whole for now… and H3d closes it" |
| `envelope.py:47–50` | "a misspelled… `methodd` in `holdout` is reported by no check in this build" |
| `units.py:312–316` | "**`holdout.from` still is not** [reachable]" |
| `units.py:720` | "**`holdout.from` is not reachable through this registry today**… nothing in this task builds one" |
| `materialize.py:126` | The generated `holdout: null # optional single fixed train/test split` line and its comment |

**Forward references, fine as written — 8:** `artifacts.py:175` and `:309`
(`holdout_hash` ruled out, correctly and in advance), `replication.py:28` (the
`E-REPL-KIND` route, already true), `stats.py:770` and `:835`, `validate.py:1034`,
`:1926`, `:2540`, `generators/template.py:42` (example prose in a generated file).

**Plus five document sites** already listed under task 18.

---

## 10. What is NOT in H3d — re-verified against the old § 7

- **Drawing the split within each cell.** H3c-3's, by task 7's refusal. Unchanged.
- **`resume`.** H9's. No reader exists; H3d builds none. Unchanged.
- **Three-way splits.** § A fixed holdout split is two partitions; the feasibility
  analysis routes its `dev` split into `step02` through `derive_seed("dev-split")`
  over `io.units.train`, needing nothing from core. Unchanged.
- **`statistics.null_test`.** Still `E-STATS-NULLTEST-UNSUPPORTED`, still unbuilt.
  **`statistics.resample` is no longer on this list** — H4a landed it, and H3d's only
  business with it is task 15 and one documentation sentence.
- **`E-DATA-RESOLVER-UNSUPPORTED`.** H7b's. The feasibility configs run *as written*
  only after it, which is § 7's whole point.
- **A `holdout_hash`.** Ruled out by `artifacts.allocation_hash`'s docstring.
- **Anything in `sweep.yaml`. Checked, not assumed.** `reference.md:807` gives
  `partitions` to a **`fold`** level ("the unit keys in each fold's train and test
  side"); `reference.md:1316` sends a holdout's realized membership to
  `allocation.json` and nowhere else. The two documents agree, so a holdout writes
  no `sweep.yaml` key. Worth stating because the adjacency is live — H3c-3-SCOPING's
  own task 12 is `sweep.yaml`'s `partitions` per cell — and a task-9 implementer will
  otherwise re-derive it.
- **Any `limits.min_units_per_cell` warning.** Specified, unbuilt, carried by an open
  `spec-defects.md` entry that leaves the naming to whichever slice builds it. H3d does
  not, since a thin *test* partition is refused outright by task 6.
- **Interactions with `data.units.measurements` or `weight_by`.** Neither partitions.
  **One correction to the old scoping here:** `measurements` does touch H3d after all,
  through `holdout.from`'s constant-column rule (§ 4). The *collapse* still runs before
  any split, which is what the old claim got right.
