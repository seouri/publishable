# H6a — the two hash definitions

**Written 2026-08-22, against `main` at `560e3a8`.** Design only; nothing under `src/`, `tests/` or
the four documents was edited by this pass. Every measurement below was run in a scratchpad
project built for it, and every literal digest in this file was **computed, not recalled** — the
probes are named where the claim is made.

The scoping is [`H6-SCOPING.md`](../H6-SCOPING.md), measured 2026-08-22 against `da9907b`. This
design re-checks its load-bearing measurements rather than trusting them, and **disagrees with it
in one place that changes the implementation** (Decision 2). The charter under test is one row of
[`2026-08-08-implementation-spine-design.md`](2026-08-08-implementation-spine-design.md) § The
hardening slices, and one of its two clauses is **rejected** here (Decision 9).

---

## What this slice is, in one paragraph

H6a changes what **`code_hash`** computes: a file the repo's own `.gitignore` skips stops moving
the identity claim, and a repo with no file to hash stops publishing the digest of nothing at exit
0. It changes what **`parameters_hash`** computes: **nothing** — the charter's normalization clause
is rejected with grounds, and what H6a fixes instead is the half that misleads, an omitted
template parameter that validates clean and then kills every execution. One hash moves, five
record fields carry it, one warning and two errors are minted, and no config in the feasibility
analysis becomes more or less executable. Twelve tasks, six batches, every batch reviewed.

---

## The measurements this rests on

Every row was produced by a probe under the session scratchpad. Where the probe is the scoping's,
it was **re-run here** rather than cited.

| Claim | How it was measured | Result |
|---|---|---|
| Three of the scaffold's own four ignore patterns move `code_hash` | one committed probe project, one perturbation at a time, baseline digest re-asserted after each | `.env` **MOVES**, `.venv/lib/site.py` **MOVES**, `loose.pyd` **MOVES**; `__pycache__/x.pyc` and a loose `.pyc` **SAME** |
| The scaffold writes exactly those four patterns | `scaffold.GITIGNORE`, read | `.env`, `__pycache__/`, `*.py[cod]`, `.venv/` |
| `code_hash` has one caller in `src/` | `grep -rn "code_hash(" src/publishable/*.py` | `cli.command_run` and the definition; nothing else |
| `hashed_files` reads no git and `_SKIP_*` is a fixed set | `hashes.py`, read in full | confirmed |
| `HASHED_TREES` has two readers | grep | `hashes.hashed_files`, `provenance.git_provenance` |
| 13 `code_hash(` call sites in `tests/test_hashes.py`, none with a repository | `grep -c "code_hash(" tests/test_hashes.py` → 13; `grep -c "git init\|subprocess" tests/test_hashes.py` → 0 | confirmed |
| Two of those tests use the empty digest as a **negative control** | read: `test_code_hash_skip_list_matches_relative_path_not_absolute`, `test_code_hash_handles_a_dot_git_intermediate_path_component` | both call `code_hash(tmp_path / "nonexistent_empty_repo")` |
| `test_code_hash_ignores_pycache` and `test_code_hash_still_skips_a_genuine_pycache_dir_inside_the_tree` are byte-identical in body | read both | confirmed — a duplicated pin |
| `sha256` of the empty string is the zero-file digest | `python -c` | `e3b0c442…b855`, equal to `code_hash` of a directory that does not exist |
| `parameters_hash` normalizes key order already | `sort_keys=True` is recursive; the scoping reversed three levels and got one digest | confirmed by reading `_canonical` |
| Core-schema defaults exist nowhere as data | `materialize.materialize_config` builds literal text lines; only `_parameters_block` reads `parameter_spec` | confirmed |
| An omitted `parameter_spec` default validates clean and kills the step | scoping's run; the code path re-read here: `_check_parameters` reports only `E-PARAM-MISSING` for a **defaultless** parameter, and `Node.__getattr__` raises `E-STEP-PARAM-UNKNOWN` for any absent path | confirmed |
| The reader for "unset and defaulted" already exists, gated | `validate._check_versions` computes `unset` and names it inside `W-TEMPLATE-VERSION`, only under a version mismatch | confirmed |
| `run.yaml`'s `schema_version` cannot carry a marker | scoping edited a record to `1.1` → `E-UPSTREAM-RECORD-VERSION`; `lineage.read_record_file` re-read here | confirmed |
| `diff` recomputes `parameters_hash` for a **config** operand only | `diff.py::_parameters_hash_for` | confirmed; a run side reads the recorded string |
| Only one hash of the eleven the record carries is `code_hash`'s | scoping's § 5 table, re-checked against `grep -rn '"code_hash"' src/publishable/*.py` | five carriers, enumerated in § The value change |

### What this pass measured that the scoping did not

Seven things, each of which changed a decision.

1. **`git ls-files` quotes a non-ASCII or quote-bearing path** with C-style octal escapes
   (`"src/pkg/na\303\257ve step.py"`) unless `-z` is passed. A naive implementation of the
   scoping's recommended route would fail to match such a file against `hashed_files`' own
   relative path and **silently drop a real source file from the hash**.
2. **`git ls-files -co --exclude-standard` lists a tracked file that has been deleted from the
   working tree** — measured. Driving the hash from git's list would then read a file that does not
   exist.
3. **It also lists a tracked file inside `__pycache__`** — measured. Driving from git's list would
   hash it, falsifying § Templates' *"unconditionally"*.
4. **It silently drops the contents of a git submodule under `src/`.** Measured on a host repo with
   `src/vendor` as a submodule: git lists the gitlink `src/vendor`, `rglob` finds
   `src/vendor/lib/z.py`, and the intersection drops the file. Hashed today, unhashed after — with
   no diagnostic.
5. **`git check-ignore -z --stdin` answers the direct question and costs the same.** Over this
   repo's 53 hashed paths: `check-ignore` **12.1 ms**, `ls-files -co --exclude-standard`
   **12.2 ms** (five runs each). It returns **0** when some listed path is ignored, **1** when none
   is, and **128** with a legible `fatal:` naming the submodule when a path is inside one. That
   tri-state is the ground for Decision 2 and Decision 6.
6. **`check-ignore` is right about a tracked file and `check-ignore --no-index` is wrong about it.**
   For a committed `src/pkg/tracked.pyd` against a `*.py[cod]` pattern: plain `check-ignore` reports
   **no match** (git does not ignore a tracked file), `--no-index` reports
   `.gitignore:3:*.py[cod]`. The flag that looks like a purity improvement is the one that breaks
   the rule.
7. **A tracked non-ASCII filename joins correctly on this platform, and the check is set equality.**
   `src/pkg/naïve.py`, `src/pkg/ünïcode dir/mod.py` and `src/pkg/emoji_🙂.py`, all committed:
   git's `-z` output decoded with `os.fsdecode` equals `hashed_files`' relative-path set exactly
   (`core.precomposeunicode = true`, APFS). The claim is pinned as **set equality**, not as "the
   hash moved", because a hash comparison passes under a mutual drop.

---

## Decisions

### 1. `code_hash` honours `.gitignore`; § How the three are computed wins and § Templates' sentence narrows to the dirty gate

**The question.** § How the three are computed says `code_hash` is *"taken from the working tree
and skipping whatever `.gitignore` skips."* § Templates says the `__pycache__`/`.pyc` skip is
unconditional *"— it reads the working tree rather than git, so no ignore file could have done that
for it"*, and later that a hand-assembled repo's *"`code_hash` is unchanged, that being the
mechanism an ignore file has no bearing on."* Read generally, the second contradicts the first.
Which is normative?

**The answer.** § How the three are computed. `code_hash` becomes `.gitignore`-aware, and § Templates'
clause narrows to the **dirty gate**, which is the question that sentence is actually about.

**Grounds, measured.** The defect is not the hash alone; it is that **the dirty gate consults git and
the hash does not**, so one mechanism says *nothing changed* and the other says *the code moved*.
Two runs at the same commit, both `code_dirty: false`, differing only by a git-ignored `src/mix/.env`,
produce `code_hash DIFFERS` at `diff` and a bundled `W-STUDY-CODE-HASH-MISMATCH` whose § Warnings row
names three candidate causes — a dirty tree, an uncommitted `templates/**` edit, another experiment's
package moving inside the trees — and **none of them is this one**. Three of the four ignore patterns
`publishable new` itself writes are unhonoured, so **the scaffold ships the disagreement**; the
unhonoured three include the credentials line, whose contents therefore move a published identity
claim that cannot be reproduced from the commit. § How the three are computed states the rule in one
sentence; § Templates states it in a clause of a sentence about scaffolding, and that clause is true
of the mechanism it was written about.

**Alternatives rejected.** *Ratify the code and edit § How the three are computed instead* — rejected:
it would make the hash and the gate disagree **by specification**, and the sentence that would have to
be written is *"a file your `.gitignore` excludes still moves your `code_hash`"*, which nothing in
`design-principles.md` argues for. *Honour `.gitignore` and drop the unconditional `__pycache__` skip*
— rejected by Decision 3.

