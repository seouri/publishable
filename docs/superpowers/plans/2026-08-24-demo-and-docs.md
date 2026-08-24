# H9d — `demo`, `docs`, `list-templates` — the plan

**Fourteen tasks in six batches, every batch reviewed.** The design is
[`docs/superpowers/specs/2026-08-24-demo-and-docs-design.md`](../specs/2026-08-24-demo-and-docs-design.md);
its § numbers are cited, never its line numbers. Four controller rulings bind this slice — **CC**,
**DD**, **EE**, **FF** — and **each is restated inside every task section it binds**, because the
ledger reaches the controller and the reviewers and reaches **no implementer**. A ruling you find only
in the design is a ruling somebody will re-derive.

**H9d is the last slice of the command surface.** After it, only H3c-3's remaining 14 — folds and
holdouts inside cells — remain in the whole project. Anything you decline that H3c-3 does not own is
**unowned**, so decline in writing, with the reason, and never as *"whichever slice next touches X."*

**Read before your task:** the design's § 0 (what was measured, by running), § Corrections against the
code below **in full**, and the § 8 guard-pin row for any arm your task is allowed to touch. **If your
task is not named as an arm's sole authorized editor, you may not edit that arm — leave the branch red
and say so.**

**§ Corrections against the code lives outside the task sections and `task-brief` does not carry it.**
Every task section below therefore names, at its top, which corrections bind it. Read those, and read
the list whole anyway.

**Every task:**
- runs `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy` before reporting;
- reports **full-suite** mutation counts and says they are full-suite;
- greps every claim it makes about other code or other tests, **newline-insensitively**, and reports
  **what it grepped and what each hit was**, attributing every hit — never a count. **Do not report
  zero disagreements**: six consecutive slices did and all six were wrong, and every one hid in a claim
  about *other* tests or *other* rows that a brief supplied as established fact. **A count without a
  noun is not a claim anyone can check.**
- runs any creation command **outside this repository**, in the scratchpad — H6a made the dirty gate
  load-bearing.

---

## § Corrections against the code

**Thirty-three, each measured at `8413c16`, each with the method named. A brief-supplied figure that
disagrees with one of these is wrong; grep before you trust either.**

1. **`GenericTemplate` declares no `aggregate`.** Read all 26 lines of
   `src/publishable/templates/builtin/generic.py`. It inherits `BaseTemplate.aggregate`'s `{}`. A demo
   config naming `generic` derives nothing.
2. **`reference.md` § Templates' fenced class is `@register_template("generic")` and shows an
   `aggregate`** computing pearson/spearman/kendall. That contradicts correction 1 and contradicts the
   same document's § Validation row *"template `generic` defines no `aggregate`"*. Three readings, one
   name. **Filed, not repaired** — design § 5.
3. **`self.rng` is a `random.Random`,** not a `numpy.random.Generator`:
   `src/publishable/base_step.py` assigns `random.Random(seed)`. `reference.md` says
   `numpy.random.Generator` at **two** sites (§ Using them in step code's fenced comment, § Randomness'
   table row).
4. **A step calling `self.rng.normal(...)` fails its execution.** Measured by running:
   `AttributeError: 'Random' object has no attribute 'normal'`, 15 executions failed, `run` exit `3`.
5. **No test in `tests/` mentions `self.rng`.** `grep -rn 'self.rng' tests/*.py` → **zero hits**. The
   attribute has never been exercised by the suite.
6. **`run` prints no results table, no progress bars and no execution banner.** Its entire stdout for a
   successful 19-execution run is the warning block and one line `run.yaml → <path>`. Captured to a
   file and read whole, not tailed. **README's stop-5 block is fiction except its last line.**
7. **`dry-run` prints 19 executions** for a 3-condition × 5-repeat plan whose pipeline has a
   `run`-scoped and a `condition`-scoped step (1 + 3 + 15). § What `demo` walks you through's stop 4
   and README both say **15**.
8. **A derived metric carries no `repeat_spread`.** Read from a real `run.yaml`: `r` has no such key
   while the recorded `pred`/`truth` columns carry `{std: …, n: 5, kind: seed}`. `reference.md`'s
   worked `run.yaml` shows a **derived** `r` with one.
9. **A derived metric gets `percentile_over_units` and `resample_draws: 2000` with no
   `statistics.resample` declared anywhere.** So the demo needs no `resample` block, and stop 2's
   *"this config's `sweep` and `replication` blocks"* stays true.
10. **A derived metric whose `aggregate` reads declared attributes gets `0 of 2000` on its paired
    contrast draw** — `W-STATS-CONTRAST-RESAMPLE-THIN`, `ci95: null`, `method: null` — while the same
    metric reading **recorded columns** gets `paired_percentile_over_units` and a real interval.
    Measured by two runs differing only in that. **Casting the attribute to `float` does not help** —
    also measured.
11. **Declared attributes from `index.csv` arrive as `str`.** `spearmanr` over them ranks
    lexicographically: `0.4212` against the float column's `0.6781`.
