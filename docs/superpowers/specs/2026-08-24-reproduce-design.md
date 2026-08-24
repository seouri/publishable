# H9c — `reproduce`: the lockfile decisions, the clone, `apparatus.expected.json` — design

**Written 2026-08-24, against `main` at `a628707`** (the H9b merge). H9 was scoped at **49 tasks in
four parts** ([`H9-SCOPING.md`](../H9-SCOPING.md), measured 2026-08-23 against `822fe4b`, corrected
before dispatch); H9c is scoped there at **11 tasks** and this plan is **15**. That is stated first
rather than buried: every re-scoping in this spine has run under in the same direction, and merging
tasks to hit a number is the failure mode the scoping's own prediction is about.

H9c is why H9 goes last. The spine's charter row says *"`reproduce` is what reads the environment
back, so it decides the unresolved lockfile questions,"* and the scoping's § 3 turned that into four
named questions plus a fifth (`diff`'s `uv.lock` detail). H9a made the re-entry seam, H9b made
`identity.json` durable and taught a second entry to compare recorded against recomputed, H6a
changed what `code_hash` computes and H6b what the environment record holds. **This slice is the
reader those four were writing for**, and the asymmetry that puts it after `resume` is the one the
scoping names: `resume` compares one lockfile against a byte copy it can always reach, while
`reproduce` must **choose between two sources that can disagree** — or find that neither is
reachable at all.

Four controller rulings bind it: **Y** (one path, no target device), **Z** (a hash difference names
the input, never the cause), **AA** (two lockfile sources, neither silently preferred), **BB**
(`apparatus.expected.json` is a comparison, not a gate). H6a's Rulings C, F and M and H6b's Ruling Q
still bind where cited; H9b's Rulings V and W bind the `identity.json` reader this slice does **not**
use, and § 4 says why.

---

## 0. What was measured, before any decision

Every project, clone, bundle and run directory below lives under the session scratchpad, **outside
this repository** — H6a made the dirty gate load-bearing, and a creation command run inside the tree
would dirty what that gate reads. Nothing under `src/`, `tests/` or the four documents was edited by
this pass. The fixture project is a `publishable new` scaffold plus one `generate experiment`
(template `generic`, 6 units from a CSV, 2 seed repeats), committed at `fcc45b7`, run at
`run_2026-08-24T11-01-44Z_0cc6ddd`.

**1. A run records an untracked `uv.lock`; a clone of the recorded commit has none.** `git status
--porcelain` printed `?? uv.lock` and the run exited `0` — the dirty gate's pathspec is
`HASHED_TREES` only, narrowed there by H6b's Ruling L. The run directory holds
`environment/uv.lock` with those bytes and `uv_lock_hash: sha256:45cd9f56…`; `git clone` of the same
repo at the same commit holds **no `uv.lock` at all**. The scoping's § 3 Q2, reproduced.

**2. `code_hash` reproduces exactly in a plain clone.** Both trees, recomputed with `command_run`'s
own git-aware predicate: **6 files each, the same six, `short` = `0cc6ddd` on both sides**, equal to
the run ID's own suffix and to `identity.json`'s `code_hash`. Step 3 of § Reproducing on another
device is achievable.

**3. The H6a boundary breaks it on an unchanged tree.** The same clone with a **git-ignored**
`src/pilot/.env` present (`git check-ignore -v` → `.gitignore:2:.env`): post-H6a (git-aware)
`0cc6ddd`, pre-H6a (`include=None`) `bdf2ce9`. A pre-H6a record therefore carries a figure a post-H6a
`reproduce` will not reproduce — and § Reproducing on another device says a mismatch means *"a
rewritten or force-pushed history."* This is the scoping's § 11 and it is Ruling Z's ground.

**4. A FOURTH cause of that mismatch, and it is new here — machine-local git configuration.** With an
ambient `core.autocrlf = true`, `git clone` of the same commit gives **`d37416e`**: the working tree
is checked out with CRLF line endings, so the file *contents* `code_hash` folds over are different
bytes. Measured, and the fix measured with it: `git -c core.autocrlf=false clone …` under the same
ambient setting gives **`0cc6ddd`**. **Each flag was armed separately, on H6a Ruling M's own
precedent** — `core.autocrlf=false` alone gives `0cc6ddd`; `core.eol=lf` alone gives `d37416e`, so it
is **not load-bearing and is dropped**.

**5. A FIFTH cause, and this one cannot be fixed — a tracked `.gitattributes`.** With
`* text eol=crlf` committed, a clone made with `core.autocrlf=false` still checks out CRLF and hashes
`d37416e`, while the original working tree — never re-materialized — still hashes `0cc6ddd`. So under
that attribute **`code_hash` is not a property of the commit at all**: it is a property of how a
working tree was materialized. `.gitattributes` travels with the tree, so H6a's Ruling F does not
license overriding it, and no `-c` flag this slice passes may try. Filed (§ 5, item 3).

**6. A bundle member's recorded lockfile path is a dangling reference.** `study new` + `study add`
over the same run gives a bundle of exactly two files, `study.yaml` and `main.run.yaml`. The member's
`provenance.environment.uv_lock` still reads **`environment/uv.lock`** — a relative path into a run
directory the bundle does not contain — while `repo_root`, `hostname` and `input_manifest` are
`<redacted by study add>` and `data.input_dir`/`output_dir` are redacted in the embedded config too.
`git.commit` and `git.remote` survive. **So from a bundle member only `uv_lock_hash` travels, and the
byte copy is unreachable.** This is Ruling AA's hardest case and Ruling Y's cost-if-wrong.

**7. `provenance.environment` names no `pyproject.toml` at all**, though the run directory holds
`environment/pyproject.toml` beside the lockfile. And that copy can disagree with the commit: an
edit to `pyproject.toml` left uncommitted gives `git status --porcelain` → ` M pyproject.toml`, the
run exits `0`, and `diff`-ing the recorded copy against the clone's shows the edit. **A third
environment input that can disagree**, reachable in the run-directory form and absent from the
bundle form.

**8. `remote: null` is ordinary.** The scaffolded project has one local commit and no origin;
`provenance.git.remote` is `null` and the run exits `0`. § Reproducing on another device step 1 has
nothing to clone.

**9. `covered_config` excludes `metadata`, `data.input_dir` and `data.output_dir`.** So a config
written back with both paths blanked has **the recorded `parameters_hash`**, exactly — which is what
makes the write-back self-checkable (Decision 11).

**10. An installed template's class is never constructed by this interpreter.**
`templates/registry._claims` reads entry-point *metadata* for an installed name and attaches
`cls=None`; `_merged` keeps only claims with a class, so `get_template` returns `None` for a
plugin-provided template. A plugin is also not installed in the interpreter running `reproduce` — it
is installed into the **clone's** environment by `uv sync`. **So step 6's `required_env` list is
unbuildable in-process for the plugin case**, which is the same shape as `dry-run`'s greenfield
collision (Decision 12).

**11. `secrets.load_env` treats an empty value as missing** (`missing_env` does; a bare key parses to
`None` and is skipped). So writing a blank `.env` from `.env.example` cannot turn a *missing*
credential into a *present* one.

**12. `Observations.record` then `Observations.changed` already is the gate**, per-condition,
first-*answered*, tolerant of `null` in both directions — and `apparatus.replay_ledger` already
reconstitutes one from a file by replaying through `record`. **The expected-file comparison needs no
new comparison function** (Decision 4).

**13. `reproduce` is `NOT BUILT` and reachable.** `main(["reproduce", "run.yaml"])` exits `2` with
*"specified but not built … § Reproducing on another device"*. `NOT_BUILT_COMMANDS` holds four names:
`demo`, `docs`, `list-templates`, `reproduce`.

---

## 1. The four controller rulings

### Decision 1 (Ruling Y) — the operand is a run record **file** or a config **file**, discriminated by `run_id`; a directory and a `study.yaml` are refused by name

**The question.** *"Reproducing on another device"* names where the user is, not an argument, and
*"operation commands take paths and nothing else"* is a `CLAUDE.md` invariant. So `reproduce` runs
**on** the other device against a record it is given, and there is no target-device argument, no
`--into`, and no host, user or key anywhere in its interface. What remains is: **which** path.

**The answer.** One path, which must be a **file**:

| Operand | Verdict |
|---|---|
| `<run_dir>/run.yaml` | **Accepted** — the run-directory form. `environment/` is reachable as a sibling |
| A bundle member, `main.run.yaml` | **Accepted** — the bundle form. `environment/` is **not** reachable (§ 0.6) |
| A config file | **Accepted** — the config form, steps 4 onward, already specified |
| A **directory** | **Refused**, `E-REPRODUCE-OPERAND`, naming `<dir>/run.yaml` |
| A bundle root, `study.yaml` | **Refused**, `E-REPRODUCE-BUNDLE`, **listing the members it holds** |
| Anything else | **Refused**, `E-REPRODUCE-OPERAND` |

**Discrimination is structural, not by basename.** A bundle member is `main.run.yaml`, not
`run.yaml`, so a basename test is the reserved-name proxy this repo has already paid for at a
`report_by` stratum. The rule is: parse the YAML once; a mapping holding **`run_id`** is a record and
goes to `lineage.read_record_file` for the version check; a mapping holding `experiment_type` and no
`run_id` is a config; a mapping holding `provenance` or `results` but no `run_id` is an **edited
record** and is refused rather than read as a config; anything else is `E-REPRODUCE-OPERAND`.

**`read_record_file` is the reader, and it is the reader because of the bundle.** Its own docstring
says so: *"a bundle member is not `<dir>/run.yaml` … so a reader keyed to a directory cannot address
one at all."* H9c is its fifth caller and adds no refusal set of its own for the parse.

**Alternatives rejected.** *A run directory* — accepting one would give `reproduce` and `resume` the
same operand for opposite actions, and `resume` is documented as *"the one command that can't take a
`run.yaml`."* Refusing it costs the user one path component and the message supplies it. *A
`study.yaml` plus a member name* — two arguments describing one thing, which § CLI reference already
rejects for `resume`; and the refusal can **list the members**, which is more useful than guessing
one. *Basename discrimination* — the proxy above.

**Cost if wrong.** If the bundle member form were refused, a reader holding a published bundle — the
case `study` exists to serve — could not reproduce from it at all. That is why the bundle form is a
first-class arm here rather than a note, and why its two degradations (§ 0.6, § 0.7) are reported
facts rather than silences.

### Decision 2 (Ruling Z) — every verdict is derivable from what was compared; a difference names the **input** and the candidate causes it cannot separate, and never a cause

**The question.** § Reproducing on another device step 3 says a `code_hash` mismatch catches *"a
rewritten or force-pushed history."* The scoping measured that claim false across the H6a boundary
(§ 0.3), and this pass found two more counter-examples (§ 0.4, § 0.5). A confident wrong diagnosis is
worse than an honest unknown, and this repo has shipped four sentences that invented a cause.

**The answer.** `reproduce` prints, for each figure it compared, **the figure, the two values, and
the input it read each from** — and where a difference has more than one possible cause it
**enumerates the candidates without choosing**. Concretely, a `code_hash` difference prints the
recorded digest, the computed digest, the **file count and the file list** the computation folded over
(both derivable), the checkout path, and this closed list of causes it cannot tell apart:

- the code at that commit really is different — a rewritten or force-pushed history;
- the record predates H6a's redefinition of which files are hashed (§ 0.3), which **no key in
  `run.yaml` can date** — H6a's Ruling C refused a definition marker and did not bump
  `schema_version`, so `uv.lock` is the carrier and a scaffolded project may have none;
- this machine's git materialized the tree differently — `core.autocrlf` (§ 0.4), which the clone
  neutralizes, or a tracked `.gitattributes` (§ 0.5), which it may not.

**The one cause it names is the one the record names.** A record with `draft: true` was made from a
tree that was never reachable from any commit, so a `code_hash` difference is **expected** and its
cause is recorded. `reproduce` says so and declines the verification rather than reporting a mismatch
— joining the pattern § Reproducing on another device already uses for the config form, which
*"cannot verify a `code_hash` and says so, rather than reporting a match it never made."* See
Decision 10.

**Alternatives rejected.** *Keep the sentence and print it* — measured false three ways. *Mint a
marker for the hash definition* — **forbidden**: H6a Ruling C, and the scoping's § 12 lists it under
what H9 may not fold in. *Read `uv_lock_hash` to date the record* — cannot work in general: the
lockfile is the carrier only when there is one, and a scaffolded project's is `null`; offered as one
candidate cause, not as a dating mechanism. *Silence on the causes* — a bare "differs" sends the
reader to the wrong first guess, which is the harm.

**Cost if wrong.** A `reproduce` that accuses a faithful clone of a rewritten history is a serious
accusation made by a machine that could not have known, and the reader has no way to check it. In the
other direction, an enumeration nobody reads costs three lines of output.

### Decision 3 (Ruling AA) — the recorded `uv_lock_hash` is the authority, the run directory's byte copy is the preferred carrier, and the clone's committed lockfile is used only when it matches; every absence and every disagreement is a printed fact

**The question.** § 0.1: there are two candidate lockfiles and they can disagree. § 0.6: in the
bundle form the byte copy is unreachable and only the hash travels. § 0.7: there is a **third**
environment input, `pyproject.toml`, which can disagree with the commit too. Nothing in the four
documents rules any of it.

**The answer.** One ranking, evaluated in order, and each step prints what it found:

1. **`uv_lock_hash` is `null`** (the record pinned no environment) → `E-REPRODUCE-UNLOCKED`, exit
   `1`, the checkout kept. Decision 6.
2. **The record's byte copy is reachable** — `environment/uv.lock` beside the operand, which is the
   run-directory form — → its sha256 is checked against the recorded `uv_lock_hash`
   (`E-REPRODUCE-LOCKFILE-EDITED` if it fails: a run directory whose copy was edited after the
   run), then it is **copied into the checkout**. The clone's own lockfile is then reported as one of
   *absent*, *identical*, or *DIFFERS* — never silently overwritten without the line.
3. **The byte copy is unreachable** (the bundle form) → the clone's committed `uv.lock` is used **if
   and only if** its sha256 equals the recorded `uv_lock_hash`, and the line says so. If it differs,
   or there is none, → `E-REPRODUCE-LOCKFILE-UNREACHABLE`, exit `1`, checkout kept, the message
   naming both facts (the recorded digest, and what the clone holds).
4. **`pyproject.toml`** — where `environment/pyproject.toml` is reachable, it is compared against the
   clone's byte for byte and reported *identical* or *DIFFERS*, **before** `uv sync` runs. It is not
   copied in and it does not refuse: it is the input that explains a `uv sync --locked` failure a
   reader would otherwise have to guess at.
5. `uv sync --locked` in the checkout. A failure is exit **`5`** — § Exit codes' *"a clone or `uv
   sync` that failed"*, gaining its first reader.

**The byte copy wins because it is what the run actually used.** The clone's committed lockfile is a
claim about the commit; the byte copy is a record of the environment the numbers came through, and
`uv_lock_hash` covers it. Where they disagree the recorded one is authoritative and the disagreement
is the interesting fact, which is why it is printed rather than resolved.

**A bundle carries no lockfile, and that is `study`'s gap, not `reproduce`'s.** Step 3 is a real
degradation: a bundle member whose project never committed its lockfile cannot be reproduced from the
bundle alone. **Filed against `study add` with its owner named (§ 5, item 4) and deliberately not
fixed here** — `study`'s bundle contents are H8c's surface and widening them is charter growth.

**Alternatives rejected.** *Always sync against the clone's lockfile* — reproduces numbers through an
environment nobody recorded, which is Ruling AA's stated cost. *Refuse any run whose lockfile was
never committed* — refuses every run of every scaffolded project today (§ 0.1 and Q1's bootstrapping
fact), and it is `run`'s question rather than `reproduce`'s. *Prefer whichever exists* — the silent
preference the ruling forbids. *Copy `pyproject.toml` in too* — it is a **tracked** file at the
recorded commit, and overwriting the commit's own manifest with an uncommitted edit would make the
checkout a tree that exists nowhere.

**Cost if wrong.** An environment restored from the wrong lockfile reproduces numbers nobody can
trace, and — worse — reports success while doing it.

### Decision 4 (Ruling BB) — `reproduce` **writes** the expectation and refuses nothing on apparatus grounds; the comparison happens at the next `run`'s first probe, through a second `Observations` and one new code

**The question.** H7d Part B made a fact that moves from its first *answered* observation fail the
run. On another device the apparatus will differ — a GPU model, a hostname, an OS — and that is
expected rather than exceptional. So what does `reproduce` do about it?

**The answer, in two halves.**

*`reproduce`'s half.* When `provenance.apparatus` is non-`null` it writes
`configs/<name>/apparatus.expected.json` — the recorded `facts` mapping verbatim, condition key to
fact mapping — **once, and never rewritten** (it refuses to overwrite an existing one rather than
replacing it, `E-REPRODUCE-EXPECTED-EXISTS`); and it prints the block § Reproducing on another device
already specifies, *"This run measured through an apparatus. Reproducing it needs:"*. It **probes
nothing, compares nothing and refuses nothing** on apparatus grounds. `reproduce` is not one of the
four places a probe runs, exactly as `diff` is not, and the reason is the same: it has no config
resolved against a plugin it does not have.

*`run`'s half.* When the config's directory holds `apparatus.expected.json`, the run's first probe
**per condition** is additionally compared against it, and a contradiction raises
**`E-APPARATUS-UNEXPECTED`**.

**The comparison is the shipped gate, not a new one** (§ 0.12). A second `Observations` is built by
`record`-ing each condition's expected facts; the incoming probe's facts are then passed to that
object's `changed`. Everything the gate's own terms buy comes along for free and structurally rather
than by argument: per-condition scoping, first-*answered* semantics, `null → value` **passing** so a
fact the original never answered does not fail a reproduction that answers it, `value → null`
passing for the same reason, and reflexivity-safety for a `nan`. § Reproducing on another device
states that asymmetry and calls it *"more evidence rather than less"*; this is what makes the
sentence true of the code.

**The seeded object is used for `changed` and nothing else, and that is load-bearing.**
`Observations.record` bumps `_total_counts` and `_null_counts`, which feed
`provenance.apparatus.unobserved` and `W-APPARATUS-UNANSWERED`. Seeding the run's **own**
`Observations` — the shape `Resumed.baseline` uses, where the counts were real probes of that run —
would make the reproduction's record claim probe calls it never made. A second object cannot: it is
never asked for `facts_document`, `unobserved` or `warn_unanswered`.

**A distinct code, because the remedy is distinct.** `E-APPARATUS-CHANGED` means *the apparatus moved
during this run — stop*. `E-APPARATUS-UNEXPECTED` means *this apparatus is not the recorded one —
either accept that this is not a reproduction, or edit `apparatus.expected.json`, which
§ Reproducing on another device says you may*. One code covering both would be H4d's *one code, five
faults* again. **No exit code is minted**: the new code joins `STOP_CODES`, so `1` before the first
execution and `4` once there are results, derived from `run_status`'s shipped fold exactly as H9b
derived the same pair. It does **not** join `APPARATUS_CODES`, for `E-APPARATUS-CHANGED`'s own
documented reason — the loop breaks on a `STOP_CODES` member before `command_run`'s containment
filter is reached, so admitting it would add a member nothing exercises.

**Alternatives rejected.** *`reproduce` probes and refuses* — a reproduce that cannot run anywhere,
and it needs a plugin `uv sync` has only just installed into a different interpreter. *`reproduce`
probes and warns* — same interpreter problem, and the warning would fire before the environment
exists. *`run` reports the mismatch instead of failing* — § Reproducing is explicit that the first
probe *"fails on any difference, at the same volume as a lockfile mismatch"*, and numbers that came
through an apparatus nobody recorded is Ruling BB's other stated cost. *Use `diff`'s wider net* — the
third reading of one comparison, and the document rules against it: `diff` flags `null → value`
because it asks whether two runs measured alike; the gate tolerates it because it asks whether the
apparatus moved; the expectation file sides with the **gate**, and § Reproducing says why in its own
words. H8b ruled the first two are two questions rather than one contradiction; this is the third,
and it is stated so nobody folds it into either.

**Cost if wrong.** Either a reproduce that cannot run anywhere, or one whose numbers came through an
apparatus nobody recorded.

---

## 2. The lockfile questions the charter promised to decide

### Decision 5 (Q1) — `W-ENV-UNLOCKED` is **affirmed**, not promoted, and § Design goals gains the footnote its own filing proposes

**The question.** `design-principles.md` § Design goals says *"uv is not optional. Environments are
captured and rebuilt through uv"* — read strictly, a run with no lockfile should refuse. The oldest
H9-owned entry in `spec-defects.md` says the slice that builds `reproduce` is positioned to decide.

**The answer: affirm the warning.** Re-measured 2026-08-24: `uv lock` inside a project
`publishable new` scaffolds still fails outright — *"Because publishable was not found in the package
registry"* — so promoting `W-ENV-UNLOCKED` would refuse **every run of every scaffolded project**
against this checkout. The constraint is a bootstrapping fact about this repository's publication
state, not a principle, and refusing on it would block the users least able to diagnose it.
`design-principles.md` § Design goals gains the footnote the filing itself proposes: **"not optional"
describes `reproduce`'s obligation, not `run`'s** — which is now a true sentence rather than a
promise, because Decision 6 makes `reproduce` the command that refuses.

**The oldest H9-owned entry is closed by this decision** and struck in `spec-defects.md`. The
sibling entry — *a scaffolded project cannot resolve a lockfile until `publishable` is published* —
**stays open**, because its retirement condition is a release, not a slice.

**Alternatives rejected.** *Promote it* — refuses every scaffolded run. *Leave it undecided* — the
charter's own reason for scheduling H9 last. **Cost if wrong:** a run recorded as unpinned that
should have been refused, which `reproduce` then refuses instead — one command later, and with a
checkout to show for it.

### Decision 6 (Q3) — `uv_lock: null` is `E-REPRODUCE-UNLOCKED` at exit `1`, and the checkout is kept

**The question.** § Reproducing on another device step 4 has nothing to `--locked` against when the
record pinned no environment.

**The answer.** A named refusal at exit `1`, **after** the clone, with the checkout left on disk and
the closing transcript printed with the `uv sync` line replaced by the stated gap. Exit `1` because
nothing outside the machine refused — `5`'s class is the one you retry — and the thing you asked
about is genuinely wrong: you asked to reproduce a run whose environment was never pinned. The
checkout is kept because the deliverable of `reproduce` is a prepared checkout, and a stop that
discards its own artifacts is the fault H9b closed at exit 4 (*a stop must be legible from the
artifacts*, H7d Part B).

**This is what `W-ENV-UNLOCKED`'s shipped message already promises.** Its text — pinned in
`tests/test_cli.py` — reads *"`reproduce` will not be able to restore it"*. Decision 6 is that
sentence coming true, which is the strongest available ground for it and the reason arm I of the
guard pin exists.

**Alternatives rejected.** *Exit 0 with a warning* — `reproduce` would report success having restored
nothing. *Refuse before cloning* — the clone is the half that still works and the user still wants
it. *Exit 5* — nothing external refused. **Cost if wrong:** a user who wanted the checkout gets it
either way; a script keying on `0` correctly learns this is not a reproduction.

### Decision 7 — the clone is two git invocations, `-c core.autocrlf=false` on both, `core.eol=lf` dropped as not load-bearing, and `.gitattributes` is out of reach by ruling

**The question.** § 0.4: a faithful clone on a machine with `core.autocrlf = true` hashes `d37416e`
against a recorded `0cc6ddd`. Does `reproduce` neutralize it?

**The answer: yes, for `core.autocrlf`, and the ground is H6a's own.** Ruling F: *a rule that does
not travel with the tree cannot define the tree's identity*. H6a's Ruling M declined to neutralize
`core.autocrlf` **for the dirty gate**, and the ledger states the distinction in as many words: *a
gate answers "may this run proceed here", which is local by nature; a hash answers "is this the same
code", which is not.* `reproduce` is not a gate. So:

```
git -c core.autocrlf=false clone -c core.autocrlf=false <remote> <dest>
git -C <dest> checkout --detach <commit>
```

**Both placements, and each has a job.** The leading `-c` fixes the **initial** checkout, which is
where the conversion happens; `clone -c` **persists** the setting into the new repo's `.git/config`,
so a later `git checkout` in the prepared checkout does not re-convert. Measured: `clone -c` alone
stored `false` and still produced CRLF, because the ambient value won for the initial checkout — so
neither placement is redundant.

**`core.eol=lf` is dropped, measured rather than assumed.** `core.autocrlf=false` alone gives
`0cc6ddd`; `core.eol=lf` alone gives `d37416e`. H6a Ruling M's precedent is that **each `-c` flag
gets its own arm** — *removing the excludes flag fails four tests, removing the untracked flag fails
exactly one* — and a flag with no arm is a flag nobody can prove is doing anything.

**A tracked `.gitattributes` is deliberately NOT overridden** (§ 0.5). It travels with the commit, so
Ruling F licenses nothing against it, and forcing `text=auto` off would materialize a tree the repo's
own declared rules say should not exist. It is instead one of Decision 2's enumerated candidate
causes, and it is **filed** (§ 5, item 3) because it is a genuine spec-level fact: under
`* text eol=crlf`, `code_hash` is a property of how a working tree was materialized rather than of
the commit, and the author's own machine and every fresh clone will disagree forever.

**Nothing else is neutralized.** No `GIT_CONFIG_GLOBAL`, no `GIT_CONFIG_SYSTEM`, no
`core.excludesFile` — the last because the clone is a *fresh* checkout of a commit and the
`.gitignore` files that decide the hash are **tracked**, so `hashed_files`'s own predicate asks the
right question already (§ 0.2 confirms it: 6 files, the same six, on both sides). Answering with a
blunt instrument that happens to contain the answer is Ruling M's own named failure.

**Cost if wrong.** Over-neutralizing blocks a correct checkout on a machine whose settings exist
because filesystems differ — Ruling M's measured harm. Under-neutralizing reports a `code_hash`
difference on every Windows reproduction, which is Ruling Z's harm.

### Decision 8 — `remote: null` is `E-REPRODUCE-NO-REMOTE` at exit `1`; exit `5` stays for a clone that was attempted and failed

**The question.** § 0.8: `remote: null` is ordinary, and step 1 has nothing to clone. § What `demo`
walks you through acknowledges the state and no document gives it a code.

**The answer.** Exit `1`, with a message that names the recorded `git.commit` so a reader who *has*
the repository can `git checkout` it themselves. Not `5`: nothing outside the machine refused, and
`5`'s row is *"a clone or `uv sync` that failed"* — a clone that was **attempted**. Keeping `1` here
preserves `5` as the retry class, which is the property § Exit codes says it exists for.

**A bundle member keeps its remote** (§ 0.6), so this refusal is about local-only repositories rather
than about bundles. **Cost if wrong:** a user with a local-only record and no other copy of the repo
gets one honest refusal instead of a retry loop against nothing.

### Decision 9 — the destination is derived, and it refuses to collide or to nest

**The question.** § Reproducing on another device: *"No `--into`: the destination is derived, so it
can't collide with an existing checkout and doesn't need naming."* The first clause is a rule; the
second is a **claim**, and it is false — running `reproduce` twice on one record derives the same
name twice.

**The answer.** The name is the remote URL's last component with a trailing `.git` removed, then
`_`, then the `run_id` — `my-study_run_2026-08-06T14-02-11Z_8e21ab3/`, which is § Reproducing's own
worked example. It is created **relative to the working directory**, which is where the user is, and:

- an existing destination is `E-REPRODUCE-DEST-EXISTS` at exit `1` — the creation-command family's
  rule (*refusing is how one stays safe to re-run*), not an overwrite;
- a destination that resolves **inside a git repository** is `E-REPRODUCE-DEST-IN-REPO` at exit `1`,
  the walk-up being `find_repo_root` from the destination's parent. Nesting a reproduction inside
  another experiment repo makes every walk-up question — which repo, which `code_hash`, which dirty
  gate — answerable two ways, which is exactly what `CLAUDE.md`'s `input_dir`/`output_dir` invariant
  exists to prevent.

**The document's "can't collide" clause is narrowed** to what is true: the destination is derived so
you do not name it, and a second `reproduce` of the same run refuses rather than overwriting.
`repo_root` is **not** an input — it is `<redacted by study add>` in a bundle, and the remote is the
only name that travels in both forms.

**Cost if wrong.** A derived name that collides silently overwrites a previous reproduction; a
nested one hands the next command the wrong repository.

### Decision 10 — `code_hash` is verified in the checkout with the run's own predicate, and a `draft` record declines the verification rather than failing it

**The answer.** After the checkout, `code_hash` is recomputed with **exactly** `command_run`'s
predicate — `hashes.hashed_files(dest, lambda c: unignored_under_hashed_trees(dest, c))` then
`code_hash_of` — and compared against the record's `code_hash`. Equal → one line saying so, with the
file count. Different → `E-REPRODUCE-CODE-HASH` at exit `1`, Decision 2's output, **checkout kept**.

**Not re-implemented, and not `code_hash(root, include)` either**: the pair form is what gives the
file **list** Decision 2 prints, which is why `code_hash_of` was extracted (§ How the three are
computed's own disclosure).

**`draft: true` declines rather than fails.** The record says the tree was not reachable from any
commit, so the comparison has no operand worth reporting a verdict on. `reproduce` prints *"this
record is a draft: its code was not committed, so `code_hash` is not verified"* and continues — the
same posture § Reproducing on another device takes for the config form, which *"cannot verify a
`code_hash` and says so, rather than reporting a match it never made."* Refusing a draft outright was
the alternative; it was rejected because a draft's checkout is still worth having and because
`report` already refuses to *cite* a draft, which is where that guard belongs.

### Decision 11 — the config is written by **re-serializing the record's embedded config**, not by editing the byte copy, and the write is verified by `parameters_hash`

**The question.** § 0.9 and the scoping's § 11: `run.yaml`'s `config` is the **parsed dict**, so
writing it back loses every inline comment `init` wrote — the comments § The one config file calls
*"the documentation"* of the file. The run directory holds `config.yaml` as a byte copy.

**The answer: re-serialize from the record.** § Reproducing on another device says the two paths are
*"blanked and marked `# REQUIRED: set to your local copy`"* — core **writing a comment** means core
is generating the YAML, not patching someone else's. And the byte copy loses on three counts: it does
not exist in the bundle form (§ 0.6); locating two keys inside arbitrary YAML text to blank them is a
text scan over a structure, which is the proxy this repo keeps paying for; and a config the record
carries and a byte copy on disk can disagree, in which case the record is what produced the numbers.

**The write is self-checkable, and it is checked.** `covered_config` excludes `metadata`,
`data.input_dir` and `data.output_dir` (§ 0.9), so `parameters_hash` over the file just written must
equal the record's `parameters_hash` **exactly** — blind to the blanking, sensitive to a
re-serialization that drops or retypes a key. Mismatch → `E-REPRODUCE-CONFIG-WRITEBACK`, exit `1`.

**Two more reported facts, neither of them a refusal.** The clone already holds a tracked
`configs/<name>/config.yaml` at the recorded commit, so `reproduce` computes `parameters_hash` over
**that** file too and reports `identical` or `DIFFERS` beside `provenance.git.config_committed` — a
`DIFFERS` under `config_committed: true` is a real fact about the record. And the comment loss is
disclosed in the transcript, naming where the comments still live: the run directory's own
`config.yaml`, in the run-directory form, and nowhere in the bundle form.

### Decision 12 — step 6 is narrowed: `.env` is written from `.env.example` when absent, and `required_env` is listed only for a template this interpreter can construct

**The question.** § 0.10: an installed template's class is never constructed by this interpreter, and
a plugin is installed into the **clone's** environment by `uv sync`, not into `reproduce`'s. So
step 6's *"lists the `required_env` variables that need values"* cannot be built as promised for the
case it was written for.

**The answer.** Two halves, and the second is a document narrowing.

*`.env`.* `.env.example` is **tracked**, so the clone already holds it — "copies" means
`cp .env.example .env`, which is § The generated README's own setup line. `reproduce` writes `.env`
**only when it does not exist** and never overwrites one, and says so. It is safe: `missing_env`
treats an empty value as missing (§ 0.11), so a blank `.env` cannot turn a missing credential into a
present one. When `.env.example` is absent the line says that instead.

*`required_env`.* Listed where the template **resolves in this process** — core's `generic`, or a
project-local `templates/**` discovered by path in the checkout. For an installed, plugin-provided
template it is **not** listed; the transcript names the template and its plugin and defers to the
`validate` line it already prints, because `validate` in the prepared checkout **already reads
`required_env`** (H7c gave it that reader) in the interpreter where the plugin exists. The reader is
one step later and in the right place, which is better than a subprocess this command would have to
invent.

**Resolving a project-local template imports user code, and the containment is copied WHERE IT SITS.**
`report`'s credential leak came from lifting `freeze`'s calls without the `try` they sit inside; the
`sys.path` entry is removed **by identity**, never by `pop(0)`, and the restoration is pinned on the
failure path. Both are `CLAUDE.md` § Misreadings entries with this repo's own scars on them, and the
sibling that already got it right is `report.render_with_override`.

**Alternatives rejected.** *Shell into the clone* — core executing user code in a second interpreter
to read a declaration, when the command that already does it is printed two lines below. *Drop the
list entirely* — it is real and buildable for two of the three template homes. *Claim it and print
nothing for a plugin* — the documented-rule-with-no-code fault. **Cost if wrong:** a reader of a
plugin-backed record types one command to learn what `reproduce` could not tell them.

### Decision 13 — the config-operand form runs steps 4 onward in place, creates no directory, and says which verifications it is not making

**The answer.** Given a config, there is no remote, no commit and no recorded hash, so steps 1–3 have
no input and step 5 is moot — the config is already where it would have been written. What runs is
Decision 3's ranking against the **repo the config sits in** (found by walk-up from the config path,
never from the working directory), `uv sync --locked`, Decision 12's `.env` and `required_env`, and
the same closing instructions. It **names what it did not verify** — `code_hash`, the input manifest,
and the apparatus — rather than reporting a match it never made, which is § Reproducing's own
sentence and `diff`'s own rule for a config side.