**Cost if wrong.** Every existing `code_hash` for a repo carrying an ignored file under the two trees
becomes unreproducible from the new build — see § The value change, which is where that cost is paid
and disclosed. If the ruling is wrong, the symptom is a user who *wants* an ignored artefact inside the
identity claim (a generated `src/pkg/_version.py` that is git-ignored, say) and finds it silently no
longer covered. The route for them is the direct one and it is the same route git offers: commit the
file, or stop ignoring it.

### 2. The predicate asks git *"is this path ignored?"*, not *"which paths do you list?"* — a measured disagreement with the scoping

**The question.** Which git command answers *what does `.gitignore` skip under the two trees*?

**The answer.** `git check-ignore -z --stdin`, fed the relative paths `hashed_files` already found,
run with `cwd=repo_root`. **Not** `git ls-files -co --exclude-standard -- src templates`, which the
scoping recommended and measured a route for.

**Grounds, measured here.** `ls-files` answers *which paths does git list*, which is a **correlate** of
*which paths does git ignore* — the substitution this repo names as answering a question with a proxy —
and the three places the correlation breaks were all measured (§ What this pass measured, items 2, 3,
4): a tracked file **deleted from the working tree** is listed and cannot be read; a tracked file
**inside `__pycache__`** is listed and must not be hashed; a **submodule's** contents are not listed and
would be dropped with no diagnostic. Reconstructing the right answer from `ls-files` means an
intersection plus two exceptions, and the submodule case survives all of them silently.
`check-ignore` answers the question the normative sentence asks, in the sentence's own words, and it
costs the same: **12.1 ms against 12.2 ms** over this repo's 53 paths. It is also correct about the
case the intersection route gets wrong by default: a **tracked** file matching an ignore pattern is
reported as not ignored, so it stays hashed — and the plausible "improvement" `--no-index` inverts
exactly that (§ What this pass measured, item 6), which is why the design forbids the flag by name and
Mutation 4 pins it.

**Two mechanics that are part of the decision, not details.** The call passes **`-z` on both ends** and
decodes each entry with **`os.fsdecode`** — because git quotes a non-ASCII path without `-z` (item 1),
and because `text=True` decodes with the locale's encoding rather than the filesystem's. The join key
is the **repo-relative posix string `hashed_files` already produced**, so there is exactly one spelling
of a path in this slice, and the pin asserts **set equality** between git's answer and `hashed_files`'
own paths on a tracked-non-ASCII fixture (item 7).

**Alternatives rejected.** *`ls-files -co --exclude-standard`, intersected* — above. *A pure-Python
`.gitignore` parser inside `hashes.py`* — rejected: it is a second implementation of a rule git owns,
it would disagree with the dirty gate the first time a pattern is subtle, and the filing this slice
closes already names *"passing an `is_ignored` predicate in from the caller, which already shells to
git"* as the resolution. *`--no-index`* — rejected, measured wrong (item 6).

**Cost if wrong.** If `check-ignore` proves slow on a very large tree, the cost is one subprocess per
`run`, once, measured at 12 ms for 53 paths; the fallback is `ls-files` plus the three exceptions,
which this design has already enumerated so a successor does not re-derive them.

### 3. The fixed skip set stays, is applied first, and the whole rule is enumerated once

**The question.** Does the `__pycache__`/`.pyc`/`.pyo`/tool-cache skip survive an ignore-aware hash?

**The answer.** Yes, unconditionally, and it is applied **before** the ignore question is asked, so
git is never consulted about a path that is skipped anyway.

**Grounds, measured.** § Templates' *"unconditionally"* is wanted for a repo whose `.gitignore` omits
those patterns, and the measurement that forces it: a **tracked** `src/pkg/__pycache__/keep.py` is
reported by git as **not ignored** (it is tracked), so an ignore-only rule would hash it. Applying the
fixed set first keeps that file out and keeps the sentence true — verified by literal: the digest
before and after adding it is `6ddb8634…` both ways.

**The rule has four cases, and a four-case rule invites a two-case sentence at every site that mentions
it** — H5b shipped one five times in five files. So it is enumerated **once**, as a table in
`reference.md` § How the three are computed, and every other site links to that anchor rather than
restating it: § Templates, `hashes.py`'s module docstring, the ignore-predicate's docstring in
`provenance.py`, the § Warnings row for `W-STUDY-CODE-HASH-MISMATCH`, and the `spec-defects.md` strike.

| A file under `src/**` or `templates/**` is | Hashed? |
|---|---|
| in the fixed skip set (`__pycache__`, `.git`, `.ruff_cache`, `.mypy_cache`, `.pytest_cache` as a path component; suffix `.pyc`/`.pyo`) | **no**, whatever git says — including when it is tracked |
| tracked | **yes**, even when it matches an ignore pattern |
| untracked and not ignored | **yes** |
| ignored | **no** |

**Cost if wrong.** A repo that deliberately tracks a `.pyc` gets a hash that ignores it. That is
today's behaviour, and § Templates already documents it.

### 4. `include` is a **required, batch** parameter of `hashed_files` and `code_hash`; `None` is an explicit claim

**The question.** How does the ignore answer reach `hashes.py` without making it shell to git?

**The answer.** `hashed_files(repo_root, include)` and `code_hash(repo_root, include)`, where
`include: Callable[[list[str]], set[str]] | None` is **positional and required**. It is handed **every
candidate path that survived the fixed skip set**, as repo-relative posix strings, and returns the
subset to keep. `None` means *hash every file the trees hold*.

**It is a batch filter and not a per-path predicate, and that is a measured decision rather than a
style choice.** `git check-ignore` costs **12.1 ms for 53 paths in one call**; asking it per path would
cost 53 subprocesses — roughly 640 ms — and Decision 2's *"costs the same"* ground would stop holding.
The alternative to batching is a memoizing per-path closure, which would have to do **its own walk** to
build its cache and would thereby re-introduce the second path spelling Decision 2 exists to eliminate.
Batching also makes Decision 3's *"git is never consulted about a path that is skipped anyway"*
literally true: the filter is called **after** the skip set has run, over exactly the survivors.

**Grounds, measured.** 13 `code_hash(` call sites in `tests/test_hashes.py` run against a bare
`tmp_path` with **no repository** — so the predicate must be injectable, which is the only half of the
spine's *"`hashes.py` is pure"* rule that survives contact with the code (`hashes.py` already rglobs,
reads bytes, and carries `_SKIP_DIRS`, which is filesystem policy; the scoping measured that the purity
rule is **not in `design-principles.md` at all**). Making the parameter **required rather than
defaulted** is the anti-fail-open choice: `code_hash` has exactly **one** production caller, so
requiring it costs one line there and 13 mechanical edits in the pins — **14 call sites in all**, which
task 3 names individually — and it converts *a future caller forgets and silently gets the un-ignored
hash* into a `mypy` error. Both of H7a's fail-opens were
predicates that answered permissively when nobody had told them otherwise.

**Alternatives rejected.** *A default of `None`* — rejected above. *A per-path
`Callable[[str], bool]`* — rejected above, measured. *Passing a bare `set[str]` of allowed paths
instead of a callable* — rejected: the caller would have to enumerate the candidates **before**
`hashed_files` has walked, which means walking twice or exporting the walk, and the whole point of
handing the callable the survivors is that the walk happens once, in one place, producing one spelling.
*Shelling to git inside `hashes.py`* — rejected: it breaks the 13 repo-less pins, which are the property
the purity rule was protecting.

**Cost if wrong.** The 14 call sites gain a literal `None`. If a reader mistakes `None` for "no files",
the docstring says the opposite in one sentence: *"`None` is not a default; it is the explicit claim
`hash every file these trees hold`, which only a caller without a repository can honestly make."*

### 5. The predicate is built in `provenance.py` and bound at the moment of hashing

**The question.** Who constructs it, and when?

**The answer.** `provenance.unignored_under_hashed_trees(repo_root, candidates: list[str]) -> set[str]`
— the batch filter Decision 4 specifies, matching its signature exactly — passed as `include` at
`cli.command_run`'s **single** `code_hash` call site (phase 5), not at the dirty gate (phase 3).

**Grounds, measured.** `provenance.py` already shells to git and **already imports `HASHED_TREES`** —
it is the sibling that got it right, and the containment it sits in is the point, not only the calls it
makes. The timing half is the H7a corollary: **state read at the wrong moment is a proxy.** Between
phase 3 and phase 5 the command resolves units, which runs a plugin resolver — user code that can
create or remove files under `src/`. An ignore answer captured at phase 3 and used at phase 5 answers
*what did git see before user code ran*, which is not the question the hash asks.

**Alternatives rejected.** *Compute once at phase 3 and reuse* — rejected above. *A module-level cache*
— rejected for the same reason.

**Cost if wrong.** A resolver's quota may already be spent when Decision 7's refusal fires. That cost is
named again in Decision 7 and is the reason that refusal has exactly one site.