12. **Every numeric recorded column publishes its own metric and joins the correction family.**
    `family_size: 6`, `{comparisons: 2, metrics: 3}` for one derived metric beside two recorded
    columns. A **non-numeric** recorded column publishes none: `{comparisons: 2, metrics: 1}`.
13. **A unit becomes `failed` by being handed to a recording execution and neither recorded nor
    skipped** — `runner._units_failed_anywhere`. Produced `{resolved: 240, completed: 228,
    ineligible: 0, failed: 12}` from a step that skips twelve keys.
14. **`limits.max_failed_fraction` materializes at `0.2`** (`materialize.py`), so 12/240 = 0.05 passes.
15. **`W-ENV-UNLOCKED` fires on every `run` in a `publishable new` project.** Measured. The demo's own
    first run prints it, and `uv lock` still cannot resolve `publishable` (re-measured 2026-08-24 by
    H9c).
16. **`scaffold.GITIGNORE` holds `.env`, `__pycache__/`, `*.py[cod]`, `.venv/` and no
    `.demo-progress`.**
17. **`scaffold.README` writes two regions**, `overview` and `experiments`, with `## Experiments`
    **outside** its region and prose inside it, and **no `cp .env.example .env` line**. Read the
    constant, then read a scaffolded README back.
18. **There is no region parser or rewriter anywhere in `src/`.** The marker strings appear at exactly
    four lines, all in `scaffold.py`.
19. **`src/publishable/readme_templates/` is an empty package**: `__init__.py`, **0 bytes**, nothing
    else. § Package layout says it holds *"the shipped README/CITATION.cff/LICENSE scaffolds"*. The S1
    spine plan scheduled the move for *"when `publishable docs` needs to rewrite managed regions."*
20. **§ Package layout gives `docs.py` a `— not yet built` row and gives `demo` and `list-templates`
    no row at all.** It also names `examples/generic/`, and `ls examples/` says no such directory.
21. **An installed template's `Claim.cls` is `None` by construction.** `_claims` builds an entry-point
    claim with `cls=None`, `_merged` drops it, `get_template` returns `None`. So **`list-templates`
    cannot print an installed plugin's parameter spec without importing the package.**
22. **`_claims` raises `PartialLoadError`/`E-TEMPLATE-COLLISION` on a duplicated name** and is
    imported by `validate.py` and `generators/experiment.py` despite its underscore. Its docstring's
    *"the two cross-module imports are the whole set"* is **already filed as wrong (there are three)**
    — do not repeat the claim.
23. **`report`'s markdown `## Conditions` is a 15-column raw table**, one row per condition × metric,
    with `n` and `by_*` as nested mappings. It is not README's compact four-column table.
24. **The bytecode-cache defect reproduces at HEAD.** Ran the filing's own recipe: `discover_local`
    served `f_probe` twice, from two different files at one path, in one process, no exception, no
    diagnostic.
25. **`NOT_BUILT_COMMANDS` holds exactly three keys** — `demo`, `docs`, `list-templates` — and
    **`NOT_BUILT_GENERATORS` is `{}`**.
26. **`_dispatch`'s `any(n.startswith(f"{command} "))` group fallback already matches nothing**: no
    two-token key remains. Emptying the dict makes `_report_not_built` **unreachable from dispatch**,
    and `test_reference_cli_tables_match_what_the_cli_does`' `if status == "NOT BUILT"` branch **dead**.
27. **`E-GIT-NO-REPO`'s § Errors row says "Eight paths reach it"** and enumerates two uncaught, three
    caught **by code**, three caught **by type**. `grep -rn 'find_repo_root' src/publishable/*.py`
    returns the call sites; `cli.py`'s `find_repo_root(Path.cwd())` is the creation-command one.
28. **`tests/test_cli.py`'s `_H5A_ARM_D_README_LINES`' first five entries are README's demo-transcript
    lines**, and `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text` is H6b guard-pin **arm R,
    sole authorized editor NONE**. Its golden is a **scan result**, not a literal list.
29. **Two neighbouring pins are NOT collisions**, attributed so nobody stops at them.
    `tests/test_validate.py::test_the_worked_examples_intervals_in_reference_md_are_not_narrowed_by_the_null_test_work`
    reads `reference.md` **only**, and its docstring says it deliberately leaves README's
    `[0.347, 0.477]` unpinned. `tests/test_diff.py`'s H8c arm D pins README's `diff` block, which is
    **hashes only** and carries no demo statistic.
30. **`main`'s `except PublishableError` handler uses no `Collector`**, so anything raised into it is
    printed **without the redaction pass** (H9b correction C3). Every refusal `docs` and
    `list-templates` decide is printed through their own `Collector`, never raised into `main`.
31. **SciPy is reachable from a scaffolded project, checked rather than assumed.**
    `publishable`'s own `pyproject.toml` declares `scipy>=1.11` as a **runtime** dependency, and a
    scaffolded project depends on `publishable` — so `demo`'s generated template may import
    `pearsonr`/`spearmanr`/`kendalltau`. Decision 10's in-process dispatch is part of why: `demo` runs
    in the interpreter that already holds it, not against an environment `uv lock` cannot resolve
    (correction 15).
