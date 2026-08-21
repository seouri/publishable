# H8c — `report`, `study`, and `BaseReport` — design

H8c is the last of H8's three sub-slices. H8a shipped lineage (`io.reuse_from`, `provenance.upstream`,
`lineage.read_run_record`); H8b shipped `diff` and `freeze`. What remains is the reporting half:
`BaseReport` and its export, override discovery, `generate report`, the four standard sections, the
two renderers, `report <run.yaml>`, `report <study.yaml>` with its two cross-checks, and
`study new` / `study add`.

**H8c moves no config count.** The four-row table in
[the feasibility analysis](../../feasibility-llm-growth-studies.md) § Executability on this build stays
**8 of 8 · 0 · 7 · 1**; the `report_by`-under-`resample` gap is H4's and is not touched here. No fifth
number is minted. Like H8b, the only direction this slice could move a count is down, and it does not
move one: **nothing in H8c stops or alters a run** — `report` reads, `study` bundles.

**Two things are carried to this slice by name**, and both are load-bearing rather than incidental:

1. **`BaseReport` is H8c's.** § Package layout makes `report.py` *be* `BaseReport` ("standard sections,
   html/markdown, override discovery") and § The importable surface lists `BaseReport.sections` as "the
   standard sections `super().sections` yields". A `report` without it is not a narrower `report`; it is
   a different design. `spec-defects.md`'s owner note said otherwise on 2026-08-20 and was corrected the
   same day.
2. **The three worked `diff` outputs predate `diff`'s per-side header**, filed OPEN with owner H8c. Its
   blocks sit at three different levels of concreteness, so there is no one identical edit. It is planned
   as work below (Decision 20), and § The worked example is treated as binding: no interval narrows, no
   hash prefix moves, no delta line changes.

---

## The measurement this rests on

**Measured on 2026-08-21 against commit `9963841`** (`main` at HEAD, clean tree). Read-only: nothing
under `src/`, `tests/`, `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md` or `docs/feasibility-llm-growth-studies.md` was edited to produce it; every project,
roster and run directory built for it lives under the session scratchpad. This document is the only file
this pass writes.

Gates at this commit: `uv run pytest` → **2636 passed, 1 skipped, 2 xfailed** (run directly, no wait
constructed). The H8 scoping recorded 2456 at `a346151`; the difference is H8a's and H8b's own suites.

**A scoping expires.** `H8-SCOPING.md` was measured on 2026-08-20 against `a346151`, *before* H8a and
H8b landed. Everything below was re-measured against the code rather than carried, and § What did not
survive H8a and H8b shipping lists the scoping claims that fell.

### How each class of claim was measured

- **Four real end-to-end runs** through `main(["run", …])`, driven by `tests/test_cli.py`'s
  `run_a_project` from a scratchpad script: (r2) baseline + `grid` + 3 `seed` repeats + `report_by` +
  one declared hypothesis; (r3) the same plus a recorded numeric column, `io.skip`, and a
  `summary`-scoped step returning an `Estimate` with no `n`; (r4) the same pipeline with **no
  `data.units` declared at all**, whose step returns a bare scalar. Every `run.yaml` was read key by key.
- **`diff` invoked** against two of those run directories through the real console script, to read its
  per-side header format rather than infer it.
- **Greps for the code, not for the sentence**, per § Misreadings — `grep -n '"basis"'` over `src/` for
  the emit sites of a metric's `basis`, and `grep -rn nondeterministic src/publishable/*.py` for the
  writer of a documented `execution` field.
- Where a claim rests on **reading a document**, it says so.

### The five things the measurement changed

1. **`basis: repeats` is written by nothing.** `grep -n '"basis"'` over `src/publishable/` returns five
   sites and **all five write `"units"`** (`cli.py` ×3, `stats.py` ×2). Confirmed against output, twice:
   in r3 the step returned `n_units` alongside a recorded `score` column, and `aggregated` held `score`
   and `by` and **no `n_units` entry at all** — the returned scalar appears only under `per_repeat`. In
   r4, with `data.units` undeclared, `results.conditions[0]` carries `per_repeat` and **no `aggregated`
   key whatsoever**. Meanwhile `reference.md` asserts in the present tense, in five separate passages,
   that such a metric "says `basis: repeats`, reports the spread, and omits `ci95`", and the shipped
   `W-HYPOTHESIS-INFERENCE-BASE`'s own message names the shape. This lands directly on Decision 13.
2. **`execution.*.nondeterministic` is written by nothing.** § The two files' `run.yaml` example shows
   it on every repeat-scoped execution entry, and `design-principles.md` § Not bit-identical reruns says
   core "records that in `run.yaml` and **notes it in `report`**". Measured on r3: zero occurrences in
   `run.yaml` **and** zero in `executions.jsonl`. `nondeterministic` exists only as a `BaseStep` class
   attribute and as the thing `W-REPL-DETERMINISTIC` reads off the classes at `validate`.
3. **`environment/repo_root.txt` exists, and H8b invented it.** It holds one line, the absolute repo
   root `run` walked up to from the config path it was given. It is the reason Decision 3 is answerable
   at all.
4. **A metric named `by` is unreachable in a record, and `report` still owes the exclusion.**
   `coerce_scalars` constrains a returned mapping's values and never its keys, so a template's
   `aggregate` may return `by` — and when it does the derived metric is lost, measured with
   `report_by` declared and without it, against a control that appears. S4d filed this and shipped
   both halves of the refusal; what it means for H8c is that `aggregated[step]`'s key set is *not*
   the metric set, and Decision 5 says so.
5. **`provenance` now carries `upstream`** (H8a), always a list. It does **not** carry `hostname`, `os`
   or `hardware` — those stay H6's, which is what makes one row of `study add`'s redaction table
   testable only against a synthesized record.

---

## Decisions

Each is numbered, states its grounds, and states what it costs if wrong.

### 1. `report`'s two forms are told apart by the argument's **file name**, and by nothing else

`report` takes one path, per § Operation commands: a `run.yaml` or a `study.yaml`. The form is decided
by `path.name` — `run.yaml` is a run, `study.yaml` is a bundle, **any other name is refused**
(`E-REPORT-FORM`). Not by parsing the document and looking for a discriminating key, and not by
`path.is_dir()`.

