# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status: specification and implementation

This repository holds both the normative specification and the tool it specifies.

- `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md` and `docs/reference.md` are **the four documents**. They are normative and they lead.
- `src/publishable/` is the implementation. It follows the documents. Where it cannot follow them, **the document changes first** — record the gap in `docs/superpowers/spec-defects.md` rather than diverging silently.

**Commands:**

| Task | Command |
|---|---|
| Tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Types | `uv run mypy` |

`docs/reference.md` § Package layout describes a tree that now **partially** exists. Modules not yet built are still planned; the slices that would build them are in `docs/superpowers/specs/2026-08-08-implementation-spine-design.md`.

**Nothing remains on the charter.** Every hardening slice has merged and the command surface is finished — every row of `reference.md` § CLI reference reads `built`. Three consequences for anyone reading this file next:

- **There is no later slice**, so a `spec-defects.md` entry owned by *unassigned* is not deferred work — **it is what this project ships with**, and every such entry says so in those words.
- **A gap found from here is a new slice's charter**, and it starts with **a dated scoping measured against the code first**. Every charter re-scoped in this project was stale in the same direction: under-counted and missing surface.
- **Quote no single number for a feasibility analysis' executability** — quote its table, or name the dependency. The recurring failure is a slice retiring one blocker, moving configs out of the *refused* column, and carrying the summary phrase forward without re-deriving what it counted.