32. **A percentile interval's bounds are ORDER STATISTICS, not interpolations.**
    `stats.interval_at` returns `pool[lo]`, `pool[hi]` at two fixed integer ranks off a sorted pool
    (`_percentile_ranks`), with no interpolation and an `assert` that the pool is sorted. So a
    rounding-boundary margin check is **necessary and not sufficient** for an interval bound: a bound
    moves by the *gap between adjacent draws* if two draws swap rank.
33. **README's v0.x notice goes false the moment this slice lands** — *"not every command described
    here dispatches yet … the rest say so when you invoke them"*, with every `Status` cell reading
    `built` after task 13.

---

## Task 1

**Binding corrections: 25, 26, 27, 28, 29.**

**The guard pin, captured before anything else moves.** Build the seven arms of the design's § 8 exactly
as that table specifies, and prove **every** arm able to fail by a mutation in **production** code or in
a document. **You are the only task in batch 1, and no later task may capture a pin.**

- **Arm A** — *cite, do not re-capture.* `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text`'s
  `DESIGN_PRINCIPLES` and `REFERENCE` parametrizations already hold `cohort-pilot`'s numbers as raw
  text. **Re-capturing recreates H8a's *same list pinned twice*.** Editor **NONE**. Name the test by
  function in your report.
- **Arm B** — the `[README]` parametrization of the same test. **Do not edit it.** Record that its sole
  authorized editor is **task 12** and that its post-edit state is the **procedure** in design § 8.1 —
  **not a literal tuple**. Copy that procedure verbatim into your report.
- **Arm C** — **build this.** A whole-file `sha256` of `docs/design-principles.md` and
  `docs/experimental-designs.md`, asserted as two literals. Editor **NONE** — both must be
  byte-identical at merge, and a red arm is a finding rather than a hash to refresh. **`README.md` and
  `docs/reference.md` are deliberately NOT in this arm**, and design § 8.2 says why: task 12 must edit
  README twice and task 14 must edit `reference.md` in eight sections, so a whole-file digest over
  either would report only *an edit happened*. What needs protecting in those two is pinned by
  **content** — arms A, B and E — not by a digest.
- **Arm D** — **build this.** A `{relative path → sha256}` map of a `publishable new` project's whole
  tree **except `README.md`**, built by running `scaffold_project` into `tmp_path`. Editor **NONE**.
  Its job is Decision 16: after the constants move into `readme_templates/`, every other scaffolded
  byte must be identical.
- **Arm E** — *cite, do not re-capture.* `tests/test_diff.py`'s H8c arm D. Editor **NONE**.
- **Arm F** — **build this.** `assert set(NOT_BUILT_COMMANDS) == {"demo", "docs", "list-templates"}`,
  plus a citation (not a copy) of the shipped `("list-templates", "NOT BUILT")` row assertion. Sole
  authorized editor **task 13**; post-edit state is design § 8's row F.
- **Arm G** — *cite, do not re-capture*, per correction 29. Editor **NONE**.

**Mutations required, each full-suite:** change one digit of a `cohort-pilot` interval in
`docs/reference.md` (arm A) and in `README.md` (arm B); append a blank line to
`docs/design-principles.md` and to `docs/experimental-designs.md` (arm C, both halves); change one byte of `scaffold.CITATION` (arm D); add a
fourth key to `NOT_BUILT_COMMANDS` (arm F).

**Must not touch:** `src/` except to mutate and revert; any existing test assertion; the four documents
except to mutate and revert. **Never `git checkout -- <file>` to revert** — keep a copy and verify the
revert by **behaviour**, not by `git status`.

---

## Task 2

**Binding corrections: 17, 18, 30.**

**The managed-region machinery.** Create `src/publishable/docs.py` with the parser and the rewriter,
and nothing that dispatches. No command wiring in this task.

> **RULING EE (binding, restated here):** `docs` rewrites **only what a region encloses**, and a region
> it cannot find is a **named refusal, never a silence** — *a command that silently rewrites nothing
> looks identical to one that worked.* **Cost if wrong: a user's hand-written prose outside a region is
> destroyed, which is unrecoverable and is why the markers exist at all.**

Build:
- `regions(text) -> dict[str, tuple[int, int]]` — region name to the half-open **line** span strictly
  between its `begin` and `end` markers. **Lines inside a fenced code block are not scanned**: the
  documents contain markdown inside markdown, and a marker there is content.
- `rewrite(text, name, body) -> str` — replaces exactly that span, leaving every other byte, including
  both marker lines and the trailing newline convention, untouched.
- The five refusals of design § 3's table, each raised as a `ContractError` with its code.

**The four managed region names are `overview`, `credentials`, `experiments`, `templates`** — the first
three from § The generated README, the fourth from § Templates.