### 6. A path git cannot answer for **refuses**: `E-CODE-FILE-LIST`

**The question.** `check-ignore` returns 0 (some path ignored), 1 (none ignored), or something else.
What does core do with the third case?

**The answer.** Refuse, with a new code `E-CODE-FILE-LIST`, carrying git's own stderr verbatim. The
returncode is **checked**; the answer is never inferred from whether stdout was empty.

**Grounds, measured.** The reachable instance is a **git submodule under the hashed trees**: on a host
repo with `src/vendor` as a submodule, `check-ignore` exits **128** with
`fatal: Pathspec 'src/vendor/lib/z.py' is in submodule 'src/vendor'`. Inferring "nothing is ignored"
from empty stdout would be the same substitution `provenance._git` already makes with
`check=False`/`strip()` — and `provenance.py`'s own `E-GIT-NO-COMMIT` comment is the precedent for
refusing at the one call site where an empty answer has no honest reading. Refusing is also
**substantively right** rather than merely safe: a submodule's files are code another repository
supplies with its own history, and `run.yaml` records no gitlink, so hashing them is a claim the record
cannot support — which is the same argument § Three hashes already makes for pinning a dependency's
code in `uv.lock` instead. Today those files are hashed silently; the intersection route would drop
them silently; this refuses loudly.

**One implementation route is forbidden by name, because it is the likely error.** The helper must
**not** call `provenance._git`. That helper runs `check=False` and returns `result.stdout.strip()`,
discarding the returncode — which is precisely the inference this decision forbids, and it would turn
rc 128 into an empty string indistinguishable from *nothing is ignored*. `provenance.py` is the right
place for the helper to **sit**; `_git` is the wrong thing for it to **call**. *A recipe is its calls
plus where they sit*, and here the containment is right and one call is wrong. Mutation 6 targets this
seam by name.

**Alternatives rejected.** *Fall back to today's un-ignored behaviour with a warning* — rejected: the
hash would then mean one of two different things depending on whether a subprocess succeeded, and a
warning is not something a `run.yaml` reader ever sees. *Treat rc 128 as "nothing ignored"* — rejected,
that is the proxy. *Special-case submodules and hash them anyway* — rejected: core would then have to
decide what a gitlink means for provenance, which is a question no charter owns.

**Cost if wrong.** A repo vendoring code as a submodule under `src/**` cannot `run` until it moves the
submodule out of the two trees or installs it as a dependency. That is a real cost, it is loud, and the
diagnostic names the submodule git named. If it proves too strict, the successor's route is the
fallback rejected above — recorded here so it is not re-derived.

### 7. Ruling D — zero hashed files refuses, at the caller, `E-CODE-EMPTY`, **one** emit site

**The question.** A repo with an empty `src/`, no `templates/`, and an importable entrypoint produces a
**completed run at exit 0** whose `code_hash` is `sha256:e3b0c442…` — the digest of nothing — carried
into the `run_id`, with no diagnostic. What does core do?

**The answer.** `command_run` refuses with `E-CODE-EMPTY` when `hashed_files` returns no pair, before
`allocate_run_dir` and before any execution is paid for. The guard is at the **caller**, and
`hashes.code_hash` still returns the empty digest for an empty tree.

**Grounds, measured.** Two tests in `tests/test_hashes.py` use `code_hash(tmp_path /
"nonexistent_empty_repo")` as a **negative control**, so a refusal inside `hashes.py` would break the
two pins that prove the skip list is matched against relative parts. The scoping's own reasoning —
*"guarding against it is a validation-engine question, not something the pure hashing module should
decide"* — reaches the same place from the filing's side. And Decision 1 makes the case **more**
reachable, which is the strongest argument for shipping both in one slice: a repo whose entire `src/`
is untracked and matched by an ignore pattern has a **clean** dirty gate (`git status --porcelain --
src templates` prints nothing, measured) and, after Decision 1, **zero** hashed files — so a run that
today records a real digest would, without this refusal, start recording the digest of nothing.

**One emit site, and the alternative is named because the choice costs something.** The site is
immediately before `allocate_run_dir`, where the file list the hash is computed over is the file list
in hand. Placing a second, earlier gate at phase 3 would save a resolver's quota in the empty-repo
case — but a mutation deleting the phase-5 site would then be **blind** unless a fixture makes the
trees empty *between* the two phases, which needs user code unlinking under `src/` during resolution.
**Two sites where one has a blind mutation and no replacement** is the shape this repo's § Errors work
exists to catch, so H6a ships **one** and states the cost: a config whose resolver spends quota pays it
before this refusal fires.

**Alternatives rejected.** *A warning* — rejected: a record whose code hash is the digest of nothing
proves nothing, and the run would still be published, cited, and bundled. *Refusing inside `hashes.py`*
— rejected, measured above. *A check at `validate`* — Decision 15.

**Cost if wrong.** A project that legitimately keeps all its code outside `src/**` and `templates/**`
cannot run. That project has no `code_hash` worth the name today either, and the refusal's message
says so and names the two trees.

### 8. Ruling C — no marker in `run.yaml`; `uv.lock` is the carrier

**The question.** H6a changes what `code_hash` computes for an unchanged tree. Should the record mark
which definition produced its figure?

**The answer.** No. Nothing is minted, and `run.yaml`'s `schema_version` is **not** bumped.

**Grounds, measured.** `run_record.SCHEMA_VERSION` is `"1.0"` and `lineage.read_record_file`
**refuses** any other value — the scoping edited one record to `1.1` and got `E-UPSTREAM-RECORD-VERSION`.
Bumping it would make `io.reuse_from` refuse **every record already on disk**, which is strictly worse
than an unmarked value change. The carrier that already exists is `uv.lock`: core's own version is
pinned there — which is precisely **why** `code_hash` covers only the repo's two trees — and
`provenance.environment.uv_lock_hash` is written by `cli.py` and read by `diff.py`'s `uv.lock` row.
This is the same ruling H5b shipped under, on the same carrier, eleven days after H8b's Decision 7
established that an additive change may pass quietly and a value change may not.

**Alternatives rejected.** *A `provenance.hash_definition` key* — rejected: a second source of truth for
something `uv.lock` answers, the same argument that forbids a separate defaults file, and a key that
would have to be maintained by every future slice that touches a hash. *A fourth hash* — same. *A
`diff` row of its own* — same, and `diff` reads records rather than knowing about builds.

**The disclosure obligation is therefore heavier, not lighter**, and § The value change discharges it.
One consequence belongs here rather than there because it is this ruling's cost specifically: a
post-H6a run that consumes a pre-H6a upstream through `io.reuse_from` publishes **one record carrying
two hash definitions** — its own `code_hash` under the new rule and `provenance.upstream[].code_hash`
copied verbatim from the old one — **with nothing marking which is which**. That is the sharpest form
of this ruling's cost, and it is stated in the ledger and in `CLAUDE.md`'s slice entry rather than
mitigated.

**Cost if wrong.** A reader who compares two runs across the boundary sees `uv.lock DIFFERS` beside
`code_hash DIFFERS` and cannot tell whether the code moved or the definition did. The mitigation is the
disclosure, not a key.

### 9. Ruling B — `parameters_hash` is **not** normalized, and the charter's second clause is rejected

**The question.** The charter says *"`parameters_hash` normalization against `parameter_spec`."*
Does H6a build it?

**The answer.** No. `parameters_hash` computes exactly what it computes today. § How the three are
computed's sentence *"Values are normalized to what `init` would have materialized before hashing"* is
**deleted**, replaced by the rule the code implements and the reason it is right, and the false
justification that follows it is deleted rather than rewritten.

**Grounds, re-checked here.** Three, and each is independently sufficient.

1. **`parameter_spec` cannot reach the gap.** Of the nine omissions the scoping measured moving the
   hash, **eight are core-schema keys** — `data.units.cluster_by`, `.holdout`, `.measurements`,
   `sweep`, `statistics`, `hypotheses`, `plugin` — and core-schema defaults exist **nowhere as data**:
   `materialize.materialize_config` emits them as literal text lines, and only the `parameters` block
   is generated from `parameter_spec` via `_parameters_block` (read here, confirmed). Normalizing
   "against `parameter_spec`" therefore reaches **one** of nine.
2. **Reaching the other eight needs a structure `CLAUDE.md` § Invariants forbids by name** —
   *"there is deliberately no separate defaults file"* — and `reference.md` § There is no separate
   defaults file states it normatively.
3. **Normalizing the `parameters` half would be actively wrong.** An omitted `parameter_spec` default
   validates clean and then the step that reads it dies with `E-STEP-PARAM-UNKNOWN`, every execution
   `failed`, `status: failed`. Core does **not** materialize defaults into `cfg`. So normalizing would
   hand **one identity claim to a config that runs and a config that cannot** — the opposite of what
   an identity claim is for. Two configs differing by an omitted default **are** different
   declarations: *a config read against a different spec is a different declaration* is § Three
   hashes' own sentence about the four identifying fields, and it applies here unchanged.

