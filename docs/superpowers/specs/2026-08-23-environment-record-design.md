# H6b — the environment record and the diagnostic debt — design

**Written 2026-08-23 against `main` at `2b18435`** (the H6a merge), clean tree. Every claim below was
run or grepped at that commit; nothing is carried from
[`H6-SCOPING.md`](../H6-SCOPING.md) without re-checking, because that scoping was measured on
2026-08-22 against `da9907b` — **before H6a merged** — and three of its eight rows are stale in
consequence (§ Corrections to the charter).

## What this slice is, in one paragraph

`run.yaml` gains the three `provenance.environment` keys `reference.md` § The two files has shown and
no code has ever written — `os`, `hostname`, `hardware` — closing the last live row of the
six-unwritten-keys filing. `study add`'s waiting `hostname` redaction gets the record it was written
against, and the two keys it must **not** redact get a stated reason and a pin. Two shipped `E-` codes
raised by the git layer H6a just rewrote — `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT` — get the § Errors
rows they have never had. And two questions H6a handed forward, § Templates' *"goes dirty at
`validate`"* sentence and the uncommitted-root-`.gitignore` filing, are decided **together**, because
the filing says in its own words that they are one question asked at two surfaces.

**H6b is additive, and that is a measured claim rather than a framing.** No value any shipped key
carries moves. The three new keys are written into the `provenance` mapping `cli.command_run` builds
at line-of-execution *after* every hash is computed: `hashed_files`/`code_hash_of` and
`parameters_hash` run at `command_run`'s hashing phase, `design_digest` at its pin-hashes phase,
`manifest_hash`/`units_hash`/`allocation_hash` are folded over the manifest, the roster and the
allocation document respectively — **grepped: `grep -n "hash(provenance\|hash(run_doc\|hash(record"
src/publishable/*.py` returns nothing, so no hash reads the record it is written into.** Adding a key
to `provenance.environment` therefore cannot move `code_hash`, `parameters_hash`,
`input_manifest_hash`, `uv_lock_hash`, `units_hash`, `allocation_hash` or `design_digest`. Guard-pin
arm Q is what turns that paragraph into a test.

**H6b moves NO row of § Executability's four-row table and mints no fifth number** (Decision 15,
derived rather than assumed).

---

## Corrections to the charter, measured against the code

[`H6-SCOPING.md`](../H6-SCOPING.md) § 10 charters H6b as eight tasks, 13–20. Reported as a list, not as
a count, and each one grepped or run.

1. **Task 17 is smaller than its row says.** The row asks for *"`E-CODE-DIRTY`'s § Errors row, plus
   `E-GIT-NO-REPO`/`E-GIT-NO-COMMIT`'s"*. **`E-CODE-DIRTY` already has one** — H6a's batch-4
   controller follow-up wrote it. Verified by reading, not by the ledger:
   `grep -n "E-CODE-DIRTY" docs/reference.md` returns one hit, a full row in § Errors core raises
   whose `Type` cell reads *(no exception; a `Collector` diagnostic)*. This is **Ruling N**
   (Decision 1).
2. **Task 18 is a confirmation, not a change.** The scoping frames it as *"either `validate` gains a
   dirty warning, or the sentence changes"*, on the ground that `validate` is silent. H6a's design
   carries an **appended correction dated 2026-08-23** establishing that the sentence, read with its
   own subject, is true as written and says nothing about a gate inside `validate`. This is
   **Ruling P** (Decision 11).
3. **H6b owns a filing the scoping's eight tasks do not contain.** `spec-defects.md` carries
   *"OPEN — an uncommitted root `.gitignore` decides what `code_hash` covers, and the dirty gate
   cannot see it — **Owner: H6b**"*, filed 2026-08-23 by H6a's whole-branch fix round from the gate's
   Major 3, after the scoping was written. Its own owner paragraph says H6b *"holds the `validate`
   tree-state ruling, which is the same question asked at the other surface. A successor should decide
   the two together rather than widening this one pathspec by hand."* That is Decision 12, and it is
   decided in the same task as Ruling P for exactly that reason.
4. **Tasks 13, 14 and 15 cannot be three tasks.** They write three keys into **one** dict literal in
   `cli.command_run` and each of them invalidates **one** shipped exact-key-set assertion —
   `tests/test_cli.py::test_h8b_arm_d_the_five_figures_diff_reads`, whose body reads
   `assert environment == {"manager": "uv", "uv_lock": None, "uv_lock_hash": None}` after popping
   `python_version`. Splitting the write across three tasks means editing one pin three times, which
   is the shape *a pin that must move can be moved once, by a named task* exists to prevent. **One
   task, one editor, one edit** (Decision 9, task 3).