No `apparatus.expected.json` is written: a config records no facts. No destination is derived and
nothing is cloned, so Decision 9's two refusals are unreachable from this form and the design says so
rather than leaving a reader to wonder.

### Decision 14 — eleven `E-REPRODUCE-*` codes and one `E-APPARATUS-*` are minted, no exit code is, and each row is placed by its table's own scope sentence

| Code | Raised by | Exit |
|---|---|---:|
| `E-REPRODUCE-OPERAND` | the operand is neither a record nor a config (a directory included) | `1` |
| `E-REPRODUCE-BUNDLE` | the operand is a `study.yaml`; the message lists its members | `1` |
| `E-REPRODUCE-NO-REMOTE` | `provenance.git.remote` is `null` | `1` |
| `E-REPRODUCE-DEST-EXISTS` | the derived destination exists | `1` |
| `E-REPRODUCE-DEST-IN-REPO` | the derived destination resolves inside a git repository | `1` |
| `E-REPRODUCE-CODE-HASH` | the checkout's `code_hash` differs from the record's | `1` |
| `E-REPRODUCE-UNLOCKED` | `uv_lock_hash` is `null` | `1` |
| `E-REPRODUCE-LOCKFILE-EDITED` | the byte copy's digest does not match `uv_lock_hash` | `1` |
| `E-REPRODUCE-LOCKFILE-UNREACHABLE` | no lockfile matching `uv_lock_hash` is reachable | `1` |
| `E-REPRODUCE-CONFIG-WRITEBACK` | the written config's `parameters_hash` differs from the record's | `1` |
| `E-REPRODUCE-EXPECTED-EXISTS` | `apparatus.expected.json` already exists | `1` |
| `E-APPARATUS-UNEXPECTED` | a probe contradicts `apparatus.expected.json` | `1`/`4` |