**Fixtures:** design § 9's fixture B (five malformed READMEs, one condition each, **each carrying one
well-formed region beside the broken one** so a refusal cannot pass by the file being empty) and
fixture C (all four regions, prose above/between/below, **and a line containing a marker spelling
inside a fenced block**).

**Mutations:** design § 10 rows 1, 2, 3, 4. Row 3's assertion must check **the code and the stderr
line**, never only the exit code.

**Must not touch:** `cli.py`, `scaffold.py`, any generator, any document.

---

## Task 3

**Binding corrections: 16, 17, 19, 20. This is the slice's only behaviour change to a shipped command,
and it is its own batch.**

Two moves, in this order.

**(a) `readme_templates/` receives the scaffolds.** Move `README`, `CITATION`, `MIT` and `GITIGNORE`
out of `scaffold.py`'s module globals into files under `src/publishable/readme_templates/`, read at
scaffold time. `scaffold.py` keeps the `.format(name=…)` calls and every refusal. Add the package data
declaration `pyproject.toml` needs, and **verify by installing into a fresh venv that the files ship**
— a template that is not packaged is a scaffold that raises on someone else's machine.

**(b) `scaffold.README` becomes what § The generated README specifies:** the `credentials` region with
its two-column table, `## Experiments` moved **inside** the `experiments` region with its
`Name | Template | Run` table, the `cp .env.example .env    # then fill in the values below` line, the
`## Reproducing a published result` section, and a **`templates` region** (correction 17's fifth drift
— the document declares one nowhere and § Templates needs one).

**`scaffold.GITIGNORE` does not change.** Decision 9: `.demo-progress` is appended by `demo` to the
demo repository's own `.gitignore`, not added to every `publishable new` project. **The documented
sentence is what moves**, and task 14 moves it. Adding it here is the *widening a behaviour change to
make a document self-consistent* fault.

**Guard-pin arm D is yours to keep passing, not to edit.** Its editor is **NONE**. It hashes every
scaffolded file **except `README.md`**, so move (a) must produce byte-identical output for all four
others; if arm D goes red, move (a) is wrong, not the arm.

**Mutation:** change one byte of the `credentials` region body and confirm a test fails that names the
region rather than the whole file.

**Must not touch:** `docs.py`, `cli.py`, the four documents, guard-pin arms.

---

## Task 4

**Binding corrections: 17, 21, 22.**

**The `credentials` region body, and `generate experiment`'s `required_env` merge** — the § Generators
half filed `NOT BUILT`. The body is the two-column `Variable | Needed by` table, one row per variable
any experiment's resolved template declares in `required_env`, sorted by variable name, with the
experiments needing it in the second cell. The empty state is the documented
`_(none yet — added as experiments declare them)_` row.

**Correction 21 binds this:** an **installed** template's class is `None`, so its `required_env` is
unreadable. A row is emitted only for a template whose class this build holds; an experiment whose
template is installed contributes a row saying so, **not silence**.

**Fixture:** two experiments, one declaring two variables and one declaring one of the same two, so the
merge has something to merge — a single experiment tests the write and not the merge.

**Must not touch:** `demo`, `list-templates`, `docs`' dispatch.

---

## Task 5

**Binding corrections: 17, 18.**

**The `experiments` region body as a table, and `generate experiment`'s row merge** — the other
§ Generators `NOT BUILT` half. `Name | Template | Run`, one row per `configs/*/config.yaml`, sorted by
name, `Run` holding the `uv run publishable run configs/<name>/config.yaml` invocation. Empty state is
the documented `_(none yet — add one with `publishable generate experiment`)_` row.

**`## Experiments` is inside the region** as of task 3, so this body carries the heading. Read the
region span from `docs.py`; do not re-implement a scan.

**Mutation:** add a second experiment and confirm the region gains exactly one row and that **every
byte outside it is unchanged**, asserted as a whole-file comparison rather than as a substring.

---

## Task 6

**Binding corrections: 18, 21, 22.**

**The `templates` region body, and `generate template`'s write into it.** One sub-section per template
this build can hand back a class for, with its full `parameter_spec` as a table: parameter, type,
default (or **required** when `default` is omitted), constraints, `help`. **`parameter_spec` is the
single source of truth** — do not read a second one, and do not invent a defaults file.

**An installed template gets a named line, not a table** (correction 21), and it says its spec is not
readable in this build, citing `E-TEMPLATE-INSTALLED-UNSUPPORTED`.

**Fixture:** a local template declaring one required parameter (no `default`), one `nullable=True`
`default=None`, one with `choices` and `requires_env`, and one `list` with `item_type` — the four
shapes whose rendering differs.

---

## Task 7

**Binding corrections: 27, 30.**

**`docs`' dispatch.** Wire `publishable docs`, taking **no arguments**, walking up from `Path.cwd()`.

> **RULING FF (binding, restated here):** `docs` and `list-templates` **take no path**, and that is the
> **documented exception already stated at `E-GIT-NO-REPO`'s § Errors row** — *"the creation commands
> walk up from `Path.cwd()` … the one place `CLAUDE.md` § Invariants' … does not apply."* **Reuse it;
> do not mint a second one.** Cost if wrong: a second explanation of one rule, which is how a rule
> acquires two sources of truth.

