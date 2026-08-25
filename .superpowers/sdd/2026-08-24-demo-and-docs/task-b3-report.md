# H9d batch 6 (and batch 5) — tasks 10, 11, 12, 13, 14

**Five tasks, five commits, plus one fix round of my own defects.** Gates clean at every commit;
full suite **3336 passed, 1 skipped, 2 xfailed**.

| Commit | Task |
|---|---|
| `beedd17` | 10 — `demo` stops 1–2 |
| `42e04b0` | 11 — `demo` stops 3–6 and the stop-5 render |
| `88856eb` | 12 — README's transcript, guard-pin arm B |
| `ebe58ca` | fix round — two defects of mine, found before the gate |
| `cbfda10` | 13 — the `NOT BUILT` retirement, `E-GIT-NO-REPO`'s row |
| `1c49187` | 14 — the four documents, `CLAUDE.md`, `spec-defects.md`, § Executability |

**Test count, with its nouns rather than a total.** The dispatch's `3319` is the **pre-work
baseline**: I ran `uv run pytest` at `42e3f02` before writing a line and got exactly
`3319 passed, 1 skipped, 2 xfailed`. Final is **3336**: **+18** in `tests/test_demo.py`, **−2** in
`tests/test_docs.py` (the two `…_defers…` tests deleted with the dictionary key), **+1**
`test_the_not_built_machinery_is_retained_with_no_row_marked`. A report claiming 3319 would be
claiming I added no tests.

---

## Ruling GG — none of my tasks owns `base_step.py`, so the escape clause fired

**Measured, not assumed.** No task section 1–14 of the plan names `base_step.py` as an edit
(`grep -n "base_step" docs/superpowers/plans/2026-08-24-demo-and-docs.md` → corrections 3 and 5, the
task-10 and task-14 mentions of `self.rng`, and ruling GG itself — no edit assignment), and
`git log main..HEAD -- src/publishable/base_step.py` is **empty**. GG's own clause: *"whichever task
owns `base_step.py` owns all four. If no task does, the batch that discovers it says so and stops
rather than folding it in silently."* **So I stopped, and this is the saying-so.** The ruling lives
at `f9434bf`.

**The four obligations, each answered:**

1. **A disclosure section** — **not written**, because the behaviour did not change. Unowned.
2. **A pin on the type itself** — **not written**. Unowned. The measurement behind it stands:
   `grep -rn 'self.rng' tests/*.py` → **zero hits**, still, at `1c49187`.