**And the document's stated reason for the rule is false against the shipped command**, which is why
the sentence is deleted rather than softened. The document argues *"`diff` would report a difference
with nothing to print."* `diff` prints:

```
parameters_hash    DIFFERS
  data.units.cluster_by  null → (absent)
```

— exactly the right thing. **Prefer deleting a claim to rewriting it**: the false clause goes, and what
replaces it is the subtractive rule already stated two paragraphs later plus one sentence naming the
consequence honestly (a hand-trimmed config and the file `init` wrote are two declarations, and `diff`
shows which key differs).

**Alternatives rejected.** *Normalize the `parameters` block only* — rejected by ground 3, and it would
make the hash's coverage rule depend on which block a key sits in, which nothing else in § Three hashes
does. *Build a core-schema defaults table and argue against the invariant* — rejected: the argument
would have to be made against `design-principles.md`, and the thing it buys is that two configs which
behave differently hash the same. *Materialize defaults into `cfg` at load* — rejected: it makes the
config file no longer the whole truth, against § Everything is in the file, and a reader of the
embedded config in `run.yaml` would no longer see the values the run used.

**Cost if wrong.** A user who hand-trims a config to remove a `null` line gets a different
`parameters_hash` from the `init`-written original and, if a run is in flight, `resume` refuses. That
is the documented behaviour of every other key in the hash, `diff` names the key, and the remedy is
one line of YAML.

### 10. What H6a fixes instead: `W-PARAM-UNSET`, for the `parameters` block **only**

**The question.** Ruling B leaves the misleading half — an omission that validates clean and then kills
every execution. Is closing it H6a's, or a filing?

**The answer.** **Built here, for the `parameters` block.** One new warning, `W-PARAM-UNSET`, reported
by `validate._check_parameters` for every `parameter_spec` path that carries a default and that this
config does not set — **one diagnostic naming all of them**, on `W-TEMPLATE-VERSION`'s own message
shape, not one per parameter. The **core-schema** half is filed, not built, and § Ruling B's boundary
says so in the design rather than leaving the word *"fixed"* to overclaim.

**Grounds for building the `parameters` half.** The check is cheap and local: the reader **already
exists** — `_check_versions` computes exactly this list — so the work is extracting one comprehension
into a shared helper and calling it from a second site, which is the `covered_config` precedent for how
two sites do not drift. And it is the one place core can state the fact without reading user Python:
the template declares the parameter, `init` would have written it, this config does not hold it, and
`cfg.parameters.<path>` will raise.

**Grounds for it being a warning and not an error, measured.** Of **40** parameter blocks a regex sweep
finds across `tests/**` (`"parameters": {…}` dict literals and `parameters:` YAML blocks; the sweep
under-counts nested literals, so 40 is a floor), **exactly one** names all four of `generic`'s
defaulted parameters. **39 of 40 omit at least one**. What that count measures is exactly *parameter blocks written in the
suite*, not *configs that reach `_check_parameters`* — many are dict literals in unit tests that never
go through `validate` — so the honest form is: **omitting a defaulted parameter is what almost every
config in this repo does**, and the end-to-end configs among them run to completion. A refusal would
therefore refuse the ordinary shape of a hand-written config — and
core cannot know whether a step reads the parameter, because reading the body of user Python is the
line it does not cross. A freshly `init`-ed config sets all four, so the warning does **not** fire for a
scaffolded project: it fires exactly on the hand-trimmed configs the fact is about.

**Grounds for the boundary — the part that would otherwise be an overclaim.** `W-PARAM-UNSET` covers
`parameter_spec` parameters. An omitted **core-schema** key is the same symptom through the same code
(`Node.__getattr__` → `E-STEP-PARAM-UNKNOWN`) and is **not** covered. It is filed rather than built for
a reason that is not "no time": core itself reads core-schema keys defensively — `(config.get("sweep")
or {})`, `(config.get("data") or {}).get("units")` — so an omitted core-schema key harms nothing core
does; the only casualty is a **step** reaching for it through `cfg`, and knowing whether a step does
that means reading its body. Closing it would need either the forbidden defaults structure or the
greenfield line crossed. **Owner: unassigned, with the reason** — no remaining slice (H6b, H9, H3c-3's
remaining 14) has core's schema envelope as its surface.

**Alternatives rejected.** *An error* — measured above. *One diagnostic per parameter* — rejected: on
`generic` a bare config would print four, and `W-TEMPLATE-VERSION` already established the enumerating
shape. *Nothing at all, filed* — rejected: the reader exists, the site exists, and a filing whose fix is
three lines is how a live defect becomes a permanent one.

**Cost if wrong.** Every test config that omits a defaulted parameter gains a warning line in
`validate`'s render. Measured blast radius: 5 tests assert on the `✓ config valid` string and 4 on the
`N problems (…)` summary line; **the plan must run the full suite once with the warning wired and
report the count**, because a warning that changes many renders is a pin-weakening pressure and the
count is what tells a reviewer whether any assertion was loosened rather than updated.

### 11. `W-TEMPLATE-VERSION` keeps its unset-and-defaulted clause; the comprehension is shared and the message is pinned

**The question.** With `W-PARAM-UNSET` reporting the same list unconditionally,
`W-TEMPLATE-VERSION`'s detail clause becomes redundant. Delete it?

**The answer.** No. The clause stays, its § Warnings row stays, and the redundancy is recorded as
deliberate. What changes is that both sites compute the list through **one** helper.

**Grounds.** The clause is **true**, so *prefer deleting a claim to rewriting it* does not license
removing it — that rule is about false claims. Deleting it would make H6a change a **second** shipped
message in a slice whose declared value change is `code_hash`, and would edit a documented § Warnings
row for tidiness rather than correctness. Both warnings render in one `Collector` output, so a reader
who sees the version mismatch sees the list attached to it and sees it again standing alone; that is
duplication, not contradiction. The helper extraction is non-behavioural and is the answer to the two
sites drifting.

**Cost if wrong.** Two warnings name the same parameters on a version-mismatched config. If that proves
noisy, deleting the clause later is a one-line change against a row that will then be redundant rather
than wrong.

### 12. Ruling E — `diff`'s `uv.lock` detail lines stay H9's, and `diff <config> <run>`'s recomputation is untouched

**The question.** H5b filed *"`diff`'s `uv.lock` row prints two digests and never names the package
whose pin moved"* against H9. Does H6a fold it in? And `diff.py::_parameters_hash_for` recomputes
`parameters_hash` for a config operand — does H6a move verdicts about runs already on disk?

**The answer.** **No** to both, and the second is a consequence of Decision 9 rather than a separate
choice.

**Grounds.** On H4b-2's precedent — a slice that declines a neighbouring gap says so in writing rather
than absorbing it — the `uv.lock` routing survives: `diff`'s `parameters_hash` row prints per-key detail
because `diff` reads two embedded **configs**, while `uv.lock`'s row has two digests because a run
archives the lockfile and the record carries only its hash. Producing a per-package delta means reading
two archived `environment/uv.lock` files and ruling on what a moved pin means, which is the question
H9's charter is defined by. And because **Decision 9 changes nothing about what `parameters_hash`
computes**, `diff <config> <run>` returns exactly the verdicts it returns today for every run already on
disk. Had Ruling B gone the other way, that recomputation would have moved published verdicts on the
day it landed — which is the sharpest argument the scoping made for ruling it narrowly, and it is
recorded here as an argument that was used rather than one that became moot.

**`code_hash`'s row in `diff` is a different matter and is not silent**: a run-vs-run comparison reads
two **recorded** strings, so a pre-H6a run and a post-H6a run of identical code can print
`code_hash DIFFERS`. That is § The value change's business, and no `diff` code changes.

**Cost if wrong.** A user diffing across the boundary reads `uv.lock DIFFERS` without knowing which
package moved. Filed against H9, unchanged.

### 13. The hash and the dirty gate share **one pathspec**, not one file list

**The question.** The scoping says the hash and the gate *"would share one file list."* Do they?

**The answer.** No, and saying they do would be a false claim in a comment. They share
`HASHED_TREES` — one constant, one pathspec — and ask git **two different questions**:
`git status --porcelain -- src templates` (has anything moved?) and `git check-ignore` (is this path
ignored?). `status` never lists a clean tracked file, so it cannot produce the hash's file list.

**Grounds, measured.** The agreement that matters is behavioural and is pinned rather than asserted:
after Decision 1, an **ignored-but-present** file under the two trees is **neither dirty nor hashed**,
where today it is not dirty and *is* hashed. The three other states agree too — untracked-not-ignored is
dirty and hashed, tracked-modified is dirty and hashed, tracked-clean is not dirty and hashed — and one
test asserts both halves of the ignored case in one place so that a future change cannot move one
without the other.

**Cost if wrong.** None known; this decision exists to stop a true-sounding sentence about one file list
from being written into a docstring where a mutation would never reach it.

### 14. § Executability does not move, and the four rows are repeated character for character