**Eleven `E-REPRODUCE-*` codes and one `E-APPARATUS-*`, twelve minted in total, twelve § Errors rows
— one row per code, covering every site that raises *or* reports it.** Each figure carries its noun,
because a count without one is not a claim anyone can check, and that is what made two of H9b's
figures disagree for a whole slice.

**No exit code is minted.** `1` is *"the thing you asked about is wrong"* and its row already
anticipates this class; `5` gains its **first reader** for the *"a clone or `uv sync` that failed"*
clause, which is `EXIT_EXTERNAL` acquiring a reader exactly as H7d Part B did; `E-APPARATUS-UNEXPECTED`'s
`1`-versus-`4` split is `run_status`'s shipped fold, derived rather than chosen, the same derivation
H9b recorded. `E-IO-FAILED` covers an unreadable operand path, joining `diff`'s and `resume`'s
precedent rather than getting a thirteenth code.

**Row placement.** All twelve go to § Errors **core raises** — none is reported by `validate`, which
never dispatches `reproduce`. `E-APPARATUS-UNEXPECTED` sits with the other five `E-APPARATUS-*` rows.

### Decision 15 — `reproduce` walks no lineage chain, and the upstream-hash filing is declined with its reason

`spec-defects.md`'s entry on `UpstreamLedger.record` reading `record.get("code_hash")` names **H9** as
owner, on the ground that `reproduce` *"walks a resolved `run_id` back through its own recorded
ancestors."* Re-read against § Reproducing on another device: **it does not.** Its seven steps read
one record's `git`, `environment`, `config` and `apparatus`; `provenance.upstream` is named in none of
them, and `io.reuse_from`'s own reader is the consumer that would observe a silently-`None` hash.
Declined, and re-owned to **unassigned with the reason** — H9d is `demo`/`docs`/`list-templates` and
H3c-3 is folds inside cells, so there is no successor to name and saying so is the honest record.