`docs` catches `E-GIT-NO-REPO` **by code** and re-reports it through its own credential-bearing
`Collector` at exit `1` — never raises it into `main`, which applies **no redaction** (correction 30).

**Behaviour:** rewrite every region of the four that the README holds; **name on stdout every one it did
not find**, at exit `0`. A README holding **none** of the four is `E-DOCS-NO-REGIONS` at exit `1`; no
README at the root is `E-DOCS-NO-README` at exit `1`.

**Mutations:** design § 10 row 4, plus turning the "names what it did not find" line into a `pass` and
confirming a test fails on the **stdout content**, not on the exit code.

**Must not touch:** `NOT_BUILT_COMMANDS` — that is task 13's, and removing a key early breaks
guard-pin arm F, whose editor you are not.

---

## Task 8

**Binding corrections: 21, 22, 27, 30.**

**`list-templates`.** Takes no arguments; walks up from `Path.cwd()`; **catches `E-GIT-NO-REPO` by
type**, leaving `repo_root=None`, and **prints one line saying no repository was found so no
`templates/**` was searched.** A shorter list with no explanation is the *silently skipped* fault.

> **RULING FF (binding, restated here)** — see task 7 for the sentence. **And it rejects
> `H9-SCOPING.md` § 7.2's own preferred answer**, which is to narrow `list-templates` to the installed
> set and never a local template. **Do not build the narrower thing.** A project-local template is the
> case § Templates says path discovery exists for, and it is the case task 6's region needs.

**Output:** every claim `_claims(repo_root)` returns, in name order — name, provenance
(`core` | `local` | `installed`), provider — with the full `parameter_spec` for `core` and `local`.
**An `installed` name prints its provider and one line saying its spec is not readable in this build**
(correction 21), citing `E-TEMPLATE-INSTALLED-UNSUPPORTED`. **Do not import a plugin to read a spec**:
that would make this the one command in the build that loads what every other surface refuses to load.

`E-TEMPLATE-COLLISION` is **not** caught — it reaches `main`, the same answer `validate` gives.

**Fixture D (design § 9):** two local templates, `aaa_probe` and `zzz_probe`, **one on each side of
`generic` in sort order**, plus a fake installed entry point. Two on each side because *a decoy whose
sort position agrees with the bug* has been hit twice here, and because **two elements only ever
distinguish two orderings**.

**Mutations:** design § 10 rows 7, 8, 9. Row 7's assertion needs a **sentinel module that records its
own import**, not an absence of output.

**Also yours:** § Operation commands' `list-templates` row is narrowed to what this builds. Write the
replacement wording in your report; **task 14 makes the edit**, so the four documents move in one task.

---

## Task 9

**Binding corrections: 24.**

**The bytecode-cache fix, at all three call sites, closing two filings.**

Replace the implicit loader with an explicit `importlib.machinery.SourceFileLoader` at
`templates/discovery.py::_import_file`, `report.py::render_with_override` and
`base_experiment.py::load_experiment`. **One root cause, three call sites** — the filing's own *check
its owner must make* requires the same option at all three in one pass.

**Option (b), documenting the weaker per-process property, is rejected by design Decision 10, and this
is the last chance to reject it:** H8b declined it, the filing was re-owned to H9 for that reason, and
there is no owner after this slice. **`sys.dont_write_bytecode = True` is also rejected**: it is
module-global and changes compilation for every concurrent import in the process, which is a proxy for
the question.

**Fixture E (design § 9):** the filing's own recipe, **at the same byte length** — a differently-sized
second file is picked up even unfixed, so it tests nothing.

**Mutations:** design § 10 rows 5 and 6. **Row 6 is the one that matters**: revert the fix at exactly
one of the three sites and confirm a distinct test fails for that site. *A sweep that stops one file
short* has happened three times in one slice here.

**Do not** rewrite the two `spec-defects.md` entries — task 14 strikes them, with the entries' own
claims re-read against the code you changed.

---

## Task 10

**Binding corrections: 1, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16.**

**`demo` stops 1–2.** Create `src/publishable/demo.py`. Stop 1 writes the data **outside** the created
repo, scaffolds the project, and commits. Stop 2 prints the config's `sweep` and `replication` blocks
verbatim.

> **RULING DD (binding, restated here):** `demo` **produces its own numbers**. It generates a real
> dataset, runs the real arc, and README's demo numbers become whatever `demo` actually prints.
> **`cohort-pilot`'s numbers must not move — not one digit.** Cost if wrong: README shows numbers no run
> produces, which is the *documented rule with no code behind it* defect on the one page a new user
> reads first.