3. **`demo`'s generated step drawing from `self.rng`** — **DONE, and forward-compatibly.** The step
   draws `self.rng.random()`, a method **both** `random.Random` and `numpy.random.Generator` carry
   (GG's own disclosure names `shuffle`, `random`, `uniform` as surviving). Never `.gauss`, never
   `.normal`. If the ruling is later built, `demo` needs no edit — `correlation_pilot`'s numbers move,
   which Ruling DD explicitly permits, and `cohort-pilot`'s do not.
4. **The two `reference.md` statements checked against the code rather than assumed correct** —
   **DONE, and it is a finding: both were false of the shipped code, and TWO NEIGHBOURING ONES WERE
   TOO.** § Using them in step code's fenced comment and § Randomness' table row both said
   `numpy.random.Generator`; beyond them, § Randomness told a concurrent step to use
   **`self.rng.spawn(n)`** — which `random.Random` does not have at all — and said *"`self.rng` is
   exactly `default_rng(self.derive_seed("<this step>"))`"*. All four are corrected to what the code
   does (task 14). GG asked for exactly this check and it found two more sites than it named.

**Filed, because a report's own escalation is not a filing:** `spec-defects.md` now carries
*OPEN — ruling GG asked for `self.rng` to become a `numpy.random.Generator` and NO task built it*,
`Owner: unassigned, with the reason`. It states which way the divergence was closed (the **document**
moved, per Decision 13) so it cannot be read as contradicting design § 5 entry 2, and it keeps M7.

---

## Every line `demo` actually prints, measured

Run unattended (`</dev/null`) in a clean scratch `HOME` outside this repository, at `1c49187`, with
absolute paths elided to `~`. **129 lines.** Nothing here is transcribed from a document; README's
`demo` blocks were made from this.

```
Created publishable-demo/
  240 synthetic units      ~/publishable-demo-data/input/
  template                 templates/correlation.py
  experiment               src/correlation_pilot/
  config                   configs/correlation-pilot/config.yaml

Your data sits outside the repo, where real data belongs. Everything from
here is the CLI you'd use on an experiment of your own.

Next:  a look at the config that describes this run

sweep:
  # What varies across conditions. `baseline` is the condition every delta is
  # measured against; `grid` is the axis itself.
  baseline: {analysis.method: pearson}
  grid:
    analysis.method: [spearman, kendall]

replication:
  repeats:
    - {kind: seed, n: 5}             # seed | batch | fold
  order: as_declared               # as_declared | randomized
  rationale: "Five seeds, to show how much the pipeline itself moves"

That is the whole description of what is about to run: three conditions
on one axis, five seed repeats each. Read the config, don't edit a step —
`code_hash` covers `src/**` and `templates/**`, so an edited step would
dirty the tree and make the run at stop 5 refuse.

Next:  publishable validate configs/correlation-pilot/config.yaml

  ✓ config valid · configs/correlation-pilot/config.yaml

validate read your config and your data. It created nothing and reached
nothing off this machine — the 240 units it resolved came from the
index.csv outside the repo, and `input_dir` being outside is enforced.

Next:  publishable dry-run configs/correlation-pilot/config.yaml

  warning W-ENV-UNLOCKED       environment
          no uv.lock found at ~/publishable-demo; the environment is not pinned, and `reproduce` will not be able to restore it
1 problem (0 errors, 1 warning)
sweep: 3 conditions (baseline + grid) × 5 repeats = 19 executions
  00_baseline  analysis.method=pearson
  01_method=spearman  analysis.method=spearman
  02_method=kendall  analysis.method=kendall
repeats: seed(n=5)
  seeds: [3834353537, 3929976627, 1573656686, 4250950106, 3816265336]  (auto, from design digest)
  comparisons: paired (allocation: within)
steps: step01_load_cohort (run) -> step02_fit_model (condition) -> step03_analyze (repeat)
statistics: basis units (n=240 resolved); correction holm; derived metric names come from the template's aggregate() and are not knowable before the run
scale:  4560 unit-executions (19 executions × 240 units handed to each)
would create 19 step directories under ~/publishable-demo-data/results/run_.../
  shared/step01_load_cohort
  conditions/00_baseline/step02_fit_model
  conditions/00_baseline/seed37/step03_analyze
  conditions/00_baseline/seed27/step03_analyze
  conditions/00_baseline/seed86/step03_analyze
  conditions/00_baseline/seed06/step03_analyze
  conditions/00_baseline/seed36/step03_analyze
  conditions/01_method=spearman/step02_fit_model
  conditions/01_method=spearman/seed37/step03_analyze
  conditions/01_method=spearman/seed27/step03_analyze
  conditions/01_method=spearman/seed86/step03_analyze
  conditions/01_method=spearman/seed06/step03_analyze
  conditions/01_method=spearman/seed36/step03_analyze
  conditions/02_method=kendall/step02_fit_model
  conditions/02_method=kendall/seed37/step03_analyze
  conditions/02_method=kendall/seed27/step03_analyze
  conditions/02_method=kendall/seed86/step03_analyze
  conditions/02_method=kendall/seed06/step03_analyze
  conditions/02_method=kendall/seed36/step03_analyze
and 8 fixed files in that directory:
  config.yaml
  environment/pyproject.toml
  environment/repo_root.txt
  executions.jsonl
  identity.json
  manifest/input.json
  run.yaml
  sweep.yaml
the ~/publishable-demo-data/results/latest pointer is repointed too; it sits beside the run directory rather than inside it
artifact files inside a step directory are NOT listed: their names are `io.write`
  arguments in step code, which core never inspects, so they are declared nowhere
  in the config and cannot be known before the run
creates nothing

3 conditions × 5 repeats = 15 repeat-scoped executions, and 19 in all —
the plan also runs step01_load_cohort once for the whole sweep and
step02_fit_model once per condition. Still creates nothing.

Next:  publishable run configs/correlation-pilot/config.yaml

  warning W-ENV-UNLOCKED       environment
          no uv.lock found at ~/publishable-demo; the environment is not pinned, and `reproduce` will not be able to restore it
1 problem (0 errors, 1 warning)
run.yaml → ~/publishable-demo-data/results/run_2026-08-25T05-52-14Z_f1fd0ef/run.yaml

W-ENV-UNLOCKED fired because this project has no uv.lock: its pyproject
depends on `publishable`, which cannot resolve until the package is
published, so there is nothing to pin yet. Nothing was suppressed.

run printed no table — its whole output is that warning and the path to the
record. Everything below is `demo` reading the record back:

  condition             r       95% CI            vs baseline (paired, 95% CI)
  00_baseline           0.697   [0.630, 0.757]    —
  01_method=spearman    0.666   [0.582, 0.739]    -0.031  [-0.068, -0.002]
  02_method=kendall     0.482   [0.413, 0.550]    -0.215  [-0.240, -0.190]

  intervals over 228 of 240 units (12 failed) · seed spread std 0.003 of recorded `pred`

  `pred` and `truth` are recorded columns, so each publishes its own
  metric and joins the correction family beside `r` — six members, and
  two of them nobody reads. A template that derived twenty diagnostics
  would correct every interval in the run for numbers nobody reads.

Next:  the run.yaml all of this produced, and who reads it

The record is ~/publishable-demo-data/results/run_2026-08-25T05-52-14Z_f1fd0ef/run.yaml
It carries the results AND everything needed to regenerate them. On any
other machine, a collaborator runs:

  publishable reproduce ~/publishable-demo-data/results/run_2026-08-25T05-52-14Z_f1fd0ef/run.yaml

Not run here, and that is the lesson: `reproduce` clones the repository
`provenance.git.remote` names, and this demo repo has one local commit and
no remote. It is what somebody ELSE runs, on a machine holding neither your
data nor your credentials.
```

**Attribution, since three commands' output is passed through unchanged.** `demo` itself prints the
`Created …` block, the `Next: …` lines, the two config blocks at stop 2, every commentary paragraph,
the stop-5 table and the stop-6 hand-off. `validate` prints its one `✓` line; `dry-run` prints its
warning block and its whole plan; `run` prints **its warning block and one `run.yaml → <path>` line
and nothing else** — correction 6, confirmed on my own run rather than carried.

**Two README blocks were fiction, not one.** Correction 6 named `run`'s. Stop 3's was fiction too:
README claimed `✓ config valid · 240 units resolved · input_dir outside the repo` and `validate`
prints `✓ config valid · configs/correlation-pilot/config.yaml`. Both are now what the commands
print. README's stop-1 block also gained the `template  templates/correlation.py` line `demo` writes
— an edit beyond task 12's enumerated list, made because the alternative is a documented transcript
no command produces, which is the defect this slice exists to close.

---

## Ruling DD — `cohort-pilot`'s numbers did not move, and arm B's PROCEDURAL re-scan

**`cohort-pilot`: not one digit.** Evidence is the arms whose editor is NONE, green at `1c49187`:
`test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text[DESIGN_PRINCIPLES]` and `[REFERENCE]`
(arm A), the whole-file `sha256` arm C over `docs/design-principles.md` and
`docs/experimental-designs.md` (**byte-identical at merge — neither file was touched by any of my
five tasks**), arm E (`test_diff.py`'s three worked `diff` blocks), and arm G. Correction 29's two
neighbouring pins are **attributed, not edited**:
`test_validate.py::test_the_worked_examples_intervals_in_reference_md_are_not_narrowed_by_the_null_test_work`
reads `reference.md` only and deliberately leaves README's `[0.347, 0.477]` unpinned, and
`test_diff.py`'s H8c arm D pins README's `diff` block, which is hashes only.

**Arm B, by design § 8.1's procedure, in order:**

1. Re-scanned README **before** any edit with the unmodified
   `_h5a_arm_d_lines_carrying_the_worked_example` and the unmodified 25-entry `_H5A_ARM_D_LITERALS`.
   Result: 15 entries, **equal to the shipped golden** (`pre == _H5A_ARM_D_README_LINES` → `True`).
2. Edited README. Re-scanned with the same unmodified helper and the same unmodified literals.
   Result: **11 entries**.
3. The difference is **exactly these four and nothing else**:
   - `  00_baseline           0.581   [0.488, 0.661]    —`
   - `  01_method=spearman    0.607   [0.517, 0.683]    +0.026  [−0.007,  0.059]`
   - `  02_method=kendall     0.412   [0.347, 0.477]    −0.169  [−0.213, −0.125]`
   - `  intervals over 228 of 240 units (12 failed) · seed spread std 0.014`
4. **Every survivor accounted for**, verbatim, in the pre-edit order —
   `post == tuple(l for l in pre if l not in removed)` → `True`:
   the `…_2f5c8d0/run.yaml` line (Decision 2 keeps it), `└── run_2026-08-07T09-14-03Z_8e21ab3/`, the
   two `step03_analyze: {r: {value: …}}` lines, the `step03_analyze: {r: {delta: …}}` line, the three
   `code_hash`/`parameters_hash`/`input_manifest_hash` comment lines, and the three
   `code_hash`/`input_manifest`/`uv.lock` `identical` lines. **Zero lines survived outside that
   eleven-entry remainder and zero new lines appeared** — so design § 8.1 step 4's finding condition
   did not fire. Checked mechanically (`[l for l in post if l not in pre]` → `[]`), not by eye: the
   demo's new numbers (`0.697`, `0.630`, `0.757`, `0.666`, `0.582`, `0.739`, `0.482`, `0.413`,
   `0.550`, `0.031`, `0.068`, `0.002`, `0.215`, `0.240`, `0.190`, `0.003`) contain no substring of
   the literal list.
5. **`_H5A_ARM_D_LITERALS` was NOT extended.** `correlation_pilot`'s numbers are pinned against a
   real run by `tests/test_demo.py::test_the_stop_5_summary_is_demos_own_and_matches_the_record_run_wrote`,
   which reads them back out of the `run.yaml` `run` wrote.

**And the arm was proven still able to fail**, both directions, as H9c's controller ruling did:
moving a `cohort-pilot` hash literal in README (`sha256:6b1f…` → `6b2f…`) fails `[README]` alone;
reintroducing `0.581` into the demo table fails `[README]` alone. Restored by copy, verified by
behaviour (green), never by `git status`.

---

## Task 11's two stability checks, both measured

Instrumented `stats._percentile_ranks` to capture each pool at the moment its ranks are read, then
ran a real `run`. **Seven pools** — three `percentile_of_derived` (the per-condition `r`), two
`paired_percentile_of_derived` (the deltas), two `interval_at` (the corrected pair).

**Point estimates, deltas and bounds — distance from the nearest rounding boundary at 3 decimals.**
Smallest margin over all 21 printed quantities: **6.2e-05** (`cond2 r delta ci lo`,
`-0.2395622718340421`). Every margin is `>1e-6`, so the printed precision stands and was not reduced.

**Interval bounds as ORDER STATISTICS — neighbour gaps at each selected rank** (correction 32; a
boundary margin says nothing about a rank swap). Smallest gap between a selected draw and either
neighbour, across all seven pools: **3.66e-06** (the kendall delta's upper rank). Every gap is
`>1e-12` by six orders of magnitude, so no rank swap is reachable from last-ulp SciPy differences.
**Both checks pass, so README QUOTES the intervals** rather than describing them.

**The spread line reports a RECORDED column's, and says so.** `r` is derived and its record carries
**no `repeat_spread` key at all** (asserted, not assumed:
`assert "repeat_spread" not in entry`). The line reads
`seed spread std 0.003 of recorded \`pred\``.

---

## § Executability on this build — re-derived, and it does not move

One dated entry, *"Measured on 2026-08-25 against commit `ebe58ca`"*, all four rows derived
individually (the derivations are in the entry). **It retires no refusal and unblocks ZERO configs.**

**The table block was extracted programmatically and `diff`-ed to empty against the H9c entry's
copy, by both documented methods**: the walk that finds the last `| Figure | Count | Visible to`
header and reads forward while the line starts with `|` (6 lines), and the fixed six-line slice from
the same index (6 lines). `diff` returncode **0**, empty output, both ways. **Can-fail control**:
changing one cell (`**8 of 8**` → `**9 of 9**`) makes the comparison differ. Cells still name
**H8a**. **No fifth number, and no single figure quoted.**

---

## Task 13 — `E-GIT-NO-REPO`, enumerated BY READING, then confirmed by grep

I read every `find_repo_root` call site in `src/` (each one printed and read in full), **then**
confirmed with `grep -rn "find_repo_root" src/publishable/*.py src/publishable/**/*.py`, **then**
confirmed a third way with an AST sweep that classifies each call by its enclosing `try`. All three
agree. **TEN paths — two uncaught, four by code, four by type.** The row states the breakdown, not
the total.

| Site | Kind | What it does |
|---|---|---|
| `cli.py` `_prepare_run` | uncaught | surfaces at `main`'s printer, exit 1; walks from the **config path** |
| `cli.py` `_dispatch_generate` | uncaught | same, walking from **`Path.cwd()`** |
| `validate.py` `_check_data` | by code | returns quietly — a pass branch |
| `study.py` `_refuse_if_in_repo` | by code | the pass branch of its own in-repo refusal |
| `reproduce.py` config form | by code | **re-reports** under the same code through its own `Collector`, exit 1 |
| `docs.py` `command_docs` | by code | **NEW** — re-reports, exit 1: a README is the command's whole input |
| `reproduce.py` `prepare_checkout` | by type | the raise **is** the ordinary case |
| `validate.py` `validate_config` | by type | `repo_root` stays `None`, discovery skipped, every other check runs |
| `cli.py` `_preloaded_experiment` | by type | under `except Exception`, returns `None` |
| `cli.py` `command_list_templates` | by type | **NEW** — lists core and installed, prints the absence |

Three of the ten walk up from `Path.cwd()` — `generate`/`init`, `docs`, `list-templates` — and the
row names all three; the other seven walk from a path their command was given. Design § 10's
**mutation 16** (delete the widened subject) was run: the AST sweep compares the row's own claim
against the code and **fails loudly** (`ROW AND CODE DISAGREE: row={...3,3} code={...4,4}`), passes
unmutated.

**The neighbour check found a real undercount nobody had widened.** `E-PROJECT-EXISTS` has **two**
emit sites — `scaffold.py:50` (`new`) and `plugin_scaffold.py:169` (`plugin new`) — found by reading
both files; § Errors' sentence named only `publishable new`. Fixed. (An older `spec-defects.md`
entry had asked for exactly this and recorded it as still undone; it is now done, and I have not
struck that entry because it is not mine to close — it is a *different* filing about `E-PARAM-MISSING`
whose sweep noticed this in passing. Flagged for the reviewer.)

---

## What I grepped, and what every hit was

File lists filtered, never sweep output. Every sweep run against a string known to be present first.

1. `grep -n "self.rng" README.md docs/design-principles.md docs/experimental-designs.md
   docs/reference.md CLAUDE.md docs/feasibility-llm-growth-studies.md | grep -i generator` — **2 hits,
   both attributed and both left**: `reference.md:2504` (*"Take the generator core hands you"* — the
   word is generic English in a paragraph about numpy's globals, and the claim stays true), and
   `CLAUDE.md:833` (*"`self.rng` is the generator to draw from"* — type-agnostic, exactly as
   Decision 13 says). Can-fail control: bare `self.rng` → 9 hits in `reference.md`, 1 in `CLAUDE.md`.
2. `grep -n 'generated \`.gitignore\`'` over the same six files — **0 hits**, the sentence moved.
   Control: `demo-progress` → 1 hit in `reference.md`.
3. `grep -n "not yet built"` over the four documents — **3 hits, all attributed**: `reference.md`'s
   two *convention* sentences (§ The importable surface, § Package layout), which are
   self-maintaining derivations over a `Status` column and a tree marker — both now cover zero rows,
   and CLAUDE.md's own § Misreadings row argues against replacing a self-maintaining sentence with an
   enumeration — and README's pointer at the `Status` column, whose second sentence I deleted (below).
4. `grep -n "specified but not\|specified-but-unbuilt"` over the four documents — **3 hits**:
   `reference.md:3771` (§ Creation commands' paragraph, which Decision 12 keeps and which I extended
   to say no row carries the marker today), `reference.md:3826` (the exit-`2` row, still true of the
   retained machinery), and one unrelated `sweep.baseline` row matching on *"specified"*.
5. `grep -c "NOT BUILT" docs/reference.md` — **3**, each attributed: § The one config file's history
   sentence, § Validation's *"would be marked"* convention line, and § Creation commands' paragraph
   explaining the column. **No row carries the marker.**
6. `grep -rn "find_repo_root"` across `src/` — 13 + 13 hits over two globs: 1 definition, 1 docstring
   mention, 1 internal call in `provenance.git_provenance` (reached only from `_prepare_run`, not a
   separate path), 10 call sites, each enumerated above.
7. `grep -rn "E-DOCS-" src/publishable/docs.py` — 17 hits: 4 docstring lines, 12 raises, 1 in
   `command_docs`' path-column branch. Every raise is covered by one of the five new § Errors rows,
   and the rows name `merge_into_readme`'s generator path as the second reporting surface.
8. `grep -rn "aggregate" src/publishable/templates/builtin/generic.py` — **0 hits**, which is
   correction 1 re-verified at HEAD before filing it.
9. `ls src/publishable/` — read to check the § Package layout tree row by row; this is what found
   that **`list_templates.py` does not exist**.

**I am not reporting a count of disagreements.** Each is named where it belongs: the design's
`list_templates.py` row against `cli.py`'s actual home for the command; the brief's *"`docs` **raises**
these"* against § Errors' own scope sentences (which land on the same table for a different reason —
`ContractError`s raised in `docs.py` and re-reported, exactly `E-GIT-NO-REPO`'s shape); design § 10
row 14's whole-tree snapshot being **blind** to the mutation it names; and the two defects of my own
below.

---

## Two defects of mine, found before the gate, fixed in `ebe58ca`

Both are *§ Answering a question with a proxy* in its plainest form, and both are mine.

1. **`_print_remaining` sliced by position.** `walk_commands()[after_stop - 2:]` dropped the command
   just declined — quitting at stop 4 handed back `run` alone. The existing arm quit at stop 2, the
   one value where a position-based slice is right whatever the arithmetic. **A new arm quits at
   stop 4**, and its own mutation (the old expression restored) fails both arms.
2. **`latest_run_yaml(root)` never read `root`.** It globbed the **shared**
   `~/publishable-demo-data/results`, so two demos on one machine made stop 6 name whichever ran
   last. It now reads this project's own `data.output_dir` from its own config. New arm, own mutation.

Also deleted: `q`'s `publishable report <the run.yaml those write>` line — a command the six-stop walk
never runs.

---

## Mutations, all full-suite, foreground, unfiltered

| # | Mutation | Result |
|---:|---|---|
| 10a | delete `demo`'s `.gitignore` append | **1 failed** — `test_demo_progress_is_ignored_in_the_demo_repo` |
| 10b | add `.demo-progress` to the shipped `gitignore.tmpl` (row 10's other half) | **3 failed** — including guard-pin **arm D** and task 3's own pin |
| 11 | seed the data generator from the clock | **1 failed** — `test_the_dataset_is_byte_identical_across_two_invocations` |
| 12 | pause even with no tty | **8 failed** |
| 13 | let a tty prompt reach the config | **1 failed** — `test_no_pause_alters_the_config`, on `parameters_hash` |
| 14 | stop 6 **runs** `reproduce` instead of printing it | **2 failed** |
| 15 | `read_progress` always answers 0 | **5 failed** |
| 16 | delete the widened subject from `E-GIT-NO-REPO`'s row | the row-versus-code AST sweep **fails loudly**; passes unmutated |
| B1 | move a `cohort-pilot` hash literal in README | arm B `[README]` alone |
| B2 | reintroduce `0.581` into the demo table | arm B `[README]` alone |
| F1 | `_print_remaining`'s old off-by-one | **2 failed** |
| F2 | `latest_run_yaml` globbing the shared results dir | **1 failed** |

**Row 10's two halves needed two arms and I deleted my duplicate of the second.** Task 3 already ships
`test_the_scaffolded_gitignore_still_says_nothing_about_demo_progress`; I cite it rather than pin the
same list twice, and mutation 10b exercises both.

**Design § 10 row 14's whole-tree snapshot is BLIND, measured.** A `demo` that both prints the
invocation **and** runs `reproduce` leaves the tree byte-identical — this repo has no remote, so
`reproduce` refuses before creating anything — and the snapshot arm passed with the behaviour
neutered. The arm now carries a **sentinel on `_run_in_project`** beside the snapshot, and that
combined mutation fails it. The snapshot is kept: it is what catches a stop 6 that clones on a
machine where the clone would succeed.

---

## Consistency passes

**Mechanical**, over the four documents **named individually** plus the feasibility analysis, fenced
blocks skipped: every relative link and `#anchor` resolves (**0 problems**, with a can-fail control
proving an invented anchor is reported and that the anchor set is non-empty and holds real members);
no duplicate anchors; every table's rows match its header's column count; no empty table rows; no
trailing whitespace, tabs or invisible unicode. **My first slugger was wrong and reported 31 false
positives** — it collapsed runs of whitespace, so `Secrets & credentials` slugged to one hyphen where
GitHub emits two; corrected to one hyphen per space, which is what GitHub does, and the 31 vanished.
Recorded because a checker that reports a real anchor as broken is the same class of error as one
that misses a broken one.