**Grounds.** `diff`'s Decision 5 already ruled that an operand's form is decided from the path's shape
alone, "never from whether something at it parses — that is content". The same discipline applies, but
the *question is different*: `diff` asks "config or run record" over two operands of the same document
family; `report` asks "run record or bundle", two document families with two distinct renderers. So
`diff.py`'s `_form` is **not** reused — reusing a predicate that answers a different question is the
proxy substitution § Answering a question with a proxy is about. `_record_dir`'s rule *is* reused in
substance (a `run.yaml` path's run directory is its parent), because that is the same fact.

A **directory** argument is refused rather than accepted. `diff` accepts one because a run directory is
one of two things a *run record* operand can be; `report`'s two forms are two file names, and admitting
a directory would make "which of the two did you mean" a question core answers by guessing.

**Cost if wrong.** A user who types the run directory gets a refusal naming the two file names instead
of a render. That is one extra keystroke, and it is recoverable; a form decided from content is not,
because a truncated `run.yaml` would then read as a bundle.

### 2. `BaseReport` yields `Section` values; `sections` is a generator and `format` is a class attribute with no base default

```python
class BaseReport:
    def sections(self, run, io): ...      # a generator, yielding Section
    def section(self, title, *, body): ...  # construct one; core's
```

- `sections(self, run, io)` is a **generator**, exactly as § The importable surface's table says. Core
  never materializes the list before rendering: an override that yields a cheap section first and an
  expensive figure last should print the cheap one first.
- What it yields is a `Section` — `title` and `body`, where `body` is **markdown text or a mapping core
  knows how to table**. `self.section(...)` is core's constructor for one, because § A report override's
  worked block calls `self.section("Method agreement", body=render_scatter(...))` and a subclass must not
  have to import a name that block does not import.
- `yield from super().sections(run, io)` yields the four standard sections **in order** (Decision 5). An
  override composes by yielding it and then yielding more; omitting the `yield from` yields none of them,
  which is the documented meaning of "adds and reorders sections".
- **An override adds and reorders sections; it cannot obtain a figure core did not already compute.**
  That is the honest form of § A report override's "it cannot change a number", and the claim is sized to
  what the code provides: the standard sections are constructed by `BaseReport.sections` from `run` and
  handed over as **frozen** `Section` values, so a subclass that yields them re-yields objects it did not
  build and cannot rebind their fields. `Section` is frozen for exactly this reason — a plain value class
  whose `body` is a mapping would let a subclass reach into that mapping, and *a safety argument in a
  comment is a claim needing a mutation*, so the immutability is a property of the type rather than a
  sentence about intent (M14). What an override can still do is compute its own number and yield it in a
  section of its own, which is not a change to core's — it is the override's own claim, in its own block,
  and § A report override's "the values it renders come from `results`" is about the standard blocks.
  **Core never inspects the body of user Python** to enforce any of this, and does not need to.
- **`format` has no base default**, which is why § The importable surface's middle column omits it:
  `generate report` always writes the line, so a base default would be a value no generated class could
  ever be observed to take. A class that nonetheless declares none is refused at render
  (`E-REPORT-FORMAT`) rather than silently defaulted — the same reason `BaseTemplate.aggregate` has no
  base returning `{}`, that a default makes "declared" and "omitted" indistinguishable.

**Cost if wrong.** If `sections` were a list-returning method instead, § A report override's
`yield from super().sections(run, io)` line would be wrong in a normative document, and every override
ever written against it would break when it was fixed. If `format` gained a base default, the
`generate report --format` seed line becomes decorative and a hand-edited class silently renders the
wrong medium.

### 3. Override discovery asks **which module this run's own `entrypoint` names**, and reads its sibling `report`

The direct question, stated as a question with one answer: *the run record's embedded
`config.entrypoint` is an import path `<module>:<attribute>`; its root package is this experiment's
package; the override is that package's `report` module, and the class is the `BaseReport` subclass that
module defines.* Nothing else is consulted — not a directory scan of `src/`, not a module-name prefix,
not a marker stamped on a class, not "does this file sit under this repo".

**Grounds.** H7a's two fail-opens and their follow-on both came from answering "is this local?" with
something *correlated* — a module-name prefix, then a marker on the class — and the third from reading
state after `sys.modules` had been restored. The lesson § Answering a question with a proxy draws is to
ask the direct question with machinery that already exists. Here the machinery is
`base_experiment.load_experiment`, which already resolves `entrypoint` from `<repo_root>/src` on
`sys.path`, already purges the root package from `sys.modules` first (two projects in one process can
declare the same package name), and already raises `E-ENTRYPOINT-IMPORT` on a bad path. Override
discovery imports `<root_pkg>.report` through the same window and by the same rule.

**Where `repo_root` comes from, and why it cannot be walked up to.** `report <run.yaml>` is handed a
path inside `output_dir`, and **`output_dir` may never resolve inside the git repo** — the standing
invariant, checked at generate, at validate, and by every command that executes. So `find_repo_root`
walked up from the argument is *structurally* wrong here: it answers "is there a repo above
`output_dir`", a different question, and on a correctly configured project it finds nothing. The fact is
**`environment/repo_root.txt`**, the one-line run-start artifact H8b introduced for exactly this class
of problem, read from the run directory (the argument's parent, Decision 1). `provenance.git.repo_root`
in the record is *not* used: it is the same value recorded at run end, `study add` redacts it
(Decision 10), and two sources for one fact is how the two drift.

**The whole read happens inside the `sys.path` window.** `load_experiment` pops `sys.path` in a
`finally`, so a `sections` body that lazily imported a sibling module at render time would fail after
the pop — the "state read at the wrong moment" corollary in a new costume. So the override module is
imported **eagerly**, the class object taken, **and the whole render performed inside the same window**,
before `sys.path` is restored. Rendering inside the window is the part that is easy to get wrong and
cheap to get right.

**Three refusals, none of them a fail-open.** No `report` module → **no override**, standard sections
only (the ordinary case: `generate report` is opt-in). A `report` module that raises on import →
`E-REPORT-OVERRIDE-IMPORT`, never "no override". A `report` module defining **no** `BaseReport`
subclass, or **more than one** → `E-REPORT-OVERRIDE-CLASS`; "more than one" is refused rather than
resolved by definition order, because definition order is exactly the proxy this section forbids and a
project has one report.

**`report <study.yaml>` performs no override discovery at all.** A bundle sits outside every experiment
repo by construction (§ Why not in the repo), carries records rather than run directories, and has
`provenance.git.repo_root` redacted out of every one of them — so there is no repo, no
`environment/repo_root.txt`, and no `src/**` for `code_hash` to cover. A bundle therefore renders the
standard sections and nothing else. This is a rule with grounds, not a limitation: an override is *one
experiment's presentation*, hashed under that experiment's commit, and a device-independent bundle is
the one artifact that deliberately has neither.

**Cost if wrong.** A directory scan would render one experiment's figures for another's run whenever a
project's `src/` holds two packages — the shape H7a shipped twice. Discovering the module from the
argument's path instead of `repo_root.txt` would silently render standard-sections-only for every
correctly configured project, and the failure looks like "I never wrote an override".

### 4. The `io` a report gets is a new read-only accessor, not a `StepIO`

§ A report override calls `io` "the same read-only accessor a [`summary` step] gets". **Measured: a
`summary`-scope `StepIO` is not read-only** — it carries `record`, `write`, `append`, `skip` and
`finalize`. Handing one to a renderer would give presentation code the ability to write into a finished
run directory, which is the opposite of what `report` is.

So `report` constructs a **`ReportIO`**: four members, exactly the read half a `summary` step has —
`conditions`, `repeats`, `read_condition(condition, step, name, repeat=None)`, `read_input(relpath)`.
Same signatures, same refusals, same containment check on `name`, so the documented pattern
`for condition in io.conditions: io.read_condition(condition, ...)` is byte-identical in an override and
in a `summary` step.

**Everything it needs is reconstructible from the record, and none of it is guessed.** `conditions` is
`[(index, label)]` read off `results.conditions`; `repeats` off the same record's repeat labels;
`step_scopes` from `execution`'s three-way nesting — `shared` → `run`, `summary` → `summary`, a step
under `conditions[].steps` with repeat-label sub-keys → `repeat`, without them → `condition` — which is
the identical derivation `lineage.resolve_step` already performs over the same block. `run_dir` is the
argument's parent; `input_dir` is `config.data.input_dir` from the embedded config.

**How `ReportIO` relates to `StepIO` is a shared-helper question, not a subclassing one.**
`ReportIO` does not subclass `StepIO` (that would inherit the write half it exists to withhold) and
`StepIO` does not subclass `ReportIO`. The four bodies are shared by extracting the read half of
`read_condition`/`_nest_repeat` into module-level functions in `artifacts.py` that both call, so a
change to the artifact-tree layout cannot move for a step and hold still for a report.

**§ A report override's sentence changes**, from "the same read-only accessor a `summary` step gets" to
naming the four members and saying they are the read half of one. That is the document changing first,
per `CLAUDE.md`, rather than the code being bent to a sentence that was never true of `StepIO`.

**Cost if wrong.** Handing over a real `StepIO` lets a figure write into a completed run directory, and
the append-only guarantee stops being structural. Building a *narrower* surface than four members breaks
the documented `read_condition` pattern an override needs to reach any condition's artifacts, which is
the entire point of the override.

### 5. The four standard sections, and exactly what each reads

In order, and the order is `BaseReport.sections`'s:

| # | Section | Reads | Needs a real `run`? |
|---|---|---|---|
| 1 | **Conditions** | `results.conditions[]` — `index`, `label`, `values`, `is_baseline`; `aggregated[step][metric]`'s `value`, `ci95`, `method`, `n`; and `aggregated[step].by[attribute][level][metric]` when `statistics.report_by` was declared | No |
| 2 | **Deltas** | `results.conditions[].vs_baseline[step][metric]` **and top-level `results.contrasts`** — `delta`, `method`, `paired`, `ci95`, `ci95_corrected`, `correction`, `correction_level`, `family_size`, `family`, and whichever of `n_paired` / `n_of`+`n_against` / `n_paired_clusters` / `n_paired_effective` / `weighted_by` / `cohens_d` / `cohens_ds` / `p_value` / `p_value_corrected` the entry carries | No |
| 3 | **Hypothesis verdicts** | `results.hypotheses[]` — `id`, `kind`, `declared_in`, `observed`, `verdict_evaluated_on`, `supported`, `verdict_rests_on` | No |
| 4 | **Attrition** | `provenance.units.n`, each metric's own `n: {resolved, completed, ineligible, failed}`, `execution`'s per-execution `status`, top-level `status`, and `provenance.input_manifest_changed` | No |

**All four are pure functions of `run.yaml`.** That is the cost argument for the whole slice and it was
checked rather than assumed: every field above was read out of a real record in this pass. So the four
standard sections are testable from a **fixture record**, and a real `run` is needed only to *produce*
one cheaply and honestly. The one thing that needs the run **directory** rather than the record is an
**override**, through `ReportIO.read_condition` — which is Decision 4's surface, not a standard
section's. Two consequences worth stating:

- **A standard section never opens a file under the run directory.** So `report` renders a record handed
  over on its own, with no directory beside it — which is exactly the case `report <study.yaml>` is,
  every time.
- **`by` is not a metric name, and the Conditions section must exclude it — from `stats.RESERVED_METRIC_NAMES`, never from a literal.** `aggregated[step]` holds the strata block under the key `by`, **as a sibling of the metric names**, so a section that iterated that mapping's keys as metrics would render a strata block as a metric with no value. This is not a new hazard: S4d filed it (*"New reserved metric name: `by`"*) after `cli._compute_one_contrast` differenced `by` as though it were a metric, and `_comparison_step_blocks` already excludes it unconditionally at that choke point. **`report` is the next consumer of the same mapping and inherits the same obligation**, which is why it is stated here rather than discovered: the filing's own opening sentence is "every consumer of a step block reads its keys as metric names." Measured in this pass, twice, that the collision is live on the write side too: a template `aggregate` returning a key named `by` produces a record whose `aggregated[step]` holds `pred` and `by`-the-strata-block with `report_by` declared, and `pred` alone with it undeclared — the derived metric is gone either way, contained by `cli.py`'s retry exactly as the filing describes, against a control (`derived_r`) that appears. So the record `report` reads can never hold a *metric* called `by`, and the exclusion is a correctness requirement rather than a defensive one (M13).
- **Section 2 must read `results.contrasts` as well as `vs_baseline`.** Measured: `command_run` splits
  `resolve_contrasts`'s output, sending undeclared comparisons to each condition's `vs_baseline` and
  declared `statistics.contrasts` entries to a **top-level `results.contrasts`**. A deltas section that
  read only `vs_baseline` would silently omit every declared contrast, and § The two files' `run.yaml`
  example — which shows `vs_baseline` and no `contrasts` — is precisely the reading that produces that
  bug. This is the seam Fixture D exists for.

**Cost if wrong.** Omitting `results.contrasts` drops named comparisons from a paper's report while
reporting success — the silent-no-op class. Making a standard section depend on the run directory makes
`report study.yaml` structurally impossible, since a bundle has no directories.

### 6. `report` of a `partial` run **exits 0**, and this is the same ruling `diff`'s exit code already leans on

§ Exit codes and diagnostics is explicit and is the one exit code it disambiguates for `report`: "`report`
of a `partial` run exits `0` — it was asked to render a record and it rendered one, with the failures
shown. A reader learns the run was partial from the report, which is where that belongs, not from the
exit code of the command that printed it."

So: **any status renders at 0** — `completed`, `partial`, `failed` alike — with the status printed in the
Attrition section and the failed executions enumerated there. `3` and `4` belong to the commands that
execute, which § Exit codes says in those rows' own text ("`run`, `draft`, `resume` only").

**Consistency with H8b, stated rather than assumed.** `diff`'s Decision 4 ruled **0 whenever it rendered
a comparison**, and `CLAUDE.md` records that ruling as having leaned on this `report` row as its
precedent. The two now agree in both directions and for one reason: **a read command's exit code reports
whether it could read, never what it read.** Anything else makes a script that keys on `1` unable to tell
"your record says the run was partial" from "I could not read your record". `report` exits `1` only for
its own refusals (Decision 15) and `2` only for an invocation fault.

**Cost if wrong.** Exiting `3` on a partial record would put `report` in the class of commands that
execute, and a pipeline that archives on `3` would archive the *report* rather than the run.

### 7. `report` refuses to render a **draft** as a final result — a refusal, and it is reachable today

§ Draft runs: "Draft runs are recorded with `draft: true` and `git.code_dirty: true`, `report` refuses to
render one as a final result, and `diff` labels it." So `report` on a record whose `draft` is `true` is
`E-REPORT-DRAFT` at exit `1`, and renders nothing.

**Two things about the shape of that refusal.**

- **It is a refusal, not a watermark.** The document's verb is "refuses". A report that rendered a draft
  with a banner would be citable, and "you just can't accidentally cite one" is the sentence the whole
  `draft`-versus-`--allow-dirty` argument rests on.
- **It is testable today and reachable only later.** `draft: true` is a **shipped** key — measured,
  `draft: false` is written by `run` on every record — while the `draft` *command* is `NOT BUILT` and is
  H9's. So H8c builds and pins the behaviour from a fixture with the key flipped, and H9 makes it
  reachable through a real command. This is the *"an unbuilt reader of a shipped surface is a defect; of
  an unbuilt surface is specification"* line, on the shipped side. The fixture's provenance is stated in
  its docstring rather than left to look like a real draft.

**`report <study.yaml>` does not refuse; it flags.** § Building one says the bundle render "flag[s] any
draft runs" — a bundle is a set, and refusing the whole render because one of five runs was a draft would
throw away four legitimate renders. So a bundle's per-run block is rendered with a `draft` label, and the
bundle-level exit stays `0`. The asymmetry is the same one `code.commit` has: a single run is one claim,
a bundle is a set of them.

**Cost if wrong.** Rendering a draft makes an uncitable run citable, which is the one thing § Draft runs
promises against. Refusing a whole bundle for one draft member makes the flag pointless.

### 8. `report study.yaml`'s two cross-checks compare **recorded figures**, and compute neither

The bundle render cross-checks two things, per § Building one: that runs claiming the same code really
share a `code_hash`, "and the same for `provenance.apparatus.hash`, since 'these runs used one
deployment' is a claim a paper makes and a bundle can check".

**Both are string comparisons over what the records already hold.** `report` calls neither
`hashes.code_hash` nor `apparatus.apparatus_hash`.

- **`code_hash`**: recomputing it is impossible offline anyway — it covers `src/**` and `templates/**` of
  a repo the bundle deliberately does not carry. `reproduce` sets the precedent in words: "It cannot
  verify a `code_hash` and says so, rather than reporting a match it never made."
- **`apparatus.hash`**: recomputing it *is* arithmetically possible from a record's own `facts`, and it
  is **still refused**. `apparatus_hash`'s own docstring states that a reader must re-canonicalize the
  parsed mapping with exactly its `json.dumps` arguments, and `diff`'s Decision 2 already ruled that the
  `apparatus` row's verdict compares `provenance.apparatus.hash` and "must not be able to disagree with
  the one figure this project treats as authoritative". `report` computing a second answer would create
  exactly that disagreement, in the artifact a paper cites. **The apparatus is explicitly not a fourth
  hash** — it sits beside `uv_lock_hash` as an environment fingerprint — and a fingerprint that two core
  commands can disagree about is worse than none.

**What "claiming the same code" means, precisely.** Two bundled runs whose `provenance.git.commit`
agree. Those runs' `code_hash` values must then agree too — same commit, same two trees — and when they
do not, that is a real finding about the bundle and is reported as a **notice** at exit `0`, not a
refusal. **The notice says what was found and does not diagnose why** — "these runs record commit `X`
and their `code_hash` differs" is checkable from the two records; "one of them was a dirty tree" is a
guess, and a dirty tree is only one of the candidates (an uncommitted `templates/**` edit is another,
and `code_hash` covers the two **trees**, so another experiment's package moving inside them is a
third — `CLAUDE.md`'s invariant names that last case precisely because people expect tree-scoping to be
per-experiment and it is not). A notice that stated a cause as fact would be the
comment-claiming-a-guarantee habit one layer out: `report` reads, and the author is the one who decides whether the paper's
claim survives. The apparatus check is the same shape one column over — runs sharing a commit whose
`apparatus.hash` differs measured through two deployments — and a run whose `provenance.apparatus` is
`null` is **excluded from that check rather than counted as a mismatch**, because "this experiment
declares no probe" is not a deployment claim. (`diff` makes the opposite call for a one-sided `null`,
and correctly: `diff` compares two runs and a fact one answered and the other did not is a real
difference between them. `report` is testing whether a *group* of runs makes one deployment claim, and a
run making no such claim is not a counter-example to it. The two commands ask different questions —
which is the same distinction `reference.md` § The apparatus core can only observe now records for
`diff` versus the run-time gate.)

**Cost if wrong.** A recomputed `apparatus.hash` that disagrees with the recorded one turns the
bundle-level check into a bug report about core. Refusing on a `null` apparatus makes every bundle of
`generic` runs — the whole worked example — print a mismatch notice for a deployment nobody claimed.

### 9. `study new` creates an empty bundle, outside any repo, and refuses an existing one

`publishable study new <bundle> --title "..."` writes `<bundle>/study.yaml` with `title`, `authors: []`
and `runs: {}` — and **no `code` block**, because `code.commit` is a specific run's and there is no run
yet (Decision 11). It is a **creation command**, so the `--title` argument is legitimate: creation
commands take what is needed to bring something into existence.

- **Outside any repo.** § Why not in the repo gives three arguments and they are structural, so the check
  is too: a bundle path resolving inside a git repo is `E-STUDY-IN-REPO`, the same walk-up
  `input_dir`/`output_dir` already use. The route is in the message — put it where the manuscript lives.
- **Refuses an existing bundle**, `E-STUDY-EXISTS` at exit `1`, joining the family § Exit codes already
  defines (`E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`, `E-STEP-EXISTS`, `E-TEMPLATE-EXISTS`) and matching
  `scaffold.py`'s shipped shape: refusing is how a creation command stays safe to re-run. "Existing"
  means *a `study.yaml` is already there* — not that the directory exists, since `~/papers/x/study` next
  to a manuscript is a directory a person may well have made first.

**Cost if wrong.** Overwriting a bundle destroys a manuscript's supplementary material, and the
append-only rule this repo applies everywhere else would have one exception in the one place that is
beside a paper.

### 10. `study add` copies the record and replaces four fields with a marker that distinguishes *redacted* from *never captured*

`publishable study add <bundle> <run.yaml> --as <name>` copies the record to
`<bundle>/<name>.run.yaml`, adds `runs.<name>: {file, run_id}` to `study.yaml`, and replaces each field
in § What `study add` redacts' table with a marker.

**The marker is a string that says which of two things happened.** § What `study add` redacts requires
"a marker recording that a value existed and was removed, so a reader can distinguish 'redacted' from
'never captured'". So: a field present in the source record becomes the literal
`"<redacted by study add>"`; a field **absent or `null`** in the source record is **left exactly as it
was**, absent or `null`. The distinction is carried by the two states themselves rather than by two
marker strings, because "never captured" is already spelled unambiguously in this format and has been
since `apparatus: null` — minting a second marker for it would give one fact two spellings.

**The table is four rows, not five, at this commit.** § What `study add` redacts names
`data.input_dir`, `data.output_dir`, `provenance.git.repo_root`, `provenance.environment.hostname`, and
`provenance.input_manifest`. Measured: **`hostname` is never written** (`provenance.environment` is
`{manager, python_version, uv_lock, uv_lock_hash}`), and it is **H6's**. So four rows are exercisable
against a real record and `hostname`'s rule is testable only over a **synthesized** record — which the
fixture's docstring says in those words, rather than presenting a hand-built record as a real one.
The rule itself needs no special case: `hostname` absent today is the "never captured" branch, and it
becomes the "redacted" branch on the day H6 writes it, with no code change.

**Every hash stays.** `input_manifest_hash` survives while `input_manifest`'s path does not, so a holder
of the data can still verify it without the record disclosing where it lives. `parameters_hash` never
covered the path fields and `code_hash` covers only the two trees, so redaction disturbs no
verification — which is § What `study add` redacts' own closing argument and is the reason the redaction
can be this blunt.

**Redaction here is not `secrets.redact`.** That function matches credential *values* by substring
anywhere in a string, for exception text. This is field replacement at four known paths. Naming the
distinction because the two words are the same and the mechanisms share nothing.

**Nothing is redacted from `provenance.apparatus`, by design.** § The apparatus core can only observe
makes a probe emit non-identifying facts precisely so that this table has no apparatus row. The design
records that as an inherited property rather than re-deriving it.

**Cost if wrong.** One marker string for both states destroys the distinction the section exists to
create. Redacting a hash alongside its path makes a bundled record unverifiable by the one reader — a
data holder — it was meant to serve.

### 11. `code.commit` names **one run's** commit: the one added `--as main`, else the first added

Written on the **first** `study add`, from that run's `provenance.git.commit`, along with
`code.remote` from `provenance.git.remote`. A later `study add --as main` **replaces** it; a later add
under any other name does not.

**Grounds, and they are the section's own.** "`code.commit` is one commit and a study's runs need not
share one, so it names a specific run's… `code` is the citable pointer a reader follows from the paper,
not a claim that every run came from it." Each bundled record still carries its own
`provenance.git.commit` and `code_hash`, which is where a per-run answer lives.

**A commit mismatch is a notice, not a refusal.** "A sensitivity analysis rerun a month later at a later
commit is ordinary, so `study add` prints a notice when a run's commit differs from `code.commit` rather
than refusing." Exit stays `0`. The notice names both commits and which run each belongs to, so the
author can decide whether the paper's citable pointer is still the right one.

**`code.remote` is `null` when the run's own is.** A run from a repo with no remote records none, and a
bundle inventing one would be a claim about where code lives that nobody made.

**Cost if wrong.** Refusing a differing commit makes the ordinary sensitivity-analysis workflow
impossible. Recomputing `code.commit` as "the commit all runs share" gives a bundle whose runs
legitimately differ no citable pointer at all.

### 12. `study add` **refuses** a name already in the bundle

`E-STUDY-NAME-EXISTS`, exit `1`, and this is the load-bearing refusal of the whole command. § Building
one: "what it refuses is a **name already in the bundle**, since `main.run.yaml` silently becoming a
different run is exactly the overwrite [append-only] forbids, and a bundle beside a manuscript is the
last place to allow it. Re-add under a new name, or start a new bundle." Both routes go in the message.

**The name is checked against `study.yaml`'s `runs` keys *and* against the file on disk**, and either
being present refuses. Two checks rather than one because they can disagree — a hand-edited
`study.yaml`, or a copy interrupted between the two writes — and the *file* is the thing whose overwrite
loses data.

**Adding the same `run_id` twice under two names is permitted.** The refusal is about the name, and a
paper legitimately reports one run in two roles. Nothing in the section forbids it, and inventing a
second refusal would be core deciding what a paper may say.

**Cost if wrong.** A silent overwrite loses a run record from a manuscript's supplementary material,
and the loss is invisible because the file name is unchanged.

### 13. The `min_reported_n` prompt walks the **record**, not a list of shapes — and one of the three branches is unreachable in any record this build writes

`study add` "prints any reported metric whose `n.completed` falls below `limits.min_reported_n` — or, for
a `basis: repeats` metric, its repeat count, and for a reported `Estimate` the `n` it declared — and asks
you to confirm". An `Estimate` that declared no `n` is listed too.

**The implementation iterates the record's actual entries and keys each on what that entry carries**,
rather than iterating three shapes and looking each up:

| Entry carries | Figure compared | Producible today? |
|---|---|---|
| `basis: "units"` | `n.completed` | **Yes** — measured in r3, `aggregated`, `by` strata, and `vs_baseline` alike |
| `reported: true` | the declared `n`; **listed unconditionally when `n` is `null`** | **Yes** — measured in r3's `results.summary` |
| `basis: "repeats"` | the repeat count | **No. Nothing in this build writes this shape** |

**The third branch ships behind a synthesized fixture, and this design says so rather than letting it
pass as covered.** Measured at `9963841`: `grep -n '"basis"'` over `src/publishable/` returns five sites
and every one writes `"units"`; a step-returned scalar reaches `per_repeat` and no `aggregated` entry at
all (r3, with a unit table present), and a run with `data.units` undeclared writes **no `aggregated` key
whatsoever** (r4). So `reference.md`'s five present-tense passages asserting that such a metric "says
`basis: repeats`, reports the spread, and omits `ci95`" describe a shape core does not produce, and the
**shipped** `W-HYPOTHESIS-INFERENCE-BASE` names it in its own message.

That is a defect, it is **filed** (§ The filings this slice makes), and it is **not H8c's to close** —
writing a metric into `aggregated` is `run`'s work, and nothing in H8c may alter a run. What H8c owes is
a ruling, and the ruling is: **build the branch, from the document, and pin it on a record synthesized
by hand whose docstring says it was.** The alternative — omit the branch until a producer exists — would
ship a prompt that silently under-reports the day the producer lands, in the command whose entire job is
to catch a disclosure nobody else will.

**What the prompt is, and what it may never be.** It prints the offending metrics and asks
proceed-or-quit. Nothing else. `design-principles.md` § Everything is in the file: "every one of those
prompts is proceed-or-quit: **a pause may never alter the config**… Pausing changes what a person sees,
never what executes." Here there is no config and nothing executes, and the same rule binds one step
further: **quitting writes nothing** — not a partial copy, not a `study.yaml` entry — and proceeding
writes exactly what a bundle with no thin metric would have written. The prompt changes no bytes either
way. With no TTY it does not silently proceed: `study add` prints the list and refuses,
`E-STUDY-CONFIRM-REQUIRED`, because an unattended `study add` that proceeded past a disclosure warning
is the automation this prompt exists to prevent.

**`limits.min_reported_n` is read from the bundled record's own embedded config**, never from a config in
the working directory, because the limit is a property of the run being bundled.

**Cost if wrong.** Iterating shapes instead of entries silently skips whatever the record actually holds
— including `by` strata and `vs_baseline`, which is where the disclosure risk is highest. Shipping the
`basis: repeats` branch without the filing gives the prompt a reader for a shape core never writes, with
nobody knowing. Proceeding without a TTY turns a judgment prompt into a no-op.

### 14. **Ruling: a bundle never carries `allocation.json`**

§ What `study add` redacts leaves this open in writing "for whichever slice builds `study.py`". This is
that slice, and the ruling is: **`allocation.json` never enters a bundle, and no option is added to put
it there.**

**Grounds, in the order they bind.**

1. **The shape § Building one already commits to decides it.** `study add` takes a run's `run.yaml`
   **path**, not a run directory, and the fenced bundle tree shows `study.yaml` plus one `*.run.yaml` per
   run. `allocation.json` is a run-*directory* artifact and is not reachable from the argument the
   command takes. Admitting it would mean `study add` reading a sibling of its own argument — quietly
   turning a record-copying command into a directory-copying one.
2. **It is the one run artifact that is a list of unit identities** — "which patients were in the
   treatment arm". § What `study add` redacts' table redacts *host* identity and has never named
   participant identity, because on the shape above there is nothing of it in a bundle to scrub. Adding
   the file would create the gap, then require a redaction rule to close it, in the artifact most likely
   to be deposited publicly.
3. **The hash is already in the bundle and discloses nothing.** `provenance.allocation` is a bare
   filename and `provenance.allocation_hash` a digest — measured, both written whenever an arm
   assignment or holdout resolves, `null`/`null` together otherwise. So a bundle already carries a
   *commitment* to the split without carrying the split.
4. **The route for the reader who wants to verify the split, named rather than left implicit.** They
   need `allocation.json` itself, and it is one file the author can attach as supplementary material
   beside the bundle, or hand over with the run directory. `allocation_hash` is what makes that transfer
   checkable: a reader who holds both can prove the file is the one the run used. That is exactly the
   posture § What `study add` redacts already takes for `input_manifest` — the hash travels, the thing
   it covers does not, and verification stays available to whoever legitimately holds the data.

**§ What `study add` redacts changes**: the paragraph's closing "is a question this slice leaves open for
whichever slice builds `study.py`" is replaced by the ruling and reason 4's route. The paragraph's
hedge — "`study add` is not yet built, so what follows is a reading of the shape § Building one already
commits to, not a checked fact" — comes out with it, since the fact is now checked.

**Cost if wrong.** If a bundle should have been able to carry the split, an author who needs to ship one
ships two artifacts instead of one, and the bundle is still self-contained for every claim it makes. The
reverse error is not recoverable: a bundle carrying unit identities has been deposited, and no later
version of `study add` un-publishes it.

### 15. Codes, and where each is documented

New codes, all in the one namespace, each with a **row per code** in
§ Errors `validate` reports — which is where H8b put every `E-FREEZE-*` and `E-DIFF-CONFIG-UNREADABLE`,
establishing that the table is the registry rather than a `validate`-only list. Codes raised through a
`ContractError` a *step* could see would go in § Errors core raises instead; none of these can, because
no step runs.

| Code | Fires when | Exit |
|---|---|---|
| `E-REPORT-FORM` | the argument is named neither `run.yaml` nor `study.yaml`, or is a directory | `1` |
| `E-REPORT-DRAFT` | the record's `draft` is `true` (Decision 7) | `1` |
| `E-REPORT-FORMAT` | the resolved report class declares no `format` (Decision 2) | `1` |
| `E-REPORT-OVERRIDE-IMPORT` | `<pkg>.report` exists and raises on import (Decision 3) | `1` |
| `E-REPORT-OVERRIDE-CLASS` | `<pkg>.report` defines no `BaseReport` subclass, or more than one | `1` |
| `E-STUDY-UNREADABLE` | a `study.yaml` is absent, unparseable, not a mapping, or names a `runs` entry whose `file` is not in the bundle | `1` |
| `E-STUDY-IN-REPO` | a bundle path resolves inside a git repo (Decision 9) | `1` |
| `E-STUDY-EXISTS` | `study new` onto a path already holding a `study.yaml` | `1` |
| `E-STUDY-NAME-EXISTS` | `study add --as <name>` where the name or its file is already in the bundle (Decision 12) | `1` |
| `E-STUDY-CONFIRM-REQUIRED` | the `min_reported_n` prompt has no TTY to ask (Decision 13) | `1` |
| `E-REPORT-EXISTS` | `generate report` onto a path already holding `src/<pkg>/report.py` (Decision 17) | `1` |
| `W-STUDY-COMMIT-MISMATCH` | a run's commit differs from `code.commit` (Decision 11) — a notice, exit unchanged | `0` |

**`E-STUDY-EXISTS` and `E-REPORT-EXISTS` also join a sentence, not just a table.** § Exit codes'
creation-command paragraph enumerates that family **by hand** — `E-PROJECT-EXISTS`,
`E-EXPERIMENT-EXISTS`, `E-STEP-EXISTS`, `E-TEMPLATE-EXISTS` — under the claim that it is "one rule
shared by every generator with something to protect." Two new members make that enumeration incomplete,
which is the *count phrase near an insertion* trap in its normative form: the sentence is wrong the
moment the codes exist and no table check would catch it. Both go in, and the sentence's own claim
is what makes them belong there rather than a judgement call.

A run record `report` cannot read is **not** a new code: `lineage.read_run_record` already raises
`E-UPSTREAM-RECORD-MISSING` / `-UNREADABLE` / `-VERSION`, and § Errors core raises' row for them already
names `diff`'s operand as a second caller. `report` and `study add` become the third and fourth, and the
row's wording widens rather than three codes being reminted. A missing operand path stays `E-IO-FAILED`
at exit `1`, as § Exit codes already specifies for "a local filesystem failure".

**Cost if wrong.** Minting a fourth spelling of "this record will not read" is H4d's one-code-for-five-
faults shape run backwards, and a reader greps for a code that does not exist.

### 16. Two renderers, one section stream

`Section` values are rendered by a markdown renderer and an HTML renderer, selected by the report
class's `format`. Both consume the **same** generator: a section's `body` is markdown text or a mapping
core tables, and the renderers differ only in how they emit a heading, a table and a block. There is no
third representation and no template language.

**`generate report`'s `--format` writes the attribute and nothing else** — "the class is the source of
truth from then on, exactly as `--input-dir` seeds a config field it doesn't afterwards own". So `report`
never takes a format argument: an operation command takes paths and nothing else, and a `--format` on
`report` would be the behaviour-changing flag § Everything is in the file forbids. The medium is a
property of the experiment's own committed code, under `code_hash`.

**HTML is self-contained and offline.** A bundle render is explicitly offline ("`publishable report
study.yaml` renders it offline"), so the HTML carries no external stylesheet, script or font, and an
override that embeds a figure embeds it.

**Cost if wrong.** A `--format` flag on `report` breaks the operation-command invariant in the most
visible place. An HTML render that fetches anything makes an archived report degrade.

### 17. `generate report`, claimed here because nothing else claims it

`publishable g report <experiment> [--format html|markdown]` writes `src/<pkg>/report.py` — the class
§ A report override shows, with the `format` line seeded. It leaves `NOT_BUILT_GENERATORS` and its
§ Generators row flips to `built`.

**Grounds.** It is in nobody's charter: it is in `NOT_BUILT_GENERATORS`, § Generators marks it NOT
BUILT, and it is not in H9's list. It writes the class `BaseReport` exists to be subclassed from, so the
alternative is shipping a base class with no writer. It refuses an existing `src/<pkg>/report.py`,
`E-REPORT-EXISTS`, joining the same `E-*-EXISTS` family for the same reason as Decision 9.

**The scaffolded body must be runnable as-is**, on `generate step`'s and the starter step's precedent: it
`yield from super().sections(run, io)` and yields nothing else, with a `TODO` marking the one place a
figure goes. A generated override that raised, or that rendered *fewer* sections than no override at
all, would make `generate report` a downgrade.

**Cost if wrong.** If a later reader charters `generate report` elsewhere, H8c drops one task and
`BaseReport` ships with no way to obtain a subclass except by hand — which is survivable but is a worse
first experience than the one § A report override describes.

### 18. Module homes: `report.py` and `study.py`, both already named by § Package layout

Unlike `diff` and `freeze` — which H8b had to find homes for, § Package layout naming neither — both of
H8c's modules are already in the tree block with `— not yet built` markers, glossed exactly as this
slice builds them: `report.py` "BaseReport: standard sections, html/markdown, override discovery" and
`study.py` "study new/add: bundle assembly, redaction, cross-run report". Both markers come off. No new
module is added and no gloss is rewritten, which is the cheapest possible outcome and worth noting
because H8b's was not.

`ReportIO` lives in **`artifacts.py`**, beside the `StepIO` whose read half it shares (Decision 4), not
in `report.py`: § Package layout's `artifacts.py` is where the `io` surface lives, and splitting one
artifact-tree traversal across two modules is how the two drift. `report.py` imports it.

**Cost if wrong.** A second traversal of the artifact tree means a layout change fixed for steps and
broken for reports, with the two answers computed from different code.

### 19. `report` **can** make the correction family visible, and does — in one line per family

§ Invariants warns that "every metric a template's `aggregate` returns is comparisons × metrics, so a
template returning twenty diagnostics corrects every interval in the run for numbers nobody reads". The
question this design owes is whether `report` can surface that. It can, and cheaply: every
`vs_baseline` and `results.contrasts` entry already records `family_size` and
`family: {comparisons, metrics}` — measured on r3, `family_size: 1, family: {comparisons: 1,
metrics: 1}`. So the **Deltas** section prints the family's size and its two factors **once per family**,
beside the corrected intervals it explains.

That is what makes the trap visible: a run whose family reads `{comparisons: 2, metrics: 20}` prints
`family_size: 40` next to intervals a reader can see are wider than they need to be, and the cause is
named in the same line. Nothing is computed to do it — the figures are recorded — and nothing warns:
`report` reads. **`validate`'s `W-STATS-FAMILY` is the warning for this**, before the run, which is
where a warning belongs; `report` is where the consequence becomes legible after it.

**Cost if wrong.** Omitting it costs nothing structurally and loses the one place a reader of a finished
run can see why every interval widened.

### 20. The three worked `diff` blocks each gain a header at that block's own level of concreteness

The measured format, re-taken through the real console script at `9963841` against two run directories
this pass produced:

```
A  run record  run_2026-08-21T07-28-48Z_436cab2  completed
B  run record  run_2026-08-21T07-29-19Z_49f2765  completed
```

Two-space column separators; the letter, the form, then a run record's `run_id` and `status`, with the
word `draft` appended when `draft: true`; a config side shows the form and the path **as given, never
resolved**, and no status word.

Each of the three blocks gets two header lines matching **its own** abstraction, which is why this is
three edits and not one:

| Block | Header, at that block's concreteness |
|---|---|
| `reference.md` § The apparatus core can only observe | the worked example's real run IDs, `run_2026-08-06T14-02-11Z_8e21ab3` and `run_2026-08-07T09-14-03Z_8e21ab3`, each `completed` — and `completed` beside `apparatus DIFFERS` is the pairing worth showing rather than leaving a reader to wonder: an apparatus that moved between two *finished* runs is exactly what that block is about |
| `README.md` § The loop you'll actually live in | its own `~/results/cohort-pilot/run_A` and `run_B` level — the header's identity column carries `run_A` / `run_B` |
| `design-principles.md` § Same code, different parameters | its `<run_a>` / `<run_b>` placeholders, unchanged in kind |

**What must not change**, and this list is the filing's own: no hash prefix (`8e21`, `3d8a`, `6b1f`,
`1a2b`), no run ID, no delta line, no row label, no row order, and the two-space separator stays. § The
worked example's intervals are numerically checked and are not touched by this edit at all — the `diff`
blocks carry hashes and deltas, not intervals — which is stated so that a later reader does not go
looking for a narrowing that never happened.

**Both consistency passes run**, since three fenced blocks in three of the four documents move together
and the cross-document class this touches is the shared worked example.

**Cost if wrong.** Three normative documents keep showing output the command does not produce, and a
wrong worked example is self-propagating in a way a filed defect is not.

### 21. Nothing in H8c stops or alters a run, and it follows from what each command opens

Stated with the care H7d Part B and H8b used, because it is the property the whole slice rests on.

- **`report` opens nothing for writing.** Every standard section is a pure function of the parsed record
  (Decision 5); the only file `report` may open under a run directory is through
  `ReportIO.read_condition` / `read_input`, and `ReportIO` has no write member to call (Decision 4). It
  takes no lock, so it is safe against a run holding its own — and unlike `freeze` it does not need to
  be, since it has nothing to append.
- **`study add` writes only inside the bundle**, and the bundle is refused inside any repo and is by
  construction outside every `output_dir` too. It reads the source `run.yaml` and never its directory
  (Decision 14, reason 1).
- **No probe runs.** `report` and `study` are not among the four phases a probe executes at, so neither
  spends quota against anybody's meter, and neither appends to `apparatus/probes.jsonl`. `freeze` is
  H8's one command that probes, and it shipped in H8b.

**Cost if wrong.** A `report` that wrote into a run directory would break append-only for the artifact a
paper cites, and would do it while a run was still executing.
---

## Refusals, each with its route

| Refused | Route |
|---|---|
| `report --format html` — any flag on an operation command | The medium is `BaseReport.format` in your repo's own `src/<pkg>/report.py`; `generate report --format` seeds it (Decision 16) |
| `report <a run directory>` | Pass its `run.yaml` (Decision 1) |
| `report` of a **draft** run | `publishable run` a committed tree, or read the record directly; a draft is deliberately not citable (Decision 7) |
| An override that changes a figure | Impossible by construction — the standard sections are finished `Section` values. A different number is a different `aggregate`, or a `summary`-step `Estimate` (Decision 2) |
| An override on a **bundle** render | An override is one experiment's presentation under one commit; render each run in its own repo, or ship the figure beside the bundle (Decision 3) |
| Two `BaseReport` subclasses in one `report.py` | One project, one report — delete one or import the other from a plugin, which is the documented route for a renderer several experiments share (Decision 3) |
| `report` recomputing `code_hash` or `apparatus.hash` | It compares recorded figures; a recomputation is `publishable diff`'s and `reproduce`'s business, against a tree that exists (Decision 8) |
| A `study` bundle inside a git repo | Put it where the manuscript lives (Decision 9) |
| `study add --as main` twice | Re-add under a new name, or start a new bundle (Decision 12) |
| A commit differing from `code.commit` | **Not refused** — a notice. Each record carries its own commit; re-add `--as main` to move the citable pointer (Decision 11) |
| `study add` with a thin metric and no TTY | Run it attended, or raise `limits.min_reported_n` in the config **before the run** — a bundled record's limit is the run's own (Decision 13) |
| `allocation.json` in a bundle | Ship it as separate supplementary material; `provenance.allocation_hash` in the bundle is what makes that transfer checkable (Decision 14) |
| Anything that would stop or alter a run | Not reachable: `report` and `study` open no run directory for writing and take no lock. `report` reads a record; `study add` writes only inside the bundle (Decision 21 below) |

### Out of scope, with the route for each

**H9 owns `reproduce`, `dry-run`, `draft`, `resume`, `demo`, `docs`.** Named individually so none is
folded in:

| Not H8c's | Route |
|---|---|
| `publishable draft` — making a `draft: true` record producible | **H9** (§ Draft runs). H8c pins the refusal from a fixture with the shipped key flipped; H9 makes it reachable |
| `apparatus.expected.json` | **H9**, `reproduce` step 5 (§ Reproducing on another device); `H7-SCOPING.md` § 10 routes it there and nothing routes it to H8 |
| `reproduce` following paper → study → repo state | **H9**. H8c's contribution is that `code.commit` is in the bundle for it to follow (Decision 11) |
| `publishable docs` regenerating managed regions | **H9**. No `publishable:begin/end` region holds report output |
| `list-templates` | **H9**'s list, still `NOT BUILT` |
| `provenance.environment.hostname` being written | **H6**. H8c redacts a field H6 writes, so that one row is testable only against a synthesized record (Decision 10) |
| A metric with `basis: repeats` ever existing | **Filed, owner named below.** H8c builds the prompt's branch for it and cannot write the metric (Decision 13) |
| `execution.*.nondeterministic` being written | **Filed, owner named below.** Nothing in H8c may alter a run, so no section may claim the field |
| `report_by` under `resample` keeping a `t_over_units` interval | **H4 Statistics**, filed, live on C1–C3. `report` renders what the record holds |
| `max_failed_fraction`'s truncation status | **Unassigned**, filed by H7d Part B; a `run` semantics question no H8 command reaches |
| `BaseTemplate.field_convention` | **Unassigned**; still the shape's live example, and not a report concern |

---

## The discriminating fixtures

**A fixture is a claim too.** Every literal below is **computed by the fixture** from the record it was
produced from, never typed from memory, and each entry says which. Where a record is hand-built, the
fixture's own docstring says so in those words.

### Fixture R — one real completed run, the base record

`run_a_project`: a scaffolded project, a 24-row synthetic index, a declared `baseline` plus a one-axis
`grid` (2 conditions), 3 `seed` repeats, `statistics.report_by: [cohort]`, one declared hypothesis, a
starter step that records a numeric `score` column and calls `io.skip` on a known subset, and a
`summary`-scoped step returning an `Estimate` with `ci95` and **no `n`**. Produced in this pass: it
yields `aggregated` with `n: {resolved: 24, completed: 21, ineligible: 3, failed: 0}`, a `by.cohort`
block with two levels, a `vs_baseline` entry carrying `family_size`/`family`, `results.hypotheses` with
one verdict, and `results.summary` with a reported `Estimate` whose `n` is `null`. **Every figure the
report prints for it is read back from the record**, never asserted against a literal.

`run_a_project` is reused rather than reinvented: it is `test_cli.py`'s one end-to-end driver, and H8b's
own fixtures are built on it.

### Fixture D — the declared contrast, which `vs_baseline` cannot reach

Fixture R plus one `statistics.contrasts` entry. The assertion is that the **Deltas** section names it,
read from top-level `results.contrasts`. **Without this fixture, Decision 5's "read both" ships
unpinned**, because Fixture R's every delta is in `vs_baseline` and a section reading only `vs_baseline`
passes the whole suite. This is the fixture sized to distinguish the two readings rather than to exercise
one.

### Fixture P — a partial run, and the failures shown

Fixture R's starter step raising for one condition's units, through `expect_exit=EXIT_PARTIAL`. Two
assertions, because one cannot see it: **exit 0** from `report`, *and* the failed executions present in
the Attrition section by their own condition and repeat labels. Asserting only the exit code passes
identically if the section rendered nothing, which is the *control asserting only absences* shape.

### Fixture T — the draft record, synthesized and labelled as such

Fixture R's record with `draft` flipped to `true` and `provenance.git.code_dirty` with it. The
docstring says the record was hand-edited and why (`publishable draft` is H9's), so nobody later reads it
as a real draft run. Two arms: `report <run.yaml>` → exit 1, `E-REPORT-DRAFT`, **and no rendered
output**; `report <study.yaml>` over a bundle holding it → exit 0 with the run flagged (Decision 7's
asymmetry, which one arm cannot show).

### Fixture O — the override, over **two** packages

A Fixture R project whose `src/` holds **two** packages, each with its own `report.py` yielding a
distinctly-titled extra section, with `entrypoint` naming one of them. The assertion is that the
titled section from the **named** package's report appears and the other's does not. **One package
cannot distinguish an entrypoint-derived answer from a directory scan** — both find the same file — so
this fixture is sized to the two candidate answers Decision 3 rules between. Sibling arms, one project
each: a `report.py` raising on import (`E-REPORT-OVERRIDE-IMPORT`); one defining no subclass and one
defining two (`E-REPORT-OVERRIDE-CLASS`); one whose class declares no `format` (`E-REPORT-FORMAT`); and
a positive control with **no** `report.py`, asserting the four standard sections render and no
diagnostic prints — the control that must report something rather than only an absence.

### Fixture V — the override reaching a condition's artifact

Fixture O's override calling `io.read_condition(condition, step, name)` for a real artifact its own step
wrote. This is the one fixture that needs the run **directory** and not just the record, and it is what
pins that the render happens **inside** the `sys.path` window (Decision 3) and that `ReportIO`'s four
members carry a `summary` step's signatures. Its sibling arm asserts `ReportIO` has **no** `write`,
`record`, `append` or `finalize` member — the withheld half, which the positive arm cannot see.

### Fixture B — a two-run bundle, one pair sharing a commit and one not

Two Fixture R runs from the **same** commit (`study add` prints no notice, the `code_hash` check passes)
and a third from a second commit (`W-STUDY-COMMIT-MISMATCH`, exit still 0). Then a hand-edited fourth
whose `provenance.git.commit` matches the first while its `code_hash` does not — the "claiming the same
code and not sharing a hash" case Decision 8 exists for, unreachable from two honest runs, and its
docstring says the record was edited.

### Fixture A — the apparatus cross-check, and the hand-edited hash

H7d's shape, inherited from H8b's Fixture P: a synthetic installed distribution registering a probe, a
project-local template declaring `apparatus_probe` and `apparatus_facts`, and a probe whose answers come
from a file the test writes. Three arms. Two runs whose facts agree → no notice. Two whose facts differ
under one commit → the deployment notice. And **one record whose recorded `provenance.apparatus.hash`
has been hand-edited to disagree with a recomputation over its own `facts`** — which is the only fixture
on which "compare the recorded string" and "recompute from `facts`" give different answers, and the
docstring says the record was edited to make them differ. A fourth arm holds one run with
`apparatus: null` beside one with a real block, asserting **no** mismatch notice (Decision 8's exclusion
rule), which the other three arms cannot see.

### Fixture N — the three metric shapes, and the one that had to be synthesized

Fixture R already produces two: a `basis: units` entry (in `aggregated`, in a `by` stratum, and in
`vs_baseline`) and a reported `Estimate` with `n: null`, with `limits.min_reported_n` set so that the
`by` strata fall below it and the whole-condition metric does not — so the prompt's list is a **proper
subset** of the record's metrics and a rule that listed everything fails. The **third** shape,
`basis: "repeats"`, is a **hand-written entry in a synthesized record**, and the fixture's docstring
says that nothing in this build writes it, cites the filing, and names the measurement
(`grep -n '"basis"'` → five sites, all `"units"`). A fourth arm holds a reported `Estimate` **with** an
`n` above the floor, asserting it is **not** listed.

### Fixture Y — `study new` and `study add` on disk

A bundle created outside any repo, then two adds. Assertions read the bytes: `study.yaml`'s `title`,
`authors`, `code.remote`/`code.commit`, and `runs.<name>.{file, run_id}`; the copied
`<name>.run.yaml`'s four redacted paths carrying the marker; **`input_manifest_hash` and all three of
`parameters_hash`/`code_hash`/`uv_lock_hash` still present and byte-equal to the source record's**; and
`provenance.environment` carrying no `hostname` key (the "never captured" branch, with the reason in the
docstring). Sibling arms: a bundle path inside a repo (`E-STUDY-IN-REPO`); a second `study new` onto the
same path (`E-STUDY-EXISTS`); a re-add under a used name (`E-STUDY-NAME-EXISTS`, asserting **the file on
disk is unchanged** afterwards, which is the assertion that catches a refusal raised after the copy);
and one run added under two names, asserted to succeed.

### Fixture H — the header edit's own check

The three documents' fenced `diff` blocks, parsed out of the files, compared against `diff`'s **real**
output for a run pair — label set, label order, the two-space separator, and the header's own column
shape. `tests/test_diff.py` already parses row labels out of all three documents; this extends the same
reader to the header lines rather than inventing a second one. The hash prefixes and delta lines are
asserted **unchanged** against the pre-edit text, which is what makes "do not narrow the worked example"
a test rather than an instruction.

---

## The mutations, each with the assertion that catches it, and each with two branches that can differ

**A mutation is a claim too.** For each, the two branches were checked to be able to produce different
results on the named fixture — the failure mode recent slices produced repeatedly (a mutation that was
what the code already did, a mutation whose branches were identical, one placed a line off, one that
fired for the wrong reason, one applied to a proxy).

| # | Mutation | Caught by | Why the branches can differ |
|---|---|---|---|
| M1 | Discover the override by scanning `src/*/report.py` instead of from `entrypoint`'s root package | Fixture O's two-package assertion on **which** titled section appears | Two packages, two distinct section titles, one named by `entrypoint` — a scan finds both and must pick, and any pick is observable. On a one-package project the branches are identical, which is why the fixture has two |
| M2 | Read `repo_root` from `provenance.git.repo_root` instead of `environment/repo_root.txt` | A Fixture O arm whose record's `provenance.git.repo_root` is hand-edited to a path that exists and holds a *different* project | Two real directories, two different `report.py` files. Both branches find *a* repo, so an assertion on "an override was found" cannot see it — the assertion is on the **section title** |
| M3 | Recompute `apparatus_hash` over `facts` instead of comparing recorded `hash` strings | Fixture A's hand-edited-hash arm | On every honest record the recorded hash **equals** a recomputation, so the branches are identical on Fixtures R and B. Only the edited record separates them, which is why that arm exists |
| M4 | Drop `results.contrasts` from the Deltas section | Fixture D | Fixture R has no declared contrast, so the branches are identical there; Fixture D is the only fixture on which they differ |
| M5 | Return `EXIT_PARTIAL` from `report` on a `partial` record | Fixture P's exit-0 assertion | The record's `status` is genuinely `partial`, so both branches read the same input and return different codes |
| M6 | Render a draft with a banner instead of refusing | Fixture T's run arm, asserting exit 1 **and** empty stdout | A banner render exits 0 and prints sections; the refusal exits 1 and prints none. Asserting only the exit code would still catch it, but asserting emptiness catches a refusal that prints first |
| M7 | Make the `min_reported_n` prompt list every metric | Fixture N's proper-subset assertion | The fixture's floor is chosen so the strata fall below and the whole-condition metric does not — measured from the record, not guessed — so "all" and "the thin ones" are different lists |
| M8 | Proceed silently when there is no TTY | Fixture Y's non-TTY arm, asserting `E-STUDY-CONFIRM-REQUIRED` **and** that the bundle holds no new file | Two observable branches: a written record versus a refusal. Asserting only the code would pass a build that refused *after* copying |
| M9 | Let `study add` overwrite an existing name | Fixture Y's re-add arm, asserting the file's **bytes** unchanged | The two runs differ, so an overwrite changes the bytes; a name-set check alone would pass a build that refused after writing |
| M10 | Give `format` a base default of `"markdown"` | Fixture O's no-`format` arm, asserting `E-REPORT-FORMAT` | With a default the arm renders markdown at exit 0; without one it refuses. The class genuinely declares nothing, so the branches read the same input |
| M11 | Perform the render **after** `sys.path` is restored | Fixture V, whose override reads a condition artifact | The override's module is imported either way; only a render that touches the project's own code after the pop fails. An override that yields a constant string cannot see it, which is why Fixture V's override reads |
| M12 | Compare `min_reported_n` against a working-directory config instead of the bundled record's own | A Fixture N arm run from a directory holding a config with a **different** floor | Two floors, two lists. One floor makes the branches identical, so the arm supplies two |

| M13 | Iterate `aggregated[step]`'s keys as the metric set, without the `RESERVED_METRIC_NAMES` exclusion | Fixture R's Conditions section, asserting the rendered metric names are exactly the record's real ones | Fixture R declares `report_by: [cohort]`, so its `aggregated[step]` genuinely holds a `by` key beside `score`. Without the strata declared the branches are identical, which is why the exclusion is pinned on the fixture that has one |
| M14 | Make `Section` a plain (unfrozen) value class | A Fixture O arm whose override mutates a standard section's `body` before yielding it, asserting the rendered figure is the record's | Frozen raises and the arm's override fails loudly; unfrozen renders a mutated number. Both branches read the same record, so the difference is entirely in what reaches the page |

**One mutation deliberately not prescribed, with the reason.** Section *order* is not mutated by
reordering `BaseReport.sections`'s four yields — that is *the thing under test iterating itself*, the
shape a recent slice shipped. It is pinned instead by an assertion on the four titles' order in the
rendered text of Fixture R, computed from the render rather than from the generator. **Said rather than
left as a silent gap**, since a mutation that changes nothing is evidence about the tests and not about
the code.

**And one claim that nearly shipped unmutated.** An earlier draft of Decision 2 argued that "an override
cannot change a number" was *structural* — a subclass re-yields objects it did not build — and concluded
there was no guard to weaken and so nothing to mutate. That argument is false for a `Section` whose
`body` is a mapping, which this design permits: a subclass can reach into one. The claim is now sized to
what the type provides, and the type is frozen so that it is true (M14). Recorded here because it is this
repo's most-repeated habit — *a safety argument in a comment is a claim needing a mutation* — and it was
made inside a design whose own house rules forbid it.

---

## The filings this slice makes

Two, both found by measurement in this pass, both **naming an owner that is not H8c** and saying why.

1. **`basis: repeats` is written by nothing, while five `reference.md` passages and one shipped warning
   name it.** Measured at `9963841`: `grep -n '"basis"'` over `src/publishable/` → five sites, all
   `"units"`; verified against output twice (a step-returned scalar reaches `per_repeat` and no
   `aggregated` entry; a run with `data.units` undeclared writes no `aggregated` key at all). The
   affected passages are § The unit table is the inference base, § Steps and artifacts, § `Estimate`'s
   neighbourhood, two § Validation rows, and `W-HYPOTHESIS-INFERENCE-BASE`'s own message. **Owner: not
   H8c** — writing a metric into `aggregated` is `run`'s work and nothing in H8c may alter a run. The H4
   family is complete, so the filing names the question rather than an owner who would inherit it
   silently: *is the documented shape the intended one (and `run` owes an emitter), or has the design
   moved to "a step-returned scalar lives in `per_repeat` and nowhere else" (and six passages owe a
   rewrite)?* The check to run before dispositioning it: whether `W-HYPOTHESIS-INFERENCE-BASE`'s message
   can be true of any record this build writes. It cannot be, today.
2. **`execution.*.nondeterministic` is written by nothing**, while § The two files' `run.yaml` example
   shows it on every repeat-scoped entry and `design-principles.md` § Not bit-identical reruns says core
   "records that in `run.yaml` and **notes it in `report`**". Measured: zero occurrences in a real
   `run.yaml` **and** zero in `executions.jsonl`; the attribute exists only on `BaseStep` and as what
   `W-REPL-DETERMINISTIC` reads off the classes. This is **not** covered by the "Six `provenance` and
   `results` keys" filing, which is about `provenance` and `results` and names H6's three remaining
   keys. **Owner: not H8c**, for the same reason as above — and the consequence for this slice is
   recorded rather than worked around: **the Attrition section does not claim it**, because a section
   that printed "nondeterministic: false" for every execution would be reporting a default nothing
   measured. `design-principles.md`'s "notes it in `report`" becomes true the day the field is written,
   and the filing says which section it lands in.

**A ledger line saying "filed" is not a filing**: both go into `docs/superpowers/spec-defects.md` as
entries, in the task that finds them, not into a report.

---

## What H8c reuses from H8a and H8b rather than rebuilding

The scoping was written before either shipped, so this is the list it could not have.

| Reused | From | What it saves |
|---|---|---|
| `lineage.read_run_record(run_dir)` | **H8a** task 1 | The `run.yaml` reader with its three refusals (`E-UPSTREAM-RECORD-MISSING` / `-UNREADABLE` / `-VERSION`) and the `SCHEMA_VERSION` check, imported rather than restated. § Errors core raises' row for those codes already names `diff` as a second caller; `report` and `study add` widen the row rather than minting a fourth spelling |
| `read_run_record`'s **`partial`-tolerant** posture | **H8a** | Its docstring already argues that a `partial` or `failed` record is not refused, which is exactly what Decision 6 needs and does not have to re-argue |
| `environment/repo_root.txt` | **H8b** | Decision 3's whole answer. Without it, override discovery has no way to reach the repo from a `run.yaml` inside `output_dir` — and H8b invented the file for the structurally identical problem in `freeze` |
| `_record_dir`'s rule (a `run.yaml`'s run directory is its parent) | **H8b** | The one-line normalization Decision 1 needs. The *predicate* `_form` is deliberately **not** reused — it answers "config or run record", a different question |
| `provenance.upstream`, always a list | **H8a** task 7 | A report can name a run's ancestors with no absent-versus-`null` special case, because H8a ruled `[]` rather than omission |
| `diff`'s ruling that a hash row's verdict compares the **recorded** figure | **H8b** Decision 2 | Decision 8's grounds, and the consistency argument. H8b's own docstring already names `report study.yaml` as the other consumer of `provenance.apparatus.hash` |
| `diff`'s exit-code ruling (0 whenever it rendered) | **H8b** Decision 4 | Decision 6 is the same rule; the two now agree in both directions, and H8b's leaned on `report`'s § Exit codes row to begin with |
| The `reference.md` sentence on `diff` versus the run-time gate | **H8b** task 12 | **Already landed.** The filing routed it to H8c; H8b took it while editing the same section. Nothing to do |
| `apparatus.replay_ledger` and H7d's probe-plugin fixture shape | **H8b** / **H7d** | Fixture A's installed-distribution-plus-local-template scaffolding, inherited whole |
| `tests/test_diff.py`'s document-parsing row-label reader | **H8b** | Fixture H extends it to the header lines instead of writing a second parser over the same three files |
| `stats.RESERVED_METRIC_NAMES` | **S4d**, pre-H8 | Decision 5's `by` exclusion, imported rather than restated as a literal. `_comparison_step_blocks` is the shipped precedent for one consumer excluding it; `report` is the next |
| `test_the_apparatus_hash_is_recomputable_from_the_recorded_facts` | **H8b** | The pin that makes M3's branches provably identical on every honest record — which is *why* Fixture A needs a hand-edited one to separate them |
| `run_a_project` | pre-H8, used by both | Every fixture above. It already supports `_starter_step`, `extra_step_source`, `unit_attributes`, `units_overrides`, `expect_exit` and `capsys` — this pass drove all four of its measurement runs through it |

**And two things H8c does *not* inherit, named so they are not assumed.** `freeze`'s
`E-FREEZE-PLAN-MISMATCH` re-expansion cross-check is not `report`'s: `report` reads a *finished* record
whose `config` is embedded verbatim, so there is no copy to disagree with a plan. And H8b's
run-start `config.yaml` byte copy is not read by `report` at all — the embedded `config` in `run.yaml`
is the fact for a finished run, and reading both would be two sources for one thing.

---

## What did not survive H8a and H8b shipping

The scoping's H8c claims, re-measured. **Six did not survive**, all in the same direction every charter
on this project has been stale in — under-counted and missing surface.

| Claim, and where | Verdict |
|---|---|
| *"`study add`'s `min_reported_n` prompt … over three shapes … **All three are producible today**"* (§ 5's testability table) | **False, and it was false at `a346151` too.** `basis: repeats` is written by nothing — five `"basis"` emit sites, all `"units"`, verified against two real runs. Two shapes are producible; the third's branch ships behind a synthesized record with the filing attached (Decision 13) |
| *"Whether `report`'s standard sections can be rendered from `run.yaml` alone, or need the run directory too"* — listed under **what could not be measured** | **Measured, and the answer is `run.yaml` alone.** All four sections are pure functions of the parsed record; the run directory is needed only by an **override**, through `ReportIO`. That is the whole cost argument for the slice and it is now a measurement rather than an inference from § A report override's argument (Decision 5) |
| The scoping's H8c list, and § 5's table, on where `report` gets a **repo root** | **Absent, and the answer did not exist when the scoping was written.** `report <run.yaml>` cannot walk up to a repo — `output_dir` may never resolve inside one — so override discovery was unanswerable until H8b invented `environment/repo_root.txt`. Neither the scoping's task 20 nor its testability table names the problem (Decision 3) |
| § A report override's *"`io` is the same **read-only** accessor a `summary` step gets"*, carried into the scoping's task 20 without challenge | **False of the code.** A `summary`-scope `StepIO` carries `record`, `write`, `append`, `skip` and `finalize`. The document changes first, and `ReportIO` is the four-member read half (Decision 4) |
| The `spec-defects.md` filing's owner note: H8c owns *"the one `reference.md` sentence closing the `diff`-versus-gate ruling"* | **Stale within a day.** **H8b task 12 already landed it**, in § The apparatus core can only observe beside the fenced `diff` example, because that task was editing the same section for another reason. The filing's own text anticipated the alternative ("rather than routing it to H8c as first ruled") — so this is a filing's claim about the code going stale like any other comment, one day old |
| The scoping's task 22, *"The standard sections: condition table, deltas, hypothesis verdicts, attrition"*, as four independent renderings | **Under-specified in one load-bearing way.** The deltas section must read **top-level `results.contrasts`** as well as each condition's `vs_baseline` — measured: `command_run` splits `resolve_contrasts`'s output between the two. § The two files' `run.yaml` example shows only `vs_baseline`, so the reading that produces the bug is the one a reader of that example reaches first (Decision 5, Fixture D) |

**Two scoping claims that survive entirely**, restated because they are load-bearing and were confirmed
rather than carried: **`BaseReport` is H8c's** (§ Package layout, § A report override and § The
importable surface, all three re-read at this commit, all three unchanged by H8a or H8b); and
**`generate report` is in nobody's charter** (still in `NOT_BUILT_GENERATORS`, still NOT BUILT in
§ Generators, still absent from H9's list), so H8c claims it (Decision 17).

---

## Task decomposition — 16, up from the scoping's 12

The arithmetic, rather than an anchor to 12. The scoping's twelve are tasks 1–12 below with two
consolidations and four additions; H8b went 8 → 12 on the same grounds and for the same reason.

| # | Task |
|---|---|
| 1 | `BaseReport` and a **frozen** `Section` in `report.py`: `sections` as a generator, `self.section`, `format` with no base default, `yield from super().sections` composition. Exported from `publishable/__init__.py`; § The importable surface's row `not yet built` → `built`; **the `spec-defects.md` entry struck** (Decision 2) |
| 2 | **`ReportIO` in `artifacts.py`**: the four read members, the shared traversal extracted so `StepIO` and it cannot drift, and the withheld write half (Decision 4). *New — the scoping had no task for the `io` half* |
| 3 | Override discovery: `entrypoint`'s root package, its sibling `report` module, `environment/repo_root.txt` as the repo fact, the render inside the `sys.path` window, and the three refusals (Decision 3) |
| 4 | `report`'s argument and form: name-based dispatch, the directory refusal, `E-REPORT-FORM`, and `read_run_record` wired in (Decision 1) |
| 5 | Standard sections 1 and 2 — Conditions (with `by` strata rendered as strata, and `by` excluded from the metric set via `stats.RESERVED_METRIC_NAMES`) and Deltas (with `results.contrasts` **and** the family line of Decision 19) |
| 6 | Standard sections 3 and 4 — Hypothesis verdicts, and Attrition **without** claiming `nondeterministic` (Decision 5, filing 2) |
| 7 | The markdown and HTML renderers over one section stream; HTML self-contained and offline (Decision 16) |
| 8 | `report <run.yaml>` end to end: **exit 0 on `partial`** with the failures shown (Decision 6) |
| 9 | The **draft** refusal, and the bundle's flag-not-refuse asymmetry (Decision 7) |
| 10 | `report <study.yaml>`: bundle render, the `code_hash` cross-check, the `provenance.apparatus.hash` cross-check comparing recorded figures with the `null` exclusion, draft flagging, every hypothesis in one table, **no override discovery** (Decisions 3, 8) |
| 11 | `study new`: bundle creation, `--title`, `E-STUDY-IN-REPO`, `E-STUDY-EXISTS` (Decision 9) |
| 12 | `study add` part 1: copy, the four-field redaction with the marker rule, every hash kept, `code.remote`/`code.commit`'s single-run semantics, `W-STUDY-COMMIT-MISMATCH` (Decisions 10, 11) |
| 13 | `study add` part 2: the duplicate-name refusal, checked against both `study.yaml` and the file, and refusing **before** any write (Decision 12) |
| 14 | The `min_reported_n` prompt over the record's entries, all three branches, the non-TTY refusal, and the record's own `limits` (Decision 13). *Split from task 13 — the scoping had one task; the unreachable branch and its filing are their own work* |
| 15 | `generate report <exp> --format`, out of `NOT_BUILT_GENERATORS`, § Generators row to `built`, `E-REPORT-EXISTS`, and a scaffolded body that renders more than no override does (Decision 17). *The scoping's task 21* |
| 16 | Documents and codes: Decision 15's rows in § Errors `validate` reports, plus `E-REPORT-EXISTS`; the widened `read_run_record` row in § Errors core raises; § Package layout's two markers off; § CLI reference's three `Status` cells (`report`, `study new`, `study add`) and § Generators' fourth; § What `study add` redacts' **`allocation.json` ruling** and the removal of its "not yet built" hedge; § A report override's `io` sentence; **the three worked `diff` blocks' headers** (Decision 20); and both consistency passes. *The scoping's task 30, plus the three-document header edit it could not have known about* |

**Where the four extra tasks came from**, so a later reader can undo the split if they disagree:
`ReportIO` (task 2, an `io` surface the scoping's task list has no home for); the `min_reported_n` split
(task 14, because the unreachable branch plus its filing is not the same work as the redaction); the
three worked `diff` blocks at three concreteness levels (inside task 16, filed OPEN to H8c after the
scoping was written); and the two filings, which land in the tasks that find them rather than as a task
of their own. **If `generate report` is chartered elsewhere, H8c drops to 15.**

---

## The consistency sweep this slice owes

Both passes, over the **four documents** named individually — `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md` — never over `*.md`,
which no longer means what it used to now that the development record is tracked. And never over a
**filtered output**: filter the file list, and prove each sweep can fail by running it against a string
known to be present.

**Mechanical**, in full: every relative link and `#anchor` resolves; no duplicate heading anchors; every
table's rows match its header's column count; no trailing whitespace, tab or invisible unicode; fenced
blocks skipped throughout, since these documents contain markdown inside markdown. `×` not `x`. Hyphens,
never en dashes, in anything that becomes an anchor.

**Cross-document**, the classes this slice actually moves:

- **The shared worked example.** Task 16's header edit touches three of the four documents' `diff`
  blocks. The intervals, hash prefixes, run IDs, delta lines and row order do not move; the assertion
  that they did not is Fixture H, not a promise.
- **`Status` columns.** `tests/test_cli.py` reads all three CLI tables and checks both directions, so a
  marker outliving its slice fails a test. Four cells flip: `report`, `study new`, `study add`, and
  § Generators' `report` row. § The importable surface's `BaseReport` row flips with them, and the
  sentence *"Importing one raises `ImportError` today"* **derives** its claim from the `Status` column —
  so it needs no edit, which is the self-maintaining property a previous slice learned by breaking.
- **Schema fields in prose.** `study.yaml`'s keys are named in § Building one's fenced block and must
  match what `study new`/`study add` write, in both directions.
- **After removing a string, grep for what should no longer exist** — and note that one of the three is
  **link-wrapped**, so a bare-string grep for it finds nothing. The spans, quoted as they appear:
  § What `study add` redacts' "is a question this slice leaves open for whichever slice builds
  `study.py`"; the hedge in the same paragraph, whose removable clause is
  ``` `study add` is [not yet built](#package-layout), so what follows is a reading of the shape [§ Building one](#building-one) already commits to, not a checked fact ``` — the phrase "not yet built" sits
  **inside a link to `#package-layout`**, so grep the clause rather than the phrase; and § A report
  override's "the same read-only accessor a `summary` step gets". `spec-defects.md`'s `BaseReport` entry
  is **struck rather than deleted**, since that file is a live list.
- **§ Exit codes' four-code creation-command enumeration** gains `E-STUDY-EXISTS` and `E-REPORT-EXISTS`
  (Decision 15). Named in this pass rather than left to the mechanical check, which cannot see a prose
  enumeration going stale.
- **Not the development record.** Neither pass touches a spec, a plan, a scoping or a ledger. A scoping
  records what was measured on its date; § What did not survive above **appends** its corrections rather
  than editing `H8-SCOPING.md`.

---

## What could not be measured

- **`report` against a bundle assembled on another machine.** Every fixture builds its bundle locally,
  so the device-independence claim — "every reference is relative, `run_id` is a label rather than a
  locator, and nothing resolves through the original output storage" — is pinned by asserting the
  bundle's references are relative and that the render opens no path outside it, not by moving a bundle
  between machines. Said rather than claimed.
- **`provenance.environment.hostname`'s redaction against real output.** It is never written (H6's), so
  that one row of Decision 10's table is exercised only over a synthesized record.
- **A genuine `draft` run.** `publishable draft` is `NOT BUILT` and H9's; Fixture T's record is
  hand-edited from a real one and says so.
- ~~Whether a metric named `by` collides with the strata block.~~ **Measured, and it is neither
  unmeasured nor a new filing** — see Decision 5. `coerce_scalars` constrains a returned mapping's
  *values* and never its *keys*, so the key is reachable; a run with `aggregate` returning `by` loses the
  derived metric, with `report_by` declared and without it, against a control that appears. S4d already
  filed it, minted `E-STEP-KEY-COLLISION` and `W-STATS-STRATUM-SHADOWED` for the two halves, and pinned
  all three arms. Its **open residual is a document gap** the filing states in its own words —
  "`reference.md` documents no reserved metric names at all" — and H8c does not claim it: this slice's
  documents task edits § Errors, § Package layout, § CLI reference, § Generators, § What `study add`
  redacts and § A report override, none of which is where a reserved metric name belongs. What H8c owes
  is the exclusion, and Decision 5 owes it.
- **What an override does with a `failed` run whose `results` are thin.** Fixture P covers `partial`;
  a run that stopped with almost nothing recorded renders whatever the record holds, which is the same
  code path, but no fixture exercises the degenerate end of it.
