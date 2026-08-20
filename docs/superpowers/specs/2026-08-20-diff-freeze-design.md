# H8b — `diff` and `freeze` — design

**Goal:** two commands that read what a run already wrote and say what moved. `diff` compares two
runs hash by hash and names the parameters that differ; `freeze` re-probes a run **in progress**
and reports a moved apparatus before the next block of executions is spent on it. Neither executes
a step, neither changes a run's status, and between them they write exactly one kind of byte into a
run directory: an appended line in `apparatus/probes.jsonl`.

**What it delivers, stated so it cannot be rounded. H8b unblocks ZERO configs and mints no fifth
number.** `CLAUDE.md`'s 2026-08-20 correction rules that a single figure answers no consistent
question for [the feasibility analysis](../../feasibility-llm-growth-studies.md), and H8a's own
§ Executability entry replaced the number with a table. H8b **repeats that table unchanged** — all
four rows — because nothing it builds runs at `validate`, nothing it builds is called from a step,
and no config in that analysis declares an `apparatus_probe` a real plugin backs:

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — the method ships; six configs still need the plugin body to call it |
| Meet the `report_by`-under-`resample` gap | **7** | no — H4 Statistics' gap, untouched here |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

The only direction H8b could move a count is **down** — H7d Part B's shape, and worth saying for the
same reason. It retires no refusal. It mints eight error codes — seven `E-FREEZE-*` and one
`E-DIFF-*` — plus one warning, and it makes one change to a command that executes: `run` writes two
more artifacts at run start, which is what makes `freeze` possible at all (Decision 7).

---

## The measurement this rests on, and why it was re-taken

[`H8-SCOPING.md`](../H8-SCOPING.md) was measured against `a346151` — **before H8a existed** — and
H8a then merged **10 tasks** H8b reads directly: `lineage.py`, a `run.yaml` reader, locator and step
resolution, eleven `E-UPSTREAM-*` refusals, and `provenance.upstream`. `CLAUDE.md`'s rule is that a
scoping expires and a spec does not, so **every build claim below was re-measured on 2026-08-20
against `main` at `3ed3907`**, by running rather than reading. § What did not survive H8a shipping
says where the scoping and the code now disagree.

### Measured on 2026-08-20 against commit `3ed3907`

One real end-to-end `run` through `main(["run", …])`: a scaffolded project, a 24-row synthetic
index, `sweep.grid` over `analysis.method` (2 conditions), 5 `seed` repeats, exit 0,
`status: completed`. Every claim in this table is from that run directory or from a direct call, not
from a read of the source.

| What was measured | Result |
|---|---|
| `run.yaml`'s top-level keys | `schema_version`, `run_id`, `status`, `draft`, **`config`**, `parameters_hash`, `code_hash`, `provenance`, `layout`, `execution`, `results`. The config **is** embedded, so both of `diff`'s parameter-delta operands are in the two records |
| `provenance` keys | `git`, `environment`, `apparatus`, `input_manifest`, `input_manifest_hash`, `input_manifest_changed`, `publishable_version`, `plugin_versions`, `units`, `units_hash`, `allocation`, `allocation_hash`, **`upstream`** |
| `provenance.upstream` on a run with no upstream | **`[]`** — present, empty. The scoping measured it **absent**; H8a changed that, and it is what makes Decision 6's upstream block a reader of a **shipped** surface |
| `provenance.environment` | `{manager, python_version, uv_lock, uv_lock_hash}` — **`uv_lock` and `uv_lock_hash` are both `None`** on a scaffolded project with no lockfile. `os`/`hostname`/`hardware` are H6's and absent |
| `provenance.apparatus` | `None` — `generic` declares no probe |
| The run directory | `conditions/…`, `environment/pyproject.toml`, `executions.jsonl`, `manifest/input.json`, `run.yaml`, `sweep.yaml`. **No config, and no `lock`** (removed when `run.yaml` is written) |
| `sweep.yaml`'s top-level keys | `design_digest`, `conditions`, `repeats`, `labels`, `order`, `execution_order`. Each condition entry is `{index, label, values, is_baseline}` — **no `selectors`**, which is why Decision 8 re-expands rather than rebuilding cfgs from this file |
| `lineage.read_run_record(run_dir)` against that directory | Returns the parsed record; keyed on the **directory**, appending `run.yaml` itself |
| `main(["diff", a, b])`, `main(["freeze", d])` | *"specified but not built … see docs/reference.md § Operation commands"*, exit **2**, through `NOT_BUILT_COMMANDS` |
| `main(["validate", "/nope/nope.yaml"])` | `E-IO-FAILED`, exit **1** — not 2, though § Exit codes lists "unreadable path" under 2. The shipped precedent `diff` follows (Decision 4) |
| `append_observation(phase="BOGUS_FIFTH_SPELLING", …)` | Wrote that string **verbatim** to `apparatus/probes.jsonl`. The docstring's "closed vocabulary of four" is unenforced at this commit — the scoping's mutation, re-run rather than carried |
| `get_template(name, repo_root=None)` | A **project-local** template is found only through `discover_local(repo_root)`, and `_claims` skips it entirely when `repo_root is None`. So resolving the template a run used needs the repo root — the measurement that forced Decision 7's second artifact |
| `load_document` | Pure `yaml.safe_load` plus a mapping check: no defaults injected, no path resolved relative to the config. So a **byte copy** of the config file parses to a document equal to `run.yaml`'s embedded `config` |
| `doc` inside `command_run` | Never mutated between load and `assemble_run_yaml(config=doc)` — grepped for `doc[…] =`, `doc.setdefault`, `doc.update`: no assignment. The equality in the line above is therefore a property, not a coincidence |
| `expand(config)` | Takes the config and nothing else — no roster, no `io`. Conditions are re-derivable from the config alone, which is what lets `freeze` reach the apparatus without resolving units |
| Run-start writes in `command_run` | `manifest/`, `environment/`, `sweep.yaml`, `allocation.json`. Nothing globs or iterates the run directory's root anywhere in `src/`, so adding a file there is inert |
| A hand-written `uv.lock` in a scaffolded project, run end to end | Copied to `environment/uv.lock` and recorded as a real `uv_lock_hash` — `uv_lock_info` is a plain content hash with **no** `--locked` drift check (*"syncing arrives with `reproduce`"*). Fixture L's premise, measured rather than assumed |
| `declared_credential_names(doc, template, conditions)` and `secrets.missing_env(names)` | Both callable from a config, a resolved template and an expanded condition list — exactly what Decision 8 gives `freeze`, so its credential pre-check and its redaction set need no new machinery |
| `Observer.__init__` | Needs `probe_name`, `probe`, `declared_facts`, `conditions`, `cfgs`, `run_dir`, `credentials`. The first two and `declared_facts` come from the resolved **template**; `cfgs` from `resolve_condition_cfg(doc, condition)`, which takes the whole `Condition` (its `selectors`, not just its `values`) |

Gates at this commit, run directly: `uv run pytest` → **2513 passed, 1 skipped, 2 xfailed**;
`ruff check`, `ruff format` and `mypy` were not re-run, since no production code ships from this
file.

---

## Decisions

Fifteen, each with grounds and what it costs if wrong. Two of them (4 and 5) resolve contradictions
[`H8-SCOPING.md`](../H8-SCOPING.md) § 8 enumerated and deliberately left open.

### 1. `diff`'s five rows — what each compares, and how a row renders

**Ruling.** Five rows, in this order, with these labels:

| Row label | Compares | Source in each record |
|---|---|---|
| `code_hash` | the identity claim over `src/**` + `templates/**` | top-level `code_hash` |
| `input_manifest` | the content hash over the input tree | `provenance.input_manifest_hash` |
| `uv.lock` | the environment fingerprint | `provenance.environment.uv_lock_hash` |
| `apparatus` | the apparatus fingerprint — Decision 2 | `provenance.apparatus.hash`, with `…facts` for the detail |
| `parameters_hash` | the declaration identity claim | top-level `parameters_hash`, with `config` for the deltas |

