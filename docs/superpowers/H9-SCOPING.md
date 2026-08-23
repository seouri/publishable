# H9 scoping — reproduction and the other modes

**Measured on 2026-08-23 against commit `822fe4b`** (`main` at HEAD, clean tree; verified with
`git status --porcelain` before and after every probe). **Read-only**: nothing under `src/`,
`tests/`, `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md`, `docs/feasibility-llm-growth-studies.md` or `docs/superpowers/spec-defects.md`
was edited by this pass. Every project, roster, clone, crashed run directory and template built for
it lives under the session scratchpad, **outside this repository** — H6a made the dirty gate
load-bearing, so a creation command run inside the tree would dirty what that gate reads. The
suite was run once at HEAD as a baseline: **`2973 passed, 1 skipped, 2 xfailed`**.

The charter under test is one row of
[`2026-08-08-implementation-spine-design.md`](specs/2026-08-08-implementation-spine-design.md)
§ The hardening slices: *"`reproduce`, `dry-run`, `draft`, `resume`, `demo`, `docs` — every command
that is a second entry into `run`'s own sequence. Last — `reproduce` is what reads the environment
back, so it decides the unresolved lockfile questions."* Follows
[`H6-SCOPING.md`](H6-SCOPING.md)'s shape, including its habit of saying how each claim was measured.

---

## 0. Executive summary

**H9 is 45 tasks in four parts, and it is seven commands rather than six.**

| Part | Owns | Tasks |
|---|---:|---:|
| **H9a** The re-entry seam, `draft`, `dry-run` | the phase extraction, the two modes that need no new record | 12 |
| **H9b** `resume` | what a run must make durable so a second entry can continue it | 11 |
| **H9c** `reproduce` | the lockfile decisions, the clone, the checkout, `apparatus.expected.json` | 11 |
| **H9d** `demo`, `docs`, `list-templates` | the guided arc and the managed-region machinery | 11 |

**Order: H9a → H9b → H9c → H9d.** H9a extracts the seam the next two re-enter and is the only part
that touches a shipped command's code path. H9b settles *what a run writes* so a second entry can
read it; H9c then settles the same question against a published record, which is the harder half.
H9d is last because `demo`'s stop 4 runs `dry-run` and its stop 6 prints `reproduce`, so it cannot
be written before either exists.

**Six headline measurements, each by running:**

1. **Seven commands are `NOT BUILT`, not six.** `list-templates` is the seventh, and the only live
   claim of ownership routes it to H9 — § 1.
2. **`resume`'s documented `code_hash` comparison has no possible input.** A crashed run directory
   holds no `run.yaml`, and `code_hash` is recorded nowhere else; the run ID's 7-hex prefix is the
   only surviving trace — § 4.2.
3. **The commonest crash leaves `lock` behind, so `resume` refuses with `E-RUN-LOCKED` before it can
   compare any hash** — and `E-RUN-LOCKED` is documented in none of the four documents, while
   `--force` is forbidden by the invariant — § 4.3.
4. **A run records an *untracked* `uv.lock`, and a clone of the recorded commit has none.** The
   record and the checkout `reproduce` makes can disagree about the environment, and no document
   rules which wins — § 3.2.
5. **`dry-run`'s documented promise to print "every artifact path that *would* be written" cannot be
   kept without inspecting the body of user Python**, which `design-principles.md` § Greenfield only
   forbids — § 5.
6. **README's `demo` transcript asserts the worked example's exact intervals, which `CLAUDE.md`'s own
   acceptance bar says cannot be reproduced.** `demo` is the command that would have to produce
   them — § 6.1.

**The charter's own claim survives, which is rare in this file.** *"`reproduce` is what reads the
environment back, so it decides the unresolved lockfile questions"* is right, and § 3 names them as
questions. It is right for a reason the charter does not give: **`resume`'s lockfile comparison is
answerable and `reproduce`'s is not.** A run directory holds a byte copy at `environment/uv.lock`, so
`resume` can compare; a fresh clone may hold no lockfile at all, so `reproduce` must decide between
two sources rather than compare one.

---

## 1. What is `NOT BUILT`, measured by invoking

`cli.NOT_BUILT_COMMANDS` is a dict, and a previous scoping was wrong because it read one. Every name
below was put through `main([...])` in-process, stdout and stderr captured
(`scratchpad/probe_cli.py`), including the two-token and no-argument forms:

| Invocation | Exit | What it printed |
|---|---:|---|
| `demo` | 2 | `is specified but not built … § What `demo` walks you through` |
| `demo --into /tmp/x` | 2 | the same — the flag reaches no parser |
| `docs` | 2 | `… § Operation commands` |
| `draft c.yaml` | 2 | `… § Draft runs` |
| `dry-run c.yaml` | 2 | `… § Operation commands` |
| `list-templates` | 2 | `… § Operation commands` |
| `reproduce run.yaml` | 2 | `… § Reproducing on another device` |
| `resume /tmp/rd` | 2 | `… § Resuming` |
| `generate` | 2 | `takes a generator name` — a usage error, not the unbuilt diagnostic |
| `generate experiment` | 2 | `needs a name plus --template, --input-dir, --output-dir` |
| `generate bogus n` | 2 | `unknown generator` |
| `study` / `study bogus` | 2 | `needs a subcommand: new or add` |
| `plugin` / `plugin bogus` | 2 | `plugin new takes exactly one path` |
| `nonsense` | 2 | `unknown command` — the reserved wording, correctly distinct |
| *(no argument)* | 2 | `usage: publishable <command> [args]` |

**Seven commands, zero generators.** `NOT_BUILT_GENERATORS` is empty and all four generators
(`experiment`, `step`, `template`, `report`) dispatch — H8c task 15 built the last of them.

### 1.1 `list-templates` is the seventh command, and its charter is closed

`list-templates` is not in H9's charter row. Its only chartered home was H7:
[`2026-08-14-project-local-templates-design.md`](specs/2026-08-14-project-local-templates-design.md)
says *"`list-templates` … are all H7b/H7d"*, and every H7 scoping repeated it —
`H7a-SCOPING.md` (*"it is still H7's, not H7a's"*), `H7b-SCOPING.md`, `H7b-SCOPING-2.md` and
`H7b-PartB-SCOPING.md`, the last two recording that it is *reachable* since Part A's task 9 gave
`template_names` the installed claims and that it stays `NOT BUILT` **so nobody folds it in
unbriefed**. **H7 is complete and it did not land.**