---

## 3. Where this design disagrees with the scoping and the record

Reported individually and attributed, never counted — six consecutive slices claimed zero and all six
were wrong.

1. **The scoping's § 11 says `reproduce` might "read `uv_lock_hash` to date the record"** across the
   H6a boundary. Measured: it cannot in general — a scaffolded project's `uv_lock_hash` is `null`, and
   the lockfile is the carrier only where one exists. Kept as one of Decision 2's candidate causes
   rather than as a mechanism.
2. **The scoping's H9c task 5 says "one git operation."** It is **two** — clone, then a detached
   checkout — and each needs its own `-c core.autocrlf=false` (§ 0.4, Decision 7). The document's own
   step 2 says *"The only git operation"* in the singular; the design keeps the document's *spirit*
   (you typed none of it) and states the count.
3. **§ Reproducing on another device's "it can't collide with an existing checkout" is false**
   (Decision 9). A second `reproduce` of one record derives the same name.
4. **§ Reproducing on another device step 6 cannot be built as written** for a plugin-provided
   template (§ 0.10, Decision 12) — the same class as `dry-run`'s greenfield collision, and not named
   by the scoping.
5. **A faithful clone's `code_hash` depends on machine-local git configuration** (§ 0.4) and, under a
   tracked `.gitattributes`, on how the working tree was materialized (§ 0.5). Stated in no document,
   no filing and no scoping. New here, and filed.