The set, the order and the labels are not invented here: all three worked outputs — `README.md`
§ The loop you'll actually live in, `design-principles.md` § Same code, different parameters, and
`reference.md` § The apparatus core can only observe — agree on them, including that the label is
`input_manifest` rather than `input_manifest_hash` and `uv.lock` rather than `uv_lock_hash`. A row's
verdict is one of three words:

- **`identical`**, followed by the digest truncated to `sha256:` plus four hex characters plus `…`,
  which is the width all three worked outputs show.
- **`DIFFERS`**, followed by its detail lines. `parameters_hash` details are the deltas (Decision 3)
  and `apparatus`'s are the per-fact lines (Decision 2). The other three rows have no detail beyond
  the two digests, so a `DIFFERS` there prints `8e21… → 4c07…` on the following line — an addition
  the worked outputs are silent about, made because a bare `DIFFERS` gives a reader nothing to cite.
- **`not captured`**, when the figure is `null` on either side. Measured above: a scaffolded project
  with no lockfile records `uv_lock_hash: None`, so two such runs would otherwise print
  `uv.lock  identical  sha256:None…` — a match over a fact neither run holds. `not captured` is
  `study add`'s own vocabulary for *never captured* as against *redacted*, reused rather than minted.

**Grounds.** The rows are documented three ways and the labels are what a reader greps for. `not
captured` exists because § The apparatus core can only observe already argues the general form of it
for facts — *"an apparatus that never answers can never contradict itself, so an unobserved fact is
a pin you don't have rather than a pin that held"* — and a `null` hash is that same object.

**Cost if wrong.** Printing `identical` over two `null`s is the single most dangerous output this
command can produce: it is the sentence a reader quotes to claim the environment held still, made
over a lockfile that never existed. Getting the labels wrong instead costs a stale grep, which is
recoverable.

### 2. The `apparatus` row — what `DIFFERS` means now that H7d ships both halves

**Ruling.** The row's **verdict** compares `provenance.apparatus.hash`, the digest H7d Part A
assembles over the resolved condition → facts mapping. Its **detail lines** are computed from
`provenance.apparatus.facts`, one line per `(condition, fact)` pair whose value differs, each
qualified by the condition key exactly as the record keys it:

```
apparatus          DIFFERS
  00_baseline.calibration_id     CAL-2026-07-19 → CAL-2026-08-02
  01_dose=high.calibration_id    CAL-2026-07-19 → CAL-2026-08-02
```

Three sub-rulings the documents do not answer:

