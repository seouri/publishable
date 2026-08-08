# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status: specification only, no implementation

`git ls-files` returns eight files. There is no `src/`, no `pyproject.toml`, no `tests/`, and no installed CLI — the entire repo is `README.md`, `CITATION.cff`, `LICENSE` and `docs/*.md`.

**There are no build, lint, or test commands.** Do not invent them, and do not run `publishable <anything>`: the binary does not exist here. The commands described throughout the docs are the CLI this project *specifies*, not commands available in this working tree. Likewise, `docs/reference.md` § "Package layout" is a *planned* source tree — those files do not exist yet.

Work in this repo is therefore documentation work: refining the design, keeping the three docs consistent with each other and with the README.

## The documents

| File | Role |
|---|---|
| `README.md` | The pitch and the whole arc, for someone deciding whether to use it |
| `docs/design-principles.md` | **Normative.** Why each rule is what it is |
| `docs/experimental-designs.md` | How each experimental design is expressed; what core prevents and refuses |
| `docs/reference.md` | Config schema, CLI, `io` API, templates, sweeps, artifact layout |

`design-principles.md` is the tiebreaker. Read it before proposing a change to any rule — if a rule looks arbitrary, that file explains it, and if it doesn't, that gap is itself worth fixing.

## Invariants a change must not quietly break

These are load-bearing across all four documents; contradicting one in a single section creates a real inconsistency, not a wording nit.

- **Operation commands take paths and nothing else.** No parameter flags, no selectors, no behavior-changing env vars. Modes get their own command names (`dry-run`, `draft`, `resume`) rather than `--dry-run`/`--allow-dirty`. Only creation commands (`new`, `plugin new`, `generate`/`init`, `study new|add`) take arguments beyond a path. (`design-principles.md` § Everything is in the file)
- **Three hashes, split on purpose.** `code_hash` covers `src/**` and `templates/**` only — the code your repo supplies, a plugin's being pinned by `uv.lock` instead — separate from `parameters_hash` and `input_manifest_hash`. That split is what makes "same code, different parameters" provable across unrelated commits.
- **`input_dir`/`output_dir` may never resolve inside the git repo**, checked at generate, validate, and run.
- **Condition vs. repeat.** A condition is a difference being measured; a repeat is a difference being averaged over. Statistics aggregate *within* a condition and compare *across* conditions — never the reverse.
- **A repeat is an execution, so the kinds are exactly the three things a re-execution can change: `seed` (RNG state), `fold` (which units it sees), `batch` (the state of the apparatus it measures through — see § The apparatus core can only observe).** A `batch` takes no field but `n`, executes in order with `order: randomized` shuffling inside it, and `validate` warns when no step sets `nondeterministic = True`. Resampling and permutation are `statistics.resample`/`statistics.null_test` over the unit table (thousands of executions otherwise, and an all-permuted design has no unpermuted value to test); technical replication is `data.units.measurements`, collapsed at unit resolution (re-running an identical step recomputes the same answer); a fixed holdout is `data.units.holdout`. `validate` rejects `bootstrap`, `permutation`, `technical`, `biological`, and `holdout` as kinds by name.
- **Units are the inference base; repeats never are.** Every interval core reports is computed from the per-unit table, `n` counts units (`resolved`/`completed`/`ineligible`/`failed`, where `io.skip` declares the third and `max_failed_fraction` guards only the fourth), and repeat dispersion is reported separately as `repeat_spread`. A metric that exists only as a step-returned scalar is `basis: repeats` and gets **no** `ci95`; the one interval core stores without computing is an `Estimate` returned by a `summary` step, marked `reported: true`, outside the correction family and never recomputed. A hypothesis may name one — it takes no `compare` — and the verdict records `verdict_rests_on: reported` rather than `computed`. Pairing is over units, never over repeats, and a contrast — `vs_baseline` or a declared `statistics.contrasts` entry — is computed over the intersection of both sides' completed units, recorded as `n_paired` — and its interval is its own construction over that intersection (`paired_t_over_units`, `paired_percentile_over_units` drawing once for both sides, or the `welch_`/`unpaired_` counterparts), never a difference of the two sides' intervals. Holm ranks on the point estimate over half the raw `ci95` width, because the family often carries no p-value at all, which is also why `fdr_bh` over such a family warns. `data.units.weight_by` weights an enriched sample's estimates and records `weighted_by`; `statistics.report_by` repeats metrics over strata without adding executions or joining the correction family; a subgroup you want to *test* is a contrast with `within`, which does join it. Contrasts compare conditions and do not nest: anything comparing two contrasts — a dose-response ordering, a difference-in-differences, a nested mean over cells — is an interaction and stays a `summary`-step `Estimate`. The table `aggregate` receives supports exactly four operations — row iteration, column access, `len`, `columns` — deliberately not a `DataFrame`, so core can change what backs it without breaking every plugin. (`reference.md` § The unit table is the inference base, § Templates)
- **`parameter_spec` is the single source of truth** for what `init` writes, what its inline comments say, and what `validate` enforces. There is deliberately no separate defaults file. `Param` types are `str`/`int`/`float`/`bool`/`list` (with `item_type`); omitting `default` is what makes a parameter required, and `default=None` requires `nullable=True`.
- **Core vs. plugin test:** would it be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark? If not, it's a plugin. Core ships exactly one template, `generic`. A template *reads* the whole config in `validate` (cross-block rules are properties of what its steps do) but declares nothing outside `parameters`.
- **Greenfield only** — no `adopt` command, ever. Core validates *declarations* and verifies *effects*; it never inspects the body of user Python.
- **`uv` and git are mandatory**, not optional paths.