5. **Task 16's "close the six-unwritten-keys filing" is right and its "rule whether § What `study
   add` redacts needs `os`/`hardware` rows" is **Ruling Q** (Decision 10), which also requires a pin
   the scoping does not name.
6. **Three shipped claims about the environment block go stale or are already false, and the charter
   names none of them** (Decision 13): `src/publishable/secrets.py`'s module docstring asserts
   *"`provenance.environment` is assembled from `os`, `hostname`, `hardware` and `uv.lock` alone"* —
   **false today**, since the block is `{manager, python_version, uv_lock, uv_lock_hash}`, and still
   false after H6b, which adds the three but removes none of the four;
   `src/publishable/study.py::_redact`'s docstring says `hostname` *"is never written today (measured
   at `ebf642a`…)"*, made false by task 3; and `tests/test_study.py::_fixture_y_record`'s docstring
   repeats the same measurement.
7. **`CLAUDE.md`'s order line and slice entry are nobody's task in the charter.** The line reads
   *"Order of the slices that remain: H6b, H9, then H3c-3's remaining 14"* and must lose H6b.
8. **§ Executability gets its own task**, on H6a's own precedent: both of the wrong figures that
   analysis has carried were made by a slice that folded the entry into a records sweep and repeated a
   phrase without re-deriving what it counted.

**Net: 11 tasks, not 8.** Every re-scope in this repo has been stale in the same direction —
under-counted and missing surface — and this one is too.

---

## The measurements this rests on

Run at `2b18435` unless stated. Nothing is cited by line number.

**The baseline gates**, all four run in the foreground in the real repo:

- `uv run pytest -q` → **2963 passed, 1 skipped, 2 xfailed** in 193 s
- `uv run pytest --collect-only -q` → **2966 collected** (2963 + 1 + 2 = 2966, so the two agree)
- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **93 files already formatted**
- `uv run mypy` → **Success: no issues found in 52 source files**

**What `provenance.environment` holds today**, read from `cli.command_run`'s construction:
`{"manager": "uv", "python_version": …, "uv_lock": …, "uv_lock_hash": …}` — four keys. Confirmed
end to end on a scaffolded project run through the installed console script in the scratchpad
(`run_2026-08-23T06-02-37Z_436cab2`).

**What reads `provenance.environment`**, grepped over `src/publishable/*.py` for `"environment"`,
`["environment"]` and `environment.get`: exactly two readers, and neither iterates the block —
`diff._figure` reads `uv_lock_hash` and nothing else, and `study._redact` reads `hostname` and nothing
else. Every other hit is the *directory* `environment/`, which is a different thing. **So three new
keys are invisible to every existing reader**, which is what makes this slice additive.

**Both new codes were reached through the installed console script**, not derived from emit sites:

| What was run | Result |
|---|---|
| `publishable run <cfg>` on a project whose `.git` was removed | `error   E-GIT-NO-REPO   no git repository found from …/configs/cohort-pilot upwards`, **exit 1**, stderr; `validate` printed nothing at all first |
| `publishable generate experiment …` with cwd outside any repo | the identical code and message, **exit 1**, stderr, walked up from the **cwd** |
| `publishable init` with cwd outside any repo | the identical code and message, **exit 1**, stderr |
| `publishable run <cfg>` in a `git init`-ed repo with no commit | `error   E-GIT-NO-COMMIT  repository at … has no commits yet; provenance requires a HEAD`, **exit 1**; the same config's `validate` printed `✓ config valid` at **exit 0** |

**No existing test asserts either code at the CLI**, and this was grepped rather than assumed —
newline-insensitively, over every file in `tests/`, by flattening whitespace before matching, because
a `grep -F` cannot match a wrapped phrase. Nine hits total: two direct calls in
`tests/test_provenance.py` (`find_repo_root(...)` and `git_provenance(...)` under
`pytest.raises`), four monkeypatched raises in `tests/test_validate.py`, one docstring each in
`tests/test_lineage.py` and `tests/test_study.py`. **None goes through `main([...])`**, so guard-pin
arm T is new coverage.

**`platform` and `socket`, measured on this machine** (`Darwin`, arm64):

| Call | Value |
|---|---|
| `platform.platform()` | `'macOS-26.5.2-arm64-arm-64bit-Mach-O'` |
| `platform.platform(terse=True)` | `'macOS-26.5.2'` |
| `'-'.join((platform.system(), platform.release(), platform.machine()))` | `'Darwin-25.5.0-arm64'` |
| `socket.gethostname()` | `'macbookair.lan'` |
| `os.cpu_count()` | `8` |
| `os.sched_getaffinity` | **absent on this platform** |

**`E-GIT-NO-REPO`'s one raise site and every path that reaches it**, enumerated by reading rather than
by grepping for a spelling — the grep was the confirmation, not the enumeration:

| Reached from | What happens |
|---|---|
| `cli.command_run` | **uncaught** — `main`'s `except PublishableError` prints it to stderr, exit `EXIT_WRONG` |
| `cli`'s `generate`/`init` dispatch, `find_repo_root(Path.cwd())` | **uncaught**, same printer, and the walk-up starts at the **working directory** |
| `validate._check_data` | caught **by code** and `return`ed quietly — "not in a repo, so *inside the repo* doesn't arise" |
| `validate.validate_config` | caught by a **bare `except ContractError`** — repo_root becomes `None` and local template discovery is skipped |
| `cli._load_experiment_for` | caught by `except Exception`, returns `None`; `validate_config` reports the fault |
| `study._refuse_if_in_repo` | caught by code as the **pass branch** of `E-STUDY-IN-REPO`/`E-DATA-IN-REPO`'s sibling rule |

**`E-GIT-NO-COMMIT` has one raise site and one reach path**: `provenance.git_provenance`, called only
from `cli.command_run` (`grep -rn "git_provenance" src/` → the definition, the import, one call). It
fires **before** the dirty gate, because `git_provenance` raises while computing the `GitInfo` the gate
then reads.

**`_H5A_ARM_D_LITERALS` does not contain anything on the `hardware` line.** The tuple is
`("8e21", "1a2b", "3d8a", "6b1f", "2f5c8d0")` plus the worked example's interval bounds in both
minus-sign spellings; the line `    hardware: {gpu: "1x A100 80GB", cpu_count: 32}` contains none of
them, so `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text` does not scan it and Ruling O's
edit cannot move that arm. Checked by extracting the tuple and testing each member against the line.

---

## Decisions

### 1. CONTROLLER RULING N — the charter widens to exactly two undocumented codes

**Question.** `spec-defects.md`'s *"Nine undocumented run-time and creation-command `E-` codes"* entry
offers, as option 1, widening H6's charter. The scoping recommended taking three. Which does H6b take?

**Answer. Two: `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT`. Not three, and not nine.**

**Grounds, measured.** The scoping's third — `E-CODE-DIRTY` — **already has its row**, written by
H6a's batch-4 controller follow-up because `E-CODE-EMPTY`'s new row had no sibling to be consistent
with. `grep -n "E-CODE-DIRTY" docs/reference.md` returns exactly one hit and it is a full row of
§ Errors core raises. The nine-codes entry's own appended note records this and says the heading's
count is now **eight**. Taking it again would be documenting a documented code.

The two that remain are inside the charter for a reason that is a fact rather than a word: **both are
raised by `provenance.py`, the file H6a rewrote** — the neutralized `_git`, the walk-up, the dirty
gate's pathspec. A code whose emit site this slice's own family touched is inside the charter; the
other **five** are `run_identity.py`, `generators/` and the manifest path, which no H6 task has ever
opened. (**Five, and it was re-derived rather than carried** — see the count below.)

**One row per code, covering EVERY emit site — and here the interesting half is not the emit site.**
Each of the two has exactly one `raise`. `E-GIT-NO-REPO` has **six** paths that reach it, three of
which swallow it deliberately and two of which surface it (table above). A row that says only
*"raised by `find_repo_root` when no repository is found"* would be true and would mislead: a reader
who meets `✓ config valid` on a repo-less project and then `E-GIT-NO-REPO` at `run` needs to know that
`validate` swallows it **by design**, and that the creation commands walk up from the **working
directory** because they have no path argument to walk up from — which is the one place
`CLAUDE.md` § Invariants' *"a walk-up from the path the command was given, not from the working
directory"* does not apply, and a reader who compares the two without that sentence concludes one of
them is wrong.

**The table's own scope sentence was checked, not the design's instruction.** § Errors core raises'
header is `| Raised by | Type · code |`, over a preamble introducing the exception hierarchy and then
naming an exception: *"Two rows in this table are not raises, and the `Type` cell says so."* Both new
codes **are** raises, both carry `ContractError`, and both are met at `run` or at a creation command
rather than reported by `validate` — so the preamble's own reason for siting `E-CODE-DIRTY` here
(*"`validate` does not report them … a reader who meets one at `run` looks for it here"*) covers them
with no widening. **Neither row needs an invented `Type` cell**, which is the failure H6a's batch-4
review found when a design directed a row into a table whose scope did not admit it.

**Alternatives rejected.** *Take all nine* — five of them are `run_identity.py`, `generators/` and
the manifest path, surfaces no H6 task opens, and two are already documented; inheriting them is the "description standing in for a slice" failure the S5
checkpoint closed once already. *Take none and file* — the two sit one row from a row this family has
already written, and the entry's own option 1 exists precisely for them.

**Cost if wrong.** If the two really belong to a tenth slice, H6b has documented two codes slightly
early and the tenth slice's list is shorter by two — recoverable. If they are left, they stay
undocumented behind a charter boundary nobody will cross, which is the state the entry has been in
since H1.

**What is filed instead, each owner a fact with a reason — and the count is FIVE, re-derived from the
entry's own table rather than carried from the ruling that commissioned it.** The controller ruling
that widened this charter said *"the other six"*; that subtracted `E-CODE-DIRTY` from the nine and not
`E-EXPERIMENT-UNKNOWN`, which H8c task 16 documented at `c794029`. Derived here: the nine are
`E-GIT-NO-REPO`, `E-GIT-NO-COMMIT`, `E-CODE-DIRTY`, `E-INPUT-CHANGED`, `E-RUN-LOCKED`,
`E-RUN-ID-EXHAUSTED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`, `E-EXPERIMENT-UNKNOWN`; minus
`E-CODE-DIRTY` (H6a batch 4) and `E-EXPERIMENT-UNKNOWN` (H8c task 16) leaves **seven** undocumented
before H6b; minus H6b's two leaves **five**. The remaining five —
`E-INPUT-CHANGED`, `E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED`, `E-PROJECT-EXISTS` and
`E-EXPERIMENT-EXISTS` — are **appended to the nine-codes entry** with the heading's count corrected
from nine to five and with H6b's reason stated: no remaining chartered slice has `run_identity.py`, the
manifest path or `generators/` as its surface — H9 is
`reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`, H3c-3's remaining 14 are folds and holdouts
inside cells. **Owner: unassigned, with the reason**, never *"whichever slice next touches a creation
command"*. (`E-EXPERIMENT-UNKNOWN`, the ninth, gained its row at H8c task 16 — recorded in the entry
already and re-checked here rather than carried:
`git log -S "E-EXPERIMENT-UNKNOWN" --oneline -- docs/reference.md` → `c794029`.)

### 2. `E-GIT-NO-REPO`'s row states the raise, the two surfacing paths, and the three deliberate swallows

**Question.** What does one row have to carry so it is not narrower than its code?

**Answer.** Four facts: the single raise in `provenance.find_repo_root`; that `run` and the creation
commands surface it at **exit 1 on stderr**; that the creation commands walk up from the **cwd**,
being the commands with no path to walk up from; and that `validate` and `study` catch it **by code**
as the pass branch of a rule of their own — `E-DATA-IN-REPO`'s and `E-STUDY-IN-REPO`'s — so a config
outside every repository validates clean and refuses at `run`.

**Grounds.** Measured at the console script, all four rows of the measurement table above. The last
fact is the one a reader cannot infer: `✓ config valid` followed by `E-GIT-NO-REPO` looks like an
inconsistency until you know that `validate`'s only interest in a repository is whether `input_dir`
resolves inside one.

**Alternatives rejected.** *Two rows, one per surface* — § Errors carries one row per code, not per
emit site, and that shape was the whole-branch Major on two of H8's sub-slices. *A row that names only
the raise* — narrower than the code, which is the same Major from the other end.

**Cost if wrong.** A reader debugging a repo-less project reads `validate`'s silence as a bug in
`validate`.

### 3. `E-GIT-NO-COMMIT`'s row states one path and its ordering against the dirty gate

**Answer.** Raised by `provenance.git_provenance` on a repository with no `HEAD`; one reach path,
`cli.command_run`; raised **while computing** the `GitInfo` the dirty gate reads, so it precedes
`E-CODE-DIRTY` — a fresh `git init` with every file untracked reports **this** code, not the gate's.
The row also records why the check exists at all, which is already in the code's own comment and is
worth carrying into the document: `--verify` is used because plain `git rev-parse HEAD` writes the
literal string `HEAD` to stdout as part of its usage hint on a commitless repo, which `_git`'s
`check=False`/`strip()` convention would read back as a commit.

**Grounds.** Run: a `git init`-ed copy of a working project reported `E-GIT-NO-COMMIT` at exit 1 while
carrying two untracked trees that would have been `E-CODE-DIRTY`.

**Cost if wrong.** A reader expects the dirty gate and gets this, with no row explaining the order.

### 4. Both rows sit beside the row that describes the dirty gate

**Answer.** In § Errors core raises, adjacent to **the row whose subject is `src/**`/`templates/**`
carrying uncommitted changes when a command that executes starts** — named by what it does, never by
position, and never as "the two rows above."

**Grounds.** The three are one subject: what the git layer refuses before a run can start. A reader
who meets any of them is reading the same paragraph of their own terminal output.

**Cost if wrong.** Nothing behavioural; a row in an odd place is a Minor.

### 5. CONTROLLER RULING O — `hardware` carries `cpu_count` and NOT `gpu`, and `gpu` leaves the example

**Question.** § The two files shows `hardware: {gpu: "1x A100 80GB", cpu_count: 32}`. What does core
write?

**Answer.** `hardware: {cpu_count: <int|null>}` — one key. **`gpu` leaves the example**, replaced by a
sentence naming the apparatus as its route.

**Grounds.** `CLAUDE.md` § Invariants' core-vs-plugin test: *would it be identical for a wet-lab assay,
a simulation sweep, and an LLM benchmark?* A CPU count is `os.cpu_count()`, stdlib, answerable on every
machine. A GPU is not: core cannot name one without a dependency or a subprocess, and **the apparatus
is the existing route for anything core cannot observe** — H7d Part A and Part B built the probe, the
projection onto `apparatus_facts`, the ledger and the change gate for exactly this shape of fact, and
`reference.md` § The apparatus core can only observe already carries a worked template declaring
`apparatus_facts = ["model", "firmware", "calibration_id", "reagent_lot"]`.

**Which way the example changes, and why that way.** The alternative — leaving `gpu` in the example
but sourcing it from the apparatus — was rejected on a measurement: § The apparatus core can only
observe says *"An experiment whose measurements never leave the machine declares nothing and records
`apparatus: null` — **the worked example throughout this document is one**"*, and the same
`run.yaml` example two thousand lines earlier writes `apparatus: null   # no probe declared`. Making
`gpu` come from the apparatus **in that example** would give `cohort-pilot` a probe, which is a change
to the shared worked example that `CLAUDE.md` § The worked example governs and that Ruling O does not
authorize. So the example's `hardware` line becomes `hardware: {cpu_count: 32}`, and the sentence
that replaces the fact says where a GPU is recorded instead — a link to § The apparatus core can only
observe, not a restatement of it.

**Measured, so the edit is safe:** `_H5A_ARM_D_LITERALS` contains no substring of that line, so
`test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text` — the arm with **no authorized editor in
its own slice** — does not scan it and cannot move. Guard-pin arm R re-asserts this after the edit.

**Cost if wrong, stated rather than hidden.** *A reader of a bundle cannot tell what hardware produced
a number unless the producer declared an apparatus probe.* That is exactly the trade this project makes
everywhere else — core records what it can observe and refuses to guess the rest — and it is written
into the document beside the change rather than left for a reader to discover. A project that needs
the GPU in the record declares a probe; a project that does not, does not, and the record says
`apparatus: null` rather than a hardware string nobody computed.

### 6. `os` is `system-release-machine`, not `platform.platform()`

**Answer.** `f"{platform.system()}-{platform.release()}-{platform.machine()}"`.

**Grounds, measured on this machine.** `platform.platform()` returns
`'macOS-26.5.2-arm64-arm-64bit-Mach-O'` — the **marketing** name and version, not the kernel the same
module's `uname()` reports (`Darwin`, `25.5.0`) — and appends build details that differ per platform
(`-with-glibc2.35` on Linux, `-SP0` on Windows). `platform.platform(terse=True)` returns
`'macOS-26.5.2'`, dropping the architecture entirely on this platform while keeping it on Linux. **The
composed form is the only one of the three that yields exactly three components on every platform**,
and it is the shape § The two files already shows: `os: "Linux-6.8.0-x86_64"`.

**Alternatives rejected.** `platform.platform()` — more detail, but a different fact on macOS and an
inconsistent shape across platforms; adopting it would also mean editing the documented example to
something no reader could predict. `platform.uname()` as a mapping — `uname_result.node` **is the
hostname**, so a mapping would put the same identifying value in a second place and give `study add`'s
redaction a second site to miss.

**Cost if wrong.** A reader gets `Darwin-25.5.0` where they expected `macOS 26.5.2`, and a libc
difference between two Linux machines is invisible in this key. Both are recoverable by widening the
string later; neither is a value another key already carries.

### 7. `hostname` is `socket.gethostname()` — the sibling that already got it right

**Answer.** `socket.gethostname()`.

**Grounds.** `src/publishable/run_identity.py` already writes
`json.dump({"host": socket.gethostname(), "pid": os.getpid()}, fh)` into the run lock. **Before
writing a call, grep for one that already exists**: core already has an answer to *what machine is
this* and it is this one. Using `platform.uname().node` instead would introduce a second spelling of
one fact, which is the shape `report`'s `repo_root` row rejects by name (*"two sources for one fact is
how the two drift"*).

**Cost if wrong.** `socket.gethostname()` can return a short name where a reader wanted the FQDN. The
redaction makes this moot inside a bundle, which is where the value is most read.

### 8. `hardware.cpu_count` is `os.cpu_count()`, and `None` is a real answer

**Answer.** `{"cpu_count": os.cpu_count()}`, written as-is, `None` included.

**Grounds.** `os.cpu_count()` is documented to return `None` when the count is indeterminable, and
this project already spells "never captured" as `null` rather than as a marker — `apparatus: null`,
`uv_lock: null`, `units: null`. Substituting `0` or `1` would publish a number nobody measured.
`len(os.sched_getaffinity(0))` — the count of CPUs this process may actually use, which is the more
honest number under a cgroup or a scheduler affinity mask — is **absent on this platform** (measured),
so it cannot be the primary source; core writes the machine's count and says so.

**Alternatives rejected.** `os.process_cpu_count()` is 3.13+, and the project targets ≥ 3.11.
Preferring `sched_getaffinity` where present and falling back would make the key mean two different
things on two machines with no way to tell which — worse than one meaning.

**Cost if wrong.** A containerized run records the host's cores rather than its quota. The key is
descriptive, not an identity claim: no hash covers it and `diff` does not compare it.

### 9. The three keys are written in § The two files' own order, in one dict literal, by one task

**Answer.** `cli.command_run`'s `environment` mapping becomes, in this order:
`manager`, `python_version`, `os`, `hostname`, `uv_lock`, `uv_lock_hash`, `hardware` — exactly the
order § The two files' example prints.

**Grounds.** The order costs nothing to match and buys one thing: `spec-defects.md`'s standing note
that *"the example's `provenance` key order differs from `cli.py`'s construction order … reordering the
example to match today's code would pin the document to an implementation detail, which is
backwards"* applies to the outer `provenance` block. Here we are **adding** keys rather than
reordering an example, so matching the document costs one argument's position and makes
`environment` the one block where the two agree. The note itself is unaffected and stays.

**One task, one editor.** The write invalidates one shipped exact-key-set assertion (guard-pin arm P).
Splitting the three keys across three tasks would edit that arm three times; **a pin that must move is
moved once, by a named task, with the post-edit state written in advance.**

**Cost if wrong.** None behavioural — YAML mappings are unordered and no reader indexes by position.

### 10. CONTROLLER RULING Q — `os` and `hardware` are not redacted; `hostname` is; and the pin is the point

**Question.** § What `study add` redacts lists `hostname` and lists neither `os` nor `hardware`. Does
the table need two more rows?

**Answer. No.** `hostname` is redacted, `os` and `hardware` travel verbatim, and the **reason** is
written into § What `study add` redacts so the next reader does not re-litigate it.

**Grounds.** Redaction here exists for **identity and credentials** — the table's own opening is
*"Everything host-identifying"* and its four rows are two absolute paths, a repo root that *"usually
contains a username"*, and a node name that *"often identifies an institution on its own"*. A
platform string and a core count name neither a person nor an institution, and a bundle reader needs
them: *what platform produced this number* is provenance, which is the thing a bundle exists to carry.
The section's own closing argument already draws this line — *"None of this disturbs verification"* —
and it is the same line § What `study add` redacts draws for `input_manifest_hash`, which survives
while its path does not.

**The pin is the point, and it must be end-to-end.** H8c wrote the `hostname` redaction against a key
**nobody writes** — its own docstring says so — so the only test of it today runs over a record
synthesized by hand. Fixture E runs a **real** `run`, bundles it with `study new`/`study add`, and
asserts **both halves** on the bundled member: `hostname` is the marker, and `os` and `hardware` are
byte-equal to the source record's own values. Asserting only the redaction would leave the
not-redacted half untested, and *a control asserting only absences passes identically if nothing ran*.

**Alternatives rejected.** *Redact `hardware` too* — a core count discloses nothing, and a bundle
reader comparing two runs' plausibility needs it. *Redact nothing and drop `hostname`'s row* — the row
is right; a node name is the field this table was written for.

**Cost if wrong.** A bundle deposited publicly discloses that a run happened on Linux 6.8 with 32
cores. If that is disclosive for someone, the remedy is not to publish the bundle, and it is the same
remedy the `code_hash` and `uv_lock_hash` rows already imply.

### 11. CONTROLLER RULING P — no `W-` seat at `validate`, and § Templates' sentence stays

**Question.** § Templates says a hand-assembled repo whose `.gitignore` omits `__pycache__` *"goes
dirty at `validate`"*, and `validate` performs no dirty check. Does `validate` gain a warning, or does
the sentence change?

**Answer. Neither. Nothing is added and the sentence stays.** Task 18 is a **confirmation**.

**Grounds.** H6a's design carries an appended correction, dated 2026-08-23 and written by its batch-6
review, establishing that the sentence read with its own subject is **true**: template discovery
imports every file under `templates/` to find its registration, which writes `templates/__pycache__/`,
so a repo whose `.gitignore` omits that line **becomes dirty as a result of validating** — a statement
about a side effect of the command, not about a gate inside it. Beyond that: **a `W-` code is a
registry seat**, permanent and documented in two tables; the condition is already caught at `run` by
`E-CODE-DIRTY`; and the scaffold's own `.gitignore` excludes `__pycache__`, so only a hand-assembled
repo reaches it.

**What the confirmation actually checks, and it is not a re-read of the same sentence.** Ruling F
changed what the surrounding paragraph claims. § Templates' neighbouring clause says `code_hash`
*"skips `__pycache__` directories and compiled `.pyc`/`.pyo` files unconditionally … it reads the
working tree rather than git, so no ignore file could have done that for it"* — **the second half is
now false**: the hash asks git. The fixed skip set is still applied unconditionally, which is what
keeps the first half true. So the task's job is to check the whole paragraph against the code **as
H6a left it**, and the likely finding is in the clause the scoping never named rather than in the one
it did. **Prefer deleting a false clause to rewriting it.**

**Cost if wrong.** If the sentence really is false, a reader of § Templates believes `validate` warns
about a dirty tree and it does not — which is the *assuming a documented rule has code behind it*
misreading, running in the direction this project has been caught in five times. The task's
deliverable is therefore a **measurement**, not an assertion: build the hand-assembled repo, run
`validate`, and report what `git status` says before and after.

### 12. The uncommitted-root-`.gitignore` filing is DECLINED, re-owned with a reason, and decided in the same task as Ruling P

**Question.** `spec-defects.md`'s OPEN entry, **Owner: H6b**, filed by H6a's gate: `code_hash`'s
exclude question is `git check-ignore`, which answers from the **working tree**, so an
edited-and-uncommitted or never-committed root `.gitignore` narrows a published `code_hash` while the
dirty gate — whose pathspec is `src/**` and `templates/**` — cannot see it. Does H6b close it?

**Answer. No. H6b declines it, in writing, and re-owns it as unassigned with the reason.** The
decision is made in the same task as Ruling P because the filing itself says the two are one question
asked at two surfaces.

**Grounds.** Closing it means the dirty gate reading a file **outside** the two hashed trees. That is a
**behaviour change to a shipped command**: every uncommitted root file becomes a candidate
`E-CODE-DIRTY` must rule on, and a repo with an ordinary uncommitted `README.md` would stop running.
H6b is chartered **additive** — no shipped key's contents move, no shipped verdict moves — and this is
the one item in H6b's inbox that cannot be done additively. The filing's own owner paragraph
anticipates this: it says a successor should decide the pathspec question **together with** the
`validate` tree-state ruling, and Ruling P answers the second with *no new seat*. Answering the first
with *widen the gate* would leave the two decided in opposite directions in one slice, on no argument.

**What the re-owning says, because a ledger line saying "filed" is not a filing.** The entry is
**amended, not struck** — the gap is real and reproduces (H6a measured it on 2026-08-23 and this
design did not re-perturb a tree to re-measure it; the entry's own reproduction recipe stands). The
amendment records: H6b considered it, declined it on the additive-charter ground above, decided it
beside Ruling P as the entry asked, and re-owns it **unassigned, with the reason** — no remaining
chartered slice has `E-CODE-DIRTY`'s pathspec as its surface (H9 is
`reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`; H3c-3's remaining 14 are folds and holdouts
inside cells), and the closer's own cost accounting is named for them: what an uncommitted root file
that is not a `.gitignore` should do at the gate.

**Alternatives rejected.** *Widen the pathspec to the repo root* — a behaviour change H6b cannot price,
and it would refuse runs on trees that are correct today. *Refuse a run whose root `.gitignore` is
dirty* — narrower, and still a new refusal on a shipped command, still unpriced, and it invents a
seventh state for a gate that has one. *Say nothing* — the entry names H6b by name, and a slice that
closes with it untouched reads as the *"a ledger line saying filed is not a filing"* failure from the
other end.

**Cost if wrong.** A run whose `code_hash` was narrowed by a rule no clone of its commit carries still
publishes, and the record does not say so. That cost is already disclosed in `reference.md` § How the
three are computed, which H6a rewrote to state the **mechanism** — whatever exclude rule the working
tree holds decides, committed or not — rather than an enumeration. H6b adds no new exposure; it
declines to close an existing one and says why.

### 13. Three stale claims about the environment block; `secrets.py`'s enumeration is DELETED, not rewritten

**Question.** Which shipped sentences go false when task 3 lands?

**Answer.** Three, and they are handled two different ways.

| Where | The claim | What happens |
|---|---|---|
| `src/publishable/secrets.py` module docstring | *"`provenance.environment` is assembled from `os`, `hostname`, `hardware` and `uv.lock` alone"* | **The enumeration is deleted.** The sentence's job is *"Never touches provenance"*, and the structural ground beside it — *"nothing in this module imports `publishable.provenance` or writes into the document it builds"* — carries the whole claim on its own |
| `src/publishable/study.py::_redact` docstring | `hostname` *"is never written today (measured at `ebf642a`) … becomes 'redacted' the day H6 writes it, with no code change here"* | **Rewritten to the fact**, because the sentence is *about* this slice: the day arrived, no code changed here, and Fixture E is the pin. The dated measurement is kept as history and marked superseded rather than deleted |
| `tests/test_study.py::_fixture_y_record` docstring | the same `ebf642a` parenthetical, plus *"which nothing in this build writes"* | **The parenthetical is deleted**; the fixture's own reason for existing — a hand-built record exercising every redacted field at once — survives unchanged, and it stays valuable beside Fixture E's real record rather than being replaced by it |

**Grounds.** `secrets.py`'s enumeration is **already false at `2b18435`** — the block is
`{manager, python_version, uv_lock, uv_lock_hash}`, so the sentence names three keys that do not exist
and omits three that do — and it stays false after H6b, which adds the three and removes none of the
four. **A rewrite invents; a deletion cannot**, and a round that closed a false-owner comment by
propagating it to two more sites is the reason this project prefers the deletion. The `study.py` one is
the exception the rule allows: its subject *is* the arrival of this slice, so there is a fact to state
rather than a claim to drop.

**Cost if wrong.** If the deleted enumeration was load-bearing for a reader's understanding of why
`secrets.py` cannot leak, the structural sentence beside it says the same thing without a list that
goes stale — which is the argument for the deletion, restated.

### 14. `diff` gains no row, and neither does `report`

**Answer.** Refused. `diff` compares five figures — `parameters_hash`, `code_hash`, `input_manifest`,
`uv.lock`, `apparatus` — and § What `diff` compares says *"five rows"* three times in its own prose.
`report` renders no environment key at all.

**Grounds.** A sixth row is a behaviour change to a shipped command's output on every invocation, and
`os`/`hardware` are descriptive rather than identity claims: `uv_lock_hash` is the environment
fingerprint `diff` compares, and § The apparatus core can only observe already argues that a fourth
fingerprint sits *"beside `uv_lock_hash`"* rather than becoming a hash. Nothing about H6b changes that
argument.

**Route and owner.** Filed with the six-unwritten-keys closure as a **stated non-gap**: `diff`'s row
count is documented and deliberate, so this is not a defect and no owner is invented for it.

**Cost if wrong.** Two runs on different platforms compare `identical` on all five rows. That is
already true today and is what `provenance` is read for.

### 15. § Executability does not move, and the derivation is given ahead of the table

**Answer.** The four-row table is repeated **character for character**, extracted from the H6a entry
with `sed` and diffed against that extraction. **No fifth number.**

**Derived, not assumed:**

- **Row 1 counts configs validating with zero errors.** H6b emits nothing at `validate`: it writes
  three keys inside `cli.command_run`, documents two codes raised by `provenance.py`, and edits
  documents. The two documented codes were undocumented, not unraised — **documenting a code changes
  no behaviour**, so nothing that did not fire before fires now. The sweep to confirm is
  `grep -c "E-GIT-NO-REPO\|E-GIT-NO-COMMIT" src/publishable/validate.py`, whose answer is **1** — the
  catch at `_check_data` that makes the check pass quietly, not an emit — with the control
  `grep -c "E-PARAM-MISSING" src/publishable/validate.py` → **3**, so the sweep can find a code
  `validate` does report.
- **Rows 2 and 3 name dependencies H6b does not touch** — `io.reuse_from`'s plugin-side call, and the
  `report_by`-under-`resample` construction inside `summarize_step`. H6b is `cli.command_run`'s
  provenance assembly, `study.py`'s and `secrets.py`'s docstrings, and documents.
- **Row 4 counts configs free of every core-side dependency this analysis can name.**
  `provenance.environment` is written for every run regardless of config; there is no declaration that
  opts into it and none that opts out, **so no config gains or loses a dependency**.
- **Neither new-documented code can fire for any of the nine.** Both are properties of a
  **repository** — no repository at all, or a repository with no commit — and no config in that
  analysis names a repository or reads any declaration to reach them.

**Cost if wrong.** A wrong figure in that analysis is the failure this repo has now made twice, both
times by carrying a summary phrase without re-deriving what it counted. The mitigation is the same
one H6a used: the derivation is written **before** the table so a reader checks the reasoning rather
than checking that the characters match.

### 16. What the guard pin is, and why arm P's post-edit state is written in the decided shape

**Answer.** Six arms, captured in task 1 before anything moves. **Four have no authorized editor.**

The one arm with an editor, **P**, is the shipped exact-key-set assertion, and its post-edit state is
specified **now, in the shape Decisions 5–9 have already decided** — a mapping for `hardware`, not a
scalar. H6a's batch-2 Major was a pin captured against a **superseded signature**, which forced the
next task to choose between a broken import and an unauthorized edit; the cause was capturing before
the design's own decision was reflected. Here `hardware`'s shape is Ruling O's, so the arm's advance
spec names `isinstance(hardware, dict) and set(hardware) == {"cpu_count"}` rather than "a type
assertion."

---

## The guard pin, captured before anything moves

| Arm | The claim | Sole authorized editor | State specified in advance |
|---|---|---|---|
| **P** | `tests/test_cli.py::test_h8b_arm_d_the_five_figures_diff_reads` — a real run's `provenance.environment`, with `python_version` popped, equals `{"manager": "uv", "uv_lock": None, "uv_lock_hash": None}` | **task 3 only** | **The `assert environment == {...}` line is BYTE-IDENTICAL after the edit.** Task 3 adds exactly three `.pop(...)` calls — `os`, `hostname`, `hardware` — and exactly three assertions on what it popped: `isinstance(os_value, str) and os_value`; `isinstance(hostname, str) and hostname`; `isinstance(hardware, dict) and set(hardware) == {"cpu_count"}`. Nothing else in the test moves, and the docstring gains one sentence naming H6b as the authorized editor. **A task-3 edit to the `==` literal, to any other assertion, or to `python_version`'s pop is a finding** |
| **Q** | `tests/test_cli.py::test_h8b_arm_c_the_records_key_lists_status_and_exit` — `run.yaml`'s eleven top-level keys and `provenance`'s thirteen, in order | **NONE** | unchanged, byte for byte. H6b adds no top-level `provenance` key and no top-level `run.yaml` key. **A passing arm after task 3 is the proof that the additive claim held at the level the record's own shape is read at** |
| **R** | `tests/test_cli.py::test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text` — every line of README, `design-principles.md` and `reference.md` carrying a worked-example literal, byte for byte | **NONE** | unchanged. Ruling O edits the `hardware:` line of § The two files, which carries **no** member of `_H5A_ARM_D_LITERALS` (measured). A passing arm after task 2 is the proof that the edit stayed off the worked example |
| **S** | `tests/test_study.py::test_study_add_redacts_hostname_when_present_on_a_synthesized_record` and `…_leaves_hostname_untouched_when_absent_from_the_source` — the hand-built record's two branches | **NONE** | unchanged. Task 4 **adds** Fixture E beside them rather than replacing either: the synthesized record still exercises every redacted field at once, and the real record exercises the wiring against a key core now writes. Only `_fixture_y_record`'s **docstring** moves, by task 7, and that is stated here so a docstring edit is not read as an arm edit |
| **T** | Both codes at the CLI, through `main([...])`: `run` outside any repository → `E-GIT-NO-REPO`, exit 1, on **stderr**; `generate experiment` with cwd outside any repository → the same code, exit 1, stderr; `run` in a commitless repository → `E-GIT-NO-COMMIT`, exit 1, and **not** `E-CODE-DIRTY` | **NONE** | captured green in task 1 against today's behaviour, which task 5 documents and does not change. **New coverage** — grepped newline-insensitively over `tests/`, nine hits for the two codes and none through `main`. A passing arm after task 5 is what makes the two new § Errors rows checkable against behaviour rather than against prose |
| **U** | `tests/test_cli.py`'s `_h6a_pin_project` arms B and C — the seven present figures a record carries for H6a's pin project, as literals | **NONE** | unchanged. This is the arm that would catch an H6b change that was not additive after all. It asserts individual keys rather than the `environment` mapping, so the three insertions are invisible to it — **which is the claim, and a passing arm is the proof** |

---

## The fixtures, each a claim with every literal computed

*A fixture is a claim too* — six in one slice once failed their own constraints, one asserting the very
value it existed to reject. Every literal below is either computed by the test at run time from a
value the test itself installed, or measured and named here.

**Fixture A — `os` is the three-component composition, and the fixture cannot be satisfied by
`platform.platform()`.** Monkeypatch `platform.system` → `"Fixtureos"`, `platform.release` →
`"9.9.9"`, `platform.machine` → `"fixarch"`, run a project end to end through `main(["run", …])`, and
assert `run.yaml`'s `provenance.environment.os == "Fixtureos-9.9.9-fixarch"`.
**Why the sentinels rather than recomputing the composition in the test:** a test that recomputes
`f"{platform.system()}-…"` and compares is *a mutation whose two branches cannot differ* — it would
pass against any implementation using the same three calls, in any order, and against
`platform.platform()` on a platform where the extra components happen to be empty. Installed sentinels
make the expected value a literal the test owns.

**Fixture B — `hostname` comes from `socket.gethostname`.** Monkeypatch it to
`"pinhost.example.invalid"` and assert the record carries that string verbatim.
**Discriminating against the plausible wrong source:** `platform.uname().node` returns the machine's
real node name and is unaffected by this patch, so an implementation reading it fails.

**Fixture C — `hardware` is a mapping of exactly one key, and `None` is carried.** Two arms, because
one arm cannot distinguish "writes the count" from "writes a constant". Arm 1: monkeypatch
`os.cpu_count` → `77`; assert `hardware == {"cpu_count": 77}`. Arm 2: monkeypatch it → `None`; assert
`hardware == {"cpu_count": None}` — **the key present with a null value**, not the key absent, which
is the distinction § The two files' `apparatus: null` already spells.

**Fixture D — the block's key order is § The two files' order.** Assert
`list(record["provenance"]["environment"]) == ["manager", "python_version", "os", "hostname",
"uv_lock", "uv_lock_hash", "hardware"]`, read from `yaml.safe_load` of the raw file (mappings preserve
insertion order). **This enumerates the literals the list should contain rather than iterating the
thing under test**, which is the vocabulary-test trap in its own words.

**Fixture E — Ruling Q, end to end, both halves.** Run a real project; `study new` a bundle **outside
any repository** and `study add` the run's `run.yaml`; read the bundled member and assert three things
against the **source** record read from the run directory:
`bundled.provenance.environment.hostname == REDACTED`; `bundled…os == source…os` and is a non-empty
`str`; `bundled…hardware == source…hardware` and is a mapping. **The positive control is the source
record itself** — comparing against a value the same run produced means an implementation that wrote
nothing fails both the redaction half and the verbatim half, where a bare `is not None` would pass on
an empty string.
*Measured precondition:* `study new` refuses a bundle path inside a git repository
(`E-STUDY-IN-REPO`), so the fixture's bundle is built under `tmp_path`, outside the project.

**Fixture F — arm T's three CLI invocations.** Measured today at the console script and reproduced in
the test through `main([...])`: `E-GIT-NO-REPO` at `run` on a de-`.git`-ed project, `E-GIT-NO-REPO` at
`generate experiment` from a cwd outside any repository, `E-GIT-NO-COMMIT` at `run` in a `git init`-ed
repository with no commit. Each asserts the **code string on stderr** and **exit 1**, and the third
additionally asserts `E-CODE-DIRTY` is **absent** from the output — the ordering claim Decision 3's row
makes. **What else in that output could produce the substring:** nothing — `E-CODE-DIRTY` appears in no
other message — and the assertion is made on `capsys`' **err** stream, which is where `main`'s
`PublishableError` printer writes.

**Fixture G — one row per code, checked mechanically rather than promised.** Extract every code in
§ Errors core raises' `Type · code` column from `docs/reference.md`, and assert `E-GIT-NO-REPO` and
`E-GIT-NO-COMMIT` each appear in **exactly one** row. **Both ends are read**: the same test greps
`src/publishable/` for `code="E-GIT-NO-REPO"` / `code="E-GIT-NO-COMMIT"` and asserts one raise site
each, so the test compares two independently obtained sets rather than comparing the table with
itself. Deleting a row fails it; adding a second row for the same code fails it; adding a second raise
site fails it.

---

## The mutations, each with the assertion that catches it and two branches that can differ

**A mutation is a claim too**: before trusting "this would prove X", check the two branches can
actually produce different results.

| # | Mutation | Caught by | Why the two branches differ |
|---|---|---|---|
| 1 | Delete `"os"` from the `environment` literal | Fixtures A and D; arm P | The key is absent where a string is asserted |
| 2 | Compute `os` as `platform.platform()` | Fixture A | Under Fixture A's patches, `platform.platform()` returns the sentinels **plus** its extra components (and, if its cache was already warmed by an earlier call, the machine's real string) — **neither equals `"Fixtureos-9.9.9-fixarch"`**. Checked in advance: `platform.platform()` resolves `system`/`release`/`machine` through module-global lookup, so the patch reaches it, and its memoization can only make the value *more* different, never equal |
| 3 | Read `hostname` from `platform.uname().node` | Fixture B | The patch is on `socket.gethostname`; `uname().node` returns the machine's real name, which is not the sentinel. **Two branches differ on every machine** |
| 4 | Write `hardware` as the bare int rather than a mapping | Fixture C arm 1; arm P's `set(hardware) == {"cpu_count"}` | `77 != {"cpu_count": 77}` |
| 5 | Write `cpu_count` as `os.cpu_count() or 1` | Fixture C **arm 2** | Arm 1 passes identically; only the `None` arm separates them, which is why arm 2 exists |
| 6 | Swap `os` and `hostname`'s insertion order | Fixture D only | Arm P passes (it compares a set-shaped dict after popping); Fixture D fails. **This is the mutation that proves Fixture D earns its place beside arm P** |
| 7 | `_redact` also redacts `os` | Fixture E's verbatim half | The redaction half still passes, so a fixture asserting only redaction would be silent — which is the reason both halves are in one assertion block |
| 8 | `_redact` stops redacting `hostname` | Fixture E's redaction half **and** arm S's synthesized-record test | Two independent tests fail, from a real record and a hand-built one |
| 9 | Delete `E-GIT-NO-REPO`'s new § Errors row | Fixture G | The extracted code set loses a member while the `src/` grep still finds the raise |
| 10 | Give `E-GIT-NO-COMMIT` a second § Errors row | Fixture G | Exactly-one becomes two |
| 11 | Reorder `git_provenance` so the dirty gate is computed before the `HEAD` check | Fixture F's third invocation | `E-CODE-DIRTY` appears and `E-GIT-NO-COMMIT` does not. **This mutation is against code H6b does not change** and is run to prove the fixture discriminates, then reverted — kept in a copy, never with `git checkout -- <file>` |

**Named blind in advance, and owed a replacement.** *A mutation to the prose of either new § Errors
row's message text* is caught by nothing: no test reads a row's sentence. **The replacement is Fixture
G plus arm T** — G pins that the row exists exactly once and that the code is raised exactly once, T
pins the behaviour the row describes (code, stream, exit code, ordering), so a row that drifts from
behaviour is falsifiable by reading the two beside each other. The residue — a row whose *English* is
wrong while its code, count and behaviour are right — is left to the batch review, named here rather
than discovered there.

**Also named blind:** *a mutation to Decision 12's re-owning paragraph in `spec-defects.md`*. Records
carry no tests anywhere in this project. Replacement: the batch-5 review checks every "filed" against
the file and every re-owning against the form this repo requires, which is the same check H6a's
batch 6 ran and which found two wrong authorities.

---

## What this slice refuses to build, each with its route and owner

| Refused | Route and owner |
|---|---|
| A `gpu` key under `provenance.hardware` | **Refused by ruling**, Decision 5. The route is an `apparatus_probe` declaring the fact; `reference.md` § The apparatus core can only observe is the section, and § The two files links to it where `gpu` used to be. No owner: this is a design answer, not a gap |
| A `W-` seat at `validate` for a dirty or empty tree | **Refused by ruling**, Decision 11. A `W-` code is a registry seat; the condition is caught at `run` by `E-CODE-DIRTY`. The `spec-defects.md` entry that named *"H6b task 18's ruling"* is updated to record the answer |
| Widening `E-CODE-DIRTY`'s pathspec to the repository root | **Declined, and re-owned unassigned with the reason**, Decision 12. Not additive; every uncommitted root file becomes a gate candidate. No remaining chartered slice has that pathspec as its surface |
| Narrowing `validate_config`'s bare `except ContractError` around `find_repo_root` | **Filed, unassigned with the reason.** The catch is wider than the comment's claim (*"No repo at all"*) and would swallow any future coded fault from the walk-up. Narrowing it is a behaviour change to `validate`, and no remaining slice has `validate`'s template-discovery path as its surface |
| A sixth `diff` row, or any `report` rendering, for `os`/`hardware` | **Refused by ruling**, Decision 14. Recorded as a stated non-gap rather than filed, since the five-row shape is documented and deliberate |
| The remaining **five** undocumented `E-` codes | **Filed, unassigned with the reason**, Decision 1. `run_identity.py`, `generators/` and the manifest path are nobody's chartered surface. **Five, not six** — the count was re-derived from the entry's table, and `E-STEP-EXISTS` is a **separate** observation rather than a member of the nine |
| A § Errors row for `E-STEP-EXISTS` | **Not one of the nine, and not H6b's.** The entry describes it as *"the one sibling that is documented, and only partially"* — a sentence in § Exit codes and diagnostics and no row. Recorded in the filing as its own observation so a later reader does not count it into the nine |
| A reader for `BaseTemplate.field_convention` | **Not H6b's, and re-verified rather than carried.** `grep -rn "field_convention" src/` at `2b18435` returns three hits — the declaration on `BaseTemplate`, `generic`'s copy of it, and a generator comment saying the file would be *"a string nothing reads"* — and no reader. It is still the sole standing example of *an unbuilt reader of a shipped surface*, and H6b creates no new one: `os` and `hardware` are **record data**, not declarations, and the § Errors rows document codes that are raised |

---

## Task decomposition — 11 tasks, six batches, every batch reviewed

| # | Task |
|---|---|
| 1 | **The guard pin, six arms**, captured before anything moves. Arms Q, R, S, T, U have **no authorized editor**; arm P names task 3 as its sole editor with the post-edit state written now |
| 2 | **Ruling O written into § The two files**: `hardware: {cpu_count: 32}`, and the sentence that names the apparatus as a GPU's route. Documents lead |
| 3 | **THE WRITE** — `os`, `hostname`, `hardware` in `cli.command_run`'s one dict literal, in the document's order; Fixtures A–D; arm P edited exactly as specified |
| 4 | **Ruling Q** — the reason written into § What `study add` redacts, and Fixture E, the end-to-end bundle pin with both halves |
| 5 | **Ruling N** — the two § Errors rows, and Fixture G |
| 6 | **Ruling P and Decision 12, decided together** — the § Templates paragraph re-read against the code as H6a left it, and the root-`.gitignore` filing declined and re-owned |
| 7 | The three stale claims (Decision 13) — `secrets.py`'s enumeration **deleted**, `study.py`'s rewritten to the fact, the test fixture's parenthetical deleted |
| 8 | `spec-defects.md` — the six-unwritten-keys entry **closed**, the nine-codes entry appended to, the `validate`-seat question answered, what H6b declines filed with reasons |
| 9 | `CLAUDE.md` — the slice entry and the order line |
| 10 | The consistency passes: mechanical over every edited `*.md`, cross-document over the four documents |
| 11 | § Executability — one dated entry, four rows character for character, no fifth number |

| Batch | Tasks | What its review must look for |
|---|---|---|
| **B1** | 1, 2 | Does every arm have a named sole editor or an explicit **NONE**, and is arm P's post-edit state written in the shape Ruling O decided (`hardware` a **mapping**)? Was arm R proven unaffected by the `hardware:` edit **by extracting `_H5A_ARM_D_LITERALS` and testing the line**, not by reading? Was arm T demonstrated able to fail? Does the § The two files edit link to § The apparatus core can only observe rather than restating it, and does the worked example still record `apparatus: null`? Mechanical pass on the `reference.md` edit |
| **B2** | 3 | **A real-command review**: run the installed console script and read `run.yaml` key by key. Is arm P's edit **exactly** three pops and three assertions with the `==` literal byte-identical? Are arms Q, R, S, U green **without** an edit? Does Fixture A use installed sentinels rather than recomputing the composition? Does Fixture C have **both** arms? Does mutation 6 fail Fixture D and pass arm P, as claimed? |
| **B3** | 4, 5 | Does Fixture E assert **both** halves against the **source** record, and is the bundle built outside any repository? Does each new § Errors row cover every reach path — the two that surface, the three that swallow, the cwd walk-up — and was the table's own **scope sentence** checked rather than this design's instruction? Does Fixture G read **both** ends, or does it compare the table with itself? |
| **B4** | 6, 7 | Was § Templates' whole paragraph re-read **against the code as H6a left it**, and was the finding reported as a measurement (`git status` before and after a real `validate`) rather than as an assertion? Was the *"no ignore file could have done that for it"* clause checked, since Ruling F made it false? Was Decision 12 recorded as a **decline with a reason and a re-owning**, never as a strike? Was `secrets.py`'s enumeration **deleted** rather than rewritten? |
| **B5** | 8, 9 | Every struck or amended entry checked against the code; every "filed" checked against the file; every owner a fact with a reason and never *"whichever slice next touches X"*; the six-unwritten-keys entry closed only if **every** row of its table is closed. Does `CLAUDE.md`'s order line lose H6b and keep H9 and H3c-3's 14? |
| **B6** | 10, 11 | **A full review, not a skim** — this is the batch whose output no later batch reads. Every sweep **names its files**, never filters its output, is **newline-insensitive**, and is **proven able to fail**. The four-row table repeated character for character, extracted with `sed` and diffed; **no fifth number**; the derivation printed ahead of the table |

---

## What could not be measured, and what this design assumed

- **`os.cpu_count()` returning `None` was never observed**, only documented. Fixture C arm 2 installs
  it by monkeypatch rather than provoking it, which measures the code's handling and not the
  platform's behaviour. Stated so nobody reads arm 2 as evidence that `None` occurs.
- **The `os` string on Linux and Windows was not observed** — this design measured only Darwin. The
  claim that the composed form yields exactly three components everywhere rests on `platform`'s
  documentation plus the observed Darwin shape, and Fixture A's sentinels make the test independent of
  it either way.
- **The uncommitted-root-`.gitignore` gap was not re-perturbed.** Decision 12 declines it and relies
  on H6a's 2026-08-23 measurement, whose reproduction recipe is in the entry. A decline does not need
  a re-measurement; a strike would have.


---

## Correction, 2026-08-23, made before dispatch — the remaining-codes count is five, not six

**Ruling N as it reached this design said *"the other six belong to their own surfaces"*. Re-derived
from the entry's own nine-row table, the number is FIVE**, and both the ruling's arithmetic and this
design's first draft carried the same omission: nine minus `E-CODE-DIRTY` is eight, but
`E-EXPERIMENT-UNKNOWN` was documented at H8c task 16 (`c794029`, recorded in the entry's own appended
note), so seven were undocumented before H6b and five remain after it. The first draft also filled the
sixth slot with **`E-STEP-EXISTS`, which was never one of the nine** — the entry names it as *"the one
sibling that is documented, and only partially."* Decision 1 and § What this slice refuses to build are
corrected above; `E-STEP-EXISTS` is recorded as a separate observation. **This is the shape
`CLAUDE.md` names twice — a count carried forward without re-deriving what it counted — caught here
before it reached a live filing.**

## Correction, 2026-08-23, made before dispatch — the other thirteen document-reading tests were swept

The design's *"`_H5A_ARM_D_LITERALS` contains nothing on the `hardware` line"* checked **one** pin.
`tests/` holds **thirteen** other sites that read `docs/reference.md` as text — seven in
`tests/test_cli.py`, five in `tests/test_diff.py`, one in `tests/test_report.py`. All were swept for
every literal of the environment block (`hardware`, `A100`, `hms-gpu-node`, `Linux-6.8.0`,
`manager: uv`, `python_version:`, `uv_lock:`, `environment:`, `The two files`), with
`grep -c "uv_lock_hash" tests/test_cli.py` → **4** as the control proving the sweep can find a string
that is present. **No test extracts § The two files' `run.yaml` fenced block.** The only `A100` hits are
`tests/test_report.py`'s **apparatus** fixture facts (`{"gpu": "A100"}`), which are correct and which
task 2 must not move; the only *"The two files"* hit is a docstring mention. So task 2's edit reaches no
pin beyond arm R, and **no additional post-edit state is owed.**