**The question.** Does a hash-definition change move any config's executability in
[the feasibility analysis](../../feasibility-llm-growth-studies.md)?

**The answer.** No. The entry repeats the four-row table unchanged and mints no fifth number.

**Grounds, derived rather than assumed.** Row 1 counts configs **validating with zero errors**;
`W-PARAM-UNSET` is a warning, which changes no exit code and no error count, and the two new **errors**
are raised by `command_run`, not by `validate`. Rows 2 and 3 name `io.reuse_from`'s plugin-side call and
the `report_by`-under-`resample` gap, neither of which this slice touches. Row 4 counts configs free of
every core-side dependency the analysis can name; `code_hash` is computed for every run regardless of
config, so no config gains or loses a dependency. **Following H5b's own dated correction** — whose
finding was a miscounted *newly-firing* thing rather than a moved row — the entry also states in prose
whether `W-PARAM-UNSET` newly fires on those configs: **unknowable, with the reason**, since it depends
on the `growth_screen` template's `parameter_spec` and neither `growth_screen` nor `publishable-llm` is
installable in any build.

**Cost if wrong.** If a config did move, the entry would carry a fifth wrong number made the way both
previous ones were made — by carrying a phrase forward without re-deriving it. The derivation above is
what a reviewer checks.

### 15. H6a adds no tree check to `validate`

**The question.** `validate` says nothing about a dirty tree, an empty tree, or an ignored file. Should
H6a's two new errors also fire there?

**The answer.** No. Both are raised by `command_run`.

**Grounds.** `validate` walks no tree and shells to no git today (`grep -rn "dirty"
src/publishable/validate.py` → zero hits), and `E-CODE-DIRTY` — the existing member of this family — is
a `run`-only gate for that reason. § Templates' claim that a hand-assembled repo *"goes dirty at
`validate`"* describes behaviour that does not exist, and **deciding whether `validate` gains a
tree-state warning is H6b's task 18** by the scoping's split. Adding one here would pre-empt a ruling
this slice does not own and would mint a `W-` seat against a section H6b is rewriting.

**Cost if wrong.** A user learns of an empty or unhashable tree at `run` rather than at `validate`,
after `validate` said the config is fine — which is exactly what `E-CODE-DIRTY` already does, so the
behaviour is consistent rather than novel.

---

## The value change, said loudly

**H6a is not additive.** One published identity claim moves for an unchanged tree at an unchanged
commit, and this section is the argument made in the open, on H5b's and H8b Decision 7's precedent.

**Exactly one hash moves: `code_hash`.** The other ten figures the record carries are unmoved, and the
list is enumerated rather than counted so a reviewer can check it: `parameters_hash`,
`input_manifest_hash`, the per-file `sha256`s in `manifest/input.json`, `uv_lock_hash`, `units_hash`,
`allocation_hash`, `apparatus.hash`, `design_digest`, the copied upstream `parameters_hash`, and every
derived seed. **Ruling B is what keeps that list at ten**; had normalization shipped,
`parameters_hash` would move too and `diff <config> <run>` would return different verdicts about runs
already on disk.

**Every record field carrying the moved hash, enumerated.**

| Field | Where |
|---|---|
| `code_hash` | `run.yaml`, top level (`run_record.py`) |
| `run_id` | `run.yaml`, and the run **directory's name** — `allocate_run_dir` uses `short(code_hash)`, the first 7 hex characters |
| `provenance.upstream[].code_hash` | `lineage.py`, **copied** from an upstream record — so one record can carry two definitions (Decision 8) |
| the bundled copy of each of the above | `study add` copies `run.yaml` into `runs/<name>/` verbatim |
| the `latest` pointer's target | `point_latest`, which names the run directory |

**When it moves, with computed literals.** One probe project: `.gitignore` holding the scaffold's four
patterns, `src/pkg/step.py` = `a = 1\n`, `templates/t.py` = `b = 2\n`, committed. Every digest below was
computed by running the shipped `code_hash` for the "today" column and the Decision 2 predicate for the
"after" column.

| Tree state | `code_hash` today | `code_hash` after |
|---|---|---|
| clean | `71bf339c…` | **`71bf339c…` — unmoved** |
| plus untracked `src/pkg/.env` (git-ignored) | `ebc5ee53…` | **`71bf339c…`** |
| plus untracked `src/pkg/loose.pyd` (git-ignored) | `6ddb8634…` | **`71bf339c…`** |
| plus **tracked** `src/pkg/loose.pyd` | `6ddb8634…` | `6ddb8634…` — unmoved |
| plus tracked `src/pkg/__pycache__/keep.py` | `6ddb8634…` | `6ddb8634…` — unmoved |

The `run_id` suffix follows: `run_<stamp>_ebc5ee5` becomes `run_<stamp>_71bf339` for the same tree.

**A coincidence in that table that a fixture must not be built on.** The untracked `.pyd` row and the
tracked `.pyd` row have the **same** value in the *today* column (`6ddb8634…`), because the file's
content is the same and today's hash cannot tell tracked from untracked. **The discriminating literal is
the `after` column**, and a fixture asserting only the *today* value would pass under a mutation that
ignores tracked files too. Fixture D is built on the after value for exactly this reason.

**Three things newly stop.**

1. A repo with **no file to hash** stops running: `E-CODE-EMPTY`, exit 1, where today it completes at
   exit 0 with the empty digest in its `run_id`. Reachable two ways — an empty `src/` with the
   entrypoint importable from elsewhere (measured by the scoping through the console script), and, new
   with Decision 1, a repo whose entire `src/` is untracked and ignored, whose dirty gate is **clean**
   (measured: `git status --porcelain -- src templates` prints nothing).
2. A repo with a **submodule under the hashed trees** stops running: `E-CODE-FILE-LIST`, carrying
   git's `fatal: Pathspec … is in submodule …`. Today its files are hashed; the rejected intersection
   route would have dropped them silently.
3. A hand-trimmed config newly **warns**: `W-PARAM-UNSET`. It does not stop anything, and it is listed
   here because *name what actually stops* covers a warning a shipped run newly earns.

**Nothing is retired.** Two errors and one warning are minted; no code is removed.

**Cost if the ruling is wrong.** Two runs of the same config over the same data at the same commit, on
either side of this slice, publish **different `code_hash` values and different `run_id`s** whenever the
repo carries an ignored file under the two trees — which the scaffold's own `.gitignore` makes the
common case, not the exotic one. `diff` prints `code_hash DIFFERS` for identical code.
`report study.yaml` over a bundle spanning the boundary prints `W-STUDY-CODE-HASH-MISMATCH`, whose
message names three candidate causes and will still name three, **none of which is a build boundary**.
The row is not widened, because widening it would document a transient. The carrier is `uv.lock`
(Decision 8), and the honest statement is the one H5b made: **the change is visible as a dependency
change and is not visible as a hash-definition change**, and a reader comparing two runs across the
upgrade must read the `uv.lock` row as covering it.

**Why ship it anyway.** Today the dirty gate says *nothing changed* and the hash says *the code moved*,
about the same tree, in the same run, and the warning that fires downstream cannot name the cause. A
`.env` under `src/` — the one file the scaffold promises is never committed — moves a published
identity claim, so the claim cannot be reproduced from the commit it names. **A published identity
claim that no commit can reproduce is not a behaviour worth preserving.**

---

## What this slice refuses to build, each with its route and owner