The one live claim of ownership is H8c's:
[`2026-08-21-report-study-design.md`](specs/2026-08-21-report-study-design.md) § *What is not
H8c's* reads `| list-templates | **H9**'s list, still NOT BUILT |`. So the measured position is:
one closed slice's charter, one completed slice's routing to H9, and an H9 charter row that never
received it. **H9 should take it** — its job is enumerating the merged template set with full
parameter specs, which is the same machinery `docs`'s `templates` region needs (§ 6.2), and there
is no eighth slice to hand it to. That makes H9 **seven** commands, and it is why H9d is three
commands rather than two.

---

## 2. The seam: `command_run` is one function and three commands re-enter it

**Measured**: `command_run` spans `cli.py`'s lines 2009–3926 — **1918 lines, with exactly one nested
`def`** (`_include`, the git keep-predicate H6a added). It carries a **ten-phase** sequence in
comments:

| Phase | Comment | What it does |
|---:|---|---|
| 1–2 | `resolve, walk up, load, validate` | `validate_config`, then return on any error |
| 3 | `clean src/**+templates/**` | `git_provenance`, the `E-CODE-DIRTY` gate, the entrypoint import |
| 5 | `pin hashes` | design digest, `expand`, template, credentials, roster, `code_hash`, `parameters_hash`, manifest, `uv_lock_info` |
| 4 | `build_plan` | out of numeric order in the source |
| 6 | `first creation` | `allocate_run_dir`, `RunLock`, the run-start artifacts |
| 7 | `execute_plan` | |
| 8 | `re-verify` | the aggregate phase and `verify_manifest` |
| 9 | `assemble and write` | `assemble_run_yaml` |
| 10 | the exit code | `{"completed": 0, "partial": 3}.get(status, 4)` |

**That numbering appears in no document.** Grepped `phase` over the four documents named
individually: five hits, none of them a sequence — a `probes.jsonl` field, the `E-CODE-EMPTY` row's
*"two phases earlier"*, `dry-run`'s own *"runs its phases in cost order"*, and one unrelated
`study phase` in § Naming conventions. So the phase decomposition is an implementation fact, and a
re-entry seam built on it is H9's to name.

**What the three re-entering commands need:**

| Command | Phases | The difference |
|---|---|---|
| `dry-run` | 1–5, and the probe; **never 6** | creates nothing, takes no lock |
| `draft` | all ten | phase 3's dirty gate relaxed; `draft: true` and `code_dirty: true` recorded |
| `resume` | 6–10, over a directory that already exists | phases 1–5's outputs must be *read* rather than recomputed |

**Reusable already, and none of it is inside `command_run`:** `validate.validate_config`,
`sweep.expand`, `scope.build_plan`, `units.resolve_units`, `manifest.build_manifest`,
`hashes.hashed_files`/`code_hash_of`/`parameters_hash`, `provenance.git_provenance`,
`uv_support.uv_lock_info`, `run_identity.allocate_run_dir`/`RunLock`, `runner.step_dir_for`,
`runner.execute_plan`, `run_record.assemble_run_yaml`, and `freeze`'s own reader of the two
run-start artifacts. **What is not reusable is the 1918 lines of wiring between them** — the
credential set, the group-axis realization, the holdout, the per-condition rosters, the aggregate
phase. Extracting phases 1–5 behind a value object is the prerequisite for `dry-run` and `resume`
alike, and it is **a change to a shipped command's code path**, which is the seam this project has
split on twice (H8b Decision 7, H7d Part B). It therefore goes first, behind a guard pin captured
before anything moves.

---

## 3. The unresolved lockfile questions, named as questions

The charter says `reproduce` *decides* them. It does not say what they are. Here is what a run
records, measured by reading one:

```
provenance.environment:
  manager: uv
  python_version: 3.13.7
  os: Darwin-25.5.0-arm64          # H6b
  hostname: macbookair.lan         # H6b
  uv_lock: environment/uv.lock     # a byte copy, in the run directory
  uv_lock_hash: sha256:45cd9f56…
  hardware: {cpu_count: 8}         # H6b
```

plus `environment/pyproject.toml` (a byte copy) and `environment/repo_root.txt` (one line). So
**what `reproduce` could compare** is the recorded `uv_lock_hash` against a lockfile it finds;
**what it can restore** is `uv sync --locked` in a checkout; **what it can only report** is a moved
pin, since it has no authority to rewrite anyone's lockfile.

### Q1 — Should a missing `uv.lock` refuse the run, or keep warning?

The standing entry, `spec-defects.md` § *Whether a missing `uv.lock` should refuse the run instead
of warning is unresolved*, amended 2026-08-11 to **Owner: H9**. Measured live: a project scaffolded
by `publishable new` has no lockfile, `uv_lock_info` returns `(None, None)`, and `run` prints
`W-ENV-UNLOCKED` — whose message already says *"`reproduce` will not be able to restore it"*. The
entry immediately below it records why promoting the warning would refuse **every** run of **every**
scaffolded project today: `dependencies = ["publishable"]` cannot resolve until the package is
published. **The question is live and its answer is constrained by a bootstrapping fact, not by a
principle.**

### Q2 — Which lockfile wins, the record's copy or the clone's commit?

**Measured, and named by no filing.** The dirty gate's pathspec is `HASHED_TREES` only —
`git status --porcelain -- src templates` in `provenance.git_provenance`, narrowed there by H6b's
Ruling L — so `uv.lock` may be uncommitted while `run` proceeds. Probe: wrote
`# lock: pkg-a==1.0.0` into a scaffolded project's `uv.lock` **without committing it**, ran:

- `git status --porcelain` → `?? uv.lock`, and the run exited `0`;
- the run directory holds `environment/uv.lock` with those bytes and
  `uv_lock_hash: sha256:45cd9f56…`;
- `git clone` of the same repo → **no `uv.lock` in the checkout at all**.

So `reproduce` step 4's *"Runs `uv sync --locked`, failing loudly on lockfile mismatch"* has two
candidate inputs that can disagree, and § Reproducing on another device names only one implicitly.
Three answers are available — restore from the record's copy, sync against the clone's and refuse a
hash mismatch, or refuse a run whose lockfile was never committed — and choosing is H9's.

### Q3 — What does `reproduce` do with `uv_lock: null`?

A run whose `uv_lock` is `null` recorded no environment. Nothing in § Reproducing on another device
covers it: step 4 has nothing to `--locked` against. Q1's answer decides whether this state can
exist at all, which is why the two must be answered together.

### Q4 — What does `resume` compare `uv.lock` against?

§ Resuming: *"`resume` refuses if `parameters_hash`, `code_hash`, or `uv.lock` don't match current
state."* This one is **answerable**, and that is the asymmetry the charter's ordering rests on: the
run directory holds the byte copy, so `resume` compares `environment/uv.lock` against
`uv_lock_info(repo_root)`. What is undecided is the `null` case — resuming a run that was never
pinned.

### Q5 — `diff`'s `uv.lock` row detail

`spec-defects.md` § *`diff`'s `uv.lock` row prints two digests and never names the package whose pin
moved* — **Owner: H9**, filed by H5b task 15, re-affirmed by H6a's Ruling E. Its own reproduction
recipe is inline in the entry and its carrier was verified by grep at filing time; nothing in this
pass disturbs it. Answering Q2 answers this: once H9 has ruled which lockfile is authoritative, the
detail lines are the same comparison rendered for a reader.

---

## 4. `resume` — what it must read, and how much of it exists

### 4.1 A crashed run directory, built rather than imagined

A scaffolded project whose repeat step calls `os._exit(9)` on its third execution, run for real
(4 seed repeats, 6 units). The directory it left:

```
config.yaml                                   # byte copy, run start
environment/pyproject.toml                    # byte copy, run start
environment/repo_root.txt                     # one line
environment/uv.lock                           # only when a lockfile existed
executions.jsonl                              # one line per finished execution
lock                                          # NOT removed — `os._exit` skips `__exit__`
manifest/input.json
sweep.yaml
seed47/step01_summarize_units/units.parquet    # the partial artifacts
```

**No `run.yaml`, which is the whole point** — and therefore no `code_hash`, no
`parameters_hash`, no `uv_lock_hash`, no `provenance` of any kind. Reproduced twice, on two
independent crashes.

### 4.2 `code_hash` has no recorded value for `resume` to compare against

This is the sharpest `resume` finding. § Resuming names three comparisons; the three are not alike:

| Figure | Recoverable from a run directory with no `run.yaml`? |
|---|---|
| `parameters_hash` | **Yes** — recomputable from the `config.yaml` byte copy; `hashes.parameters_hash` is a pure function of the parsed file |
| `uv.lock` | **Yes** — `environment/uv.lock` is a byte copy |
| `code_hash` | **No.** One call site in all of `src/` (`cli.command_run`), written only into `run.yaml` |

The only surviving trace is the run ID's own suffix: `allocate_run_dir` names the directory
`run_<stamp>_<short(code_hash)>`, and `hashes.short` is the first **7 hex characters**. Measured on
the crashed run: directory `run_2026-08-23T10-32-39Z_66ec8b1`, and a fresh recomputation of the
same tree gives `66ec8b1`. So H9's options are a 7-hex-prefix comparison (a real comparison, at
28 bits), a new run-start artifact recording the figure, or narrowing § Resuming's sentence to the
two figures it can actually answer. **`reference.md` § `config.yaml` and `environment/repo_root.txt`
already states the underlying fact for `freeze`** — *"`code_hash` at run start is not recoverable
from a tree that has since moved, which is why `freeze` does not compare code"* — and § Resuming
was written as though `resume` can. The two passages cannot both hold.

**A consequence § Resuming leans on falls with it.** Its draft paragraph — *"A draft's `code_hash`
is taken from the working tree, so any edit between the crash and the resume moves it and `resume`
declines"* — is a claim about a comparison that has no recorded operand.

### 4.3 The stale lock refuses before any hash is compared

`RunLock.__enter__` raises `E-RUN-LOCKED` on `FileExistsError`, and § One execution at a time is
explicit that *"a lock left behind by a killed process is reported rather than assumed dead — core
can't tell a crashed run from a live one on another node."* **Measured: the crash left `lock` in
place.** So on the commonest shape of the failure `resume` exists for, `resume` refuses on the lock,
and the hash comparisons § Resuming describes are never reached.

There is no documented route out. **Operation commands take paths and nothing else**, so
`resume --force` is forbidden by the invariant, and no second command name is specified. H9 must
rule: a document sentence telling the operator to remove the file, a command name for it, or a
liveness check the document explicitly declines to make. **This may widen the charter**, which is
why it is a decision task rather than a note.

`lock`'s contents were also measured: `{"host": "macbookair.lan", "pid": 84597}`. § One execution at
a time says it *"records the host, pid, and start time."* **There is no start time** —
`run_identity.RunLock.__enter__` writes two keys.

### 4.4 The ledger's shape disagrees with its own documentation, in both directions

§ `executions.jsonl` prints this example:

```json
{"condition": 1, "repeat": "seed17", "step": "step03_analyze", "status": "completed",
 "started_at": "…", "wall_seconds": 903.1, "attempt": 1,
 "n": {"resolved": 240, "completed": 231, "failed": 9}}
```

The line `runner.execute_plan` actually appends, read off the crashed run:

```json
{"step": "step01_summarize_units", "scope": "repeat", "condition": 0, "repeat": "seed47",
 "status": "completed", "started_at": "2026-08-23T10:32:39Z", "wall_seconds": 0.156,
 "error": null}
```

Eight keys each, six shared. **Documented and never written: `attempt`, `n`.** **Written and never
documented: `scope`, `error`.** Both directions matter to `resume`: `run.yaml`'s `execution` block
carries an `n` triple per repeat-scoped execution, and § `executions.jsonl` says the block *"is this
file folded into the scope nesting, which is why the two never disagree"* — a claim that cannot hold
for a resumed run, because the fold has no `n` to read for a triple it skipped.

### 4.5 `per_repeat` is in memory only, and a resume cannot reconstruct it

`run_record.assemble_run_yaml` builds `results.conditions[i].per_repeat[step][repeat]` from
`ExecutionResult.returned`, and `returned` — *"exactly what the step returned"*, § The two files —
**is written to no file at all**. Grepped: `per_repeat` has one producer,
`run_record.py`, reading the in-memory results list.

So a resumed run's `run.yaml` has a hole exactly where the previous attempt's completed triples
were. `aggregated` survives (it is recomputed from `units.parquet`, which is on disk); `per_repeat`
does not. **This is the one thing `resume` needs that no artifact holds**, and it is a decision
about what a run must make durable rather than a bug in `resume`. It is also why H9b is its own
part: it changes what `run` writes.

### 4.6 `allocation.json`'s "read rather than re-drawn" reader

§ Resuming states the rule and then states, in the same section, that it *"has no reader in this
build"* and that *"the command that must honour it still does not exist."* H3c-3's scoping puts it
outside its own slice by name — [`H3c-3-SCOPING.md`](H3c-3-SCOPING.md) § *What is not in this
slice*: *"`resume` and `allocation.json`'s 'read rather than re-drawn' (no reader exists)."* So it
is H9b's, uncontested.

### 4.7 Two undocumented error codes H9 acquires by measurement

`E-RUN-LOCKED` and `E-RUN-ID-EXHAUSTED` are raised in `run_identity.py` and appear **nowhere in any
of the four documents** — swept over `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md` and `docs/reference.md` named individually, `grep -c` returning `0`
for each while the same four-file list returns `1` for `E-PARAM-MISSING` as a can-fail control. They
are two of the **five** in `spec-defects.md`'s standing filing, whose owner line reads *"H9 … reads
a run's identity claim and re-derives it, and **touches neither the run lock's own refusals** nor a
creation command's overwrite guard."*

**That clause is falsified by § Resuming's own text.** `resume` is documented as refusing
*"one whose lock is held"* — § Resuming's own words, linking to § One execution at a time, which
says `run`, `draft` and `resume` *"each take it and each release it."*
`E-RUN-LOCKED` is not merely reachable from `resume` — it **is** `resume`'s documented refusal, and
it cannot be reached by `run` or `draft`, whose lock file cannot pre-exist a directory they just
`mkdir`'d. So `run_identity.py` becomes H9's surface, and two of the five codes get their rows here.
The remaining three (`E-INPUT-CHANGED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`) stay unassigned:
the manifest path and `generators/`/`scaffold.py` are still nobody's, and taking them because they
sit near a file H9 touches is the charter growing rather than the surface.

---

## 5. `dry-run` — the greenfield collision, measured

§ Operation commands: *"Validates, expands the sweep and repeat plan, builds the input manifest,
probes the apparatus, **prints every artifact path that *would* be written**. Creates nothing."*
§ Before you spend it's worked transcript ends `would write 64 artifacts under
/secure/results/cohort-pilot/run_.../`.

**What core can enumerate without executing anything**, all of it from functions that already ship:

- the fixed run-directory files — `config.yaml`, `sweep.yaml`, `manifest/input.json`,
  `environment/{uv.lock,pyproject.toml,repo_root.txt}`, `executions.jsonl`, `run.yaml`, plus
  `allocation.json` and `apparatus/probes.jsonl` when declared;
- one directory per (step, condition, repeat) triple — `scope.build_plan` then
  `runner.step_dir_for`, which already owns the degenerate-level collapse.

**What it cannot enumerate**: the artifact *files*. Every one comes from an `io.write` / `io.record`
/ `io.append` call inside a step body, whose name is a string in user Python. `reference.md`
§ Validation says so itself — *"what a step reads, calls, and returns is not a declaration. Core
never inspects the body of your Python (`design-principles.md` § Greenfield only), so … which keys it
returns all exist nowhere until it runs."* There is **no artifact declaration anywhere in the config
schema** to read instead. Even the per-unit tables are unknowable: `artifacts.finalize` writes
`units.parquet` only when a step recorded at least one row, and `measurements.parquet` only when it
passed `measurement=`.

So the sentence promises something the greenfield rule forbids, and the `64` is not derivable from
anything core knows. **H9 must narrow the promise** — step directories plus the fixed files, which
is a genuinely useful line — rather than breach the rule. This is a document change H9 owes, and it
is the kind § Misreadings warns about: *assuming a documented rule has code behind it*, here in the
harder form of a documented rule that cannot have code behind it.

### 5.1 `PHASE_DRY_RUN`, and where a ledger line would even go

`spec-defects.md` § *no build appends a `PHASE_DRY_RUN` ledger line…* — **Owner: H9**. Re-verified:
`apparatus.py` defines `PHASE_DRY_RUN` and puts it in `PHASES`; the only `phase=` call sites in
`src/` pass `PHASE_RUN_START` (`cli.py`), `PHASE_PRE_EXECUTION` (`runner.py`) and `PHASE_FREEZE`
(`freeze.py`). The entry names the contradiction between § Operation commands' *"Creates nothing"*
and § The apparatus files listing `dry_run` among the four phases.

**One thing the entry does not say, and it decides the answer**: `apparatus/probes.jsonl` lives
**inside a run directory**, and `dry-run` never creates one — phase 6 is exactly what it skips. So
there is no file to append to. The three answers are: probe and append nothing (and edit § The
apparatus files); probe and append into a location no run directory owns; or do not probe at all
(which contradicts § Exit codes' *"only a config that validates gets as far as a `5`"* and
§ Before you spend it's whole argument for the split). H9 rules.

### 5.2 What `validate` already does, so H9 does not rebuild it

`validate_config` calls `resolve_units` and `expand(doc)` for real (grepped: `resolve_units` at
`_check_units`, `expand` at four sites). It does **not** call `build_manifest` — one comment
mentions it. So `dry-run`'s phases 1–2 are `validate`, its manifest build is new-but-thin, and its
`unit-executions` line is the genuinely new arithmetic: the sum of `len(io.units)` over planned
executions, which under a `fold` or a group axis must narrow the same way `runner._handed_keys` and
`_arm_keys` narrow, or the number will not be the one the run bills.

---

## 6. `demo`, `docs`, `list-templates`

### 6.1 `demo` — every stop specified, nothing built, and one number it cannot produce

Grepped `src/` for `demo`, `correlation_pilot`, `.demo-progress`: **one hit**, the
`NOT_BUILT_COMMANDS` entry. There is a full approved design —
[`2026-08-08-demo-guided-onboarding-design.md`](specs/2026-08-08-demo-guided-onboarding-design.md),
deliverable *"documentation only"* — plus § What `demo` walks you through's six-stop table and
README § Try it's transcript. Six things measured against them:

1. **README's transcript asserts the worked example's exact statistics.** `r = 0.581 / 0.607 /
   0.412` with their intervals, `+0.026 [−0.007, 0.059]`, `−0.169 [−0.213, −0.125]`, *"intervals
   over 228 of 240 units (12 failed) · seed spread std 0.014"*. `demo` is the command that would
   have to produce them from data it generates. **`CLAUDE.md` § Purpose and acceptance bar already
   ruled this class of test out** — *"the pinned intervals … were checked against a synthetic
   228-unit table that is not in this repository, so exact reproduction would mean
   reverse-engineering a dataset to hit three interval targets."* And `CLAUDE.md` § The worked
   example forbids changing the numbers. **So H9 must rule where the acceptance bar ruled: the
   transcript is illustrative and says so, or `demo` engineers a dataset the bar rejects.** This is
   a charter-level decision, not a detail.
2. **A `run` in the demo repo must fail 12 of 240 units on purpose**, because the transcript says
   it does — the generated pipeline and the generated data have to be designed together.
3. **README says "a three-step pipeline"** while `reference.md`'s worked example (`cohort-pilot`) is
   four steps. `correlation_pilot` is a separate experiment and the two are allowed to differ, but
   H9 owes a three-step pipeline that produces a baseline-plus-two-condition sweep.
4. **`.demo-progress` is documented as *"listed in the generated `.gitignore`"*.** Measured:
   `scaffold.GITIGNORE` holds `.env`, `__pycache__/`, `*.py[cod]`, `.venv/` — **no
   `.demo-progress`**. A documented line with no code behind it.
5. **Stop 4 runs `dry-run` and stop 6 prints `reproduce`** — the ordering constraint that puts H9d
   last.
6. **The design document's stop 2 says *"the `conditions` and `replication` blocks"*** while
   § What `demo` walks you through says *"this config's `sweep` and `replication` blocks"*. There is
   no `conditions` block in the schema. The specification is right and the design is stale; a spec is
   not retro-edited, so H9 must build from `reference.md` and not from the design's table.

### 6.2 `docs` — two managed regions exist, four are documented, and the machinery is zero

Grepped `publishable:begin` over `src/` and the four documents. **`src/` has two**, both in
`scaffold.README`: `overview` and `experiments`. **The documents specify four**: `overview`,
`credentials`, `experiments` (§ The generated README) and `templates` (§ Templates). There is **no
region parser or rewriter anywhere in `src/`** — `docs` is built from nothing.

The scaffolded README, generated for real and read back, diverges from § The generated README in
four ways beyond the missing region:

| § The generated README | What `publishable new` writes |
|---|---|
| `uv sync` **and** `cp .env.example .env    # then fill in the values below` | `uv sync` alone (though `.env.example` **is** written) |
| a `credentials` region holding a two-column table | no region and no section |
| `## Experiments` **inside** the `experiments` region, with a `Name \| Template \| Run` table | `## Experiments` **outside** the region, prose inside it |
| a `## Reproducing a published result` section with the `reproduce` invocation | absent |

Two of these are already filed as `NOT BUILT` halves in § Generators — `generate experiment`'s
experiments-table row and its `required_env` merge, and `generate template`'s parameter table, the
last of which § The generated README notes *"is different in kind"* because the scaffolded README
declares no region for it at all. **All of it is H9d: a region cannot be regenerated before it
exists.**

### 6.3 `list-templates` and the repo-root problem

`list-templates` must enumerate the merged set — core's `generic`, entry-point-registered plugin
templates, and **project-local** ones — with full parameter specs. The first two need no repo; the
third needs `discover_local(repo_root)`. See § 7.2: it takes no path, so it has no repo to walk up
from.

---

## 7. The invariant, checked command by command

*"Operation commands take paths and nothing else. No parameter flags, no selectors, no
behavior-changing env vars. … Only creation commands (`new`, `plugin new`, `generate`/`init`,
`study new|add`) take arguments beyond a path."* The normative form is
`design-principles.md` § Design goals: *"No **operation** command takes any argument other than a
path — creation commands take what is needed to bring something into existence, and they are the
only exception."* Note that the normative sentence is **categorical** while `CLAUDE.md`'s is an
**enumeration**; that difference is the first finding below.

| Command | Table | Arguments | Verdict |
|---|---|---|---|
| `reproduce` | Operation | one path (`run.yaml` **or** config) | **Compliant.** § Reproducing on another device makes the point explicitly — *"No `--into`: the destination is derived"*, and *"`--input-dir` and `--output-dir` would only duplicate what the config already expresses"* |
| `dry-run` | Operation | config path | Compliant |
| `draft` | Operation | config path | Compliant |
| `resume` | Operation | run directory | Compliant — and § CLI reference argues for the *directory* rather than a config-plus-identifier pair |
| `demo` | **Creation** | *(none)*, `[--into DIR]` | **See 7.1** |
| `docs` | Operation | *(none)* | **See 7.2** |
| `list-templates` | Operation | *(none)* | **See 7.2** |

### 7.1 `CLAUDE.md`'s enumeration omits `demo`, which `reference.md` tables as a creation command

`publishable demo` is a **row of § Creation commands**, whose lead sentence is *"These take a name
plus what's needed to bring something into existence."* Under `design-principles.md`'s categorical
rule, `--into DIR` is therefore legal — a creation command taking what it needs. Under `CLAUDE.md`'s
enumeration (`new`, `plugin new`, `generate`/`init`, `study new|add`) it is not, because `demo` is
not in the list. **The enumeration is narrower than the normative rule it summarizes**, and H9 is
the slice that builds the command it omits. This is a `CLAUDE.md` edit, not a design change — but
it must be made deliberately, because the alternative reading (that `--into` is an illegal flag)
would delete a documented argument from a documented table.

### 7.2 `docs` and `list-templates` take no path, and the repo-walk-up invariant has no input

Both sit under § Operation commands, whose lead reads *"These take paths and nothing else"* — and
both are specified with `*(none)*`. Zero arguments is arguably inside *"nothing else"*, but the
sentence reads as requiring a path, and something sharper follows from it. `CLAUDE.md`'s invariant:
*"Which repo is decided by a **walk-up from the path the command was given**, not from the working
directory."*

`docs` must rewrite the README of *a* repository, and `list-templates` must discover *a*
repository's `templates/**`. **Neither is given a path, so neither has the input that invariant
names**, and the only remaining source is the working directory — which the same sentence forbids.
Precedent exists and cuts against a silent cwd walk-up: `spec-defects.md` § *`E-NAME-DIR` is
silently skipped when `validate` is run from inside the config's own directory* is the same class of
fault. H9 must rule: give both a path argument (a document change to two rows), state a cwd-based
exception and scope it, or accept that `list-templates` enumerates only the installed set and never
a local template. **The third answer is the cheapest and it is a real narrowing**, since local
templates are the case § Templates says path discovery exists for.

---

## 8. The other filings H9 owns, each re-verified rather than carried

Six entries in `spec-defects.md` name H9 as owner. Every one was re-checked at `822fe4b`:

| Entry | State at HEAD |
|---|---|
| *Whether a missing `uv.lock` should refuse the run instead of warning is unresolved* | **Live.** `W-ENV-UNLOCKED` fires; the bootstrapping entry below it still holds — a scaffolded project cannot resolve a lockfile. § 3, Q1 |
| *`discover_local`'s bytecode cache can serve a STALE `templates/*.py`…* | **Reproduced.** Wrote `templates/s_assay.py` with `apparatus_probe = "f_probe"`, called `discover_local`, overwrote the same path with `"g_probe"`, called again → **`f_probe`**, no exception, no diagnostic. § 8.1 |
| *a same-size, same-second rewrite of a report override is silently not picked up* | **The same root cause at a third call site** — `report.render_with_override` and `base_experiment.load_experiment` both purge `sys.modules` and re-import, and neither invalidates the `.pyc`. Not re-perturbed; the entry's own recipe is byte-length-controlled and its cause is `SourceFileLoader`'s `(mtime, size)` validation, which § 8.1's probe demonstrates directly |
| *a plain `parameters` edit to the run-start `config.yaml` copy changes the cfg `freeze` probes under* | **Live**, and its own *check its owner must make* is H9b's: `parameters_hash` is computed once at `run.yaml` assembly, so no run-start artifact records it. `resume`'s answer to Q "did this config change since run start" is what closes it, or a run-start `parameters_hash` artifact is warranted independently — H8b declined to build toward either |
| *no build appends a `PHASE_DRY_RUN` ledger line…* | **Live.** Re-grepped: zero call sites. § 5.1, plus the observation the entry lacks — the ledger lives inside a run directory `dry-run` never creates |
| *`diff`'s `uv.lock` row prints two digests and never names the package whose pin moved* | **Live**, re-affirmed by H6a Ruling E. § 3, Q5 |

### 8.1 The bytecode-cache defect is **one** fault at **three** call sites

`discover_local._import_file`, `report.render_with_override` and `base_experiment.load_experiment`
all build a spec for a file whose `__pycache__` entry CPython validates against `(mtime, size)`.
The measured probe above is the direct evidence: `f_probe` served twice, from two different files at
the same path, in the same second, in one process. **H9 fixes it once and it closes two filings.**
The entry's option (a) — an explicit `SourceFileLoader`, or a scoped
`sys.dont_write_bytecode = True` — is the one H9 should weigh, because `resume` resolves the same
project-local template from the same two run-start artifacts `freeze` does and would inherit the
identical hazard; option (b), documenting the weaker per-process property, is the fallback and is
no longer anyone else's to take.

---

## 9. Exit codes — the readers, and which H9 must supply

| Code | Documented meaning | Readers in `src/` at HEAD |
|---:|---|---|
| `0` | Succeeded | many |
| `1` | The thing you asked about is wrong — *"a `resume` whose hashes moved"* included | many |
| `2` | The invocation is wrong | `_dispatch`, `_report_not_built`, every usage error |
| `3` | **`run`, `draft`, `resume` only** — `status: partial` | **one**: `command_run`'s final `{"completed": 0, "partial": 3}.get(status, 4)` |
| `4` | **`run`, `draft`, `resume` only** — `status: failed` | **one**: the same line |
| `5` | Outside the machine refused — *"an unreachable apparatus, a missing credential, **a clone or `uv sync` that failed**"* | `command_run` (three sites) and `freeze` (two). **Nothing reads the clone/`uv sync` half** |

**What H9 must supply:** `draft` and `resume` are named in `3`'s and `4`'s own rows and have no
reader for either; `dry-run`'s cost-ordered `1`-then-`5` (§ Exit codes' own paragraph) has no reader;
and `reproduce` is the sole reader `5`'s *"a clone or `uv sync` that failed"* clause is waiting for
— the same shape as `EXIT_EXTERNAL` gaining its first reader in H7d Part B. **No new code is
needed.** `1`'s row already anticipates `resume`, and `5`'s precedence rule (*"when both apply, `5`
wins"*) already covers a `reproduce` that fails externally. H9 mints nothing here, which is worth
stating because three of the last five slices minted codes.

---

## 10. Documented rows and claims checked against the code

Every claim below was grepped before it was written, over files named individually, never over
`*.md`, and never with the output filtered. **Newline-insensitively where a phrase could wrap**: the
`uv.lock`, `code_hash` and lock-file claims were each searched by a distinctive short fragment
(`refuses if`, `host, pid`, `every artifact path`) rather than by a full sentence a `grep -F` would
miss across a line break, and each hit was read and attributed individually rather than reconciled
against a list of expected homes.

| Documented | Code |
|---|---|
| § Resuming: *"refuses if `parameters_hash`, `code_hash`, or `uv.lock` don't match current state"* | No command compares any of the three against a recorded value. `code_hash` has **one** call site in `src/` (`cli.command_run`) |
| § One execution at a time: `lock` *"records the host, pid, and start time"* | `RunLock.__enter__` writes `{"host", "pid"}` |
| § `executions.jsonl`'s example line | `attempt` and `n` are never written; `scope` and `error` are written and undocumented (§ 4.4) |
| § Operation commands: `dry-run` *"prints every artifact path that would be written"* | Unbuildable without inspecting step bodies (§ 5) |
| § What `demo` walks you through: `.demo-progress` *"listed in the generated `.gitignore`"* | `scaffold.GITIGNORE` does not list it |
| § The generated README's three managed regions | `scaffold.README` has two (§ 6.2) |
| § The two files' `provenance` key order | **The code's order is pinned by a shipped guard-pin arm** — `tests/test_cli.py`'s H8a arm B asserts `list(provenance.keys()) == [...]` with `publishable_version`, `plugin_versions` **before** `units`, where § The two files puts them last. A real run confirms the code's order. The pin is authorized-editor-only, so the **document** is the side that moved; not H9's charter, recorded so it is not rediscovered as a code defect |
| § The apparatus files: the ledger is written *"at `dry-run`"* | No `PHASE_DRY_RUN` call site (§ 5.1) |
| § Reproducing on another device step 3: verify the checked-out tree's `code_hash` | Achievable **within one hash definition** and not across the H6a boundary (§ 11) |
| `apparatus.expected.json` | Written by nothing and read by nothing; the whole file is H9c's |

**Two things this pass looked for and did NOT find**, reported because a zero is a claim: no
§ Validation row describes a `dry-run`, `draft`, `resume`, `reproduce`, `demo` or `docs` check
(swept § Validation and § Errors `validate` reports for each of the six names — zero hits), and no
`E-` code in `src/` is emitted by any of the seven commands, since none of them dispatches.

---

## 11. What `reproduce` can verify, and the boundary it cannot

**Measured, both directions.**

**Step 3 works within one hash definition.** Cloned the crashed project's repo (`git clone`) and
recomputed `code_hash` on both sides with `command_run`'s own predicate:

```
crash/proj  files=6  short=66ec8b1
clone       files=6  short=66ec8b1   # identical
```

Six files each, the same six. **Why it reproduces** is worth stating rather than merely observing:
the H6a keep-predicate asks git in whatever checkout it is run in, and `.gitignore` is a **tracked**
file that travels with the commit — so a faithful clone asks the same question of the same rules and
gets the same answer. A run's clean-tree gate also guarantees no untracked file under either hashed
tree was folded in.

**Step 3 fails across the H6a boundary, on an unchanged tree.** The same tree, with a git-ignored
`src/cohort_pilot/debug.log` present:

```
pre-H6a  (include=None)  e09ab27
post-H6a (git-aware)     66ec8b1
```

A pre-H6a record therefore carries a figure a post-H6a `reproduce` will not reproduce, and § Reproducing
on another device's step 3 says a mismatch means *"a rewritten or force-pushed history."* **H6a's
Ruling C stated this ruling's cost for a `diff` reader only** — *"sees `uv.lock DIFFERS` beside
`code_hash DIFFERS` and cannot tell whether the code moved or the definition did"* — and refused a
marker on the ground that `uv.lock` is the carrier. That reasoning is sound for `diff`, which
compares two records. It does not transfer to `reproduce`, which compares a record against a tree
and has a *published verdict* to render: **"the history was rewritten"** is a serious accusation to
make about a faithful clone. H9c must decide whether `reproduce` says so, hedges the wording, or
reads `uv_lock_hash` to date the record. **This consequence is stated in no document and no filing**;
it is new here rather than carried.

**And two things about the config write-back.** `run.yaml`'s `config` is the **parsed dict**
(`run_record.assemble_run_yaml`'s `"config": config`), so writing it back out re-serializes it and
**every inline comment `init` wrote is gone** — the comments § The one config file calls *"the
documentation"* of the file. The alternative already exists: the run directory holds `config.yaml`
as a **byte copy**, beside the `run.yaml` `reproduce` was handed. § Reproducing on another device
says *"Writes the embedded config"*, so H9c must rule which source it writes from — and either way
it must inject `# REQUIRED: set to your local copy` beside two blanked paths.

**A third: `provenance.git.remote` can be `null`.** Measured on a scaffolded project: `remote: null`,
with `run` exiting `0`. `reproduce` step 1 *"Reads `provenance.git.remote` … and clones it"* — there
is nothing to clone. § What `demo` walks you through acknowledges the state for the demo repo
(*"the demo repo has one local commit and no remote — so running it here would fail on the first
step"*) and no document gives it a diagnostic or an exit code. H9c mints one, or rules that `5`'s
*"a clone … that failed"* covers it.

---

## 12. What H9 must NOT fold in

**H3c-3's remaining 14 is the only slice after H9**, so anything H9 declines and H3c-3 does not own
is unowned, and saying which is which is part of the deliverable.

| Not H9's | Where it goes |
|---|---|
| Folds and holdouts **inside cells** — the phase hoist of `_resolved_group_axes`/`arm_members`, the cell decomposition, `fold_basis` per cell, `_fold_k`'s cell clause, `sweep.yaml`'s per-cell `partitions`, the H3d retrofit's two halves | **H3c-3's remaining 14**, enumerated in [`H3c-3-SCOPING.md`](H3c-3-SCOPING.md) § 6 tasks 2–17. H9a's phase extraction moves *phases*, and it must not move the arm-plan resolution H3c-3's task 2 owns — **they touch the same function and are different moves.** State it in H9a's design |
| `E-DATA-HOLDOUT-CELLS` / `E-REPL-FOLD-CELLS` retirement | **H3c-3**, per the spine's *Order, amended against outside evidence* |
| `E-INPUT-CHANGED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS` § Errors rows | **Unassigned, with the reason.** The manifest path and `generators/`/`scaffold.py` are neither H9's nor H3c-3's surface. H9 takes only `E-RUN-LOCKED` and `E-RUN-ID-EXHAUSTED`, and only because `resume`'s documented refusal **is** the first (§ 4.7) |
| `BaseTemplate.field_convention`'s missing reader | **Unassigned.** Re-verified at `822fe4b`: three hits in `src/`, none a reader. Still the sole standing example of *an unbuilt reader of a shipped surface*, and H9 creates no new one |
| `report_by` under `resample` keeping a `t_over_units` interval | **Unassigned**, filed against H4, live on C1–C3. `report` and `reproduce` both render what the record holds |
| `max_failed_fraction`'s truncation status semantics | **Unassigned**, filed by H7d Part B with a written justification in a shipped test's docstring. `resume` re-enters the same loop and must not weaken that pin to make a resumed truncation tidier |
| `validate_config`'s bare `except ContractError` around `find_repo_root` | **Unassigned.** H9 does not touch `validate`'s template-discovery path — but note § 7.2: if H9 rules that `docs`/`list-templates` take a path, the walk-up they use is `find_repo_root`, and the *next* slice to hold this filing should be re-checked then |
| `limits.min_units_per_cell` having no reader | **Unassigned**, and explicitly outside H3c-3 too (its § 7) |
| A `W-PARAM-UNSET` equivalent for **core-schema** omissions | **Unassigned**, filed by H6a Decision 10 |
| A marker for the hash definition in `run.yaml` | **Refused by ruling** (H6a Ruling C). H9c may not mint one; § 11 is a decision about `reproduce`'s **wording and verdict**, not about a new key |
| A fourth hash, or a `provenance` key naming core's version | **Refused by ruling** (H6a Decision 12 / Ruling E). `uv.lock` is the carrier |
| A `gpu` key under `provenance.hardware` | **Refused by ruling** (H6b Decision 5). The route is an `apparatus_probe` |
| Widening `E-CODE-DIRTY`'s pathspec to the repository root | **Declined and unassigned** (H6b Decision 12). **`draft` must not close it sideways**: relaxing the gate for a draft is not the same as widening what the gate covers, and H9a's design must say so, because they are one line apart |

---

## 13. Decomposition — 45 tasks, four parts, every task named

Sized at the grain of H8a (10), H8b (8), H8c (12), H6a (13 shipped), H5b (16 shipped),
H3c-3 (17 measured). Those are calibration, not targets: the count below is the number of tasks
named, counted with `grep`, not a figure landed near a precedent.

### H9a — the re-entry seam, `draft`, `dry-run` (12)

| # | Task |
|---:|---|
| 1 | **The guard pin, captured before anything moves.** Arms: `run.yaml` key-for-key over a real run; the `executions.jsonl` line's key set; `sweep.yaml`; the run-directory file list; the exit-code mapping; and the § CLI reference table parser's `("dry-run", "NOT BUILT")` assertion. Every arm gets a named sole editor or an explicit **NONE**, with each authorized post-edit state written now |
| 2 | **Ruling: what a second entry may share.** The ten-phase sequence is an implementation fact in comments (§ 2). Decide whether it becomes named functions, whether the phase names enter `reference.md` at all, and what the extraction may not move — H3c-3's arm-plan hoist named explicitly (§ 12) |
| 3 | **The extraction**: phases 1–5 behind one value object, behaviour-preserving, the guard pin unedited. The batch review's job is a **real-command** read of `run.yaml` key by key, not a direct call |
| 4 | **`draft`**: the dirty gate relaxed, `draft: true` and `git.code_dirty: true` written, exits `3`/`4` reached from a second command. Every reader already ships — `E-REPORT-DRAFT` (`report.py`), `study`'s bundle flag, `diff`'s per-side label — so this is **the writer for three shipped readers** |
| 5 | **`draft`'s positive controls**: `report` refusing a **real** draft and `study add` flagging one, both of which are today testable only against synthesized records (H8c Decision 7 says so in its own docstring). A fixture per reader, each shown able to fail |
| 6 | **Ruling: what `dry-run` may print** (§ 5). The greenfield collision, the narrowed promise, and § Before you spend it's `64 artifacts` — restated as what core can derive, or removed |
| 7 | **Ruling: `PHASE_DRY_RUN`** (§ 5.1) — the ledger lives inside a run directory `dry-run` never creates. Closes the H9-owned filing either way, and decides whether `replay_ledger`'s two-phase filter widens |
| 8 | **`dry-run`'s phases**, in cost order: validate → manifest → probe, exiting `1` before the probe and `5` at it |
| 9 | **`dry-run`'s `unit-executions`** — the sum of `len(io.units)` over planned executions, narrowed the way `runner._handed_keys` and `_arm_keys` narrow, with a fold fixture and a group-axis fixture that give different answers |
| 10 | **`dry-run` creates nothing and takes no lock**: a pin that the filesystem is byte-identical across the whole command, including against a run directory holding a live lock (§ One execution at a time says pointing one at a live run is *"as ordinary as reading the ledger"*) |
| 11 | **The three tables**: § Operation commands' `dry-run` and `draft` rows, § Exit codes' `3`/`4`/`5` rows, `NOT_BUILT_COMMANDS`, and arm 1's `("dry-run", "NOT BUILT")` edited by **this** named task and no other |
| 12 | **Consistency passes** — mechanical over every edited `*.md`, cross-document over the four documents; `spec-defects.md`'s `PHASE_DRY_RUN` entry closed against the code |

### H9b — `resume` (11)

| # | Task |
|---:|---|
| 1 | **Ruling: what `resume` compares** (§ 4.2). `code_hash` has no recorded operand; choose the 7-hex prefix, a run-start artifact, or a narrowing of § Resuming — and reconcile it with § `config.yaml`'s already-true sentence about `freeze` |
| 2 | **Ruling: the stale lock** (§ 4.3). `E-RUN-LOCKED` fires before any hash comparison on the commonest crash; no route out is documented and `--force` is forbidden. May widen the charter |
| 3 | **Ruling: the ledger's shape** (§ 4.4) — `attempt` and `n` documented and unwritten, `scope` and `error` written and undocumented. Decide write-them versus edit-the-example, against § `executions.jsonl`'s *"the two never disagree"* claim |
| 4 | **Ruling: `returned` durability** (§ 4.5). `per_repeat` is *"exactly what the step returned"* and lives only in memory; a resumed `run.yaml` has a hole. A ledger key, or a documented hole |
| 5 | **`resume` itself**: read `sweep.yaml` rather than re-derive, skip `completed` triples, take the lock, refuse a directory holding a `run.yaml`, append into the same ledger and tree |
| 6 | **`attempts` from the ledger** — the count of a triple's records — plus the two rules § Resuming rests on: `io.units` never narrowed, and `io.recorded_keys` non-empty only on a resume. A fixture where a triple has three records and `attempts: 3` while its neighbour stays `1` |
| 7 | **`allocation.json` read rather than re-drawn** (§ 4.6) — the reader the document says does not exist, over a **drawn** axis where a second draw would differ |
| 8 | **`E-RUN-LOCKED` and `E-RUN-ID-EXHAUSTED`** § Errors core raises rows, one row per code covering every emit site, and the `spec-defects.md` five-codes filing amended to three with the reason |
| 9 | **The run-start `parameters_hash` question** (§ 8, the `freeze` filing) — whether `resume`'s comparison closes it for `freeze` too, or a run-start artifact is warranted independently. H8b declined to build toward either; H9b decides |
| 10 | **The bytecode-cache fix** (§ 8.1), once, at all three call sites, with a positive control that a same-second same-size rewrite is now seen — closing **two** H9-owned filings |
| 11 | **§ Resuming, § CLI reference, § Exit codes, `spec-defects.md`, `CLAUDE.md`, and both consistency passes** |

### H9c — `reproduce` (11)

| # | Task |
|---:|---|
| 1 | **Ruling: Q1, the missing lockfile** (§ 3) — refuse or warn, against the bootstrapping fact that no scaffolded project can resolve one. Closes the oldest H9-owned entry, and either affirms `W-ENV-UNLOCKED` with the § Design goals footnote its own filing proposes, or promotes it |
| 2 | **Ruling: Q2 and Q3, which lockfile wins** (§ 3) — the record's byte copy, the clone's commit, or a refusal; and what `uv_lock: null` does |
| 3 | **Ruling: the H6a boundary** (§ 11) — whether `reproduce` accuses a faithful clone of a rewritten history, hedges, or dates the record. **No marker may be minted** (H6a Ruling C) |
| 4 | **Ruling: `remote: null`** (§ 11) — the diagnostic and whether exit `5` covers it |
| 5 | **The clone and the detached checkout**: destination derived from repo name and run ID, no `--into`, one git operation |
| 6 | **`code_hash` verification in the checkout** (measured achievable, § 11), with a positive control that a rewritten file is caught and a negative control that a faithful clone passes |
| 7 | **`uv sync --locked`**, and `EXIT_EXTERNAL`'s first reader for the clone/sync half of code `5`'s documented meaning |
| 8 | **The config write-back** (§ 11): which source, the two blanked paths, the `# REQUIRED` markers, and what happens to `init`'s inline comments |
| 9 | **`apparatus.expected.json`** — written once from `provenance.apparatus.facts`' per-condition mapping, never rewritten, and the *first-probe* comparison against it, on the gate's own terms so an unanswered original fact does not fail a reproduction that answers it |
| 10 | **The closing transcript**: `.env.example`, the `required_env` list, and the apparatus block § Reproducing on another device prints verbatim |
| 11 | **The config-operand form** (steps 4 onward, `code_hash` explicitly not verified and said so), plus § Reproducing on another device, § Reproducing a published result, § CLI reference, and both consistency passes |

### H9d — `demo`, `docs`, `list-templates` (11)

| # | Task |
|---:|---|
| 1 | **Ruling: README's `demo` transcript** (§ 6.1) versus `CLAUDE.md` § Purpose and acceptance bar. The transcript is illustrative and labelled, or `demo` engineers a dataset the bar rejects. **The worked example's numbers may not move** |
| 2 | **Ruling: `docs` and `list-templates` take no path** (§ 7.2) — the repo-walk-up invariant has no input. Give both a path, scope a cwd exception, or narrow `list-templates` to the installed set |
| 3 | **Ruling: `CLAUDE.md`'s creation-command enumeration omits `demo`** (§ 7.1), whose `--into DIR` § Creation commands tables. A `CLAUDE.md` edit, made deliberately |
| 4 | **The managed-region machinery**: parse `publishable:begin/end`, rewrite one region, leave every byte outside it untouched. A pin that hand-written text survives, and that an unbalanced marker is a diagnostic rather than a silent no-op |
| 5 | **The `credentials` region** — absent from `scaffold.README` entirely — plus `generate experiment`'s `required_env` merge, the § Generators half filed as `NOT BUILT` |
| 6 | **The `experiments` region as a table**, `## Experiments` moved inside it, and `generate experiment`'s row merge — the other § Generators `NOT BUILT` half |
| 7 | **The `templates` parameter-table region**, which the scaffolded README declares nowhere, plus `generate template`'s write into it |
| 8 | **`list-templates`**: the merged set with full parameter specs, honouring task 2's ruling about which repo it may see |
| 9 | **`demo` stops 1–2**: the synthetic generator, `src/correlation_pilot/`, `configs/correlation-pilot/config.yaml`, `git init` and the first commit, `~/publishable-demo-data/` outside the repo, `.demo-progress` **and its `.gitignore` line** |
| 10 | **`demo` stops 3–6**: proceed-or-quit only, no pause that can alter the config, headless straight-through with no flag, `q` printing the remainder, `--into DIR` resuming a directory that holds a `.demo-progress`, and stop 6 printing rather than running `reproduce` |
| 11 | **The three tables, the four documents, `spec-defects.md`, `CLAUDE.md`, both consistency passes, and § Executability on this build** — one dated entry, the table repeated character for character, **no new number**: none of the nine feasibility configs declares a `study`, a `fold`, a group axis or an `apparatus_probe`, and **H9 unblocks zero of them** — every command it builds is a second entry into a sequence those configs already reach or do not |

**Charter accuracy: the row's six names all survive, and it is missing one command and every seam.**
Missed by the charter: `list-templates` (§ 1.1); the phase extraction that makes "a second entry"
mean anything (§ 2); the durability changes to what `run` writes that `resume` requires (§ 4.4–4.5);
the greenfield narrowing `dry-run` needs (§ 5); the four managed regions of which two exist (§ 6.2);
the two-command hole in the path invariant (§ 7.2); and six owned filings. **6 named → 7 commands
and 45 tasks**, the same direction every re-scoping in the spine has moved.

---

## 14. Disagreements with the record found by this pass

Reported individually rather than counted, per `CLAUDE.md`'s note that six consecutive slices
claimed zero and all six were wrong.

1. **`spec-defects.md`'s five-undocumented-codes filing says H9 *"touches neither the run lock's own
   refusals."*** § Resuming makes `E-RUN-LOCKED` **`resume`'s own documented refusal**, and `run` and
   `draft` cannot reach it. Two of the five are H9's (§ 4.7).
2. **The spine's H9 row and H8c's design disagree about `list-templates`**, and the H7 family — its
   only chartered home — closed without it (§ 1.1).
3. **H6a's Ruling C stated its cost for a `diff` reader and not for `reproduce`**, whose step 3
   renders a *verdict* about a rewritten history rather than a comparison (§ 11). New here.
4. **§ Resuming and § `config.yaml` and `environment/repo_root.txt` contradict each other** about
   whether a mid-run command can compare `code_hash` (§ 4.2).
5. **§ Operation commands' `dry-run` promise cannot be kept under § Greenfield only** (§ 5).
6. **§ The apparatus files lists a `dry_run` ledger phase for a command that creates no run
   directory to hold the ledger** — the half the standing filing does not state (§ 5.1).
7. **`lock` records two keys, not the three § One execution at a time names** (§ 4.3).
8. **§ `executions.jsonl`'s example line disagrees with the code in both directions** (§ 4.4).
9. **§ The generated README specifies three managed regions and `scaffold.README` writes two**, with
   four further drifts in the same file (§ 6.2).
10. **`.demo-progress` is documented as listed in the generated `.gitignore` and is not** (§ 6.1).
11. **§ The two files' `provenance` key order disagrees with a shipped guard-pin arm**, which is
    what makes the document the side that moved rather than the code (§ 10). Not H9's charter;
    recorded so it is not rediscovered as a defect.
12. **`CLAUDE.md`'s creation-command enumeration is narrower than `design-principles.md`'s
    categorical rule**, and omits the command H9 builds (§ 7.1).
13. **The `demo` design document's stop 2 names a `conditions` block that does not exist in the
    schema**, where § What `demo` walks you through says `sweep` (§ 6.1). A spec is not
    retro-edited; H9 builds from `reference.md`.

---

## Correction, 2026-08-23, made before dispatch — H9b is 15, and the total is 49

Appended rather than edited, so the dated measurements above stay as they were made. This replaces
**H9b's count and its task list only**; § 13's other three parts, and every measurement in §§ 1–12,
stand unchanged. Four things, all in `resume`, and three of them were invisible to the probe § 4.1
was built from: **that project's template was `generic`, which declares no `apparatus_probe`**, so
its crashed run directory has no `apparatus/` at all and none of the questions below could surface
from it.

### C1. `resume`'s apparatus baseline IS recoverable, and the reader's codes are named for `freeze`

§ The apparatus core can only observe gates every pre-execution probe against the **first
*answered*** observation, which `run.yaml` carries as `provenance.apparatus.facts` — and a
resumable run has no `run.yaml`. Measured by **reading the two functions rather than by grepping a
name**:

- `apparatus.append_observation` writes each line **at the probe call**, and its own docstring gives
  the reason in these terms: *"What after-the-execution WOULD lose is the observation for a run that
  dies **inside** the execution itself, or between executions."* So `apparatus/probes.jsonl` is
  durable across exactly the crash `resume` exists for.
- `apparatus.replay_ledger` already reconstructs the baseline `Observations` from it, **filtered to
  `PHASE_RUN_START`/`PHASE_PRE_EXECUTION`** — *"exactly the calls the run's own in-memory
  `Observations` held while it executed"* — replayed through the shipped `Observations.record`, so
  the first-answered rule, the per-condition scoping and the `null` transitions all come along.

**So no third artifact is needed**, which is the good news, and it makes this the one durability
question in H9b that answers *yes*. Two things follow that are H9b's:

1. **The reader is general and its refusals are not.** `replay_ledger`'s sole caller is `freeze`,
   and it raises `E-FREEZE-LEDGER-UNREADABLE`. A `resume` calling it would print a `FREEZE` code
   from a command that is not `freeze`. Either the code is renamed — a change to a shipped
   diagnostic with a § Errors row — or `resume` gets its own, and H9b decides which.
2. **An absent or empty baseline means something different to `resume` than to `freeze`.**
   `replay_ledger` returns an empty `Observations` for a missing file, deliberately, because *"there
   is no baseline" is `freeze`'s own `E-FREEZE-LEDGER-MISSING` to report* — probing now would pin a
   fact the run never adopted. For a `resume` that is the **legitimate** case: a run that crashed
   before its first probe has no baseline and its next execution is entitled to set one, exactly as
   the original run's first probe would have. `freeze`'s refusal must not be inherited by copy.

**And this is the same filter H9a task 7 asks about.** `replay_ledger`'s docstring says a `dry_run`
line is excluded *"for the same reason, and one more: nothing appends one yet (§ Refusals routes that
gap to H9)"*. So H9a's `PHASE_DRY_RUN` ruling and H9b's baseline reader are two readings of one
filter, and the H9a ruling must be written knowing `resume` will be its second caller.

### C2. `run_status`'s bare assert is a tripwire on `resume`'s first invocation

`run_record.run_status(results, *, planned, stop)` holds
`assert len(results) >= planned` whenever `planned` is given and no stop reason is — and its own
docstring calls a shorter list *"a core defect … nothing core ships truncates a plan silently."*
**A resumed run's `results` list holds only the triples it re-executed**, so on the first `resume`
of any partially-completed plan the assert fires. That is not a bug in `run_status`; it is the
statement that a second entry must either reconstitute the prior attempt's results or change what
`planned` means.

It is also the **status** question, and it belongs with C1's and § 4.4–4.5's durability questions
rather than beside them: § What status means defines `partial` as *"the plan reached its end with
some executions failed"*, so a resumed run's status has to fold the **previous** attempt's `failed`
ledger records — which the ledger does carry (`status`, and `error`, § 4.4) — while `per_repeat` and
`n` for those same triples it does not (§§ 4.4–4.5). **One artifact, three different answers**, and
that is why H9b needs one ruling task covering status, `n`, `returned` and the apparatus baseline
together rather than four independent ones.

### C3. `E-RUN-LOCKED`'s sites, enumerated by reading rather than counted by grep

§ 4.7 reported *"raised in `run_identity.py`"* from `grep -rc`, which answers **where the string
appears**. § Errors carries one row per code covering every site that **raises *or* reports** it —
the `E-TEMPLATE-UNKNOWN` precedent — so the enumeration is:

| Site | What it does |
|---|---|
| `run_identity.RunLock.__enter__` | **raises** `ContractError(code="E-RUN-LOCKED")` on `FileExistsError`, after reading the holder line |
| `cli.main`'s `except PublishableError` | **reports** it: `print(f"  error   {exc.code:<20} {exc}", file=sys.stderr)` and returns `EXIT_WRONG` |

So the code that a held lock produces today is **`1`**, which is the code § Exit codes already
assigns to *"a `resume` whose hashes moved"* — the same class. **H9b task 8 is therefore a row and
not also a code decision**, which is one fewer ruling than § 4.7 implied.

Two things the reading adds that the grep could not. `main`'s handler uses **no `Collector`**, so
this diagnostic is printed without the redaction pass every `Collector.render` applies — harmless
for a lock message, and worth knowing before `resume` routes anything else through the same path.
And `E-RUN-LOCKED` is **unreachable from `run` and `draft` for a structural reason**, not merely an
unlikely one: `allocate_run_dir`'s `mkdir` *is* the claim — a directory that already exists sends it
to the next suffix — so a lock file can never pre-exist a directory those two commands just created.
That strengthens § 4.7's argument rather than qualifying it: `resume` is the **only** command from
which the code is reachable at all.

### C4. Two withdrawals and one connection

- **§ 10's causal clause is withdrawn.** It read *"The pin is authorized-editor-only, so the
  **document** is the side that moved."* Pin authorization says which arm an editor may touch; it
  does not say which side drifted, and inferring one from the other is the proxy substitution
  `CLAUDE.md` § Answering a question with a proxy names. **What stands is the observation**:
  § The two files puts `publishable_version` and `plugin_versions` last, `tests/test_cli.py`'s H8a
  arm B pins them before `units`, and a real run agrees with the pin. Which side moved is settled by
  `git log -S` over § The two files and was not spent here. Still not H9's charter.
- **`demo`'s `--into DIR` and `reproduce`'s refusal of `--into` are one question with two documented
  answers**, and H9 builds both. § Reproducing on another device: *"No `--into`: the destination is
  derived, so it can't collide with an existing checkout and doesn't need naming."* § Creation
  commands gives `demo` `[--into DIR]`, and § What `demo` walks you through makes it load-bearing —
  *"given one that already holds a `.demo-progress`, it resumes there."* **A ruling that legitimizes
  `demo`'s flag has to say why `reproduce`'s refusal still holds**, and the available answer is that
  `reproduce`'s destination is *derived from the record* while `demo` has no record to derive from.
  That belongs in H9d task 3 beside the enumeration finding, not as a separate task.

### H9b, recounted — 15 tasks

| # | Task | Changed |
|---:|---|---|
| 1 | Ruling: what `resume` compares (§ 4.2) | unchanged |
| 2 | Ruling: the stale lock (§ 4.3) | unchanged |
| 3 | **Ruling: what a run must make durable, in one place** — the ledger's `attempt`/`n` (§ 4.4), `returned`/`per_repeat` (§ 4.5), the resumed run's **status** and `run_status`'s `planned` contract (C2). One artifact, four readings | **merges old 3 and 4, and gains status** |
| 4 | **Ruling: the apparatus baseline** (C1) — `replay_ledger` as `resume`'s reader, whether `E-FREEZE-LEDGER-UNREADABLE` is renamed or a code minted, and why an empty baseline is legitimate for `resume` and a refusal for `freeze` | **new** |
| 5 | `resume` itself: read `sweep.yaml`, skip `completed` triples, take the lock, refuse a directory holding a `run.yaml`, append into the same ledger and tree | unchanged |
| 6 | **The apparatus wiring**: the replayed baseline threaded into the pre-execution gate, so a resumed execution is gated against the *original* run's first-answered facts and not against its own first probe | **new** |
| 7 | `attempts` from the ledger; `io.units` never narrowed; `io.recorded_keys` non-empty only on a resume | old 6 |
| 8 | `allocation.json` read rather than re-drawn (§ 4.6), over a **drawn** axis | old 7 |
| 9 | `E-RUN-LOCKED` and `E-RUN-ID-EXHAUSTED` § Errors rows — **both sites each** (C3) — and the five-codes filing amended to three with the reason | old 8, narrowed by C3 |
| 10 | The run-start `parameters_hash` question, closing the `freeze` filing or warranting an artifact | old 9 |
| 11 | The bytecode-cache fix at all three call sites, closing two H9-owned filings (§ 8.1) | old 10 |
| 12 | **The status fixture**: a real crash, a real `resume`, and a `run.yaml` whose `status` is `partial` because of a failure recorded by the **previous** attempt — the one shape no direct call can build | **new** |
| 13 | **`run_status`'s `planned` contract**, implemented per task 3's ruling, with the bare assert either satisfied or replaced by a stated rule — and the H7d Part B `max_failed_fraction` pin left alone (§ 12) | **new** |
| 14 | The guard pin for everything tasks 3, 6 and 13 move — `run.yaml` key-for-key on a resumed run, the ledger line's key set, the gate's baseline — captured before any of them, each arm with a named sole editor or **NONE** | **new; hoisted to first at dispatch** |
| 15 | § Resuming, § `executions.jsonl`, § What status means, § CLI reference, § Exit codes, `spec-defects.md`, `CLAUDE.md`, and both consistency passes | old 11, widened |

**So H9 is 12 + 15 + 11 + 11 = 49**, and the order is unchanged: H9a → H9b → H9c → H9d. Task 14
executes first inside H9b despite its number, which is stated here rather than renumbered so this
correction stays readable against the list it corrects.

**One thing to say about 49 before anyone quotes it.** § 13 cites its own calibration — H5a 9→13,
H5b 10→16, H6a 12→13 — and **every one of those moved up between the scoping and the plan that
shipped.** 49 is the *scoping* figure, measured by naming and counting tasks, and the pattern this
file documents predicts the approved plan will exceed it. Quote it as a scoping measurement with a
date, not as H9's size.