What stop 1 creates:
- `~/publishable-demo-data/input/index.csv` — **240 rows**, columns `unit_id`, `x`, `y`, by design
  § 9's fixture-A recipe: `random.Random(<fixed literal>)`, `x = rng.gauss(0, 1)`,
  `y = ρ·x + sqrt(1 − ρ²)·rng.gauss(0, 1)`, **both rounded to six decimals**. The rounding is
  deliberate: it makes the CSV the artifact of record.
- `templates/correlation.py` — a **project-local** template registered `correlation`. **Not `generic`**
  (correction 1: `generic` derives nothing, so a demo naming it prints no `r`).
- `src/correlation_pilot/` — **three** steps: `step01_load_cohort` (`run`), `step02_fit_model`
  (`condition`), `step03_analyze` (`repeat`).
- `configs/correlation-pilot/config.yaml` — `experiment_type: correlation`, **no `template_version`**,
  `baseline: {analysis.method: pearson}` and `grid: {analysis.method: [spearman, kendall]}`, one
  `{kind: seed, n: 5}` repeat. **No `statistics.resample` block** (correction 9: a derived metric is
  bootstrapped without one, and stop 2 promises only `sweep` and `replication`).
- `.demo-progress`, and **an append to the demo repo's own `.gitignore`** — **not** to
  `scaffold.GITIGNORE` (correction 16, design Decision 9).
- `git init` and one commit, with the tree clean afterwards so stop 5's `run` is not pushed onto
  `draft`.

**`aggregate` reads RECORDED columns** (`units.pred`, `units.truth`), never declared attributes —
correction 10: the attribute route gives the paired contrast `0 of 2000` and a `null` interval, which
is README's headline number. **`step03_analyze` records `{"pred": …, "truth": …}` and skips twelve
named keys** (correction 13), and sets `nondeterministic = True`, drawing from `self.rng` — **which is
a `random.Random`, so `.gauss`, never `.normal`** (corrections 3 and 4; a step written from the
document raises).

**Mutations:** design § 10 rows 10 and 11. Row 10's assertion has **two halves that one assertion
cannot separate**: `.demo-progress` is ignored in the demo repo **and** absent from a plain
`publishable new` project's `.gitignore`.

**Must not touch:** `scaffold.GITIGNORE`; README; guard-pin arms.

---

## Task 11

**Binding corrections: 6, 7, 8, 12, 15, 23.**

**`demo` stops 3–6, and the stop-5 render.**

> **RULING DD (binding, restated here)** — see task 10 for the sentence. **You are the task that
> computes the numbers**, by running.

Stops 3, 4 and 5 each: print the next command exactly as typed, wait, run it **in-process** through
`main([...])` on `Enter`, then say in two or three lines what its output meant. Stop 6 **prints** the
`reproduce` invocation and does not run it. `q` at any stop prints the remaining commands in order.
**Unattended it does not pause** — no flag, no second command name. **No prompt may alter the config.**

**Stop 5's summary is `demo`'s own, rendered from the `run.yaml` `run` just wrote.**
**`run` is not changed and `report` is not invoked** (design Decision 7): correction 6 — `run` prints
no table at all; correction 23 — `report`'s is a 15-column raw table and would make the six-stop walk
seven commands.

**Stop 4's commentary names both counts** (correction 7, Decision 14): *"3 conditions × 5 repeats = 15
repeat-scoped executions, and 19 in all."* **`dry-run`'s own output is not changed.**

**Stop 5's commentary names `W-ENV-UNLOCKED`** and why it fires (correction 15, Decision 15). Nothing
is suppressed and no lockfile is fabricated.

**The spread line is a claim** (correction 8): a **derived** metric carries no `repeat_spread`, so
report a **recorded** column's or drop the line. Say in your report which you did and why. **Do not
report a derived metric's.**

**Every literal you print is computed by running, and TWO different stability checks are owed, because
one does not cover both quantities** (corrections 31, 32).

- **Point estimates and the delta.** Report each value's **distance from the nearest rounding boundary
  at the printed precision**. A margin below `1e-6` is a finding: reduce the printed precision until
  every margin clears it, and say so. A value one libm ulp from a boundary is a transcript that flips
  on someone else's machine.
- **Interval bounds.** Correction 32: they are **order statistics** — `pool[lo]`, `pool[hi]` at fixed
  integer ranks — so a boundary margin says nothing about a **rank swap**, which moves a bound by the
  gap between adjacent draws. The draw *composition* is safe (indices come from a generator seeded off
  the design digest); only each draw's statistic can move in its last ulps across SciPy versions.
  **Report, for each selected rank, the gap between that draw and each of its neighbours in the sorted
  pool.** A gap below `1e-12` means a rank swap is reachable and the interval may not be quoted at that
  precision. **If any bound fails, README quotes the point estimates and the delta exactly and
  DESCRIBES the intervals rather than quoting them** — a smaller claim, honestly made. Say which you
  did.

**Mutations:** design § 10 rows 12, 13, 14, 15. Row 14's assertion needs a **whole-tree snapshot**, not
a check for an absent `mkdir` call.