| Refused | Route and owner |
|---|---|
| `parameters_hash` normalization | **Refused by ruling**, Decision 9. The charter clause is rejected; § How the three are computed's sentence is deleted. No successor owns it: normalizing needs a defaults structure the invariants forbid |
| A `W-PARAM-UNSET` equivalent for **core-schema** omissions | **Filed. Owner: unassigned, with the reason** — no remaining slice (H6b, H9, H3c-3's remaining 14) has core's schema envelope as its surface, and closing it needs either the forbidden defaults structure or reading user Python (Decision 10) |
| A dirty-tree or empty-tree check at `validate` | **H6b, task 18** — § Templates' *"goes dirty at `validate`"* has no code, and whether `validate` gains a `W-` seat is that task's ruling (Decision 15) |
| `E-CODE-DIRTY`'s missing § Errors row, and `E-GIT-NO-REPO`/`E-GIT-NO-COMMIT`'s | **H6b, task 17**, which the scoping gates on the spine owner's ruling about widening this charter to the nine undocumented codes. H6a mints rows for **its own** two new codes and touches no other |
| `diff`'s `uv.lock` detail lines naming the moved package | **H9**, per H5b's filing, re-affirmed in writing (Decision 12) |
| `provenance.environment.os`/`.hostname`/`.hardware` | **H6b, tasks 13–16.** H6a writes no environment key |
| Hashing a submodule's contents, or deciding what a gitlink means for provenance | **Refused by ruling**, Decision 6. No charter owns it; the refusal names the submodule so a user can move it |
| A marker for the hash definition in `run.yaml` | **Refused by ruling**, Decision 8. `uv.lock` is the carrier |

---

## The fixtures

Every fixture is stated as a **claim**, and every literal in it was computed by a probe named in the
row. *A fixture is a claim too* — six in one slice once failed their own constraints, one asserting the
very value it existed to reject.

**Fixture A — the ordinary path does not move.** A committed project with the scaffold's `.gitignore`,
`src/pkg/step.py` = `a = 1\n` and `templates/t.py` = `b = 2\n`, holding **no ignored file**, hashes to
`sha256:71bf339cc9463f4c776c711f3d65ccf9b3bc1e18d383b78ae7d4e5170b526c2b` **before and after** this
slice. Computed by running the shipped `code_hash` and the Decision 2 predicate over the same tree; the
two printed the same digest. This is also guard-pin arm A.

**Fixture B — the credentials case.** The same project plus untracked `src/pkg/.env` containing
`OPENAI_API_KEY=sk-live-1\n`. Today `sha256:ebc5ee53…`; after, `sha256:71bf339c…` — **equal to
Fixture A's**, which is the claim: an ignored file leaves the hash where it would be without the file.
Both literals computed.

**Fixture C — `.venv/` and a loose `.pyd`, the other two unhonoured patterns.** Untracked
`src/.venv/lib/site.py` and untracked `src/pkg/loose.pyd`; both are reported ignored by
`git check-ignore -z --stdin` (measured: the call returned rc 0 listing exactly
`src/.venv/lib/site.py`, `src/pkg/.env`, `src/pkg/untracked.pyd`), and both leave the hash at
Fixture A's digest.

**Fixture D — a tracked file matching an ignore pattern is still hashed.** `src/pkg/loose.pyd`
committed with `git add -f`. `git check-ignore` reports **no match** for it (measured), and the digest
after is `sha256:6ddb8634b7f2a276afb4e8a7265c2879560ca5a9bfc09fd507d048de32c327b9` — **different from
Fixture A's**, which is the whole assertion. The *today* value is also `6ddb8634…`, identical to the
untracked-`.pyd` case, so **this fixture asserts the after value**; asserting the today value would pass
under a mutation that drops tracked files too.

**Fixture E — the fixed skip set survives, tracked or not.** On Fixture D's tree, add
`src/pkg/__pycache__/keep.py` = `k = 1\n` and `git add -f` it. git reports it as **not ignored**
(measured: it appears in `git ls-files`' output and `check-ignore` does not match it), and the digest
stays `sha256:6ddb8634…` — unmoved. This is the positive control for § Templates' *"unconditionally"*.

**Fixture F — a tracked non-ASCII filename joins by set equality.** `src/pkg/naïve.py`,
`src/pkg/ünïcode dir/mod.py` and `src/pkg/emoji_🙂.py`, all committed. The assertion is
`git_answer_set == {rel for rel, _ in hashed_files(repo)}` — **set equality**, not a hash comparison,
because a mutual drop leaves a hash comparison green. Measured true here with `-z` and `os.fsdecode`;
measured **false** without `-z`, where git returns `"src/pkg/na\303\257ve.py"` with the quotes as
literal characters. The docstring records the platform this was measured on
(`core.precomposeunicode = true`, APFS) and names NFC normalization as the fallback if a platform ever
diverges.

**Fixture G — the zero-file refusal, end to end.** A committed repo with an **empty** `src/`, no
`templates/`, and an entrypoint importable from a `PYTHONPATH` directory outside both trees. Today:
a completed run at exit 0 with `code_hash: sha256:e3b0c442…` and that digest in the `run_id` (measured
by the scoping through the console script). After: exit 1, `E-CODE-EMPTY`, **no run directory created** —
the last clause asserted by listing `output_dir`, because a refusal that leaves an empty run directory
behind is a different behaviour from one that does not.

**Fixture H — the zero-file case Decision 1 creates.** A committed repo whose `.gitignore` is `src/`
and whose `src/pkg/step.py` is untracked. Measured: `git status --porcelain -- src templates` prints
**nothing**, so the dirty gate passes; `git check-ignore` reports the file ignored; hashed files: zero.
The claim is that this repo runs today with a real digest and refuses after, with `E-CODE-EMPTY` — the
same code as Fixture G, from the same site, which is why the § Errors row names both situations.

**Fixture I — the submodule refusal.** A host repo with `src/pkg/step.py` and `src/vendor` added as a
submodule holding `lib/z.py`. Measured: `check-ignore` exits **128** with
`fatal: Pathspec 'src/vendor/lib/z.py' is in submodule 'src/vendor'`, and `ls-files -co
--exclude-standard` lists `src/pkg/step.py` and `src/vendor` while `hashed_files` finds
`src/pkg/step.py` and `src/vendor/lib/z.py`. The claim: `run` refuses with `E-CODE-FILE-LIST`, and the
message contains the substring `src/vendor`.

**Fixture J — hash and gate agree on the ignored-but-present file.** One test, two assertions on the
same tree: `git_provenance(...).code_dirty is False` **and** the file is absent from `hashed_files`'
output. Both halves in one place so neither can move alone (Decision 13).

**Fixture K — `W-PARAM-UNSET` fires, with its can-fail control.** Two configs against `generic`: one
omitting `analysis.drop_missing` and `analysis.confidence` (warning fires, naming **both** paths in one
diagnostic, exit 0, `has_errors` False), one setting all four (**no** warning — the control, which fails
if the check fires unconditionally). The second arm is what makes the first non-vacuous.

**Fixture M — one record carrying two hash definitions.** Decision 8's sharpest cost claim, pinned
rather than asserted. A `run.yaml` produced **before** this slice is checked in as a fixture artefact —
its `code_hash` computed under the old rule over a tree carrying a git-ignored `.env` — and a
post-change run consumes it through `io.reuse_from`. The claim: the new record's own `code_hash` is the
**new**-definition digest (`71bf339c…` for Fixture A's tree), `provenance.upstream[0].code_hash` is the
**old**-definition digest copied verbatim (`ebc5ee53…`), and **no key in the record distinguishes
them** — asserted by naming the record's top-level key set, so a future slice that adds a marker fails
this fixture and has to come back and read Decision 8. This is also the only fixture that exercises the
third carrier in § The value change's table.

**Fixture L — the two negative controls still hold.** `code_hash(tmp_path / "nonexistent_empty_repo",
None)` still returns `sha256:e3b0c442…`. This is not a new fixture; it is the two existing tests, and
the claim is that the guard did **not** migrate into `hashes.py`. Guard-pin arm E.

---

## The mutations

Each row names the assertion that catches it and **why the two branches can differ**, checked in
advance. *A mutation is a claim too.*

| # | Mutation | Caught by | The two branches differ because |
|---|---|---|---|
| 1 | Make `include` default to `None` instead of required | `uv run mypy` on a synthetic caller omitting it | typing, not runtime — **named partly blind**, see below |
| 2 | Drop the `include` filter from `hashed_files`' loop (compute it and ignore it) | Fixtures B, C — `ebc5ee53…` vs `71bf339c…` | measured: the two digests differ on that exact tree |
| 3 | Drop `-z` from the `check-ignore` call and split on newlines | Fixture F's **set equality** | measured: git returns `"src/pkg/na\303\257ve.py"` quoted, which is not the key `hashed_files` produces |
| 4 | Add `--no-index` to the `check-ignore` call | Fixture D's after value | measured: with the flag the tracked `.pyd` is reported ignored (`.gitignore:3:*.py[cod]`), so the digest becomes `71bf339c…` instead of `6ddb8634…` |
| 5 | Ask git before applying the fixed skip set, and drop the skip for a path git calls unignored | Fixture E | measured: the tracked file inside `__pycache__` is **not** ignored by git, so it would enter the hash and move the digest |
| 6 | Route the call through `provenance._git`, whose `check=False` + `strip()` infers the answer from stdout | Fixture I | measured: rc 128 comes with **empty stdout**, so the mutant reads "nothing ignored" and hashes the submodule's files; the guard refuses. Named as the concrete mutant because it is also the tempting implementation |
| 7 | Build the predicate at phase 3 and reuse it at phase 5 | a fixture whose **resolver writes `src/pkg/generated.py`** during resolution: the mutant's file list predates the write, so the new file is absent from `include` and drops out of the hash | the two digests differ by one file, computed by hashing the tree with and without it |
| 8 | Delete the `E-CODE-EMPTY` guard | Fixtures G and H — exit code and the absence of a run directory | measured today: exit 0 and a completed run |
| 9 | Move the `E-CODE-EMPTY` guard **after** `allocate_run_dir` | Fixture G's *no run directory* assertion | the mutant leaves a directory behind; the assertion lists `output_dir` |
| 10 | Delete the `W-PARAM-UNSET` call site | Fixture K's first arm | the warning names `analysis.drop_missing`; nothing else in that render does — checked against the render's other diagnostics rather than assumed |
| 11 | Make `W-PARAM-UNSET` fire for parameters that **are** set | Fixture K's control arm | the control config sets all four, so the mutant produces a warning where the fixture asserts none |
| 12 | Delete `W-TEMPLATE-VERSION`'s unset clause after extracting the shared helper | guard-pin arm F, which asserts the full message string | the clause is a substring of the pinned message |
| 13 | Replace the shared helper's body at **one** of its two call sites with an inlined copy | nothing — **named blind in advance** | two identical implementations produce identical results; that is what sharing them prevents. **Replacement: the batch review reads both call sites and reports that each calls the helper**, which is a reading obligation rather than a test, and it is stated as such |
| 14 | Recompute an upstream's `code_hash` at ledger time instead of copying it out of the upstream record | Fixture M's two-digest assertion | the mutant recomputes over **this** run's tree under the **new** rule, so both digests become `71bf339c…` and the record no longer shows two definitions |

**Mutation 1 is partly blind and its replacement is named.** A defaulted-versus-required parameter has
no runtime difference for callers that pass it. `mypy` catches the omission, and `uv run mypy` is in
the batch's gate; the runtime property that *matters* — that the one production caller passes a real
predicate — is mutation 2's.

**One mutation deliberately not proposed, and why.** *Replace `check-ignore` with `ls-files -co
--exclude-standard`* would be caught by Fixture E and Fixture I, but it is a **re-implementation**, not
a mutation: it changes which decision the code implements rather than whether it implements it. The
decision is defended in Decision 2 with measurements; the fixtures pin the behaviour either
implementation would have to produce, and Fixture I is the one only Decision 2's route passes.

---

## The guard pin, captured before anything moves

Six arms, captured in **batch 1**, before any code task runs. **Three arms have no authorized editor,
so a passing arm is itself the proof.** This device is the answer to five slices weakening a pin
quietly, and to the two that pinned one list twice and edited both.

| Arm | The claim | Sole authorized editor | State specified in advance |
|---|---|---|---|
| **A** | Fixture A's project — no ignored file under either tree — hashes to `sha256:71bf339c…`, and an end-to-end `run` over it produces a `run_id` ending `_71bf339` | **NONE** | unchanged, byte for byte. A passing arm after every task is the proof that the ordinary path did not move |
| **B** | Fixture B's project — the same tree plus a git-ignored `.env` — hashes to `sha256:ebc5ee53…` and its `run_id` ends `_ebc5ee5` | **task 5 only** | **exactly two literals move**, both stated now: `ebc5ee53…` → `71bf339c…` and `_ebc5ee5` → `_71bf339`. Every other literal in the arm — the `parameters_hash`, `input_manifest_hash`, `uv_lock_hash`, `units_hash`, `allocation_hash`, `design_digest` and the manifest's per-file digests, all captured in this arm for this purpose — **stays put**. A task-5 edit to any of them is a finding |
| **C** | The **other ten** figures a record carries are unmoved for Fixture B's project. **Seven are present values and are asserted as literals**: `parameters_hash`, `input_manifest_hash`, the per-file manifest digests, `uv_lock_hash`, `units_hash`, `allocation_hash`, `design_digest`. **Three would be absences on that project** — `apparatus.hash` (no probe declared under `generic`), the copied upstream `code_hash`/`parameters_hash` (no `io.reuse_from`), and the derived seeds (not published as digests) — so they are **moved out of this arm** and into Fixture M and a written statement, because *a control asserting only absences passes identically if nothing ran* | **NONE** | zero lines changed. With the three absences removed, this is the arm that makes "exactly one hash moves" a pin rather than a sentence, and Fixture M is what covers the upstream pair |
| **D** | Fixtures D and E: a tracked file matching an ignore pattern is hashed, and a tracked file inside `__pycache__` is not — both asserted on the **after** value `6ddb8634…`, which is also their today value | **NONE** | unchanged. The two literals are written **now**, as the after values computed by this design's probe, and the arm is captured green against them before anything moves. A passing arm after task 5 **is** the proof; there is no editor who could make it pass another way |
| **E** | `tests/test_hashes.py`'s two negative controls still return `sha256:e3b0c442…` from `code_hash` | **task 3 only** | task 3 adds the literal `None` argument to **13** call sites and changes **no assertion**. The batch review reports the `git diff` line count and confirms every changed line is a call, not an assert |
| **F** | `W-TEMPLATE-VERSION`'s full message string, including its unset-and-defaulted clause | **task 11 only** | **zero characters change.** Task 11 extracts the comprehension into a helper and calls it from both sites; if the message moves, the extraction was not behaviour-preserving |

---

## The § Errors and § Warnings work

**One row per code, covering every emit site.** That shape was the whole-branch Major on two of H8's
sub-slices, shipped twice inside a third, and miscounted twice in H5b.

| Code | Level | Sites | Work |
|---|---|---|---|
| `E-CODE-EMPTY` | error, `run` only | **one** — `cli.command_run`, immediately before `allocate_run_dir` (Decision 7 rules out a second) | new row in § Errors core raises, naming **both reachable situations** in one row: no file under the two trees at all, and every file under them ignored. The row says the guard is at the caller and that `hashes.code_hash` still returns the empty digest, so a reader does not go looking for it in `hashes.py` |
| `E-CODE-FILE-LIST` | error, `run` only | **one** — `provenance`'s ignore helper, reached from `command_run`'s single `code_hash` call site | new row in § Errors core raises. Names the submodule case as the reachable instance, says the message carries git's own stderr, and says explicitly that an empty answer is **not** read as "nothing ignored" |
| `W-PARAM-UNSET` | warning, `validate` | **one** — `validate._check_parameters` | new row in § Warnings core reports **and** a new § Validation row; the message enumerates every unset-and-defaulted path in one diagnostic and states the consequence (`cfg.parameters.<path>` raises `E-STEP-PARAM-UNKNOWN`) |
| `W-TEMPLATE-VERSION` | warning | one, unchanged | **no row change** (Decision 11). Guard-pin arm F |
| `W-STUDY-CODE-HASH-MISMATCH` | warning | one, unchanged | **no row change.** Its three candidate causes stay three: Decision 1 makes the fourth cause *disappear* rather than need naming, which is the scoping's § 8 reading. The row gains one link to § How the three are computed's new four-case table and nothing else |
| `E-CODE-DIRTY` | error | one, unchanged | **not H6a's.** It has no § Errors row today and H6b task 17 owns that, gated on the spine owner's ruling. Named here so nobody reads its absence as this slice's omission |
| `E-STEP-PARAM-UNKNOWN` | error | unchanged | **no row change.** The row describes a `cfg` path the config does not hold, which stays exactly true; `W-PARAM-UNSET` is a new warning about a subset of those paths, not a change to this one |

---

## The records this slice owes

`spec-defects.md` is a live list, so a closed gap is struck rather than left to mislead; every other
tracked record is appended to, never retro-edited.

| Record | Work |
|---|---|
| *"`code_hash` is not `.gitignore`-aware (S1 deviation, not a spec defect)"* | **struck**, with the ruling and with its own false sentence quoted and corrected: *"In practice nothing else gitignored appears under `src/**` or `templates/**`, so the two agree today"* was falsified by **three of the scaffold's own four patterns** |
| *"`parameters_hash` does not normalize to what `init` would have materialized"* | **struck as ruled, not as built** — the entry's own second option (*"state in § How the three are computed that normalization is the caller's job and name the caller"*) is close to what shipped, and the strike says which of the two it took and that the document sentence was **deleted** rather than relocated |
| *"`code_hash` over zero files is indistinguishable from several distinct situations"* | **struck**, and its **stale owner line corrected first**: it routes the diagnostic to *"H1 Validation's registry once H6 says what it should say"* and **H1 has shipped** — the closed-slice-owner pattern this file rejects by name at its own `RE-OWNED 2026-08-19` entry |
| The six-unwritten-`run.yaml`-keys entry | **not touched.** Its last live row (`provenance.environment.os`/`.hostname`/`.hardware`) is H6b's; H6a writes no environment key and says so |
| The nine-undocumented-codes entry | **appended to**, recording that H6a documented its own two new codes and took none of the nine, and that `E-CODE-DIRTY` remains H6b task 17's gated question |
| **New filing** — an omitted **core-schema** key validates clean and kills a step that reads it | filed **unassigned, with the reason** (Decision 10). Not *"whichever slice next touches the schema"*, the form this file rejects |
| The spine design § The hardening slices | **append a correction, do not edit**: the H6 row's *"`parameters_hash` normalization against `parameter_spec`"* is **rejected** with Decision 9's grounds, its *"the purity rule that forced both"* names a rule that is not in `design-principles.md` and is already broken in its own terms, and its *"Independent"* verdict is too strong in one direction — **H6 before H9** |
| `CLAUDE.md` | a slice entry in the running record, stating the value change, the two minted errors and one warning, **zero configs unblocked**, and the mixed-definition upstream record from Decision 8; and the order line updated to H6b, H9, H3c-3's remaining 14 |
| The feasibility analysis § Executability | one dated entry per Decision 14: the four rows repeated character for character, no fifth number, and `W-PARAM-UNSET`'s effect on those configs marked **unknowable with the reason** |
| `hashes.py`'s `covered_config` docstring | its *"an OPEN gap owned by H6"* paragraph is **replaced by the ruling**, since the gap is closed by decision rather than by code and a docstring pointing at a struck entry misleads |

---

## Task decomposition — 12, and the batches

| # | Task |
|---|---|
| 1 | **Ruling A written into the documents**: § How the three are computed wins; the **four-case table** added there; § Templates' clause narrowed to the dirty gate; every other site links to the table rather than restating it |
| 2 | **The guard pin, six arms**, captured before anything moves |
| 3 | `hashed_files`/`code_hash` gain the **required batch** `include` parameter; **all 14 call sites** pass `None` — the 13 in `tests/test_hashes.py` **and `cli.command_run`'s `ch = code_hash(repo_root)`**, which task 5 then swaps for the real filter. Without the production site, batch 2 does not typecheck. The docstring says what `None` claims |
| 4 | The ignore helper in `provenance.py`: `check-ignore -z --stdin`, `os.fsdecode`, tri-state returncode, `E-CODE-FILE-LIST`; Fixtures F and I |
| 5 | **Wire it at `command_run`'s single call site**; Fixtures A–E, J and **M**; mutations 2–7 and 14 |
| 6 | The hash ↔ gate agreement (Decision 13), and **replace the two byte-identical `__pycache__` tests** with one that can fail plus Fixture E's tracked arm |
| 7 | **Ruling C written**: no marker, `uv.lock` is the carrier, the mixed-definition upstream record named |
| 8 | `E-CODE-EMPTY`: the guard, its § Errors row, Fixtures G and H, mutations 8 and 9 |
| 9 | The zero-file blast radius: guard-pin arm E re-run and reported, and the struck entry's stale H1 owner corrected before it is struck |
| 10 | **Ruling B written into the documents**: the normalization sentence **deleted**, its false `diff` justification **deleted**, the subtractive rule left standing, `covered_config`'s docstring re-pointed |
| 11 | `W-PARAM-UNSET` at `validate`, the shared helper, arm F held, its § Warnings and § Validation rows; Fixture K; mutations 10–12; **the full-suite render count reported** |
| 12 | The records: strikes, the new filing, the spine correction, the § Executability entry, `CLAUDE.md` |

| Batch | Tasks | What its review must look for |
|---|---|---|
| **1 — the rulings, the documents, the pin** | 1, 2, 7, 10 | Does the four-case table exist in **one** place, and does every other site **link** rather than restate? (A four-case rule invites a two-case sentence; H5b shipped one five times.) Does any new sentence claim behaviour the code will not have after batch 3? Does the pin have a named sole editor per arm, **three arms with none**, and are arm B's two moving literals and arm D's two after-values written down **now**? Were the two false clauses in § How the three are computed **deleted** rather than rewritten? Mechanical pass on every `reference.md` edit |
| **2 — the seam** | 3, 4 | Is `include` **required**, and does `mypy` pass? Does the helper check the **returncode** rather than stdout, pass `-z` on both ends, and decode with `os.fsdecode`? Is Fixture F asserting **set equality** rather than a hash comparison? Arm E's `git diff` line count **reported**, every changed line a call and not an assert |
| **3 — THE VALUE CHANGE** | 5, 6 | **A real-command review**: run the installed console script end to end on Fixtures A, B, D and J's projects and read `run.yaml` **key by key** against § The value change's tables — not `validate`, not a direct call. Is arm B's edit exactly the two enumerated literals, with the other ten figures untouched? Does Fixture M's record really carry **two** digests, and does its assertion name the record's key set rather than merely asserting the absence of a marker? Is arm A still passing, unedited? Is arm D still green **without** an edit? Was the duplicated `__pycache__` pin replaced by a test that can fail, and was **that** demonstrated by mutation rather than asserted? |
| **4 — the zero-file refusal** | 8, 9 | Is there exactly **one** emit site, and does the § Errors row cover **both** reachable situations? Does Fixture G assert that **no run directory** was created, not only the exit code? Was the stale H1 owner line corrected **before** the entry was struck, so the correction survives in the record? |
| **5 — the parameters half** | 11 | Is the boundary stated — `parameters` block only, core-schema half filed **unassigned with the reason**? Is the control arm of Fixture K present and can it fail? Is arm F byte-unchanged? **Report the suite-wide count** of tests whose render changed, and for each, say whether the assertion was *updated* or *loosened* |
| **6 — the records** | 12 | **A full review, not a skim.** Twice a controller ran a final batch straight into the whole-branch gate, and the second time three of four Majors lived in it. Check every struck entry against the code, every "filed" against the file, the spine correction appended rather than edited, and the § Executability table's four rows **character for character** |

**Every batch gets a review.** Batch 3 is the value change and gets the real-command review.

**Should H6a split further? No.** Decisions 1, 2, 3 and 7 are one argument — an ignore-aware hash makes
the zero-file case more reachable, so shipping the first without the second would newly publish the
digest of nothing for a repo that today publishes a real one (Fixture H). § The value change has to be
made **once**, over the whole set of moving fields, or it is not an argument.

---

## Disagreements with the record this pass found

Reported as a list, not as a count, and each grepped or run rather than recalled.

1. **The scoping's recommended implementation route is the wrong one**, and this design takes a
   different one (Decision 2). `git ls-files -co --exclude-standard` answers a correlated question;
   its three failure modes — a deleted tracked file, a tracked file inside `__pycache__`, and a
   submodule's contents — were each measured here, and the third is silent.
2. **The scoping's route also needs `-z` and would have been written without it.** Its § 2.1 quotes
   the command without the flag, and git quotes non-ASCII paths by default — measured.
3. **The scoping's *"the hash and the dirty gate … would share one file list"* is not achievable**, and
   writing it into a docstring would be a false claim (Decision 13). `git status --porcelain` never
   lists a clean tracked file. What they share is the pathspec.
4. **The charter's *"normalization against `parameter_spec`"* is rejected outright**, not narrowed
   (Decision 9) — the scoping offered three options and this design takes the third with an added
   ground the scoping did not state: normalizing would give one identity claim to a config that runs
   and one that cannot.
5. **`E-CODE-DIRTY` is raised by shipped code and appears in none of the four documents** — the
   scoping's finding, re-swept here: `grep -rn "E-CODE-DIRTY" src/ tests/ docs/*.md` → 3 hits, all in
   `src/` and `tests/`, none in a document. Control: `grep -rn "E-GIT-NO-REPO" docs/reference.md` → 2,
   so the sweep can find a documented code.
6. **The zero-file entry's owner line routes to H1, which shipped** — re-read here, corrected by task 9.
7. **The spine's *"Independent"* for H6 is too strong in one direction** — H6 before H9, the scoping's
   § 9 argument, unchanged by anything measured here.
8. **`covered_config`'s docstring will point at a struck entry** the moment task 10 lands, which is why
   it is in the records table rather than left to a sweep.

**What was grepped, rather than a count.** `grep -rn "code_hash(" src/publishable/*.py` (one caller
besides the definition); `grep -c "code_hash(" tests/test_hashes.py` → 13 and
`grep -c "git init\|subprocess" tests/test_hashes.py` → 0; `grep -rn "E-CODE-EMPTY"`,
`"E-CODE-FILE-LIST"`, `"W-PARAM-UNSET"` across `src/`, `tests/` and `docs/*.md` → **0** each, control
`E-CODE-DIRTY` → 3; `grep -rn '"code_hash"\|code_hash:' src/publishable/*.py` for the carrier list;
`grep -rn "dirty" src/publishable/validate.py` → 0. Each sweep names its file list; none filters the
output of a sweep whose job is to find a string.

---

## What could not be measured, and what this design assumed

- **Whether a tracked non-ASCII filename joins correctly on Linux or on a case-insensitive
  non-APFS filesystem.** Measured true on macOS/APFS with `core.precomposeunicode = true`. Fixture F
  records the platform and names NFC normalization as the fallback; if CI is on Linux, the plan should
  **read the fixture's result there before trusting it**.
- **`check-ignore`'s cost on a very large tree.** 12.1 ms over 53 paths on this repo; nothing here
  measures 10,000.
- **Whether a real resolver writing under `src/` during resolution is buildable as a fixture**, which
  mutation 7 needs. It should be — a project-local resolver is user code — but no such fixture exists
  today and the plan must build one or **name mutation 7 blind and owe a replacement**.
- **The exact suite-wide render blast radius of `W-PARAM-UNSET`.** Bounded here: 5 tests assert on the
  `✓ config valid` string and 4 on the `N problems` line, and 39 of 40 parameter blocks the sweep found
  omit a defaulted parameter. The plan runs the suite and reports the real number.
- **Whether any project in the wild carries a submodule under `src/**`.** Unknowable, which is why
  Decision 6's cost-if-wrong names the fallback rather than claiming there is none.
