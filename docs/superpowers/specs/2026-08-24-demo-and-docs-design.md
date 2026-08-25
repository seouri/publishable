# H9d — `demo`, `docs`, `list-templates`: the guided arc and the managed-region machinery — design

**Written 2026-08-24 against `main` at `8413c16`** (clean tree, verified with `git status --porcelain` before and
after every probe). H9d is the **last slice of the command surface**: after it, only
[H3c-3's remaining 14](../H3c-3-SCOPING.md) — folds and holdouts inside cells — remain in the whole
project. Anything this design declines and H3c-3 does not own is **unowned**, and saying which is which
is part of the deliverable (§ 4).

The scoping is [`H9-SCOPING.md`](../H9-SCOPING.md), measured 2026-08-23 at `822fe4b`; its § 6, § 7.1,
§ 7.2 and § 8 are H9d's. **A scoping expires**, so every claim it makes that this design rests on was
re-measured, and the four places it is wrong or incomplete are in § 3.

Four controller rulings bind this slice — **CC**, **DD**, **EE**, **FF** — and each is Decision 1
through 4 below.

---

## 0. What was measured, before any decision

Everything in this section was produced by **running**, outside this repository, in the session
scratchpad. The repo tree was verified clean with `git status --porcelain` before and after. Nothing
under `src/`, `tests/` or the four documents was edited by this pass.

**The whole README walkthrough was built and run by hand**, five times, as a `publishable new` +
`publishable generate experiment` project with a three-step pipeline, a `baseline` + two-condition
sweep over `analysis.method`, five `seed` repeats, 240 units of which 12 fail. It reached
`status: completed` at exit `0`. **That is the shape proof this design rests on**, and it falsified
six documented claims on the way.

| # | Measured | How |
|---:|---|---|
| M1 | `GenericTemplate` declares **no `aggregate`** — it inherits `BaseTemplate.aggregate`'s `{}` | read `src/publishable/templates/builtin/generic.py`, all 26 lines |
| M2 | `reference.md` § Templates' fenced class is `@register_template("generic")` **and shows an `aggregate` computing pearson/spearman/kendall** | read § Templates |
| M3 | The same document's § Validation says, in one row, *"template `generic` defines no `aggregate`"* and, in another row of the same table, *"template `generic`'s `aggregate` returned `r`"* | read § Validation |
| M4 | `self.rng` is a **`random.Random`** | `src/publishable/base_step.py`: `self.rng: random.Random = random.Random(seed)` |
| M5 | `reference.md` documents it **twice** as a `numpy.random.Generator` — § Using them in step code's fenced comment and § Randomness' table row | `grep -n 'self.rng' docs/reference.md` → 5 hits, each read and attributed |
| M6 | A step calling `self.rng.normal(...)` **fails the execution**: `AttributeError: 'Random' object has no attribute 'normal'`, 15 executions failed, `run` exit `3` | ran it |
| M7 | **No test in `tests/` mentions `self.rng` at all** | `grep -rn 'self.rng' tests/*.py` → zero hits |
| M8 | `run`'s **entire stdout** for a successful 19-execution run is the warning block and one line: `run.yaml → <path>`. No banner, no progress bars, **no results table** | captured stdout and stderr to files and read them whole |
| M9 | `dry-run` prints **19 executions** for that plan — 1 `run`-scoped + 3 `condition`-scoped + 15 `repeat`-scoped — while § What `demo` walks you through's stop 4 and README both say **15** | ran `dry-run` |
| M10 | A **derived** metric carries **no `repeat_spread`**; a recorded numeric column does | read `run.yaml`: `r` has no such key, `pred`/`truth` carry `{std: …, n: 5, kind: seed}` |
| M11 | A derived metric gets `method: percentile_over_units` and `resample_draws: 2000` with **no `statistics.resample` declared anywhere in the config** | read `run.yaml` |
| M12 | A derived metric computed from **declared attributes** gets a per-condition percentile interval but its **paired contrast draw yields `0 of 2000`** — `W-STATS-CONTRAST-RESAMPLE-THIN`, `ci95: null`, `method: null`. The same metric computed from **recorded columns** gets `paired_percentile_over_units` and a real interval | two runs differing **only** in which column `aggregate` reads |
| M13 | Declared attributes from `index.csv` arrive as **`str`**: `spearmanr` over them ranks lexicographically and answers `0.4212` where the float column answers `0.6781` | compared the two runs' values |
| M14 | **Every numeric recorded column publishes its own metric and joins the correction family** — `family_size: 6`, `family: {comparisons: 2, metrics: 3}` for one derived metric beside two recorded columns. A **non-numeric** recorded column publishes none: `{comparisons: 2, metrics: 1}` | read both runs' `vs_baseline` blocks |
| M15 | A unit becomes `failed` by being handed to a recording execution and **neither recorded nor skipped** — `runner._units_failed_anywhere`. 12 of 240 is producible from a step that skips twelve keys | read the function, then produced `{resolved: 240, completed: 228, ineligible: 0, failed: 12}` |
| M16 | `limits.max_failed_fraction` materializes at **`0.2`**, so 12/240 = 0.05 passes | `src/publishable/materialize.py` |
| M17 | **`W-ENV-UNLOCKED` fires on every `run` in a `publishable new` project** — the demo's first run included | ran it |
| M18 | `scaffold.GITIGNORE` holds `.env`, `__pycache__/`, `*.py[cod]`, `.venv/` — **no `.demo-progress`** | read `src/publishable/scaffold.py` |
| M19 | `scaffold.README` writes **two** regions (`overview`, `experiments`), with `## Experiments` **outside** its region and prose inside it, and **no `cp .env.example .env` line** | read the constant, then read a scaffolded README back |
| M20 | **There is no region parser or rewriter anywhere in `src/`** — `publishable:begin` appears at exactly four lines, all in `scaffold.py` | `grep -rn` for both marker spellings over `src/` and `tests/` |
| M21 | `src/publishable/readme_templates/` is an **empty package**: `__init__.py`, **0 bytes**, nothing else | `wc -c`, `ls` |
| M22 | § Package layout gives `docs.py` a row marked `— not yet built` and gives **`demo` and `list-templates` no row at all**; it also names `examples/generic/`, **which does not exist** | read § Package layout; `ls examples/` → no such directory |
| M23 | An **installed** template's `Claim.cls` is `None` by construction, so `get_template` returns `None` for it and `_merged` drops it — **`list-templates` cannot print an installed plugin's parameter spec without importing the package**, which is the thing `validate` deliberately does not do | read `templates/registry.py` `_claims`/`_merged`/`get_template` |
| M24 | `report`'s markdown `## Conditions` section is a **15-column raw table** (one row per condition × metric, `by_attribute`/`by_level`/`n` as nested mappings) — not README's compact four-column one | ran `publishable report` on the walkthrough's `run.yaml` |
| M25 | The **bytecode-cache defect reproduces at HEAD**: `discover_local` served `f_probe` twice, from two different files at one path, in one process, no exception, no diagnostic | ran the filing's own recipe |
| M26 | `NOT_BUILT_COMMANDS` holds exactly three keys — `demo`, `docs`, `list-templates` — and `NOT_BUILT_GENERATORS` is `{}` | read `cli.py` |
| M27 | `_dispatch`'s `any(n.startswith(f"{command} "))` group fallback **already matches nothing**: no two-token key remains | read `_dispatch` |
| M28 | `E-GIT-NO-REPO`'s § Errors row says *"Eight paths reach it"* and enumerates two uncaught, three caught **by code**, three caught **by type** | read the row; `grep -rn 'find_repo_root' src/publishable/*.py` |
| M29 | `tests/test_cli.py`'s `_H5A_ARM_D_README_LINES`' **first five entries are exactly README's demo-transcript lines**, and the test that reads them is H6b guard-pin **arm R, sole authorized editor NONE** | read the tuple and the docstring |

---

## 1. The four controller rulings

### Decision 1 (Ruling CC) — `list-templates` is H9d's, and the spine's H9 row is amended by appending

**Question.** Which slice owns `list-templates`? It is `NOT BUILT`, it is in no H9 charter row, and H9d
is the last slice with a CLI surface.

**Answer.** **H9d owns it.** The spine design
([`2026-08-08-implementation-spine-design.md`](2026-08-08-implementation-spine-design.md)
§ The hardening slices) is amended by **appending** a dated note to its *Order, amended against outside
evidence* section — never by editing the H9 row in place. Its own 2026-08-22 amendment and same-day
correction are the precedent, and § Checking consistency after any `*.md` edit forbids retro-editing a
spec: *"append the correction and say what it replaces."*

**Grounds, measured.** Its only chartered home was H7:
[`2026-08-14-project-local-templates-design.md`](2026-08-14-project-local-templates-design.md)
says *"`list-templates` … are all H7b/H7d"*, and four H7 scopings repeat it — `H7a-SCOPING.md`,
`H7b-SCOPING.md`, `H7b-SCOPING-2.md`, `H7b-PartB-SCOPING.md`, the last two recording that it stays
`NOT BUILT` *"so nobody folds it in unbriefed."* **H7 closed without it.** The one live routing is
H8c's design § *What is not H8c's*: `| list-templates | **H9**'s list, still NOT BUILT |`. **The
spine's H9 row never received it.** So one closed slice's charter, one completed slice's routing to
H9, and an H9 charter row that never took delivery.

**And the general form is the point.** A command orphaned by a closed family is found by **re-reading
the charter against the code** — `NOT_BUILT_COMMANDS` has three keys and the H9 row names two of them
— not by waiting for someone to notice. Four scopings said *"it is still H7's"* and were each right at
the moment they were written and wrong the day H7 merged; none of them re-owned it, which is the same
fault `spec-defects.md` names by name (*"re-owner a deferral when the slice that filed it finishes"*)
applied to a charter rather than to a filing.

**Alternatives rejected.** *Leave it unowned* — there is no slice after H3c-3, and H3c-3 is folds
inside cells, so unowned means never. *Fold it into H3c-3* — its surface is the template registry,
which H3c-3 does not touch, and it would be work handed to a slice that cannot review it.

**Cost if wrong.** H9d ships one more command than its charter names, in a slice whose other two
commands already need the same merged-template machinery (§ 2, Decision 8). The cost of the opposite
error is a specified command that never dispatches, with `NOT_BUILT_COMMANDS` carrying it forever and
the `Status` column telling every reader it is coming.

### Decision 2 (Ruling DD) — `demo` produces its own numbers, and README's `correlation_pilot` transcript becomes what `demo` prints

**Question.** README § Try it asserts the worked example's exact intervals over 228 of 240 units.
`CLAUDE.md` § Purpose and acceptance bar says exact reproduction *"would mean reverse-engineering a
dataset to hit three interval targets."* Which side moves?

**Answer.** **`demo` generates a real dataset, runs the real arc, and README's demo numbers become
whatever `demo` actually prints.** `cohort-pilot`'s numbers do not move — not one digit.
`correlation_pilot` is a separate experiment (`CLAUDE.md` § The worked example says so: *"README's
`demo` walkthrough reuses the same statistics under a separate `correlation_pilot` experiment"*), and
**that sentence is the thing that stops being true**, deliberately and in writing.

**Grounds, measured.** The transcript's six statistics are `cohort-pilot`'s own, and they were checked
numerically against a synthetic 228-unit table **that is not in this repository**. A `demo` that
printed them would have to be handed a dataset engineered to hit them, which the acceptance bar
rejects by name. The remaining choice is between a transcript labelled illustrative and a transcript
that is true; a transcript that is true is worth more on the one page a new user reads first, and it
is now cheap, because M8 through M16 establish that the arc runs.

**What moves and what does not, exactly.**

- **Moves:** the three condition rows (`r`, `ci95`, `vs baseline`) and the attrition/spread line, in
  README's stop-5 block, to values a shipped test re-derives by running `demo` (§ 9, fixture A).
- **Does not move:** `run.yaml → ~/publishable-demo-data/results/run_2026-08-07T09-14-03Z_2f5c8d0/run.yaml`.
  A run ID carries a **timestamp**, which no recipe reproduces, so that line is illustrative whatever
  else changes, and one sentence beside the block says so. Keeping it byte-identical also keeps
  `2f5c8d0` out of the arm-R edit and out of `CLAUDE.md` § The worked example, which names it.
- **Does not move:** every `cohort-pilot` literal in README, `design-principles.md` and
  `reference.md`. Guard-pin arm R's `DESIGN_PRINCIPLES` and `REFERENCE` parametrizations already prove
  this and are **cited rather than re-pinned** (§ 8) — re-pinning the same list is the *same list
  pinned twice* fault H8a hit.

**Alternatives rejected.** *Label the transcript illustrative and change nothing* — cheapest, and it
leaves README asserting numbers no run produces, which is the *documented rule with no code behind it*
defect on the highest-traffic page in the repo. *Engineer the dataset to hit `cohort-pilot`'s targets*
— refused by the acceptance bar. *Delete the numbers from README* — a transcript with no numbers does
not show what `run` buys, which is the block's whole job.

**Cost if wrong.** README shows numbers no run produces. That is the defect this ruling exists to
close, so getting the *mechanism* wrong (a recipe that is not reproducible across platforms) reopens
it silently — which is why § 9 treats `demo`'s dataset as a fixture with its determinism argued rather
than assumed.

### Decision 3 (Ruling EE) — `docs` rewrites only what a region encloses, and a region it cannot find is a named refusal

**Question.** The documents specify **four** machine-managed regions; the scaffold writes **two**; there
is **no region parser anywhere in `src/`** (M19, M20). What are the four, and what happens when one is
missing or malformed?

**Answer.** The four are **`overview`, `credentials`, `experiments`, `templates`** — § The generated
README names the first three and § Templates names the fourth. `docs` rewrites the bytes **strictly
between** a region's `begin` and `end` markers, inclusive of neither marker line, and touches nothing
else in the file. **A missing or malformed region is a refusal with its own code, printed, at exit
`1`** — never a silence:

| Condition | Code |
|---|---|
| A `begin` marker with no matching `end` before EOF, or an `end` with no `begin` | `E-DOCS-REGION-UNBALANCED` |
| Two `begin` markers naming the same region in one file | `E-DOCS-REGION-DUPLICATE` |
| A region name core does not manage | `E-DOCS-REGION-UNKNOWN` |
| The README holds **none** of the four regions | `E-DOCS-NO-REGIONS` |
| No `README.md` at the repository root | `E-DOCS-NO-README` |

A README missing *some* of the four is **not** a refusal — it is the ordinary state of every project
scaffolded before this slice, and `docs` rewrites the regions it finds and **names the ones it did
not**, on stdout, at exit `0`. That asymmetry is the whole content of the ruling: *a command that
silently rewrites nothing looks identical to one that worked*, and a command that refuses a
legitimately older README would be unusable on exactly the projects that need it.

**Grounds.** The markers exist to bound what a generator may overwrite; § The generated README states
it as *"a generator that populates one leaves everything outside it untouched."* Every failure mode
above is a case where the bound cannot be computed, and a rewrite performed against a bound that could
not be computed is the unrecoverable outcome. Prose outside a region is hand-written by definition and
has no other copy.

**Alternatives rejected.** *Rewrite the whole README from a template* — destroys hand-written prose,
which is the thing the markers exist to protect. *Skip a malformed region quietly* — indistinguishable
from success. *Re-insert a missing region* — `docs` would then be writing outside every existing
region, which is the one thing this ruling forbids; adding a region to an old README is
`publishable new`'s shape, not `docs`', and is Decision 9's behaviour change instead.

**Cost if wrong.** A user's hand-written prose outside a region is destroyed. It is unrecoverable, and
it is why the markers exist at all.

### Decision 4 (Ruling FF) — `docs` and `list-templates` take no path, and reuse the documented cwd exception rather than minting a second one

**Question.** `CLAUDE.md` § Invariants says the repository is decided by *"a walk-up from the path the
command was given, not from the working directory."* These two commands are specified with `*(none)*`
and have no path to walk up from.

**Answer.** Both walk up from **`Path.cwd()`**, and that is the **already-documented** exception, not a
new one. `reference.md` § Errors core raises' `E-GIT-NO-REPO` row states it in as many words: *"the
creation commands walk up from `Path.cwd()` rather than a path argument, being the commands with none
to walk up from — the one place `CLAUDE.md` § Invariants' … does not apply."* H9d **widens that
clause's subject** from *the creation commands* to *the creation commands, `docs` and
`list-templates`* and re-derives the row's count. It mints no second explanation.

**And the row's own enumeration is re-derived rather than incremented** (§ 3, trap 2). The row says
*"Eight paths reach it"* and enumerates two uncaught, three caught by code, three caught by type
(M28). H9d adds two, and they are of **different kinds**, so the sentence cannot be repaired by
changing one digit:

- **`docs`** — caught **by code** and re-reported through its own `Collector`, at exit `1`. A README
  to rewrite is the command's entire input, so no repository means nothing to do, and re-reporting
  rather than re-raising keeps the redaction pass over it (`main`'s `except PublishableError` handler
  uses **no `Collector`** — H9b's correction C3).
- **`list-templates`** — caught **by type**, leaving `repo_root=None`, exactly as
  `validate.validate_config` does. Core's `generic` and every installed claim are answerable without a
  repository; only `templates/**` discovery is skipped, and the output **says so on its own line**
  rather than silently listing a shorter set.

So the row becomes **ten paths: three uncaught-or-by-code additions counted correctly, and four caught
by type.** The exact final enumeration is derived by task 13 **by reading every call site**, not by
adding two to eight — the *§ Errors carries one row per code covering every emit site* rule, applied
to a row this slice is widening.

**Alternatives rejected.** *Give both a path argument* — a document change to two rows of § Operation
commands, and it makes `publishable docs` require a path to the repository you are standing in.
*State a new cwd exception scoped to these two* — a second source of truth for one rule, which is the
cost this ruling names. *H9-SCOPING § 7.2's own preferred answer — narrow `list-templates` to the
installed set and never a local template* — **rejected by this ruling**, and an implementer who reads
the scoping will otherwise build the narrower thing. A project-local template is the case § Templates
says path discovery exists for, and it is the case `docs`' `templates` region needs (Decision 8).

**Cost if wrong.** A second explanation of one rule — which is how a rule acquires two sources of
truth, and how the next reader concludes one of them is a defect.

---

## 2. The commands, decided

### Decision 5 — `demo`'s config names a **project-local** template, not `generic`

**Question.** README's stop-5 table reports `r` with an interval and a paired delta. Which template
derives it?

**Answer.** `demo` writes `templates/correlation.py`, registered as `correlation`, and
`configs/correlation-pilot/config.yaml` declares `experiment_type: correlation` with **no
`template_version`** (which is what `init` writes for a project-local template).

**Grounds, measured.** **`generic` defines no `aggregate`** (M1) and a template that defines none can
derive nothing — `reference.md` § Validation's *Hypothesis bound exists* row says so itself. So a demo
whose config named `generic` would print no `r` at all. Two further payoffs: `templates/**` is inside
`code_hash`, so the demo teaches the hash covering the analysis code; and it gives `list-templates`
(Decision 8) and `docs`' `templates` region (Decision 7) a real local template to find in the one
project a new user has.

**This exposes a three-way disagreement H9d does not repair** — § 3, finding 1. `reference.md`
§ Templates shows `@register_template("generic")` **with** an `aggregate` (M2); § Validation says
`generic` has none (M3); the code has none (M1); and `CLAUDE.md` § The worked example says
`cohort-pilot` uses `generic` and derives `r` by `aggregate(units)`. **Filed, owner unassigned with
the reason** (§ 5). Repairing it means either adding an `aggregate` to a shipped `generic` — which
falsifies `E-HYPOTHESIS-BOUND`'s shipped premise and its tests — or editing the worked example across
four documents. Neither is `demo`/`docs`/`list-templates`' surface, and this slice's own config depends
on **neither reading**, which is precisely why it can decline.

**Cost if wrong.** The demo's headline metric does not exist and stop 5 prints an empty table.

### Decision 6 — `demo` derives `r` from **recorded columns**, and accepts the correction family that costs

**Question.** `aggregate` can read a recorded column or a declared attribute. Which?

**Answer.** **Recorded columns.** `step03_analyze` records `{"pred": …, "truth": …}` per unit and the
template's `aggregate` reads `units.pred`/`units.truth`.

**Grounds, measured — and this one is a live core asymmetry, not a preference.** M12: with `aggregate`
reading **declared attributes**, the per-condition percentile interval computes fine and the **paired
contrast draw yields `0 of 2000`** — `W-STATS-CONTRAST-RESAMPLE-THIN`, `ci95: null`, `method: null`.
With the identical `aggregate` reading **recorded columns**, the same contrast gets
`paired_percentile_over_units` and a real interval. Two runs differing only in that. The paired delta
**is** README's headline number, so the attribute route produces a transcript with a dash where the
delta belongs. M13 is the second reason: attributes from `index.csv` arrive as **`str`**, so
`spearmanr` over them ranks lexicographically and answers a number that is simply wrong.

**What it costs, stated rather than hidden.** Every numeric recorded column publishes its own metric
and joins the correction family (M14): the demo's family is `{comparisons: 2, metrics: 3}`,
`family_size: 6`, and `pred`/`truth` deltas of exactly `0.0` sit in the record beside `r`. **`demo`'s
stop-5 render prints the `r` row and names the other two rather than hiding them**, because the
feasibility procedure's own trap (*"a template returning twenty diagnostics corrects every interval in
the run for numbers nobody reads"*) is a lesson this walkthrough is well placed to teach in one
sentence.

**Alternatives rejected.** *Attributes, cast to float in `aggregate`* — measured, still `0 of 2000`
(the cast is not the cause). *A non-numeric marker column plus attribute derivation* — gives
`metrics: 1`, the tidiest family, and no paired interval at all.

**Cost if wrong.** The delta column of README's table is `null` and the demo's last statistical claim
is missing.

**Filed:** the asymmetry itself — a derived metric's paired contrast draw failing when the metric
reads declared attributes while its per-condition draw succeeds — § 5.

### Decision 7 — **`demo` prints the stop-5 summary; `run` is not changed and `report` is not invoked**

**Question.** README's stop-5 block shows an execution banner, per-condition progress bars, and a
four-column results table. Who prints them?

**Answer.** **`demo` does**, as its stop-5 *"what that output meant"* commentary, rendered from the
`run.yaml` the real `run` just wrote. **`run` gains nothing.** `report` is not invoked.

**Grounds, measured.** M8: `run`'s entire stdout for a successful run is the warning block and
`run.yaml → <path>`. **There is no banner, there are no progress bars, and there is no results
table** — README's block is fiction for everything except its last line, which is real and correct.
M24: `report`'s `## Conditions` is a 15-column raw table, so it is not the compact thing either, and
invoking it would make the six-stop walk seven commands.

`demo` reading the record it just produced is the honest shape and it is what stops 3 through 5
already are: *"print the next command exactly as you would type it, wait, run it on `Enter`, then say
in two or three lines what its output meant."* A summary of the record **is** saying what it meant.
README's block is edited so `run`'s two real lines are attributable to `run` and the table beneath
them is attributable to `demo`.

**Alternatives rejected.** *Give `run` a results table* — a behaviour change to the most-tested shipped
command, on the last slice of the project, to make a README block true. It is not `demo`'s surface, it
would move every `run` stdout pin in the suite, and the four documents nowhere say `run` prints one.
*Add a seventh stop invoking `report`* — § What `demo` walks you through fixes the count at six.
*Drop the table from README* — the ruling that made the numbers real, spent on deleting them.

**Cost if wrong.** A behaviour change to `run` on the last slice, which is the shape H8b Decision 7
and H7d Part B both split on. **Filed as a disclosure rather than built:** that `run` prints no
progress indication at all for a long plan is a real gap; it is named in § 5 with owner unassigned.

### Decision 8 — `list-templates` prints every **claim**, and prints a parameter spec only where a class exists

**Question.** § Operation commands says *"Registered templates, including plugin-provided, with their
full parameter specs."* Can it?

**Answer.** It prints, in name order, **every claim `_claims(repo_root)` returns** — name, provenance
(`core` | `local` | `installed`), provider — and the full `parameter_spec` for `core` and `local` only.
An `installed` name prints its provider and one line saying its spec is **not readable in this build**,
citing `E-TEMPLATE-INSTALLED-UNSUPPORTED`. **§ Operation commands' row is narrowed to say so.**

**Grounds, measured.** M23: an installed claim is built with `cls=None` and `_merged` drops it, by
construction and with the reason in `_claims`' own docstring — the entry-point scan reads package
**metadata** and imports nothing, which is the invariant *"`validate` resolves a name without importing
the package."* Printing an installed spec means importing the package, which would make
`list-templates` the one command in the build that loads what every other surface refuses to load, and
would resolve a name a config naming it is refused for.

**Outside a repository** it prints `core` and `installed` claims and **one line stating that no
repository was found, so no `templates/**` was searched** — Decision 4's by-type catch. A shorter list
with no explanation is the *silently skipped* fault `spec-defects.md` § *`E-NAME-DIR` is silently
skipped…* already names.

**`E-TEMPLATE-COLLISION` is not caught.** `_claims` raises `PartialLoadError` on a duplicated name, and
`list-templates` lets it reach `main` — the same answer `validate` gives, and the command whose job is
enumerating names is the wrong place to invent a tolerant enumeration.

**Cost if wrong.** A documented row promising something the build cannot do — the `field_convention`
shape — minted by the last slice, with nobody left to close it.

### Decision 9 — `scaffold.README` gains the two missing regions and the four documented lines; **`scaffold.GITIGNORE` does not gain `.demo-progress`**

**Question.** § The generated README specifies a README that `publishable new` does not write (M19).
And `.demo-progress` is documented as *"listed in the generated `.gitignore`"* and is not (M18).

**Answer.** Two different answers, on purpose.

**`scaffold.README` is brought to what § The generated README specifies** — the `credentials` region
with its two-column table, `## Experiments` moved **inside** the `experiments` region with its
`Name | Template | Run` table, the `cp .env.example .env    # then fill in the values below` line, the
`## Reproducing a published result` section, and the **`templates` region** § Templates needs and the
document declares nowhere (a fifth drift, found here rather than carried). **This is a behaviour
change to a shipped creation command** and it is Decision 14's batch.

**`scaffold.GITIGNORE` does not change.** `demo` **appends** `.demo-progress` to the demo repository's
own `.gitignore`, after `scaffold_project` returns and before the first commit. Adding it to the
shipped constant would put a line about a file `demo` invents into every `publishable new` project
forever, for a file those projects never hold. The **documented sentence** is what moves: *"listed in
the generated `.gitignore`"* becomes *"listed in the demo repository's `.gitignore`, which `demo`
appends"* — a one-clause narrowing that is true of the code and preserves the property the sentence
exists for (it is ignored, so it can never dirty the tree and push you onto `draft`).

**Grounds.** The README regions are a *specified* surface of `new` that `new` does not write, which is
a divergence between a shipped command and its own documentation. `.demo-progress` is not: it is a
file of `demo`'s, and § The generated README's scaffold is not the place to declare it.

**Cost if wrong.** Widening `GITIGNORE` is a behaviour change to `publishable new` for a file its
projects never have — the *widening a behaviour change to make a document self-consistent* fault H7d
Part B names by name.

### Decision 10 — `demo` runs each stop **in-process**, and the bytecode-cache fix is decided with it

**Question.** Does `demo` invoke `validate`/`dry-run`/`run` in-process or as subprocesses?

**Answer.** **In-process**, through the same `main([...])` dispatch the console script uses — and the
bytecode-cache filing is fixed in the same slice, at **all three call sites**, by option **(a)**: an
explicit `importlib.machinery.SourceFileLoader`.

**Grounds.** They are one question. A subprocess per stop makes the demo's output depend on how
`publishable` was installed, and the walkthrough's whole claim is *these are the commands you would
type*, which `main` already is. But in-process means one process resolves the demo's project-local
template and its entrypoint **four times** — at `validate`, at `dry-run`, at `run`, and at `demo`'s
own stop-6 read — and M25 shows `discover_local` serving a stale class for a file rewritten inside one
wall-clock second in one process. `demo` writes `templates/correlation.py` and then resolves it
seconds later, in the same process, which is exactly the access pattern the filing describes.

The fix goes at `discover_local._import_file`, `report.render_with_override` and
`base_experiment.load_experiment` — **one root cause, three call sites** — closing both H9-owned
filings, as their own *check its owner must make* requires (*"Whichever option this owner picks for the
entry above should be picked for both … in the same pass"*).

**Option (b) — document the weaker per-process property — is rejected**, and it is the last chance to
reject it: H8b declined it, the filing was re-owned to H9 for that reason, and there is no owner after
this slice. `sys.dont_write_bytecode = True` is rejected too: it is **module-global** and would change
compilation behaviour for every concurrent import in the process, which is a proxy for the question
(*don't cache anything* standing in for *don't serve a stale entry for this file*).

**Cost if wrong.** `demo` renders a stale template's parameters, or a user iterating a `report.py`
override ships a figure one edit stale at exit `0` — the filing's own stated cost.

### Decision 11 — `demo` is a creation command, `--into DIR` is legal, and `reproduce`'s refusal of `--into` still holds

**Question.** `CLAUDE.md` § Invariants enumerates the creation commands as `new`, `plugin new`,
`generate`/`init`, `study new|add` — and omits `demo`, which `reference.md` § Creation commands
tables with `[--into DIR]`.

**Answer.** `demo` is a creation command; `--into DIR` is legal; **`CLAUDE.md`'s enumeration gains
it.**

**Grounds.** `design-principles.md` § Design goals states the rule **categorically** — *"No
**operation** command takes any argument other than a path — creation commands take what is needed to
bring something into existence, and they are the only exception"* — while `CLAUDE.md`'s is an
**enumeration** summarizing it. The enumeration is narrower than the rule it summarizes, and the
narrower one is the summary. Reading it the other way would delete a documented argument from a
documented table.

**Why `reproduce`'s refusal of `--into` still holds, which this ruling owes.** § Reproducing on another
device: *"No `--into`: the destination is derived, so it can't collide with an existing checkout and
doesn't need naming."* **`reproduce` derives its destination from the record**, which names a
repository and a run ID; **`demo` has no record to derive from**, and *"where would you like the demo?"*
has no other answer. The two are not one question with two answers. This sentence goes in the design
and in `CLAUDE.md`'s own § Invariants clause, because H9-SCOPING § C4 asked for it by name.

**Cost if wrong.** Either a documented flag deleted, or a second reading of the operation/creation
line that the next reader has to reconcile.

### Decision 12 — the specified-but-unbuilt machinery **stays**, deliberately unreachable, and its binding test is stopped from going vacuous

**Question.** H9d empties `NOT_BUILT_COMMANDS`. `NOT_BUILT_GENERATORS` is already `{}` (M26).
`_report_not_built` then has **zero reachable call sites**, every `Status` cell in all three tables
reads `built`, and `test_reference_cli_tables_match_what_the_cli_does`' `if status == "NOT BUILT"`
branch becomes **dead** (M27, M29). Does the machinery stay or go?

**Answer.** **It stays** — the dict, the helper, the three `Status` columns and § Creation commands'
paragraph explaining them — and the binding test gains an assertion that **fails if no row is marked**
only in the sense of recording the fact, never of demanding one. Concretely: the test asserts, in a
named companion, that `cli.NOT_BUILT_COMMANDS == {}` **and** that `_report_not_built` still produces
the documented diagnostic when called directly with a name and a real § heading — so the *formatting*
half stays exercised while the *dispatch* half has no input.

**Grounds.** Deleting the helper is a behaviour change: a future command specified before it is built
would have to re-argue the distinction between *specified and unbuilt* and *unknown command*, which
§ Creation commands' paragraph defends at length and which `test_an_unspecified_name_still_reports_an_unknown_command`
still exercises from the other side. Keeping it while saying nothing is worse than either: it is a
shipped writer with no reachable reader, which is the `field_convention` shape this repo has one
example of and is told not to create a second of. **So the state is stated**: § Creation commands'
paragraph gains one sentence saying no row carries the marker today, that the column and the diagnostic
are retained for the next command specified ahead of its build, and that the direction-binding test
covers the built direction for every row and the unbuilt direction for none.

**Cost if wrong.** Either a deleted distinction that has to be re-argued, or a second standing example
of *an unbuilt reader of a shipped surface* minted by the slice with nobody after it.

### Decision 13 — `self.rng`'s documented type is corrected to `random.Random`; the code does not move

**Question.** M4/M5/M6: the code hands a `random.Random`; `reference.md` says `numpy.random.Generator`
twice; a step written against the document **fails its execution**.

**Answer.** **The document changes.** § Using them in step code's fenced comment and § Randomness'
table row say `random.Random`. `BaseStep` is untouched.

**Grounds.** *The code outranks both* — and the direction is forced here rather than chosen: making
`self.rng` a numpy `Generator` would break every step already written against `random.Random`, on the
last slice, with no reader to catch it. **M7 is why this surfaces now**: `grep -rn 'self.rng'
tests/*.py` returns **zero hits**, so nothing in the suite has ever exercised the attribute, and
`demo`'s generated step is the first shipped code in the repository to draw from it. `CLAUDE.md`
§ Invariants' own sentence is type-agnostic (*"`self.rng` is the generator to draw from — core also
seeds the `random` and legacy `numpy.random` globals"*) and needs no edit.

It also **helps** Decision 2: `random.Random` is the Mersenne Twister with a documented,
version-stable stream, which is a better foundation for a reproducible transcript than a numpy
`Generator` whose availability depends on an installed version.

**Cost if wrong.** A generated demo step that raises on its first execution — measured, at exit `3`
(M6) — and a document that keeps teaching it.

### Decision 14 — stop 4's execution count is the **repeat-scoped** count, and the document says which

**Question.** M9: `dry-run` prints **19 executions** where § What `demo` walks you through's stop 4 and
README both say **15**.

**Answer.** Both figures are right about different things and the documents say which. `demo`'s stop-4
commentary reads *"3 conditions × 5 repeats = 15 repeat-scoped executions, and 19 in all — the plan
also runs `step01_load_cohort` once and `step02_fit_model` once per condition."* § What `demo` walks
you through's stop-4 cell and README's line gain the same distinction. **`dry-run`'s own output is not
changed.**

**Grounds.** `3 × 5 = 15` is the arithmetic a reader can do and the sweep is what stop 4 is teaching;
`19` is what the command prints, and a walkthrough whose commentary contradicts the output on the
screen teaches the reader to distrust it. Naming both is one clause. Changing `dry-run` to print 15
would be false and would break every shipped `dry-run` pin.

**Cost if wrong.** The stop whose entire job is *"say what its output meant"* disagrees with the output
in the first number.

### Decision 15 — `W-ENV-UNLOCKED` on the demo's first run is **explained, not suppressed**

**Question.** M17: every `run` in a `publishable new` project prints `W-ENV-UNLOCKED`. The demo repo
is one, so the first `run` a newcomer ever issues prints a warning.

**Answer.** `demo`'s stop-5 commentary names it in one line and says why: the demo project's
`pyproject.toml` depends on `publishable`, which cannot resolve until the package is published, so
there is no lockfile to write. **Nothing is suppressed and no lockfile is fabricated.**

**Grounds.** H9c Decision 5 **affirmed** `W-ENV-UNLOCKED` rather than promoting it, and the
bootstrapping constraint it rests on was re-measured 2026-08-24 (*"Because publishable was not found in
the package registry"*). A `demo` that hid the warning would be teaching a newcomer that warnings are
noise, in the one command whose job is teaching what the output means; and a `demo` that ran `uv lock`
would fail.

**Cost if wrong.** The demo's headline `run` ends with an unexplained yellow line, or `demo` fails at
stop 5 on a machine where `uv lock` cannot resolve — which is every machine, today.

### Decision 16 — `readme_templates/` receives the scaffold constants, and § Package layout gains the two missing rows

**Question.** M21/M22: `readme_templates/` is an empty package whose § Package layout row claims it
holds *"the shipped README/CITATION.cff/LICENSE scaffolds"*, which live as string constants in
`scaffold.py`. § Package layout has no row for `demo` or `list-templates` at all.

**Answer.** The scaffolds move into `src/publishable/readme_templates/` as **files**
(`README.md.tmpl`, `CITATION.cff.tmpl`, `LICENSE.mit.tmpl`, `gitignore.tmpl`), read at scaffold time;
`scaffold.py` keeps the formatting and the refusals. § Package layout gains `demo.py` and
`list_templates.py` rows and `docs.py` loses its `— not yet built` marker.

**Grounds.** The S1 spine plan wrote the schedule down: *"They move into `readme_templates/` as files
when `publishable docs` needs to rewrite managed regions, which is a hardening slice."* **This is that
slice.** And it is not tidying: `docs` must regenerate the same region bodies `new` writes, so the two
either share one source or become two copies of four regions that drift — the second copy being
exactly the defect § The generated README already documents against the first (M19).

`examples/generic/` is **not** created — § Package layout names it and it does not exist (M22). That is
a third missing directory with no reader and no slice; **filed, owner unassigned** (§ 5), because
inventing an examples tree is not `demo`'s surface and `demo` is the thing a reader wanting an example
now has.

**Cost if wrong.** Two copies of four region bodies, one in `scaffold.py` and one in `docs.py`, which
is the maintenance obligation § The generated README exists to prevent.

---

## 3. Where this design disagrees with the scoping and the record

Reported individually, never as a count, per `CLAUDE.md`'s note that six consecutive slices claimed
zero and all six were wrong.

1. **The scoping's § 6.1 item 1 frames the `demo` transcript as *"the transcript is illustrative and
   says so, or `demo` engineers a dataset the bar rejects"* — a false dichotomy.** There is a third
   answer and it is the one Ruling DD takes: `demo` produces its own numbers and README adopts them.
   The scoping missed it because it read `CLAUDE.md` § The worked example's sentence about
   `correlation_pilot` *"reusing the same statistics"* as a constraint rather than as the claim that
   stops being true.
2. **`H9-SCOPING.md` § 7.2 recommends its own third answer — narrow `list-templates` to the installed
   set, never a local template — and Ruling FF rejects it.** Recorded here and echoed inside the task,
   because an implementer reading the scoping will otherwise build the narrower thing.
3. **The scoping never measured whether the demo's headline metric is producible at all.** It does not
   name `GenericTemplate`'s missing `aggregate` (M1), the derived-metric/attribute contrast asymmetry
   (M12), or that `run` prints no results table (M8). Each of the three would have made stop 5
   unbuildable as specified, and none is in § 6.
4. **`reference.md` § Templates and § Validation contradict each other about `generic`'s `aggregate`,
   and the code agrees with one of them** (M1–M3). Not filed anywhere; new here. Owner unassigned
   (§ 5) — see Decision 5 for why this slice can decline it.
5. **`reference.md` documents `self.rng` as a `numpy.random.Generator` at two sites and the code hands
   a `random.Random`** (M4–M6), with **no test anywhere exercising it** (M7). Not filed anywhere; new
   here. Fixed by Decision 13.
6. **`reference.md`'s worked `run.yaml` gives a *derived* `r` a `repeat_spread`, and the code gives a
   derived metric none** (M10). Not filed; new here. Owner unassigned — it is the worked example's
   record shape, not `demo`'s.
7. **§ What `demo` walks you through's stop 4 and README both say 15 executions where `dry-run` prints
   19** (M9). Not filed; new here. Decision 14.
8. **§ Package layout names `examples/generic/`, which does not exist** (M22). Not filed; new here.
9. **`spec-defects.md`'s re-owning of *`diff`'s `uv.lock` row prints two digests and never names the
   package whose pin moved* to H9d reasons from *"the only remaining slice with a CLI rendering
   surface"* — a **schedule argument wearing a surface argument's clothes**.** `demo`, `docs` and
   `list-templates` render, but none of them renders a `diff` row, resolves a dependency graph, or
   reads a lockfile. Declined with the route in § 4.
10. **The scoping's § 6.2 lists four drifts in the scaffolded README beyond the missing region; there
    is a fifth** — the `templates` region, which § Templates needs and § The generated README's own
    fenced example declares nowhere. Decision 9 writes it.
11. **README's v0.x notice goes false the moment this slice lands.** It reads *"not every command
    described here dispatches yet … the rest say so when you invoke them"*, and after task 13 every
    row of all three `Status` tables reads `built` (M26 is the starting state). Not filed; new here.
    Corrected by task 12, which is README's editor.


---

## 4. What this slice refuses to build, each with route and owner

**H3c-3's remaining 14 is the only slice after H9d.** So *unowned* here means *unowned*, and it is said
rather than implied.

| Not H9d's | Where it goes |
|---|---|
| Folds and holdouts **inside cells**; `E-DATA-HOLDOUT-CELLS`/`E-REPL-FOLD-CELLS` retirement | **H3c-3's remaining 14.** `demo`'s config declares no group axis, no `fold` and no `holdout`, so nothing here touches that surface |
| **`diff`'s per-package `uv.lock` detail lines** | **Declined, and re-owned to unassigned with the reason** (§ 5). Re-owned to H9d on 2026-08-24 by H9c task 14 on the ground that H9d is *"the only remaining slice with a CLI rendering surface"*. That is a schedule argument: `diff` is H8b's command, resolving a dependency graph is neither `demo`'s, `docs`' nor `list-templates`', and building it here means one slice adding a rendering feature to another slice's command with no fixture family of its own. **H8b is complete and H3c-3 is folds** |
| A results table, a banner or progress indication in **`run`** | **Unassigned, with the reason** (§ 5). Decision 7 |
| `generic` gaining an `aggregate`, or the worked example's template story | **Unassigned, with the reason** (§ 5). Decision 5 |
| A `repeat_spread` for a derived metric | **Unassigned, with the reason** (§ 5). It is `stats.summarize_step`'s construction; no remaining slice has the `statistics` block as its surface |
| The derived-metric paired-contrast draw failing over declared attributes | **Unassigned, with the reason** (§ 5). Same surface as above; Decision 6 routes *around* it |
| `examples/generic/` | **Unassigned, with the reason** (§ 5) |
| `BaseTemplate.field_convention`'s missing reader | **Unassigned**, unchanged. Re-verified at HEAD: `grep -rn 'field_convention' src/publishable/` → three hits, none a reader. **This slice creates no new one** (Decision 12 is why the `NOT BUILT` machinery is not left as one) |
| `report_by` under `resample` keeping a `t_over_units` interval | **Unassigned**, unchanged |
| `max_failed_fraction`'s truncation status semantics | **Unassigned**, unchanged, and **not weakened**: the demo's 12/240 is 0.05 against a 0.2 default (M15, M16), so nothing here approaches that pin |
| `E-INPUT-CHANGED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS` § Errors rows | **Unassigned**, unchanged — except that Decision 9 edits `scaffold.py`, and task 13 re-checks whether `E-PROJECT-EXISTS`' row is still accurate afterwards rather than assuming it |
| Promoting `W-ENV-UNLOCKED` | **Refused by ruling** (H9c Decision 5). Decision 15 explains it and does not touch it |
| A `dry-run` that lists artifact files | **Refused by ruling** (H9a). `demo` stop 4 says what `dry-run` says |

---

## 5. Filings this slice makes or closes

**Closed:**

- *`discover_local`'s bytecode cache can serve a STALE `templates/*.py`…* — **closed by Decision 10**,
  option (a), re-verified as reproducing at HEAD before the fix (M25).
- *a same-size, same-second rewrite of a report override is silently not picked up* — **closed by the
  same fix at the same pass**, as its own *check its owner must make* requires.

**Declined with a route, and re-owned:**

- *`diff`'s `uv.lock` row prints two digests and never names the package whose pin moved* —
  **re-owned from H9d to `unassigned`, with the reason**, quoted and answered in § 4.

**Made (all `Owner: unassigned, with the reason` — no slice remains that has the surface):**

1. `reference.md` § Templates shows `@register_template("generic")` **with** an `aggregate`; the same
   document's § Validation says `generic` defines none; the shipped class defines none. Three readings,
   one name.
2. `reference.md` documents `self.rng` as a `numpy.random.Generator` at two sites — **struck by
   Decision 13 in the same pass**, so this is filed as *closed on filing*, with the measurement kept
   because M7 (no test anywhere reads the attribute) outlives the wording fix.
3. `reference.md`'s worked `run.yaml` gives a **derived** metric a `repeat_spread` that the code
   computes only for recorded columns.
4. A derived metric whose `aggregate` reads **declared attributes** gets a per-condition percentile
   interval and a paired contrast draw of `0 of 2000`; reading **recorded columns** gets both. Measured
   by two runs differing only in that.
5. `run` prints no execution banner, no progress indication and no results table, for a plan of any
   size.
6. § Package layout names `examples/generic/`, which does not exist.

---

## 6. Is this additive? — the disclosure, measured

**No. There is exactly one behaviour change to a shipped command, and it is Decision 9.**

| Surface | Moves? |
|---|---|
| `publishable new`'s README | **CHANGES.** Two regions added, `## Experiments` moved inside its region, three documented lines added. Every existing byte of the `overview` region is preserved verbatim |
| `publishable new`'s `.gitignore`, `CITATION.cff`, `LICENSE`, `pyproject.toml`, tree | unchanged — Decision 9 refuses the `GITIGNORE` widening; Decision 16 moves *where the bytes are read from*, and task 3's pin asserts the produced files are **byte-identical** |
| `generate experiment` | **CHANGES** — it now merges a row into the `experiments` region and any `required_env` into the `credentials` region. Both halves are documented `NOT BUILT` in § Generators, so this closes a marker rather than moving a behaviour |
| `generate template` | **CHANGES** — writes its parameter table into the `templates` region. Same: a documented `NOT BUILT` half |
| `run`, `draft`, `resume`, `dry-run`, `validate`, `report`, `diff`, `freeze`, `reproduce`, `study` | **unchanged.** No exit code, key, verdict or status moves |
| `discover_local`, `render_with_override`, `load_experiment` | the **loader** changes (Decision 10); the resolved class does not. Pinned by a mutation that a *stale* answer fails and a *fresh* one passes |
| `publishable demo`, `docs`, `list-templates` | `2` → dispatch. **Three exit-code changes**, each from the specified-but-unbuilt diagnostic to real behaviour |

**No exit code is minted, and the only `E-` codes minted are `docs`' five** (Decision 3). `demo`,
`list-templates` and `docs` all reach `1` for a refusal, `0` otherwise; `E-GIT-NO-REPO` gains two
readers rather than a sibling (Decision 4). **The five get § Errors rows, one row per code covering
every emit site, each placed by its table's own scope sentence** — `docs` **raises** them, so which of
the two tables that is gets read rather than assumed. They are task 14's, named there explicitly,
because a code minted in one task and documented in another is how a row comes to undercount its own
emit sites — the shape that has produced a whole-branch Major on five sub-slices.

---

## 7. Does § Executability on this build move? — derived

**No. It unblocks ZERO configs, and the four-row table is repeated character for character with no
fifth number.** Derived per row rather than asserted:

- **Row 1, transplantable configs validating with zero errors — 8 of 8.** None of `demo`, `docs` or
  `list-templates` runs at `validate` or is invoked from a step. Decision 9 changes what
  `publishable new` writes into a **README**, which no `validate` check reads; Decision 16 changes
  where four scaffold constants are stored, which `validate` does not read either. Decision 10 changes
  a **loader**, not a resolution: the class `validate` gets for a given file is the same class, and the
  arm proving that is the mutation in § 10.
- **Row 2, blocked on `io.reuse_from` — 0.** Untouched. Nothing here reads an upstream or walks a
  lineage chain.
- **Row 3, meet the `report_by`-under-`resample` gap — 7.** Untouched and still unowned. It is a
  construction inside `summarize_step`; no command this slice builds enters that phase. Decision 6
  files a *neighbouring* construction defect and builds none.
- **Row 4, free of every core-side dependency this analysis can name — 1.** `demo` scaffolds its own
  project and its own data; it accepts no config of anyone else's. `docs` and `list-templates` read no
  config at all. So none can add a dependency to this row or remove one.

None of the nine configs declares a `study`, a `fold`, a group axis or an `apparatus_probe`, and every
one validates against `generic` — so Decision 5's project-local template is reachable from none of
them either.

The dated entry is one section, *"Measured on 2026-08-24 against commit `<sha>`"*, and the table block
is **extracted programmatically and `diff`-ed to empty** against the H9c entry's copy, by the two
independent methods the H8a, H9a, H9b and H9c entries describe. Its cells still name **H8a**, because
updating them is exactly how a repeated table stops being repeated.

---

## 8. The guard pin

**Captured in batch 1, before anything moves.** Seven arms. Every arm names a sole authorized editor or
**NONE**, and every editor's post-edit state is written here **in advance**.

| Arm | What it pins | Sole authorized editor | Post-edit state |
|---|---|---|---|
| **A** | `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text[DESIGN_PRINCIPLES]` and `[REFERENCE]` — the worked example's own numbers as raw text. **Cite, do not re-capture** | **NONE** | unchanged. A passing arm after task 12 **is** the proof that `cohort-pilot`'s numbers did not move |
| **B** | `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text[README]` — the same scan over README | **task 12** (Ruling DD authorizes it; **see the procedure below — the tuple may not be specified as a literal in advance**) | § 8.1 |
| **C** | A whole-file `sha256` of `docs/design-principles.md` and `docs/experimental-designs.md`, captured at batch 1. **`README.md` and `docs/reference.md` are deliberately NOT in this arm** — § 8.2 | **NONE** | Both files **byte-identical at merge**. If either moves, that is a finding, not a hash to refresh |
| **D** | A `{path → sha256}` map of a `publishable new` project's whole tree **except `README.md`**, before and after Decision 16's move | **NONE** | unchanged. Decision 16 moves *where* the bytes are read from; the bytes produced are identical, and this arm is what says so |
| **E** | `test_diff.py`'s H8c arm D — the three worked `diff` blocks. **Cite, do not re-capture** | **NONE** | unchanged |
| **F** | The current `cli.NOT_BUILT_COMMANDS` key set, as a literal `{"demo", "docs", "list-templates"}`, plus the shipped `assert ("list-templates", "NOT BUILT") in tables["Command"]` H9c task 11 added | **task 13** | `NOT_BUILT_COMMANDS == {}`, and the three marked-row assertions replaced by the companion Decision 12 specifies |
| **G** | `test_validate.py::test_the_worked_examples_intervals_in_reference_md_are_not_narrowed_by_the_null_test_work`. **Cite, do not re-capture** — it reads `reference.md` only and its docstring says it deliberately leaves README's `[0.347, 0.477]` unpinned, so it is **not** a collision | **NONE** | unchanged |

### 8.1 Arm B's post-edit state is **procedural**, and specifying it as a literal would destroy the arm

`_H5A_ARM_D_README_LINES` is a **scan result**, not a hand-written list: the test collects every line of
README containing any of `_H5A_ARM_D_LITERALS` and compares the tuple byte for byte. So a new demo
number like `0.5817` still contains the substring `0.581` and would **keep** its line in the scan with
different bytes. **The post-edit tuple therefore cannot be written down before `demo` runs**, and an
implementer handed a fixed tuple will paste `demo`'s output into it, which converts a pin into a
transcript.

**Task 12's post-edit state, specified procedurally and in advance:**

1. Re-scan README with the **unmodified** `_h5a_arm_d_lines_carrying_the_worked_example` helper and the
   **unmodified** `_H5A_ARM_D_LITERALS` tuple. Neither may be edited.
2. The result must equal the pre-edit tuple **minus exactly these four entries** — the three condition
   rows and the attrition/spread line — **and nothing else**:
   - `  00_baseline           0.581   [0.488, 0.661]    —`
   - `  01_method=spearman    0.607   [0.517, 0.683]    +0.026  [−0.007,  0.059]`
   - `  02_method=kendall     0.412   [0.347, 0.477]    −0.169  [−0.213, −0.125]`
   - `  intervals over 228 of 240 units (12 failed) · seed spread std 0.014`
3. **Every other entry of the pre-edit tuple must survive verbatim**, including
   `run.yaml → ~/publishable-demo-data/results/run_2026-08-07T09-14-03Z_2f5c8d0/run.yaml` (Decision 2
   keeps it) and the six `cohort-pilot` lines below it.
4. **Any surviving line that is not in that eleven-entry remainder is a finding, not a literal to
   refresh** — it means a new demo number happens to contain a worked-example literal, and the design
   owes an answer before the tuple is touched.
5. `_H5A_ARM_D_LITERALS` is **not** extended with the demo's new numbers. Arm B pins the *worked
   example's* numbers; `correlation_pilot`'s are pinned by fixture A instead (§ 9), which asserts them
   against a real `demo` run rather than against a literal list.

### 8.2 Why `README.md` and `reference.md` carry no whole-file hash arm

An earlier cut of arm C hashed all four documents with **task 12** named as editor for `README.md` and
`reference.md`. **That arm could not have stayed green**, and the contradiction is worth recording
rather than quietly dropping: **task 14 is required to edit `reference.md`** — § Operation commands,
§ Creation commands, § What `demo` walks you through, § Randomness, § Package layout, § The generated
README, § Generators, and five new § Errors rows — and **task 12 is required to edit `README.md`**
twice over (the transcript and the v0.x notice, § 3 finding 11). A whole-file hash over a file two
tasks must edit is a pin that reports *an edit happened*, which is not a claim worth making, and an
implementer meeting it red has to guess whether it is a finding.

**What actually needs protecting in those two files is already pinned by content, not by a hash.** Arm
A's `REFERENCE` parametrization holds every `reference.md` line carrying a worked-example literal; arm
B holds README's; arm E holds the three worked `diff` blocks. **Those are the claims**; a whole-file
digest over the same files would be the *same list pinned twice* fault wearing a different unit.

---

## 9. Fixtures as claims

**Fixture A — `demo`'s dataset and its transcript.** `demo` writes 240 rows to
`~/publishable-demo-data/input/index.csv` with columns `unit_id`, `x`, `y`.

- **The recipe, exactly:** `random.Random(<a fixed integer literal in `demo.py`>)`; for
  `i` in `1..240`, `x = rng.gauss(0, 1)`, `y = ρ·x + sqrt(1 − ρ²)·rng.gauss(0, 1)` with ρ a fixed float
  literal, both rounded to six decimals, `unit_id = f"u{i:03d}"`.
- **Determinism across platforms — argued, not assumed.** `random.Random` is the Mersenne Twister with
  a stream the standard library documents as stable across platforms and versions, and
  `Random.gauss`'s algorithm is fixed in `random.py`. The arithmetic is IEEE-754 `+`, `*` and
  `math.sqrt` — the last correctly rounded — over the same operations in the same order, so the written
  file is byte-identical everywhere. **The rounding to six decimals is deliberate**: it makes the CSV
  the artifact of record, so every downstream number is computed from bytes rather than from a float
  repr.
- **SciPy is reachable, and that was checked rather than assumed.** `pearsonr`/`spearmanr`/
  `kendalltau` live in SciPy, and `demo`'s generated template imports them. `publishable`'s own
  `pyproject.toml` declares `scipy>=1.11` as a **runtime** dependency, and a scaffolded project depends
  on `publishable`, so a machine that can run `publishable demo` has SciPy transitively — which is also
  why Decision 10's in-process dispatch matters here: `demo` runs in the interpreter that already holds
  it, rather than in a subprocess against an environment `uv lock` cannot resolve (Decision 15).
- **What is NOT platform-stable, and what task 11 must therefore measure.** Two different quantities,
  and one check does not cover both.
  - **The point estimates** pass through SciPy on a fixed table. **Task 11 reports, for each printed
    value, its distance from the nearest rounding boundary at the printed precision.** A margin below
    `1e-6` is a finding, and the printed precision is reduced until every margin clears it: a value
    sitting on a `.0005` boundary is one libm ulp from printing differently, and a transcript that
    flips on someone else's machine is worse than one never claimed to be real.
  - **The interval bounds are ORDER STATISTICS, not interpolations** — `stats.interval_at` returns
    `pool[lo]`, `pool[hi]` at two fixed integer ranks off a sorted pool, with no interpolation. So the
    boundary-margin check is necessary and **not sufficient**: a bound moves by the *gap between
    adjacent draws* if two draws swap rank, which is orders of magnitude larger than an ulp. The draw
    **composition** is safe — the resampled indices come from a generator seeded off the design digest,
    so the same units are drawn everywhere — and only each draw's *statistic* can differ in its last
    ulps across SciPy versions. **So task 11 additionally reports, for each selected rank, the gap
    between that draw and each of its neighbours in the sorted pool.** A gap below `1e-12` means a rank
    swap is reachable and the interval may not be quoted at that precision. If any bound fails, README
    quotes the point estimates and the delta exactly and **describes** the intervals rather than
    quoting them — which is a smaller claim, honestly made.
- **The 12 failures are a claim too.** `step03_analyze` skips twelve named keys, so those units are
  handed to a recording execution and neither recorded nor skipped-by-`io.skip` — which is what
  `runner._units_failed_anywhere` counts as `failed` (M15). The expected attrition is
  `{resolved: 240, completed: 228, ineligible: 0, failed: 12}`, and `12/240 = 0.05` against a
  materialized `max_failed_fraction` of `0.2` (M16), so the run reaches `completed` at exit `0`.
- **The `seed` spread is a claim too, and it is over a recorded column.** A **derived** metric carries
  no `repeat_spread` (M10), so the transcript's spread line reports a **recorded** column's, or is
  dropped. Task 11 decides by reading its own run and says which; it may not report a derived metric's.
  `step03_analyze` sets `nondeterministic = True` and draws from `self.rng` — a `random.Random`
  (Decision 13) — so the spread is non-zero and `validate`'s no-nondeterminism warning does not fire.

**Fixture B — a README with each malformed region, one per file.** Five files, one condition each
(Decision 3's table), each a **minimal** README carrying one well-formed region beside the broken one,
so a refusal cannot pass by the file having nothing in it. Each file's expected code is the literal in
Decision 3.

**Fixture C — the hand-written-prose survival file.** A README with all four regions, arbitrary prose
above, between and below each, including a line that itself contains the substring
`publishable:begin` **inside a fenced code block**. The claim: after `docs`, every byte outside the
four region bodies is identical, **including the fenced decoy**. That decoy is the fixture's whole
point — the documents contain markdown inside markdown, and a parser that scans lines without
excluding fences will rewrite an example.

**Fixture D — a project-local template beside an installed claim and core's `generic`.** For
`list-templates`: two local templates named `aaa_probe` and `zzz_probe`, **one on each side of
`generic` in sort order**, plus a fake installed entry point. Two on each side because *a decoy whose
sort position agrees with the bug* has been hit twice in this repo, and because **two elements only
ever distinguish two orderings** — with core, installed and local all present and locals on both
sides, name order, provenance order and discovery order each give a different answer.

**Fixture E — the stale-bytecode pair.** The filing's own recipe (M25): write `templates/s.py`
declaring `apparatus_probe = "f_probe"`, resolve, overwrite the **same path** with `"g_probe"` **at
the same byte length**, resolve again. Same length is required — a length change is picked up even
unfixed, so a differently-sized second file tests nothing. The claim: `g_probe`.

---

## 10. Mutations

Each names the assertion that catches it and the two branches that can differ. Blind ones are named
here, in advance, and each is owed a replacement.

| # | Mutation | Caught by | The two branches |
|---:|---|---|---|
| 1 | In the region rewriter, replace the `end`-marker search with *rest of file* | fixture C | prose below the region survives / is consumed |
| 2 | Drop the fenced-block exclusion from the region scanner | fixture C's fenced decoy | the decoy line is untouched / is rewritten |
| 3 | Turn `E-DOCS-REGION-UNBALANCED` into a `return EXIT_OK` | fixture B, arm 1 — asserting the **code and the stderr line**, never only the exit code | a refusal is printed / nothing is printed and the file is unchanged, which is Ruling EE's whole subject |
| 4 | Make a README missing one region a refusal | the "rewrites what it finds, names what it did not" test | exit `0` with a named absence / exit `1` |
| 5 | Replace the explicit `SourceFileLoader` with `spec_from_file_location`'s default | fixture E | `g_probe` / `f_probe` |
| 6 | Apply mutation 5 at only **one** of the three call sites | three separate fixtures, one per site | the untouched site still serves stale — *a sweep that stops one file short* is the fault this arm exists for |
| 7 | Make `list-templates` import an installed template to read its spec | the installed-claim assertion — that its spec line reads *not readable in this build* and that **no module was imported**, checked by a sentinel module that records its own import | metadata-only / imported |
| 8 | Reverse `list-templates`' sort | fixture D | `aaa_`/`zzz_` on both sides of `generic` make name order, provenance order and insertion order three different answers |
| 9 | Make `list-templates` **raise** rather than continue when no repository is found | the outside-a-repo test, asserting **both** the core/installed rows **and** the explanatory line | lists with a note / exits `1` |
| 10 | Delete `demo`'s `.gitignore` append | the demo-repo test asserting `.demo-progress` is git-ignored **and** that `publishable new`'s own `.gitignore` does **not** contain it | Decision 9's two halves, which one assertion cannot separate |
| 11 | Make `demo`'s data generator seed from the clock | fixture A's byte-identical CSV across two invocations in one test | identical / different |
| 12 | Make `demo` pause when stdin is not a tty | the headless test, asserting the full sequence completes **and** that nothing was read from stdin | straight through / blocks |
| 13 | Make a `demo` prompt accept a value that reaches the config | the *no pause may alter the config* test, comparing `parameters_hash` after a `q`-then-resume against a straight-through run | equal / not equal |
| 14 | Make `demo` stop 6 **run** `reproduce` rather than print it | the stop-6 test asserting the invocation appears on stdout and that **no directory was created**, by whole-tree snapshot | printed / executed |
| 15 | Make `--into DIR` start over in a directory holding a `.demo-progress` | the resume test asserting the second invocation reports the stop it left | resumes / restarts |
| 16 | Delete the widened subject from `E-GIT-NO-REPO`'s row | task 13's row-versus-code sweep, which enumerates call sites **by reading** and compares against the row's own claim | row and code agree / disagree |

**Blind in advance, each owed a replacement:**

- **A mutation to `_report_not_built` is blind after task 13**, because Decision 12 leaves it with no
  reachable dispatch. *Replacement*: Decision 12's companion calls the helper **directly** with a name
  and a real § heading and asserts the exact diagnostic, so the formatting half stays killable while
  the dispatch half has no input. The companion also asserts `NOT_BUILT_COMMANDS == {}`, so the two
  claims cannot drift apart.
- **A mutation to Decision 16's file move is blind on behaviour** — reading four constants from files
  instead of from module globals produces identical bytes by design. *Replacement*: guard-pin arm D,
  a whole-tree hash map of a scaffolded project excluding `README.md`, which fails if any byte of any
  other scaffolded file moves. The *absence* of a behaviour difference is the claim, so the arm asserts
  it rather than a mutation disproving it.
- **A mutation asserting `demo`'s exact statistics is not a mutation of `demo`** — it is a mutation of
  the data recipe, and mutation 11 covers the recipe. There is deliberately **no** mutation that
  perturbs a printed value and checks README, because such a test would pass by editing README, which
  is the thing under test.

---

## 11. Batching

**Fourteen tasks in six batches. Every batch is reviewed.**

| Batch | Tasks | Why together |
|---:|---|---|
| 1 | 1 | The guard pin, alone, before anything moves. **No later task may capture a pin** |
| 2 | 2, 9 | The region parser and the bytecode fix — independent of each other and of everything after |
| 3 | 3 | **The behaviour change**, alone: `scaffold.README` and the `readme_templates/` move. Reviewed on its own so the one shipped-command change in this slice has a review of its own |
| 4 | 4, 5, 6, 7, 8 | The three region bodies, `docs`' wiring, `list-templates`. All read the parser batch 2 built |
| 5 | 10, 11, 12 | `demo` stops 1–2, stops 3–6, and the transcript. Task 12 is arm B's sole editor and runs last in the batch |
| 6 | 13, 14 | The `NOT BUILT` retirement and the documents. **Neither is skippable**: *a batch with no review is where the findings will be*, and a documents-and-codes task is the one whose output no later batch reads |

**Batch 3 is the behaviour change.** It is the only batch that moves a shipped command's output, and
guard-pin arm D is what bounds it: every scaffolded file except `README.md` must be byte-identical
across it.

---

## Controller ruling GG, 2026-08-24 — `self.rng` becomes a `numpy.random.Generator`; the CODE follows the documents here

**Corrections 3, 4 and 5 found a divergence the slice cannot walk past**: `reference.md` states in a table
row *and* in prose that `self.rng` is a **`numpy.random.Generator`**, while `base_step.py` builds a
**`random.Random`** — and a step calling `self.rng.normal(...)`, which the documents invite, **fails its
execution at exit 3, measured.**

**The code changes, not the document.** `CLAUDE.md` § Repository status sets the default — *"Where it
cannot follow them, the document changes first"* — so the question is whether the code **can** follow, and
here it can:

- **The documents are coherent and the code is the odd one out.** § Randomness's whole surrounding
  argument is written for a modern Generator: the legacy global `RandomState`, `numpy.random.default_rng`,
  the concurrency note, and `derive_seed`'s role beside it. Changing the sentence would mean rewriting the
  section's argument, not fixing a word.
- **Nothing pins the current type.** **Zero tests in `tests/` mention `self.rng`** (correction 5) — so this
  surface has shipped without ever being exercised, which is the *unbuilt reader of a shipped surface*
  defect wearing its other face.
- **numpy is already a hard runtime dependency**, so nothing is added to the install.
- **A research tool whose per-execution stream cannot draw a normal is a defect in the tool**, and the
  person who meets it is a new user following the documented example on their first step.

**Cost if wrong, and it is real:** a project already written against `random.Random` methods that
`Generator` does not carry — `randint`, `gauss`, `choice`'s different signature — breaks at the call.
`shuffle`, `random` and `uniform` survive. The exposure is bounded by this being v0.x and greenfield-only,
with every project created by `init` — **but this is a behaviour change to a shipped surface and it gets a
disclosure section of its own**, on H5b's, H6a's, H9a's and H9b's precedent. **`demo`'s own generated step
must draw from `self.rng`**, so the walkthrough exercises the thing the walkthrough documents, and the
gap that made this possible — a surface with no test at all — closes with it.
