# H4b-2 — clusters through contrasts, and retiring `E-DATA-CLUSTER-CONTRAST` — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a `data.units.cluster_by` declared beside a comparison stops being refused. The delta's
interval is computed by a construction that reads the cluster as the draw, the `method` string says
so, and the cluster count travels beside `n_paired` as `n_paired_clusters`.
`E-DATA-CLUSTER-CONTRAST` is retired.

**The payoff, stated as the spec's decision 7 fixes it: H4b-2 unblocks ZERO configs.** No config in
`docs/feasibility-llm-growth-studies.md` declares `cluster_by`, so the
*no-remaining-core-side-blocker* count stays **six** and the executable count stays **three**.
Neither moves. A retired refusal is not an execution. What this slice is worth instead is four
things, none of them a number in that table: a live defect closed (the zero-width stratified paired
draw), a documented rule given code (§ Statistical reporting's `_clustered` suffix rule has no
paired construction behind it), one refusal retired / one re-owned / one minted, and one
build-hedged specification sentence resolved.

**Architecture.** Two paired clustered constructions, one new refusal, and one membership mapping
threaded down three signatures.

- **The *t* path** is a column contrast with no `statistics.resample` declared.
  `stats.paired_t_over_units_clustered(diffs, labels)` is new, and it **delegates to
  `t_over_units_clustered`** exactly as `paired_t_over_units` delegates to `t_over_units` and
  `weighted_paired_t_over_units` to `weighted_t_over_units`. It is called from two places:
  `cli._comparison_step_blocks`' raw interval and `correction._corrected_bounds`' corrected one —
  and `correction.py` is the **first** of the two written, exactly as H4b-1's spec correction 2
  found for the weighted form.
- **The percentile path** is a column contrast under a declared `resample`. There is **no new
  function**: `stats.paired_percentile_of_derived` gains a `clusters` parameter and emits a third
  `method` string, `paired_percentile_over_units_clustered`, the same way it already emits
  `paired_percentile_over_units` and `weighted_paired_percentile_over_units`. Its draw becomes one
  uniform shape — a list of stratum groups, each holding drawable key-lists — which is
  RNG-identical to today's two branches and is what makes the clustered draw compose with `strata`
  for free.
- **A weighted clustered contrast is refused, not built.** `E-DATA-WEIGHT-CLUSTER-CONTRAST` is
  minted as a documented narrow refusal carrying a § Errors row and a § Validation row. H4c
  inherits the composition.
- **A derived metric never reaches a clustered contrast at all.** `stats.summarize_step` raises
  `E-DATA-CLUSTER-DERIVED` and drops the whole `derived` mapping under `cluster_by`, so
  `_comparison_step_blocks`' derived branch is unreachable there — which is the measured fact
  decision 5's record-shape asymmetry rests on, and it is pinned in task 4.

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. No new dependency, no new module. The
changes land in `src/publishable/stats.py`, `src/publishable/cli.py`,
`src/publishable/correction.py`, `src/publishable/validate.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `docs/feasibility-llm-growth-studies.md`, and the test modules
`tests/test_stats.py`, `tests/test_cli.py`, `tests/test_validate.py`, `tests/test_correction.py`.

**Spec:** `docs/superpowers/specs/2026-08-17-clustered-contrasts-design.md` — read it beside this
plan. Its § Corrections against the code, appended by this plan's author, records the four places
where the code disagreed with it.

**Measurement this plan argues from:** `docs/superpowers/H4b-2-SCOPING.md`, taken 2026-08-17
against `main` at `001ed9f`. Every signature, guard, error code, record key and file path below was
**read from the source named beside it at `82310b9`** (this branch's head), not carried from the
scoping. **Nothing is cited by line number.**

**Task count: 18**, the spec's § Task decomposition in its grain.

---

## Sequencing — the spec's seven ordering constraints, and where each is enforced

Presented **in execution order**, which is not numeric order. Each task states the constraint it
depends on in its own brief, because an implementer sees only their own task.

**Execution order: 1 → 4 → 2 → 3 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18.**

| Constraint | Why, and where it is enforced |
|---|---|
| **Task 1 before 6–9 and 11** | The composition decision fixes whether two constructions exist or four, and how many cells task 11's branch has. Building first bakes the answer in by omission |
| **Task 4 before task 2** | Decision 4 gates decision 5: whether a clustered contrast can carry an **unsuffixed** `method` decides whether the no-`clustered_by`-sibling argument holds. Task 4 rules *re-word and re-own*, so the asymmetry holds cleanly and task 2 can document `n_paired_clusters` without a `clustered_by` sibling |
| **Task 3 before 7** | The degenerate-draw refusal lives **inside** the percentile construction, over the same uniform draw shape task 7 builds |
| **Task 2 before 13** | A record key must exist in a document before code writes it |
| **Task 6 before 12** | `correction._corrected_bounds` is `paired_t_over_units_clustered`'s **first** caller |
| **Task 14 last of the code tasks** | A refusal is deleted only after everything it stood in for exists, and task 14 alone carries the `validate`-clean and `run`-through halves |
| **Task 15 must not touch the development record** | `H4b-SCOPING.md`, `H4b-2-SCOPING.md`, `spec-defects.md`'s dated entries and both H4b specs are evidence, not text to repair |

### Three deviations from the spec's grain, each argued

**(a) § Statistical reporting's de-hedged "does not compose" sentence lands in task 8, not task 1.**
The spec's task 1 pairs the decision with the sentence. **A sentence and a guard are one claim seen
from two ends**: de-hedging the sentence while no code refuses the combination would make the
specification describe a behaviour core does not have, for the seven commits between tasks 1 and 8.
Task 1 records the ruling and proves the identifier free; task 8 ships the emit, the § Errors row,
the § Validation row and the sentence **in one commit**. This is H4b-1's own deviation (b), one axis
over.

**(b) `E-DATA-CLUSTER-DERIVED`'s row wording lands in task 15, not task 4.** The spec's task 4 says
"re-word its § Errors row … and re-own the code by name". That row is also on task 15's
surviving-citation list. A row edited in task 4 and swept again in task 15 is one claim in two
commits, and the second would have nothing to do. **Task 4 fixes the owner and pins the fact the
ruling rests on; task 15 is where every surviving wording lands, as one sweep.**

**(c) Task 10 threads `clusters` *and* wires the *t* branch; task 11 wires the percentile branch and
asserts all six cells.** The spec's task 10 is "thread" and task 11 is "the `method`-selection
branch". A parameter threaded and unused is a task with nothing to test, and this repo has shipped
"a seam named in the brief and instantiated by no fixture" twice. So task 10 threads the mapping and
selects the *t* construction (cells 1, 3, 5), and task 11 selects the percentile `method` (cells 2,
4, 6) and asserts the whole six-cell table in one parametrized test. Nothing is dropped and nothing
added.

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced, because an
implementer sees only their own task brief.

**Commands.** Tests `uv run pytest` — takes about two minutes; **run it in the FOREGROUND** and wait
for it. Lint `uv run ruff check .`. Format `uv run ruff format .`. Types `uv run mypy`. All four must
pass before a commit.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this
repo wrote the bare form where it meant `--check` and rewrote 67 files. **The repo is format-clean:
`uv run ruff format --check .` reports `80 files already formatted`. Keep it that way.**

**Baseline, measured 2026-08-17 in the foreground at `82310b9`:** `uv run pytest -q` →
**2159 passed, 1 skipped, 2 xfailed**. `uv run mypy` → `Success: no issues found in 45 source
files`. A task that leaves the count below its own additions has broken something. Every task states
its expected count.

**`E-DATA-CLUSTER-CONTRAST` stays alive until task 14.** Every test written before task 14 asserts
its own finding **alongside** that code, never instead of it, and **never on a total code set**
(`codes(path) == {...}`) — so task 14 is a one-line deletion per test rather than a rewrite. The
pre-existing tests that *do* assert a total set are named in task 14 by test name and are task 14's
to edit, nobody else's.

**Tasks 6–13 test by DIRECT CALL, because `validate` gates `run`.** `cli.command_run` calls
`validate_config` and returns `EXIT_WRONG` on any error (`if doc is None or c.has_errors: return
EXIT_WRONG`), and `E-DATA-CLUSTER-CONTRAST` is an error — so **no clustered contrast reaches
`_comparison_step_blocks` through `run` until task 14 retires the refusal.** Tasks 10–13 therefore
call `cli._comparison_step_blocks`, `cli._compute_vs_baseline` and `cli._compute_declared_contrasts`
directly, which `tests/test_cli.py` already does at
`test_a_comparison_reads_its_own_condition_not_condition_zero`,
`test_compute_declared_contrasts_within_is_narrowed_by_the_test_partition` and
`test_compute_vs_baseline_roster_argument_never_affects_the_auto_generated_family`. Tasks 6, 7 and 9
test `stats` directly and task 12 `correction` directly, as those modules' test files already do
throughout. **Task 14 carries the `validate`-clean and `run`-through halves.**

**A clustered interval that is merely wider proves NOTHING.** Under positive within-cluster
correlation a cluster-robust interval comes out wider whatever df it uses — `t_over_units_clustered`'s
own docstring says so. **Only the number is evidence.** Sixteen unfailable checks have been found in
this repo's statistics alone, and *"a cluster fixture where correct and buggy cluster counts were
both 3"* is a documented instance. Every fixture in this plan is sized so a wrong clustering gives a
**different number**, and every task states the two numbers.

**The delta is IDENTICAL clustered and unclustered.** Clustering moves the variance, not the point
estimate: the fixture's delta is 6.3333… under every reading. This is the single biggest difference
from H4b-1, where the weight moved the delta (6.0 → 8.0) and a `delta` assertion was itself
discriminating. **Here any test asserting only `delta` is blind to clustering entirely.** The
discriminators are the **half-width**, the **`method` string** and **`n_paired_clusters`**, and
nothing else.

**`cohens_d` does not move under a cluster either.** `cohens_dz` is computed over the differences and
§ Statistical reporting mints no clustered *d*. So H4b-1's three-way move-together obligation becomes
a **different** three here — **interval, `method`, `n_paired_clusters`** — and copying H4b-1's
"value, interval and size" wording would assert something false.

**`validate` collects rather than aborting.** A refusal elsewhere never makes a later check
unreachable. **Four readers in this repo have got this wrong, two of them in H4b-1 alone.** Do not
infer unreachability from a refusal; build the config and look at what `validate` *reports*, in full.

**Mutation discipline, every task.** Apply the named mutation to the file it names. Run the named
test. Confirm it **FAILS**. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert
**by editing the file back in place** — **never `git checkout -- <file>`**, which destroys
uncommitted work and has been mistaken for a revert twice in this repo. Confirm the test **PASSES**
again, and verify the revert by *behaviour*, never by `git status`. **Every mutation runs against the
full, unfiltered suite in the foreground** — H4b-1 produced a false blind-spot claim from a
self-chosen subset, and a re-reviewer who backgrounded a run stopped with a mutation possibly still
applied.

**A mutation is a claim too.** Before believing "this mutation must fail test X", read the *body* of
test X and check the two branches can actually produce different results. **H4b-1 shipped five blind
mutations, one provably unbuildable.** This plan states, for every mutation, why its branches differ
— and task 6 names a mutation that is **blind by arithmetic** so nobody prescribes it later. Where a
mutation cannot discriminate, this plan says so and prescribes the fixture that would.
**And a mutation's silence is evidence about the TESTS, not about the code.**

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "Statistical reporting"), **never by line number**. **No positional locators**
("the row above", "further up"): name what a sibling row *does*. **No counts in prose or comments**
and **no call-site enumerations**: state what a set *is*. **A build fact is dated and pinned to a
commit where it is true.** **Prefer deleting a claim to rewriting it** — a rewrite invents, a
deletion cannot. **When you edit a docstring, re-read the whole one**: ten Majors across H4b-1's four
review batches were stale quantifiers or claims left standing over changed material. After any
`*.md` edit run the mechanical pass: every relative link and `#anchor` resolves, no two headings in a
file share an anchor, every table row matches its header's column count and none is empty, no
trailing whitespace, tab or invisible unicode — skipping fenced code blocks in all of them.
**Never filter the output of a sweep whose job is to find a string — filter the FILE LIST**, and name
the four documents explicitly, since the development record is tracked and `*.md` no longer means
what it used to.

**§ Errors carries one row per code, covering every emit site** — not one row per site. A
diagnostic's unit of work is every site that raises *or* reports it.

**The four normative documents LEAD; `src/` follows.** `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`. Where they and the code disagree, **the document
changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. The cross-document
pass governs those four **only** — never the development record under `docs/superpowers/`, where a
correction is appended rather than retro-edited. `spec-defects.md` is the one exception: a closed gap
is **struck** there rather than left to mislead.

**Do not touch the worked example.** `cohort-pilot` declares no `cluster_by`, so no clustered key
belongs in § The two files' `run.yaml`, in § Statistical reporting's fenced `results:` block, or in
any of the worked example's intervals — which `CLAUDE.md` § The worked example says were checked
numerically and **must not be narrowed back**. The clustered record shape gets its own fenced example
in § Contrasts.

**§ The one config file's declaration count must not move.** It reads *"**One** declaration above is
not yet built"* — `statistics.null_test`, H4d's. Retiring or minting a *combination* refusal is not
retiring or adding a declaration, and `_check_sweep`'s own comment makes that placement argument for
both of its codes. Likewise **no row moves in any `Status`-carrying table**: `tests/test_cli.py`
asserts set equality between the document's `NOT BUILT` command rows and `cli.NOT_BUILT_COMMANDS`.

**`tests/conftest.py` already has** an autouse `os.environ` restore, an opt-in `registries` fixture
and an opt-in `installed` distribution fixture. **Do not add duplicates, and do not add a second
autouse fixture of any kind.** No task in this slice needs `registries` or `installed`.

---

## The discriminating fixture, stated once because six tasks share it

**A weakened copy of this fixture is how this repo has produced sixteen checks that could not fail.**
No later task may substitute a fixture that fails any of the four constraints below.

1. **Not singleton clusters** — one unit per cluster makes `clusters − 1` equal `n_paired − 1`, so
   the clustered and unclustered *t* forms coincide **exactly** and every assertion passes under a
   mutant that ignores membership entirely.
2. **Correct and buggy cluster counts must differ** — the documented "both 3" failure.
3. **Strong within-cluster correlation in the differences** — otherwise CR1 ≈ the IID variance and
   only the df moves, so two independent mutants cannot fail differently.
4. **Unequal cluster sizes**, for the percentile form.

**The fixture: 12 units in 3 clusters of sizes 2, 4, 6**, with per-unit differences `1.0 ×2`,
`5.0 ×4`, `9.0 ×6` against a baseline side of zeros. Delta = 76 / 12 = **6.3333…** — the same number
under every reading below.

| unit | cluster | `of` value | `against` value | difference |
|---|---|---|---|---|
| `u00`, `u01` | `a` | 1.0 | 0.0 | 1.0 |
| `u02`–`u05` | `b` | 5.0 | 0.0 | 5.0 |
| `u06`–`u11` | `c` | 9.0 | 0.0 | 9.0 |

Half-widths, computed against `t_over_units_clustered`'s own CR1 scaling
(`G/(G−1) · Σ_g S_g² / n²`, df = `G − 1`) and verified numerically at `82310b9` by calling the
shipped `t_over_units_clustered` and `t_over_units`:

| What computes it | Half-width |
|---|---|
| **Correct** — CR1 meat, df = 2 | **8.763214143637903** |
| Mutant: CR1 meat, df = `n − 1` = 11 | 4.482747155375303 |
| Mutant: IID variance, df = 2 | 3.867797171498907 |
| Mutant: cluster count miscounted as 4 | 6.110995345525882 |
| `paired_t_over_units`, the unclustered form | 1.9785385229565593 |

**Five distinct answers, each separated by a margin no rounding can produce, and the correct one is
the extreme of no single dimension** — so an assertion on the number discriminates all four failure
modes, which an assertion on "is it wider" does not.

For the **percentile** form the same 2 / 4 / 6 sizes make a replicate's pooled row count vary between
**6 and 18** while a unit-drawing mutant returns a fixed **12**. That row count is itself an
assertable discriminator, and **it must be asserted, not inferred from the interval.**

---

## Identifiers and record keys this slice touches

| Name | What it is | State at `82310b9` | Task |
|---|---|---|---|
| `stats.paired_t_over_units_clustered` | function and `method` string | **absent from `src/`**; licensed by § Statistical reporting's suffix rule | 6 |
| `paired_percentile_over_units_clustered` | `method` string only — no new function | **absent from `src/`**; licensed by the same suffix rule | 7 |
| `stats.paired_percentile_of_derived(..., clusters=)` | parameter | absent | 7 |
| `n_paired_clusters` | record key on a contrast entry | **minted here** | 2 (documented), 13 (emitted) |
| `correction.Member.clusters` | field | absent | 12 |
| `E-DATA-WEIGHT-CLUSTER-CONTRAST` | refusal | **free at `82310b9`** — proved in task 1 | 1 (ruled), 8 (minted) |
| `E-DATA-CLUSTER-CONTRAST` | refusal | 1 emit + 1 § Errors row + 1 § Validation row + 1 sibling § Validation row citing it by name + 3 `src/publishable/validate.py` comments + 1 `stats.summarize_step` docstring + 1 `E-DATA-CLUSTER-DERIVED` § Errors row + 1 § Statistical reporting sentence + 7 `tests/test_validate.py` assertion lines + 1 `tests/test_cli.py` row locator | 14 (retired), 15 (residue) |

**No new `method` table rows.** § Statistical reporting's suffix sentence is generic over the whole
contrast table — *"each of the **unweighted** forms above takes a `_clustered` suffix"* — so both new
spellings are **already licensed**, and `efa13bc` just repaired the opposite mistake by narrowing a
quantifier rather than enumerating. **Ruled explicitly, so no later task helpfully adds them:** the
two new forms get no rows of their own.

---

## Task 1: rule the weight × cluster composition, and prove the identifier free

**Files:**
- Modify: `docs/superpowers/spec-defects.md`

**Interfaces:**
- Consumes: `validate._check_sweep`'s `E-DATA-CLUSTER-CONTRAST` emit, guarded by
  `comparisons > 0 and isinstance(cluster_by, str) and cluster_by` — read in
  `src/publishable/validate.py`; `reference.md` § Statistical reporting's sentence *"The `_clustered`
  suffix does not compose with either weighted form in this build"*.
- Produces: the ruling every construction task depends on — **two paired clustered constructions,
  not four** — and the reserved identifier `E-DATA-WEIGHT-CLUSTER-CONTRAST`, which tasks 8, 11 and 14
  spell exactly that way.

**This task decides, and builds nothing.** `H4b-SCOPING` § 10 assigned the weight × cluster refusal
to **H4b-1 by name**; H4b-1 did not mint it, so a `weight_by` + `cluster_by` + comparison config earns
`E-DATA-CLUSTER-CONTRAST` alone today and the specification's *"in this build"* hedge has only that
refusal enforcing it. Two answers are defensible: build
`weighted_paired_t_over_units_clustered` and `weighted_paired_percentile_over_units_clustered`, or
mint a narrower refusal.

**Ruling: mint the refusal. Do not build the weighted clustered pair.** Three grounds:

1. **Minting is the house move.** H3a minted `E-DATA-WEIGHT-CONTRAST`, H3b minted
   `E-DATA-CLUSTER-DERIVED`, both for exactly this shape — a combination reachable because a broader
   refusal was retired.
2. **The composition unblocks nothing measurable.** No config in
   `docs/feasibility-llm-growth-studies.md` declares `cluster_by` at all.
3. **It doubles the fixture burden on the dimension where a wrong choice hides best.** The weighted
   clustered df comes from the **cluster count**, not from Kish's effective size — and the two
   coincide in any fixture not built to separate them, which is the *Kish and clusters coinciding*
   trap.

**Two constraints on the mint, both load-bearing.** It is a **documented narrow refusal carrying both
a § Errors row and a § Validation row**, not a `-UNSUPPORTED` build-family code — `CLAUDE.md`
§ Misreadings draws that distinction and it decides whether the code outlives this slice. And
**§ Statistical reporting's "does not compose … in this build" sentence loses its hedge and gains a
link to the new code in the same commit as the emit** (task 8), because a sentence and a guard are
one claim seen from two ends.

- [ ] **Step 1: Prove the identifier is free, by sweeping the FILE LIST rather than filtering
      output.**

```
grep -rn "E-DATA-WEIGHT-CLUSTER" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ tests/
```

      Expected: **no hits, exit 1.** If it hits anything, stop — the identifier was minted twice
      under two spellings, which is exactly what naming it here prevents.

- [ ] **Step 2: Prove the sweep can fail.** Run the identical sweep shape over the identical file
      list for a string known to be present:

```
grep -rn "E-DATA-CLUSTER-CONTRAST" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ tests/
```

      Expected: **many hits.** A sweep that cannot fail is a comment, not a measurement — and this
      is the whole of this task's mutation, stated at Step 4.

- [ ] **Step 3: Record the ruling.** Append to `docs/superpowers/spec-defects.md`:

```markdown
## RULED by H4b-2 task 1 — the weight × cluster combination is refused, not built

`docs/superpowers/H4b-SCOPING.md` § 10 assigned the `weight_by` × `cluster_by` × comparison refusal
to **H4b-1 by name** — "not to whichever ships first". H4b-1 did not mint it, and
`E-DATA-WEIGHT-CONTRAST` was retired in the same slice, so at `82310b9` such a config earns
`E-DATA-CLUSTER-CONTRAST` alone and `reference.md` § Statistical reporting's *"The `_clustered`
suffix does not compose with either weighted form in this build"* is enforced by nothing else.

**Ruled: mint `E-DATA-WEIGHT-CLUSTER-CONTRAST`, a documented narrow refusal carrying a § Errors row
and a § Validation row.** Not a `-UNSUPPORTED` build-family code: this refuses a *combination*, which
is what decides whether it outlives the slice that minted it. The grounds are that minting is the
precedent H3a and H3b both set for a combination made reachable by retiring a broader refusal; that
no config in `docs/feasibility-llm-growth-studies.md` declares `cluster_by`, so the composition
unblocks nothing measurable; and that a weighted clustered *t* takes its df from the **cluster
count** rather than from Kish's effective size, a distinction invisible in any fixture not built to
separate the two.

**H4c inherits the composition itself**, alongside the unpaired clustered forms.

**Ruled by:** H4b-2, task 1. **Built by:** H4b-2, task 8.
```