**Must not touch:** README (task 12's), `run`, `dry-run`, `report`.

---

## Task 12

**Binding corrections: 6, 7, 28, 29, 33. You are guard-pin arm B's sole authorized editor. You are
named on NO other arm — arm C's editor is NONE and it does not cover README.**

**README's `demo` transcript becomes what `demo` prints.** Take task 11's measured values.

> **RULING DD (binding, restated here)** — see task 10. **It is what authorizes you to edit an arm whose
> editor is otherwise NONE.**

Edits:
- README's stop-5 block: the three condition rows and the attrition/spread line become task 11's
  values. **The `run.yaml → …_2f5c8d0/run.yaml` line does not move** — a run ID carries a timestamp, so
  it is illustrative whatever else changes, and one sentence beside the block says so.
- README's progress-bar block and its `Running 3 conditions × 5 repeats = 15 executions` banner:
  correction 6 says `run` prints neither. Attribute `run`'s two real lines to `run` and the summary
  beneath them to `demo`, in the block itself.
- § What `demo` walks you through's stop-4 cell and README's execution count: both counts, per
  correction 7.
- **README's v0.x notice** (correction 33). It reads *"not every command described here dispatches yet
  … the rest say so when you invoke them"*, and after task 13 every `Status` cell in all three tables
  reads `built`. **Prefer deleting the false clause to rewriting it** — a rewrite invents, a deletion
  cannot — and leave the rest of the notice (the settled design, the shifting interfaces, the feedback
  invitation) exactly as it is. Coordinate the wording with task 13 in batch 6's review if the
  retirement's own sentence overlaps.

**Arm B's post-edit state is PROCEDURAL, and a literal tuple destroys the arm** (correction 28, design
§ 8.1). Follow it exactly:

1. Re-scan README with the **unmodified** helper and the **unmodified** `_H5A_ARM_D_LITERALS`. Edit
   neither.
2. The result must equal the pre-edit tuple **minus exactly these four entries and nothing else**: the
   three condition rows and the `intervals over 228 of 240 units (12 failed) · seed spread std 0.014`
   line.
3. Every other entry survives **verbatim**, the `2f5c8d0` line included.
4. **Any surviving line not in that eleven-entry remainder is a finding**, not a literal to refresh —
   it means a new demo number contains a worked-example literal, and it goes to the controller before
   the tuple is touched.
5. **Do not extend `_H5A_ARM_D_LITERALS`** with the demo's numbers. Arm B pins the worked example's;
   task 11's fixture pins `correlation_pilot`'s against a real run.

**Arm A's `DESIGN_PRINCIPLES` and `REFERENCE` parametrizations have editor NONE, and so does the whole
of arm C** — which covers `design-principles.md` and `experimental-designs.md` only, and neither
README nor `reference.md` (design § 8.2). If arm A goes red you have moved a
`cohort-pilot` number; if arm C goes red you have edited a document no task in this slice may touch.
Correction 29 names the two neighbouring pins that are **not** collisions — attribute them in your
report rather than editing them.

**Must not touch:** `src/`; the guard-pin arms you are not named on.

---

## Task 13

**Binding corrections: 25, 26, 27. You are guard-pin arm F's sole authorized editor.**

**The `NOT BUILT` retirement, and the `E-GIT-NO-REPO` row.**

Empty `NOT_BUILT_COMMANDS`, flip all three `Status` cells to `built`, and handle what that creates.

> **RULING CC (binding, restated here):** `list-templates` **is H9d's**, and the spine design's H9 row
> is amended by **appending** a dated note to its *Order, amended against outside evidence* section —
> **never** by editing the row in place. Say in that note that a command orphaned by a closed family is
> found by **re-reading the charter against the code**, not by waiting for someone to notice: four H7
> scopings said *"it is still H7's"*, each was right when written, and none re-owned it when H7 merged.