The per-slice history that used to live here is in the [development record](#the-development-record): each slice has a design, a plan, and a ledger of its own. Read those rather than re-deriving.

## The documents

| File | Role |
|---|---|
| `README.md` | The pitch and the whole arc, for someone deciding whether to use it |
| `docs/design-principles.md` | **Normative.** Why each rule is what it is |
| `docs/experimental-designs.md` | How each experimental design is expressed; what core prevents and refuses |
| `docs/reference.md` | Config schema, CLI, `io` API, templates, sweeps, artifact layout |
| `docs/feasibility-*.md` — [`llm-growth-studies`](docs/feasibility-llm-growth-studies.md), [`growth-chart-literacy`](docs/feasibility-growth-chart-literacy.md) | **Non-normative.** One feasibility analysis each; carries its own examples — see § Feasibility analyses |
| [`docs/releasing.md`](docs/releasing.md) | **Non-normative.** The maintainer's runbook for a PyPI and Homebrew release, with each step's reason attached |
| [`docs/tutorial-writing-a-plugin.md`](docs/tutorial-writing-a-plugin.md) | **Non-normative.** The plugin tutorial — why/when a plugin, and how to build one, measured end to end and pinned to a commit. It reuses `reference.md` § Creating a plugin's own `my_assay` for the project-local template and a second stem for the installed plugin, because one name claimed twice is refused and the tutorial shows that refusal; every build claim in it is dated |

The first four are *the four documents* everywhere below: the invariants, the consistency passes, and the worked example govern those and only those. A `feasibility-*.md` is analysis output, not specification, and nothing in it is authoritative over them.

`design-principles.md` is the tiebreaker. Read it before proposing a change to any rule — if a rule looks arbitrary, that file explains it, and if it doesn't, that gap is itself worth fixing.

## The development record

The four documents say what `publishable` **is**. These say how it got there, and they are **tracked** — read them before re-deriving anything.

| Where | What it is | Read it when |
|---|---|---|
| `docs/superpowers/README.md` | What the record is, what governs it, and why it is tracked | Before reading anything else in it, or before adding to it |
| `docs/superpowers/specs/<date>-<slice>-design.md` | A slice's design: its decisions, each with grounds, and what it refuses | Before planning or changing that slice |
| `docs/superpowers/plans/<date>-<slice>.md` | The same slice as numbered tasks, with code and per-task mutations | While executing it |
| `docs/superpowers/*-SCOPING.md` | What was **measured against the code**, dated and pinned to a commit | Before trusting any charter |
| `docs/superpowers/spec-defects.md` | Gaps found and deliberately not closed, with the owner | Before filing a "new" gap |
| `.superpowers/sdd/<plan>/progress.md` | The ledger: every ruling, its reason, and what it costs if wrong | To learn why something is the way it is |
| `.superpowers/sdd/<plan>/task-N-report.md`, `task-N-review.md` | What was built, what the brief got wrong, what each finding was verified by | Before repeating a task's work |

**A scoping expires; a spec does not.** Every charter re-scoped so far was stale **in the same direction** — under-counted and missing surface — so a scoping is dated and pinned to a commit, and a claim carried from one without re-checking is worse than one omitted. Re-measure rather than trust.

**The plan argues from the spec, and the code outranks both.** Where they disagree, the code wins and the *document changes first* — six of six implementers on the most recent slice found a real disagreement, so finding one is expected, not exceptional.

Two things stay untracked because git already holds them: task briefs (extracted from the plan by the installed `superpowers` plugin's `task-brief`) and every `.diff` (regenerable from the two commits in its filename).

**The plugin's `sdd-workspace` rewrites `.superpowers/sdd/.gitignore` to a bare `*` every time it runs, and `task-brief` calls it.** Both scripts live in the installed `superpowers` plugin and **not in this repository — `scripts/` does not exist here**, and this file described them as repo paths for several slices, which is the *assuming a documented rule has code behind it* row applied to its own author. Already-tracked files stay tracked, so the damage is only to records created after a clobber. Restore that file's content when you notice, and use `git add -f` when committing new records.

## Invariants a change must not quietly break

These are load-bearing across all four documents; contradicting one in a single section creates a real inconsistency, not a wording nit.

- **Operation commands take paths and nothing else.** No parameter flags, no selectors, no behavior-changing env vars. Modes get their own command names (`dry-run`, `draft`, `resume`) rather than `--dry-run`/`--allow-dirty`. Only creation commands (`new`, `plugin new`, `generate`/`init`, `study new|add`, `demo`) take arguments beyond a path — `demo`'s is `[--into DIR]`, and it is one rule with `reproduce`'s refusal of the same flag rather than two: **`reproduce` derives its destination from the record, and `demo` has no record to derive from.** (`design-principles.md` § Everything is in the file)
- **Three hashes, split on purpose.** `code_hash` covers `src/**` and `templates/**` only — the code your repo supplies, a plugin's being pinned by `uv.lock` instead — separate from `parameters_hash` and `input_manifest_hash`. That split is what makes "same code, different parameters" provable across unrelated commits — unrelated meaning outside the two hashed trees, since another experiment's package is inside them.
- **`input_dir`/`output_dir` may never resolve inside the git repo**, checked at generate, at validate, and by every command that executes (`run`, `draft`, `resume`). Which repo is decided by a walk-up from the path the command was given, not from the working directory.
- **Condition vs. repeat.** A condition is a difference being measured; a repeat is a difference being averaged over. Statistics aggregate *within* a condition and compare *across* conditions — never the reverse.
- **A repeat is an execution, so the kinds are exactly the three things a re-execution can change: `seed` (RNG state), `fold` (which units it sees), `batch` (the state of the apparatus it measures through — see § The apparatus core can only observe).** A `batch` takes no field but `n`, executes in order with `order: randomized` shuffling inside it, and `validate` warns when no step sets `nondeterministic = True`. Resampling and permutation are `statistics.resample`/`statistics.null_test` over the unit table (thousands of executions otherwise, and an all-permuted design has no unpermuted value to test); technical replication is `data.units.measurements`, collapsed at unit resolution (re-running an identical step recomputes the same answer); a fixed holdout is `data.units.holdout`. `validate` rejects `bootstrap`, `permutation`, `technical`, `biological`, and `holdout` as kinds by name.
- **Units are the inference base; repeats never are.** Every interval core reports is computed from the per-unit table, `n` counts units (`resolved`/`completed`/`ineligible`/`failed`, where `io.skip` declares the third and `max_failed_fraction` guards only the fourth), and repeat dispersion is reported separately as `repeat_spread`. A metric that exists only as a step-returned scalar is `basis: repeats` and gets **no** `ci95`; the one interval core stores without computing is an `Estimate` returned by a `summary` step, marked `reported: true`, outside the correction family and never recomputed. A hypothesis may name one — it takes no `compare` — and the verdict records `verdict_rests_on: reported` rather than `computed`. Pairing is over units, never over repeats, and a contrast — `vs_baseline` or a declared `statistics.contrasts` entry — is computed over the intersection of both sides' completed units, recorded as `n_paired` — and its interval is its own construction over that intersection (`paired_t_over_units`, `paired_percentile_over_units` drawing once for both sides, or the `welch_`/`unpaired_` counterparts), never a difference of the two sides' intervals. Holm ranks on the point estimate over half the raw `ci95` width, because the family often carries no p-value at all, which is also why `fdr_bh` over such a family warns. `data.units.weight_by` weights an enriched sample's estimates and records `weighted_by`; `statistics.report_by` repeats metrics over strata without adding executions or joining the correction family; a subgroup you want to *test* is a contrast with `within`, which does join it. Contrasts compare conditions and do not nest: anything comparing two contrasts — a dose-response ordering, a difference-in-differences, a nested mean over cells — is an interaction and stays a `summary`-step `Estimate`. The table `aggregate` receives supports exactly four operations — row iteration, column access, `len`, `columns` — deliberately not a `DataFrame`, so core can change what backs it without breaking every plugin, and it carries **every** recorded column — a non-numeric one included, which earns no metric block because there is no mean of strings — beside every declared unit attribute. A metric over a column only some units carry a number for is computed over those units and reports **that** contributing count as its own `n.completed`, which is what makes the interval honest; the four-way `n` above is not widened by it. (`reference.md` § The unit table is the inference base, § Templates)
- **One import root, one registration, one return shape.** Everything a user writes against is imported from `publishable` itself — `publishable.templates` and every other submodule are implementation detail, and `reference.md` § The importable surface is the enumerated list. The entry-point key *is* a plugin artifact's registered name and the `@register_*` argument is checked against it (so `validate` resolves a name without importing the package); a collision or a shadow of a core name fails at load rather than being resolved by install order. `io.write` dispatches on the longest suffix of the name's last component that a writer has registered **or an installed distribution claims** — a claim resolved from package metadata and loaded only when it wins, and winning requires being strictly longer, so core's five cannot be shadowed — and each core writer takes exactly what its reader gives back — rows as mappings for `.csv`/`.parquet`/`.jsonl`, any parsed structure for `.json`/`.yaml`, `bytes` or `str` for everything else, never a `DataFrame` or an object core would have to guess at. A step's `run` and a template's `aggregate` both return a flat mapping of scalars — the same set `io.record` takes — with a NumPy scalar coerced, anything structural a `ContractError`, and an `Estimate` at `summary` scope the one exception. Core raises `PublishableError` → `ContractError` / `ArtifactError` → `ArtifactExistsError`, each carrying the same stable `E-` identifier a diagnostic prints. (`reference.md` § The importable surface, § Steps and artifacts, § Creating a plugin)
- **What core hands a step is minimal and immutable on purpose.** `io.units` supports three operations — iterate, `len`, index — plus `.train`, on the same argument `aggregate`'s four-operation table rests on; a `Unit` is frozen and hashable by `key`, because one roster is resolved per run and shared across every condition. `cfg` is dot-access with no methods at all (so no parameter name can be shadowed) — the one exception being the root node's single `raw` accessor, which is how anything holding a node whole — a step's `cfg`, or the `cfg` a template's `aggregate` gets — obtains a plain mapping, and which costs the one top-level name core already owns; **core needs it nowhere**, since `validate` and a template's `validate(config)` both read the parsed document rather than a node, which is what makes that method's argument a `Mapping` and its idiom `config.get(...) or {}` — raising `ContractError` on a path the config doesn't hold and `AttributeError` on an underscore-prefixed name. `self.rng` is the generator to draw from — core also seeds the `random` and legacy `numpy.random` globals, but only so an unreachable library is covered, and a concurrent step must give each worker its own stream. `scope` is read from the class before any instance exists, and `__init__` is core's. (`reference.md` § The importable surface, § The unit list is three operations, § Randomness)
- **`parameter_spec` is the single source of truth** for what `init` writes, what its inline comments say, and what `validate` enforces. There is deliberately no separate defaults file. `Param` types are `str`/`int`/`float`/`bool`/`list` (with `item_type`); omitting `default` is what makes a parameter required, and `default=None` requires `nullable=True`. `requires_env` is the one thing a `Param` carries that isn't a constraint on its value — it needs `choices` and must be total over them, and it stays out of the closed constraint vocabulary for that reason.
- **Core vs. plugin test:** would it be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark? If not, it's a plugin. Core ships exactly one template, `generic`. A template *reads* the whole config in `validate` (cross-block rules are properties of what its steps do) but declares nothing outside `parameters`.
- **Greenfield only** — no `adopt` command, ever. Core validates *declarations* and verifies *effects*; it never inspects the body of user Python.
- **`uv` and git are mandatory**, not optional paths.

The stated non-promises — adaptive/sequential designs, per-condition pipeline variation, factorial main effects and interactions, bit-identical reruns, scientific validity — are deliberate refusals with reasons attached, not gaps waiting to be filled. Treat a request to add one as a design change requiring an argument against `design-principles.md`, not a feature request.

## Misreadings this repo has made more than once

Every one of these was made by someone competent, reading carefully, more than once. They are not carelessness — each is a reasonable reading that happens to be wrong here, so knowing the rule is what prevents it. The slice ledgers hold the instances; this section is the short form worth carrying into every session.

### Reading the documents

| Misreading | The rule |
|---|---|
| Taking a § Validation row's own wording as its whole scope | Several rows read as method-independent while the **surrounding prose carries the gating**. Read the section, not the cell |
| Treating a row's example as its definition | An example can be a fault under *every* candidate reading, so the row looks settled and is not |
| Citing a sentence whose job is to **contrast** as if it supported the claim | A sentence distinguishing two cases is not licence to route one into the other |
| Assuming a documented rule has code behind it | Five § Validation rows described checks with no emit site, no check and no test. **Grep for the code before building on the row**; a row and a code are the same check seen from two ends, and either end can be missing |
| Reading a temporary refusal as permanent, or the reverse | A `-UNSUPPORTED` suffix **used to mean** the undocumented build family — retired wholesale, absent from the registry — and the charter completing emptied that reading: `E-TEMPLATE-INSTALLED-UNSUPPORTED` is all that remains, it is **permanent**, and since 2026-08-27 it is documented and carries a row like any other refusal. **Read the suffix as a claim about the feature, never about the schedule.** A *narrow* refusal of a combination is documented, carries rows, and outlives the slice that minted it |
| Scoping a diagnostic by the helper it calls | **§ Errors carries one row per code, not per emit site**, so a diagnostic's unit of work is every site that raises *or* reports it. A task scoped by one helper's call site missed a second emit site still claiming the opposite of its own row |
| Reading a subprocess probe as a pin | A probe proves the moment; a test proves tomorrow. **Five times in three slices a correct fix shipped unpinned**, each verified through the real console script and caught by no mutation. Verify by probe, then pin by mutation |
| Reading a mutation's **silence** as confirmation | A mutation that changes nothing is evidence about the **tests**, not about the code. "No mutation reaches this" and "no mutation *can* reach this" are different claims, and only the second justifies leaving a thing unpinned |
| Reporting **zero disagreements** with the code | **Six consecutive slices claimed it and all six were wrong** — and every one hid in a claim about **other tests or other rows**, never in the implementer's own reasoning about its own code. **Brief-supplied prose is where zero hides**, because it reads as established rather than as a claim. The check is mechanical: before writing "no existing test asserts X", or repeating any claim a brief makes about the code, grep for it. Report what you grepped, not a count |
| Inferring "this path does not run" from "this config is refused" | **`validate` collects rather than aborting**, so a refusal elsewhere never makes a later check unreachable. Ask what `validate` *reports*, in full, rather than whether it refuses |
| Reading an unbuilt reader as a defect | An unbuilt reader of an **unbuilt** surface is specification — present tense is correct, and § Package layout's `— not yet built` carries it. An unbuilt reader of a **shipped** surface is a defect. **This row now has NO live example, and the way it ran out is the point.** (`required_env`, `apparatus_probe`, `apparatus_facts` and `field_convention` were its examples in turn, each retired when a slice gave that surface a reader; `EXIT_EXTERNAL` was the same fault outside `BaseTemplate`. **The row's evidence is its own attrition** — an empty example list is not a reason to delete a row that took five slices to empty, and a declarable field with no reader is exactly what this project keeps producing) |

### Writing checks that can fail

**Sixteen checks across two slices could not fail**, and roughly a dozen more in another — every one caught by a mutation and none by reading. Run the mutation before believing the test, **and run it where the behaviour lives** — not where the test happens to look. The shapes, each seen more than once:

| Shape | Why it passes anyway |
|---|---|
| A fixture whose numbers agree with the bug | A 13-unit apportionment matched a reverse-order mutant by coincidence; a cluster fixture where correct and buggy counts were both 3 |
| A dimension no assertion can see | Per-stratum arm counts are **forced** by apportionment, so no count assertion can detect an RNG change — deleting the shuffle left the suite green |
| An assertion implied by another in the same test | Arm sizes summing to the roster is arithmetic, not a check, once the sizes are pinned |
| A control asserting only absences | Passes identically if nothing ran. Pair it with something that must report |
| A parametrized test asserting a **failure** for both arms | Proves nothing about either arm's **success** path |
| Testing the refusal, never the honouring | `validate` refused bad values while nothing checked the draw *used* a good one, so ignoring it entirely passed the suite |
| A mutation applied to a proxy | The extracted helper's body rather than the call site; the fixture rather than the wiring |
| Varying config **shape** when the property is about roster **content** | **A refusal that happens to fire must be attributed before it is counted** |
| A test whose **name** claims the guarantee | A test named `..._matches_...` compared each of two messages against **its own** hard-coded literal, so nothing compared the two — and a reader greps for exactly that name and stops looking |
| A test that **iterates the thing under test** | Looping over the frozenset under test changes the expectation and the actual together. **Enumerate the literals the set should contain**, or the test measures only that the set equals itself |
| An assertion satisfied by **neighbouring output** | `assert "draft" in out` passed on a member named `draft_run`. **When you assert a substring, ask what else in the output could produce it** — and when you assert an absence, assert it on the stream the thing writes to |
| A decoy whose **sort position agrees with the bug** | Twice in one task a scan-versus-lookup fixture ruled out only *first*-wins: the decoy sorted before the real package, so scan-first failed and **scan-last passed**. The second instance came after the first had been caught and disclosed — **catching it once does not immunize the next fixture.** Put a decoy on **each side** (`aaa_`/`zzz_`) |
| A fixture with too few elements to distinguish the candidate orderings | **Two elements only ever distinguish two answers.** Count the orderings you must rule out, then size the fixture so each yields a different answer |
| A monkeypatch left aimed at a name the code no longer calls | **When you move a call site, grep the suite for patches aimed at what you moved** |
| A seam named in the brief and instantiated by no fixture | Naming a seam is not testing it: ask what config separates the readings, then check it exists |
| The test's **reader** normalising the defect away | A YAML alias defect died inside `yaml.safe_load`. When a defect could live in *how* a value is written, assert on the raw text |
| A sweep whose **triage** discards a true hit | *Every hit must be attributed before it is counted* — reconciling hits against a table of known homes reads a real one as noise |
| Proving an arm **cannot move** offered as proof the line is **pinned** | Those are opposite facts wearing one sentence. **Ask what fails if the value comes back**, and prove it by neutering the new pin's own assertions and watching the suite stay green |
| A parameter **added, documented, and wired to a constant** | Four slices in a row shipped one. **The docstring is not the wiring**, and *an unread parameter is an unbuilt reader of a shipped surface*. Grep every new parameter's call sites for a literal |
| A **count** where the property needs **membership** | A proportional holdout over two arms of ten lands 2/2 **by chance with probability ≈0.42**. **Before asserting a number, ask what fraction of wrong implementations produce that same number** |
| A sweep that has never been shown to fail | Two of three sweeps written in one batch were **incapable of failing** when first run. **Run every sweep against a string you know is present before believing a zero**, and report that proof rather than the zero |
| A mutation's **result** reported as a count nobody read | **A number offered as verification evidence has to be the number the command printed**, or the reader who trusts it is the one who later moves a pin it was supposed to guard |
| A mutation whose **prediction** went stale under a later task in its own slice | **A whole-branch re-run is not a formality**: the branch under each mutation changed after the mutation was written |
| A **mutation** whose two branches cannot differ | **A mutation is a claim too**: before trusting "this would prove X", check the two branches can actually produce different results |

### Answering a question with a proxy

Every instance below came from the same move: answering with something *correlated* rather than with the fact. **When a predicate keeps failing open, the proxy is the bug, not the guard** — close it by asking the direct question, usually with a helper that already exists.

- **A module-name prefix, or a marker stamped on a class**, standing in for *does this file sit under this repo's `templates/`*. Both fail open, in different directions.
- **State read at the wrong moment.** A fix placed after `sys.modules` was restored inverts its own answer: a genuinely local class's module is gone while an external one is still cached.
- **A reserved NAME standing in for a structural fact.** A `report_by` stratum was excluded by testing the string `by`, and a recorded column legitimately named `by` was silently dropped. A stratum is identifiable by **where it sits**, not by what it is called.
- **Copying a recipe's calls without its containment.** Credential-redaction calls were lifted while the `try` they sit inside was not, and a declared credential reached stderr verbatim. **A recipe is its calls PLUS where they sit.**
- **Removing by position.** A `sys.path` entry inserted at 0 and removed with `pop(0)` answers *which entry did I add?* with a position; user code runs inside that window by design. Remove by identity, and pin the restoration on the failure path.
- **A grep for one spelling.** Siting redaction by `grep 'type(exc).__name__'` answers *where does this spelling appear*, not *where does this happen* — a site formatting a bare `{exc}` matched nothing and leaked a credential. Enumerate by **reading** where a thing can happen, then confirm with greps; the reverse order is the substitution, and it was made by the author of the rule forbidding it.

### Habits that cost real work

- **A comment or docstring claiming a guarantee the code does not provide** — at least a dozen instances, including one that promised a fail-open defect as if intended. When you change a guard, re-read its justification. A sentence can also contradict **the argument that justifies the thing it describes**.
- **A fix that carries its own justification is not thereby verified**, and the justification is written from the intent while the behaviour has already moved. One `.env` fix shipped a docstring justifying it with *the precise property the change had just broken*. Probe the property the sentence names, not the intent behind it.
- **Prefer deleting a claim to rewriting it.** A rewrite invents; a deletion cannot. But deleting a **true** claim is not licensed by that — a dated measurement that was true on its date gets corrected, not removed.
- **A safety argument in a comment is a claim, and needs a mutation like any other.** A retry's comment argued it could never raise because the faults "surface on the first call" — the first call was inside the `try`, and the real failure cost every execution in a run with no `run.yaml` written. If a comment says *this cannot happen*, make it happen.
- **Sweep for the claim, not for the file the claim was first noticed in.** One false sentence had five homes in a single slice, and each round of sweeping stopped one file short.
- **A batch with no review is where the findings will be.** A documents-and-codes task looks like the safest one to skip and is the one whose output no later batch reads, so **nothing else will find its errors.**
- **A ruling that overrules a brief has to reach the brief.** **The ledger reaches the controller and the reviewers; it reaches no implementer.** Append the correction to the plan when the ruling is made, or restate every live overruling in the dispatch.
- **The sibling that already got it right is the first place to look.** **Before writing a walk, a guard or a containment, grep for one that already exists** — and if you cite it as precedent, copy where it sits, not only what it calls.
- **Carrying a finding into a brief is necessary and not sufficient.** *A ledger line saying "filed" is not a filing*, **and neither is a dispatch line** — a report that lists five carry-forwards and discharges four reads as complete. **A report's claim that a carried finding is closed has to be checked against the code like any other claim**, because the carry itself creates the expectation that it was done.
- **A filing's claims about the code go stale like any other comment.** When you change code a `spec-defects.md` entry describes, re-read the entry — and **re-owner a deferral when the slice that filed it finishes**, or it reads as live work nobody holds.
- **Rewriting a sentence when a table row was the thing that was wrong.** A sentence that **derives** its claim from a `Status` column is repaired by fixing the column. Replacing it with an enumeration converts a self-maintaining statement into a maintenance obligation nobody owns.
- **Locating a table row by position** ("the two rows above", "further up") — at least seven instances, wrong twice. Name what a sibling row *does*. When you insert or remove a row, check every row it **moved**, and every count phrase near it.

### Mechanical traps

- **Never filter the output of a sweep whose job is to find a string** — filter the file list. A reviewer checking this exact rule lost a true hit to `grep -v superpowers`, because the matching line contained that path. Prove each sweep can fail by running it against a string known to be present. This matters more now that the [development record](#the-development-record) is tracked: a sweep over the four documents must **name** them, since `*.md` no longer means what it used to.
- **A `grep -F` for a phrase cannot match the phrase once it wraps**, and prose in this repo wraps at every edit. **Sweep for a distinctive short fragment, or normalise newlines first** — and when a claim has already been found twice, assume the next home is one your last sweep *could not* have matched rather than one you forgot to include.
- **A guard pin can EXPIRE rather than break.** **A digest over a document whose job is to describe behaviour slices change is a proxy that fails whenever the document does its job**; a digest over one that should never move is the direct question. **When an arm fires, ask whether the finding is about the code or about the arm** — retiring it with the reason recorded is a legitimate outcome, and refreshing the hash is not.
- **A commit message describing a command can RUN it.** Backticks inside a double-quoted shell string are command substitution, and this repo's prose quotes commands constantly — a message reading *"drops `uv publish` so nothing is uploaded"* ran `uv publish` against real PyPI, saved only by an unexported token. **Write any message that quotes a command with a single-quoted heredoc** (`git commit -F - <<'MSG'`), and reserve `-m` for messages with no backtick, `$`, or `!` in them; the same reading applies to `--notes`, `--title` and every other flag that takes prose. And **a step that is destructive when it fires should be proven absent by an assertion, not by having removed it**.
- **`git checkout -- <file>` destroys uncommitted work**, twice mistaken for reverting a mutation. Keep a copy before mutating, and verify a revert by **behaviour**, never by `git status`.
- **`ruff format` does not touch `*.md`** — it processes `.py`, `.pyi` and `.ipynb`, and this repo adds no `extend-include`. **Two agents on two slices have blamed it for rewriting a document's fenced Python block**, and both reverted files on that reading; measured both times, the file is byte-identical. Whatever moved those bytes, it was something else, so **find it rather than restoring on a story.** A revert is verified by **behaviour**, never by `git status`, and least of all by an account of what caused the change.

## Checking consistency after any `*.md` edit

Editing one document is almost never a one-file change. Both passes below run before an edit is finished; the second is the one that catches real defects, and no tooling substitutes for it. The **cross-document** pass governs the four documents only — a [feasibility analysis](#feasibility-analyses) is exempt from it and subject to the mechanical pass in full.

**Mechanical.** Write these as throwaway greps or a short script each time rather than keeping a checker around — the repo ships no tooling, and each pass wants slightly different checks. Verify that every relative link and `#anchor` resolves, that no two headings in a file produce the same anchor, that every table's rows match its header's column count and no row is empty, and that no line carries trailing whitespace, a tab, or invisible unicode. Skip fenced code blocks in all of these: the docs contain markdown inside markdown, and a `##` or `|` there is content, not structure. After removing or renaming any string, grep the four documents, this file, and any feasibility analysis for what should no longer exist.

**Both passes govern those files only — never the [development record](#the-development-record).** A spec records what was decided when it was written and a scoping what was measured on its date; retro-editing either destroys the evidence they exist to hold. Correct one the way this repo corrects a published claim: append the correction and say what it replaces. The one exception is `spec-defects.md`, a live list, where a closed gap is struck rather than left to mislead.

**Cross-document.** These are the classes that actually drift, and none of them is visible to a mechanical check:

| Class | The rule |
|---|---|
| **The shared worked example** | README, `design-principles.md`, and `reference.md` describe *one* experiment. Changing a value in one means changing it everywhere it appears — see § The worked example below |
| **Config completeness** | Every config field documented anywhere in `reference.md` must appear in § The one config file, whose fenced example calls itself "the config schema for template `generic` ... at full expansion: every parameter `publishable init` materializes, plus the optional blocks it leaves empty or undeclared." Adding one can invalidate downstream `run.yaml` examples that were correct under the previous default |
| **Enum comments** | An inline `# a \| b \| c` comment must list every value its corresponding table or section defines |
| **Schema fields in prose** | A field named in prose must exist in the `config.yaml` or `run.yaml` example, and vice versa |
| **Declared vs. derived** | If one passage says a value is derived, no other may show it as a settable input. This is how `replication.design` contradicted four passages at once |
| **Versions** | Version numbers in examples must agree with `CITATION.cff` and the README's v0.x notice |
| **Prevented mistakes** | Anything in `experimental-designs.md` § Mistakes core prevents must be structurally impossible in the schema, not merely discouraged |

### The worked example

One experiment runs through README, `design-principles.md`, and `reference.md`: config `cohort-pilot`, package `cohort_pilot`, template `generic`. (`experimental-designs.md` deliberately uses varied domain examples instead — `stimulus.contrast`, `drug.dose`, `samples.csv`, `cell_id` — because its job is to show many designs, not one pipeline.) The steps and scopes are `step01_load_cohort` (run) → `step02_fit_model` (condition) → `step03_analyze` (repeat) → `step04_compare_methods` (summary). It sweeps `analysis.method` over pearson/spearman/kendall — 3 conditions × 5 seed repeats — against 240 units, of which 228 complete and 12 fail. Results are r = 0.581 baseline (ci95 [0.488, 0.661]), 0.607 spearman ([0.517, 0.683]), 0.412 kendall ([0.347, 0.477]); delta 0.026 with a paired ci95 of [−0.007, 0.059] (kendall's is −0.169, [−0.213, −0.125]), and a seed `repeat_spread` std of 0.014. **Those intervals were checked numerically against a synthetic 228-unit table and must not be narrowed back.** The two r intervals agree with both Fisher-z and a percentile bootstrap; kendall's is a percentile bootstrap of τ, because Fisher-z on τ is the wrong transform and is what the earlier [0.298, 0.514] came from — no 228-unit dataset gives τ = 0.412 a half-width above 0.087. The deltas come from a joint resample over the paired intersection, whose half-width does not go below ≈0.033 for a linear-versus-rank contrast at this n, so the earlier ±0.009 was unreachable. A consequence to preserve rather than tidy away: the spearman delta's interval spans zero while `h1` is supported on `observed`, and `reference.md` § Pre-registration turns that into the point of `verdict_evaluated_on`. `cohens_d` is `null` throughout: `r` is derived by `aggregate(units)`, and Cohen's d needs a per-unit value to difference — don't reintroduce an effect size for it. The per-condition intervals are deliberately much wider than the delta's — that contrast *is* what `allocation: within` buys, and flattening it would reintroduce the defect this scheme fixed. Hash prefixes are `8e21` (code), `1a2b` (parameters), `3d8a` (input manifest), `6b1f` (uv.lock), and the run IDs are `run_2026-08-06T14-02-11Z_8e21ab3` and `run_2026-08-07T09-14-03Z_8e21ab3`. README uses `~/data` and `~/results` paths where `reference.md` uses `/secure/...`, and README's `demo` walkthrough reuses the same statistics under a separate `correlation_pilot` experiment, and carries its own code hash prefix `2f5c8d0` — a different `src/` cannot share one, since `code_hash` covers the tree. Those differences are deliberate, the rest is not.

## Feasibility analyses

A **feasibility analysis** asks whether a real research project could be run on `publishable` as specified: which of its experiments the schema expresses, what each config actually looks like, what executing it costs, and — the load-bearing half — which parts core refuses and where each refusal routes. It is the main way this repo gets evidence from outside itself, because the spec is otherwise validated only against its own worked example.

One analysis per file, at `docs/feasibility-<subject>.md`, kebab-case matching its title. Link it from § The documents above.

**These files are exempt from the cross-document passes**, and that exemption is deliberate rather than laziness: an analysis carries the subject project's own cohorts, statistics, and hash prefixes, and reconciling them with `cohort-pilot` would destroy the thing being analyzed. The **mechanical** pass still applies in full — links, anchors, tables, whitespace, `×` for multiplication, hyphens in anchors.

### The procedure

1. **Read the source project for its goal, not its implementation.** State in one sentence what each source repository is trying to learn. Do not replicate its file layout, CLI, or artifact names — those are the parts `publishable` is meant to replace.
2. **Name what the source hand-rolled that core already owns**, as a table. Manifests, run ledgers, timestamped directories, split records, usage reports, and reproduce commands are the recurring ones. This is both the strongest adoption argument and the list of things a proposed plugin must not rebuild.
3. **Express each experiment in the spec's vocabulary**, in this order: the problem in two sentences, the design decision (which axis, which repeat kind, which allocation, where the units come from), then the actual YAML.
4. **Every YAML must be checkable against `reference.md` § The one config file**, whose fenced example is the config schema for template `generic` at full expansion — every parameter `publishable init` materializes, plus the optional blocks it leaves empty or undeclared. Any field you show must exist there or in the proposed template's `parameter_spec`; a template declares nothing outside `parameters`, so there is no top-level block of a plugin's own.
5. **Do the arithmetic before writing the YAML, not after.** Every config states its condition count, its repeat structure, its execution count against `limits.max_executions`, its unit-executions (which is what a metered run is billed by, and what `dry-run` prints), and its cost and runtime from anchors the source itself observed. A feasibility section without execution counts is decorative — and a repeat structure chosen without them is how a translated design silently costs several times the original.
6. **Name every refusal with its route.** Interactions, dose-response orderings, differences-in-differences, adaptive selection, model fitting, counterbalancing, roster-changing variants. `experimental-designs.md` § What core will not do for you is the list to check against; the route is usually a `summary`-step `Estimate`, a separate run joined in a `study`, or a `report_by` stratum.
7. **Separate what is not an experiment at all.** Reference-standard adjudication, governance firewalls, and human decisions made between runs are not pipelines core executes. Say so explicitly — treating them as runs is the failure mode this step exists to catch.
8. **Propose the plugin last, from what the designs actually needed.** Apply the core-vs-plugin test to every piece, keep the registered artifacts to the five registries, and say which of them the domain does *not* need. Watch the correction family: every metric a template's `aggregate` returns is comparisons × metrics, so a template returning twenty diagnostics corrects every interval in the run for numbers nobody reads.
9. **Record the gaps the analysis found in the spec**, separately from the analysis itself. These are the deliverable's second output — a real project pressing on the schema is where an under-specified rule shows up.
10. **Never state a build fact undated.** A claim about what the tool *does today* — that a config validates, that a command dispatches, that a slice has landed — is perishable in a way a spec claim is not, so it must be dated and pinned to a commit where it is made, and kept in a section of its own so a reader can see at a glance what has an expiry date. `feasibility-llm-growth-studies.md` § Executability on this build is the shape: one section, "Measured on \<date\> against commit \<sha\>", and every refusal named by its code. Anything you are not willing to date belongs in the present tense of the specification instead — write it as what `publishable` specifies, not as what it does. This is the same distinction `reference.md` § CLI reference marks with its `Status` column, and it exists because an undated build claim reads as a spec claim a month later, which is how an unbuilt command was once asserted as fact.

### Traps this repo has already hit

| Trap | The rule |
|---|---|
| A roster-changing variant written as a sweep axis | `data.units` is one roster per run. A different sampling ratio, cohort cap, or eligibility population is a different run, joined in a `study` — not a condition |
| An eligibility change written as a roster change | When the superset roster is shared, a condition that admits fewer units uses `io.skip`, landing in `ineligible`. Eligibility must be constant across a condition's repeats, or the unit is counted `failed` |
| A path or a slashed identifier as a swept value | A swept value must render as `[A-Za-z0-9._+-]+`. Sweep an alias or an ID and resolve it inside the step |
| A metric averaged, ordered, or combined across two contrasts | Contrasts do not nest. It is an interaction, and it is a `summary`-step `Estimate` |
| A mean *absolute* difference read as a contrast | A contrast is the mean of the differences. Two one-sided bounds, or an `Estimate` |
| A model fitted where the split does not exist | `optimizer`-style configs need a `holdout` or a `fold`; this is exactly the cross-block rule a template's `validate` is for |
| Per-request measurements written to a side report | Tokens, latency, and attempts are per-unit measurements. Through `io.record` they become `basis: units` with intervals; in a usage report they have no denominator |
| A repeat structure copied from the source without costing it | Repeats multiply metered work. Put expensive fitting at `condition` scope, and say in `replication.rationale` what the repeat count bought |

## Documentation conventions

- Filenames are kebab-case, matching the doc's title.
- **Hyphen, never an en dash, in anything that becomes a filename or an anchor.** Headings use `dose-response` and `case-control`, not `dose–response` — GitHub's slugger strips an en dash entirely, so `Dose–response` silently becomes `#doseresponse`, an anchor nobody would guess when hand-writing a cross-reference. This overrides the Unicode preference below, which applies to prose and diagrams only.
- Cross-references between the four documents are dense and anchor-based. Renaming a heading breaks links elsewhere — grep the other files for the old anchor.
- Cite another file by section — `reference.md` § "Package layout" — never by line number. Line numbers go stale on the next edit above them.
- `×`, not `x`, for multiplication, including inside fenced blocks. Unicode is already the house style there (`├──`, `←`, `·`).
- README writes bare `publishable <cmd>`; `reference.md` writes `uv run publishable <cmd>` for commands run inside a project and bare for `new`, `demo`, and `study`. Both are correct — README installs globally at its Try it step. Describing this so it isn't "fixed" in either direction.
- `<!-- publishable:begin ... -->` / `publishable:end` regions in the docs are examples of *machine-managed* README regions in generated projects, rewritten by `publishable docs`. Text outside them is hand-written.
- Prose style is declarative and reason-giving: state the rule, then why it exists. Tables carry the dense material.