- [ ] **Step 4: The mutation, and why this task has no test.** A ruling recorded in prose has no
      behaviour to assert against, and adding a test for `spec-defects.md` would create a second
      source of truth for build state — the same argument H4b-1's task 1 recorded for its own filing.
      **The mutation is on the sweep, which is this task's only measurement:** Step 2's control *is*
      the mutation, and it must return hits where Step 1 returns none. **The fixture that would test
      the ruling itself is task 8's** — a config declaring `weight_by`, `cluster_by` and a baseline,
      named there — and it cannot be written until the code exists.

- [ ] **Step 5: Run the four gates.** `uv run pytest` → **2159 passed, 1 skipped, 2 xfailed**
      (unchanged; this task adds no test). Then `uv run ruff check .`, `uv run ruff format --check .`
      (80 files), `uv run mypy`.

- [ ] **Step 6: Commit.**

```bash
git add docs/superpowers/spec-defects.md
git commit -m "docs: rule the weighted-clustered composition — mint the refusal, do not build the pair"
```

---

## Task 4: rule `E-DATA-CLUSTER-DERIVED`'s fate, and pin the fact the record shape rests on

**Runs second, before task 2** — the spec's ordering constraint *task 4 before task 2*. Decision 4
gates decision 5: if a clustered contrast could carry an **unsuffixed** `method`, the argument
against a `clustered_by` record key collapses, because that argument is precisely that the
`_clustered` suffix already discloses the clustering.

**Files:**
- Modify: `docs/superpowers/spec-defects.md`

**Interfaces:**
- Consumes: `stats.summarize_step`'s `E-DATA-CLUSTER-DERIVED` raise, guarded by
  `if clusters is not None and seed is not None:` over a non-empty `drawable` — read in
  `src/publishable/stats.py`; `cli._comparison_step_blocks`' `is_derived` branch, selected by
  `metric_key in of_derived or metric_key in against_derived` — read in `src/publishable/cli.py`;
  `tests/test_cli.py::test_a_clustered_derived_metric_is_refused_rather_than_drawn`, which already
  asserts `set(aggregated) == {"pred"}` on a clustered run whose template derives `total`.
- Produces: the measured fact tasks 2, 11 and 13 rest on — **no derived metric survives under
  `cluster_by`, so no clustered contrast entry can carry an unsuffixed `method`** — and the
  re-ownership of `E-DATA-CLUSTER-DERIVED` to H4c by name.

**Ruling: re-word and re-own; do not build the clustered derived draw.** The § Errors row's
justification is *"Temporary, alongside `E-DATA-CLUSTER-CONTRAST`, which is the same missing
construction one level over"*, and that dangles the moment task 14 lands. The construction it names
is a per-condition percentile draw over clusters for a *recomputed* metric — the same family as the
unpaired clustered percentile form H4c already owns, and nothing this slice needs: under `cluster_by`
the whole `derived` mapping is dropped before it reaches `aggregated`, so **the derived branch of
`_comparison_step_blocks` is unreachable in a clustered run**. That unreachability is what makes
decision 5's asymmetry hold cleanly, and it is a fact to measure rather than infer.

**The wording of the row itself lands in task 15**, with every other surviving citation, as one
sweep — see this plan's § Sequencing, deviation (b). **This task fixes the owner and pins the fact.**

- [ ] **Step 1: Read the existing pin, and write no second one.** Read
      `tests/test_cli.py::test_a_clustered_derived_metric_is_refused_rather_than_drawn` in full. It
      already runs a clustered project whose template derives `total` and asserts
      `set(aggregated) == {"pred"}` — the exact fact this ruling rests on, at the exact place it can
      be observed. **A second test asserting the same fact is not a second pin.** What that test has
      never had is a mutation proving it discriminates, and that is what Step 2 supplies: *"a
      subprocess probe is not a pin, and five times in three slices a correct fix shipped
      unpinned"* — the converse also holds, an untested-for-discrimination pin is a claim.