6. **`provenance.environment` names `uv_lock` and no `pyproject.toml`** (§ 0.7), though the run
   directory holds both — so a reader of `run.yaml` alone cannot know the second copy exists, and a
   bundle member references a lockfile path that is not in the bundle (§ 0.6). Two asymmetries, one
   cause: `provenance` records run-directory-relative paths that survive redaction unredacted.
7. **The upstream-hash filing's ground is false of `reproduce`** (Decision 15).
8. **`spec-defects.md`'s two-`required_env`-readers entry says the `reproduce` half is
   "`reproduce`'s slice"** — it is this one, and Decision 12 discharges **half** of it and narrows the
   other half. The entry is amended rather than struck.

---

## 4. What this slice refuses to build, each with route and owner

**H3c-3's remaining 14 is the only slice after H9d.** Anything declined here that H3c-3 does not own
is unowned, and saying which is which is part of the deliverable.

| Not H9c's | Where it goes |
|---|---|
| `demo`, `docs`, `list-templates` | **H9d.** `demo`'s stop 6 *prints* `reproduce` rather than running it, so it needs this slice and not the reverse |
| A lockfile inside a study bundle | **Filed against `study add`, owner named** (§ 5, item 4). `study`'s bundle contents are H8c's surface; widening them here is charter growth |
| A `pyproject_hash` or any fourth environment key in `provenance` | **Refused by ruling** — H6a Decision 12 / Ruling E: `uv.lock` is the carrier. Decision 3 compares the byte copy it already has |
| A marker for the hash definition in `run.yaml` | **Refused by ruling** — H6a Ruling C, and the scoping's § 12 names it |
| Promoting `W-ENV-UNLOCKED` to a refusal | **Decided against** (Decision 5), not deferred. The entry is closed |
| `resume`'s `identity.json` comparison, extended to `reproduce` | **Not applicable, stated so it is not folded in.** `identity.json` is a run-directory artifact for a *mid-run* reader; `reproduce` reads a *finished* record, where `run.yaml` carries all three figures. Using it would make the bundle form impossible |
| Re-drawing or verifying `allocation.json` in the checkout | **Out of scope by document**: § Reproducing prepares a checkout and stops; the roster is resolved by the `run` the user then types, against data core will not fetch. A bundle carries no `allocation.json` **by H8c's own ruling**, whose route is `allocation_hash` |
| `diff`'s `uv.lock` row naming the package whose pin moved (Q5) | **Filed, owner H9d.** Decision 3 answers *which* lockfile is authoritative, which is the input Q5 was waiting on; rendering per-package detail lines is `diff`'s surface, and H9d is the only remaining slice with a CLI surface |
| The bytecode-cache defect at three call sites | **H9d**, per the later of the two dated records (`spec-defects.md`, 2026-08-23). Decision 12 imports a project-local template in the **checkout**, a fresh directory that cannot hold a stale `__pycache__`, so this slice inherits no new exposure |
| `BaseTemplate.field_convention`'s missing reader | **Unassigned.** Re-verified at `a628707`: three hits in `src/`, none a reader. H9c creates no new one |
| `report_by` under `resample` keeping a `t_over_units` interval | **Unassigned**, filed against H4. `reproduce` renders no intervals at all |
| `max_failed_fraction`'s truncation status semantics | **Unassigned**, filed by H7d Part B with a written justification in a shipped test's docstring. Decision 4 must not weaken it to make a reproduction's status tidier |
| Folds and holdouts inside cells, `E-DATA-HOLDOUT-CELLS`, `E-REPL-FOLD-CELLS` | **H3c-3's remaining 14** |
| Widening `E-CODE-DIRTY`'s pathspec to the repository root | **Declined and unassigned** (H6b Decision 12). Decision 3 *reports* an uncommitted `pyproject.toml`; it does not gate on one, and those are one line apart |

---

## 5. Filings this slice makes or closes

1. **CLOSED** — *Whether a missing `uv.lock` should refuse the run instead of warning is unresolved*
   (Owner: H9). Decision 5 decides it: affirmed, with the § Design goals footnote the entry proposes.
   Struck.
2. **AMENDED** — *two specified readers of `required_env` belong to unbuilt commands*. The
   `reproduce` half is discharged for the two template homes this interpreter can construct and
   **narrowed** for the third (Decision 12); the `dry-run` half landed with H9a.
3. **NEW** — *a tracked `.gitattributes` carrying a `text`/`eol` attribute makes `code_hash` a
   property of how a working tree was materialized rather than of the commit.* Reproduction recipe
   inline: commit `* text eol=crlf`, clone with `core.autocrlf=false`, and the clone hashes `d37416e`
   where the never-re-materialized original hashes `0cc6ddd`. **Owner: unassigned, with the reason** —
   no remaining slice (H9d's three commands, H3c-3's folds) has `hashes.py` or § How the three are
   computed as its surface, and H6 is complete. Decision 7 states why `reproduce` may not override it.
4. **NEW** — *a study bundle carries no lockfile, so a bundle member whose project never committed
   one cannot be reproduced from the bundle alone.* Measured at § 0.6: the member's
   `provenance.environment.uv_lock` is a dangling `environment/uv.lock`. **Owner: unassigned, with the
   reason** — `study add`'s bundle contents are H8c's surface and H8c is complete; H9d is
   `demo`/`docs`/`list-templates`. The check its closer must make is stated: whether `study add`
   should copy `environment/uv.lock` into the bundle, or whether `provenance.environment.uv_lock`
   should be redacted in a bundle member the way `input_manifest` already is, so the dangling
   reference is at least visible.
5. **NEW** — *`provenance.environment` names no `pyproject.toml`*, though `run` writes
   `environment/pyproject.toml` at run start (§ 0.7). **Owner: unassigned, with the reason** — H6 is
   complete and Decision 3 finds the file by convention rather than by record.
6. **DECLINED and RE-OWNED** — the `UpstreamLedger.record` `.get` filing (Decision 15).

---

## 6. Is this additive? — the disclosure

**`reproduce` is new, and one thing it needs changes a shipped command.** H9b added two artifacts and
had to disclose both; H8b's Decision 7 was additive-only and said so. This one is **additive-only in
the H8b sense, and the boundary is stated rather than asserted.**

| # | What changes | Additive? |
|---:|---|---|
| 1 | `run`'s probe gate gains a second comparison, against `configs/<name>/apparatus.expected.json` when that file exists (Decision 4) | **Yes, conditionally.** No run of any project that does not hold that file can reach it, and no shipped code writes one. No existing key, verdict, status or exit code moves for any run without it |
| 2 | `STOP_CODES` gains a third member | **Yes.** Its set-equality assertion is a guard-pin arm with the post-edit state written in advance (arm D) |
| 3 | `reproduce` leaves `NOT_BUILT_COMMANDS` and joins `OPERATION_COMMANDS` | **Behaviour change to two shipped invocations**, and item 5 of this list |
| 4 | `provenance.apparatus` gains **no key** naming the expectation | **Nothing moves.** H6a Ruling C's refusal of a definition marker is the precedent: the reproduction's record carries the facts it **observed**, and a key naming what it was compared against would be a second source of truth for a comparison the checkout's own file already holds |
| 5 | `publishable reproduce <path>` stops printing *"specified but not built"* (exit `2`) and starts dispatching. **`publishable reproduce new` dispatches into the command with `new` as its path** — `new` is a single token, so the arity arm is never reached and the two-token `NOT_BUILT_COMMANDS` lookup never happens — and prints `E-IO-FAILED` at exit **1**. Exit `2` → `1`, and the identifier is new | **Behaviour change, disclosed and pinned rather than only disclosed.** H9a got the analogous `draft new` claim wrong three ways and H9b then measured its own; this one is measured through the real console script in the dispatch task and its four shapes are asserted |
| 6 | No run directory is written into, ever | **Nothing moves**, and it is pinned by a whole-filesystem snapshot arm (arm G) rather than by reading for absent writes |

**The file's location keeps item 1 inside the boundary, and the ground is a measurement rather than
the pathspec.** `configs/<name>/apparatus.expected.json` sits outside `src/**` and `templates/**`, so
neither `code_hash` nor the dirty gate sees it — **cited from § 0.1's own measurement**, where an
untracked `uv.lock` at the repo root left `git status --porcelain` reading `?? uv.lock` and the run
exiting `0`. Reasoning from the pathspec alone would be answering with a proxy; the run was actually
performed.

---

## 7. Does § Executability on this build move? — derived

**No, and no fifth number is minted.** Derived rather than carried:

- **`reproduce` does not run at `validate` and is not invoked from a step**, so no config's
  validation outcome can move. The one figure `validate` can see — *transplantable configs validating
  with zero errors, 8 of 8* — is untouched.
- **None of the nine configs is a run record**, so none of them is an operand `reproduce` accepts;
  and none declares a `study`, so no bundle member exists to reproduce from.
- **None of the nine declares an `apparatus_probe`** — `generic` is the template they validate
  against — so Decision 4's new comparison and `E-APPARATUS-UNEXPECTED` are unreachable for all nine,
  exactly as H7d Part A's and Part B's apparatus work was.
- **Twelve codes are minted and none is retired**, and every one is reachable only from `reproduce`
  or from a `run` whose config directory holds a file only `reproduce` writes.

