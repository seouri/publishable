
## `Config.raw` shadows a config key named `raw`

`reference.md` § The importable surface says a `cfg` node has "no method of any kind",
which is what makes a parameter named `items` or `values` safe. The implementation needs
some way to reach the underlying mapping for hashing and embedding. `Config.raw` is a
property on the root only, so `cfg.raw` would shadow a top-level key named `raw` — core
owns the envelope's top level, so no user key can collide today, but the rule as written
admits no exception at all. Proposed resolution: state in § The importable surface that
the root object carries one accessor and nested nodes carry none.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED.** Task 5 landed exactly the proposed
resolution in `reference.md` § The importable surface ("**The root config node carries exactly one
accessor, `raw`; every nested node carries none.**"), and task 16 reconciled `CLAUDE.md`'s
"dot-access with no methods at all" invariant, which had not been updated with it. Nothing owes
this entry.

## What `init` writes into `replication.repeats` is underspecified

§ The one config file shows `init --template generic` producing
`repeats: - {kind: seed, n: 5}`, while § Naming conventions & repeat defaults gives
`generic` a `default_repeats` of 1 and § Templates shows `default_repeats = 1` on
`GenericTemplate`. Both are satisfiable at once only if `default_repeats` is a warning
floor rather than the materialized value — but the table's column header reads "Default
repeats", which invites the other reading. S1 implements the floor reading and writes 5.
Proposed resolution: rename the column to "Repeat floor", or state in § Naming
conventions that `init` writes a starter value independent of the floor.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED.** Task 7 took the first branch — the column
in `reference.md` § Naming conventions & repeat defaults now reads "Repeat floor", and the
paragraph beneath it states "This is a floor, not a value `init` writes." Task 16 re-checked the
declared-vs-derived class across all four documents: no other passage shows `default_repeats` as a
settable input (`design-principles.md`'s only mention lists it among naming conventions;
`reference.md:1218` is a template's own declaration).

## S1 omits `data.units` from the materialized config

Unit resolution is S2, so `materialize_config` writes no `data.units` block, which
§ The one config file shows populated and § The starter step runs depends on. Not a spec
defect — a slice boundary. Removed from this ledger when S2 lands.

## The generated config calls itself "the complete parameter set" before it is one

S1 emitted `metadata`, `entrypoint`, `data` (minus `units`), `parameters`, `replication`,
`statistics.correction`, `limits`, and `hypotheses` — absent the whole `sweep` block, `data.units`,
and `statistics.contrasts` / `resample` / `null_test` / `report_by`. S2 restored `data.units`;
S3a restores `sweep` (an empty `sweep: {}` plus commented `baseline`/`grid` guidance, matching
what this build actually expands). Narrowed to what's left: `statistics.contrasts` / `resample`
/ `null_test` / `report_by` are still absent, arriving in S4. Retire this entry when those land;
no change to the four documents is needed.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): NARROWED AGAIN, AND THE "no document change"
CLAUSE WAS WRONG.** S4 landed `statistics.contrasts` and `statistics.report_by` for real, so two
of the four are now **built features whose key `init` does not write** — which is what `CLAUDE.md`'s
config-completeness triage calls a real gap, not a slice boundary. At the time of this amendment
(2026-08-11), `resample` and `null_test` were both still refused outright
(`E-STATS-RESAMPLE-UNSUPPORTED`, `E-STATS-NULLTEST-UNSUPPORTED`) and remained a boundary. **That is
no longer true of `resample` as of H4a task 12 (2026-08-15), which retired
`E-STATS-RESAMPLE-UNSUPPORTED` wholesale — `resample` is now a third built feature whose key `init`
does not write, same as `contrasts` and `report_by`. `null_test` remains refused
(`E-STATS-NULLTEST-UNSUPPORTED`) and is the one sub-block this entry's "built vs. boundary" split
still describes.** Two document changes were in fact needed and were made by task 16:

- `reference.md` § The one config file: task 6's clause explained the four blocks' absence by "a
  feature core does not yet execute", which is false for `contrasts` and `report_by`. Rewritten to
  rest the point on the schema being wider than `init`'s output, with no claim about which features
  are built.
- `experimental-designs.md` § Mistakes core prevents: "**A typo'd parameter silently using a
  default** | `init` materializes every valid key…" was a direct contradiction of that clause — the
  prevention actually rests on `validate` checking every key against a closed schema, which is what
  it now says. The prevented mistake is not weakened: an unknown key still fails validation.

**Residual — CLOSED by H4a (2026-08-15).** Whether `init` should materialize the optional
`statistics` sub-blocks: **no.** Grounds 2 and 3 carry the ruling; ground 1 is context, qualified
below rather than dropped, because an earlier draft over-read it.

1. **Context, not a standalone argument: `parameter_spec` is the single source of truth for what
   `init` writes as a plugin's *own* parameters, but this does not by itself forbid a hand-written
   `statistics` sub-block** — `materialize.py` already writes `statistics.correction` (and a
   top-level `hypotheses: []`), and neither is a `Param` either. So "not a parameter" alone proves
   too much; it would argue against the block core already materializes. What ground 1 does
   establish: nothing about `resample`/`null_test`/`contrasts`/`report_by` being non-`Param`
   *requires* materializing them, which leaves the decision to grounds 2 and 3.
2. **The argument, not just the citation: `reference.md` § The one config file's "wider than
   `init`'s output" sentence was written by task 16 specifically to let a BUILT feature go
   unmaterialized.** Before task 16, the config-completeness clause explained an absent block by
   "a feature core does not yet execute" — false once `contrasts` and `report_by` were built, which
   is why task 16 rewrote it to rest on the schema being wider than `init`'s literal output "with no
   claim about which features are built" (the amendment two paragraphs above). `resample` becoming a
   built feature at H4a task 12 is exactly the condition that sentence was generalized to cover, not
   a new case needing its own carve-out — the same logic that lets `report_by` go unmaterialized
   today lets `resample` go unmaterialized now that it stands in the same place. `null_test` still
   sits where `contrasts`/`report_by` sat before task 16 (unbuilt, refused wholesale) and inherits
   the pre-task-16 reasoning instead: an unbuilt feature's key is not one `init` can honor by writing
   it.
3. **The argument only this slice could make:** now that `resample` is honored, a materialized
   `resample: {method: bootstrap, n: 2000}` would be a *declared* resample, so every generated
   project would give every recorded column a percentile interval by default — reversing
   § Statistical reporting's asymmetry, which is that a column has a t-interval available so
   resampling it is a **choice** and `resample` is what makes it. A materialized `resample: null`
   would be inert but would need its own inline comment and would invite the
   `.get("resample", DEFAULT)` reading that separates the absent key from the explicit null.

No `materialize.py` change and no `reference.md` change. Recorded so the absence is a decision.

## The specification's error registry does not cover step-name collisions

`reference.md` § Errors core raises enumerates identifiers like `E-STEP-SCOPE-UNKNOWN` and
`E-STEP-CONTEXT-ABSENT` but has no code for two step classes deriving the same `step_name` (two
`class Analyze` in different modules both yield `"analyze"`). The loss this causes is silent
rather than loud: a later slice uses `step_name` as both the step's artifact directory and the
key in the run record's `per_repeat[step_name][repeat_label]`, so a collision either overwrites
one step's recorded values with no error, or — if the two happen to write the same filename —
fails only incidentally, deep in an unrelated write path. S1 introduces `E-STEP-NAME-COLLISION`,
raised by `build_plan` alongside the existing scope check, in the same style as
`E-STEP-SCOPE-UNKNOWN`. Proposed resolution: add this code to § Errors core raises in
`reference.md` so the registry is complete.

## The specification's error registry does not cover a repeat-seed collision

`reference.md` § Errors core raises has no code for two repeats deriving the same seed from
`_seed_for(digest, index)`, which truncates a SHA-256 digest to 4 bytes (32 bits) before
reducing it to a seed and a `seed<NN>` label. Two repeats that derive the same seed are not
two repeats — they execute identically and produce the same answer — so a design that asked
for `n` repeats would silently run fewer, and a later slice's `repeat_spread` would understate
dispersion over the collapsed set without any error surfacing. This is the same failure shape
as the step-name collision recorded above (a silent overwrite through a different door), so it
is treated the same way: S1 introduces `E-REPL-SEED-COLLISION`, raised by `resolve_repeats`
after building the repeat list, checking both seeds and labels for uniqueness and naming the
colliding seed and the digest in the message. The seed is never perturbed to break a tie — a
seed that quietly differed from what the digest determines would undermine the reproducibility
the derivation exists for — so a collision is a hard error, not a silent fixup. Proposed
resolution: add this code to § Errors core raises in `reference.md` so the registry is
complete, alongside `E-STEP-NAME-COLLISION`.

At 4 bytes, the seed space is 2³² and the collision probability across `n` repeats is on the
order of `n² / 2³³` (birthday bound). At `n = 5` that is roughly `10⁻⁹`; even at `n = 250` (run
against `_seed_for` in practice) no collision was observed. This is why the truncation is
acceptable as a default derivation rather than a latent defect: the guard exists for the
astronomically unlikely case, not because collisions are expected in ordinary use.

## Two accepted-as-is behaviors around `BaseStep`/`BaseExperiment` construction

Recorded, not fixed, because both are consequences of deliberate design choices elsewhere in this
ledger's parent documents rather than bugs: (1) a user step subclass that defines a zero-argument
`__init__` silently "works" — nothing calls `super().__init__()` for them, but `_bind` sets all
context state directly before `run`, so the object still ends up correctly bound; a subclass whose
`__init__` requires arguments instead fails with a plain `TypeError` at construction, before core
ever gets a chance to bind it, which is an acceptable failure mode given "`__init__` is core's" is
already a documented rule a violation of which is the user's error to surface. (2)
`BaseExperiment.steps: list[type[BaseStep]] = []` is a mutable class-level default shared across
any subclass that does not override it; this is harmless in practice because every subclass in
the four documents' vocabulary rebinds `steps` to its own list rather than appending to the
inherited one, so no two experiments can alias the same list object through normal use.

## `code_hash` is not `.gitignore`-aware (S1 deviation, not a spec defect)

§ How the three are computed says `code_hash` is taken from the working tree "skipping
whatever `.gitignore` skips". S1 skips a fixed set instead — `__pycache__`, `.pyc`/`.pyo`,
and the tool cache directories — because honouring `.gitignore` means asking git, and this
plan makes `hashes.py` pure so it can be tested without a repository. In practice nothing
else gitignored appears under `src/**` or `templates/**`, so the two agree today. Closing
it properly means passing an `is_ignored` predicate in from the caller, which already
shells to git. Do that in hardening, or relax the purity rule and say so.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): OPEN, OWNER NAMED.** "Do that in hardening" named no
slice. **Owner: H6 Hashes and provenance** (spine § The hardening slices), which owns both branches
— the `is_ignored` predicate and the purity rule that forced the divergence.

## `parameters_hash` does not normalize to what `init` would have materialized

§ How the three are computed says values are "normalized to what `init` would have
materialized before hashing — an omitted `cluster_by` and an explicit `cluster_by: null`
are the same declaration". S1 hashes the config as written, so a hand-trimmed config and
the file `init` wrote hash differently even when they declare the same run. Normalizing
requires the template's `parameter_spec`, which `parameters_hash` deliberately does not
take. Every config in S1 comes straight from `init`, so nothing hits this yet. Resolution:
either give `parameters_hash` the spec, or state in § How the three are computed that
normalization is the caller's job and name the caller.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): OPEN, OWNER NAMED. Owner: H6 Hashes and
provenance**, which owns `parameters_hash` normalization against `parameter_spec` and the same
purity question entry 89 raises. The two must be decided together: both turn on whether `hashes.py`
may take an argument it does not compute.

## Two `git_provenance` environment facts worth keeping (not defects)

Verified empirically while hardening `commit`'s empty-string case (see the
`E-GIT-NO-COMMIT` fix in `provenance.py`), and worth recording so they aren't
re-litigated: a missing `templates/` directory is safe for
`git status --porcelain -- src templates` — git treats an unmatched pathspec
component as no-match rather than fatal, exit 0, and a genuinely dirty `src/`
is still reported. Separately, a symlinked `/tmp` → `/private/tmp` prefix
mismatch between `find_repo_root`'s resolved repo root (used as `cwd`) and an
unresolved `config_path` string resolves correctly — git normalizes the
pathspec against `cwd` internally, so `ls-files --error-unmatch` still matches.

## `code_hash` over zero files is indistinguishable from several distinct situations

"No `src/` at all", "an empty `src/`", and the now-fixed absolute-path skip-list bug all
produced the identical empty-tree digest `sha256:e3b0c442...`, which is what made that bug
hard to notice — a well-formed hash that certified nothing looked the same as a repo with
genuinely no code. Not fixed here by design: guarding against it or changing the empty-tree
return value is a validation-engine question, not something the pure hashing module should
decide. If a later slice wants zero hashed files to be an error or a warning, it belongs
there, checked against what the caller expected to find.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): OPEN, OWNER NAMED.** "A later slice" named nothing.
**Owner: H6 Hashes and provenance**, which is where the empty-tree return value is decided, with
the diagnostic itself landing through **H1 Validation**'s registry once H6 says what it should say.

## An unwritable or missing `output_dir` surfaced as a bare traceback — now fixed at the CLI

`run_identity.allocate_run_dir` creates `output_dir` with `mkdir(parents=True,
exist_ok=True)` — a missing directory is handled — but an *unwritable* one (permissions,
read-only mount, quota, or `output_dir` resolving to an existing plain file) raises a bare
`PermissionError`/`FileExistsError`/`OSError` straight out of `mkdir()`. `run_identity.py`
is unchanged: wrapping OS errors module by module would scatter the same `try` across the
codebase, and that module's job is allocation, not presentation. `src/publishable/cli.py`
is now the single point where that becomes a diagnostic: `main` wraps its whole dispatch in
one `except OSError`, prints a stable `E-IO-FAILED` identifier (new — not yet in
`reference.md` § Errors core raises, in the same style as `E-STEP-EXISTS` and its
siblings below), and returns exit `1`, not `5` — the specification's exit-code table
reserves `5` for something outside the machine, and a local filesystem refusal is not that.
`tests/test_cli.py::test_an_unwritable_output_dir_is_a_diagnostic_not_a_traceback` provokes
it by pointing `output_dir` at a path that already exists as a plain file. Proposed
resolution: add `E-IO-FAILED` to § Errors core raises, and state in § Exit codes and
diagnostics that a local `OSError` from any command exits `1`.

## `runner.py` is missing from § Package layout

**AMENDED 2026-08-11 (S5 checkpoint audit):** **Understates the divergence by 6×.**
`docs/reference.md` § Package layout omits six shipped modules, not one: `runner.py`,
`coercion.py`, `contrasts.py`, `correction.py`, `estimate.py`, `strata.py`. It also omits
`templates/registry.py`. Its closing sentence "No other module built in S1 diverges from the
layout table" is true only of S1. Owned by task 5 of this plan.

`reference.md` § Package layout lists `scope.py` and `cli.py` but no execution loop; S1
added `runner.py` (the walk-the-plan, construct-a-step-per-execution, catch-and-record
loop that `cli.py`'s `command_run` calls at phase 7) because hiding that loop inside
dispatch is worse than naming it. `docs/superpowers/specs/2026-08-08-implementation-spine-design.md`
already calls this "a divergence from § Package layout" and says it and any further
divergence are logged here and applied to `reference.md` at the **S5 checkpoint**, not
piecemeal — this entry is that logging, not yet applied. No other module built in S1
diverges from the layout table; everything else `ls src/publishable` shows (`cli.py`,
`scaffold.py`, `generators/`, `config.py`, `validate.py`, `hashes.py`, `manifest.py`,
`provenance.py`, `uv_support.py`, `run_identity.py`, `run_record.py`, `replication.py`,
`scope.py`, `artifacts.py`, `base_step.py`, `base_experiment.py`, `param.py`,
`templates/{base.py,builtin/generic.py}`, `readme_templates/`, `materialize.py`,
`diagnostics.py`, `errors.py`) is already named there.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED.** Task 5 applied all seven to `reference.md`
§ Package layout — `runner.py`, `coercion.py`, `contrasts.py`, `correction.py`, `estimate.py`,
`strata.py` and `templates/registry.py` are in the tree now, each with a one-line purpose — and
marked every *unbuilt* module `— not yet built` rather than deleting it, with the paragraph that
gives the reason ("The tree is a map of what core's source will hold, and a module removed from it
because today's `src/` lacks it would have to be re-argued when its slice lands"). Task 16
re-verified the tree against `ls src/publishable`: every shipped module is named, and no name in
the tree is unmarked-but-absent. Nothing owes this entry.

## New error identifiers: `E-ENTRYPOINT-IMPORT`, `W-ENV-UNLOCKED`

Neither is in the specification's error registry. `base_experiment.py`'s `load_experiment`
raises `E-ENTRYPOINT-IMPORT` — wrapped as a `ContractError` — when `entrypoint` doesn't parse
as `<module>:<attribute>`, or when the import or the attribute lookup fails
(`ImportError`/`ModuleNotFoundError`/`AttributeError`). Written in S1 as `run`'s phase-3
"entrypoint imports" gate, checked after the `src/**`/`templates/**` dirty gate and before any
hash is pinned; either way a config pointed at a class that doesn't exist fails the same way a
dirty tree does — a diagnostic and exit `1`, never a bare `ModuleNotFoundError` traceback.
**Superseded in S3b on placement and on the module it lives in:** `validate` now imports the
entrypoint (so it can answer `W-REPL-DETERMINISTIC`), which puts the check *before* the dirty
gate and reports it as a collected finding rather than a raised error. See the two entries at
the end of this file.

`command_run` emits `W-ENV-UNLOCKED` — a warning, not an error, so it never changes the
exit code — when `uv_support.uv_lock_info` finds no `uv.lock` at the repo root. Without it,
a run with `provenance.environment.uv_lock: null` looked exactly as legitimate as one with
a lockfile, silently contradicting README's "Code, environment, and data all pinned" and
`design-principles.md` § Design goals ("uv is not optional"). See the two entries below for
why this is a warning rather than a refusal, and why it fires constantly today.

Proposed resolution: add both codes to § Errors core raises (or, for `W-ENV-UNLOCKED`, the
warning equivalent if the registry ever grows one), alongside the other CLI-introduced
identifiers above.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED on the documentation half.** The registry did
grow a warning equivalent — task 4 added `reference.md` § Warnings core reports, and
`W-ENV-UNLOCKED` has a row there stating both its condition and that it fires on every scaffolded
run today. `E-ENTRYPOINT-IMPORT` is in § Errors core raises. Nothing owes this entry; the
behavioural question about a missing lockfile is the separate entry immediately below.

## Whether a missing `uv.lock` should refuse the run instead of warning is unresolved

`design-principles.md` § Design goals states plainly that "uv is not optional. Environments
are captured and rebuilt through uv" — read strictly, a run with no lockfile to capture
should refuse, the same way a dirty `src/**` does, rather than proceed with a warning.
`W-ENV-UNLOCKED` (above) takes the warning reading instead, for a reason that is really
about what consumes the lockfile rather than what captures it: nothing in S1 rebuilds an
environment from `uv.lock` yet, so refusing here would block every run in a tool that has
no working alternative to offer instead — including, right now, every run of every project
`publishable new` scaffolds (see the next entry). The decision belongs with the slice that
implements `reproduce`, which is what actually reads `environment/uv.lock` back — that
slice is positioned to know whether an unpinned environment is a run worth refusing or a
run worth recording faithfully as unpinned. Proposed resolution: `reproduce`'s design
either affirms the warning (and § Design goals gains a footnote: "not optional" describes
`reproduce`'s obligation, not `run`'s) or promotes `W-ENV-UNLOCKED` to a refusal once
`reproduce` exists to make that refusal meaningful.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): OPEN, OWNER NAMED.** "The slice that implements
`reproduce`" was a description; that slice now has a name. **Owner: H9 Reproduction and the other
modes** (spine § The hardening slices), which owns `reproduce` and is listed last for exactly this
reason — it is what reads `environment/uv.lock` back, so it is the slice positioned to decide
whether an unpinned environment is a run worth refusing.

## A scaffolded project cannot resolve a lockfile until `publishable` is published

Running `uv lock` inside a project `publishable new` scaffolds fails outright, because the
generated `pyproject.toml` declares `dependencies = ["publishable"]` and `publishable` is
not yet on any package index this resolver can reach:

```
error: Because publishable was not found in the package registry and your project depends
on publishable, we can conclude that your project's requirements are unsatisfiable.
```

This is why `W-ENV-UNLOCKED` fires on every run of every project scaffolded against this
checkout today, and it is a bootstrapping fact about this repository's publication state,
not a defect in `uv_support.py` or in the capture code added in `cli.py` — `uv_lock_info`
returning `(None, None)` for an absent file is correct. Recorded so a future reader
diagnosing "every run warns" does not go looking for a bug in the hashing or copying logic;
the fix is publishing the package, not changing `run`. Retire this entry once `publishable`
has a release a scaffolded project's `pyproject.toml` can actually resolve.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED as not a defect.** This is bootstrapping, not
a gap in any slice's work, and it retires on the first published release rather than on a code
change — so it owes no slice and none owes it. It is also now visible to a reader outside this
ledger: `reference.md` § Warnings core reports states in `W-ENV-UNLOCKED`'s own row that it fires
on every scaffolded run today for this reason. No further tracking needed here.

## Where a `"run"`-scoped step's return value goes is unstated

§ The two files gives `results` exactly two children, `conditions` and `summary`, and
`execution` gives `"run"` steps a `shared` block carrying status and timing but no
returned values. So a `"run"`-scoped step's `return {...}` is silently discarded. Every
other scope's return is recorded somewhere. Proposed resolution: either state in
§ Steps and artifacts that a `"run"` step's return is not recorded and should be an
artifact instead, or add a `results.shared` block alongside `results.summary`.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED.** Task 6 landed the first branch in
`reference.md` § Steps and artifacts: "**A `run`- or `condition`-scoped step's return value is not
recorded.**" — with the reason (a metric is keyed by unit or reported per repeat, and a wide scope
has neither) and the route (`io.write`). This closes both this entry and the later
"A `"run"`-scoped AND a `"condition"`-scoped step's return both have nowhere to land".

## A single repeat has no dispersion, and the documents don't say what is reported

§ The unit table is the inference base says that with no `data.units` declared, core
reports "mean, std, sem and a t-based `ci95` over repeats". With `n: 1` — legal, and what
`generic`'s `default_repeats` floor of 1 permits — std, sem and a t-interval are all
undefined. The documents state no rule for it. S1 does not hit this, because it emits no
`aggregated` block at all; **S4 does**, and needs an answer before it computes anything.
Proposed resolution: state in § The unit table is the inference base that a single repeat
reports the value with `basis: repeats` and omits `std`, `sem` and `ci95`.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): ANSWERED for the undeclared case, and the declared
case is now a separate open defect.** Task 9 stated the rule in `reference.md` § The two files:
`repeat_spread` "is omitted, not zeroed, when the run declared no repeat axis at all", because a
standard deviation over an execution that was never repeated "would read as agreement between
repeats that don't exist, the same mistake a zero-width `ci95` over one unit would make". That is
this entry's question and it is closed. What the same task's sentence *also* says — that a
**declared** level resolving to one member writes `{std: 0.0, n: 1, kind}` — is the opposite ruling
for an indistinguishable situation, and is filed as its own defect below ("`repeat_spread` writes
`std: 0.0` for a declared single-repeat level"). Read the two together.

## A "run"-scoped AND a "condition"-scoped step's return both have nowhere to land

§ The two files gives `results` exactly two children, `conditions` and `summary`; a
`"run"`-scoped step's `return {...}` was already known to be discarded (see above). The
same is true of a `"condition"`-scoped step's return — the worked example's
`step02_fit_model` is condition-scoped and never appears anywhere under `results`. This
slice (task 14, after coordinator review) deliberately drops both rather than inventing
schema for either — an earlier draft invented an undocumented `per_condition` key for the
condition case while discarding the run case, which was the same situation given opposite
treatment. The fix is a documentation decision: either state that a `"run"`- or
`"condition"`-scoped step's return is not recorded and should be an artifact instead, or
extend `results.conditions[i]` with a documented block for it.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED.** Task 6 landed the first branch for both
scopes at once — see the amendment on "Where a `"run"`-scoped step's return value goes is
unstated" above. `reference.md` § Steps and artifacts now states the refusal, its reason, and
`io.write` as the route.

## `per_repeat`'s shape when a run has no repeats is unspecified

With no `replication` block declared, `replication.resolve_repeats` returns a single
`Repeat(kind="seed", label="", seed=...)`. That empty-string label flows through
verbatim into `executions.jsonl`'s `"repeat"` field and into `run.yaml`'s
`results.conditions[i].per_repeat[step]` as a `""` key. The documents state no rule for
what `per_repeat` should look like when nothing repeats — a `""` key is what falls out
of the current label scheme, not a considered shape. Left as an open question for the
slice that adds `aggregated`, since a single repeat also has no dispersion (see the
existing entry above on that).

**AMENDED 2026-08-11 (S5 checkpoint, task 16): ANSWERED, CLOSED.** Task 9 answered it in
`reference.md` § The two files, and answered it *as a considered shape* rather than by ratifying
what fell out: "A run with no repeat level still writes `per_repeat`, keyed by the empty string —
the one repeat has no label because there is no repeat axis to render one from — as soon as some
repeat-scoped step recorded a return; the key is `''` there rather than absent. The block is
present rather than omitted so that a reader parsing `per_repeat` does not need two code paths, and
the empty key is what says 'this run had one execution per condition' rather than 'this run
recorded nothing'." Nothing owes this entry.

## Artifacts written before a raise survive under `status: failed` — by design, not a bug

A step that writes some artifacts and then raises leaves those artifacts on disk with the
execution recorded `failed`. This was flagged during task 14 review as a possible defect
("does a failed execution leave a partially-written artifact directory behind?") but it
is intended: § Resuming makes `io.exists` the question a resumed execution asks before
writing, so the design already anticipates debris from a prior failed attempt. Recorded
here as context so a future reader does not mistake it for something to fix.

## New error identifiers: `E-RUN-SEED-MISSING`, `E-STEP-RETURN-TYPE`

**AMENDED 2026-08-11 (S5 checkpoint audit):** Now in the registry.
`E-RUN-SEED-MISSING`, `E-RUN-CFG-MISSING`, `E-RUN-ORDER-MISMATCH`, `E-REPL-ORDER-UNRESOLVED` and
`E-RUN-FOLD-UNRESOLVED` are all in `reference.md` § Errors core raises' last row. Closed at entry
lines 927 and 1094.

Both raised by `runner.execute_plan`. `E-STEP-RETURN-TYPE` is already in the
specification's registry (`reference.md` § Errors core raises) and this slice is its
first implementation: a step's `run` must return a mapping or `None`; anything else
raises inside the loop, failing that execution while the run continues. `E-RUN-SEED-MISSING`
is new and not yet in the registry — it is a runner-internal consistency check
(`execute_plan`'s `plan` and `repeats` arguments must name the same repeat labels) rather
than something a step itself does; raised before the per-execution `try`, so it stops the
run rather than failing one execution, since a label/seed mismatch means the run's
randomness cannot be trusted to be what the digest determined for *any* remaining
execution, not just the one where the mismatch was first noticed.

## New error identifiers: `E-STEP-EXISTS`, `E-EXPERIMENT-EXISTS`, `E-PROJECT-EXISTS`

None of the three is in the specification's error registry (`reference.md` § Errors core
raises); all were introduced by the `new`/generators slice, alongside the existing
`E-STEP-NAME-COLLISION`, `E-REPL-SEED-COLLISION`, and `E-RUN-SEED-MISSING` entries above.
`generate_step` raises `E-STEP-EXISTS` when a `step[0-9][0-9]_<name>.py` already exists for the
requested name, checked before anything is written or `experiment.py` is rewritten — a failed
generation leaves the package exactly as it was. `generate_experiment` raises
`E-EXPERIMENT-EXISTS` when `src/<pkg>/` already exists, checked before any directory is created —
this replaces a bare `FileExistsError` that previously escaped from `mkdir(..., exist_ok=False)`
uncaught, which broke the `PublishableError`-tree convention the CLI's exception handling relies
on. `scaffold_project` raises `E-PROJECT-EXISTS` when the target directory already exists and is
non-empty, checked before any file is written — this replaces a prior silent overwrite of
`README.md`, `CITATION.cff`, `LICENSE`, `pyproject.toml`, `.gitignore`, and `.env.example` on a
second `new` against the same path, which also left the destruction uncommitted because `.git`
already existing skipped the first-commit step too. An empty or absent target directory still
proceeds normally, since scaffolding into an empty directory is ordinary use, and there is
deliberately no `--force` to bypass the refusal — a flag that changes what a command does is a
parameter wearing a disguise; the remedy is to choose a different path or delete the old one
deliberately. All three are consistency checks a generator or scaffolder makes about its own
target, not questions a template or a step author's code raises, which is why they sit next to
the collision-style codes above rather than the step/runner ones. Proposed resolution: add all
three codes to § Errors core raises in `reference.md`.

Recorded limitation, not fixed: `generate_step`'s rewrite of `experiment.py` is a string
replacement, not a parse — it assumes the file retains the shape `generate_experiment` produced
(a single-line `STEPS = [...]` list, one `from .steps.stepNN_name import Step as X` per line). A
user who has hand-restructured `experiment.py` — wrapped the list across lines, added a comment
containing `STEPS = [` or a stray `]`, renamed the list — gets undefined rewrite behavior rather
than a clean refusal. Making the rewrite robust against arbitrary hand-edits is a parsing
problem, not a string one, and is out of scope for this slice; a user who has restructured
`experiment.py` should add the step by hand instead of calling `generate step`.

## `validate` findings are not ordered by config position

§ Exit codes and diagnostics says `validate` "reports every error and warning it can find
in one pass, ordered by config position". S1 orders by internal check-function sequence
(metadata → parameters → versions → data → replication → template rule), which loosely
tracks a typical config's layout but diverges whenever fields are declared out of the usual
order — an unknown key under `parameters` is reported before an unreadable `data.input_dir`,
though `data` precedes `parameters` in the file. The order is deterministic and defensible;
it is just not what the sentence promises. Resolution: either track document position
through the loader and sort findings by it, or amend § Exit codes and diagnostics to say
findings are grouped by check rather than by file position.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED.** Task 6 took the second branch in
`reference.md` § Exit codes and diagnostics: the "ordered by config position" clause is gone, and
the paragraph now says findings "are grouped by the check that produced them, not by where in the
config the offending value sits", with the reason (a reader fixing one block wants that block's
mistakes together). Task 16 checked the removed phrase across all four documents and `CLAUDE.md`:
`grep -rn "config position"` returns nothing anywhere.

## `run.yaml` gains two keys `reference.md` does not enumerate

Fixing two review findings against the S1 spine added top-level `layout` (which levels —
`conditions/`, a repeat level — survived collapse, per § How artifacts are organized's
promise that "the active layout is recorded in `run.yaml` so tooling can rely on it," which
was previously unmet) and `provenance.input_manifest_changed` (the paths a post-run
`verify_manifest` found changed, so a `status: failed` run from manifest drift carries its
own reason rather than looking identical to every execution simply reading `completed`).
Neither key appears in § The two files' `run.yaml` example. Both are additive — no existing
key changed shape — but the example is titled as if it shows the whole record. Proposed
resolution: add `layout: {conditions: false, repeats: true}` and
`input_manifest_changed: []` to the § The two files example, in the same style as
`input_manifest_hash`.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED.** Task 9 added both to the § The two files
`run.yaml` example, each with the inline comment the proposed resolution asked for. Task 16 ran the
schema-fields-in-prose class over them: `layout` is named in prose at § How artifacts are organized
("The active layout is recorded in `run.yaml` so tooling can rely on it"), and
`input_manifest_changed`'s meaning is named in prose at § What status means ("the input manifest
failing its re-verification … fails a run that otherwise reached the end of its plan") even though
the key's own spelling appears only in the example's comment — which is the same treatment
`started_at` and every other record-only key gets, and is not a defect.

## New error identifiers: `E-SWEEP-UNSUPPORTED`, `E-DATA-UNITS-UNSUPPORTED`, `E-REPL-ORDER-UNSUPPORTED`, `E-DATA-NOT-ABSOLUTE`

None of the four is in the specification's error registry (`reference.md` § Errors core
raises). The first three follow the pattern `replication.py` already established for
`E-REPL-KIND-UNSUPPORTED`: a config block this slice reads but does not execute must be a
refusal, not a silent no-op, because a no-op here means `run.yaml`'s embedded `config:`
describes an experiment that never happened. `E-SWEEP-UNSUPPORTED` fires when `sweep`
declares a non-empty `baseline`, `grid`, `paired`, `ablate`, `sample`, or `groups` — S1
hardcodes `conditions=[(0, None)]` in `cli.py`, so a declared sweep would otherwise run one
condition under exit 0. `E-DATA-UNITS-UNSUPPORTED` fires when `data.units` is non-empty —
it is read by `hashes.design_digest` (silently redrawing every derived seed) but resolves
no roster, so declaring it changes randomness while doing nothing else. `E-REPL-ORDER-UNSUPPORTED`
fires when `replication.order` is set to anything other than `as_declared` — nothing in the
runner reads `order` at all, so `randomized` would validate clean and then execute in
declaration order regardless. All three are raised from a new `validate._check_unimplemented`,
called from `validate_config` alongside the existing per-block checks, and each message states
plainly that the block is specified but not implemented in this build and that it will be
honored in a later slice, so a user is not left thinking their config is malformed. A
config that declares none of the three continues to validate clean — this is required
alongside each identifier's test. Proposed resolution: add all three to § Errors core
raises in `reference.md`, and drop them again once each corresponding slice lands.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): each retirement now names its slice.** The
"-UNSUPPORTED" policy is unchanged — an identifier of this family retires with the feature it
refuses — but "the corresponding slice" is no longer a description. Of these four,
`E-DATA-UNITS-UNSUPPORTED` and `E-REPL-ORDER-UNSUPPORTED` are already retired (S2, S3b), and
`E-SWEEP-UNSUPPORTED` was retired by S3a and survives only as the four per-mode refusals
`E-SWEEP-ABLATE-`/`GROUPS-`/`PAIRED-`/`SAMPLE-UNSUPPORTED`, which **retire with H2 Sweeps**.
`E-DATA-NOT-ABSOLUTE` is not of this family — it is a permanent rule and retires with nothing.
The documentation half is done: the surviving codes are in `reference.md` § Errors core raises.

**AMENDED 2026-08-11 (H1 Validation): the line just above is FALSE at HEAD, and was false when
written.** `grep` against `reference.md` § Errors core raises (828–869) finds none of the four
per-mode `-UNSUPPORTED` codes there — they were never added. The claim conflated "raised by
`validate.py`" with "belongs in § Errors core raises," which the task-8 brief corrected: that
section scopes itself to the raise-time surface, "where there is a step to raise into," and every
code named in this entry is a `validate`-time declaration refusal. `E-DATA-NOT-ABSOLUTE` is the one
exception that actually closed, and it closed in the right registry: it is now a row in
`reference.md` § Errors `validate` reports, the validate-time registry H1 created. The four
per-mode sweep codes are `-UNSUPPORTED` family, so they follow the standing policy for that family
rather than the registry: they stay out of the documents entirely until H2 Sweeps retires the
feature they refuse, at which point the code disappears rather than gaining a row. Nothing else
owes this entry.

## New error identifiers: `E-DATA-ALLOCATION-UNSUPPORTED`, `E-DATA-ASSIGN-UNSUPPORTED`, `E-DATA-CLUSTER-UNSUPPORTED`, `E-DATA-WEIGHT-UNSUPPORTED`, `E-DATA-MEASUREMENTS-UNSUPPORTED`, `E-DATA-HOLDOUT-UNSUPPORTED`, `E-DATA-RESOLVER-UNSUPPORTED`

S2 resolves a unit roster, which retires the blanket `E-DATA-UNITS-UNSUPPORTED` above — a
plain `data.units.from`/`key` declaration now validates clean and is honored. But several
`data.units` sub-fields are still read by nothing this slice: a non-`within` `allocation`
(no `sweep.groups` axis exists to say what the arms are), `assign`, `cluster_by`,
`weight_by`, `measurements`, `holdout`, and a `from: {resolver: ...}` source (resolvers are
plugin artifacts and the plugin registry does not exist yet). Each would otherwise validate
clean and then run something other than what the config describes, exactly the failure the
retired blanket refusal existed to prevent one level up. None of the seven is in the
specification's error registry (`reference.md` § Errors core raises). All seven are raised
from the same `validate._check_unimplemented`, in place of the retired block: `allocation`
is refused only when set to something other than `null`/`within`, since `within` is the
default and means nothing with one condition; the other five sub-fields and the resolver
source are refused only on a truthy declaration, since `init` writes each of them as `null`
and a null must not be read as a declaration. Proposed resolution: add all seven to §
Errors core raises in `reference.md`, and drop each in turn once its corresponding slice
lands.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): OPEN, OWNER NAMED — all seven, plus
`E-REPL-FOLD-STRATIFY-UNSUPPORTED`, retire with H3 Units** (spine § The hardening slices), which
owns `allocation`, `assign`, `cluster_by`, `weight_by`, `measurements`, `holdout` and registered
resolvers as one slice. They are listed together deliberately: each is one `data.units` sub-field,
they share `validate._check_unimplemented`, and splitting them across slices would leave
`_check_unimplemented` half-retired for several slices running. The documentation half is already
done — all seven are in `reference.md` § Errors core raises.

**AMENDED 2026-08-11 (H1 Validation): the sentence just above is FALSE at HEAD, and was false when
written.** None of the seven `-UNSUPPORTED` codes named in this entry's heading is in
`reference.md` § Errors core raises (828–869) — `grep` finds no hits. The proposed resolution two
paragraphs up ("add all seven to § Errors core raises") was never landable regardless: every one is
a `validate`-time declaration refusal, and that section scopes itself to the raise-time surface.
They follow the standing `-UNSUPPORTED` policy instead — no registry row at all until H3 Units
retires the feature each one refuses, at which point the code disappears rather than gaining a row.
`E-DATA-NOT-ABSOLUTE` and `E-UNITS-EMPTY`, described further down in this same entry, are not of
this family and did land, correctly, in `reference.md` § Errors `validate` reports (the registry H1
created).

`E-DATA-NOT-ABSOLUTE` fires when `data.input_dir` or `data.output_dir`, after `expanduser()`,
is not an absolute path. `reference.md` calls `data.input_dir` an absolute path; before this
fix `validate.py` accepted a relative one (resolving it against the validating process's cwd)
and `run.yaml` recorded the literal relative string — a provenance record naming no fixed
location, and one config meaning different data depending on the directory a command is run
from. The check sits in `validate._check_data`, ahead of the `E-DATA-IN-REPO` containment
check, which now only receives already-absolute, already-resolved paths.
`generators.experiment.generate_experiment` is deliberately left writing whatever
`--input-dir`/`--output-dir` string it is given, including a relative one: resolving it there
too would mean `generate` silently rewrites what the user typed into something anchored to the
directory `generate` happened to run from, which is itself provenance the user didn't ask for.
Catching it uniformly at `validate` keeps one place responsible for the absoluteness rule,
consistent with `parameter_spec` being the single source of truth for constraint checks
elsewhere. A scaffolded config with a relative path will fail `validate` immediately after
`generate`, which is the intended feedback loop rather than a gap.

Also fixed in the same pass: the previous fix wave hoisted `_check_data`'s
`E-DATA-IN-REPO`-adjacent policy check above the `E-GIT-NO-REPO` early return but left
`E-DATA-REQUIRED` and `E-DATA-UNREADABLE` behind it under identical reasoning — a repo-less
config missing `input_dir` entirely validated clean. Both are now hoisted above the same
early return; only `E-DATA-IN-REPO` legitimately stays behind it, since it is the one check
that needs a repo root to compare against. The in-repo containment test itself
(`resolved == repo_root or repo_root in resolved.parents`) was also extracted to a shared
`provenance.resolves_inside_repo` helper, called by both `validate._check_data` and
`generators.experiment.generate_experiment`, which previously duplicated it with different
messages; each call site keeps its own error code and message, only the boolean test is shared.

**AMENDED 2026-08-11 (H1 Validation): CLOSED.** `E-UNITS-EMPTY` is a `validate`-time refusal
(`units.resolve_units` is called from `validate._check_units`), so the "Proposed resolution: add
`E-UNITS-EMPTY` to `reference.md` § Errors core raises" below was never landable as written.
Landed instead in `reference.md` § Errors `validate` reports, which now carries the row "The table
`data.units.from` names has no data rows, or the `glob` it names matches no files under
`input_dir`." The second half of the proposed resolution — a sentence stating the empty-roster
refusal wherever units are named the inference base — is still open and belongs to whichever slice
next touches that passage; it is not H1's to close.

`E-UNITS-EMPTY` fires from `units.resolve_units` when resolution yields zero units, whether
the source was a table with a header row and no data rows or a glob that matched no files.
Neither the four documents nor `reference.md` § Errors core raises says what an empty roster
should do — resolution's error vocabulary is scoped to malformed declarations (a missing key
column, a missing source, a duplicate key), not to a well-formed declaration that happens to
resolve to nothing, so this identifier is not in the specification's registry. This build
refuses it rather than letting it through, for a reason that would not be reconstructable from
`units.py` alone: a later task's attrition check only runs `if counts["resolved"]`, so a
zero-unit roster does not just produce empty results downstream, it silently disables the
`max_failed_fraction` safety guard along with everything else that check protects — a run over
nothing would report success with every guard bypassed. Before this fix the glob path had no
check at all (an empty match silently produced an empty `UnitList`), and the table path
happened to refuse only by accident: with zero rows there are zero columns, so the key-column
check fired first and reported a plausible-sounding but wrong problem (`index.csv does not have
patient_id (columns: )`), sending a user looking for a column typo in a file that was simply
empty. The fix adds an explicit emptiness check to both `_from_table` (before the key-column
check, so a genuinely empty file gets the honest message) and `_from_glob` (after computing the
match, since a glob has no key-column check to preempt); both raise `E-UNITS-EMPTY` naming
their source (the table filename or the glob pattern) and stating that a run measuring zero
units has nothing to report. Proposed resolution: add `E-UNITS-EMPTY` to `reference.md` §
Errors core raises, and add a sentence to whatever section states units are the inference base
saying explicitly that an empty roster is refused at resolution, not merely reported as `n=0`
downstream.

`UnitList`'s docstring says "exactly four operations" (iterate, `len`, integer index, `.train`),
and a strict reading of "exactly" would also forbid `in` and `reversed()` — neither is one of
the four, and both work today (`in` falls back to `__iter__` plus `==`; `reversed()` falls back
to `__len__` plus integer `__getitem__`, the classic old-style sequence protocol). Only
`__getitem__` on a non-integer index was fixed to raise `E-STEP-UNITS-CONTRACT`: a slice returns
a foreign type (`list`), and that type leak is the actual failure the four-operation contract
exists to prevent — a step that slices gets a `list`, writes code against `list`, and breaks the
moment core changes what backs the roster. `in` and `reversed()` are different in kind: they are
*derived from* the three promised operations rather than escaping them, so any backing that
supports the contract (a lazily materialized roster, a view over a partition) supports these for
free, with no foreign type appearing anywhere. Adding `__contains__` and `__reversed__` that
raise would mean adding methods to a class whose entire point is having as few as possible, in
order to forbid something that cannot actually outlive the four operations it already has. So
`docs/reference.md`'s wording is imprecise (it should read as "no operation beyond these that
returns something other than what these already return", not literally "exactly four
callable special methods"), and this build permits `in`/`reversed()` deliberately rather than
narrowing the class further — a future reader should not mistake their presence for an
oversight symmetrical with the slicing gap, which was one.

## `validate` still crashes on wrong scalar LEAF types (container shapes are fixed)

S2 closed the container-shape class: `_check_shape` runs first and reports `E-CONFIG-SHAPE`
for any top-level block, `data.units`, `replication.repeats`, or `data.units.attributes` that
is the wrong container type. A fourth layer remains, and it is a different class — a correctly
shaped container holding a wrong-typed scalar reaches a type-specific operation with no guard.
Five confirmed, each escaping `validate_config` as an exception rather than a diagnostic:

- `data.input_dir` / `data.output_dir` as a list -> `TypeError` in `Path(raw)`
- `metadata.name` as a list -> `TypeError` in `re.match(...)`
- `replication.repeats[i].n` as `"many"` -> `ValueError` in `int(count)`; as a list -> `TypeError`
- `data.units.key` as a list -> `TypeError: unhashable type` (used as a set member)
- `data.units.attributes` items that are lists or dicts -> same

Latent but not yet reachable: `hypotheses` items, `sweep` axis values, `metadata.authors` as a
string — nothing indexes into them in this build.

**Deliberately not fixed in S2.** The container fix was one table and one loop. This needs
per-field type knowledge for the whole envelope, which is a config-envelope schema — a real
piece of design with its own questions (where it lives, whether it subsumes `_check_shape`,
how it relates to `parameter_spec`, which already does exactly this job for `parameters`).
Bolting it onto a fix round of a units task would be the partial-sweep-that-looks-complete
failure. It deserves its own task and its own reviewer.

Related question for whoever writes it: `n: "5"` currently passes silently because `int("5")`
succeeds. Whether a numeric string should coerce or be refused is a separate decision from
whether a non-numeric one should crash.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): OPEN, OWNER NAMED.** "Its own task and its own
reviewer" named no slice. **Owner: H1 Validation** (spine § The hardening slices), which is the
slice that builds the full check engine and is therefore the one that decides where a config-envelope
type schema lives and how it relates to `_check_shape` and `parameter_spec`. H1 is ordered first
among the hardening slices partly for this reason: every slice below it adds checks that would
otherwise each have to guess at the same envelope. Task 14 closed the narrower `expand(doc)` crash
class inside `_check_sweep`/`_check_contrasts`; the five leaf-type crashes listed above are
untouched and remain live.

## New error identifiers: `E-STEP-UNIT-UNKNOWN`, `E-STEP-UNIT-SETTLED`

Raised by `io.record`/`io.skip`. Neither is in § Errors core raises, which enumerates the
raise-time codes. `E-STEP-UNIT-UNKNOWN` fires when a step records a key absent from its
roster; `E-STEP-UNIT-SETTLED` when a unit is both recorded and skipped in one execution —
the two states are mutually exclusive by construction, since `completed` and `ineligible`
partition the roster alongside `failed`. Propose adding both to that section's table.

## `units.parquet` type unification across rows within a column is unspecified

§ The per-unit tables describes the column set — unit key, then declared attributes, then
the union of recorded keys — but says nothing about what happens when two rows recorded
different types under the same key. `_encode_parquet` (`src/publishable/artifacts.py`)
hands the column to `pyarrow.table`, which unifies types per column rather than trusting
the first row, with two different outcomes depending on which types collide:

- **int and float in the same column promote to float**, silently: `{"v": 1}` and
  `{"v": 1.5}` recorded across two units come back as `1.0` and `1.5`. This is
  deliberate, not a bug to fix: a per-unit metric that is whole for some units and
  fractional for others is ordinary, requiring a step to pre-float its own values would
  be worse, and the promoted column is a truthful representation of the values it holds.
  Pinned by `test_a_mixed_int_and_float_column_promotes_to_float_deliberately` in
  `tests/test_artifacts.py`.
- **bool/int and str/int clashes raise** (`pyarrow.lib.ArrowInvalid` for bool/int,
  `pyarrow.lib.ArrowTypeError` for str/int) rather than coercing. These are genuine type
  confusions where silence would hide a real bug, so the crash is the right boundary.
  Pinned by `test_a_bool_and_int_column_clash_raises_rather_than_coercing` and
  `test_a_str_and_int_column_clash_raises_rather_than_coercing`.

Whoever writes the slice that adds `aggregate` — which reads this table back and may do
integer-shaped arithmetic over a column that could arrive as float — should inherit this
reasoning rather than rediscover the question. No fix proposed here; the boundary between
"promote" (numeric) and "refuse" (non-numeric mixed with numeric, or vice versa) is
already what pyarrow gives us for free, and it lines up with what a step author would want.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): OPEN as a documentation debt, OWNER NAMED.** The
behaviour is settled and pinned; what is still unspecified is `reference.md` § The per-unit tables,
which states no rule for cross-row type unification at all — so an author cannot learn from the
documents that a bool/int clash raises. **Owner: H5 Artifacts** (spine § The hardening slices),
which owns `units.parquet` integrity and is the slice that also lands non-numeric recorded columns
— the change that makes this column-typing question load-bearing rather than latent.

## ANSWERED in S2: a single completed unit reports no interval

The open question was what a design with no dispersion reports. S2's answer, applied to
`basis: units`: below two completed units, `value` is reported and `ci95` and `method` are
`null`. Reporting a point with no interval is honest; inventing one is not, and this matches
the posture § The unit table is the inference base already takes toward `basis: repeats`.
The `t_over_units` construction returns `None` below n=2 rather than raising, so the caller
renders the absence rather than the failure. Propose stating this in § Statistical reporting.

## ANSWERED in S2: `collapse_repeats`/`summarize_step` refuse a non-numeric column rather than crashing or coercing

The question left open just above — what the slice that reads the per-unit table back
should inherit from `units.parquet`'s promote/refuse boundary — is answered differently at
this layer, and deliberately so: `collapse_repeats` and `summarize_step`
(`src/publishable/stats.py`) never raise. A column is dropped from the collapsed table (or
omitted from `summarize_step`'s output) the moment any of its values is not a real number
— a string, or a `bool`, which is an `int` subclass in Python but is never a quantity worth
averaging into a proportion. This is not the same boundary `_check_column_types` enforces at
`io.record` time: that one raises on a genuine type clash within a column because silence
would hide a bug in the step; this one is downstream of a column that already wrote
successfully; failure caused by refusing to average is not a bug to surface. Reporting no
value for a column that cannot be averaged is the same honesty this section's other entry
extends to a missing interval: an omission is legible, a silently-averaged `True`/`False`
column (mean 0.5) would not be. Pinned by
`test_a_non_numeric_column_is_not_summarized`,
`test_a_bool_column_is_not_silently_averaged_to_a_proportion`, and
`test_collapse_drops_a_bool_column_rather_than_averaging_it` in `tests/test_stats.py`.

## RETIRED in S2: "S1 omits `data.units` from the materialized config"

`materialize_config` now emits the block and `validate` resolves it. The seven sub-fields
S2 does not implement are refused individually rather than the block being refused whole.

## The swept-value pattern and the label separator contradict each other on `_`

`reference.md` § How artifacts are organized states two rules four lines apart that cannot
both hold for every value:

- A swept value must render as `SWEPT_VALUE_PATTERN`, `^[A-Za-z0-9._+-]+$` — a class that
  admits `_`.
- A condition label joins axes with `__`.

A value that renders as `a__b` satisfies the first rule and destroys the second:
`{"m.one": ["a__b"], "m.two": ["c"]}` yields the label `one=a__b__two=c`, which splits into
three axes instead of two rather than the two actually declared. This is more than
cosmetic because a label is also a selector — a hypothesis's `compare.condition`, a
contrast's `of`/`against`, and a `report` filter all name conditions by parsing the label's
body back into axes. An ambiguous split means a hypothesis could select the wrong
condition, or none, with no signal to the reader that anything went wrong.

Two candidate resolutions for whoever amends the documents:

1. Tighten `SWEPT_VALUE_PATTERN` to exclude `_` entirely.
2. Keep `_` legal and state explicitly that the two-character sequence `__` is forbidden
   in a swept value's rendering — `_` alone is fine, the separator sequence is not.

This build implements the second: `sweep.py`'s `check_swept_value` accepts the existing
pattern class but separately refuses any rendered value containing `AXIS_SEPARATOR`
(`"__"`), because refusing all underscores (option 1) is over-correction — `a_b` is a
perfectly nameable value that never collides with the separator. `check_swept_value` is
written for Task 4's `_check_sweep` to call once it exists; it is not yet wired into
`validate`.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): the last sentence is FALSE at HEAD, and the stale
claim was in the code as well as here.** `validate.py:20` imports `check_swept_value` and
`_check_sweep`'s `_value_checks` calls it per swept `grid` value, reporting
`E-SWEEP-VALUE-UNNAMEABLE`; a `baseline` entry is exempt by design, because `label_for` renders a
baseline condition as the literal `baseline` and never joins its fixed values into a label. Task 7
of this checkpoint flagged the stale claim in `sweep.py`'s own docstring — task 16 corrected that
docstring to describe the wiring that exists. Nothing owes this entry; the underlying
document-level contradiction was resolved by option 2 and is stated in `reference.md`.

Pinned by `test_a_value_rendering_the_axis_separator_is_refused`,
`test_a_single_underscore_is_still_accepted`, and
`test_values_already_refused_by_the_pattern_are_still_refused` in `tests/test_sweep.py`.

## New error identifiers: the four sweep modes

`E-SWEEP-PAIRED-UNSUPPORTED`, `E-SWEEP-ABLATE-UNSUPPORTED`, `E-SWEEP-SAMPLE-UNSUPPORTED`,
`E-SWEEP-GROUPS-UNSUPPORTED`. None is in § Errors core raises, which enumerates raise-time
codes. They replace the blanket `E-SWEEP-UNSUPPORTED` S1 introduced, following the pattern S2
used when it split `data.units`: retiring a blanket refusal must not leave the modes it covered
silently accepted. Retire these entries as each mode lands.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): OPEN, OWNER NAMED — all four retire with H2
Sweeps** (spine § The hardening slices), together with `E-SWEEP-BASELINE-PARTIAL`. They are one
slice's work rather than four because they share `validate._check_unimplemented` and because
`groups` in particular unlocks `allocation: between` and the unpaired interval constructions, which
H4 Statistics is waiting on.

## `E-RUN-CFG-MISSING` is raise-time and belongs in the registry

**AMENDED 2026-08-11 (S5 checkpoint audit):** Now in the registry — same last row
of § Errors core raises. Closed at entry line 927.

Unlike the `E-SWEEP-*` validate-time diagnostics above, `E-RUN-CFG-MISSING` is raised at
execution, so § Errors core raises — which enumerates exactly the raise-time
`ContractError`/`ArtifactError` codes — is where it should appear. It fires when a condition
index in the plan has no entry in the resolved `cfgs` mapping: a core invariant violation
rather than a step failure, which is why it is deliberately fatal and sits outside
`execute_plan`'s per-execution `try`. The runner's guarantee — *a failed execution never stops
the run; only crossing the attrition threshold does* — is about steps, and this is not one.

`E-RUN-SEED-MISSING` has the same gap and predates this slice, so the amendment should add
both rather than one. Pinned by the missing-key test in `tests/test_runner.py`.

## New error identifiers: `E-STEP-SCOPE-ONLY`, `E-STEP-READ-REPEAT-REQUIRED`, `E-STEP-READ-CONDITION-UNKNOWN`

None is in § Errors core raises, which enumerates raise-time codes — the same gap Task 7
found and did not introduce. `E-STEP-SCOPE-ONLY` fires when `io.conditions`, `io.repeats`, or
`io.read_condition` is called outside `summary` scope; `E-STEP-READ-REPEAT-REQUIRED` when
`read_condition` names a repeat-scoped step without a `repeat=`. `E-STEP-READ-CONDITION-UNKNOWN`
is new territory the brief's pseudocode did not raise for at all: naming a condition index
absent from `io.conditions` used to resolve to a path built from `f"{condition}_None"` and fail
opaquely inside `_read`'s `FileNotFoundError`. Given `E-STEP-UNIT-UNKNOWN` already names the
equivalent mistake for a unit key, leaving the condition-index case as an unnamed crash was the
larger inconsistency. Pinned by `test_read_condition_rejects_an_unresolved_condition_index` in
`tests/test_artifacts.py`.

## RESOLVED — `read_condition` did not accept what `io.conditions` yields

Not a specification ambiguity: `reference.md`:1784, :1806, :2318 all write `for condition in
io.conditions: io.read_condition(condition, ...)`, passing the loop element straight through —
that pattern works for any element type `io.conditions` yields, provided `read_condition`
accepts it. The first implementation didn't: it did `dict(self._conditions).get(condition)`
with `condition` as the key, which misses when `io.conditions` yields `(index, label)` tuples
(as pinned by the brief's `io.conditions == [(0, "baseline"), ...]`), raising
`E-STEP-READ-CONDITION-UNKNOWN` on the documented usage. Fixed: `read_condition`'s `condition`
parameter now takes `int | tuple[int, str]` and normalizes to the index before any lookup.
Pinned by `test_read_condition_accepts_the_element_io_conditions_yields`, which iterates
`io.conditions` and passes the element straight into `read_condition`, plus the existing
literal-index tests.

One genuine (minor) under-specification remains: `reference.md` never states `io.conditions`'s
element type in prose — only through the three examples' use. Worth one line in § "`io.conditions`
/ `io.repeats` / `io.read_condition`" saying it yields `(index, label)` pairs.

## RETIRED in S3a: `E-SWEEP-UNSUPPORTED`

`baseline` and `grid` now expand and execute. The four modes S3a does not implement are
refused individually, and the `sweep` block is back in the config `init` generates, narrowing
the "complete parameter set" entry to the `statistics` sub-keys alone.

## A `sweep` block present but declaring only falsy keys silently expands to zero conditions

`sweep.expand`'s guard is `sweep = config.get("sweep") or {}; if not sweep: return [<single
unlabeled condition>]` — it treats the *block's presence* as the signal, not whether any mode
it declares actually varies anything. A hand-written `sweep: {groups: [], paired: [], ablate:
null}` is a non-empty mapping (so the guard does not fire), yet every key inside is falsy, so
`rows` stays empty and `expand` returns `[]`: zero conditions, `build_plan` emits no
`condition`- or `repeat`-scoped executions at all, and the run reports `status: completed`
having executed nothing — the exact failure `E-SWEEP-AXIS-EMPTY` exists to catch for one empty
`grid` axis, reachable here without tripping it. `materialize_config` now writes a literally
empty `sweep: {}` (zero keys) specifically to avoid this, but nothing in `validate.py` stops a
hand-edited config from reintroducing it. Proposed resolution: after computing
`conditions = expand(doc)` in `_check_sweep`, add `if sweep and not conditions: c.error(...)` —
"sweep" truthy, "conditions" empty, distinct from the no-`sweep`-at-all path.

**FIXED, new identifier `E-SWEEP-EXPANDS-EMPTY`.** Implemented exactly as proposed: in
`_check_sweep`, immediately after `conditions = expand(doc)`, `if sweep and not conditions:`
emits `E-SWEEP-EXPANDS-EMPTY` at path `sweep`. It sits as a backstop *beneath* the per-axis
`E-SWEEP-AXIS-EMPTY` check rather than replacing it — that check still runs first and still
fires with its specific message for an empty grid axis; the backstop additionally catches
every shape that check doesn't enumerate (`sweep: {grid: {}}`, a hand-written block of only
falsy keys, and any future mode that expands to nothing) because it checks the *expansion
result* rather than the declaration's shape. Grepped `docs/reference.md` for
`E-SWEEP-EXPANDS-EMPTY`, `E-SWEEP-EMPTY`, `E-SWEEP-ZERO`, and `E-SWEEP-NO-CONDITIONS` before
minting — none exist in the spec, so no registry collision. The no-`sweep`-at-all path is
unaffected: `sweep = doc.get("sweep") or {}` is falsy there, so the `if sweep and ...` guard
never fires and `expand({})`'s one unlabelled condition stays unflagged. Tests:
`test_an_empty_grid_block_is_refused_by_the_backstop`,
`test_an_empty_axis_still_gets_the_specific_diagnosis_not_just_the_backstop`,
`test_no_sweep_at_all_still_validates_clean`,
`test_a_normal_baseline_plus_grid_config_still_validates_clean` in `tests/test_validate.py`.
This identifier is not yet recorded anywhere in `reference.md` itself — worth a line in
§ Errors core raises' surrounding prose (or wherever `E-SWEEP-AXIS-EMPTY` is introduced) the
next time that section is touched, so the registry catches up with the implementation.

**AMENDED 2026-08-11 (H1 Validation): CLOSED, in the other registry.** `E-SWEEP-EXPANDS-EMPTY` is a
`validate`-time refusal (`_check_sweep`), so § Errors core raises was never the right home for it.
`reference.md` § Errors `validate` reports — the registry H1 created — now carries the row "`sweep`
is declared and resolves to zero conditions, whatever shape produced that — a backstop beneath the
per-axis checks above," beside `E-SWEEP-AXIS-EMPTY` itself, which the same registry also names.
Nothing owes this entry.

## ~~New error identifier: `E-SWEEP-BASELINE-PARTIAL`~~ RETIRED

**AMENDED 2026-08-12 (H2 Sweep expansion modes, task 7): CLOSED — the identifier is retired and
the refusal is gone.** Task 6 implemented per-cell expansion in `sweep._baseline_cells`, which is
what this entry said the identifier should retire with; task 7 removed the check from
`_check_unimplemented`, its registry row from `reference.md` § Errors `validate` reports, and the
import of `_swept_paths` that only it used. The identifier is now unused everywhere in `src/` and
`tests/`. The three configs this entry pinned as supported still are, and are now pinned by what
they *expand to* rather than by an absent code: `test_a_baseline_fixing_every_axis_is_one_condition`,
`test_a_bare_baseline_with_no_grid_is_one_condition`, and
`test_an_empty_baseline_beside_a_grid_yields_no_baseline_condition`. The shape it refused is pinned
in both halves — validates clean *and* expands to one baseline per cell — by
`test_a_baseline_that_leaves_a_grid_axis_free_validates_and_expands`. What retiring it made
reachable is recorded under "Three baseline shapes per-cell expansion makes reachable" below.

Not in § Errors core raises, which enumerates raise-time codes; this is a validate-time
refusal, like the four sweep-mode codes above. Grepped `docs/reference.md` for
`E-SWEEP-BASELINE-PARTIAL`, `E-SWEEP-BASELINE`, and `E-SWEEP-PARTIAL` before minting — the
document names no `E-SWEEP-*` identifier at all, so there is no registry collision.

`reference.md`:1415-1422 states one rule with two cases, neither a default the other
overrides: **the baseline expands over whichever axes it doesn't fix.** A baseline fixing a
value on every axis is one condition, `00`; a baseline fixing values on only *some* axes is
**one baseline condition per cell of the unfixed axes**, each `vs_baseline` targeting its own
cell. `sweep.expand` implements the first row only — it unconditionally prepends exactly one
`00_baseline` row carrying only the values the baseline literally names. So
`baseline: {analysis.method: pearson}` beside `grid: {analysis.method: [...],
analysis.min_samples: [10, 20]}` validated clean and executed a single baseline that fixes
`min_samples` at nothing: the declared design is not the executed design, and nothing said so.

Per-cell expansion is a real feature and out of S3a's scope, so this build **refuses** rather
than diverges, following the precedent the slice set for `paired`/`ablate`/`sample`/`groups`:
`_check_unimplemented` emits `E-SWEEP-BASELINE-PARTIAL` at `sweep.baseline` when a truthy
`baseline` leaves any declared `grid` axis unfixed, naming the free axes and saying the mode is
specified but not implemented in this build. Retire the identifier when per-cell expansion
lands.

The supported row is untouched and pinned in both directions: a baseline fixing every axis
(`test_a_baseline_fixing_every_axis_is_supported`), the bare baseline with no grid at all
(`test_a_bare_baseline_with_no_grid_is_supported`, plus the existing
`conditions/00_baseline/seed17/analyze` assertion in `tests/test_runner.py`), and `baseline: {}`
beside a grid, which declares nothing and so is not a partial baseline
(`test_an_empty_baseline_beside_a_grid_is_not_a_partial_baseline`). The refusal itself is
pinned by `test_a_baseline_that_leaves_a_grid_axis_free_is_refused`.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): OPEN, OWNER NAMED.** "Retire the identifier when
per-cell expansion lands" named no slice. **Owner: H2 Sweeps** (spine § The hardening slices),
which owns per-cell baseline expansion alongside `ablate`, `groups`, `paired` and `sample` — the
four refusals this one was modelled on, so all five retire together.

## `io.read_upstream` can only reach `run`-scoped steps — MARKED FOR THE NEXT SLICE

**AMENDED 2026-08-11 (S5 checkpoint audit):** FALSE at HEAD. Fixed in S3b task 7, recorded at
entry line 901. `artifacts.py`'s `read_upstream` resolves per target scope — `run`/unknown to
`run_dir/shared`, `summary` to `run_dir/summary`, otherwise the caller's own condition directory
via `condition_dir_name`, then `_nest_repeat`. The hard-coded `shared/` path this entry describes
is gone. **The "MARKED FOR THE NEXT SLICE" marker is withdrawn.**

`reference.md`:1083 states that *"a narrower step reads wider ones via `io.read_upstream(step,
name)` regardless of scope."* `artifacts.StepIO.read_upstream` hard-codes
`self.run_dir / "shared" / step / name`, which is where only `run`-scoped steps write
(`runner.step_dir_for`). A `repeat`-scoped step calling `read_upstream` on a `condition`-scoped
step therefore fails every execution — exit 3, `status: partial` — even though the direction is
legal.

Pre-existing: it predates `s3a-sweeps-and-conditions` and is not caused by it. It is recorded
here because S3a is what makes it load-bearing. The new `SCOPE_ORDER` direction check
(`read_upstream`'s `E-STEP-READ-DIRECTION`) explicitly *permits* a `condition` → `repeat` read,
advertising a path that cannot resolve, and the new `conditions/<nn>_<label>/` level is what a
correct resolution now has to account for. The `summary` case is covered by the new
`io.read_condition`, so the live blast radius is repeat → condition only.

Deliberately not fixed in S3a: the resolution has to mirror `runner.step_dir_for`'s scope → path
mapping (which needs the reader's own condition index, and the condition label), and the next
slice reshapes `step_dir_for` for folds anyway. Fixing it twice is how the two implementations of
that path drift apart — `sweep.condition_dir_name` exists for exactly that reason. Whoever picks
it up: make `read_upstream` resolve through the same helper `step_dir_for` uses, rather than
composing a second copy of the layout.

## RETIRED in S3b: `E-REPL-KIND-UNSUPPORTED`

The S3b plan text described this slice as *narrowing* `E-REPL-KIND-UNSUPPORTED` to `fold` alone,
since `batch` was moving from unsupported to supported. The implementation instead retired the
identifier outright and minted `E-REPL-FOLD-UNSUPPORTED` in its place, following the precedent
`E-SWEEP-PAIRED-UNSUPPORTED`/`E-SWEEP-ABLATE-UNSUPPORTED`/`E-SWEEP-SAMPLE-UNSUPPORTED`/
`E-SWEEP-GROUPS-UNSUPPORTED` set when the four sweep modes each got their own name rather than
sharing one generic "unsupported" code. `resolve_repeats` now also raises two identifiers that
did not exist before: `E-REPL-LEVEL-DUPLICATE` (two repeat levels of the same kind) and
`E-REPL-LEVEL-DEPTH` (more than `MAX_LEVELS == 2` levels declared).

`E-REPL-KIND-UNSUPPORTED` is gone, not narrowed — grep `src/`, `tests/`, and the four documents
before assuming a surviving narrowed form exists anywhere to reconcile against.

## PARTLY RESOLVED — `validate` importing the entrypoint

**Resolved (S3b docs pass, 2026-08-09).** The premise below is stale: `reference.md` § Generators
already states the capability outright ("It resolves at `validate`, not at `run` … That is also
the one thing `validate` executes"), and § What you define and § Exit codes and diagnostics both
restate it. The one clause that genuinely strained — "without looking at what any step does" in
§ A `batch` says *when*, not *what* — was reworded to say core reads the *declared class
attribute* off classes it has already imported to derive the plan, and never the step's body.
§ Validation gained a one-sentence pointer to § Generators rather than a second statement of the
rule. The three "consequences" below are code-ordering facts with no document text to change;
they stay here as the record.

## `validate` importing the entrypoint (as originally filed)

`reference.md` § A `batch` says *when*, not *what* says "`validate` warns when no step in the
pipeline sets `nondeterministic = True`", and calls it "a declaration-level check, so core can
make it: it compares the declared kind against the declared attribute, without looking at what
any step does". The second half is true of what is *compared* and misleading about what is
*read*: `nondeterministic` is a class attribute of a user step, so answering the check requires
importing the user's package. Before S3b, `validate` imported nothing of the user's — it
resolved the template from the registry and read the config — and `cli.py` imported the
entrypoint separately, after `validate_config` returned.

S3b's `W-REPL-DETERMINISTIC` therefore gives `validate` a capability no document states it has.
Warning at run time instead was considered and rejected: a warning is non-fatal, so the run
would proceed and spend exactly the compute the warning is about, and `validate` is the only
placement where warning saves anything.

Three consequences the documents should record along with the capability:

- **A failed import is now a `validate` finding.** A syntax error, a missing dependency, or a
  module-scope raise in a step module used to surface at `run`. It now surfaces at `validate`,
  as `E-ENTRYPOINT-IMPORT` (below), because `validate` collects and never raises to report.
- **The entrypoint import moved ahead of the `src/**`/`templates/**` dirty gate.** `command_run`
  calls `validate_config` before that gate, so an edit that both dirties the tree and breaks the
  import is now reported as an import failure rather than as `E-CODE-DIRTY`. The entry above
  describing `E-ENTRYPOINT-IMPORT` as "`run`'s phase-3 gate, checked after the dirty gate" is
  superseded for that reason.
- **`validate` executes module-scope user code.** It always did at `run`; the point is that
  `validate` is now no longer a read-only operation on the config, and the documents present it
  as one.

Proposed resolution: state in `reference.md` § Validation that `validate` imports the
`entrypoint`, list what that buys and what it costs, and drop "without looking at what any step
does" from § A `batch` says *when*, not *what* — it reads the step's declared attribute, which
is not the same as inspecting its body (core still never does that).

## NO DOCUMENT CHANGE — `E-ENTRYPOINT-IMPORT` widened at validate time

**Reviewed 2026-08-09 and deliberately not landed.** `E-ENTRYPOINT-IMPORT` is named in no
document, and the behaviour it describes already is: `reference.md` § Exit codes and diagnostics
lists "an experiment package that won't import" among the failures fatal on their own, and
§ Generators says an import failure fails `validate` with the import error as its message. What
this entry adds — that the catch is broad at validate time and narrow at run time, and that the
import now precedes the `src/**` dirty gate — is implementation ordering, not a rule a reader of
the four documents needs. Naming the code here would also half-land a validate-diagnostic
registry that does not exist (see the `W-REPL-DETERMINISTIC` entry). Kept as the record.

## `E-ENTRYPOINT-IMPORT` widened at validate time (as originally filed)

The entry above describes the code as raised by `load_experiment` for
`ImportError`/`ModuleNotFoundError`/`AttributeError` and a malformed `<module>:<attribute>`.
`validate_config` reports the same code for **any** exception the import raises, deliberately:
importing user code can fail every way user code can fail, and each of those must arrive as one
finding rather than a traceback. The broad catch is confined to that one call, and `run` keeps
the narrow raising form for the paths `validate` did not already cover.

`load_experiment` also moved from `cli.py` to `base_experiment.py` in S3b, so `validate.py` and
`cli.py` can both reach it without importing each other. That is not a layout divergence:
`reference.md` § Package layout already names `base_experiment.py`, and no new module was added.

## PARTLY RESOLVED — new warning identifier: `W-REPL-DETERMINISTIC`

**Resolved in part (S3b docs pass, 2026-08-09).** The name now appears in `reference.md`
§ A `batch` says *when*, not *what*, on the sentence that specifies the behaviour. The registry
half is **declined**: there is no warning registry to add it to. § Errors core raises is a
raise-time surface — the section says so itself ("the hierarchy above covers exactly the
run-time surface, where there is a step to raise into") — and a `validate` diagnostic does not
belong in it, the same reason the `E-SWEEP-*` validate codes were correctly left out. Minting a
warning registry to hold `W-TEMPLATE-VERSION`, `W-REPL-FLOOR`, `W-ENV-UNLOCKED`,
`W-EXEC-BUDGET`, `W-STATS-FAMILY`, and this one is a document design change, not an amendment;
it needs its own argument about where a diagnostic registry lives relative to § Validation's
check table, which already carries every one of those warnings as a row in prose form. Leaving
the gap open here rather than closing it badly.

## `W-REPL-DETERMINISTIC` (as originally filed)

`reference.md` § A `batch` says *when*, not *what* specifies the behaviour — "`validate` warns
when no step in the pipeline sets `nondeterministic = True`" — and `experimental-designs.md`
§ Repeat kinds says the same thing in prose. Neither names a code for it, and § Errors core
raises has no warning registry to have named it in. S3b mints `W-REPL-DETERMINISTIC`, reported
against `replication.repeats`, exactly when the declaration carries a `batch` level and no step
class on the loaded experiment sets `nondeterministic = True`.

Two properties worth fixing in the document along with the name. It does not fire when the
entrypoint could not be imported — `E-ENTRYPOINT-IMPORT` is already reported and a second
finding about a pipeline nobody could load is noise. It *does* fire alongside
`E-REPL-LEVEL-DUPLICATE` for a design declaring two `batch` levels: the duplicate refusal
reports and falls through, and the determinism warning is about a declaration that is
independently wrong.

Proposed resolution: name the code in `reference.md` § A `batch` says *when*, not *what*, and
add it to whichever registry warnings land in — the same gap `W-TEMPLATE-VERSION`,
`W-REPL-FLOOR`, and `W-ENV-UNLOCKED` are already sitting in.

## RESOLVED — new error identifier: `E-REPL-ORDER-UNRESOLVED`

**Landed (S3b docs pass, 2026-08-09)** in `reference.md` § Errors core raises, in one new row
shared with `E-RUN-SEED-MISSING`, `E-RUN-CFG-MISSING`, and `E-RUN-ORDER-MISMATCH` — see the
`E-RUN-ORDER-MISMATCH` entry below for why the four went in together and with a framing
paragraph rather than as four bare rows. The `LABEL_JOIN` contract between `cross_levels` and
`realize_order` stays undocumented deliberately: it is a constant internal to `replication.py`,
and the four documents describe the repeat directory name (`batch03_seed42`) rather than the
function that composes it.

## `E-REPL-ORDER-UNRESOLVED` (as originally filed)

`realize_order` (Task 6, S3b) groups the `(condition, leaf_label)` pairs it is given by the
resolved `batch` level's members, matching each pair's label against
`batch_level.members[i].label` rather than parsing a fixed prefix — see § A `batch` says
*when*, not *what*. Every pair `realize_order` sees today is built from the same `cross_levels`
call as the `levels` it is passed, so every label matches some member and the grouping is a
bijection over reachable input; nothing before Task 8 constructs `pairs` any other way.

Task 8 adds a second caller in `cli.py` that will construct `pairs` itself, which is exactly the
circumstance where a label could fail to match — a stale roster, a mismatched digest, or a
config edited between resolving `levels` and building `pairs`. A bare `next(...)` with no
default previously raised `StopIteration` on that path, which inside a generator/comprehension
context can be swallowed as ordinary iteration exhaustion rather than surfacing as an error —
one of the worst diagnostics Python offers for a real contract violation.

S3b mints `E-REPL-ORDER-UNRESOLVED`, raised by `realize_order` when a pair's label matches no
member of the resolved `batch` level, naming the offending pair and the batch labels it was
checked against. Proposed resolution: add the code to whichever registry `reference.md` § Errors
core raises keeps for `E-REPL-*`, alongside `E-REPL-SEED-COLLISION` and the level-shape codes.

Also worth recording: `cross_levels` composes leaf labels by joining members with `LABEL_JOIN`
(`"_"`), and `realize_order` groups by splitting on the same character — a real contract between
the two functions that no document states. S3b names it as a shared module-level constant in
`replication.py` rather than leaving it as a comment on one side, so a future change to the join
character cannot silently desynchronize from the split.

## RESOLVED — new error identifier: `E-STEP-READ-AMBIGUOUS`

**Landed during S3b itself.** `reference.md` § Errors core raises carries the row
("`io.read_upstream` from `summary` scope naming a condition- or repeat-scoped step, once the
sweep labels its conditions"), and § Step scope carries the explaining paragraph. Verified in
the 2026-08-09 docs pass; nothing outstanding.

## `E-STEP-READ-AMBIGUOUS` (as originally filed)

Task 7 (S3b) fixed `read_upstream` hard-coding `shared/` by resolving a target's directory from
its own scope. Doing that exposed a second gap in the same method: `SCOPE_ORDER` puts `summary`
above `run`, `condition`, and `repeat` alike, so the pre-existing direction check lets a
`summary` step call `io.read_upstream` naming a condition- or repeat-scoped step. A real
`summary` `Execution` (`scope.py::build_plan`) always carries `condition_index=None,
condition_label=None` — a summary step sits above every condition, not inside one — so once a
sweep labels its conditions there is no single condition for such a call to resolve to, and the
label-is-`None` fallback would silently resolve to `run_dir/step/name`, a path no writer uses
once `conditions/<nn>_<label>/` exists.

S3b mints `E-STEP-READ-AMBIGUOUS`, raised by `read_upstream` when the caller is `summary`-scoped,
the named step is `condition`- or `repeat`-scoped, and any of this run's resolved conditions
carries a non-`None` label — the label is the right discriminator because the `conditions/`
level appears when a sweep is *declared*, not when there is more than one condition: a bare
`sweep.baseline` still yields one condition, but with the level. The message points at
`io.read_condition`, which resolves the same read unambiguously by taking the condition as an
argument. With no sweep declared, `read_upstream` still resolves directly, since there is
exactly one, unlabeled condition and no `conditions/` level to be ambiguous about.

Proposed resolution: add the code, and the paragraph above `docs/reference.md` § Step scope now
carries describing it, to whichever registry `reference.md` § Errors core raises keeps for
`E-STEP-*`. Pinned by
`test_a_summary_step_cannot_read_upstream_from_a_labeled_sweep` in `tests/test_artifacts.py`.

## RESOLVED — new error identifier: `E-RUN-ORDER-MISMATCH`

**Landed (S3b docs pass, 2026-08-09)**, together with `E-REPL-ORDER-UNRESOLVED` and the two
older gaps this entry names, as one row in `reference.md` § Errors core raises plus a paragraph
establishing them as a class. The framing was the load-bearing part of the decision: that
table's own header says a `ContractError` is "your code asked for, or handed back, something its
declarations don't allow", and every pre-existing row is reachable from user code. Four
core-bug guards added as bare rows would read to someone deciding whether to use the tool as
four more mistakes they could make. The paragraph names them as core checking its own work,
says why they carry a code instead of being an `assert` (`python -O`), and says that seeing one
is a bug to report rather than a config to fix — which is the only thing a reader can act on.

## `E-RUN-ORDER-MISMATCH` (as originally filed)

Not in § Errors core raises, the same gap `E-RUN-CFG-MISSING` and `E-RUN-SEED-MISSING` are
already recorded above as having. `command_run` (`src/publishable/cli.py`) now reorders
`plan`'s repeat-scope executions to match `sweep.yaml`'s `execution_order` exactly — a recorded
order the run didn't follow would be worse than recording nothing — via a new
`_apply_execution_order(plan, execution_order)` helper. It raises `E-RUN-ORDER-MISMATCH` when a
repeat-scope execution in `plan` has no home among `execution_order`'s `(condition, repeat
label)` pairs: the same invariant class as `E-RUN-CFG-MISSING` — plan and resolved state
disagree, a core bug rather than a step failure — raised the same way, outside any
per-execution `try`.

In `command_run` this should be unreachable: `declared_pairs` (fed to `realize_order`) and
`plan`'s repeat-scope labels are both built from the same `conditions`/`repeats`/`levels`, so
they can never diverge in practice. The check exists anyway, as a `ContractError` rather than
an `assert`, per this project's error convention (`PublishableError` → `ContractError`, every
raise-time failure carrying a stable `E-` code, and `assert` vanishing under `python -O` is
exactly the wrong property for a guard on a condition nothing else detects). Pinned directly —
bypassing `command_run` — by
`test_a_plan_pair_missing_from_execution_order_is_a_core_bug` in `tests/test_cli.py`, which
constructs a `plan`/`execution_order` mismatch `_apply_execution_order` never resolves itself,
the same way `tests/test_runner.py` pins `E-RUN-CFG-MISSING` and `E-RUN-SEED-MISSING`.

Proposed resolution: add `E-RUN-ORDER-MISMATCH` alongside `E-RUN-CFG-MISSING` and
`E-RUN-SEED-MISSING` to § Errors core raises' registry in the same pass that closes that gap
for the other two.

## New error identifier: `E-REPL-LEVEL-BATCH-INNER`

Found by the S3b whole-branch review, not by any of the nine task reviews: it sits in the seam
between `resolve_repeats` (task 4) and `cross_levels` (task 3), each of which is correct on its
own.

`cross_levels` gives every leaf the *innermost* member's seed, and `_seed_members` derives a
level's seeds from `digest|kind` alone, independent of the outer member. That pairing is exactly
right when `batch` is the outer level — `reference.md` § A `batch` says *when*, not *what* is
explicit that a batch varies nothing the pipeline declares, so `batch01_seed42` and
`batch02_seed42` **should** draw alike. Declared the other way round it inverts:

```yaml
replication:
  repeats:
    - {kind: seed,  n: 2}
    - {kind: batch, n: 3}
```

validated clean and produced six leaves over three distinct seeds — `seed04_batch01` and
`seed26_batch01` handed the same `self.rng`, so in a pipeline whose only nondeterminism is the
seed they compute bit-identical answers. The declared `seed` level varied nothing but a directory
name, the run reported success, and a later `repeat_spread` would have reported a `kind: seed`
std of exactly zero as though it were a measurement. A second symptom shared the root:
`realize_order` finds the batch level by kind rather than by position, so it blocked on batch
regardless, and the composed labels and the directory tree said the opposite.

S3b mints `E-REPL-LEVEL-BATCH-INNER`, raised by `resolve_repeats` when a `batch` level is
declared at any position but the first, following the `E-REPL-LEVEL-DEPTH` /
`E-REPL-LEVEL-DUPLICATE` precedent — refusals that are properties of the declaration's shape, so
`validate` translates them into findings via `REPL_DECLARATION_CODES` rather than letting them
escape.

Refusing is the fix rather than re-deriving the leaf seed from the whole combo: that would break
the invariant the documents state, which is the entire point of the kind. Every design the
documents describe nests other levels *inside* a batch — the section fixes the outer batch order
and shuffles within one — so a batch nested inside a seed has no documented meaning to preserve.
The refusal also closes the `realize_order` symptom rather than leaving it latent: with batch
guaranteed outermost, find-by-kind and find-by-position coincide. Trivially lifted if a document
ever describes the inverted nesting.

Pinned by `test_a_batch_declared_inside_another_level_is_refused` (`tests/test_replication.py`)
and `test_a_batch_inside_another_level_is_refused` (`tests/test_validate.py`), with
`test_a_batch_declared_outermost_is_accepted` holding the accepted side.

Proposed resolution: no `reference.md` amendment is needed — the section already describes batch
as the outer level throughout, and this code makes the code follow it. The `E-REPL-LEVEL-*`
family is not in § Errors core raises at all (neither `-DEPTH` nor `-DUPLICATE` is listed); if
that registry ever gains declaration-time refusals, all three belong there together.

**AMENDED 2026-08-11 (H1 Validation): CLOSED, and the registry the last sentence hoped for
exists.** All of `E-REPL-LEVEL-BATCH-INNER`, `-DEPTH`, `-DUPLICATE`, and `-FIELD` are declaration-
time refusals — every one is caught by `validate._check_replication`'s `REPL_DECLARATION_CODES`
translation of `resolve_repeats`, never left to escape as a raised exception — so § Errors core
raises was never their registry to begin with. All four now have rows in `reference.md` § Errors
`validate` reports, together with the `fold`-count siblings `E-REPL-FOLD-K`,
`E-REPL-FOLD-K-TOO-LARGE`, and `E-REPL-FOLD-NO-UNITS`. Nothing owes this entry.

## `SystemExit` at module scope escapes `validate`'s broad catch

Logged, not fixed, per the S3b whole-branch review's triage.

`validate.py`'s entrypoint import catches `Exception` and reports `E-ENTRYPOINT-IMPORT` as a
finding, so a user package that raises at import scope produces a diagnostic rather than a
traceback. `SystemExit` and `KeyboardInterrupt` derive from `BaseException`, not `Exception`, so
a module-scope `sys.exit()` — an `argparse` module parsed at import time, a
`if not os.environ.get(...): sys.exit(1)` guard — terminates `validate` with no diagnostic at
all and an exit code the user's module chose. That is the "silent" half of the failure mode
`E-ENTRYPOINT-IMPORT` exists to prevent, and it defeats the exit-code contract in
`reference.md` § Exit codes and diagnostics.

Not fixed here because the right catch is not obviously `BaseException`: swallowing
`KeyboardInterrupt` would make `validate` un-interruptible, which is worse in the common case
than a missing diagnostic in the rare one. The narrow fix is to catch `SystemExit` specifically,
beside the existing `except Exception`, and report it as `E-ENTRYPOINT-IMPORT` with a message
naming the exit call — an ordinary import must not decide the process's fate.

Proposed resolution: add the `except SystemExit` arm with a test that produces
`E-ENTRYPOINT-IMPORT` from a module whose body calls `sys.exit`, in whichever slice next touches
`validate`'s import path.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): RESOLVED — and this entry is the audit's exhibit
for why a deferral must name a slice.** "Whichever slice next touches `validate`'s import path" was
satisfied by S4a, S4b, S4c, S4d, S5a and S5b, and honoured by none of them; it took a checkpoint
task commissioned by name (task 11 of `docs/superpowers/plans/2026-08-11-s5-checkpoint.md`) to land
the two-line arm. `validate.py` now catches `SystemExit` beside `except Exception` and reports
`E-ENTRYPOINT-IMPORT`. One finding from that task worth carrying: `SystemExit` does **not**
subclass `Exception`, so the new arm's placement above `except Exception` is convention, not
correctness. A bare `BaseException` subclass raised at module scope still escapes, judged
acceptable — no stdlib type does this at import, and catching `KeyboardInterrupt` would break
Ctrl-C. Nothing owes this entry.

## RESOLVED: A `summary` step's `read_upstream` to a `repeat`-scoped step has no repeat to resolve

Found while fixing the S3b whole-branch review's I2, which was the same defect one scope over.
`read_upstream` resolves a `repeat`-scoped target to its repeat directory by reusing
`read_condition`'s rule (`StepIO._nest_repeat`), taking the segment from the calling execution's
own `repeat_label`. A `summary` execution has none — `scope.py::build_plan` gives a summary step
no repeat, because it sits above every one of them — so `_nest_repeat` returned the un-nested
base and the read resolved to a path nothing wrote. Verified directly on a no-sweep run with two
repeats: `runner.step_dir_for` writes `run_dir/seed17/fit`, and a summary caller's
`read_upstream("fit", …)` resolved `run_dir/fit/x.json`.

`E-STEP-READ-AMBIGUOUS` did not cover it: that code fired only when a sweep labels the run's
conditions, and this was reachable with no `sweep` block at all.

**Resolution taken: the first of the two proposed, "refuse it."** `read_upstream` now refuses a
`summary` caller naming a `repeat`-scoped step whenever the run resolved more than one repeat,
whether or not a sweep labels the conditions — the same `E-STEP-READ-AMBIGUOUS` code, no sibling
minted, with the message extended to name either cause and still point at
`io.read_condition(condition, step, name, repeat=…)`. The discriminator is the same collapse
rule `read_condition` already used to decide whether a repeat directory exists at all
(`len(self._repeats or []) <= 1`), so the reader and the writer cannot drift on when the level
collapses. With exactly one repeat the directory collapses, `run_dir/<step>/<name>` is genuinely
correct, and the read keeps working.

`docs/reference.md` § Step scope now states the repeat case beside the condition case it already
described. Pinned by
`test_a_summary_step_cannot_read_upstream_from_a_repeat_scoped_step_with_several_repeats` (the
new refusal) and `test_a_summary_step_reads_upstream_from_a_repeat_scoped_step_with_one_repeat`
(the collapse case a careless fix would have broken), both in `tests/test_artifacts.py`, beside
the pre-existing `test_a_summary_step_cannot_read_upstream_from_a_labeled_sweep` and
`test_a_summary_step_reads_upstream_from_every_narrower_scope_in_a_no_sweep_run`, which still
pass unchanged.

## RESOLVED: `_handed_keys`'s no-match fallback silently returned the whole roster

Found in code review of the fold-repeats S3c slice, Task 6. `runner._handed_keys` (introduced by
that task to fix `_units_failed_anywhere`'s roster-wide subtraction under a fold) fell back to
returning the whole roster when a repeat label's components matched no `fold_members` key. That
fallback was reachable only by a core defect, never by user input: `fold_members_for` returns
`None` unless a `fold` level is declared, and `cross_levels` composes every leaf label from every
declared level, so under a non-`None` `fold_members` every repeat label carries a fold token by
construction. But its only possible failure mode was silently resurrecting the exact bug Task 6
fixed — subtracting from the whole roster, counting every unit outside an execution's own
partition as failed, and aborting the run at `max_failed_fraction` on a healthy fold.

`E-REPL-ORDER-UNRESOLVED` was considered and rejected as a reuse: it covers a batch member
unresolvable against a *realized order* pair, a distinct fault surface (order realization in
`replication.py`, not per-execution membership in `runner.py`) even though the shape — a composed
label failing to match any resolved group — rhymes.

**Resolution taken:** mint `E-RUN-FOLD-UNRESOLVED`, raised as a `ContractError` from
`_handed_keys` naming the offending repeat label, alongside `E-RUN-SEED-MISSING`,
`E-RUN-CFG-MISSING`, and `E-RUN-ORDER-MISMATCH` in the same "core's execution plan disagreeing
with the state core resolved beside it" family — loud rather than a silent default, since an
`assert` disappears under `python -O` and a default would produce plausible wrong numbers.
`docs/reference.md` § Errors core raises lists it beside its three siblings, and the row's prose
now says "those five" instead of "those four." Pinned by
`test_a_label_with_no_fold_component_raises_rather_than_falling_back` in `tests/test_runner.py`,
calling `_handed_keys` directly with a label carrying no fold token — a unit-level test, since a
real run can never reach this state and contorting one into it would test nothing real.

## RESOLVED: a `fold` level with no `data.units` validated clean and then either crashed or ran a fold-shaped `sweep.yaml` over nothing

Found in code review of the fold-repeats S3c slice, Task 9. `resolve_repeats` accepts a fixed
`{kind: fold, k: N}` with `unit_count=None` — only `k: all` needs a real count, and that path
already reports `E-REPL-FOLD-K` — so `validate` raised nothing for a `fold` level declared
alongside no `data.units` block at all. At `run`, `cli.py` computed `partitions = None` in that
case and passed `fold_members_for(levels, partitions or [])`: `fold_members_for` zips the fold
level's members against the empty list with `strict=True`, so it raised a bare `ValueError`
`main` does not catch (it catches `PublishableError`), producing a traceback with no `E-` code
for a config that had just validated clean. Guarding only the `run`-time path would have left the
alternative outcome standing, which is worse than the crash: `k` roster-less repeats completing
identically while `sweep.yaml` and `run.yaml` describe a k-fold cross-validation that never
partitioned anything. This project refuses that shape — a config that validates clean must not
then fail or lie about what ran.

No existing code fit: `E-DATA-REQUIRED`/`E-DATA-UNREADABLE` are `data.input_dir`/`data.output_dir`
presence checks with no view of `replication.repeats`, and every `E-REPL-FOLD-*` code names a
defect in the fold's own count (`k`), not in the roster it would partition.

**Resolution taken:** mint `E-REPL-FOLD-NO-UNITS`, raised by `_check_replication` in `validate.py`
as soon as any declared repeat level is `kind: fold` and `data.units` is absent — before
`resolve_repeats` runs, alongside the other declaration-shape checks in that function (it is not
one of `resolve_repeats`'s own refusals, so it is not added to `REPL_DECLARATION_CODES`). This
makes the `run`-time crash unreachable by construction rather than merely caught: `cli.py` still
guards `partition_units`/`fold_members_for` behind a `roster is None` refusal inside the
`fold_level is not None` branch (defensive, matching the pattern the rest of `command_run` uses
when a check upstream is expected to have already refused), but a config that reaches that line
with a fold and no roster is now a config `validate` already rejected. That guard was written as
a bare `assert` and is now a `ContractError` carrying `E-RUN-FOLD-UNRESOLVED` — see the
whole-branch entry below. Pinned by
`test_a_fold_level_with_no_units_declared_is_refused` in `tests/test_validate.py`, calling
`validate_config` directly (through the collector, not `resolve_repeats`) so the assertion is
against the same surface a user's `publishable validate` run reports.

## RESOLVED: a repeat level's count field was read by precedence, so one declaration meant two different things to two readers

Found in the whole-branch review of the fold-repeats S3c slice (Important 2). `reference.md`
§ Repeat kinds gives each repeat kind its own fields *and only these*: a `fold` takes `k` and an
optional `stratify_by`, a `seed` and a `batch` take `n`. Nothing enforced it. `resolve_repeats`
dispatches on `kind` and reads only `k` for a fold, while both `_check_replication` and
`_repeat_total` in `validate.py` read `n` first and fell back to `k` for every kind. So
`{kind: fold, k: 2, n: 5}` validated clean, `W-EXEC-BUDGET` reported five executions, and the run
executed two folds — the recorded warning stating a count the run would never execute. The mirror
(`{kind: seed, n: 2, k: 9}`) silently accepted and ignored a `k`. Unreachable before this slice,
because `fold` was refused by name and `k` was therefore never a live field; making `fold` live
made it live.

Teaching the budget check to ignore the wrong field was rejected: a config that means two
different things to two readers is itself the defect, and silently preferring one reading hides
it. No existing code fit — `E-REPL-N` names an out-of-range count rather than a misplaced one,
`E-REPL-FOLD-K` names a malformed fold count (and `{kind: fold, n: 5}` would report it as
"`k: None` is not a fold count", which sends the reader after the wrong field), and
`E-REPL-KIND` names an unrecognised kind.

**Resolution taken:** mint `E-REPL-LEVEL-FIELD`, raised by `_check_count_field` in
`replication.py` for a level declaring the count key its kind does not take, in the same
declaration-shape family as `E-REPL-LEVEL-DUPLICATE` and added to `REPL_DECLARATION_CODES` so
`validate` collects it rather than letting it escape. It is checked after the kind checks (so an
unknown kind still gets `E-REPL-KIND`) and before `_fold_k` (so the reader is told which field
was ignored). The arithmetic half of the same rule lives in `validate.py`'s `_declared_count`,
which reads `k` for a fold and `n` otherwise, so every count `validate` derives is the count the
run executes. Pinned by `test_a_fold_declaring_n_is_refused_rather_than_read_two_ways` and
`test_a_seed_declaring_k_is_refused_the_same_way` in `tests/test_validate.py`, both through
`validate_config`. Refusing *unknown* keys wholesale (`{kind: fold, k: 2, wibble: 7}`) is a
larger change and is deliberately not taken here; only the `n`/`k` cross-talk produces a wrong
number.

Two document consequences. `reference.md` § Validation has listed **"Batch takes no fields —
`{kind: batch, k: 3}`"** as a check since before anything enforced it; that row is now true, and
is pinned. A sibling row, "Each kind takes its own count", was added beside it for the `fold`
half, which the table did not name. § Repeat kinds needed no edit — it already said each kind
takes its own fields "and only these", so this is the code coming to follow the document.

One trap worth recording, hit while writing the arithmetic half. Distinguishing "declared but
unresolvable" from "absent" by `_declared_count(level) is not None` made *any* unreadable count
suppress `W-EXEC-BUDGET` for the whole config — including `n: yes`, which `yaml.safe_load`
parses as a bool and which `resolve_repeats` runs as one repeat. That is the same silent-skip
this pass exists to end, reintroduced one layer up. The test is `isinstance(..., str)`: a count
declared as a *word* can be genuinely unknown, and everything else executes 1× and is reported
under its own identifier. Pinned by
`test_an_unreadable_count_that_is_not_a_word_still_leaves_the_budget_computable`.

## RESOLVED: two bare `assert`s guarded fold invariants the documents say must carry a code

Found in the whole-branch review of the fold-repeats S3c slice (Important 3). `cli.py` asserted
`roster is not None` before `partition_units`, and `sweep.py` asserted a `fold` level exists
before pairing `partitions` with its member labels. Both are unreachable — `validate` refuses a
fold with no roster (`E-REPL-FOLD-NO-UNITS`), and `partitions` is built only inside the
`fold_level is not None` branch — but unreachability is exactly the property `_handed_keys`'s
fallback had when this same slice minted `E-RUN-FOLD-UNRESOLVED` for it. `docs/reference.md`
§ Errors core raises, in a line this branch rewrote, says core signals these with a stable `E-`
code rather than an `assert` because `assert` disappears under `python -O` — "precisely the wrong
property for the only guard on a condition nothing else detects". Under `-O` the two degraded to
`partition_units(None, ...)` → `TypeError` and `zip(None.members, ...)` → `AttributeError`,
neither carrying a code and neither caught by `main`'s `PublishableError` handler.

**Resolution taken:** raise `ContractError` at both sites, reusing `E-RUN-FOLD-UNRESOLVED` rather
than minting. Both faults are the same one that code already names — core's resolved state
disagreeing with itself about a declared fold — and reusing keeps `reference.md`'s "those five"
count correct; the row's description is widened to cover a fold whose roster or partitions core
cannot pair. `sweep.py` stays pure: `errors.py` has no dependencies and no I/O, and the module
docstring now says so. Pinned by
`test_partitions_with_no_fold_level_raise_a_coded_error_rather_than_asserting` in
`tests/test_sweep.py`; the `cli.py` site is not separately pinned, because reaching it requires
bypassing `validate` entirely and the identifier is already produced by two tests.

## New error identifier: `E-STEP-COLUMN-UNKNOWN`

**AMENDED 2026-08-11 (S5 checkpoint audit):** Landed. The row is in
`reference.md` § Errors core raises; recorded at entry line 1515.

Found while building `UnitTable`, the four-operation table a template's `aggregate` receives
(S4a task 3). Attribute access is how the worked example reads a column — `units.pred`,
`units.truth` — so a name that is not a recorded column has to fail through the same path, and
every sibling refusal in this family (`E-STEP-PARAM-UNKNOWN` for `cfg`, `E-STEP-UNITS-UNAVAILABLE`
for `io.units`) is a `ContractError` with its own code rather than the bare `AttributeError`
Python would raise on its own.

`docs/reference.md` § Errors core raises was grepped first for this identifier and for a
plausible synonym under the `E-STEP-*` family; neither existed, so this is genuinely new rather
than a rediscovery of an existing code under different wording.

Raised by `UnitTable.__getattr__` when the name is not underscore-prefixed (which stays a plain
`AttributeError`, since dunder and private-attribute probes are not a step author's mistake) and
no row carries that key. Pinned by `test_an_unknown_column_raises` in `tests/test_stats.py`.

Proposed resolution: add a row to `reference.md` § Errors core raises alongside
`E-STEP-PARAM-UNKNOWN` — both are "a name the step reached for that core's structure doesn't
hold." Not yet done in this pass because the row also documents `aggregate`'s four operations,
which belongs with whichever task first writes that section of prose rather than being added
piecemeal by the task that only builds the class.

## RETIRED — a derived metric's `ci95` was resampled without recomputing `aggregate`

Filed when S4a task 6 first landed `summarize_step`'s `derived` handling: with `derived` pinned
to a bare `dict[str, float]` (name → the single scalar `aggregate` already returned) and
`aggregate` called only once per recording step, `summarize_step` had no callable and no
`UnitTable` to recompute anything with, so it built a generic per-unit surrogate (summed rows,
recentered on the reported value) instead of the recomputation `reference.md` § How a metric
becomes a number specifies. That surrogate's width was a proxy for "how much units in this table
vary," not for how the actual derived quantity — a sum, a ratio, a correlation — propagates that
variation, and could be substantially wrong for exactly the worked example's own metric, `r`.

**Resolved in the same slice, before task 6 closed**, once the interface gap was named instead of
worked around: `summarize_step` gained a third parameter, `resample: dict[str, Callable[[UnitTable],
float | None]] | None`, one callable per derived key that recomputes it on a resampled table.
`percentile_of_derived` (new in `stats.py`) draws bootstrap unit samples, builds a `UnitTable` from
each, and calls the supplied callable — `cli.py` supplies `lambda units: template.aggregate(units,
cfg).get(key)`, since that is where the template and `cfg` live; `stats.py` still imports neither. A
derived key with no matching `resample` entry now reports `ci95: null` rather than an invented
width, which is the honest answer `t_over_units` already gives below two units. No document
change was needed: the implementation now follows `reference.md` as written, so there is nothing
left to record as a gap. Pinned by
`test_a_correlation_like_derived_metrics_interval_reflects_its_own_scatter` in
`tests/test_stats.py` — two fixtures with nearly the same Pearson `r` but very different
sensitivity to resampling, which a summed-row surrogate could not have told apart because it never
looks at the correlation at all.

## New warning identifier: `W-STATS-AGGREGATE-FAILED`; and four quality fixes to the resample

Found by the review of S4a task 6's `aggregate`-recomputation landing, against the still-live
`cli.py`/`stats.py` from the entry above.

**The identifier.** `template.aggregate` is user code, in exactly the sense a step's `run` is —
`runner.py` wraps that call in `except Exception: # a failed execution never stops the run` — but
the single unresampled call to `aggregate` in `cli.py` (phase 8, after every execution has already
completed) sat outside any such guard. `main()` catches only `PublishableError` and `OSError`, so
a template whose `aggregate` raised anything else (a `ZeroDivisionError` on a degenerate ratio, a
`KeyError`) produced a bare traceback, no `run.yaml` at all, and discarded every completed
execution over one metric core could not compute. `docs/reference.md` § Errors core raises has no
entry for a derived-metric failure, and no plausible synonym, so `W-STATS-AGGREGATE-FAILED` is new.
Raised as a warning, not an error: the run's `status` (already decided by the executions, all of
which completed) is deliberately left alone — a metric that could not be computed is not the same
fact as a run that did not happen. Pinned by
`test_a_failing_aggregate_does_not_cost_the_run_its_record` in `tests/test_cli.py`. Proposed
resolution: add a row to `reference.md` § Errors core raises once that section is next touched,
alongside `W-STATS-FAMILY`.

**Unit identity on a resampled draw.** `percentile_of_derived` built each draw's `UnitTable` by
re-keying to `str(i)` for `i` in `range(n)`, because a resampled draw repeats units and a `dict`
cannot hold two rows under one key — but `UnitTable` derives its `unit` column from that key, so
every draw's units read as `n` distinct labels even though a bootstrap draw duplicates some and
omits others by construction. A template that legitimately reads `unit` (a per-unit lookup keyed
by it) would see the wrong roster on every draw. Fixed with `_unit_table_from_rows`, a new private
constructor that bypasses `UnitTable.__init__`'s dict-keyed signature and builds rows directly,
preserving the real (possibly repeated) unit key per row. Pinned by
`test_a_resampled_draw_reports_the_real_unit_key_not_a_synthetic_index`.

**`draws` was unreachable.** `percentile_of_derived` always took its 2000 default because
`summarize_step` had no parameter to pass one through. Added as `summarize_step(..., draws: int =
2000)`, threaded to `percentile_of_derived`. Pinned by `test_draws_is_reachable_through_
summarize_step`.

**The surviving-draw count was undisclosed.** A `compute` that returns `None`/`nan` on some draws
(§ How a metric becomes a number's `weight_by`/`cluster_by` sections use `n.effective` and
`n.clusters` for the analogous disclosure over *units*, but neither is the right field — those
describe the roster, not the resample) shrinks the interval's effective draw count silently: an
interval built from 200 of 2000 requested draws read identically to a clean one. `reference.md`
was grepped for an existing field name for this and none exists, so a minimal one was added:
`Interval` gained an optional `draws_used: int | None`, `None` for every construction over raw
values and set by `percentile_of_derived` alone, and a derived metric's `run.yaml` entry gained
`resample_draws`, alongside `ci95`/`method`/`cohens_d`. Pinned by
`test_resample_draws_discloses_a_shrunken_surviving_count`. Proposed resolution: add
`resample_draws` to the § How a metric becomes a number derived-metric shape once that section
next changes.

**The resample closure bypassed `coerce_scalars`.** `cli.py`'s per-draw closure did a bare
`float(value)` on `template.aggregate(...).get(key)`, while the same call for the reported `value`
went through `coerce_scalars`. A structural return (a list, a dict) `TypeError`d instead of raising
the `ContractError` the main call would have — indistinguishable from the Critical above until the
call site was checked. Routed through `coerce_scalars` in both places now.

**Raise-versus-`nan` inside a resample draw.** Once the Critical above was contained, whether a
*resample draw's* raise should also be treated as degenerate (rather than caught only at the
`cli.py` call site, which would fail the whole interval on the first bad draw of up to 2000) needed
deciding. `percentile_of_derived` now catches `Exception` around each draw's `compute` call and
drops the draw, exactly like a `None`/`nan` return — the reasoning is that which library `aggregate`
happens to call (one that returns `nan` on degenerate input versus one that raises) is not a fact
about whether the draw was degenerate, so it cannot be what decides whether the draw counts. This
does not extend to the single unresampled call: that one is the metric's real definition for the
real table, not a draw, and its failure is the Critical's `W-STATS-AGGREGATE-FAILED` case instead.
Pinned by `test_a_raising_compute_is_treated_as_degenerate_not_propagated` and, at the integration
level, `test_a_raising_resample_draw_does_not_crash_the_run`.

Also added: `test_percentile_ranks_are_symmetric_at_the_default_draw_count`, pinning
`_percentile_ranks(2000, 0.95) == (49, 1949)` directly — the shared rank arithmetic is genuinely one
copy, and this is what catches an asymmetry reappearing in it without driving 2000 draws through a
resample to see it (the defect Task 4 already had once).

## Two `repeat_spread` figures the S4a passenger declines to compute, rather than compute wrong

Found in review of S4a task 7's landing. Both are "no entry over a wrong one" refusals, not
implemented gaps waiting to be filled casually — each would need a genuinely heavier operation
than this passenger does, and `docs/reference.md` § A `batch` says *when*, not *what* does not
specify either construction closely enough to build blind.

**A `fold` level nested with another level omits `repeat_spread` entirely, not just the fold's own
entry.** `reference.md:1632-1638` shows `fold x seed` reporting two entries — `{kind: fold}` and
`{kind: seed}` — each "recomputing the metric over that level's slice." That is a materially
different operation from the per-member mean-of-recorded-values this passenger computes for
`seed`/`batch`: recomputing "the metric" over a fold's slice means re-deriving whatever the
condition's real metric is (a per-unit mean, or a template's `aggregate`) on that fold's own
partition, not averaging raw recorded values across the fold's members. Rather than report the
inner level's simple figure alone under a key the document specifies as two recomputed numbers,
`repeat_spread` returns `[]` for the whole result whenever a `fold` level appears alongside
another level. A bare `fold` (no other level) already returned `[]` for the reason
`docs/superpowers/specs/2026-08-10-derived-metrics-design.md` § `repeat_spread`, a passenger
states — nothing to average across, one fold per unit — and this extends the same refusal to the
nested case rather than leaving it to compute a number the document doesn't mean. Pinned by
`test_a_fold_nested_with_another_level_is_omitted_entirely`. Proposed resolution: a future slice
that threads a per-slice `aggregate` recompute through `cli.py` (the same shape
`percentile_of_derived` already uses for resampling) can replace the omission with the two-entry
figure the document shows.

**A derived (`aggregate`-computed) metric gets no `repeat_spread` at all**, even though
`reference.md:1979`'s worked-example `r` — itself `aggregate`-derived — shows one. Computing a
derived metric's per-member mean honestly means recomputing `aggregate` over that member's own
collapsed subset of units, the same "recompute rather than average a proxy" rule
`percentile_of_derived` already follows for a derived metric's `ci95`. `stats.py` stays pure and
`repeat_spread` takes no template/`cfg`, so doing this from inside `stats.py` isn't possible without
threading a callable through from `cli.py` exactly the way `resample_fns` does for the interval —
undertaken here would have doubled this task's surface for a figure no test in the brief asked
for. `cli.py` now computes `repeat_spread` only for the columns `collapse_repeats` actually
collapsed (i.e., genuinely recorded per-unit values), and skips every key that came from `derived`.
Proposed resolution: extend the `resample_fns`-style closure to also drive `repeat_spread`'s
per-member mean for a derived key, once a slice actually needs it.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): both figures OPEN, ONE OWNER NAMED.** "A future
slice that threads a per-slice `aggregate` recompute through `cli.py`" and "once a slice actually
needs it" were descriptions. **Owner for both: H4 Statistics** (spine § The hardening slices).
They are one piece of work, not two: the nested-`fold` figure and the derived-metric figure both
need the same `resample_fns`-shaped closure threaded from `cli.py` into `stats.py`, and building it
twice is how one of them ends up computing a different number than the other. H4 is ordered after
H3 Units for the related reason that H3 is what makes a `fold` level real.

## `resample_draws: null` and `resample_draws: 0` were the same fact until this fix

Found by the second review round of S4a task 6's resample landing (against the fixes recorded in
the entry above, still on `938e1c7`/`1819874`).

**`draws` stayed unreachable in production.** `summarize_step` grew a `draws` parameter, but
`cli.py`'s only call site never passed one, so every real run stayed hardcoded to the 2000
default regardless — reachable from tests, from nowhere else. Fixed by naming the value at the
call site, `derived_metric_draws = 2000`, and passing it explicitly; the value is unchanged
(`statistics.resample` still isn't honored, so there is nothing else to pass), but the plumbing is
now visible end to end rather than resting on an unwired parameter.

**Total resample failure was indistinguishable from no resample at all.** `percentile_of_derived`
returned a bare `Interval | None`, so "every draw raised or returned `nan`" and "nobody supplied a
`resample` callable" both produced `ci95: null` with nothing else to tell them apart — and the
unit-identity fix in the entry above makes the first case *more* likely, not less: a bootstrap
draw now carries real, duplicated unit keys, so a template whose `aggregate` assumes distinct ones
raises on every single draw rather than some. Fixed by widening `percentile_of_derived`'s return
to `tuple[Interval | None, int]`, the second element the surviving-draw count *always*, even when
the interval is `None`; `summarize_step` now reports `resample_draws: null` only when resampling
was never attempted (no callable, or no `seed`) and `resample_draws: 0` when it was attempted and
every draw failed. `Interval.draws_used`, added in the entry above as the field carrying this,
was removed — the tuple is now the one source of truth rather than a value duplicated onto both.

**The two failure classes are disclosed the same way and cannot both fire for one metric.**
`cli.py` now checks every metric's `resample_draws` after `summarize_step` returns, and warns with
the *same* identifier, `W-STATS-AGGREGATE-FAILED`, when it is `0` — reusing rather than minting a
second one, since both are the same class of event (user code could not produce a number). The two
paths are mutually exclusive per metric: a failure in the single unresampled call already removes
that key from `derived` (and so from `step_summary`) entirely, so the per-metric total-failure
check can never also see it. `status` is left alone in both cases, for the same reason recorded
above — a metric that could not be computed is not the same fact as a run that did not happen —
and a comment that had claimed the disclosure worked "the same way `E-INPUT-CHANGED` is" was
corrected: that path *does* set `status = "failed"`, for an unrelated reason (the input data a
completed run rested on changed), and the similarity claimed was false. The disclosure remains
stdout-only; `run.yaml` has no diagnostics channel to carry a finding that isn't a metric, an
interval, or a status, which is worth recording here rather than treating as a gap to close, since
adding one is a schema change with its own cross-document consequences.

Pinned by `test_total_resample_failure_is_distinguishable_from_no_resample_supplied` (unit level)
and `test_a_total_resample_failure_is_disclosed_not_silent` (integration level, `tests/test_cli.py`
— empirically confirmed to exercise the `resample_draws: 0` branch deterministically, not just
possibly). The unit-identity test from the entry above,
`test_a_resampled_draw_reports_the_real_unit_key_not_a_synthetic_index`, was also tightened per
review: it previously asserted only that each draw's keys were a subset of the real roster at the
right length, which a synthetic re-key would also satisfy — it now asserts a repeated key actually
appears in at least one draw, the property the fix exists to produce.

**Deferred to the whole-branch review, not fixed here:** `_percentile_ranks(1, confidence)` returns
`(0, 0)` — a one-draw pool's single value reported as both bounds of a degenerate interval — and is
unpinned by any test.

**AMENDED 2026-08-15 (spec-defects staleness audit at `5578988`): the first fix's parenthetical is
now false.** "`statistics.resample` still isn't honored, so there is nothing else to pass" was true
when written. H4a made a declared `resample` real, and `cli.py` now sets
`derived_metric_draws = resample_spec["n"]` when the config declares one, keeping the named 2000
default when it does not — so the value this fix made visible end to end is exactly the one a
config now supplies. Nothing else in the entry changes; the `null`/`0` distinction it minted is
unaffected.

## New error identifiers: `E-STATS-CONTRASTS-UNSUPPORTED`, `E-STATS-RESAMPLE-UNSUPPORTED`, `E-STATS-NULLTEST-UNSUPPORTED`, `E-STATS-REPORTBY-UNSUPPORTED`, `E-HYPOTHESIS-UNSUPPORTED`

**Retirement status:** `E-STATS-CONTRASTS-UNSUPPORTED` retired with S4b,
`E-STATS-REPORTBY-UNSUPPORTED` with S4d, and `E-HYPOTHESIS-UNSUPPORTED` with S5b — each when its
slice implemented the block, and S5b's in the same commit that made `cli` evaluate, so `validate`
never accepted a hypothesis nothing honoured. The two that remain — `-RESAMPLE-` and `-NULLTEST-`
— are still live refusals. A retired code is gone from `src/`, `tests/` and the four documents;
the entries below are history and stay. One deliberate exception: `tests/test_validate.py` keeps
`assert "E-HYPOTHESIS-UNSUPPORTED" not in found` as the retirement's own regression guard, on the
precedent `test_declared_report_by_is_checked_rather_than_refused` set — a negative assertion is
not a surviving use.

S4a task 8. A declared `statistics.contrasts`, `.resample`, `.null_test`, or `.report_by` block,
or a top-level `hypotheses` block, validated clean and was read by nothing — the same silent-no-op
class `E-SWEEP-PAIRED-UNSUPPORTED` and the `data.units` sub-field refusals already close for their
own blocks. A config declaring a 2000-draw bootstrap and a pre-registered hypothesis ran, reported
success, and honored neither. `_check_unimplemented` (`validate.py`) now refuses each the same
way: a real declaration is an error naming the identifier above, and each message says the block
is specified but not implemented in this build and will be honored in a later slice, matching the
register the sibling `-UNSUPPORTED` messages already use.

`statistics.correction` stays exactly as it is — disclosed rather than refused, via
`W-STATS-FAMILY` and a `correction: null` recorded on every aggregated metric — since a
warned-and-marked declaration is not a declaration that changes nothing while claiming otherwise;
it is deliberately excluded from this refusal.

Every check fires on a *real* declaration, not on the key's mere presence: an empty list
(`contrasts: []`, `report_by: []`, `hypotheses: []`) or a `null` mapping (`resample: null`,
`null_test: null`) is exactly what a hand-edited-empty or freshly generated config holds and must
not be refused. Checked directly against a fresh scaffold (`publishable new` → `generate
experiment` → `validate`), which currently writes only `statistics.correction` and `hypotheses:
[]` — `materialize.py` does not yet emit `contrasts`/`resample`/`null_test`/`report_by` keys at
all, empty or otherwise, so the absent-key case and the empty-value case both had to be verified
non-refusing.

Pinned by `test_declared_contrasts_are_refused`, `test_a_declared_resample_is_refused`,
`test_a_declared_null_test_is_refused`, `test_declared_report_by_is_refused`,
`test_a_declared_hypothesis_is_refused`, `test_empty_declarations_are_not_refused`, and
`test_correction_is_still_not_refused` — all in `tests/test_validate.py`, all exercised through
`validate_config` rather than any internal check directly.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): the two live refusals now name their retiring
slice.** `E-STATS-RESAMPLE-UNSUPPORTED` and `E-STATS-NULLTEST-UNSUPPORTED` **retire with H4
Statistics** (spine § The hardening slices), which owns `statistics.resample` and
`statistics.null_test`. The messages' "will be honored in a later slice" wording is a user-facing
string and is left alone — a diagnostic should not name this repository's internal slice IDs — but
the *ledger's* deferral now has an owner, which is what was missing. The three retired codes need
nothing further.

**AMENDED 2026-08-15 (spec-defects staleness audit at `5578988`): one of the two live refusals has
retired; `E-STATS-NULLTEST-UNSUPPORTED` is the only one left.**
`E-STATS-RESAMPLE-UNSUPPORTED` retired with **H4a**, which honours a declared `statistics.resample`
for real — method enum, draw count, strata, column metrics, clustered metrics, derived metrics and
column contrasts. It is gone from `src/` (zero occurrences) and from the four documents;
`reference.md` § The one config file records the block *leaving* the `NOT BUILT` list rather than
still naming it. Two surviving mentions, both deliberate and neither a use: `tests/test_validate.py`
keeps `assert "E-STATS-RESAMPLE-UNSUPPORTED" not in found` and a sweep asserting no source file
carries the string — the same negative-assertion exception `E-HYPOTHESIS-UNSUPPORTED` already holds,
now its second instance — and `docs/feasibility-llm-growth-studies.md` § Executability on this build
names it inside a dated measurement, which is a feasibility analysis and not one of the four
documents. `E-STATS-NULLTEST-UNSUPPORTED` is unchanged and still live; its retiring slice is
**H4d** specifically, which the 2026-08-11 amendment above could only name as the H4 family.

## S4a whole-branch review: four defects fixed, and what `reference.md` gained

The whole-branch review of `s4a-derived-metrics` found two Criticals and five Importants. Four
were fixed on the branch; the document changes they implied are in `reference.md` rather than
deferred here, because each is a permanent, user-visible surface and CLAUDE.md's "the document
changes first" governs an addition to the artifact schema directly.

**`E-STEP-KEY-COLLISION` escaped the containment task 6 built.** `summarize_step` refuses a
derived key that shadows a recorded column, and that call sat outside the `try` wrapped around
`template.aggregate` — so a template returning a name the step also recorded exited 1 with no
`run.yaml`, discarding every completed execution, while the sibling case (a structural return)
merely warned. The refusal is unchanged; `cli.py` now contains it exactly as it contains a
coercion failure, dropping the whole `derived` mapping and disclosing
`W-STATS-AGGREGATE-FAILED … E-STEP-KEY-COLLISION`. The recorded columns keep their own summaries.
Pinned by `test_a_colliding_derived_key_does_not_cost_the_run_its_record`.

**`UnitTable` column access misaligned ragged columns.** `__getattr__` dropped missing rows
independently per column, so two columns ragged in *different* rows came back mispaired — and
when their surviving counts happened to be equal, `pearsonr(units.pred, units.truth)` (the
document's own example) returned a correlation over pairs drawn from different units, with a
resampled interval around it and nothing wrong-looking anywhere. A column is now one entry per
row in row order, `None` where the unit recorded nothing, which is what `reference.md` § Templates
("the same shape whichever of the two supplied them") and § The per-unit tables ("a column absent
from a row reads as `None`") already specified. This reverses the "a ragged column omits the
missing unit" rule S4a task 3 was written to — right for a single-column mean, wrong for every
multi-column read; core's own column means read the collapsed table directly and are unaffected,
and a template summing a column holding a `None` now gets a loud `TypeError` contained as
`W-STATS-AGGREGATE-FAILED`. The unknown-column refusal is keyed on "this name appears in no row",
not on `columns` membership, so `units.unit` stays readable. Pinned by
`test_a_ragged_column_reads_none_in_row_order`, `test_two_differently_ragged_columns_stay_paired`,
`test_the_unit_column_is_still_readable_by_attribute`.

**`repeat_spread` described a different population than the interval beside it.** It read every
recorded row while `value` and `ci95` rest on `collapse_repeats`'s completed-unit intersection, so
one unit's ordinary attrition reported `std: 24.75` for a pipeline that had not moved — under
`batch` repeats, readable as apparatus drift. `repeat_spread` now takes a required `keys`
argument, the collapsed table's units. Pinned by
`test_dispersion_reads_only_the_units_the_metric_rests_on`, which asserts both the corrected `0.0`
and the `24.75` the unfiltered read produced.

**A percentile interval below 80 surviving draws.** At 2 survivors the two ranks coincided and
`run.yaml` carried a zero-width 95 % interval labelled `percentile_over_units`; below 80 the lower
rank is pinned to the sample minimum by `_percentile_ranks`'s `max(0, …)` floor while the upper
keeps shrinking, so the interval was low-biased and too narrow across that whole range. The ranks
themselves are unchanged and now pinned at 1, 2, 79 and 80 — they are shared with
`percentile_over_units`, and the honest place for the refusal is the construction, not the
arithmetic. `min_honest_draws(confidence)` is the floor: the smallest n with `int(tail · n) >= 2`,
so both ranks are interior — 80 at 95 %, 400 at 99 % — and below it `percentile_of_derived`
returns no interval while still reporting the surviving count. This also absorbs the deferred
`_percentile_ranks(1, ·) == (0, 0)` item.

**New warning identifier: `W-STATS-RESAMPLE-THIN`.** `cli.py` warned only at
`resample_draws == 0`; between 1 and `draws` there was no signal at all except a field
`reference.md` did not document. It now warns on any shortfall, naming both counts and saying when
the shortfall put the count below the floor. A separate identifier rather than a third event under
`W-STATS-AGGREGATE-FAILED`: `aggregate` did not fail — it produced numbers, on fewer draws than
were requested — and one `reference.md` sentence cannot honestly describe both.

**`reference.md` now documents `resample_draws`, `W-STATS-AGGREGATE-FAILED`,
`W-STATS-RESAMPLE-THIN`, and `E-STEP-COLUMN-UNKNOWN`**, closing the "add … once that section is
next touched" deferrals recorded above. The five `-UNSUPPORTED` codes stay undocumented, following
the established pattern: they retire with their slice. The worked example is untouched — the field
was added to § The per-unit tables' fullest metric block, whose numbers are unchanged.

## Carried out of the S4a whole-branch review

Recorded rather than fixed, each with the reason and where it lands.

| Carried | Why, and where it goes |
|---|---|
| The table `aggregate` receives omits declared unit attributes and every non-numeric column, against `reference.md` § Templates' "plus every declared unit attribute" | **S4c.** Both halves need work that does not exist yet: a string or bool column surviving `collapse_repeats` needs a collapse rule across repeats (`data.units.measurements`, refused since S2), and attributes appear in no recorded row, so carrying them means threading the resolved roster into `cli.py`'s `UnitTable` construction. Narrowing the document is not the cheap alternative — "plus every declared unit attribute" is a commitment to stratification inside `aggregate`, so removing it needs an argument against `design-principles.md`. S4c is where `report_by` and strata land, which is the work that wants string columns anyway. Both `aggregate` examples in § Templates fail on this build for this reason, loudly, as `W-STATS-AGGREGATE-FAILED` |
| `limits.max_ineligible_fraction` validates clean and is read by nothing | Documented at § The one config file and § Validation as a warning `run` emits; `runner.attrition` already computes `ineligible`. Pre-existing, not introduced by S4a, and the last live instance of the silent-no-op class this slice's refusals close — `min_clusters`, `min_units_per_cell` and `min_reported_n` are unread too but unreachable, since `cluster_by`, `allocation: between` and `report_by`/`within` are each already refused. Assigned to **S4c** — see § `limits.max_ineligible_fraction` moves from S4b to S4c below, which records why S4b closed only `min_reported_n` |
| `np.str_` / `np.bytes_` are refused by `coerce_scalars`'s `__len__` guard | Literally correct under `reference.md` § Steps and artifacts' protocol wording — neither carries `__float__`, `__index__`, or `__bool__` — but "a NumPy scalar is a float that arrived through a library" reads as covering them, and a string column arriving from `pandas`/`pyarrow` will hit it. Revisit with the non-numeric column work above; the two share a slice |
| The bootstrap-vs-analytic convergence tolerance is 0.02 against a 200-seed worst case of 0.0198 | Deliberately not loosened: the margin is thin because the test is measuring something real. Carried as a comment the test still wants |
| `tests/test_cli.py` monkeypatches `STARTER_STEP` | Test ergonomics — the generator has no seam for "scaffold a project whose step records these columns", and inventing one for tests would be a production surface nothing else uses |
| `materialize.py` emits none of `statistics.contrasts`/`.resample`/`.null_test`/`.report_by`, and there is no end-to-end test of its real output | Absent and empty behave identically, and both were verified non-refusing against a fresh scaffold. The missing regression test is pre-existing and shared with the `data.units` refusals. The `validate.py` comment that claimed all five keys were written has been corrected |
| A `summary` step returning an `Estimate` will need an exemption at `runner.py`'s coercion call | **RESOLVED by S5a.** The exemption landed in `coercion.py`, not at the call site this line predicted: `CLAUDE.md`'s invariant states the rule as a property of what a step's return may contain, so `coerce_scalars` gained a `scope` keyword and `runner.py` passes the scope it already had. Two corrections to this line's own reasoning, both found in implementation. The exemption also had to **coerce the `Estimate`'s own fields** — a mixed model hands back `numpy.float64` more often than a derived metric does, and passing the object through untouched would have reintroduced the `RepresenterError` traceback S4a removed at the top level. And `reference.md` § Errors core raises already names `E-STEP-ESTIMATE-SCOPE` and `E-STEP-ESTIMATE-METHOD`, so only `W-STEP-ESTIMATE-N` was genuinely unnamed |
| `W-STATS-AGGREGATE-FAILED` covers two events (the single call failed; every resample draw failed) | Verified mutually exclusive per metric — a failure in the single call removes the key from `derived` and hence from `step_summary`, so the draw sweep can never see it — and disambiguated by message. `W-STATS-RESAMPLE-THIN` deliberately did *not* become its third event. Revisit only if `reference.md`'s description can no longer cover both |

**AMENDED 2026-08-11 (S5 checkpoint, task 16): swept row by row; two remain open, both owned.**

| Carried | Status |
|---|---|
| The `aggregate` table omits declared unit attributes and non-numeric columns | **Half closed, half open.** Task 13 landed the attributes half — `cli.py` now carries declared unit attributes into the table, with the collapse rule and the namespace fact stated in `reference.md` § Templates; that task's own reframing is worth keeping, since the document was already right and the code was wrong, so this was closing a divergence rather than adding a feature. **The non-numeric-column half is open: owner H5 Artifacts** |
| `limits.max_ineligible_fraction` read by nothing | **CLOSED.** Read by `cli.py`; `W-DATA-INELIGIBLE` exists and has a row in `reference.md` § Warnings core reports |
| `np.str_` / `np.bytes_` refused by `coerce_scalars`'s `__len__` guard | **OPEN. Owner H5 Artifacts**, which the row itself already pairs it with ("the two share a slice") — non-numeric columns are exactly what makes a string scalar arrive |
| Bootstrap-vs-analytic tolerance 0.02 against a 0.0198 worst case | **No slice; closed.** Deliberately not loosened; carried as a comment the test still wants |
| `tests/test_cli.py` monkeypatches `STARTER_STEP` | **No slice; closed.** Test ergonomics; inventing a production seam for it would be worse |
| `materialize.py` emits none of the four `statistics` sub-blocks, untested end to end | **Superseded.** Now tracked as a real gap on "The generated config calls itself 'the complete parameter set'" above, since two of the four are built features — **owner H4** |
| A `summary` step's `Estimate` needs a coercion exemption | **CLOSED by S5a**, as the row already records |
| `W-STATS-AGGREGATE-FAILED` covers two events | **No slice; closed.** Verified mutually exclusive per metric and disambiguated by message |

## New error identifier: `E-STATS-CONTRAST-WITHIN`

S4b task 6. `reference.md`:272 ("Contrast stratum is an attribute") states the rule —
`statistics.contrasts[i].within` names a unit attribute, and `data.units.attributes` is where
one is declared — but names no identifier for it, the same gap the S4a batch above closed for
five other blocks. Left unchecked, `within: {sexx: f}` (a typo of a declared `sex` attribute) is
indistinguishable downstream from a stratum that is genuinely empty: `contrasts.units_matching`
reads it with `attributes.get(name)`, which returns `None` either way. Task 2's review flagged
this as belonging in `validate`, analogous to the (also still unimplemented, since `report_by` is
refused wholesale until S4c) unknown-attribute rule `reference.md`:2124 describes for
`report_by`.

`_check_contrasts` (`validate.py`) now refuses a `within` key not present in the declared
`data.units.attributes` list as `E-STATS-CONTRAST-WITHIN`, alongside the two identifiers the S4b
plan already named for this task — `E-STATS-CONTRAST-UNKNOWN` for an unresolvable `of`/`against`
and `E-STATS-CONTRAST-NESTED` for one naming another entry's `id`. Only `-WITHIN` is new relative
to the plan; the other two were pre-specified. Pinned by
`test_a_contrast_naming_an_unknown_within_attribute_is_refused` and
`test_a_contrast_with_a_declared_within_attribute_validates_clean`, both in `tests/test_validate.py`,
both exercised through `validate_config`.

## `percentile_over_units` is unguarded and currently unreachable

**AMENDED 2026-08-11 (S5 checkpoint audit):** FALSE at HEAD. The floor landed; `stats.py`'s
`percentile_over_units` returns `None` below two values and below `min_honest_draws(confidence)`
draws. Closed by entry line 1779. The entry's *second* claim — "nothing in production calls it" —
is **still true**, because `statistics.resample` is refused by `E-STATS-RESAMPLE-UNSUPPORTED`.

S4a added a survivor floor (`min_honest_draws`) inside `percentile_of_derived`, but its sibling
`percentile_over_units` has no such guard and returns a zero-width interval at two draws. That
is harmless today because nothing in production calls it — column metrics use `t_over_units`,
and `statistics.resample` is refused — but S4b or S4c will wire it up when the declared
`resample` block lands, and would inherit the gap. Apply the same floor at that point, or make
the two share one entry point.

**AMENDED 2026-08-15 (spec-defects staleness audit at `5578988`): the 2026-08-11 amendment's
surviving half is FALSE too, and the entry is closed on both claims.** "Nothing in production calls
it" no longer holds: `E-STATS-RESAMPLE-UNSUPPORTED` retired with H4a, and `stats.summarize_step`'s
recorded-column branch calls `percentile_over_units` whenever a declared `statistics.resample` makes
`resample_columns` true. It arrives **guarded** — the survivor floor S4c task 9 added sits on the
path the production caller now takes, which is the sequencing that task hoped for when it landed the
floor ahead of a caller. The same correction governs "RESOLVED in S4c Task 9: `percentile_over_units`
now shares `percentile_of_derived`'s survivor floor" below, whose "still unreachable in production as
of this task" was true of that task and is not true at HEAD; it is recorded here so there is one copy
of the correction rather than three.

## New identifiers from the S4b whole-branch review: `E-STATS-CONTRAST-SAME-SIDES`, `E-STATS-CONTRAST-SHAPE`, `W-STATS-CONTRAST-THIN`

Three codes minted while closing the S4b whole-branch review, all in the same shape as
`E-STATS-CONTRAST-WITHIN` above: `reference.md` states the rule and names no identifier.

`E-STATS-CONTRAST-SAME-SIDES` implements `reference.md` § Validation's row "Contrast has two
distinct sides" (`statistics.contrasts[1]` sets `of` and `against` to the same condition). It was
simply not built: a self-comparison validated clean and published a perfect null — `delta: 0.0`
with a zero-width `ci95` over every unit — as a finding, which under S4c would additionally take
a slot in the correction family and tighten every other interval in the run. Checked only once
both sides resolve, so a typo stays the more specific `E-STATS-CONTRAST-UNKNOWN`.

`E-STATS-CONTRAST-SHAPE` covers three shape faults with no document sentence of their own,
reachable only because this slice retired `E-STATS-CONTRASTS-UNSUPPORTED`: a non-list
`statistics.contrasts`, an entry that is not a mapping (`contrasts: [method=spearman]`, a list of
condition labels, is the plausible slip), and a missing or non-string `id`. The first two reached
`run` as an `AttributeError` traceback out of `resolve_contrasts` — whose own comment says the
bare `KeyError` it permits is acceptable "only because validate refuses that at validate time",
a claim that was not true for these shapes. The third reached a published `run.yaml` as the
literal string `'None'`, where two such entries collide under one name; it was recorded as a
deferred Task 1 minor and is closed here rather than carried, since it corrupts an artifact.

`W-STATS-CONTRAST-THIN` implements `limits.min_reported_n` for contrasts, which `reference.md`
describes in three places (§ Contrasts' "applies to a `within` contrast's `n_paired`", the §
The one config file comment, and § Validation's "Contrast stratum is populated" row) without
naming a code. It is scoped to `within` contrasts, as all three passages have it: `min_reported_n:
10` is written into every generated config, so warning on every comparison would fire a
disclosure warning on any ordinary sub-ten-unit pilot for a comparison the document never scoped
it to.

## RESOLVED (S4c task 8): `confounded: true` is documented on a contrast entry and emitted by nothing

`reference.md` § Contrasts marks a contrast crossing two axes `confounded: true`, § Validation
carries it as a warning, and the § Sweeps entry shape shows the field. Multi-axis grids are
expressible today — `sweep.expand` takes the product over `grid.items()` — so a baseline fixing
two axes yields conditions differing from it on both, and S4b writes a `vs_baseline` entry for
each with no marker. **Assigned to S4c**, with the correction family: `confounded` is a property
of which axes two conditions differ on, the same derivation `paired` already needs, and both
belong beside the family arithmetic rather than split across two slices. Recorded here because
CLAUDE.md's "unimplemented must mean refused" makes silence the wrong outcome for it.

**Closed by S4c task 8.** A comparison whose two conditions differ on more than one axis now
records `confounded: true` and `differs_on: [<axis>, <axis>]` on the metric entry, both absent
rather than `false`/`[]` when one axis differs. Two corrections to the analysis above emerged in
implementation. First, the axis comparison has to be a **union** of both conditions' `values`
keys: `validate` enforces only that every grid axis appears in `sweep.baseline`, never the
reverse, so a baseline may fix an axis the grid never sweeps, and a one-directional comparison
silently misses it. Second, `paired` stays hard `true` — the `paired: false` and
`unpaired_percentile_over_units` shape `reference.md` § Allocation shows beside `confounded` is
for a crossed *group* axis, and group axes (`E-SWEEP-GROUPS-UNSUPPORTED`) and
`allocation: between` (`E-DATA-ALLOCATION-UNSUPPORTED`) are both still refused, so that shape is
unreachable in this build.

## `rank_family`'s tie-break is lexicographic where the document says declaration order

Found by the S4c task 4 review. `reference.md` § Statistical reporting says ties in the ranking
statistic "break by condition index, then by metric name in declaration order, so a rank is a
function of the record rather than of an iteration order." `correction.rank_family` sorts by
`(condition_index, metric)` — metric name lexicographically, because `Member` carries no
declaration order to sort by, and the module's docstring honestly drops the "declaration order"
claim rather than overclaiming it.

Reachable only when two members tie *exactly* on the point-estimate-over-half-width ratio and
share a condition index, so no run observed so far distinguishes the two orderings. The S4c task 7
review found a related gap: the tie-break omits `where` entirely, so two members of one comparison
can tie and fall through to build order — deterministic today, but by accident rather than by
construction. **Assigned to the slice that next touches `correction.py`.** [Task 16's note: this
phrasing is the audit's second exhibit — a description, satisfied repeatedly and honoured by none
of the slices that satisfied it. It stands here as filed; the amendment below is what closed it.]
Either thread a
declaration index onto `Member` and sort by it, or change the document to say lexicographic —
what cannot stand is the current state, where the document claims an ordering the code does not
implement.

**AMENDED 2026-08-11 (S5 checkpoint, task 10):** took the first branch. `Member` gained a
required `declaration_index: int`, assigned once — in `cli.py`'s `command_run`, over
`vs_baseline_members + contrast_members` concatenated in that order — so it is unique and
monotonic across the whole family rather than restarted per comparison. `rank_family`'s key
became `(-_evidence_ratio(m), m.declaration_index)`. `condition_index` was removed from `Member`
entirely rather than kept as a second tie-break key: a follow-up review found it had become
write-only (read nowhere outside its one construction site) the moment `declaration_index` took
over the tie-break, and an unread field on a frozen dataclass invites a future reader to assume
it is load-bearing when it is not. `reference.md` § Statistical reporting was corrected to say
ties break by declaration order rather than by condition index and metric name.

## `limits.max_ineligible_fraction` moves from S4b to S4c

**AMENDED 2026-08-11 (S5 checkpoint audit):** FALSE at HEAD. It is read: `cli.py` reads
`limits.max_ineligible_fraction` and warns `W-DATA-INELIGIBLE`. Closed by entry line 1752. The
entry's other two claims **survive**: `min_clusters` and `min_units_per_cell` appear nowhere in
`src/` and remain unread behind refused features.

The S4a carry table above assigned it to S4b "with the rest of the limits work". S4b closed
`min_reported_n`, which was the half made reachable by `within` becoming legal; the rest did not
move. `max_ineligible_fraction` is still written by `materialize.py` and read by nothing, and
`min_clusters` and `min_units_per_cell` stay unreachable behind `cluster_by` and
`allocation: between`. It needs `runner.attrition`'s `ineligible` count at the point the run
record is assembled, which is where S4c's reporting work already is.

**AMENDED 2026-08-15 (spec-defects staleness audit at `5578988`): one of the two surviving claims is
now false.** `limits.min_clusters` **is read** — `validate.py` names it at eleven sites and emits
`W-STATS-RESAMPLE-CLUSTERS` when a declared `data.units.cluster_by` would put a resample below it.
Two slices did that between them: H3b made `cluster_by` reachable, and H4a gave the limit the
declaration it is checked against. `limits.min_units_per_cell` is the only one of the three still
declared, typed, and read by nothing, and it has its own live entry below
("`limits.min_units_per_cell` is still declared, typed, and read by nothing, now that
`allocation: between` is reachable for real"), which is where that half is tracked. The carry table
in "Carried out of the S4a whole-branch review" states the same "unread … but unreachable" fact in
one of its historical cells and is deliberately
left as filed — this is the single correction, so the count of copies does not drift.

## `W-STATS-FAMILY` counts a baseline comparison per condition even with no baseline

**AMENDED 2026-08-11 (S5 checkpoint audit):** FALSE at HEAD. `validate.py`'s `_check_statistics`
computes the family as `len(resolve_contrasts(doc, conditions))`, not `len(conditions) - 1`, and
fires only for `correction: none` over a non-empty family. Closed by entry line 1678.

Found by the S4b whole-branch re-review, alongside the declared-contrast undercount fixed with
it. The warning reports `len(conditions) - 1` baseline comparisons, but `sweep.expand` marks a
condition `is_baseline` only when `sweep.baseline` is declared, and `resolve_contrasts` yields
baseline comparisons only when one exists — so a grid-only sweep over three conditions is told it
forms a family of two comparisons while the run publishes none. Pre-existing, and left alone in
S4b only because the fix belongs with the arithmetic that consumes it rather than with a count
only a warning reads.

**It is a false positive, not a backstop** — the re-review's correction to an earlier version of
this entry, which claimed the warning was still owed as a "correction is not implemented"
disclosure. It is not: that shape publishes no comparison at all (`resolve_contrasts` returns
`[]`, and `test_a_run_with_no_baseline_has_no_vs_baseline_block` asserts the record carries no
comparison block), so there is no uncorrected interval to disclose. **Assigned to S4c**, which
should derive the count from `resolve_contrasts` rather than from `len(conditions)` and let the
warning disappear for that shape rather than preserving it.

## `statistics.contrasts` is absent from `_check_shape`'s nested-shape pass

**AMENDED 2026-08-11 (S5 checkpoint audit):** FALSE at HEAD. `validate.py`'s `_check_shape` now
carries a `statistics` branch refusing a non-list `contrasts` **and** a non-list `report_by` as
`E-CONFIG-SHAPE`. Closed by entry line 1794. **The residue moves to entry 1794**, which is headed
`RESOLVED` and is therefore invisible to a reader scanning headings: `contrasts.resolve_contrasts`
itself is still unguarded against an unhashable side.

Recorded from the S4b whole-branch re-review, as the general form of the R11 regression rather
than as another instance of it. `_check_shape` runs first and `validate_config` early-returns on
its failure, so a scalar `sweep` or `statistics` never reaches a `_check_*` reader at all — but
the nested key `statistics.contrasts` is not in that pass, so a scalar there reaches every reader
individually. `validate.py`'s own comment on the pass says an unguarded container means "the crash
just moves one level down, into whichever `_check_*` reads it next", which is exactly what
happened: `_check_sweep`'s family count read the block ahead of `_check_contrasts`'s shape
refusal and raised a `TypeError` out of `validate`. Both readers are guarded now, and that is
sufficient for this build. **S4c** should add the key to the nested pass, so its own new readers
of the block — the correction family is one — inherit a single `E-CONFIG-SHAPE` refusal and the
early exit instead of each needing its own guard.

## `W-STATS-FAMILY` changed condition without changing identifier; two new identifiers, `E-STATS-CORRECTION-UNKNOWN` and `W-STATS-CORRECTION-INAPPLICABLE`

S4c Task 6. The entry above ("`W-STATS-FAMILY` counts a baseline comparison per condition even
with no baseline") is resolved by this change, not superseded by it: the count now comes from
`resolve_contrasts(doc, conditions)` — every baseline comparison plus every declared
`statistics.contrasts` entry, the same list `cli.py`'s correction pass will consume — rather than
from `len(conditions) - 1`. The identifier is unchanged because the fact it discloses is the same
fact, better counted. What did change is the *condition* it fires under: it used to warn whenever
the family was non-empty, with a message saying multiplicity correction "is not implemented in
this build". That was true until this slice and is false now, so the warning now fires only for
`statistics.correction: none` over a non-empty family — exactly `reference.md` § Validation's row
"Correction declared for a family". `materialize.py` writes `correction: holm` into every
generated config, so the old condition warned on nearly every multi-condition run; the new one
warns only on a config that opted out of the correction the generated default supplies.

**`W-STATS-CORRECTION-INAPPLICABLE` implements `reference.md` § Validation's row "Correction can
be applied"** (`statistics.correction: fdr_bh`, but no comparison in the family will carry a
p-value). The document states the rule and names no identifier for it, the same shape as
`E-STATS-CONTRAST-SAME-SIDES` above. It was reachable only once `statistics.contrasts` stopped
being refused wholesale and `resolve_contrasts` became the family's source of truth — before that,
nothing checked `fdr_bh`'s applicability at all, and a run with it declared would validate clean,
execute, and publish every comparison with a `null ci95_corrected` and no `p_value_corrected`,
the exact silent-correction-not-applied state `reference.md` § "Corrected fields" says this
section exists to prevent. `statistics.null_test` is refused in this build
(`E-STATS-NULLTEST-UNSUPPORTED`), so no comparison can ever carry a p-value yet — the warning is
therefore unconditional on `fdr_bh` for now rather than conditional on `null_test`'s `shuffle`
reaching the family, which is the refinement a later slice that implements `null_test` owes it.
**AMENDED 2026-08-11 (S5 checkpoint, task 16): that refinement is OPEN and its owner is H4
Statistics** (spine § The hardening slices), the slice that implements `statistics.null_test`.
Until it lands, `W-STATS-CORRECTION-INAPPLICABLE` being unconditional on `fdr_bh` is correct
rather than approximate — no comparison can carry a p-value at all — so H4 must make the warning
conditional in the same change that makes p-values reachable, or the warning becomes false the
moment `null_test` works.

**`E-STATS-CORRECTION-UNKNOWN` has no document sentence at all.** `reference.md` § "The one config
file" enumerates `statistics.correction` as `none | bonferroni | holm | fdr_bh` and says nothing
about a value outside that set — the schema names the enum but the document never states what
happens to a fifth value, string or otherwise. Before this slice nothing read `correction` in
`validate` at all, so an out-of-enum value validated clean and reached `cli.py`'s correction pass
undiagnosed.

The code covers both faults reachable from `_check_sweep`'s guard, widened from the initial cut
after review: a non-string `correction` (`5`, `True`, a list, a mapping) — for the same reason
`E-STATS-CONTRAST-SHAPE`'s `isinstance` guards exist, this module collects findings and never
raises, and the R11 regression was exactly a `len()` call on an unguarded config value ahead of
its shape check — **and a string outside the enum** (`correction: "bonferonni"`, a plausible typo
of `bonferroni`). The second half was the load-bearing gap: left unchecked, `cli.py`'s
`corrected_for` returns `ci95_corrected: null`, `correction: "bonferonni"`, `correction_level:
null`, `thin: false` for every member of the family — the record names a correction as applied
while applying none, with `thin: false` suppressing the one signal that would flag it, which is
verbatim the state `reference.md` § "Statistical reporting" says the correction machinery exists
to prevent, and is the same record shape an undiagnosed `fdr_bh` would have produced before
`W-STATS-CORRECTION-INAPPLICABLE` above. The check is `isinstance(correction, str) and correction
in known_corrections` rather than a plain `not in`, deliberately in that order: `in` on a `set`
raises `TypeError` for an unhashable value (a `list` or a `dict`), and `and` short-circuits before
that ever runs, so the non-string branch still cannot raise. Closed by this widening — no
remaining gap in `statistics.correction`'s value space is undiagnosed.

## New warning identifier: `W-STATS-CORRECTED-THIN`

S4c Task 7, where the correction pass first reaches a record. `reference.md` § Statistical
reporting states what a correction is and when `ci95_corrected` is `null` — under `fdr_bh`, whose
corrections are not interval-shaped — but says nothing about the other route to a null: a
percentile interval whose stored draw pool cannot support the corrected level. Holm hands rank 1
of a family of *m* the level α/*m*, and `interval_at` refuses any level whose honest-draw floor
(`min_honest_draws`) exceeds the pool it was given, for the reason `reference.md` gives at
"Below 80 surviving draws core reports no interval" — the ranks stop being interior and the
"interval" contains the sample minimum by construction. So a large family over a small
`resample_draws` yields `ci95_corrected: null` beside
a `correction` and a `correction_level` that both name what was asked for. Silent, that reads as
`fdr_bh`'s deliberate null; the warning says which of the two it is, and that the null is a
refusal rather than a too-narrow number. The document names no identifier for it, the same shape
as `E-STATS-CONTRAST-SAME-SIDES` and `E-STATS-CORRECTION-UNKNOWN` above.

Emitted by `cli.py` from the `thin` flag `corrected_fields` returns and the caller pops — `thin`
is deliberately not a record field, since the warning is the disclosure and a fifth boolean per
metric entry is not. The branch is unexercised end to end as of Task 7: no fixture in
`tests/test_cli.py` yet builds a family large enough, over a pool small enough, to fire it. The
slice plan gives that test to Task 10.

## RESOLVED in S4c Task 9: `limits.max_ineligible_fraction` read; new warning identifier `W-DATA-INELIGIBLE`

Closes the entry above ("`limits.max_ineligible_fraction` moves from S4b to S4c"). `command_run`'s
per-condition, per-step aggregate loop already computes `counts = attrition(...)`; immediately
after that call it now compares `counts["ineligible"] / counts["resolved"]` against
`limits.max_ineligible_fraction` and warns `W-DATA-INELIGIBLE` when the ratio exceeds it. The
denominator is `resolved` (not the full roster), matching `reference.md`'s own framing of the rule
at § "The one config file" ("buildable for fewer units") and its worked instance at § Validation
("buildable for 96 of 330 units") — both state the fraction over what the condition could resolve
to, not over the roster before any step ran. Guarded the same way `W-STATS-CORRECTION-INAPPLICABLE`
above discovered `statistics.correction` must be: `isinstance(max_ineligible, (int, float)) and
not isinstance(max_ineligible, bool)`, since `limits` is user-written YAML and a string or
mis-typed threshold must not raise out of `run`. `bool` is excluded because `True` compares equal
to `1` and would silently never fire (every fraction is `<= 1`).

`grep -rn "max_ineligible_fraction|W-DATA-INELIGIBLE" src/ docs/reference.md` before this change
found `max_ineligible_fraction` in `materialize.py` (written into every generated config) and in
`reference.md` three times (§ The one config file, § Validation, § Contrasts), all saying `run`
"warns" without naming a code — the same shape as `E-STATS-CONTRAST-SAME-SIDES` and
`W-STATS-CORRECTION-INAPPLICABLE` before their entries above, so `W-DATA-INELIGIBLE` is minted
here rather than found. Per condition and per step, not run-level like `max_failed_fraction`,
because `reference.md` § The one config file is explicit that ineligibility is a design property
of one condition's own eligibility window, not an execution failure the whole run should be
judged by. Pinned by `test_a_condition_skipping_too_many_units_warns` in `tests/test_cli.py`,
through `main(["run", ...])` end to end, with a fixture step that declares 8 of 10 units
ineligible via `io.skip`.

## RESOLVED in S4c Task 9: `percentile_over_units` now shares `percentile_of_derived`'s survivor floor

Closes the entry above ("`percentile_over_units` is unguarded and currently unreachable"). Added
`if draws < min_honest_draws(confidence): return None` immediately after the existing `len(values)
< 2` guard — the same floor `percentile_of_derived` already enforces on its *surviving* draw
count, applied here to the *requested* draw count before any resampling runs, since
`percentile_over_units` has no notion of a degenerate draw to drop (unlike its derived-metric
sibling, every draw here is a plain mean over the fixed pool and cannot fail). Still unreachable
in production as of this task — `statistics.resample` remains refused
(`E-STATS-RESAMPLE-UNSUPPORTED`) — which is exactly why the fix landed now rather than being
carried again into the slice that wires `resample` up. Pinned by
`test_percentile_over_units_refuses_a_pool_below_the_honest_floor` in `tests/test_stats.py`: a
60-value pool returns `None` at 10 draws (below the 80-draw floor at the default 95% confidence)
and a real interval at 2000.

## RESOLVED in S4c Task 9: `statistics.contrasts` added to `_check_shape`'s nested pass — and a second, narrower crash the fix does not close

Closes the entry above ("`statistics.contrasts` is absent from `_check_shape`'s nested-shape
pass") for the shape that entry described: a scalar or otherwise non-list `statistics.contrasts`
(`5`, `True`, a mapping, a string) now produces `E-CONFIG-SHAPE` and validate_config early-returns,
the same treatment `sweep.grid` and `sweep.baseline` already get. This changes which identifier
two pre-existing tests see for a non-list block —
`test_a_non_list_contrasts_block_is_refused` and
`test_a_scalar_contrasts_block_is_refused_without_raising` in `tests/test_validate.py` now assert
`E-CONFIG-SHAPE` rather than `E-STATS-CONTRAST-SHAPE`, since `_check_contrasts` never runs for
those inputs any more. `_check_contrasts`'s own `isinstance(entries, list)` guard is kept
regardless (per this task's brief: `_check_contrasts` is reachable directly from tests, and
removing a guard because another now exists upstream is how the R11 regression happened), and is
now exercised directly by `test_check_contrasts_still_refuses_a_non_list_when_called_directly` so
it is not dead code between reviews.

**A second, narrower crash was found and closed in the same task, on review.** The
`_check_shape` addition above does not by itself close every crash the original entry's language
suggested — the "family count in `_check_sweep` reached it before `_check_contrasts` refused its
shape" scenario the brief described for a bare *scalar* `statistics.contrasts` turned out, on
verification against the actual base commit, not to be a live crash at all: `_check_sweep`
already wraps its `resolve_contrasts` call in `try/except (TypeError, KeyError, AttributeError,
ValueError)`, and `_check_contrasts` already carries its own `isinstance(entries, list)` guard, so
a scalar there already produced a clean `E-STATS-CONTRAST-SHAPE` finding before this task, with no
`TypeError` reaching `validate`. (The two guards' comments elsewhere in this file still say why
each is load-bearing on its own terms — see below.)

What *did* crash, uncaught, through the full `validate_config` pipeline, verified with a direct
repro (`statistics.contrasts: [{id: x, of: [a, b], against: baseline}]` — list shape fine, entry a
mapping, `of` a list) was a case neither existing guard covers: `resolve_contrasts` raises
`TypeError` on `by_label[["a", "b"]]` inside `_check_sweep`'s try/except, which swallows it there,
but `_check_contrasts` (running after `_check_sweep`, unguarded at this line) then evaluated
`value in ids` — `ids` a `set` — on that same unhashable `of` at its per-entry field loop, and
raised `TypeError` a second time, this time uncaught. Closed in the same task: `_check_contrasts`'s
field loop and its same-sides check now test `isinstance(value, str)` before every set-membership
test on `of`/`against`, mirroring the guard `E-STATS-CORRECTION-UNKNOWN`'s fix uses for
`statistics.correction`. No new identifier: a non-string `of`/`against` now falls into the
existing `E-STATS-CONTRAST-UNKNOWN` branch ("names `...`, which no condition's label matches"),
since a list or a mapping is exactly as much "not a condition's label" as an unresolvable string
is. Pinned by
`test_an_unhashable_side_inside_a_well_shaped_contrast_is_refused_not_a_crash` in
`tests/test_validate.py`, through `validate_config` end to end.

**Correction, S4c whole-branch review: that fix was scoped to `of`/`against` and the class was
not closed.** The paragraph above is accurate as written but its framing overstated — two further
sites in the same function hash an entry's **`id`**, and both still raised. The whole-branch
reviewer found them by fuzzing 784 malformed `statistics.contrasts` configs through
`validate_config`; 56 crashed, all on this one fault, and it reproduces at the pre-slice base
commit `e8cd629`, so it is pre-existing rather than introduced by S4c. The two sites are (1) the
`ids` **set construction** three lines *above* the patched field loop, which hashes every entry's
`id` before the loop begins — so `id: {name: sensitivity}` (one bad indent) or `id: [sensitivity]`
raised `TypeError: unhashable type` before a single finding was collected — and (2) the
`entry.get("id") in seen_ids` repeat check inside the loop, which hashes the same value against a
`set[str]` and would have raised identically once the first site was guarded. Both now test
`isinstance(..., str)` first, via a hoisted `raw_id`/`is_named` pair, and a non-string `id` falls
through to the missing-or-not-a-string `E-STATS-CONTRAST-SHAPE` branch the function already had —
again no new identifier, and the same routing chosen for a non-string `of`/`against`. Pinned by
`test_an_unhashable_contrast_id_is_refused_not_a_crash` in `tests/test_validate.py`, parametrized
over a mapping and a list `id`, through `validate_config` end to end. `entry["id"]` is read
nowhere else in `_check_contrasts`, so the three sites (`of`/`against`, `ids`, `seen_ids`) are the
whole set — "validate collects findings and never raises" now holds for every shape of
`statistics.contrasts` the fuzz reached.

The `_check_sweep` try/except remains load-bearing, kept, and correctly attributed to a fault it
actually guards: an unresolvable label (a typo in `of`/`against`) raises `KeyError` from
`by_label[entry["of"]]` inside `resolve_contrasts`, caught there, with `_check_contrasts` going on
to report the friendlier `E-STATS-CONTRAST-UNKNOWN` afterward — that dependency is real and this
task did not change it.

**Known boundary, not fixed here:** `contrasts.resolve_contrasts` itself — the function
`_check_sweep`'s try/except calls, and the one `cli.py` calls at run time to build the actual
comparison list — is still unguarded against the same unhashable-side input. `validate.py`'s copy
of the check (in `_check_contrasts`, fixed above) is the only place this class of malformed value
is now refused. That is fine as long as every path to `resolve_contrasts` is preceded by
`validate_config` — `run` always validates before it runs, and `validate_config`'s `_check_shape`
plus the `_check_contrasts` fix above now refuse this input before `resolve_contrasts` is ever
called for real. A later slice that calls `resolve_contrasts` from anywhere that does not go
through `validate` first (a standalone `dry-run`-style dump of the family, say) would need its own
guard, or would need to reuse `validate_config`'s.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): OPEN, OWNER NAMED — H9 Reproduction and the other
modes** (spine § The hardening slices), which owns `dry-run` along with `reproduce`, `draft`,
`resume`, `demo` and `docs` — every command that is a second entry into `run`'s own sequence, and
therefore the only place a caller can appear that reaches `resolve_contrasts` without
`validate_config` in front of it. H9 must either run `validate_config` first (the cheaper answer,
and the one `reference.md` already implies by making `dry-run` an honest prefix of `run`'s phases)
or add `contrasts.resolve_contrasts`'s own guard. This is a **precondition on H9, not a bug at
HEAD**: `run` always validates, so no live path reaches the unguarded function today.

**AMENDED 2026-08-11 (task 14 of the S5 checkpoint plan):** A fourth unguarded `expand(doc)` call
in this same function, found and closed in the same task. `_check_contrasts` calls `expand(doc)`
directly to resolve `of`/`against` against condition labels, and a `sweep.grid` axis value of
`null` — past `_check_shape`'s per-axis `list` guard, which only refuses a *present, non-list*
value, not an absent-looking `None` — makes `itertools.product` raise `TypeError` inside `expand`.
Guarded the way `_condition_labels` already guards its own `expand(doc)` call, one function above:
`conditions = []` on any exception rather than a bare `return`, so the shape and `id`-collision
checks that don't depend on a resolved sweep still run, and every `of`/`against` correctly reports
`E-STATS-CONTRAST-UNKNOWN` against an empty `labels` rather than the rest of the block going
silently unchecked. No new identifier. Pinned by
`test_check_contrasts_guards_expand_when_called_directly` in `tests/test_validate.py`, called
directly rather than through `validate_config`.

**Review round: the first draft of this fix stopped at `_check_contrasts` and left the pipeline
crash live.** `_check_sweep` calls the same pure `expand(doc)` on the same doc one statement
earlier than `_check_contrasts`, so any sweep malformed enough to make `expand` raise already
crashed *there* first — with no `statistics.contrasts` needed at all — meaning guarding
`_check_contrasts` alone did not make `validate_config` itself stop raising for the exact input
Debt B named. Closed in the same task, on review: `_check_sweep`'s own `expand(doc)` call is now
guarded identically (`conditions = []` on any exception), with `E-SWEEP-EXPANDS-EMPTY` deliberately
*skipped* rather than fired on the caught exception — "could not expand at all" and "expanded to
zero conditions" are different claims, and firing the empty-grid error on a crash would misreport
one as the other. `validate_config` now returns findings (typically the earlier, more specific
`E-SWEEP-AXIS-EMPTY` a `null` axis value also triggers) rather than a traceback, for a malformed
sweep whether or not any contrast is declared. Pinned end to end by
`test_a_malformed_sweep_with_contrasts_is_a_diagnostic_not_a_crash` and
`test_a_malformed_sweep_alone_with_no_contrasts_is_also_a_diagnostic`, both in
`tests/test_validate.py` through `validate_config`, plus the corresponding correction to the
`E-HYPOTHESIS-*` entry's own paragraph naming this same gap (§ "New error identifiers:
`E-HYPOTHESIS-KIND`, `E-HYPOTHESIS-THRESHOLD`, `E-HYPOTHESIS-CONDITION`," below).

The second hole in the same task's brief — `compare: {condition: X}` with no `to` and no
`sweep.baseline` fires neither the baseline check nor the contrast check — stands by decision
rather than by fix: a `compare` naming a condition with no `to` and no `sweep.baseline` is a form
no documented rule covers, and inventing a refusal here would be core deciding a question
`reference.md` § Pre-registration has not asked. Routed to the hardening slice that specifies
`compare`'s full grammar. **AMENDED 2026-08-11 (S5 checkpoint, task 16): OWNER NAMED — H1
Validation** (spine § The hardening slices). "The hardening slice that specifies `compare`'s full
grammar" was a description of work no slice had claimed. H1 owns the full check engine, and this
is a check that does not exist rather than one that is wrong; the `reference.md` § Pre-registration
sentence it needs is H1's to write first, per `CLAUDE.md`'s document-leads rule.

## Residue carried out of the S4c whole-branch review

Triaged as "may ship" by the whole-branch review at `804950f`, recorded here because the SDD
workspace that held the ledger is deleted once a slice merges. Each is real; none blocks.

| Carried | Why it is safe today, and what would change that |
|---|---|
| `correction.corrected_fields` dedupes duplicate `(where, step, metric)` keys, and no test pins it | Unreachable while `validate` refuses both a repeated and a non-string contrast `id`, and `vs_baseline` is keyed by condition index. A slice that builds `Member` lists from anywhere other than `cli._comparison_step_blocks` makes it reachable and should pin it first |
| `_evidence_ratio`'s `assert member.ci95 is not None` is stripped under `python -O` | Third instance of the pattern in this codebase. The next line would raise `TypeError` rather than misbehave silently, so the failure stays loud. Worth a convention decision rather than a one-off fix |
| `W-STATS-CORRECTED-THIN`'s message leads with the machine key `cond:1` where `W-STATS-CONTRAST-THIN` says `condition 1 ('method=spearman') vs baseline` | `reference.md` § Exit codes and diagnostics makes the identifier the contract and the wording explicitly not. Harmonise opportunistically |
| Nothing asserts `paired_percentile_of_derived` returns a **sorted** pool, which `interval_at` depends on | Both return paths sort, and `interval_at`'s docstring states the precondition, so an unsorted pool is unconstructible from inside the package. A new percentile construction returning an unsorted pool would break it silently |
| `PairedResample.pool` is a `list`, so the frozen dataclass is unhashable | Nothing keys on it; making it a tuple would copy on every resample for no reader |
| `Member.__post_init__` exempts `ci95 is None`, so a member with no interval and both `pool` and `diffs` set passes | Deliberate and documented: `family_members` drops such a member before either field is read, and nothing constructs one |

**AMENDED 2026-08-11 (S5 checkpoint, task 16): routed row by row.** Every row above is a
"safe today, and here is what changes that" note rather than a defect owing a fix, so none of them
blocks; what each was missing is a named owner for the day its precondition breaks.

| Carried | Owner |
|---|---|
| `correction.corrected_fields` dedupe unpinned | **H4 Statistics** — it is the slice that would build `Member` lists from somewhere other than `cli._comparison_step_blocks`, which is the condition the row names |
| `_evidence_ratio`'s `assert` stripped under `python -O` | **No slice; closed as a convention question.** Third instance of the pattern, and the row itself says the next line raises loudly. A repo-wide convention on `assert` is not a slice's work and should not sit in a defect ledger pretending to be one |
| `W-STATS-CORRECTED-THIN`'s message leads with `cond:1` | **No slice; closed.** `reference.md` § Exit codes and diagnostics makes the identifier the contract and the wording explicitly not, so this is a cosmetic harmonisation any slice may do opportunistically and none owes |
| ~~`paired_percentile_of_derived`'s sorted-pool precondition unasserted~~ | **CLOSED 2026-08-18 (H4c, task 20).** `stats.interval_at` now asserts `list(pool) == sorted(pool)` before reading ranks off it, placed before the `min_honest_draws` floor so a too-short unsorted pool is still caught first. Pinned by `test_interval_at_refuses_an_unsorted_pool_rather_than_reading_two_positions` (`tests/test_stats.py`), mutated and confirmed to fail with the assertion removed against the full suite. Scoped to a normal interpreter: `python -O` strips `assert`, the same standing every other `assert` in this codebase has |
| `PairedResample.pool` is a `list`, so the dataclass is unhashable | **No slice; closed.** Nothing keys on it and a tuple would copy per resample. Recorded so it is not re-litigated |
| `Member.__post_init__` exempts `ci95 is None` | **No slice; closed.** Deliberate, documented, and pinned by `family_members` dropping such a member first |

**AMENDED 2026-08-18 (H4b-2, task 16), two rows.**

**The sorted-pool row.** Checked again at `82310b9`: both of `paired_percentile_of_derived`'s return
paths sort the pool (`pool=sorted(values)` and `values.sort()` before `pool=values`), so a reading
that treated the `strata` parameter's per-stratum key pools as "a second route to an unsorted-pool
input" was wrong — those are a different object from `PairedResample.pool`, sorted independently and
never returned as the interval's own pool. The row above restores the original condition rather than
that reasoning. **H4b-2 task 7 was checked against it**: the clustered draw it added returns through
the same two sorted paths, so it created no new unsorted-pool route either. The row stays open,
owned by H4b-2 still, for the same reason it always was — a *future* percentile construction is what
would break the precondition, and none has been added that does.

**The `correction.corrected_fields` dedupe row.** Recorded as **not H4b-2's**, rather than moved:
the row's condition is "the slice that would build `Member` lists from somewhere other than
`cli._comparison_step_blocks`." H4b-2 widens `Member` with a `clusters` field (task 12) and builds no
`Member` list anywhere but that one function — the condition is unmet, not satisfied narrowly. Owner
stays **H4 Statistics** at large; recording this here is what stops the next scoping re-deriving the
question of whether H4b-2 met it.

## New error identifier: `E-STATS-REPORTBY-UNKNOWN`

S4d task 3. `reference.md`:2127 ("`validate` rejects a `report_by` attribute that isn't
declared in `data.units.attributes`") states the rule but names no identifier for it — the
same gap `E-STATS-CONTRAST-WITHIN` closed for a contrast's `within`, and for the same reason:
`statistics.report_by` used to be refused wholesale (`E-STATS-REPORTBY-UNSUPPORTED`, retired by
this task), so nothing could reach the attribute check until the block was implemented for real.

Left unchecked, `report_by: [sexx]` (a typo of a declared `sex` attribute) is indistinguishable
downstream from an attribute that genuinely holds no unit: `strata.levels_for` reads it with
`.get`, which returns `{}` either way — the record would simply carry no `by` block for it and
never say whether that is because nothing matched or because nothing was declared.

`_check_report_by` (`validate.py`) now refuses a `report_by` entry not present in the declared
`data.units.attributes` list, or not a string at all (an unhashable entry — a list or a mapping —
would otherwise reach a set membership test and raise out of a module whose contract is that it
collects findings rather than raising), as `E-STATS-REPORTBY-UNKNOWN`. Pinned by
`test_a_report_by_attribute_must_be_declared` and `test_a_non_string_report_by_entry_is_refused`,
both in `tests/test_validate.py`, both exercised through `validate_config`.

## Amendment: an empty reporting stratum gets no block

S4d task 5, ruled by the slice owner during fix round 1. The slice plan said "an empty or
thin level still gets a block"; the implementation attaches one only when the level's own
table produced at least one metric entry, and this is the amendment rather than a
divergence.

A level that completed nothing has no rows to summarize, so its block would hold either
nothing at all or — once a template's `aggregate` is in play — derived metrics computed
over an empty table. Neither says anything `W-STATS-STRATUM-THIN` does not already say
before the run, and the second is worse than silence: a number with no observations
behind it. The behaviour before the amendment was also incoherent, since such a level
appeared iff a derived metric happened to keep the block non-empty. A *thin* level — some
units completed — still gets its block, which is the case the threshold warning is for.

`reference.md` § Reporting strata does not state either rule, so no document changes; what
it does say is that levels' counts need not sum to the condition's, which an absent empty
level is consistent with. Pinned by `test_a_level_that_completed_nothing_gets_no_block`
(`tests/test_cli.py`).

## New reserved metric name: `by`

S4d task 5. Attaching the reporting strata at `aggregated[condition][step]["by"]` — the
shape `reference.md` § Reporting strata shows — puts a non-metric key beside the metric
names in one mapping, and every consumer of a step block reads its keys as metric names.
The first consumer proved it: `cli._compute_one_contrast` differenced `by` as though it
were a metric and, sorting before every real name, made it the head of every `vs_baseline`
block. That is fixed at the choke point (`by` is excluded there), but the name itself is
now spent, and nothing had reserved it.

The refusal is split, because the two halves cannot be refused in the same place:

- A **derived** key named `by` — a template's `aggregate` returning one — raises
  `E-STEP-KEY-COLLISION` from `stats.summarize_step`, beside the existing recorded-column
  collision and with the same identifier, for the same reason: one name cannot hold both a
  metric and the block's strata. `cli.py`'s existing retry contains it, dropping the whole
  `derived` mapping exactly as the sibling case does, and the run survives.
- A **recorded column** named `by` must NOT raise there. That retry passes the same
  `collapsed` table, so a refusal keyed off a column would re-raise on the retry, and the
  run would die after spending every one of its executions — the most expensive place in
  the program to fail. `cli.py` warns instead (`W-STATS-STRATUM-SHADOWED`) and attaches no
  strata for that step. The column wins: it is a real measurement over the units, while
  the strata re-present numbers already in the record.

`stats.RESERVED_METRIC_NAMES` is the list, currently `{"by"}`. The second consequence of
spending the name: because `_comparison_step_blocks` excludes `by` from every comparison's
metric set unconditionally, a recorded column of that name also gets no `vs_baseline`
delta and no seat in the correction family. That consequence does not depend on
`report_by` being declared, so **the warning does not either** — `W-STATS-STRATUM-SHADOWED`
fires whenever a step records a column named `by`, since the undeclared case is precisely
the one where the author has no other hint that the name is reserved. (It was gated on a
non-empty `by` block until the S4d whole-branch review; that gating left the dropped delta
entirely silent.) It is reported at the template's `aggregate` location rather than at
`statistics.report_by`, because the fault is the column and there may be no such config
key. `reference.md` documents no reserved metric names at all, which is the gap this entry
records — a future edit to § Reporting strata or § Steps and artifacts should say the name
is spent. Pinned by `test_a_derived_metric_named_by_is_refused_not_silently_overwritten`,
`test_a_recorded_column_named_by_keeps_its_metric_and_warns`, and
`test_a_recorded_by_column_warns_even_with_no_report_by_declared` (`tests/test_cli.py`).

## New warning identifier: `W-STATS-STRATUM-THIN`

S4d task 6. `reference.md`:2127 states the rule and stops at the validate boundary: "`validate`
rejects a `report_by` attribute that isn't declared in `data.units.attributes`, and warns when a
level would hold fewer units than `limits.min_reported_n` — before the run rather than at
disclosure." That warning (`W-STATS-REPORTBY-THIN`, `validate.py`) counts a level's size off
`strata.levels_for(roster, name)` — the *resolved* roster, all that exists before a run — so it
can state only what a level would hold if every resolved unit went on to complete. It cannot see
attrition: a level that looks comfortable pre-run can complete on a handful, or on nothing, once
`io.skip` and step failures are known. `W-STATS-STRATUM-THIN` (`cli.py`, inside the `report_by`
loop) closes that gap, counting each level's actual `completed` count and firing against the same
`limits.min_reported_n` — the disclosure `reference.md` § Reporting strata's "applies per stratum"
sentence and § What `study add` redacts both already say no automatic rule can judge safe over a
handful of units.

This is not a novel shape: `W-STATS-CONTRAST-THIN` already warns at run time for the same reason,
scoped to a `within` contrast's `n_paired` rather than a reporting level's `completed` — pairing,
like attrition, is only known once the run's units have resolved. Both live in `cli.py` rather
than `validate.py`, and `reference.md`'s § Validation table lists both as if they were validate-time
checks ("Contrast stratum is populated", "Reporting stratum is populated") — true for the roster-time
`W-STATS-REPORTBY-THIN` companion, but not for either run-time warning itself. `reference.md` names
no identifier for either at all, so this entry is the first record of `W-STATS-STRATUM-THIN`'s
existence as well as the second data point that the § Validation table's two rows blur a validate-time
estimate with a run-time actual.

The `isinstance(floor, (int, float)) and not isinstance(floor, bool)` guard on the floor comparison
is kept here even though task 4 dropped its counterpart from `validate.py`'s roster-time check. That
drop was sound only because `strata.levels_for` never emits a zero-count level, making a floor of `0`
(`False`) or `1` (`True`) unreachable at validate time — `len(keys) < floor` never fires either way.
A level's *completed* count can genuinely be `0` at run time (every unit in the level failed or was
skipped), so `min_reported_n: true` giving a floor of `1` makes `0 < 1` true; the guard is what keeps
that case from warning. Pinned by `test_min_reported_n_true_over_an_empty_level_does_not_warn`
(`tests/test_cli.py`), which fails without the guard.

The warning is placed ahead of both gates in the `report_by` loop — the empty-level `continue` and
the no-metric-produced check that follows it — rather than after either. A level thinned to zero by
attrition is skipped from the `by` block by design (an earlier amendment above), and is exactly the
most disclosive case; placing the warning after either gate would mean that case never warns.
Pinned by `test_a_stratum_thinned_by_attrition_warns_at_run_time` and
`test_a_thick_stratum_does_not_warn_stratum_thin` (`tests/test_cli.py`).

## Residue carried out of the S4d whole-branch review

Triaged as "may ship" at `e5e7f95`, recorded here because the SDD workspace holding the ledger is
deleted once a slice merges. Each is real; none blocked merge.

| Carried | Why it is safe today, and what changes that |
|---|---|
| The second empty-level gate in `cli`'s stratum loop — attach a block only when the level's table produced a metric entry — is unpinned: the mutation survives the suite | It is currently **unreachable**, because the first gate (`if not level_collapsed: continue`) already catches every empty level a numeric-only table can produce. It goes live when **S4e** lands non-numeric recorded columns, where a level can have rows that yield no numeric metric. Attach the test there rather than deleting the gate now |
| A `report_by` whose every level is empty, with `limits.min_reported_n` absent, produces no `by` block and no diagnostic | A narrow silent no-op: the author asked for stratification and got nothing, with nothing said. Reachable only when every unit fails or is skipped, which a run already discloses through `n`. Worth a warning the day someone hits it |
| `E-STATS-CONTRAST-UNKNOWN` renders its value with `!r` where `E-STATS-REPORTBY-UNKNOWN` no longer does | Defensible rather than inconsistent: the contrast code guards a value that has not been narrowed to `str`, so showing its repr distinguishes `1` from `"1"` — exactly the coercion trap `units_matching` exists for. Left as is deliberately |
| A stratum level whose every resample draw is degenerate records `resample_draws: 0` with no warning on stdout | The record carries the count, so a reader can see it; only the console disclosure is missing. The parent-level sibling (`W-STATS-AGGREGATE-FAILED`) warns, so the asymmetry is worth closing when strata reporting is next touched |

**AMENDED 2026-08-11 (S5 checkpoint audit):** `S4e` names a slice
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md` § The slices does not define —
it runs S1–S5 and then "hardening slices". This deferral has no owner. Reassigned by task 16 of
`docs/superpowers/plans/2026-08-11-s5-checkpoint.md`.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): reassigned, row by row.** The spine now defines a
closed set of named hardening slices (§ The hardening slices, amended by this task), and `S4e`'s
work — non-numeric recorded columns — belongs to **H5 Artifacts**.

| Carried | Owner |
|---|---|
| The second empty-level gate in `cli`'s stratum loop is unpinned | **H5 Artifacts.** The gate goes live exactly when non-numeric recorded columns land, which is H5's work; the test attaches there, and the gate is not deleted in the meantime |
| A `report_by` whose every level is empty produces no `by` block and no diagnostic | **H4 Statistics**, which owns `report_by` hardening. A new warning identifier, so it is H4's to mint and to add to `reference.md` § Warnings core reports |
| `E-STATS-CONTRAST-UNKNOWN` renders with `!r` where `E-STATS-REPORTBY-UNKNOWN` does not | **No slice; closed as deliberate.** The row already argues it: showing the repr distinguishes `1` from `"1"` where the value has not been narrowed to `str` |
| A stratum level whose every resample draw is degenerate records `resample_draws: 0` with no console warning | **H4 Statistics.** The record carries the count, so only the disclosure is missing; the parent-level sibling `W-STATS-AGGREGATE-FAILED` already warns, and H4 owns both sides of that asymmetry |

## New identifiers: `E-STEP-ESTIMATE-SCOPE`, `E-STEP-ESTIMATE-METHOD`, `W-STEP-ESTIMATE-N`

S5a task 4. `reference.md` § `Estimate` ("`Estimate` carries your interval without core claiming
it") states three rules in one bulleted list, each a declaration check rather than a judgement
about a step's statistics:

- "**`method` is required whenever `ci95` is present.**" — implemented as `E-STEP-ESTIMATE-METHOD`
  (`coercion.py`, at the point a `summary` step's return is coerced).
- "**`n` is optional but its absence is surfaced**, because an interval with no stated denominator
  is exactly the disclosure risk `min_reported_n` exists to catch." — implemented as
  `W-STEP-ESTIMATE-N` (`cli.py`, `command_run`, in the aggregate-phase collector — the same one
  `W-STATS-AGGREGATE-FAILED` warns into, so it prints with the run's other run-time findings and
  survives even though `assemble_run_yaml` takes no `Collector`).
- "**`Estimate` is accepted at `scope: "summary"` only.**" — implemented as `E-STEP-ESTIMATE-SCOPE`
  (`coercion.py`, same call site as `-METHOD`).

Same gap as `E-STATS-CONTRAST-WITHIN` above for `W-STEP-ESTIMATE-N`: the prose states the rule and
never names an identifier for it anywhere in the document — § Errors core raises' table (the row
at "An `Estimate` outside `"summary"` scope, or one carrying `ci95` with no `method`") only covers
the two `ContractError`s, because a warning that lets the run complete does not fit that table's
"raised by" framing, which is `ContractError`/`ArtifactError` only. `-SCOPE` and `-METHOD` are a
milder version of the same gap: that table names both identifiers, but the § `Estimate` bullet
list — the actual rule statement quoted above — names neither, so a reader of the rule in place has
to already know the errors table exists to find out what a violation is called. Recorded together
because all three read as one design (`Estimate`'s three declaration checks) and a fix to one prose
location plausibly wants to name all three at once.

Pinned by `test_an_estimate_is_refused_at_every_other_scope` and
`test_ci95_without_method_is_refused` (`-SCOPE`/`-METHOD`, `tests/test_coercion.py`, S5a task
1/2) and by `test_an_estimate_with_an_interval_and_no_n_warns`,
`test_an_estimate_with_an_n_does_not_warn`, and `test_an_estimate_with_no_interval_does_not_warn`
(`-N`, `tests/test_cli.py`, all three through `main(["run", ...])`).

## The importable surface names five things `publishable/__init__.py` does not export

**AMENDED 2026-08-11 (S5 checkpoint audit):** **Miscounted, and one claim is false.** `__all__`
holds nine names; the § The importable surface table names **seven** that are absent — `Unit`,
`Apparatus`, `BaseReport`, `register_template`, `register_resolver`, `register_probe`,
`register_writer`. The parenthetical "`register_template` is the only one of the four core
actually ships today" is **false**: `grep -rn "def register_" src/publishable/` returns nothing.
The template registry is `get_template`/`template_names` in `templates/registry.py`; there is no
`register_template` decorator. **Zero** of the four registries exist. The reverse direction is
clean — nothing is exported that the table does not name.

Carried from S5a task 1, confirmed still true after S5a task 4 exported `Estimate`. `reference.md`
§ The importable surface's table and its `from publishable import ...` example line list `Unit`,
`Apparatus`, `BaseReport`, and the four `register_template` · `register_resolver` · `register_probe`
· `register_writer` decorators — none of which `src/publishable/__init__.py` exports. Checked
directly: `Unit` is a real, implemented class at `src/publishable/units.py:25`, simply left off
`__all__`; `Apparatus`, `BaseReport`, and the four `register_*` decorators are not defined anywhere
under `src/publishable/` at all — `grep -rn "class Apparatus\|class BaseReport\|def register_"
src/publishable/*.py` returns nothing.

The pattern is coherent rather than broken, which is why this is recorded rather than fixed here.
Each missing name belongs to a feature this build has not built and, per `CLAUDE.md`'s stated
non-promises, may be refusing on purpose: `Apparatus` and a probe are the apparatus core can only
observe — a facility for custom instrumentation; `register_resolver`/`register_probe` are the
plugin hooks for supplying your own unit roster or apparatus; `BaseReport`/`register_writer` are
report and artifact-writer overrides. None of the four registries the document bundles together in
one row (`register_template` is the only one of the four core actually ships today) has a home in
`src/publishable/` yet. `Estimate` is the control case: it is exported precisely because S5a built
the feature it names, and only S5a's task 4 export closed that gap for `Estimate` specifically — the
other five names are exactly as unexported as they were before S5a, and this entry is what keeps
that from reading as new breakage.

`Unit` differs from the other four in kind, not just in whether core has built the feature: the
class exists, is complete, and is exercised by name in six test files — `test_artifacts.py`,
`test_units.py`, `test_contrasts.py`, `test_cli.py`, `test_runner.py`, `test_replication.py` — every
one of them importing `from publishable.units import Unit` rather than `from publishable import
Unit`. That is a live instance of the one-import-root invariant's own rule ("no second path to any
name") being violated inside this repository's own test suite, pre-existing and untouched by this
slice. `Apparatus`, `BaseReport`, and the four `register_*` decorators cannot be imported by *any*
path, so no test could violate the rule for them even by accident — the violation is specific to the
one name among the five that core has actually implemented.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): the audit amendment above is itself now STALE, and
the document half is CLOSED.** Two corrections to it, both caused by work that landed after it was
written:

- `__all__` holds **ten** names, not nine — task 5 exported `Unit`, which was the one name in the
  list whose feature core had actually built. The list is `ArtifactError`, `ArtifactExistsError`,
  `BaseExperiment`, `BaseStep`, `BaseTemplate`, `ContractError`, `Estimate`, `Param`,
  `PublishableError`, `Unit`.
- The § The importable surface table therefore names **six** absent things, not seven:
  `Apparatus`, `BaseReport`, and the four `register_*` decorators. The audit's finding that **zero**
  of the four registries exist stands and is still true — `grep -rn "def register_"
  src/publishable/` returns nothing.

**The document half is closed.** Task 5 gave the table a `Status` column marking each row `built`
or `not yet built`, and added the paragraph that makes the promise explicit: "**A row marked `not
yet built` is a promise, not an export.** Importing one raises `ImportError` today." That is the
resolution — the table stays the enumerated surface plugins are written against, and a reader can
now tell which rows they can import. The one-import-root violation task 1 found in this repo's own
tests (`from publishable.units import Unit`) is closed by the export.

**Open residual, routed: Owner H7 Plugins and the apparatus** (spine § The hardening slices), which
owns all six remaining names — `Apparatus` and `register_probe` are the apparatus,
`register_template`/`register_resolver`/`register_writer` are the other three registries, and
`BaseReport` is the report override. `BaseReport` is shared with **H8 Studies and reporting**,
which builds `report`; H7 exports the name, H8 makes it do something.

**AMENDED 2026-08-15 (spec-defects staleness audit at `5578988`): one of the six landed, and the
audit's "zero registries exist" no longer stands.** H7a shipped project-local templates, so
`register_template` is defined (`src/publishable/templates/discovery.py`) and exported: `__all__`
holds **eleven** names, not ten, and `reference.md` § The importable surface marks that row `built`
while the other three registries keep `not yet built` — document and code agree, so this is a
closure rather than a new divergence. **One** of the four registries exists, not zero. The table
therefore names **five** absent things, not six: `Apparatus`, `BaseReport`, `register_resolver`,
`register_probe`, `register_writer`. The residual narrows with it and stays H7's, now by sub-slice:
`register_resolver`/`register_writer`, `register_probe` and `Apparatus` are **H7b/H7d** — H7a shipped
none of entry-point resolution, the other three registries, probes, the `Apparatus`, or the change
gate — and `BaseReport` is still shared with **H8**.

## Carried out of S5a for S5b: `Estimate.ci95` has no length or ordering rule

The whole-branch review recorded this rather than fixing it, and it is not a defect in S5a:
`reference.md` § `Estimate` states three rules — `method` required whenever `ci95` is present, a
surfaced missing `n`, and `summary` scope only — and says nothing about `ci95`'s shape. So core
stores whatever list the step supplied, including a one-element or reversed one.

**S5b is where that stops being harmless.** A hypothesis may declare `evaluate_on: ci95_lower` or
`ci95_upper`, and `reference.md` § What a hypothesis is tested against says that "when the metric
is a reported `Estimate`, the bound tested is the one the step supplied". Reading a bound means
indexing that list, so S5b must decide what a malformed one does before it can evaluate a verdict
against it: refuse it at coercion under the existing `E-STEP-ESTIMATE-METHOD` sibling, refuse it
when a hypothesis names it, or define the ordering as the author's responsibility and say so.
Deciding by accident — indexing `[0]` and `[1]` and trusting — is the one option that produces a
verdict nobody can check.

**RESOLVED by S5b task 2, as the first option above.** `_coerce_estimate` (`coercion.py`) now
checks the coerced `ci95` list — after the existing `method` check, and after the fields are
coerced, so the comparison is between plain floats rather than `numpy.float64` — and refuses a
length other than two, or a lower bound greater than its upper, as **`E-STEP-ESTIMATE-CI95`**.
`grep -rn "E-STEP-ESTIMATE" src/ docs/` at the start of this task found `reference.md` § Errors
core raises already naming `E-STEP-ESTIMATE-SCOPE` and `E-STEP-ESTIMATE-METHOD`, but nothing
covering `ci95`'s shape or order, confirming the gap this entry described rather than closing it
by reuse — so `E-STEP-ESTIMATE-CI95` is a genuinely new identifier, not a rename. It is a fourth
rule alongside the three `reference.md` § `Estimate` states (`method` required, a surfaced missing
`n`, `summary` scope only); the document does not name it, because nothing indexed the list by
position until `evaluate_on: ci95_lower`/`ci95_upper` did. The check deliberately uses `>`, not
`>=`, for the ordering half: a zero-width interval is legitimate (S4b's point-mass bootstrap
produces one), and refusing an equal pair would refuse a correct answer to protect against a
malformed one. Pinned by `test_a_ci95_that_is_not_two_elements_is_refused`,
`test_a_reversed_ci95_is_refused`, and `test_an_equal_pair_is_allowed`, all in
`tests/test_coercion.py`.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED — the document caught up with the code.**
The paragraph above notes that "the document does not name it". Task 8 fixed that: `reference.md`
§ `Estimate` now states **five** rules rather than three, and § Errors core raises carries the row
"An `Estimate` whose `ci95` is not two numbers in ascending order, or whose `value` is not a
number | `ContractError` · `E-STEP-ESTIMATE-CI95`, `E-STEP-ESTIMATE-VALUE`". Nothing owes this
entry.

## New error identifiers: `E-HYPOTHESIS-METRIC`, `E-HYPOTHESIS-FORM`, `E-HYPOTHESIS-DIRECTION`, `E-HYPOTHESIS-EVALUATE-ON`, `E-HYPOTHESIS-BASELINE`, `E-HYPOTHESIS-CONTRAST`, `E-HYPOTHESIS-BOUND`, `E-HYPOTHESIS-COMPARE-TO`, `W-HYPOTHESIS-INFERENCE-BASE`

S5b tasks 6 and 7. `grep -rn "E-HYPOTHESIS\|W-HYPOTHESIS" src/ tests/ docs/` at the start of each
task found only `E-HYPOTHESIS-UNSUPPORTED` (the blanket refusal this same slice's task 8 retires
once `cli` evaluates hypotheses for real); none of the eight below existed under any name. Task 7
extends this entry rather than opening a second, since both tasks close the identical gap — a
`reference.md` § Validation row stating a rule in prose and naming no identifier for it — against
different rows.

**`E-HYPOTHESIS-METRIC` and `E-HYPOTHESIS-FORM` implement rules `reference.md` § Validation
already states in prose but names no identifier for** — the same gap `E-STATS-CONTRAST-WITHIN`
above closed for `within`. The Validation table's two rows, quoted in full:

- "Hypothesis names a metric" — `hypotheses[1]` declares `compare.contrast` and no `metric`; "a
  contrast reports a value per step metric, so the quantity under test is unnamed." →
  `E-HYPOTHESIS-METRIC`, raised in `_check_hypotheses` (`validate.py`) for a missing, non-string,
  or dotless `metric`, and reused (not a third identifier) for a `metric` naming a step outside
  the entrypoint's `steps` list — that string also fails to name a quantity the run will ever
  produce, just by a different route, and reference.md draws no distinction between the two.
- "Hypothesis form matches its metric" — `hypotheses[1].metric` names a metric of a `scope:
  "summary"` step but declares `compare`; "a summary metric is one value per run, not a contrast
  between conditions — and a condition-step metric without `compare` is the same mistake
  inverted." → `E-HYPOTHESIS-FORM`, raised both directions: a `scope: "summary"` metric with
  `compare`, and a `condition`- or `repeat`-scoped metric without one.

**`E-HYPOTHESIS-DIRECTION` and `E-HYPOTHESIS-EVALUATE-ON` implement no rule the four documents
state at all** — worth recording plainly rather than leaving a future reader to wonder where they
came from. `direction` is never given an enumerated vocabulary in prose anywhere (`greater`/`less`
appear only in worked examples); `evaluate_on`'s vocabulary *is* documented
(`observed | ci95_lower | ci95_upper`, `reference.md` § What a hypothesis is tested against), but
no passage says an out-of-vocabulary value is checked, at `validate` or anywhere else. Both were
added instead to close a Task 4 review finding (Critical: `direction: greatr` on a superiority
hypothesis silently inverted the verdict, because the evaluator treated anything not `"greater"`
as `"less"` and never echoed `direction` into the record for a reader to catch by eye). Task 4's
own fix landed first, in `hypotheses.py::verdict_for`: `supported` is now `None`, never a wrong
verdict, for a `direction` outside `{greater, less}`. So the two new identifiers are **not**
equally urgent, and their diagnostics say so rather than sharing one framing:

- `E-HYPOTHESIS-DIRECTION` moves an *already-guarded* fault earlier — a mistyped `direction`
  today runs cleanly and returns an honest `supported: None`; this refusal means it never reaches
  a real run at all.
- `E-HYPOTHESIS-EVALUATE-ON` closes a fault with **no runtime guard whatsoever**:
  `hypotheses.py::_tested_number` reads `evaluate_on == "observed"`, then (failing that)
  `evaluate_on == "ci95_lower"`, and anything else — including a typo of either string — silently
  falls through to `ci95_upper`. A mistyped `evaluate_on` therefore builds a genuinely different,
  wrong verdict with nothing in the record to reveal the value was never recognized, since
  `verdict_evaluated_on` records what was *used*, not what was *typed*. This is the more urgent
  of the two.

Both are checked independently of `metric`/`compare` validity: a bad `direction` or `evaluate_on`
is its own declaration fault regardless of whether the metric also has problems. Pinned by
`test_a_mistyped_direction_is_refused_rather_than_silently_inverted`,
`test_a_valid_direction_is_not_flagged`,
`test_a_mistyped_evaluate_on_is_refused_rather_than_silently_read_as_an_upper_bound`,
`test_a_valid_evaluate_on_is_not_flagged`,
`test_a_hypothesis_with_compare_and_no_metric_is_refused`,
`test_a_summary_metric_hypothesis_may_not_declare_compare`,
`test_a_condition_metric_hypothesis_must_declare_compare`,
`test_a_hypothesis_naming_an_undeclared_step_is_refused_as_a_metric_fault`, and
`test_a_hypothesis_entry_that_is_not_a_mapping_is_refused_as_a_metric_fault`, all in
`tests/test_validate.py`, all exercised through `validate_config`.

**`E-HYPOTHESIS-BASELINE`, `E-HYPOTHESIS-CONTRAST`, `E-HYPOTHESIS-BOUND`, and
`W-HYPOTHESIS-INFERENCE-BASE` (task 7) close the same gap as `E-HYPOTHESIS-METRIC`/`-FORM` above,
against the four remaining `reference.md` § Validation rows that state a rule in prose and name no
identifier for it.** Quoted in full:

- "Hypothesis needs baseline" — `hypotheses[0].compare.to: baseline` but `sweep.baseline` is not
  declared. → `E-HYPOTHESIS-BASELINE`. Nothing downstream guards this: `hypotheses.resolve` reads
  `vs_baseline`, which `cli` never populates without a declared baseline, so an unrefused
  `compare.to: baseline` would silently resolve to no observation rather than the comparison it
  names.
- "Hypothesis names a real contrast" — `hypotheses[1].compare.contrast` is `invariance`, which
  `statistics.contrasts` does not declare. → `E-HYPOTHESIS-CONTRAST`. The same unresolvable-label
  class `_check_contrasts` already refuses for `of`/`against` (`E-STATS-CONTRAST-UNKNOWN`), applied
  to the one other place a config names a contrast by `id`.
- "Hypothesis bound exists" — `evaluate_on` names a bound, but `data.units` is undeclared and
  template `generic` defines no `aggregate`, so no metric this run computes can carry an interval.
  → `E-HYPOTHESIS-BOUND`. Checked directly against the code rather than assumed: `GenericTemplate`
  (`src/publishable/templates/builtin/generic.py`) declares no `aggregate` method at all, so it
  inherits `BaseTemplate.aggregate`'s `{}`-returning default — `generic` being the only template
  this build registers, the `aggregate`-half of `reference.md`'s stated condition holds for every
  config naming it, and `data.units` presence is what discriminates in practice. The check still
  reads `type(template).aggregate is BaseTemplate.aggregate` rather than hard-coding that fact, so
  a future template that overrides `aggregate` clears the condition without this check changing.
- "Hypothesis has an inference base" — a hypothesis names a metric under the same declarations,
  without a bound: every metric will be `basis: repeats`, so it can be reported but not tested
  (**warning**). → `W-HYPOTHESIS-INFERENCE-BASE`, firing on the opposite branch from
  `E-HYPOTHESIS-BOUND` under the same gate described below: `evaluate_on` absent or `observed`
  instead of a bound. The two were verified to actually discriminate each other — a config with
  `evaluate_on: ci95_lower` gets the error and not the warning; the same config with `evaluate_on`
  removed gets the warning and not the error — rather than one silently subsuming the other.

**Both `E-HYPOTHESIS-BOUND` and `W-HYPOTHESIS-INFERENCE-BASE` carry a third gate beyond the
two-condition test above, on the metric's declared `scope`, and the code states that gate in the
docstring rather than only here** — this paragraph exists because an earlier draft of this entry
described the warning as sharing the error's condition "exactly" and omitted the gate from the
file entirely, which a task-7 review round caught as a record misdescribing the code it records.
The gate: neither check fires when the hypothesis's `metric` resolves (via `experiment.steps`) to
`scope: "summary"`, or to a scope this pass cannot determine at all (no imported `experiment`, or a
`metric` that isn't a well-formed `step.metric` string) — only a `metric` whose scope is
affirmatively known and is **not** `"summary"` reaches either check. The two-condition test's own
premise is `data.units` undeclared *and* `generic` has no `aggregate`, i.e. no `basis: units`
metric can exist — but `reference.md` § What a hypothesis is tested against ("A hypothesis may name
a summary metric") lets a `scope: "summary"` step return an `Estimate` marked `reported: true`,
with its own real `ci95` and no unit table involved at all, and CLAUDE.md's own invariant is
explicit that this is "the one interval core stores *without computing*" — which is exactly what
the Validation row's wording, "no metric this run **computes**", already excludes. Core never
inspects a step's body ([Greenfield-only](../design-principles.md#greenfield-only)) to know whether
*this* summary step actually returns one, so the gate cannot be narrower than "unknown scope is
treated like `summary`" without risking the same false refusal for a scope this pass genuinely
cannot resolve.

**The two checks are gated identically, but for two different, independently sufficient reasons —
not because the error's reason was copied onto the warning.** `command_run` treats an
`E-HYPOTHESIS-BOUND` finding as `c.has_errors`, a hard stop — refusing it unconditionally on the
two-condition test would permanently block a design `reference.md` explicitly permits, not merely
defer its verdict to run time. That argument does not transfer to the warning: a warning never
stops a run, so "it would block the run" cannot justify skipping it, and a first pass at this
change gated the warning on the error's reasoning anyway, which a review round caught as wrong
reasoning reused rather than independently checked — the caught consequence was a units-less run
with a `scope: "summary"` hypothesis and no bound getting no
warning at all, silently. The warning has its own, sufficient reason to share the gate: its stated
premise is "every metric will be `basis: repeats`", and that premise is false for a `scope:
"summary"` metric that turns out to be a `reported: true` `Estimate` — it is neither `basis:
repeats` nor untestable, it is `reported`, carries its own interval, and is exactly what
`evaluate_on` can test. The code's comment and docstring paragraph for the warning now say this
reason in its own words rather than pointing at the error's.

**The scope-parsing itself was reordered once more in the same review round, to fix a
double-report.** `metric: "step01_measure"` (no `.`) still `.partition(".")`s to
`("step01_measure", "", "")`, so `step` can collide with a real declared step name even though
`name` is empty and the metric is definitively malformed — before the fix, that let the bound/
warning block run *before* the malformed-`metric` refusal below it and read a real `scope` for an
entry about to be refused anyway, reporting one fault (a dotless `metric`) under two codes. The
fix: a `metric_is_well_formed` flag (parses to a non-empty `step.metric`) gates the bound/warning
block, checked *before* the `E-HYPOTHESIS-METRIC` refusal rather than after, so a malformed
`metric` is reported exactly once. The review separately confirmed the *other* half of "unknown
scope" — a well-formed `metric` naming a step the entrypoint's `steps` list does not declare — was
already sound: every route to an unresolvable step already reaches its own `E-HYPOTHESIS-METRIC`
below, unaffected by this reordering.

Pinned by `test_a_hypothesis_compared_to_baseline_needs_a_declared_baseline`,
`test_a_hypothesis_compared_to_a_declared_baseline_is_not_flagged`,
`test_a_hypothesis_naming_an_undeclared_contrast_is_refused`,
`test_a_hypothesis_naming_a_declared_contrast_is_not_flagged`,
`test_a_bound_hypothesis_is_refused_when_no_metric_could_carry_an_interval`,
`test_a_bound_hypothesis_is_not_flagged_once_units_are_declared`,
`test_a_hypothesis_with_no_inference_base_warns_rather_than_refuses`,
`test_a_hypothesis_with_an_inference_base_is_not_warned`,
`test_a_summary_metric_bound_is_not_refused_even_with_no_units` (the scope gate itself, on the
error side),
`test_a_summary_metric_hypothesis_gets_no_inference_base_warning` (the scope gate on the warning
side, independently — added in the review round once the shared-gate consequence above was
caught),
`test_a_dotless_metric_is_refused_once_even_when_it_names_a_real_step` (the double-report fix), and
`test_a_condition_scoped_bound_is_still_refused` (pins the gate's exact membership — `{None,
"summary"}` — using `write_config_three_scopes`, added because no earlier fixture declared a
`condition`-scoped step and a mutation widening the gate to also exempt `condition` scope passed
the entire suite without one), all in `tests/test_validate.py`, all exercised through
`validate_config`.

**`E-HYPOTHESIS-COMPARE-TO` (task 8, review round 1) closes the same gap once more, against a
field no document gives a vocabulary for.** `reference.md` § Pre-registration writes `to:
baseline` in every example and core computes no other per-condition comparison — a claim against
some other condition is a `statistics.contrasts` entry, reached through `compare.contrast`. But
`hypotheses.resolve` never reads `to` at all: it looks the named `condition` up in `vs_baseline`
and returns whatever is there. So `to: method=kendall` validated clean, ran, and produced a
verdict about the baseline comparison under a config that asked for something else, with nothing
in `run.yaml` recording the substitution — the silent-wrong-answer class, not the
declaration-that-does-nothing class. Refused in `_check_hypotheses` whenever `to` is present and
is not `baseline`; absent stays legal, since the condition form's default is the only comparison
there is. Pinned by `test_a_hypothesis_compared_to_something_other_than_the_baseline_is_refused`,
with the negative half added to
`test_a_hypothesis_compared_to_a_declared_baseline_is_not_flagged`, both in
`tests/test_validate.py` through `validate_config`.

## A comparison's `observed` block carries `method`, which the document's example omits

Found by the S5b task 10 review. `reference.md` § Pre-registration's worked verdict shows a
comparison-form `observed` as `{delta, ci95, ci95_corrected}`, and `hypotheses._observed_block`'s
docstring repeats that shape — but `cli` sets `method` on every comparison entry, so the block a
run actually produces carries four keys, not three. The acceptance test pins reality; the document
and the docstring are what is incomplete.

Not a code defect: `method` is required beside any interval core reports, so its presence is
correct and its absence from the example is the omission. **Assigned to the S5 checkpoint**, where
every entry in this file is reconciled against the four documents — the fix is a one-key addition
to that example plus a docstring line, and it belongs with the other document reconciliations
rather than as a lone edit now.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED.** Task 8 made the one-key addition:
`reference.md` § Pre-registration's `h1` verdict now reads `observed: {delta: 0.026, ci95:
[-0.007, 0.059], method: paired_percentile_over_units, ci95_corrected: [-0.007, 0.059]}`, four keys
as the run produces them. The new `h3` example shows the same shape in its degenerate form
(`method: null` beside `ci95: null`), which also makes the rule visible rather than only obeyed.
Nothing owes this entry.

## New error identifiers: `E-STEP-ESTIMATE-VALUE`, and a numeric-type rule under `E-STEP-ESTIMATE-CI95`

Found by the S5b whole-branch review as its Critical (`value`) and its first Important
(`ci95`). `grep -rn "E-STEP-ESTIMATE" README.md docs/design-principles.md
docs/experimental-designs.md docs/reference.md` finds one line — `reference.md` § Errors core
raises, naming `E-STEP-ESTIMATE-SCOPE` and `E-STEP-ESTIMATE-METHOD` — so, exactly as the `ci95`
length and ordering rules above, neither the numeric-type rule nor an identifier for it exists in
the four documents.

**The defect.** `hypotheses._tested_number` calls `float()` on a reported `Estimate`'s `value`, and
on `ci95[0]`/`ci95[1]`, with no guard; `coercion._coerce_one` accepts `str` as a scalar, because a
`str` in a recorded column is perfectly legal. So a `summary` step returning
`Estimate(value="high")` plus a hypothesis naming that metric raised `ValueError: could not convert
string to float: 'high'` in phase 8 — after every execution was spent, before `run.yaml` was
written, and `main` catches only `PublishableError`/`OSError`. The whole record was lost to a
traceback over one badly typed field, the same failure shape S3's review graded Critical for
`aggregate`. `ci95` had a nearer-term variant: `[0.1, None]` — a one-sided interval writing only
the bound it has, which `reference.md`'s own summary example ("one-sided BCa") makes plausible —
reached `coerced_ci95[0] > coerced_ci95[1]` and raised a raw `TypeError` in place of a diagnostic.

**The split, and why.** The `ci95` fault reuses **`E-STEP-ESTIMATE-CI95`**: that identifier already
carries two rules about the shape of this one field (exactly two elements, lower before upper), and
"each element is a number" is the third rule of the same kind, read by the same
`evaluate_on: ci95_lower`/`ci95_upper` indexing that motivated the first two. Splitting it would
give one field three identifiers a reader has to distinguish for no gain. The `value` fault gets its
own, **`E-STEP-ESTIMATE-VALUE`**, rather than reusing `E-STEP-RETURN-TYPE`: that code's message says
in so many words that "values must be a scalar — a bool, int, float, str, or None", which is *true*
everywhere else in `coercion` and false here, so reusing it would print one identifier under two
contradictory rules. `-METHOD` and `-SCOPE` are plainly about other fields.

**Both are refused in `_coerce_estimate`, not at the read site.** That is where the three other
`Estimate` rules live, one place decides what a step's return may contain, and refusing at the
return puts the cost at the one step that made the mistake: `runner` contains a step's raise, so the
execution fails with an identifier and the run keeps its record. The read site cannot do better —
`hypotheses` is pure, has no diagnostics channel, and by phase 8 the compute is already spent.

**The Critical has one door, checked rather than assumed.** A `summary` step returning a plain
`{"adjusted": "high"}` — no `Estimate` — never reaches `_coerce_estimate`, and `_coerce_one` accepts
a `str`. That path is closed by `resolve`'s `isinstance(block, dict)` guard: `summary_values` leaves
a non-`Estimate` return exactly as it came back, so the metric is a string where a block belongs,
`block` is `None`, and the verdict is an honest `supported: null`. Pinned by
`test_a_plain_scalar_summary_return_is_no_block_rather_than_a_crash`. Not every refused shape
crashed, either: a `None` `value` never reached `float()` (`_tested_number` skips a `None` point
estimate) and is refused on the narrower ground that `Estimate.value` is declared a number.

**`n` is deliberately outside the rule.** No verdict is read against it, and a step reporting its
own base as a label (`n="612 pairs"`) is describing rather than asserting. Pinned as a boundary by
`test_an_estimates_own_n_may_still_be_a_label` so the omission reads as a decision rather than an
oversight.

Proposed resolution: `reference.md` § `Estimate` states four rules and should state six — the `ci95`
length/order/element-type rule (one line, since it is one field) and `value` being numeric — and §
Errors core raises should name `E-STEP-ESTIMATE-CI95` and `E-STEP-ESTIMATE-VALUE` beside the two
identifiers already there. Pinned by `test_a_non_numeric_ci95_bound_is_refused`,
`test_a_non_numeric_estimate_value_is_refused` and `test_an_estimates_own_n_may_still_be_a_label` in
`tests/test_coercion.py`, and end to end by
`test_a_non_numeric_reported_estimate_does_not_cost_the_run_its_record` in `tests/test_cli.py`,
which asserts the run reaches `partial` with `run.yaml` written rather than crashing.

## New error identifiers: `E-HYPOTHESIS-KIND`, `E-HYPOTHESIS-THRESHOLD`, `E-HYPOTHESIS-CONDITION`

S5b whole-branch review, Importants 2(a), 2(b) and 2(c). `grep -rn "E-HYPOTHESIS" README.md
docs/design-principles.md docs/experimental-designs.md docs/reference.md` finds nothing at all, so
these extend the entry above in the same way task 7 extended task 6's: a `reference.md` rule stated
in prose or in a config example, with no identifier for it.

**`kind`, `direction` and `threshold` are required, and no document says so.** § The one config file
writes all three in every hypothesis and gives a default for none of them, which is the whole basis
for requiring them — but "no default is shown" is not the same sentence as "the field is required",
and the three fail differently when absent:

| Field | What an absent value did |
|---|---|
| `kind` | `_is_counted` tests `== "confirmatory"`, so the hypothesis silently left its correction family and the verdict was decided on the **raw** — tighter — bound. Over-support, demonstrated by the reviewer as `supported: false` becoming `supported: true` on one character (`confirmatry`) |
| `direction` | `verdict_for` sets `supported` only for `greater`/`less`, so the verdict came back `null` after the full run, with nothing saying why |
| `threshold` | Same, through the `isinstance(threshold, (int, float))` guard |

`kind` is the one that mattered: `direction` and `evaluate_on` got identifiers in the entry above
partly *because* they were the risky pair, and `kind` — the third member of the same triple — had no
runtime guard and changed the level a verdict was decided at rather than voiding it. All three are
now refused in `_check_hypotheses`; `direction`'s existing check drops its `is not None` guard so
one field keeps one code. `evaluate_on` stays optional, because `observed` is a documented default
rather than an omission. `E-HYPOTHESIS-THRESHOLD` mirrors `verdict_for`'s own predicate exactly —
`int`/`float`, `bool` excluded — so validate refuses precisely what the evaluator declines to judge,
and `threshold: 0.0` (`reference.md`'s own superiority form) stays legal.

**`compare.condition` was never resolved against the declared labels.** `_check_contrasts` refuses
an unresolvable `of`/`against` with `E-STATS-CONTRAST-UNKNOWN`, built from `expand(doc)`'s labels;
nothing did the same job for `compare.condition`, though `compare.contrast` had
`E-HYPOTHESIS-CONTRAST`. `{condition: "method=spearmen"}` validated clean, `resolve` returned
`where=None, block=None`, and the verdict read `observed: null, supported: null` with no
explanation. **Naming the baseline's own label is the same fault with a different cause and gets the
same code:** `vs_baseline` holds one entry per *other* condition, because a baseline has no
comparison against itself, so the resolution is equally empty. The check is gated on
`E-HYPOTHESIS-BASELINE` not having fired for the same entry — with no declared baseline there is no
comparison for any label to name, and reporting the label as unknown as well would be the
double-report the dotless-`metric` ordering fix already exists to avoid.

`expand(doc)` can raise on a malformed sweep (a scalar where an axis's value list belongs), and
`validate` collects rather than raises, so `_condition_labels` returns `None` there and the label
test skips — `_check_sweep` is the check that reports the shape fault. `_check_contrasts` calls
`expand` unguarded from the same position and would raise on the same config; that is a pre-existing
gap in a different check, recorded here and deliberately not widened into this fix. One narrower
hole also stays open by choice: `compare: {condition: X}` with no `to` and no `sweep.baseline`
fires neither check — `E-HYPOTHESIS-BASELINE` needs `to: baseline`, and the label test is gated
on it — so it still validates clean and returns `supported: null`.

**AMENDED 2026-08-11 (task 14 of the S5 checkpoint plan): the paragraph above is now false, not
merely incomplete.** `_check_contrasts`' `expand(doc)` call is guarded (`conditions = []` on any
exception, matching `_condition_labels`'s own pattern), and — found while verifying that guard was
even reachable — `_check_sweep`'s own `expand(doc)` call, one statement earlier in
`validate_config`'s pipeline, was *also* unguarded and crashed first, on the identical input, with
no `statistics.contrasts` needed at all; that is fixed too (`E-SWEEP-EXPANDS-EMPTY` is skipped
rather than fired on the caught exception, since "could not expand" and "expanded to zero" are
different claims). `validate_config` now returns findings, not a traceback, for a malformed sweep
whether or not `statistics.contrasts` is declared. Pinned by
`test_a_malformed_sweep_with_contrasts_is_a_diagnostic_not_a_crash`,
`test_a_malformed_sweep_alone_with_no_contrasts_is_also_a_diagnostic`, and
`test_check_contrasts_guards_expand_when_called_directly`, all in `tests/test_validate.py`. The
second hole named just above — `compare: {condition: X}` with no `to` and no `sweep.baseline` — is
unaffected by this fix and stays open by the same decision restated where task 14's own entry lives
(§ "RESOLVED in S4c Task 9," amended below).

Proposed resolution: `reference.md` § The one config file should mark `kind`, `metric`, `direction`
and `threshold` as required within a `hypotheses` entry, and § Validation should carry two rows —
"Hypothesis kind is declared" and "Hypothesis names a real condition" — with the three identifiers.
Pinned by `test_a_hypothesis_kind_outside_the_two_is_refused`, `test_both_declared_kinds_are_accepted`,
`test_a_hypothesis_with_no_direction_is_refused`,
`test_a_missing_or_non_numeric_threshold_is_refused`, `test_a_zero_threshold_is_accepted`,
`test_a_hypothesis_naming_an_undeclared_condition_is_refused`,
`test_a_hypothesis_naming_the_baseline_itself_is_refused`,
`test_a_hypothesis_naming_a_declared_condition_is_not_flagged` and
`test_a_sweep_expand_cannot_read_leaves_the_condition_unchecked_rather_than_raising`, all in
`tests/test_validate.py` through `validate_config`.

## `supported: null` is a third verdict state, and no document states either rule that produces it

S5b whole-branch review, Important 6. Both rules below are implemented, load-bearing, and recorded
nowhere that ships: `reference.md` § Pre-registration shows `supported: true` and reasons about
`supported: false`, and never says a verdict may be absent. Their justification lived only in
`progress.md`, which is gitignored, and the slice's own design document promised an entry for the
second one ("Nothing in `reference.md` covers this, so it gets a `spec-defects.md` entry").

**1. An unresolvable observation is `supported: null`, never `false`.** A hypothesis may name a
metric no run produced — its step failed, or every unit in the comparison was ineligible, or (before
the check above existed) it named a label that resolved to nothing. `hypotheses.resolve` returns
`block=None`, `_observed_block` returns `None`, and `verdict_for` leaves `supported` as `None`. A
`false` there would be indistinguishable from a claim that was tested and failed, which is the
worse of the two errors by a wide margin: it publishes a refutation nobody measured. The same
reasoning covers a `direction` outside `{greater, less}` and a non-numeric `threshold` — both now
refused at validate time, so the runtime path is a second line of defence rather than the only one.

**2. A corrected bound the correction could not build is also `supported: null`, beside
`observed.ci95_corrected: null`.** Task 8's ruling. When a confirmatory hypothesis evaluating on a
bound is in a corrected family whose per-comparison level cannot be produced — a family too large
for the resample's draws to support (`thin`), or `fdr_bh`, which implies no per-comparison level at
all — falling back to the raw interval would answer a question nobody asked, on the *tighter* of
the two bounds. The error direction is over-support: `supported: true` decided at α when the
verdict was asked for at α/m. So there is no number and no verdict. Chosen over a warning for the
project's own reason — a number that looks handled and is not is worse than an honest absence — and
because a pure function has no diagnostics channel: `run.yaml` has nowhere to carry a finding, so a
warning on stdout would leave the record still claiming a verdict it cannot support.

**Three states, not two, is the distinction that makes this readable.** `ci95_corrected` *absent*
means no correction was attempted at all (`correction: none`, or a hypothesis outside the family),
and the raw interval is then the right one to test. `ci95_corrected: null` means the opposite — a
level was demanded and could not be built — which is the same disclosure `W-STATS-CORRECTED-THIN`
makes on the sweep side, where "`ci95_corrected` is null rather than too narrow".

Proposed resolution: § Pre-registration should say `supported` has three states and name both
routes to the third, and the `run.yaml` verdict example should show `ci95_corrected: null` beside
`supported: null` once. Pinned by `test_a_bound_the_correction_could_not_build_is_supported_null` for the second rule and
`test_an_unresolvable_observation_is_supported_null_not_false`,
`test_a_bound_test_on_a_metric_with_no_interval_is_supported_null` and
`test_a_misspelled_direction_is_supported_null_not_a_wrong_verdict` for the first, all in
`tests/test_hypotheses.py`.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED, exactly as proposed.** Task 8 landed both
halves in `reference.md` § Pre-registration: the paragraph "**`supported` has three states, and the
third is not a failure.**" names both routes and states how a reader tells them apart (`observed:
null` for the unresolvable observation, a real `observed` block with a `null` bound for the other),
and the `run.yaml` example gained an `h3` showing the second route — one paired unit, a `delta`,
`ci95: null`, `method: null`, `supported: null`, `verdict_evaluated_on: ci95_lower`. Task 16 checked
the enum-comment class over this: no inline `# a | b | c` comment anywhere enumerates `supported`'s
states, so none went stale.

## A non-numeric `aggregate` return may reach `float()` uncontained

**AMENDED 2026-08-11 (S5 checkpoint audit):** **Not reachable**, but the containment is
incidental. The closure routes through `coerce_scalars`, which accepts `str`, so this entry's
suspicion that a `str` is refused upstream is wrong. Every call site sits inside an `except
Exception` whose docstring justifies it **only** as degenerate-draw handling —
`percentile_of_derived`, `paired_delta_of_derived`, `paired_percentile_of_derived` in `stats.py`,
and the strata path in `cli.py`. A template returning `{"m": "high"}` yields `ci95: null`,
`W-STATS-AGGREGATE-FAILED`, and a `str` in the metric's `value`. **No test pins this**, so a
plausible future narrowing of those handlers reopens the path with nothing failing. Pinned by
task 14 of this plan.

Surfaced by the S5b whole-branch re-review as the sibling of that slice's Critical, in a different
function, and **predating S5b's base commit** — so it is neither introduced nor verified by that
branch.

S5b's Critical was `hypotheses._tested_number` calling `float()` on a value coercion had let
through as a `str`, which raised in phase 8 before `run.yaml` was written and cost a real run every
completed execution's record. That one is closed at `_coerce_estimate`. The re-reviewer noted the
same shape elsewhere: a template's `aggregate` returning a non-numeric scalar reaches `float()` in
the resample closure via `stats.paired_delta_of_derived`, and `_compute_vs_baseline` does not
contain it the way the single `aggregate` call is contained.

**Assigned to the S5 checkpoint.** Two things to establish there rather than assume: whether the
path is genuinely reachable — `coerce_scalars` runs over an `aggregate` return, so a bare `str`
may already be refused before it can reach the closure — and, if it is, whether the fix belongs at
the same layer the `Estimate` fix used, refusing the value where it enters rather than guarding
every place it is read. The general rule this slice ends on is worth stating: a `float()` on a
value core did not itself compute is a traceback waiting for the one config that supplies the wrong
type, and the fix belongs at the boundary the value crosses.

**AMENDED 2026-08-11 (S5 checkpoint, task 16): CLOSED.** Both questions the "Assigned to the S5
checkpoint" paragraph poses are answered. Reachability: **not reachable** — `coerce_scalars`
constrains a derived value to `bool`/`int`/`float`/`str`/`None`, so `float(value)` can only fail on
a non-numeric `str`, which raises `ValueError`, never the `TypeError` the plan predicted. Layer:
the containment stays where it is, and task 14 pinned it there — a non-numeric `aggregate` return
now has a test asserting it yields `ci95: null` and `W-STATS-AGGREGATE-FAILED` rather than a
traceback, so a future narrowing of those `except` handlers fails a test instead of reopening the
path silently. Nothing owes this entry.

## `E-UNIT-IMMUTABLE` was documented and implemented nowhere — CLOSED by task 12

**AMENDED 2026-08-11 (S5 checkpoint, task 16): the heading and the grep claim below are both FALSE
at HEAD.** Task 12 implemented the coded refusal, so `E-UNIT-IMMUTABLE` is now documented *and*
implemented: `grep -rn E-UNIT-IMMUTABLE src/ tests/` returns hits, not nothing. It is raised on all
four write paths (field write, declared-attribute write, `__setitem__`, `__delitem__`) plus
`pop`/`popitem`/`clear`/`update`/`setdefault`. Nothing in core mutated a `Unit`, so nothing
regressed. Two facts from that task worth keeping, because both were disproved prescriptions:
defining `__setattr__` in `Unit`'s class body is **impossible** (`@dataclass(frozen=True)` raises
`TypeError` overwriting a dunder in the class's own `__dict__`), and the base-class alternative was
built and disproved too (`_set_new_attribute` installs the frozen `__setattr__` regardless, so the
write raises `FrozenInstanceError`, not `ContractError`). The dunders are bound post-decoration.
Nothing owes this entry. The original text is kept below as filed.

Found by the S5 checkpoint audit, 2026-08-11 — not by any slice.

`docs/reference.md` names it twice: in § Errors core raises ("a write through a frozen `Unit`"),
and in § The unit list is three operations, and the units in it are frozen, which spends a
paragraph on why — the roster is resolved once per run and shared across every condition, so
`unit.attributes["scored"] = True` would edit what the next condition sees, and core cannot inspect
a step's body to catch it. The document states the object refuses instead, "raising `ContractError`
· `E-UNIT-IMMUTABLE` at the write".

`grep -rn E-UNIT-IMMUTABLE src/ tests/` returns nothing. `units.py`'s `Unit` is
`@dataclass(frozen=True, eq=False)`, so `unit.key = "x"` raises `dataclasses.FrozenInstanceError` —
no `.code`, and not a `PublishableError`, so `main()` does not catch it and the user gets a bare
traceback. `attributes` is a `MappingProxyType`, so the document's own example
`unit.attributes["scored"] = True` raises `TypeError`, also uncoded.

**Decision (C1 decision 2, settled by the user 2026-08-11): implement the coded refusal.** A
documented identifier that nothing raises is the class this repo says must not exist. Owned by
task 12 of `docs/superpowers/plans/2026-08-11-s5-checkpoint.md`.

## `repeat_spread` writes `{std: 0.0, n: 1}` for a *declared* single-repeat level

Found by task 9's reviewer during the S5 checkpoint, filed by task 16. **A probable code defect,
not an asymmetry to document** — this is the reviewer's judgement and it is recorded as such
rather than softened.

`replication.resolve_repeats` treats two situations differently, and `reference.md` § The two files
now states both:

- **No `replication` block at all.** One unlabeled repeat is resolved, and `repeat_spread` is
  **omitted**, on the stated ground that "a standard deviation over an execution that was never
  repeated would read as agreement between repeats that don't exist, the same mistake a zero-width
  `ci95` over one unit would make."
- **A declared level resolving to one contributing member** — `{kind: seed, n: 1}`, which
  `generic`'s `default_repeats` floor of 1 permits. `{std: 0.0, n: 1, kind: seed}` is written.

The reasoning that justifies the first refuses the second. There was no more agreement between
repeats in the declared case than in the undeclared one; the only difference is that the config
mentioned a repeat axis, which is a fact about the declaration, not about the dispersion. And the
document already establishes the general rule one level up: a dispersion computed from one sample
is refused — `ci95: null` below two units, `percentile_over_units`'s survivor floor,
`W-STATS-RESAMPLE-THIN`. A `0.0` here is the one place core reports a dispersion it did not
measure, and `0.0` is not a neutral value: it reads as "these repeats agreed", which is the
strongest statement the field can make.

The current text defends `n` as the discriminator — "`n` is what tells the two apart, since it
counts members that actually contributed a mean". That is true and is not enough: it asks every
reader and every downstream consumer to check a second field before believing the first, which is
the shape of defect this project's own standard rejects ("a number that looks handled and is not is
worse than an honest absence").

**Owner: H4 Statistics** (spine § The hardening slices). **The document consequence must not be
missed.** Under `CLAUDE.md`'s document-leads rule, `reference.md` § The two files now *specifies*
the `{std: 0.0, n: 1, kind}` shape, so H4 cannot simply change the code — the sentence beginning
"A *declared* repeat that happens to resolve one contributing member is a different fact" is the
one that changes, in the same slice and before the code does. Task 16 deliberately did **not**
change it here: which way it should go (omit the entry, or write `std: null`) is a design decision
about what a record should carry, not a reconciliation between two documents that disagree — the
four documents agree with each other today. What they may not agree with is the project's own
standard, and that is H4's call to make with an argument attached.

**AMENDED 2026-08-11 (whole-branch review, final fix pass): `reference.md` no longer blesses the
figure, and H4 no longer has to argue against it.** The clause "a `std` of `0.0` is what a single
real repeat's dispersion honestly is" is gone from § The two files. What replaces it states only
what is defensible — the figure is a *population* standard deviation, definitionally `0.0` over one
contributing member rather than an estimate of anything — and then names the omit-versus-zero
asymmetry as **open**, listing omitting the entry and `std: null` as the two successors, and saying
that the paragraph changes with the decision. So the document now records the divergence instead of
specifying it. Two consequences for H4: the `reference.md` edit is a small rewrite of an
already-hedged paragraph rather than a reversal, and `stats.py`'s `repeat_spread` docstring still
carries the original claim verbatim ("which is what a lone repeat's dispersion honestly is") — that
is the remaining copy of the sentence, and it was left in place because this pass was scoped to the
documents.

## `finalize` lets a declared attribute named `unit` shadow the unit key in `units.parquet`

Found by task 13's reviewer during the S5 checkpoint, filed by task 16. **Pre-existing, live, and
reachable from a config that validates clean** — the highest-priority open entry in this ledger.

`artifacts.py`'s `StepIO.finalize` builds each row as `merged: dict[str, Any] = {"unit": key}` and
then overwrites from the declared attributes:

```python
merged: dict[str, Any] = {"unit": key}
for name in attribute_names:
    merged[name] = owner.attributes.get(name) if owner else None
```

`units.py`'s `RESERVED_FIELDS` is `("key", "paths", "attributes")` — the three field names on
`Unit` — and does **not** include `"unit"`, the column name the table uses. So
`data.units.attributes: [unit]` passes validation, and every row's unit-key column is replaced by
that attribute's value. `columns = ["unit", *attribute_names, *recorded]` also carries `"unit"`
twice. The shipped artifact is corrupt in the one column that makes it a per-unit table: the
identity `n`, pairing, `n_paired` and every contrast rest on.

Two things bound the severity without reducing it:

- **The table a template's `aggregate` receives is unaffected** — `cli.py` restores the key from
  the roster rather than reading it out of the parquet — so no interval core computes today is
  wrong because of this. The damage is confined to the published `units.parquet`, which is exactly
  the artifact an outside reader is meant to be able to trust.
- **It needs a deliberate-looking config.** `attributes: [unit]` is not a plausible typo of
  anything. But it is a plausible *column name* in a real `index.csv` — a roster whose identity
  column is `patient_id` and which also carries a `unit` column naming a study unit is ordinary.

**Owner: H5 Artifacts** (spine § The hardening slices), which owns `units.parquet` integrity. Two
notes for whoever takes it. First, the natural fix — adding `"unit"` to `RESERVED_FIELDS` or
refusing the declaration at `validate` — **mints a new `E-` identifier**, which means it touches
`reference.md` § Errors core raises, the registry the four documents enumerate; that is document
work to be done first, not discovered late. Second, `RESERVED_FIELDS` currently means "field names
on `Unit`" and the fix needs it to mean "names an attribute may not take", which are two different
sets; conflating them is how the next reserved column gets missed.

## Six `provenance` and `results` keys in the `run.yaml` example that no code writes

Confirmed by task 9 as pre-existing drift, filed by task 16. `reference.md` § The two files'
`run.yaml` example shows `provenance.environment.os`, `.hostname`, `.hardware`,
`provenance.allocation` / `.allocation_hash`, and `provenance.upstream`. Nothing in
`src/publishable/` writes any of them.

**This is code owing the document, not the reverse, and the example must not be trimmed.** Each key
belongs to a feature the documents specify and this build has not implemented, and per `CLAUDE.md`
the documents lead. Removing them would have to be re-argued when each feature lands, which is the
same reasoning task 5 applied to § Package layout's unbuilt modules and to § The importable
surface's unbuilt names — both of which now carry an explicit "not yet built" marker rather than
being deleted.

Routed by feature:

| Keys | Owner |
|---|---|
| `provenance.environment.os`, `.hostname`, `.hardware` | **H6 Hashes and provenance** — environment capture is its subject |
| `provenance.allocation`, `provenance.allocation_hash` | **H3 Units**, which lands `allocation` and `holdout`; both write the one `allocation.json` the hash covers |
| `provenance.upstream` | **H8 Studies and reporting**, which owns lineage and upstream chains |

**Also recorded, and deliberately not fixed:** the example's `provenance` key order differs from
`cli.py`'s construction order. Cosmetic — YAML mappings are unordered and no reader depends on it —
and reordering the example to match today's code would pin the document to an implementation
detail, which is backwards. Recorded so it is not re-found and mistaken for drift.

**AMENDED 2026-08-13 (H3c1 arms-read, task 14): the `provenance.allocation`/`.allocation_hash` row
is now written.** `command_run` writes `allocation.json` (`artifacts.build_allocation_document`)
whenever a `sweep.groups` axis resolves an arm assignment, and sets `provenance.allocation` to the
literal path and `provenance.allocation_hash` to `artifacts.allocation_hash`'s digest of it —
`None`/`None` together when no such axis resolved, the same pairing `units`/`units_hash` already
use. `holdout` is not part of this: `E-DATA-HOLDOUT-UNSUPPORTED` still refuses every declaration of
it, so the file's `holdout` key stays unwritten until H3d lands it. The table's other two rows —
`provenance.environment.os`/`.hostname`/`.hardware` and `provenance.upstream` — are unaffected and
still unwritten.

## `register_template` appears outside § The importable surface — checked, not a defect

Raised by task 15 for awareness, dispositioned by task 16. `CLAUDE.md`'s one-import-root invariant
makes § The importable surface "the enumerated list", so a registered name appearing elsewhere is
worth checking. Checked: the other occurrences are in § Templates (where a local `templates/*.py`
is found by path, "making its `@register_template` argument the whole of its registration") and
§ Creating a plugin (the entry-point-is-the-registration rule). Both are prose *about* the
decorator's semantics, not a second enumeration of the surface, and § The importable surface's
table still names all four registries in one row. Nothing to fix; no owner. The related real
residual — that none of the four is exported, and the table now marks them `not yet built` — is
tracked in "The importable surface names five things `publishable/__init__.py` does not export"
above, owned by H7.

**AMENDED 2026-08-15 (spec-defects staleness audit at `5578988`): the disposition stands; its last
clause does not.** The § Templates and § Creating a plugin occurrences are still prose *about* the
decorator's semantics, so this remains not a defect. What changed is the tail: since H7a the
§ The importable surface table no longer marks `register_template` `not yet built` — it marks it
`built`, and `publishable` exports it — so "none of the four is exported" is false of that one name.
The related residual is correspondingly narrower; see the 2026-08-15 amendment on the entry this
paragraph points at.

## Validate-time `E-` identifiers have no registry, where `W-` ones now do

Found by task 16's cross-document pass, comparing the two registries against `src/`.

Task 4 built `reference.md` § Warnings core reports and it is **complete**: every `W-` identifier
`src/publishable/` emits has a row. The `E-` side is not symmetric. § Errors core raises is scoped
to *raised* exceptions — its own prose says so, and correctly: "each carries `.code`… the same
stable `E-` identifier a command prints beside a diagnostic". But roughly seventy **validate-time**
`E-` identifiers are emitted into the collector and enumerated nowhere in the four documents —
`E-CONFIG-SHAPE`, `E-PARAM-VALUE`, `E-SWEEP-AXIS-EMPTY`, `E-SWEEP-VALUE-UNNAMEABLE`,
`E-STATS-CONTRAST-*`, `E-REPL-*`, `E-UNITS-*`, and the whole `-UNSUPPORTED` family among them.
§ Validation's table names the *checks* rather than their identifiers, so a user who greps a
printed `E-STATS-REPORTBY-UNKNOWN` finds nothing in the documents.

Verified in both directions with a script over `src/**` and `reference.md`: no identifier appears in
the documents that `src/` does not emit (the four apparent doc-only hits — `E-BASE`, `E-FAILED`,
`E-THIN`, `E-VERSION` — are substring artifacts of `W-HYPOTHESIS-INFERENCE-BASE`,
`W-STATS-AGGREGATE-FAILED`, `W-STATS-CORRECTED-THIN` and `W-TEMPLATE-VERSION`, not real codes).
So this is an under-documented registry, not a divergent one, and nothing shipped is wrong.

**Recorded and routed rather than fixed here**, because closing it is a design decision of exactly
the shape the S5 checkpoint's decision 1 made for the `W-` side — whether § Validation gains
identifier columns, or a third table appears beside § Warnings core reports, or the rule is stated
that only raise-time codes are enumerated — and task 16's brief reserves design decisions for the
slice that owns them. **Owner: H1 Validation** (spine § The hardening slices): it builds the full
~85-check engine, so it mints most of the remaining identifiers and is the only slice positioned to
register them once rather than seventy times.

**This entry subsumes the unclosed half of every "New error identifier" entry above whose proposed
resolution was "add it to § Errors core raises".** Task 16 walked all 106 entries in this file and
found that fifteen of them propose exactly that for a **validate-time** code, which § Errors core
raises cannot accept — it is scoped to raised exceptions, so the proposal was unlandable as
written rather than merely undone. Those entries are otherwise complete (the code exists, is
tested, and its behaviour is settled); what each still owes is a registry seat, and that is this
entry's subject, not fifteen separate debts. The codes concerned:

`E-EXPERIMENT-EXISTS`, `E-PROJECT-EXISTS`, `E-SWEEP-EXPANDS-EMPTY`, `E-SWEEP-AXIS-EMPTY`,
`E-SWEEP-KEY-UNKNOWN`, `E-SWEEP-PATH-UNKNOWN`, `E-SWEEP-VALUE-UNNAMEABLE`,
`E-REPL-LEVEL-BATCH-INNER`, `E-REPL-LEVEL-DEPTH`, `E-REPL-LEVEL-DUPLICATE`, `E-REPL-LEVEL-FIELD`,
`E-REPL-FOLD-K`, `E-REPL-FOLD-K-TOO-LARGE`, `E-REPL-FOLD-NO-UNITS`, `E-REPL-ORDER-UNRESOLVED`,
`E-STATS-CONTRAST-WITHIN`, `E-STATS-CONTRAST-SAME-SIDES`, `E-STATS-CONTRAST-SHAPE`,
`E-STATS-CONTRAST-UNKNOWN`, `E-STATS-CONTRAST-NESTED`, `E-STATS-CORRECTION-UNKNOWN`,
`E-STATS-REPORTBY-UNKNOWN`, `E-HYPOTHESIS-BASELINE`, `E-HYPOTHESIS-BOUND`,
`E-HYPOTHESIS-COMPARE-TO`, `E-HYPOTHESIS-CONDITION`, `E-HYPOTHESIS-CONTRAST`, `E-UNITS-*`,
`E-CONFIG-*`, `E-DATA-*`, `E-META-REQUIRED`, `E-NAME-*`, `E-PARAM-*`, `E-TEMPLATE-*`, `E-GIT-*`,
`E-CODE-DIRTY`, `E-INPUT-CHANGED`, `E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED`, `E-ENTRYPOINT-REQUIRED`.

The **raise-time** codes those entries also proposed *were* landed — task 3 put eleven
`ContractError` rows into § Errors core raises, and task 4 put every `W-` code into § Warnings core
reports. So the split is clean: raise-time errors registered, warnings registered, validate-time
errors not, and H1 owns the third.

**AMENDED 2026-08-11 (H1 Validation): CLOSED, with two corrections to the code list above.** H1's
tasks 5–7 built `reference.md` § Errors `validate` reports, and every genuinely validate-time code
named above now has a row there, closing the "unclosed half" this entry described. Two entries in
the code list at "The codes concerned" were misclassified, found while landing the registry:

- **`E-REPL-ORDER-UNRESOLVED` does not belong on this list at all.** It is raised only by
  `replication.realize_order`, called only from `cli.py`'s run path — never from `validate.py` —
  so it was never validate-time, and it was already correctly sitting in § Errors core raises
  before this entry was written (S3b's docs pass landed it there). Its inclusion above conflated
  "an `E-REPL-*` code" with "a validate-time `E-REPL-*` code."
- **`E-EXPERIMENT-EXISTS` and `E-PROJECT-EXISTS` are not validate-time either.** Both are raised by
  creation commands (`generate_experiment`, `scaffold_project`) checking their own target before
  writing anything — genuinely raise-time, the same class as `E-STEP-EXISTS` beside them in their
  originating entry. They do not close via this registry; they, and seven siblings on the same
  run/creation surface, are still undocumented and are recorded as their own finding below, routed
  to the spine slice that owns run identity and provenance rather than to H1.

Every other code in the list — the `E-SWEEP-*` shape/value checks, the `E-REPL-LEVEL-*` and
`E-REPL-FOLD-*` declaration-shape family, the `E-STATS-CONTRAST-*` family,
`E-STATS-CORRECTION-UNKNOWN`, `E-STATS-REPORTBY-UNKNOWN`, the five `E-HYPOTHESIS-*` codes, and the
wildcard families (`E-UNITS-*`, `E-CONFIG-*`, `E-DATA-*`, `E-META-REQUIRED`, `E-NAME-*`,
`E-PARAM-*`, `E-TEMPLATE-*`) — is genuinely validate-time and now has a row in § Errors `validate`
reports. `E-GIT-*`, `E-CODE-DIRTY`, `E-INPUT-CHANGED`, `E-RUN-LOCKED`, and `E-RUN-ID-EXHAUSTED`
were also swept into the wildcard families above by description rather than by checking each: like
the two `-EXISTS` codes, these fire from `provenance.py`/`run_identity.py`/`cli.py`'s run path, not
from `validate.py`, and are part of the same undocumented-run-time-code finding below rather than
this registry. `E-ENTRYPOINT-REQUIRED` is the one exception among that batch that really is
validate-time (`validate._check_entrypoint` raises it directly) and really did close here.

## S5 checkpoint complete

Both `CLAUDE.md` consistency passes ran over the four documents on 2026-08-11 — the mechanical pass
by task 15 (clean, with a self-test confirming the anchor checker can fail), the cross-document pass
by task 16. Every entry above either closes, records work done, or names a slice the spine defines.
No entry defers to a description of a slice.

**The sweep was exhaustive, not sampled.** All **106** `##` entries in this file were walked. Of
those, **23 are open and each names a slice** (listed below); the remaining 83 close, and they close
in four ways, every one of which was checked rather than assumed:

- **~40 already close by their own heading** — `RESOLVED`, `RETIRED`, `ANSWERED`,
  `NO DOCUMENT CHANGE`, `PARTLY RESOLVED`, or an `(as originally filed)` twin kept as history.
- **~15 are "New error identifier" entries whose only remaining residue is a registry seat**, and
  that residue is now one entry rather than fifteen: see § Validate-time `E-` identifiers have no
  registry, where `W-` ones now do, which enumerates the codes and owns them under H1. Their
  raise-time siblings were landed by task 3 and their warnings by task 4.
- **~15 were closed by tasks 1–15 of this checkpoint** and are marked so, each with the sentence
  that closed it quoted.
- **The rest are records rather than defects** — the two `git_provenance` environment facts, the
  by-design survival of artifacts under `status: failed`, the whole-branch review summaries, and
  the decisions record.

Open at close: **23 entries**, each routed. The largest classes are the `-UNSUPPORTED` families,
which retire with their own features (H2 Sweeps: five; H3 Units: eight; H4 Statistics: two), and
the hardening debts on hashes (H6), `validate`'s type envelope (H1), and `repeat_spread` (H4). Two
entries carry priority beyond "documented": `finalize`'s `unit`-column shadow (H5), a live
corruption path in a shipped artifact from a config that validates clean, and `repeat_spread`'s
`{std: 0.0, n: 1}` for a declared single-repeat level (H4), judged a probable code defect with a
`reference.md` sentence that must change with it.

**The 23, by primary owner. Each entry is counted exactly once, and the column sums to 23.**

| Owner | × | Entries |
|---|---|---|
| **H1** | 3 | `validate`'s scalar-leaf type envelope · the S4c-task-9 entry (`compare`'s grammar; its `resolve_contrasts` half is H9) · the validate-time `E-` registry |
| **H2** | 3 | The four sweep modes · `E-SWEEP-BASELINE-PARTIAL` · S1's original sweep-family entry |
| **H3** | 1 | The seven `E-DATA-*-UNSUPPORTED` (+ `E-REPL-FOLD-STRATIFY-`) |
| **H4** | 6 | `init` and the optional `statistics` sub-blocks · the two declined `repeat_spread` figures · `E-STATS-RESAMPLE-`/`NULLTEST-UNSUPPORTED` · the `W-STATS-CORRECTION-INAPPLICABLE` refinement · the S4c residue table · `repeat_spread`'s `std: 0.0` |
| **H5** | 4 | `units.parquet` type unification · the S4a residue table (non-numeric columns, `np.str_`) · the S4d residue table (the unpinned stratum gate; its two other rows are H4) · `finalize`'s `unit` shadow |
| **H6** | 4 | `code_hash`'s `.gitignore` awareness · `code_hash` over zero files (its diagnostic half is H1) · `parameters_hash` normalization · the six unwritten `run.yaml` keys (its allocation half is H3, its upstream half H8) |
| **H7** | 1 | The unexported importable-surface names (`BaseReport` is shared with H8) |
| **H9** | 1 | The missing-`uv.lock` decision |
| | **23** | |

**Five entries name a second owner**, and each is counted only at its primary above: `code_hash`
over zero files (H6 → H1), the S4c-task-9 entry (H1 → H9), the S4d residue table (H5 → H4), the
importable surface (H7 → H8), and the six unwritten `run.yaml` keys (H6 → H3, H8). A slice picking
up an entry should read the whole entry rather than this table, which is a census and not a work
plan.

The routing target is `docs/superpowers/specs/2026-08-08-implementation-spine-design.md`
§ The hardening slices, amended by task 16 to define H1–H9. Before that amendment the spine defined
S1–S5 and then one prose sentence, so **no entry could have named a slice even in principle** —
which is why three deferrals named an owner by description instead, and why none of the three was
ever honoured.

## S5 checkpoint decisions record

Nine decisions gating the transcription tasks of
`docs/superpowers/plans/2026-08-11-s5-checkpoint.md`. `design-principles.md` is the tiebreaker.
Decisions 2 and 3 were settled by the user on 2026-08-11.

| # | Decision | Ruling | Grounds | Transcribed by |
|---|---|---|---|---|
| 1 | Where the 13 unnamed `W-` codes live | § Validation gains a diagnostics table, shaped like § Errors core raises' | A warning is a diagnostic carrying an identifier a user greps. A separate registry file has no precedent in the four documents, and § Exit codes and diagnostics already promises that a command prints the identifier beside the message — the table it points at must exist | Task 4 |
| 2 | `E-UNIT-IMMUTABLE` | Implement the coded refusal | **Settled by the user.** A documented identifier nothing raises is the class this repo says must not exist | Task 12 |
| 3 | "the complete parameter set" | Narrow the phrase | **Settled by the user.** The code route changes what `init` writes, which is `parameter_spec`-driven — the single-source-of-truth invariant. Three of the four missing `statistics` blocks are still refused features | Task 6 |
| 4 | `supported: null` | § Pre-registration states three verdict states and both routes to the third | A `false` there is indistinguishable from a claim tested and failed — the same confusion `verdict_evaluated_on` exists to prevent one level up. The two routes are an observation core cannot resolve, and a bound test against an absent interval | Task 8 |
| 5 | Unbuilt names in § The importable surface | Keep them, marked unbuilt | The table is the enumerated normative surface, and `reference.md` calls it "the promise". Deleting the four `register_*` rows would delete the plugin contract four hardening slices build against | Task 5 |
| 6 | Reserved metric names | § Steps and artifacts states the reserved set, currently `{by}` | `statistics.report_by` spends `by` as a column name. A user learns this today only by collision, and § Steps and artifacts is where the flat-mapping return contract already lives | Task 6 |
| 7 | A `run`- or `condition`-scoped step's return | State that it is not recorded | A wide scope has no unit and no repeat to key a value by, so there is nowhere for it to land. Inventing a `results` block would add a record with no denominator — the failure mode the "per-request measurements in a side report" trap already names | Task 6 |
| 8 | `Config.raw` | § The importable surface states that the root node carries one accessor and nested nodes carry none | A top-level config key named `raw` is shadowed today. That is a real narrowing of "dot-access with no methods at all", and an invariant with an undocumented exception is worse than one with a documented one | Task 5 |
| 9 | Finding order | Amend the sentence, not the code | § Exit codes promises config-position order; `validate` collects by check. Ordering by document position needs position tracking threaded through every check — a hardening change with its own tests, not a checkpoint one | Task 6 |

## `limits.max_ineligible_fraction`/`min_reported_n`'s runtime `bool`-exclusion guards are now unreachable from any config

Found by the H1 Validation slice's task 2 (wiring `check_envelope` into `validate`), while
resolving a suite regression it caused.

`cli.py`'s `command_run` carries two inline runtime guards over `limits` fields, each written
`isinstance(x, (int, float)) and not isinstance(x, bool) and ...`: one before `W-DATA-INELIGIBLE`
(around the `max_ineligible`/`counts["ineligible"]` comparison), one before `W-STATS-STRATUM-THIN`
(around `stratum_floor`/`completed`). Both exist so a non-numeric or `bool` value in `limits`
(`"half"`, `true`, `false`) is silently skipped rather than misread — `False == 0` is the
discriminating case: without the `bool` exclusion, `max_ineligible_fraction: false` would be read
as a real `0.0` threshold and warn the moment any unit is ineligible at all.

Task 2 wired `LEAF_TYPES` (task 1's table) into `_check_shape`, and `LEAF_TYPES` types both fields
numeric (`int`/`float`) and — by the same reasoning as the runtime guards, stated in `envelope.py`'s
own docstring ("a budget of `true` is not a budget") — `_is_type` excludes `bool` from every numeric
leaf. So a config carrying `"half"`, `true`, or `false` in either field is now refused at *validate*
time with `E-CONFIG-TYPE`, before `command_run` reaches either runtime guard at all. Four
`test_cli.py` tests drove exactly these values through a full `run_a_project(...)` and asserted the
corresponding warning did not appear; each now gets `EXIT_WRONG` instead of a completed run, so
task 2 reframed them (as `test_a_string_ineligible_limit_is_refused_at_validate_time` and its three
siblings) to assert the new refusal, preserving each original docstring's reasoning about the
runtime guard as historical/defence-in-depth documentation rather than deleting it.

**Not fixed here, because there is nothing to fix in `validate.py` or the tests — the runtime
guards themselves are the open question.** They are inline in `command_run`, reading loop-local
state (`results`, `roster`, `fold_members`, `counts`, `cond`, `step_name`) with no seam that makes
either guard callable in isolation without extracting it into a standalone function first — the
task 2 report confirmed this by inspection rather than assuming it. Two options, neither taken by
task 2 because both are a design decision for the owning slice, not a wiring task:

1. **Extract each guard's comparison into a small testable function** (e.g. `_ineligible_exceeds
   (max_ineligible, resolved, ineligible) -> bool`), give it direct unit coverage for the `bool`/
   `str` cases the four `test_cli.py` tests used to cover through a full run, and keep it called
   from `command_run` as today — the guard stays, now provably alive by a test that does not go
   through `validate` at all.
2. **Retire the two runtime guards outright**, on the grounds that every value they defend against
   is now refused by `check_envelope` before `command_run` can be reached with one — the guards
   would be a well-covered generic-Python bug class than a design intent — leave the comparisons
   as plain numeric comparisons and record that `E-CONFIG-TYPE` is the sole defence.

Either way, the reasoning `test_a_false_ineligible_limit_is_refused_at_validate_time`'s docstring
carries (`False == 0`, so the exclusion is the only thing standing between a `false` reading and a
real `0.0` threshold) must survive into whichever form wins — task 2 kept it in the reframed test's
docstring rather than let it disappear with the test that used to prove it end to end.

**Owner: H1 Validation** (spine § The hardening slices) — it is the slice that built the type
envelope causing this, and the one positioned to decide whether defence-in-depth earns its own
test or is retired.

## Nine undocumented run-time and creation-command `E-` codes

Found by task 7's reviews while landing the validate-time `E-` registry (see "Validate-time `E-`
identifiers have no registry" above): comparing every raised `E-` identifier against the four
documents turned up nine that appear in none of them, and that are misclassified as
validate-time debt in that entry's original code list — corrected there, recorded here as their
own finding because they are a different kind of gap with a different owner.

Each is raised outside `validate.py`, on the `run`/`reproduce` execution path or from a creation
command, never caught and translated into a collected finding the way the `E-REPL-*`
declaration-shape family is:

| Code | Raised by | Surface |
|---|---|---|
| `E-GIT-NO-REPO` | `provenance.find_repo_root` | no git repository found walking up from the given path |
| `E-GIT-NO-COMMIT` | `provenance.git_provenance` | a repo with no commits yet |
| `E-CODE-DIRTY` | `cli.command_run`'s phase-2 gate | uncommitted changes under `src/**`/`templates/**` |
| `E-INPUT-CHANGED` | `cli.command_run` / `verify_manifest` | the input manifest changed since it was recorded |
| `E-RUN-LOCKED` | `run_identity` | a run directory another process holds the lock on |
| `E-RUN-ID-EXHAUSTED` | `run_identity` | all 26 suffixes for one commit+day already taken |
| `E-PROJECT-EXISTS` | `generators.scaffold_project` | `new`'s target directory already exists and is non-empty |
| `E-EXPERIMENT-EXISTS` | `generators.generate_experiment` | `src/<pkg>/` already exists |
| `E-EXPERIMENT-UNKNOWN` | `generators.step.generate_step` | `generate step` named a package with no `src/<pkg>/` to add a step into |

These were originally proposed for `reference.md` § Errors core raises by three ledger entries
above ("New error identifiers: `E-STEP-EXISTS`, `E-EXPERIMENT-EXISTS`, `E-PROJECT-EXISTS`" among
them) — correctly targeted, since every one is genuinely raised rather than collected, unlike the
entries this task-8 pass closed. Those entries are left alone rather than amended: the proposal
was landable, it simply never landed. `E-STEP-EXISTS` is the one sibling that is documented, and
only partially — it has a sentence in § Exit codes and diagnostics but no row in § Errors core
raises' table either.

**Not H1's business — H1 owns the validate-time registry, and none of these nine is validate-time.**

**No current slice's charter covers this, and forcing a fit is the wrong move.** H6's charter,
verbatim from the spine (§ The hardening slices), is "`code_hash`'s `.gitignore` awareness and its
zero-file case, `parameters_hash` normalization against `parameter_spec`, and the purity rule that
forced both" — hashes and hash purity, nothing about git state, run locking, or a creation
command's own target. Checked against all nine individually: `E-GIT-NO-REPO`/`E-GIT-NO-COMMIT` are
arguably provenance and could be argued into H6 on that word alone, but `E-PROJECT-EXISTS`
(`scaffold.py`), `E-EXPERIMENT-EXISTS`/`E-EXPERIMENT-UNKNOWN` (`generators/`),
`E-RUN-LOCKED`/`E-RUN-ID-EXHAUSTED` (`run_identity.py`), and `E-INPUT-CHANGED`/`E-CODE-DIRTY`
(the manifest path and the run gate, both in `cli.py`) are not hashes, not provenance-purity
questions, and appear in no other H1–H9 charter either. Routing them to H6 anyway would mean
whoever plans H6 inherits seven codes their charter never mentions — the same "description
standing in for a slice" failure the S5 checkpoint already closed once (§ The hardening slices'
own amendment: "the ledger's deferrals fell back on descriptions of a slice... and none was
honoured").

**Recommendation, not a decision this task is entitled to make:** the spine's own amendment gives
the rule for exactly this situation — "a residual that fits none of these is an argument for
amending this table, not for inventing a tenth name in the ledger." These nine codes are one
coherent unit of work (documenting the `run`/`reproduce`/creation-command surface in § Errors core
raises, the raise-time registry that already exists and already has a documented shape), and no
current slice owns it. Two ways to close the gap, either amending the spine rather than this
ledger:

1. **Widen H6's charter** from "Hashes and provenance" to something that also names run identity
   and the creation commands — the argument for this is that `E-GIT-NO-REPO`/`E-GIT-NO-COMMIT`
   already sit at that boundary, and a run's provenance record is incomplete without knowing why a
   run refused to start.
2. **Add a tenth slice** scoped to "the raise-time registry's remaining gaps" — the argument for
   this is that git-dirty/run-locking/creation-command refusals are a colder, `run`-adjacent
   surface than hash purity, and conflating them with H6 risks the same "one slice, unrelated
   charter items" shape H6 itself does not currently have.

This entry does not pick between them; that decision is the spine owner's, made with the argument
above in hand, not silently defaulted by a documentation task.

## `E-NAME-DIR` is silently skipped when `validate` is run from inside the config's own directory

Found while auditing the validate-time registry (H1's tasks 5–7) for what documenting `validate`'s
checks against `src/` would expose that a purely textual pass would not.

`validate._check_metadata` gates the check on `directory = config_path.parent.name` being
non-empty: `if name and directory and name != directory: c.error("E-NAME-DIR", ...)`. Neither
`command_validate` nor `main()` resolves `config_path` to an absolute path before this runs, and
`cli.py` passes through whatever string the shell handed it. `publishable validate config.yaml`,
run with the current working directory already inside the config's own directory (the ordinary
way to invoke it once you `cd` there), gives `config_path.parent == Path(".")`, whose `.name` is
`""`. `directory` is falsy, the whole check is skipped, and a config whose `metadata.name` genuinely
disagrees with its directory validates clean. `publishable validate configs/foo/config.yaml`, run
from one level up, does not have this problem — `parent.name` is `"foo"` — so the bug is specific
to the relative, no-directory-component invocation, not to relative paths in general.

This is a code defect, not a documentation one: § Validation's own row for the check ("Name matches
directory") states the rule the code already intends, and the registry entry `validate.py` earns
for `E-NAME-DIR` is accurate about *what* the check does, not about *when* it fires. Fixing it means
resolving `config_path` (or comparing against `config_path.resolve().parent.name`) before the
comparison, which changes behavior rather than prose — out of scope for a documentation-registry
task to do in passing.

**Owner: H1 Validation** (spine § The hardening slices) — the slice that found this is the same
slice that owns it, and it is routed forward deliberately rather than fixed here: a documentation-
registry task closing a code defect in passing is exactly the "fixed opportunistically, unreviewed"
shape this project avoids elsewhere, and fixing `_check_metadata`'s resolution is a behavior change
with its own test, not a registry edit. A reader should not have to wonder why the slice that found
this did not also close it — it owns "the full ~85-check engine," and this is exactly the
well-formedness question that engine exists to make reliable regardless of the
directory a command is run from.

## New warning identifier: `W-SWEEP-BASELINE-CONFOUNDED`, and `W-STATS-CONTRAST-THIN` gains a validate-time half

H1 task 10, the two rows of `reference.md` § Validation that state a check nothing performed and
that were buildable against today's schema rather than against a block still refused wholesale.

**`W-SWEEP-BASELINE-CONFOUNDED` is new.** Row 271 ("Baseline leaves contrasts confounded") named
no identifier; `W-SWEEP-`, `W-BASELINE-` and `-CONFOUNDED` were grepped across the four documents,
`src/`, `tests/` and `docs/superpowers/` before minting, and § Warnings core reports — the complete
set built by S5 — carries its row. `cli.py` computes `confounded`/`differs_on` per comparison at
run time from `_differing_axes`; nothing said so from the declaration, which is all the fact needs.

Two things the new row has to disclose, and does:

- **The check is narrower than run time, deliberately.** It compares `sweep.grid`'s axes only, and
  only when `sweep.baseline` fixes every one of them. `cli._differing_axes` walks the *union* of
  both sides' keys against a `_MISSING` sentinel, so a baseline fixing an axis the grid never
  sweeps adds a differing axis to every comparison and can mark `confounded` where this warning
  stays silent (`tests/test_cli.py::test_a_two_axis_contrast_is_marked_confounded`'s sibling at
  `analysis.confidence` is exactly that shape). Under-warning is the safe direction — the warning
  never fires where a run would not mark the comparison — and it is why the check reimplements
  three lines rather than importing `cli._differing_axes`, which would drag the wider semantics
  along with it into a module `cli` already imports.
- ~~**The row's own remedy is a config core currently refuses.**~~ **CLOSED 2026-08-12 (H2 Sweep
  expansion modes, task 7).** Row 271 ends "leaving one axis unfixed gives a baseline per cell
  instead", and `_check_unimplemented` refused exactly that with `E-SWEEP-BASELINE-PARTIAL` until
  per-cell baseline expansion landed — so a ≥2-axis grid with a baseline could be warned about but
  not fixed. Task 6 landed the expansion and task 7 retired the refusal, so the remedy is now a
  config core accepts, verified end to end by
  `test_a_baseline_that_leaves_a_grid_axis_free_validates_and_expands`. Three things followed, and
  all three are done rather than one of them: the § Warnings core reports row no longer names the
  refusal (it now says a free axis is the remedy, not the fault); the emit-site comment no longer
  justifies the check's narrowness with "the only baseline-plus-grid shape this build admits at
  all", which had gone false, and gives the surviving reason instead — a half-fixed baseline is the
  shape where nothing is confounded by construction; and **the warning's message now offers the
  remedy**, which it deliberately did not while following the advice met an error. The warning
  itself is unchanged in when it fires — the `all(axis in baseline)` guard, the >1 differing-axis
  threshold, and `tests/test_validate.py`'s four assertions on it are all as they were.

**`W-STATS-CONTRAST-THIN` is reused, not split.** Row 276 ("Contrast stratum is populated") is the
second half of the blur this file already recorded under `W-STATS-STRATUM-THIN`: § Validation lists
the check as validate-time and `cli.py` performed it at run time over `n_paired`. `validate` now
counts roster units matching the `within` stratum, under the same identifier.

**The one-identifier choice stands; the reason first given for it does not, and has been withdrawn
rather than replaced.** The amended § Warnings core reports row originally justified the single code
as "one condition observed twice; the roster count bounds the realized one from above". That
sentence is true of this pair — `cli.py` computes `n_paired` as `paired_keys(of, against, allowed)`
with `allowed = units_matching(roster, comp.within)` over the same full roster, and `units_matching`
reads `Unit.attributes` off the frozen roster rather than any recorded column, so no `.train`,
holdout, or fold subsetting breaks the bound. But it is **equally** true of
`W-STATS-REPORTBY-THIN`/`W-STATS-STRATUM-THIN`, whose validate half counts roster units per level and
whose run half counts *completed* units per level — and that pair is **split into two identifiers**,
with `W-STATS-STRATUM-THIN`'s own row in the same table drawing the opposite conclusion from the
identical premise ("the attrition between the roster `validate` saw and what a run completes is
exactly what this catches beyond `W-STATS-REPORTBY-THIN`"). A reader taking the withdrawn sentence
seriously would conclude the `report_by` pair ought to be merged. Since the bound is identical in
both cases, no honest discriminator was available, so the row now states only that the code fires at
two observation points and leaves why-one-identifier unargued.

**The open question this leaves, named rather than hidden:** the table now contains one thinness
condition observed at two points under one code and another under two, with no stated rule for which
shape a third should take. Deciding that rule is a documentation question about the whole `W-…-THIN`
family, not about either check's behaviour, and neither this task nor the `report_by` slice that
minted the split had the standing to settle it. **Owner: whichever slice next touches the
`limits.min_reported_n` family.**

The one behavioural subtlety, pinned by
`test_an_unknown_within_attribute_is_refused_without_also_being_called_thin`: the thinness count is
skipped for a `within` naming an attribute `E-STATS-CONTRAST-WITHIN` just refused. An undeclared
attribute matches no unit, so counting it would publish `0 of 12 units` beside the typo diagnosis
and send the reader looking for missing units. `_check_report_by` skips a refused entry the same
way.

**Not fixed here, and not a defect:** `reference.md` § Validation's rows still name no identifiers
for either check, which is the file's convention for that table — § Warnings core reports is where
a `W-` code is looked up, and both rows resolve there now.

**Two minors recorded here rather than fixed, per the task review:**

1. **The under-warning gap has an owner.** A `sweep.baseline` fixing an axis the grid never sweeps
   passes `validate` silently and is written `confounded: true` into `run.yaml`, because
   `cli._differing_axes` walks the union of both sides' keys against a `_MISSING` sentinel while the
   validate check compares the declared grid axes only
   (`tests/test_cli.py::test_a_baseline_only_axis_still_counts_toward_confounded` is that shape and
   passes unchanged). Closing it means deciding whether a baseline-only axis is part of the design
   the warning describes — a baseline-semantics question. **Owner: H2 Sweeps**, alongside per-cell
   baseline expansion, which is the same block of work.
2. **The message-text assertion in
   `test_a_baseline_fixing_every_axis_of_a_crossed_grid_warns_before_the_run` is deliberate.** This
   project pins identifiers and not wording, so an assertion on `"2 of 4 baseline comparisons"` would
   normally be over-specification. It is kept because it is what kills the always-warn mutant: with
   the threshold dropped the code still fires, the count silently becomes `4 of 4`, and every
   presence-only assertion still passes. A future edit to the message should update this assertion,
   not delete it.

---

## Task 11 (H1 Validation hardening): three of the seven partials routed, plus two gaps found alongside

Rows are `docs/reference.md` § Validation line numbers as of this task. Each is recorded below with
the slice that owns it, taken from
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md` § H1–H9.

Of the seven, four rows are closed — 205 and 208 by tasks 1–4's `check_envelope`, verified rather
than assumed and not edited here; 225 and 244 by this task — plus the second half of 212. The three
that are not are the first three sections below. **The last two sections are not among the seven at
all**: they are gaps this task measured while closing the others, filed here because a per-task
report is not a ledger a later slice reads.

### Row 211 "Template is installed" — **Owner: H7 Plugins and the apparatus**

The row is `experiment_type` names `llm_diagnostic`, which no installed plugin registers — `plugin`
says it should come from `someuser/publishable-llm`. `validate_config` reports `E-TEMPLATE-UNKNOWN`
and lists the known template names, but not the `plugin` field's hint. The hint is only useful once
an unresolvable `experiment_type` can name a template some *uninstalled* distribution registers,
which is the entry-point resolution H7 owns; with `generic` the only installed template, the hint
would name a distribution core has no way to check. No code change made.

**AMENDED 2026-08-15 (spec-defects staleness audit at `5578988`): locator corrected; finding and
owner unchanged.** H7a renamed the § Validation row this section names. It is **"Template resolves"**,
not "Template is installed" — grep for the new name, not the old one. (The line number `211` is the
one task 11 measured and is not re-measured here; the row is located by its name.) The finding
survives intact: `validate_config` still reports `E-TEMPLATE-UNKNOWN` through
`unknown_template_message(name, known)` and still prints no `plugin` hint. So does the reasoning,
with one term corrected — H7a made a project-local `templates/*.py` resolvable, so `generic` is no
longer the only *resolvable* template, but it is still the only *installed* one, and an uninstalled
distribution is precisely what core still has no way to check. Two load-time refusals joined the same
surface (`E-TEMPLATE-LOAD`, `E-TEMPLATE-COLLISION`), reported under the code the raise carries;
neither bears on this row. **Owner stays H7 — specifically H7b**, which owns entry-point resolution.

**STRUCK 2026-08-16 (H7b Part A task 11).** `unknown_template_message` takes the config's `plugin`
field and renders it, so `validate`'s finding names where the template was expected to come from.
The row's stated precondition — that an unresolvable `experiment_type` can name a template some
uninstalled distribution registers — is satisfied by task 7's metadata scan and task 8's merge.
`generate experiment` passes `None` and shows no hint, deliberately: it is writing the file that
would hold the field.

### Row 212 "Template version moved", first half — **Owner: H7 Plugins and the apparatus**

`_check_versions` compares the declared `template_version` against the module constant
`materialize.TEMPLATE_VERSION`, not against the installed template's own reported version. Closing
it means `BaseTemplate` declaring a `version` attribute, which § Templates' class-attribute example
does not list — a four-document change — and which is behaviourally inert while `generic` is the
only installed template and `materialize` is the only writer of the field. It becomes observable
when a plugin ships a template with a version of its own, which is H7's work.

The row's *second* half — "`request.timeout` is new and unset (warning)" — was implemented here
instead: it is computable from `parameter_spec` alone, needs no new identifier, and is named inside
`W-TEMPLATE-VERSION`'s existing message gated on the version mismatch.

**AMENDED 2026-08-15 (spec-defects staleness audit at `5578988`): the justification is stale; the
finding, the row name and the owner are not.** "Behaviourally inert while `generic` is the only
installed template" no longer carries the point by itself, because H7a made a second kind of template
resolvable. Inertness now rests on a composed reason: `generic` is still the only *installed*
template and `materialize` still the only writer of the field, **and** H7a ruled that a project-local
template writes **no `template_version` at all** and is never version-checked — `materialize.py`
omits the line for a local template, and `_check_versions` skips the comparison whatever a local
config declares, which `reference.md` § Validation and § Three hashes both state. The gap itself is
untouched: `_check_versions` still compares against the module constant `materialize.TEMPLATE_VERSION`
rather than an installed template's own reported version, and still becomes observable only when a
plugin ships a template carrying one. **Owner stays H7 — specifically H7b.** Unlike its sibling, this
row was *not* renamed: it is still "Template version moved".

**AMENDED 2026-08-16 (H7b Part A task 10): the comparison is fixed; the reachability is not.**
`BaseTemplate.version` now exists, `GenericTemplate` reports it, `_check_versions` compares a
config's `template_version` against `type(template).version`, and `materialize` writes what the
template reports. The false guarantee this row named — a warning saying "the installed template
reports" while comparing against core's own module constant — is gone.

What remains, and it is why this row is amended rather than struck: **no installed template's class
is ever held in this build**, so the comparison still only ever runs against core's own template and
a project-local one is still skipped. `Claim.cls` is `None` for an installed claim by decision 3 of
`2026-08-16-plugin-registries-design.md`. This row's own words — "It becomes observable when a
plugin ships a template with a version of its own" — are still the condition, and it is now filed
separately as `## OPEN — an installed template's name resolves but its class is never loaded`,
**owner unassigned**. Strike this row when that one is closed, not before.

### Row 284 "Correction can be applied" — **Owner: H4 Statistics**

`_check_sweep` raises `W-STATS-CORRECTION-INAPPLICABLE` whenever `statistics.correction` is
`fdr_bh` and the family holds at least one comparison. The row's condition is a three-way
disjunction — `statistics.null_test` is undeclared, **or** its `shuffle` reaches none of the
family's members, **or** a parameter-axis contrast accounts for every member. The check tests none
of them. It is correct by accident today, because `_check_unimplemented` refuses any declared
`statistics.null_test` outright (`E-STATS-NULLTEST-UNSUPPORTED`), so no config that validates can
carry one.

Not narrowed here. Gating on `statistics.get("null_test")` implements one disjunct and leaves the
other two unevaluated, and the only configs that gate could affect are ones that already fail — so
the narrowing would be unobservable in any config that validates while looking, to a later reader,
like the condition had been implemented.

One consequence, found while routing this row and **fixed in the review-fix round of the same
task**: when a config *does* declare `statistics.null_test` alongside `fdr_bh`, the error and the
warning are both reported, because `validate` collects rather than stopping — and the warning's
message used to assert "(`statistics.null_test` is undeclared, and a parameter-axis contrast cannot
supply one)", which is false of that config. That parenthetical no longer exists in the codebase; do
not grep for it. The message now says no comparison in this family can carry a p-value *in this
build*, which is true of every config that reaches the line, and
`test_the_inapplicable_correction_warning_asserts_nothing_about_null_test` pins it.

**AMENDED 2026-08-11 (task 11, review-fix round): the message is corrected; the condition is still
H4's.** The first draft of this entry said the wording was left alone deliberately, on the reasoning
that editing it would narrow the check in the message rather than in the condition. That reasoning
was reversed under review and the earlier sentence does not stand: removing a false assertion is
independent of whether the disjunction is complete. What is unchanged, and what this row is still
routed to H4 for, is the *condition* — `if comparisons > 0 and correction == "fdr_bh"` tests none of
the row's three disjuncts and is narrowed by whichever slice implements `null_test`.

### Not one of the seven, but measured while closing 225: `seeds` is declared and read by nothing — **Owner: H1 Validation**

`reference.md` § Repeat kinds gives a `seed` level two ways to say what it repeats over: "`n` (how
many), or `seeds: [17, 42, …]` for specific values". Only the first is implemented.
`_seed_members(digest, kind, n)` derives every seed from `digest|kind`, so `seeds` is never read,
under either shape it can take:

- `{kind: seed, n: 2, seeds: [17, 42]}` resolves two repeats and runs two digest-derived seeds — not
  17 and 42. The author asked for specific values and silently got other ones, which is worse than
  an ignored field: the run *looks* like it honored the declaration, and `run.yaml` records the
  seeds it actually used with nothing saying they were not the declared ones.
- `{kind: seed, seeds: [17, 42]}` with no `n` resolves to `int(level.get("n", 1))` — **one** repeat.
  Two declared repeats become one, silently, and the execution-count arithmetic
  (`_repeat_total`, `W-EXEC-BUDGET`, `dry-run`) agrees with the wrong number.

This is a larger silent divergence than row 225, which this task did fix, and it is why
`tests/test_replication.py::test_the_key_closure_does_not_reach_a_seed_level` asserts only a
negative (if a refusal is raised, its code is not `E-REPL-LEVEL-FIELD`) rather than pinning
successful resolution — the test must not entrench the acceptance.

Two routes, and the choice between them is the decision this entry hands over. Either `seeds` is
*refused* until it is implemented, as `fold.stratify_by` already is
(`E-REPL-FOLD-STRATIFY-UNSUPPORTED`) and as the whole `E-SWEEP-*-UNSUPPORTED` family is — which is a
validate-time refusal for an unimplemented declaration, and so **H1 Validation's**, the slice this
task belongs to; or `_seed_members` honors it, which the H1–H9 table assigns to no slice at all,
`replication.py` appearing there only as "the `seed` kind: *n* repeats, resolved seeds, repeat
labels". **That absence is itself part of what is being recorded here.** The refusal is the smaller
and the safer of the two, and it is the one that stops a config from running seeds nobody asked for.

### The closed-schema walk does not reach a leaf's own keys — **Owner: H4 Statistics for two of the three blocks; H1 Validation for `hypotheses`**

Recorded as a gap, not as row 208 reopened. Row 208's stated example is a key under `parameters`,
which `E-PARAM-UNKNOWN` closes, and the boundary is stated deliberately in `_check_unknown_keys`'s
own docstring in `envelope.py` — verbatim: "never descending into a known LEAF's value — a leaf's
own children (`data.units.holdout`'s `method`, a `from` dict's `resolver`) have no fixed dotted path
a table entry could name, so they are `_check_shape`'s job". So it is a stated limit rather than a
silent one, and tasks 1–4 were right not to cross it.

What is genuinely absent is *per-entry* key closure for the three blocks whose entries are mappings
with a fixed key vocabulary of their own — `hypotheses`, `statistics.contrasts`, and
`statistics.report_by`. `_check_unknown_keys` returns at `path in _KNOWN_LEAVES`, and the three
per-block checks (`_check_hypotheses`, `_check_contrasts`, `_check_report_by`) each read the keys
they know and ignore the rest. A `hypotheses` entry writing `evaluate_onn` for `evaluate_on` is
therefore reported by neither: the entry validates clean and the pre-registration it declares is
evaluated under the default the misspelled key failed to change. `statistics.contrasts` has the same
shape (`of`, `against`, `within`, `id`), and so does a `report_by` entry once it is anything but a
string.

Each of the three vocabularies belongs to the slice that owns its block —
**H4 Statistics** for `statistics.contrasts` and `statistics.report_by`, whose key sets are still
growing there; **H1 Validation** for `hypotheses`, whose vocabulary is settled and whose checks
already live in `_check_hypotheses`. A fourth option worth weighing first: a small shared closure
helper in `envelope.py` taking a path and an allowed key set, so the three do not grow three
difflib hints.

## CONFIRMED CLOSED (H1 Validation, task 12): the `BaseException` residual on `E-ENTRYPOINT-IMPORT`

Task 12's step 1 re-examined the residual recorded in the AMENDED 2026-08-11 note on
§ `SystemExit` at module scope escapes `validate`'s broad catch, and the judgement holds.
`validate.py` catches `SystemExit` and then `Exception`; a user package raising a *bare*
`BaseException` subclass at module scope still escapes both.

The reachability question was re-asked rather than re-asserted. The only `BaseException`
subclasses outside `Exception` are `SystemExit` (already caught), `KeyboardInterrupt` and
`GeneratorExit`. No stdlib type raises `KeyboardInterrupt` or `GeneratorExit` at import — the
first arrives from the tty and must terminate `validate`, which is precisely why catching it
would be a regression, and the second is only ever raised into a generator being closed. A
user-defined `class Abort(BaseException)` raised at module scope is reachable in principle, but
it is a deliberate act by the author of the very package `validate` is importing, and it is
indistinguishable from that author choosing to make their module unimportable. No reachable
case was found. **Closed. Nothing owes this entry.**

## CONFIRMED (H1 Validation, task 12): per-entry key closure gap re-verified, not re-opened

The gap recorded above under § The closed-schema walk does not reach a leaf's own keys was
re-verified during task 12's cross-document pass and is unchanged: `hypotheses` and
`statistics.contrasts` are both `LEAF_TYPES` entries, so `_check_unknown_keys` returns at
`path in _KNOWN_LEAVES` and never descends, and no per-entry key vocabulary is enforced by
`_check_hypotheses` or `_check_contrasts` (`grep -n 'unknown\|_KEYS\|allowed' src/publishable/validate.py`
matched nothing scoped to either). Recorded here because `reference.md` line 292's claim — "the
schema is closed and `validate` checks every key against it ... any key not in the spec is a typo
by construction" — is *overclaimed for these two blocks specifically*, and unlike the other
leaf-internal cases they are not shielded by an `-UNSUPPORTED` refusal: both are implemented and
reachable today. Ownership stays as already assigned (H4 for `statistics.contrasts`, H1 for
`hypotheses`). Task 12 changed no code and no prose for this — the honest fix is the closure,
not a softening of line 292.

### AMENDED 2026-08-11 (task 12, second follow-up): the gap is **four** blocks, not two — and one has no owner

The entry above, and the first task-12 confirmation, both named only `hypotheses` and
`statistics.contrasts`. A full enumeration over **every** `LEAF_TYPES` entry declared `list` or
`dict` — 18 of them, each probed with a *control* config and a *probe* config differing only by an
injected unknown key, so an incidental finding could not be mistaken for closure — found two more:

| Whole-leaf block | Unknown key inside it | Verdict |
|---|---|---|
| `hypotheses` entry | `evaluate_onn` | **silent** |
| `statistics.contrasts` entry | `withn` | **silent** |
| `replication.repeats` entry, kind `seed` | `bogus`, and a typo'd `nn` | **silent** |
| `replication.repeats` entry, kind `fold` | `bogus` beside a valid `k` | **silent** |
| `replication.repeats` entry, kind `batch` | `bogus` | closed — `E-REPL-LEVEL-FIELD` |
| `data.units.from`, mapping form | extra key beside a valid `glob` | **silent** (see below) |
| `data.units.attributes`, `statistics.report_by` | — | closed; entries are strings |
| `sweep.baseline`, `sweep.grid` | — | closed; dynamic keys are parameter paths (`E-SWEEP-PATH-UNKNOWN`) |
| `measurements`, `holdout`, `assign`, `resample`, `null_test`, `sweep.groups`/`paired`/`ablate`/`sample` | — | unreachable; refused by the `-UNSUPPORTED` family |

Two distinctions the enumeration forced, and which the narrowed sentence in `reference.md`
§ Validation now reflects:

- **`batch` is closed and `seed`/`fold` are not, deliberately.** `_check_batch_keys`
  (`replication.py:151`) closes `batch` against `_BATCH_KEYS`; the same closure over `seed` or
  `fold` would refuse declarations the document allows, since `seed` takes `seeds` and `fold`
  takes `stratify_by`. So the exception is `replication.repeats` entries **of kind `seed` or
  `fold`**, never the block as a whole — naming the block would be a fresh over-claim in the
  opposite direction.
- **`data.units.from` is a lesser case, but still a case.** A typo of the key that matters *is*
  caught — `{gob: "*.csv"}` and `{}` both report `E-UNITS-SOURCE-MISSING`, because the mapping
  must be recognizable as `{glob: …}` — so no silent *behavioural* divergence is possible there.
  What is silently accepted is an **additive** junk key beside a valid `glob`. That still
  falsifies "any key not in the spec is a typo by construction", which is why it is in the clause,
  and it is why the clause says a key not in the spec is *ignored rather than reported* rather
  than saying every such key silently keeps a default.

**Ownership. `replication.repeats` has no owner, and that is the finding here.** `hypotheses`
stays with **H1 Validation** and `statistics.contrasts` with **H4 Statistics**, unchanged.
`data.units.from`'s mapping vocabulary belongs with whichever slice implements `resolver`
(`E-DATA-RESOLVER-UNSUPPORTED`), since that is the second key of the two. The `seed`/`fold`
closure belongs to no slice in the H1–H9 table.

**It does not merge with the `seeds` entry filed earlier in this slice, and they stand
separately.** That entry is about `_seed_members` *ignoring a key the document defines* —
`seeds` is real, specified, and silently unhonoured, and its two routes are "refuse it" or
"implement it". This one is about a key the document defines *nothing* for being silently
accepted. They share a file (`replication.py`) and a symptom (silence) but not a fix: closing the
key vocabulary would *refuse* `seeds`, which is precisely one of the two routes the earlier entry
is still deciding between. **Closing `seed`/`fold` keys must therefore wait on that decision, or
be written to admit `seeds` and `stratify_by` explicitly.** Recorded so the sequencing is not
rediscovered.

Task 12 changed no code for any of this. What it changed is the sentence in `reference.md`
§ Validation, which now names all four cases and is true as written.

**AMENDED 2026-08-15 (spec-defects staleness audit at `5578988`): the enumeration's row for
`measurements` · `holdout` · `assign` · `resample` · `null_test` · `sweep.groups`/`paired`/`ablate`/`sample`
has aged.** Its verdict "unreachable; refused by the `-UNSUPPORTED` family" was true of all nine
blocks on
2026-08-11 and is true of three today. The `-UNSUPPORTED` codes still raised anywhere in `src/` are
`E-DATA-ALLOCATION-UNSUPPORTED`, `E-DATA-HOLDOUT-UNSUPPORTED`, `E-DATA-RESOLVER-UNSUPPORTED`,
`E-REPL-FOLD-STRATIFY-UNSUPPORTED`, `E-SWEEP-GROUPS-UNSUPPORTED` and
`E-STATS-NULLTEST-UNSUPPORTED` — so of that row's blocks only `data.units.holdout`,
`statistics.null_test` and `sweep.groups` are still unreachable behind one.
(`E-STATS-CONTRASTS-UNSUPPORTED` also matches a `src/` grep, but only inside explanatory comments in
`cli.py` and `validate.py`; it is raised nowhere and its retirement stands.) `statistics.resample` is
the one this audit followed through: reachable since H4a **and closed one level in** —
`envelope.LEAF_TYPES` types `statistics.resample.method` / `.n` / `.stratify_by` individually rather
than leaving the block whole, and `envelope.py`'s own comment records that the closure landed
*before* the wholesale refusal retired, so a typo among the three was never briefly unreachable.
`data.units.measurements` was already closed the same way, and `data.units.assign` has
`_check_assign_axis_keys`. **Not verified by this audit:** `sweep.paired`, `sweep.ablate` and
`sweep.sample` became reachable with H2/H3 work and are still typed as whole `dict`s in
`LEAF_TYPES`, so whether an additive junk key inside one is reported rests on each mode's own
checker — named here as an open question rather than answered.

## `sweep.grid` and `sweep.paired` naming the same path is unaddressed by § Expansion modes

§ Expansion modes states the composition rule as "the final condition set is the product of
every axis-shaped mode present" and says nothing about what happens when two axis-shaped modes
write to the *same* dotted path. H2 Task 2 makes this reachable: once `paired` is a real axis
(rather than refused wholesale), a config can declare `grid: {analysis.min_samples: [30, 50]}`
alongside `paired: [{analysis.min_samples: 30, analysis.confidence: 0.95}, {analysis.min_samples:
50, analysis.confidence: 0.99}]`. `expand`'s product loop applies each axis's cell to `values` in
order (`for cell in combo: values.update(cell)`), so whichever axis is later in `_axes`'s list
wins the path outright — `paired` always follows `grid` today, so every resulting condition's
`analysis.min_samples` is `paired`'s value, never `grid`'s. Two of the four combinations then
collapse to byte-identical `values`: `(grid=30, paired={min_samples:30,...})` and `(grid=50,
paired={min_samples:30,...})` both resolve to `min_samples=30`, and its sibling pair resolves to
`min_samples=50` twice. `validate` reported nothing, because no check compared the two modes'
declared paths — `_condition_labels` returns a **set**, so a duplicate label (and the duplicate
condition behind it) was structurally invisible to every check built on it, and the run would
execute the same condition twice while `results.contrasts`' `family_size` counted four
comparisons instead of two.

Proposed resolution: state in § Expansion modes that a path may be written by at most one
axis-shaped mode per run, and refuse a config that violates it.

**AMENDED 2026-08-12 (H2 Task 2, review follow-up): partially closed — refusal added, document not yet updated.**
`validate.py`'s `_check_sweep` now refuses a path named by both `sweep.grid` and `sweep.paired`
under `E-SWEEP-PATH-DUPLICATE`, so the collapsing-conditions case above is refused rather than
silently mis-executed. `docs/reference.md` § Expansion modes and § Validation's error table still
say nothing about this rule — adding the row and the one-sentence composition constraint is left
to whichever task next touches that section (Task 3 or Task 9, since both still have § Expansion
modes open for `sample`/`groups` reasons). Filed here rather than closed outright because the
document half is real work, not bookkeeping: the exact wording needs to state whether the rule
generalizes to any two axis-shaped modes (grid × paired, and — once built — grid × groups,
paired × groups) or is scoped narrower.

## `sweep.paired` entries get none of `grid`'s three per-entry checks

`_check_sweep` (`validate.py`) runs three checks over every `sweep.grid` axis value and — for the
first two — every `sweep.baseline` value too: `_path_resolves` (`E-SWEEP-PATH-UNKNOWN`, the value's
dotted path must be a parameter the template's `parameter_spec` declares), `_value_checks`'s
`spec[path].check(value)` (`E-PARAM-VALUE`, the value must satisfy that `Param`'s own constraint),
and — for `grid` only, since a baseline is never rendered into a label — `check_swept_value`
(`E-SWEEP-VALUE-UNNAMEABLE`, the rendered value must not break the `__` label separator or fail
`SWEPT_VALUE_PATTERN`). H2 Task 2 makes `sweep.paired` a real axis-shaped mode `_axes` composes for
real, but none of the three loops was extended to walk `sweep.paired`'s entries. Concretely, today:

- `paired: [{analysis.min_sample: 30}]` (a typo of `analysis.min_samples`) validates clean, then
  plants the misspelled path verbatim into a condition's config via the same `setdefault` walk
  `_check_sweep`'s own comment names as the reason `sweep.baseline` needed this check
  (`resolve_condition_cfg`) — the run executes with the parameter's default rather than the
  declared override, under a label claiming otherwise.
- `paired: [{"analysis.min_samples": -5}]` (a value failing `Param`'s own `ge=2` constraint)
  validates clean and fails, if at all, wherever the step first reads the parameter — not at
  `validate`, and not with `E-PARAM-VALUE`.
- `paired: [{"analysis.min_samples": {"a": 1}}]` (a value that cannot render into a label —
  confirmed directly: `check_swept_value({"a": 1})` returns a message, `SWEPT_VALUE_PATTERN`
  rejects `str({"a": 1})`) validates clean and produces a condition label no selector
  (`compare.condition`, a contrast's `of`/`against`, a `report` filter) can parse back into axes —
  the exact failure `check_swept_value`'s own docstring exists to prevent, reached through the one
  mode it isn't wired to.

None of these three is a new crash — `_check_shape`'s guards (this same slice) already close every
way a malformed `paired` shape reaches `dict()`/`_keys_for` before a value is ever read; these are
silent semantic gaps in what's read after the shape is confirmed good, the same class `E-SWEEP-
PATH-UNKNOWN`/`E-PARAM-VALUE`/`E-SWEEP-VALUE-UNNAMEABLE` already close for `grid`.

**Ownership.** The H2 charter amendment (`specs/2026-08-08-implementation-spine-design.md`,
"H2 scoping") names exactly six § Validation checks H2 owns beyond `paired`/`ablate`/`sample`/
`groups` existing at all: ablation targets, ablation needs a baseline, ablation doesn't compose
with a parameter axis, the ablation baseline isn't a group level, sample ranges, and axis names
are distinct. Per-entry checking of `paired` values is not among the six, and is not assigned to
any task in `plans/2026-08-12-sweep-expansion-modes.md` either (`grep -n "paired"` on that plan
shows it named only in Task 1's composition table and Task 2, which this entry's own commit
implements). Since `paired` is an **H2 Sweeps** mode, H2 is the natural owner of the gap in its
own charter — recorded here rather than left implicit, so a future H2 task (or a charter revision)
finds it named rather than rediscovering it against a shipped feature with no per-entry
validation. Proposed resolution: extend the two loops already in `_check_sweep` (the one over
`grid.items()`, and the one over `baseline.items()`) with a third, over `sweep.get("paired") or
[]`, calling `_path_resolves`/`_value_checks` (with `nameable=True`, since a `paired` value is
rendered into a label exactly like a `grid` value) per key of each entry.

## `sweep.sample`'s seed derivation is stated two ways, and the two differ on one observable

**Found by:** H2 Sweeps, Task 3 (`sample` expansion), while implementing the seed derivation.
**Severity:** Minor — the two readings agree on every observable except one, named below.

Two passages of `reference.md` describe where a `sample` draw's randomness comes from, and they do
not say the same thing:

- § Expansion modes, in the `sample` block itself: `seed: auto  # derived from the design digest;
  recorded in sweep.yaml`. The digest, and nothing else.
- § What `auto` derives from, in its table: `| sweep.sample draws | digest + n, method, ranges |
  the sample declaration changes |`. The digest **mixed with** `n`, `method` and `ranges`.

Task 3 implements the first: the seed is `sha256(digest|sample|0)`, and `n`/`method`/`ranges` change
the *draws* (they are inputs to the drawing) without changing the *seed*. The table's own
"So it moves when" column — the observable half — therefore still holds for `method` and `ranges`
under either reading, and for `n` under `latin_hypercube`, whose points depend on `n` structurally.

**The one observable difference is `n` under `random` and `sobol`.** Both draw a prefix of one
stream, so raising `n` from 8 to 16 keeps the first eight conditions and appends eight — an
extension, not a redraw. Under the table's "mixes `n`" reading, raising `n` would redraw all
sixteen. Extension is the behaviour the same table explicitly *prefers* one row up, for a `seed`
level's seeds: "*not* when you raise `n`, which extends the list rather than redrawing it". Nothing
states the preference for `sample`, which is the gap.

Proposed resolution: state the rule once. Either narrow the § What `auto` derives from row to
"digest" with a "the draws are also functions of `n`, `method` and `ranges`" note, or state that
`sample` redraws on an `n` change and say why it differs from a `seed` level. Recorded rather than
silently resolved because the two passages are equally normative and the choice has a real
consequence for anyone who raises `n` on a running design.

## CLOSED HERE: `run`/`summary` scope could read a `paired` or `sample` path

**Found by:** H2 Sweeps, Task 3, checking every call site that reads the sweep block.
**Fixed in the same commit** — recorded because it was live on `main` for `paired` between task 2
and task 3, and because it is the shape of gap a *later* mode will reopen.

`command_run` built the set of paths made unreadable at `run`/`summary` scope as
`set(sweep.grid) | set(sweep.baseline)`. `runner.resolve_wide_cfg` plants a `SweptAway` marker at
each, so a `run`- or `summary`-scoped step reading one gets `E-STEP-SWEPT-PARAM` rather than a
value that "could only be wrong for every condition but one" (its own docstring). Neither
`sweep.paired` nor `sweep.sample` was in that set, so once each became a real axis a step at those
scopes silently read the **base config's** value for a path every condition overrode — for a
sampled path, a value no condition in the run used at all.

Now `set(_swept_paths(sweep_block)) | set(sweep.baseline)`, which is the same union `label_for`
already builds from (and, until task 7 retired it, `E-SWEEP-BASELINE-PARTIAL`), so a mode added to
`_swept_paths` reaches this set automatically. Pinned end to end by `test_a_sampled_path_is_unreadable_at_run_scope`, which runs a
`summary` step that reads a sampled parameter and asserts the execution fails with
`E-STEP-SWEPT-PARAM`; reverting the one line makes it pass a run that should have refused.

## `design_digest` over a non-JSON-serializable `data.units` crashes `run` with a bare traceback

**Found by:** H2 Sweeps, Task 3, while narrowing `sweep.sample`'s own exposure to the same call.
**Pre-existing and independent of `sweep.sample`** — reproduced against any config.

`hashes.design_digest` json-dumps `{"units": data.units, "groups": sweep.groups}`, and both are
arbitrary user YAML. A bare date is the easy example, because YAML parses `enrolled: 2026-08-12`
as a `datetime.date` with no quoting mistake in sight:

```
>>> design_digest({"data": {"units": {"from": "c.csv", "enrolled": datetime.date(2026, 8, 12)}}})
TypeError: Object of type date is not JSON serializable
```

`cli.command_run` calls it at phase 5 (`digest = design_digest(doc)`), before any expansion, and
`main` catches `PublishableError`/`OSError` only — so the user gets a raw traceback rather than a
diagnostic. `validate` never calls `design_digest` directly, so nothing refuses it first; the only
`validate`-time guard over `data.units` is `_check_shape`'s **container** type, which a mapping
holding a date passes.

Not fixed here because the refusal belongs where `data.units` is checked, which is **H3 Units** —
and choosing between refusing non-scalar leaves at `validate` time and making `design_digest`
canonicalize what it hashes is a real decision, not a one-line guard. `sweep.sample_seed_for`
converts the same `TypeError` into `E-SWEEP-SAMPLE-INVALID` for its own callers, which keeps
`expand`'s "raises `PublishableError`" contract true but does **not** close this, since `cli`
reaches the digest first.

## ~~RETIRING `E-SWEEP-ABLATE-UNSUPPORTED` OPENED A WINDOW UNTIL TASK 5 LANDS~~ CLOSED

**Found by:** H2 Sweeps, Task 4 review, reading what the retired refusal was also doing.
**Closed by task 5**, which minted `E-SWEEP-ABLATE-BASELINE-MISSING` (row 217) and
`E-SWEEP-ABLATE-CROSSED` (row 218) in `_check_sweep`. Both xfail markers below are gone and the
two tests now assert the exact error-code set each config produces, so
`E-SWEEP-BASELINE-PARTIAL` can no longer carry either one. The record is kept because the window
was real: it was live on this branch between the two commits.

`E-SWEEP-ABLATE-UNSUPPORTED` fired on *any* truthy `ablate`, so it was also the only thing refusing
the two compositions § Expansion modes rules out. Both now validate clean and expand:

| The declaration | What executes today | The rule it breaks |
|---|---|---|
| `ablate` with **no** `sweep.baseline` | `n` conditions, each carrying only its own change and no baseline row at all (`expand({'sweep': {'ablate': {'remove': ['features.labs']}}})` → one condition, `labs=None`) | § Expansion modes: "It therefore **requires** `sweep.baseline`, which `validate` checks" — § Validation row 217 |
| `ablate` × `grid`/`paired`/`sample` | baseline + the product's rows + the ablate rows, e.g. `baseline`, `c=1`, `c=2`, `b=false` from one `grid` axis and one `remove` | § Expansion modes: "the product of 'vary one thing at a time' with a second parameter axis is no longer one thing at a time, and there is no defensible reading of what it would mean" — § Validation row 218 |

`E-SWEEP-PATH-DUPLICATE` does not catch the second either: ablated paths deliberately do not join
`named_by`, for the same reason they do not join `_swept_paths`.

Task 5 owns rows 217 and 218 and closes both. Recorded rather than fixed here because minting their
identifiers is that task's step 1 ("grep for an existing identifier before minting one"), and
splitting one block's identifier work across two commits is how a family ends up half-named.

**The window has a mechanical handle, in a tracked file**, because this file is gitignored and a
prose record of a gap is how this slice already lost one: `tests/test_validate.py` carries
`test_ablate_without_a_baseline_is_refused` and
`test_ablate_crossed_with_a_parameter_axis_is_refused`, both
`@pytest.mark.xfail(strict=True)`, both asserting only that `validate` reports *some* error —
no identifier, since task 5 greps before minting one. `strict=True` means they fail loudly the
moment either gap is closed, so task 5's reviewer confirms closure by watching them flip rather
than by trusting a report. The `ablate × grid` one fixes the grid axis in its baseline
deliberately, so `E-SWEEP-BASELINE-PARTIAL` cannot make it pass for an unrelated reason.

## ~~Row 216 has two readings, and `expand` has now coupled them~~ RESOLVED

**Found by:** H2 Sweeps, Task 4 review. **Resolved by task 5**: both readings are checked, under
the one identifier `E-SWEEP-ABLATE-TARGET`, because the coupling below makes them one question
asked of the two things that answer it. The row's own words are branch 1 (the parameter is neither
boolean nor nullable — a fact about the `Param` alone, ungated by the baseline). Branch 2 asks
`sweep.removal_value` — shared with `ablation_changes` rather than reimplemented — what the entry
*produces*, and the parameter's `Param` whether it may hold it; it therefore fires exactly where
the coupling bites, on a **boolean** the baseline leaves free, and is gated on a declared baseline
because `E-SWEEP-ABLATE-BASELINE-MISSING` owns the no-baseline config whole. The baseline reading
is `remove`'s alone: an `override` states its own value, and refusing one on a path the baseline
leaves free would reject a legal config.

The slice plan glosses § Validation row 216 as "every `remove`/`override` path must be one the
baseline fixes". `reference.md`'s actual row says something else: "`sweep.ablate.remove[0]` is
`analysis.min_samples` (int); `remove` needs a boolean or nullable parameter — use `override`".
Those are two different checks — one about the baseline, one about the parameter's `Param` — and
task 5 must implement **both**, not pick whichever the plan's paraphrase suggests.

They are no longer independent. `sweep.ablation_changes` decides what `remove` sets — `false` or
`null` — from `baseline.get(path)`, because `sweep.py` is pure and has no `parameter_spec` to ask.
So a `remove` path the baseline does not fix silently takes the `null` reading, which means the
baseline-fixes-it check is now load-bearing for the boolean/nullable one: skip it and a
non-nullable `int` gets `null` planted at it with nothing reporting either fault. The path itself
*is* checked as of this task (`E-SWEEP-PATH-UNKNOWN` on `sweep.ablate.remove[i]`), which is a
different question again — the path exists in the template, not that the baseline fixes it.

## `sweep.ablate` has three value-level shapes nothing refuses

**Found by:** H2 Sweeps, Task 4, enumerating what `expand` reads off `ablate`.
**Still open after task 5**, which closed § Validation's three `ablate` rows (216–218) and no
others: none of the three shapes below is any of those rows, each needs an identifier of its own,
and the first is a registry edit to `E-SWEEP-KEY-UNKNOWN`'s documented condition rather than a new
check.

`_check_shape` now guards every `ablate` shape that makes `sweep.ablation_changes` raise, and
`_check_sweep` checks each `override` **value** against its parameter's own `Param`. Three faults
survive both, because each is a legal shape carrying a meaning core reads past:

| The declaration | What executes |
|---|---|
| `ablate: {from: grid, remove: [...]}` | `expand` reads `sweep.baseline` unconditionally — § Expansion modes gives `from` exactly one legal value — so a `from` naming anything else is silently ignored |
| `ablate: {removes: [...]}` | An unrecognised key inside `ablate`; the block is truthy, `ablation_changes` yields nothing, and the run executes the baseline alone while reporting success |
| `ablate: {override: [{a.b: 1, c.d: 2}]}` | One condition **two** changes from the baseline, in the one mode whose entire contract is one change at a time — the same division `sample_fault`'s `len(spec) != 1` draws for a range's single form key |

`E-SWEEP-KEY-UNKNOWN` covers the first family one level up, but its documented condition is
"one of the six recognized sweep modes" — top level only — so widening it to `ablate`'s own keys
is a registry edit rather than a code change, which is why it is recorded rather than taken.

Two smaller consequences of the same block, recorded so they are not re-discovered as bugs:
a duplicated `remove` entry produces two conditions with identical labels (a label is also a
selector — still open), and a `remove` whose path the baseline does not fix takes the nullable
reading and sets `null` — which § Validation row 216 ("`remove` needs a boolean or nullable
parameter") is the check for, not `expand`'s to guess at, and which task 5 closed as
`E-SWEEP-ABLATE-TARGET`'s second branch.

## Per-cell baseline numbering: `expand` emits baselines as a leading block, and the § How artifacts are organized Index row says it must not

**Found by:** H2 Sweep expansion modes, Task 6 review (the divergence), Task 6 (the two
arguments below).

**AMENDED 2026-08-12 (task 7): now reachable.** This entry was written while
`E-SWEEP-BASELINE-PARTIAL` refused every config with more than one baseline — verified at the time
across `grid × grid`, `grid × paired`, a half-fixed `paired`, a baseline fixing nothing swept, and
both `sample` cases. Task 7 retired that refusal, so a multi-baseline config now validates clean
and ships the leading-block numbering this entry describes. Nothing about the argument changes; its
status does. It remains the numbering **task 8 builds on**, and it is no longer theoretical.

`reference.md` § How artifacts are organized, label-grammar table, **Index** row:

> Assigned over the expansion in order, each cell's baseline first *within its cell*. … With one
> baseline it is condition `00`; with [one per cell](../reference.md#expansion-modes) they land at the head of
> each cell, which is why `ablate × groups` numbers `00_cohort=derivation__baseline` and
> `03_cohort=validation__baseline` rather than putting both baselines first.

That is a general rule with `ablate × groups` as its illustration — "which is why" — not a
statement about that mode pair alone. Task 6 implements the opposite: every baseline row is
emitted first as a block, so a baseline fixing `analysis.method` over
`grid: {analysis.method: [pearson, spearman], data.sex: [f, m]}` numbers
`00_sex=f__baseline`, `01_sex=m__baseline`, then the four product rows from `02`.

**The interleaved rule is ill-defined, not merely unimplemented, and that is the argument for
changing the document rather than the code.** "The head of each cell" presupposes that a cell's
rows are contiguous in the expansion, and they are not whenever the free axis is not the outermost
one. In the example above `data.sex` is declared last, so it varies fastest (the same Index row
says so, and `test_the_last_declared_axis_varies_fastest` pins it): the `sex=f` rows are conditions
`02` and `04`, interleaved with the `sex=m` rows, and there is no position that is "the head of the
`sex=f` cell". Satisfying the rule would require reordering the product so each cell is contiguous
— which contradicts the declaration-order nesting of the same row and would renumber every
condition of every existing design — or reading "cell" as something other than a combination of the
unfixed axes. Both readings are design decisions, so neither is taken here.

The `ablate × groups` illustration is consistent only because it has exactly one axis: with one
group axis the cells *are* contiguous, and the rule and the example agree. A second axis is what
separates them.

**AMENDED 2026-08-13 (H3c-1 task 20): the sentence above is true of the two documents and false of
the code, and the difference matters.** It says the *rule* and the *example* agree at one group
axis. They do. What it invites a reader to conclude — that the single-axis case is therefore not
part of this divergence — is wrong, and task 20 measured it rather than reasoning from this entry.
`expand` on § Expansion modes' own printed config (`groups: [{by: cohort, levels: [derivation,
validation]}]` × `ablate` over two removals) returns:

```
00_cohort=derivation__baseline
01_cohort=validation__baseline
02_cohort=derivation__labs=false
03_cohort=derivation__notes=false
04_cohort=validation__labs=false
05_cohort=validation__notes=false
```

The document's comment on that same config prints `00_cohort=derivation__baseline`,
`01_cohort=derivation__labs=false`, … `03_cohort=validation__baseline`. So the leading-block
numbering shows up here too, and a reader designing against the printed example looks for a
directory `03_cohort=validation__baseline` that is named `01_` instead.

This is where the entry's own argument for *changing the document* runs out. "The interleaved rule
is ill-defined once a second axis exists" is sound, and it is not a defence of the code at one
axis, where the rule is perfectly well-defined and simply not implemented. **Task 20's decision:
this is a code finding, not a documentation fix.** The documents lead, the printed example is what
they lead with, and renumbering conditions changes condition directory names, `sweep.yaml` indices
and every downstream reference — not a change to make on the way past in a consistency pass, and
not one to bless by quietly editing the example to match. Task 20 therefore leaves `reference.md`
alone and hands the ordering forward as an open code defect with a measured reproduction.

**Owner is still unassigned.** Task 19's reviewer grepped this slice's plan, its design spec and
`H3c-SCOPING.md` for "the groups slice" and found no mention; H3c-1 was not scoped to it and did
not do it. The deliverable named below — a decision on the Index row — remains undone, and now has
the output above to decide against.

**Owner: the `groups` slice**, which is the slice that makes a multi-baseline config reachable and
therefore the first that must be right. Its deliverable is a document decision on the Index row —
either narrow it to the single-axis case it actually describes and bless the leading block, or
define "cell" and the ordering that makes it contiguous — not a code change taken on the way past.
**Task 8 must not build cell-to-baseline targeting on positional numbering** while this is open:
resolve a condition's baseline by matching its unfixed-axis values, which is invariant under either
numbering.

### RESOLVED (task 8) — § Expansion modes row 2's own example is circular, and task 8 owns it

**Closed by task 8, in the document.** The example was the defective half, so the example changed
and the rule text did not. Row 2 now reads `{analysis.method: pearson}` over a grid sweeping
`analysis.method` and `data.sex`, names the two baselines it produces (`sex=f__baseline`,
`sex=m__baseline`) and states the target as `method=spearman__sex=f` against `sex=f__baseline` —
strings pasted from `expand`'s own output, and the exact shape
`test_two_per_cell_baselines_are_four_comparisons_not_five` runs. Two further arguments for
replacing rather than repairing the `arm`/`sex` example: `arm` is a group level, so that design is
not executable at all while `E-SWEEP-GROUPS-UNSUPPORTED` stands, and the new example is the one the
targeting code is tested against. `experimental-designs.md` § Crossed group axes carried the same
circular claim (`sex=f__arm=treatment` against `sex=f__arm=control`) and was corrected the same
way, to `sex=f__baseline` — that stratum's reference, holding `arm: control`.

The original finding follows. The same table's second row read:

> A value on some axes — `{analysis.method: pearson}`, with `arm` and `sex` left free | One per
> cell of the unfixed axes | Its own cell's baseline: `sex=f__arm=treatment` compares against
> `sex=f__arm=control`

If `arm` is free then the baseline expands over `arm` as well, so what exists is
`sex=f__arm=control__baseline` and `sex=f__arm=treatment__baseline` — and the stated target,
`sex=f__arm=control`, is a *product* row, not a baseline. The rule text underneath ("the baseline
expands over whichever axes it doesn't fix — group axes and parameter axes alike") is unambiguous
and is what task 6 implements; the **example** is the defective half, and its confusion is exactly
the one a targeting implementation would inherit. **Owner: task 8**, which owns "each `vs_baseline`
targets its own cell's baseline".

### Two minors riding along

| The declaration | What executes | Route |
|---|---|---|
| ~~A `baseline` fixing **no** swept path~~ | Every axis is unfixed, so the baseline expands over all of them — eight conditions for a four-cell design, and the correction family doubles | **Superseded by "Three baseline shapes per-cell expansion makes reachable" below**, which corrects this row's example (`z.unknown` is refused by `E-SWEEP-PATH-UNKNOWN` before any of this) and its claim that the baseline rows' `values` equal the product rows' (they carry the baseline's own fixed paths on top) |
| A label body now mixes `key=value` components with a bare `baseline` — `sex=f__baseline` | Nothing at all: no code in `src/` parses a label body (checked recursively, `templates/` and `generators/` included), and `condition_dir_name` is unchanged | No owner today. The residual is for whoever writes the **first** label-body parser: `baseline` is a *trailing component of a mixed body*, not only a whole-label special case, so a parser splitting on `__` and then on `=` must tolerate a final component with no `=`. Task 8 avoids the question entirely by matching on `Condition.values` rather than on the label |

## Three baseline shapes per-cell expansion makes reachable

**Found by:** H2 Sweep expansion modes, task 6 review (the first two), task 7 (the third, and the
corrections below). **Recorded rather than refused, deliberately** — the argument is in the last
section. All three validate clean today.

§ Expansion modes states one rule with no caveat: "the baseline expands over whichever axes it
doesn't fix". `sweep._baseline_cells` is that rule, and it reads fixedness off the *cells' paths*.
Three shapes follow from it that nobody wrote the rule for, and all three were unreachable until
task 7 retired `E-SWEEP-BASELINE-PARTIAL`.

| The declaration | What executes | Pinned by |
|---|---|---|
| A truthy `baseline` fixing **no** swept path — `baseline: {analysis.drop_missing: true}` over a four-cell grid | Every axis is unfixed, so the baseline expands over all of them: four baseline conditions beside the four product rows. Eight conditions for a four-cell design, and the correction family doubles | `test_a_baseline_fixing_no_swept_path_expands_over_every_axis` (`tests/test_sweep.py`) |
| The same shape over a `sample` axis — `baseline: {analysis.method: pearson}` beside `sample: {n: 6, …}` | 6 baseline conditions beside the 6 draws, each baseline carrying its own draw | `test_a_baseline_that_leaves_a_sampled_axis_free_doubles_the_draws` (`tests/test_validate.py`) |
| A `baseline` naming **one** path of a multi-path `paired` cell — `baseline: {analysis.min_samples: 30}` over cells that also set `analysis.confidence` | The axis counts as fixed, so it does not expand; the baseline row carries `min_samples` and lets `confidence` fall to the **base config's** value, which may be neither declared cell's. A cell the axis never produces | `test_a_baseline_naming_one_path_of_a_paired_entry_fixes_that_whole_axis` (`tests/test_sweep.py`) |

**Two corrections to how the first was recorded** under "Two minors riding along" above, both found
by running it rather than reading it. Its example, `baseline: {z.unknown: 9}`, is refused by
`E-SWEEP-PATH-UNKNOWN` before any expansion happens — `validate._check_sweep` resolves every
`sweep.baseline` path against `parameter_spec` — so the entry illustrated the shape with a config
that cannot reach it; a *declared* path is what makes it live. And the baseline rows' `values` do
**not** equal the product rows': each carries the cell plus the baseline's own fixed paths, so the
rows differ by exactly what the baseline names.

**The sharp version of the first shape is narrower and worse than "the count doubles."** The
`values` differ, but the *resolved parameters* coincide whenever the baseline's fixed value equals
the base config's own — `analysis.drop_missing: true` over a config whose `parameters` already say
`true` gives four baseline conditions whose resolved config, and therefore whose `parameters_hash`,
is identical to the product row in the same cell. The run pays twice for one answer, and the
correction family counts it twice. That is the degenerate case; the doubling is the general one.

### Why recorded and not refused

1. **The rule the document states is unconditional.** "The baseline expands over whichever axes it
   doesn't fix — group axes and parameter axes alike," and § Expansion modes tells a reader to
   "prefer the second row whenever the levels are peers". Carving the all-axes-unfixed case out of
   it is a change to a normative document with an argument attached, which is not a refusal taken
   on the way past — and this repo's rule is that the document changes first.
2. **The shape is legitimate under a non-degenerate reading.** A baseline fixing a declared
   non-swept path to a value the config does not already hold is a per-cell **reference arm**:
   every cell measured once at `drop_missing: false` and once at the config's own setting. Refusing
   it is the same error `sweep.ablated_paths` already exists to avoid — refusing a legal config
   with a message about cells. Nothing distinguishes the two readings structurally except whether
   the fixed value equals the config's, which is a `parameters_hash` fact, not a declaration one.
3. **The harm is expressed in comparisons, and comparisons are task 8's.** Doubling the correction
   family and deciding which baseline a `vs_baseline` targets are the same question, and task 8
   owns it. A refusal minted here would have to be re-argued there.

**Owner: task 8** for the first two, which are its comparison-count question in another form; it
should decide whether a baseline fixing no swept path warrants a `W-` row (the identifier is
unminted — grep `W-SWEEP-BASELINE-` before minting one) or is simply a costed design. **Owner: the
`groups` slice** for the third, alongside the numbering entry above: resolving a half-fixed
multi-path axis needs a baseline matched against actual cells, which is the same machinery. All
three are pinned by tests today, so a later slice that changes the behaviour changes a test that
says why, rather than discovering it as a surprising condition count.

## RESOLVED (task 8) — Per-cell baselines reach `resolve_contrasts`, which targets the first baseline for every condition

**Found by:** H2 Sweep expansion modes, task 7 **review**. **Opened by task 7's own commit**
(`eba1804`), which retired the refusal that was keeping any config from reaching per-cell
expansion. Task 6's audit named this consequence and named the refusal as the blocker; task 7
removed the blocker, so the window is live on this branch. **Owner: task 8.**

`contrasts.resolve_contrasts` does `next((c for c in conditions if c.is_baseline), None)` and then
compares every other condition against that one. With one baseline that is right. With per-cell
baselines it is two faults at once, measured on the shape § Expansion modes tells a reader to
prefer — `baseline: {analysis.method: pearson}` over `grid: {analysis.method: [pearson, spearman],
data.sex: [f, m]}`:

```
6 conditions, 2 baselines → 5 comparisons
  sex=m__baseline         of=1 against=0      ← a reference compared against a reference
  method=pearson__sex=f   of=2 against=0
  method=pearson__sex=m   of=3 against=0      ← cross-cell: differs on method AND sex
  method=spearman__sex=f  of=4 against=0
  method=spearman__sex=m  of=5 against=0      ← cross-cell
```

§ Expansion modes says four: *"Baseline conditions are references rather than comparisons, so they
never count as one: six conditions under two per-arm baselines are four comparisons in the
correction family, not five."* And `correction.family_shape` counts `len({m.where for m in
members})`, so `family_size` is 5 × metrics rather than 4 × metrics and **every corrected interval
in the run rests on the wrong denominator, with no diagnostic anywhere**.

**The handle is tracked, in `tests/test_contrasts.py`**, because this file is gitignored and a
prose-only record of a window is how this slice already lost one:

| Test | Asserts | Marker |
|---|---|---|
| `test_two_per_cell_baselines_are_four_comparisons_not_five` | `len(resolve_contrasts(...)) == 4` | `xfail(strict=True)` |
| `test_no_comparison_has_a_baseline_condition_as_its_subject` | no comparison's `of` is a baseline index | `xfail(strict=True)` |

`strict=True` rather than task 4's precedent for a *missing refusal*: this is a wrong **number**,
and the specification states the number, so it is pinnable today. Both flip from `XPASS(strict)` to
a hard failure the moment targeting is fixed — verified by mutation, not by reading: filtering
baselines out of the subject loop makes both pass and therefore both fail.

**Task 8's checklist from this entry**, beyond the two tests going green:

- Resolve each condition's baseline by matching **unfixed-axis values**, not positionally — the
  constraint the numbering entry above already records.
- **The message is not one of the places to edit.** Task 7 tried appending the remedy plus a
  build-state hedge and the re-review cut both: taking that advice does not remove the verdict while
  targeting is single-baseline, and this project puts build state in a message only when the build
  gap *is* the finding (`fold.stratify_by`, the resolver refusals, the `-UNSUPPORTED` family), not
  when the finding is a fault in the user's own config. The message is byte-identical to its
  pre-task-7 text. **Adding the remedy back is task 8's, once targeting makes it true** — the
  emit-site comment says so at the point of the decision.
- Delete the `contrasts.resolve_contrasts` sentence from the emit-site comment and the "what those
  baselines are compared *against* is not settled" paragraph from
  `validate._check_unimplemented`'s docstring. Both exist only because this window does.
- Re-read § Warnings core reports' `W-SWEEP-BASELINE-CONFOUNDED` row: it now says silence on a
  free-axis baseline "is not a verdict that such a design confounds nothing", which stops being the
  honest phrasing once per-cell targeting makes it one.

**How task 8 closed it.** `contrasts.baseline_for` resolves a condition to the baseline of its own
cell by matching the **free axes' values** — the paths the baseline rows disagree on, which
`_free_axis_paths` derives from the conditions themselves rather than from `sweep.baseline`, since
`resolve_contrasts` is handed a config that need not carry one. `expand` lays the same fixed mapping
over every cell, fixed values last, so a path the baseline fixes holds one value across all baseline
rows and can never appear in that set; with one baseline the set is empty, every condition matches
it, and the answer is byte-identical to the single-baseline behaviour this replaced. **No condition
index is read**, which is the constraint the numbering entry above imposes. A baseline is skipped as
an `of` in the generated loop only — a declared `statistics.contrasts` entry may legitimately name
one on either side, and a filter over the returned list would have dropped it while both tracked
tests still passed (`test_a_declared_contrast_naming_a_baseline_as_its_subject_survives`).

Both `xfail(strict=True)` markers are removed and the two tests pass, with the four `(of, against)`
pairs asserted rather than the count alone — `[(2, 0), (3, 1), (4, 0), (5, 1)]`, since four
comparisons all aimed at baseline `0` would satisfy `== 4`. `family_size` is observed end to end by
`test_per_cell_baselines_correct_against_four_comparisons_not_five` (`tests/test_cli.py`): `family:
{comparisons: 4, metrics: 1}` and Holm levels α/4 … α, where first-baseline targeting gave five
members and levels from α/5.

**Two rulings this entry asked for.**

- **The remedy is back in the `W-SWEEP-BASELINE-CONFOUNDED` message**, as this entry's checklist
  scoped it: "fix the axis you are measuring and leave the ones you are stratifying over free, and
  each cell gets its own baseline". Per-cell targeting is what makes it true — the freed axis now
  disappears from `differs_on` — and no build-state hedge is needed, which is exactly why task 7 was
  right to leave it out and this task is right to add it.
- **§ Warnings core reports' row is left as it is, and the softening is declined.** Its caution is
  still literally true, measured rather than reasoned: a baseline fixing *two* of three swept axes
  leaves the third free, so the row's guard is False and nothing is reported, while every cell that
  moves both fixed axes differs from its own cell's baseline on both and is marked `confounded` at
  run time. Pinned by `test_a_partly_fixed_baseline_is_silent_while_its_run_marks_confounded`
  (`tests/test_validate.py`), which also pins that the free axis never appears in `differs_on`.

**A third ruling, from the entry above** ("Three baseline shapes"): a `baseline` fixing no swept path
gets **no new `W-SWEEP-BASELINE-` identifier** — the family stays `W-SWEEP-BASELINE-CONFOUNDED`
alone. It is a costed design, not a fault: every axis is free, so every cell gets its own reference
and every comparison differs in exactly one place. What it costs — twice the conditions and twice
the correction family — is already visible in `dry-run`'s condition count, in `validate`'s
execution-count warning, and now in `family`'s own `comparisons` breakout, which is the disclosure a
reader needs. Warning on it would fire on the legitimate per-cell reference-arm reading the entry
above argues for. The degenerate sub-case it names (the fixed value equal to the config's own, so
the baseline row and the product row resolve to the same `parameters_hash`) is the one worth a
diagnostic, and it is a `parameters_hash` fact rather than a declaration one — routed to whoever owns
duplicate-condition detection, not minted here.

## A sampled condition joins the correction family, which § Sweeps and repeats says it must not

**Found by:** H2 Sweeps, Task 9 (the slice's consistency passes).
**Severity:** Major — it narrows every interval a `sample` sweep reports, which is the specific
harm the passage naming it argues against.

Two normative statements say a `sample` draw is not a comparison:

- `reference.md` § Sweeps and repeats: "So `family` counts conditions from `grid`, `paired`,
  `ablate`, and `groups`, and skips `sample`", with the reason attached — "forty sobol draws over
  `drug.dose_mg` are forty points feeding one downstream curve, and nobody claims a finding about
  draw 17 against draw 1. Holm-adjusting thirty-nine such contrasts corrects a multiplicity no one
  is exposed to, and it would shrink every interval the curve is fitted through."
- § Validation's "Correction declared for a family" row: the warning is "Not raised for a
  `sample`-only sweep, whose draws aren't a family".

Neither holds at `632018b`. **Two code sites, named separately because a fix at one leaves the
other live:**

1. `validate._check_statistics` counts the family as `len(resolve_contrasts(doc, conditions))`, and
   `resolve_contrasts` emits one `vs_baseline` comparison per non-baseline condition whatever mode
   produced it. So `W-STATS-FAMILY` *is* raised for a sample sweep.
2. `cli.command_run` builds the correction family as `vs_baseline_members + contrast_members` with
   no mode filter anywhere, so `family_shape` counts each draw and `corrected_fields` narrows each
   draw's `ci95_corrected` against the others.

Two repros, both validating with no `E-` finding:

```yaml
# (a) baseline + sample. `baseline` is a non-axis mode, so this IS the "sample-only sweep"
# § Validation exempts — the only axis present is the sample axis.
sweep:
  baseline: {analysis.confidence: 0.9}
  sample: {n: 3, method: random, seed: 7,
           ranges: {analysis.confidence: {uniform: [0.8, 0.99]}}}
statistics: {correction: none}
```
`expand` → 4 conditions; `resolve_contrasts` → 3 comparisons; `validate` reports exactly
`{W-STATS-FAMILY}`, naming "3 comparisons per metric form a family".

```yaml
# (b) grid × sample, which violates the § Sweeps and repeats claim under any reading of
# "sample-only".
sweep:
  baseline: {analysis.method: pearson}
  grid: {analysis.method: [spearman, kendall]}
  sample: {n: 3, method: random, seed: 7,
           ranges: {analysis.confidence: {uniform: [0.8, 0.99]}}}
```
`expand` → 9 conditions (3 per-cell baselines, one per draw, since the sample axis is the free
one); `resolve_contrasts` → **6** comparisons. Counting "conditions from `grid` … and skipping
`sample`" gives **2**. No error, no warning — `correction` defaults to `holm`, so every one of the
six intervals is corrected at α/6 … α where the document says the family is two.

**Why this slice, and why nobody caught it earlier.** Task 3 checked the § Validation exemption and
recorded that it "holds structurally, since `resolve_contrasts` needs a DECLARED baseline and a
sample-only sweep has none" — true at the time, because `baseline` + `sample` was refused by
`E-SWEEP-BASELINE-PARTIAL` (task 3's own note (d)). Task 6 retired that refusal and made
`baseline` + `sample` a legal per-cell design, which removed the protection. The verdict was correct
when it was made and false three commits later; nothing re-derived it.

**The document is right and the code is wrong**, so no document was edited to describe the code. The
fix belongs wherever condition provenance is available: `Condition` carries no record of which mode
produced it, so either it gains one or `resolve_contrasts` and `cli` are handed the sample axis's
paths (from `sweep.sample.ranges`). Note that the *second* half of the § Sweeps and repeats sentence
— "`report` says so beside the table" — is dormant rather than violated: there is no `report` command
in this build.

**What the semantics are is not obvious, which is why they were not implemented here.** The
document's expected count for `grid × sample` is **2**, so the three draws *collapse* into the
grid's own comparisons; skipping sampled conditions as comparison subjects gives **0**, a second
wrong number. Deciding between them is correction-family work, not sweep work.

**Shipped instead, and narrowly: `E-SWEEP-SAMPLE-BASELINE`** (H2 task 9, fix round 1), a
validate-time refusal of `sweep.baseline` declared beside `sweep.sample`, in the same
specified-but-not-implemented idiom `E-SWEEP-BASELINE-PARTIAL` used. That is the point: the partial
refusal is what made this combination unreachable, so retiring it in task 6 removed a protection
nothing replaced. The refusal restores it over exactly the reachable harm and no more —
`sample` with no baseline stays legal (no comparison is generated without a declared baseline), and
a declared `statistics.contrasts` entry stays legal (its members are named, not generated per
condition). The refusal retires with the exclusion, and both are the same slice's work.
`tests/test_contrasts.py::test_sample_draws_are_not_comparisons_in_the_correction_family` carries
the `xfail(strict=True)` handle at `expand`/`resolve_contrasts` level, where the semantics will
land.

**Compounds with the entry below.** A declared `statistics.contrasts` entry is the one way a sample
condition joins the family without a baseline, and declaring one today means typing
`confidence=0.8615282253183009` as a label by hand.

## Sampled conditions are labelled with their drawn value, where § How artifacts are organized says `01_sample`

**Found by:** H2 Sweeps, Task 9 (the slice's consistency passes).
**Severity:** Major — it is an artifact-path rule, so it is visible in every directory name a
`sample` run writes, and § How artifacts are organized states it as an exception "deliberately".

The document:

> `sample` conditions are the exception, and deliberately: a sobol draw of `dose_mg` has no short
> exact spelling, and rounding one into a directory name makes two distinct conditions collide at
> some precision. Sampled conditions are labelled `01_sample`, `02_sample`, with the drawn values in
> `sweep.yaml` and in `results.conditions[i].values`. Anything that selects a condition by name — a
> hypothesis `compare.condition`, a `report` filter — is therefore selecting a discrete label, never
> a float you have to spell identically twice.

At `632018b` `label_for` renders a sample cell like any other axis cell, so a 3-draw sample over
`analysis.confidence` labels its conditions `confidence=0.8615282253183009`,
`confidence=0.8286613430456554`, `confidence=0.9236775498775722`, and `condition_dir_name` nests
them under `01_confidence=0.8615282253183009/` and so on. Nothing in `sweep.py`, `artifacts.py` or
`runner.py` produces a `NN_sample` label. Composed with a grid the drawn value lands mid-label:
`method=spearman__confidence=0.8615282253183009`.

`render_value` uses `repr` for a float, so the spelling is exact and nothing *collides* — the
divergence is the second half of the rule, that a selector must name a discrete label rather than a
float, and it is live: `compare.condition` and a contrast's `of`/`against` name conditions by label.

**This is not a one-line change to `label_for`, which is why it is recorded rather than fixed.**
Under the documented rule every draw's label *body* is the literal `sample`, distinguished only by
the numeric prefix — and § How artifacts are organized also says a selector "names the label's body
rather than its prefix". `_condition_labels` returns a **set** (recorded in this file under
`sweep.grid` and `sweep.paired` naming the same path), so n draws sharing one body collapse to one
entry and become structurally invisible to every check built on it. That may be the intent — "nobody
claims a finding about draw 17 against draw 1" implies a draw is not individually selectable — but
it is a ruling about selector identity, not a rendering tweak. Whoever takes it owes an answer to:
what does a `compare.condition` of `sample` select, and what does `E-SWEEP-VALUE-UNNAMEABLE` mean
for a value that is never rendered into a label at all (today a sampled float is checked against
`SWEPT_VALUE_PATTERN` precisely because it *is* rendered).

**The document is right and the code is wrong**, so no document was edited.

## The constant-collapse rule and `sum`'s numeric membership are each stated; their interaction isn't

**Found by:** H3a, Task 1 (`collapse_measurements`), fix round 2 code review.
**Severity:** Critical while unstated — the interaction is what made a silent, data-dependent
corruption of `sum` reachable, and no test caught it because no test constructed a constant
numeric column under a numeric rule.

`reference.md` § What isn't a repeat states two things, each true on its own:

> `collapse` is `mean`, `median`, or `sum` for numeric columns and `first` or `mode` for the
> rest … Attributes constant within a key collapse to that value with no rule needed.

Read together as "if constant, always short-circuit to the value, regardless of rule," the second
sentence breaks the first for exactly one rule: `sum([5, 5])` under that reading returns `5`, not
`10`, because two agreeing depth reads look the same as a non-numeric attribute agreeing by
constitution (a `site` string that never varies within a unit). `mean`, `median`, `first`, and
`mode` are all idempotent on constant input — the naive reading is invisible for three of the five
rules and silently wrong for the fourth, which is exactly why it survived a first round of
implementation and review.

**Resolution, recorded here rather than in `reference.md` because it narrows an interaction
between two already-correct sentences rather than correcting either:** the constant-collapse
sentence's job is to let a **non-numeric** rule succeed over values it has no operation for — it
is not a general-purpose no-op for anything that happens to agree. A numeric rule meeting
genuinely numeric values is the user asking for an aggregation and must get one, even where the
answer happens to equal one of the inputs (`mean([5, 5])` is legitimately `5` — that's not the
shortcut, that's arithmetic). `src/publishable/units.py::apply_rule` now gates the shortcut: it fires
only when the rule is not in `NUMERIC_COLLAPSE_RULES` (`mean`, `median`, `sum`) or the values
are not all `int`/`float` (excluding `bool`, since `isinstance(True, int)` is `True` in Python and
summing booleans is a different intent than summing depths). `tests/test_units.py::
test_the_constant_shortcut_does_not_corrupt_a_numeric_aggregation` pins `sum([5, 5]) == 10`,
`sum([1000, 1000]) == 2000`, `mean([5, 5]) == 5`, and `mean(["A", "A"]) == "A"` (the case the
shortcut exists for) together, so the four rules' behavior on constant input can't drift apart
again unnoticed.

## RESOLVED (H3a task 6) — Two `measurements` codes are now raised where the roster resolves, and their rows say `validate`

**Found by:** H3a, Task 3 (the input path collapses before uniqueness).
**Severity:** Documentation only — the behavior is right and one problem carries one code; what is
stale is which surface each row names. Live until task 6, which already edits these sections.

`validate_config` calls `_check_units` — which resolves the roster, and now collapses it — **before**
`_check_measurements` reports shape faults. So resolution meets a malformed or uncollapsible
`measurements` block first, and `_check_units` catches `ContractError` only: anything else escapes
`validate`, which is required to collect findings and never raise. `resolve_units` therefore now
raises two codes that task 2 introduced as `validate` findings:

- `E-DATA-MEASUREMENTS-INVALID` — from `units._measurement_axis`, for a `measurements` that is not a
  mapping, or whose `by` is missing, empty, or not a string (`str(measurements["by"])` would have
  been a `KeyError`/`AttributeError` out of `validate`).
- `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` — from `units.coerce_for_rule`, for a numeric rule over a
  group it cannot compute (`mean` over `["10", "north"]`), which would otherwise be a bare
  `TypeError` out of `sum`.

`reference.md` § Errors `validate` reports states both rows purely as `validate` checks. The repo's
own convention for a code reached from two surfaces is the dual-listing `E-UNITS-COLLAPSE-RULE`
gets — its row says "raised where technical replicates are collapsed, which `validate` also
resolves and reports under the same code", and it is repeated in § Errors core raises. Neither of
these two has that clause, or a row in the run-time table.

**Recorded rather than fixed here** because the edit lands in the same two sections task 6 already
rewrites when it retires `E-DATA-MEASUREMENTS-UNSUPPORTED`, and splitting one section's consistency
pass across two commits is how a row gets edited twice into disagreement. Whoever takes it: mirror
`E-UNITS-COLLAPSE-RULE`'s wording in both rows, and decide whether the run-time table gains one row
for the pair or one each.

**Resolved (H3a task 6).** Both rows in § Errors `validate` reports now carry the dual-listing
clause, and § Errors core raises gains one row for the pair — one row, because a reader meeting
either code at run time is meeting the same block from the same two surfaces, and two rows would
have to repeat the whole `measurements` premise to say so. The
`E-DATA-MEASUREMENTS-COLLAPSE-TYPE` row also stopped calling the run-time coercion "future": task 3
wired it into `resolve_units` and task 5 into `StepIO.finalize`, and the row now names both.

## RESOLVED (H3a task 6), narrowly — `data.units.measurements.by` need not name a declared attribute

**Found by:** H3a, Task 3.
**Severity:** Minor, and latent — the collapse is correct either way; the declaration is just
weaker than it reads.

`by` is documented as "the attribute distinguishing one measurement of a unit from another", but
nothing checks that it names one. `{measurements: {by: read_id}}` with `attributes: [depth]` — no
`read_id` among them — collapses on the key alone and succeeds, silently treating rows the config
never gave it a way to tell apart as measurements of one unit. The natural home is
`validate._check_measurements`, beside its collapse-rule check, which already holds the resolved
roster and so knows the attribute names; it belongs with task 6's work on the same block.

**Resolved (H3a task 6), for the half that can be checked.** `validate._check_measurements` now
reports `E-UNITS-ATTR-MISSING` at `data.units.measurements.by` when `by` names no column of the
**source table** **and** the input path actually merged rows (`technical_n.max > 1`). The columns
are threaded out of the one read `units._from_table` already does.

**The reference set is the source's columns, not `data.units.attributes`,** and the first cut of
this fix got that wrong. Three things settle it: § What isn't a repeat's own fence — and the
identical one in `experimental-designs.md` § Technical and biological replication — declares
`from`/`key`/`measurements` with **no `attributes` key at all**; `design-principles.md` § Core vs.
plugin lists `key`, `attributes`, `cluster_by`, `measurements.by`, `holdout.from`, `assign.from`
and `stratify_by` as *parallel* namers of input fields, so `by` names a column in its own right;
and `E-UNITS-ATTR-MISSING`'s own registry row already states the predicate as "names a value the
source table has no column for". Checked against `attributes`, the rule refused the exact YAML two
normative documents print. The gate is not timidity — see the entry below, which is what is left of
this one.

## `data.units.measurements.by` means two different things on the two collapse paths

**Found by:** H3a, Task 6.
**Severity:** Minor, and documentation-shaped — the behavior is right on both paths; the field's
description is true of only one of them.

`reference.md` § What isn't a repeat describes `by` as "the attribute distinguishing one measurement
of a unit from another", which is exactly what it is on the **input** path: `units.collapse_measurements`
consumes it, dropping that column from the merged attributes. On the **step** path it is nothing of
the kind. `StepIO._collapse_measurements` never reads `by` at all — the measurement identity is
whatever the step passed as `measurement=`, a value the step invents, and no input column carries
it. So the same declaration is a claim about the input table in one design and an unchecked label in
the other, and a `by` that names no declared attribute is a defect in the first case and the normal
case in the second.

That is why task 6's check is gated on the input path having merged rows rather than applied
unconditionally: applied unconditionally it would refuse a design § What isn't a repeat documents.
The gap it leaves is that a typo'd `by` in a step-measured config is reported by nothing — it costs
nothing today, because nothing reads it, and it would start costing something the moment anything
does. The fix is a document one first: say which path each half of the field describes, and either
give the step path a `by` that means something or say plainly that it does not read one.

## `technical_n` reports the input path's collapse only

**Found by:** H3a, Task 6.
**Severity:** Minor — a fact that is absent rather than wrong, and deliberately so.

`technical_n` reaches every metric block from the roster's own collapse counts
(`summarize_step`'s `beside_n`). A run whose *step* does the measuring has one input row per unit,
so those counts are all ones — a claim of no replication beside a `measurements.parquet` holding
three rows per unit. `command_run` therefore reports `technical_n` only when the input path merged
something, and a step-measured run's counts reach `run.yaml` through no field at all; the file is
the only record of them.

Carrying them properly means a per-execution measurement count on `ExecutionResult`, reconciled
across the repeats of a condition — a unit measured three times in every repeat is one count, not
three — which is the work this entry defers rather than guesses at. `reference.md` § What isn't a
repeat now states the reporting condition, so the absence is documented rather than silent.


## `E-DATA-WEIGHT-INVALID` is registry-listed as a `validate` finding only

**Found by:** H3a, Task 8.
**Severity:** Minor — an identifier reused correctly, in a table that does not yet say it is reused.

`stats.weighted_t_over_units` gates its weights on `units.usable_weight`, the same predicate
`validate` approves a `data.units.weight_by` config against, and raises `ContractError` with
`E-DATA-WEIGHT-INVALID` when one gets through. That is the arrangement `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`
already has — `validate` reports it, `units.coerce_for_rule` raises it at run time, and both
`reference.md` § Validation and § Errors core raises at run time say so in as many words.

`E-DATA-WEIGHT-INVALID` has only the § Validation row. Its § Errors row does not exist, so the
document currently describes the code as something `validate` reports and nothing raises. Nothing
diverges *yet*: no wiring reaches `weighted_t_over_units`, so the raise is unreachable outside its
own tests. It starts diverging the moment task 9 or task 11 wires the weighted path, which is why
the row belongs in whichever of them does the wiring — alongside the retirement of
`E-DATA-WEIGHT-UNSUPPORTED`, which is the same table.


## The cluster-varies-within-measurements rule is stated with no check behind it

**Found by:** H3b, Task 1.
**Severity:** Minor for now — the rule is unbuilt on both sides; sharper than its weight sibling
because the failure it names is a train/test leak rather than a mis-sized estimate.

`reference.md` § Clustered units now states that a cluster must not vary within a unit's
measurement rows, mirroring the sentence § Weighted samples carries for weights. Neither sentence
has a check: `measurements` collapses the column under `first` or `mode` and nothing reports that
the rows disagreed. Reproduced against the built collapse path — `p1`'s replicate rows declaring
sites `S1` and `S2` collapse to `S1` under the `first` fallback, silently.

The asymmetry with the weight case is the reason to record it. A mis-collapsed weight mis-sizes
one unit's contribution; a mis-collapsed cluster decides which side of a train/test split that unit
lands on, so the unit's real cluster is on both sides — and
`experimental-designs.md` § Mistakes core prevents carries **A cluster split across train and
test**, a row CLAUDE.md's *Prevented mistakes* class requires to be structurally impossible rather
than merely discouraged. It is impossible through the partition, which core computes; it is not
impossible through the input file. Proposed resolution: a § Validation row and an `E-` code
refusing a `cluster_by` column that varies within a collapsed key — the same shape as **Holdout
strata survive clustering** — landing with whichever slice builds the collapse-time cluster read.
Deliberately not added in Task 1, which was scoped to state the rule the code below implements.


## RESOLVED (H3b task 13) — The method table has no row for a clustered percentile, and the suffix rule is stated only for contrasts

**Resolved (H3b task 13).** § Statistical reporting's first method table now carries
`percentile_over_units_clustered`, in the proposed wording. Landing it ahead of a caller is
deliberate: the entry below shares one edit with it, and the table's own purpose — "named here so
two readers of one `run.yaml` agree on what they're holding" — is not served by naming a
construction only once something reaches it. **The derived half of this entry is not resolved and
is no longer a documentation gap**: `percentile_of_derived`'s clustered form still does not exist,
and task 12 refused the combination as `E-DATA-CLUSTER-DERIVED` rather than building it. Task 13
added the conditional clause § Statistical reporting was missing, so the "a derived metric is
resampled whether or not you declare `statistics.resample`" claim no longer reads as
unconditional. H4 owns the construction.

**Found by:** H3b, Task 10.
**Severity:** Minor — a `method` string core now writes that no table in the documents defines.

`reference.md` § Statistical reporting carries two method tables. The first — the one that names
what a `basis: units` metric's interval *is* — has rows for `t_over_units`,
`t_over_units_clustered`, `percentile_over_units` and `t_over_repeats`. There is no row for a
clustered percentile. The `_clustered` suffix rule is stated in the paragraph under the *second*
table, the contrast one: "When `cluster_by` is declared each takes a `_clustered` suffix and reads
the cluster as the draw … and the percentile forms resample whole clusters." Its "Same rule and
same reason as `t_over_units_clustered` above" makes the rule general, which is why task 10 named
its construction `percentile_over_units_clustered` — but the name is one the documents do not
contain, and `method` exists precisely so two readers of one `run.yaml` agree on which
construction they are holding.

Proposed resolution: a fifth row in the first table — `percentile_over_units_clustered` | *The
2.5th and 97.5th percentiles of the resampled distribution, drawing whole clusters with
replacement and pooling their units; the number of draws per replicate is the cluster count* —
landing with the slice that wires it. § Clustered units already carries the substance ("Core draws
whole clusters with replacement, so a resampled table has a varying row count, and the interval's
effective `n` is the cluster count"); what is missing is only the name in the table that
enumerates names.

**A second, larger gap sits behind it.** The percentile interval that actually runs today for
every derived metric is `stats.percentile_of_derived`, called from `summarize_step` under `cli`'s
hard-coded `derived_metric_draws = 2000` and ungated by `statistics.resample`. Task 10 built the
clustered *column* form (`percentile_over_units_clustered`); `percentile_over_units` itself has no
call site in `src/` at all, `statistics.resample` being unbuilt. So the clustered draw that a
declared `cluster_by` will need first is `percentile_of_derived`'s — each replicate drawing `G`
clusters and building a `UnitTable` from their pooled units, which `unit_table_from_rows` already
supports — and it does not exist. Whichever task retires `E-DATA-CLUSTER-UNSUPPORTED` must either
build it or refuse the combination, because a clustered run reaching `summarize_step` today would
get a 228-draw percentile interval on every derived metric with nothing to say so.


## RESOLVED (H3b task 13) — The method table has no row for a weighted clustered interval either

**Resolved (H3b task 13), and it was three rows rather than one.** Enumerating every `method=`
string `src/` writes against § Statistical reporting found a *third* absentee:
`weighted_t_over_units`, H3a's own construction, which the table never named either — § Weighted
samples describes it in prose as "a weighted `t_over_units` interval" and the full string appears
nowhere. All three landed together, since a row for the weighted clustered form reads as an
exception to a row that has to exist first. Every string core writes is now in the table, checked
both directions.

**Found by:** H3b, Task 11.
**Severity:** Minor — a second `method` string core now writes that no table in the documents
defines. Same class as the entry above, and the same one-edit fix.

`reference.md` § Weighted samples names the combination among its "four interactions worth
knowing" — "`cluster_by` still decides the draw when both are declared, since a cluster is what's
independent and a weight is what it represents" — and § Statistical reporting's first method table
carries `weighted_t_over_units` and `t_over_units_clustered` as separate rows with no row for the
two together. Task 11 wired the combination rather than refusing it, because refusing would cost
every `basis: units` interval in a run declaring a documented pair, and because both halves are
decided by a document sentence: the draw (and so the df, clusters − 1 per § Statistical reporting)
is the cluster, and the estimate is the weighted mean. The construction is
`stats.weighted_t_over_units_clustered`, and it reduces to `t_over_units_clustered` digit for digit
at equal weights.

Proposed resolution: a row — `weighted_t_over_units_clustered` | *The weighted mean, with a
cluster-robust variance whose scores carry the weights; df = clusters − 1, not Kish's effective
size, since `cluster_by` decides the draw* — beside the `percentile_over_units_clustered` row the
entry above proposes, landing in the same doc edit. § Weighted samples' own "four interactions"
sentence is the substance; only the name is missing.

**The derived-metric half of the entry above is unchanged and now sharper.** Task 11 wired every
recorded column's interval, weighted or not, but a DERIVED metric's interval is still
`percentile_of_derived`, which draws units. The clustered construction for it does not exist, and
the slice retiring `E-DATA-CLUSTER-UNSUPPORTED` owes a refusal of that combination by name —
recorded in `stats.summarize_step`'s docstring so the next reader of the branch finds it there too.

## RESOLVED (H3c-1, task 16) — `design_digest` included `assign.seed`, which § What `auto` derives from excludes

`reference.md` § What `auto` derives from states the design digest is taken over "`data.units`
(every field except `assign.seed` itself) and `sweep.groups`". `hashes.design_digest`
canonicalises `data.units` **wholesale** — `{"units": units, "groups": groups}` — so an
`assign.seed` pinned to an integer is inside the digest today.

**The document is right and the code is wrong.** The section's own argument settles it: pinning a
seed is "the deliberate act", and every `auto` value in the table below it mixes the digest. With
`assign.seed` inside, pinning the `arm` axis's seed would move every repeat seed, every fold
boundary, every `sweep.sample` draw, and every *other* axis's allocation — the exact confounding
("one visible change and two invisible ones") this section exists to refuse. The exclusion is also
what makes the row *An axis's `assign.seed` | digest + the axis name + the resolved roster* honest:
that derivation reads the digest, so a field it produces must not feed it.

The fix is one line in `hashes.design_digest` — drop `seed` from each `assign.<axis>` block before
canonicalising, leaving every other `assign` field (`method`, `from`, `stratify_by`, `ratio`,
`block_size`) inside, since those describe what is randomized over. **H3c-1 task 16 owns it.**
No document change is owed.

**Closed by task 16.** `hashes._units_excluding_drawn_seeds` (named `_units_excluding_assign_seed`
until renamed by H3d task 4) drops `seed` from each `assign.<axis>` block, per-axis, before
`design_digest` canonicalises `data.units` — every other `assign` field, and a second or later
axis's own `seed`, still moves the digest. It also never raises on a shape it does not expect
(`assign` or an axis block that is not a mapping), since `validate` can reach `design_digest`
before a config is known-good.

**~~One field over, the same defect is latent.~~ Closed by H3d, task 4.**
`hashes._units_excluding_assign_seed` was renamed `_units_excluding_drawn_seeds` and now
drops `data.units.holdout.seed` as well as each `assign.<axis>.seed`, so a pinned holdout
seed no longer perturbs any other derived draw. `reference.md` § What `auto` derives from
gained the matching row and named `E-DATA-HOLDOUT-SEED` in the same slice.

**Found by:** H3c-1, Task 1 (documents-only). **Closed by:** H3c-1, Task 16 (`assign.seed`
half); H3d, Task 4 (`holdout.seed` half).
**Severity:** Was Minor while open, since `assign` is refused outright as `NOT BUILT` and no
config could reach a pinned `assign.seed` — but it would have become live the moment H3c-1
retired that refusal, so closing it now rather than later avoids a fix landing after the
confounding it prevents becomes reachable. The `holdout.seed` half above is closed by H3d
task 4.

## RESOLVED (H3c, task 10) — `assign.<axis>.from`'s "unchanged" divergence from `weight_by`/`cluster_by`

Task 10's brief said `_check_weight_by` "is the model" for the new `assign.<axis>.from`
checks, and "every one of those applies here unchanged" — including "why a non-str
declaration returns silently (`check_envelope` owns `E-CONFIG-TYPE`, and reporting it
again would describe `3` as 'empty')".

**That reason did not carry over, and the brief was wrong that it did.** `weight_by`
and `cluster_by` are `envelope.py` `LEAF_TYPES` entries (`"data.units.weight_by": str`,
`"data.units.cluster_by": str`), so a non-`str` value there really is caught by
`E-CONFIG-TYPE` before `_check_weight_by`/`_check_cluster_by` ever run, and returning
silently defers to a real backstop. `assign.<axis>.from` is not in `LEAF_TYPES` at all —
`envelope.py`'s own comment names `assign`'s children as one of the dynamic-key
families (`grid`, `baseline`, `assign`) "which no fixed dotted path reaches" — so a
`from: 3` or `from: [x]` was typed by nothing, and the first draft of `_check_assign`
skipped it (matching the two siblings' silent-return *shape*, but with no backstop
behind the skip): reported by nothing in this build, not deferred to something that
already reports it — the inverse of what this whole plan hunts for, since a config
shape `validate` is silent about is a live gap rather than a documented refusal.

**Closed in the same task, once the review caught it.** `_check_assign` no longer
skips a non-`str`, non-`None` `from`: it reports `E-DATA-ASSIGN-UNKNOWN`, naming the
value's type rather than a resolved attribute name, folding the fault into the
existing code rather than minting a second one — the same absorption
`E-DATA-ASSIGN-METHOD` already performs for a non-mapping block ("the block naming no
method that it is"). `weight_by`/`cluster_by` still return silently, correctly: they
have a real `E-CONFIG-TYPE` backstop this key does not, so their silence defers to
something that already reports it, where `from`'s did not.

**Found by:** H3c, Task 10. **Closed by:** the same task, on review.
**Severity:** Was Minor while open — a malformed `from` (a type no YAML author reaches
by a plausible typo; the plausible one, a bad *string*, is `E-DATA-ASSIGN-UNKNOWN`'s
own case already) reported nothing rather than a diagnostic. No document change is
owed: `reference.md`'s `E-DATA-ASSIGN-UNKNOWN` row and `_check_assign`'s docstring
both state the closed behavior directly.

## RESOLVED (H3c, task 11) — "one column named as both the arm attribute and `cluster_by` should draw both codes" is false for one `resolve_units` call

Task 11's brief (Controller additions, mutation paragraph) said: "one column named as
*both* the arm attribute and `cluster_by` **should** draw both codes, which is exactly
what `CONSTANT_COLUMN_RULES`' docstring means by keying on the declaration so a config
'is checked once for each rather than silently dropping one under a precedence rule
nothing in the documents states'."

**Checked by observation, not inference, and it does not hold literally.**
`collapse_measurements` raises the first `ContractError` its `constant` loop finds and
stops — it is a raise, not a `Collector` that gathers every finding before reporting.
A single config declaring `cluster_by: arm` *and* `assign: {arm: {method:
by_attribute}}` over rows where `arm` varies gets exactly **one** code from one
`resolve_units` call: `E-DATA-CLUSTER-VARIES`, because `constant` gathers the flat
declarations (`cluster_by`, `weight_by`) before `_assign_constant_columns` adds the
per-axis `assign.<axis>.from` entries, so `cluster_by`'s check runs first and the loop
never reaches `assign`'s. `validate`'s own `except ContractError` around
`resolve_units` converts that one raise into one finding, so this is true at both
surfaces, not an artifact of the direct call.

**What survives is the weaker, true half the pre-existing docstring actually
supports**: each declaration, considered *on its own* (a config naming only
`cluster_by`, or only `assign`), still raises its own code over the same varying
column — neither check is skipped *because* the other declaration also names it, which
is what "checked once for each ... rather than silently dropping one under a
precedence rule" can honestly mean. `tests/test_units.py`'s
`test_one_column_named_by_both_cluster_and_arm_reports_exactly_one_code` pins the
literal (single-code) behavior, and
`test_the_three_codes_are_not_one_code_and_none_excludes_another` pins the weaker
(each-checked-independently) claim across three separate calls.

**Closed by rewording rather than by code**: `CONSTANT_COLUMN_RULES`'s docstring in
`src/publishable/units.py` now states both halves explicitly — the true "no mutual
exclusion" claim and the false "reports both from one call" claim it is not — so a
future reader does not re-derive the same wrong expectation from the same true-sounding
sentence. No behavior changed; `resolve_units`/`collapse_measurements` were already
correct (a single raise is the load-bearing property `validate`'s
`except ContractError` boundary depends on), and reporting *all* the constancy faults
a config carries at once would need `constant`'s loop rewritten to collect rather than
raise — out of scope here and not something this task's brief asked for.

**Found by:** H3c, Task 11. **Severity:** Minor — a doc-comment overclaim inherited
from the cluster/weight pair (task 9/H3a's pattern), not a behavior gap; the two tests
above are the record that it was checked rather than assumed.

## RESOLVED (H3c, task 17) — An out-of-enum `allocation` beside a declared group axis will be checked by nothing once `E-DATA-ALLOCATION-UNSUPPORTED` retires

**Resolved (H3c, task 17).** `_check_assign` now checks `data.units.allocation` against
`ALLOCATION_MODES = ("within", "between")` before either *Allocation needs arms* or
*Arms need allocation* runs, reporting an out-of-enum value (present and not `within`
or `between`) as `E-DATA-ALLOCATION-METHOD` — the exact resolution proposed below,
including the code name. `docs/reference.md` § The one config file and § Errors
`validate` reports and § Validation each carry the new row.
`tests/test_validate.py`'s `test_an_out_of_enum_allocation_is_refused_by_its_own_check`
pins `allocation: sideways` to exactly that one finding, with `within` and a
well-formed `between` config as controls that must not draw it.

Task 12 (H3c) added `E-DATA-ALLOCATION-WITHIN-ARMS` — *Arms need allocation*, the
mirror of *Allocation needs arms* — gated explicitly on
`units.get("allocation") in (None, "within")` rather than a bare `elif axes:`, so a
misspelled or otherwise out-of-enum `allocation` value (`allocation: sideways`) beside
a declared group axis is deliberately left unreported by this row: reporting it as
"within" would misname the value, and no enum-shape check on `data.units.allocation`
exists anywhere in `validate.py` today — `envelope.py` only types it `str`.

That gap is currently invisible because `_check_unimplemented`'s blanket
`E-DATA-ALLOCATION-UNSUPPORTED` fires for *any* value other than `None`/`within`,
`"sideways"` included, so a config in this shape always carries at least one error
today. Once the slice that retires `E-DATA-ALLOCATION-UNSUPPORTED` lands (task 17), a
config declaring `sweep.groups` plus `allocation: sideways` will validate with **no**
finding naming the allocation value at all — neither `E-DATA-ALLOCATION-NO-ARMS`,
`E-DATA-ALLOCATION-WITHIN-ARMS`, nor anything else — and will presumably also fail to
build `arm_members` in `cli.command_run` (whose gate is `selector_paths(sweep_block)`,
which does not read `allocation` at all), most likely surfacing later, if at all, as an
opaque `KeyError` from `units.arm_members` rather than a diagnostic.

Proposed resolution: whichever slice retires `E-DATA-ALLOCATION-UNSUPPORTED` should add
an enum-shape check on `data.units.allocation` (`within`/`between`, matching
`ASSIGN_METHODS`'s own enum-check pattern in the same file) — most likely a new
`E-DATA-ALLOCATION-METHOD` beside `_check_assign`'s codes, checked before either the
*Allocation needs arms* or *Arms need allocation* row runs, so both can safely assume
`allocation` is already one of the two values they gate on.

**Found by:** H3c, Task 12, on review (a reviewer traced what covers an out-of-enum
`allocation` after `E-DATA-ALLOCATION-UNSUPPORTED` retires and found nothing does).
**Severity:** Minor today (the blanket refusal still covers it); becomes a real gap the
moment task 17 lands, so it is recorded now rather than rediscovered then.


## `limits.min_units_per_cell` is still declared, typed, and read by nothing, now that `allocation: between` is reachable for real

H3c-SCOPING.md § 1 named this the sixth thing `E-DATA-ALLOCATION-UNSUPPORTED` masked, and task
17's check-off confirms no task between 1 and 16b closed it: `grep -rn min_units_per_cell
src/publishable/*.py` finds it declared in `materialize.py` (`init` writes
`min_units_per_cell: 20` into every generated config) and typed in `envelope.py`
(`"limits.min_units_per_cell": int`), and nowhere else — no `validate.py` check reads it, the
same `grep` control the scoping document ran for `max_executions` (which does have live reads)
confirms is not a grep artifact.

`docs/reference.md` § The one config file's inline comment states the rule in the present tense,
with no `NOT BUILT` marker: `min_units_per_cell: 20  # validate warns for a smaller design cell
under allocation: between`. § Validation lists two rows for it — *Cells are populated* (a
`sweep.groups × grid` cross whose smallest cell is below the limit) and *Allocation is coherent*
(a plain `allocation: between` split below the limit) — both worded as warnings, present tense,
no `NOT BUILT` marker, and neither has a code anywhere in `validate.py` or the registry table.

Before task 17, this was inert rather than wrong: every `allocation: between` config that could
exercise it also carried `E-DATA-ALLOCATION-UNSUPPORTED`, so a reader could believe the two
`min_units_per_cell` rows were merely unreached by their test suite rather than unbuilt. After
task 17, `allocation: between` validates and runs for real, and a design whose smallest arm ×
condition cell is thin — the exact shape `experimental-designs.md` warns against for
`report_by` strata ("five reporting attributes as `groups` axes multiply into a cartesian
product of cells, each ... most of them below `limits.min_units_per_cell`") — completes with no
warning at all, contradicting `reference.md`'s own present-tense claim.

Proposed resolution: two warnings in `_check_assign` (or a sibling function reading the same
resolved roster and group axes), each needing the roster to have resolved: the smallest
`len(arm_members(...))` cell under a bare `between` allocation, and the smallest cell of the full
group-axis × parameter-axis cross, each against `limits.min_units_per_cell`. Naming — `W-DATA-
ALLOCATION-CELL` or two codes, one per § Validation row — is left to whichever slice builds it,
since neither row's own code was ever minted.

**Found by:** H3c, Task 17, re-verifying every item H3c-SCOPING.md § 1 listed under
`E-DATA-ALLOCATION-UNSUPPORTED` rather than assuming tasks 12–16b closed all six. **Severity:**
Moderate — task 17 makes the shape reachable for the first time; a user relying on
`reference.md`'s stated warning for a thin cell gets none.


## RESOLVED (arms-drawn, task 4) — `data.units.assign`'s per-axis blocks now have unknown-key closure

`docs/reference.md` § The one config file's own paragraph promised this: "`.holdout` and
`.assign` inherit the same treatment when their slices land" (the whole-leaf schema closure
`measurements.by`/`.collapse` get). `.assign`'s slice — `_check_assign`, `arm_members`,
`allocation.json` — landed across tasks 7–16, but the closure did not: `envelope.py` still types
`data.units.assign` a bare `dict` with no `data.units.assign.<axis>.*` entries (H3c-SCOPING.md
§ 1's `E-DATA-ASSIGN-UNSUPPORTED` masked-item 1), so a misspelled field inside an axis block —
`assign.arm.stratifyy_by` for `stratify_by`, or `assign.arm.form` for `from` — is silently
ignored rather than reported. `_check_assign` reads only the specific keys it knows
(`method`, `from`, `stratify_by`, `ratio`, `block_size`, `seed`); a key it does not know sits in
the block unread and undiagnosed, the same way `E-CONFIG-KEY-UNKNOWN`'s "did you mean" closure
exists to prevent for every other block in the config.

Task 17 updated the § The one config file paragraph to say this plainly rather than repeat the
"when their slices land" promise past the point where it stopped being accurate — see the edit
beside `.weight_by`/`.cluster_by`'s own paragraph.

Proposed resolution: whichever slice builds `assign.<axis>.from`'s registry accessor for
`CONSTANT_COLUMN_RULES` (H3c-SCOPING.md § 1's masked-item 2, also still open — `units.py`'s own
comment names it) is a natural place to also close this, since both need a way to name a key
under an open, axis-named dotted path the same closed-schema pass already has for `parameters`
and `sweep`.

**Found by:** H3c, Task 17, re-verifying every item H3c-SCOPING.md § 1 listed under
`E-DATA-ASSIGN-UNSUPPORTED`. **Severity:** Minor — a missing "did you mean" diagnostic, not a
silent-no-op on a value that changes the record; the misspelled key's *default* still applies
(`from` defaults to the axis name, `stratify_by`'s absence just means no stratification), so the
run is well-formed under the default rather than wrong.

**Closed by task 4 of the arms-drawn plan.** `envelope.py` adds `ASSIGN_AXIS_KEYS = frozenset({
"method", "from", "ratio", "block_size", "stratify_by", "seed"})` and `_check_assign_axis_keys`,
called from `check_envelope` alongside `_check_unknown_keys`: it walks `data.units.assign`,
and for every axis block that is a mapping, checks the block's own keys against that closed
set — the same `E-CONFIG-KEY-UNKNOWN` code and "did you mean" hint the generic closure uses,
built by hand because the generic mechanism (`_check_unknown_keys`) never descends into a known
LEAF's value and the axis name one level up is exactly the dynamic key `LEAF_TYPES` cannot name,
so it cannot be pointed at this block by adding a dotted path. `stratifyy_by` and `assign.arm.form`
are both now reported; `docs/reference.md` § The one config file's paragraph beside `.assign` was
rewritten to say so rather than record the gap. Mutation-tested both directions: removing
`stratify_by` from `ASSIGN_AXIS_KEYS` is caught by the existing
`test_an_assignment_declaring_no_method_is_refused` (its exact-set assertion gains an unexpected
`E-CONFIG-KEY-UNKNOWN`), and a config declaring all six keys in one axis block reports nothing.


## CONFIRMED CLOSED (H3c, task 11) — `assign.<axis>.from`'s registry accessor and `E-DATA-ASSIGN-VARIES`, re-verified rather than assumed for task 17

H3c-SCOPING.md § 1's masked-item 2 and 3 under `E-DATA-ASSIGN-UNSUPPORTED` read, at the branch
point (`cb96c7d`, before tasks 7–16 landed), as still open. Task 17's check-off re-verified them
against the code as it now stands rather than trusting that older snapshot: `units.py`'s
`_assign_constant_columns` (task 11) is exactly the accessor the masked item asked for —
`resolve_units` builds it from `units_decl.get("assign")` and merges it ahead of the flat
`cluster_by`/`weight_by` pair, so an axis's `from` column reaches `CONSTANT_COLUMN_RULES`'s
severity ordering after all. `E-DATA-ASSIGN-VARIES` exists, in both `units.py` and
`docs/reference.md` (§ Validation's *Arm is constant within a unit*, § Errors `validate` reports,
and § Allocation's own paragraph) — `grep -n E-DATA-ASSIGN-VARIES docs/reference.md src/` returns
five hits, not zero. Both items are closed; no action needed from task 17 beyond this
confirmation.


## A validate-time `comparisons × metrics` bound on `resample.n` cannot be built

Found while scoping H4a (2026-08-15, `eaf3605`). `H4-SCOPING.md`'s trap 1 asked `validate` to
bound `statistics.resample.n` against the correction family, which `correction.family_shape`
computes as `comparisons × metrics`.

**The metric count is unknowable at `validate` time by design.** `family_shape` reads
`len({(m.step, m.metric) for m in members})` from `Member`s `cli._comparison_step_blocks` builds
*after every execution has run*, out of (a) recorded columns, which come from `io.record` calls
inside user step code, and (b) `aggregate`'s returned keys, which come from user template code.
Neither is declared anywhere in the config — `envelope.LEAF_TYPES` has no `metrics` path,
`parameter_spec` declares parameters, and `hypotheses` names metrics only for the ones a user
pre-registered. `CLAUDE.md`'s greenfield invariant closes the door: core "never inspects the body
of user Python."

**What H4a built instead:** `W-STATS-RESAMPLE-FAMILY`, a comparisons-only lower bound — with `k`
comparisons and at least one metric each, `holm`'s tightest level is `ALPHA / k` and needs
`min_honest_draws(1 − ALPHA/k)` draws. Always true when it fires, silent when it might not be.

**The residue, accepted rather than fixed:** a config with many metrics can still null every
`ci95_corrected` while clearing this bound. That is already disclosed at run time by
`W-STATS-CORRECTED-THIN`, which names the realized `family_size` and `correction_level`. Proposed
resolution: none — a validate-time check that reported the real requirement would have to know
what user code returns, and the run-time disclosure is the honest surface for it. Recorded so the
absence is a decision rather than a gap nobody noticed.

**The residue names one family; there is a second.** `hypotheses.py` corrects the same
`resample`-backed pools at its own level, `ALPHA / H`, where `H` is the confirmatory hypothesis
family core actually computed — `reference.md`'s "Counted-iff-corrected applies to that family
too" — not the count of hypotheses a config merely declares. A `kind: exploratory` hypothesis and
a summary-metric hypothesis (a reported `Estimate`, never corrected) are both named in the config
but excluded from `H`, so declared count is an upper bound on `H`, not `H` itself — the same
one-step-removed relationship that makes `comparisons × metrics` unboundable from declarations
alone, just one layer thinner. `W-STATS-RESAMPLE-FAMILY`'s task-6 bound reads only
`statistics.contrasts`/the sweep's baseline family; it says nothing about a config whose only
correction pressure comes from `hypotheses`. Same proposed resolution as above: none — the
hypothesis family's own `W-STATS-CORRECTED-THIN` at run time is where this is honestly caught,
and a validate-time version would need to know which declared hypotheses survive to `H`, which is
run-time knowledge by the same argument as the metric count above.

## `statistics.null_test` has no no-units check, unlike `fold` and `resample`

Found during task 7's review (2026-08-15, H4a, `01b2b97`). Task 7 gave `resample` a
declared-with-no-`data.units` refusal, `E-STATS-RESAMPLE-UNITS`, matching the existing
`E-REPL-FOLD-NO-UNITS` precedent for `fold`. `reference.md`'s "required by fold, resample,
null_test" line names all three, but only two now have the check: `null_test` is still refused
wholesale by `E-STATS-NULLTEST-UNSUPPORTED` with nothing underneath it, so the moment that
refusal retires, a bare `null_test: {shuffle: status}` with no `data.units` validates clean and
runs nothing — the identical hole task 7 closed for `resample`, reopened one field over.

Proposed resolution: whichever slice retires `E-STATS-NULLTEST-UNSUPPORTED` (H4d, per the current
plan) adds the same declaration-gated check `_check_resample` and `_check_replication` both use —
`not (doc.get("data") or {}).get("units")` — under its own code (`E-STATS-NULLTEST-UNITS`, to
match the naming this task settled on rather than the `E-REPL-FOLD-K` name once miscited for it),
reporting without returning, so a roster-independent `null_test` shape fault (its own `shuffle`
checks) still surfaces in the same pass.

**CLOSED by H4d task 8 (2026-08-18).** `_check_null_test` reports `E-STATS-NULLTEST-UNITS` from the
declaration, without returning, so a roster-independent shape fault in the same block still surfaces
in the same pass — pinned by
`tests/test_validate.py::test_a_null_test_with_no_units_is_refused_and_the_shape_faults_still_report`,
whose fixture carries a sub-floor `n` beside the missing roster for exactly that reason.

## A column metric's `resample_draws` records the requested `n`, not a survivor count

Decided in H4a (2026-08-15). `stats.percentile_over_units` returns a bare `Interval` where
`percentile_of_derived` returns `(Interval, int)`, so a recorded column under a declared
`statistics.resample` has no survivor count to record beside its interval.

**Ruling: record the requested `n`, and only when an interval is actually produced — conditional
on finite inputs.** A column's draw statistic is a mean over a non-empty sample of *finite*
values with *finite* weights, and under that condition it is always defined — the unweighted
branch divides by `n >= 2`, `checked_weights` refuses a non-positive or non-finite weight before
any draw, and a stratified pool is non-empty by construction — so `draws_used == n` whenever
`ci95` is non-null, and the return type need not change (~20 existing tests read it). Verified
rather than assumed, by
`tests/test_stats.py::test_a_column_resample_is_never_degenerate_across_adversarial_columns_of_finite_values`
and the parametrized weight refusal beside it. **The finiteness condition does not hold
unconditionally** — see the separate entry below, filed rather than fixed here.

**The `None` case, worked out rather than left unanswered.** `percentile_over_units` returns
`None` for three reasons: too few values, too few draws for the confidence level, or (as of
tasks 9/10) a structural constant-pair refusal. In every one of those, `ci95` is `null` and there
is no interval for `resample_draws` to describe — recording the requested `n` there would assert
survivor evidence for a refused interval, which is incoherent. **Ruling: `resample_draws` is
`null` whenever `ci95` is `null`, for any of the three reasons.** This repurposes the derived
metric's "`null` = resampling never attempted" bucket to also cover "attempted, but structurally
refused before a single draw" — a fourth case in truth (the roster *was* declared, resampling
*was* requested, yet nothing was drawn), collapsed onto the same `null` symbol because its
observable effect is identical: no interval, no evidence. **The consequence for the existing
three-way scheme:** the derived metric's `0` bucket ("attempted, every draw individually
degenerate") is structurally unreachable for a column given finite inputs, because nothing on
this path can make one draw's mean fail while another succeeds — a column's degeneracy, if any,
is a fact about the whole sample before any draw runs, never about one draw among many. So a
column's field is genuinely two-valued (`null` or the requested `n`), not three-valued, and that
asymmetry with the derived metric's field is real and should be named wherever `resample_draws`
is documented for columns, not smoothed over. This is new content `reference.md` § Statistical
reporting does not state today (see below) and is owed as part of whichever slice (task 12/14)
wires column resample into `summarize_step`.

**Consequence to keep in view:** `W-STATS-RESAMPLE-THIN` fires on `used < requested`, so it can
never fire for a column (a column's `resample_draws` is only ever `null` or the full `n`, per the
ruling above — there is no partial-survivor state to be "thin"). That is correct — the warning
exists for a template's `aggregate` producing nothing on some draws — but it means the two metric
kinds carry the same field with subtly different provenance.

**Correcting this entry's own citation, per review.** An earlier draft of this entry cited
`reference.md` § Statistical reporting as already stating that provenance split. It does not: the
section's `resample_draws` paragraph says the field is "recorded beside every derived metric" and
never mentions columns at all. That was this entry citing a document for a claim the document
does not make — the exact inversion `CLAUDE.md` warns about ("the document changes first").
**Corrected: § Statistical reporting has no column-provenance language yet, and adding it —
including the `null`-only-or-`n` two-way scheme ruled on above — is owed to whichever slice wires
`statistics.resample` for columns (task 12/14), not claimed as already written.**

**Task 11's own docstring text was itself an instance of the trap this section warns about.**
The brief's Step 3 text read "a column's `resample_draws` is the requested `n` and is recorded as
such by `summarize_step`" in the present tense. Checked against the code (2026-08-15,
`c5de085`): `summarize_step`'s recorded-column branch (`out[column] = {...}`, distinct from the
derived-metric branch a few lines below it) carries no `resample_draws` key at all today — only
`value`, `basis`, `n`, `ci95`, `method`, `correction`. Wiring `statistics.resample` into that
branch is task 12/14's work; `E-STATS-RESAMPLE-UNSUPPORTED` still refuses a declared `resample`
end to end. The docstring landed in `stats.py` was reworded to say the invariant holds for
whenever that wiring lands, rather than asserting current behavior the code does not have — the
same "comment claiming a guarantee the code does not provide" failure mode this repo has hit at
least eight times before.

**AMENDED 2026-08-15 (spec-defects staleness audit at `5578988`): the documentation debt this entry
books was PAID, and its owner — "whichever slice (task 12/14) wires column resample into
`summarize_step`" — is a closed slice, so nothing here is left owing.** That slice ran: it was H4a.
`reference.md` § Statistical reporting now carries the column-provenance paragraph this entry said
was owed, and it says what the ruling above ruled — a recorded column's `resample_draws` is
**absent** (not `null`) with no declared `resample`, `null` whenever `ci95` is, and otherwise the
**requested** `n`, explicitly "given finite recorded values and finite weights", with the
two-valued-for-a-column against three-valued-for-a-derived-metric asymmetry named rather than
smoothed over and the unchecked-finiteness gap disclosed in the same paragraph. The
`W-STATS-RESAMPLE-THIN` consequence recorded above (it can never fire for a column) is unchanged and
still correct. **One sentence of this entry is false at HEAD** and is corrected rather than deleted:
the closing clause "`E-STATS-RESAMPLE-UNSUPPORTED` still refuses a declared `resample` end to end"
described the code at `c5de085` and stopped being true when H4a task 12 retired that code;
`summarize_step`'s recorded-column branch now emits `resample_draws` under a declared resample, as
the entry "A column's `resample_draws` under a refused (too-few-units) interval is `null`, not the
requested `n`" records. The rest of that paragraph stands as the dated
record it is. The separate finiteness gap it uncovered is **not** closed and keeps its own entry and
its own H4b-2 owner below.

## A column resample is only ever defined given finite inputs, and nothing checks that today

Found during task 11's review (2026-08-15, H4a, `d5f6b6b`). The entry above rules that a column's
`resample_draws` can safely be the requested `n` because a column's draw statistic — a mean — is
"always defined." That is true only given finite `values` and finite weights, and nothing on
`percentile_over_units`'s path checks either:

- **A `nan`/`inf` among `values`** passes straight through every branch — nothing here parses or
  validates `values` for finiteness (that is `summarize_step`'s `_is_numeric`'s job upstream, and
  it never checks `math.isfinite`, only that the value is an `int`/`float` and not `bool`) — and
  produces `Interval(nan, nan)` today, reachable by calling `percentile_over_units` directly:
  `percentile_over_units([1.0, 2.0, 3.0, float("nan")], seed=1, draws=100)`.
- **A weight vector that is individually finite-and-positive can still overflow when summed.**
  `checked_weights`/`usable_weight` gate each weight alone; `[1e308] * 4` passes that gate letter
  for letter (every entry is finite and positive) yet Σw overflows `float`, and the weighted mean
  comes out `nan`.

Both are pinned as *known, unfixed* defects (not correct behavior) by
`tests/test_stats.py::test_a_column_resample_over_non_finite_values_is_a_known_unfixed_gap` and
`tests/test_stats.py::test_a_column_resample_with_an_overflowing_weight_sum_is_a_known_unfixed_gap`
— a future change that fixes either must update those tests and this entry together, rather than
silently making the gap disappear from the record.

**Why `(Interval, int)` is not the remedy either**, confirmed rather than assumed: nothing on this
path treats a `nan`/`inf` draw statistic as a failed draw to filter out — there is no per-draw
survivor check anywhere in `percentile_over_units`, unlike `percentile_of_derived`, which can
observe an individual draw's `compute` fail. Adding a survivor count here would report
`(Interval(nan, nan), n)`: the identical false claim, with an extra field implying it was
checked.

**Owner re-assigned to H4b-2 — clusters through contrasts**
(`docs/superpowers/H4-SCOPING.md` § Decomposition), amended by the H4a whole-branch review
(2026-08-15, `d59316d`) and again by H4b's split into H4b-1 (weights through contrasts, merged) and
H4b-2 (clusters through contrasts, not yet built). The original owner named below — "whichever slice
wires column resample into `summarize_step` (task 12/14)" — **was H4a**, and both tasks landed
without it. That was a deliberate decline, not an oversight: H4a task 14's ledger entry records the
choice, and the disclosure it took instead is live in two places — `stats.summarize_step`'s
docstring, which says in terms that "nothing on this path checks that condition", and `reference.md`
§ Statistical reporting. The two `*_is_a_known_unfixed_gap` tests below still pin it, unmoved by
H4b-1. **Still untouched by H4b-1**: this entry is about `summarize_step`'s per-condition column
resample, not the paired contrast constructions H4b-1 built — the weighted paired forms
(`weighted_paired_t_over_units`, the weighted closure in `paired_percentile_of_derived`) already gate
their weight vectors through `checked_weights`/`usable_weight`, the same finite-and-positive check
`validate` approves the config against, so the unchecked-finiteness gap this entry names does not
reach them. H4b-2 is the successor because a clustered paired construction is the next place a whole
weight vector or value column is drawn as a unit, which is where the same unchecked finiteness
assumption would land.

**Proposed resolution, not attempted here:** whichever slice takes it should validate `values` and
any weight vector for finiteness
before drawing — plausibly reusing `is_measurement_numeric`/`usable_weight`'s existing finite
checks, extended to also catch a weight sum that overflows once accumulated — and route a
failure to a real refusal (`ci95: null`, `resample_draws: null` per the ruling above) rather than
publishing `nan` under a false `resample_draws: n`. This is bigger than task 11's scope: it likely
also affects the unweighted and clustered percentile constructions and the `t_over_units` family,
none of which check finiteness either, and none of which this entry claims to have surveyed.

**AMENDED 2026-08-18 (H4b-2, task 16), re-owned to H4c.** The prediction above — "H4b-2 is the next
place a whole weight vector or value column is drawn as a unit" — did not come true, checked rather
than assumed: the paired clustered *t* H4b-2 built (`paired_t_over_units_clustered`) delegates to
`t_over_units_clustered`, which does no weight arithmetic at all, and the clustered percentile draw
`paired_percentile_of_derived` gained pools rows it does not sum. Neither construction is a place
this entry's finiteness gap can land. Re-owned to **H4c**, the next slice past this one to touch
`summarize_step`'s column path.

**AMENDED 2026-08-18 (H4c, task 20) — measured rather than inherited, and the premise is falsified
for one of the two new constructions it names.** H4c's unpaired *t* forms sum per-side value columns
and compute per-side variances, which made the premise likelier here than at H4b-2 — so it was
checked rather than assumed. Probed directly at this commit:

```
welch_t_over_units([1.0, inf, 3.0], [1.0, 2.0, 3.0])  -> Interval(low=nan, high=nan, method='welch_t_over_units')
welch_t_over_units([1.0, nan, 3.0], [1.0, 2.0, 3.0])  -> Interval(low=nan, high=nan, method='welch_t_over_units')
welch_t_over_units_clustered(...)                     -> Interval(low=nan, high=nan, method='welch_t_over_units_clustered')
cohens_ds([1.0, inf, 3.0], [1.0, 2.0, 3.0])            -> None
cohens_ds([1.0, nan, 3.0], [1.0, 2.0, 3.0])            -> None
```

**`welch_t_over_units[_clustered]` does not refuse a non-finite value and does not raise — it returns
an `Interval` whose `low`/`high` are `nan`.** That is neither this entry's "plausible but wrong"
shape (a `nan` is visibly not a number, not a number that looks like one) nor a clean refusal
(`ci95: null`) — it is a third shape this entry did not name, and it reaches `run.yaml` as written
today: `[interval.low, interval.high]` serializes `nan` through PyYAML's own `.nan` literal rather
than raising. `cohens_ds` returns `None`, but by coincidence of comparison semantics rather than a
deliberate check: `pooled` becomes `nan`, `sd = sqrt(nan)` is `nan`, and `nan > 0` is `False` in
Python, so the `if sd > 0` guard reads as a refusal without being one.

**Ruled: re-decline, not fix here — the premise is confirmed likelier but the fix is a task, not a
line.** Closing it means validating both value vectors (and, for the clustered forms, the per-cluster
sums `_cr1_variance` accumulates) for finiteness before any arithmetic, on the same
`is_measurement_numeric`/`usable_weight` precedent the original entry proposed, and routing the
failure to a real refusal rather than a `nan`-valued `Interval` reaching the record. That is out of
this task's scope (a claim/decline pass, not a construction task), and threading it through the
unpaired forms while also fixing the pre-existing `t_over_units` family (which this probe did not
re-check and which the original entry already flagged as unsurveyed) is more than one task's worth of
work. **Owner: H4d**, the last remaining slice whose surface is the `statistics` block — the same
terminal reasoning the `report_by`/`resample_columns` entry below carries.

**MEASURED 2026-08-19 (H4d, task 23) — the permutation half of the same finiteness surface, claimed;
the resample half named above stays open.** H4d recomputes metrics over relabelled tables, which is
the identical unchecked-finiteness surface one construction over, so the premise was measured rather
than inherited a fourth time. Probed directly at `a207702`:

```
permutation_over_units([1.0, 2.0, 3.0, float('nan')], ['of','of','against','against'], 'of', seed=1, n=100)
  -> 0.009900990099009901
permutation_of_derived({'a': {'y': 1.0}, 'b': {'y': float('inf')}, 'c': {'y': 2.0}, 'd': {'y': 3.0}},
                        {'a':'of','b':'of','c':'against','d':'against'},
                        lambda t, l: sum(r['y'] for r in t) / len(list(t)), seed=1, n=100)
  -> (None, 100)
```

`permutation_of_derived` already drops a `nan` draw — its survivor discipline checks `math.isnan` —
so the derived path was clean before this task touched it. `permutation_over_units` had no such
check: an unguarded `nan` observed statistic makes every `>=` comparison `False`, reported as
`p_value = 1/(n+1) = 0.0099...` — a small, real-looking p-value from a table nobody could compute a
mean of, worse than the existing `Interval(nan, nan)` this filing's original entry names for the
resample path. **Claimed**: `stats._label_delta` — the one function both the observed statistic and
every draw's recomputation pass through, for both `permutation_over_units` and
`permutation_over_units_clustered` — now returns `None` whenever the computed delta is `nan`, the
same honest absence an empty arm already gets. Re-probed after the fix: both calls above now return
`None`. Pinned by
`tests/test_stats.py::test_a_permutation_over_units_with_a_nan_value_reports_no_p_value_rather_than_a_false_one`,
with a mutation removing the guard (the assertion then reads `0.009900990099009901`, a value rather
than a crash).

**The resample (column-bootstrap) half this entry was originally about is untouched and stays open**
— `percentile_over_units` and its siblings still have no finiteness check, and
`tests/test_stats.py::test_a_column_resample_over_non_finite_values_is_a_known_unfixed_gap` and
`::test_a_column_resample_with_an_overflowing_weight_sum_is_a_known_unfixed_gap` are unchanged and
still pin it. This slice narrowed the filing to the resample half only; it is not closed, and H4d
being the last slice whose surface is the `statistics` block means no further slice can inherit it —
**it stays open with no owner**, which is worth stating plainly rather than leaving the heading above
to imply otherwise.

## `statistics.resample.stratify_by` is checked by `validate` and honoured by nothing — CLOSED

Found during task 14's review (2026-08-15, H4a, `ce2f2db`). `validate._check_resample` refuses a
`stratify_by` naming an undeclared attribute (§ Validation's *Resample strata exist* /
*Resample strata survive clustering* rows), and `cli._resolved_resample` normalizes and carries it
on `resample_spec`, so a config declaring it validates clean and looks accepted. Nothing downstream
reads it: `percentile_over_units`/`percentile_over_units_clustered` accept a `strata` parameter
(built and verified in tasks 9–10) but task 14's column-resample wiring does not pass one, and
`percentile_of_derived` has no `strata` parameter to pass one to at all. So a declared
`resample.stratify_by` changes no arithmetic anywhere today — a stratified bootstrap by name, an
unstratified one by construction.

**Why task 14 didn't close it, deliberately rather than by oversight.** Threading `strata` into
the column path alone (the cheaper of the two, since the construction already exists) would put two
intervals in one `aggregated` block computed under different designs — a stratified column's
`percentile_over_units` beside an unstratified derived metric's `percentile_of_derived` — with
`method` reading identically either way (`percentile_over_units` doesn't encode whether `strata`
was passed) and nothing else in the record to tell a reader which is which. That is worse than the
status quo, not better: today both paths agree (neither honours it), so no divergence is visible
even though neither is doing what the config asked. Refusing the combination outright was
considered and rejected too — `reference.md` § Weighted samples documents `resample.stratify_by`
with a worked YAML as an accepted, ordinary declaration, so refusing it retroactively is a document
change `CLAUDE.md` puts far outside a single task's scope.

**What is owed, and by whom.** Threading `strata` into `percentile_of_derived` — recomputing
`aggregate` on a within-stratum resample rather than an unconditional one — is a real construction,
not wiring: the derived case has no per-unit value to stratify directly, so the draw itself has to
change shape (stratified indices into the collapsed table, then the same per-draw `compute` call).
Only once that exists can a slice safely wire `strata` into the column path too, landing both
together so the two constructions never disagree about whether stratification happened. Until then,
`stratify_by` remains resolved and carried on `resample_spec` but read by no interval construction —
a fact stated in `_resolved_resample`'s own docstring and in `cli.py`'s comment beside the primary
`summarize_step` call, so a future reader hits the citation before hitting the gap.

**AMENDED 2026-08-15 (task 14 merge-gate review): the gap is now DISCLOSED at run time, not only in
this record.** The review that found this entry also found the option set this entry's "Why task 14
didn't close it" paragraph weighed (threading, refusing, shipping the asymmetry) incomplete — a
run-time warning is neither a divergent construction (the threading option) nor a document change
(the refusal option), and is the cheap, user-visible route every other unbuilt-but-declared gap in
this project takes. Before this amendment a declared `resample` moved nothing, so a `stratify_by`
beside it doing nothing was consistent with the rest of the declaration also doing nothing; after
task 14 landed, `resample` visibly moves a column's interval, which makes the silence beside
`stratify_by` a materially worse gap than the one this entry originally described — six of seven
non-null `resample` declarations in `docs/feasibility-llm-growth-studies.md` carry a `stratify_by`.
`cli.command_run` now warns `W-STATS-RESAMPLE-STRATIFY-UNHONOURED` once per run whenever `resample`
is declared with a non-empty `stratify_by`, naming every stratum and stating plainly that no
construction in this build honours it — registered in `reference.md` § Warnings core reports. The
gap itself (no construction stratifies either path) is unchanged and still owed to whichever slice
gives `percentile_of_derived` a `strata` parameter, per this entry's own "What is owed, and by whom"
paragraph; only its visibility changed.

**CLOSED 2026-08-15 (H4a task 15).** `percentile_of_derived` now takes a `strata` parameter — the
"What is owed, and by whom" paragraph's own construction: it draws unit **keys** with replacement
within each stratum, preserving each stratum's key count, rather than drawing a per-unit value the
way `percentile_over_units` does, since a derived metric has no per-unit value of its own. Task 15
landed that alongside wiring `strata` into the column path (`percentile_over_units`/
`percentile_over_units_clustered`) in the same commit, exactly as this entry's "Only once that
exists can a slice safely wire `strata` into the column path too, landing both together" said —
`cli.command_run` composes one `resample_strata` mapping (the cross of every declared
`stratify_by` name, a unit missing a name joining a stratum of its own labelled from the absence
rather than being dropped) and threads it into both `summarize_step` call sites that resample at
all, so a declared `stratify_by` now moves a recorded column's interval and a derived metric's
interval the same way in the same table. `W-STATS-RESAMPLE-STRATIFY-UNHONOURED` is retired — the
gap it disclosed no longer exists — and its `reference.md` § Warnings core reports row and its two
`tests/test_cli.py` pins are removed rather than kept as dead code warning about nothing.

## `cli.resample_strata`'s composed label can collide with a real attribute value, or with itself

Found during task 15's review (2026-08-15, H4a). `cli.command_run` composes one stratum label per
unit for a declared `statistics.resample.stratify_by` naming more than one attribute: the names'
values joined by `|`, with a missing name rendered `<absent>` rather than dropping the unit
(`resample_strata`, next to `unit_attributes`). Neither the separator nor the sentinel is a reserved
character — both are ordinary printable text a unit's own attribute value could equally contain —
so two distinct designs read back as one stratum:

- **Sentinel collision.** A unit whose attribute is genuinely present and equal to the literal
  string `<absent>` composes to the identical label a unit MISSING that attribute would, so the two
  populations are pooled into one stratum rather than kept apart.
- **Separator collision.** `stratify_by: [a, b]` with one unit's `a = "x|y", b = "z"` and another's
  `a = "x", b = "y|z"` both compose to `"x|y|z"` — two different (a, b) pairs joining into one label.

Neither is refused by `validate` (`_check_resample`'s rows check that each named attribute exists
and survives clustering, not what values it may hold) nor detected at run time — `stats.py` receives
only the composed label and has no way to tell a genuine collision from an intentional one. This
also weakens the "cannot disagree" guarantee `E-STATS-RESAMPLE-STRATIFY-VARIES`'s dual listing makes
(`stats.percentile_over_units_clustered`'s inline re-implementation of `units
.stratum_varies_within_cluster`'s equality): that guarantee was built for a single, uncomposed name
read straight off the roster, where both checks see the identical raw value. A composed, multi-name
`stratify_by`'s cross-label reaches `percentile_over_units_clustered` already transformed by
`cli.py`, so the run-time check's own `stratum is None` branch is rarely if ever what distinguishes
a missing unit there in production — `cli.py`'s sentinel already has, before `stats.py` sees
anything. `reference.md` § Errors validate reports and § Errors core raises both amend their
`E-STATS-RESAMPLE-STRATIFY-VARIES` rows to state this narrowed scope rather than the unqualified
claim task 10 wrote it under.

**Not fixed here.** An unambiguous encoding (a delimiter and sentinel neither can appear in a
user's own attribute values, or a structured label carrying the individual attribute values rather
than a joined string) is a bigger change than a doc-and-comment fix: `stats.py` sees "one label per
unit and never learns how many attributes made it" by design (task 15's own brief), and any fix
preserving that would need to move the collision-avoidance into the encoding itself. Left as an
acknowledged, unaddressed gap — a real value or a real combination has to collide for it to bite,
and the near-unique-attribute case that would make an attribute value equal to `<absent>` a live
risk (an identifier column, say) is already a poor choice of `stratify_by` on other grounds (task
15's own constant-pool refusal in `percentile_of_derived` and `percentile_over_units` both refuse a
near-unique stratum as uninformative before this collision would ever surface in an interval).

## A column's `resample_draws` under a refused (too-few-units) interval is `null`, not the requested `n`

Found during task 14's implementation (2026-08-15, H4a, `ce2f2db`), reviewing the brief's own Step 1
test against the ruling in "A column metric's `resample_draws` records the requested `n`, not a
survivor count" (this file). That entry's own text rules: **"`resample_draws` is `null` whenever
`ci95` is `null`, for any of the three reasons [`percentile_over_units` returns `None`]."** The brief's fourth
test (`test_a_column_below_two_units_reports_no_interval_under_resample`) asserted
`got["pred"]["resample_draws"] == 2000` for a one-unit column under a declared resample — an
interval that is `None`, so `ci95` is `null` — which is the exact case the ruling calls out by name
and the exact incoherence its own prose warns against: "recording the requested `n` there would
assert survivor evidence for a refused interval." This is the "one test pinned wrong behaviour as
correct" the task's own "Where this goes wrong" guidance named without identifying which one.

**Resolution:** implemented per the ruling. `summarize_step`'s emitted `resample_draws` is
`draws if interval else None` (not unconditionally `draws`) whenever `resample_columns` is true and
a `seed` is given; absent entirely otherwise. The test was rewritten as
`test_a_column_below_two_units_reports_a_null_draw_count_under_resample`, asserting the key is
present (a resample was declared and attempted) and `None` (nothing was produced to describe a draw
count for) — distinct from the absent-key case, which means no resample was ever asked for. Both
mutations — dropping the `if interval else None` guard, and gating the key's presence on anything
but `resample_columns and seed is not None` — are pinned by this test and by
`test_the_undeclared_resample_shape_is_pinned_absent_key` respectively; both were run and confirmed
to fail before being reverted.

## `percentile_of_derived` reported a zero-width interval for a near-unique stratum — CLOSED; and a report_by asymmetry deferred beside it

Found during task 15's review (2026-08-15, H4a). Two related findings, recorded together because
the fix for the first is what makes the second visible rather than merely theoretical.

**Finding 1, CLOSED.** `percentile_of_derived`'s new stratified branch (this task's own construction)
shipped with no constant-pool refusal, unlike its two siblings: `percentile_over_units`'s stratified
branch refuses when every stratum's own (value, weight) pairs are all identical (task 9's own first
❌), and `percentile_over_units_clustered` refuses when every stratum's own clusters are pairwise
identical in content (task 10 shipped the identical hole once, closed the same way). A near-unique
`stratify_by` — one stratum per unit, which validates clean — makes every draw of a singleton
stratum pick the identical one key every time, so a deterministic `compute` returns the identical
value on every draw: `Interval(x, x)` at `resample_draws: 2000`, indistinguishable from a real
2000-draw interval, reachable end to end with no warning. The extra sting: the recorded column
beside it (which does have the refusal) reports `ci95: null` for the identical design, so a reader
sees one metric refuse and its neighbour publish a point as if it were an interval. Fixed by adding
the same content-based check — every key in a stratum carrying the identical recorded row, a
singleton stratum being the trivial case of that — before any draw is taken, mirrored from its two
siblings and pinned by three tests (`test_percentile_of_derived_refuses_the_singleton_stratum_case`,
`test_percentile_of_derived_refuses_a_multi_key_stratum_of_identical_rows_too`,
`test_percentile_of_derived_does_not_over_refuse_one_constant_stratum_among_others`), each mutated
and confirmed to fail before being reverted.

**Finding 2, deferred — owed to whichever slice hardens `report_by` (`H4 Statistics`, per this
file's existing "A `report_by` whose every level is empty…" entry, which names the same owner).**
**Live on C1–C3, still untouched by H4b-1**: all three of this analysis's payoff configs declare
both `statistics.report_by` and a `resample`, so the gap this finding names — a level's own
recorded-column interval stays `t_over_units` rather than honouring `resample_columns` — sits on
their own record. `docs/feasibility-llm-growth-studies.md` § Executability on this build's H4b-1
entry qualifies "no remaining core-side blocker" against exactly this finding rather than treating
`report_by` as settled.
`cli.command_run`'s `report_by` level call (`level_summary = summarize_step(...)`) does not pass
`resample_columns`, so a level's own recorded-column interval stays `t_over_units` even under a
declared `resample`; `strata` (this task's own thread) reaches only that level's *derived* metrics
there, because a derived metric has no unresampled fallback and is always resampled when a `seed` and
a callable exist, `resample_columns` or no. Under a declared `resample` with a `stratify_by`, a
`report_by` level block therefore holds an unresampled column interval beside a *stratified*
`percentile_over_units` derived one — two different designs in one table.

**Adjudicated NOT the same class task 14 declined to create, and that is why it is deferred rather
than fixed here.** Task 14's asymmetry was two IDENTICAL `method` strings computed under different
designs with nothing in the record to tell them apart. Here the two blocks carry DIFFERENT `method`
strings (`t_over_units` beside `percentile_over_units`) and differ on whether `resample_draws` is
present at all — `run.yaml` already discloses the difference, it just doesn't explain it. It also
predates this task: the level path never got `resample_columns` in task 14 either, so this is not a
regression task 15 introduced, only one task 15's own `strata` thread reaches one layer further into.
The fix is a task, not a line: a level's own two-valued `resample_draws`, a level-thin
`min_honest_draws` check (a level with fewer units than the floor should refuse the same way the
whole-condition case does), and end-to-end tests crossing `report_by` with a declared `resample` —
not something to improvise inside this task's already-amended scope.

**AMENDED 2026-08-15 (H4a task 19 review): the disclosure premise above was written before task 17
landed the resolved-`resample`-beside-every-interval recording, which changed what a level's own
column block actually carries — re-checked against `run.yaml` as this task now writes it, not
against what task 15 observed three tasks earlier.** A level's recorded-column block today (verified
end to end, `report_by: [cohort]` crossed with a declared `resample`) is:

```yaml
resample: {method: bootstrap, n: 500, stratify_by: []}
method: t_over_units
# no resample_draws key at all — ABSENT, not null
```

— the resolved `resample` declaration now sits beside `method: t_over_units`, where before task 17
it sat beside nothing at all (the key did not exist for a recorded column until task 17 threaded it
onto every metric block `resample_spec["declared"]` reaches, level blocks included). **The disclosure
argument still holds, and holds on the same two signals as before plus one more, not on a weaker
one:** `method` is unchanged (`t_over_units` beside `percentile_over_units` remains the read a
`report_by` + `contrasts`-savvy reader already has to make), `resample_draws` is unchanged in kind
(present-with-a-count for the column that honored `resample_columns`, absent for the one that
didn't — the same absent/null/count three-way split `reference.md` § Statistical reporting documents
everywhere else in the run, not a new or contradictory reading invented for this one block). The new
element — a `resample` echo sitting beside `t_over_units` with no `resample_draws` — reads as
"declared, not the basis of this interval" to a reader who already holds that convention, not as a
contradiction: it is the identical shape `test_no_resample_block_is_recorded_when_none_was_declared`
already established for an undeclared run's OWN unresampled columns (absent `resample_draws`, no
claim of a resolution attempted here), transplanted to a column that sits beside a sibling
declaration it did not use. Nothing about task 17's own change makes the level path lie; it makes
the level path echo a declaration whose relevance to that one block a reader must still work out from
`method`, which is exactly the "discloses, does not explain" gap this entry already named as the
open half of the fix. The deferral, its owner, and the fix list above are unchanged by this
amendment.

**DECLINED 2026-08-18 (H4b-2, task 16), re-owned to H4c.** Live on C1–C3 still, unchanged by this
slice: the gap is created by neither a weight nor a cluster, and `docs/superpowers/H4b-SCOPING.md`
§ 12 warned against folding a `report_by` hardening question into a sibling contrast-family slice for
exactly this reason. Owner moves from the general "H4 Statistics" to **H4c** by name, the direction
the scoping recommends, rather than staying a description any of H4's remaining slices could read as
its own.

**RE-DECLINED 2026-08-18 (H4c, task 20) — another decline in the same unbroken line, and the
terminal one named as such.** Still live on C1–C3, and confirmed unrelated to this slice's own
surface: it is created by neither a weight, a cluster, nor a pairing derivation —
`cli.command_run`'s `report_by` level call still does not pass `resample_columns` through to
`summarize_step`, exactly as H4a task 15 left it, and nothing H4c built touches that call site. This
is the only one of the five filings this task inherited that is genuinely unrelated to the unpaired
contrast constructions.

This entry has now been carried forward, unbuilt, across H4a's own review, H4b-2, and this slice —
each declining in turn rather than fixing it, on grounds that keep being correct (it is not that
slice's surface) and keep leaving the entry owned by a description rather than a name. Naming another
description here would repeat the exact habit `CLAUDE.md` § Habits that cost real work calls out: "a
ledger line saying 'filed' is not a filing" and a deferral pointing at a closed slice reads as live
work nobody holds. **Owner: H4d**, named rather than described, because it is the last remaining
slice in the charter whose surface is the `statistics` block at all.

**H4d is terminal for this entry.** After H4d there is no further statistics slice in the charter for
a fifth decline to point at. If H4d does not close it, the correct move at that point is not another
deferral — it is converting this into a documented, permanent limitation: a § Errors or § Validation
row (or a `reference.md` § Statistical reporting sentence, if no code check is warranted) stating
plainly that a `report_by` level's recorded-column interval does not honour a declared
`resample_columns`, so a reader stops expecting a fix that the charter no longer has a slice to
deliver.

**CONVERTED 2026-08-18 (H4d, task 24) — Finding 2 is now a documented permanent limitation.** The
entry's own terminal instruction was that *"the correct move at that point is not another deferral —
it is converting this into a documented, permanent limitation"*, and H4d is the last slice whose
surface is the `statistics` block. `reference.md` § Statistical reporting now states plainly that a
`report_by` level's recorded-column interval does not honour `resample_columns`, with the
disclosure that distinguishes the two constructions in the record and the reason a level joins no
correction family. **The code is unchanged**, which is what "limitation" means here: this is not a
fix and must not be read as one. `W-STATS-REPORTBY-THIN`'s whole-roster-versus-arm gap is a
*different* half of this entry and is left as § What isn't a repeat already records it.

## ~~The contrast path discloses nothing about its resample~~, ~~and `paired_percentile_of_derived` never got the zero-width sweep~~ (CLOSED — the first half by H4d task 22, the second by H4b-2 task 9)

Found by the **task 16 review** (H4a, `2026-08-15-resample-honoured`), at commit `b06079c`; a third
finding added below by the whole-branch review at `d59316d`. Three
findings, all **deferred with a named owner** (`docs/superpowers/H4-SCOPING.md` § Decomposition; a
third finding was appended by the H4a whole-branch review, and the owner named here was "H4's
contrast-side hardening", a description rather than a slice, until the same review) — because all
are disclosure/refusal gaps on a path task 16 widened rather than created, and none is a regression.
**Re-owned**, `H4b` having since split into H4b-1 (weights through contrasts) and H4b-2 (clusters
through contrasts): Finding 2 is the general form of the gap H4b-1 task 5 closed the reachable
instance of — see the entry below this one, `CLOSED by H4b-2 task 9 — a stratified paired draw
could publish a zero-width contrast interval`, which gives `paired_percentile_of_derived` the
content-based degenerate refusal it lacked, over both the clustered and unclustered draws and the
stratified and unstratified ones as one check.
Findings 1 and 3 are general contrast-disclosure gaps that neither weights nor clusters created, so
they stay with the nearer of the remaining contrast-family slices rather than being split a third way.

**RE-OWNED 2026-08-18, after H4b-2 merged — Findings 1 and 3 pass to H4c.** H4b-2 has landed and
closed Finding 2; the sentence above named it as the nearer slice, and it is no longer a slice that
will run. H4c — the unpaired contrast constructions — is now the nearest, and it touches the same
`_comparison_step_blocks` disclosure surface both findings are about. Re-ownered by name rather than
left reading as live work nobody holds, per `CLAUDE.md` § Habits that cost real work.

**Finding 1 — a declared `resample` can silently remove a column contrast's interval.** Task 16
routes a recorded column's contrast through `stats.paired_percentile_of_derived` under a declared
`statistics.resample`. When the surviving draws fall below `min_honest_draws(confidence)` — a ragged
column, a degenerate closure — the construction returns `interval=None` and the entry publishes
`ci95: null` where it previously published a `paired_t_over_units` interval over the same
`col_keys`. **Nothing warns.** `W-STATS-RESAMPLE-THIN` is emitted from exactly one site,
`cli.py`'s per-condition `summarize_step` loop; `_comparison_step_blocks` emits no resample finding
at all, so neither `vs_baseline` nor `results.contrasts` can say a contrast's interval was lost to a
thin pool rather than to a thin intersection. Pre-existing for **derived** contrasts, which have had
this shape since they were built; task 16 widens it to every recorded column under a declared
`resample`. The fix is a task, not a line — a contrast-scope thin finding needs a `where` that names
the comparison (`cond:<index>` / `contrast:<id>`, which `_comparison_step_blocks` already carries as
`where_id`) and a registry row, and it should be built alongside Finding 2 rather than separately.

**Finding 2 — CLOSED by H4b-2 task 9.** ~~`paired_percentile_of_derived` carries none of the
content-based degenerate refusals its three siblings now have.~~ `percentile_over_units` (strata
branch), `percentile_over_units_clustered` (cluster-content branch) and — as of task 15, recorded
one entry above this one — `percentile_of_derived` each refuse a draw whose structure cannot vary, on
the stated authority of `reference.md` § Statistical reporting: "a zero-width 95 % interval is not
[honest]; reporting a point with no interval is honest." ~~The paired construction has no such
check.~~ It now does: `_drawable_content` and the check built around it in
`paired_percentile_of_derived` (H4b-2, task 9) refuse a draw whose every drawable thing within every
stratum carries the same pair of rows — a key's row pair by default, a whole cluster's sorted
multiset of row pairs once `clusters` is given — covering the stratified/unstratified and
clustered/unclustered cases as one expression rather than a fourth sibling refusal built separately.

**Scoped by the whole-branch review (`d59316d`): each of those three refusals is on its stratified
or clustered branch, and none of them is a general "core never publishes a zero-width percentile
interval" guarantee.** Probed directly: an **unstratified** constant pool still returns
`Interval(5, 5)` from `percentile_over_units` and `(Interval(5, 5), 200)` from
`percentile_of_derived`; the same pool with `strata` (or with `cluster_by`) returns `None`. That is
not a regression — `t_over_units` over the identical column returns `Interval(5, 5)` too — and it
is defensible on its own terms, since an unstratified bootstrap of a constant column genuinely has
no sampling variance. It is recorded because within one run a constant column is refused with
`stratify_by` declared and published without it, and a reader inferring the general guarantee from
the sentence above would be wrong.
Verified end to end at `b06079c`: a column recorded identically under both conditions
(`tests/test_cli.py`'s `_AGGREGATE_STEP`, whose `pred = float(i)` ignores `cfg`) under
`resample: {method: bootstrap, n: 2000}` publishes
`method: paired_percentile_over_units, delta: 0.0, ci95: [0.0, 0.0], ci95_corrected: [0.0, 0.0]`.

**Why this is deferred and not a task-16 defect.** It is **not a regression**:
`paired_t_over_units([0.0] * 40)` already returns `Interval(0.0, 0.0)`, so the same design published
the same zero-width interval before task 16 under a different `method` string. It is also **not** the
"plausible but wrong" case `paired_percentile_of_derived`'s own docstring warns about — that one is a
*nonzero* point-estimate delta beside a zero-width interval at zero, produced when a shared closure
cancels across two identical tables; here the delta is `0.0` beside it, so the record is internally
consistent and a reader can see what happened. Task 16's own decision to pass `_column_mean` twice is
sound for the same reason: the two tables are the two conditions' own collapsed data, not one table
seen twice, so nothing cancels. ~~What is owed is consistency — the paired construction is now the
fourth reachable from a recorded column and the only one the zero-width sweep never touched, and the
sweep should finish rather than stop at three.~~ **CLOSED by H4b-2, task 9**: the paired
construction now carries the identical content-based check its three siblings do, so the sweep
covers all four.

**Finding 3 — a contrast entry carries no resolved-`resample` echo, while every `aggregated` block
beside it does.** Filed by the **H4a whole-branch review** (2026-08-15, at `d59316d`), which found
the gap real and found that it had never been filed: H4a task 17's ledger entry recorded it as
"registered against H4's contrast-side hardening, same owner as task 16's filed items", and no such
amendment was ever made to this entry. The ledger is tracked, so the ruling was not lost, but
`CLAUDE.md` names this file as the place to look before filing a "new" gap, and it was not here.

The gap, confirmed by the review by running a config, and re-confirmed here at the construction
site: under a declared `statistics.resample`, a `vs_baseline` entry reports
`method: paired_percentile_over_units` with no `resample` block beside it, while every `aggregated`
metric block in the same `run.yaml` carries the resolved `{method, n, stratify_by}` echo task 17
added. `_comparison_step_blocks` builds each entry as a literal
`{delta, n_paired, method, ci95, cohens_d, correction}` mapping and takes no `beside_n` parameter
at all, so there is no route by which the echo could reach it. `cli.py` merges `resample_beside` into
`weighted_beside`, which reaches `summarize_step`'s `beside_n` and so the per-condition blocks;
`_comparison_step_blocks` builds its entries by another route and receives no such mapping. So a
reader can see what a condition's own interval rests on and cannot see it for the contrast between
two conditions — which is the half `reference.md` § Statistical reporting's "so the number is never
the result of an undocumented default" reason applies to equally.

**Same owner as Findings 1 and 2, and it should be built with them:** all three are contrast-path
disclosure gaps, and a `where` that names the comparison is the thing Finding 1 needs and this one
would reuse. Not a regression — no contrast entry ever carried the echo, the echo itself being H4a
task 17's own addition.

**DECLINED 2026-08-18 (H4b-2, task 16), re-owned to H4c.** Finding 1 is a contrast-scope thin
finding needing a `where` and a registry row; Finding 3 is a contrast entry carrying no resolved-
`resample` echo. Neither is a cluster question, and building either would mint a warning identifier
and a § Warnings row this slice did not scope — H4b-2 added a third `method` spelling to the
contrast entry (`paired_percentile_over_units_clustered`) and no new disclosure surface. Both stay
deferred, re-owned to **H4c**.

**RULED 2026-08-18 (H4c, task 20) — the "no new disclosure surface" ground does not transfer, and
this task rules on both findings rather than deferring both again unchanged.** H4c adds four
`method` spellings (`welch_t_over_units[_clustered]`, `unpaired_percentile_over_units[_clustered]`)
and a new record shape (`n_of`/`n_against` in `n_paired`'s place), so the ground H4b-2 declined on —
that nothing about the contrast entry's disclosure surface changed — is false here, checked rather
than carried.

**Finding 3 — CLAIMED as still real and now unambiguously scoped to the shape this slice built.**
Verified against the current `_comparison_step_blocks`: every unpaired and every paired arm still
builds its entry as a literal mapping with no `beside_n`/`resample_beside` parameter, so a `run.yaml`
entry for `welch_t_over_units` or `unpaired_percentile_over_units_clustered` carries no resolved-
`resample` echo beside it, identically to the paired forms the original finding named. Not fixed
here — the fix is a `beside_n`-shaped parameter threaded through both call sites in
`_compute_vs_baseline`/`_compute_declared_contrasts`, which is a construction task rather than a
claim/decline pass. **Owner: H4d.**

**Finding 1 — RE-DECLINED, same reasoning, same owner.** A contrast-scope `W-STATS-RESAMPLE-THIN`
needs a `where` (`_comparison_step_blocks` already carries `where_id`) and a new § Warnings registry
row — warning-registry work this task does not scope. Verified still live: an unpaired column
contrast whose resample draw falls below `min_honest_draws` publishes `ci95: null` with nothing
warning that the loss came from a thin pool rather than a thin `n_of`/`n_against`, the identical gap
the original finding named for the paired case. **Owner: H4d**, the same slice Finding 3 and the
`report_by`/`resample_columns` entry below are owned by — the last remaining slice whose surface is
the `statistics` block, so a fifth deferral past it is not available.

**CLAIMED 2026-08-19 (H4d, task 22) — both findings, in the same commit.** Finding 3:
`_comparison_step_blocks` now takes a `resample_echo` parameter (`_resolved_resample`'s own
`{method, n, stratify_by}` dict, the same one `cli` merges into every `aggregated` block as
`weighted_beside["resample"]`), threaded through `_compute_vs_baseline` and
`_compute_declared_contrasts`, and written onto every metric entry — derived and column, paired and
unpaired alike — absent, not null, when nothing is declared. Finding 1: `W-STATS-CONTRAST-RESAMPLE-THIN`
is minted, emitted from `_comparison_step_blocks` with `where_id` (`cond:<index>` / `contrast:<id>`)
whenever a resampled comparison's `draws_used` falls below what was requested, distinct from
`W-STATS-CONTRAST-THIN`'s `limits.min_reported_n` path so the two cannot collide on one `where`.
Verified by a direct call with a 3-unit fixture, two of whose units carry `nan` for the recorded
column: most of 400 bootstrap draws fail `math.isnan` and are dropped, landing below the 80-draw
floor and publishing `ci95: null` alongside the new warning. Pinned by a mutation that suppresses the
emit (`if False and resampled is not None...`): the assertion on the warning's presence fails by a
named `AssertionError`, not a crash, and the mutation is reverted in the same commit.

## `reference.md` § *How a metric becomes a number* is cited across the repo and does not exist

Found by the **H4a whole-branch fix pass** (2026-08-15, at `d59316d`), while adding a citation to
that section and checking that its anchor resolved. It does not: **no heading of that name exists**
in `reference.md` or in any of the four documents, and no commit in this repo's history ever
removed one (`git log -S` over `docs/reference.md`). The name is nonetheless in wide, consistent
use — **eighteen files name it**: five sites in `src/` (four in `stats.py`, one in `validate.py`),
both scoping documents, four plans, four specs, five files of the development record (this pass's
own report among them), and this file, whose `W-STATS-AGGREGATE-FAILED` entry proposes to "add
`resample_draws` to the § How a metric becomes a number derived-metric shape once that section next
changes". Nothing anywhere records it
as a section that is *owed*; every use reads as a citation of something already written. Two further
instances were written by this pass and corrected before they landed.

**Where the cited material actually lives, checked by locating the quotations rather than assumed:**
`stats.py`'s "can do only for a metric it knows how to compute" is under `#### What isn't a repeat`;
the `resample_draws` `null`/`0`/*n* scheme and the recorded-column paragraph are under
`### Statistical reporting` → `#### The unit table is the inference base`. So the phantom name spans
at least two real sections, which is why this is not a `sed`: each site has to be read to see which
one it leans on.

**Two readings, and the fix differs.** Either the citations are misaddressed and should each be
repointed at the real section — or the repo has been describing a section `reference.md` genuinely
lacks, in which case the fix is to write it: a single place saying how a metric gets from a step
return or an `aggregate` to a value, a basis, and an interval, which is what those eighteen files
have been pointing at. The second is the more likely reading given how uniform the usage is, and it
is a documentation change of real size, which is why nothing is repointed here.

Not a behaviour defect, and no reader is misled about a *rule* — every quoted sentence is true and
resolves somewhere in `reference.md`; only the address is wrong. Filed because `CLAUDE.md`
§ Documentation conventions makes section citation the one durable way to point between files
("never by line number"), and a cited section that does not exist is precisely the failure that
convention exists to prevent.

**Owner: unassigned, and explicitly declined once more.** H4b-1 touched § Statistical reporting
directly — minting the weighted-contrast `method` vocabulary, the record shape, and the two weighted
paired constructions — and did not write § How a metric becomes a number; task 9's own docstring
inherits a citation of it from `paired_t_over_units` rather than resolving it. Any slice editing
`reference.md` § Statistical reporting can settle which reading is right; H4b-2 is next to touch
that material.

**DECLINED 2026-08-18 (H4b-2, task 16), a third time — in writing, so a fourth silent pass does not
happen.** H4b-2 edited two docstrings citing this phantom section (`stats.py`'s
`paired_t_over_units_clustered` and `paired_percentile_of_derived`) without resolving either, the
same shape task 9 left. Writing § How a metric becomes a number is a documentation change of real
size over material a statistics slice edits but does not own describing — deciding between the two
readings § Documentation conventions requires is not H4b-2's decision to make in passing. **Owner:
explicitly unassigned** — no slice in the spine is named "documentation", and inventing one here
would be the same maintenance-obligation-nobody-owns mistake this file's own conventions warn
against. Re-check on the next slice that edits `reference.md` § Statistical reporting, still.

## OPEN — `technical_n` is a whole-roster figure beside a test-partition `n`

`cli._cond_beside_n` withholds `technical_n` from a condition whose roster was narrowed to
an arm, on the stated grounds that "copying a whole-roster figure onto a subset states a
spread nobody computed over that subset". A `data.units.holdout` narrows the same way and
the same withholding is not applied: `technical_n` is `{min, max, median}` over the whole
roster's measurement counts, and under a holdout it would sit beside an `n` counting the
test partition alone.

**Deliberately not closed by H3d.** It needs `data.units.measurements` *and*
`data.units.holdout` declared together, which no config in
`docs/feasibility-llm-growth-studies.md` does, and closing it inside H3d's task 15 would
add an unbudgeted behaviour change to the task the scoping already names as the one most
likely to ship wrong.

**Correction (H3d task 15, `fa85b26`), replacing the "mechanism is cheap" sentence above:**
task 15 narrowed `_condition_beside_n`'s call into `_cond_beside_n` to pass `eval_roster`
(the holdout's test partition) as the third argument in place of the whole `roster`. Both
the `cond_roster` argument and that third argument now derive from the same narrowed
value, so the identity check `cond_roster is roster` can no longer distinguish "narrowed
to an arm" from "narrowed to a holdout's test partition" — it never could tell those apart
by the roster's *content*, but before this task the identity reference was still the
whole roster, and the mechanism only worked by accident of that specific pairing. Closing
this gap now needs a fourth parameter carrying the un-narrowed roster as a separate
identity reference (or the whole roster threaded alongside), not merely reading the
existing third argument.

**Found by:** H3d, Task 2 (documents-only). **Owner:** whichever slice next changes
`_cond_beside_n`, or H3c-3 if it retrofits the holdout to cells first — re-owner this entry
when that slice finishes rather than leaving it pointing at a closed one.
**Severity:** Minor. Both numbers are individually true and separately labelled; the fault
is that a reader must know which roster each was computed over.

## OPEN — a typo'd `data.units.holdout.from` reports as a values fault with no hint that the column is absent

`_check_holdout`'s roster half reports `E-DATA-HOLDOUT-VALUES` when a `by_attribute` column
does not hold exactly `train` and `test`. When the declared `from` names a column the roster
has no attribute for at all, the same code fires with the same message shape — it says the
column's values are wrong rather than that the column does not exist, and the values it lists
are the ones a missing attribute yields rather than anything the user wrote. A misspelt
`from` is the likeliest way to reach it, and the message sends the reader to look at their
data instead of at their config.

**Deliberately not closed by H3d.** The fix is a distinct finding — an attribute-existence
check ahead of the values check, with its own code and its own § Errors row — and H3d's task
7 was scoped to the values rule alone. Closing it there would have added a thirteenth code to
a task already carrying three. `assign` has the same shape and the same gap, so a fix should
close both rather than only the holdout half.

**Found by:** H3d, Task 7 review. **Owner:** whichever slice next adds a diagnostic to
`_check_holdout` or `_check_assign` — re-owner this entry when that slice finishes rather
than leaving it pointing at a closed one.
**Severity:** Minor. The config is refused either way, so nothing invalid runs; the cost is
the reader's time between the message and the cause.

## OPEN — `units.stratum_names`'s docstring names two call sites and has seven

The docstring claims the helper is "shared by `assign.<axis>.stratify_by` and
`statistics.resample.stratify_by`, and written against neither in particular". The
enumeration was true when written and is not now: `stratum_names` is called from seven sites
in `src/`, including `validate._check_holdout`'s stratum check, which H3d added. The
"written against neither in particular" half remains true and is the load-bearing part; it is
the enumeration that has gone stale.

**Deliberately not closed by H3d.** Task 6's review found it and its brief did not own it;
task 7 was offered it and correctly declined, because task 7 adds no call site and absorbing
an unrelated docstring into a task carrying a Critical finding is how a slice's diff stops
being reviewable. It is recorded here rather than deferred a third time in review prose,
which is not a filing.

**A sibling to check at the same time:** `stratum_varies_within_cluster` had the identical
defect — two claimed call sites against three real ones — and H3d's task 7 corrected it to
four. An enumeration of call sites inside a docstring is a maintenance obligation nobody
owns, so the fix worth preferring is to state what the helper is *for* and drop the count.

**Found by:** H3d, Task 6 review; deferred again at Task 7. **Owner:** whichever slice next
edits `units.stratum_names` — re-owner this entry when that slice finishes rather than
leaving it pointing at a closed one.
**Severity:** Minor. A stale count in a docstring misleads a reader deciding whether a change
is safe, which is exactly the decision this repo's § Development record exists to support.

## OPEN — an evaluation split cannot be drawn within a cell

`data.units.holdout` and a `{kind: fold}` repeat both partition the whole roster once, and
`data.units.allocation: between` / a non-empty `sweep.groups` divides that same roster into
cells. `reference.md` § A fixed holdout split and `experimental-designs.md` both now name the
refusal this entry documents and record drawing the split **within** each cell as the design
that would lift it. **No build draws one.**

H3d refuses the combination instead, at one site under two codes — `E-DATA-HOLDOUT-CELLS`
and `E-REPL-FOLD-CELLS` — because the `fold` half was a live defect: `replication._fold_k`
bounds `k` against `units.fold_basis` over the whole roster, so 15 units split 12/3 by arm
permitted `k: 5` and left the 3-unit arm with two empty folds, and the config validated
clean. Refusing rather than disclosing follows `E-DATA-ASSIGN-BLOCKED-CLUSTER`'s precedent:
a truthful record of an imbalance no reader crosses by hand is the silently-wrong class.

**Owner of the retirement: H3c-3**, the slice that builds folds and holdouts inside cells.
Re-owner this entry if that slice's scope changes, rather than leaving it pointing at a
closed one.

**Found by:** H3d, Task 8. **Severity:** Was Major for `fold` while open — a validated
config produced empty folds per arm — and is now closed as a refusal rather than as a
capability.

## OPEN — the generated README's `credentials` region does not exist, so nothing can merge into it

`reference.md` § The generated README shows a scaffolded README carrying a
`<!-- publishable:begin credentials -->` region with a *"(none yet — added as experiments declare
them)"* placeholder row, and a `cp .env.example .env` setup line above it. **Neither is emitted.**
Measured at `d86290c` and re-confirmed on 2026-08-16 for this filing: a freshly scaffolded
`README.md` grepped for `publishable:begin` returns `overview` and `experiments` and nothing else
(`scaffold.py`'s `README` constant holds exactly two such regions), and there is no `cp` line
anywhere in that constant. The control — the same grep for the two regions that do exist — hits
both.

Three consequences, in the order they bite. `reference.md` § Generators already marks *"merging any
new `required_env` into the credentials table"* **NOT BUILT** (`docs` is in `cli.NOT_BUILT_COMMANDS`,
re-confirmed) and used to say in the same paragraph that `required_env` "compounds that gap rather
than merely sharing it" because the attribute had no reader — that half is now stale and has been
corrected in place, since H7c gave `required_env` its first reader at `validate`; what remains
unbuilt is the merge, not the reader. `publishable docs`, which § The generated README says
regenerates every managed region, is in `cli.NOT_BUILT_COMMANDS`. And a merge built against an
absent region would have nothing to merge into, which is why H7c refused the charter item rather
than absorbing it.

**Routing, and it corrects `H7b-SCOPING.md` § 11.** That document routes "the README managed
regions — `credentials`, a parameter-table region, `generate experiment`'s merge" wholesale to
**`docs`**. It is right about the merge and wrong about the region: the *static* `credentials`
region and the `cp .env.example .env` line are written by **`new`**, i.e. `scaffold.py`'s `README`
constant, and `docs` has nothing to populate until they exist.

**Owner:** whichever slice next edits `new`'s README emission owns the region and the setup line;
`docs`'s slice owns regenerating it; `generate experiment`'s merge follows both.

**Found by:** H7c, Task 14, re-measured against `main` on 2026-08-16. **Severity:** Minor. No
config is affected — this is scaffolding output, not validation — but a reader following
§ Reproducing on another device or § Secrets & credentials today gets instructions for a file
region that was never written.

## OPEN — two specified readers of `required_env` belong to unbuilt commands

H7c made `BaseTemplate.required_env` readable and gave it its first reader, at `validate`. Two more
readers are specified and cannot be built here, because each belongs to a command in
`cli.NOT_BUILT_COMMANDS` (re-confirmed 2026-08-16: both `reproduce` and `dry-run` are still listed).
Filed so neither is folded into a slice that has no business with it.

| Specified | Owner |
|---|---|
| `reference.md` § Reproducing on another device, step 6 — `reproduce` *"copies `.env.example` and lists the `required_env` variables that need values"*, and the consequence stated beneath it | **`reproduce`'s slice** |
| `reference.md` § Metering — `dry-run` *"needs … real credentials"* | **`dry-run`'s slice**, which inherits H7c's load site and its two checks without change |

H7c owes only that the attribute is readable, which it now is.

**Found by:** H7c, Task 14, re-measured against `main` on 2026-08-16. **Severity:** None — both
are present-tense specification of unbuilt commands, not defects; filed to prevent either reader
being folded into an unrelated slice's scope.

## OPEN — `BaseTemplate.field_convention` is declarable and read by nothing

Measured at `478c1f3` and re-confirmed on 2026-08-16: `grep -rn "field_convention" src/publishable/`
returns two declarations (`templates/base.py`, `templates/builtin/generic.py`) and one comment in
`generators/template.py` naming it among the members the `generate template` stub omits. Nothing
reads it. `reference.md` § Naming conventions & repeat defaults specifies what it means — a naming
pattern and a repeat floor per convention class — and `naming_pattern` and `default_repeats` are
both read while the class that groups them is not.

This is `CLAUDE.md`'s *unbuilt reader of a shipped surface*, and it is now that row's worked
example: H7c retired `required_env` from that role by giving it a reader, and of the three
remaining members `apparatus_probe` is **H7b task 13's** and `apparatus_facts` is **H7d's**, which
leaves this one unowned.

**Owner:** unassigned. Whichever slice next touches § Naming conventions & repeat defaults should
either give it a reader or state in `reference.md` that it is declarative only.

**Found by:** H7c, Task 14. **Severity:** Minor. The value is inert rather than misleading — no
config field references it — but it is a second shipped-and-unread surface alongside the ones this
repo has already tracked.

**Amended 2026-08-17 — H7b Part A task 13:** `apparatus_probe` gained a reader. `validate` now
checks it against the installed `publishable.probes` distributions (`E-PROBE-UNKNOWN`), so the
family this entry's `field_convention` belongs to is now `field_convention` and `apparatus_facts`
only.

## OPEN — `io.reuse_from` is unbuilt and unowned by any H7 sub-slice

`docs/superpowers/specs/2026-08-16-credentials-and-secrets-design.md` § Out of scope names
`io.reuse_from` as "unbuilt and unowned by any H7 sub-slice, which is a gap this slice files rather
than closes." Re-confirmed on 2026-08-16: `grep -n "reuse_from" docs/superpowers/spec-defects.md`
returned nothing before this entry, so there was no prior filing to re-owner. `reference.md` §
Steps that consume an earlier run's artifacts is where `reuse_from` is specified — a step that
reads another run's output records it as an upstream with its own hashes — and nothing in `src/`
implements it.

**Owner:** unassigned. No H7 sub-slice (H7a, H7b, H7c, H7d) claims it in its charter.

**Found by:** H7c, Task 14. **Severity:** Minor. Specification of an unbuilt feature, not a
contradiction between a built check and its documentation — filed so it is not silently assumed
closed by a later slice's scoping.

**AMENDED 2026-08-17 (H7b Part B task 33): now the sole remaining core-side blocker for three
experiments, and an owner request rather than a second filing.** With `E-DATA-RESOLVER-UNSUPPORTED`
retired, [the feasibility analysis](../feasibility-llm-growth-studies.md) § Executability on this
build's 2026-08-17 entry finds E1, E2 and E5's `data`/`statistics` blocks validate with no core-side
error at all — `io.reuse_from` is the one thing standing between E3, E4 and E6 and the same result,
since each reads a frozen artifact through it and `grep -rn "reuse_from" src/publishable/` still
returns nothing. Still no H7 sub-slice claims it. Amending this entry rather than opening a second
one, per `CLAUDE.md`'s own rule that a duplicate filing is the same failure as an unfiled gap in the
other direction — this is the same gap, now with three concrete configs waiting on it. **Owner
request:** the next slice to touch step-level artifact consumption should claim it, or the spine
design should assign it explicitly rather than leaving it to be rediscovered a third time.

## `python-dotenv` honoured an undocumented behavior-changing environment variable — CLOSED by H7c

~~`python-dotenv`'s `load_dotenv` checks `PYTHON_DOTENV_DISABLED` and skips loading entirely when it
is set to a truthy value (confirmed 2026-08-16 against the installed package,
`.venv/lib/python3.13/site-packages/dotenv/main.py`: `if "PYTHON_DOTENV_DISABLED" not in
os.environ: ...`). `secrets.load_env` calls `load_dotenv` directly and inherits this, so core's
`.env` load path honours an environment variable that changes behavior — no flag, no config field,
nothing in `reference.md` names it — which is exactly what `CLAUDE.md`'s first invariant (operation
commands take paths and nothing else, no behavior-changing env vars) rules out for anything this
repo builds itself.~~

~~It fails **closed**: setting it silently disables `.env` loading, so a declared credential that
would otherwise be satisfied from the file instead reports `E-CRED-MISSING`/`E-CRED-PARAM-MISSING`
rather than executing with a value nobody meant to hide. It is not core's own code — it is a
property of the dependency `secrets.py` calls, present in `python-dotenv` before this slice added
the dependency to this project — so this is a filing rather than a fix. A fix would mean core
either not calling `load_dotenv` at all (losing the mechanism this slice built) or pre-emptively
clearing the variable before every call (a behavior change of its own, and one that would fight a
developer's own shell rather than serve them).~~

~~**Owner:** unassigned. Worth a `reference.md` § Secrets & credentials footnote naming the variable
and its fail-closed direction, the next time that section is touched.~~

~~**Found by:** H7c, Task 14. **Severity:** Minor. Fails closed (a missing credential is refused, not
silently accepted), and no config in this repository sets the variable — filed because it exists
and is undocumented, not because it has been observed to bite anyone.~~

**STRUCK 2026-08-16 (H7c whole-branch review, finding 5): FIXED, not merely re-reasoned.** The
"fix would mean" paragraph argued a false dichotomy: `load_dotenv` consults
`PYTHON_DOTENV_DISABLED`, but `dotenv_values` — read against the installed package — does not touch
it at all, and never touches `os.environ` itself either. `secrets.load_env` now parses with
`dotenv_values(path)`, skips the `None` values a bare `KEY` line produces, and
`os.environ.setdefault`s the rest — keeping the mechanism, keeping the dependency, and removing the
undocumented behavior-changing variable `CLAUDE.md`'s first invariant rules out. Pinned by
`tests/test_secrets.py::test_python_dotenv_disabled_is_not_honoured` and
`::test_a_bare_key_with_no_value_is_missing_not_empty`.

**AMENDED 2026-08-16 (H7c whole-branch re-review, finding N1):** `dotenv_values` hardcodes
`override=True` internally, and that flag is also what `python-dotenv`'s `resolve_variables`
consults to decide whether a `${VAR}` reference inside the file resolves against the shell or
against the file — so the parse above silently stopped honouring an exported variable inside an
interpolated value, even though a direct assignment still won via `setdefault`. `secrets.load_env`
now parses with `dotenv.main.DotEnv(path, stream=None, verbose=False, interpolate=True,
override=False).dict()` instead — the constructor `dotenv_values` itself calls, with the flag it
hardcodes passed explicitly — which never consults `PYTHON_DOTENV_DISABLED` either, so this
amendment does not reopen the struck gap. Pinned by
`tests/test_secrets.py::test_interpolation_resolves_from_the_shell_not_a_stale_file_value`.

## OPEN — `declared_credential_names` reports a template-default credential for a parameter value never written

`cli.declared_credential_names` and `validate._check_requires_env` both resolve a swept parameter's
value by flattening `parameters` with `_flatten_parameters`/`_flatten`, which recurses into every
nested `dict` and only ever stores leaf, non-dict values. A dict-valued parameter — for example
`parameters.llm.provider: {a: 1}` — is therefore flattened to `llm.provider.a` alone; `llm.provider`
itself is absent from the flattened mapping. Both call sites then do `resolved.get(path,
param.default)`, so the lookup falls through to the **template's default** for `llm.provider`, and
if that default's `requires_env` entry names a credential, the config reports
`E-CRED-PARAM-MISSING` for a value that was never actually written or resolved — the config's own
dict value is silently ignored by this check.

Confirmed by reading `cli.py`'s `_flatten_parameters` (recurses on `isinstance(value, dict)`) and
`declared_credential_names`'s `resolved.get(path, param.default)` fallback, and the identical shape
in `validate._check_requires_env`'s `param.requires_env.get(value)` against the same resolution.

This is cosmetic rather than a correctness gap: `llm.provider: {a: 1}` is not a member of `choices`
regardless, so the config is refused either way — **CORRECTED 2026-08-16 (H7c whole-branch review,
finding 6): not by the `choices` check**, which never sees `llm.provider` at all (`_flatten`
produces `llm.provider.a`, never the parent path, so the leaf that reaches the `choices` check does
not exist). Probed: the refusal is `E-PARAM-UNKNOWN` on the nested leaf `parameters.llm.provider.a`
("is not a parameter of this template"), reported alongside `E-CRED-PARAM-MISSING` for the
template-default fallback this entry is about. What is wrong is only the *message* — it asserts a
resolution (the template default was in effect) that never actually happened, because the config
supplied a value that just isn't visible to a path-flattening reader.

**Owner:** whichever slice next touches `_flatten_parameters`/`_flatten` or
`declared_credential_names`.

**Found by:** H7c, Task 14. **Severity:** Minor. The config is refused regardless (by
`E-PARAM-UNKNOWN` on the nested leaf, not by the `choices` check — corrected above), so nothing
invalid runs — the defect is a misleading message on an already-refused config, not a missed
refusal.

## OPEN — `main`'s last-resort stderr handler prints an exception un-redacted, by construction

`cli.main`'s bare `except PublishableError as exc:` handler (the catch-all around `_dispatch`)
prints `f"  error   {exc.code:<20} {exc}"` straight to stderr, with no redaction. This sits outside
both of decision 3's serialization boundaries (`runner.execute_plan`'s step-error path and
`Collector.render()`) **by construction**: it exists to catch whatever escapes every collector, and
`main` holds no config or condition context, so it has no credential values to check against — it
cannot know what to redact without a global carrying the run's declared credentials into a
function that today takes only `argv`.

The demonstrated path into it is closed: task 12's review found `template.validate(doc)` raising
unguarded in `validate.py`, letting a credential-bearing raise reach this exact handler verbatim,
and the fix (commit `cd72c3a`) routed that call through `Collector.render()` instead, closing the
one path this slice built that could reach it with a declared value. The handler itself is
unchanged and remains reachable by any other `PublishableError` raised outside a collector.

**Owner:** unassigned. Not a task for this slice — closing it would mean giving `main` a way to
know which values are credentials, which is a design question (a module-level or threaded
credential set) rather than a redaction-site fix. Filed with its reasoning rather than as a bug to
patch, per the routing brief.

**Found by:** H7c, Task 12 review; filed at Task 14. **Severity:** Minor today (the one reachable
path was closed in the same slice) but structural — any future `PublishableError` raised with a
credential in its text, outside a collector, reaches stderr unredacted.

## OPEN — the constraint table documents `min_items`/`max_items` in the rendered comment; `Param.comment()` doesn't render them

`reference.md` § Templates: where parameters are defined documents the `list` row's constraint
column as `item_type` · `min_items` · `max_items`, with the example inline comment `# list of
float, 2 to 5 items`. Confirmed 2026-08-16: `Param.comment()`'s `list` branch is `if self.type_ is
list and self.item_type is not None: return f"list of {_TYPE_NAMES[self.item_type]}"` — it names
the item type and nothing else. `min_items`/`max_items` are stored on the instance and enforced by
`Param.violation` (both raise a message when the length bound is crossed), but no renderer reads
either for the inline comment `init` writes, so a generated config's comment never states the item
count bound the parameter actually enforces.

Pre-existing, unrelated to `requires_env`/`required_env` — found while sweeping `param.py` for this
slice's own changes to `comment()` and not owned by any H7c task.

**Owner:** whichever slice next touches `Param.comment()` or the list constraint row.

**Found by:** H7c, Task 14. **Severity:** Minor. `validate` still enforces the bound at value time
regardless of what the comment says — a reader is under-informed, not let through a bad config.

## OPEN — a pre-existing positional reference at § the provenance table

`reference.md`'s participant-identity paragraph (beside § the provenance table) reads "this
section, and the table above, have never named it" — a positional reference (`CLAUDE.md` bans
locating anything by position: "the two rows above", "further up"). Confirmed 2026-08-16 still
present, unchanged by this slice. Pre-existing and out of scope for every H7c task — none of them
touches this paragraph or the table it refers to.

**Owner:** whichever slice next edits that paragraph or the provenance table it names
positionally; should name the table by its heading instead.

**Found by:** H7c, Task 14 (surfaced while sweeping `reference.md`, not itself part of the
credential family). **Severity:** Minor. A wording nit rather than a factual defect — the claim it
makes is still true, only the cross-reference is positional.

## `publishable.readers` had no entry-point group, so a third-party writer had no reader — CLOSED by H7b Part A task 15

**Was:** § Creating a plugin declared four entry-point groups and said of a writer "its reader
inverts it", with no mechanism for supplying one. `artifacts.WRITERS` and `artifacts.READERS` are
two module dicts, `io.write` dispatches through `_suffix_for`, which iterates `WRITERS` alone, and
`StepIO._read` indexes `READERS` — so a suffix registered as a writer and not as a reader gives
`io.read_upstream` a bare `KeyError` rather than a coded `ArtifactError`. Proved by mutation
(`H7b-SCOPING-2.md` § 5a): adding one key to `WRITERS` alone reproduced it, and deleting the key
restored the read. Filed here for the first time — `H7c` task 14 filed four entries in this family
and none of them was this one.

**Closed by specification** in H7b Part A task 3: a fifth group `publishable.readers` and a fifth
decorator `register_reader`, ~~with `register_writer` refusing a suffix that has no reader. The
code is owed by tasks 14 and 15 of the same slice; this entry is struck when task 15 lands, not
before.~~

**CORRECTED 2026-08-17 (H7b Part A task 15 merge-gate review):** the struck clause named the wrong
mechanism. **Closed in code by task 15**: `StepIO._read` now raises `ArtifactError` ·
`E-ARTIFACT-UNREADABLE` for a suffix `WRITERS` holds and `READERS` does not, rather than the bare
`KeyError`. The refusal fires at the read, not at registration — `register_writer` does not refuse
a suffix with no reader, since a plugin may register the reader later in the same module; task 14's
registration-time refusal is the unrelated core-suffix-shadow check, under the same code for a
different reason.

## OPEN — an installed template's name resolves but its class is never loaded — **Owner: unassigned**

H7b Part A task 8 makes an installed distribution's `publishable.templates` entry point a claim in
the merge, so its name is known, collisions against it are decided, and `template_names` lists it.
Task 9 refuses a config naming one, as `E-TEMPLATE-INSTALLED-UNSUPPORTED` — the `-UNSUPPORTED` build
family, no § Errors row. Closed at both emit sites that can name a template: `validate_config`'s
finding and `generate_experiment`'s raise (the task 8-11 review's C1, closed the same review cycle —
the second site had been left reporting the false `E-TEMPLATE-UNKNOWN` instead).

The refusal exists because decision 3 of `2026-08-16-plugin-registries-design.md` states the
entry-point invariant of **resolution** and not merely of the negative answer: "`validate` resolves a
name *without importing a line*". Loading the one entry point a config names would answer a narrower
reading of the same sentence and is the natural next step, but it is a decision, not an oversight,
and it is not H7b Part B's — Part B is the resolver half and its nine tasks do not touch template
loading.

**What retiring it needs:** `Claim.cls` populated for an installed claim; `is_local_template`'s two
class-taking callers (`validate._check_versions`, `materialize.materialize_config`) reading
`Claim.provenance` instead, since `installed` becomes reachable at both for the first time; and
`provenance.plugin_versions` recording which distribution supplied it. **Owner: unassigned.**

**AMENDED 2026-08-17 (H7b Part B task 30):** one of the three preconditions above is now built —
`provenance.plugin_versions` records the distribution and version a resolver-sourced run resolved
through (`plugins.versions_for`, threaded in `cli.command_run`). It records only what a resolver
declaration named, never an installed template's class, so it does nothing for this gap's own
case — a config naming an installed *template* still resolves no class. Amended, not closed; owner
stays unassigned.

## OPEN — `PROBES` and `RESOLVERS` are written by their decorators and read by nothing

H7b Part A tasks 12 and 13 gave `publishable.plugins` two more module-level registries.
`RESOLVERS["<name>"] = fn` is set by `register_resolver`'s decorator (task 12) and
`PROBES["<name>"] = fn` by `register_probe`'s (task 13); `grep -rn "RESOLVERS\|PROBES" src/`
shows each written at exactly one site and read at none. This is a different fact from what
`validate._check_probe` does: that check reads `BaseTemplate.apparatus_probe` against
`plugins.names("publishable.probes")`, the entry-point **metadata** scan — a reader for the
declared *name*, not for the `PROBES` **registry** the decorator populates. The registry itself
stays unread by either check.

**Why this is a filing rather than a fix.** A reader for `PROBES` means *executing* a probe —
`Apparatus`, per-condition facts, the ledger, and the change gate — all H7d and explicitly out of
scope for H7b (`docs/superpowers/specs/2026-08-16-plugin-registries-design.md` § Out of scope).
Shipping any part of that to give `PROBES` a reader here would be worse than recording the gap. A
reader for `RESOLVERS` is `data.units.from.resolver`'s dispatch — the resolver-half of `data.units`
that H7b Part B builds, not this task.

This makes the shipped-and-unread family **larger** than the amendment task 13 wrote in the entry
above (`BaseTemplate.field_convention` is declarable and read by nothing): that amendment correctly
narrows the *`BaseTemplate` attribute* family to `field_convention` and `apparatus_facts`, but
`PROBES` and `RESOLVERS` are a different shape — module-level registries, not class attributes —
and join the wider shipped-but-unread family in the same four commits.

**AMENDED 2026-08-17 (whole-branch review, finding I4): the filing under-counted by four.** Four
more surfaces this branch added have no production caller either — `grep -rn` for each across `src/`
returns only its own definition or its own module's docstring:

| Surface | Added by |
|---|---|
| `plugins.load_entry_point` | task 17 |
| `plugins.check_registration` | task 16 |
| `plugins.declared_names` | task 16 |
| `registry.template_provenance` | task 9 |

`load_entry_point`, `check_registration` and `declared_names` are group-generic — the same three
calls serve templates, resolvers, probes, writers and readers alike — so their first production
caller is whichever slice first dispatches *any* group, which by construction is **H7b Part B**: its
nine tasks build the resolver half's dispatch, the first slice scheduled to call `load_entry_point`
at all. `template_provenance` is template-specific and belongs with the *installed template's class
is never loaded* gap below rather than with this one; that entry's owner is unassigned, and
`template_provenance` shares it.

**Owner:** `PROBES` → **H7d** (probe execution: `Apparatus`, facts, ledger, change gate).
`RESOLVERS`, `load_entry_point`, `check_registration`, `declared_names` → **H7b Part B**, the
resolver-dispatch task. `template_provenance` → unassigned, with
`## OPEN — an installed template's name resolves but its class is never loaded`.

**Found by:** H7b Part A tasks 12-15 review; extended by the H7b whole-branch review (finding I4).
**Severity:** Minor. All six surfaces are populated or computed correctly and read by nothing yet —
inert rather than misleading, since no config field depends on any of them being read today.

**AMENDED 2026-08-17 (H7b Part B task 30): four of the six now have a production caller.**
`RESOLVERS`, `load_entry_point`, `check_registration` and `declared_names` are read from
`units.py`'s resolver dispatch (tasks 24-25) — `RESOLVERS` via `_resolve_resolver`'s scan-then-load,
`load_entry_point` and `check_registration`/`declared_names` at the same site, checking the
`@register_resolver` argument against the entry-point key that loaded it. `PROBES` stays with H7d,
unread by anything Part B built. `registry.template_provenance` stays with the unassigned installed-
template entry above — Part B's four tasks were the resolver half and never touched template
loading.

**CORRECTION 2026-08-17 (whole-branch review), replacing this entry's function name only:** the
scan-then-load function is `_resolver_for`, not `_resolve_resolver` — `_resolve_resolver` appears
nowhere in `src/`. The substance stands: `RESOLVERS` is read there, verified by tracing
`declared_names` → `_registry_for` → `RESOLVERS` rather than assumed.

## OPEN — a plugin-side collision carries no class, so its finding cannot be redacted — **Owner: none; accepted**

H7c's `PartialLoadError` carries the classes a discovery pass constructed, so a credential a refused
`templates/*.py` declared is redacted out of the refusal's own message. H7b Part A task 8 adds
installed distributions as a third claim source to that merge, and an installed claim carries **no
class**: the scan is metadata-only by decision 3 of
`2026-08-16-plugin-registries-design.md`, so nothing was imported and there is no `required_env` or
`parameter_spec` to read.

**Filed as accepted rather than as work.** The repair is to call `EntryPoint.load()`, which destroys
the invariant the entry-point mechanism exists for — that `validate` resolves a name without
importing a line — and § Creating a plugin justifies the whole design by that promise. A named
residual beats a silently weaker guarantee. Recorded here so the next reader meets the argument
rather than the temptation, which will arrive dressed as "we need the class to redact its
credentials."

**Bound on the exposure.** A collision message names providers — a distribution and a version, a
path and a class name — and interpolates no declaration, so the text at risk is an exception's
rather than a credential's by construction. What is unmatched is a credential value appearing in a
message core built from an installed claimant's own data, and no such message exists today.

**Struck when** an installed template's class is held at the merge, which is
`## OPEN — an installed template's name resolves but its class is never loaded`, owner unassigned.
The two close together or not at all.

## CLOSED — a core-suffix claim's `E-PLUGIN-COLLISION` becomes `E-PLUGIN-LOAD` once loading is wired

A writer or reader claiming an extension core itself writes or reads is refused at decoration time
as `ContractError` · `E-PLUGIN-COLLISION` — `register_writer`/`register_reader` raise it directly,
with no plugin loaded yet. `docs/reference.md` § Errors core raises promises `E-PLUGIN-COLLISION` its
own code for that arm, distinct from the code a plugin's top-level import failure carries
(`E-PLUGIN-LOAD`).

That promise holds only because nothing loads a plugin today. The moment `load_entry_point` gets a
production caller — Part B's, by construction, per the amendment above — the same raise is reached
*inside* the module import it decorates, where `load_entry_point`'s broad `except Exception` catches
it and re-reports it as `E-PLUGIN-LOAD` instead. That is the identical substitution
§ Errors already documents and accepts for `E-TEMPLATE-LOAD` swallowing a coded error from a local
template's top level — the precedent exists — but `E-PLUGIN-COLLISION`'s own row does not yet say
its code can be re-coded this way for the writer/reader groups.

**Filed as a hazard for Part B to resolve when it wires loading, not fixed here**: there is no
production caller yet, so the substitution cannot happen today and there is nothing to reproduce.
Part B's task that gives `load_entry_point` its first caller should either let the `E-PLUGIN-LOAD`
re-code stand and add one sentence to `E-PLUGIN-COLLISION`'s row noting the precedent, or catch
`ContractError` before the broad `except` so the writer/reader arm keeps its own code through a load.

**Found by:** H7b whole-branch review, finding M4.

**Closed by H7b Part B, task 24, taking the first resolution named above: let the re-code stand.**
Catching `ContractError` ahead of `load_entry_point`'s broad arm would let *any* coded
`ContractError` a plugin's top level raises escape the containment under whatever code it happened
to carry — a fail-open of exactly the shape `CLAUDE.md` § Answering a question with a proxy names,
and one that would defeat the reason `load_entry_point` is broad. Narrowing the catch to the single
code `E-PLUGIN-COLLISION` would instead make `load_entry_point` — a group-generic function — know
about a code only two of the five groups can raise. The precedent already exists and is documented:
§ Errors accepts `E-TEMPLATE-LOAD` swallowing a coded error from a local template's top level, for
the same reason. `docs/reference.md` § Errors core raises' `E-PLUGIN-COLLISION` row now carries one
sentence recording this precedent.

## CLOSED — `hash_index` hashed nothing for any source, and was unfiled

**Measured 2026-08-17 against `352ea28` (H7b Part B task 30):** `build_manifest`'s `index_names`
parameter had zero callers in `src/` and `hash_index` appeared in no test. Under `hash_index` every
`sha256` came back `None` — for a table source and a glob source exactly as much as for a resolver's,
since nothing supplied the set the policy needs. Three `reference.md` passages promised otherwise —
§ Three hashes ("Content hashes for the files `data.units.from` resolves — the index and whatever it
names"), § What `run.yaml` records ("Under `hash_index` the `sha256` key is present for the files
`data.units.from` resolves and absent for the rest"), and § Where units come from — and the gap had
no entry here.

**Closed by H7b Part B task 31.** `units.index_names(units_decl, roster, reads=())` covers all three
sources in one expression: the source's own file where it names one (a table), plus every path its
resolved units name (a glob's per-unit path, a resolver's `Unit.paths`), plus whatever the resolver
itself read (`ResolverIO.read_paths`, threaded through `resolver_io` at the one `build_manifest` call
site in `cli.command_run`). A roster that failed to resolve still yields the source's own file, since
the index is named by the declaration rather than by the roster.

**Found by:** the same task that needed it closed to build the resolver half — `hash_index`'s
resolver case cannot be tested against a policy broken for every source.

**The two `ResolverIO` questions task 23's docstring left as task 31's, decided.** Both are benign.
Append-before-read means a read that raises still lands in `read_paths`, and `index_names` therefore
still names it — but `build_manifest` only ever hashes a path it found by walking `input_dir`, so a
name that corresponds to no file on disk (the ordinary shape of a failed read) simply never gets a
`files` entry to attach a hash to; nothing crashes and nothing hashes a file that was not there. A
`relpath` containing `../` behaves the same way in the other direction: `index_names` would include
it verbatim, but `build_manifest`'s `files` dict is keyed by paths `rglob`'d from inside `input_dir`,
so a name that resolves outside it never matches an entry either. Neither needs a containment check
to make `hash_index` correct; one would be a change to what a resolver may read, which is a decision
this task was not asked to make.

## OPEN — a run whose template declares an installed probe records a false `apparatus: null` — **Owner: H7d**

`cli.command_run`'s provenance document writes `"apparatus": None` unconditionally — there is no
branch reading a template's `apparatus_probe` at all. `reference.md` § The apparatus core can only
observe defines `apparatus: null` as *"no probe declared"*, which was accurate for every run this
build could produce until H7b Part B gave a template's `apparatus_probe` a second, real declaration
path: `validate._check_probe` already checked the name against the installed `publishable.probes`
group (H7b Part A), but nothing before Part B could make that declaration true end to end, since no
resolver could dispatch and no plugin naming both a resolver and a probe could be exercised. Now that
one can, a run whose template declares an installed, resolvable probe still writes `apparatus: null`
in its own `run.yaml` — a false record of "no probe declared" for a run that declared one.

**Filed rather than fixed, because a reader is out of scope for the slice that surfaced it.** Reading
`apparatus_probe`, executing it, building the per-condition facts, the ledger, and the change gate the
document describes are all `Apparatus`'s job — `docs/superpowers/specs/2026-08-16-plugin-registries-design.md`
§ Out of scope and the entry above (`## OPEN — "PROBES" and "RESOLVERS" are written by their decorators
and read by nothing`) already assign that machinery to H7d. This entry is narrower and newly true: not
"the registry is unread" but "the record is actively false" for the one config shape H7b Part B makes
reachable for the first time.

**Owner:** H7d. **Found by:** H7b Part B task 33, while re-measuring the feasibility analysis's
executability — no config in that analysis declares an `apparatus_probe` today, so this is a defect
about the shape now reachable rather than one any of the nine configs currently hits.

## OPEN — a relative `glob` pattern escaping `input_dir` resolves units from outside it — **Owner: unassigned**

`units._from_glob` builds the roster from `input_dir.glob(pattern)` with no containment check on the
matches. An **absolute** pattern (`/etc/*.conf`) or one that is absolute after normalization
(`/../*.csv`) hits `Path.glob`'s own `NotImplementedError` and is recoded to
`E-UNITS-SOURCE-UNREADABLE` — that much `reference.md`'s row for the code describes correctly. A
**relative** pattern that still escapes `input_dir` (`../*.csv`, `../outside.csv`, `**/../*.csv`) does
not: `Path.glob` returns the outside match, so the roster silently includes a unit whose `paths` entry
is `../outside.csv`, read from outside the declared `input_dir` — on 3.11, 3.12 and 3.13 alike, so this
is not one interpreter's behavior.

The same asymmetry task 31 already recorded for `ResolverIO` (a resolver's own reads are unchecked
against `input_dir` too, decided benign there because `build_manifest`'s `files` dict is keyed by paths
walked from *inside* `input_dir`, so an escaping name simply never gets a `files` entry). It applies
identically here: `hash_index` cannot hash such a unit's path either.

**Found by:** H7b Part B's whole-branch re-review, while checking a normative § Errors row against the
code rather than reading it — the row had claimed this exact pattern raises, which it does not for the
relative case. Filed rather than fixed: closing it is a containment-check decision (what a `glob` or a
resolver may read) that no task in this slice was asked to make, the same reasoning task 31's entry
already gives for `ResolverIO`.

## CLOSED by H4b-1 task 1 — the paired derived estimators were owed a weights decision, and the code had already made it

`docs/superpowers/H4-SCOPING.md` § 4.3 recorded "H4b's first task, not an observation": whether
`paired_delta_of_derived` and `paired_percentile_of_derived` take weights, or whether a weighted
derived contrast is record-only. `docs/superpowers/H4b-SCOPING.md` § 2.1 re-measured it at `b65ab91`
and found the code had settled it — a derived metric's resample closure is
`tmpl.aggregate(_attributed(units, attrs), cfg)`, so the weight column reaches `aggregate` as a unit
attribute on the contrast path exactly as it does per condition, and there is no per-unit vector for
core to weight.

**Settled: they take no weights, and `weighted_by` and the effective size still travel beside a
derived contrast** — the declaration is true of the run either way. `method` stays the unweighted
spelling, because core did not do the weighting.

What was actually owed was the *filing*, because the settlement narrows a published refusal message
and a normative § Errors row that both promised three constructions would take weights. Both were
narrowed by deletion in this task; both are deleted outright in H4b-1 task 13.

**Found by:** H4b-SCOPING § 2.1. **Closed by:** H4b-1, task 1.

## CLOSED by H4b-2 task 9 — a stratified paired draw could publish a zero-width contrast interval

H4b-1 task 5 gave `stats.paired_percentile_of_derived` a `strata` parameter, so
`statistics.resample.stratify_by` is honoured on a contrast for the first time. Its three sibling
percentile constructions each carry a **content-based degenerate refusal** —
`percentile_over_units`'s strata branch, `percentile_over_units_clustered`'s cluster-content branch,
and `percentile_of_derived`'s identical-row branch, which refuses before drawing when every key in
every stratum carries the same recorded row. `paired_percentile_of_derived` carries none of them,
which `docs/superpowers/spec-defects.md`'s entry on the contrast path's disclosure gaps already
records as deferred.

**What task 5 changed is the reachability.** A near-unique `stratify_by` now makes every stratified
contrast draw pick from an identical multiset of rows, so `compute_of`/`compute_against` return the
same difference every time and the entry publishes `ci95: [x, x]` — a zero-width 95 % interval, which
§ Statistical reporting refuses in those terms — indistinguishable from a genuine interval. Before
task 5 the same config's contrast draw was unstratified and could not reach it.

Not built in H4b-1: it is a third construction's worth of work (the paired form has two collapsed
tables to compare rows across, not one) and the slice's task budget does not hold it.

**Owner: H4b-2 — clusters through contrasts**, by name and not "whichever slice ships next": H4b-2 is
the half that adds the remaining paired percentile construction, so it is where the degenerate sweep
belongs for all of them at once. It should be built together with the zero-width sweep the contrast
disclosure entry already defers to H4b-2.

**Found by:** H4b-1, task 5. **Severity:** Minor — reachable only from a `stratify_by` whose strata
are near-unique, which `validate` does not refuse.

**AMENDED 2026-08-17 (H4b-2, task 3).** Ruled and specified: `reference.md` § Statistical reporting
now states the rule — a contrast draw whose every stratum's drawable things carry the same pair of
rows reports `ci95: null` — and H4b-2 task 9 gives it code inside
`stats.paired_percentile_of_derived`, covering the clustered and unclustered draws and the stratified
and unstratified ones as one check over the drawable item. **The entry is closed by that task, not by
this one.**

**CLOSED 2026-08-17 (H4b-2, task 9).** `stats.paired_percentile_of_derived` now refuses a draw whose
every drawable thing within a stratum carries the same pair of rows, returning
`PairedResample(interval=None, draws_used=0, pool=[])` — the shape its `len(keys) < 2` early return
already had. Content-based rather than count-based, and over the **drawable thing** — a key by
default, a whole cluster under `clusters` — so it covers the stratified and unstratified draws and
the clustered and unclustered ones as one expression. The rule was stated in `reference.md`
§ Statistical reporting first, by task 3.

**What is closed and what is bounded.** The filed reachability — a near-unique `stratify_by` making
every draw pick from an identical multiset — is closed outright: one drawable thing per stratum
satisfies the check whatever the rows carry. The check compares **whole collapsed rows**, so a table
holding several recorded columns can differ on a column a given metric's closure never reads, and
that metric's draw can still be constant without the refusal firing. Bounded and stated rather than
claimed away; a signature keyed on the metric the closure reads would close it, and no filed defect
asks for that today.

## RULED by H4b-2 task 1 — the weight × cluster combination is refused, not built

`docs/superpowers/H4b-SCOPING.md` § 10 assigned the `weight_by` × `cluster_by` × comparison refusal
to **H4b-1 by name** — "not to whichever ships first". H4b-1 did not mint it, and
`E-DATA-WEIGHT-CONTRAST` was retired in the same slice, so at `82310b9` such a config earns
`E-DATA-CLUSTER-CONTRAST` alone and `reference.md` § Statistical reporting's *"The `_clustered`
suffix does not compose with either weighted form in this build"* is enforced by nothing else.

**Ruled: mint `E-DATA-WEIGHT-CLUSTER-CONTRAST`, a documented narrow refusal carrying a § Errors row
and a § Validation row.** Not a `-UNSUPPORTED` build-family code: this refuses a *combination*, which
is what decides whether it outlives the slice that minted it. The grounds are that minting is the
precedent H3a and H3b both set for a combination made reachable by retiring a broader refusal; that
no config in `docs/feasibility-llm-growth-studies.md` declares `cluster_by`, so the composition
unblocks nothing measurable; and that a weighted clustered *t* takes its df from the **cluster
count** rather than from Kish's effective size, a distinction invisible in any fixture not built to
separate the two.

**H4c inherits the composition itself**, alongside the unpaired clustered forms.

**Ruled by:** H4b-2, task 1. **Built by:** H4b-2, task 8.

## RULED by H4b-2 task 4 — `E-DATA-CLUSTER-DERIVED` is re-owned to H4c, not built here

`docs/superpowers/H4b-SCOPING.md` § 5 recommended that H4b-2 take the clustered derived draw
"because the construction it needs is the same membership-aware derived draw". Re-measured at
`82310b9`: it is emitted once, from `stats.summarize_step`, and its `reference.md` § Errors row
justifies itself as *"Temporary, alongside `E-DATA-CLUSTER-CONTRAST`"* — a justification that dangles
the moment H4b-2 task 14 retires that code.

**Ruled: do not build it. Re-own it to H4c by name, and let the row state its own justification.**
The missing construction is a per-condition percentile draw over clusters for a *recomputed* metric —
each replicate drawing whole clusters and rebuilding a `UnitTable` from their pooled units — which is
the same family as the unpaired clustered percentile form H4c already owns, and is not a contrast
construction at all.

**H4b-2 does not need it**, and that is measured rather than assumed: under `cluster_by` the whole
`derived` mapping is dropped before it reaches `aggregated`, so `cli._comparison_step_blocks`' derived
branch — selected by `metric_key in of_derived or metric_key in against_derived` — is unreachable in
a clustered run. Pinned by
`tests/test_cli.py::test_a_clustered_derived_metric_is_refused_rather_than_drawn`, which asserts
`set(aggregated) == {"pred"}` and whose discriminating mutation — `summarize_step`'s own
`seed is not None` guard — was run against the full suite here rather than assumed. That
unreachability is also what makes every clustered
contrast entry carry a `_clustered` `method`, which is the argument H4b-2 task 2 rests on for
recording no `clustered_by` key.

**The row's wording is repaired by H4b-2 task 15**, with every other citation of
`E-DATA-CLUSTER-CONTRAST` that task 14 does not delete, as one sweep rather than two commits over one
claim.

**Ruled by:** H4b-2, task 4. **Owner from here:** H4c.

**Built by H4d, task 15 (2026-08-19), not H4c.** H4c deferred it again on a new ground — building it
while the derived branch's two-ground suppression guard was being written would make one guard
distinguish three states — and named the condition for building it: that the guard has shipped and
survived a whole-branch review. It has, and H4d task 15a built the construction named here:
`stats.percentile_of_derived_clustered`, a per-condition percentile draw over `G` clusters with
replacement, pooling their units into a `UnitTable` built from a row list per replicate. Task 15b
retired `E-DATA-CLUSTER-DERIVED` and routed `stats.summarize_step`'s derived branch through it, and
removed `cli._comparison_step_blocks`' `clusters is None` suppression, so a derived paired contrast
under `cluster_by` now computes through `stats.paired_percentile_of_derived`'s own clustered branch —
built earlier, for the recorded-column arm — rather than publishing `null` beside `n_paired_clusters`.

**CORRECTION, fix round 1 (task-b1 review, Major 2):** the "H4b-2 does not need it" paragraph above
reasons from a proxy and overstates what it found. `_comparison_step_blocks` iterates
`set(of_summary) & set(against_summary)` from **`aggregated`**, but the branch it takes —
`is_derived = metric_key in of_derived or metric_key in against_derived` — reads **`derived_by_key`**,
a different mapping. Those two disagree in one reachable state: `stats.summarize_step` raises
`E-STEP-KEY-COLLISION` for a derived key shadowing a recorded column **before** its
`clusters is not None and seed is not None` guard; `cli.command_run` assigns `derived_by_key` and
`resample_fns_by_key` **before** calling `summarize_step`; and that call's `except ContractError`
retry re-summarizes with no `derived` but never clears either mapping. So a clustered step whose
derived key collides with a recorded column's name reaches `aggregated` holding the recorded column
while `derived_by_key` still holds the name, and `_comparison_step_blocks` takes the derived branch —
confirmed by a direct call producing `method: 'paired_percentile_over_units'`, unsuffixed, beside
`ci95: [0.6, 0.6]` (task 3's zero-width shape, incidentally).

**The ruling is unchanged** — re-own to H4c, do not build the clustered derived draw, on the
construction-family argument, which this collision does not touch. What is narrowed is the reachability
claim: the derived branch is unreachable in a clustered run **only through `validate` and `run`
end-to-end, and only while `E-DATA-CLUSTER-CONTRAST` refuses cluster + contrast wholesale** — it is
directly reachable today by calling `_comparison_step_blocks` itself, which is not a path `validate`
closes. **Task 14, which retires `E-DATA-CLUSTER-CONTRAST`, must re-check this corner before treating
it as closed** — the collision case, and with it whatever `method`/`ci95` shape a name-colliding
clustered derived metric should record, is not decided by this entry and does not resolve itself when
the wholesale refusal lifts.

**CORRECTION (H4b-2 task 14, fix round 1), the re-check the paragraph above names, done and dated.**
The wholesale refusal is now gone, so the reachability condition above no longer obtains: a real
project whose template's `aggregate` returns a derived key colliding with a recorded column's, under
a declared `cluster_by`, can now reach this corner through `validate` and a genuine `run` end to end
— retiring `E-DATA-CLUSTER-CONTRAST` was exactly what stood between the collision and a real run, not
merely between a direct call and one. Confirmed by reproducing the shape through
`_comparison_step_blocks` directly (`derived_by_key` naming the collided key on both conditions,
`resample_fns_by_key` holding nothing for it — the state the collision's uncleared retry leaves):

```
{'delta': None, 'basis': 'units', 'paired': True, 'method': None, 'n_paired': 12,
 'ci95': None, 'cohens_d': None, 'correction': None, 'n_paired_clusters': 3}
```

Pinned by `tests/test_cli.py::test_a_derived_key_collision_under_a_cluster_still_carries_the_intersection_facts`.

**The decision the paragraph above deferred: `n_paired_clusters` beside a null interval is the record
`reference.md` wants, and no code changes.** `n_paired` is written unconditionally in both branches of
`_comparison_step_blocks` — a fact about the paired intersection, not about whether a construction
ran, and the too-few-units and degenerate-draw shapes already publish it beside a null `method`/`ci95`
with no cluster involved at all. `n_paired_clusters` is `reference.md` § Contrasts' own "scalar
sibling of `n_paired`... a fact about the intersection `n_paired` counts" — the identical class of
fact, so giving it the identical treatment (present whenever `clusters is not None`, regardless of
what the construction that follows manages to compute) keeps the two intersection-facts in the same
class rather than making the newer one conditional on something the older one ignores. Guarding the
write on `interval is not None` would turn `n_paired_clusters` into a claim about the construction,
which its own documentation does not make it. `reference.md` § Contrasts now states this decision
directly rather than leaving it fully open.

**CORRECTION (whole-branch review, DO-NOT-MERGE Critical), replacing the premise of the correction
above — the null shape it pinned was right, but the reason it gave for reaching that shape was
false, and false in a way that let a real defect through.** "`resample_fns_by_key` holding nothing
for it — the state the collision's uncleared retry leaves" is not what the collision leaves.
`command_run` builds a resample closure for **every** key in a step's `derived` mapping (gated on
`if derived:`, before the call that can raise `E-STEP-KEY-COLLISION`), so a colliding key's closures
survive in `resample_fns_by_key` exactly as its name survives in `derived_by_key` — both maps are
populated, not one empty and one populated. `_comparison_step_blocks`'s derived branch therefore had
real callables to compute with, and — verified by an end-to-end `run`, the direct-call fixture above
cannot see this — it published a genuine, UNCLUSTERED `paired_percentile_over_units` delta and
interval beside `n_paired_clusters: 3`, on a real project, with `validate` reporting zero errors.
This is the exact failure decision 2 named as the reason the retirement had to come last, newly
reachable on this branch because `E-DATA-CLUSTER-CONTRAST` no longer blocks the config from
running at all.

**Fixed, not merely re-diagnosed: a clusters-guarded suppression in `_comparison_step_blocks`'s
derived branch** (`if compute_of is not None and compute_against is not None and clusters is None:`)
— matching the intent this entry, `reference.md` § Contrasts and the test's own docstring already
claimed, now actually enforced. Deliberately not "clear both maps in the `except ContractError`
retry": that would also change the pre-existing **unclustered** collision path, out of this slice's
scope. Pinned end to end by
`tests/test_cli.py::test_a_derived_key_collision_under_a_cluster_end_to_end`, which runs a real
project through `main(["run", ...])` rather than a direct call, and fails on `entry["delta"]` when
the suppression is removed — checked against the full, unfiltered suite (one failure, the pin
itself; the shipped test's own name and premise corrected in the same commit).

**RE-DECLINED 2026-08-18 (H4c, task 20), on a new ground — do not build the clustered derived draw
here, owner H4d.** The old ground (cost and reachability, ruled by H4b-2 task 4 above) is used up:
H4c is the slice that gave the derived branch a **second**, independent suppression condition
(decision 8's unpaired ground, added in task 15 beside the pre-existing clustered one, stated as one
guard naming both). Building the clustered derived draw inside H4c would mean that same guard having
to distinguish three states — clustered, unpaired, and neither — rather than two, compounding in one
commit the exact corner that has already been given four wrong grounds in four separate commits
(recorded above: the reachability claim, the uncleared-retry premise, and the two corrections to
both). Building it after the two-ground guard has shipped and stood through a whole-branch review is
strictly safer than building it while that guard was still being written. **Owner: H4d**, the same
terminal slice the other two re-declined filings in this task land on.

Measured at `82310b9`: `cli._comparison_step_blocks` writes `"paired": True` unconditionally at both
metric branches, so no code path produces an unpaired contrast entry and every comparison reaching
that function survived `E-DATA-ALLOCATION-CONTRAST`. That is why H4b-2 built
`paired_t_over_units_clustered` and `paired_percentile_over_units_clustered` and no unpaired
counterparts: they are unreachable, not merely unbuilt.

**The dependency runs the other way for H4c.** The slice that retires
`E-DATA-ALLOCATION-CONTRAST` must build `welch_t_over_units_clustered` and
`unpaired_percentile_over_units_clustered` in the same slice, or a clustered cross-arm comparison
will take a paired construction over an empty intersection. Two tripwires pin it, deliberately
neither of them the obvious "assert `paired` is never `False`", which is a mutation whose branches
cannot differ:

- `tests/test_cli.py::test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch`
  fails the moment either literal becomes conditional. **Scope:** it reads
  `inspect.getsource(_comparison_step_blocks)`, so it is defeated by extracting either `"paired": True`
  write into a helper function — a real gap in the pin, not only a hypothetical one, since the source
  it inspects is exactly one function body.
- `tests/test_validate.py::test_a_contrast_beside_groups_and_cluster_by_draws_the_allocation_refusal`
  fails the moment the allocation refusal stops firing for a declared cross-arm contrast beside
  `cluster_by`. (Fix round 1, Major/Minor review: a second test once duplicated this fixture under the
  name `test_every_unpaired_comparison_shape_still_earns_the_allocation_refusal`, quantifying over
  "every" shape while asserting only this one; it was deleted as non-discriminating rather than kept
  beside an identical fixture. The other unpaired shape — a *generated* cross-arm comparison — is
  pinned separately by two pre-existing tests, neither declaring `cluster_by`, named in this test's
  own docstring. **Renamed again by H4b-2 task 14**, fix round 1: `E-DATA-CLUSTER-CONTRAST` retired,
  so this fixture now draws the allocation refusal alone rather than both, and
  `…_draws_both_refusals` became `…_draws_the_allocation_refusal` — this entry updated to the current
  name, checked by `grep -c` against `tests/`.)

**Ruled by:** H4b-2, task 5. **Owner of the obligation:** H4c.

## RULED by H4c task 1 — the vocabulary, the weighted unpaired refusal, and the unpaired clustered df

Four rulings, made before any construction is built, so a later task cannot bake the answer in by
omission:

1. **`welch_t_over_units` and `unpaired_percentile_over_units` already have § Statistical reporting
   rows.** Confirmed unchanged. They are the spellings tasks 4 and 6 emit.
2. **`welch_t_over_units_clustered` and `unpaired_percentile_over_units_clustered` get NO rows of
   their own.** They are licensed by the `_clustered` suffix rule. H4b-2's decision 5 verbatim: adding
   rows converts a self-maintaining rule into a maintenance obligation nobody owns.
3. **The weighted unpaired pair gets no spelling at all.** `weighted_welch_t_over_units` and
   `weighted_unpaired_percentile_over_units` are refused by `E-DATA-WEIGHT-ALLOCATION-CONTRAST`,
   minted in task 9 as a **standing** narrow refusal — not a `-UNSUPPORTED` build-family code, and
   carrying no "until the estimators exist" hedge. An alternation grep for both stems over `src/`,
   `docs/` (excluding `docs/superpowers/`, which is evidence) and `tests/` returned **zero** at
   `051600c`, so refusing it removes nothing and mints over vapour.
4. **The df of an unpaired clustered *t* is Welch-Satterthwaite over the two cluster-robust per-side
   variances, each side contributing df = `G_s` − 1.** Two rejected readings, named so nobody
   re-derives them: `min(G_of, G_against) − 1` discards a side's information and contradicts "df =
   clusters − 1" on the side it discards; `G_total − 2` is the **pooled** reading `welch_t_over_units`
   refuses by construction.

**Sweep outputs (Step 1), run against `src/`, `docs/reference.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `README.md` and `tests/` — `docs/superpowers/` excluded as evidence:**

```
E-DATA-WEIGHT-ALLOCATION-CONTRAST  → exit 1 (no hits)
weighted_welch|weighted_unpaired   → exit 1 (no hits, once docs/superpowers/ is excluded;
                                       with it included, 8 hits, all in the development record)
welch_t_over_units_clustered|unpaired_percentile_over_units_clustered → exit 1 (no hits)
cohens_ds                          → exit 1 (no hits)
n_of:|n_against|n_clusters_of|n_clusters_against → exit 1 (no hits)
```

Can-fail controls: `grep -rc E-DATA-WEIGHT-CLUSTER-CONTRAST src/publishable/validate.py
docs/reference.md` → 1, 2 (both non-zero). `grep -rc 'n_paired:' docs/reference.md` → 3
(non-zero). All identifiers this task rules on were free at the time of ruling.

**No slice inherits `E-DATA-WEIGHT-ALLOCATION-CONTRAST` as work.** `E-DATA-WEIGHT-CLUSTER-CONTRAST` is
the precedent, a narrow refusal nobody owns retiring — writing this one as a deferral instead is how
an entry comes to read as live work nobody holds.

**Ruled by:** H4c, task 1. **Owner of the obligation:** none — retiring is not owed.

**Addendum (batch-1 review, fix round 1): the mint itself is owed to task 9, not this task.** Task 1
only names and grounds the refusal in prose (`reference.md`, above); it mints no § Errors row and no
§ Validation row for `E-DATA-WEIGHT-ALLOCATION-CONTRAST`, and writes no test. **Task 9 owns both
rows and the pin**: the twin of `tests/test_cli.py::test_the_weight_cluster_refusal_has_both_of_its_rows`
(the H4b-2 precedent for exactly this claim), which task 9's own plan brief cites as "the shape of
the pin that says so" without writing it. Recorded here, at the ruling's own entry, so task 9's
implementer finds the obligation rather than re-discovering it.

## `paired_percentile_of_derived`'s degenerate-draw refusal is row-content-based, and a compute-cancellation still publishes a zero-width interval and a zero-width corrected interval

**Found by the H4d batch-3 review** (2026-08-19, at `4ea6f97`), and confirmed here at fix round 1
against a reachable, non-degenerate-*rows* fixture. `_drawable_content` and the check built around
it in `paired_percentile_of_derived` (H4b-2 task 9, whose own entry records the row-level check) refuse a
draw whose every drawable thing carries the *same pair of rows* — a genuinely constant table. That
is a ROW-content check. It says nothing about a draw whose rows **do** vary but whose two
`compute_of`/`compute_against` calls evaluate to the *same* difference on every draw anyway — the
"plausible but wrong" case that function's own docstring already names in words, with "nothing to
raise": two computes evaluating the identical formula over the identical per-unit data (the
recorded-column contrast's own `_column_mean` closure, called on both sides, is exactly this shape
whenever the two conditions record the metric identically) cancel to `0.0` on every single draw,
rows or no rows, clusters or no clusters.

**Verified reachable end to end**, unclustered, at `d97ec9c` (pre-existing, confirmed by the
reviewer as not introduced by H4d): the batch-3 review's own `_AGGREGATE_STEP` fixture (`pred =
float(i)`, identical under both conditions) publishes `method: paired_percentile_over_units,
delta: 0.0, ci95: [0.0, 0.0], ci95_corrected: [0.0, 0.0]`. **This is the identical shape already
recorded and reasoned about** in the entry titled ("The contrast path discloses nothing about its
resample... Finding 2"), which judged it *not a regression* because `paired_t_over_units` gives the
same zero-width interval for a genuinely constant column and the record is "internally consistent."
That reasoning is sound for a column contrast, where a zero-width interval beside a `0.0` delta
over identical values is the honest answer — there is no sampling variance to report.

**It stops being sound the moment `clusters` enters, which is what H4d task 15b did.** Task 15b
routed a derived-key collision's surviving closures through `paired_percentile_of_derived` with a
`clusters` mapping, and cited the resulting `run.yaml` (`delta: 0.0, ci95: [0.0, 0.0],
ci95_corrected: [0.0, 0.0], n_paired_clusters: 3`) as its end-to-end verification that the fix
works — without noticing that the fixture reaching that record was **also** compute-degenerate (a
derived key whose `aggregate` recomputes the exact value already recorded, over exactly the
intersection both sides share), so the record proves nothing about the clustered construction and
is a second instance of the same unfixed gap, now beside a *cluster count* that makes the record
look more authoritative than it is: `n_paired_clusters: 3` beside a zero-width interval reads as "3
independent clusters agree on zero," which `reference.md` § Statistical reporting's own words
refuse — "a zero-width 95 % interval is not [honest]; reporting a point with no interval is
honest" — for a construction that, unlike a genuinely constant column, had no way to tell its
caller the cancellation was coming.

**Not a regression, and not owed to any slice that already ran.** `paired_t_over_units` over a
constant column has the identical shape and the identical honesty; the difference `_drawable_content`
cannot see is COMPUTE cancellation on VARYING rows, which no row-content check can catch by
construction — it would have to run `compute_of`/`compute_against` on more than one draw and compare
outputs, which is exactly what a resample already does, so the fix is a variance check on the
resulting pool (`len({round(v, ...) for v in values}) <= 1`, content-based over the DRAWN VALUES
rather than over the rows feeding them) rather than a structural one over `collapsed`/`strata`/
`clusters` alone.

**Owner: unassigned, and stated as such rather than deferred.** No slice remaining in the spine has
this function as its surface — H4d is the last whose surface is the `statistics` block — so naming a
successor here would be the *"whichever slice does X"* form this file's own H4c entry rejects by name.
It is recorded as a **live gap with no owner**, which is the honest shape, and the check below is
written so whoever does claim it needs no re-derivation: after the resample loop collects `values`, refuse
(`interval=None`, `draws_used=len(values)`, matching every other degenerate-draw return in this
function) when every surviving value is identical — content over the COMPUTED POOL, the value-level
counterpart to `_drawable_content`'s row-level check, checked whether or not `clusters`/`strata`
were declared. A test fixture needs rows that genuinely vary (so `_drawable_content`'s own check
does not fire first) with `compute_of`/`compute_against` that still cancel to the identical
difference on every draw — the recorded-column `_column_mean` closure over two conditions recording
one metric identically is the shape already reachable through a real `run` today, clustered or not.

## OPEN — a derived metric's permutation null has no clustered construction — **Owner: unassigned**

`reference.md` § What isn't a repeat gives `null_test`'s relabelling two designs, gated on
`cluster_by`: "within clusters, or whole clusters at a time." H4d task 20 built the write for a
derived metric's own `p_value` (`stats.permutation_of_derived`, task 12), and measured directly
against Fixture C's roster: `permutation_of_derived` performs one free `rng.shuffle` over every
unit's label and takes no cluster argument at all, so a design declaring `cluster_by` gets the
**wrong** relabelling — the spec's own "permutes across clusters (the wrong stratum)" answer
(≈0.4845 on Fixture C), not the within-cluster `1/5001` a declared `cluster_by` promises. No
clustered counterpart (`permutation_of_derived_clustered`, on `percentile_of_derived_clustered`'s
precedent) exists in this build.

**Not silently shipped as the wrong number, but incomplete on disclosure.**
`stats.summarize_step` gates the whole write — `p_value`, `null_draws`, and the `null_test` echo —
on `clusters is None`: a derived metric under a declared `cluster_by` gets no p-value at all rather
than one whose `level` echo would claim a construction that did not run. That much is right — no
number is published that the construction did not earn. **What is not right, and is a second, live
half of this same gap:** the three keys are simply absent, which is the exact shape a run that
declared no `null_test` at all writes — so a user who DID declare one beside `cluster_by` gets a
record indistinguishable from one that declared nothing. `p_value: null` beside the echo (§
Statistical reporting's own precedent, "the resolved `null_test` echo sits beside the `null` p-value,
which says the test ran and produced nothing") is not the fix either: the test did not run here at
all, so writing that shape would claim the opposite of what happened. No run-level disclosure exists
either — `null_test` never reaches `assemble_run_yaml`. This needs either a warning (`validate`
cannot fire it, since it cannot know whether a template's `aggregate` will produce a derived metric
at all — a declaration-time refusal would have to refuse `null_test` + `cluster_by` outright, which
is a design call this entry does not make) or some other run-time disclosure; left open rather than
guessed at. The contrast-side write (task 19, `stats.permutation_over_contrast`) is unaffected: it
delegates to `permutation_over_units_clustered` (task 13), which does carry the within-cluster
construction, so Fixture C1's `1/5001` is genuine and only the derived (C2) side is gapped.

**Owner: unassigned.** Closing it needs a new construction (`permutation_of_derived_clustered`)
outside what task 20's own file list scopes (`stats.py` only for `summarize_step`'s signature), so
naming a successor here would invent one the plan does not have. Whoever claims it: draw `G`
clusters' worth of labels as one unit exactly as `percentile_of_derived_clustered` draws `G`
clusters' worth of rows, and gate `summarize_step`'s write on that construction existing rather than
on `clusters is None`. Whoever closes the CONSTRUCTION half should also close the DISCLOSURE half
above in the same pass — building the clustered null makes the disclosure gap moot for that path,
but does not retroactively fix the record a run wrote before it existed, and the two are one finding
either way.

**Found by:** H4d task 20, while writing Fixture C2 to the letter its own design spec
(`docs/superpowers/specs/2026-08-18-null-test-design.md` § Fixture C) states — the spec's C2 promised
`p_value: 1/5001` under a declared `cluster_by`, and direct computation against the shipped
`permutation_of_derived` returned ≈0.4845 instead. Reported rather than adjusted: `CLAUDE.md`'s own
rule is to report a fixture that disagrees with the code, not to force the fixture to agree.

**RECONFIRMED 2026-08-19 (H4d task 25, end to end).** Task 25's own run-verified fixture C2
(`tests/test_cli.py::test_fixture_c2_null_test_runs_end_to_end_and_confirms_the_filed_clustered_gap`)
runs fixture C2 through a real `run` — a project-local template's `aggregate`, not a direct call —
and confirms both halves of this gap on live output: `delta_y` computes `2.5` and resamples
(`method: percentile_of_derived_clustered`, `E-DATA-CLUSTER-DERIVED` claimed), and its block carries
none of `p_value`, `null_draws`, or `null_test` — the disclosure half's own "indistinguishable from a
run that declared no `null_test` at all," reproduced rather than assumed. Fixture C1's
`1/5001` (the contrast-side write, task 19) is unaffected and asserted in the sibling test. Still
**unowned**: H4d is the last slice whose surface is the `statistics` block, so this gap has no
successor to fall to.

## OPEN — the contrast-side `null_test` write carries no `null_draws` — **Owner: unassigned**

`docs/reference.md` § Statistical reporting: *"`null_draws` is what the p-value actually rests on …
a metric-block sibling of `null_test`, not a key inside it,"* and *"present in every metric block
carrying a `p_value`."* H4d task 19's contrast-side write (`cli.py`'s unpaired arm of
`_comparison_step_blocks`) writes `p_value` and the `null_test` echo and nothing else — verified by
running Fixture C1 through it and printing the entry's key list: `null_draws` is absent.

**Not a write that was skipped by oversight — a write that has no number to write.**
`stats.permutation_over_contrast` returns `float | None`, no survivor count, because it delegates
entirely to `permutation_over_units`/`permutation_over_units_clustered`, neither of which returns
one either (unlike `stats.permutation_of_derived`, task 12, whose per-draw `aggregate` recompute can
raise or return `nan` and so needs a survivor count to disclose that). Closing this needs a
signature change on whichever of the three functions actually drops draws — and it is not "equal by
construction" for every one of them, which is this entry's second half: **the document's own claim
is false for a clustered whole-cluster relabelling.** In `permutation_over_units_clustered`, a
whole-cluster draw whose relabelling empties the `of` arm is `continue`d (dropped) rather than
counted as a survivor — pre-existing to this slice, task 13's surface — so a contrast under
`shuffle`'s `whole_cluster` level can genuinely rest on fewer than `n` draws, and `null_draws` there
is not `n` "by construction" the way the recorded-column paragraph states. A within-cluster or
unclustered (`rows`) contrast IS exactly `n`, because a permutation there only reorders a fixed
label multiset and can never empty an arm — so the gap is narrower than "every contrast," but the
document does not currently say which shape it applies to.

**Owner: unassigned.** Closing it in full needs: (1) `permutation_over_units` and
`permutation_over_units_clustered` to return `(float | None, int)` — a signature change with real
blast radius, since both are called directly by roughly twenty already-merged tests in
`tests/test_stats.py` expecting a bare `float | None`, so the change must update every one of those
call sites in the same pass, not just the two production functions; (2) `permutation_over_contrast`
threading the count through instead of returning its inner call's result directly; (3) `cli.py`'s
contrast-side write adding `null_draws` to the metric block beside `p_value` and the echo; and (4)
`reference.md`'s "equal for a recorded column by construction" sentence narrowed to the shapes it is
actually true of (unclustered and within-cluster; not whole-cluster). Whoever claims it should do
all four together — a `null_draws` key added without narrowing the document's own claim would still
leave that sentence false.

**Found by:** H4d batch 4's review, verified by running `_fixture_c1_call()` and printing
`block["s"]["y"]`'s key set.