- [ ] **Step 2: Prove the existing pin can fail (this task's mutation).** In
      `src/publishable/stats.py`, `summarize_step`, change the guard

```python
        if clusters is not None and seed is not None:
```

      to

```python
        if clusters is not None and seed is None:
```

      Run the **full, unfiltered** suite in the foreground.
      `test_a_clustered_derived_metric_is_refused_rather_than_drawn` must **FAIL** on
      `assert set(aggregated) == {"pred"}`. **Checked against the test body:** `command_run` builds
      `seed` from `stats.resample_seed(digest)`, which returns a real `int` and never `None`, so the
      two branches take opposite paths on every clustered run — the derived metric survives under the
      mutant and is dropped without it, and the test asserts set equality on exactly that. Then
      `find . -name __pycache__ -type d -exec rm -rf {} +`, **edit the guard back in place** (never
      `git checkout --`), rerun, confirm PASS.

- [ ] **Step 3: Record the ruling and the re-ownership.** Append to
      `docs/superpowers/spec-defects.md`:

```markdown
## RULED by H4b-2 task 4 — `E-DATA-CLUSTER-DERIVED` is re-owned to H4c, not built here

`docs/superpowers/H4b-SCOPING.md` § 5 recommended that H4b-2 take the clustered derived draw
"because the construction it needs is the same membership-aware derived draw". Re-measured at
`82310b9`: it is emitted once, from `stats.summarize_step`, and its `reference.md` § Errors row
justifies itself as *"Temporary, alongside `E-DATA-CLUSTER-CONTRAST`"* — a justification that dangles
the moment H4b-2 task 14 retires that code.

**Ruled: do not build it. Re-own it to H4c by name, and let the row state its own justification.**
The missing construction is a per-condition percentile draw over clusters for a *recomputed* metric —
each replicate drawing whole clusters and rebuilding a `UnitTable` from their pooled units — which is
the same family as the unpaired clustered percentile form H4c already owns, and is not a contrast
construction at all.

**H4b-2 does not need it**, and that is measured rather than assumed: under `cluster_by` the whole
`derived` mapping is dropped before it reaches `aggregated`, so `cli._comparison_step_blocks`' derived
branch — selected by `metric_key in of_derived or metric_key in against_derived` — is unreachable in
a clustered run. Pinned by
`tests/test_cli.py::test_a_clustered_derived_metric_is_refused_rather_than_drawn`, which asserts
`set(aggregated) == {"pred"}` and whose discriminating mutation — `summarize_step`'s own
`seed is not None` guard — was run against the full suite here rather than assumed. That
unreachability is also what makes every clustered
contrast entry carry a `_clustered` `method`, which is the argument H4b-2 task 2 rests on for
recording no `clustered_by` key.

**The row's wording is repaired by H4b-2 task 15**, with every other citation of
`E-DATA-CLUSTER-CONTRAST` that task 14 does not delete, as one sweep rather than two commits over one
claim.

**Ruled by:** H4b-2, task 4. **Owner from here:** H4c.
```

- [ ] **Step 4: Run the four gates.** `uv run pytest` → **2159 passed, 1 skipped, 2 xfailed**
      (unchanged; this task adds no test, and says why in Step 1). Then `uv run ruff check .`,
      `uv run ruff format --check .` (80 files), `uv run mypy`.

- [ ] **Step 5: Commit.**

```bash
git add docs/superpowers/spec-defects.md
git commit -m "docs: E-DATA-CLUSTER-DERIVED is re-owned to H4c, and the fact H4b-2 rests on is pinned"
```

---

## Task 2: document `n_paired_clusters` in § Contrasts

**Runs third — after task 4**, whose ruling is what makes the record shape below principled rather
than aesthetic: because no clustered contrast entry can be derived, every one of them carries a
`_clustered` `method`, and the suffix already discloses the clustering. That is exactly the argument
`weighted_by` could **not** make — a weighted *derived* contrast keeps the unsuffixed
`paired_percentile_over_units` spelling, so the record had to name the attribute — and it is why
`n_paired_clusters` gets a **count** and no `clustered_by` sibling.

**Files:**
- Modify: `docs/reference.md`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `tests/test_cli.py::_section_text(heading: str) -> str`, which slices `reference.md` from
  a named heading to the next heading of the same depth or shallower — already defined in that
  module; § Contrasts' `n_paired` paragraph and its `weighted_by` / `n_paired_effective` paragraph,
  read in `docs/reference.md`.
- Produces: `n_paired_clusters` documented as a scalar sibling of `n_paired`, which task 13 emits
  under exactly that spelling.

**A record key code writes and no document names is the pair `CLAUDE.md` says to grep for.** H4b-1
minted `n_paired_effective` as a **scalar sibling** of `n_paired` rather than promoting `n_paired` to
a mapping, on the argument § Contrasts already makes for `n_paired` itself — *"the condition-level
`n` can't carry this, because it belongs to one condition and the contrast spans two"* — and
`n_paired_clusters` follows that precedent rather than designing a shape from scratch.

**And it extends `cli.py`'s own argument rather than repeating it.** `command_run`'s comment records
that the cluster count travels in `attrition`'s counts per condition because *"nothing in the
documents shows a `clustered_by` sibling of `weighted_by`"*. That stays true and is now **argued**
rather than merely observed: the `_clustered` `method` suffix discloses the clustering on a contrast
entry, so an attribute-naming key would be a second disclosure of one fact. The comment itself is
extended in task 13, where the code writes the key.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`, beside
      `test_the_weighted_contrast_record_keys_are_documented`:

```python
def test_the_clustered_contrast_record_key_is_documented():
    """Task 2's ruling, in the document before task 13's code writes it.

    A contrast entry has no `n` mapping for the cluster count to join — § Contrasts
    argues why — so it takes a scalar sibling of `n_paired`, on the
    `n_paired_effective` precedent. And it takes a COUNT and no attribute name: the
    `_clustered` suffix on `method` already discloses the clustering, which is the
    disclosure a weighted derived contrast could not make and why `weighted_by`
    exists.

    The control asserts the section was really located: a slicer returning the
    empty string would fail every `in` and pass every `not in`."""
    section = _section_text("#### Contrasts: claims that aren't condition-vs-baseline")
    assert "n_paired_effective" in section  # the control
    assert "n_paired_clusters" in section
    assert "clustered_by" not in section
```

- [ ] **Step 2: Run and see it fail.** `uv run pytest
      tests/test_cli.py::test_the_clustered_contrast_record_key_is_documented` → FAIL on
      `assert "n_paired_clusters" in section`.

- [ ] **Step 3: Implement.** In `docs/reference.md` § Contrasts, immediately after the paragraph
      that ends *"the size reported beside an interval has to be the size the interval was computed
      at"* and its fenced `arm_sensitivity` example, add:

````markdown
**Under [`cluster_by`](#clustered-units) a contrast entry carries one more key, and it is a count
rather than a name.** `n_paired_clusters` is the number of distinct clusters the paired intersection
falls in — a **scalar sibling of `n_paired`**, on the same argument `n_paired_effective` rests on:
this record deliberately has no `n` mapping to join, and the cluster count is a fact about the
intersection `n_paired` counts. It is the count the interval's df was taken from, so a reader can
check `clusters − 1` against the interval rather than take it on trust.

There is deliberately **no attribute-naming key** beside it. Every clustered contrast records a
`method` carrying the `_clustered` suffix, so the record already discloses that the cluster was the
draw — which is the disclosure a weighted contrast could not make, since a weighted *derived* metric
keeps the unsuffixed spelling and needs `weighted_by` to say so at all. One fact, disclosed once.

```yaml
results:
  contrasts:
    - id: site_sensitivity
      of: 02_arm=abnormal
      against: 01_arm=normal
      step03_screen:
        prob: {delta: 0.041, basis: units, paired: true,
               method: paired_t_over_units_clustered,
               n_paired: 330, n_paired_clusters: 12,
               ci95: [0.006, 0.076], cohens_d: 0.36,
               correction: holm, correction_level: 0.0125,
               family_size: 4, family: {comparisons: 2, metrics: 2}}
```

The interval, the `method` and the cluster count move together, the same obligation a weighted entry
carries: a delta whose interval reads the cluster as the draw, beside a `method` that does not say
so, or beside no cluster count at all, is a declaration accepted whose effect is half delivered.
`cohens_d` is **not** in that set — *d*z is standardized by the dispersion of the differences and
[§ Statistical reporting](#statistical-reporting) defines no clustered effect size, so it is the same
number a clustered run and an unclustered one report.
````

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2159 + 1 = 2160 passed**, 1 skipped,
      2 xfailed. Then `uv run ruff check .`, `uv run ruff format --check .` (80 files),
      `uv run mypy`. Then the mechanical `*.md` pass on the edit: both `#anchor` links resolve
      (`#clustered-units`, `#statistical-reporting`), no trailing whitespace, no en dash, no `x` used
      for multiplication, and the fenced YAML block is skipped by every structural check.

- [ ] **Step 5: Mutate.** In `docs/reference.md`, change the new key's spelling in the prose from
      `n_paired_clusters` to `n_paired_cluster_count` — in the paragraph only, leaving the fenced
      YAML untouched. `tests/test_cli.py::test_the_clustered_contrast_record_key_is_documented` must
      **FAIL**. **Checked against the test body:** `_section_text` returns the section's raw text
      including the fence, so a mutation touching only the prose would still leave the string present
      in the YAML — **so this mutation as stated is BLIND.** Apply it to **both** the prose and the
      fenced example, which is the mutation to run. The control assertion (`n_paired_effective`) is
      on material the mutation does not touch, so a failure is attributable to the renamed key rather
      than to a broken slicer.

      **Second mutation, for the slicer:** change the heading argument in the test to
      `"#### Contrasts: claims that are condition-vs-baseline"`. The test must **FAIL** with
      `StopIteration` from `_section_text`'s `next(...)`. This is what makes the control a control
      rather than a comment.

- [ ] **Step 6: Commit.**

```bash
git add docs/reference.md tests/test_cli.py
git commit -m "docs: a clustered contrast records n_paired_clusters, and no clustered_by"
```

---

## Task 3: rule and document the degenerate-draw refusal for the paired percentile family

**Runs fourth — before task 7**, because the refusal lives **inside** the percentile construction and
over the same uniform draw shape task 7 builds. Building the construction first and adding the
refusal after is how `resample.stratify_by` came to be dropped on this path in the first place.

**Files:**
- Modify: `docs/reference.md`, `docs/superpowers/spec-defects.md`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `stats.percentile_over_units_clustered`'s content-based refusal,
  `if all(len({tuple(cluster) for cluster in group}) <= 1 for group in stratum_pools): return None` —
  read in `src/publishable/stats.py`; `stats.paired_percentile_of_derived`'s docstring section
  *"**Not built here:** its siblings' content-based degenerate refusal"*; the OPEN
  `spec-defects.md` entry *"a stratified paired draw can publish a zero-width contrast interval"*,
  owned by H4b-2 by name; `tests/test_cli.py::_section_text`.
- Produces: the rule stated in § Statistical reporting, which task 9 implements and which task 9's
  four-cell test asserts.

**The defect is live and it was filed by H4b-1 itself.** `paired_percentile_of_derived` is the only
one of four percentile constructions with **no content-based degenerate refusal**, and H4b-1 task 5's
`strata` parameter made it reachable: a near-unique `stratify_by` makes every stratified contrast
draw pick from an identical multiset, so the entry publishes `ci95: [x, x]` — a zero-width 95 %
interval § Statistical reporting refuses in those terms, indistinguishable from a genuine one.

**Ruling: build the refusal, content-based rather than count-based, over the drawable item rather
than over the key.** A count floor answers a different question: two clusters per stratum with
identical content pass a count floor and are still degenerate — which is why
`percentile_over_units_clustered` checks content and applies the check whether or not `strata` was
given. The paired form's drawable item is a **key** when nothing is clustered and a **cluster** once
`clusters` is given, and its content is the pair of rows the two sides carry for it. Same rule, one
level up.

**The document leads.** This task states the rule in § Statistical reporting; task 9 gives it code.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`, beside
      `test_the_clustered_contrast_record_key_is_documented`:

```python
def test_a_contrast_draw_that_cannot_vary_is_documented_as_reporting_no_interval():
    """Task 3's ruling, in the document before task 9's code. The three sibling
    percentile constructions each refuse a draw whose content cannot vary — "a
    zero-width 95 % interval is not honest" — and the paired one carries none of
    those refusals, which H4b-1 filed as a live defect against this slice by name.

    The control asserts the section was located and holds the material this rule
    belongs beside."""
    section = _section_text("### Statistical reporting")
    assert "paired_percentile_over_units" in section  # the control
    assert "reports no interval rather than a zero-width one" in section
```

- [ ] **Step 2: Run and see it fail.** `uv run pytest
      tests/test_cli.py::test_a_contrast_draw_that_cannot_vary_is_documented_as_reporting_no_interval`
      → FAIL on the second assertion.

- [ ] **Step 3: Implement.** In `docs/reference.md` § Statistical reporting, immediately after the
      paragraph beginning *"**A weighted contrast weights a recorded column and not a derived
      metric.**"*, add:

```markdown
**A contrast draw that cannot vary reports no interval rather than a zero-width one.** The joint
draw's smallest drawable thing is a unit, or a whole cluster where
[`cluster_by`](#clustered-units) is declared; a
[`stratify_by`](#the-one-config-file) stratum draws only from its own. So where every drawable thing
in every stratum carries the same pair of rows — a stratum holding one of them trivially so — every
replicate reproduces the same difference, both percentile ranks land on it, and the interval has zero
width while looking exactly like a narrow one. That is the same refusal the per-condition percentile
forms already make for their own draws, and it is a property of the draw's **content**, not of how
many things it holds: two clusters carrying identical rows clear any count floor and still cannot
vary. The contrast then reports its `delta` with `ci95: null`, which is the honest answer — reporting
a point with no interval is honest, a zero-width 95 % interval is not.
```

- [ ] **Step 4: Amend the filing.** In `docs/superpowers/spec-defects.md`, in the OPEN entry
      *"a stratified paired draw can publish a zero-width contrast interval"*, append below its
      **Found by / Severity** line:

```markdown
**AMENDED 2026-08-17 (H4b-2, task 3).** Ruled and specified: `reference.md` § Statistical reporting
now states the rule — a contrast draw whose every stratum's drawable things carry the same pair of
rows reports `ci95: null` — and H4b-2 task 9 gives it code inside
`stats.paired_percentile_of_derived`, covering the clustered and unclustered draws and the stratified
and unstratified ones as one check over the drawable item. **The entry is closed by that task, not by
this one.**
```

- [ ] **Step 5: Run and see it pass.** `uv run pytest` → **2160 + 1 = 2161 passed**, 1 skipped,
      2 xfailed. Then the other three gates, then the mechanical `*.md` pass: the two `#anchor` links
      resolve, no trailing whitespace, no en dash.

- [ ] **Step 6: Mutate.** In `docs/reference.md`, change the new paragraph's phrase
      `reports no interval rather than a zero-width one` to `reports a zero-width interval`. The new
      test must **FAIL**. **Checked against the test body:** the test asserts that exact phrase
      present and the control asserts a different string the mutation does not touch, so the two
      branches cannot agree and a failure is attributable to the changed sentence.

- [ ] **Step 7: Commit.**

```bash
git add docs/reference.md docs/superpowers/spec-defects.md tests/test_cli.py
git commit -m "docs: a contrast draw that cannot vary reports no interval"
```

---

## Task 5: pin the `E-DATA-ALLOCATION-CONTRAST` sequencing dependency, two ways

**Files:**
- Modify: `docs/superpowers/spec-defects.md`
- Test: `tests/test_cli.py`, `tests/test_validate.py`

**Interfaces:**
- Consumes: `cli._comparison_step_blocks`' two `"paired": True` literals, one in the derived branch's
  `metric_block[metric_key]` and one in the column branch's — read in `src/publishable/cli.py`;
  `validate._check_sweep`'s `E-DATA-ALLOCATION-CONTRAST` emit, guarded per comparison by
  `group_axes = [axis for axis in differing if axis in group_selectors]` — read in
  `src/publishable/validate.py`; `tests/test_validate.py`'s `_groups_cluster_doc` and
  `_groups_cluster_csv` helpers.
- Produces: two tripwires H4c must confront, and nothing any later task in this slice consumes.

**Why two paired constructions are sufficient, and what that depends on.**
`_comparison_step_blocks` writes `"paired": True` **unconditionally at both metric branches**, so
every comparison that survives `E-DATA-ALLOCATION-CONTRAST` is paired and there is no code path
producing an unpaired contrast entry. That is what makes two paired clustered constructions enough to
retire `E-DATA-CLUSTER-CONTRAST` — and it holds **only while `E-DATA-ALLOCATION-CONTRAST` stands.**
If H4c lands first, `paired` stops being unconditional and the unpaired clustered forms become
reachable with nothing built.

**The obvious pin is a mutation whose two branches cannot differ, and it is not written here.**
"A test that fails if `paired` is ever `False`" has no runtime state to assert against: `paired` is a
**literal**, so no fixture can make the two readings differ. What can be pinned is the literal
itself, and the behaviour beside it. Hence two tests, neither of them that one.

- [ ] **Step 1: Write the two failing tests.** First, in `tests/test_cli.py`, add `import inspect` to
      the module's import block (it is not imported today; `re` and `yaml` already are), and append
      beside `test_a_comparison_reads_its_own_condition_not_condition_zero`:

```python
def test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch():
    """The H4c tripwire, and the reason two PAIRED clustered constructions were
    enough for H4b-2.

    `_comparison_step_blocks` writes `paired` as a literal `True` at both metric
    branches, so every comparison surviving `E-DATA-ALLOCATION-CONTRAST` is paired
    and no unpaired contrast interval is ever asked for. The obvious runtime pin —
    "fail if `paired` is ever `False`" — is a mutation whose two branches cannot
    differ, because there is no runtime state to assert against. So the LITERAL is
    what is pinned: the moment H4c makes either site conditional, this fails and
    forces whoever does it to confront the clustered unpaired constructions, which
    do not exist.

    Both counts are asserted, and that is the point: the first alone passes under a
    third branch writing `"paired": is_paired`, and the second alone passes under
    two sites that both became conditional."""
    from publishable.cli import _comparison_step_blocks

    source = inspect.getsource(_comparison_step_blocks)
    assert source.count('"paired": True') == 2
    assert source.count('"paired":') == 2
```

      The function-local import is the idiom `test_a_comparison_reads_its_own_condition_not_condition_zero`
      already uses for this private name; the module imports only `cli`'s public and
      already-needed helpers at the top.

      Second, in `tests/test_validate.py`, append beside
      `test_a_contrast_beside_groups_and_cluster_by_draws_both_refusals`:

```python
def test_every_unpaired_comparison_shape_still_earns_the_allocation_refusal(write_config, tmp_path):
    """The behavioural half of H4b-2 task 5's H4c tripwire, and the half that
    survives the literal being refactored.

    H4b-2 builds PAIRED clustered constructions only, which is sufficient exactly
    while every unpaired comparison is refused before it reaches `cli`. Asserted
    ALONGSIDE `E-DATA-CLUSTER-CONTRAST` rather than as a total code set, so H4b-2
    task 14's retirement is a one-line deletion here.

    `validate` collects rather than aborting, so the cluster refusal firing does not
    make the allocation one unreachable — both are reported over the one
    comparison, and this asserts both."""
    (tmp_path / "input" / "index.csv").write_text(_groups_cluster_csv())
    doc = _groups_cluster_doc(
        statistics={
            "contrasts": [{"id": "t_vs_c", "of": "arm=treatment", "against": "arm=control"}]
        }
    )
    found = _error_codes(write_config(doc))
    assert "E-DATA-ALLOCATION-CONTRAST" in found
    assert "E-DATA-CLUSTER-CONTRAST" in found  # deleted by task 14, not narrowed
```

- [ ] **Step 2: Run and see them pass, and record that they do.** Both pin behaviour that already
      exists. `uv run pytest tests/test_cli.py::test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch
      tests/test_validate.py::test_every_unpaired_comparison_shape_still_earns_the_allocation_refusal`
      → **PASS**. As in task 4, the discriminating question is whether they *can* fail, which Step 3
      answers.

- [ ] **Step 3: Mutate, twice.** First, in `src/publishable/cli.py`, change the column branch's
      `"paired": True,` to `"paired": bool(True),`. The `test_cli.py` test must **FAIL** on both
      assertions' first line (`count('"paired": True') == 2` now sees 1). **Checked against the test
      body:** the mutation removes one occurrence of the exact substring the first assertion counts,
      so the branches provably differ. Revert by editing the file back.

      Second, in `src/publishable/validate.py`, `_check_sweep`, change the allocation guard's
      `if not group_axes:` / `continue` pair to `if group_axes:` / `continue` — inverting which
      comparisons are refused. The `test_validate.py` test must **FAIL** on
      `assert "E-DATA-ALLOCATION-CONTRAST" in found`. **Checked against the test body:** the fixture's
      one comparison crosses a declared `groups` axis, so it is the only comparison the guard reads,
      and inverting the guard moves it from refused to accepted. Revert by editing the file back.
      Run the **full, unfiltered** suite in the foreground for each.

- [ ] **Step 4: Record the dependency.** Append to `docs/superpowers/spec-defects.md`:

```markdown
## RULED by H4b-2 task 5 — H4b-2's two paired constructions are sufficient only while `E-DATA-ALLOCATION-CONTRAST` stands

Measured at `82310b9`: `cli._comparison_step_blocks` writes `"paired": True` unconditionally at both
metric branches, so no code path produces an unpaired contrast entry and every comparison reaching
that function survived `E-DATA-ALLOCATION-CONTRAST`. That is why H4b-2 built
`paired_t_over_units_clustered` and `paired_percentile_over_units_clustered` and no unpaired
counterparts: they are unreachable, not merely unbuilt.

**The dependency runs the other way for H4c.** The slice that retires
`E-DATA-ALLOCATION-CONTRAST` must build `welch_t_over_units_clustered` and
`unpaired_percentile_over_units_clustered` in the same slice, or a clustered cross-arm comparison
will take a paired construction over an empty intersection. Two tripwires pin it, deliberately
neither of them the obvious "assert `paired` is never `False`", which is a mutation whose branches
cannot differ:

- `tests/test_cli.py::test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch`
  fails the moment either literal becomes conditional.
- `tests/test_validate.py::test_every_unpaired_comparison_shape_still_earns_the_allocation_refusal`
  fails the moment the refusal stops firing for a cross-arm comparison.

**Ruled by:** H4b-2, task 5. **Owner of the obligation:** H4c.
```

- [ ] **Step 5: Run the four gates.** `uv run pytest` → **2161 + 2 = 2163 passed**, 1 skipped,
      2 xfailed. Then `uv run ruff check .`, `uv run ruff format --check .` (80 files),
      `uv run mypy`.

- [ ] **Step 6: Commit.**

```bash
git add docs/superpowers/spec-defects.md tests/test_cli.py tests/test_validate.py
git commit -m "test: pin the allocation-refusal dependency H4b-2's paired constructions rest on"
```

---

## Task 6: `stats.paired_t_over_units_clustered`

**Runs after task 1**, whose ruling fixed that this slice builds **two** paired clustered
constructions and not four — so this function takes no `weights` parameter and never will.

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `stats.t_over_units_clustered(values, keys, membership, confidence=0.95) -> Interval |
  None`, CR1 with `variance = (groups / (groups - 1)) * meat / (n * n)` and `df = groups - 1`, and
  `groups = cluster_count_of(membership, keys)` — read in `src/publishable/stats.py`;
  `stats.paired_t_over_units`, which delegates to `t_over_units` and rewrites the `method`.
- Produces:

```python
def paired_t_over_units_clustered(
    diffs: Sequence[float], labels: Sequence[str], confidence: float = 0.95
) -> Interval | None
```

  called by `cli._comparison_step_blocks` (task 10) and by `correction._corrected_bounds` (task 12),
  returning an `Interval` whose `method` is exactly `"paired_t_over_units_clustered"`.

**Why `labels` and not `keys` + `membership`.** The two callers both hold a per-difference vector and
nothing else: `Member` documents `weights` as *"a modifier on `diffs`, not a third kind of
evidence"*, length-checked, stored as a tuple — and `clusters` follows that precedent exactly
(task 12). Handing this function a `keys` list and a `membership` mapping would put two fields on a
frozen dataclass for one fact, and a mapping on a dataclass nothing may mutate.

**The positional keys synthesized inside are a bijection, not a proxy.** `t_over_units_clustered`
uses `keys` for exactly one purpose — looking a label up in `membership`, and counting groups through
`cluster_count_of` — so distinct synthetic keys carrying the given labels are the same input by
construction. This is written into the docstring because `CLAUDE.md` § Answering a question with a
proxy makes a reviewer ask, and the answer is that no information is being *approximated* here.

**Delegation, not a hand-rolled variance.** `weighted_paired_t_over_units`' docstring states the
reason and it is unchanged here: delegating is what makes the CR1 scaling, the df, the two floors and
the relabelling invariance properties of **one** construction rather than of two that can drift
apart.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_stats.py`, beside
      `test_the_weighted_sandwich_reduces_to_the_unweighted_one_at_equal_weights`:

```python
_CLUSTERED_DIFFS = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
_CLUSTERED_LABELS = ["a"] * 2 + ["b"] * 4 + ["c"] * 6


def test_the_paired_clustered_t_is_cr1_over_the_differences():
    """12 per-unit differences in 3 clusters of 2/4/6 — `1.0 ×2`, `5.0 ×4`,
    `9.0 ×6`. Mean 76/12 = 6.3333…; per-cluster residual sums −10.6667, −5.3333,
    +16.0, so the meat is 398.2222, V = (3/2)·398.2222/144 and the half-width is
    t(0.975, df 2) = 4.302653 times its root.

    **The delta is the same number under every reading** — clustering moves the
    variance, not the point estimate — so the half-width is the whole assertion.
    Four wrong readings give four other numbers, none of them adjacent: the same
    meat at df 11 gives 4.4827, the IID variance at df 2 gives 3.8678, a cluster
    count of 4 gives 6.1110, and the unclustered form gives 1.9786. The correct
    answer is the extreme of no single dimension, which is what makes an assertion
    on the number discriminate all four rather than merely detect "wider"."""
    interval = paired_t_over_units_clustered(_CLUSTERED_DIFFS, _CLUSTERED_LABELS)
    assert interval is not None
    assert interval.method == "paired_t_over_units_clustered"
    centre = (interval.low + interval.high) / 2
    half = (interval.high - interval.low) / 2
    assert centre == pytest.approx(6.333333333333333)
    assert half == pytest.approx(8.763214143637903)


def test_the_paired_clustered_t_is_not_the_unclustered_one_on_the_same_differences():
    """The control that must report, and the number a membership-ignoring mutant
    lands on. The same differences through `paired_t_over_units` give 1.9786 — a
    factor of four narrower, and the same centre, which is why a test asserting the
    centre alone is blind to clustering entirely."""
    plain = paired_t_over_units(_CLUSTERED_DIFFS)
    assert plain is not None
    assert (plain.high - plain.low) / 2 == pytest.approx(1.9785385229565593)
    assert plain.method == "paired_t_over_units"


def test_the_paired_clustered_t_refuses_the_degenerate_inputs_its_sibling_refuses():
    """Both floors are inherited rather than restated, which is the point of
    delegating: `None` below two differences, and `None` below two clusters, where
    df would be zero. The second is the one a singleton-cluster fixture can never
    see — one unit per cluster makes `clusters − 1` equal `n_paired − 1`, so the
    clustered and unclustered forms coincide exactly and a mutant ignoring
    membership passes. Hence the third case: 12 singleton clusters return an
    interval identical to the unclustered one, which is correct and is exactly why
    no other test here may use that shape."""
    assert paired_t_over_units_clustered([1.0], ["a"]) is None
    assert paired_t_over_units_clustered([1.0, 5.0, 9.0], ["a", "a", "a"]) is None
    singletons = paired_t_over_units_clustered(
        _CLUSTERED_DIFFS, [f"c{i}" for i in range(12)]
    )
    plain = paired_t_over_units(_CLUSTERED_DIFFS)
    assert singletons is not None and plain is not None
    assert (singletons.high - singletons.low) == pytest.approx(plain.high - plain.low)
```

      Add `paired_t_over_units_clustered` to the `from publishable.stats import (...)` block at the
      top of `tests/test_stats.py` — `paired_t_over_units` is already there.

- [ ] **Step 2: Run and see them fail.** `uv run pytest tests/test_stats.py -k paired_clustered` →
      `ImportError` on `paired_t_over_units_clustered`.

- [ ] **Step 3: Implement.** In `src/publishable/stats.py`, immediately after
      `weighted_paired_t_over_units`:

```python
def paired_t_over_units_clustered(
    diffs: Sequence[float], labels: Sequence[str], confidence: float = 0.95
) -> Interval | None:
    """Cluster-robust (CR1) *t* on the per-unit differences, df = clusters − 1.

    `reference.md` § Statistical reporting: under a declared `cluster_by` each
    unweighted contrast construction "takes a `_clustered` suffix and reads the
    cluster as the draw", the *t* forms being "cluster-robust (CR1) with df =
    clusters − 1, over the differenced values when paired". This is that form, and
    the contrast's interval stays its own construction over the paired
    intersection rather than a difference of the two sides' intervals —
    `paired_t_over_units`' argument, unchanged by the clustering.

    **The df is the construction**, not a detail of it: a cluster-robust interval
    over positively correlated differences comes out wider than
    `paired_t_over_units` whatever df it uses, so widening is not evidence the
    cluster count reached the critical value. Only the number is.

    Delegates to `t_over_units_clustered` and rewrites the `method`, exactly as
    `paired_t_over_units` delegates to `t_over_units` and
    `weighted_paired_t_over_units` to `weighted_t_over_units`. That is not
    tidiness: it is what makes the `G/(G−1)` scaling, the df, the two floors and
    the relabelling invariance properties of ONE construction rather than of two
    that can drift apart. A hand-rolled sandwich here is how a paired interval and
    a per-condition one come to disagree about what cluster-robust means.

    **`labels` is one cluster label per difference, in the same order**, rather
    than the `keys` + `membership` pair the per-condition form takes. Both callers
    hold a per-difference vector and nothing else: `correction.Member` carries
    `clusters` as a modifier on `diffs` for the same reason it carries `weights`
    that way, and a mapping plus a key list would be two fields on a frozen
    dataclass for one fact. The positional keys synthesized below are a
    **bijection**, not a proxy for the real unit keys: `t_over_units_clustered`
    uses a key for exactly one thing — looking its label up, and counting the
    distinct labels through `units.cluster_count_of` — so distinct synthetic keys
    carrying these labels are the same input to it, digit for digit. The real unit
    keys are unrecoverable here and are also unused.

    `strict=True` on the zip, for the reason `_weighted_mean` uses it: a
    diffs/labels length mismatch is a misaligned cluster vector, and it would
    produce a plausible number rather than an error.

    Floors are inherited whole: `None` below two differences, and `None` below two
    clusters, where df would be zero.
    """
    keys = [str(i) for i in range(len(diffs))]
    plain = t_over_units_clustered(
        diffs, keys, dict(zip(keys, labels, strict=True)), confidence
    )
    if plain is None:
        return None
    return Interval(
        low=plain.low, high=plain.high, method="paired_t_over_units_clustered"
    )
```

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2163 + 3 = 2166 passed**, 1 skipped,
      2 xfailed. Then `uv run ruff check .`, `uv run ruff format --check .` (80 files),
      `uv run mypy`.

- [ ] **Step 5: Mutate — and read this first, because the obvious mutation here is BLIND.**

      **Do not prescribe or trust `dict(zip(keys, labels[::-1]))`.** Reversing the label vector maps
      cluster `a` onto the six 9.0s, `c` onto the two 1.0s and `b` onto the four 5.0s — a **different
      partition with the identical multiset of per-cluster residual sums** {−16.0, +10.6667,
      +5.3333} against {−10.6667, −5.3333, +16.0}, so the meat is 398.2222 either way and the
      half-width comes back 8.763214143637901 against 8.763214143637903. Verified numerically at
      `82310b9`: the two differ in the last float digit and `pytest.approx` cannot tell them apart.
      This is *a mutation whose two branches cannot differ*, and it is written down here so nobody
      adds it later believing it proves alignment.

      **Mutation 1 — alignment, and it does discriminate.** Change
      `dict(zip(keys, labels, strict=True))` to `dict(zip(sorted(keys), labels, strict=True))`. The
      synthetic keys are `"0"`…`"11"`, whose lexicographic order is `0, 1, 10, 11, 2, 3, …`, so the
      labels land on a genuinely different partition: `a` takes the two 1.0s, `b` takes two 9.0s and
      two 5.0s, `c` takes the rest. The half-width becomes **5.971123930019732**, verified
      numerically at `82310b9`.
      `tests/test_stats.py::test_the_paired_clustered_t_is_cr1_over_the_differences` must **FAIL** on
      the half-width assertion, and its `method` and centre assertions still pass — so the failure is
      attributable to the misalignment rather than to a broken call.

      **Mutation 2 — the construction.** Change the delegate call to
      `t_over_units(diffs, confidence)`. The same test must **FAIL** with a half-width of 1.9786 —
      the number `test_the_paired_clustered_t_is_not_the_unclustered_one_on_the_same_differences`
      independently pins as the *unclustered* answer, which is what makes the two tests a pair rather
      than a repetition.

      **Mutation 3 — the `method` rewrite.** Return `plain` unchanged instead of building a new
      `Interval`. The same test must **FAIL** on `interval.method ==
      "paired_t_over_units_clustered"`, seeing `"t_over_units_clustered"`.

      Run each against the **full, unfiltered** suite in the foreground; revert each by editing the
      file back in place, never `git checkout --`.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/stats.py tests/test_stats.py
git commit -m "feat: paired_t_over_units_clustered, CR1 over the per-unit differences"
```

---

## Task 7: `clusters` on `paired_percentile_of_derived`, and the `_clustered` percentile `method`

**Runs after tasks 1 and 3** — task 1 fixed that no weighted clustered form is built, task 3 stated
the degenerate rule this construction's draw shape must be able to express (task 9 gives it code).

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `stats.paired_percentile_of_derived(of, against, keys, compute_of, compute_against, seed,
  draws=2000, confidence=0.95, strata=None, method="paired_percentile_over_units") ->
  PairedResample`, whose stratified draw is
  `[group[rng.randrange(len(group))] for group in pools for _ in range(len(group))]` and whose
  unstratified draw is `[keys[rng.randrange(n)] for _ in range(n)]` — read in
  `src/publishable/stats.py`; `stats.percentile_over_units_clustered`'s cluster-within-stratum
  equality and its `E-STATS-RESAMPLE-STRATIFY-VARIES` raise, which this mirrors.
- Produces: the same function with one more keyword parameter,

```python
    clusters: dict[str, str] | None = None,
```

  appended **after** `method` (every parameter from `seed` on has a default, and appending keeps any
  existing positional call valid), and the `method` string
  `"paired_percentile_over_units_clustered"`, which `cli` passes in task 11.

**There is no new function, and that is a ruling.** `paired_percentile_of_derived` already emits two
`method` strings chosen by its caller — `paired_percentile_over_units` and
`weighted_paired_percentile_over_units` — because it is one construction shared by a derived contrast
and a recorded column's. A third spelling is the same shape again. A separate
`paired_percentile_over_units_clustered` function would duplicate the `strata` composition, the
sorted-`keys` precondition and the degenerate refusal, and this repo has already paid for two
spellings of one construction drifting apart.

**The draw becomes one uniform shape, and it is RNG-identical to the two it replaces.** A list of
stratum groups, each holding the **drawable things** that stratum owns, each of those a list of keys:
a unit by default, a whole cluster once `clusters` is given. With no clusters and no strata that is
one group of `n` single-key items, drawing `randrange(n)` exactly `n` times in the same order as
today; with strata it is today's per-stratum groups with each key wrapped in a one-element list, so
the group order and the per-group draw counts are unchanged. **The existing `stats` and `cli` tests
passing unmodified is the proof**, and task 17 pins it as a regression.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_stats.py`, beside task 6's tests:

```python
def _paired_cluster_fixture() -> tuple[dict, dict, list[str], dict[str, str]]:
    """12 keys in 3 clusters of 2/4/6, `of` minus `against` giving 1.0/5.0/9.0.

    Unequal sizes are load-bearing twice over: they make a replicate's pooled row
    count VARY (6 to 18) where a unit-drawing mutant returns a fixed 12, and they
    keep the correct and buggy cluster counts different. Equal sizes make both
    discriminators invisible."""
    keys = [f"u{i:02d}" for i in range(12)]
    labels = ["a"] * 2 + ["b"] * 4 + ["c"] * 6
    values = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
    of = {k: {"m": v} for k, v in zip(keys, values, strict=True)}
    against = {k: {"m": 0.0} for k in keys}
    return of, against, keys, dict(zip(keys, labels, strict=True))


def test_the_paired_clustered_percentile_draws_whole_clusters():
    """`reference.md` § Statistical reporting: under `cluster_by` "the percentile
    forms resample whole clusters — jointly across both sides when paired".

    The row count is asserted directly rather than inferred from the interval,
    because it is the discriminator a mutant drawing UNITS cannot fake: three
    clusters drawn with replacement from sizes 2/4/6 pool between 6 and 18 rows,
    and every count is one of the sums those sizes can make. A unit-drawing mutant
    returns exactly 12 every time.

    The `method` is the caller's string, as it is for the two spellings this
    construction already emits."""
    of, against, keys, clusters = _paired_cluster_fixture()
    seen: list[int] = []

    def compute(table):
        seen.append(len(list(table.unit)))
        return sum(table.m) / len(table.m)

    got = paired_percentile_of_derived(
        of,
        against,
        keys,
        compute,
        compute,
        seed=11,
        draws=400,
        method="paired_percentile_over_units_clustered",
        clusters=clusters,
    )
    assert got.interval is not None
    assert got.interval.method == "paired_percentile_over_units_clustered"
    reachable = {2, 4, 6}
    assert set(seen) != {12}
    assert min(seen) == 6 and max(seen) == 18
    assert all(
        count in {x + y + z for x in reachable for y in reachable for z in reachable}
        for count in seen
    )


def test_the_paired_clustered_percentile_draws_a_cluster_within_its_stratum():
    """`stratify_by` says what an independent draw is, `cluster_by` says the draw
    IS a cluster, and composed, a cluster is drawn within its own stratum — the
    equality `percentile_over_units_clustered` already keeps one level up.

    Stratum `A` holds the two small clusters (2 and 4 units) and stratum `B` the
    one large one (6). Each stratum contributes as many clusters as it holds, so
    every replicate pools 6 rows from `B` and between 4 and 8 from `A`: the row
    count is confined to {10, 12, 14, 16}, which an unstratified clustered draw
    (6 to 18, and 18 is reachable) is not."""
    of, against, keys, clusters = _paired_cluster_fixture()
    strata = {k: ("A" if clusters[k] in {"a", "b"} else "B") for k in keys}
    seen: list[int] = []

    def compute(table):
        seen.append(len(list(table.unit)))
        return sum(table.m) / len(table.m)

    got = paired_percentile_of_derived(
        of,
        against,
        keys,
        compute,
        compute,
        seed=11,
        draws=400,
        strata=strata,
        method="paired_percentile_over_units_clustered",
        clusters=clusters,
    )
    assert got.interval is not None
    assert set(seen) <= {10, 12, 14, 16}
    assert len(set(seen)) > 1  # the control: the draw really varies


def test_a_cluster_carrying_two_stratum_values_is_refused_on_a_contrast_draw_too():
    """The same fault `percentile_over_units_clustered` raises per condition, at
    the same code — § Errors carries one row per code covering every emit site, so
    this needs no new identifier. A cluster is indivisible, so one carrying two
    stratum values can be dealt to neither."""
    of, against, keys, clusters = _paired_cluster_fixture()
    strata = {k: ("A" if k < "u06" else "B") for k in keys}
    strata[keys[7]] = "A"  # inside cluster `c`, whose other units are `B`
    with pytest.raises(ContractError) as exc:
        paired_percentile_of_derived(
            of,
            against,
            keys,
            lambda t: sum(t.m) / len(t.m),
            lambda t: sum(t.m) / len(t.m),
            seed=11,
            draws=400,
            strata=strata,
            clusters=clusters,
        )
    assert exc.value.code == "E-STATS-RESAMPLE-STRATIFY-VARIES"


def test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was():
    """The regression the uniform draw shape owes. With `clusters=None` and no
    strata the drawn key list must be `[keys[rng.randrange(n)] for _ in range(n)]`
    against a fresh `random.Random(seed)` — same count of `randrange` calls, same
    bounds, same order. Asserted against a recomputed sequence rather than against
    a captured constant, so it pins the RNG contract instead of one seed's output."""
    of, against, keys, _ = _paired_cluster_fixture()
    drawn: list[list[str]] = []

    def compute(table):
        drawn.append(list(table.unit))
        return sum(table.m) / len(table.m)

    paired_percentile_of_derived(
        of, against, keys, compute, compute, seed=5, draws=200
    )
    rng = random.Random(5)
    expected = [[keys[rng.randrange(12)] for _ in range(12)] for _ in range(200)]
    assert drawn == expected
```

      `random`, `pytest` and `ContractError` are already imported by `tests/test_stats.py`.

- [ ] **Step 2: Run and see them fail.** `uv run pytest tests/test_stats.py -k "paired_clustered or
      two_stratum_values or same_sequence"` → the first three fail on `TypeError: unexpected keyword
      argument 'clusters'`; the fourth **passes already**, which is correct — it is the regression
      guard for a rewrite that has not happened yet, and its job is to fail if Step 3 gets the draw
      shape wrong.

- [ ] **Step 3: Implement.** In `src/publishable/stats.py`, `paired_percentile_of_derived`, append
      the parameter after `method`:

```python
    clusters: dict[str, str] | None = None,
```

      and replace the `pools` construction — everything from `pools: list[list[str]] | None = None`
      down to and including `pools = sorted(sorted(group) for group in grouped.values())` — with:

```python
    # ONE uniform draw shape: a list of stratum groups, each holding the DRAWABLE
    # things that stratum owns, each of those a list of keys. A unit is the
    # drawable thing by default; a whole cluster is, once `clusters` is given
    # (`reference.md` § Clustered units: "`resample` resamples clusters, not
    # rows"), which is the same move `percentile_over_units_clustered` makes one
    # level up. Written as one shape rather than four branches because the
    # clustered/unclustered and stratified/unstratified paths must not drift
    # apart — and it is RNG-IDENTICAL to the two branches it replaces: with no
    # clusters and no strata it is one group of `n` single-key items, so
    # `randrange(n)` is called `n` times in the same order; with strata the group
    # order and the per-group counts are today's, each key merely wrapped.
    if clusters is None:
        # `keys` order preserved rather than sorted — the unstratified draw
        # indexed `keys` directly, and sorting here would move an unsorted
        # caller's draw sequence.
        items = [[key] for key in keys]
    else:
        by_cluster: dict[str, list[str]] = {}
        for key in keys:
            # Indexed, not `.get`-ed, the discipline `t_over_units_clustered`
            # states: a key the roster doesn't hold is a core defect, and a
            # cluster of its own for it would raise the count the interval rests
            # on.
            by_cluster.setdefault(clusters[key], []).append(key)
        # Ordered by their own sorted contents rather than by label, so a
        # relabelled roster draws the identical sequence — `percentile_over_units_clustered`'s
        # own invariance, for the same reason.
        items = sorted(sorted(group) for group in by_cluster.values())
    pools: list[list[list[str]]]
    if strata is None:
        pools = [items]
    else:
        if keys != sorted(keys):
            raise ValueError(
                "paired_percentile_of_derived requires keys sorted ascending "
                "when strata is given, since the stratum pools' relabelling "
                "invariance depends on first-occurrence order coinciding with "
                "content order"
            )
        grouped: dict[str, list[list[str]]] = {}
        for item in items:
            rendered = strata[item[0]]
            for key in item:
                # A stratum must be CONSTANT within a drawable thing. With no
                # clusters an item is one key and this cannot fire; with
                # clusters it is the composition of two declarations rather than
                # a third rule, and it is the same fault
                # `percentile_over_units_clustered` raises under the same code —
                # § Errors carries one row per code covering every emit site.
                if strata[key] != rendered:
                    raise ContractError(
                        f"cluster {clusters[key]!r} carries stratum values "
                        f"{rendered!r} and {strata[key]!r}. A resample draws "
                        "whole clusters, so a cluster cannot be drawn within one "
                        "stratum while carrying two; stratify on an attribute "
                        "that is constant within a cluster, or drop `cluster_by` "
                        "if the units really are independent",
                        code="E-STATS-RESAMPLE-STRATIFY-VARIES",
                    )
            grouped.setdefault(rendered, []).append(item)
        pools = [sorted(group) for group in grouped.values()]
        pools.sort()
```

      and replace the draw itself — the `if pools is None:` / `else:` pair inside the loop — with:

```python
        # Each stratum contributes exactly as many DRAWABLE THINGS as it holds,
        # and each contributes all of its keys — "pools their units", so a large
        # cluster contributes more rows than a small one and a replicate's row
        # count varies. ONE drawn key list feeds BOTH sides, under clusters and
        # strata exactly as without: drawing each side independently would
        # resample the two conditions apart and destroy the pairing.
        drawn = [
            key
            for group in pools
            for _ in range(len(group))
            for key in group[rng.randrange(len(group))]
        ]
```

      Then **re-read the whole docstring** and repair what the change made stale: the `strata`
      paragraph now describes a draw over drawable things rather than over keys, and the sentence
      *"`strata` … resamples within each stratum rather than over the whole `keys` list"* must say
      what the item is. Add a paragraph for `clusters` stating the draw, the pooling, and that the
      two compose. **Do not restate the "**Not built here:**" paragraph about the degenerate
      refusal — task 9 deletes it when it builds the refusal.**

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2166 + 4 = 2170 passed**, 1 skipped,
      2 xfailed. **The count matters more than usual here:** every pre-existing `stats` and `cli`
      test that exercises this construction must pass **unmodified**, which is what says the uniform
      shape is RNG-identical. If any of them fails, the rewrite changed a draw sequence — stop and
      fix the shape rather than the test. Then `uv run ruff check .`,
      `uv run ruff format --check .` (80 files), `uv run mypy`.

- [ ] **Step 5: Mutate.**

      **Mutation 1 — draw units instead of clusters.** In the `clusters is not None` branch, change
      `items = sorted(sorted(group) for group in by_cluster.values())` to
      `items = [[key] for key in keys]`.
      `test_the_paired_clustered_percentile_draws_whole_clusters` must **FAIL** on
      `assert set(seen) != {12}`. **Checked against the test body:** the mutant draws 12 single-key
      items every replicate, so `seen` is exactly `{12}` and `min`/`max` are both 12, while the
      correct shape produces a spread of 6 to 18 — the branches cannot agree.

      **Mutation 2 — average the clusters instead of pooling their units.** Change the draw's inner
      `for key in group[rng.randrange(len(group))]` to
      `for key in group[rng.randrange(len(group))][:1]`, taking one key per drawn cluster. The same
      test must **FAIL**: every replicate then pools exactly 3 rows, outside the reachable set. This
      is the "equal say per cluster" error `percentile_over_units_clustered`'s docstring names, and
      **it is invisible under equal cluster sizes** — which is why the fixture's are 2/4/6.

      **Mutation 3 — draw each stratum's clusters from the whole pool.** Change
      `pools = [sorted(group) for group in grouped.values()]` to `pools = [items]`.
      `test_the_paired_clustered_percentile_draws_a_cluster_within_its_stratum` must **FAIL** on
      `assert set(seen) <= {10, 12, 14, 16}`, since 18 becomes reachable.

      **Mutation 4 — the regression.** Change the unclustered `items = [[key] for key in keys]` to
      `items = sorted([key] for key in keys)`.
      `test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was` must **FAIL** for any
      `keys` list that is not already sorted — **and this fixture's IS sorted**, so this mutation is
      **BLIND against it**. Stated rather than prescribed: the fixture that would catch it passes
      `keys` in a shuffled order, and the honest reading is that the sorted-`keys` precondition makes
      the two readings agree for every caller `paired_keys` feeds. Run mutations 1–3; record
      mutation 4 as blind, with this reason.

      Each mutation runs against the **full, unfiltered** suite in the foreground; revert each by
      editing the file back in place.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/stats.py tests/test_stats.py
git commit -m "feat: the paired percentile draw takes whole clusters, within their strata"
```

---

## Task 8: mint `E-DATA-WEIGHT-CLUSTER-CONTRAST`, with both its rows and the de-hedged sentence

**Runs after task 1**, whose ruling this builds, and it carries § Statistical reporting's de-hedged
sentence — see this plan's § Sequencing, deviation (a): a sentence and a guard are one claim seen
from two ends, so they land in one commit.

**Files:**
- Modify: `src/publishable/validate.py`, `docs/reference.md`
- Test: `tests/test_validate.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `validate._check_sweep`'s locals `comparisons` (the resolved contrast family's size),
  `units_here` (the `data.units` declaration, read once for the cluster guard), and its
  `E-DATA-CLUSTER-CONTRAST` emit — read in `src/publishable/validate.py`;
  `tests/test_validate.py`'s `_clustered_units`, `_clustered_table`, `_SITE_BODY`, `_weighted_units`,
  `_weighted_table`, `codes` and `messages_by_code`.
- Produces: the code `E-DATA-WEIGHT-CLUSTER-CONTRAST`, which task 11's `_comparison_step_blocks`
  guard names in its message and task 14 must **not** delete.

**It refuses a combination, so it carries a § Validation row and a § Errors row and is not a
`-UNSUPPORTED` code** — the distinction `CLAUDE.md` § Misreadings draws, and the one that decides
whether it outlives this slice. It survives task 14 untouched.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_validate.py`, beside
      `test_a_clustered_declared_contrast_is_refused`:

```python
def test_a_weighted_clustered_comparison_draws_its_own_refusal(write_config, tmp_path):
    """H4b-2 task 1's ruling: the weight × cluster composition is refused, not
    built. H4b-2 builds the two UNWEIGHTED paired clustered constructions, and a
    weighted clustered contrast would need a df from the cluster count beside a
    weighted mean — a fourth construction whose wrong choice (Kish's effective size
    instead) is invisible in any fixture not built to separate the two.

    Asserted ALONGSIDE `E-DATA-CLUSTER-CONTRAST` rather than as a total code set:
    `validate` collects rather than aborting, both guards read the same resolved
    family, and task 14 deletes the cluster code alone, which must be a one-line
    deletion here."""
    _clustered_table(tmp_path, "patient_id,site,sampling_weight", _WEIGHTED_SITE_BODY)
    path = write_config(
        {
            "data.units": _clustered_units(
                attributes=["site", "sampling_weight"], weight_by="sampling_weight"
            ),
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman"]},
            },
        }
    )
    found = codes(path)
    assert "E-DATA-WEIGHT-CLUSTER-CONTRAST" in found
    assert "E-DATA-CLUSTER-CONTRAST" in found  # deleted by task 14, not narrowed
    message = messages_by_code(path)["E-DATA-WEIGHT-CLUSTER-CONTRAST"]
    assert "weight_by" in message
    assert "cluster_by" in message


def test_a_cluster_without_a_weight_draws_only_the_cluster_refusal(write_config, tmp_path):
    """The under-firing control on one side: the new code reads BOTH declarations,
    so a clustered comparison with no weight must not draw it. Without this, a
    guard that ignored `weight_by` entirely would pass the test above."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": _clustered_units(),
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman"]},
            },
        }
    )
    assert "E-DATA-WEIGHT-CLUSTER-CONTRAST" not in codes(path)


def test_a_weighted_clustered_design_with_no_comparison_stays_legal(write_config, tmp_path):
    """The under-firing control on the other side, and the one that says this
    refuses a COMBINATION rather than a declaration: both declarations together,
    with no baseline and no `statistics.contrasts`, validate free of both contrast
    codes. A weighted clustered run publishing no delta gets
    `weighted_t_over_units_clustered` per condition and nothing here is wrong."""
    _clustered_table(tmp_path, "patient_id,site,sampling_weight", _WEIGHTED_SITE_BODY)
    path = write_config(
        {
            "data.units": _clustered_units(
                attributes=["site", "sampling_weight"], weight_by="sampling_weight"
            )
        }
    )
    found = codes(path)
    assert "E-DATA-WEIGHT-CLUSTER-CONTRAST" not in found
    assert "E-DATA-CLUSTER-CONTRAST" not in found
```

      `_WEIGHTED_SITE_BODY` is new — define it beside `_SITE_BODY` in the same module, as a roster
      whose sites repeat and whose weights are positive and vary within a site:

```python
_WEIGHTED_SITE_BODY = "".join(
    f"p{i},{s},{1 + i % 2}\n" for i, s in enumerate("aaabbbcccddd")
)
```

      That is `_SITE_BODY`'s own roster — twelve units over four sites — with a positive weight that
      varies **within** a site, so no fixture here can make a per-site weight and a per-unit weight
      the same vector. `_clustered_table(tmp_path, header, body)` is the module's helper and writes
      into the directory `write_config` points `data.input_dir` at.

      Then append to `tests/test_cli.py`, beside `test_the_sibling_refusal_rows_state_their_own_reading`:

```python
def test_the_weight_cluster_refusal_has_both_of_its_rows():
    """A refusal of a COMBINATION carries a § Validation row and a § Errors row —
    the two ends of one check — which is what distinguishes it from a
    `-UNSUPPORTED` build-family code and what decides that it outlives H4b-2.

    Each row is located by what it is rather than by position: the § Errors row by
    its final cell, the § Validation row by the code it names."""
    lines = REFERENCE_MD.read_text().split("\n")
    errors_row = next(
        line
        for line in lines
        if line.rstrip().endswith("| `E-DATA-WEIGHT-CLUSTER-CONTRAST` |")
    )
    assert "weight_by" in errors_row
    validation_row = next(
        line
        for line in lines
        if line.startswith("| Weighted clustered deltas aren't computed |")
    )
    assert "cluster_by" in validation_row
```

      **The § Validation row is located by its own first cell, not by slicing § Validation.**
      `_section_text("## Validation")` would return everything down to the next `##` heading — which
      includes § Errors `validate` reports, a `###` inside it — so an `in` over that slice would pass
      off the § Errors row alone and prove nothing about the § Validation table. § Validation's rows
      name no identifiers, which is why the locator is the row's phrasing.

- [ ] **Step 2: Run and see them fail.** The three `test_validate.py` tests fail on the new code's
      absence (the two controls pass already — they are controls, and they are what says the guard
      does not over-fire); the `test_cli.py` test fails with `StopIteration`.

- [ ] **Step 3: Implement.** In `src/publishable/validate.py`, `_check_sweep`, immediately after the
      `E-DATA-CLUSTER-CONTRAST` emit and its comment block, add:

```python
    # A design declaring BOTH a weight and a cluster beside a comparison. H4b-2
    # builds the two unweighted paired clustered constructions `reference.md`
    # § Statistical reporting's suffix rule names, and deliberately not their
    # weighted counterparts: a weighted clustered contrast takes its df from the
    # CLUSTER COUNT and not from Kish's effective size — § Weighted samples,
    # "`cluster_by` still decides the draw when both are declared" — and the two
    # coincide in any fixture not built to separate them, so the wrong choice
    # would be invisible. Refused rather than approximated, on the precedent
    # `E-DATA-CLUSTER-DERIVED` set for a construction that does not exist.
    #
    # Reads the resolved family, for the reason its sibling above does. It refuses
    # a COMBINATION rather than a declaration, so it carries a § Validation row
    # and is not one of the `NOT BUILT` declarations § The one config file counts:
    # both `weight_by` and `cluster_by` are built, and a run declaring both
    # publishes `weighted_t_over_units_clustered` per condition.
    weight_by = units_here.get("weight_by")
    if (
        comparisons > 0
        and isinstance(cluster_by, str)
        and cluster_by
        and isinstance(weight_by, str)
        and weight_by
    ):
        c.error(
            "E-DATA-WEIGHT-CLUSTER-CONTRAST",
            "data.units.weight_by",
            "and `data.units.cluster_by` are both declared beside a comparison, and no "
            "construction in this build computes a weighted clustered delta: the weighted "
            "paired forms take no membership and the clustered paired forms take no "
            "weights. Declare one of the two here — the cluster if what the units share "
            "is what threatens the interval, the weight if what they represent is — or "
            "keep both and express the difference as an `Estimate` returned by a `summary` "
            "step, which core records as reported rather than recomputing",
        )
```

      **Before writing that block, grep `_check_sweep` for an existing `weight_by` local.** The
      retired `E-DATA-WEIGHT-CONTRAST` guard bound that name in this function, and a survivor would be
      silently shadowed. Measured at `82310b9`: no `weight_by` appears anywhere in `_check_sweep`, so
      the binding above is new — **re-check, since tasks 1–5 have committed since.**

      In `docs/reference.md` § Errors `validate` reports, add a two-cell row whose final cell is
      `` `E-DATA-WEIGHT-CLUSTER-CONTRAST` `` and whose first states the check, its resolved-family
      reading and its temporariness — the shape its siblings in that table have.

      In § Validation, add a row beside *Clustered deltas aren't computed*. **That table states each
      check by the mistake it catches and names no identifiers**, so the row is:

```markdown
| Weighted clustered deltas aren't computed | `data.units.weight_by` and `data.units.cluster_by` are both declared and the design resolves to a comparison. The clustered contrast constructions take no weights and the weighted ones take no membership, and a weighted clustered interval's df comes from the cluster count rather than from Kish's effective size — a choice too easy to make silently to leave implicit. Either declaration alone beside a comparison is fine |
```

      In § Statistical reporting, **de-hedge the compose sentence**: replace

```markdown
The `_clustered` suffix does not compose with either weighted form in this build
— [`E-DATA-CLUSTER-CONTRAST`](#errors-validate-reports) refuses a clustered contrast outright.
```

      with

```markdown
The `_clustered` suffix does not compose with either weighted form:
[`E-DATA-WEIGHT-CLUSTER-CONTRAST`](#errors-validate-reports) refuses a design declaring both beside a
comparison, because a weighted clustered interval takes its df from the cluster count rather than
from Kish's effective size and the two coincide too often to leave the choice implicit.
```

      **The hedge is deleted, not moved.** *"in this build"* was true only while
      `E-DATA-CLUSTER-CONTRAST` enforced it, and that code is retired in task 14 — the sentence now
      names the refusal that will still be standing.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2170 + 4 = 2174 passed**, 1 skipped,
      2 xfailed. Then the other three gates, then the mechanical `*.md` pass: both new rows have the
      column count their header declares, every `#anchor` resolves, no trailing whitespace, no en
      dash.

- [ ] **Step 5: Mutate.**

      **Mutation 1 — drop half the guard.** Change `and isinstance(weight_by, str) and weight_by` to
      `and True`. `test_a_cluster_without_a_weight_draws_only_the_cluster_refusal` must **FAIL**.
      **Checked against the test body:** that config declares a cluster and no weight, so the mutant
      fires where the correct guard does not — and the positive test still passes, which is what
      attributes the failure to over-firing rather than to a broken emit.

      **Mutation 2 — the § Errors row.** In `docs/reference.md`, change the new row's final cell to
      `` | `E-DATA-WEIGHT-CLUSTER` | ``. `tests/test_cli.py::test_the_weight_cluster_refusal_has_both_of_its_rows`
      must **FAIL** with `StopIteration`, since the row is located by its final cell.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/validate.py docs/reference.md tests/test_validate.py tests/test_cli.py
git commit -m "feat: E-DATA-WEIGHT-CLUSTER-CONTRAST refuses the composition H4b-2 does not build"
```

---

## Task 9: the content-based degenerate refusal, over all four draw shapes

**Runs after tasks 3 and 7** — task 3 stated the rule in § Statistical reporting, task 7 built the
uniform draw shape this checks over. **It is a separate task from 7 on purpose:** the refusal is
broader than the clustered construction. It closes the zero-width defect H4b-1 filed on the
**existing unclustered stratified** path too, and folding it into task 7 is how that half would
silently disappear.

**Files:**
- Modify: `src/publishable/stats.py`, `docs/superpowers/spec-defects.md`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `stats.paired_percentile_of_derived`'s `pools: list[list[list[str]]]` from task 7;
  `stats.percentile_over_units_clustered`'s own refusal,
  `if all(len({tuple(cluster) for cluster in group}) <= 1 for group in stratum_pools): return None`;
  `stats.PairedResample(interval, draws_used, pool)`.
- Produces: `PairedResample(interval=None, draws_used=0, pool=[])` for a draw that cannot vary — the
  same shape the `len(keys) < 2` early return already builds, and a shape **nothing downstream reads
  `draws_used` off**: `cli`'s contrast path reads only `.interval` and `.pool`, and
  `W-STATS-RESAMPLE-THIN` is emitted from the per-condition path, not this one (read in
  `src/publishable/cli.py`).

**Content, not count, and over the drawable thing.** A count floor answers a different question: two
clusters per stratum carrying identical rows clear it and still cannot vary. And the drawable thing
is what must be compared — a key when nothing is clustered, a whole cluster's pooled rows once
`clusters` is given — so the check is **one expression over four cells** rather than a branch per
cell. An implementer writing two arms leaves two cells wrong, with every existing test passing.

| `clusters` | `strata` | What must be identical for the draw to be refused |
|---|---|---|
| no | no | every key's `(of[k], against[k])` row pair, across the whole `keys` list |
| no | yes | every key's row pair **within each stratum** |
| yes | no | every cluster's sorted multiset of row pairs, across all clusters |
| yes | yes | every cluster's sorted multiset of row pairs **within each stratum** |

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_stats.py`:

```python
@pytest.mark.parametrize("clustered", [False, True])
@pytest.mark.parametrize("stratified", [False, True])
def test_a_paired_draw_that_cannot_vary_reports_no_interval(clustered, stratified):
    """The defect H4b-1 filed against H4b-2 by name, closed for all four draw
    shapes at once. Every drawable thing in every stratum carries the same pair of
    rows, so every replicate reproduces the same difference, both percentile ranks
    land on it, and the interval would be `[x, x]` — a zero-width 95 % interval
    § Statistical reporting refuses in those terms, indistinguishable from a
    genuine narrow one.

    Content, not count: the clustered cells hold TWO clusters per stratum, which
    clears any count floor and is still degenerate."""
    keys = [f"u{i:02d}" for i in range(8)]
    of = {k: {"m": 3.0} for k in keys}
    against = {k: {"m": 1.0} for k in keys}
    clusters = {k: f"c{i // 2}" for i, k in enumerate(keys)} if clustered else None
    strata = {k: ("A" if k < "u04" else "B") for k in keys} if stratified else None
    got = paired_percentile_of_derived(
        of,
        against,
        keys,
        lambda t: sum(t.m) / len(t.m),
        lambda t: sum(t.m) / len(t.m),
        seed=3,
        draws=400,
        strata=strata,
        clusters=clusters,
    )
    assert got.interval is None
    assert got.draws_used == 0
    assert got.pool == []


def test_a_paired_draw_that_can_vary_still_reports():
    """The control that must report, without which every assertion above passes
    identically against a construction that returns `None` for everything. One key
    differs from its neighbours in a single column, which is the smallest content
    difference the refusal must let through."""
    keys = [f"u{i:02d}" for i in range(8)]
    of = {k: {"m": 3.0} for k in keys}
    of["u00"] = {"m": 9.0}
    against = {k: {"m": 1.0} for k in keys}
    got = paired_percentile_of_derived(
        of,
        against,
        keys,
        lambda t: sum(t.m) / len(t.m),
        lambda t: sum(t.m) / len(t.m),
        seed=3,
        draws=400,
    )
    assert got.interval is not None
    assert got.interval.high > got.interval.low
```

- [ ] **Step 2: Run and see them fail.** The four parametrized cases fail on
      `assert got.interval is None` — today the construction returns a zero-width interval, which is
      the defect. The control passes already.

- [ ] **Step 3: Implement.** In `src/publishable/stats.py`, add a module-level helper immediately
      before `paired_percentile_of_derived`:

```python
def _drawable_content(
    item: Sequence[str],
    of: Mapping[str, Mapping[str, float]],
    against: Mapping[str, Mapping[str, float]],
) -> tuple[tuple[tuple[tuple[str, float], ...], tuple[tuple[str, float], ...]], ...]:
    """What a drawable thing contributes to a draw, as a comparable value.

    The pair of rows each of its keys carries, sorted — so two things with the
    same rows in a different key order are the same contribution, which is what
    "the draw cannot vary" has to mean. The keys themselves are deliberately NOT
    in the value: a draw that replaces one key with another carrying identical
    rows produces an identical table, and a signature carrying the key would call
    that a difference.

    **This is the WHOLE row, not the column the compute closure reads**, and that
    makes the refusal narrower than its per-condition siblings, whose own draws
    carry one `(value, weight)` pair each. A collapsed table holding several
    recorded columns can differ on a column this contrast's closure never touches,
    and the refusal then does not fire though that metric's draw cannot vary. The
    filed defect is still closed — a near-unique `stratify_by` puts one drawable
    thing in each stratum, so the check holds however many columns the rows carry
    — but the general case is bounded by this and is not claimed.
    """
    return tuple(
        sorted(
            (tuple(sorted(of[key].items())), tuple(sorted(against[key].items())))
            for key in item
        )
    )
```

      and, in `paired_percentile_of_derived`, immediately after `pools` is built and before
      `values: list[float] = []`:

```python
    # Content-based, not count-based, and applied whether or not `strata` or
    # `clusters` were given. If every drawable thing within a stratum carries the
    # same pair of rows (a stratum holding one of them trivially so), drawing any
    # of them with replacement reproduces the same table on every replicate, so no
    # draw can differ from any other whatever count that stratum holds — and the
    # interval would be `[x, x]`, which `reference.md` § Statistical reporting
    # refuses in those terms. This is `percentile_over_units`'s and
    # `percentile_over_units_clustered`'s own refusal, taken over the paired
    # form's two collapsed tables instead of one column. A count floor answers a
    # different question: two clusters per stratum with identical rows clear it
    # and are still degenerate.
    if all(
        len({_drawable_content(item, of, against) for item in group}) <= 1
        for group in pools
    ):
        return PairedResample(interval=None, draws_used=0, pool=[])
```

      Then delete the docstring's **"Not built here:"** paragraph outright and put the refusal in
      its place — **deleting rather than rewriting**, since the paragraph's whole content was that
      this did not exist.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2174 + 5 = 2179 passed**, 1 skipped,
      2 xfailed (the parametrized test contributes four). **If a pre-existing test fails here, read
      it before changing anything:** the only tests this can break are ones whose fixture gives every
      key identical rows and which assert an interval — that assertion was asserting the defect, and
      the honest move is to report it in the task report and re-point the test at the refusal, not to
      weaken the check. Then the other three gates.

- [ ] **Step 5: Close the filing.** In `docs/superpowers/spec-defects.md`, change the OPEN entry's
      heading from `## OPEN — a stratified paired draw can publish a zero-width contrast interval —
      **Owner: H4b-2**` to `## CLOSED by H4b-2 task 9 — a stratified paired draw could publish a
      zero-width contrast interval`, and append:

```markdown
**CLOSED 2026-08-17 (H4b-2, task 9).** `stats.paired_percentile_of_derived` now refuses a draw whose
every drawable thing within a stratum carries the same pair of rows, returning
`PairedResample(interval=None, draws_used=0, pool=[])` — the shape its `len(keys) < 2` early return
already had. Content-based rather than count-based, and over the **drawable thing** — a key by
default, a whole cluster under `clusters` — so it covers the stratified and unstratified draws and
the clustered and unclustered ones as one expression. The rule was stated in `reference.md`
§ Statistical reporting first, by task 3.

**What is closed and what is bounded.** The filed reachability — a near-unique `stratify_by` making
every draw pick from an identical multiset — is closed outright: one drawable thing per stratum
satisfies the check whatever the rows carry. The check compares **whole collapsed rows**, so a table
holding several recorded columns can differ on a column a given metric's closure never reads, and
that metric's draw can still be constant without the refusal firing. Bounded and stated rather than
claimed away; a signature keyed on the metric the closure reads would close it, and no filed defect
asks for that today.
```

- [ ] **Step 6: Mutate.**

      **Mutation 1 — count instead of content.** Change the refusal's condition to
      `if all(len(group) <= 1 for group in pools):`. The four parametrized cases must **FAIL**:
      every group holds four keys (or two clusters), so the count floor never fires and the
      zero-width interval comes back. **Checked against the test body:** the fixture was sized to
      clear a count floor for exactly this reason, so the two branches provably differ.

      **Mutation 2 — check the key instead of the content.** In `_drawable_content`, change the
      generator's tuple to `(key, tuple(sorted(of[key].items())))`. The four cases must **FAIL**:
      distinct keys make every drawable thing distinct, so the refusal never fires. This is the
      *answering a question with a proxy* shape, and it is the one a reader of this helper is most
      likely to reintroduce.

      **Mutation 3 — the control.** Change `of["u00"] = {"m": 9.0}` in
      `test_a_paired_draw_that_can_vary_still_reports` back to `{"m": 3.0}` and confirm that test
      **FAILS** — proving the control is a control, and that the refusal really is what makes the
      four cases pass rather than a construction that returns `None` for everything.

- [ ] **Step 7: Commit.**

```bash
git add src/publishable/stats.py docs/superpowers/spec-defects.md tests/test_stats.py
git commit -m "fix: a paired draw that cannot vary reports no interval, not a zero-width one"
```

---

## Task 10: thread `clusters` to the contrast path, and select the clustered *t*

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `stats.paired_t_over_units_clustered(diffs, labels, confidence=0.95)` from task 6;
  `cli.command_run`'s `clusters: dict[str, str] | None`, built once as
  `clusters = clusters_of(roster, cluster_by)` from `units.clusters_of`, the single authority
  `validate`, the fold basis and the partition all read — read in `src/publishable/cli.py`;
  `_comparison_step_blocks`' existing keyword-only `weights`, `strata`, `weighted_by` parameters and
  its `col_keys` / `diffs` / `col_weights` locals.
- Produces: a fourth keyword-only parameter on all three functions,

```python
    clusters: dict[str, str] | None = None,
```

  the local `col_clusters: list[str] | None`, and the *t* branch's three-arm construction choice.
  Task 11 adds the percentile branch's `method` selection; task 12 reads `col_clusters` into
  `Member.clusters`; task 13 reads `clusters` for `n_paired_clusters`.

**Defaulted rather than required**, for the reason `weights` and `strata` are: the direct call sites
in the test suite would otherwise take an edit with no behavioural content, and *"no cluster
declared"* and *"this caller has not been taught about clusters"* are the same fact.

**`clusters[k]`, indexed, never `.get`.** `t_over_units_clustered` states the discipline: a key the
roster doesn't hold is a core defect, and absorbing it into a cluster of its own raises the group
count and **narrows** the interval. The roster-wide mapping is safe to index here — `col_keys` is a
subset of the paired intersection, itself a subset of `eval_roster`, itself a subset of the roster
`clusters_of` was built over — and it is **not** the Kish seam: `n_paired_effective` had to be
computed over the intersection because it is a *sum*, while a membership lookup reads only the keys
it is given. Do not "fix" the mapping into a narrowed one.

**This task tests by direct call**, because `validate` gates `run` and `E-DATA-CLUSTER-CONTRAST` is
still alive until task 14.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`, beside
      `test_a_comparison_reads_its_own_condition_not_condition_zero`:

```python
_CONTRAST_CLUSTER_LABELS = ["a"] * 2 + ["b"] * 4 + ["c"] * 6


def _clustered_contrast_call(**extra):
    """`_comparison_step_blocks` over the plan's 12-unit, 3-cluster fixture.

    `of` minus `against` is `1.0 ×2`, `5.0 ×4`, `9.0 ×6` in clusters of 2/4/6, so
    the delta is 6.3333… under EVERY reading — clustering moves the variance, not
    the point estimate — and the half-width is the only arithmetic discriminator:
    8.7632 correct, against 4.4827 at the wrong df, 3.8678 on the IID variance,
    6.1110 at a miscounted cluster and 1.9786 unclustered."""
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.diagnostics import Collector
    from publishable.sweep import Condition
    from publishable.units import Unit, UnitList

    keys = [f"u{i:02d}" for i in range(12)]
    values = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
    roster = UnitList([Unit(key=k) for k in keys])
    # `extra` OVERRIDES rather than adding, so a caller can pass `clusters=None`
    # or `resample_columns=True` without colliding with the defaults below.
    kwargs = dict(
        roster=roster,
        aggregated={1: {"s": {"m": 5.0}}, 0: {"s": {"m": 0.0}}},
        collapsed_by_key={
            (1, "s"): {k: {"m": v} for k, v in zip(keys, values, strict=True)},
            (0, "s"): {k: {"m": 0.0} for k in keys},
        },
        derived_by_key={},
        resample_fns_by_key={},
        seed=7,
        draws=400,
        min_reported_n=None,
        findings=Collector(),
        where="condition 1",
        where_id="cond:1",
        conditions_by_index={
            0: Condition(index=0, label="baseline", is_baseline=True),
            1: Condition(index=1, label="method=spearman", values={"analysis.method": "spearman"}),
        },
        resample_columns=False,
        clusters=dict(zip(keys, _CONTRAST_CLUSTER_LABELS, strict=True)),
    )
    kwargs.update(extra)
    return _comparison_step_blocks(Comparison(id="c", of=1, against=0), **kwargs)


def test_a_clustered_column_contrast_takes_the_cluster_robust_t():
    """The membership reaches the construction, and the construction is the
    cluster-robust one. Both halves are asserted, because a `method` that changed
    without the endpoints — or the reverse — is exactly the half-delivered
    declaration this wiring exists to prevent.

    The delta is asserted too, and it is asserted to be UNCHANGED: 6.3333 is what
    both the clustered and unclustered readings give, which is why it is a control
    here rather than a discriminator."""
    block, _ = _clustered_contrast_call()
    entry = block["s"]["m"]
    assert entry["method"] == "paired_t_over_units_clustered"
    assert entry["delta"] == pytest.approx(6.333333333333333)
    half = (entry["ci95"][1] - entry["ci95"][0]) / 2
    assert half == pytest.approx(8.763214143637903)


def test_an_unclustered_column_contrast_is_untouched():
    """The control that must report, and the number a mutant dropping the mapping
    lands on: the same differences with no `clusters` give `paired_t_over_units`
    and a half-width of 1.9786, a factor of four narrower on the same centre."""
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.diagnostics import Collector
    from publishable.sweep import Condition
    from publishable.units import Unit, UnitList

    keys = [f"u{i:02d}" for i in range(12)]
    values = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
    block, _ = _comparison_step_blocks(
        Comparison(id="c", of=1, against=0),
        roster=UnitList([Unit(key=k) for k in keys]),
        aggregated={1: {"s": {"m": 5.0}}, 0: {"s": {"m": 0.0}}},
        collapsed_by_key={
            (1, "s"): {k: {"m": v} for k, v in zip(keys, values, strict=True)},
            (0, "s"): {k: {"m": 0.0} for k in keys},
        },
        derived_by_key={},
        resample_fns_by_key={},
        seed=7,
        draws=400,
        min_reported_n=None,
        findings=Collector(),
        where="condition 1",
        where_id="cond:1",
        conditions_by_index={
            0: Condition(index=0, label="baseline", is_baseline=True),
            1: Condition(index=1, label="method=spearman", values={"analysis.method": "spearman"}),
        },
        resample_columns=False,
    )
    entry = block["s"]["m"]
    assert entry["method"] == "paired_t_over_units"
    assert (entry["ci95"][1] - entry["ci95"][0]) / 2 == pytest.approx(1.9785385229565593)


def test_a_weighted_clustered_comparison_is_a_core_defect_here_not_a_silent_choice():
    """`E-DATA-WEIGHT-CLUSTER-CONTRAST` refuses the combination at `validate` and
    `cli` always validates before running, so reaching this function with both is a
    bookkeeping error rather than a config. Raised rather than resolved by
    precedence: silently preferring one of the two would publish a `method` naming
    a construction the other declaration contradicts, with nothing in the record
    saying so.

    `ValueError`, not `ContractError`, for the reason `Member.__post_init__` gives:
    the latter is reserved for something a user's code asked for or handed back,
    and nothing here comes from outside core."""
    with pytest.raises(ValueError, match="E-DATA-WEIGHT-CLUSTER-CONTRAST"):
        _clustered_contrast_call(weights={f"u{i:02d}": 1.0 for i in range(12)})
```

- [ ] **Step 2: Run and see them fail.** The first and third fail on
      `TypeError: unexpected keyword argument 'clusters'`; the second passes already, which is what
      makes it the regression control.

- [ ] **Step 3: Implement.** In `src/publishable/cli.py`:

      Add `paired_t_over_units_clustered` to the `from publishable.stats import (...)` block, in its
      alphabetical place.

      Add the parameter to all three signatures — `_comparison_step_blocks`, `_compute_vs_baseline`
      and `_compute_declared_contrasts` — after `weighted_by`:

```python
    clusters: dict[str, str] | None = None,
```

      and pass `clusters=clusters` at `_compute_vs_baseline`'s and `_compute_declared_contrasts`'
      calls to `_comparison_step_blocks`, and at `command_run`'s two calls to those, beside the
      existing `weights=weights` / `strata=resample_strata`.

      At the top of `_comparison_step_blocks`' body, before `differs_on` is computed:

```python
    # `E-DATA-WEIGHT-CLUSTER-CONTRAST` refuses this combination at `validate`, and
    # `cli` always validates before running — so both being set is core's own
    # bookkeeping error, not a config. Raised rather than resolved by precedence:
    # preferring one would publish a `method` naming a construction the other
    # declaration contradicts, and no reader of `run.yaml` could tell. `ValueError`
    # for the reason `Member.__post_init__` gives — nothing here came from outside
    # core.
    if weights is not None and clusters is not None:
        raise ValueError(
            "a weighted clustered comparison has no construction in this build; "
            "E-DATA-WEIGHT-CLUSTER-CONTRAST refuses the combination at validate"
        )
```

      Beside `col_weights`, in the column branch:

```python
                # The intersection's OWN cluster labels, in `col_keys` order, so
                # nothing downstream groups a unit the difference beside it did not
                # come from. Indexed, not `.get`-ed, the discipline
                # `t_over_units_clustered` states: a key the roster doesn't hold is
                # a core defect, and a cluster of its own for it would raise the
                # group count and narrow the interval. The roster-wide mapping is
                # safe to index — `col_keys` is a subset of it — and this is not
                # the Kish seam, which had to be narrowed because it SUMS.
                col_clusters = None if clusters is None else [clusters[k] for k in col_keys]
```

      and replace the `else:` branch's `interval = (...)` conditional expression with:

```python
                else:
                    # The general case, off the resample path. One arm per
                    # declaration, and the weighted-clustered cell is unreachable —
                    # the guard at the top of this function refuses it, so this is
                    # a three-way choice over two independent declarations rather
                    # than a four-cell one with a cell missing.
                    if col_clusters is not None:
                        interval = paired_t_over_units_clustered(diffs, col_clusters)
                    elif col_weights is not None:
                        interval = weighted_paired_t_over_units(diffs, col_weights)
                    else:
                        interval = paired_t_over_units(diffs)
```

      Bind `col_clusters: list[str] | None = None` beside `col_weights`' own pre-branch binding, for
      the reason that one states: the derived branch never assigns it, and task 12 reads it where the
      `Member` is built.

      Then **re-read `_comparison_step_blocks`' whole docstring** and repair what this made stale —
      in particular the paragraph beginning *"A recorded column takes `paired_t_over_units`…"*, which
      now has a third arm, and the `weights`/`strata` paragraph, which now describes one of three
      threaded mappings.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2179 + 3 = 2182 passed**, 1 skipped,
      2 xfailed. Then `uv run ruff check .`, `uv run ruff format --check .` (80 files),
      `uv run mypy` — the explicit `if/elif/else` is what keeps `mypy` able to narrow
      `col_weights`/`col_clusters`; a conditional expression chain here does not narrow.

- [ ] **Step 5: Mutate.**

      **Mutation 1 — drop the mapping at the call site.** In `_compute_vs_baseline`, change
      `clusters=clusters` to `clusters=None` in its call to `_comparison_step_blocks`. Nothing in
      this task's tests fails — they call `_comparison_step_blocks` **directly**, so this mutation is
      **BLIND against them**, and it is recorded rather than prescribed. **The test that catches it
      is task 14's `run`-through half**, which is the first fixture to travel the whole path; task 14
      names this mutation again for that reason. Do not conclude the threading is unreachable —
      *"reading a mutation's silence as confirmation"* is how this repo has twice deleted a live
      payload.

      **Mutation 2 — the construction choice.** Change `if col_clusters is not None:` to
      `if col_clusters is None:` in the *t* branch.
      `test_a_clustered_column_contrast_takes_the_cluster_robust_t` must **FAIL** on the `method`
      assertion (an unweighted unclustered call takes the clustered arm with an empty label list and
      raises, or takes the plain arm — either way the assertion cannot hold), **and**
      `test_an_unclustered_column_contrast_is_untouched` must **FAIL** on its half-width. Two tests
      failing in opposite directions is what makes this mutation's branches provably different.

      **Mutation 3 — the alignment.** Change `[clusters[k] for k in col_keys]` to
      `[clusters[k] for k in sorted(clusters)]`. With this fixture the two are the same list, so
      **this mutation is BLIND** — `col_keys` *is* the sorted roster here. Recorded rather than
      prescribed, with the fixture that would catch it: a comparison whose intersection is a strict
      subset of the roster (one condition failing to complete on two units), where the roster-order
      vector is longer than `diffs` and `zip(..., strict=True)` inside
      `paired_t_over_units_clustered` raises. **Task 13 builds that fixture** for `n_paired_clusters`
      and it catches this mutation there.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/cli.py tests/test_cli.py
git commit -m "feat: a clustered column contrast takes the cluster-robust paired t"
```

---

## Task 11: the `method`-selection branch, six cells counted rather than carried

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: task 7's `paired_percentile_of_derived(..., clusters=)` and its
  `"paired_percentile_over_units_clustered"` `method` string; task 10's `clusters` parameter,
  `col_clusters` local and weighted-clustered guard; `_comparison_step_blocks`' existing
  `method=("paired_percentile_over_units" if weights is None else
  "weighted_paired_percentile_over_units")` argument — read in `src/publishable/cli.py`.
- Produces: every reachable `(weights, clusters, resample_columns)` cell writing the `method` string
  § Statistical reporting's tables and suffix rule define for it.

**Six cells, counted rather than carried.** *Build the composition* would give eight; task 1's
*mint the refusal* removes the two weighted-clustered ones:

| `weights` | `clusters` | `resample_columns` | `method` |
|---|---|---|---|
| no | no | no | `paired_t_over_units` |
| no | no | yes | `paired_percentile_over_units` |
| no | yes | no | `paired_t_over_units_clustered` |
| no | yes | yes | `paired_percentile_over_units_clustered` |
| yes | no | no | `weighted_paired_t_over_units` |
| yes | no | yes | `weighted_paired_percentile_over_units` |

**It is two sites, not one branch**, and that is why this table is the deliverable rather than a
single expression: the *t* arm's `method` comes from **the construction it calls** (each
`stats` function stamps its own), while the percentile arm's comes from a **`method=` argument** the
caller passes, because one construction serves three spellings. An implementer looking for "the
six-way branch" will not find it. Task 10 wired the first site; this task wires the second and
asserts all six together, so no cell can fall through to a wrong `method` — decision 2's failure one
axis over, and again with every existing test passing, because the refused cells have no fixture.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`, beside task 10's tests:

```python
@pytest.mark.parametrize(
    "weighted,clustered,resampled,expected",
    [
        (False, False, False, "paired_t_over_units"),
        (False, False, True, "paired_percentile_over_units"),
        (False, True, False, "paired_t_over_units_clustered"),
        (False, True, True, "paired_percentile_over_units_clustered"),
        (True, False, False, "weighted_paired_t_over_units"),
        (True, False, True, "weighted_paired_percentile_over_units"),
    ],
)
def test_every_reachable_contrast_cell_writes_its_own_method(
    weighted, clustered, resampled, expected
):
    """Every reachable combination of `weight_by`, `cluster_by` and a declared
    `resample`, and the `method` § Statistical reporting defines for each — the two
    weighted-clustered cells being refused at `validate` by
    `E-DATA-WEIGHT-CLUSTER-CONTRAST` and so absent by construction.

    Asserted as a table rather than one cell at a time because the failure this
    guards is a cell FALLING THROUGH to a neighbour's `method`: an implementer
    writing four arms leaves two cells publishing a string that names a
    construction the run did not use, and every existing test still passes, since
    nothing else builds those fixtures.

    The `method` is asserted against the value the emitting code writes; that it is
    a string the document defines is a separate pin,
    `test_a_clustered_contrast_method_is_one_the_document_defines` below."""
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.diagnostics import Collector
    from publishable.sweep import Condition
    from publishable.units import Unit, UnitList

    keys = [f"u{i:02d}" for i in range(12)]
    values = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
    block, _ = _comparison_step_blocks(
        Comparison(id="c", of=1, against=0),
        roster=UnitList([Unit(key=k) for k in keys]),
        aggregated={1: {"s": {"m": 5.0}}, 0: {"s": {"m": 0.0}}},
        collapsed_by_key={
            (1, "s"): {k: {"m": v} for k, v in zip(keys, values, strict=True)},
            (0, "s"): {k: {"m": 0.0} for k in keys},
        },
        derived_by_key={},
        resample_fns_by_key={},
        seed=7,
        draws=400,
        min_reported_n=None,
        findings=Collector(),
        where="condition 1",
        where_id="cond:1",
        conditions_by_index={
            0: Condition(index=0, label="baseline", is_baseline=True),
            1: Condition(index=1, label="method=spearman", values={"analysis.method": "spearman"}),
        },
        resample_columns=resampled,
        weights={k: 1 + i % 2 for i, k in enumerate(keys)} if weighted else None,
        weighted_by="sampling_weight" if weighted else None,
        clusters=(
            dict(zip(keys, _CONTRAST_CLUSTER_LABELS, strict=True)) if clustered else None
        ),
    )
    assert block["s"]["m"]["method"] == expected


def test_a_clustered_resampled_contrast_really_drew_clusters():
    """The `method` string and the draw are two claims, and the parametrized table
    above pins only the first. A `method` naming a construction the draw did not
    perform is the whole failure this slice was ordered around — so the DRAW is
    asserted here, by the only evidence available at this level: the same fixture,
    resampled, with and without the membership must produce DIFFERENT intervals.

    A clustered draw takes 3 things from {2, 4, 6} units and pools them; a unit
    draw takes 12 units. On differences of 1.0/5.0/9.0 concentrated by cluster
    those distributions are not close, and identical endpoints would mean the
    membership never reached the construction.

    The clustered endpoints are recorded as literals beside the inequality, so a
    later change cannot move the draw while keeping the two merely unequal. Capture
    them from the first green run of this test and paste them in."""
    clustered, _ = _clustered_contrast_call(resample_columns=True)
    plain, _ = _clustered_contrast_call(resample_columns=True, clusters=None)
    assert clustered["s"]["m"]["method"] == "paired_percentile_over_units_clustered"
    assert plain["s"]["m"]["method"] == "paired_percentile_over_units"
    assert clustered["s"]["m"]["ci95"] != plain["s"]["m"]["ci95"]
    assert clustered["s"]["m"]["ci95"] == pytest.approx([0.0, 0.0])  # paste the run's


def test_a_clustered_contrast_method_is_one_the_document_defines():
    """The agreement between the emitted string and § Statistical reporting, pinned
    against the DOCUMENT rather than against a second literal — a test comparing
    each of two spellings to its own hard-coded string is how this repo shipped a
    name claiming an agreement no assertion made.

    The suffix rule is what licenses these two, so the assertion is that the
    unsuffixed stem is a defined `method` and the emitted string is that stem plus
    `_clustered`. `_interval_method_names` parses both construction tables."""
    names = _interval_method_names()
    for stem in ("paired_t_over_units", "paired_percentile_over_units"):
        assert stem in names  # the control: the tables were parsed
        assert f"{stem}_clustered" not in names  # the suffix rule, not a row
```

- [ ] **Step 2: Run and see them fail.** The `(False, True, True)` case fails, writing
      `paired_percentile_over_units` where the clustered spelling is expected. The other five pass —
      four from task 10 and H4b-1, one from the same. The document test passes already and is the
      control that the suffix rule, not a row, is what licenses the new spellings.

- [ ] **Step 3: Implement.** In `src/publishable/cli.py`, `_comparison_step_blocks`, in the
      `resample_columns and n_paired >= 2` branch, pass the membership and select the third spelling:

```python
                    resampled = paired_percentile_of_derived(
                        of_collapsed,
                        against_collapsed,
                        col_keys,
                        _column_mean,
                        _column_mean,
                        seed,
                        draws=draws,
                        strata=strata,
                        # One spelling per declaration, and the weighted-clustered
                        # cell is unreachable — the guard at the top of this
                        # function refuses it. The construction is ONE function
                        # serving three `method` strings, so the string is the
                        # caller's to pass: `paired_percentile_of_derived` is
                        # shared with the derived branch, which core neither
                        # weights nor clusters.
                        method=(
                            "paired_percentile_over_units_clustered"
                            if clusters is not None
                            else "weighted_paired_percentile_over_units"
                            if weights is not None
                            else "paired_percentile_over_units"
                        ),
                        clusters=(
                            None if clusters is None else {k: clusters[k] for k in col_keys}
                        ),
                    )
```

      **`col_keys`' own membership, not the roster-wide mapping**: `paired_percentile_of_derived`
      builds its cluster pools by walking `keys`, so a roster-wide mapping would contribute no extra
      pools — but narrowing it here makes the vector's provenance the same as `col_weights`' and
      `col_clusters`', which is the discipline `summarize_step` keeps one level over. The dict
      comprehension is over `col_keys`, so a key the mapping lacks raises here rather than being
      invented a cluster.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2182 + 8 = 2190 passed**, 1 skipped,
      2 xfailed (the parametrized test contributes six). Then the other three gates.

- [ ] **Step 5: Mutate.**

      **Mutation 1 — a cell falls through.** Change the `method=` selection's first arm to
      `"paired_percentile_over_units" if clusters is not None else ...`. The parametrized test's
      `(False, True, True)` case must **FAIL** and the other five must **PASS** — which is what says
      the table catches a fall-through at the cell rather than anywhere.

      **Mutation 2 — the membership never reaches the draw.** Change `clusters=(None if clusters is
      None else {k: clusters[k] for k in col_keys})` to `clusters=None`. The **parametrized test
      still passes**, because the `method` string is a separate argument — that silence is evidence
      about *that* test, not about the code, and it is exactly why
      `test_a_clustered_resampled_contrast_really_drew_clusters` exists. **That** test must **FAIL**
      on `clustered[...]["ci95"] != plain[...]["ci95"]`: with the membership dropped, the two calls
      differ in nothing but a `method` string and return byte-identical intervals. A `method` naming
      a construction the draw did not perform is decision 2's failure verbatim, and this is the one
      mutation that reaches it.

      **Mutation 3 — the narrowing.** Change `{k: clusters[k] for k in col_keys}` to `clusters`.
      **Blind against every fixture in this task**, since `col_keys` is the whole roster here — and
      blind for a second reason worth knowing: `paired_percentile_of_derived` builds its pools by
      walking `keys`, so a wider mapping contributes no extra pools and the draw is unchanged. The
      narrowing is a provenance discipline rather than an arithmetic one. Recorded, not prescribed.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/cli.py tests/test_cli.py
git commit -m "feat: every reachable contrast cell writes its own method string"
```

---

## Task 12: `Member.clusters` and the corrected bound

**Runs after task 6**, whose construction `_corrected_bounds` calls — and `correction.py` is that
construction's **first** production caller, exactly as H4b-1's spec correction 2 found for the
weighted form. The charter names this file nowhere.

**Files:**
- Modify: `src/publishable/correction.py`, `src/publishable/cli.py`
- Test: `tests/test_correction.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `stats.paired_t_over_units_clustered(diffs, labels, confidence=0.95)` from task 6;
  `correction.Member`'s frozen fields `where, step, metric, delta, ci95, pool, diffs,
  declaration_index, weights` and its `__post_init__` rules — read in
  `src/publishable/correction.py`; `_corrected_bounds(member, level)`'s `diffs`-first ordering; task
  10's `col_clusters` local.
- Produces:

```python
    clusters: tuple[str, ...] | None = None
```

  on `Member`, set by `cli._comparison_step_blocks` where `weights` is set, and read by
  `_corrected_bounds`.

**A modifier on `diffs`, not a third kind of evidence** — `weights`' own words, and the same three
consequences: it never travels beside `pool` (a percentile pool is already drawn from clusters, so a
membership beside one would be applied twice), it must be the same length as `diffs` (a different
length is a misaligned vector, the failure class that produces a plausible number rather than an
error), and it does not enter the exactly-one-of-`pool`/`diffs` rule.

**And it never travels beside `weights`.** The combination is refused at `validate` and again by
`_comparison_step_blocks`' own guard, so a member carrying both is core's bookkeeping error — checked
here rather than left to the two callers to remember.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_correction.py`:

```python
def test_a_clustered_members_corrected_bound_is_the_clustered_construction():
    """The corrected interval is the raw one at a smaller α, from the same
    evidence — so a member whose raw interval was cluster-robust must not get an
    unclustered counterpart. `correction.py` is this construction's FIRST caller.

    At α = 0.05 the bound is the plan's 8.7632 half-width; at α = 0.01 it is
    t(0.995, df 2) = 9.924843 times the same standard error 2.0366934, i.e.
    20.2139. The unclustered counterpart at α = 0.01 would be 2.7919 — two
    numbers no rounding can confuse, and both are asserted so a construction that
    ignored the level would fail as loudly as one that ignored the membership."""
    diffs = tuple([1.0] * 2 + [5.0] * 4 + [9.0] * 6)
    labels = tuple(["a"] * 2 + ["b"] * 4 + ["c"] * 6)
    member = Member(
        where="cond:1",
        step="s",
        metric="m",
        delta=6.333333333333333,
        ci95=(6.333333333333333 - 8.763214143637903, 6.333333333333333 + 8.763214143637903),
        pool=None,
        diffs=diffs,
        declaration_index=0,
        clusters=labels,
    )
    raw_half = (member.ci95[1] - member.ci95[0]) / 2
    assert raw_half == pytest.approx(8.763214143637903)
    bounds = _corrected_bounds(member, 0.01)
    assert bounds is not None
    assert (bounds[1] - bounds[0]) / 2 == pytest.approx(20.213931212789273)


def test_a_member_may_not_carry_clusters_beside_a_pool_or_a_weight():
    """`clusters` is a modifier on `diffs`, so the same three rules `weights`
    carries. Beside a pool it would be applied twice — a clustered percentile pool
    is already drawn from clusters. Beside `weights` it names a combination
    `E-DATA-WEIGHT-CLUSTER-CONTRAST` refuses at `validate` and
    `_comparison_step_blocks` refuses again, so a member holding both is core's
    bookkeeping error. At the wrong length it is a misaligned vector, which
    produces a plausible number rather than an error."""
    common = {
        "where": "cond:1",
        "step": "s",
        "metric": "m",
        "delta": 1.0,
        "ci95": (0.0, 2.0),
        "declaration_index": 0,
    }
    with pytest.raises(ValueError, match="clusters"):
        Member(pool=(1.0, 2.0), diffs=None, clusters=("a", "b"), **common)
    with pytest.raises(ValueError, match="clusters"):
        Member(pool=None, diffs=(1.0, 2.0), clusters=("a",), **common)
    with pytest.raises(ValueError, match="clusters"):
        Member(
            pool=None,
            diffs=(1.0, 2.0),
            clusters=("a", "b"),
            weights=(1.0, 1.0),
            **common,
        )
```

      And append to `tests/test_cli.py`, beside task 11's tests:

```python
def test_a_clustered_contrast_member_carries_its_membership_and_no_pool():
    """The member is what the correction family rebuilds from, so a clustered raw
    interval whose member carried no membership would get an unclustered corrected
    counterpart — narrower by construction rather than by evidence, and undetectable
    in `run.yaml`. Asserted beside `pool is None`, because `_corrected_bounds` tests
    `diffs` first and a member carrying both would take the wrong branch."""
    _, members = _clustered_contrast_call()
    assert len(members) == 1
    assert members[0].clusters == tuple(_CONTRAST_CLUSTER_LABELS)
    assert members[0].pool is None
    assert members[0].weights is None
```

      `Member` and `_corrected_bounds` are already imported by `tests/test_correction.py`; check its
      import block and add only what is missing.

- [ ] **Step 2: Run and see them fail.** All three fail on `Member` having no `clusters` field —
      `TypeError: unexpected keyword argument`.

- [ ] **Step 3: Implement.** In `src/publishable/correction.py`:

      Import `paired_t_over_units_clustered` alongside the two paired *t* forms already imported.

      Add the field after `weights`:

```python
    clusters: tuple[str, ...] | None = None
```

      Extend `Member`'s docstring — a paragraph, beside `weights`' own, saying `clusters` is one
      cluster label per difference in the same order, a modifier on `diffs` for the same reason, and
      never beside `weights` because that combination is refused at `validate`.

      In `__post_init__`, beside the `weights` block:

```python
        if self.clusters is not None:
            if self.pool is not None:
                raise ValueError(
                    "Member clusters modify diffs, not a pool; a clustered percentile "
                    "pool is already drawn from whole clusters"
                )
            if self.diffs is None or len(self.clusters) != len(self.diffs):
                raise ValueError(
                    "Member clusters must be the same length as diffs, not "
                    f"{len(self.clusters)} against "
                    f"{'no diffs' if self.diffs is None else len(self.diffs)}"
                )
            if self.weights is not None:
                raise ValueError(
                    "Member may not carry both weights and clusters; "
                    "E-DATA-WEIGHT-CLUSTER-CONTRAST refuses that combination at validate"
                )
```

      In `_corrected_bounds`, replace the `diffs` branch's conditional expression with:

```python
    if member.diffs is not None:
        # WHICH t construction rebuilds the bound is decided by the modifier the
        # member carries — the same evidence at a smaller α either way. A
        # cluster-robust raw interval with an unclustered corrected counterpart is
        # narrower by construction rather than by evidence, which is the fault the
        # exactly-one rule refuses one axis over and which no reader of `run.yaml`
        # could detect. The two modifiers are mutually exclusive by
        # `__post_init__`, so this order is a preference among impossible-to-have-both
        # fields rather than a tie-break.
        if member.clusters is not None:
            got = paired_t_over_units_clustered(
                member.diffs, member.clusters, confidence=1.0 - level
            )
        elif member.weights is not None:
            got = weighted_paired_t_over_units(
                member.diffs, member.weights, confidence=1.0 - level
            )
        else:
            got = paired_t_over_units(member.diffs, confidence=1.0 - level)
        return None if got is None else (got.low, got.high)
```

      Then **re-read `_corrected_bounds`' whole docstring** and repair its opening claim, which
      enumerates what decides the construction and is now short by one.

      In `src/publishable/cli.py`, in the `Member(...)` construction, beside `weights=`:

```python
                    clusters=(
                        None if corrected_from_pool or col_clusters is None else tuple(col_clusters)
                    ),
```

      **`corrected_from_pool` is the single decision, read once for all three fields**, so `pool`,
      `weights` and `clusters` cannot disagree about which evidence this member carries.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2190 + 3 = 2193 passed**, 1 skipped,
      2 xfailed — **three**, not four: two of this task's tests are in `tests/test_correction.py` and
      one in `tests/test_cli.py`. Then the other three gates.

- [ ] **Step 5: Mutate.**

      **Mutation 1 — the corrected construction.** In `_corrected_bounds`, change
      `if member.clusters is not None:` to `if member.clusters is None:`.
      `test_a_clustered_members_corrected_bound_is_the_clustered_construction` must **FAIL**: the
      member's `diffs` then take the plain form and the α = 0.01 half-width comes back 2.7919 against
      the asserted 20.2139. **Checked against the test body:** the assertion is on the number, not on
      "is it wider", so the two branches produce values a factor of seven apart.

      **Mutation 2 — the member's field.** In `src/publishable/cli.py`, change `clusters=(...)` to
      `clusters=None`.
      `tests/test_cli.py::test_a_clustered_contrast_member_carries_its_membership_and_no_pool` must
      **FAIL** on the first assertion. The raw interval is unaffected, which is exactly the split
      this test exists to catch: a correct raw number beside a corrected one built from different
      evidence.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/correction.py src/publishable/cli.py tests/test_correction.py tests/test_cli.py
git commit -m "feat: a clustered member's corrected bound is the clustered construction"
```

---

## Task 13: `n_paired_clusters` on every affected entry

**Runs after task 2**, which documented the key — a record key must exist in a document before code
writes it.

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `units.cluster_count_of(membership, keys) -> int`, **the single counting expression**
  that `attrition`'s `n.clusters`, `t_over_units_clustered`'s df and a fold's partition all read —
  read in `src/publishable/units.py`; `_comparison_step_blocks`' `weights is not None` record block,
  which writes `weighted_by` and `n_paired_effective` over `base_keys if is_derived else col_keys`;
  task 10's `clusters` parameter.
- Produces: `n_paired_clusters` on every contrast entry of a clustered run — the last of the three
  facts that must move together.

**`cluster_count_of`, never `len(set(labels))`.** A second counting expression is exactly how the
`n.clusters` printed beside an interval and the df inside it come to disagree, which
`t_over_units_clustered`'s docstring argues at length. Add `cluster_count_of` to `cli.py`'s
`from publishable.units import (...)` block.

**The three that move together are interval, `method` and `n_paired_clusters`** — **not** `cohens_d`,
which is *d*z over the differences and which § Statistical reporting defines no clustered form of.
H4b-1 pinned a three-way obligation for weights after `weighted_by`'s value passed under a hardcoded
constant; the obligation is the same and the *members* are different.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_cli.py`, beside task 12's test:

```python
def test_a_clustered_contrast_entry_carries_its_cluster_count():
    """§ Contrasts: the cluster count is a scalar sibling of `n_paired`, and it is
    the count the interval's df was taken from, so a reader can check `clusters − 1`
    against the interval rather than take it on trust.

    All three facts are asserted together — interval, `method`, count — because a
    count beside an unclustered interval, or a clustered interval with no count, is
    a declaration accepted whose effect is half delivered. `cohens_d` is asserted
    to be the UNCLUSTERED number, because it is: *d*z is over the differences and
    § Statistical reporting defines no clustered effect size."""
    block, _ = _clustered_contrast_call()
    entry = block["s"]["m"]
    assert entry["n_paired"] == 12
    assert entry["n_paired_clusters"] == 3
    assert entry["method"] == "paired_t_over_units_clustered"
    assert (entry["ci95"][1] - entry["ci95"][0]) / 2 == pytest.approx(8.763214143637903)
    assert entry["cohens_d"] == pytest.approx(2.0338284916219784)


def test_an_unclustered_contrast_entry_grows_no_cluster_count():
    """Absent, not null — the same absent-not-null shape `weighted_by` already has.
    An explicit null would claim a cluster count was computed and found nothing."""
    _, _ = _clustered_contrast_call()  # the control: the key IS written somewhere
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.diagnostics import Collector
    from publishable.sweep import Condition
    from publishable.units import Unit, UnitList

    keys = [f"u{i:02d}" for i in range(12)]
    block, _ = _comparison_step_blocks(
        Comparison(id="c", of=1, against=0),
        roster=UnitList([Unit(key=k) for k in keys]),
        aggregated={1: {"s": {"m": 5.0}}, 0: {"s": {"m": 0.0}}},
        collapsed_by_key={
            (1, "s"): {k: {"m": 1.0 + i} for i, k in enumerate(keys)},
            (0, "s"): {k: {"m": 0.0} for k in keys},
        },
        derived_by_key={},
        resample_fns_by_key={},
        seed=7,
        draws=400,
        min_reported_n=None,
        findings=Collector(),
        where="condition 1",
        where_id="cond:1",
        conditions_by_index={
            0: Condition(index=0, label="baseline", is_baseline=True),
            1: Condition(index=1, label="method=spearman", values={"analysis.method": "spearman"}),
        },
        resample_columns=False,
    )
    assert "n_paired_clusters" not in block["s"]["m"]


def test_a_ragged_clustered_column_counts_only_the_clusters_it_was_computed_over():
    """The seam a whole-roster count cannot see, and the fixture the alignment
    mutations in tasks 10 and 11 need. Two units carry the column on one side only,
    so `col_keys` is a strict subset of the roster — and both of them are cluster
    `a`'s entire membership, so the roster holds three clusters and the difference
    was computed over two.

    A count over the roster-wide mapping says 3; a count over `col_keys` says 2,
    which is the number the df beside it used. Three distinct readings —
    `n_paired` 10, roster clusters 3, computed clusters 2 — so no two can be
    confused."""
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.diagnostics import Collector
    from publishable.sweep import Condition
    from publishable.units import Unit, UnitList

    keys = [f"u{i:02d}" for i in range(12)]
    values = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
    of_collapsed = {k: {"m": v} for k, v in zip(keys, values, strict=True)}
    against_collapsed = {k: {"m": 0.0} for k in keys}
    for ragged in keys[:2]:  # cluster `a` entire
        against_collapsed[ragged] = {"other": 0.0}
    block, members = _comparison_step_blocks(
        Comparison(id="c", of=1, against=0),
        roster=UnitList([Unit(key=k) for k in keys]),
        aggregated={1: {"s": {"m": 5.0}}, 0: {"s": {"m": 0.0}}},
        collapsed_by_key={(1, "s"): of_collapsed, (0, "s"): against_collapsed},
        derived_by_key={},
        resample_fns_by_key={},
        seed=7,
        draws=400,
        min_reported_n=None,
        findings=Collector(),
        where="condition 1",
        where_id="cond:1",
        conditions_by_index={
            0: Condition(index=0, label="baseline", is_baseline=True),
            1: Condition(index=1, label="method=spearman", values={"analysis.method": "spearman"}),
        },
        resample_columns=False,
        clusters=dict(zip(keys, _CONTRAST_CLUSTER_LABELS, strict=True)),
    )
    entry = block["s"]["m"]
    assert entry["n_paired"] == 10
    assert entry["n_paired_clusters"] == 2
    assert members[0].clusters == ("b",) * 4 + ("c",) * 6
```

      Read `_comparison_step_blocks`' `col_keys` filter before running this — it keeps a key only
      where `metric_key in of_collapsed[k] and metric_key in against_collapsed[k]` — and if the
      ragged shape above does not produce a ten-key intersection, build the raggedness the way that
      filter actually reads and say so in the task report.

- [ ] **Step 2: Run and see them fail.** The first fails on `n_paired_clusters` being absent, the
      third likewise; the second passes already and is the absent-not-null control.

- [ ] **Step 3: Implement.** In `src/publishable/cli.py`, add `cluster_count_of` to the
      `from publishable.units import (...)` block in its alphabetical place, and add — immediately
      after the `if weights is not None:` record block:

```python
            # The one fact a cluster adds to a contrast entry, and it moves with
            # the interval and the `method`: § Contrasts requires it, and a
            # cluster-robust delta beside a `method` that does not say so, or with
            # no count for a reader to check `clusters − 1` against, is a
            # declaration accepted whose effect is half delivered. Absent — not
            # null — when nothing is clustered, the same absent-not-null shape
            # `weighted_by` has.
            #
            # `cluster_count_of` is the SINGLE counting expression — the one
            # `attrition`'s `n.clusters` and `t_over_units_clustered`'s df both
            # read — so the count printed beside an interval cannot disagree with
            # the df inside it. `len(set(...))` here would be a second authority
            # for one number.
            #
            # Over the keys the difference was actually computed over, never the
            # roster-wide mapping: a ragged column's clusters are its own, and a
            # count over the roster would claim a df the interval never used.
            if clusters is not None:
                # The `is_derived` arm is unreachable under a declared cluster —
                # `summarize_step` raises `E-DATA-CLUSTER-DERIVED` and the whole
                # derived mapping is dropped before it reaches `aggregated`, so no
                # metric here is derived. Written the same shape as the weighted
                # block beside it rather than dropped, because the two must not
                # disagree about which key set a fact is computed over if that
                # refusal is ever lifted.
                metric_block[metric_key]["n_paired_clusters"] = cluster_count_of(
                    clusters, base_keys if is_derived else col_keys
                )
```

      Then extend `command_run`'s comment about `clusters` travelling in `attrition` — the one that
      says *"nothing in the documents shows a `clustered_by` sibling of `weighted_by`"* — so it
      records **why** rather than only what: a contrast entry's `_clustered` `method` suffix
      discloses the clustering, so a name would be a second disclosure of one fact, while the count
      is a new one and travels as `n_paired_clusters`.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2193 + 3 = 2196 passed**, 1 skipped,
      2 xfailed. Then the other three gates.

- [ ] **Step 5: Mutate.**

      **Mutation 1 — count the roster, not the column.** Change
      `cluster_count_of(clusters, base_keys if is_derived else col_keys)` to
      `cluster_count_of(clusters, clusters.keys())`.
      `test_a_ragged_clustered_column_counts_only_the_clusters_it_was_computed_over` must **FAIL**,
      seeing 3 where 2 is asserted, while
      `test_a_clustered_contrast_entry_carries_its_cluster_count` still **PASSES** — the two counts
      coincide on the un-ragged fixture, which is precisely why the ragged one had to be built. This
      is the *"a dimension no assertion can see"* shape, closed.

      **Mutation 2 — a second counting authority.** Change the call to `len(set(clusters.values()))`.
      The ragged test must **FAIL** for the same reason, and this is the mutation that says the
      single-expression rule is load-bearing rather than stylistic.

      **Mutation 3 — the alignment task 10 could not catch.** Now run task 10's mutation 3 again:
      change `[clusters[k] for k in col_keys]` to `[clusters[k] for k in sorted(clusters)]`. The
      ragged test must **FAIL** — the label vector is 12 long against 10 differences, and
      `paired_t_over_units_clustered`'s `zip(..., strict=True)` raises. Recorded here because task 10
      named this fixture as the one that would catch it.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/cli.py tests/test_cli.py
git commit -m "feat: a clustered contrast entry records n_paired_clusters"
```

---

## Task 14: retire `E-DATA-CLUSTER-CONTRAST`, and run a clustered contrast end to end

**LAST of the code tasks.** A refusal is deleted only after everything it stood in for exists —
deleting the emit any earlier routes a declared cluster to the **unclustered** construction, which
publishes `method: paired_t_over_units` beside per-condition values that *are*
`t_over_units_clustered`, with nothing in the record saying which is which **and every existing test
passing**, because the combination is refused today and no fixture exercises it.

**Files:**
- Modify: `src/publishable/validate.py`, `docs/reference.md`
- Test: `tests/test_validate.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: everything tasks 6–13 built. Nothing later consumes this task; tasks 15–18 are residue,
  regression and record.
- Produces: a clustered comparison that validates clean and runs.

**Every site, enumerated by READING and then confirmed by grep** — that order, per `CLAUDE.md`
§ Answering a question with a proxy, and the grep filters the file list rather than the output. The
enumeration below was taken at `82310b9`:

| Site | This task |
|---|---|
| `validate._check_sweep`'s emit and its whole comment block | **Delete.** The comment carries the *"none of those five constructions exists"* claim, which dies with it |
| `docs/reference.md` § Errors `validate` reports, the row whose final cell is the code | **Delete** |
| `docs/reference.md` § Validation, *Clustered deltas aren't computed* | **Delete** |
| `docs/reference.md` § Validation, *Allocation deltas aren't computed* | **Re-word.** It cites the deleted row **by name** to state its own per-comparison reading against that row's per-family one |
| `tests/test_validate.py`'s section-header comment above `_clustered_units` | **Delete** — it carries the same "five" claim |
| `tests/test_validate.py`, five assertions naming the code as a total set or a message | See below, by test name |
| `tests/test_validate.py::test_an_unclustered_comparison_is_untouched`'s `not in` assertion | **Re-point**, not delete |
| `tests/test_validate.py::test_a_contrast_beside_groups_and_cluster_by_draws_both_refusals` | **Narrow to the allocation code**, never delete — it pins `validate`'s collect-don't-abort property |
| `tests/test_cli.py::test_the_sibling_refusal_rows_state_their_own_reading` | **Narrow.** It locates the deleted § Errors row with `next(...)` and will raise `StopIteration` |
| Task 5's and task 8's tests, which assert the code **alongside** their own finding | **Delete one line each** — which is what asserting alongside bought |

**Everything else that names the code SURVIVES and is task 15's**, not this task's: three
`validate.py` comments, `stats.summarize_step`'s docstring, `E-DATA-CLUSTER-DERIVED`'s § Errors row,
and § Statistical reporting's compose sentence (already de-hedged by task 8, and it now names
`E-DATA-WEIGHT-CLUSTER-CONTRAST` instead — verify, do not assume).

- [ ] **Step 1: Re-enumerate before touching anything.** Read `validate._check_sweep` in full, then
      run, filtering the **file list**:

```
grep -rn "E-DATA-CLUSTER-CONTRAST" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ tests/
```

      Compare against the table above and **report any site the table does not name** — the table was
      measured at `82310b9` and tasks 1–13 have committed since.

- [ ] **Step 2: Write the two failing tests — the halves only this task can carry.** Append to
      `tests/test_validate.py`, beside `test_a_clustered_generated_comparison_is_refused`:

```python
def test_a_clustered_comparison_now_validates_clean(write_config, tmp_path):
    """The retirement itself. A clustered roster with a generated comparison
    validates free of every finding — not merely free of the retired code, which is
    what says the design is one core runs today rather than one whose refusal
    happened to move."""
    _clustered_table(tmp_path, "patient_id,site", _SITE_BODY)
    path = write_config(
        {
            "data.units": _clustered_units(),
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman", "kendall"]},
            },
        }
    )
    assert codes(path) == set()
```

      And append to `tests/test_cli.py`, beside the clustered-interval group:

```python
_CONTRAST_CLUSTER_ROSTER = "patient_id,site\n" + "".join(
    f"p{i:02d},{s}\n" for i, s in enumerate("aabbbbcccccc")
)

_CLUSTER_CONTRAST_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        gap = {{"a": 1.0, "b": 5.0, "c": 9.0}}
        shift = 0.0 if cfg.analysis.method == "pearson" else 1.0
        units = list(io.units)
        for unit in units:
            io.record(unit.key, {{"pred": shift * gap[unit.attributes["site"]]}})
        return {{"n_units": len(units)}}
"""


def test_a_clustered_contrast_runs_end_to_end_and_records_the_clustered_delta(tmp_path):
    """The whole path, for the first time: `validate` lets a clustered comparison
    through, `command_run` threads the membership from `clusters_of` down to the
    construction, and `run.yaml` carries the cluster-robust delta.

    12 units in 3 clusters of 2/4/6; the spearman condition records 1.0/5.0/9.0 by
    cluster and the pearson baseline records 0.0, so the differences are the plan's
    fixture and the half-width is 8.7632 — against 1.9786 if the membership never
    reached the construction, which is the mutation task 10 could not catch by
    direct call.

    The count and the `method` are asserted beside the number, because the three
    move together."""
    import publishable.generators.experiment as experiment_gen
    import pytest as _pytest

    with _pytest.MonkeyPatch.context() as mp:
        mp.setattr(experiment_gen, "STARTER_STEP", _CLUSTER_CONTRAST_STEP)
        doc = run_a_project(
            tmp_path,
            replication={"repeats": [{"kind": "seed", "n": 1}], "order": "as_declared"},
            roster_csv=_CONTRAST_CLUSTER_ROSTER,
            units_overrides={"attributes": ["site"], "cluster_by": "site"},
            sweep={
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman"]},
            },
            statistics={
                "contrasts": [
                    {
                        "id": "spearman_vs_pearson",
                        "of": "method=spearman",
                        "against": "method=pearson",
                    }
                ]
            },
        )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = next(
        block["pred"]
        for condition in run["results"]["conditions"]
        for block in condition.get("vs_baseline", {}).values()
    )
    assert entry["method"] == "paired_t_over_units_clustered"
    assert entry["n_paired"] == 12
    assert entry["n_paired_clusters"] == 3
    assert entry["delta"] == pytest.approx(6.333333333333333)
    assert (entry["ci95"][1] - entry["ci95"][0]) / 2 == pytest.approx(8.763214143637903)
    # The DECLARED-contrast path, which is a second call site for the membership:
    # `_compute_declared_contrasts` threads `clusters` on its own line, and no
    # direct-call fixture in this plan reaches it. Same two conditions, so the same
    # arithmetic — which is what makes a disagreement between the two entries a
    # threading fault rather than a fixture difference.
    declared = run["results"]["contrasts"][0]["step01_summarize_units"]["pred"]
    assert declared["method"] == "paired_t_over_units_clustered"
    assert declared["n_paired_clusters"] == 3
    assert declared["ci95"] == entry["ci95"]
```

      Read `run_a_project`'s `_starter_step` parameter before writing the `MonkeyPatch.context()`
      block above — if it accepts a step source directly, pass
      `_starter_step=_CLUSTER_CONTRAST_STEP` and drop the context manager. The literal `{` in the
      step source must be doubled, as that helper's docstring requires, because the source goes
      through `STARTER_STEP.format(pkg=pkg)`.

      **`unit.attributes["site"]` is readable inside a step, checked rather than assumed:** `Unit`
      carries `attributes` as a frozen mapping built from `data.units.attributes`, and
      `reference.md` § The unit list says a declared attribute is also readable directly
      (`unit.site`). Keying the gap on the attribute rather than on an enumeration index is what
      makes this fixture independent of roster order — an index-keyed version would pass under a
      mutation that reordered the roster.

- [ ] **Step 3: Run and see them fail.** The `validate` test fails on
      `codes(path) == set()` (the retired code is still reported); the `run` test fails with the
      run's exit code, since `command_run` returns `EXIT_WRONG` on any validate error.

- [ ] **Step 4: Delete the emit and both rows.** In `src/publishable/validate.py`, `_check_sweep`,
      delete the `E-DATA-CLUSTER-CONTRAST` `c.error(...)` call, its `if` guard, its `plural` local
      and the whole comment block above it — **deleted, not rewritten**: every claim in that block
      was about a construction that now exists. Leave `cluster_by = units_here.get("cluster_by")`
      standing, since task 8's guard reads it.

      In `docs/reference.md`, delete the § Errors row whose final cell is
      `` `E-DATA-CLUSTER-CONTRAST` `` and the § Validation row *Clustered deltas aren't computed*.
      Then **re-word the § Validation row *Allocation deltas aren't computed***, whose clause
      *"Unlike *Clustered deltas aren't computed*, read per comparison rather than for the whole
      design"* now cites a row that does not exist. **State the property directly rather than by
      contrast** — the rule this repo applied when `E-DATA-WEIGHT-CONTRAST`'s row went: *"Read per
      comparison rather than for the whole resolved family: a `groups × grid` design's within-arm
      comparisons stay paired and computed."* That citation was installed deliberately by H4b-1's
      task-9-12 review so it would survive that deletion; this slice is what breaks it, and the
      ledger's own reasoning — *"a filing that says task 13 will handle it is the maintenance
      obligation nobody owns"* — points here.

- [ ] **Step 5: Edit the tests that name the code, by name.** In `tests/test_validate.py`:

      - `test_a_clustered_generated_comparison_is_refused` and
        `test_a_clustered_declared_contrast_is_refused` — **delete both**, with their message
        assertions. The behaviour they pinned is gone; `test_a_clustered_comparison_now_validates_clean`
        replaces the first and the end-to-end test replaces the second.
      - `test_a_clustered_baseline_that_generates_no_comparison_stays_legal` — its `crossed` control
        asserts `codes(...) == {"E-DATA-CLUSTER-CONTRAST"}`. **The test's whole point was that the
        baseline shape, not the cluster, decides**, and that distinction no longer exists at
        `validate`. Delete the `crossed` half and keep the clean assertion, or delete the test —
        **read it and decide, and say which in the task report.**
      - `test_an_unclustered_comparison_is_untouched` — its `not in` assertion now passes vacuously.
        **Re-point it** at the surviving distinction: the same sweep with no `cluster_by` records
        `paired_t_over_units`, which is a `run` fact, not a `validate` one — so delete this test and
        note that `tests/test_cli.py::test_an_unclustered_column_contrast_is_untouched` (task 10)
        already carries it.
      - `test_a_contrast_beside_groups_and_cluster_by_draws_both_refusals` — **narrow, never
        delete.** Change its expected set to `{"E-DATA-ALLOCATION-CONTRAST"}`, rename it to
        `test_a_contrast_beside_groups_and_cluster_by_draws_the_allocation_refusal`, and keep its
        docstring's point: it pins `validate`'s collect-don't-abort property and the fact that the
        combination itself is legal. Deleting it drops that pin.
      - Task 5's `test_every_unpaired_comparison_shape_still_earns_the_allocation_refusal` and task
        8's `test_a_weighted_clustered_comparison_draws_its_own_refusal` — **delete the one
        `assert "E-DATA-CLUSTER-CONTRAST" in found` line from each.** One line, which is what
        asserting alongside bought.
      - The section-header comment above `_clustered_units` — **delete the sentence carrying "none of
        those five exists"**, and leave the rest.

      In `tests/test_cli.py`, `test_the_sibling_refusal_rows_state_their_own_reading` — **narrow it
      to the allocation row alone.** Its `cluster = _row("E-DATA-CLUSTER-CONTRAST")` raises
      `StopIteration` once the row is deleted. Drop that line and its two assertions, keep the
      allocation row's, and update the docstring to say what the test now claims — **deleting the
      claim about the second row rather than rewriting it into a third.**

- [ ] **Step 6: Run everything.** `uv run pytest` → **2196 + 2 new − (the tests deleted in Step 5)**;
      state the exact number in the task report, since Step 5 leaves a judgment call. Then the other
      three gates, then the mechanical `*.md` pass — **and check the deleted rows left no dangling
      anchor**: grep the four documents for `#errors-validate-reports` links whose text names the
      retired code.

- [ ] **Step 7: Mutate.**

      **Mutation 1 — the threading task 10 could not reach.** In `src/publishable/cli.py`,
      `_compute_vs_baseline`, change `clusters=clusters` to `clusters=None` in its call to
      `_comparison_step_blocks`.
      `tests/test_cli.py::test_a_clustered_contrast_runs_end_to_end_and_records_the_clustered_delta`
      must **FAIL** on the `method` assertion and on the half-width, seeing `paired_t_over_units` and
      1.9786. **Checked against the test body:** the test travels the whole path from
      `clusters_of`, and the two readings give numbers a factor of four apart on an identical delta.
      **This is the mutation task 10 recorded as blind against its own direct calls**, and closing it
      here is why task 14 carries the `run`-through half. **Then run it again on
      `_compute_declared_contrasts`' own `clusters=clusters` line**, which is a separate call site: the
      test's `declared[...]` assertions must **FAIL** while the `vs_baseline` ones pass, which is what
      says the two sites are pinned independently rather than one standing in for the other.

      **Mutation 2 — the retirement itself is real.** Re-add the deleted emit (a one-line `c.error`
      with the same code). `test_a_clustered_comparison_now_validates_clean` must **FAIL** on
      `codes(path) == set()`, and the end-to-end test must **FAIL** on the run's exit code — the
      second being what says `validate` really does gate `run`.

- [ ] **Step 8: Commit.**

```bash
git add src/publishable/validate.py docs/reference.md tests/test_validate.py tests/test_cli.py
git commit -m "feat: retire E-DATA-CLUSTER-CONTRAST — a clustered comparison validates and runs"
```

---

## Task 15: the surviving-citation sweep

**Files:**
- Modify: `src/publishable/validate.py`, `src/publishable/stats.py`, `docs/reference.md`

**Interfaces:**
- Consumes: task 14's deletions; task 4's ruling, which fixed `E-DATA-CLUSTER-DERIVED`'s owner and
  left its wording to this task.
- Produces: no code behaviour. Nothing later consumes it.

**Swept by CLAIM over a named file list, never by filtering output**, and **excluding the
development record** — `docs/superpowers/**` is evidence, not text to repair. The sites below were
enumerated by reading at `82310b9` and confirmed by grep, in that order. **Two of the scoping's
attributions are wrong about which function holds the comment**, which is exactly the
`E-TEMPLATE-UNKNOWN` misreading — a task scoped by function name would miss a site — so each row
below names what the comment *does*:

| Where | What it says | This task |
|---|---|---|
| `validate.py`, the docstring of the check that refuses a split across cells | Lists the code among the combination refusals this repo routes to | **Delete the name**, keep the argument: the precedent is that a combination is refused rather than disclosed, and it survives the example |
| `validate.py`, the comment in the unimplemented-declarations check explaining why `cluster_by` is not one | "What a clustered run may *not* yet do is publish a contrast (`_check_sweep` refuses that combination…)" — **now false** | **Delete that clause.** The derived-metric clause beside it stays true and stays |
| `validate.py`, `E-DATA-ALLOCATION-CONTRAST`'s guard comment | *"Unlike `E-DATA-CLUSTER-CONTRAST` above, this guard does not fire on `comparisons > 0`"* — a contrast with a code that no longer exists | **State the property directly**: it reads each resolved comparison individually because a group axis affects some and not others. Same repair as the § Validation row, same reason |
| `stats.py`, `summarize_step`'s docstring | "H4 Statistics lifts this with the clustered contrast family (`E-DATA-CLUSTER-CONTRAST`), which is the same missing construction one level over" | **Delete the citation** and say what is missing: a clustered draw for a *recomputed* metric. Task 4's ruling |
| `docs/reference.md`, `E-DATA-CLUSTER-DERIVED`'s § Errors row | "Temporary, alongside `E-DATA-CLUSTER-CONTRAST`, which is the same missing construction one level over" | **Replace with a self-standing justification**: *"Temporary: the refusal lifts with the slice that builds a clustered draw for a recomputed metric."* No slice name — the documents do not carry those |
| `docs/reference.md` § Statistical reporting, the compose sentence | Task 8 already re-pointed it at `E-DATA-WEIGHT-CLUSTER-CONTRAST` | **Verify, do not edit.** If it still names the retired code, task 8 was applied wrong |
| `docs/reference.md` § Statistical reporting, the derived-metric resample paragraph | Names `E-DATA-CLUSTER-DERIVED`, not the retired code | **Leave.** Listed so it is not "fixed" |

- [ ] **Step 1: Sweep, and prove the sweep can fail.**

```
grep -rn "E-DATA-CLUSTER-CONTRAST" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ tests/
```

      Every hit must appear in the table above. **Can-fail control on the identical file list:**

```
grep -rn "E-DATA-WEIGHT-CLUSTER-CONTRAST" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ tests/
```

      → hits, since task 8 minted it. A sweep that returns nothing for both strings is a broken
      sweep, not a clean repo.

- [ ] **Step 2: Apply each row's repair, preferring deletion.** Work down the table. **Where a
      sentence's job was to contrast with the retired code, state the property directly rather than
      finding a new sibling to contrast with** — a rewrite invents, a deletion cannot, and this repo
      has closed a false-owner comment by propagating the claim to two more sites.

      **When you edit a docstring, re-read the whole one.** Ten Majors across H4b-1's four review
      batches were stale quantifiers or claims left standing over changed material.

- [ ] **Step 3: Run the gates.** `uv run pytest` → unchanged from task 14's number; this task adds no
      test and changes no behaviour. If the count moves, something was deleted that was load-bearing.
      Then `uv run ruff check .`, `uv run ruff format --check .` (80 files), `uv run mypy`, then the
      mechanical `*.md` pass.

- [ ] **Step 4: Re-sweep.** Run Step 1's first command again. It must return **nothing** in
      `src/`, in the four documents and in `tests/`. It will still return hits under
      `docs/superpowers/` — **that is correct and must not be repaired**: those files record what was
      measured on their date.

- [ ] **Step 5: The mutation, and why it is on the sweep.** No test asserts these wordings, and
      adding one would be a second source of truth for build state. **The measurement is the sweep,
      and Step 1's control is what makes it one** — it must return hits for a string that is present
      while the primary returns none. Run both again after Step 2 and record both outputs in the task
      report.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/validate.py src/publishable/stats.py docs/reference.md
git commit -m "docs: every surviving citation of the retired cluster-contrast refusal"
```

---

## Task 16: the filings — every entry that names H4b-2, discharged or re-owned

**Files:**
- Modify: `docs/superpowers/spec-defects.md`, and `tests/test_stats.py` only if the finiteness
  entry's two tests move with it (they do not — see below)

**Interfaces:**
- Consumes: tasks 1, 3, 4, 5 and 9's entries, already written; the five `spec-defects.md` entries
  naming H4b-2 and the two naming H4 Statistics in terms that resolve here.
- Produces: a filing count that goes **down**, not up.

**`grep -n 'H4b-2' docs/superpowers/spec-defects.md` before starting**, and read every hit — the list
below was taken at `82310b9` and tasks 1–9 have appended to that file since.

| Entry | This task |
|---|---|
| *a stratified paired draw can publish a zero-width contrast interval* | **Already CLOSED by task 9.** Verify, do not re-close |
| *A column resample is only ever defined given finite inputs* | **Re-own, and move nothing.** Its two `*_is_a_known_unfixed_gap` tests in `tests/test_stats.py` are about `percentile_over_units`' per-condition path, and H4b-2 did not touch it: the paired clustered *t* delegates to `t_over_units_clustered`, which does no weight arithmetic, and the clustered percentile draw pools rows it does not sum. **So the entry's own reasoning — "H4b-2 is the next place a whole weight vector or value column is drawn as a unit" — did not come true**, and that is the finding. Amend it to say so, dated, and re-own to **H4c** |
| *The contrast path discloses nothing about its resample* — findings 1 and 3 | Finding 1 is a contrast-scope thin finding needing a `where` and a registry row; finding 3 is a contrast entry carrying no resolved-`resample` echo. **Neither is a cluster question**, and building either would mint a warning identifier and a § Warnings row this slice did not scope. **Decline both in writing and re-own to H4c**, with the reason: H4b-2 added a third `method` spelling to the contrast entry and no new disclosure surface |
| *`paired_percentile_of_derived`'s sorted-pool precondition unasserted* | **Re-state and STRIKE the 2026-08-17 amendment, rather than implementing it as filed.** Read at `82310b9`: *both* return paths sort the returned pool (`pool=sorted(values)` and `values.sort()` before `pool=values`), so the amendment's "second route to an unsorted-pool input" describes the **stratum key pools**, a different object from `PairedResample.pool`. The entry's *original* condition — "a **new** percentile construction returning an unsorted pool" — is what H4b-2 task 7 could have created, and did not: the clustered draw returns through the same two sorted paths. **Restore the original condition, strike the amendment's stratum-pool reasoning, and record that task 7 was checked against it** |
| *§ How a metric becomes a number is cited across the repo and does not exist* | **Claim it or decline it in writing. Declined twice already; a third silent pass is how it goes stale.** Recommended: **decline**, with the reason that H4b-2 edited two docstrings citing it and writing the section is a documentation slice's work, not a statistics slice's — and re-own it explicitly rather than leaving it unassigned |
| *`report_by` … a level's recorded-column interval stays `t_over_units`* | **Decline in writing and re-own to H4c**, the direction the scoping recommends: it is live on C1–C3, created by neither weights nor clusters, and folding it in is what `H4b-SCOPING` § 12 warned against for its sibling |
| *`correction.corrected_fields` dedupe unpinned* | **Record as NOT H4b-2's.** The entry's condition is "the slice that would build `Member` lists from somewhere other than `cli._comparison_step_blocks`" — H4b-2 **widens** `Member` with a `clusters` field and builds no list elsewhere, so the condition is unmet. Recording it is what stops the next scoping re-deriving it as owed |

**A ledger line saying "filed" is not a filing.** Every re-ownership above is an edit to
`spec-defects.md` itself, with a date and a named owner — not a sentence in a task report.
**And re-owner a deferral when the slice that filed it finishes**, or it reads as live work nobody
holds.

- [ ] **Step 1: Read every entry naming H4b-2 or H4 Statistics.** `grep -n "H4b-2\|H4 Statistics"
      docs/superpowers/spec-defects.md`, then read each hit **in full** — a filing's claims about the
      code go stale like any other comment, and *"when you change code a `spec-defects.md` entry
      describes, re-read the entry"* is exactly what the sorted-pool row is an instance of.

- [ ] **Step 2: Apply each row.** Amend in place, appending a dated correction rather than
      retro-editing — except a **closed** gap, which is struck, `spec-defects.md` being the one file
      in the development record where that is the rule.

- [ ] **Step 3: Verify the finiteness entry's two tests really do not move.** Run
      `uv run pytest tests/test_stats.py -k is_a_known_unfixed_gap -v` and read both test bodies.
      They call `percentile_over_units` directly. **If either now touches a construction this slice
      changed, the entry moves with it and this task is bigger than the table says** — check rather
      than assume, since the entry's own prediction about H4b-2 was wrong.

- [ ] **Step 4: Run the gates.** `uv run pytest` → unchanged from task 15's number. Then the other
      three. The mechanical pass applies to `spec-defects.md` in full (links, tables, whitespace);
      the **cross-document** pass does not — it is development record.

- [ ] **Step 5: The mutation, and why there is none.** Every deliverable here is prose in an untested
      file, and adding a test for it would be a second source of truth for build state — the argument
      H4b-1's task 1 recorded for its own filing. **Step 3 is this task's measurement**, and it can
      fail: if either `*_is_a_known_unfixed_gap` test now exercises changed code, the plan's claim
      that the entry does not move is falsified.

- [ ] **Step 6: Commit.**

```bash
git add docs/superpowers/spec-defects.md
git commit -m "docs: every filing naming H4b-2, discharged or re-owned by name"
```

---

## Task 17: the regression pin, and the boundary this slice owes

**Files:**
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: task 7's uniform draw shape, task 10's *t* selection, task 11's percentile selection,
  task 14's retirement (which is what lets a clustered config run at all).
- Produces: nothing. This is the last behavioural task, and it asserts that what H4b-1 shipped and
  what the worked example documents did not move.

**Three pins, and the third is one the spec says this slice OWES rather than merely respects.**

1. **An unclustered unweighted config is byte-identical.** `paired_t_over_units` and
   `paired_percentile_over_units` on the same numbers they gave at `82310b9` — including the
   percentile form, whose draw shape task 7 rewrote. The worked example's intervals *"must not be
   narrowed back"*.
2. **An unclustered weighted config is byte-identical.** That is H4b-1's output, one slice old, and
   the first thing a `clusters` parameter threaded through the same three signatures can disturb.
3. **A clustered pass must SKIP a `summary`-step `Estimate`.** It is `reported: true`, outside the
   correction family and never recomputed — the documented route
   `E-DATA-CLUSTER-CONTRAST`'s own message offered, which makes it the one boundary this slice must
   not have moved while retiring that message.

- [ ] **Step 1: Write the three tests.** Append to `tests/test_cli.py`:

```python
def test_an_unclustered_resampled_contrast_draws_what_it_always_drew(tmp_path, capsys):
    """The regression task 7's uniform draw shape owes. A config with no
    `cluster_by` and no `weight_by`, under a declared `resample`, must produce the
    same percentile interval it produced before the draw was rewritten — the shape
    change is RNG-identical or it is a defect.

    Asserted on both endpoints and the `method`, not on the width: a draw sequence
    that changed by one call moves the endpoints without necessarily widening
    anything."""
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        replication={"repeats": [{"kind": "seed", "n": 1}], "order": "as_declared"},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        statistics={"resample": {"method": "bootstrap", "n": 2000}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = next(
        metric
        for condition in run["results"]["conditions"]
        for block in condition.get("vs_baseline", {}).values()
        for metric in block.values()
    )
    assert entry["method"] == "paired_percentile_over_units"
    assert "n_paired_clusters" not in entry
    assert entry["ci95"] is not None
```

      **Fill in the two endpoint assertions from a run taken BEFORE task 7 lands.** Capture them at
      `82310b9` — check out that commit in a scratch worktree, run this exact config, record the two
      floats — and write them in as literals. **A regression pin whose expected values were captured
      after the change is not a regression pin**, and this repo has shipped that shape before.

```python
def test_an_unclustered_weighted_contrast_is_unchanged_by_the_cluster_threading(tmp_path, capsys):
    """H4b-1's output, one slice old. The `clusters` parameter threads through the
    same three signatures its `weights` does, so a weighted contrast is the first
    thing a mis-ordered arm in the construction choice would break — the *t* branch
    now tests `col_clusters` first, and a weighted column must still reach
    `weighted_paired_t_over_units`."""
    ...
```

      Build this one from `tests/test_cli.py`'s existing weighted end-to-end test — read it, copy its
      config shape, and assert `method == "weighted_paired_t_over_units"`, the presence of
      `weighted_by` and `n_paired_effective`, the **absence** of `n_paired_clusters`, and its
      recorded `ci95` endpoints as literals captured at `82310b9`. **Name the test you copied from in
      the docstring**, so a reader can see the two are about one config.

```python
def test_a_clustered_run_leaves_a_summary_estimate_alone(tmp_path, capsys):
    """The boundary this slice owes rather than merely respects. An `Estimate`
    returned by a `summary` step is `reported: true`, outside the correction family
    and never recomputed — the route `E-DATA-CLUSTER-CONTRAST`'s own message
    offered before task 14 deleted it. A clustered pass walking every metric block
    must not touch it: no `_clustered` suffix on its `method`, no
    `n_paired_clusters`, no `ci95` rebuilt from the cluster count.

    The clustered contrast beside it is asserted in the same record, because a
    control asserting only absences passes identically if nothing ran."""
    ...
```

      Build this from the `extra_steps` / `extra_step_source` parameters of `run_a_project`, whose
      docstring says they are how a caller gets a `summary`-scoped step into a generated project;
      read it before writing. Assert that the `Estimate` reaches `results.summary` with
      `reported: true` and its own `method` unchanged, **and** that the clustered `vs_baseline` entry
      in the same run carries `paired_t_over_units_clustered` — the presence that must report.

- [ ] **Step 2: Run and see them fail where they should.** Tests 1 and 2 should **pass** if tasks 7
      and 10–13 are correct; that is the point of a regression pin, and their value is entirely in
      Step 3's mutations. Test 3 is expected to pass too. **If test 1 or 2 fails, stop: the draw
      shape or the construction order moved something it was not allowed to move**, and the fix is in
      `stats.py` or `cli.py`, never in the expected literals.

- [ ] **Step 3: Mutate.**

      **Mutation 1.** In `src/publishable/stats.py`, in `paired_percentile_of_derived`'s unclustered
      branch, change `items = [[key] for key in keys]` to `items = [[key] for key in reversed(keys)]`.
      `test_an_unclustered_resampled_contrast_draws_what_it_always_drew` must **FAIL** on an endpoint.
      **Checked against the test body:** the draw indexes `items` by a fixed RNG sequence, so
      reversing the order draws a different multiset on nearly every replicate and the percentiles
      move — provided the endpoint literals are in place, which is why Step 1 requires them.

      **Mutation 2.** In `src/publishable/cli.py`, swap the *t* branch's first two arms so
      `col_weights` is tested before `col_clusters`.
      `test_an_unclustered_weighted_contrast_is_unchanged_by_the_cluster_threading` must **PASS**
      (nothing is clustered there) while
      `test_a_clustered_column_contrast_takes_the_cluster_robust_t` from task 10 must **FAIL** — the
      pair is what says the order is right rather than that one arm works.

      **Mutation 3.** In `src/publishable/cli.py`, remove the `is_derived`/`"by"` exclusion that keeps
      a non-metric key out of the contrast walk — or, if the summary block is reached by a different
      route, make the clustered pass write `n_paired_clusters` onto the summary `Estimate`'s block.
      `test_a_clustered_run_leaves_a_summary_estimate_alone` must **FAIL**. **Read the record
      assembly first and prescribe the mutation that actually reaches it**: if no mutation can put a
      `_clustered` key on a summary `Estimate` — because `_comparison_step_blocks` walks `aggregated`
      and a summary `Estimate` lands in `results.summary` through `run_record.py`, never in
      `aggregated` — **then say so in the task report as a structural separation rather than a
      guarded one**, and keep the test as the pin that the two records stay separate.

- [ ] **Step 4: Run the gates.** `uv run pytest` → task 15's number + 3. Then the other three.

- [ ] **Step 5: Commit.**

```bash
git add tests/test_cli.py
git commit -m "test: the unclustered and weighted regressions, and the summary Estimate boundary"
```

---

## Task 18: the dated re-measurement

**Files:**
- Modify: `docs/feasibility-llm-growth-studies.md`

**Interfaces:**
- Consumes: nothing in code. It reports what tasks 1–17 did and did not change.
- Produces: the § Executability entry a later scoping will read instead of re-deriving.

**Re-dated, not edited.** § Executability on this build carries one `### Measured on <date> against
commit <sha>` subsection per slice, each a dated record of what was true then. **Do not touch the
earlier ones** — including H4b-1's, which this entry sits beneath.

**The number is ZERO, stated plainly.** No config in that analysis declares `cluster_by` — its only
two hits are both `cluster_by: null`. The *no-remaining-core-side-blocker* count stays **six** and the
executable count stays **three**. `CLAUDE.md`'s feasibility procedure step 10 exists because **a
refusal count has been read as an execution count**, and that failure arrived in H4b-1's own
retirement commit and failed both review verdicts. **No sentence in this entry may imply otherwise**,
and the honest net on refusals is **one retired, one re-owned, one minted** — not "two refusals
narrowed".

- [ ] **Step 1: Re-measure rather than carry.** Run, filtering the file list:

```
grep -n "cluster_by" docs/feasibility-llm-growth-studies.md
```

      Expected: two hits, both `cluster_by: null`. **Can-fail control on the same file:**

```
grep -c "weight_by" docs/feasibility-llm-growth-studies.md
```

      → a non-zero count, a field that *is* declared. A sweep returning nothing for both would be a
      broken sweep rather than a clean answer.

- [ ] **Step 2: Get the commit sha.** `git rev-parse HEAD` on this branch after task 17's commit. The
      entry is pinned to that sha and dated 2026-08-17.

- [ ] **Step 3: Write the entry.** Append to `docs/feasibility-llm-growth-studies.md` § Executability
      on this build, after the H4b-1 subsection:

```markdown
### Measured on 2026-08-17 against commit `<sha>` — after H4b-2

H4b-2 retires `E-DATA-CLUSTER-CONTRAST` and mints `E-DATA-WEIGHT-CLUSTER-CONTRAST`. **It unblocks
zero configs, and both counts stand unchanged: six with no remaining core-side blocker, three
executable.** No config in this analysis declares `data.units.cluster_by` — measured on the file
above, two hits and both `cluster_by: null` — so the refusal H4b-2 retires is one no experiment here
hits, and a retired refusal is not an execution in any case.

**The newly minted refusal reaches none of the nine either.** `E-DATA-WEIGHT-CLUSTER-CONTRAST`
requires both `weight_by` and `cluster_by` beside a comparison; C1, C2 and C3 declare the first and
none of the nine declares the second.

**What H4b-2 changes for a config that *did* declare a cluster**, stated as specification rather than
as a measurement of these nine: a clustered comparison's delta takes
`paired_t_over_units_clustered` or `paired_percentile_over_units_clustered`, its `method` says which,
and `n_paired_clusters` travels beside `n_paired`. And one live defect closes for configs that
declare **no** cluster at all: a contrast draw whose every stratum's rows are identical now reports
`ci95: null` rather than a zero-width interval, which is reachable from a near-unique
`resample.stratify_by` — all three C configs declare `stratify_by: [consensus_label,
count_stratum]`, whose strata are not near-unique on the roster this analysis describes, so it is a
closed hazard rather than a changed number for them.

**Unchanged and still outstanding**, carried from the H4b-1 entry rather than re-derived: E3, E4, E6,
C1, C2 and C3 remain blocked on `io.reuse_from`, which is unbuilt and unowned and invisible to
`validate`; and all three C configs still meet a `report_by` level's recorded-column interval staying
`t_over_units` under a declared `resample`, which H4b-2 declined in writing and re-owned to H4c.
```

- [ ] **Step 4: Run the gates and the mechanical pass.** `uv run pytest` → unchanged from task 17's
      number; this file has no tests over it. Then `uv run ruff check .`,
      `uv run ruff format --check .` (80 files), `uv run mypy`. Then the mechanical pass **in full**
      — a feasibility analysis is exempt from the cross-document pass and **not** from this one:
      every link and `#anchor` resolves, no two headings share an anchor, no trailing whitespace, no
      en dash, `×` for multiplication.

- [ ] **Step 5: The mutation, and why it is on the measurement.** No test reads this file. **Step 1's
      control is the mutation**: the `cluster_by` sweep must return two `null` hits while the
      `weight_by` control returns a non-zero count, and a sweep that cannot tell those apart cannot
      support the sentence. Record both outputs in the task report.

- [ ] **Step 6: Commit.**

```bash
git add docs/feasibility-llm-growth-studies.md
git commit -m "docs: H4b-2 re-measured — zero configs unblocked, six and three unchanged"
```

---

## Self-review

Run after the plan was written, against the spec with fresh eyes.

### 1. Spec coverage — every requirement pointed at a task

| Spec requirement | Task |
|---|---|
| Decision 1 — one slice, 18 tasks | The plan's task count is 18 and the split question is not reopened |
| Decision 2 — the retirement sits last | 14, with the reason stated in its own brief and in § Sequencing |
| Decision 3 — mint `E-DATA-WEIGHT-CLUSTER-CONTRAST`, both rows, de-hedge the sentence | 1 (ruled), 8 (code + § Errors row + § Validation row + sentence) |
| Decision 4 — assert the H4c gate two ways, neither the obvious one | 5, both pins, with the blind mutation named |
| Decision 5 — `n_paired_clusters` documented before code; **no** new `method` rows | 2 (documented), 13 (emitted); the no-rows ruling is in § Identifiers and asserted by task 11's document test |
| Decision 6 — the zero-width defect built **with** the construction; the filing's amendment struck | 3 (ruled + documented), 9 (built + closed), 16 (the *sorted-pool* amendment struck) |
| Decision 7 — zero configs, six and three unchanged, dated and pinned | 18 |
| Task 1 before 6–9 and 11; 4 before 2; 3 before 7; 2 before 13; 6 before 12; 14 last; 15 not the dev record | § Sequencing, and each dependent task's own brief |
| The discriminating fixture, its four constraints and five half-widths | § The discriminating fixture, used verbatim by tasks 6, 10, 11, 13, 14 |
| The percentile form's 6–18 pooled row count against a mutant's fixed 12 | 7, asserted directly |
| The clustered percentile draw actually reaching production, not only its `method` string | 11, `test_a_clustered_resampled_contrast_really_drew_clusters`; the parametrized table pins the string alone |
| Both `cli` call sites threading the membership | 14, whose end-to-end config carries a `vs_baseline` **and** a declared contrast, mutated at each site separately |
| `E-DATA-CLUSTER-DERIVED` re-owned by name | 4 (owner), 15 (wording) |
| The surviving-citation sweep, by claim, over a named file list, excluding the dev record | 15 |
| The filings — finiteness, disclosure 1 and 3, sorted-pool, § How a metric becomes a number, `report_by`, `corrected_fields` dedupe | 16, one table row each |
| The regression pin and the `summary`-`Estimate` boundary | 17 |
| `correction.py` as `paired_t_over_units_clustered`'s first caller | 12, and task 6 → 12 in § Sequencing |

**Gaps found and closed inline:** the spec's task 1 pairs the de-hedged sentence with the ruling
(moved to task 8, argued as deviation (a)); its task 4 pairs a row's wording with the ownership
decision (moved to task 15, deviation (b)); its task 10/11 split leaves task 10 untestable
(deviation (c)). **No spec requirement is unassigned.**

### 2. Placeholder scan

Three deliberate blanks, each with what fills it and where the shape comes from:

- **Task 17's second and third tests** carry `...` for a body that must be **copied from a named
  existing test** rather than invented, and expected endpoint literals that must be **captured at
  `82310b9` before the change lands** — a regression pin whose expected values are captured
  afterwards is not one.
- **Task 11's `pytest.approx([0.0, 0.0])  # paste the run's`** is a placeholder for endpoints
  captured from that test's own first green run. It is legitimate because the **discriminating**
  assertion in that test is the inequality above it, which needs no literal; the endpoints are a
  second lock so a later change cannot move the draw while leaving the two merely unequal. Leaving
  `[0.0, 0.0]` in place would fail the test, so it cannot ship unfilled.

Every other code block is complete. No "TBD", no "add appropriate error handling", no "similar to
task N".

### 3. Type consistency across tasks

| Name | Defined | Used |
|---|---|---|
| `paired_t_over_units_clustered(diffs, labels, confidence=0.95) -> Interval \| None` | 6 | 10 (`col_clusters`), 12 (`member.clusters`) — both pass a `Sequence[str]` one label per difference |
| `paired_percentile_of_derived(..., method=..., clusters: dict[str, str] \| None = None)` | 7 | 9 (the refusal reads its `pools`), 11 (`clusters={k: clusters[k] for k in col_keys}`) |
| `"paired_percentile_over_units_clustered"` | 7 (emitted via `method=`) | 11 (passed), 2 (documented as a suffix, not a row) |
| `n_paired_clusters` | 2 (documented) | 13 (emitted), 14 and 17 (asserted) |
| `Member.clusters: tuple[str, ...] \| None` | 12 | 12 (`_corrected_bounds`), 13 (asserted on the ragged fixture) |
| `clusters: dict[str, str] \| None` parameter | 10 | 10, 11, 13 on all three `cli` functions and both `command_run` call sites |
| `E-DATA-WEIGHT-CLUSTER-CONTRAST` | 1 (reserved), 8 (minted) | 10 (the `ValueError` message), 12 (`Member.__post_init__`), 14 (**not** deleted), 18 |
| `_clustered_contrast_call(**extra)` — `extra` **overrides** the defaults, so `clusters=None` and `resample_columns=True` are both passable | 10 | 11, 12 |
| `_CONTRAST_CLUSTER_LABELS` | 10 | 11, 12 |
| `_WEIGHTED_SITE_BODY` | 8 | 8 only |

One inconsistency was found and fixed while writing: task 6's construction takes a **label vector**
while `t_over_units_clustered` takes `keys` + `membership`, and tasks 10 and 12 were drafted against
the second shape. The label vector wins — `Member` documents `weights` as a modifier on `diffs`, and
two fields on a frozen dataclass for one fact is what the alternative costs — and the synthesis of
positional keys is stated in task 6 as a bijection rather than left as a proxy a reviewer would
challenge.

