# H6 scoping — hashes and provenance

**Measured on 2026-08-22 against commit `da9907b`** (`main` at HEAD, clean tree). **Read-only**:
nothing under `src/`, `tests/`, `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `docs/feasibility-llm-growth-studies.md` or
`docs/superpowers/spec-defects.md` was edited by this pass. Every project, roster, config, run
directory, bundle and probe built for it lives under the session scratchpad; one probe project was
copied out of an unrelated scratch tree and re-pointed rather than built fresh, and its own files
were the only ones edited. This document is the whole deliverable.

The charter under test is one row of
[`2026-08-08-implementation-spine-design.md`](specs/2026-08-08-implementation-spine-design.md)
§ The hardening slices: *"`code_hash`'s `.gitignore` awareness and its zero-file case,
`parameters_hash` normalization against `parameter_spec`, and the purity rule that forced both.
Independent."* Follows [`H8-SCOPING.md`](H8-SCOPING.md)'s and [`H5b-SCOPING.md`](H5b-SCOPING.md)'s
shape, including their habit of saying how each claim was measured.

---

## 0. Executive summary

1. **The charter's second clause names the wrong source of truth, and this is the finding that
   resizes the slice.** Every omitted-default case that moves `parameters_hash` today is a **core
   schema** key, not a template parameter — and core-schema defaults exist **nowhere as data**:
   `materialize.materialize_config` emits them as literal text lines (`cluster_by: null`,
   `allocation: within`, `correction: holm`, all six `limits`). Only the `parameters` block comes
   from `parameter_spec`. So "normalization against `parameter_spec`" reaches almost none of the
   measured gap, and closing it properly needs a defaults structure that
   `CLAUDE.md` § Invariants forbids by name (*"There is deliberately no separate defaults file"*).
   That is a **ruling**, not an implementation (§ 3).
2. **And the `parameters` half is not the easy half either.** An omitted `parameter_spec` default
   validates clean — `✓ config valid`, exit 0 — and then the step that reads it dies:
   `E-STEP-PARAM-UNKNOWN ContractError: parameters.analysis.min_samples is not a path this config
   holds`, every execution `failed`, `status: failed` (§ 3.3). Core does **not** materialize
   defaults into `cfg`, so normalizing the two configs to one hash would give **one identity claim
   to a config that runs and a config that cannot** — the opposite of what the rule is for.
3. **The two documents contradict each other about whether `.gitignore` touches `code_hash`, and
   the code sides with neither cleanly** (§ 2.1). § How the three are computed: *"taken from the
   **working tree** and skipping whatever `.gitignore` skips."* § Templates: *"while its `code_hash`
   is unchanged, that being the mechanism an ignore file has no bearing on."* Measured: **three of
   the four ignore patterns `publishable new` itself writes are not honoured** — `.env` MOVES the
   hash, `.venv/` MOVES it, and `*.py[cod]` is honoured for `.pyc`/`.pyo` and **not** for `.pyd`.
4. **The gap is not theoretical any more, and the S1 filing's "the two agree today" is falsified.**
   Two real runs, **same commit `a9b5df1`, both `code_dirty: false`**, differing only by a
   git-ignored `src/mix/.env`: `diff` prints `code_hash DIFFERS`, and
   `report study.yaml` over a bundle of both prints **`W-STUDY-CODE-HASH-MISMATCH`** — whose message
   names three candidate causes, **none of which is this one** (§ 2.2).
5. **The zero-file case is reachable through a shipped command.** A repo with an empty `src/`, no
   `templates/`, and an `entrypoint` importable from outside the two trees produced a **completed
   run at exit 0**: `run_id: run_2026-08-22T21-37-14Z_e3b0c44`,
   `code_hash: sha256:e3b0c442…` — the sha256 of the empty string — with no diagnostic (§ 2.3).
   So this branch is a refusal-or-warning plus pins, not a documentation decision.
6. **The purity rule the charter says "forced both" is not in `design-principles.md` at all**, and
   in its own terms it is already broken (§ 4). It is a module-boundary line in the spine design:
   *"`hashes.py` is pure. Resolved paths and a `Config` in, hex out. No filesystem policy, no
   git."* `hashes.py` rglobs and reads bytes today, and `_SKIP_DIRS` **is** filesystem policy. The
   real constraint is narrower and measurable: **13 `code_hash(` calls in `tests/test_hashes.py`
   run against a directory with no repository**, so the ignore predicate must be injected, not
   shelled for unconditionally.
7. **H6 is not independent of H9, in one direction.** Both branches change what `code_hash` and
   `parameters_hash` compute for an unchanged tree and an unchanged config, and `resume`/`reproduce`
   — H9's, both measured NOT BUILT — are the commands that compare a **recorded** figure against a
   **recomputed** one. H6 must land before H9, or H9 builds against definitions that then move
   (§ 9). H3c-3 touches no H6 surface.
8. **20 tasks, and it should split 12 / 8** on the value-changing / additive seam, with the additive
   half first on H5's precedent (§ 10).

---

## 1. Method

- **Ran, did not read, wherever a command could answer.** Nine real `publishable run` invocations
  across two scaffolded-and-committed projects, plus `validate`, `diff`, `study new`, `study add`,
  `report study.yaml` and `freeze` at the installed console script. Every `run.yaml`,
  `sweep.yaml` and bundle read key by key.
- **Hash arithmetic was measured by calling the shipped functions**, one probe per claim, each
  restoring the tree it perturbed and re-asserting the baseline digest afterwards (the final line of
  the § 2.1 probe re-checks `code_hash(p) == base`, and it printed `True`).
- **`NOT_BUILT_COMMANDS` was measured by invoking the commands**, not by printing the dict — a
  previous scoping was wrong for reading a constant. `resume`, `reproduce`, `dry-run`, `draft`,
  `demo`, `docs` each print *"is specified but not built in this version"*.
- **Sweeps were run over a named file list and each was proved able to fail.** `E-CODE-DIRTY` was
  swept across the four documents individually (`README.md`, `docs/design-principles.md`,
  `docs/experimental-designs.md`, `docs/reference.md`) — zero hits in each; the control was
  `grep -c "E-GIT-NO-REPO" docs/reference.md` → **2**, so the same sweep does find a code that is
  documented. The purity sweep over `docs/design-principles.md` (`pure|purity|without a
  repository|hashes.py`) returned zero; its control was `grep -c hash docs/design-principles.md` →
  **18**, so the file was being read.
- **Numbers in this document are counts I ran**, not estimates: 23 test functions and 13
  `code_hash(` call sites in `tests/test_hashes.py`, one `code_hash(` call site in all of `src/`,
  two `HASHED_TREES` readers.

---

## 2. `code_hash` today

`hashes.hashed_files` walks `src/**` and `templates/**` under the repo root, skipping any path whose
**tree-relative parts** hit `{__pycache__, .git, .ruff_cache, .mypy_cache, .pytest_cache}` or whose
suffix is `.pyc`/`.pyo`, sorts the `(repo-relative posix path, file)` pairs, and `code_hash` folds
`sha256(path) \0 sha256(contents) \n` over them. It reads the **working tree**, never git — which
§ How the three are computed states and gives `draft`'s reason for. It has **exactly one caller in
`src/`**: `cli.command_run` (`grep -rn "code_hash(" src/publishable/*.py`, one hit besides the
definition). `freeze` re-reads the lockfile and the apparatus and does not recompute it; `diff`,
`report` and `study` compare **recorded** strings and § Warnings core reports says so for both.

`HASHED_TREES` has two readers, and this matters for the fix: `hashes.hashed_files` and
`provenance.git_provenance`, which passes the same tuple to `git status --porcelain --`. **The hash
and the dirty gate already share one constant and would share one file list.**

### 2.1 The `.gitignore` case, measured

One committed probe project, one perturbation at a time, baseline digest re-asserted after each:

| Perturbation under `src/` | git | `code_hash` |
|---|---|---|
| `src/mix/deep/__pycache__/x.pyc` | ignored | **SAME** |
| `src/mix/loose.pyc` (no `__pycache__` dir) | ignored | **SAME** |
| `src/mix/loose.pyd` — matched by the scaffold's own `*.py[cod]` | ignored | **MOVES** |
| `src/mix/.env` — matched by the scaffold's own `.env` | ignored | **MOVES** |
| `src/.venv/lib/site.py` — matched by the scaffold's own `.venv/` | ignored | **MOVES** |
| a **file** named `src/__pycache__` | untracked | **SAME** |
| a **file** named `src/.git` | untracked | **SAME** |
| symlink `src/mix/linked.py` → outside the repo | untracked | **MOVES** (target's bytes) |
| symlinked **directory** `src/mix/linkeddir` → outside the repo | untracked | **SAME** (`rglob` does not descend it) |

`git check-ignore --stdin` confirmed the git side for the `.env` and `.pyd` rows
(`.gitignore:2:.env` and `.gitignore:6:*.py[cod]`), and a step file fed through the same call
matched nothing.

So the S1 filing's *"In practice nothing else gitignored appears under `src/**` or `templates/**`,
so the two agree today"* is **falsified by the scaffold's own `.gitignore`**: three of its four
patterns disagree with the hash, and one of the three is the credentials line. A `.env` under
`src/` is not a leak — a sha256 discloses nothing — but its **contents move a published identity
claim**, and the file is one the scaffold promises is never committed, so the claim cannot be
reproduced from the commit.

Two smaller facts worth carrying into the design. The skip test is over **path parts**, so it
answers *"does any component have this name"* rather than *"is this a directory named
`__pycache__`"* — a file with that name is silently skipped (rows 6 and 7). And the `__pycache__`
skip is genuinely **unconditional**, as § Templates claims, including for a repo whose `.gitignore`
omits it — which means the fix is an **intersection**, not a replacement: git's file list *minus*
the fixed skip set.

**The document contradiction this branch has to rule on, quoted rather than paraphrased.**
§ How the three are computed: *"**`code_hash` is `sha256` over the sorted list of `(repo-relative
path, sha256 of file contents)` pairs** across `src/**` and `templates/**`, taken from the **working
tree** and skipping whatever `.gitignore` skips."* § Templates: *"`code_hash` skips `__pycache__`
directories and compiled `.pyc`/`.pyo` files unconditionally, wherever in the hashed trees they sit
— it reads the working tree rather than git, so no ignore file could have done that for it. […] A
hand-assembled repo whose `.gitignore` omits that line goes dirty at `validate` and fails `run` —
while its `code_hash` is unchanged, that being the mechanism an ignore file has no bearing on."*
Read narrowly, § Templates is only saying that the `__pycache__` skip owes nothing to an ignore
file. Read as written — *"the mechanism an ignore file has no bearing on"* — it describes
`code_hash` generally and **contradicts § How the three are computed**. Which reading wins decides
whether H6 *closes* a defect or *ratifies the code and edits § How the three are computed instead*,
so it is task 1 rather than an implementation detail.

**A measured implementation route, so the ruling is made with a cost in hand.**
`git ls-files -co --exclude-standard -- src templates` returns exactly *tracked plus
untracked-not-ignored* — one subprocess, **12 ms on this repo** for 52 paths, the same pathspec
`git_provenance` already passes to `git status`, and the right semantics for a tracked file that
matches an ignore pattern (git does not skip it, so the hash must not either). On the probe project
it returned the five source files and both `.gitkeep`s, and omitted `.env`, `loose.pyd` and the
`__pycache__` entry.

### 2.2 What the gap already costs, end to end

Two runs of one config at the **same commit**, the second after writing a git-ignored
`src/mix/.env`:

```
-- run_2026-08-22T21-33-26Z_6a23283   code_hash: sha256:6a23283c…  commit: b16a9b9…  code_dirty: false
-- run_2026-08-22T21-33-27Z_770ec37   code_hash: sha256:770ec370…  commit: b16a9b9…  code_dirty: false
```

`diff` on the pair printed `code_hash DIFFERS` at exit 0, `parameters_hash identical`. Re-run at a
later commit and bundled through `study new` / `study add` / `report study.yaml`:

```
warning W-STUDY-CODE-HASH-MISMATCH …/bundle/study.yaml
        runs m1, m2 all record commit a9b5df1a470fa81e19a3186a0a9d825579c0ff34 and their
        code_hash differs (['sha256:6a23283c…', 'sha256:770ec370…'])
```

§ Warnings core reports' row for that code says the finding is real *"since the same commit means
the same two hashed trees"*, and lists *"a dirty tree, an uncommitted `templates/**` edit, and
another experiment's package moving inside the two hashed trees"* as candidate causes. **None of the
three applies here**, and the run records say `code_dirty: false` on both sides. So the
`.gitignore` branch is not only a hash-purity question — it is the one live cause of that warning
that a reader cannot diagnose from the record. Whether the row gains a fourth candidate or the
cause disappears is decided by task 1.

### 2.3 The zero-file case, and it is reachable

Three distinct situations produce the identical digest, exactly as the S1 filing describes:

| Repo | `code_hash` |
|---|---|
| empty `src/`, no `templates/` | `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| no `src/`, no `templates/` | the same |
| `src/` holding only `__pycache__/x.pyc` | the same |

**The filing's owner line is stale**: it routes the diagnostic to *"H1 Validation's registry once H6
says what it should say"*, and H1 has shipped — the closed-slice-owner pattern this repo rejects by
name at its own `RE-OWNED 2026-08-19` entry. H6 owns both halves now.

And it is not hypothetical. A repo with an **empty `src/`**, no `templates/`, and
`entrypoint: "outside_pkg.experiment:OutsideExperiment"` importable from a directory on
`PYTHONPATH` — `load_experiment` inserts `<repo>/src` at the front of `sys.path` but
`importlib.import_module` still resolves anything else already importable — produced:

```
run_id: run_2026-08-22T21-37-14Z_e3b0c44
status: completed
code_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

A completed run at exit 0, no warning, whose entire pipeline came from outside both hashed trees,
and whose **`run_id` carries the empty digest as its own short hash**. This is precisely the failure
`design-principles.md` § Core generates the standard pipeline argues against for core's own code
(*"anything core hands you by import sits outside it"*) — reached here with the user's own package.

**Blast radius, measured rather than guessed:** two tests in `tests/test_hashes.py`
(`test_code_hash_skip_list_matches_relative_path_not_absolute`,
`test_code_hash_handles_a_dot_git_intermediate_path_component`) use
`code_hash(tmp_path / "nonexistent_empty_repo")` as a **negative control**, so a refusal at the
`hashes.py` level would break them and the diagnostic has to live at the caller.

---

## 3. `parameters_hash`

`parameters_hash` is `sha256` over `covered_config(config)`'s canonical JSON — `json.dumps` with
`sort_keys=True`, compact separators, `ensure_ascii=False` — where `covered_config` drops `metadata`
and `data.input_dir`/`output_dir`. It hashes the **parsed config as written**: the digest of the
probe config computed directly from `yaml.safe_load` equalled the `parameters_hash` its real run
recorded, so nothing materializes defaults on the way in. Its docstring already says it does not
normalize and names the filing.

### 3.1 Key order is already normalized — that half of the charter's word is done

Reversing the top-level key order, `data`'s key order and `data.units`' key order together left the
digest **identical** (`sha256:dc9c0975…` both ways). `sort_keys=True` is recursive, so YAML key
order can never move this hash. `tests/test_hashes.py::test_parameters_hash_is_insensitive_to_key_order`
already pins it, over a two-key mapping.

### 3.2 An omitted default is not normalized — 7 of 7 cases move the hash

| Omission from the `init`-written config | `parameters_hash` |
|---|---|
| `data.units.cluster_by` (the filing's own example) | DIFFERS |
| `data.units.holdout` | DIFFERS |
| `data.units.measurements` | DIFFERS |
| `sweep` | DIFFERS |
| `statistics` | DIFFERS |
| `hypotheses` | DIFFERS |
| `plugin` | DIFFERS |
| `metadata.description` rewritten (control) | identical |
| `parameters.analysis.min_samples` (a real `parameter_spec` default) | DIFFERS |

End to end: the config with the `cluster_by: null` line deleted **validates clean** and its run
recorded `parameters_hash: sha256:f4954b3a…` against the full config's `sha256:dc9c0975…`.

**And `diff` prints the delta, so § How the three are computed's justification for the rule is
false against the shipped command:**

```
parameters_hash    DIFFERS
  data.units.cluster_by  null → (absent)
```

The document's argument is *"`diff` would report a difference with nothing to print."* It reports a
difference **with exactly the right thing printed**. The defect is real; its stated reason is not,
and the reason has to be re-argued from the real symptom — two configs declaring the same run carry
different identity claims, which is what `resume`'s refusal and a hypothesis's `declared_in:
parameters_hash …` read. (`hypotheses.py` writes that string; grepped.)

**The eight rows above are core schema keys, and this is where the charter breaks.** Only the
ninth is a `parameter_spec` default. Core-schema defaults are **not data anywhere in `src/`**:
`materialize.materialize_config` builds the config as a list of literal strings —
`"    cluster_by: null                # e.g. site, when units aren't independent"`,
`"  correction: holm                 # none | bonferroni | holm | fdr_bh"`, all six `limits`
lines — and only the `parameters` block is generated from `template.parameter_spec` via
`_parameters_block`. So "normalize to what `init` would have materialized" cannot be computed from
`parameter_spec`; it needs either a new core-schema defaults structure — a **second source of
truth**, which `CLAUDE.md` § Invariants forbids for `parameter_spec` by name and which
`reference.md` § There is no separate defaults file states normatively — or a narrower rule.

### 3.3 The `parameters` half is worse than the core half, and this was a surprise

With `parameters.analysis.min_samples` deleted, `validate` says `✓ config valid` at exit 0. A step
that reads it then fails:

```
error: 'E-STEP-PARAM-UNKNOWN ContractError: parameters.analysis.min_samples
  is not a path this config holds'
```

— every execution `failed`, `status: failed`. Core does **not** apply `parameter_spec` defaults to
`cfg`; `validate` uses them only for its own checks (`validate.py` reads `param.default` at its
constraint sites, and `W-TEMPLATE-VERSION`'s message already enumerates *"every `parameter_spec`
parameter carrying a default that this config does not set"* — so the reader exists but only fires
under a version mismatch). **Normalizing the hash first would give one identity claim to a config
that runs and a config that cannot run at all.** The honest order is: rule on whether an omitted
defaulted parameter is refused at `validate`, or materialized into `cfg`, *and then* let the hash
follow. That is two rulings, not one implementation.

---

## 4. The purity rule the charter says "forced both"

It is **not in `design-principles.md`.** Swept for `pure|purity|without a repository|hashes.py`:
zero hits, with a passing control (`grep -c hash` → 18). What exists is a module-boundary line in
the spine design § Modules and boundaries: *"**`hashes.py` is pure.** Resolved paths and a `Config`
in, hex out. No filesystem policy, no git."* The S1 filing gives the same reason in its own words:
*"this plan makes `hashes.py` pure so it can be tested without a repository."*

**In its own terms the rule is already broken**, which narrows the decision usefully. `hashes.py`
rglobs the working tree and reads file bytes; `_SKIP_DIRS`/`_SKIP_SUFFIXES` *is* filesystem policy,
and it is policy that decides what the hash covers. What survives, and what actually constrains the
fix, is the testability half — and it is measurable: **13 of the 23 test functions'
`code_hash(` calls in `tests/test_hashes.py` run against a bare `tmp_path` with no repository**
(`grep -c "git init\|subprocess" tests/test_hashes.py` → 0). So the design is forced towards an
**injected predicate defaulting to today's behaviour**, resolved by the caller — `provenance.py`
already shells to git and already imports `HASHED_TREES` — rather than `hashes.py` shelling out.

`artifacts.allocation_hash`'s docstring states a companion boundary H6 must not break:
`hashes.py` holds hashes of things the caller already has, while a hash of a document is placed
beside the code that assembles it. Environment capture (§ 5) therefore does not belong in
`hashes.py` either.

---

## 5. Every hash the record carries, against § Provenance

Enumerated from the code (`grep -rn "hashlib\|_hash(" src/publishable/*.py`), then checked against
`reference.md` § The two files and § Three hashes:

| Figure | Computed by | In the record | Documented |
|---|---|---|---|
| `code_hash` | `hashes.code_hash` | `run.yaml` top level, and `run_id`'s suffix | § Three hashes ✓ |
| `parameters_hash` | `hashes.parameters_hash` | top level | ✓ |
| `input_manifest_hash` | `manifest.manifest_hash` | `provenance` | ✓ |
| per-file `sha256` at the policy's depth | `manifest.build_manifest` | `manifest/input.json` | ✓ (`hash_all`/`hash_index`/`none`) |
| `uv_lock_hash` | `uv_support.uv_lock_info` | `provenance.environment` | ✓ |
| `units_hash` | `units.units_hash` | `provenance` | ✓ |
| `allocation_hash` | `artifacts.allocation_hash` | `provenance` | ✓ |
| `apparatus.hash` | `apparatus.apparatus_hash` | `provenance.apparatus` | ✓ § The apparatus core can only observe |
| upstream `code_hash`/`parameters_hash` | copied by `lineage.UpstreamLedger` | `provenance.upstream[]` | ✓ |
| `design_digest` | `hashes.design_digest` | `sweep.yaml`, *"a derivation input, not an identity claim"* | ✓ |
| seed derivations (32/64-bit ints) | `replication`, `sweep`, `units`, `stats`, `base_step` | not published as digests | ✓ § What `auto` derives from |

**No hash is documented and uncomputed, and none is computed and undocumented.** `holdout_hash` is
the near-miss and it is deliberate: § `allocation.json` says *"There is no `holdout_hash`"*, and
`artifacts.py` says the same in its own docstring. Where the record **is** short of the document is
not a hash: `provenance.environment.os`, `.hostname` and `.hardware` are in § The two files'
`run.yaml` example and **written nowhere** — `cli.command_run` builds `environment` with exactly
four keys (`manager`, `python_version`, `uv_lock`, `uv_lock_hash`), and a real run's record shows
those four and no others. That is the last live row of the six-unwritten-keys filing, and it is
H6's.

One carried expectation to honour rather than rediscover: `study.py`'s `_redact` **already**
redacts `provenance.environment.hostname` and says in its own docstring that the field *"is never
written today (measured …) … becomes 'redacted' the day H6 writes it, with no code change here."*
§ What `study add` redacts lists `hostname` and lists neither `os` nor `hardware`, so H6 must rule
on those two rather than assume the table covers them.

---

## 6. The dirty gate — what counts, and who checks

`provenance.git_provenance` computes `code_dirty` from `git status --porcelain -- src templates`;
`cli.command_run` turns it into `E-CODE-DIRTY` and returns exit 1 before any execution. Measured
at the console script:

| Tree state under `src/`/`templates/` | `validate` | `run` |
|---|---|---|
| untracked file (`?? src/mix/untracked_helper.py`, `?? templates/…`) | `✓ config valid`, exit 0 | `E-CODE-DIRTY`, exit 1 |
| staged, uncommitted (`M  src/mix/steps/step01…py`) | `✓ config valid`, exit 0 | `E-CODE-DIRTY`, exit 1 |
| ignored-but-present (`src/mix/.env`, `src/mix/loose.pyd`) | exit 0 | **runs**, `code_dirty: false`, hash moved |
| `draft`, `resume` | — | NOT BUILT (measured) |

Two document defects fall out, both inside H6's measured surface.

**§ Templates says a hand-assembled repo *"goes dirty at `validate`"*, and `validate` says nothing
at all.** There is no dirty check in `validate.py` (`grep -rn "dirty" src/publishable/validate.py`
→ zero hits) and no `W-` code for it anywhere in `src/`; the only site is `command_run`'s gate. The
sentence describes behaviour that does not exist — the *"assuming a documented rule has code behind
it"* misreading, in a section H7a already rewrote.

**`E-CODE-DIRTY` has no § Errors row.** Swept individually across all four documents: zero hits in
each, control passing. It is raised by shipped code and named in one test's comment
(`tests/test_acceptance.py`, 2 mentions — the whole suite's total). It is one of the nine codes the
`spec-defects.md` entry *"Nine undocumented run-time and creation-command `E-` codes"* routes to
nobody, and that entry explicitly offers **"widen H6's charter"** as option 1 while saying the
choice is the spine owner's, not a task's. **This scoping does not absorb the nine.** It
recommends H6 take the **three on its own measured surface** — `E-CODE-DIRTY` (the gate above),
`E-GIT-NO-REPO` and `E-GIT-NO-COMMIT` (`provenance.py`, the walk-up this slice is named for) — and
leave the six creation-command and run-identity codes to a tenth slice or a later amendment. That
is one task, not seven, and it needs a ruling before it is planned.

---

## 7. `reproduce` and `resume`'s comparisons — none of them exist

Measured by invoking, not by reading `NOT_BUILT_COMMANDS`: `resume`, `reproduce`, `dry-run`,
`draft`, `demo` and `docs` all print *"is specified but not built in this version"*. So **no shipped
command compares a recorded hash against a recomputed one.** `freeze` re-hashes only the lockfile
(`W-FREEZE-LOCK-MOVED`), and refuses a run directory that already holds a `run.yaml`
(`E-FREEZE-RUN-ENDED`, measured). `diff`, `report study.yaml` and `study add` compare **recorded**
strings and the documents say so.

This is what makes both H6 branches cheap **now** and expensive later, and it is the whole ordering
argument: H6 changes what the two identity functions compute for an unchanged input, so every
`run.yaml` already on disk holds a figure the new build will not reproduce. **Nothing in the record
marks which definition produced it**, and the obvious carrier is not free: `run.yaml`'s
`schema_version` is core's own constant `run_record.SCHEMA_VERSION = "1.0"`, and
`lineage.read_record_file` **refuses** any other value — measured by editing one run's record to
`'1.1'`: `E-UPSTREAM-RECORD-VERSION`. Bumping it to signal a hash-definition change would break
`io.reuse_from` against every record already written. A `provenance` key is the cheaper carrier;
adding nothing at all is a defensible third answer. It needs to be decided in writing, which is why
it is a task of its own.

---

## 8. `diff`'s hash rows — H9's `uv.lock` filing is H9's, and here is where H6 stops

H5b filed *"`diff`'s `uv.lock` row prints two digests and never names the package whose pin moved"*
against **H9**, on the ground that `reproduce` is what reads the environment back. **That routing
survives H6's scoping**, and the reason is visible in one command's output rather than argued:
`diff`'s `parameters_hash` row already prints per-key detail lines
(`data.units.cluster_by  null → (absent)`, § 3.2) because `diff` reads the two embedded configs;
`uv.lock`'s row has only two digests because a run archives the lockfile but the record carries
only its hash. Producing a per-package delta means reading two archived `environment/uv.lock`
files and deciding what a moved pin means — the question H9's charter is defined by (*"`reproduce`
is what reads the environment back, so it decides the unresolved lockfile questions"*).

**H6's surface stops at what the record claims and how it is computed**, not at how a comparison
renders. One consequence for H6 to honour rather than widen: if task 1 rules that `code_hash`
becomes `.gitignore`-aware, `diff`'s `code_hash` row and § Warnings core reports'
`W-STUDY-CODE-HASH-MISMATCH` row both keep their wording — the cause listed above disappears
instead. If task 1 rules the other way, that row **gains** a candidate cause, and editing it is
H6's, not H8's.

---

## 9. What H6 blocks, and what blocks H6

- **H6 → H9: a real ordering constraint, replacing "independent."** H9 builds `resume` (which
  § Resuming says refuses when `parameters_hash`, `code_hash` or `uv.lock` moved) and `reproduce`
  (which recomputes both against a published record). Both branches of H6 change what those
  functions return for an unchanged input. H6 after H9 means H9 ships comparisons against
  definitions that then move, and its own pins would be the first thing H6 has to weaken — the
  failure mode `CLAUDE.md` names for pins. **H6 before H9.**
- **H6 ← H9: nothing.** The one lockfile question H9 owns per `spec-defects.md` is *the missing
  `uv.lock` decision*; `W-ENV-UNLOCKED` already fires (observed on every probe run in this pass),
  and no H6 task reads it. H6 does not need H9's answers; it supplies the definitions H9 compares.
- **H3c-3: independent, verified.** Its surface is folds inside cells. The only hash in that
  neighbourhood is `allocation_hash`, which hashes whatever `build_allocation_document` returns and
  is owned by H3 — H3d already extended that document with a fourth key without touching any hash
  code, which is the precedent. No H6 task and no H3c-3 task share a file.
- **H5 (complete) left H6 one thing and no obstacle:** `study.py`'s waiting `hostname` redaction
  is H8c's, not H5's, and it is a gift rather than a dependency.

---

## 10. The task count, and the split

**20 tasks. It should split 12 / 8**, on the seam this project has now used twice (H7d Part B,
H8b Decision 7, H5a/H5b): *changing what an existing key reports* versus *additive*.

### H6a — the two hash definitions (12 tasks, value-changing)

| # | Task | Why this size |
|---|---|---|
| 1 | **Ruling + document edit:** § How the three are computed's *"skipping whatever `.gitignore` skips"* versus § Templates' *"an ignore file has no bearing on"*. Both quotes reproduced, both readings named, one wins | The whole branch's direction; a doc-only task if the code is ratified |
| 2 | `hashed_files`/`code_hash` gain an injected file-list predicate, default = today's behaviour | 13 repo-less `code_hash(` calls in `tests/test_hashes.py` must keep passing |
| 3 | The git-backed predicate in `provenance.py` (which already imports `HASHED_TREES` and shells to git): one `git ls-files -co --exclude-standard -- src templates`, **intersected** with the fixed skip set so a repo whose `.gitignore` omits `__pycache__` still skips it | Measured route, 12 ms; the intersection is what keeps § Templates' "unconditionally" true |
| 4 | Wire it at `command_run`'s single call site; pins with positive controls for `.env`, `*.pyd`, `.venv/`, **and a tracked file matching an ignore pattern** (git does not skip it, so the hash must not) | The tracked-file arm is the one a naive `check-ignore` implementation gets wrong |
| 5 | Hash ↔ dirty-gate agreement: one file list, one pin that an ignored-but-present file is neither dirty nor hashed; and replace the two byte-identical `__pycache__` tests with one that can fail | `test_code_hash_ignores_pycache` and `test_code_hash_still_skips_a_genuine_pycache_dir_inside_the_tree` have identical bodies |
| 6 | **Ruling:** does a `code_hash`/`parameters_hash` definition change get a marker in `run.yaml`? With the measured cost of the obvious carrier — bumping `schema_version` makes `read_record_file` refuse every existing record (`E-UPSTREAM-RECORD-VERSION`) | A decision with a written cost, not an implementation |
| 7 | The zero-file diagnostic: refusal or warning, its code, its § Errors row, its registry seat, at the **caller** | Reachable at `run` today (§ 2.3) |
| 8 | Zero-file blast radius: re-pin the two `tests/test_hashes.py` tests that use the empty digest as a negative control, plus an end-to-end pin of the empty-`src/` run | Those two tests are why the guard cannot live in `hashes.py` |
| 9 | **Ruling:** `parameters_hash` normalization's scope, given that core-schema defaults exist only as literal text in `materialize_config` and that a defaults structure is forbidden by name. Three options: normalize `parameters` only; build a core-schema default table and argue against the invariant; delete the sentence and name the caller | The charter's second clause, re-derived — the single largest finding |
| 10 | **Ruling:** the `parameters` half — an omitted defaulted parameter validates clean and its step raises `E-STEP-PARAM-UNKNOWN`. Refuse/warn at `validate`, or materialize defaults into `cfg`? | Normalizing before this is settled equates a runnable and an unrunnable config |
| 11 | Implement whatever 9 and 10 rule, with pins over the nine measured cases of § 3.2 | Sized against the ruling; two of the three options for task 9 are code |
| 12 | Correct § How the three are computed's justification: `diff` prints `data.units.cluster_by null → (absent)`, so *"a difference with nothing to print"* is false | Prefer deleting the false clause to rewriting it |

### H6b — the environment record and the diagnostic debt (8 tasks, additive)

| # | Task | Why this size |
|---|---|---|
| 13 | `provenance.environment.os`, beside the `python_version` that already ships | One key, one pin, `platform` is stdlib |
| 14 | `provenance.environment.hostname`, plus a pin that a bundle carries `<redacted by study add>` for it — the wiring exists and is waiting | H8c wrote the redaction against a key nobody writes; the pin is the point |
| 15 | `provenance.environment.hardware`: `cpu_count` is stdlib; **`gpu` is a decision** — core cannot probe one without a dependency or a subprocess, and § The two files shows `{gpu: "1x A100 80GB", cpu_count: 32}` | A ruling plus possibly a document edit; the apparatus is the existing route for anything core cannot observe |
| 16 | Close the six-unwritten-keys filing's last row; rule whether § What `study add` redacts needs `os`/`hardware` rows | The filing's other rows are already struck; this closes it |
| 17 | `E-CODE-DIRTY`'s § Errors row, plus `E-GIT-NO-REPO`/`E-GIT-NO-COMMIT` — **needs the spine owner's ruling first** on whether H6's charter widens (the nine-codes entry's option 1). Recommendation: take these three, leave six | One row per code covering **every** emit site, which is what two sub-slices shipped wrong |
| 18 | § Templates' *"goes dirty at `validate`"*: either `validate` gains a dirty warning, or the sentence changes | `validate` is silent today (measured); a `W-` code is a registry seat, so this is a ruling too |
| 19 | Documents-and-codes consistency pass — mechanical (links, anchors, tables, whitespace) and cross-document over the four documents | The batch with no review is where the findings are; this one is nobody else's input |
| 20 | `spec-defects.md`: strike H6's four entries that close, re-own what H6 declines, and correct the zero-file entry's stale *"H1's registry"* owner | Four entries name H6; a ledger line saying "filed" is not a filing |

### Which half first

**H6b first, H6a second**, on H5's precedent: the additive half lands alone, and the half that
changes what a shipped key reports ships last and by itself, so a whole-branch review of it is not
also reviewing new record keys. Three supporting facts rather than the analogy alone: H6b's keys
(`provenance.environment.*`) and H6a's possible marker (§ 7) are **different key sets**, so the
split does not cut through one behaviour change; H6b unblocks a redaction H8c already shipped
against nothing; and H6a's task 1 is a document ruling that benefits from being the branch's own
first task rather than the tenth.

**Both halves must land before H9.** If only one can, it is H6a.

---

## 11. Disagreements with the record found by this pass

Reported as a list, not a count of zero, and each one grepped or run rather than recalled.

1. **The charter's *"normalization against `parameter_spec`"* names a source of truth that cannot
   reach 8 of the 9 measured cases** (§ 3.2). Read `materialize.py` in full to confirm core-schema
   defaults are text.
2. **The S1 filing's *"nothing else gitignored appears under `src/**` or `templates/**`, so the two
   agree today"* is falsified** by three of the scaffold's own four ignore patterns (§ 2.1).
3. **§ Templates and § How the three are computed contradict each other** about `.gitignore` and
   `code_hash`, under § Templates' general reading (§ 2.1).
4. **§ Templates' *"goes dirty at `validate`"* has no code** — zero `dirty` hits in `validate.py`
   (§ 6).
5. **§ How the three are computed's justification for normalization is false** against the shipped
   `diff` (§ 3.2).
6. **The zero-file entry's owner line is stale** — it routes the diagnostic to H1, which has
   shipped (§ 2.3).
7. **The spine's *"Independent"* verdict for H6 is too strong in one direction** — H6 before H9
   (§ 9).
8. **`E-CODE-DIRTY` is raised by shipped code and documented in none of the four documents**, and
   the nine-codes entry's option 1 is a live, unruled proposal to widen this charter (§ 6).
9. **The purity rule cited by the charter is not in `design-principles.md`**, and is already broken
   in its own terms (§ 4).
10. **Two tests in `tests/test_hashes.py` are byte-identical in body** — a duplicated pin, not a
    defect, recorded so task 5 does not "fix" one and leave the other (§ 2.1, § 10).