So the four-row table is **repeated character for character**, by the two independent extraction
methods the H8a and H9a entries describe, and its cells still name **H8a**, because updating them is
exactly how a repeated table stops being repeated. **Quote the table, or name the dependency** — do
not quote a single figure for this analysis' executability.

**One behaviour change worth naming even though it moves no row**: exit `5` gains its first reader
for the *"a clone or `uv sync` that failed"* clause, and `run` gains a refusal it cannot reach
without a file this build could not previously produce.

---

## 8. The guard pin

Captured in **batch 1, before any code moves.** Every arm names a sole authorized editor or an
explicit **NONE**, and every authorized post-edit state is written **now** — H6a captured against a
superseded signature and forced an unauthorized edit; H6b, H9a and H9b captured forward and their
edits matched the advance spec byte for byte. **An implementer may not self-authorize an arm edit. The
route is a controller ruling, and leaving the branch red is correct** — H9a task 2 did exactly that,
and H9b's batch 1 re-aimed only a *clause* and **stated the discrepancy** rather than the assertion,
which is the third and right option.

**Captured in the shape this design has already decided**, which is the point of writing § 1 and § 2
first: three slices running have proved that works, and H6a proved the alternative forces an
unauthorized edit.

| Arm | What it holds | Authorized editor |
|---|---|---|
| **A** | **A completed `run`'s `run.yaml` leaf by leaf, its run tree path by path, and its full stdout** — H9a arms A and B and H9b arm A, **cited, not re-captured.** Re-capturing would recreate H8a's *same list pinned twice*, which a later task then edited in both places. They are what Decision 4's "nothing moves for a run without the file" is measured against | **NONE** |
| **B** | `test_reference_cli_tables_are_parsed_at_all`'s shipped `assert ("reproduce", "NOT BUILT") in tables["Command"]` — placed there by H9b task 15 **as a marked row-presence probe**, so it must be replaced rather than deleted. Post-edit state, written now: that line becomes `("reproduce", "built")` **and** a line `assert ("list-templates", "NOT BUILT") in tables["Command"]` is added, keeping one marked probe. The `set(NOT_BUILT_COMMANDS)` equalities beside it are **self-maintaining and must not be edited** | **The dispatch task only** (plan task 11) |
| **C** | `apparatus.STOP_CODES`'s set-equality assertion in `tests/test_apparatus.py`. Post-edit state, written now: `{"E-APPARATUS-RAISED", "E-APPARATUS-CHANGED", "E-APPARATUS-UNEXPECTED"}` — one member added, none removed, nothing reordered | **The `run`-side reader task only** (plan task 9) |
| **D** | `assert "E-APPARATUS-CHANGED" not in APPARATUS_CODES` and `assert "E-APPARATUS-RAISED" in APPARATUS_CODES`. **Both assertions are NONE.** Task 9 may **add** a sibling `assert "E-APPARATUS-UNEXPECTED" not in APPARATUS_CODES` beside them; adding an assertion is not editing one, and this clause exists so nobody reads the addition as a self-authorized edit | **NONE** for the two shipped assertions |
| **E** | **`reproduce` writes nothing outside its derived destination.** A whole-tree `{path → sha256}` map of the run directory, the operand's own tree, and the source repository, before and after the command, asserting ADDED/REMOVED/CHANGED all empty. **Established by snapshotting rather than by reading for absent writes** — H9a's `dry-run` arm is the precedent, and *if a comment says nothing is created, make it create something* is the rule | **NONE** |
| **F** | `tests/test_cli.py`'s shipped assertion that `W-ENV-UNLOCKED`'s message contains *"`reproduce` will not be able to restore it"*. **Decision 5 affirms the warning, so this arm must not move**, and it is the arm that pins Decision 5 against a later slice quietly promoting it | **NONE** |
| **G** | Already pinned elsewhere and **not re-captured**: H8b arm B (`environment/`'s contents), H8a arms A and B (`run.yaml`'s and `provenance`'s key lists — Decision 4 adds no `provenance` key, item 4 of the disclosure), H9b arm B (the run directory's root list — `reproduce` adds no run-directory artifact), H9b arm D (`dry-run`'s fixed-file count), `sweep.yaml`'s key list, and H9a arms C and E (the four exit codes and the four early exits) | **NONE.** Cited so a reviewer does not read the absence as missing coverage |

**Every arm must be proven able to fail** before batch 1 is reviewed, by a mutation in the
**production** code — not by reading. **Report every mutation count against the full suite**, and say
so: nine of the last five slices' miscounts were single-test-scoped numbers reported as suite-wide.
**And proving an arm cannot move is not proof the line is pinned** — an arm offered as evidence that
an edit is safe *because it cannot see the edit* is two opposite facts wearing one sentence.

---

## 9. Fixtures as claims

Every literal is computed, and the method is named. A fixture whose numbers agree with the bug is
this repo's most frequent single defect.

**The clone is a fixture, and its recipe is stated because a clone is exactly where determinism is
easy to assume.** Reproducibility is a property of *contents*: `code_hash` folds `(relative path,
sha256 of contents)` pairs, and it never reads an mtime, a mode bit or an owner — which is why the
recipe below is deterministic while the clone's *filesystem metadata* is not. Checked by running it:
`0cc6ddd` on both sides over the same six files (§ 0.2), and again as `0cc6ddd` under an ambient
`core.autocrlf = true` with Decision 7's override (§ 0.4).

| Fixture | The claim | How every literal is obtained, and why it can fail |
|---|---|---|
| **A** — the source repository | A real repo with a real remote, at a recorded commit | **Built, not synthesized.** A `publishable new` scaffold plus one `generate experiment` (`generic`, 6 CSV units, 2 seed repeats) **outside this repository**, committed; then `git clone --bare` of it into a sibling path and `git remote add origin <that path>`, so `provenance.git.remote` is a **real, cloneable URL** rather than `null`. A local bare repo is used deliberately: a fixture that reaches the network is a fixture that fails on a build machine, and `git clone` treats a path and a URL identically |
| **B** — the recorded run | An operand with every figure real | `run` against Fixture A with a lockfile present. The `uv.lock` is **written by the fixture, not resolved** — a scaffolded project cannot resolve one (§ 0.1, Decision 5), so `uv lock` is not part of any recipe here. Its digest is read back out of the record rather than asserted as a literal, and `code_hash`'s literal is **not** hard-coded: it is compared against `hashes.code_hash_of(hashed_files(...))` computed in the test, since a commit SHA and everything derived from it cannot be a stable literal — H9a's self-caught defect, an arm compared against its own read-back, is the shape avoided |
| **C** — the plain clone | Step 3 passes on a faithful clone | The **negative control** for Fixture D, and it must exist: a positive control alone proves nothing about the success path (*a parametrized test asserting a failure for both arms*). Asserts `code_hash` **equal** and the reported file count `6` |
| **D** — the rewritten file | Step 3 fails when the code moved | The recorded commit is **rewritten** in the source repo after the run: one byte changed in `src/pilot/experiment.py`, `git commit --amend`, then the original SHA force-updated onto the amended tree, so `git.commit` still resolves and holds different bytes. That is what a rewritten history **is**, and it is why the fixture does not simply add a second commit — a second commit leaves the recorded SHA reachable and correct, the clone passes, and the arm tests nothing. Asserts the code, the two digests, and that the checkout was **kept** |
| **E** — the `autocrlf` clone | Decision 7's override is load-bearing | Ambient `core.autocrlf = true` through `GIT_CONFIG_GLOBAL` pointing at a throwaway file — the same instrument H6a's batch 1 used, and it must be set that way rather than through the user's real config. **Two arms, one per flag**: with the override, `0cc6ddd`; with it removed, `d37416e`. Both literals computed by running (§ 0.4). A **third** arm asserts `core.eol=lf` is absent from the invocation, since a flag with no arm is a flag nobody can prove is doing anything |
| **F** — the bundle member | The bundle form works, and its two degradations are reported | `study new` + `study add` over Fixture B, then `reproduce bundle/main.run.yaml`. Asserts the clone happened (the remote survives redaction — measured, § 0.6), that `environment/uv.lock` was **not** reached, and that the lockfile line names the recorded digest. **The arm that makes Ruling Y's cost-if-wrong a test rather than a sentence** |
| **G** — the bundle with no committed lockfile | `E-REPRODUCE-LOCKFILE-UNREACHABLE` | Fixture F with the source repo's `uv.lock` left **untracked**, which is the shape § 0.1 measured. The refusal's message must name the recorded digest **and** that the clone holds none — a message asserting only the code would pass if it named neither |
| **H** — the bundle whose lockfile **is** committed | Step 3's success arm | The same, with `uv.lock` committed at the recorded commit. **Without this arm Fixture G tests only that something refused**, and the two readings *"a bundle can never sync"* and *"a bundle syncs when the lockfile travels with the commit"* would be indistinguishable |
| **I** — the disagreeing lockfile | The clone's lockfile is reported, not silently used | The source repo commits a lockfile whose bytes differ from the one the run recorded. Asserts the checkout's `uv.lock` is byte-equal to the **recorded** copy and that a `DIFFERS` line named the clone's. **Two branches that can differ by construction**, which the single-lockfile fixtures cannot supply |
| **J** — the moved `pyproject.toml` | Decision 3 step 4 reports it before `uv sync` speaks | Built by the § 0.7 recipe: an uncommitted edit to `pyproject.toml`, the run performed (exit `0`, ` M pyproject.toml`), then reproduced. Asserts a `DIFFERS` line **and** that it precedes the `uv sync` line in the output — the ordering is the whole point of the row |
| **K** — `remote: null` | `E-REPRODUCE-NO-REMOTE`, and the recorded commit is named | The scaffolded project with no `origin`, which is § 0.8's measured default state. Asserts the code, exit `1`, that **no directory was created**, and that the message contains the recorded commit — a refusal that told the reader nothing is a refusal with no remedy |
| **L** — `uv_lock: null` | `E-REPRODUCE-UNLOCKED`, checkout kept | Fixture A with no `uv.lock` at all, which is every scaffolded project (Decision 5). Asserts the code, exit `1`, **and that the destination exists and holds the checked-out tree** — a refusal arm asserting only the code would pass identically if the checkout were discarded, which is the behaviour Decision 6 exists to specify |
| **M** — the config write-back | The written config is faithful, and the comparison against the committed one is real | Asserts `hashes.parameters_hash` over the written file **equals the record's**, computed by calling the function rather than by literal; that `data.input_dir` and `data.output_dir` are the blank-plus-marker form; and, on a second arm where the config was edited after being committed, that the `DIFFERS` line against the clone's committed copy fires. **The second arm is what makes the comparison non-vacuous**: with `config_committed: true` and no edit, `identical` is the answer whether the code compares anything or not |
| **N** — the config operand | Decision 13's form | `reproduce configs/pilot/config.yaml` inside Fixture A. Asserts no directory created, `uv sync` reached, and that `code_hash`, the input manifest and the apparatus are each **named as not verified** — three positive assertions, because *a control asserting only absences passes identically if nothing ran* |
| **O** — the apparatus expectation, written | Decision 4's first half | A project-local template declaring an `apparatus_probe`, and a probe distribution installed, so `provenance.apparatus.facts` is real and **has two conditions with different facts** — one condition is not enough to tell a per-condition write from a flattened one. Asserts the file's parsed content equals the record's `facts` **mapping for mapping**, and that a second `reproduce` into a destination already holding one refuses `E-REPRODUCE-EXPECTED-EXISTS` |
| **P** — the apparatus expectation, honoured | Decision 4's second half, on the gate's own terms | Four arms over one probe whose answers come from a file the fixture rewrites: a **moved value** fails `E-APPARATUS-UNEXPECTED`; `null → value` **passes**; `value → null` **passes**; and a fact present for one condition and absent for the other is compared **per condition**. The four cannot be collapsed: three of them are the asymmetry § Reproducing on another device calls *"more evidence rather than less"*, and a fixture with only the failing arm would leave every tolerance untested |
| **Q** — the reproduction's own record | No `provenance` key names the expectation, and the counts are the run's own | The `run` of Fixture P's checkout. Asserts `provenance.apparatus.facts` holds the **observed** values, `unobserved`'s `total_probes` equals the probes this run actually made, and `provenance`'s key list is unchanged. **The arm that catches Decision 4's rejected alternative**: seeding the run's own `Observations` would inflate `total_probes` while every other assertion stayed green |
| **R** — the credential positive control | A project-local template raising at import prints `<redacted:…>` | The credential is declared through `Param(requires_env=)` and **set in the environment**, so the redaction has a real value to match — an undeclared one would pass vacuously. This is `report`'s own leak reproduced against `reproduce`, and its control is the same one that caught it: `validate` over the identical project printing `<redacted:…>` |
| **S** — the operand discrimination | Decision 1's five verdicts | Five arms: a run directory (`E-REPRODUCE-OPERAND`, message naming `<dir>/run.yaml`), a `study.yaml` (`E-REPRODUCE-BUNDLE`, message listing **both** members — a one-member bundle cannot distinguish "lists members" from "names the first"), a `run.yaml` with `run_id` deleted (`E-REPRODUCE-OPERAND`, **not** read as a config), a YAML list, and a missing path (`E-IO-FAILED`) |
| **T** — the destination guards | Decision 9's two refusals | A pre-existing destination directory, and a working directory inside a git repository. The second asserts the walk-up is from the **destination's parent** and not from the operand, by placing the two in different repositories — a fixture with one repository cannot tell the two readings apart |

---

## 10. Mutations

Each is named with the assertion that catches it, and **each was checked in advance for two branches
that can differ** — a mutation is a claim like any other, and a reviewer has proposed one whose
branches were a mathematical no-op.

| Mutation | Caught by | Two branches differ? |
|---|---|---|
| Drop `-c core.autocrlf=false` from the clone invocation | Fixture E arm 1 | **Yes, and measured**: `0cc6ddd` → `d37416e` under the ambient setting the fixture installs (§ 0.4) |
| Drop it from the leading `git -c` but keep `clone -c` | Fixture E arm 2 | **Yes, and measured**: the stored config read `false` and the checkout was still CRLF (Decision 7) |
| Add `-c core.eol=lf` back | Fixture E arm 3 | Yes — the arm asserts the invocation's flag list, and § 0.4 shows the flag changes nothing, so an assertion on the *hash* would be blind. This is the arm that would otherwise be a proxy |
| Discriminate the operand by basename (`endswith("run.yaml")`) | Fixture F | Yes — the bundle member is `main.run.yaml`, so the mutation refuses the arm Ruling Y exists for |
| Read a `run_id`-less mapping as a config | Fixture S arm 3 | Yes — that arm's file has `provenance` and `results` and no `run_id`, so the two readings give a refusal and a config-form run |
| Prefer the clone's lockfile over the byte copy | Fixture I | Yes — I's two lockfiles differ by construction, so the checkout's bytes differ |
| Use the byte copy without checking its digest | a Fixture I arm with the copy edited after the run | Yes — the edited copy's digest no longer matches `uv_lock_hash`, so one path refuses and the other syncs |
| Accept the clone's lockfile in the bundle form without comparing digests | Fixture G | Yes — G's clone holds none, so the comparison is what produces the refusal; and Fixture H is the arm proving the *success* path is not simply unreachable |
| Skip the `pyproject.toml` comparison | Fixture J | Yes — J's two copies differ, and the assertion is on the line **and its position** before `uv sync` |
| Compare `code_hash` with `include=None` instead of the git-aware predicate | a Fixture C arm with a git-ignored file under `src/` | Yes, and measured: `0cc6ddd` versus `bdf2ce9` (§ 0.3). Without that ignored file the two predicates agree and the mutation is blind — which is exactly how a fixture whose numbers agree with the bug happens |
| Report a `code_hash` difference as *"a rewritten or force-pushed history"* | Fixture D | Yes — the arm asserts the enumeration is printed and that the phrase naming a single cause is **absent**. An assertion on the code alone would pass under both wordings |
| Refuse a `draft` record instead of declining the verification | a Fixture B arm run under `draft` | Yes — one path exits `1` with no checkout preparation past step 3, the other reaches the closing transcript at exit `0` |
| Discard the checkout on `E-REPRODUCE-UNLOCKED` | Fixture L | Yes — L asserts the destination **exists and holds the tree**, which a code-only assertion could not see |
| Write the config from the byte copy | Fixture F | Yes — the bundle form has no byte copy, so the mutation cannot produce a config at all there |
| Skip the `parameters_hash` check on the written config | a Fixture M arm whose record's `config` has one key retyped by the fixture | Yes — the arm makes the round trip lossy on purpose, so the check fires or does not |
| Seed the run's own `Observations` from the expectation instead of a second one | Fixture Q | Yes — `unobserved.total_probes` inflates by one per condition per expected fact, while every arm of Fixture P stays green. **This is the mutation the naive implementation IS**, which is why Q exists |
| Compare the expectation with `!=` instead of `Observations.changed` | Fixture P arms 2 and 3 | Yes — `null → value` and `value → null` fail under `!=` and pass under the gate's rule |
| Compare the expectation against the run's whole `facts` rather than per condition | Fixture P arm 4 | Yes — P has two conditions with **different** facts, so a flattened comparison reports a change that per-condition scoping does not |
| Reuse `E-APPARATUS-CHANGED` for the expectation mismatch | Fixture P arm 1 | Yes — the arm asserts the identifier, and the two codes have different § Errors rows and different remedies |
| Add `E-APPARATUS-UNEXPECTED` to `APPARATUS_CODES` | arm D's addition plus Fixture P arm 1 | Yes — the containment filter would then swallow it instead of the loop breaking on it, changing the exit code from `1`/`4` to the filter's re-raise |
| Remove `E-APPARATUS-UNEXPECTED` from `STOP_CODES` | Fixture P arm 1 | Yes — the loop would continue past the contradiction and the run would finish `completed` |
| Copy Decision 12's calls without the enclosing `try` | Fixture R | Yes — R's declared credential reaches stderr verbatim on one path and `<redacted:…>` on the other. **`report`'s own shipped leak, and its own control** |
| Remove the `sys.path` entry with `pop(0)` | a Fixture R arm whose project-local template does its own `sys.path.insert(0, …)` at import | Yes — the pop removes the wrong entry and the next resolution in the same process sees the leaked `src/`. Without the inserting template the two are indistinguishable, which is the fixture the shipped defect lacked |
| Walk up from the operand rather than the destination's parent for `E-REPRODUCE-DEST-IN-REPO` | Fixture T arm 2 | Yes — the two live in different repositories by construction |
| Print the members' count instead of their names for `E-REPRODUCE-BUNDLE` | Fixture S arm 2 | Yes — that bundle holds **two** members, so a count and a list differ; a one-member bundle would make them agree |
| Overwrite an existing `apparatus.expected.json` | Fixture O arm 2 | Yes — the second `reproduce` writes or refuses |
| Replace `isinstance(...)`-style structural checks at `command_reproduce`'s early exits with truthiness | **Named blind in advance** — `0` is the only `int` a swap mishandles and no early exit returns `EXIT_OK` | **No. Owed a replacement**: the rule is stated once in `command_reproduce`'s docstring, `mypy` is the enforcer, and H9a arm E pins the early-exit codes end to end. **The same mutation was named blind by H9a and by H9b and the reason is unchanged** — repeated rather than re-derived |
| Neutralize `core.excludesFile` in the clone | **Named blind in advance** — the `.gitignore` files that decide `code_hash` are tracked and travel with the commit, so a fresh clone has no untracked exclude rule for the flag to reach | **No. Owed a replacement**: the non-use is asserted **structurally** — a test asserting the clone invocation's flag list is exactly `("-c", "core.autocrlf=false")`, which is arm 3 of Fixture E and is the same device that arms the dropped `core.eol` |

---

## 11. Batching

**Fifteen tasks in seven batches, every batch reviewed.** The count is what the tasks came to, not a
figure aimed at the scoping's 11 — the scoping predicts a plan exceeds its own count, and merging
tasks to hit a number is the failure mode that prediction is about.

| Batch | Tasks | Why together | Review |
|---:|---|---|---|
| **1** | 1 | The guard pin, before anything moves — including arm B's and arm C's re-authorizations | Every arm proven able to fail by a **full-suite** mutation, with the count reported as such |
| **2** | 2, 3 | The operand reader and the clone — Rulings Y and Z's first halves, and nothing yet writes | Fixture S's five verdicts; Fixture E's three arms with the ambient setting installed |
| **3** | 4, 5, 6 | `code_hash`, the lockfile ranking, `uv sync` — **the three questions the charter said this slice decides**, and they read one record together | Fixtures C, D, G, H, I, J, L. **The batch where a mutation's two branches must be shown, not argued** |
| **4** | 7, 8 | The config write-back and step 6 — the two things written into the checkout, and both import or re-serialize something | Fixture R and its `pop(0)` arm, through the **real console script**: a credential leak is not visible to a direct call that never reaches `main` |
| **5** | 9, 10 | **The behaviour-change batch.** Task 9 is `run`'s new comparison and task 10 is the writer it reads from | **A real-command review**, on the `no expected file` path: `run.yaml` leaf by leaf against a `main` worktree, normalization list written in advance, every remaining difference attributed. Green tests are not the evidence |
| **6** | 11, 12, 13 | Dispatch, the config-operand form, and the closing transcript — `reproduce` becomes reachable here | **All four invocation shapes measured through the real console script**, and disclosure item 5 corrected if any differs. H9a got this wrong three ways for `draft new` |
| **7** | 14, 15 | The documents, `spec-defects.md`, `CLAUDE.md`, § Executability, both consistency passes | **The batch with no review is where the findings will be**; this one is reviewed, and three of one gate's four Majors lived in exactly such a task |

**Batch 5 is the behaviour change**, and it is reviewed against a real command rather than against
the suite — the split this project has taken three times (H8b Decision 7, H7d Part B, H9a batch 2).
Batch 3 is the slice's centre of gravity and is where its charter is discharged.

---

## Appendix — corrections appended 2026-08-24, before dispatch

Appended rather than edited, so the dated measurements in §§ 0–11 stay as they were made. Four items;
two of them change a mechanism and one changes a count, so **every task section they touch carries the
same correction appended in the plan** — a ruling that lives only in a design is one an implementer
re-derives.

### C1 — Fixture D is **not constructible as written**, a rewritten history is caught at the **checkout** rather than by the hash, and a thirteenth code follows

**The recipe was impossible.** § 9's Fixture D said *"the original SHA force-updated onto the amended
tree, so `git.commit` still resolves and holds different bytes."* **A commit SHA is a hash over its own
tree, parents, message and metadata**, so a different tree cannot live at the same SHA; `git update-ref`
moves a ref, not an object. Measured: amending the fixture commit produced a **new** SHA
(`fcc45b7…` → `ff45afe…`) and left the original's tree untouched, so checking the recorded SHA out gives
the recorded bytes and the comparison **passes**. `E-REPRODUCE-CODE-HASH` would have shipped with no
fixture that reaches it.

**Fixture D becomes two constructible arms, and neither is a rewritten history:**

- **D1 — the H6a boundary, which is the case Ruling Z exists for.** The record's `code_hash` is set to
  the **pre-H6a** figure, computed in the test by `hashes.code_hash(root, None)` over the same tree that
  holds a git-ignored file under `src/` — measured at `bdf2ce9` against the post-H6a `0cc6ddd` (§ 0.3).
  Both literals computed by calling, never hard-coded. This arm is also what pins Decision 2's
  enumeration, because it is a difference with **no** wrongdoing behind it.
- **D2 — a tampered record.** `code_hash` edited to an arbitrary digest. The plain case, and the one that
  proves the comparison reads the record rather than its own recomputation.

**And the finding underneath it: § Reproducing on another device's step 3 is wrong about *where* a
rewritten history is caught.** A force-pushed history makes the recorded commit **unreachable**, so the
failure lands at the **checkout** — task 3 — and never reaches the hash comparison at all. Measured:
after an amend, `git clone --no-local` of the intermediate bare repo does not carry the old object
(`git cat-file -t` fails) and `git checkout --detach <recorded-sha>` fails
`fatal: unable to read tree`. So a **thirteenth** code is minted, `E-REPRODUCE-COMMIT-UNREACHABLE` at
exit **`5`** — the clone-and-checkout half of code `5`'s documented meaning, whose message names the
recorded commit and says the remote does not hold it. **That is the honest home for step 3's claim**, and
Decision 2's enumeration keeps *"a rewritten or force-pushed history"* as a candidate cause only for the
narrower case where the SHA still resolves and the tree differs — which, per the paragraph above, means a
record whose `code_hash` no longer matches its own commit.

**A trap for the fixture author, measured, in a currency this repo has not paid in yet.** `git clone` of
a **local path** hardlinks the whole object database, **unreachable objects included** — so a fixture
built on a local-path remote (which § 9's Fixture A is, deliberately, so nothing reaches the network)
**cannot reproduce the unreachable-commit state at all**: the checkout succeeded in the measurement
above. The recipe needs a bare intermediate cloned with **`--no-local`**, and a fixture built the obvious
way would pass while testing the opposite state. *A fixture whose numbers agree with the bug*, in git's
currency rather than in arithmetic. **`reproduce` itself passes no `--no-local`** — that would break the
legitimate local-remote case and slow every clone; the flag belongs to the fixture, not to the command.

### C2 — Decision 4's mechanism is `record(incoming)` **then** `changed(incoming)`; calling `changed` alone on a seeded `Observations` raises `AssertionError` on three cases, one of which the document says must pass

**Decision 4 said "asked only for `changed`". That is false of the shipped class**, and the measurement
is the whole correction. `Observations.changed`'s `assert` rests on a caller contract its own docstring
states — *"`record` runs before `changed` for the same `facts`"* — which holds for a run's own object and
**does not hold for an object seeded from a foreign record**, where `record` saw the *recorded* facts and
`changed` sees the *incoming* ones. Measured on a seeded object, `changed` alone:

| Case | `changed` alone | `record(incoming)` then `changed(incoming)` |
|---|---|---|
| a moved value | `('a', 'x', 'w')` — correct | `('a', 'x', 'w')` — correct |
| **`null → value`** | **`AssertionError`** | `None` — **passes**, as § Reproducing requires |
| `value → null` | `None` | `None` |
| the incoming probe lacks an expected fact | `None` | `None` |
| **an extra incoming fact** | **`AssertionError`** | `None` |
| **a condition the expectation does not carry** | **`AssertionError`** | `None` |
| per-condition scoping (`01` expects `p`, sees `x`) | `('a', 'p', 'x')` | `('a', 'p', 'x')` — correct |
| a constant `nan` | `None` | `None` |

**`null → value` asserting is the one that matters**: it is the exact asymmetry § Reproducing on another
device calls *"more evidence rather than less"*, so the naive mechanism breaks the sentence Decision 4
exists to make structurally true. With `record(incoming)` first — **which is what `Observer` itself
does**, and is the contract the assert names — every one of the eight cases is right, and still with **no
new comparison function**. Decision 4's conclusion stands; its mechanism is corrected to the two-call
form, and § 10's *"compare with `!=` instead of `Observations.changed`"* mutation gains a sibling:
**drop the `record` call and keep the `changed` call**, caught by Fixture P arm 2, which becomes the arm
that separates an `AssertionError` from a pass.

**§ 6's disclosure is unchanged**: the second object is still never asked for `facts_document`,
`unobserved` or `warn_unanswered`, so Fixture Q's claim about `total_probes` holds exactly as written —
the seeded object's counts are its own and reach no record.

### C3 — Ruling AA's two forms are told apart by a **filesystem probe**, and the design says so rather than implying a structural test

Decision 3 step 2 reads *"the byte copy is reachable — `environment/uv.lock` beside the operand."* Made
explicit: the test is `(<operand>.parent / "environment" / "uv.lock").is_file()`, and it is a **probe for
a file**, not a structural fact about the operand. It is correct for both measured forms — a run
directory holds `environment/`, a bundle holds only `study.yaml` and its members — and it is stated
because a bundle placed *inside* a run directory would take the run-directory branch and compare a
digest that belongs to a different run. **The digest check is what makes that safe**:
`E-REPRODUCE-LOCKFILE-EDITED` fires when the copy's sha256 does not match the record's `uv_lock_hash`,
so a foreign `environment/uv.lock` is refused rather than used. That is why the probe is acceptable, and
naming the reason is the difference between a proxy and a guarded one.

### C4 — the count moves, and every figure carries its noun

C1 mints one more code. The slice mints **twelve `E-REPRODUCE-*` codes and one `E-APPARATUS-*` code —
thirteen codes, thirteen § Errors rows, one row per code covering every site that raises *or* reports
it.** Decision 14's table gains `E-REPRODUCE-COMMIT-UNREACHABLE` at exit `5`, and § 7's *"twelve codes
are minted and none is retired"* reads **thirteen**; the § Executability verdict — **no row moves, no
fifth number** — is untouched, because a count of refusals says nothing about whether any of the nine
configs can reach one, and none can. **Still no exit code is minted**: `5` gains a second reader here
rather than a first, since Decision 3 step 5 already reads it for `uv sync`.