**Cross-document**, over the four only: the **shared worked example** did not move (arms A, C, E, G,
all editor NONE, all green); **config completeness** — no config field was added or renamed by any of
my edits, and `demo`'s own config is materialized by `materialize_config`, so every key it holds is a
key § The one config file already shows; **enum comments** — no enum moved; **schema fields in
prose** — none added; **declared vs. derived** — untouched; **versions** — untouched, and the README
v0.x notice keeps everything but the clause correction 33 named; **prevented mistakes** — untouched;
**the `Status` column** — every cell in all three tables now reads `built`, which is what made the
notice's clause false and is why it is gone.

---

## Concerns

1. **`CLAUDE.md` § Repository status has no H9d paragraph, and no task owns writing one.** Every
   merged slice so far carries one, and the order sentence still reads *"H5 Artifacts, H6 Hashes and
   provenance, H9, then H3c-3's remaining 14"*. My brief scopes `CLAUDE.md` to § Invariants, so I did
   not write it. It is the controller's or the whole-branch gate's.
2. **`CLAUDE.md` § Misreadings' `field_convention` row now has ZERO current examples**, which b2
   escalated and no task owns. Restated, not fixed — its own text says it keeps retired entries as
   evidence that it retires them, so whether the row survives with an empty list is a decision, not
   an example to update.
3. **The design's `list_templates.py` row was not written.** `command_list_templates` lives in
   `cli.py`; documenting a module that does not exist would mint a second `examples/generic/`. If the
   controller wants the module extracted instead, that is a code move, not a document edit.
4. **I added a third `…_defers…` deletion the controller's amendment did not count.** The amendment
   names *"the two commented lines AND the two `…_defers…` tests"*; task 10 wired `demo` through the
   same transitional deferral batch 4 gave `docs` and `list-templates`, so there were **three** of
   each, and task 13 deleted all three pairs together.
5. **`demo` writes to `~/publishable-demo-data` by default**, which is what the document specifies.
   Every probe I ran used a scratch `HOME`; the tests monkeypatch `HOME`. A reviewer running `demo`
   by hand will write into their own home directory.
6. **`demo`'s stop-5 commentary claims a family of six.** It is read from the design's measurement and
   from my own run's `family_size: 6`; if a future change to the correction family moves it, that
   sentence is prose and no test pins the number.
