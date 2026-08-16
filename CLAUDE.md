# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status: specification and implementation

This repository holds both the normative specification and the tool it specifies.

- `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md` and
  `docs/reference.md` are **the four documents**. They are normative and they lead.
- `src/publishable/` is the implementation. It follows the documents. Where it cannot
  follow them, **the document changes first** — record the gap in
  `docs/superpowers/spec-defects.md` rather than diverging silently.

**Commands:**

| Task | Command |
|---|---|
| Tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Types | `uv run mypy` |

`docs/reference.md` § Package layout describes a tree that now **partially** exists.
Modules not yet built are still planned, and the slices that build them are listed in
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md`.

**Order of the slices that remain: H4b → H7b → the rest.** Amended twice on 2026-08-14
against outside evidence — all nine experiments in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) were run through `validate`, and
**none executed**. The gate was the **template registry**, not the plugin system: `get_template` read a
builtin dict, so every config stopped at `E-TEMPLATE-UNKNOWN` before any other check — but § Templates
gives a template three homes, and a **project-local** one in `templates/` is *discovered by path*, not
through an entry point. **H7a was that subset** — `register_template` exported, `templates/**` discovered
by path, `generate template` — and it needed none of entry-point resolution, probes or the change gate.
**It merged on 2026-08-15 and that gate is gone.** **H4a (`resample`) merged the same day** — one refusal
retired that 8 of 9 configs hit, a regression preserved, and **zero experiments newly executing**, which
is the honest form of that number. **H3d (`holdout`) merged on 2026-08-16, in the identical honest form**:
one refusal retired that 6 of 9 configs hit (`E-DATA-HOLDOUT-UNSUPPORTED`), one live defect closed (a
`fold` beside a cell structure validated clean and produced empty per-arm folds; both that and a holdout
beside the same structure are now a named refusal, `E-REPL-FOLD-CELLS` / `E-DATA-HOLDOUT-CELLS`), and
**zero experiments newly executing** — all nine still declare a resolver and still earn
`E-DATA-RESOLVER-UNSUPPORTED`, which is H7b's. A re-measurement dated 2026-08-16 is in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) § Executability on this build. H4b
(weighted contrasts) retires the one refusal C1–C3 carry beyond the resolver — a retired refusal is not an
execution, and all nine, C1–C3 included, still declare a resolver, so *as written* none runs until H7b.

A second amendment the same day scoped all five remaining slices against the code. **Every charter was
stale in the same direction**: H4 is ~54 tasks split four ways, H7's remainder 38 split three ways, H3d
16 against a charter saying "3 rows", H3c-3 17 against a charter saying 6. Two consequences worth
carrying: `statistics.resample` for the unclustered case is **wiring, not construction** (two percentile
constructions are built with zero production callers), and **H3c-3 contains a 3-task refusal that closes
a live defect** — `groups` + `between` + `fold` validates clean today and produces empty folds per arm,
because `fold_basis` answers over the whole roster. That refusal ships with H3d; the other 14 tasks wait
for a design that needs folds inside cells.

The cost is that H3d now precedes the cells work it was scheduled to consume, so **H3c-3 owns
retrofitting the holdout to cells and retiring `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS`, both
already named on H3d's branch, once drawing within a cell is built** — acceptable only because no
experiment in that analysis declares a group axis. The reasoning lives in the spine design's *Order,
amended against outside evidence*, which is now tracked — cite it rather than restating it.

## The documents

| File | Role |
|---|---|
| `README.md` | The pitch and the whole arc, for someone deciding whether to use it |
| `docs/design-principles.md` | **Normative.** Why each rule is what it is |
| `docs/experimental-designs.md` | How each experimental design is expressed; what core prevents and refuses |
| `docs/reference.md` | Config schema, CLI, `io` API, templates, sweeps, artifact layout |
| `docs/feasibility-*.md` — currently [`llm-growth-studies`](docs/feasibility-llm-growth-studies.md) | **Non-normative.** One feasibility analysis each; carries its own examples — see § Feasibility analyses |

The first four are *the four documents* everywhere below: the invariants, the consistency passes, and the worked example govern those and only those. A `feasibility-*.md` is analysis output, not specification, and nothing in it is authoritative over them.

`design-principles.md` is the tiebreaker. Read it before proposing a change to any rule — if a rule looks arbitrary, that file explains it, and if it doesn't, that gap is itself worth fixing.

## The development record

The four documents say what `publishable` **is**. These say how it got there, and they are **tracked** — read them before re-deriving anything.

| Where | What it is | Read it when |
|---|---|---|
| `docs/superpowers/specs/<date>-<slice>-design.md` | A slice's design: its decisions, each with grounds, and what it refuses | Before planning or changing that slice |
| `docs/superpowers/plans/<date>-<slice>.md` | The same slice as numbered tasks, with code and per-task mutations | While executing it |
| `docs/superpowers/*-SCOPING.md` | What was **measured against the code**, dated and pinned to a commit | Before trusting any charter |
| `docs/superpowers/spec-defects.md` | Gaps found and deliberately not closed, with the owner | Before filing a "new" gap |
| `.superpowers/sdd/<plan>/progress.md` | The ledger: every ruling, its reason, and what it costs if wrong | To learn why something is the way it is |
| `.superpowers/sdd/<plan>/task-N-report.md`, `task-N-review.md` | What was built, what the brief got wrong, what each finding was verified by | Before repeating a task's work |

**A scoping expires; a spec does not.** Every charter re-scoped so far was stale **in the same direction** — under-counted and missing surface — so a scoping is dated and pinned to a commit, and a claim carried from one without re-checking is worse than one omitted. Re-measure rather than trust.

**The plan argues from the spec, and the code outranks both.** Where they disagree, the code wins and the *document changes first* — six of six implementers on the most recent slice found a real disagreement, so finding one is expected, not exceptional.

Two things stay untracked because git already holds them: task briefs (extracted from the plan by `scripts/task-brief`) and every `.diff` (regenerable from the two commits in its filename).

**`scripts/sdd-workspace` rewrites `.superpowers/sdd/.gitignore` to a bare `*` every time it runs, and `task-brief` calls it.** Already-tracked files stay tracked, so the damage is only to records created after a clobber. Restore that file's content when you notice, and use `git add -f` when committing new records.

## Invariants a change must not quietly break

These are load-bearing across all four documents; contradicting one in a single section creates a real inconsistency, not a wording nit.

- **Operation commands take paths and nothing else.** No parameter flags, no selectors, no behavior-changing env vars. Modes get their own command names (`dry-run`, `draft`, `resume`) rather than `--dry-run`/`--allow-dirty`. Only creation commands (`new`, `plugin new`, `generate`/`init`, `study new|add`) take arguments beyond a path. (`design-principles.md` § Everything is in the file)
- **Three hashes, split on purpose.** `code_hash` covers `src/**` and `templates/**` only — the code your repo supplies, a plugin's being pinned by `uv.lock` instead — separate from `parameters_hash` and `input_manifest_hash`. That split is what makes "same code, different parameters" provable across unrelated commits — unrelated meaning outside the two hashed trees, since another experiment's package is inside them.
- **`input_dir`/`output_dir` may never resolve inside the git repo**, checked at generate, at validate, and by every command that executes (`run`, `draft`, `resume`). Which repo is decided by a walk-up from the path the command was given, not from the working directory.
- **Condition vs. repeat.** A condition is a difference being measured; a repeat is a difference being averaged over. Statistics aggregate *within* a condition and compare *across* conditions — never the reverse.
- **A repeat is an execution, so the kinds are exactly the three things a re-execution can change: `seed` (RNG state), `fold` (which units it sees), `batch` (the state of the apparatus it measures through — see § The apparatus core can only observe).** A `batch` takes no field but `n`, executes in order with `order: randomized` shuffling inside it, and `validate` warns when no step sets `nondeterministic = True`. Resampling and permutation are `statistics.resample`/`statistics.null_test` over the unit table (thousands of executions otherwise, and an all-permuted design has no unpermuted value to test); technical replication is `data.units.measurements`, collapsed at unit resolution (re-running an identical step recomputes the same answer); a fixed holdout is `data.units.holdout`. `validate` rejects `bootstrap`, `permutation`, `technical`, `biological`, and `holdout` as kinds by name.
- **Units are the inference base; repeats never are.** Every interval core reports is computed from the per-unit table, `n` counts units (`resolved`/`completed`/`ineligible`/`failed`, where `io.skip` declares the third and `max_failed_fraction` guards only the fourth), and repeat dispersion is reported separately as `repeat_spread`. A metric that exists only as a step-returned scalar is `basis: repeats` and gets **no** `ci95`; the one interval core stores without computing is an `Estimate` returned by a `summary` step, marked `reported: true`, outside the correction family and never recomputed. A hypothesis may name one — it takes no `compare` — and the verdict records `verdict_rests_on: reported` rather than `computed`. Pairing is over units, never over repeats, and a contrast — `vs_baseline` or a declared `statistics.contrasts` entry — is computed over the intersection of both sides' completed units, recorded as `n_paired` — and its interval is its own construction over that intersection (`paired_t_over_units`, `paired_percentile_over_units` drawing once for both sides, or the `welch_`/`unpaired_` counterparts), never a difference of the two sides' intervals. Holm ranks on the point estimate over half the raw `ci95` width, because the family often carries no p-value at all, which is also why `fdr_bh` over such a family warns. `data.units.weight_by` weights an enriched sample's estimates and records `weighted_by`; `statistics.report_by` repeats metrics over strata without adding executions or joining the correction family; a subgroup you want to *test* is a contrast with `within`, which does join it. Contrasts compare conditions and do not nest: anything comparing two contrasts — a dose-response ordering, a difference-in-differences, a nested mean over cells — is an interaction and stays a `summary`-step `Estimate`. The table `aggregate` receives supports exactly four operations — row iteration, column access, `len`, `columns` — deliberately not a `DataFrame`, so core can change what backs it without breaking every plugin. (`reference.md` § The unit table is the inference base, § Templates)
- **One import root, one registration, one return shape.** Everything a user writes against is imported from `publishable` itself — `publishable.templates` and every other submodule are implementation detail, and `reference.md` § The importable surface is the enumerated list. The entry-point key *is* a plugin artifact's registered name and the `@register_*` argument is checked against it (so `validate` resolves a name without importing the package); a collision or a shadow of a core name fails at load rather than being resolved by install order. `io.write` dispatches on the longest registered suffix of the name's last component, and each core writer takes exactly what its reader gives back — rows as mappings for `.csv`/`.parquet`/`.jsonl`, any parsed structure for `.json`/`.yaml`, `bytes` or `str` for everything else, never a `DataFrame` or an object core would have to guess at. A step's `run` and a template's `aggregate` both return a flat mapping of scalars — the same set `io.record` takes — with a NumPy scalar coerced, anything structural a `ContractError`, and an `Estimate` at `summary` scope the one exception. Core raises `PublishableError` → `ContractError` / `ArtifactError` → `ArtifactExistsError`, each carrying the same stable `E-` identifier a diagnostic prints. (`reference.md` § The importable surface, § Steps and artifacts, § Creating a plugin)
- **What core hands a step is minimal and immutable on purpose.** `io.units` supports three operations — iterate, `len`, index — plus `.train`, on the same argument `aggregate`'s four-operation table rests on; a `Unit` is frozen and hashable by `key`, because one roster is resolved per run and shared across every condition. `cfg` is dot-access with no methods at all (so no parameter name can be shadowed) — the one exception being the root node's single `raw` accessor, which `validate` and a template's `validate(config)` need and which costs the one top-level name core already owns — raising `ContractError` on a path the config doesn't hold and `AttributeError` on an underscore-prefixed name. `self.rng` is the generator to draw from — core also seeds the `random` and legacy `numpy.random` globals, but only so an unreachable library is covered, and a concurrent step must give each worker its own stream. `scope` is read from the class before any instance exists, and `__init__` is core's. (`reference.md` § The importable surface, § The unit list is three operations, § Randomness)
- **`parameter_spec` is the single source of truth** for what `init` writes, what its inline comments say, and what `validate` enforces. There is deliberately no separate defaults file. `Param` types are `str`/`int`/`float`/`bool`/`list` (with `item_type`); omitting `default` is what makes a parameter required, and `default=None` requires `nullable=True`. `requires_env` is the one thing a `Param` carries that isn't a constraint on its value — it needs `choices` and must be total over them, and it stays out of the closed constraint vocabulary for that reason.
- **Core vs. plugin test:** would it be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark? If not, it's a plugin. Core ships exactly one template, `generic`. A template *reads* the whole config in `validate` (cross-block rules are properties of what its steps do) but declares nothing outside `parameters`.
- **Greenfield only** — no `adopt` command, ever. Core validates *declarations* and verifies *effects*; it never inspects the body of user Python.
- **`uv` and git are mandatory**, not optional paths.

The stated non-promises — adaptive/sequential designs, per-condition pipeline variation, factorial main effects and interactions, bit-identical reruns, scientific validity — are deliberate refusals with reasons attached, not gaps waiting to be filled. Treat a request to add one as a design change requiring an argument against `design-principles.md`, not a feature request.

## Misreadings this repo has made more than once

Every one of these was made by someone competent, reading carefully, more than once. They are not
carelessness — each is a reasonable reading that happens to be wrong here, so knowing the rule is what
prevents it. The slice ledgers hold the instances; this section is the short form worth carrying into
every session.

### Reading the documents

| Misreading | The rule |
|---|---|
| Taking a § Validation row's own wording as its whole scope | Several rows read as method-independent while the **surrounding prose carries the gating** — *Ratio names levels* and *Allocation strata exist* apply only under `random`/`blocked`. Read the section, not the cell |
| Treating a row's example as its definition | An example can be a fault under *every* candidate reading, so the row looks settled and is not. *Attribute assignment resolves* showed a disjoint value set, which fails whether the rule is set equality or subset tolerance — the ambiguity survived until someone needed the answer |
| Citing a sentence whose job is to **contrast** as if it supported the claim | "An arm no unit resolves to is already refused" exists to distinguish that case from `min_units_per_cell`'s thin-but-nonzero gap. It was read as licence to route a hard refusal into a warning-shaped gap |
| Assuming a documented rule has code behind it | Five § Validation rows described checks with no emit site, no check and no test. **Grep for the code before building on the row**; a row and a code are the same check seen from two ends, and either end can be missing |
| Reading a temporary refusal as permanent, or the reverse | A `-UNSUPPORTED` suffix is the undocumented build family, retired wholesale and absent from the registry. A *narrow* refusal of a combination is documented, carries rows, and outlives the slice that minted it |
| Scoping a diagnostic by the helper it calls | `E-TEMPLATE-UNKNOWN` had **two** emit sites; a task scoped by `template_names()`'s single call site missed the second, which went on claiming "no installed template registers" under a § Errors row just rewritten to say otherwise. **§ Errors carries one row per code, not per emit site**, so a diagnostic's unit of work is every site that raises *or* reports it |
| Reading an unbuilt reader as a defect | An unbuilt reader of an **unbuilt** surface is specification — present tense is correct, and § Package layout's `— not yet built` carries it. An unbuilt reader of a **shipped** surface is a defect: `BaseTemplate.required_env` is declarable today on a class that ships, and nothing reads it |

### Writing checks that can fail

**Sixteen checks across the two H3c slices could not fail**, and roughly a dozen more in H7a — every one
caught by a mutation and none by reading. Run the mutation before believing the test, **and run it where
the behaviour lives** — not where the test happens to look. The shapes, each seen more than once:

| Shape | Why it passes anyway |
|---|---|
| A fixture whose numbers agree with the bug | An "undeclared level" ratio that was *also* partial; a 13-unit apportionment that matched a reverse-order mutant by coincidence; a cluster fixture where correct and buggy cluster counts were both 3 |
| A dimension no assertion can see | Per-stratum arm counts are **forced** by apportionment, so no count assertion can detect an RNG change. Deleting the shuffle, and replacing the seeded generator with `Random(0)`, both left the suite green — the second while `ArmPlan.seed` still *recorded* the ignored seed |
| An assertion implied by another in the same test | Arm sizes summing to the roster is arithmetic, not a check, once the sizes are pinned |
| A control asserting only absences | Passes identically if nothing ran. Pair it with something that must report |
| A parametrized test asserting a **failure** for both arms | Proves nothing about either arm's **success** path — `blocked`'s stratified draw was fully threaded and never exercised |
| Testing the refusal, never the honouring | `validate` refused bad `block_size` values while nothing checked the draw *used* a good one, so ignoring it entirely passed the suite |
| A mutation applied to a proxy | The extracted helper's body rather than the call site; the fixture rather than the wiring |
| Varying config **shape** when the property is about roster **content** | Nineteen adversary configs over one roster made every refusal roster-incidental. **A refusal that happens to fire must be attributed before it is counted** |
| A test whose **name** claims the guarantee | `test_..._message_matches_validates` compared each of two messages against **its own** hard-coded literal, so mutating one site failed one test and nothing compared the two. The name and docstring asserted an agreement no assertion made — and a reader greps for exactly that name and stops looking |
| A fixture with too few elements to distinguish the candidate orderings | Both documented orderings survived reversal with the suite green: one colliding name and one broken file cannot tell name order from import order. **Two elements only ever distinguish two answers** — with two names the reverse of insertion order *is* sorted order for one arrangement. Count the orderings you must rule out, then size the fixture so each yields a different answer |
| A monkeypatch left aimed at a name the code no longer calls | Rerouting a call site through a new helper silently defused a patch on the old name; the test kept passing while testing nothing. **When you move a call site, grep the suite for patches aimed at what you moved** |
| A seam named in the brief and instantiated by no fixture | Twice in one slice a distinction was described precisely — `declared` versus `n`, strata threaded into the clustered call — and **the mutation passed all 1700+ tests**, because no config made the two readings differ. Naming a seam is not testing it: ask what config separates the readings, then check it exists |
| The test's **reader** normalising the defect away | A resolved-values echo shipped as a YAML alias — one anchor, five `*id001` pointers — and **both tests used `yaml.safe_load`, which resolves aliases**. The defect lived in the serialization and the reader undid it before the assertion. When a defect could live in *how* a value is written, assert on the raw text |
| A **mutation** whose two branches cannot differ | A reviewer proposed proving a distinction by swapping to a value derived from the same source — a mathematical no-op no fixture could ever catch; a controller's proposed mutation was blind for a different reason. **A mutation is a claim too**: before trusting "this would prove X", check the two branches can actually produce different results |

### Answering a question with a proxy

Both fail-opens in H7a's "is this template local?" predicate came from the same move: answering with
something *correlated* rather than with the fact. First the class's module-name prefix — a scheme built
for **anti-aliasing** (two repos both holding `templates/my_assay.py`) and applied only to non-`__`
files, so a class defined in a sibling helper read as foreign and got core's `template_version` written
against it. Then a marker stamped on the class — right about where the class was *defined*, wrong about
who *owns* it, so registering a class the repo merely imported stamped a **shared** object process-wide
and permanently. **When a predicate keeps failing open, the proxy is the bug, not the guard.** Both were
closed by asking the direct question — does this class's defining file sit under *this* repo's
`templates/` — with a helper that already existed.

A corollary that cost its own round: **state read at the wrong moment is a third proxy.** The first fix
was placed where `sys.modules` had already been restored, which inverts the answer — a genuinely local
class's module is gone, while an external one is still cached.

### Habits that cost real work

- **A comment or docstring claiming a guarantee the code does not provide** — at least a dozen instances,
  including one that explicitly promised "any other `method` string takes the `by_attribute` path" (the
  fail-open defect written down as if intended), and three overreaching claims inside a single commit
  that was itself fixing overreaching claims. When you change a guard, re-read its justification. A
  sentence can also contradict **the argument that justifies the thing it describes**: "a collision among
  the files that *did* load is still found rather than masked" appeared at four sites including a
  normative § Errors row, while the reason load-failure is checked first is precisely that a collision
  verdict computed then would be computed over a partial set of claims. Both properties cannot hold.
- **A safety argument in a comment is a claim, and needs a mutation like any other.** A retry inside an `except` was widened, and its new comment argued the retry could never raise because the faults it handles "surface on the first call". **The first call was inside the `try`.** Patching the widened function to raise gave exit 1 with no `run.yaml` and no run directory — every execution paid for, the record lost. Written by someone whose task was closing findings about false comments, and it passed a review. If a comment says *this cannot happen*, make it happen.
- **Sweep for the claim, not for the file the claim was first noticed in.** Three sweeps in one slice stopped one file short — one covered `src/` and `docs/` but not `tests/`, one fixed a sentence in `correction.py` and missed the same sentence in the function that falsified it, one stopped at the file its brief happened to name.
- **A ledger line saying "filed" is not a filing.** A gap recorded as "registered against \<owner\>" existed only in the ledger; the defects file had no such entry. And an entry naming its owner as *"whichever slice does X"* points at a closed slice once X lands — **re-owner a deferral when the slice that filed it finishes**, or it reads as live work nobody holds. A filing's claims about the code go stale like any other comment; when you change code a `spec-defects.md` entry describes, re-read the entry.
- **Rewriting a sentence when a table row was the thing that was wrong.** "Importing one raises
  `ImportError` today" was false only while `register_template` sat in a row marked `not yet built` —
  splitting the row repaired it, because the sentence **derives** its claim from the `Status` column.
  Replacing it with an enumeration of names would have converted a self-maintaining statement into a
  maintenance obligation nobody owns, and a second source of truth for build state.
- **Locating a table row by position** ("the two rows above", "further up") — at least seven instances,
  wrong twice, once in a row no diff touched, falsified by an insertion that moved it. Name what a
  sibling row *does*. When you insert or remove a row, check every row it **moved**, and every count
  phrase near it.

### Two mechanical traps

- **Never filter the output of a sweep whose job is to find a string** — filter the file list. A reviewer
  checking this exact rule lost a true hit to `grep -v superpowers`, because the matching line contained
  that path. Prove each sweep can fail by running it against a string known to be present. This matters
  more now that the [development record](#the-development-record) is tracked: a sweep over the four
  documents must **name** them, since `*.md` no longer means what it used to.
- **`git checkout -- <file>` destroys uncommitted work**, twice mistaken for reverting a mutation. Keep a
  copy before mutating, and verify a revert by **behaviour**, never by `git status`.

## Checking consistency after any `*.md` edit

Editing one document is almost never a one-file change. Both passes below run before an edit is finished; the second is the one that catches real defects, and no tooling substitutes for it. The **cross-document** pass governs the four documents only — a [feasibility analysis](#feasibility-analyses) is exempt from it and subject to the mechanical pass in full.

**Mechanical.** Write these as throwaway greps or a short script each time rather than keeping a checker around — the repo ships no tooling, and each pass wants slightly different checks. Verify that every relative link and `#anchor` resolves, that no two headings in a file produce the same anchor, that every table's rows match its header's column count and no row is empty, and that no line carries trailing whitespace, a tab, or invisible unicode. Skip fenced code blocks in all of these: the docs contain markdown inside markdown, and a `##` or `|` there is content, not structure. After removing or renaming any string, grep the four documents, this file, and any feasibility analysis for what should no longer exist.

**Both passes govern those files only — never the [development record](#the-development-record).** A spec records what was decided when it was written and a scoping what was measured on its date; retro-editing either destroys the evidence they exist to hold. Correct one the way this repo corrects a published claim: append the correction and say what it replaces. The one exception is `spec-defects.md`, a live list, where a closed gap is struck rather than left to mislead.

**Cross-document.** These are the classes that actually drift, and none of them is visible to a mechanical check:

| Class | The rule |
|---|---|
| **The shared worked example** | README, `design-principles.md`, and `reference.md` describe *one* experiment. Changing a value in one means changing it everywhere it appears — see § The worked example below |
| **Config completeness** | Every config field documented anywhere in `reference.md` must appear in § The one config file, whose fenced example calls itself "the config schema for template `generic` ... at full expansion: every parameter `publishable init` materializes, plus the optional blocks it leaves empty or undeclared." Adding one can invalidate downstream `run.yaml` examples that were correct under the previous default |
| **Enum comments** | An inline `# a \| b \| c` comment must list every value its corresponding table or section defines |
| **Schema fields in prose** | A field named in prose must exist in the `config.yaml` or `run.yaml` example, and vice versa |
| **Declared vs. derived** | If one passage says a value is derived, no other may show it as a settable input. This is how `replication.design` contradicted four passages at once |
| **Versions** | Version numbers in examples must agree with `CITATION.cff` and the README's v0.x notice |
| **Prevented mistakes** | Anything in `experimental-designs.md` § Mistakes core prevents must be structurally impossible in the schema, not merely discouraged |

### The worked example

One experiment runs through README, `design-principles.md`, and `reference.md`: config `cohort-pilot`, package `cohort_pilot`, template `generic`. (`experimental-designs.md` deliberately uses varied domain examples instead — `stimulus.contrast`, `drug.dose`, `samples.csv`, `cell_id` — because its job is to show many designs, not one pipeline.) The steps and scopes are `step01_load_cohort` (run) → `step02_fit_model` (condition) → `step03_analyze` (repeat) → `step04_compare_methods` (summary). It sweeps `analysis.method` over pearson/spearman/kendall — 3 conditions × 5 seed repeats — against 240 units, of which 228 complete and 12 fail. Results are r = 0.581 baseline (ci95 [0.488, 0.661]), 0.607 spearman ([0.517, 0.683]), 0.412 kendall ([0.347, 0.477]); delta 0.026 with a paired ci95 of [−0.007, 0.059] (kendall's is −0.169, [−0.213, −0.125]), and a seed `repeat_spread` std of 0.014. **Those intervals were checked numerically against a synthetic 228-unit table and must not be narrowed back.** The two r intervals agree with both Fisher-z and a percentile bootstrap; kendall's is a percentile bootstrap of τ, because Fisher-z on τ is the wrong transform and is what the earlier [0.298, 0.514] came from — no 228-unit dataset gives τ = 0.412 a half-width above 0.087. The deltas come from a joint resample over the paired intersection, whose half-width does not go below ≈0.033 for a linear-versus-rank contrast at this n, so the earlier ±0.009 was unreachable. A consequence to preserve rather than tidy away: the spearman delta's interval spans zero while `h1` is supported on `observed`, and `reference.md` § Pre-registration turns that into the point of `verdict_evaluated_on`. `cohens_d` is `null` throughout: `r` is derived by `aggregate(units)`, and Cohen's d needs a per-unit value to difference — don't reintroduce an effect size for it. The per-condition intervals are deliberately much wider than the delta's — that contrast *is* what `allocation: within` buys, and flattening it would reintroduce the defect this scheme fixed. Hash prefixes are `8e21` (code), `1a2b` (parameters), `3d8a` (input manifest), `6b1f` (uv.lock), and the run IDs are `run_2026-08-06T14-02-11Z_8e21ab3` and `run_2026-08-07T09-14-03Z_8e21ab3`. README uses `~/data` and `~/results` paths where `reference.md` uses `/secure/...`, and README's `demo` walkthrough reuses the same statistics under a separate `correlation_pilot` experiment, and carries its own code hash prefix `2f5c8d0` — a different `src/` cannot share one, since `code_hash` covers the tree. Those differences are deliberate, the rest is not.

## Feasibility analyses

A **feasibility analysis** asks whether a real research project could be run on `publishable` as specified: which of its experiments the schema expresses, what each config actually looks like, what executing it costs, and — the load-bearing half — which parts core refuses and where each refusal routes. It is the main way this repo gets evidence from outside itself, because the spec is otherwise validated only against its own worked example.

One analysis per file, at `docs/feasibility-<subject>.md`, kebab-case matching its title. Link it from § The documents above.

**These files are exempt from the cross-document passes**, and that exemption is deliberate rather than laziness: an analysis carries the subject project's own cohorts, statistics, and hash prefixes, and reconciling them with `cohort-pilot` would destroy the thing being analyzed. The **mechanical** pass still applies in full — links, anchors, tables, whitespace, `×` for multiplication, hyphens in anchors.

### The procedure

1. **Read the source project for its goal, not its implementation.** State in one sentence what each source repository is trying to learn. Do not replicate its file layout, CLI, or artifact names — those are the parts `publishable` is meant to replace.
2. **Name what the source hand-rolled that core already owns**, as a table. Manifests, run ledgers, timestamped directories, split records, usage reports, and reproduce commands are the recurring ones. This is both the strongest adoption argument and the list of things a proposed plugin must not rebuild.
3. **Express each experiment in the spec's vocabulary**, in this order: the problem in two sentences, the design decision (which axis, which repeat kind, which allocation, where the units come from), then the actual YAML.
4. **Every YAML must be checkable against `reference.md` § The one config file**, whose fenced example is the config schema for template `generic` at full expansion — every parameter `publishable init` materializes, plus the optional blocks it leaves empty or undeclared. Any field you show must exist there or in the proposed template's `parameter_spec`; a template declares nothing outside `parameters`, so there is no top-level block of a plugin's own.
5. **Do the arithmetic before writing the YAML, not after.** Every config states its condition count, its repeat structure, its execution count against `limits.max_executions`, its unit-executions (which is what a metered run is billed by, and what `dry-run` prints), and its cost and runtime from anchors the source itself observed. A feasibility section without execution counts is decorative — and a repeat structure chosen without them is how a translated design silently costs several times the original.
6. **Name every refusal with its route.** Interactions, dose-response orderings, differences-in-differences, adaptive selection, model fitting, counterbalancing, roster-changing variants. `experimental-designs.md` § What core will not do for you is the list to check against; the route is usually a `summary`-step `Estimate`, a separate run joined in a `study`, or a `report_by` stratum.
7. **Separate what is not an experiment at all.** Reference-standard adjudication, governance firewalls, and human decisions made between runs are not pipelines core executes. Say so explicitly — treating them as runs is the failure mode this step exists to catch.
8. **Propose the plugin last, from what the designs actually needed.** Apply the core-vs-plugin test to every piece, keep the registered artifacts to the four registries, and say which of them the domain does *not* need. Watch the correction family: every metric a template's `aggregate` returns is comparisons × metrics, so a template returning twenty diagnostics corrects every interval in the run for numbers nobody reads.
9. **Record the gaps the analysis found in the spec**, separately from the analysis itself. These are the deliverable's second output — a real project pressing on the schema is where an under-specified rule shows up.
10. **Never state a build fact undated.** A claim about what the tool *does today* — that a config validates, that a command dispatches, that a slice has landed — is perishable in a way a spec claim is not, so it must be dated and pinned to a commit where it is made, and kept in a section of its own so a reader can see at a glance what has an expiry date. `feasibility-llm-growth-studies.md` § Executability on this build is the shape: one section, "Measured on \<date\> against commit \<sha\>", and every refusal named by its code. Anything you are not willing to date belongs in the present tense of the specification instead — write it as what `publishable` specifies, not as what it does. This is the same distinction `reference.md` § CLI reference marks with its `Status` column, and it exists because an undated build claim reads as a spec claim a month later, which is how an unbuilt command was once asserted as fact.

### Traps this repo has already hit

| Trap | The rule |
|---|---|
| A roster-changing variant written as a sweep axis | `data.units` is one roster per run. A different sampling ratio, cohort cap, or eligibility population is a different run, joined in a `study` — not a condition |
| An eligibility change written as a roster change | When the superset roster is shared, a condition that admits fewer units uses `io.skip`, landing in `ineligible`. Eligibility must be constant across a condition's repeats, or the unit is counted `failed` |
| A path or a slashed identifier as a swept value | A swept value must render as `[A-Za-z0-9._+-]+`. Sweep an alias or an ID and resolve it inside the step |
| A metric averaged, ordered, or combined across two contrasts | Contrasts do not nest. It is an interaction, and it is a `summary`-step `Estimate` |
| A mean *absolute* difference read as a contrast | A contrast is the mean of the differences. Two one-sided bounds, or an `Estimate` |
| A model fitted where the split does not exist | `optimizer`-style configs need a `holdout` or a `fold`; this is exactly the cross-block rule a template's `validate` is for |
| Per-request measurements written to a side report | Tokens, latency, and attempts are per-unit measurements. Through `io.record` they become `basis: units` with intervals; in a usage report they have no denominator |
| A repeat structure copied from the source without costing it | Repeats multiply metered work. Put expensive fitting at `condition` scope, and say in `replication.rationale` what the repeat count bought |

## Documentation conventions

- Filenames are kebab-case, matching the doc's title.
- **Hyphen, never an en dash, in anything that becomes a filename or an anchor.** Headings use `dose-response` and `case-control`, not `dose–response` — GitHub's slugger strips an en dash entirely, so `Dose–response` silently becomes `#doseresponse`, an anchor nobody would guess when hand-writing a cross-reference. This overrides the Unicode preference below, which applies to prose and diagrams only.
- Cross-references between the four documents are dense and anchor-based. Renaming a heading breaks links elsewhere — grep the other files for the old anchor.
- Cite another file by section — `reference.md` § "Package layout" — never by line number. Line numbers go stale on the next edit above them.
- `×`, not `x`, for multiplication, including inside fenced blocks. Unicode is already the house style there (`├──`, `←`, `·`).
- README writes bare `publishable <cmd>`; `reference.md` writes `uv run publishable <cmd>` for commands run inside a project and bare for `new`, `demo`, and `study`. Both are correct — README installs globally at its Try it step. Describing this so it isn't "fixed" in either direction.
- `<!-- publishable:begin ... -->` / `publishable:end` regions in the docs are examples of *machine-managed* README regions in generated projects, rewritten by `publishable docs`. Text outside them is hand-written.
- Prose style is declarative and reason-giving: state the rule, then why it exists. Tables carry the dense material.