- **The row appears whenever *either* record carries a non-null `provenance.apparatus`**, and prints
  `identical` with its digest when the two hashes match. It is omitted **only** when both are
  `null`, which is the one case `design-principles.md` documents (*"No apparatus row, because
  template `generic` declares no probe"*). The scoping's § 10 lists this as underivable; it is
  ruled here.
- **One side with an apparatus and one without is `DIFFERS`**, with a detail line naming which side
  recorded none. Two runs are not comparable on a pin only one of them has, and silence would read
  as agreement.
- **A condition key present in one record and not the other** gets a detail line saying so rather
  than being skipped. When the sweep itself changed, `parameters_hash` will also be `DIFFERS` and
  the deltas say why — but the apparatus row must not imply the per-condition mappings lined up.

Every line is **qualified by the condition key**, with no collapsing when several conditions moved
identically. **The fenced example in `reference.md` § The apparatus core can only observe shows a
bare `calibration_id` and must gain its condition key** — the document changes first. The
alternative, collapsing identical moves onto one unqualified line, was considered and refused: it is
a branch nothing in the documents asks for, it needs two fixtures (identical moves and differing
moves) before either arm is pinned, and a collapsed line cannot say whether *every* condition moved
or only the ones it printed.

**Grounds.** The apparatus is explicitly **not a fourth hash** — § The apparatus core can only
observe places it *"beside `uv_lock_hash` as an environment fingerprint"* — which is exactly why it
gets a row and not a place among the three identity claims. Facts are per condition *"since the
apparatus may legitimately differ across a sweep"*, so a per-fact line that drops the condition is
reporting a mapping's value without its key.

**Cost if wrong.** Comparing the facts mappings directly instead of the hash would let the row
disagree with `provenance.apparatus.hash`, which is the figure `report study.yaml` cross-checks in
H8c — two comparisons of one fact, able to disagree. Dropping the condition qualifier makes a
one-condition drift indistinguishable from a whole-run drift, which is the difference between a
salvageable run and none.

### 3. The parameter deltas come from the projection `parameters_hash` hashes, never a second list

**Ruling.** `hashes.py` gains `covered_config(config)` — the projection `parameters_hash` already
computes inline (everything but `metadata`, minus `data.input_dir` and `data.output_dir`) — and
`parameters_hash` is rewritten to hash it. `diff` flattens **that projection** on both sides to
dotted leaf paths and reports three shapes:

```
parameters_hash    DIFFERS
  parameters.analysis.method       pearson → spearman
  limits.max_failed_fraction       0.2 → 0.4
  statistics.contrasts             (absent) → [{name: dose_high_vs_low, …}]
```

A leaf present on one side only renders `(absent) → <value>` or `<value> → (absent)`. A leaf whose
value is a list or mapping renders as one line of YAML flow style, untruncated — a config value is
small, and a truncated delta is a delta a reader cannot act on.

**Grounds.** The delta set and the verdict above it must agree about coverage or `diff` prints
`parameters_hash identical` with delta lines under it, or `DIFFERS` with none. One function is how
they do not drift — the argument H8a's `read_run_record` already made for importing `SCHEMA_VERSION`
rather than restating it. And the coverage is wider than the `parameters` block on purpose:
`reference.md` § Three hashes states both halves of this, that *"a `metadata`-only edit is invisible
to `diff`"* and that `diff` *"prints a raised `max_failed_fraction` as the parameter delta it is"* —
`limits`, not `parameters`.

**Cost if wrong.** A delta walk over `config["parameters"]` alone would print `parameters_hash
DIFFERS` with **no** delta lines for every `limits`, `statistics`, `sweep`, `replication` or
`data.units` edit — which is most edits — and the reader's conclusion would be that something
changed that core cannot name.

### 4. `diff`'s exit code — **contradiction 1, ruled**: 0 whenever it rendered a comparison

**Ruling.** `diff` exits **`0`** on every comparison it renders, whether five rows say `identical`
or five say `DIFFERS`. It exits **`1`** only when it cannot render one: a path that is not a
readable record or config (`E-IO-FAILED` for a missing path, matching `validate`'s measured
behaviour; `E-UPSTREAM-RECORD-*` for an unreadable record; `E-DIFF-CONFIG-UNREADABLE` for a config
that does not parse to a mapping). **`reference.md` § Exit codes and diagnostics must lose its
`diff` clause** — *"a `diff` of runs that don't share a hash"* leaves the `1` row.

**Grounds.** Three, and the third is what makes it a ruling rather than a preference.

1. **The advertised payoff is a difference.** `design-principles.md` § Same code, different
   parameters shows `parameters_hash DIFFERS` and calls it *"the comparison to aim for"*, and
   README's § The loop you'll actually live in shows the identical output as the point of hashing
   code and parameters separately. A command whose documented success case exits non-zero is one no
   script can put on the left of `&&`.
2. **`report` is the named precedent.** § Exit codes disambiguates exactly one command this way:
   *"`report` of a `partial` run exits `0`* — it was asked to render a record and it rendered one*."
   `diff` was asked to compare two records and it compared them. A reader learns what differed from
   the output, which is where that belongs.
3. **The `1` row generalized from `resume`, where the analogy fails.** The same row lists *"a
   `resume` whose hashes moved"* — and there a moved hash blocks an **action**: `resume` must not
   continue, so the code is what stops a script. `diff` takes no action to block. The row's other
   members (a config that fails validation, an apparatus change caught before the first execution)
   are all things that stopped something.

The third candidate reading — `1` only when `code_hash` differs — is refused: `design-principles.md`
makes comparing two runs *"weeks apart at different commits"* the whole point of the split, so a
non-zero exit on differing code would make the most ordinary exploratory comparison an error.

**Cost if wrong.** If the right answer were `1`-on-difference, a script would archive runs it should
have flagged. That cost is bounded — the output says `DIFFERS` in the first column, and a script can
key on the stable text. The reverse cost is not bounded: under `1`-on-difference, every pipeline
built around the documented payoff has to special-case the success it was told to aim for, and the
first person to do that will do it with `|| true`, which then swallows the unreadable-record case
too.

### 5. `diff`'s arguments — **contradiction 2, ruled**: two paths, form by path shape, and a config supplies exactly one row

**Ruling, in four parts.**

1. **Two paths and nothing else.** `cli.py`'s `OPERATION_COMMANDS` arm enforces *exactly one path
   and no flags*; `diff` gets its own arm enforcing **exactly two paths and no flags**, with the
   same rejection of a leading `-`. `design-principles.md` § Everything is in the file forbids
   anything else, and there is no `--format`, no `--only`, no selector.
2. **The form of each path is decided by its shape, before any parsing.** A **directory**, or a
   file **named `run.yaml`**, is a run record, read through H8a's `read_run_record` on the run
   directory. Any other file is a config. Grounds: `read_run_record` is directory-keyed (measured),
   and shape-based dispatch means the error message can name the form it assumed rather than
   guessing from content. Accepting a directory is not a convenience — `<output_dir>/latest` is a
   directory, and `diff <output>/latest <output>/run_2026-…` is the invocation a reader actually
   types.
3. **`diff` prints, per side, which form it read and what that side is** (Decision 6), so a
   misidentified path is visible in the first two lines rather than inside a row.
4. **A config supplies exactly one of the five rows — `parameters_hash` — and the other four print
   `not comparable`, each with its reason.** `parameters_hash(doc)` is a pure function of the file.
   The other four are refused rather than computed, and refused as **one rule** rather than four
   judgements:

| Row, against a config side | Printed |
|---|---|
| `code_hash` | `not comparable  a config records no code_hash; the tree it would hash is the tree now, not the tree a run used` |
| `input_manifest` | `not comparable  a config records no input manifest; building one resolves the roster and may run a plugin resolver` |
| `uv.lock` | `not comparable  a config records no lockfile hash; the repo's lockfile is the environment now, not a run's` |
| `apparatus` | `not comparable  an apparatus fact is observed by a probe, and diff is not one of the places a probe runs` |

**Grounds.** § Reproducing on another device solves the identical problem for `reproduce` and its
sentence is the precedent: *"It cannot verify a `code_hash` and says so, rather than reporting a
match it never made."* Computing `code_hash` or `uv_lock_hash` from the config's own repo would
answer a **different question** — the working tree now, which `run` refuses to execute when dirty
and which moves under the next keystroke — and printing that under the label `code_hash identical`
beside a run's recorded hash is exactly the substitution `CLAUDE.md` § Answering a question with a
proxy is about. The apparatus row is refused for a stronger reason still: § The apparatus core can
only observe enumerates where a probe runs — *"`dry-run`, at run start, before every execution, and
at `freeze` — never at `validate`"* — and `diff` is not on that list, so a probe call here would be
a new metered surface no document specifies.

**Config-vs-config and config-vs-run are therefore the same rule**, which is what closes the
scoping's contradiction: § Operation commands' *"two config or run paths"* is honoured as written,
the mixed form included, and the wording needs no change. What changes is that the section gains the
sentence saying what a config side cannot supply.

**Cost if wrong.** If the four rows should have been computed, a user asking *"is my working tree
still the code run A used"* gets nothing — and the route is `reproduce`, the command whose whole job
is preparing and checking a checkout (H9). That is a real loss, and it is smaller than the loss the
other way: a `code_hash identical` printed over a dirty working tree is a false identity claim in
the one output this project exists to make trustworthy.

### 6. Per-side header, and the upstream block the five rows cannot hold

**Ruling.** Before the rows, `diff` prints one line per side naming its form and its identity:

```
A  run record  run_2026-08-06T14-02-11Z_8e21ab3   completed
B  run record  run_2026-08-07T09-14-03Z_8e21ab3   completed  draft
```

`draft: true` earns the word `draft`, which is what § Draft runs requires (*"`report` refuses to
render one as a final result, and `diff` labels it"*). `status` is printed for the same reason
`study add` of a `partial` is *"visible as what it is"*: a comparison of a `failed` run's hashes is
a comparison against a record with nothing to report, and the reader should not have to open the
file to learn that.

**After the rows, an `upstream` block, printed only when either side's `provenance.upstream` is
non-empty**, listing each entry's `run_id` and its two short hashes — and when all five rows are
`identical` while the upstream lists differ, one line saying exactly that.

**Grounds.** § Lineage between runs claims `diff` *"can tell you two runs differ only because their
upstreams did"*, and that state is reachable: an upstream artifact is read from `output_dir`, not
`input_dir`, so it is **outside the input manifest** — two runs can match on all five rows and
consume different ancestors. The scoping recorded this claim as *"absent, and doubly so — needs both
`diff` and `provenance.upstream`"*; H8a built the second half, and `provenance.upstream` is written
on every run as of `3ed3907` (measured: `[]` when there is none). An unbuilt reader of a **shipped**
surface is a defect, not specification — `CLAUDE.md`'s own line — so H8b owes it.

**It is not a sixth row.** The five rows are documented three ways and their count is load-bearing;
`draft`, `status` and `upstream` are a header and a block, not hash comparisons.

**Cost if wrong.** Without it, two runs differing only in lineage print five `identical`s — the
precise failure § Lineage between runs warns about, in the command it names. Putting it in a row
instead would contradict three worked outputs.

### 7. `freeze`'s input — the run directory, and the two artifacts `run` must start writing

**The hole, re-measured.** A probe is `probe(cfg) -> Apparatus`, and the config a run used is
reachable from its run directory **only through `run.yaml`, written once at the end** — while
`freeze` exists precisely for a run that has not ended. `sweep.yaml`'s six keys are not the config
(measured). And resolving the run's **template** — where `apparatus_probe` and `apparatus_facts` are
declared — needs the **repo root**, because a project-local template is discovered only through
`discover_local(repo_root)` and `get_template` skips local discovery entirely when `repo_root` is
`None` (measured).

**Ruling.** `freeze` takes the **run directory**, as § Operation commands says, and `run` (and
`draft`, and `resume`, when H9 builds them) writes two artifacts at run start:

- **`<run_dir>/config.yaml`** — a **byte copy** of the config file, taken beside the existing
  run-start captures of `environment/pyproject.toml` and `environment/uv.lock`, which are byte
  copies for the same reason.
- **`<run_dir>/environment/repo_root.txt`** — one line, the absolute repo root `command_run`
  already computed by walking up from the config path it was given.

A byte copy rather than a re-dump, because `load_document` is pure `yaml.safe_load` (measured), so
the copy parses to a document **equal** to the one `run.yaml` embeds — and `doc` is never mutated
between the two points (measured, by grep for assignment) — while a re-dump would silently drop
every comment `init` wrote into the file.

**Why this is not the move H7d Part B forbade.** That rule is *a document may not be made
self-consistent by widening a **behaviour change***, and it was about widening `run_status` — a
**verdict** a run publishes about itself — so that a document about truncation would read
consistently. This adds an **artifact**, changes no verdict, no exit code and no status, and lands
in a directory nothing in `src/` enumerates (measured). The distinction is the whole justification
and it is stated here so a reviewer weighs it rather than discovering it.

**Why it is the right resolution of the three the scoping listed.** Having `freeze` take a config
path was refused: it makes one command take a different kind of argument than § Operation commands
says, and worse, a config does not name **which** in-progress run to freeze — `output_dir` may hold
several. Reconstructing `cfg` from `sweep.yaml` was refused on measurement: its condition entries
carry `values` and **no `selectors`**, and `resolve_condition_cfg` skips a selector path precisely
so a group cell never becomes a parameter, so an overlay built from that file would invent a
parameter no `parameter_spec` declares.

**Two document consequences, both owed by this slice.** § The other files a run writes and § Run
identity's tree gain the two artifacts. And **§ CLI reference's sentence about `resume` — *"that run
directory already contains the config it used"* — becomes true** rather than being edited to match a
hole. That sentence was the document defect the scoping found; the fix is the artifact, not a
rewrite.

**Where the artifact's boundary is drawn, and why it stops there.** It holds exactly the two facts a
mid-run command cannot otherwise obtain **and cannot compute**: the config as it was, and the repo
it came from. Everything else a comparison might want is either computable from those two
(`parameters_hash(config)`) or is a **recorded** figure that belongs to `run.yaml` — `code_hash` at
run start is not recoverable from a tree that has since moved, and that is why Decision 12 refuses
the code comparison and routes it rather than growing this artifact into a prefix of `run.yaml`.

**Disclosure, since someone will ask.** `provenance.git.repo_root` already lands in that directory
at run end, and `study add` copies the **record**, not the directory — so the redaction surface
§ What `study add` redacts describes is unchanged.

**Cost if wrong.** If the artifact is wrong to add, `freeze` cannot exist as specified and H9
inherits the same hole for `resume`. If it is right and the copy is taken from the wrong object —
a re-dump, or a copy after some later normalization — the run directory holds two configs that
disagree, and `freeze` probes under one the run never used. Fixture C is the pin.

### 8. `freeze`'s conditions — re-expanded from the copy, then cross-checked against the recorded plan

**Ruling.** `freeze` calls `expand()` on the copied config to get the `Condition` objects, builds
one `cfg` per condition with `resolve_condition_cfg`, and **cross-checks the resulting
`(index, label)` pairs against `sweep.yaml`'s recorded `conditions`**, refusing on any disagreement
(`E-FREEZE-PLAN-MISMATCH`) and on an unreadable or absent `sweep.yaml` (`E-FREEZE-PLAN-MISSING`).
It then probes **once per resolved condition** — that is its whole per-invocation cost, and the
output states the count.

**Grounds.** `expand(config)` takes the config and nothing else (measured), so re-expansion needs no
roster, no resolver and no input read — `freeze` reaches the apparatus and nothing else off the
machine. Re-derivation is nonetheless a re-derivation, and this repo's rule for that is *lineage is
recorded, not resolved*: the recorded plan is what the run is actually executing, so the cheap
cross-check is what makes the re-derivation safe. One probe **per condition** because the gate is
per condition — § The apparatus core can only observe: *"a deployment is compared against its own
first answered observation, never against another condition's"* — and the run-start round already
makes one call per resolved condition, so freezing one condition would leave the rest uncertified
while looking like a full check.

**Refused: a condition selector.** Naming one condition would be a selector flag, which
§ Everything is in the file forbids, and a mode with its own command name is not warranted for
saving one metered call.

**Cost if wrong.** Rebuilding cfgs from `sweep.yaml`'s `values` (the tempting shortcut) invents a
parameter for every group axis. Skipping the cross-check means a config copy edited by hand — or a
future non-deterministic expansion — silently probes a condition set the run is not running.

### 9. `freeze`'s baseline — the ledger replayed through the shipped `Observations`

**Ruling.** `apparatus.py` gains `replay_ledger(run_dir) -> Observations`: it reads
`apparatus/probes.jsonl` line by line and calls the **shipped `Observations.record`** for each line
whose `phase` is `run_start` or `pre_execution`, in file order. `freeze` compares its own
observations against that object with the **shipped `check_changed`** path.

**Two properties come from this and neither is re-derived.** The first-answered rule cannot drift
from the gate's, because it *is* the gate's code — the scoping's stated risk for this task (*"the
reconstruction must reproduce H7d Part B's rule exactly, or `freeze` and the gate disagree about the
same run"*) is closed structurally rather than by a test. And the per-condition scoping, the
`null → value` and `value → null` transitions, and the reflexivity carve-out for `nan` all come
along unchanged.

**`freeze` and `dry_run` lines are excluded from the baseline, deliberately.** The observations the
run's own in-memory `Observations` holds are exactly its `run_start` and `pre_execution` calls; a
`freeze` line is not one of them. Including them would let a fact **first answered to `freeze`**
become a pin the run's own gate never adopted — so a second `freeze` would report a change the run
will never fail on, which is the false stop H7d Part B's null handling exists to prevent. `freeze`
still **appends** its own line: § The apparatus files says the ledger is *"every observation"*.

**A document consequence.** § The apparatus files says `provenance.apparatus.facts` is *"the first
answered observation of each fact"* without saying *of the run's own probes* — and once `freeze`
appends, a naive replay of the whole file can disagree with the record. **That sentence gains the
qualifier**, or the next reader files it as a defect.

**Cost if wrong.** A baseline including `freeze` lines makes `freeze` able to invent a pin. A
reimplemented first-answered rule is the drift the scoping named, and it would be invisible until a
run whose fact went `value → null → different value` — the one transition that distinguishes *first
answered* from *most recent*.

### 10. `freeze`'s verdicts and exit codes

**Ruling.**

| What `freeze` found | Printed as | Exit |
|---|---|---|
| Every fact agrees with its first answered observation | the observation, per condition | `0` |
| A fact moved | `E-APPARATUS-CHANGED`, the shipped code, with condition, fact and both values | `1` |
| The probe raised, or returned something that is not an `Apparatus`, or omitted a declared key, or returned a credential | the shipped `E-APPARATUS-RAISED` / `-RETURN` / `-FACT-MISSING` / `-FACT-CREDENTIAL` / `-FACT-TYPE` | `5` for `-RAISED` (something outside the machine refused); `1` for the other four (the plugin and the template disagree) |
| A declared fact came back `null` | the shipped `W-APPARATUS-UNANSWERED` | unchanged by a warning |
| The repo's `uv.lock` no longer hashes to `environment/uv.lock` | **`W-FREEZE-LOCK-MOVED`** | unchanged by a warning |

**`E-APPARATUS-CHANGED` is reused, not re-minted.** § Errors carries one row per code, not per emit
site, and this is the same fault the gate reports — a reader who greps that code should find both
the run that stopped and the `freeze` that saw it coming. Its § Errors row gains `freeze` as a
second emit site.

**Exit `1` for a moved fact, and the asymmetry with Decision 4 is deliberate.** § Operation commands
says `freeze` *"reports a moved apparatus as a failure"* rather than a note, and § Exit codes'
`1` row already covers *"a changed apparatus fact caught before the first execution ran"*. The
difference from `diff` is what each command was asked: `freeze` asks a yes/no question about one
run's continued validity, and the answer *no* is a failure whose consequence — the next execution's
gate stopping the run — is certain. `diff` asks an open question about two runs, and a difference is
the answer rather than a fault.

**A moved lockfile is a warning and never changes the code.** Nothing mid-run re-checks the
lockfile, so an exit `1` here would tell a scheduler to act on something that will not stop the run
— and § Exit codes is explicit that *"a warning never changes the code"*. Reporting it at all is
required: § Operation commands says *"a moved lockfile is reported too and changes nothing on
disk."*

**`EXIT_EXTERNAL` gains its second reader.** H7d Part B gave `5` its first; an unreachable
apparatus at `freeze` is the same class — *"the class you retry"*.

**Every diagnostic `freeze` prints goes through a fresh credential-bearing `Collector`, and
`KeyboardInterrupt` is re-raised fresh and argument-less.** This is not a nicety: `freeze.py` is a
**new** call site for `_probe_for` and `observe_once`, in a process `command_run`'s containment does
not reach, and `observe_once`'s own docstring says the redaction *"is NOT here — the call site turns
it into a diagnostic through a fresh `Collector` carrying `credentials`."* An implementer who prints
`str(exc)` here ships the leak H7c shipped once already, by grepping for one spelling while a bare
`{exc}` site leaked to stderr. The credential set is `declared_credential_names(doc, template,
conditions)` — the same two collectors `validate` checks, from the same expanded conditions
(Decision 8) — and **narrowing it must fail a named test**: Fixture F5, a probe whose raise carries
a declared credential's value, asserting the value's absence from stderr and the code's presence.

**And the credentials are checked *before* the probe is called.** `freeze` runs in a different shell
from the run that is executing, so a credential the run holds may simply not be set here — and
without a pre-check that arrives as `E-APPARATUS-RAISED` at exit `5` **after** a metered call.
`secrets.missing_env` is the shipped checker and it is callable with exactly what `freeze` has
(measured). § Exit codes' argument for `dry-run`'s phase ordering is the precedent, verbatim: *"the
cheap objection should never be reported second, behind a metered request that was going to fail
anyway."* A missing credential is exit `5` — *"a missing credential"* is named in that row — with no
probe call made and no ledger line written.

**The five-code split is inherited, not re-decided.** `command_run`'s shipped probe containment
already returns `EXIT_EXTERNAL` for `E-APPARATUS-RAISED` alone and `EXIT_WRONG` for the other four
of `APPARATUS_CODES`, on H7d Part B's Decision 6 — read at this commit. `freeze` reuses that
mapping rather than choosing one, so the same fault gets the same number from a read command and
from the command that executes.

**Cost if wrong.** Exit `0` on a moved fact makes a scheduled `freeze` useless: the entire value of
the command is *when* you find out, and a script that cannot see the answer finds out at the same
moment it would have anyway. Exit `1` on a moved lockfile pages someone about a run that will finish
normally.

### 11. What `freeze` writes, and what it does not touch

**Ruling.** `freeze` appends **one line per condition** to `apparatus/probes.jsonl` with
`phase="freeze"`, in the shipped order `check_facts` → `append_observation` → `Observations.record`
→ compare. It does not take the run's lock, does not create or remove `lock`, does not write or
modify `run.yaml`, does not touch `environment/`, `sweep.yaml`, `allocation.json`, `executions.jsonl`
or any step directory, and does not change any status.

**Grounds.** § One execution at a time: `freeze` *"executes nothing and writes nothing but one line
to the append-only probe ledger, so it is safe against a live lock — which is the entire point of
having it."* The order is not re-decided here: H7d Part A ruled `check_facts` before
`append_observation` so a credential-carrying fact never reaches disk, and `freeze` inherits that
ruling rather than restating it.

**And `freeze` refuses a run that has ended** (`E-FREEZE-RUN-ENDED`, when `run.yaml` is present) —
the mirror of `resume`'s documented refusal, for a sharper reason: `provenance.apparatus` was
assembled from the observations that existed when the record was written and the record is never
modified, so appending an observation afterwards would leave the ledger and the record permanently
disagreeing about a run nobody can re-derive.

**Cost if wrong.** Taking the lock makes `freeze` refuse the only situation it exists for. Appending
to a finished run corrupts the one relationship § The apparatus files rests on — that the record is
a projection of the ledger.

### 12. `freeze`'s refusals — seven faults, seven codes and one warning, each with its own remedy

**Ruling.** Seven `E-FREEZE-*` codes plus one warning, split rather than collapsed, on H4d's
precedent (*one code that returned for five distinct faults became five named refusals*). Each row's
remedy is different, which is the test for whether a split is warranted:

| Code | Fault | Remedy |
|---|---|---|
| `E-FREEZE-RUN-ENDED` | `run.yaml` is present | read the record; there is nothing to freeze |
| `E-FREEZE-NO-CONFIG` | no `<run_dir>/config.yaml` | the run was started by a build before this artifact existed; it cannot be frozen |
| `E-FREEZE-NO-APPARATUS` | the resolved template declares no `apparatus_probe` | nothing to re-probe — the experiment does not measure through an apparatus |
| `E-FREEZE-LEDGER-MISSING` | a probe is declared but `apparatus/probes.jsonl` holds no `run_start`/`pre_execution` line | the run has not probed yet; there is no baseline, and probing now would pin a fact the run never adopted |
| `E-FREEZE-PROBE-MISMATCH` | the template now declares a different probe than the ledger records | `templates/**` was edited mid-run; check out the tree the run started from |
| `E-FREEZE-PLAN-MISSING` | no readable `sweep.yaml` | the run died before its plan was written |
| `E-FREEZE-PLAN-MISMATCH` | re-expanded conditions disagree with the recorded plan | the run directory or the config copy was edited; do not trust either |
| `W-FREEZE-LOCK-MOVED` | the repo's `uv.lock` no longer matches the captured copy | a warning, per Decision 10 |

**`E-FREEZE-PROBE-MISMATCH` is the one that is easy to miss.** `templates/**` is hashed but freely
editable while a run executes, and `freeze` resolves the template **now**. Probing a different
apparatus than the run measures through, and then reporting `unchanged`, is worse than not probing —
so the probe name `freeze` resolved is checked against the `probe` field the ledger records.

**`apparatus_facts` is deliberately *not* cross-checked the way the probe name is**, and the
asymmetry has a reason rather than being an oversight: the ledger records the facts a probe
**returned**, never the facts a template **declared**, so there is nothing on disk to compare a
declaration against. The consequence is real and is accepted: a fact **added** to `apparatus_facts`
mid-run makes `freeze` report `E-APPARATUS-FACT-MISSING` against a probe that is behaving exactly as
the run expects. That is the correct report of a real edit — `templates/**` moved under a live run —
and `E-FREEZE-PROBE-MISMATCH` catches the same edit's more dangerous form, where the probe itself
changed identity.

**Refused, with its route: comparing code.** `freeze` does not compare `code_hash`. The full figure
lives only in `run.yaml`, and the run ID's short suffix is a **prefix** — printing `identical` from a
prefix match is a proxy answer to an identity question, which is the move `CLAUDE.md`
§ Answering a question with a proxy is entirely about. Route: **H9**, whose `resume` must compare the
recorded hashes and which reads the same two artifacts Decision 7 adds.

**Cost if wrong.** Collapsing these into one `E-FREEZE-INVALID` reproduces exactly the fault H4d
spent a slice undoing: a reader with a run that died early, a run from an older build, and a run
whose template moved would all get the same string and none of the three remedies.

### 13. The phase vocabulary — enforced where every caller passes, by a named constant

**Ruling.** `apparatus.py` gains a module-level `PHASES: frozenset[str]` with the four names, four
module-level string constants (`PHASE_RUN_START`, `PHASE_PRE_EXECUTION`, `PHASE_DRY_RUN`,
`PHASE_FREEZE`), and `append_observation` opens with `assert phase in PHASES`. Every core call site
— `Observer._observe_one`, `command_run`'s rounds, `freeze` — passes a constant rather than a
literal.

**Grounds.** The docstring already claims the closure (*"a closed vocabulary of four … named here so
H8's and H9's callers do not mint a fifth spelling"*) and the mutation re-run at `3ed3907` wrote
`"BOGUS_FIFTH_SPELLING"` verbatim: **a safety argument in a comment is a claim needing a mutation**,
and this one is false today. The check is an `assert` and mints **no** `E-` code and **no** § Errors
row, because no config, plugin, CLI argument or artifact can reach it — the only way to violate it
is a core call site, which is the case `execute_plan`'s own shipped asserts about its callers
already cover. The named constants matter more than the assert: they make the fifth spelling
**unreachable by typo**, where the assert only converts it into a crash.

**Cost if wrong.** Under `python -O` the assert is stripped, so a build running optimized loses the
check — which is why the constants carry the property and the assert only backs them. And an assert
placed **after** the write would still raise while leaving a bogus line on disk; Mutation M6 is
sited to catch exactly that.

### 14. Package-layout homes — two new modules, and two shared pieces that stay where their truth is

**Ruling.** § Package layout gains two rows:

```
├── diff.py                    # `diff`: the five rows, hash comparison, parameter deltas
├── freeze.py                  # `freeze`: mid-run re-probe against the ledger, reported not decided
```

`cli.py` keeps only the dispatch arm and the two-path argument check, exactly as it does for
`validate` and `run` whose engines are `validate.py` and `runner.py`. The two pieces that are not
theirs alone stay beside their sources of truth: **`covered_config` in `hashes.py`**, beside the
`parameters_hash` that must agree with it (Decision 3), and **`replay_ledger` in `apparatus.py`**,
beside the `append_observation` that writes the file it reads and the `Observations` it replays into
(Decision 9).

**Grounds.** The layout's own pattern decides this rather than taste: `reproduce.py`, `docs.py`,
`study.py` and `report.py` are all per-command modules for commands with real machinery, and
`cli.py`'s gloss is `dispatch`. The scoping's two candidate hosts (`hashes.py`, `apparatus.py`) are
where the *shared* pieces land, which is the half of its suggestion that survives.

**Cost if wrong.** Putting `diff`'s delta walk in `diff.py` with its own exclusion list is the
drift Decision 3 exists to prevent. Putting the ledger replay in `freeze.py` puts the reader of
`probes.jsonl` in a different module from its writer, which is the arrangement H8a's `lineage.py`
docstring argued against for `read_run_record`.

### 15. What H8b reuses from H8a — named, and measured

| Reused | Where | Measured |
|---|---|---|
| `lineage.read_run_record(run_dir)` | both of `diff`'s run sides | Called against the fixture run directory: returns the parsed record, keyed on the directory |
| Its three refusals — `E-UPSTREAM-RECORD-MISSING`, `-UNREADABLE`, `-VERSION` | `diff`'s unreadable-record path | Read; each § Errors row gains `diff` as an emit site |
| The `schema_version` gate | `diff` refuses a record this build does not read, for free | Same |
| `provenance.upstream` | Decision 6's upstream block | Written on every run as `[]` when empty |
| `Observations`, `check_changed`, `append_observation`, `check_facts`, `observe_once`, `Observer`, `condition_key`, `apparatus_hash` | `freeze`, and `diff`'s apparatus row | H7d Part A/B, all shipped |

**Deliberately not reused, so nobody wires it in:** `resolve_run` and `resolve_step` (`diff` takes
paths, not locators — so it acquires neither `E-UPSTREAM-LOCATOR` nor `E-UPSTREAM-RUNID-MISMATCH`
and needs no `output_dir`); `UpstreamLedger` and `UpstreamResolver` (no accumulation, no per-locator
cache — `diff` reads each path once, and two identical paths is a degenerate comparison that prints
five `identical`s and exits 0); `resolves_inside_repo`. **Neither `diff` nor `freeze` performs a
repo-containment check**, and that is a refusal with grounds: the invariant binds *generate*,
*validate*, and every command that **executes**, and neither of these executes. A run directory
inside the repo cannot exist for `run` to have created, and refusing to *read* one adds nothing that
refusing to write it did not already buy.

---

## Refusals, each with its route

| Refused here | Route |
|---|---|
| `BaseReport`, `report`, `study new`/`add`, `generate report` | **H8c.** § Package layout makes `report.py` *be* `BaseReport`, so the class is not separable from the command |
| `apparatus.expected.json` | **H9.** § Reproducing on another device step 5 makes `reproduce` write it; `H7-SCOPING.md` § 10 routes it there. `freeze` writes one ledger line and nothing else |
| `reproduce`, `dry-run`, `draft`, `resume`, `demo`, `docs` | **H9.** `diff`'s draft label is built and pinned here from a `draft: true` fixture (the key is written today); H9 makes a genuine draft reachable |
| `resume` reading the two run-start artifacts | **H9.** Decision 7 writes them and makes § CLI reference's sentence true; consuming them is `resume`'s |
| `freeze` comparing `code_hash` | **H9**, with `resume`'s hash comparison — Decision 12's grounds |
| Where a `dry_run` phase line is appended, given `dry-run` *"creates nothing"* while § The apparatus files lists it as a phase | **H9**, filed. `PHASE_DRY_RUN` is named here and called by nothing |
| `report_by` under a declared `resample` | **H4 Statistics**, filed, live on seven configs |
| `max_failed_fraction`'s truncation status | **Unassigned**, filed by H7d Part B. No H8b command can reach a run's status |
| `provenance.environment.os` / `.hostname` / `.hardware` as `diff` rows | **H6.** The rows are five |
| `BaseTemplate.field_convention` | **Unassigned**, still the shape's live example |
| Any flag on either command — `--json`, a format switch, a condition selector | Refused permanently by `design-principles.md` § Everything is in the file. A mode gets a command name |
| Collapsing identical per-condition apparatus lines | Decision 2 — a branch nothing asks for, and two fixtures wide |

---

## The discriminating fixtures

**A fixture is a claim too.** Every literal below is computed by the fixture, never typed from
memory, and each entry says which.

### Fixture R — one real completed run, committed as the base record

A scaffolded project, a 24-row synthetic index, `sweep.grid` over `analysis.method` (2 conditions),
5 `seed` repeats, through `main(["run", …])`. Every figure `diff` prints for it is read back from
the record it wrote — `code_hash`, `parameters_hash`, `input_manifest_hash` are never asserted
against a literal, only against `run.yaml`'s own values and against the hash functions recomputed
over the same inputs.

### Fixture R2 — the same run, one parameter edited

Fixture R's config with `parameters.analysis.min_samples` moved and nothing else, run again. This is
the documented payoff, and the assertion is: `code_hash`, `input_manifest` identical; `uv.lock`
`not captured` (measured: no lockfile in a scaffolded project); `parameters_hash` `DIFFERS` with
**exactly one** delta line, whose path and both values are read from the two configs rather than
typed.

### Fixture L — the lockfile row's non-null path

Fixture R's project with a real `uv.lock` written before the run, so `environment/uv.lock` and
`uv_lock_hash` are non-null — and a second run after the lockfile's bytes change. **Without this
fixture the `uv.lock` row's `identical` and `DIFFERS` arms ship unpinned**, because every scaffolded
run measured above records `uv_lock_hash: None` and takes the `not captured` branch. Named because
it is the one branch the default fixture cannot reach.

### Fixture M — `metadata` versus `limits`, the coverage pin

Two records differing **only** in `metadata.description`, and two differing only in
`limits.max_failed_fraction`. The first must print `parameters_hash identical` with **zero** delta
lines; the second `DIFFERS` with exactly `limits.max_failed_fraction` and its two values. The two
arms cannot both pass if the delta walk and `parameters_hash` disagree about coverage.

### Fixture P — the probe plugin, inherited

H7d Part A's shape: a synthetic installed distribution registering a probe, a project-local template
declaring `apparatus_probe` and `apparatus_facts`, and a probe whose answers come from a file the
test writes, so a fact can be moved between calls. Two conditions, so the per-condition scope is
exercised rather than assumed.

### Fixture A1 — `apparatus DIFFERS`, two conditions moving

Two Fixture P runs whose probe answers a different `calibration_id` in the second. The assertion is
**two** detail lines, one per condition key, each carrying that condition's own old and new values
read from the two records' `provenance.apparatus.facts`. This is the fixture that would catch a
collapsing implementation and the one that catches a line printed without its condition key.

### Fixture A2 — `apparatus identical`, and the one-sided case

A Fixture P pair whose facts agree (row prints `identical` with the digest), and a Fixture P record
against a Fixture R record (`apparatus: null` on one side → `DIFFERS`, with a line naming which side
recorded none). The second arm is what pins "the row appears whenever either side has one."

### Fixture C — the run-start config copy

Fixture R's run directory, asserting `load_document(run_dir/"config.yaml") == run_yaml["config"]`
and that the copy's **bytes** equal the original config file's bytes. The two together catch a
re-dump (bytes differ, comments gone) and a copy taken from a different object (mappings differ).

### Fixture F1 — `freeze` on a constructed mid-run directory

Fixture P's run directory with `run.yaml` deleted and a `lock` file written by hand — a **constructed**
mid-run state, and the design says so rather than calling it a real one. `freeze` must exit 0 when
the probe's answers match, append exactly one line per condition with `phase: "freeze"`, and leave
the `lock` file **present and unmodified**. That last assertion is what catches a `freeze` that
takes or clears the lock.

### Fixture F2 — `freeze` sees a moved fact

Fixture F1 with the probe's answer file changed between the run and the `freeze`. Exit **1**,
`E-APPARATUS-CHANGED`, the condition key and both values in the message — and the ledger holding the
moving observation afterwards, since that is what makes the stop legible from the artifacts.

### Fixture F3 — `freeze` against a live run, in a second process

The one H8b surface that needs concurrency, and the only test allowed a handshake: a run whose probe
blocks on a sentinel file while the test invokes `freeze` against the same directory from the parent
process, with a timeout. It pins one thing the constructed fixtures cannot — that a genuinely held
lock does not stop `freeze` — and nothing else depends on it.

### Fixture F4 — each refusal, one run directory apiece

Seven directories, each differing from Fixture F1 in exactly the one way its code names: `run.yaml`
restored; `config.yaml` removed; a template declaring no probe; the ledger emptied of
`run_start`/`pre_execution` lines; a template declaring a different probe name; `sweep.yaml`
removed; the config copy's `sweep` edited so re-expansion yields a different label set. Seven
distinct codes, asserted by code and not by message text.

### Fixture F5 — a probe that raises with a credential in the message

Fixture P's plugin with a probe that reads a declared `requires_env` variable and raises carrying its
value, invoked through `freeze`. The assertion is the credential's **absence** from stderr and
`E-APPARATUS-RAISED`'s presence at exit `5` — the pair, since asserting only the absence passes
identically if nothing ran. Its sibling arm sets the variable to nothing at all and asserts the
credential pre-check reports before the probe is called, by a probe that writes a flag file and
asserting the flag's absence.

### Fixture U — the upstream block

Two runs identical in all five rows, one of which consumed an upstream through `io.reuse_from` and
one of which did not — reachable today because H8a ships the method. The assertion is the block's
presence, its `run_id`, and the "these differ only in their upstreams" line. **The five rows must
all read `identical` in this fixture**, which is what proves the block is carrying information no
row does.

---

## The mutations, each with the assertion that catches it, and each with two branches that can differ

Across recent slices several prescribed mutations could not discriminate — one *was* what the
shipped code already did, one made both branches identical, one was intercepted by an earlier
batch's assert, one was placed a line off. Each row below says what changes.

| # | Mutation | Caught by | Why the two branches differ |
|---|---|---|---|
| M1 | Print `identical` instead of `not captured` when a hash is `null` on both sides | Fixture R2's `uv.lock` row assertion, which asserts the literal string `not captured` | Measured: `uv_lock_hash` **is** `None` on a scaffolded run, so the branch is entered by the default fixture |
| M2 | Compare `provenance.apparatus.facts` directly for the apparatus row's verdict instead of `.hash` | Fixture A2's identical arm, with one record's `facts` re-serialized in a different key order | The mapping compares unequal under a reordering the hash is invariant to (`sort_keys=True`) |
| M3 | Drop the condition qualifier from an apparatus detail line | Fixture A1, asserting two lines each containing its condition key | Two conditions, two keys — one line versus two is the observable difference |
| M4 | Narrow the delta walk to `config["parameters"]` | Fixture M's second arm: `limits.max_failed_fraction` differs | Before: one delta line. After: `DIFFERS` with zero lines — and Fixture M's first arm still passes, so only the pair discriminates |
| M5 | Return exit `1` when any row `DIFFERS` | Fixture R2, asserting exit `0` with a `DIFFERS` row present | The fixture has a differing row **and** a rendered comparison, which is exactly the state Decision 4 splits from failure |
| M6 | Move `assert phase in PHASES` **below** the file write | The phase test asserts both the `AssertionError` **and** that `probes.jsonl` gained no line | The raise happens in both branches; only the ledger's content distinguishes them. This is the one-line-off shape, prescribed against deliberately |
| M7 | Remove one name from `PHASES` | A test calling `append_observation` once per name and asserting all four lines land | Four names, four lines: removing any one turns a pass into an `AssertionError` at a named phase |
| M8 | Include `phase == "freeze"` lines in `replay_ledger`'s baseline | A fixture whose declared fact is `null` in every run line and answered at the first `freeze`, then answered **differently** at a second `freeze` | With freeze lines excluded, both freezes report the fact as newly answered and exit 0; with them included, the second reports `E-APPARATUS-CHANGED`. Two different exit codes |
| M9 | Reimplement first-answered in `replay_ledger` as *most recent* | A ledger whose fact goes `r1 → null → r2` across `pre_execution` lines, then a `freeze` answering `r1` | Under *first answered*, `freeze` sees `r1` and agrees (exit 0). Under *most recent*, it sees `r2` and reports a change (exit 1) |
| M10 | Have `freeze` take the run's lock | Fixture F1's assertion that the `lock` file is byte-identical after `freeze`, plus Fixture F3 | A lock-taking `freeze` either refuses (exit ≠ 0) or rewrites the file |
| M11 | Let `freeze` proceed on a run directory holding `run.yaml` | Fixture F4's first arm: `E-FREEZE-RUN-ENDED`, and **no new ledger line** | Before: a refusal and an unchanged ledger. After: exit 0 and one appended line per condition |
| M12 | Write the run-start config with `yaml.safe_dump(doc)` instead of copying bytes | Fixture C's byte-equality assertion | The dump loses every comment `init` wrote, so the bytes differ while the parsed mappings still agree — which is why Fixture C asserts both |
| M13 | Skip the `sweep.yaml` cross-check in `freeze` | Fixture F4's last arm, whose config copy's `sweep` was edited | Before: `E-FREEZE-PLAN-MISMATCH`. After: `freeze` probes a condition set the run is not running, and exits 0 |
| M14 | Resolve `freeze`'s template with `repo_root=None` | Fixture F1, whose template is **project-local** | `get_template` returns `None` without local discovery (measured), so the run cannot be frozen at all |
| M16 | Narrow `freeze`'s credential set to the template's `required_env` alone, dropping a value's `requires_env` | Fixture F5, whose credential is declared on a **parameter value** | Before: the value is redacted from stderr. After: it appears verbatim, and the assertion is on stderr's text |
| M15 | Drop the probe-name cross-check | Fixture F4's fifth arm, whose template declares a second registered probe | Before: `E-FREEZE-PROBE-MISMATCH`. After: exit 0, reporting the wrong apparatus as unchanged |

---

## Task decomposition — 12, up from the scoping's 8

Stale in the same direction every charter on this project has been stale. The three the scoping did
not have: the run-start artifacts (Decision 7, which its § 4 listed as an open question rather than
a task), the upstream block (Decision 6, reachable only because H8a shipped `provenance.upstream`),
and the config-vs-run `not comparable` form as work rather than a ruling (Decision 5).

| # | Task | Depends on |
|---|---|---|
| 1 | `replay_ledger` in `apparatus.py`: phase-filtered replay through the shipped `Observations.record`; M8, M9 | — |
| 2 | `PHASES`, the four constants, the assert, every core call site converted; M6, M7 | — |
| 3 | `run` writes `<run_dir>/config.yaml` (byte copy) and `environment/repo_root.txt`; § The other files a run writes, § Run identity's tree, and § CLI reference's `resume` sentence; Fixture C, M12 | — |
| 4 | `freeze.py`: argument shape, the seven refusals, config load, template and probe resolution against `repo_root`, probe-name cross-check, the credential pre-check and the redacting `Collector`; Fixtures F4, F5, M14, M15, M16 | 1, 3 |
| 5 | `freeze`'s condition set: `expand` + `resolve_condition_cfg` + the `sweep.yaml` cross-check; M13 | 4 |
| 6 | `freeze`'s probe round, verdicts, exit codes, the lockfile warning, lock tolerance; Fixtures F1, F2, F3, M10, M11 | 5 |
| 7 | `covered_config` extracted in `hashes.py`; `diff`'s delta walk and rendering; Fixture M, M4 | — |
| 8 | `diff.py`: form detection, the per-side header, the five rows, the three verdicts, digest rendering; Fixtures R, R2, L, M1 | 7 |
| 9 | `diff`'s apparatus row and its per-fact lines; Fixtures A1, A2, M2, M3 | 8 |
| 10 | `diff`'s exit code and the config-vs-run form's four `not comparable` rows; the § Exit codes row edit; M5 | 8 |
| 11 | `diff`'s upstream block; Fixture U | 8 |
| 12 | Codes and homes: eight `E-`/`W-` rows in § Errors, the two § Package layout modules, `diff` and `freeze` out of `NOT_BUILT_COMMANDS`, both § Operation commands `Status` cells flipped, and the § Executability re-measurement repeating H8a's four-row table | all |

**Twelve rows, twelve tasks.** No hedge: a count that reads *"11 + 1"* is a count answering no
consistent question, which is the exact fault `CLAUDE.md`'s H8a entry spends a paragraph on and
this document quotes.

**Ordering constraints with their reasons.** Task 3 before 4, because `freeze` has nothing to read
until the artifact exists. Task 1 before 6, because the baseline is what a verdict is computed
against. Task 7 before 8, because a row's verdict and its detail must come from one projection.
Tasks 8–11 are all `diff` and share a fixture set, so they are one batch's worth even though each
has its own mutation.

---

## The consistency sweep this slice owes

Over the four documents **named**, plus `CLAUDE.md` and the feasibility analysis, never over a
filtered sweep's output — and each sweep run first against a string known to be present:

- `diff` and `freeze`'s `Status` cells in § Operation commands, and the `NOT BUILT` claim in each.
- The § Exit codes `1` row, which loses its `diff` clause — and then a sweep for the same claim
  anywhere else in the four documents.
- The three worked `diff` outputs, which must match what the code emits character for character in
  their verdict words and their `sha256:` truncation — including the ASCII `...` in `reference.md`
  and `design-principles.md` becoming `…`, which is what README already writes and what
  `CLAUDE.md` § Documentation conventions prefers.
- § Operation commands' `diff` row, which owes **all four** verdict strings — `identical`,
  `DIFFERS`, `not captured`, `not comparable`. The last two appear in no worked output anywhere, so a
  reader greps for a string the code emits and finds nothing normative.
- § The apparatus core can only observe's fenced `diff` output, which gains condition keys.
- § The apparatus files' *"first answered observation of each fact"*, which gains *of the run's own
  probes*.
- § The other files a run writes and § Run identity's tree, for the two new artifacts.
- § CLI reference's `resume` sentence, now true.
- § Package layout's two new rows.
- § Errors, for eight new rows and three amended emit-site notes.

---

## What did not survive H8a shipping

The scoping's H8b claims, re-measured at `3ed3907`:

| Claim, and where | Verdict |
|---|---|
| *"A `run.yaml` **reader** — absent"* (§ 2), and H8b task 11's ledger reader described as building from scratch | **Survives for the ledger, dead for the record.** H8a shipped `read_run_record` with three refusals and a `schema_version` gate; `diff` reuses it and mints nothing. Nothing still reads `probes.jsonl` |
| *"`provenance.upstream` is **absent, not null**"* (§ 3), and *"no document says what a run without one writes"* | **Dead.** Measured: written as `[]` on every run. H8a's decision is made, and the consequence is that § Lineage between runs' *"`diff` can tell you two runs differ only because their upstreams did"* is now an unbuilt reader of a **shipped** surface — a defect, so H8b owes Decision 6, which the scoping's 8-task list does not contain |
| *"`diff` ... needs nothing H9 builds"* (§ 7) | **Survives**, and narrows: `diff` needs nothing H9 builds **and** now needs something H8a built |
| *"`freeze` cannot get a `cfg` from the run directory"* (§ 4), with three candidate resolutions | **Survives, and is incomplete.** The config is only half the hole: the **template** carries `apparatus_probe`, and a project-local template needs a `repo_root` the run directory records nowhere either (measured through `get_template`/`discover_local`). A resolution writing only the config would have shipped a `freeze` that fails on exactly the templates H7a made possible |
| *"three candidate resolutions ... or have `freeze` reconstruct `cfg` from `sweep.yaml` plus something, which on inspection there is not enough there to do"* | **Survives, with the reason sharpened**: `sweep.yaml`'s condition entries carry `values` and **no `selectors`**, so the overlay would invent a parameter for every group axis — a measured mechanism, not a general shortage |
| *"`phase` ... the name exists; the closure does not"* (§ 2, § 8) | **Survives**, re-run at `3ed3907`: `"BOGUS_FIFTH_SPELLING"` still lands verbatim |
| *"§ Package layout ... `diff` and `freeze` have no module at all"*, with *"`hashes.py` and `apparatus.py` the plausible hosts"* | **Half survives.** The gap is real; the hosts are right for the two **shared** pieces and wrong for the commands, whose sibling precedent is `reproduce.py`/`docs.py`/`study.py`/`report.py` |
| *"H8b — 8 tasks"* | **Undercounted**, the same direction as every charter re-scoped on this project. 11 + 1 |
| *"Row counts and labels of `diff`'s output under an `apparatus` present but unchanged"* — could not be measured (§ 10) | **Ruled** in Decision 2 rather than left open: the row prints `identical`, and is omitted only when both records carry `null` |
| *"six with no remaining core-side blocker, three executable"* (`CLAUDE.md`, before H8a) | **Already dead before this slice**, and this design quotes the four-row table instead. Named here because the temptation is to write "H8b leaves six and three unmoved," which would mint a stale baseline while claiming to move nothing |

---

## What could not be measured

- **`freeze` against a genuinely live run holding its own lock.** Fixture F3 is prescribed and
  nothing was run for it here; every claim above about lock tolerance is a **read** of § One
  execution at a time plus the measurement that `append_observation` is callable from outside
  `command_run`. It is the one H8b surface that needs a second process, and it is the one most
  likely to be quietly downgraded to a constructed fixture during execution. It must not be.
- **Whether adding two files to a run directory breaks a reader nothing in `src/` has yet.**
  Measured: nothing in `src/` iterates or globs the run directory's root today. `resume` (H9) will
  read that directory, and it is the reader whose expectations this artifact is *for* — but it does
  not exist to check against.
- **What a `dry_run` phase line is appended to.** § The apparatus files lists `dry-run` as a phase
  and § Operation commands says `dry-run` *"creates nothing"*. Both cannot hold; `PHASE_DRY_RUN` is
  named here, called by nothing, and the contradiction is filed to H9.
- **Whether any real project's `diff` output is legible at width.** Every worked output in the four
  documents is one condition's worth of facts and two parameter deltas. A 12-condition sweep whose
  apparatus moved prints 12 lines per moved fact under Decision 2's no-collapse rule, and no
  document shows that shape. Said rather than designed around.