The stated non-promises — adaptive/sequential designs, per-condition pipeline variation, factorial main effects and interactions, bit-identical reruns, scientific validity — are deliberate refusals with reasons attached, not gaps waiting to be filled. Treat a request to add one as a design change requiring an argument against `design-principles.md`, not a feature request.

## Checking consistency after any `*.md` edit

Editing one document is almost never a one-file change. Both passes below run before an edit is finished; the second is the one that catches real defects, and no tooling substitutes for it.

**Mechanical.** Write these as throwaway greps or a short script each time rather than keeping a checker around — the repo ships no tooling, and each pass wants slightly different checks. Verify that every relative link and `#anchor` resolves, that no two headings in a file produce the same anchor, that every table's rows match its header's column count and no row is empty, and that no line carries trailing whitespace, a tab, or invisible unicode. Skip fenced code blocks in all of these: the docs contain markdown inside markdown, and a `##` or `|` there is content, not structure. After removing or renaming any string, grep all five files for what should no longer exist.

**Cross-document.** These are the classes that actually drift, and none of them is visible to a mechanical check:

| Class | The rule |
|---|---|
| **The shared worked example** | README, `design-principles.md`, and `reference.md` describe *one* experiment. Changing a value in one means changing it everywhere it appears — see § The worked example below |
| **Config completeness** | Every config field documented anywhere in `reference.md` must appear in § The one config file, which calls itself "the complete parameter set." Adding one can invalidate downstream `run.yaml` examples that were correct under the previous default |
| **Enum comments** | An inline `# a \| b \| c` comment must list every value its corresponding table or section defines |
| **Schema fields in prose** | A field named in prose must exist in the `config.yaml` or `run.yaml` example, and vice versa |
| **Declared vs. derived** | If one passage says a value is derived, no other may show it as a settable input. This is how `replication.design` contradicted four passages at once |
| **Versions** | Version numbers in examples must agree with `CITATION.cff` and the README's v0.x notice |
| **Prevented mistakes** | Anything in `experimental-designs.md` § Mistakes core prevents must be structurally impossible in the schema, not merely discouraged |

### The worked example

One experiment runs through README, `design-principles.md`, and `reference.md`: config `cohort-pilot`, package `cohort_pilot`, template `generic`. (`experimental-designs.md` deliberately uses varied domain examples instead — `stimulus.contrast`, `drug.dose`, `samples.csv`, `cell_id` — because its job is to show many designs, not one pipeline.) The steps and scopes are `step01_load_cohort` (run) → `step02_fit_model` (condition) → `step03_analyze` (repeat) → `step04_compare_methods` (summary). It sweeps `analysis.method` over pearson/spearman/kendall — 3 conditions × 5 seed repeats — against 240 units, of which 228 complete and 12 fail. Results are r = 0.581 baseline (ci95 [0.488, 0.661]), 0.607 spearman ([0.517, 0.683]), 0.412 kendall ([0.298, 0.514]); delta 0.026 with a paired ci95 of [0.017, 0.035] (kendall's is −0.169, [−0.181, −0.157]), and a seed `repeat_spread` std of 0.014. `cohens_d` is `null` throughout: `r` is derived by `aggregate(units)`, and Cohen's d needs a per-unit value to difference — don't reintroduce an effect size for it. The per-condition intervals are deliberately much wider than the delta's — that contrast *is* what `allocation: within` buys, and flattening it would reintroduce the defect this scheme fixed. Hash prefixes are `8e21` (code), `1a2b` (parameters), `3d8a` (input manifest), `6b1f` (uv.lock), and the run IDs are `run_2026-08-06T14-02-11Z_8e21ab3` and `run_2026-08-07T09-14-03Z_8e21ab3`. README uses `~/data` and `~/results` paths where `reference.md` uses `/secure/...`, and README's `demo` walkthrough reuses the same statistics under a separate `correlation_pilot` experiment; those differences are deliberate, the rest is not.

## Documentation conventions

- Filenames are kebab-case, matching the doc's title.
- **Hyphen, never an en dash, in anything that becomes a filename or an anchor.** Headings use `dose-response` and `case-control`, not `dose–response` — GitHub's slugger strips an en dash entirely, so `Dose–response` silently becomes `#doseresponse`, an anchor nobody would guess when hand-writing a cross-reference. This overrides the Unicode preference below, which applies to prose and diagrams only.
- Cross-references between the four documents are dense and anchor-based. Renaming a heading breaks links elsewhere — grep the other files for the old anchor.
- Cite another file by section — `reference.md` § "Package layout" — never by line number. Line numbers go stale on the next edit above them.
- `×`, not `x`, for multiplication, including inside fenced blocks. Unicode is already the house style there (`├──`, `←`, `·`).
- README writes bare `publishable <cmd>`; `reference.md` writes `uv run publishable <cmd>` for commands run inside a project and bare for `new`, `demo`, and `study`. Both are correct — README installs globally at its Try it step. Describing this so it isn't "fixed" in either direction.
- `<!-- publishable:begin ... -->` / `publishable:end` regions in the docs are examples of *machine-managed* README regions in generated projects, rewritten by `publishable docs`. Text outside them is hand-written.
- Prose style is declarative and reason-giving: state the rule, then why it exists. Tables carry the dense material.