**Decision 12 binds you.** `_report_not_built`, the dict, the three `Status` columns and § Creation
commands' paragraph **all stay**, deliberately unreachable. Correction 26: emptying the dict makes the
binding test's `if status == "NOT BUILT"` branch **dead**, so add the companion — `NOT_BUILT_COMMANDS
== {}` **and** a direct call to `_report_not_built` with a name and a real § heading asserting the exact
diagnostic. **Both claims in one place**, so they cannot drift apart. § Creation commands' paragraph
gains one sentence saying no row carries the marker today and why the machinery is retained.

**`E-GIT-NO-REPO`'s row is widened, and its enumeration is RE-DERIVED BY READING, never incremented.**
Correction 27: the row says *"Eight paths reach it"* and enumerates two uncaught, three caught by code,
three caught by type. `docs` adds a **by-code** site; `list-templates` adds a **by-type** site — two
additions of **different kinds**, so no single digit repairs the sentence. **Enumerate every call site
by reading `src/`, then confirm with a grep** — the reverse order is the substitution `CLAUDE.md`
§ Answering a question with a proxy names, and it once shipped a credential leak. Report what you
enumerated and what each site does.

**And check the neighbours you moved.** § Errors carries **one row per code covering every emit site**.
Task 3 edited `scaffold.py`, so re-check `E-PROJECT-EXISTS`' row against the code rather than assuming
it. **A row widened in the slice that then undercounts it has produced a whole-branch Major on five
sub-slices** — check each table's own **scope sentence**, not only its cells.

**Must not touch:** the four documents' other sections (task 14's), guard-pin arms you are not named on.

---

## Task 14

**Binding corrections: 1, 2, 3, 5, 8, 9, 10, 11, 12, 16, 19, 20, 21, 24, 29. You are named on NO
guard-pin arm.** You edit `reference.md` in eight sections and that is expected — **no arm hashes it**
(design § 8.2). **Arm A's `REFERENCE` parametrization must stay green**: it holds every `reference.md`
line carrying a worked-example literal, so if it fires you have moved a `cohort-pilot` number.

**The four documents, `CLAUDE.md`, `spec-defects.md`, both consistency passes, and § Executability.**

Document edits:
- § Operation commands: `docs` and `list-templates` lose `NOT BUILT`; `list-templates`' *Does* cell is
  narrowed to task 8's reported wording (correction 21).
- § Creation commands: `demo` loses `NOT BUILT`.
- § What `demo` walks you through: `.demo-progress` *"listed in the generated `.gitignore`"* becomes
  *"listed in the demo repository's `.gitignore`, which `demo` appends"* (correction 16, Decision 9);
  the stop-1 cell names the project-local template; stop 5's cell says the summary is `demo`'s
  (correction 6); the design document's stale *"the `conditions` and `replication` blocks"* is **not**
  followed — build from `reference.md`'s `sweep`, and **do not retro-edit the design**.
- § Using them in step code and § Randomness: `self.rng` is a **`random.Random`** (corrections 3, 4;
  Decision 13). `CLAUDE.md` § Invariants' own sentence is type-agnostic and needs no edit.
- § Package layout: `docs.py` loses `— not yet built`; **rows for `demo.py` and `list_templates.py` are
  added**; `readme_templates/`' row is now true (correction 19). `examples/generic/` **stays and is
  filed** (correction 20) — do not delete a documented directory to make a tree pass.
- § The generated README: brought to what task 3 writes, including the `templates` region it declared
  nowhere.
- § Generators: `generate experiment`'s two `NOT BUILT` halves and `generate template`'s one are gone.
- **§ Errors: five new rows, one per `E-DOCS-*` code** (`-REGION-UNBALANCED`, `-REGION-DUPLICATE`,
  `-REGION-UNKNOWN`, `-NO-REGIONS`, `-NO-README`). **One row per code covering EVERY emit site**, and
  **placed by each table's own scope sentence** — `docs` **raises** these, so read which of the two
  tables that is rather than assuming, and read the sentence rather than the cells. This is the exact
  shape that has produced a whole-branch Major on five sub-slices; it is named here rather than left to
  fall between you and task 13.
- `CLAUDE.md` § Invariants: the creation-command enumeration gains **`demo`**, with the clause Decision
  11 owes — *`reproduce` derives its destination from the record; `demo` has no record to derive from*
  — so the two documented answers about `--into` are one rule, not two.

`spec-defects.md`:
- **Strike** the two bytecode entries (task 9). **Re-read each entry's own claims against the code you
  changed** before striking — a filing's claims go stale like any comment.
- **Re-own** *`diff`'s `uv.lock` row prints two digests…* from H9d to **`unassigned`, with the
  reason**, quoting the 2026-08-24 re-owning and answering it: *"the only remaining slice with a CLI
  rendering surface"* is a **schedule argument wearing a surface argument's clothes** — `diff` is H8b's
  command, and none of `demo`, `docs`, `list-templates` renders a `diff` row or resolves a dependency
  graph.
- **File six new entries**, design § 5's list, each `Owner: unassigned, with the reason` stating that
  no remaining slice (H3c-3's remaining 14 being folds inside cells) has the surface. **Never
  *"whichever slice next touches X"*** — this file rejects that form by name.

**§ Executability on this build:** one dated entry, *"Measured on 2026-08-24 against commit `<sha>`"*,
deriving all four rows per design § 7. **The table block is extracted programmatically and `diff`-ed to
empty** against the H9c entry's copy, by the two independent methods the H8a/H9a/H9b/H9c entries
describe. **No fifth number. It unblocks ZERO configs.** Its cells still name **H8a** — updating them is
exactly how a repeated table stops being repeated.

**Both consistency passes.** The mechanical one over the four documents **named individually**, never
`*.md` — the development record is tracked and `*.md` no longer means what it used to — and **never
filter a sweep's output; filter the file list**, proving each sweep can fail against a string known to
be present. The cross-document one, especially: **the shared worked example** (arm A and arm C's NONE
half are your evidence that it did not move), **config completeness**, **enum comments**, **schema
fields in prose**, and **versions**.

**This is the batch with the most findings historically.** *A documents-and-codes task looks like the
safest one to skip and is the one whose output no later batch reads*, so nothing else will find its
errors.
