# Specification defects — gaps found and deliberately not closed

**Read this first. As of 2026-08-25 the charter is complete: every hardening slice H1–H9 and every
sub-slice has merged, and no slice is chartered after them.**

**So an `## OPEN` entry here is not deferred work. It is what this project ships with.** That is the whole
of this file's job now, and it changes how three things read:

- **`Owner: unassigned` means nobody, permanently** — not "the next slice to pass by". Where an entry says
  *"no remaining slice (H5, H6, H9, H3c-3's remaining 14) has this surface"*, the enumeration is a **dated
  record of the reasoning**, not a claim that those slices are pending. They are all merged.
- **An owner reading *"whichever slice next touches X"* resolves to a closed slice**, and is dead as
  written. This file rejects that form by name at its own `RE-OWNED 2026-08-19` entry; the instances that
  survive predate it. **Eight entries carry it**, recounted 2026-08-28 after the removal described below; the
  twenty-four this bullet used to name were counted before it.
- **A closed entry is no longer kept here.** On 2026-08-28 every entry whose own text recorded a closing
  disposition was **removed** rather than left struck — **115 sections of the 267 this file held**, leaving
  152 of which 62 are `OPEN`, and cutting its length by more than half. **Recounted 2026-08-28, later the
  same day: Task 11 of the `growth-chart-gaps` slice removed two more entries closed by code, and a
  later filing was closed by code in the same session and removed under this same rule, which nets
  to 151 of which 61 are `OPEN`.** **Recounted again 2026-08-28, after the `unevaluable` work filed one
  new entry: 152 of which 62 are `OPEN`** — a filing rather than a reopening, and the count moves with it.
  **Recounted again 2026-08-28: the `persisted-findings` slice closed the run-time-warnings-are-never-
  written entry by code and removed it, netting to 151 of which 61 are `OPEN`.**
  **Recounted again 2026-08-29: the build-claim sweep over the four documents filed the `expand`
  numbering divergence, netting to 152 of which 62 are `OPEN`** — a filing rather than a reopening,
  and it closed nothing, so the count moves in one direction only.
  **Recounted again 2026-08-30: re-deriving `feasibility-growth-chart-literacy.md` against the
  source plan's restructure filed two — a config cannot name which comparisons are its family, and a
  fixed-sequence gate has no expression — netting to 154 of which 64 are `OPEN`.** Both were found
  by expressing a real plan and one of them was measured on seven configs, which is the route this
  file's most useful entries have come by.
  **Recounted again 2026-08-30, later the same day: the unescaped-name entry was closed by code and
  removed, netting to 153 of which 63 are `OPEN`.** `generate step` and `generate experiment` now
  refuse a name that cannot be an identifier before anything reaches disk, which is the fix that
  entry's own "the check its owner must make" section specified.
  What went is exactly what said so:
  a struck `~~OPEN~~` heading, a heading declaring `RESOLVED`,
  `CLOSED`, `RETIRED`, `ANSWERED`, `RULED`, `NO DOCUMENT CHANGE` or `NOT A DEFECT`, or a body carrying a
  full closure marker. **A partial closure, a multi-item review record, and every entry with no disposition
  at all were kept**, because deleting the live half of one is the failure this file exists to prevent, and
  four `(as originally filed)` archives went only because the ruling that disposed of them did.
  `git log -p docs/superpowers/spec-defects.md` holds all of it. This replaces the rule in `CLAUDE.md`
  § Checking consistency after any `*.md` edit, which said a closed gap here is struck rather than removed.

**What to trust, from that same review.** Of thirty-three open entries checked against the code,
twenty-eight were accurate and several reproduced every clause including their nuances. **The bodies are
evidence; the headings and owner lines are not.** Five entries were found stating something false at HEAD —
four of them closed by the last two slices and left standing — and those five were struck or amended then;
the struck ones left with the removal above, and that review is also the evidence that removing a struck
entry costs a reader nothing, since it sampled thirteen of them and found **zero false closures**.
**Before building on an entry, grep the symbol it names.**

**Reopening this file's work means chartering a slice**: a dated scoping measured against the code first,
because every charter re-scoped in this project was stale in the same direction.

---


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

**RE-OWNED 2026-08-21 (spec-defects staleness sweep): H1 Validation has shipped (merged
2026-08-11); four of the five sites are fixed and one is genuinely still open.** Verified by
running `validate_config` against probe configs built for this sweep. Three close through
`envelope.check_envelope`'s `LEAF_TYPES` walk, which H1 built: `data.input_dir`/`data.output_dir`
as a list, `metadata.name` as a list, and `data.units.key` as a list each now report
`E-CONFIG-TYPE` rather than crashing, one dotted path apiece. The fourth — `data.units.attributes`
items that are lists or dicts — closes a different way: `check_envelope` cannot reach it, because
`LEAF_TYPES` types the whole `attributes` block a `list` and names no dotted path for a list
*element* (the same reason `sweep.grid`'s axis values aren't in the table either), but
`validate.py`'s own `_check_data` carries a dedicated guard — `isinstance(a, str)` over every
declared attribute name, reported as `E-UNITS-ATTR-MISSING` before `units.py`'s `_from_table` ever
reaches the `columns` set whose membership test would otherwise hash an unhashable name — verified
by probing a config with `attributes: [["a", "b"], {"y": 1}]`, which reports two
`E-UNITS-ATTR-MISSING` findings and does not crash. Only `replication.repeats[i].n` as `"many"` or
as a list still crashes (`ValueError`/`TypeError` inside `int(count)` at `validate.py`'s
repeat-budget loop), because that field sits inside a list item rather than at a fixed dotted path
or behind a dedicated per-item guard like `attributes`' — the same class of gap the
`hypotheses`/`statistics.contrasts` per-entry-key entries elsewhere in this file describe. No
remaining chartered slice has `replication.repeats`'s per-item scalar types as its surface — H5
owns `units.parquet` integrity, H6 owns hashes and provenance, H9 owns
`reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`, and H3c-3 owns folds inside cells, none of
which is "validate a repeat-level's own scalar fields." **Owner: unassigned** — the one remaining
crash site has no home in what is left of the spine.

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

**CLOSED by H5a task 1 (2026-08-22), in half.** `reference.md` § The per-unit tables now states the
rule this entry's live half named as missing — int/float promotion, and the bool/int and str/int
clashes, each with its own worked sentence and a note that the rule is checked only for `.parquet`
(`.csv` writes each row's own `str()` without unifying). **Struck: the S5 prediction that the same
slice "also lands non-numeric recorded columns."** That is a different question — a column that
never disagrees on type within itself but is not numeric at all — and it is **H5b's**, not H5a's;
H5a's task 1 documents an existing, pinned behaviour and adds nothing to it. See the S4a residue
table entry below for that question's own status.

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

**RE-OWNED 2026-08-21 (spec-defects staleness sweep): H4 Statistics is complete (H4d merged
2026-08-19, the last of the family) and neither figure was built.** Verified by reading
`stats.repeat_spread`, current at HEAD:
`if len(levels) > 1 and any(lv.kind == "fold" for lv in levels): return []` still guards the nested-fold case exactly as this entry describes, and the
function still takes no template/`cfg`/callable, so a derived metric still gets no `repeat_spread`
entry — the `resample_fns`-shaped closure this entry calls for was never threaded from `cli.py`.
No remaining chartered slice owns `stats.py`'s per-level dispersion construction: H5 is artifacts,
H6 is hashes and provenance, H9 is `reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`, and H3c-3
is folds inside cells specifically for the holdout-validation refusal, not for `repeat_spread`'s
recompute machinery. **Owner: unassigned.**

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
| The `aggregate` table omits declared unit attributes and non-numeric columns | **Half closed, half open.** Task 13 landed the attributes half — `cli.py` now carries declared unit attributes into the table, with the collapse rule and the namespace fact stated in `reference.md` § Templates; that task's own reframing is worth keeping, since the document was already right and the code was wrong, so this was closing a divergence rather than adding a feature. ~~**The non-numeric-column half is open — RE-OWNED 2026-08-22 to H5 Artifacts, sub-slice H5b**, by name and with the reason: H5a's own plan (`docs/superpowers/plans/2026-08-21-artifacts-write-side.md`, "What H5a refuses to do, with the route") states that a non-numeric column reaching `collapse_repeats`, `summarize_step` or `aggregate`'s table is H5b tasks 11–13's, and H5a "collapses nothing and needs none" of that machinery~~ **STRUCK 2026-08-22 (H5b task 15): the non-numeric half is CLOSED — see the note below this table. The attributes half was already closed by S5 task 13 and is not re-struck.** |
| `limits.max_ineligible_fraction` read by nothing | **CLOSED.** Read by `cli.py`; `W-DATA-INELIGIBLE` exists and has a row in `reference.md` § Warnings core reports |
| `np.str_` / `np.bytes_` refused by `coerce_scalars`'s `__len__` guard | **CLOSED by H5a task 10 (2026-08-22), and the pairing this row drew turned out to bind two different grounds.** Measured against `src/publishable/coercion.py`: `np.str_` is now **admitted**, not refused — it is a `str` by inheritance, and `_coerce_one` admits anything already one of the four scalar types before the `__len__` guard runs at all. `np.bytes_` stays **refused**, and correctly: `bytes` is not one of the four scalar types `CLAUDE.md`'s invariant names (`str`/`int`/`float`/`bool`), so it falls through to the same `__len__` guard a NumPy array does. The row's own "the two share a slice" was right about the routing and wrong to imply one fix — one ground closes a refusal, the other confirms one that was never a bug |
| Bootstrap-vs-analytic tolerance 0.02 against a 0.0198 worst case | **No slice; closed.** Deliberately not loosened; carried as a comment the test still wants |
| `tests/test_cli.py` monkeypatches `STARTER_STEP` | **No slice; closed.** Test ergonomics; inventing a production seam for it would be worse |
| `materialize.py` emits none of the four `statistics` sub-blocks, untested end to end | **Superseded.** Now tracked as a real gap on "The generated config calls itself 'the complete parameter set'" above, since two of the four are built features — **owner H4** |
| A `summary` step's `Estimate` needs a coercion exemption | **CLOSED by S5a**, as the row already records |
| `W-STATS-AGGREGATE-FAILED` covers two events | **No slice; closed.** Verified mutually exclusive per metric and disambiguated by message |

**AMENDED 2026-08-22 (H5a task 12): the "CLOSED by S5a" row above overstates what S5a built, and the
overstatement is corrected rather than the row rewritten.** S5a's own line just above it says the
exemption "had to coerce the `Estimate`'s own fields" — measured against `_coerce_estimate` in
`src/publishable/coercion.py`, that is true of `value` and each `ci95` bound (each passed through
`_coerce_one`) and **false of `method`**: the function's return statement is `method=value.method`,
verbatim, with no call to `_coerce_one` at all. Reproduced: `coerce_scalars({"v": Estimate(value=1.0,
ci95=[0.5, 1.5], method=np.str_("t_over_units"))}, "test", scope="summary")` returns an `Estimate`
whose `.method` is still `numpy.str_`, and `yaml.safe_dump` on that value raises the identical bare
`RepresenterError` this module exists to prevent. **No config-reachable trigger is known** — a
template's `aggregate` chooses its own `method` string as a Python literal, so a NumPy-typed one
would take an unusual template to produce — which is why this is filed rather than fixed; H5a's own
charter is the per-unit table and recorded-row contract, and a `summary`-step `Estimate`'s `method`
field is neither. **Owner: unassigned, with that reason** — no remaining slice (H5b, H6, H9, H3c-3's
remaining 14) has `coercion.py`'s `Estimate` exemption as its surface.

**AMENDED 2026-08-22 (H5b task 15): the `aggregate`-table row's non-numeric half is CLOSED, and the row
above is struck rather than rewritten.** Measured against `src/publishable/stats.py` and
`src/publishable/cli.py` on H5b's branch: `collapse_repeats` carries every recorded value and admits
every unit it was handed, so the table `aggregate` receives holds the non-numeric columns this row said
it omitted — verified end to end through the installed console script on a project recording a bool-only
column, not by reading the collapse. `reference.md` § Templates states the rule (a non-numeric column is
carried and how it collapses across repeats) and § Statistical reporting states which of them earns a
metric block. **The two halves this row paired needed two different closures**, which is why it took two
slices: the attributes half was a divergence — the document was right and the code was wrong — while the
non-numeric half was a behaviour change to what `aggregated` reports, and it is disclosed as one. The
routing sentence further up this file (under § `units.parquet` type unification across rows within a
column) points at this row for that question's status and needs no edit: it points at the row, and the
row now carries the answer.

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
| ~~The second empty-level gate in `cli`'s stratum loop is unpinned~~ | ~~**RE-OWNED 2026-08-22 to H5 Artifacts, sub-slice H5b, by name.** H5a's own plan (`docs/superpowers/plans/2026-08-21-artifacts-write-side.md`, "What H5a refuses to do, with the route") routes "the second empty-level gate in `cli.py`'s stratum loop" to H5b task 15 by that description; the gate goes live exactly when non-numeric recorded columns land, which H5a does not build, and the gate is not deleted in the meantime~~ **STRUCK 2026-08-22 (H5b task 11): PINNED.** See the note below the table |
| A `report_by` whose every level is empty produces no `by` block and no diagnostic | **H4 Statistics**, which owns `report_by` hardening. A new warning identifier, so it is H4's to mint and to add to `reference.md` § Warnings core reports |
| `E-STATS-CONTRAST-UNKNOWN` renders with `!r` where `E-STATS-REPORTBY-UNKNOWN` does not | **No slice; closed as deliberate.** The row already argues it: showing the repr distinguishes `1` from `"1"` where the value has not been narrowed to `str` |
| A stratum level whose every resample draw is degenerate records `resample_draws: 0` with no console warning | **H4 Statistics.** The record carries the count, so only the disclosure is missing; the parent-level sibling `W-STATS-AGGREGATE-FAILED` already warns, and H4 owns both sides of that asymmetry |

**STRUCK 2026-08-22 (H5b task 11): the second empty-level gate is PINNED — and this entry's own
account of why it was unreachable was wrong.** The pin is
`tests/test_cli.py::test_fixture_h_the_all_non_numeric_level_is_absent_the_numeric_one_present`
(H5b task 4, Fixture H), and task 4's mutation (iii) — `if True:` in place of the gate — already ran
against the full suite and failed it, recorded in
`.superpowers/sdd/2026-08-22-non-numeric-columns-downstream/task-b2-report.md`. That result is cited
rather than re-run: **re-running a mutation whose result is recorded is not evidence, and running it
against a stale checkout is worse.** `reference.md` § Reporting strata now states the rule the gate
enforces, so the gate has a document as well as a test.

**The correction to this entry's own reasoning.** It said the gate was unreachable *"because the
first gate (`if not level_collapsed: continue`) already catches every empty level a numeric-only
table can produce."* That names the wrong mechanism as the operative one. The measured reason is
narrower and is about the **collapse**, not about the first gate: before H5b task 4,
`collapse_repeats` did not admit a unit whose every recorded value was non-numeric at all, so no
level could hold rows that produced no metric entry — the second gate went live exactly when the
collapse started admitting such a unit. The first gate would still have been the one to fire for a
level with **no rows**; it was never the reason a level with rows and no numeric column was
unreachable, because that state did not exist. *A filing's claims about the code go stale like any
other comment; when you change code an entry describes, re-read the entry.*

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

**RE-OWNED 2026-08-21 (spec-defects staleness sweep): H4 Statistics is complete (H4d merged
2026-08-19) and the design decision this entry named — omit the entry, or write `std: null` —
was never made.** Verified by reading `stats.repeat_spread` at HEAD: a declared level resolving to
one contributing member still appends
`{"std": math.sqrt(variance), "n": len(member_means), "kind": level.kind}` with no `n == 1` special case, so `std: 0.0` is still written for exactly the shape
this entry describes, and `reference.md` § The two files still records the omit-versus-zero choice
as open rather than decided. No remaining chartered slice owns `stats.py`'s `repeat_spread`
construction (see the entry above, "Two `repeat_spread` figures the S4a passenger declines to
compute" — same function, same absent owner, same reasoning: not H5 artifacts, not H6 hashes, not
H9's CLI surfaces, not H3c-3's folds-in-cells). **Owner: unassigned.**

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

**CLOSED by H5a tasks 5 and 8 (2026-08-22), for every config; the value hijack survives for a
direct caller, filed separately below.** Task 5 minted `E-UNITS-ATTR-COLUMN` and gave
`RESERVED_COLUMNS = ("unit", "measurement", "by")` — a set of column names, not `Unit` field names,
exactly the distinction this entry's second note asked for — a single reader in `units.py`'s three
`_from_table`/`_from_glob`/`_from_resolver` roster builders; `data.units.attributes: [unit]` now
refuses at `validate`, and `run` meets the same refusal through `validate`'s gate before its own
`resolve_units` call, so there is one emit path rather than two. This closes the entry for **every
config that validates clean**, which is what the entry's own severity note bounded. Task 8's
one-line dedupe in `_finalize_columns` separately closes the **list** half — `columns` no longer
carries `"unit"` twice — a fix that does not depend on task 5's refusal to be correct, since
`finalize` is called with whatever `UnitList` its caller constructs and `Unit` is on
`reference.md` § The importable surface.

**The severity bound was too narrow, not merely inexact — struck rather than rewritten.** "The
damage is confined to the published `units.parquet`" is false of `read_condition`: § Steps and
artifacts documents a `summary` step reading every condition's own `units.parquet` back through
`io.read_condition(condition, "step02_score", "units.parquet")`, so a shadowed identity column
would also corrupt what such a step computes from — not only what an outside reader trusts. Task 5
closes this path the same way, at `validate`, so the wider bound is retired along with the entry
rather than left live.

**The prediction that the fix "touches `reference.md` § Errors core raises" was wrong, and it is
struck rather than repeated.** Measured: `E-UNITS-ATTR-COLUMN` is documented in § Errors `validate`
reports and in § Validation, and does not appear in § Errors core raises at all — `validate` is
what reports it, the same ground correction 11 of the H5a plan gives for the identical prediction
made about the sibling `E-UNITS-ATTR-RESERVED` filing.

**Residual, filed separately: a directly constructed `Unit` whose attribute is named `unit`.** Task
5's refusal runs at `validate`, over a roster `validate_config` resolves from a config's declared
source; it does not run over a `Unit` a caller builds by hand and hands to `finalize` directly.
Task 8's docstring in `src/publishable/artifacts.py` (`_finalize_columns`) states this in code; see
the entry below for the filing.

## `UpstreamLedger.record` copies a missing hash as `None` rather than refusing it

Filed 2026-08-20 (H8a batch 5 fix round, from the batch-5 review's Minor 2), not fixed here.
`src/publishable/lineage.py`'s `UpstreamLedger.record` reads `record.get("code_hash")` and
`record.get("parameters_hash")` — `.get`, not `[...]` — so an upstream `run.yaml` that parses,
carries a `run_id` and declares this build's own `schema_version` (so `read_run_record` raises
nothing) but is missing one of the two hashes publishes `code_hash: null` (or
`parameters_hash: null`) into `provenance.upstream`, silently. **Verified by running**: a
synthesized upstream record missing `code_hash` produced an entry
`{'run_id': …, 'code_hash': None, 'parameters_hash': None, 'used': [...]}` with no refusal anywhere
in `validate` or `run`. No fixture in this batch covers it — Fixture O's synthesized upstreams never
assert the two hashes, and Fixture R, which does, reads them from a genuine `run.yaml` that always
carries both.

**Not fixed, deliberately.** Decision 8 (`docs/superpowers/specs/2026-08-20-lineage-design.md`)
states H8a's obligation as "that the four keys are true," and a hand-edited or partially-written
upstream record missing a hash is exactly the case `read_run_record`'s own
`E-UPSTREAM-RECORD-UNREADABLE` ("edited or truncated") already names for a missing `run_id` — but
that check does not extend to `code_hash`/`parameters_hash`, and widening it is a real design
question this batch is not positioned to settle: is a hash-less upstream record a corrupt one
(refuse it, the `E-UPSTREAM-RECORD-UNREADABLE` reading), or an honest one from a build that wrote
fewer keys (`None` is the correct answer, the reading `apparatus`/`allocation` already establish
for "this run declared no such feature")? The two readings disagree, and settling it belongs to
whoever next reads these hashes for a purpose that depends on their truth.

**Owner: H9** (`reproduce`, § Reproducing on another device), which walks a resolved `run_id` back
through its own recorded ancestors — the design's own routing for "walking a chain deeper than one
hop, and reporting an unreachable ancestor" — and secondarily **H8b** (`diff`), which reports "two
runs differ only because their upstreams did" and so is the other consumer that would observe a
silently-`None` hash as a false absence of drift. **The check to run before dispositioning it**:
whether `read_run_record` should refuse a record missing either hash (widening
`E-UPSTREAM-RECORD-UNREADABLE`'s existing "no `run_id`" check to the same two fields), or whether
`UpstreamLedger.record` should carry the missing-hash case through as `None` on purpose and say so
in `reference.md` § Lineage between runs, which currently states only the present case.

**DECLINED and RE-OWNED 2026-08-24 (H9c task 14): the ground this entry was routed to H9 on is
FALSE of `reproduce`.** The owner line above says H9 *"walks a resolved `run_id` back through its
own recorded ancestors."* Re-read against `reference.md` § Reproducing on another device: **it does
not.** That section's seven steps read one record's `provenance.git` (remote and commit), its
`environment` (the lockfile hash), its embedded `config`, and its `apparatus.facts`;
`provenance.upstream` is named in **none** of them. Confirmed against the built command:
`grep -n "upstream\|UpstreamLedger\|read_upstream" src/publishable/reproduce.py` returns **no
hits** — `reproduce` reads a record through `lineage.read_record_file` and never through
`UpstreamLedger`, and it walks no chain of any kind. So H9c cannot settle the design question this
entry poses, and taking it in order to strike it would be worse than declining it.

**Owner: unassigned, with the reason** — no remaining slice has `lineage.py`'s upstream ledger or
§ Lineage between runs as its surface: H9d is `demo`/`docs`/`list-templates` and H3c-3's remaining
14 is folds and holdouts inside cells. **Secondarily H8b's `diff`**, which this entry already names
as the other consumer that would observe a silently-`None` hash as a false absence of drift — H8b is
complete, so that is a name for whoever reopens `diff`, not a live owner. **The check its closer
must make is unchanged** and is stated two paragraphs above: refuse a record missing either hash
(widening `E-UPSTREAM-RECORD-UNREADABLE`), or carry `None` through on purpose and say so in
§ Lineage between runs.

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

**RE-OWNED 2026-08-21 (spec-defects staleness sweep): H1 Validation has shipped and neither
option was taken.** Verified by reading `cli.py` at HEAD: both guards are still inline in
`command_run`, still written `isinstance(x, (int, float)) and not isinstance(x, bool) and ...`
around the `W-DATA-INELIGIBLE` and `W-STATS-STRATUM-THIN` comparisons, with no extracted
function and no removal. No remaining chartered slice has `command_run`'s inline `limits` guards
as its surface — H5 is `units.parquet` integrity and the reserved-column namespace, H6 is hashes
and provenance, H9 is `reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`, H3c-3 is folds inside
cells, and none of them touches this pair of comparisons. **Owner: unassigned.**

## THREE undocumented run-time and creation-command `E-` codes — filed as NINE; six have since been documented (count chain in the two 2026-08-23 amendments)

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
| ~~`E-GIT-NO-REPO`~~ | `provenance.find_repo_root` | **DOCUMENTED 2026-08-23 (H6b task 5, Ruling N)** — its own § Errors core raises row, covering the one raise and all six reach paths |
| ~~`E-GIT-NO-COMMIT`~~ | `provenance.git_provenance` | **DOCUMENTED 2026-08-23 (H6b task 5, Ruling N)** — its own § Errors core raises row, naming why it precedes `E-CODE-DIRTY` |
| ~~`E-CODE-DIRTY`~~ | `cli.command_run`'s phase-2 gate | **DOCUMENTED 2026-08-22 (H6a batch 4, `4c79905`)** — see the 2026-08-22 appended note below |
| `E-INPUT-CHANGED` | `_prepare_run` / `verify_manifest` | the input manifest changed since it was recorded |
| ~~`E-RUN-LOCKED`~~ | `run_identity` | **DOCUMENTED 2026-08-23 (H9b task 16, Ruling X)** — its own § Errors core raises row, covering all four sites (the lock's own claim, the takeover's two, and the report), naming `resume` as the one command it is reachable from and the liveness rule that decides it |
| ~~`E-RUN-ID-EXHAUSTED`~~ | `run_identity` | **DOCUMENTED 2026-08-23 (H9b task 16, Ruling X)** — its own § Errors core raises row, naming `run` and `draft` only, since `resume` allocates no directory |
| `E-PROJECT-EXISTS` | `generators.scaffold_project` | `new`'s target directory already exists and is non-empty |
| `E-EXPERIMENT-EXISTS` | `generators.generate_experiment` | `src/<pkg>/` already exists |
| ~~`E-EXPERIMENT-UNKNOWN`~~ | `generators.step.generate_step` | **DOCUMENTED 2026-08-21 (H8c task 16, `c794029`)** — see the 2026-08-22 appended note below |

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

**APPENDED 2026-08-22 (H6a task 12): H6a documented its own two new codes and took ONE of the nine —
not none, which is what this slice's own design and task brief both say.** The correction matters
because the brief's sentence would have left a documented code sitting in the table above as
undocumented.

- **Its own two**, both minted by H6a and both given a row in `docs/reference.md` § Errors core
  raises: `E-CODE-EMPTY` (one emit site, `cli.command_run`) and `E-CODE-FILE-LIST` (one emit site,
  `provenance.unignored_under_hashed_trees`).
- **`E-CODE-DIRTY`, which is one of the nine in the table above, gained the row it never had** — H6a
  batch 4's controller follow-up, commit `4c79905`, verified with
  `git log -S "E-CODE-DIRTY" --oneline -- docs/reference.md`. It was documented because the batch-4
  review found `E-CODE-EMPTY`'s new row had **no sibling to be consistent with**, which is what made
  an invented `Type` cell reading *(no exception; a `Collector` diagnostic)* look acceptable. So the
  count in the heading above is now **eight**, and `E-CODE-DIRTY` is no longer H6b task 17's to
  document.

**One further row of the table above is stale for a reason that is not H6a's**, measured here rather
than assumed: `E-EXPERIMENT-UNKNOWN` has had its own § Errors core raises row since H8c task 16
(`git log -S "E-EXPERIMENT-UNKNOWN" --oneline -- docs/reference.md` → `c794029`). Swept the same day
over the four documents named individually, the remaining seven fall in three states — `E-GIT-NO-REPO`
and `E-EXPERIMENT-EXISTS` appear only inside *other* codes' prose and have no row of their own;
`E-PROJECT-EXISTS` has a sentence in § Exit codes and diagnostics and no row, exactly as
`E-STEP-EXISTS` does; and `E-GIT-NO-COMMIT`, `E-INPUT-CHANGED`, `E-RUN-LOCKED` and
`E-RUN-ID-EXHAUSTED` appear nowhere in any of the four. **A mention inside another code's row is not
documentation of that code**, which is the distinction this entry's own heading rests on.

**The widening question is untouched and stays the spine owner's.** H6a took `E-CODE-DIRTY` because it
sat one row from a row this slice was already writing, not because the charter grew; nothing here
picks between this entry's two options.

**APPENDED 2026-08-23 (H6b task 8): the count is FIVE, and it is derived here rather than carried.**
H6b took **two** of the nine under Ruling N — `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT`, both raised by
`provenance.py`, the file H6a rewrote, which is a fact about the emit site rather than an argument from
the word *provenance*. Verified by reading `docs/reference.md` and not this entry's own amendments:
`grep -n "E-GIT-NO-REPO\|E-GIT-NO-COMMIT" docs/reference.md` returns four hits, of which two are the
new § Errors core raises rows (the other two are `E-REPORT-OVERRIDE-REPO`'s and `E-STUDY-IN-REPO`'s
cells, which named the code before it had a row of its own and are what the entry three sections below
this one was filed about).

**The chain, each link a documented commit, so the earlier numbers read as way-points rather than as
contradictions:**

| Count | What closed it |
|---|---|
| **nine** | as filed, when every raised `E-` was compared against the four documents |
| **eight** | `E-CODE-DIRTY`, H6a batch 4's controller follow-up (`4c79905`) — the 2026-08-22 note below |
| **seven** | `E-EXPERIMENT-UNKNOWN`, H8c task 16 (`c794029`) — measured in the same note |
| **five** | `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT`, H6b task 5 |

**The five that remain**, and none of them is `E-STEP-EXISTS`: `E-INPUT-CHANGED`, `E-RUN-LOCKED`,
`E-RUN-ID-EXHAUSTED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`. **`E-STEP-EXISTS` was never one of the
nine** — this entry's own paragraph above calls it *"the one sibling that is documented, and only
partially"* — and counting it in is what turned five into six in both the H6b design's and the H6b
plan's first drafts, corrected in both before dispatch. It is recorded as a separate observation at the
end of this amendment.

**Their "a mention inside another code's row is not documentation of that code" states, re-swept
2026-08-23 over the four documents named individually** — `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`:

| Code | State |
|---|---|
| `E-INPUT-CHANGED` | **nowhere in any of the four** |
| `E-RUN-LOCKED` | **nowhere in any of the four** |
| `E-RUN-ID-EXHAUSTED` | **nowhere in any of the four** |
| `E-PROJECT-EXISTS` | one hit: § Exit codes and diagnostics' shared *"every generator with something to protect"* sentence. **No § Errors row.** That sentence is still narrower than the code — `plugin_scaffold.py` raises it for `plugin new` too, which the sentence does not name |
| `E-EXPERIMENT-EXISTS` | two hits, **neither a row of its own**: one inside `E-EXPERIMENT-UNKNOWN`'s § Errors row, which is exactly the mention this entry's heading says is not documentation, and one in the same § Exit codes sentence |

**One correction to the 2026-08-22 sweep, measured rather than carried.** That note placed
`E-EXPERIMENT-EXISTS` in the *"appear only inside other codes' prose"* bucket, alongside
`E-GIT-NO-REPO`. It belonged in `E-PROJECT-EXISTS`'s bucket — a sentence in § Exit codes and
diagnostics plus no row — and had since 2026-08-14:
measured with

```
git log --oneline -S 'generate experiment` reports `E-EXPERIMENT-EXISTS' -- docs/reference.md
```

which names `075455e`, eight days before that sweep. **So the distinction this entry's heading rests on has
now gone stale for one row twice**, which is the argument for re-sweeping it on every amendment rather
than carrying the bucket assignment.

**Owner: unassigned, with the reason.** No remaining chartered slice has `run_identity.py`, the input
manifest path, or `generators/`/`scaffold.py` as its surface. **H9** is `reproduce`, `dry-run`,
`draft`, `resume`, `demo` and `docs` — it reads a run's identity claim and re-derives it, and touches
neither the run lock's own refusals nor a creation command's overwrite guard. **H3c-3's remaining 14
tasks** are folds and holdouts inside cells. The widening question this entry poses — one slice for the
raise-time registry's remainder, or a tenth slice — is **still the spine owner's** and H6b does not
pick between the two options above; taking two codes because their emit site sat inside the file this
family rewrote is not the charter growing.

**Recorded separately, and NOT one of the five: `E-STEP-EXISTS`.** One hit across the four documents,
the § Exit codes and diagnostics sentence, and no § Errors core raises row — the same state
`E-PROJECT-EXISTS` is in, which is why the entry filed at *"`E-GIT-NO-REPO` is named in two normative
§ Errors cells…"* treats the two as one family question. It is an observation about the prose-only
convention, not a tenth code, and it must not be counted into the five.

**Sweep discipline, reported because a checker is a claim too.** Every sweep above ran over a **named
file list**, never over `*.md` and never with the output filtered. Can-fail control:
`grep -c "E-PARAM-MISSING" docs/reference.md` → **1**, on the same four-file list that returns **0** for
`E-INPUT-CHANGED`, so the sweep can find a code the document does carry.

**APPENDED 2026-08-23 (H9b task 16, Ruling X): the count is THREE, and the amendment above's own
sentence is what H9b falsified.** That paragraph reads *"H9 … reads a run's identity claim and
re-derives it, and touches **neither the run lock's own refusals** nor a creation command's overwrite
guard."* The first clause is false of H9b: `E-RUN-LOCKED` is `resume`'s documented refusal — § Resuming
says so in its own text — and `resume` is the one command from which the code is reachable at all, so
H9b took it and `E-RUN-ID-EXHAUSTED` beside it (both are raised in `run_identity.py`, and the second's
row exists to say `resume` never reaches it). Both now carry § Errors core raises rows covering every
site that raises **or** reports them. **The chain gains one link: five → three**, H9b task 16.

**The three that remain**: `E-INPUT-CHANGED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS` — and the
*reason* they are not H9b's is the surface rather than the count. The input-manifest path is a
`_prepare_run`/`verify_manifest` question that `resume` **compares** rather than re-derives (H9b's own
`E-RESUME-INPUT-MOVED` is a different code for a different comparison, and taking `E-INPUT-CHANGED`
because the two sit near each other would be the charter growing), and `generators/`/`scaffold.py` is
no part of `resume` at all. **Owner: unassigned, with that reason** — H9c is `reproduce`, H9d is
`demo`/`docs`/`list-templates`, H3c-3's remaining 14 are cells.

**Re-swept 2026-08-23 over the same named four-file list, and reported rather than carried**:
`grep -c` over `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md` returns **0, 0, 0, 0** for `E-INPUT-CHANGED`; **3** for `E-RUN-LOCKED`, every hit
attributed — its new § Errors core raises row, § Resuming's takeover paragraph, and § One execution at
a time's narrowed *reported rather than assumed dead* sentence; **1** for `E-RUN-ID-EXHAUSTED`, its new
row; and the same `E-PARAM-MISSING` → **1** can-fail control.

## OPEN — `validate_config`'s bare `except ContractError` around `find_repo_root` is wider than its comment claims — **Owner: unassigned**

**Filed 2026-08-23 (H6b task 8), while documenting `E-GIT-NO-REPO`'s six reach paths for Ruling N's
§ Errors row.** `validate.validate_config` calls `find_repo_root(config_path)` inside a
`try` whose handler is a bare `except ContractError`, with a comment reading *"No repo at all."* The
handler sets `repo_root = None`, which skips project-local template discovery and lets every other
check run — correct for `E-GIT-NO-REPO`, and **wider than the comment's claim**: any coded fault the
walk-up ever raises, now or later, is swallowed into the same *"no repo at all"* reading, and a config
whose local template exists then reports `E-TEMPLATE-UNKNOWN` for a reason the diagnostic cannot name.

**Reproduce, by reading the two catch sites side by side rather than by perturbing either:**

```
grep -n "find_repo_root" src/publishable/validate.py
```

Two call sites. The one in `_check_data` catches **by code** — `except ContractError as exc:` then
`if exc.code == "E-GIT-NO-REPO": return` and `raise` otherwise. The one in `validate_config` catches
`except ContractError:` with no code test at all. **The neighbour that already got it right is in the
same file**, which is what makes this a divergence rather than a missing convention.

**Not H6b's.** Narrowing it is a behaviour change to `validate` — a fault the walk-up raises today
would start surfacing where it is currently silent — and H6b is chartered additive: it writes three
`provenance` keys, documents two codes, and edits documents.

**Owner: unassigned, with the reason.** No remaining chartered slice has `validate`'s
template-discovery path as its surface: H9 owns `reproduce`, `dry-run`, `draft`, `resume`, `demo` and
`docs`, none of which is `validate_config`'s walk-up; H3c-3's remaining 14 tasks are folds and holdouts
inside cells.

**Cost if wrong / if unclaimed:** low today — `find_repo_root` raises exactly one code — and it grows
with every future coded fault added to the walk-up, which is precisely when nobody will re-read this
handler's comment.

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

**RE-OWNED 2026-08-21 (spec-defects staleness sweep): H1 Validation has shipped without fixing
this.** Verified by running: a config named `wrong-name-here` under `metadata.name`, validated
via `config_path = Path("config.yaml")` with the working directory already inside the config's
own directory, produces no `E-NAME-DIR` finding among `validate_config`'s output — the exact
failure this entry describes, still live at HEAD. `validate._check_metadata` still reads
`config_path.parent.name` with no `.resolve()`. No remaining chartered slice has
`_check_metadata`'s path handling as its surface (H5 artifacts, H6 hashes/provenance, H9's
CLI commands, H3c-3's folds-in-cells all touch different code). **Owner: unassigned.**

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

**Owner corrected 2026-08-21: `unassigned`, stated as a fact with the reason.** *"Whichever slice next
touches the `limits.min_reported_n` family"* is the form **this file rejects by name** at its own
`RE-OWNED 2026-08-19` entry: it reads as covered while naming nobody, and it resolves to a **closed**
slice the moment that family is touched — which **H8c task 14 then did**, building the `min_reported_n`
prompt without settling the documentation question this entry names. No remaining slice (H5, H6, H9,
H3c-3's 14) has the `W-…-THIN` family's documentation as its surface. **The check its closer must make
is unchanged: decide the rule for the whole family rather than for either check's behaviour.**

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

   **RE-OWNED 2026-08-21 (spec-defects staleness sweep): H2 Sweeps shipped 2026-08-12 without
   deciding this.** Verified by reading `validate.py`'s `_check_sweep` at HEAD: the check still
   reads `swept_axes = list(grid)` and compares only those axes against `baseline_fixed`, and the
   surrounding comment still states the same reasoning this entry gives for why it does not import
   `contrasts.differing_axes`'s wider, union-based semantics. A baseline-only axis (fixed in
   `sweep.baseline` but never swept in `sweep.grid`) still passes `validate` silently and can still
   be written `confounded: true` at run time. No remaining chartered slice owns `sweep.baseline`/
   `contrasts` semantics — H5, H6, H9 and H3c-3 are all elsewhere. **Owner: unassigned.**
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

**NOTED 2026-08-21 (spec-defects staleness sweep, so an `Owner:` sweep does not stop at this
heading): the heading's "Owner: H7 Plugins and the apparatus" and this section's own "Owner stays
H7 — specifically H7b" are both superseded text, not live pointers.** H7 (all parts, including
H7d) is now complete, and this row's own last word is that the remaining work belongs entirely to
the companion entry named above, which already carries `owner unassigned` with H7d's own scoping
confirming no chartered slice populates `Claim.cls` for an installed template. Nothing here is
still asking H7 for anything.

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

**STRUCK 2026-08-21 (spec-defects staleness sweep): CLOSED by H4d task 10.** `statistics.null_test`
was the block this row's disjunction waited on, and H4d built it. Verified by reading
`validate.py`'s current `_check_sweep`: the `fdr_bh` guard now reads `null_test`, computes
`crossed_by_any_comparison` from `crossed_group_axes` over every resolved contrast, and tests all
three disjuncts by name — no `null_test` declared, every comparison differing only on a parameter
axis, or a declared `shuffle` naming an axis no comparison crosses — each with its own `reason`
string in the warning. This is exactly the row's three-way condition, not the accident-of-refusal
placeholder this entry described. Nothing owes this row further.

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

**RE-OWNED 2026-08-21 (spec-defects staleness sweep): H1 Validation has shipped without choosing
either route.** Verified by reading `replication._seed_members` at HEAD: it still derives every
seed from `digest|kind` with no read of a declared `seeds` list, and no `E-REPL-*` refusal for a
`seed` level carrying `seeds` exists in `validate.py` — the field is still silently divergent under
both shapes this entry describes. No remaining chartered slice owns `replication.py`'s `seed`-level
resolution: H5, H6, H9 and H3c-3 are all elsewhere (H3c-3's folds-in-cells touches `fold`, not
`seed`). **Owner: unassigned.**

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

**AMENDED 2026-08-21 (H8b whole-branch fix round): the same `TypeError` class reaches two more
call sites this entry did not name, and one of the three is now closed — locally, not by this
entry's own fix.** `hashes.parameters_hash` (via `hashes._canonical`'s `json.dumps`) hits the
identical fault over `covered_config(config)` — a wider projection than `data.units` alone, since
it covers everything but `metadata`/the two host paths, so a bare date in `limits`, `statistics`,
or an unknown top-level key reaches it too, not only `data.units`. Two callers were exposed:
`cli.command_run` (writing `run.yaml`'s `parameters_hash`, still open, still H3's — `run` validates
first in the ordinary path but a `draft` or a config that otherwise validates clean with a stray
date in, say, `limits` is not caught by any existing check) and `diff._parameters_hash_for`, which
H8b's whole-branch review found tracebacking a config operand after printing four rows
(`src/publishable/diff.py`). **`diff`'s instance is closed**, in `diff.py` itself: a `try`/`except
TypeError` around the one call that recomputes a config side's hash fresh, reraising as
`E-DIFF-CONFIG-UNREADABLE` — the sibling refusal a config operand `diff` cannot read already
carries, chosen over minting a tenth `E-FREEZE`-adjacent code. That closes `diff`'s **surface**, not
this entry's: `run`'s own crash — the one this entry was filed for — is untouched, still reachable
from `command_run`, still H3's to close at the `validate`-time or `design_digest`-canonicalization
level this entry already names as the real decision. Not struck.

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

## A column metric's `resample_draws` records the requested `n`, not a survivor count

Decided in H4a (2026-08-15). `stats.percentile_over_units` returns a bare `Interval` where
`percentile_of_derived` returned `(Interval, int)`, so a recorded column under a declared
`statistics.resample` has no survivor count to record beside its interval. **The asymmetry this
entry rests on is being closed as it is read**: G2 task 2 (2026-08-28) widened
`percentile_of_derived` again, to a `PairedResample` carrying the pool as well, and G2 task 3 gives
`percentile_over_units` the same shape — at which point a column DOES have a survivor count and
this entry's premise expires. The ruling below stands for every build before that; re-read it
against the code rather than carrying it forward.

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

**RE-OWNED 2026-08-25 (H3c-3 task 20), on this entry's own instruction: `unassigned`, and no
slice follows.** H3c-3 did retrofit the holdout to cells — `units.holdout_within_cells` draws the
split inside each populated cell, and task 15 narrowed a `condition`-scoped step's training side
to its own arm — so the conditional half of the owner line above has fired and the entry would
otherwise point at a closed slice, which is what it told its reader not to leave. **The gap is
unchanged and is now wider by one axis rather than narrower:** `_cond_beside_n`'s third argument
is `eval_roster`, which under a cell structure is the holdout's test partition **and** may then
be narrowed to an arm, so `cond_roster is roster` distinguishes neither of the two narrowings from
the other nor either from none. Closing it still needs the un-narrowed roster threaded as a
separate identity reference. Nothing follows this slice; it ships this way.
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

**CORRECTED 2026-08-21 (spec-defects staleness sweep): the count itself has moved again, which
is the entry's own point, not a reason to chase it.**
`grep -rn "stratum_names(" src/publishable/*.py | grep -v "def stratum_names"`, run against HEAD, finds **eight** call sites now
(`validate.py` ×5, `units.py` ×2, `cli.py` ×1) — the heading's "seven" is itself stale, one slice
after H3d added the eighth. Not corrected to "eight" here: a form that names a number goes stale
on the next call site regardless of which number it is, which is exactly why this entry's own
proposed fix — "state what the helper is for and drop the count" — is the one worth taking rather
than re-measuring forever. The substance (a docstring enumeration is a maintenance obligation
nobody owns) stands unweakened by which number is currently wrong.

**RE-READ 2026-08-25 (H3c-3 task 20), because this slice changed code this entry describes** —
`validate._check_holdout` gained the cell decomposition, and a filing's claims about the code go
stale like any other comment. The same grep at this commit finds **nine**, one more again. **Not
corrected to nine, on this entry's own argument**, which is the whole reason the re-measurement is
recorded here rather than written into the heading: the count is the thing that cannot be kept
true. The load-bearing halves — *"written against neither in particular"*, and the proposed fix —
are both re-read and both still hold. **Owner stays `unassigned`, and no slice follows this one.**

**Found by:** H3d, Task 6 review; deferred again at Task 7. **Owner:** whichever slice next
edits `units.stratum_names` — re-owner this entry when that slice finishes rather than
leaving it pointing at a closed one.
**Severity:** Minor. A stale count in a docstring misleads a reader deciding whether a change
is safe, which is exactly the decision this repo's § Development record exists to support.

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

**Owner corrected 2026-08-21: `unassigned`, stated as a fact with the reason.** The line above used the *"whichever slice next touches X"* form **this file rejects by name** at its own `RE-OWNED 2026-08-19` entry — a form that reads as covered while naming nobody, and that resolves to a closed slice the moment X is touched. No remaining slice (H5 Artifacts, H6 Hashes and provenance, H9, or H3c-3's remaining 14) has this surface, so there is no successor to name and saying so is the honest record. The check its closer must make is stated in the entry above; nothing about it changed.

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

**A demonstrated path into it was closed, then a second was found and closed too — the handler
itself is still un-redacted and still reachable by construction.** Task 12's review found
`template.validate(doc)` raising unguarded in `validate.py`, letting a credential-bearing raise
reach this exact handler verbatim, and the fix (commit `cd72c3a`) routed that call through
`Collector.render()` instead. **H7d Part A batch 3 then built a second path**, unrelated to the
first: `apparatus._probe_for` (a plugin's entry-point dispatch, called from `cli.command_run`) sat
outside the batch's own containment `try`, so a probe plugin whose module raised at import with a
declared credential reached this exact handler again, verbatim — found by that batch's review and
closed in the same batch's fix round by wrapping dispatch in a redacting `except BaseException`,
the roster wrapper's own shape. **The handler itself received neither fix and remains reachable by
any other `PublishableError` raised outside a collector** — this is the third time this repo has
shipped this class of leak, and the second time the fix closed one call site rather than the
handler's own construction.

**Owner:** unassigned. Not a task for this slice — closing it would mean giving `main` a way to
know which values are credentials, which is a design question (a module-level or threaded
credential set) rather than a redaction-site fix. Filed with its reasoning rather than as a bug to
patch, per the routing brief.

**Found by:** H7c, Task 12 review; filed at Task 14. **Severity:** Minor today (the one reachable
path was closed in the same slice) but structural — any future `PublishableError` raised with a
credential in its text, outside a collector, reaches stderr unredacted.

**AMENDED 2026-08-21 (H8c whole-branch review, Minor 1): a fourth shape, this one INSIDE a
command's own collector rather than past it.** `report <run.yaml>` and `study add` both read a run
record through `lineage.read_record_file`, and a `run.yaml` corrupt enough that PyYAML's own
`MarkedYAMLError` embeds the offending source line (`f"{path} is not valid YAML: {exc}"`,
`lineage.py:71`) carries that line — credential and all, if the corrupt edit happened to land on
one — into `command_report`'s `Collector()`, constructed **with no `credentials`** because the
record has not parsed yet and there is nothing to derive a credential set from. Verified by
running: a `run.yaml` rewritten to `run_id: x\nbad: [unclosed <SENTINEL>` prints the sentinel
verbatim at exit `1`, while the same project's override-raise arm (a positive control proving the
same collector redacts when it IS populated) prints `<redacted:…>` for the identical value. Same
probe against `diff` — untouched by H8c, shipped on `main` — leaks identically, so this is
pre-existing and structurally forced by the same ordering this entry already names for `main`'s
own handler: the credential set can only be known once the record parses, and a YAML syntax fault
is exactly the failure that happens before it does. Not re-scored: still Minor, for the reason the
entry above already gives — `docs/reference.md` § Secrets & credentials scopes `report`'s own
redaction commitment to *user-code* faults, so this is an honest gap rather than a broken promise,
and it is one instance of the ordering problem this entry is about rather than a second one.**

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

**Owner corrected 2026-08-21: `unassigned`, stated as a fact with the reason.** The line above used the *"whichever slice next touches X"* form **this file rejects by name** at its own `RE-OWNED 2026-08-19` entry — a form that reads as covered while naming nobody, and that resolves to a closed slice the moment X is touched. No remaining slice (H5 Artifacts, H6 Hashes and provenance, H9, or H3c-3's remaining 14) has this surface, so there is no successor to name and saying so is the honest record. The check its closer must make is stated in the entry above; nothing about it changed.

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

## RE-OWNED 2026-08-19, after H4d merged — five entries named H4d as owner and H4d did not claim them

`E-STATS-NULLTEST-UNSUPPORTED` retired with H4d at `3386dc9`, and **five filings still name
`Owner: H4d`**. H4d's own task 23 was the claim/decline pass that should have annotated them; it did
not, and the whole-branch review did not catch it because that review was scoped to code and documents
rather than to the filings' owner state. Recorded here rather than by editing five bodies, so the
sequence stays legible.

The five, by what they are rather than by position: the **finite-inputs premise** for a column
resample; the **`report_by`/`resample_columns` asymmetry** deferred beside the closed zero-width
finding; the two **contrast-disclosure findings** (a contrast-scope `W-STATS-RESAMPLE-THIN`, and the
`beside_n`-shaped parameter both comparison call sites would need); and the **clustered derived
permutation construction**, re-declined most recently on the ground that building it while the
two-ground guard was still being written was the riskier order.

**Owner: unassigned — stated as a fact, with the reason.** Four of the five say in their own words that
they are owned by *"the last remaining slice whose surface is the `statistics` block"*, and one says
plainly that **"a fifth deferral past it is not available."** Both are now true statements about a slice
that has shipped. No remaining slice in
[the spine design](specs/2026-08-08-implementation-spine-design.md) has the `statistics` block as its
surface, so naming a successor here would be the *"whichever slice does X"* form this file rejects by
name elsewhere — and re-declining to a slice that does not exist is worse, because it reads as covered.

**What that costs, said rather than implied.** These are **live gaps with no owner**, which is a
different and weaker position than a deferral: nothing schedules them. Each already carries the check
its closer must make, so none needs re-deriving. What none of them is, is closed.

**The transferable finding is about the pass, not the entries.** A claim/decline task whose output is
*annotations on other entries* leaves **no diff in the files a reviewer reads**, so it can be skipped
silently — unlike a construction task, which fails a gate. A later slice putting a claim/decline pass in
its plan should make its deliverable checkable: either the annotations are asserted by a test that
greps for a closed slice named as an owner, or the pass is dropped in favour of ruling each entry inside
the task that touches its code.

**Found by:** the controller, sweeping `Owner:` lines after H4d merged.

## OPEN — a fact **key** equal to a credential value is not checked by `check_facts` itself, though the diagnostic it produces is redacted at `run` — **Owner: unassigned**

`apparatus.check_facts`'s credential check (Decision 6) compares each fact **value** against every
declared credential's value; it does not compare fact **keys**. `coercion._refuse`, which
`check_facts` calls into for its scalar walk and re-codes as `E-APPARATUS-FACT-TYPE`, interpolates the
offending value's key with `{key!r}`. A probe returning `{<a credential's value>: [1, 2]}` — a
structural value keyed by a credential — reaches `E-APPARATUS-FACT-TYPE` with that credential in the
exception's own message.

**Corrected by H7d Part A batch 3's fix round 1: this is not a live leak at `run`.** The batch 3
review verified by running that the fixture above produces
`E-APPARATUS-FACT-TYPE experiment_type` with the value rendered as
`<redacted:PUBLISHABLE_TEST_TOKEN>` — because `E-APPARATUS-FACT-TYPE` is a member of
`apparatus.APPARATUS_CODES`, and `command_run`'s wrapper redacts every code in that set through a
credential-bearing `Collector` before anything reaches a stream. The original entry's claim
("reaches a diagnostic with that credential in the message") was true of the raw `ContractError`
object and false of what is actually printed — it did not check the render path. **The redaction
this rests on is now individually pinned** (`test_E_APPARATUS_FACT_TYPE_is_individually_pinned_
through_the_wrapper`), closing the qualification the batch 3 review attached to this entry (Major 2:
"the redaction rests on a set membership no test can see").

**What is still genuinely open:** Decision 6's check itself compares values, not keys — the ruling
is stated for *"a fact value,"* not a fact key — so `check_facts` still has no rule of its own
against a credential-valued key; it is `APPARATUS_CODES` membership downstream, not a check inside
`check_facts`, that happens to redact this particular shape today. A future code added outside that
set (or a future call site printing the raw exception rather than a `Collector`) would reopen the
leak with no check_facts-level guard against it. Whether core should also check keys, inside
`check_facts` itself, is the real narrowing question the design does not settle, so this entry
stays open on that question rather than being struck.

**Owner:** unassigned. **Found by:** batch 2's review, verified by reading `check_facts`'s ordering
and `coercion._refuse`'s message format together. **Corrected by:** H7d Part A batch 3, fix round 1,
verified by running.

**The predicted reopening happened, and was closed.** H7d Part B task 4 gave `E-APPARATUS-CHANGED` —
"a code added outside [`APPARATUS_CODES`]," exactly the sentence above — a live call site
(`Observer._observe_one`), and the batch 3 review verified by running that a declared credential
held as a **non-`str`** fact (`check_facts`'s containment check skips any non-`str` value by its own
carve-out, so a numeric credential is never refused there at all) that then moves prints
`E-APPARATUS-CHANGED ... changed: 13579 → 999` to stderr through `main`'s bare, un-redacted printer.
Closed in the same batch's fix round: `cli.command_run`'s containment filter now also admits
`apparatus.STOP_CODES`, so `E-APPARATUS-CHANGED` renders through the same redacting `Collector`
`APPARATUS_CODES` members already use — `redact` is a textual substring replacement, so it catches
the credential's string form even though the fact value that carried it was an `int`. This was an interim fix, and it has since been superseded rather than merely
replaced: H7d Part B task 6 wired a `StopSignal` through `execute_plan`, so a mid-plan
`E-APPARATUS-CHANGED` no longer raises out of it at all and never reaches the widened filter this
paragraph describes — verified by running, narrowing `cli.command_run`'s filter back to
`apparatus.APPARATUS_CODES` alone leaves the full suite unchanged. `test_a_moved_int_valued_credential_is_redacted_through_the_widened_wrapper`
no longer asserts a redacted render; it now asserts the credential is absent from stdout and
stderr entirely, which nothing prints at all being the stronger form of the same property. The
`<redacted:PUBLISHABLE_TEST_TOKEN>` claim above is stale and should not be re-cited as current
behaviour — it describes what happened between the batch 3 fix round and H7d Part B task 6, not
what the code does today.

**Correction, appended 2026-08-20 (H7d Part B batch 5 review, Minor 2): the "no longer asserts a
redacted render" sentence above is itself now stale.** Task 7 gave a mid-plan apparatus stop its own
printed diagnostic again (Decision 14, a fresh redacting `Collector`), so
`test_a_moved_int_valued_credential_is_redacted_through_the_widened_wrapper` once more asserts
`<redacted:PUBLISHABLE_TEST_TOKEN>` present on stderr — the assertion this paragraph said was stale
is current again, additively: `"13579" not in output` is still asserted alongside it. Per
`CLAUDE.md`, this is appended rather than rewritten into the paragraph above, which stays as the
record of what was true between task 6 and task 7.

## OPEN — `check_facts`'s credential containment check skips every non-`str` fact value, so a numeric or otherwise non-`str` credential reaches `apparatus/probes.jsonl` unredacted — **Owner: unassigned**

`apparatus.check_facts`'s credential check (Decision 6) walks only `str`-valued facts; a fact whose
value is an `int`, `float`, or `bool` never passes through the containment comparison at all, by a
carve-out the function states deliberately (a structural or numeric value cannot be compared for
*containment* the way a substring can). Found while closing the entry above: the same fixture that
makes `E-APPARATUS-CHANGED` print a credential unredacted to the **terminal** (an `int`-valued
declared credential that moves) also writes that same value into
`apparatus/probes.jsonl` **on disk**, on every call, whether or not the fact ever changes — verified
by running, two ledger lines each carrying `"serial": 13579` before the moving call. This half is
**pre-existing** (not created by task 4's wiring — `append_observation` writes whatever `check_facts`
lets through, regardless of the gate) and is unrelated to the terminal leak's fix: widening
`command_run`'s containment filter redacts what is *printed*, not what is *written to the ledger
file itself*, and nothing in this codebase redacts a run's own artifacts after the fact.

**The surface is wider than the ledger alone (H7d Part B batch 5 review, Minor 3, appended
2026-08-20).** `provenance.apparatus.facts` holds the FIRST-answered value per fact
(`Observations.facts_document`), and that value is written into `run.yaml` too whenever a record is
written at all — verified by running a clean, non-stopping run with the same `int`-valued declared
credential: the plaintext lands in both `apparatus/probes.jsonl` and `run.yaml`, and nothing prints.
`run.yaml` is not a second, separate gap; it is the same carve-out reaching a second artifact through
the same unredacted write path.

**Owner:** unassigned. **Found by:** H7d Part B batch 3 review, verified by running. **Route, stated
rather than built:** either extend `check_facts`'s containment check to a stringified comparison for
non-`str` scalars (comparing `str(value)` against each declared credential's value), or accept that
a credential declared through `required_env` must not be handed to a probe as a non-`str` fact at
all and refuse that shape at `validate` — a design decision `reference.md` does not currently make
either way, so this entry does not adjudicate it.

## OPEN — the four fact-contract refusals lose the run record mid-plan — **Owner: unassigned**

`E-APPARATUS-RETURN`, `E-APPARATUS-FACT-TYPE`, `E-APPARATUS-FACT-MISSING` and
`E-APPARATUS-FACT-CREDENTIAL` are raised in `apparatus.check_facts`, which `Observer._observe_one`
calls before `append_observation`. None of the four is in `apparatus.STOP_CODES` — Decision 9 rules
they stay contract refusals rather than joining the stop mechanism the two apparatus-*state* codes
(`E-APPARATUS-RAISED`, `E-APPARATUS-CHANGED`) get — so `execute_plan`'s loop does not catch them:
they propagate out of `execute_plan` uncaught, and `cli.command_run`'s own `except ContractError`
around that call catches them only far enough to print a redacted diagnostic and return `EXIT_WRONG`.
`execute_plan` never returns to its caller on that path, so `results` — whatever executions had
already completed inside the loop before the raise — is never received, `assemble_run_yaml` is
never called, and `run.yaml` is never written. The same shape a run-start refusal has always had
(no `run.yaml`, since none existed yet) now also applies **mid-plan**, after real executions have
run and been paid for.

**Measured 2026-08-20 against this branch's HEAD**, by running rather than by reading: a probe
whose declared fact goes missing on its third call (guarding the second planned execution, of four)
gives exit `1`, `E-APPARATUS-FACT-MISSING` on stderr, no `run.yaml` anywhere under the results
directory, and exactly one execution's artifacts on disk (`executions.jsonl` holds one `completed`
line, and that repeat's own step directory holds its recorded units) — every execution paid for, the
record lost, `CLAUDE.md`'s own name for this failure. The other three codes share the call site and
the same absence of a `STOP_CODES` membership, so the same shape is expected of each, though only
`E-APPARATUS-FACT-MISSING` was driven end to end for this entry.

**Unassigned is a fact with a reason:** no chartered slice contains this work. No sentence in
`reference.md` sites a fact-*contract* failure (a probe returning the wrong shape, a credential
leaking through a fact, a declared key never answered) at run time as anything other than an
immediate refusal — the four rows in [§ Errors core raises](../reference.md#errors-core-raises) all
read as ending the command, which was true until a mid-plan call could reach them. There is
therefore no section whose owner this defect could be assigned to without inventing one.

**The checks its owner must make**, rather than a route this entry prescribes:

1. **Whether the fault recurs identically on the next call.** A declaration mismatch
   (`E-APPARATUS-FACT-MISSING`, a probe that never supplies a declared key at all) does — nothing
   about calling the same probe again would supply the missing key, so retrying buys nothing and
   stopping the plan for good, the way `E-APPARATUS-CHANGED` does, is the shape that fits. An
   unreachable apparatus does not — `E-APPARATUS-RAISED` already gets exactly this treatment via
   `STOP_CODES` — but `E-APPARATUS-RETURN`, `-FACT-TYPE` and `-FACT-CREDENTIAL` are shape/credential
   faults, closer to the first case than the second, and this entry does not decide which of the
   two existing mechanisms (or a third) any of the four should join.
2. **What `status` such a record would carry.** [§ What `status` means](../reference.md#what-status-means-and-when-a-run-keeps-going)
   has no row for "the run stopped because what the apparatus returned could not be trusted, as
   opposed to what it reported." `failed` and `partial` are both live candidates and neither is
   compelled by the existing table.
3. **Whether assembling a record on this path costs anything Fixture Z's boundary did not
   measure.** Fixture Z (task 7) measured the zero-results case for the two `STOP_CODES` members;
   whether the same "no record when nothing executed, a record once something has" split holds for
   these four, or whether a shape/credential fault should refuse the whole run's record on
   principle regardless of how much already ran, is not something either fixture answers.

**Found by:** [`docs/superpowers/specs/2026-08-19-apparatus-part-b-design.md`](specs/2026-08-19-apparatus-part-b-design.md)
§ The filings this slice touches (Decision 9), filed here with the measurement the design itself
did not yet have, per the controller's ruling that a ledger line saying "filed" is not a filing.

## OPEN — `max_failed_fraction`'s truncation is undescribed by § What `status` means, on two faces — **Owner: unassigned**

`runner.execute_plan`'s `max_failed_fraction` guard counts **units with no settled answer**, not
failed executions, so a step that completes every execution while recording nothing trips it with
every execution `status: completed`. Measured by running at this branch's HEAD: `units=20`,
`limits.max_failed_fraction: 0.5`, a step that never records — 2 of 5 planned executions run, all
`completed`, `run.yaml` reports `status: completed`, exit `0`. This is task 1's remainder — H7d
Part B's own document task settled [§ What `status` means](../reference.md#what-status-means-and-when-a-run-keeps-going)
for the apparatus alone and named this state explicitly as left open, on the controller's ruling
that a slice about the apparatus may not widen a neighbouring guard's semantics to make its own
document edit tidy. Both halves are one document-versus-code disagreement about one guard, filed
here together rather than split across two entries, so a reader looking for either finds both.

**Two faces, not one — a review this branch ran (batch 1) found the second where the first
report named only the first:**

1. **The `failed` paragraph's `max_failed_fraction` clause is a clause the code contradicts.** The
   paragraph names `limits.max_failed_fraction` among `failed`'s four producers, but the measurement
   above produces `completed`, not `failed`. `partial`'s own **table row** — "stopped early with
   executions already recorded" — already describes the shape correctly; it is the prose paragraph
   below the table that both entries disagree with.
2. **The `partial` paragraph's "one thing produces that" is *also* false, and task 1 sharpened this
   sentence in the same commit that introduced it.** The paragraph reads: "A run that stops early
   can still be `partial`, and one thing produces that: the apparatus becoming unreachable…" But a
   `max_failed_fraction` stop over a **mixed** result set (some executions recorded, some not) also
   stops the plan early and also produces `partial` — measured at this branch's HEAD: `units=20`,
   `limits.max_failed_fraction: 0.5`, a step recording every unit on its first execution and raising
   on every later one, gives 2 of 5 executions run, statuses `[completed, failed]`, `run.yaml`
   `status: partial`, exit `3`. The apparatus becoming unreachable is not the only producer of an
   early-stopping `partial`; `max_failed_fraction` is a second, and the sentence naming "one thing"
   is contradicted by a mechanism task 1 did not touch, in a paragraph task 1 tightened to make the
   apparatus case precise. **The report that named face 1 did not name face 2**; both belong in this
   filing, corrected together.

**Unassigned is a fact with a reason:** the guard belongs to no remaining chartered slice —
[the spine design](specs/2026-08-08-implementation-spine-design.md) § The hardening slices scopes
H8, H9 and H3c-3 elsewhere, and none of the three claims `max_failed_fraction`'s status semantics.
Part B declines it as a neighbouring mechanism's semantics (Decision 5): carrying the two apparatus
stop reasons into `run_status` is this slice's own charter, and re-deciding what the failure
fraction reports would change every run that declares it — every generated config, at `0.2`,
materialized by `materialize.py` — from a slice about something else.

**The checks its owner must make:**

1. **That the current behaviour is pinned with a written justification, to be argued against
   rather than discovered.** `test_max_failed_fraction_is_measured_against_the_test_partition`'s own
   docstring states the reason `completed` is judged correct for the all-completed case today; a
   closer changes that reasoning in the same review that changes the code, not around it.
2. **That the all-completed, mixed, and nothing-completed cases are three separate answers today,
   and may need three separate rulings** rather than one rule covering all three — the two
   measurements above already show the all-completed and mixed cases landing on different statuses
   (`completed` and `partial` respectively) for what is, from the guard's own arithmetic, one
   mechanism.
3. **Which of § What `status` means' passages governs**, given that **no row or paragraph describes
   the all-completed truncation at all** — the table's `completed` row says "every execution in the
   plan completed," which is true of the 2-of-5 case only if "the plan" is read as "the executions
   that ran," a reading the table does not state and the code does not currently contradict only
   because nothing says otherwise.
4. **That `run_status` already carries the `max_failed_fraction` reason after Part B** — `stop.reason
   == "max_failed_fraction"` reaches `run_status` today, unused for anything but keeping its
   truncation-assert sound (Decision 5) — **so the change this guard's owner makes is one mapping
   entry plus the document rows, not new plumbing** — verified against the code rather than assumed
   from this entry.

**Found by:** [`docs/superpowers/specs/2026-08-19-apparatus-part-b-design.md`](specs/2026-08-19-apparatus-part-b-design.md)
§ Ruling from the controller and § What did not survive the re-measurement, and H7d Part B batch 1's
review (Minor 1, the second face). Filed here per the controller's ruling that a ledger line saying
"filed" is not a filing.

**INSTRUCTION 2026-08-21 (spec-defects staleness sweep, making `CLAUDE.md`'s H7d Part B paragraph
true of this entry): the owner is unassigned, and check 1 above is the standing order for whoever
claims it.** `CLAUDE.md`'s H7d Part B entry says of this guard that "it is filed, with its owner
told to argue against that justification rather than discover it" — that sentence describes a
directive, and `Owner: unassigned` on its own does not carry one; nobody has yet been told
anything. So it is said explicitly here, addressed to whoever claims this entry next: **do not
treat `test_max_failed_fraction_is_measured_against_the_test_partition`'s pinned justification as
neutral background to read past.** Open that test, read its docstring's argument for why
`completed` is correct on the all-completed case, and either refute that argument in the same
change that edits the behaviour, or leave the behaviour alone. Discovering that a justification
exists and proceeding anyway is not the standard this instruction sets.

## OPEN — `provenance.resolves_inside_repo` fails open when its `repo_root` argument is not already resolved — **Owner: unassigned**

`src/publishable/provenance.py`'s `resolves_inside_repo(resolved, repo_root)` is a pure path
comparison — `resolved == repo_root or repo_root in resolved.parents` — and does not resolve
`repo_root` itself. Every shipped caller (`validate._check_data`, `generators.experiment.
generate_experiment`, and H8a's `lineage.resolve_run`) passes a `repo_root` that came from
`find_repo_root`, which resolves before returning, so the gap has never fired in production.

**Verified by running** (H8a task-b3 review, "Not checked, or checked only by reading"): with an
unresolved `repo_root` under a path containing a symlinked component (`/tmp` on macOS, which is
itself a symlink to `/private/tmp`) and a `resolved` candidate already computed under the
*resolved* form (`/private/tmp/...`), `resolves_inside_repo` answers **`False`** even though the
candidate is genuinely inside that repo — `repo_root in resolved.parents` never matches, because
one side carries the symlink component and the other does not. The containment check this
function backs (`CLAUDE.md` § Invariants: `input_dir`/`output_dir` may never resolve inside the
git repo) would silently not fire for a caller that hands it an unresolved `repo_root`.

**The check its owner must make.** Either (a) `resolves_inside_repo` resolves `repo_root` itself
before comparing — `repo_root.resolve()`, done once inside the function rather than trusted from
every caller — or (b) the function's docstring states the precondition explicitly (*"`repo_root`
must already be resolved; the caller is responsible"*) and every call site is swept to confirm it
passes one. (a) is cheaper and removes the precondition from every future caller's list of things
to remember; a predicate that fails open on an ordinary-looking unresolved path is exactly the
shape `CLAUDE.md` § Misreadings names as "the proxy is the bug, not the guard" one level down —
here the proxy is *an unresolved path standing in for a resolved one*, not a different kind of
mistake, but the fix is the same: answer the direct question (does the resolved candidate sit
under the resolved repo root) rather than one that is only usually equivalent to it.

**Not a batch defect.** Every H8a test hands `resolve_run` a `repo_root` built from `tmp_path`,
which is already canonical under pytest, so no shipped test is affected either way; this is filed
against the function itself, for the next caller that does not route through `find_repo_root`.

**Found by:** H8a task-b3 review, "Not checked, or checked only by reading", fix round 1.

## OPEN — `nondeterministic` is documented as a `run.yaml` field and a thing `report` notes, and nothing writes it or reads it back — **Owner: unassigned**

**Found by:** H8c task 6, building the Attrition section, which is where § The two files' `run.yaml`
example says a reader would see it.

**The measurement.** Measured 2026-08-21, at `ebf642a`: `nondeterministic` appears **zero** times
in a real project's `run.yaml` and **zero** times in its `executions.jsonl`, over a run whose steps
include a
repeat-scoped one — grepped over both files after a genuine `main(["run", ...])`. It exists in
`src/` only as a `BaseStep` class **attribute** (a step author's own declaration) and as what
`W-REPL-DETERMINISTIC` reads off the step classes at `validate` — never as a value copied onto an
execution record.

**The two document passages this leaves stranded.** § The two files' `run.yaml` example shows
`nondeterministic: false`/`true` on every repeat-scoped execution entry, as if `run` wrote it
per-execution. `design-principles.md` § Not bit-identical reruns says core "records that in
`run.yaml` and notes it in `report`" — two documented obligations (`run` writes it, `report` notes
it) with no code behind either.

**Why H8c task 6 built the Attrition section without it.** A section printing
`nondeterministic: false` for every execution would be reporting a default nothing measured — the
exact shape of a fail-open this repo has closed before by asking whether a field is actually written
rather than assuming a documented shape has code behind it. `test_attrition_section_does_not_mention_
nondeterministic` (`tests/test_report.py`) pins the absence directly against a real run's `execution`
block, so a future build that starts writing the field breaks that test first rather than silently
becoming true underneath an untouched doc passage.

**Why neither H8c nor H4 is the right owner.** H8c's whole remit is read-and-render: nothing in this
slice may alter a run, and writing `nondeterministic` onto an execution record is exactly that. H4 is
the complete family (`docs/superpowers/plans/2026-08-21-report-study.md`'s own CLAUDE.md entry: "H4d
merged on 2026-08-19 — the last of the H4 family") — naming it here would point a live gap at a
slice that will not claim it.

**The check its owner must make.** Whether `run` owes an emitter — copying each executed step's own
`nondeterministic` class attribute onto its `executions.jsonl`/`execution` entry, the way § The two
files' example already shows it — **or** whether `design-principles.md`'s "notes it in `report`" is
the sentence that should go, on the grounds that a step-level declaration a reader can already see in
`src/<pkg>/steps/*.py` needs no execution-level echo. Not decided here.

**Which section it lands in on the day the field is written.** If `run` starts writing it onto an
execution entry, `report`'s Attrition section is where it belongs — `_execution_rows` in
`src/publishable/report.py` already builds one row per execution across `shared`, `conditions[]`
(with the repeat nesting) and `summary`, and a written field would simply be one more key `**entry`
spreads onto that row, needing no new traversal.

**Cost if wrong / if unclaimed:** two documents describe a run-level fact no run carries and a report
section no build renders, and a reader who goes looking for it in a real `run.yaml` finds nothing.

## OPEN — Decision 2's "prints the cheap one first" is not delivered at the real command — **Owner: unassigned**

`docs/superpowers/specs/2026-08-21-report-study-design.md` Decision 2 (line ~124-125): "an override
that yields a cheap section first and an expensive figure last should print the cheap one first."
That claim was unverifiable while `render_with_override`/`render_report` were exercised only by
direct call; H8c task 8's own `command_report` is what makes it checkable at the surface that
actually prints, and it is false there. `command_report` does `text = render_with_override(...)`
then `print(text)` once — nothing reaches stdout until the whole render finishes — and both
renderers (`render_markdown`, `render_html`) join every section's text into one returned `str`
before `command_report` ever sees it. `BaseReport.sections`'s own docstring in
`src/publishable/report.py` was sized down in H8c's fix round to say only what is true: the lazy
generator saves a LATER section's construction cost when an earlier one raises, never a print-order
guarantee.

**Not fixed here.** Streaming output section-by-section would need `command_report` to iterate and
print each section as `render_markdown`/`render_html` produce it, which is a real behavior change to
a shipped command, not a wording fix — out of a review's fix-round scope and not owned by any task
in this slice.

**Why unassigned, stated rather than left implicit (2026-08-21):** `command_report` and the two
renderers are H8c's own surface, and H8c is complete — the family this file elsewhere records as
finished (`docs/superpowers/plans/2026-08-21-report-study.md`'s ledger). None of what remains
charted — H5 (artifacts), H6 (hashes and provenance), H9 (`reproduce`/`dry-run`/`draft`/`resume`/
`demo`/`docs`), H3c-3 (folds inside cells) — touches `report.py`'s render-then-print path, so there
is no slice left to name without inventing one.

**Cost if wrong/if unclaimed:** a reader of the design doc believes an override can make an
expensive figure's slowness invisible by ordering it last; at the real command, it cannot — every
section blocks the first byte of output.

## OPEN — no build path writes a `basis: "repeats"` metric entry, so `study add`'s third prompt branch and five `reference.md` passages describe a shape core never produces — **Owner: unassigned**

Measured 2026-08-21 against `ebf642a`: `grep -n '"basis"'` over `src/publishable/` returns five
emit sites (`cli.py` ×3, `stats.py` ×2) and every one writes `"basis": "units"`. A step-returned
scalar reaches `per_repeat` and gets no `aggregated` entry at all when a unit table is present
(measured on a real run), and a run whose `data.units` is undeclared writes no `aggregated` key
whatsoever. So the present-tense claim that such a metric "says `basis: repeats`, reports the
spread, and omits `ci95`" — `reference.md` § The unit table is the inference base, and its four
sibling passages under § Statistical reporting and the worked-example sections that repeat the
same sentence — describes a shape this build does not produce anywhere. The shipped warning
`W-HYPOTHESIS-INFERENCE-BASE` names the identical shape in its own message ("every metric will be
`basis: repeats`"), so the same gap is asserted twice in the four documents and once in a warning's
own text, and nowhere in the code that would have to write it.

**H8c task 14 (the `min_reported_n` prompt) meets this directly.** Decision 13's own table names
`basis: "repeats"` as one of three entry shapes the prompt must recognize, marks it "Producible
today? No", and rules that the branch ships anyway — built from the document, pinned on a record
synthesized by hand whose docstring says so, because a prompt whose entire job is catching a
disclosure nobody else will should not silently under-report the day a producer lands. That
ruling is implemented (`thin_metric_lines` in `src/publishable/study.py`), and its own docstring
and the fixture exercising it both say the shape is not producible today — no test in this slice
claims otherwise.

**Why this is neither H8c's nor H4's to close.** Writing a metric into `results.conditions[].
aggregated` (or omitting it there in favor of `per_repeat` alone) is `run`'s own work — H8c may
read a record, never alter what `run` writes into one. And the H4 family, which built every other
`statistics`/`aggregated` construction this project has, is complete as of H4d
(`docs/superpowers/plans/2026-08-21-report-study.md`'s own ledger: "H4d ... merged on
2026-08-19 — the last of the H4 family") — naming it here would point a live gap at a closed
slice, the exact re-owning failure `CLAUDE.md` records against a prior entry in this same file.

**The check its owner must make before dispositioning this.** Whether `W-HYPOTHESIS-INFERENCE-BASE`'s
message can be true of any record this build writes — it cannot be, today, since nothing reaches
the `aggregated` block under the conditions the warning describes. Two readings follow, and this
entry states the question rather than pre-deciding it: either the documented shape is the intended
one and `run` owes an emitter that writes `basis: "repeats"` (with its spread and no `ci95`) onto
`aggregated` for a step-returned scalar under a declared unit table, **or** the design has moved to
"a step-returned scalar lives in `per_repeat` and nowhere else," in which case `reference.md`'s five
passages and `W-HYPOTHESIS-INFERENCE-BASE`'s own message owe a rewrite instead.

**Cost if wrong / if unclaimed:** a reader who follows `reference.md`'s present tense into a real
`run.yaml` and greps for `basis: "repeats"` finds nothing, in the same document family that treats
an undated build claim as fact; and `study add`'s own third branch stays forever pinned only against
a hand-built fixture, never against anything `run` produced.

**AMENDED 2026-08-21 (H8c batch 7, fix round 1): the pin itself was at the wrong nesting, so
"reachable the day a producer lands" did not follow as written.** The batch 7 review found
`thin_metric_lines`'s `results.summary` walk read one level too shallow — `run_record.py`'s own
producer writes `summary[e.step_name] = summary_values(r.returned)`, nested by STEP NAME, while the
walker (and all three of this branch's pins, including the `basis: "repeats"` one this entry is
about) treated `summary` as keyed directly by metric name. Fixed in the same commit, with a
real-run pin (a genuine `summary` step returning two `Estimate`s) added alongside the corrected
fixture nesting. This closes the reachability gap the amendment names — the `reported: true`
branch is now genuinely wired to what `run` writes — but it does **not** touch the substance of
this entry: `basis: "repeats"` is still written nowhere, the disposition question above is
unchanged, and the entry stays OPEN, Owner: unassigned.

**CORRECTED 2026-08-21 (spec-defects staleness sweep): "the grep returns five emit sites" no
longer holds as a grep claim; "writes ... at five sites" does.**
`grep -n '"basis"' src/publishable/*.py` now returns **eight** matches, not five: the five original emit sites
(`cli.py` ×3, `stats.py` ×2, all `"basis": "units"`) plus three reader sites this entry's own
opening sentence did not have — `report.py`'s `_CONDITION_METRIC_FIELDS` tuple and `study.py`'s
two reads of an entry's `"basis"` key (`study.py:199` and `:326`), both added by H8c to read the
record this entry is about, not to write it. The **writes** claim this entry rests its argument
on is unchanged and still exactly five; only the bare "the grep returns five" phrasing is now
false of a plain re-run. Say *writes*, not *the grep returns*, and the sentence survives readers
being added without another correction.

## PARTLY CLOSED 2026-08-23 (H6b task 5) — ~~`E-GIT-NO-REPO` is named in two normative § Errors cells for the first time on this branch, with no row of its own, and two call sites let it reach the user uncaught~~; the wider prose-only family stays OPEN — **Owner: unassigned**

**Found by:** H8c task-b9 review (Minor 7 / attack 7), on the batch's own concern in its task report
that stopped one step short of a filing.

`git show main:docs/reference.md | grep -c E-GIT-NO-REPO` → **0**. H8c task 16 is the first commit to
name `E-GIT-NO-REPO` in a normative § Errors cell at all — twice, at `E-REPORT-OVERRIDE-REPO`'s row and
`E-STUDY-IN-REPO`'s, the latter explaining at length that `provenance.find_repo_root` "raises
`E-GIT-NO-REPO` rather than returning `None`." Naming a code in a normative row **is** a widening of what
this document commits to describing: a reader who follows that name today finds no row that is *its own*
— every mention is a cross-reference from a different code's row, never the thing itself.

**And the gap is not merely documentary.** `find_repo_root` is called uncaught at `cli.py:1960`
(`command_run`) and `cli.py:3948` (`_dispatch_generate`), so a `run` or a `generate` invoked outside any
git repository reaches `main`'s bare `except PublishableError` printer under this code, with no row in
either § Errors table describing that path for `new`, `validate`, `run`, or `generate` themselves —
only `report`'s and `study new`'s own conversions of the identical raise are described.

**Same shape, wider scope than one code.** `E-PROJECT-EXISTS`, `E-STEP-EXISTS`, and `E-TEMPLATE-EXISTS`
are in an identical position: named only in § Exit codes' hand-written prose sentence
(`docs/reference.md` § Exit codes and diagnostics, "one rule shared by every generator with something to
protect"), with no § Errors row of their own — and that sentence's own claim about `E-PROJECT-EXISTS`
("`publishable new` reports `E-PROJECT-EXISTS`") is itself narrower than the code, since
`plugin_scaffold.py:169` also raises it for `plugin new`.

**What its owner must do.** Decide whether this whole family (`E-GIT-NO-REPO`, `E-PROJECT-EXISTS`,
`E-STEP-EXISTS`, `E-TEMPLATE-EXISTS`, and their siblings' own prose-only coverage) gets dedicated
§ Errors rows, or whether the prose-sentence convention is deliberate and should say so explicitly
enough that a future audit does not re-open it as a gap. Either way, `E-PROJECT-EXISTS`'s sentence
should name `plugin new` alongside `publishable new`.

**Why unassigned, stated rather than left implicit (2026-08-21):** the family spans `cli.py`'s
run/generate path, `provenance.py`, and the generator modules — no single remaining chartered
slice owns "give every raise-time code its own § Errors row." H5 owns artifact integrity, H6 owns
hashes and provenance proper (not the registry question of which codes get rows), H9 owns the
named commands (`reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`) rather than the error
registry, and H3c-3 owns folds inside cells. The nearest precedent, "Validate-time `E-` identifiers
have no registry" above, was H1 Validation's to close and closed there; this is its raise-time
sibling and no slice was ever chartered to do that half.

**Cost if wrong / if unclaimed:** a reader following a normative code reference finds nothing at the
destination, and `run`/`generate` outside a repository print a diagnostic this document never
describes at its own source.

**AMENDED 2026-08-23 (H6b task 8): the `E-GIT-NO-REPO` half is CLOSED; the family question is not, and
the "Why unassigned" paragraph above is now WRONG about H6.** Task 5 gave `E-GIT-NO-REPO` its own
§ Errors core raises row under Ruling N, and that row was written to cover **all six reach paths**
rather than the single raise: it names the two that surface the code uncaught (`command_run` and the
`generate`/`init` dispatch, at `main`'s printer, exit `1`), the two that catch it **by code** as their
own pass branch (`validate._check_data`, `study._refuse_if_in_repo`), and the two that catch it **by
type**, testing no code (`validate.validate_config`'s bare `except ContractError`,
`cli._preloaded_experiment`'s `except Exception`). **So both halves of this entry's headline are answered
for that one code** — it has a row, and the two uncaught call sites are described at their own source.
The paragraph reading *"H6 owns hashes and provenance proper (not the registry question of which codes
get rows)"* is what a reader would trust and it is false as of today: H6b took exactly that registry
question for two codes, on the narrow ground that both are raised by `provenance.py`, the file H6a
rewrote. It is amended here rather than rewritten in place, because the sentence was true on its date.

**What stays open is the family, unchanged in scope:** `E-PROJECT-EXISTS`, `E-STEP-EXISTS` and
`E-TEMPLATE-EXISTS` each still have only the § Exit codes and diagnostics *"every generator with
something to protect"* sentence and no § Errors row, and `E-EXPERIMENT-EXISTS` is in the same state —
re-swept 2026-08-23 over the four documents named individually, with `grep -c "E-PARAM-MISSING"
docs/reference.md` → **1** as the can-fail control. `E-PROJECT-EXISTS`'s sentence still does not name
`plugin new`, which this entry asked for and no slice has done. **Owner stays unassigned, with the same
reason**, and H6b taking two codes does not make it H6's: the two were taken by emit site, not by a
charter that grew.

**APPENDED 2026-08-25 (H9d task 13): the `E-PROJECT-EXISTS` half is DONE, and this entry is amended
rather than struck** — its `E-PARAM-MISSING` subject is untouched and stands. Task 13's instruction
to re-check that row against the code found the same thing by reading both emit sites
(`scaffold.py`'s `scaffold_project` and `plugin_scaffold.py`'s `scaffold_plugin`), and § Errors'
sentence now names `plugin new` beside `publishable new` with the reason the two share one refusal.
Recorded here because a filing whose claim about the code has gone stale reads as live work nobody
holds — which is this file's own rule, and the document is what changed rather than the code.

## OPEN — a bundle render's heading levels are flat, so a member boundary reads like a section — **Owner: unassigned**

**Found by:** H8c whole-branch review, Minor 7, verified by running.

`render_bundle` (`report.py`) and `_render_markdown_section` (which emits `## ` for every
`Section` regardless of caller) together produce, for a two-member bundle: `## alpha`,
`## Conditions`, `## Deltas`, `## Hypothesis verdicts`, `## Attrition`, `## beta`, `## Conditions`,
… , `## Hypotheses`. A member's own name and its own four sections are siblings at the same
heading depth, so nothing in the rendered artifact marks where one run's block ends and the next
begins, or that "Conditions" under `## beta` belongs to a different run than the "Conditions"
under `## alpha` three headings above it.

**Not a spec violation.** Decision 16 does not rule heading depth, and `Section` (the value class
`self.section(title, body=...)` returns and the four standard sections build) carries no `level`
field at all — so this is a consequence of a design that never needed two heading depths until the
bundle render introduced them, not a document a reviewer can cite against the code.

**The check its owner must make.** The bundle render is the one place two genuine levels exist: a
member (an `## alpha`-shaped boundary) and that member's own sections (nested under it). Options,
cheapest first: (a) bump every section heading to `###` inside `render_bundle` specifically, with
`##` reserved for the member boundary — no `Section` change, a `render_bundle`-local decision; (b)
give `Section` an optional `level` field, defaulted so every existing caller (the four standard
sections, an override's own `self.section(...)`) is unaffected, and have `render_bundle` pass a
deeper one. (a) costs nothing outside `report.py`; (b) is more general and is the one to prefer if
a future renderer ever needs a third level.

**Why unassigned, stated rather than left implicit (2026-08-21):** `render_bundle` and `Section`
are H8c's surface, and H8c is complete. No remaining chartered slice touches report rendering —
H5, H6 and H3c-3 are elsewhere in the code entirely, and H9's commands do not include `report`.

**Cost if wrong / if unclaimed:** a bundle rendered to markdown or HTML and skimmed by heading
alone reads as one long flat document; a reader has to track member boundaries by the plain-text
name rather than by structure, which is a paper's own citable rendering of several runs at once —
exactly the artifact this section's own load-bearing property (member boundaries stay legible) is
about.

## RE-OWNED 2026-08-21, after H8 completed — every remaining "whichever slice next touches X" owner

**This file rejects that form by name** at its own `RE-OWNED 2026-08-19` entry: it **reads as covered
while naming nobody**, and it **resolves to a closed slice the moment X is touched** — at which point the
entry reads as live work someone already declined. Three entries got individual corrections above
(`_flatten_parameters`/`_flatten`, `Param.comment()`, and the `limits.min_reported_n` family, the last
having already been consumed by H8c task 14 without settling its question). **These are the rest**, named
by what they are rather than by position:

- the one owned by *"whichever slice next changes"* a documents-only H3d finding;
- the one owned by *"whichever slice next adds a diagnostic to"* that surface;
- the H3d Task 6 finding deferred again at Task 7;
- the one owned by *"whichever slice next edits `new`'s README emission"*;
- and the one owned by *"whichever slice next edits that paragraph or the provenance table it names
  positionally"* — **whose trigger H8c task 16 already pulled**, rewriting that paragraph while the
  positional phrase survived.

**Owner: unassigned for all of them, stated as a fact with the reason.** The remaining slices are **H5
Artifacts** (`units.parquet` integrity, the reserved-column namespace), **H6 Hashes and provenance**,
**H9** (`reproduce`, `dry-run`, `draft`, `resume`, `demo`, `docs`), and **H3c-3's remaining 14** (folds
inside cells). **None of these five entries falls inside any of those surfaces** — they are documentation
and diagnostic-shape questions about surfaces that already shipped. **Each entry's own check is unchanged
and is stated in its body; nothing here re-derives one.**

**Why this is a consolidated entry rather than five appended corrections.** The `RE-OWNED 2026-08-19`
entry did the same for five at once, on the same grounds: editing five bodies would destroy what each
recorded on its date, and five near-identical corrections would bury the one fact that matters — **that
the form itself is the defect, not any single entry's choice of successor.**

**And the check that would have caught all of this does not exist.** The `RE-OWNED 2026-08-19` entry
recommended *"a test that greps for a closed slice named as an owner"*, and `grep -rn "spec-defects"
tests/` returns only docstring citations. **This entry is the recurrence that entry predicted**, two days
later and at four times the scale — ten entries naming shipped families, seven `unassigned` without a
reason, and eight surviving instances of a form this file rejects in writing. **A recommendation recorded
in a filing is not a check**, which is the same distinction as *a ledger line saying "filed" is not a
filing*.

**Owner of the missing check: unassigned, with the reason.** It would live in `tests/`, and no remaining
slice's surface is this file's own hygiene — so it wants a claimant rather than a schedule. Its shape is
stated here so whoever claims it needs no re-derivation: **parse every `## ` heading not marked closed,
extract its `Owner:` line, and fail on any that names a slice whose merge commit exists on `main`.**

## OPEN — three writers raise a bare traceback instead of a diagnostic for a NumPy scalar nested inside a mapping or list — **Owner: unassigned, no remaining slice has this as its surface**

**Measured at `d2caacf` and reconfirmed at `478639a`, quoted from
`docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md` Decision 5.** `coercion.py`'s own
docstring states its purpose as preventing "a traceback rather than a diagnostic" when a NumPy scalar
reaches a writer — but the walk it backs is flat, over one mapping's top-level values, and three
writers take *any nesting* rather than a flat row set:

- `io.write("x.yaml", {"v": np.float64(1.0)})` raises a bare `yaml.RepresenterError`.
- `io.write("x.json", {"v": np.int64(1)})` and `io.write("x.json", {"v": np.bool_(True)})` each raise
  a bare `TypeError` — `Object of type int64/bool is not JSON serializable`.
- The same two shapes raise identically through `.jsonl`, which encodes one such mapping per line.
- `np.float64` and `np.str_` happen to survive `json.dumps` unraised, because `json` accepts a `float`
  or `str` subclass on sight — which is why only two of the four coerced types are visibly excluded
  here rather than all four.

**A fourth instance, measured 2026-08-27 by [`W4-SCOPING.md`](W4-SCOPING.md) § 2 at `50d1a8a`:**
`io.write("x.json", cfg.parameters)` — a config **node** where a mapping was meant, which is the mistake
a reader of § The importable surface makes before learning about `raw` — raises the same bare
`TypeError: Object of type Node is not JSON serializable`. It widens the class rather than adding a
case: the fault is *any object `json` cannot encode*, not the NumPy types alone, and a closer sizing the
refusal should state it that way.

This is the exact traceback-instead-of-diagnostic class `coercion.py` says it exists to prevent, now
**visibly excluded** rather than merely unaddressed — H5a's own coercion work (tasks 6, 9, 10) widened
`coerce_scalars`'s callers but did not touch `.yaml`/`.json`/`.jsonl`'s own encoders, which take a
parsed structure of unbounded depth rather than a flat row.

**Route, not a fix:** one recursive walk over the structure, applied before each of the three
encoders, coercing a NumPy scalar wherever it sits and raising `ContractError` on anything else the
existing flat rule already refuses — one decision, not three, because the three writers share the
same "anything a NumPy scalar arrived through a library as" argument `coercion.py`'s docstring already
makes for the flat case.

**Owner: unassigned, with the reason.** No slice remaining in the charter (`docs/superpowers/specs/
2026-08-08-implementation-spine-design.md` § The hardening slices — H5b, H6 Hashes and provenance, H9,
H3c-3's remaining 14) has `.yaml`/`.json`/`.jsonl`'s nested-structure encoding as its surface; H5a's own
charter is the write-side integrity of the **per-unit tables and the recorded-row contract**, not of a
writer that takes arbitrary nesting.

## OPEN — a non-`str` column key writes silently through `.csv` and raises a bare `TypeError` through `.parquet` — **Owner: unassigned, same reason**

**Measured at `d2caacf` and reconfirmed at `478639a`, this plan's own find and named in no design.**
`io.write("x.parquet", [{1: "a"}])` raises a bare `TypeError: expected bytes, int found` out of
`_encode_parquet`, uncoded — the same traceback-instead-of-diagnostic class the entry above names, but
for a **column name** rather than a cell value. `io.write("x.csv", [{1: "a"}])` **writes**,
successfully, `b'1\na\n'` — `csv.DictWriter` stringifies a key the same way it stringifies a value.

**Why this is not the same gap H5a's contract sentence closes.** § Steps and artifacts' "a writer
accepts what it can give back" and H5a's own `_check_column_types` speak to a column's **values**; a
column's **name** is a different question the design named in no decision, and folding it into H5a's
scope would have been scope creep beyond what any task here was chartered to build.

**Owner: unassigned, with the same reason as the entry above** — no remaining slice names non-`str`
column keys as its surface, and it shares the recursive-walk-versus-flat-rule shape closely enough
that whoever takes either should read both.

## OPEN — a directly constructed `Unit` whose attribute is named `unit` still hijacks the identity column — **Owner: unassigned, no remaining slice has `Unit` direct construction as its surface**

**The residual left by the entry above on `finalize`'s `unit`-shadow, closed by H5a tasks 5 and 8 for
every config.** Task 5's refusal (`E-UNITS-ATTR-COLUMN`) runs at `validate`, over a roster
`validate_config`/`resolve_units` builds from a config's declared `data.units.from`; it does not run
over a `Unit` a caller constructs directly and hands to `StepIO.finalize`. `Unit` is on
`reference.md` § The importable surface, so this is reachable — not from any config this project's
`validate` can see, but from Python that imports `publishable.Unit` and builds a roster by hand.

**Measured against `src/publishable/artifacts.py`'s `StepIO.finalize` and `_finalize_columns`'s own
docstring** (added by H5a task 8): the attribute-merge loop still does `merged[name] =
owner.attributes.get(name)` for every declared attribute name, unconditionally, so a `Unit(key=...,
attributes={"unit": "HIJACK", ...})` built directly still publishes `[{"unit": "HIJACK", ...}]` in
place of the identity — the dedupe task 8 built fixes the column **list**, not this **value**.

**No guard is built for it, deliberately** — H5a's plan (correction 5) names this as "a fifth stoppage
nobody argued": refusing a directly constructed `Unit` at `finalize` time would be a new refusal with
no config-reachable trigger to test it against, decided by no one.

**Owner: unassigned, with the reason.** No remaining slice (H5b, H6, H9, H3c-3's remaining 14) charters
work on direct `Unit` construction bypassing a config's roster resolution; closing this wants a design
decision — whether `finalize` should defend against a hand-built `Unit` at all — that no slice has been
asked to make.

## OPEN — the H5a design's Fixture E claims a `None` column round-trips as `None` in **both** formats; `.csv` gives back the empty string — **Owner: unassigned, no remaining slice has `.csv`'s null encoding as its surface**

**Measured at `478639a`**, against the two encoders directly:

```
_encode_csv([{'v': None}, {'v': None}])      → b'v\n""\n""\n'   → decodes to [{'v': ''}, {'v': ''}]
_encode_parquet([{'v': None}, {'v': None}])  →                     decodes to [{'v': None}, {'v': None}]
```

`csv.DictWriter` has no null: it writes `None` as an empty field, and `csv.DictReader` reads an empty
field back as `''`. So a column of all `None` survives `.parquet` intact and comes back from `.csv` as a
column of empty strings. The design's **Fixture E** section states it round-trips as `None` "in every row"
for both, which is true of one format and false of the other — the same **per-format** asymmetry the
slice's second controller ruling was issued about, met in a second place and not noticed when the ruling
was written.

**Why this is a filing rather than an edit.** A design records what was decided when it was written and
is corrected by appending; the correction is appended to
`docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md` and this entry is the live half. The
**shipped code is not wrong** — `.csv` cannot represent a null and *"a writer accepts what it can give
back"* is a statement about refusing what it would corrupt, not a promise that two formats agree. What is
open is whether `.csv`'s null should be **refused** the way a `bytes` or a structural cell now is, since
`None → ''` is exactly the silent lossy conversion that rule exists to prevent, and it is the one such
conversion H5a left in place.

**Owner: unassigned, with the reason.** No remaining slice (H5b, H6, H9, H3c-3's remaining 14) charters
`.csv`'s null encoding: H5b's surface is non-numeric columns flowing downstream to `aggregate`, and the
question here is a **write-side refusal** decision nobody has been asked to make. Whoever takes it should
read it beside the two entries above — all three are the same shape, a format-specific lossy or
uncoded conversion that H5a's per-format ruling makes visible without settling.

**This entry is also the slice's own evidence for a rule it kept re-learning.** The gap was measured in
batch 8, recorded in the ledger as *"filed for task 12"*, named by the controller in task 12's dispatch —
and **still not filed**, caught only by task 12's review. *A ledger line saying "filed" is not a filing*,
and neither is a dispatch line.

## OPEN — an unencodable object in a `.parquet` cell raises a bare `pyarrow.lib.ArrowInvalid` rather than a coded diagnostic — **Owner: unassigned, same reason as the two entries above**

**Found by H5a's whole-branch review and measured at `270ff73`; it predates the branch**, verified by
tracing the identical code path on `main`:

```
_encode_parquet([{'v': <an arbitrary object>}])
  → pyarrow.lib.ArrowInvalid: Could not convert <…> with type C: did not recognize Python value type
```

The coercion H5a built refuses what it can **name** — a structural cell, a `bytes` cell, a NumPy scalar it
cannot encode — with `E-STEP-RETURN-TYPE` or `E-ARTIFACT-UNWRITABLE`. An object that is none of those
reaches `pyarrow` and its own exception escapes uncoded, so a user sees a third-party traceback where every
neighbouring fault gives a diagnostic with an `E-` identifier.

**Why H5a did not close it.** The slice's charter is the write-side integrity of the per-unit tables and
the recorded-row contract, and a step returning an arbitrary object is already refused at the step-return
boundary by `coerce_scalars`; this path is reachable through `io.write` with a hand-built row, which is the
same surface as the two entries above.

**Owner: unassigned, with the reason** — no remaining slice (H5b, H6, H9, H3c-3's remaining 14) charters
`io.write`'s uncoded-fault surface. **This is the fourth entry of one shape**, and they should be taken
together: a bare traceback for nested NumPy scalars through `.yaml`/`.json`/`.jsonl`, a non-`str` column
key, a `None` cell silently becoming `''` through `.csv`, and this. Each is a place where *"a writer
accepts what it can give back"* is true of the writer's **named** refusals and silent or uncoded outside
them.

## OPEN — whether `E-STEP-RETURN-TYPE` should ever be forgiving for a genuinely mixed `.parquet` column — **Owner: unassigned, with the reason**

**Filed 2026-08-22 by H5b task 3, discharging a question H5a's own design claimed was already filed.**
§ The per-unit tables used to leave this open in its own prose — *"the more forgiving reading … is a live
question … and is not decided here"* — and H5a's Decision 1 wrote of it *"Filed, not built, owner H5b."*
**There was no such filing.** `grep -n 'more forgiving\|mixed column' docs/superpowers/spec-defects.md`
returns **0 lines** at `ee8085e`; the control, `grep -c 'E-STEP-RETURN-TYPE' docs/superpowers/spec-defects.md`,
returns **4** at the same commit, so the sweep for the phrase can hit when the phrase is really there. Both
greps were re-run for this entry and reproduce. **A design line saying "Filed" is not a filing** — the same
finding this file already records once, for a different gap, now made twice in one slice pair.

**What H5b task 3 decided instead of filing.** The open question had two halves, and this slice answers
both rather than deferring either. On the **read** side, the three mixtures and what each publishes are
Ruling 1's amendment table (`docs/superpowers/plans/2026-08-22-non-numeric-columns-downstream.md`
§ "Ruling 1 — the mixed column") — the single authority every site links to instead of restating, because
a two-case sentence describing a three-case rule has been wrong here more than once. On the **write**
side, `E-STEP-RETURN-TYPE` stays exactly as strict as it is today: a column genuinely `str` for some units
and a number for others, written across repeats, still refuses at the cost of the whole execution's
record. `docs/reference.md` § The per-unit tables and § Statistical reporting now say both halves in the
present tense; this entry is what remains **open** underneath that decision.

**The residual.** Whether the write side should ever be loosened — publishing a `str`-typed column instead
of refusing the run when a step's per-unit values disagree on type — is a real design question the read-side
decision above does not answer, and this slice deliberately did not reopen it: loosening the write would
make a column's published-or-not status depend on the data a run happens to produce rather than on its
config, which is the same cost the read/write split already states in `reference.md`. Reopening it is a
write-side change, not a read-side one, and needs its own argument against the cost stated there.

**Owner: unassigned, with the reason.** No remaining slice (H6, H9, H3c-3's remaining 14) charters the
write side of the per-unit tables as its surface, and H5a — which built that write-side rule — is merged.
Whoever reopens it should read it beside the write-side entries already filed above (the `.csv` null
round-trip, the uncoded `.parquet` object, the uncoded NumPy nesting, the non-`str` column key): all are
the same write-side surface, and this is a fifth entry of a related shape rather than an unrelated one.

## OPEN — `diff`'s `uv.lock` row prints two digests and never names the package whose pin moved — **Owner: H9**

**RE-OWNED 2026-08-24 (H9c task 14): H9d, and the input this entry was waiting on has landed.**
H9c's design § 4 routes it: *which* lockfile is authoritative when a run's own copy and a commit's
own copy disagree is the question H9c's Decision 3 (Ruling AA) answers — the recorded
`uv_lock_hash` is the authority, the run directory's byte copy is the preferred carrier, and the
committed copy is used only when it matches. Rendering **per-package detail lines** underneath the
two digests is `diff`'s surface, not `reproduce`'s: `reproduce` prints no comparison table and
resolves no dependency graph. ~~**Owner: H9d** (`demo`, `docs`, `list-templates`) — the only remaining
slice with a CLI rendering surface, H8b (`diff`'s own slice) being complete and H3c-3's remaining 14
being folds and holdouts inside cells.~~ Stated as a fact with a reason rather than as *"whichever
slice next touches `diff`"*, which this file rejects by name.

**RE-OWNED AGAIN 2026-08-25 (H9d task 14): `unassigned`, with the reason, and the 2026-08-24
re-owning is answered rather than repeated.** *"The only remaining slice with a CLI rendering
surface"* is a **schedule argument wearing a surface argument's clothes**: it establishes that H9d
is next, not that `diff`'s rows are H9d's. `diff` is **H8b's** command, and none of `demo`, `docs`
or `list-templates` renders a `diff` row or resolves a dependency graph — building this here would
mean one slice adding a rendering feature to another slice's command, with no fixture family of its
own to add it to. **H8b is complete and H3c-3's remaining 14 is folds and holdouts inside cells**,
so no remaining slice has `diff`'s output as its surface. The input this entry was waiting on
(Ruling AA's authority question) has landed and stays landed; what is missing is an owner, and
saying so is more useful than an owner who would decline.

**Filed 2026-08-22 by H5b task 15, as the residual of this slice's own cost-if-wrong.** H5b changes what
`aggregated` reports for a config whose `code_hash`, `parameters_hash` and `input_manifest_hash` are all
`identical` between two runs, so the only `diff` row that moves across the upgrade is `uv.lock` — the
row that carries a change in `publishable` itself. **The controller's ruling stands and this filing is
the smaller claim it leaves:** it is not true that no row points at the change; the row that points at
it is the one a reader is least likely to read, and it points at it without saying what moved.

**Both halves of the carrier verified before filing**, by grep rather than by memory:
`grep -rn "uv_lock_hash" src/publishable/*.py` → `cli.py` writes it under `provenance.environment`
(beside `uv_lock: "environment/uv.lock"`), and `diff.py`'s `_figure` reads exactly that key for the
`uv.lock` row in `ROW_LABELS`.

**Reproduced, not reasoned.** Two runs of one config, the second after rewriting `uv.lock` so that one
package's pin moves (`# lock: pkg-a==1.0.0` → `# lock: pkg-a==2.0.0`) and committing it:

```
uv.lock            DIFFERS
  sha256:45cd… → sha256:2d84…
```

`pkg-a` appears nowhere in the output, at exit `0`. **The recipe, inline, because a scratch path is not a
reproduce:** in a test module beside `tests/test_diff.py` (or with the repo root on `PYTHONPATH`),

```python
from tests.test_diff import build          # scaffolds a project, a config and a results dir
from publishable.cli import main, EXIT_OK
from publishable.diff import command_diff  # NOT publishable.cli — that import fails

def test_repro(tmp_path, capsys):
    root, cfg, results = build(tmp_path)
    for pin in ("1.0.0", "2.0.0"):                       # one package's pin moves
        (root / "uv.lock").write_text(f"# lock: pkg-a=={pin}\n")
        subprocess.run(["git", "add", "uv.lock"], cwd=root, check=True)
        subprocess.run(["git", "-c", "user.email=t@e.com", "-c", "user.name=t",
                        "commit", "-qm", "lock"], cwd=root, check=True)
        assert main(["run", str(cfg)]) == EXIT_OK         # two runs, two lockfiles
    a, b = sorted(results.glob("run_*"))
    capsys.readouterr()
    command_diff(a, b)
    assert "pkg-a" not in capsys.readouterr().out        # passes — that is the gap
```

A `uv.lock` must be **committed before** each run or the row takes `not captured` instead, which is why
the commits are part of the recipe. The shipped
`test_h8b_fixture_l_the_lockfile_rows_non_null_path` already builds that state and asserts the exit code
and the two digests' inequality; **it takes no `capsys`**, which is why the missing detail was never
visible to it.

**The symptom this leaves for a user**, which is what makes it worth a filing rather than a note: a
reader diffing two runs sees `uv.lock DIFFERS` beside changed numbers in `aggregated` and cannot tell
from `diff`'s output whether a `publishable` upgrade or an unrelated dependency bump is what moved them.

**A route exists and is not the same as being told.** Every run archives its own lockfile at
`environment/uv.lock` (`cli.py` copies it into the run directory), so a reader *can* diff the two files
by hand and find the package. `parameters_hash`'s `DIFFERS` detail already prints per-parameter deltas
rather than two digests, so a per-package delta is the shape this row's sibling has and it does not.

**Owner: H9**, and the reason is a surface rather than a schedule: `reproduce` is what reads the
environment back, so H9 is the slice that must already decide what a moved lockfile means for a rerun,
and the row's detail lines are the same question rendered for a reader.

**Nothing was minted here to make the change more visible, and that is a decision rather than an
omission.** A fourth hash, a core-version record key, and a `diff` row of its own were each refused by
the controller on the same ground: `uv.lock` already answers *did the environment move*, and a second
carrier for it would be a second source of truth. What is missing is detail on the row that exists, not
a row.

## RE-OWNED 2026-08-22, as H5b completes — five entries name H5b inside their own *reason* for being unassigned

**This is the recurrence the `RE-OWNED 2026-08-21` entry predicted, in the one place its recommended
check would not look.** That entry's proposed test *"parses every `## ` heading not marked closed,
extracts its `Owner:` line, and fails on any that names a slice whose merge commit exists on `main`"* —
and none of the five below names H5b in an `Owner:` line. Each names it in the **enumeration of
remaining slices that justifies** the `unassigned` verdict: *"No remaining slice (H5b, H6, H9, H3c-3's
remaining 14) charters …"*. Once H5b merges, every one of those reasons asserts a closed slice is
pending, which is the same staleness in a different sentence.

**The five, named by their question rather than by position**, all verified with
`grep -n "H5b, H6, H9" docs/superpowers/spec-defects.md` — narrowed to a phrase no line-wrap breaks,
since `grep -n "H5b, H6, H9, H3c-3's remaining 14"` finds only three of the four parenthetical hits: the
one at line 1951 wraps after `H3c-3's` and a single-line grep cannot see across it — plus the
spine-citing variant:

- a `summary` step's `Estimate.method` is not coerced (the `AMENDED 2026-08-22 (H5a task 12)` note under
  § Carried out of the S4a whole-branch review);
- three writers raise a bare traceback for a NumPy scalar nested inside a mapping or list (which cites
  the spine's § The hardening slices list directly rather than the parenthetical);
- a directly constructed `Unit` whose attribute is named `unit` hijacks the identity column;
- the H5a design's Fixture E and `.csv`'s `None → ''` round-trip;
- an unencodable object in a `.parquet` cell raises a bare `pyarrow.lib.ArrowInvalid`.

**The correction, once, here rather than five times in five bodies** — the same form the
`RE-OWNED 2026-08-19` and `RE-OWNED 2026-08-21` entries took, and for the same reason: editing five
bodies would destroy what each recorded on its date. **Read every one of those five reasons with H5b
removed from the list: "no remaining slice (H6, H9, H3c-3's remaining 14)".** That is already the form
the entry filed by H5b task 3 uses, written a day later in the same file, so the corrected wording is not
invented here — it is copied from the sibling that got it right. **Not one of the five changes owner**:
H5b's surface was non-numeric columns flowing downstream into `collapse_repeats`, `summarize_step` and
`aggregate`'s table, and none of the five is that; four are `io.write`'s own encoders and one is
`coercion.py`'s `Estimate` exemption.

**And the missing check is still missing, with its shape widened by this entry.** It wants to parse the
`Owner:` line **and** any *"no remaining slice (…)"* enumeration, because this file has now produced the
same staleness in both. Still **unassigned, with the reason**: it would live in `tests/`, and no
remaining slice's surface is this file's own hygiene.

## OPEN — `W-STATS-COLUMN-THIN` fires once per column, multiplying one fact by the column count on a sub-floor roster — **Owner: unassigned, with the reason**

**Filed 2026-08-22, from the H5b whole-branch review, Minor 3.** Measured with the console script, six
units, a step recording three fully covered numeric columns and a scaffold floor `limits.min_reported_n:
10`:

```
warning W-STATS-COLUMN-THIN  limits.min_reported_n
        condition 0, step 'step01_summarize_units': recorded column 'a' carries a number for 6 unit(s),
        below limits.min_reported_n (10)
   … identically for 'b' and 'c'
```

Three warnings, one fact: the *roster* is below the floor, and no column is partially covered. The
emit site's own comment refuses per-column-per-level on exactly this ground —
*"per-column-per-level would multiply one fact by the number of columns"* — and Ruling 5's own argument
for narrowing the warning was that *"an unconditional warning would fire on runs with nothing wrong."*
Both grounds are satisfied and the warning still over-fires, at a different granularity than either
argument was written against.

**Not closed here.** This is literally what Ruling 5 ordered — one warning per condition, step and
column below the floor — and the § Warnings row is honest about what it names (*"carries a real number
for fewer units than `limits.min_reported_n`"*, not *"is partially covered"*). Narrowing a controller
ruling's just-minted warning inside a whole-branch gate, with no argument against Ruling 5 written down,
would be a behaviour change riding in on a fix round. **Owner: unassigned, with the reason** — no
remaining slice (H6, H9, H3c-3's remaining 14) has this loop's per-column granularity as its surface;
the fix, if made, is narrowing the loop `cli.py:3284` iterates to one warning per (condition, step) that
counts the columns below the floor rather than to one per (condition, step, column).

## An omitted core-schema key validates clean and then kills every execution — **Owner: unassigned, with the reason**

**Filed 2026-08-22, H6a task 12, per Decision 10 and Ruling B.** H6a's `W-PARAM-UNSET` covers the
`parameters` block only. The identical symptom reaches core's **own** schema envelope — `limits`,
`replication`, `data`, and every other block core writes — and nothing reports it: a config that omits
a key `init` materialized validates with zero findings, and a step that reads the omitted path through
`cfg` dies with `E-STEP-PARAM-UNKNOWN` at every execution.

**Reproduced end to end through the installed console script**, not derived from emit sites:

```
publishable new proj
publishable generate experiment --name cohort-pilot --template generic \
    --input-dir <outside-repo> --output-dir <outside-repo>
# delete the single line `  min_reported_n: 10` from configs/cohort-pilot/config.yaml
publishable validate configs/cohort-pilot/config.yaml
    ✓ config valid · configs/cohort-pilot/config.yaml            (exit 0, zero findings)
# add `floor = cfg.limits.min_reported_n` to the scaffolded step's run(), commit, then
publishable run configs/cohort-pilot/config.yaml
    run.yaml: status: failed
    error: 'E-STEP-PARAM-UNKNOWN ContractError: limits.min_reported_n is not a path this config holds'
```

**The code is the same one the `parameters` half names, and that was checked rather than assumed.**
`Node.__getattr__` (`config.py`) raises `E-STEP-PARAM-UNKNOWN` for any absent path, with no special
case for the `parameters` subtree — so the § Warnings row's stated consequence for
`cfg.parameters.<path>` is true verbatim of `cfg.limits.<path>` too. What differs is only that one
half has a warning in front of it.

**Why the exposure is narrower than the `parameters` half, which is the reason this was filed rather
than built.** Core reads its own schema keys **defensively** — `.get` with a default, or a check that
runs before the read — so an omitted core-schema key does not break core itself; the run above reaches
`allocate_run_dir`, writes a `run.yaml`, and records every execution's failure. The only casualty is a
**step** reaching for the key through `cfg`, and core cannot know whether a step does that without
reading the body of user Python, which `CLAUDE.md` § Invariants refuses by name (*"Greenfield only —
core validates declarations and verifies effects; it never inspects the body of user Python"*).

**Closing it needs one of two things this project forbids or has already rejected.** Either a
**defaults structure for the core schema** — the separate defaults file `reference.md` § There is no
separate defaults file forbids, and which does not exist as data today (`materialize_config`
builds literal text lines; only `_parameters_block` reads a `parameter_spec`) — or the greenfield line
crossed so core can see which paths a step reads. Warning on *every* omitted core-schema key without
either would fire on almost every hand-written config for a consequence that usually never arrives,
which is the failure mode `W-PARAM-UNSET` was deliberately narrowed to avoid.

**Owner: unassigned, with the reason.** No remaining slice has core's **schema envelope** as its
surface: H6b is the environment keys, the raise-time registry's remaining rows, and the ruling on
whether `validate` gains a tree-state seat; H9 is `reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`;
H3c-3's remaining 14 are folds and holdouts inside cells. This is deliberately **not** *"whichever
slice next touches the schema"*, the form this file rejects by name.

## `git check-ignore` costs 835 ms at ten thousand paths, and the second axis is unmeasured — **Owner: unassigned, with the reason**

**Filed 2026-08-22, H6a task 12, per controller Ruling G, which accepted the cost as a disclosure
rather than designing around it.** `code_hash` now makes one `git check-ignore -z --stdin` call per
`run`, over every candidate path under `src/**` and `templates/**`. On an ordinary repo that is
invisible — 12.1 ms over this repo's own 53 paths. On a large tree it is not.

**Re-measured on 2026-08-22 on this branch** (the plan measured the same shape at `f8450f9` and got
875 ms; this is a re-run, not a carry), against a committed tree of **10,002** files under the two
hashed trees with the scaffold's four-pattern `.gitignore`, five runs each, minimum reported:

| Call | Time |
|---|---|
| `git -c core.excludesFile= check-ignore -z --stdin`, config-neutralized, all 10,002 paths | **835 ms** |
| `git ls-files -z -co --exclude-standard` — the shape Decision 2 **rejected** | **16 ms** |
| `code_hash_of(hashed_files(root, None))` — the whole walk, read and fold | **370 ms** |

So the exclude question costs **~51× the rejected shape** and **~2.3× the entire hash it is one input
to**. **Decision 2 is not reopened by this filing and must not be reopened by citing it**: `ls-files`
answers a correlated question, its three failure modes are real, and one of them — a submodule's
contents silently dropped from the hash — is silent. Correctness outranks under a second, once per
run, on a tree larger than anything this project has seen.

**The second axis is unmeasured, and that is half of why this is filed.** Both measurements — the
53-path one and the 10,002-path one — were taken against a **four-pattern** `.gitignore`. Cost
plausibly scales with **pattern count** as well as path count, and a repo carrying hundreds of
committed patterns is unmeasured in either direction. Nothing here licenses the claim that paths are
the only axis.

**What a successor reaches for, so it is not re-derived.** H6a's design Decision 6 records the
fallback: `git ls-files -z -co --exclude-standard` **plus** explicit handling of its three failure
modes — a tracked file deleted from the working tree, a tracked file under `__pycache__`, and a
submodule's contents. Each of the three was built against the shipped predicate in H6a batch 2 and
answered correctly, so the comparison a successor needs already exists as tests.

**Owner: unassigned, with the reason.** No remaining slice has hashing **performance** as its surface,
and none has `hashes.py` or `provenance.py` at all: H6b is the `provenance.environment` keys, the
raise-time `E-` registry's remaining rows, and the `validate` tree-state ruling; H9 is `reproduce` and
the other second-entry commands; H3c-3's remaining 14 are folds and holdouts inside cells. Not
*"whichever slice next touches the hash"*.

## OPEN — an uncommitted root `.gitignore` decides what `code_hash` covers, and the dirty gate cannot see it — **Owner: unassigned (see the 2026-08-23 amendment; H6b considered and declined it)**

**Filed 2026-08-23, H6a's whole-branch fix round, from the gate's Major 3.** `code_hash`'s exclude
question is `git check-ignore`, which answers from the **working tree**. So a `.gitignore` that is
edited-and-uncommitted, or never committed at all, narrows the published `code_hash` exactly as a
committed one does — and the run's identity claim is then unreproducible from a clone of its own
commit, which is the failure `docs/reference.md` § How the three are computed exists to argue against.

**Measured on 2026-08-23**, on a repo whose `src/pkg/notes.log` is untracked and whose root
`.gitignore` has an uncommitted `notes.log` line:

```
git status --porcelain                     →   M .gitignore
git status --porcelain -- src templates    →  (nothing — the gate is clean)
git_provenance(...).code_dirty             →  False
hashed_files(root, the run's predicate)    →  ['src/pkg/step.py']   (notes.log dropped)
```

**The boundary that makes this narrow.** A `.gitignore` **inside** either hashed tree is caught by the
dirty gate, because the gate's pathspec covers those two trees — verified by behaviour on 2026-08-23,
an untracked `src/.gitignore` gives `?? src/.gitignore` and `code_dirty` `True` (the whole-branch
review measured the same tree end to end, `E-CODE-DIRTY` at exit 1). The repo **root** is the only
escape, and it is where the rule normally lives.

**Not closed by H6a's Ruling L.** That ruling neutralized the dirty gate's own git configuration so
the gate and the hash honour one exclude chain, which closes the mirror-image hole (a globally
excluded file, clean to the gate and folded into the hash). It changes nothing here: the deciding file
is outside the gate's **pathspec**, not outside its exclude chain.

**Owner: H6b, and the reason it is not H6a's.** Closing this means the dirty gate covering a file
**outside** the two hashed trees — a scope change to what `E-CODE-DIRTY` reads, which deserves its own
decision and its own cost accounting (every uncommitted root file becomes a candidate the gate must
rule on). H6b holds the `validate` tree-state ruling, which is the same question asked at the other
surface. A successor should decide the two together rather than widening this one pathspec by hand.

**AMENDED 2026-08-23, H6b task 6 (Ruling P and Decision 12, decided together as this entry asked):
DECLINED, remains open, re-owned unassigned.** H6b considered widening the dirty gate's pathspec to
cover an uncommitted root `.gitignore` and declines it. The gate's pathspec is `src/**` and
`templates/**` by the same decision that scopes `code_hash` itself — [§ Three
hashes](../reference.md#three-hashes) — and widening it to "every uncommitted root file that could
be a `.gitignore`" is a behaviour change to a shipped command with a real cost: an ordinary
uncommitted `README.md`, `NOTES.md`, or draft config at the repo root would have to be examined and
ruled either relevant or not, and a false positive there stops a run that carries no identity defect
at all. H6b is chartered additive (this file's own instructions above), and this is the one item in
this entry's inbox that cannot be closed additively — closing it changes what `E-CODE-DIRTY` refuses
for every existing repo, not only for the pathological one this entry measured. Decided *together with*
the sibling question at `validate` (Ruling P, task 6, same commit): Ruling P answers that one with **no
new seat** — no `W-` code, because a `W-` is a registry seat and the condition this entry describes is
already caught downstream, at `run`, by `E-CODE-DIRTY` itself once a step actually executes. Answering
this entry's question with "widen the gate" while Ruling P answers the neighbouring one with "add
nothing" would decide the same shape of question in opposite directions in one slice, on no argument —
so both stay narrow. **Re-owned: unassigned, with the reason** — no remaining chartered slice has
`E-CODE-DIRTY`'s pathspec as its surface. H9 owns `reproduce`, `dry-run`, `draft`, `resume`, `demo` and
`docs`, none of which touches the dirty gate's definition; H3c-3's remaining 14 tasks are folds and
holdouts inside cells. **The closer's own cost accounting, named rather than deferred again:** a
successor who does take this on must decide what an uncommitted root file that is **not** a
`.gitignore` — a stray `README.md`, a half-written config, an editor swap file — should do at the same
gate, since widening the pathspec to "the repo root" catches all of them, not only the one this entry
measured; a design that stops a run over an unrelated root file is the failure this decline exists to
avoid repeating on a wider scale.

## OPEN — the worked example's seed **labels** cannot be produced by the seed **values** printed beside them — **Owner: unassigned, with the reason**

`reference.md` § `sweep.yaml` — the resolved plan prints `labels: [seed17, seed42, seed137, seed1009, seed2027]` and
§ Before you spend it prints `seeds: [17, 42, 137, 1009, 2027]`, and `replication._seed_members`
cannot produce the first list from the second. Its rule is `f"seed{s % 100:02d}"`, with the
full-value form `f"seed{s}"` used **only** as a collision fallback when the two-digit labels are not
all distinct.

**Reproduced 2026-08-23**, on the documented values rather than on a live run, since a run's seeds
come from the design digest and cannot be forced:

```
$ uv run python -c "print([f'seed{s % 100:02d}' for s in [17,42,137,1009,2027]])"
['seed17', 'seed42', 'seed37', 'seed09', 'seed27']
```

All five are distinct, so the fallback never fires and the labels a run of the worked example would
write are `seed37`, `seed09` and `seed27` where the documents show `seed137`, `seed1009` and
`seed2027`. Three of the five documented labels are unreachable from the documented seeds.

**Two answers, and this entry deliberately picks neither.** Either the documents' seed *values* move
(to five values whose last two digits are `17`, `42`, `137`… which is impossible for the three-and
four-digit ones, so really: to five values under 100), or the labels move to the two-digit form, or
`_seed_members` gains a rule that keeps a short value whole. The third is a behaviour change to a
shipped label that appears in run-directory paths, `sweep.yaml`, `run.yaml` and `executions.jsonl`,
so it is not a documentation fix wearing a code fix's clothes.

**Not H9a's, and not fixed in passing.** `CLAUDE.md` § The worked example pins the worked example's
numbers — *"those intervals were checked numerically and must not be narrowed back"* — and the seed
list belongs to that example, so moving either side is an edit to it. Measured: the three unreachable
labels have **two** homes, both in `reference.md` (`:905` and `:923`). § Before you spend it's
transcript, added by H9a task 12, lists only `seed17` and `seed42` and elides the rest — the same
elision it already uses for conditions `01` and `02` — precisely so this slice does not give the
disagreement a third home; `README.md`'s run-directory tree shows only those same two, both of which
the shipped rule does produce, so nothing there moves either way. **Owner: unassigned, with the reason**: no
remaining slice (H9b `resume`, H9c `reproduce`, H9d `demo`/`docs`, H3c-3's remaining 14) has
`replication.py`'s label rule or § `sweep.yaml` — the resolved plan's worked example as its surface. Related but
distinct from the existing entry on `_seed_members` honouring a declared seed, which is about a
*declared* value being ignored rather than about a label a documented value cannot produce.

**Found by** H9a task 12, while deriving the step-directory list for § Before you spend it: the
transcript needs one directory component per repeat, so it needs the labels, and the labels a real
`dry-run` printed (`seed01`, `seed96`, `seed06`, `seed78`, `seed39` — two digits, every one) did not
have the documented shape. The transcript H9a landed uses the documents' own labels, so this entry is
the *only* place the disagreement is recorded rather than propagated.

## OPEN — 195 `src/`/`tests/` references to `command_run` describe code that now lives in `_prepare_run` or `_execute_prepared`, and a **signpost docstring** is the whole mitigation — **Owner: unassigned, with the reason**

**Filed 2026-08-23 by H9a task 13, as plan correction 22's residue.** H9a task 2 extracted phases 1-5
of `cli.command_run` into `cli._prepare_run` and phases 6-10 into `cli._execute_prepared`, leaving
`command_run` a nine-line delegator. Every comment, docstring and test name that attributes a
behaviour to `command_run` and means *the `run` command* is still true of the command and no longer
true of the function.

**Measured 2026-08-23** (**re-measured 2026-08-25 by H3c-3 task 20: 202 lines, `cli.py` 36 —
the class is unchanged and the number is not the claim; H3c-3 hoisted `_resolved_group_axes`
inside `_prepare_run`, which is one of the entry's own named non-`command_run` homes, and the
entry's reading of it is unchanged**), **and the count the plan carried was a lower bound.**
`grep -rn "command_run" src/ tests/` printed **195** lines across 22 files — `tests/test_cli.py` 79, `cli.py` 34,
`validate.py` 13, `apparatus.py` 10, and eighteen more files with 1-6 each. The plan's *"roughly
forty-five"* was measured over a narrower pattern; the class is the same and the number is four times
larger.

**What was fixed rather than filed.** The **normative** homes are closed: `reference.md`'s five
location rows now name `cli._prepare_run` (H9a task 2), its six dual-surface roster rows now name
`cli._prepare_run` and enumerate `run`, `draft` and `dry-run` (H9a task 12 — those had gone from
*imprecise* to *narrower than the code*, since two new commands meet the same raises), and § The one
config file's `null_test` clause now says `cli.py`, matching its four sibling clauses. **One
`command_run` mention is left in `reference.md` on purpose**, at § Errors core raises' *"since H9a, in
`cli._prepare_run`, which `command_run` calls"* — it exists to describe the split, so it is the one a
grepping reader should land on.

**The mitigation, and its limit, checked rather than assumed.** `command_run`'s own docstring carries
a signpost naming which phases live in which helper. **Naming is not sitting inside**: measured by
`ast` span, only **2 of `cli.py`'s 34 `command_run` hits** fall inside the function the signpost is
written on — the other 32 are docstrings and comments belonging to other functions
(`_resolved_group_axes`, `_cond_beside_n`, `_make_null_fn`, `_resolved_resample`, and others) that
merely *name* `command_run` in passing. A reader who greps `command_run` in `cli.py` lands on
whichever of the 34 sites matched, which is the signpost only if that site happens to be one of the
two inside it. A reader who greps `reference.md` lands on the § Errors core raises sentence, which
says the same thing correctly. **A reader who greps `tests/` — 101 of the 195 hits, against `src/`'s
94 — lands on neither**, and that is the residue this entry is for: a test named
`test_command_run_aggregate_resolves_a_project_local_template` still names the command correctly and
the function misleadingly, and nothing points from there to the split. So the honest count for the
mitigation's own reach is **2 of 195**, not 34 of 195 — the routing below is unaffected by that
correction.

**Why a rewrite is not obviously right, which is why this is filed rather than done.** A rewrite of
each site has to **decide which half it now names**, and *a rewrite invents; a deletion cannot*
(`CLAUDE.md` § Habits). For most of the 195 the honest edit is a **deletion** — `command_run` →
*the `run` command* — which loses nothing and invents nothing; H9a made exactly that edit at the one
normative site where it applied. The work is mechanical, large, and touches test names, which is a
different risk profile from a docstring.

**Owner: unassigned, with the reason.** No remaining slice has `cli.py`'s phase split as its surface:
**H9b** is `resume`, **H9c** is `reproduce`, **H9d** is `demo`/`docs`/`list-templates`, and **H3c-3's
remaining 14** is folds and holdouts inside cells. H9b and H9c will each add a **third and fourth**
caller of `_prepare_run`, which makes the residue grow rather than shrink — so the natural moment is
whichever of them first finds a `command_run` claim it cannot leave standing, and it should re-read
this entry rather than re-derive the count.

**Reproduce:** `grep -rc "command_run" src/publishable/*.py tests/*.py | grep -v ':0$'` — 22 files;
`grep -rn "command_run" src/ tests/ | wc -l` — 195.

**APPENDED 2026-08-23 (H9b task 17): re-read rather than re-derived, and the count has not moved —
still 22 files and still 195 lines**, measured with this entry's own two commands at H9b's commit.
H9b added a third caller of `_prepare_run` (`command_resume`) and did not add a `command_run`
reference, which is the shape this entry asks a later slice to keep: a new entry into the sequence
names the function it calls, not the command it resembles.

**One `command_run` claim this slice made false is DELETED rather than rewritten.**
`_execute_prepared`'s docstring said twice that its body *"stays byte-identical to what `command_run`
held"*, offered as the reviewer's mechanical check on the original move. That stopped being true when
H9b's `resumed` branches landed inside the body, and it is now false in a second way — task 16 added
the branch that publishes a record for a resume whose apparatus moved. Both sentences are gone: the
unpack block's own purpose is stated in the past tense (it is what made the move checkable), and no
weaker version of the claim replaced it, because a weaker one would be a sentence nobody can check.
**The 195 references are unaffected** — none of them is that claim.

## OPEN — `dry-run`'s sweep header reads as an equation that does not hold: `3 conditions × 5 repeats = 20 executions` — **Owner: unassigned, with the reason**

**Filed 2026-08-23 by H9a task 12**, found by running the worked example's own shape rather than by
reading the format string. `cli.command_dry_run` prints

```
sweep: {n_conditions} conditions ({modes}) × {n_repeats} repeats = {executions} executions
```

where `executions` is `len(prepared.plan)` — one entry per planned (step, condition, repeat) triple —
while `n_conditions` and `n_repeats` describe the *sweep's shape*. **The two are equal only for a
pipeline whose every step is `repeat`-scope.** For any pipeline with a `run`-, `condition`- or
`summary`-scope step the line prints an arithmetic identity that is false on its face.

**Reproduced 2026-08-23**, on a 4-step project with the worked example's four scopes (`run` →
`condition` → `repeat` → `summary`), 3 conditions and 5 seed repeats, built and `dry-run` outside this
repository:

```
sweep: 3 conditions (baseline + grid) × 5 repeats = 20 executions
scale:  4800 unit-executions (20 executions × 240 units handed to each)
```

`3 × 5` is 15; the number printed is 20, and 20 is right — 1 (`run`) + 3 (`condition`) + 15 (`repeat`)
+ 1 (`summary`). **The count is correct and the presentation asserts a derivation it is not making.**

**Not a wrong number, which is why it is filed rather than fixed.** Every figure on the line is what
it should be, so this is a question about what the line should *say* — candidates include dropping the
`=` (`sweep: 3 conditions (baseline + grid) × 5 repeats; 20 executions`), naming the quantity
(`… = 20 planned executions over 4 steps`), or printing the per-scope breakdown the step-directory
list already carries. Each changes a shipped command's output for every user, which is a presentation
ruling rather than a defect fix, and § Exit codes and diagnostics' own rule — the identifier is the
contract and the wording explicitly is not — is the precedent for treating it that way.

**What was done instead.** § Before you spend it's transcript carried `= 15 executions` and
`3,600 unit-executions`, both **false** against the shipped command for the pipeline that transcript
describes; H9a task 12 corrected them to `20` and `4,800` and added the sentence that says why the
`×` is a description rather than a derivation, with the `demo` walkthrough's genuinely-15 figure named
as the contrast. So the document no longer disagrees with the code; the code's own line is what this
entry is about. Two other homes of `15` were checked and are **correct**: `reference.md`'s
`scope = "repeat"  # 15 executions` comment counts one step's own executions, and § What `demo` walks
you through's stop-4 row describes a one-step pipeline.

**Owner: unassigned, with the reason.** No remaining slice has `dry-run`'s output format as its
surface — **H9b** is `resume`, **H9c** is `reproduce`, **H9d** is `demo`/`docs`/`list-templates`, and
**H3c-3's remaining 14** is folds and holdouts inside cells. H9d is the nearest neighbour, since
`demo`'s stop 4 prints this very line for a user's first `dry-run`, but printing a command's output is
not the same surface as choosing its wording and taking it in passing is what this file rejects.

## OPEN — `repo_root.txt` has a THIRD reader repeating the same refusal triple, and no shared guard — **Owner: unassigned, no remaining slice owns `freeze` and `report` together**

**Measured at `4ed2fa5` on H9b's branch, filed after batches 1–2's review found the escalation lived only
in a task report.** H9b's `read_repo_root` is the **third** copy of the read-and-refuse triple that
`freeze` and `report` already carry for `environment/repo_root.txt`. Each copy re-implements the same
three refusals over the same one-line file, and the copies have **already drifted**: this one omits the
`encoding="utf-8"` both precedents pass.

**Why H9b did not consolidate it.** Consolidating means one guard serving `freeze`, `report` and `resume`,
which is a change to two shipped commands' read paths in a slice chartered for a third — and *the sibling
that already got it right is the first place to look* argues for reusing a guard, not for rewriting two
callers to reach a new one mid-slice.

**Owner: unassigned, with the reason.** No remaining slice (H9c, H9d, H3c-3's remaining 14) owns `freeze`
and `report` together; whoever consolidates should note the drift above is the argument, since **three
copies of one refusal that already disagree in one keyword are three copies that will disagree in a
refusal next.**

## OPEN — `io.record`'s collision check reads only the FIRST unit's attributes, so a resolver can bypass `E-STEP-KEY-COLLISION` from a config — **Owner: unassigned, the recorded-column namespace's owner (H5) is closed**

**Measured at `dd408b5` on H9b's branch, filed after batches 3–4's review disproved a claim that this was
*"reachable only from core's own API, never from a config"*.** It is config-reachable:

- `resolve_units` checks declared attributes against the **union** of what a resolver yields, so a resolver
  whose **first** unit lacks an attribute its **later** units carry **passes `validate`**;
- `artifacts.record`'s `_declared_attributes` then reads **`self._units[0]` only**, so the collision check
  never sees that attribute and a recorded column of the same name is **accepted rather than refused**.

**Why this is the H5a value-hijack family rather than a new one.** H5a closed the case where a *directly
constructed* `Unit` hijacks the identity column, and filed the residue; this is the same shape reached
through a **resolver**, which is a config-declared surface rather than hand-written Python. **The fix is
the sibling that already got it right**: `resolve_units` reads the union, and `_declared_attributes`
should read the same set rather than one unit's.

**Why H9b did not close it.** H9b's charter is `resume`; widening a shipped refusal so it catches configs
that pass today is a behaviour change to `run`, and the slice that owned the recorded-column namespace
(H5a/H5b) is closed. **Owner: unassigned, with the reason** — no remaining slice (H9c, H9d, H3c-3's
remaining 14) names `io.record`'s collision check as its surface. Whoever takes it should read it beside
H5a's two residue entries; **all three are one question asked at three depths.**

## OPEN — a resume stopped by an UNREACHABLE apparatus still writes no record, while one stopped by a MOVED fact now does — **Owner: unassigned, with the reason (the terminality of `run.yaml` is the reason, not the surface)**

**Measured at H9b task 16, which closed the sibling half.** Task 13 made a resume's run-start apparatus
round gate against the original run's replayed baseline, and measured the cost: a resume whose apparatus
had **moved** while the run was down exited `1` with no `run.yaml`, and repeated identically for as long as
the fact stayed moved — every completed execution on disk, paid for, and unpublishable. **Task 16 closed
that**: the stop is recorded on the shared `StopSignal`, no new results are added, and the run publishes
`status: failed` with the reconstituted executions aggregated, `provenance.apparatus` naming the ledger
that holds the moving observation, at exit `4` (§ Exit codes' *"the run stopped: `status: failed`. There
is a record of what happened"*, whose row already reads **`run`, `draft`, `resume` only**).

**What is still open is the other stop reason.** A resume whose run-start round raises
`E-APPARATUS-RAISED` — the apparatus unreachable — still returns `EXIT_EXTERNAL` with no `run.yaml`, so a
resume of a directory whose instrument is down publishes nothing, exactly as before.

**Why it was NOT folded in, and this is the reason rather than the surface.** Writing `run.yaml` **ends the
run**: `resume` refuses `E-RESUME-RUN-ENDED` for a directory that holds one, and a run record is never
modified. That is the right trade for a **moved** fact, which cannot move back — no later resume could
ever pass the gate, so the choice is between a published partial record and none at all. An **unreachable**
apparatus is the opposite case: the operator's next move is to bring it back and resume again, and
publishing now would convert a recoverable state into a permanently truncated run. Deciding that trade for
the retryable class needs a rule this slice does not have — *when may a resume declare a run over?* — and
`5` is documented as **the class you retry**, which is the argument against ending the run on it.

**Owner: unassigned, with the reason.** No remaining slice (H9c `reproduce`, H9d `demo`/`docs`/
`list-templates`, H3c-3's remaining 14) has `resume`'s stop paths or § What status means as its surface.
Whoever takes it should argue against the terminality paragraph above rather than rediscover it, and
should note that the two halves are now visibly asymmetric **in the code**, one branch apart, which is
where a reader will find the question.

## OPEN — `tests/test_freeze.py`'s two claims with nothing behind them: a helper that took a `code` and never read it, and a test whose name promises a redaction it never asserts — **Owner: unassigned, with the reason (no remaining slice owns `freeze`'s test surface)**

**Filed 2026-08-24 by H9b's whole-branch fix round; the first half is CLOSED in the same commit, the
second is not.** Both are H8b's (`60f5d61`, *"H8b task 4: freeze.py — the refusal gate, template
resolution, credential pre-check"*), a closed slice, and this branch added no use of either.

**Half one, closed here.** `_assert_refused(result, code, exit_code, ledger_before, run_dir)` never read
`code`. Measured, both arms of the discriminating pair scoped to `tests/test_freeze.py` with
`freeze._refuse` mutated to emit a constant `"E-BOGUS-MUTATION"` instead of the code it is handed:
with the shipped helper **5 failed, 37 passed** — not one of the twenty arms; with the helper reading
stderr **25 failed, 17 passed**. So **twenty tests asserted *that* a refusal happened and its exit code
and its untouched ledger, and never *which* refusal it was.** (The count is twenty, not the twenty-one
the review reported: `grep -c "_assert_refused(result" tests/test_freeze.py` counts the `def` line,
whose first parameter is `result`.) The helper now reads the code off stderr — the only place it is
observable, `_Refused` carrying the exit code alone — and returns stderr for callers whose message is
the point. **What the fail-open was hiding is recorded in the same round** and is the reason this entry
exists at all rather than being a test-hygiene note: **four of the twenty had been passing a code the
code never printed since H9b minted `E-FREEZE-CONFIG-EDITED`**, whose gate (c2) sits before template
resolution (e) and the plan cross-check (h) while `covered_config` covers everything but `metadata` and
the two host paths — so every fixture that edited the run directory's `config.yaml` copy to reach a
later gate stopped at (c2) instead, and `E-TEMPLATE-UNKNOWN`, `E-TEMPLATE-INSTALLED-UNSUPPORTED` and
`E-FREEZE-PLAN-MISMATCH` silently lost their coverage. `_edit_config_yaml` now re-records
`identity.json`'s `parameters_hash` beside the edit, which is the state each of those fixtures means.

**Half two, OPEN.** `test_gate_e_a_load_fault_reuses_E_TEMPLATE_LOAD_and_carries_credentials` — its name
and its docstring (*"the template that DID load cleanly still has its declared credential redacted in
the finding"*) promise a redaction, and the body asserts the code, the exit code and the ledger only.
The fixture declares `F_CRED_TOKEN=shh` through a parameter value's `requires_env`, so the property is
reachable: assert that `shh` does not appear in the rendered finding and that the redaction marker does,
and pin it with a mutation that narrows `partial_templates`' credential read. **Not fixed here**: the
mutation belongs in a closed slice's production surface and this is a fix round on the commit before a
merge. **Owner: unassigned, with the reason** — no remaining slice (H9c `reproduce`, H9d
`demo`/`docs`/`list-templates`, H3c-3's remaining 14) has `freeze` or its tests as its surface.

**The shape was swept for and does not exist elsewhere.** An `ast` walk over every `FunctionDef` in
`tests/**` and `src/**` whose parameters include a name containing `code`, checking whether that name is
ever loaded in the body: **one hit in `tests/`** (this helper, before the fix) and **zero in `src/`**.
The sweep was proven able to fail by running it against the unfixed helper first, and it is an `ast`
walk rather than a grep because a wrapped signature defeats a line-oriented one.

## OPEN — two comments in `report.py`'s and `test_report.py`'s surface assert that H8c task 10's bundle render "does not exist yet", and it shipped — **Owner: unassigned, with the reason (H8c is closed)**

**Filed 2026-08-24 by H9b's whole-branch fix round**, found by the sweep Minor 2 required
(`grep -rn "not dispatched\|does not exist yet\|owns building it" src/ tests/`, every hit attributed).
`report.py`'s single-run draft refusal carries *"That flagging arm is task 10's, over code that does not
exist yet"*, and `tests/test_report.py` carries *"a bundle render does not exist yet, so it cannot be
pinned here; task 10's own brief owns building it"*. Both are false at HEAD: H8c task 10 built the
bundle render and its draft flag — `report.py`'s own member-identity helper implements it
(*"a bundle FLAGS a draft member rather than refusing the whole render"*), one file above the comment
denying it exists. Nothing behavioural is wrong; this is the *"a sentence went false under its own
slice's later change"* shape, in a **closed** slice, which is why it is filed rather than fixed on this
branch — H9b's own two instances of it are corrected in this round. **Owner: unassigned, with the
reason** — no remaining slice (H9c, H9d, H3c-3's remaining 14) has `report` as its surface. The remedy
is deletion, not rewriting.

## OPEN — a tracked `.gitattributes` carrying a `text`/`eol` attribute makes `code_hash` a property of how a working tree was MATERIALIZED rather than of the commit — **Owner: unassigned, with the reason (no remaining slice has `hashes.py` or § How the three are computed as its surface)**

**Filed 2026-08-24 by H9c task 14**, and reproduced by this task rather than carried from the design.
`code_hash` folds the **bytes on disk** under `src/**` and `templates/**`. A tracked `.gitattributes`
declaring `* text eol=crlf` tells git to write CRLF into every working tree it materializes — so the
repository the author never re-checked-out holds LF and every clone of the identical commit holds
CRLF, and the two hash differently. `reproduce` passes `-c core.autocrlf=false` at both git
invocations (H9c Decision 7) and that flag does **not** reach this: `.gitattributes` overrides
`core.autocrlf`, which is the whole point of the file.

**Reproduced, outside this repository, on `git version 2.50.1 (Apple Git-155)`:**

```bash
mkdir -p ga/orig/src/pkg && cd ga/orig
printf 'x = 1\ny = 2\n' > src/pkg/mod.py
printf '* text eol=crlf\n'  > .gitattributes
git init -q . && git add -A && git commit -qm init
cd .. && git -c core.autocrlf=false clone -c core.autocrlf=false -q ./orig ./clone
```

```python
from publishable.hashes import code_hash
code_hash(Path("ga/orig"),  None)   # sha256:6bac8c5…   b'x = 1\ny = 2\n'
code_hash(Path("ga/clone"), None)   # sha256:80ffbc4…   b'x = 1\r\ny = 2\r\n'
```

**The load-bearing claim is the INEQUALITY, not either digest.** Both figures are this fixture's, over
this two-file tree, and a reader reproducing the recipe on another tree will get two different numbers
that are still different from each other. (The design's § 0.5 records `d37416e` against `0cc6ddd` from
its own fixture; neither pair is canonical, and quoting one as though it were is how a recipe stops
reproducing.)

**Not closed by H9c, by ruling.** Decision 7 states why `reproduce` may not override it: a
`.gitattributes` is **tracked**, so it travels with the commit and is part of what the commit says the
tree is — neutralizing it would make `reproduce` produce a tree the repository's own rules say is
wrong, and H6a Ruling F's ground (*"a rule that does not travel with the tree cannot define the tree's
identity"*) runs the other way here precisely because this rule **does** travel. The honest fix is at
the hashing end, not at the clone end.

**The check its closer must make.** Either (a) `code_hash` normalizes line endings before folding, at
the cost of making the digest no longer a fold of the bytes on disk — which is the property H6a
Ruling C's refusal of a definition marker leans on, so changing it is a second undated definition
change; or (b) `reference.md` § How the three are computed states the dependency, so a reader who
sees `E-REPRODUCE-CODE-HASH` on a faithful clone finds the cause named. `reproduce` already names
*"a tracked `.gitattributes`, which it may not [neutralize]"* in its closed candidate set
(`reproduce._CODE_HASH_CAUSES`), which is the narrow half of (b) and is not the same as the document
saying it.

**Owner: unassigned, with the reason.** No remaining slice has `hashes.py` or § How the three are
computed as its surface — **H9d** is `demo`/`docs`/`list-templates` and **H3c-3's remaining 14** is
folds and holdouts inside cells — and **H6 is complete**. Stated as a fact with a reason rather than
as *"whichever slice next touches `code_hash`"*, which this file rejects by name.

**Severity:** Minor in reach and Major in kind. No project in this repository's own record ships a
`.gitattributes`, so nothing observed hits it; what it costs when it is hit is a `code_hash` refusal
on a clone that is byte-faithful to the commit, with no document naming the cause.

## OPEN — a study bundle carries no lockfile, so a bundle member whose project never committed one cannot be reproduced from the bundle alone — **Owner: unassigned, with the reason (`study add`'s bundle contents are H8c's surface, and H8c is complete)**

**Filed 2026-08-24 by H9c task 14**, measured against `study add`'s real output. A bundle member is a
redacted copy of one run's `run.yaml`. `study._redact` reaches `data.input_dir`/`data.output_dir`,
`provenance.git.repo_root`, `provenance.environment.hostname` and `provenance.input_manifest` — and
**not** `provenance.environment.uv_lock`, which survives reading `"environment/uv.lock"` while the
bundle holds no `environment/` directory at all. So the member names a path that resolves nowhere:
a **dangling reference**, unmarked.

**Reproduced, and pinned by a shipped arm rather than by a scratch script.**
`tests/test_reproduce.py`'s `_bundle_member` helper asserts exactly this state before every arm that
uses it — `copied["provenance"]["environment"]["uv_lock"] == "environment/uv.lock"`,
`not (member.parent / "environment").exists()`, and `uv_lock_hash is not None`. Run
`uv run pytest tests/test_reproduce.py -k bundle` to reproduce it.

**What it costs, and where H9c already pays it.** Only the **digest** travels, so `reproduce`'s
bundle form cannot use the run's own copy of the lockfile and must fall back to the commit's
committed one, using it if and only if its sha256 matches the recorded `uv_lock_hash`. When the
project never committed a lockfile — which is every scaffolded project today, since
`W-ENV-UNLOCKED` fires on every scaffolded run — that fallback has nothing to match and the bundle
form refuses with `E-REPRODUCE-LOCKFILE-UNREACHABLE`. That refusal is correct and is not the defect;
the defect is that the member advertises a lockfile it does not carry.

**The check its closer must make**, stated so it is not re-derived: either (a) `study add` copies
`environment/uv.lock` into the bundle and rewrites the member's `uv_lock` to point at it — which
makes the bundle bigger and makes it carry a second copy of a file the commit may also hold; or
(b) `study add` **redacts** `provenance.environment.uv_lock` in a member the way it already redacts
`provenance.input_manifest`, so the dangling reference becomes visible as a redaction rather than
reading as a path. (b) is the smaller change and loses nothing, because `uv_lock_hash` beside it is
the figure every reader actually compares.

**Owner: unassigned, with the reason.** `study add`'s bundle contents are **H8c's** surface and H8c
is complete; **H9d** is `demo`/`docs`/`list-templates` and **H3c-3's remaining 14** is folds and
holdouts inside cells. Widening the bundle's contents inside H9c would be charter growth (H9c
design § 4 routes it here for that reason).

**Severity:** Minor. The consequence is a path that resolves nowhere in a published artifact, not a
wrong number.

## OPEN — `provenance.environment` names no `pyproject.toml`, though `run` writes `environment/pyproject.toml` — **Owner: unassigned, with the reason (H6 is complete and no remaining slice has `provenance` as its surface)**

**Filed 2026-08-24 by H9c task 14.** `run` copies the repository's manifest into the run directory —
`cli.py` writes `(run_dir / "environment" / "pyproject.toml")` at run start, and
`environment/pyproject.toml` is in the run directory's own fixed-file list — while
`provenance.environment` records `manager`, `python_version`, `os`, `hostname`, `uv_lock`,
`uv_lock_hash` and `hardware`, and **nothing naming that second copy**. So a reader of `run.yaml`
alone cannot know the file exists.

**Reproduced by grep, both halves, rather than from memory:**
`grep -n "pyproject.toml" src/publishable/cli.py` → the write at run start and the fixed-file list
entry; `grep -n "uv_lock\|pyproject" src/publishable/provenance.py` → **no hits**, the environment
block being assembled in `cli.py`, whose `"uv_lock"`/`"uv_lock_hash"` pair is the whole of what it
records about the two manifests. `docs/reference.md` § What `run.yaml` records shows the same seven
keys and no eighth.

**Not closed by H9c, and the consequence is bounded.** H9c's Decision 3 compares the recorded
`pyproject.toml` against the checkout's committed one and prints `identical` or `DIFFERS` — it finds
the file **by convention** (`<run_dir>/environment/pyproject.toml`, beside the lockfile) rather than
by record, which works for the run-directory form and is simply absent in the bundle form, where the
transcript says so. A fourth environment key is **refused by ruling** for H9c (H6a Decision 12 /
Ruling E: `uv.lock` is the carrier, and a `pyproject_hash` would be a second one), so what is filed
here is the **naming** gap, not a proposal for a hash.

**The check its closer must make:** whether `provenance.environment` should gain a
`pyproject: "environment/pyproject.toml"` key beside `uv_lock` — a name, not a hash, so H6a Ruling E
is untouched — or whether § What `run.yaml` records should state that the run directory holds a
manifest copy the record does not name.

**Owner: unassigned, with the reason.** **H6 is complete**; **H9d** is
`demo`/`docs`/`list-templates` and **H3c-3's remaining 14** is folds and holdouts inside cells.
Neither has `provenance` or § What `run.yaml` records as its surface.

**Severity:** Minor. Nothing is wrong; something reachable is unnamed.

## OPEN — `templates/registry.py`'s `_claims` docstring says *"the two cross-module imports are the whole set"* and there are **three** — **Owner: unassigned, with the reason (no remaining slice has the template registry as its surface)**

**Filed 2026-08-24 by H9c task 14**, first noticed by H9c batch 2 (finding (e)) and re-grepped here
rather than carried. `_claims`' docstring justifies keeping the helper private with *"the two
cross-module imports are the whole set, both read-only."* Grepped
`grep -rn "_claims" src/publishable/` and every hit attributed:

| Hit | What it is |
|---|---|
| `src/publishable/validate.py:43` | a real import |
| `src/publishable/freeze.py:42` | a real import — **the third, and the one the docstring's count misses** |
| `src/publishable/generators/experiment.py:10` | a real import |
| `validate.py:521`, `:524`, `:810`, `:820`; `freeze.py:198`, `:258`; `experiment.py:86`, `:96` | prose and call sites inside the three modules above |
| `src/publishable/reproduce.py:951`, `:1028` | **prose only.** H9c is not a fourth importer: `reproduce` uses the public `get_template` and `template_provenance` and names `_claims` in two docstrings |

So the number was right when it was written and went stale when `freeze.py` landed. This is
`CLAUDE.md`'s *a comment claiming a guarantee the code does not provide*, in its mildest form.

**The remedy is DELETION, not a rewrite.** *"Prefer deleting a claim to rewriting it"* applies
exactly: the clause that justifies keeping the helper private is *"both read-only, and neither is a
signal that this function is meant for general use"*, which stands on its own and needs no count.
Replacing `two` with `three` would recreate the same obligation for the next importer.

**Why H9c did not fix it.** `templates/registry.py` was on batch 2's must-not-touch list, and tasks
11-15 touch `cli.py`, `reproduce.py`, the four documents and this file — editing a fourth module's
docstring to close a finding raised in a different batch is the *carried finding that grew a surface*
shape. Filed instead.

**Owner: unassigned, with the reason.** No remaining slice has the template registry as its surface:
**H9d** is `demo`/`docs`/`list-templates` — `list-templates` reads the registry and is the nearest
thing to a natural closer, which is a reason to look, not an assignment — and **H3c-3's remaining 14**
is folds and holdouts inside cells. H7 is complete.

**Severity:** Minor. Nothing behavioural; a reader who trusts the count adds a fourth importer
believing there were two.

---

## OPEN — `reference.md` gives template `generic` an `aggregate` in one section and denies it in another, and the shipped class has none — **Owner: unassigned, with the reason (no remaining slice owns the worked example's template story)**

**Found by:** H9d design § 3 finding 1, measured before any code was written; re-verified 2026-08-25.

Three readings of one name. `reference.md` § Templates' fenced example is
`@register_template("generic")` and **shows an `aggregate`** computing pearson/spearman/kendall;
the same document's § Validation row says *"template `generic` defines no `aggregate`"*; and
`src/publishable/templates/builtin/generic.py` — all 26 lines of it — declares none, inheriting
`BaseTemplate.aggregate`'s `{}`. `CLAUDE.md` § The worked example then says `cohort-pilot` uses
`generic` and derives `r` by `aggregate(units)`, which no shipped code can do.

**Reproduced:**

```python
from publishable.templates.registry import get_template
t = get_template("generic")
print(type(t).__dict__.get("aggregate"))     # None — inherited, returns {}
print(t.aggregate(None, None))               # {}
```

A config naming `generic` therefore derives nothing, which is why H9d's `demo` writes a
**project-local** template instead (design Decision 5) — it depends on neither reading and so
could decline this.

**Why H9d did not repair it.** Repairing means either giving a shipped `generic` an `aggregate` —
which falsifies `E-HYPOTHESIS-BOUND`'s shipped premise and the tests resting on it — or editing the
worked example across four documents. Neither is `demo`/`docs`/`list-templates`' surface.

**Owner: unassigned, with the reason.** No remaining slice has core's shipped template or the worked
example as its surface: H9d is the command surface and **H3c-3's remaining 14 is folds and holdouts
inside cells**. H5, H7 and H8 are complete.

**Severity:** Major as documentation. A reader following § Templates writes a config that derives
nothing and gets no diagnostic saying why.

---

## OPEN — ruling GG asked for `self.rng` to become a `numpy.random.Generator` and NO task built it; the four obligations it attached are unowned — **Owner: unassigned, with the reason (H9d is the last slice of the command surface)**

**Found by:** H9d batch 5-6 (tasks 10-14), reading the ruling against the plan's own task sections.

**What happened, so it is not re-derived.** H9d corrections 3, 4 and 5 measured a divergence:
`base_step.py` builds a `random.Random`, `reference.md` said `numpy.random.Generator` at two sites,
and a step calling `self.rng.normal(...)` — which the document invited — failed its execution at
exit `3`. Design **Decision 13** resolved it by moving the **document**. **Controller ruling GG,
appended 2026-08-24, overruled that and required the CODE to move**, with four obligations: a
disclosure section, a pin on the type itself, `demo`'s generated step drawing from `self.rng`, and
the two `reference.md` statements re-checked against the new code. Its own escape clause says
*"whichever task owns `base_step.py` owns all four. If no task does, the batch that discovers it says
so and stops rather than folding it in silently."*

**No task owns `base_step.py`.** Measured: no task section 1-14 of
`docs/superpowers/plans/2026-08-24-demo-and-docs.md` names the file as an edit, and
`git log main..HEAD -- src/publishable/base_step.py` is **empty**. So the escape clause fired and
H9d's batch 6 did not fold the change in.

**What H9d did instead, stated so the two entries do not read as contradicting each other.** The
document/code divergence is **closed by moving the document** (§ Using them in step code, § Randomness'
table row, and two further statements that were false of `random.Random` and are corrected with
them: `self.rng.spawn(n)`, which the standard library's generator does not have, and
*"`self.rng` is exactly `default_rng(self.derive_seed(...))`"*). GG's own fourth obligation is
therefore discharged as a finding: **both statements were false of the shipped code, and two
neighbouring ones were too.** `demo`'s generated step draws from `self.rng.random()` — a method both
types carry — so the walkthrough exercises the attribute under either resolution and nothing has to
move if the ruling is later built.

**What is unowned:** the type change itself, its disclosure section, and a pin on the type. The
measurement that outlives the wording fix is `grep -rn 'self.rng' tests/*.py` → **zero hits**: this
surface shipped without ever being exercised, which is *an unbuilt reader of a shipped surface*
wearing its other face, and is why the divergence survived a release.

**Cost if wrong / if unclaimed:** a research tool whose per-execution stream cannot draw a normal,
met by a new user following the documented example on their first step — GG's own argument, recorded
here rather than lost with the ruling.

**Owner: unassigned, with the reason.** `base_step.py` is core's step surface. **H9d is the last
slice of the command surface** and **H3c-3's remaining 14 is folds and holdouts inside cells**;
neither has `BaseStep` as its surface. A controller re-taking GG would be scheduling new work, not
assigning existing work, and this entry is what makes that visible.

---

## OPEN — `reference.md`'s worked `run.yaml` gives a DERIVED metric a `repeat_spread` the code computes only for recorded columns — **Owner: unassigned, with the reason (no remaining slice has the `statistics` block as its surface)**

**Found by:** H9d correction 8, read from a real `run.yaml`; re-verified 2026-08-25 against H9d's own
demo run.

`reference.md`'s worked record shows
`r: {value: 0.607, …, repeat_spread: {std: 0.014, n: 5, kind: seed}}` — `r` being **derived** by the
template's `aggregate`. The code computes `repeat_spread` only where a column was **recorded** per
repeat.

**Reproduced:** `publishable demo` writes a project whose `r` is derived and whose `pred`/`truth` are
recorded. In the resulting `run.yaml`, `pred` and `truth` each carry
`repeat_spread: {std: …, n: 5, kind: seed}` and **`r` carries no such key at all**. That is why
`demo`'s own transcript reports a recorded column's spread and names which column.

**Owner: unassigned, with the reason.** It is `stats.summarize_step`'s construction. No remaining
slice has the `statistics` block as its surface — H4 is complete, H9d is the command surface, and
H3c-3's remaining 14 is folds and holdouts inside cells.

**Severity:** Minor as code, Major as documentation: the worked example shows a key a reader will
look for and not find.

---

## OPEN — a derived metric whose `aggregate` reads DECLARED ATTRIBUTES gets a paired contrast draw of `0 of 2000` and a `null` interval, while the same metric over RECORDED COLUMNS gets both — **Owner: unassigned, with the reason (no remaining slice has the resample constructions as its surface)**

**Found by:** H9d correction 10 / design Decision 6, measured by two runs differing only in that.

Per condition, an attribute-reading `aggregate` computes its percentile interval fine. Its **paired
contrast** draw yields `0 of 2000` — `W-STATS-CONTRAST-RESAMPLE-THIN`, `ci95: null`, `method: null`
— while the identical `aggregate` reading recorded columns gets `paired_percentile_over_units` and a
real interval.

**Reproduced:** two runs of one config differing only in whether `aggregate` reads `units.pred` or
`unit.x`-derived attributes. **Casting the attribute to `float` inside `aggregate` does not help**,
which is what isolates the cause away from the string-typing of attributes (a real but separate
fact: attributes from `index.csv` arrive as `str`, so `spearmanr` over them ranks
lexicographically — `0.4212` against the float column's `0.6781`).

H9d routes **around** this rather than through it: `demo`'s template reads recorded columns, because
the paired delta is the walkthrough's headline number and the attribute route puts a dash where it
belongs.

**Owner: unassigned, with the reason.** The construction is in `stats.py`'s derived-contrast
resampling, reached from `cli.py`'s `_make_resample_fn`. No remaining slice has it as its surface;
H4 is complete.

**Severity:** Major. A template written the documented way silently loses every contrast interval in
the run, at exit `0`, with only a warning that reads as a thin-data problem.

---

## OPEN — `run` prints no execution banner, no progress indication and no results table, for a plan of any size — **Owner: unassigned, with the reason (a behaviour change to the most-tested shipped command)**

**Found by:** H9d correction 6, captured whole to a file rather than tailed; re-measured 2026-08-25.

**Reproduced:** a successful 19-execution run's **entire** stdout is the warning block and one line
`run.yaml → <path>`. Nothing reports that 19 executions are planned, nothing reports progress
through them, and no results table is printed — for a run that may take hours.

This is why `demo` renders its own stop-5 summary from the record `run` just wrote (design
Decision 7), and why README's stop-5 block now attributes `run`'s two real lines to `run` and
everything beneath them to `demo`.

**Owner: unassigned, with the reason.** Giving `run` progress indication is a behaviour change to
the most-tested shipped command, on the last slice of the project; it would move every `run` stdout
pin in the suite, and the four documents nowhere say `run` prints one. **H9d declined it in writing**
rather than building it. No remaining slice has `run`'s output as its surface.

**Severity:** Minor as correctness, real as usability: a long plan gives a user nothing to watch.

---

## OPEN — `reference.md` § Package layout names `examples/generic/`, which does not exist and which nothing consumes — **Owner: unassigned, with the reason**

**AMENDED 2026-08-26 — the residue stands, the stated ground does not.** The entry's ground is *"the row carries no `— not yet built` marker"*. **It does** — commit `844d526` added it at 05:31 on 2026-08-25, three and a half hours after this entry landed in the same slice. `examples/generic/` still does not exist, so the residue is real; **the reason given for filing it is false.**

**Found by:** H9d correction 20; `ls examples/` says no such directory, at HEAD.

The row carries no `— not yet built` marker, so it reads as describing a directory that ships. The S1
spine design's § Explicitly out of scope names it too: *"`examples/generic/` from § Package layout.
Nothing consumes it until `demo`."* **`demo` is now built and consumes nothing of the kind**: it
scaffolds its own project and its own data, which is the thing a reader wanting an example now has.

**Why H9d neither built nor deleted it.** Inventing an examples tree is not `demo`'s surface, and
deleting a documented directory to make a tree pass is the *delete the claim to make the check green*
move. The row is left, and this entry is what says it is unbacked.

**Owner: unassigned, with the reason.** No remaining slice has § Package layout's tree as its
surface: H9d is the command surface and H3c-3's remaining 14 is folds and holdouts inside cells.

**Severity:** Minor. A reader looking for `examples/generic/` finds nothing and no explanation.

---

## OPEN — the fresh-source loader covers the file it imports and NOT the modules that file imports, so a sibling step edited in the same second can still be served stale — **Owner: unassigned, with the reason (the two filings it completes are closed)**

**Found by:** H9d batch 1's task 9 report, concern 2, recorded there and filed here so it is not
carried only in a batch report.

`sourceimport.import_module_fresh` forces recompilation of the module **it** resolves — the template
file, the report override, the entrypoint. A module that file then imports itself — a sibling step,
a vendored helper — goes through the ordinary import system, whose `SourceFileLoader` still validates
`__pycache__` against `(mtime, size)` at whole-second resolution. So the same-size, same-second
rewrite the two struck entries above describe is still reachable **one import deeper**.

**Reproduced:** the struck entries' own recipe, with the marker moved out of the imported file and
into a sibling module it imports — the second resolution serves the first write's body.

**Why it was not built.** A meta-path finder would cover it and was deliberately declined: it makes
design § 10's mutation row 6 — *revert the fix at exactly one of three call sites* —
unexhibitable, which would trade a real pin for a wider fix.

**Owner: unassigned, with the reason.** The two filings this completes are closed by H9d task 9, and
no remaining slice has `sourceimport.py` as its surface: H9d is the command surface and H3c-3's
remaining 14 is folds and holdouts inside cells.

**Severity:** Minor. It needs a long-lived process, a same-second rewrite, and a same-size one, in a
module reached only indirectly.

## OPEN — every non-repeat execution in a run draws from `random.Random(0)`, so two `condition`-scoped steps share one stream — **Owner: unassigned, no remaining slice has `runner.py`'s seed derivation as its surface**

**Measured at `c2aa690` on H9d's branch, filed after the whole-branch gate found § Randomness asserting
something else.** `runner.py` binds `seed = 0` for every execution without a repeat label, so
`self.rng` is `random.Random(0)` — first draw `0.8444218515250481` — **identically, for every
`run`-, `condition`- and `summary`-scoped execution in the run.**

**Why this is a gap rather than a preference.** § Randomness' own argument against process-global streams
is that *"two draws sharing a stream correlate for no reason anyone chose"* — and that is exactly what a
non-repeat execution gets today, by default, from the accessor the same section says to draw from. The
document had claimed the seed was `derive_seed` of the step's own name where there is no repeat, which
would have given each step its own stream; **that claim was false of the code under both readings** (a
design declaring no repeats gets `_seed_for(digest, 0)`, not a `derive_seed`), and H9d corrected the
document rather than the code, because no task on that branch owned `runner.py`.

**The workaround is documented and sufficient for a careful user**: `derive_seed(purpose)` mixes the
design digest, the roster and the string, so a step that wants its own stream can build one. What is
missing is the default being right.

**Owner: unassigned, with the reason.** The one remaining slice (H3c-3's remaining 14) has folds inside
cells as its surface — `units.py` and `stats.py` — and this is `runner.py`'s seed derivation. Whoever
takes it should read it beside the `self.rng` type filing above: **both are the same accessor promising
more than it delivers, and closing either without the other leaves § Randomness half true.**

## RE-OWNED 2026-08-25, as H3c-3 completes and the spine's order is EXHAUSTED — thirty-eight open entries justify `unassigned` by naming a slice that does not follow, and **no slice follows any of them**

**This is the recurrence the `RE-OWNED 2026-08-21` and `RE-OWNED 2026-08-22` entries each predicted,
at the only scale it can still occur at.** H3c-3 is the last slice in the project; nothing is
chartered after it. Every reason below that reads *"no remaining slice (…, H3c-3's remaining 14)
charters …"* asserted a pending set that is now **empty**, and every owner line that reads
*"whichever slice next touches X"* — the form this file rejects by name at its own
`RE-OWNED 2026-08-19` entry — now resolves to a closed slice the moment anybody touches X.

**The correction is written once, here, rather than thirty-eight times in thirty-eight bodies** —
the same form and the same reason the `RE-OWNED 2026-08-19`, `RE-OWNED 2026-08-21` and
`RE-OWNED 2026-08-22` entries took: each body records what was measured on its own date, and editing
thirty-eight of them would destroy that and invent thirty-eight new sentences besides. **Prefer
deleting a claim to rewriting it**, and prefer governing it once to either.

**Measured 2026-08-25, at this commit, newline-insensitively** — this file is hard-wrapped and
`H3c-3's remaining 14` wraps after `H3c-3's` in at least one place, which a line-based `grep -n`
cannot see across (the `RE-OWNED 2026-08-22` entry hit exactly that and says so). Whitespace was
collapsed over each `## ` section's own body before counting, so a phrase straddling a break is
counted once:

| Measured | Count |
|---|---|
| `## OPEN` headings in this file, **before the three filings this same commit appends below** | 56 |
| …whose body names `H3c-3` | 33 |
| …whose body names *whichever slice* | 10, of which **2** are the rejection of that form rather than a use of it, and **1** (`technical_n`) is re-ownered in its own body below on its own instruction |
| …the union, which is what this entry governs | **38** |

**The sweep can fail, proved rather than asserted:** the same walk over the string `Owner:` returns
a non-zero count and over `H99z-4` returns **0**, so a zero here would have been a finding about the
sweep rather than about the file.

**And the count is stated against a moment, because this commit moves it.** The three entries filed
below — the spanning cluster, `limits.min_clusters` under cells, and the per-stratum fold bound —
each name H3c-3 in their own provenance line, so **re-running this sweep at this commit returns 59
and 41**, not 56 and 38. They are this entry's **siblings**, filed by the same task in the same
commit, rather than its subjects: each already states `unassigned` with *no slice follows* in its own
heading, which is the form this entry exists to impose on the other thirty-eight. A reader who
re-measures and gets 59/41 has reproduced the sweep correctly; a reader who gets 56/38 is standing
one commit earlier.

**Read every one of those thirty-eight reasons this way, and it is the only change:**

- **The verdict does not move.** Every one of them already says `unassigned`, and every one of them
  now says it for a *stronger* reason: the enumeration was *"no **remaining** slice has this
  surface"* and the fact is *"**no slice follows this one**"*. Not one entry changes owner, and not
  one becomes H3c-3's — H3c-3's surface is folds and holdouts drawn inside cells, and none of the
  thirty-eight is that.
- **Every *"whichever slice next touches X"* line is `unassigned`, with *no slice follows* as the
  reason.** Seven live ones remain, named by their question rather than by position: the typo'd
  `data.units.holdout.from`'s diagnostic; `units.stratum_names`' docstring call-site count; the
  generated README's `credentials` region; `declared_credential_names`' template-default credential;
  the constraint table's unrendered `min_items`/`max_items`; the positional reference at
  § the provenance table; and the unescaped interpolation in `generators/step.py`. Each ships open.
- **It is a fact, not a deferral.** Nothing about these entries is scheduled, waiting, or blocked on
  an input. A reader who wants one closed is the owner, and this file is the brief.

**SCOPE WIDENED 2026-08-25 by H3c-3's whole-branch fix round — from *the thirty-eight* to EVERY
unclosed entry in this file.** The thirty-eight above are the entries that *justify* `unassigned` by
naming a slice, and the sentences above are addressed to them; but they are not every open entry, and
the ones they leave out are the ones that most need the sentence. Re-measured by the same walk at the
fix round's commit — sections split on `^## `, each body whitespace-collapsed first:

| Measured | Count |
|---|---|
| `## OPEN` headings | 59 |
| …the union this entry governed (`H3c-3` or *whichever slice*) | 41 |
| …outside that union | 18 |
| …of those, already carrying a *no remaining slice* sentence of their own | 3 |
| **…outside the union AND carrying no such sentence — newly covered here** | **15** |

Those fifteen say `Owner: unassigned` (one says `Owner: none; accepted`) and stop there, and
`unassigned` alone reads as *awaiting an owner* — which is the reading this file's own
`RE-OWNED 2026-08-19` entry rejects. **They are not awaiting anything. No slice follows this one, so
every one of them ships open and unowned, and the same three bullets above — the verdict does not
move, it is a fact rather than a deferral, a reader who wants one closed is the owner — apply to
them verbatim.** No body is edited, so nothing is retro-edited and the fifteen keep their own dates.
(The whole-branch review counted **14** here; the walk above finds 15, the extra being the `run`
execution-banner entry. The figure to reproduce is 15, and the same control as above holds — `H99z-4`
returns **0** over the 59.)

**And the hygiene check the `RE-OWNED 2026-08-22` entry asked for is still missing, permanently.**
It wanted a test that parses every unclosed `## ` heading's `Owner:` line **and** any *"no remaining
slice (…)"* enumeration and fails on either naming a merged slice. It would live in `tests/`, and
**there is no slice left whose surface is this file's own hygiene** — so this entry is the last time
that staleness can be corrected by a slice, which is why it is corrected in bulk rather than left to
the next one.

## OPEN — a cluster may span two cells, which breaks the between-sides independence H4c's clustered unpaired constructions assume — **Owner: unassigned, and no slice follows this one**

**Filed 2026-08-25 by H3c-3 task 20, from the slice's own design Decision 13.**

Under `assign.<axis>.method: by_attribute` a group axis reads a column, and nothing requires that
column to be constant within a `data.units.cluster_by` cluster. So a cluster's units can land in two
different arms, and — once axes are crossed — in two different **cells**. Under `method: random` this
cannot happen: `units.assignment_for` allocates whole clusters, which is the property
`E-DATA-ASSIGN-BLOCKED-CLUSTER` exists to protect for `blocked`.

**What it breaks.** H4c's `welch_t_over_units_clustered` and `unpaired_percentile_over_units_clustered`
take a Welch–Satterthwaite df from two **cluster-robust per-side variances**, each side contributing
`G_s − 1`. A cluster spanning both sides is counted once in each `G_s`, so the two sides are not
independent and the df is larger than the evidence supports — wrong in the direction of a **narrower**
interval, which is the direction that matters. H3c-3 makes the shape easier to reach rather than
creating it: cells multiply the number of boundaries a cluster can straddle.

**The check that would close it** is a constant-cluster-within-arm rule —
`units.stratum_varies_within_cluster`'s shape, one declaration over: that helper already reports the
first cluster whose units disagree about a named attribute, and the arm attribute is such an
attribute. It reports the pair and lets the caller choose the code, which is exactly what a fifth
caller would need. **The reason it is not built here** is that H3c-3's charter is the fold and the
holdout inside a cell, and a new refusal over `by_attribute` allocation would change which configs
validate for designs that declare no evaluation split at all.

**Note for whoever reads this beside a fixture:** C1's own measured roster **has one**. Fifteen units,
`S1`×7 / `S2`×3 / `S3`×3 / `S4`×1 / `S5`×1 with `control` = units 0–7, puts `S2`'s first unit in
`control` and its other two in `treatment` — which is the whole of why the two scopings reported
different `treatment` rows for one roster. A fixture built to exercise the spanning case therefore
already exists in this slice's record; what does not exist is the check.

**Severity:** Major where it applies — a published interval narrower than its evidence — and it
applies only to a design that declares `cluster_by`, a `by_attribute` group axis, and an unpaired
clustered comparison together. No config in `docs/feasibility-llm-growth-studies.md` declares
`data.units.cluster_by` at all.

## OPEN — `limits.min_clusters` counts clusters over the whole roster while a resample under a cell structure draws inside one — **Owner: unassigned, and no slice follows this one**

**Filed 2026-08-25 by H3c-3 task 20, from the slice's own design Decision 4 (Ruling LL).**

`validate._check_resample`'s `limits.min_clusters` denominator is `units.fold_basis`' third call site,
and Ruling LL deliberately kept it **roster-wide** while the other two moved to the thinnest cell:
`statistics.resample` draws over the per-unit table, which holds every condition's units, so the cell
decomposition is not that call's question. That ruling stands.

**What is still open is the warning's precision, not its call.** Under `allocation: between` a
condition's units are one arm's, so a percentile interval for that condition rests on that arm's
cluster count and not the roster's — the identical shape `W-STATS-REPORTBY-THIN` already records for
itself (*"the WHOLE roster, not a group axis's own arm"*). H3d found the same figure and called it
*"wrong in the direction of NOT firing"*, which is the right direction to be wrong in and is why
nothing here was widened: a warning that fires on a design whose every arm clears the floor is worse
than one that misses a design whose thinnest arm does not.

**H3c-3 did not move it and did not make it worse**, and this entry exists so that is on the record
rather than inferred from silence: the slice threads `cells` into `_check_holdout` and into the fold
basis and into nothing else, and `_check_resample`'s call is unchanged, still `fold_basis(roster,
cluster_by)` over the roster or over the holdout's realized test side.

**CORRECTED 2026-08-25 by H3c-3's whole-branch fix round — the paragraph immediately above is false in
its first two clauses, and this paragraph replaces them.** *"Into nothing else"* and *"did not move
it"* are both wrong. `_check_units`' `cells` local has **four** consumers, not two, and they are the
whole list: the fold basis (`units.thinnest_cell`), `_check_cell_size`, `_check_holdout`, and — the
one the paragraph above misses — **`_holdout_test_roster`, whose return value *is* `_check_resample`'s
`holdout_test`.** (`cli._resolved_holdout` is the same threading on the run side.) So the decomposition reaches this denominator by one hop, and *"the holdout's
realized test side"* names a **different set of units** after this slice than before it. **This is
therefore a disclosure of something the slice did move, not a filing of something left alone.**

**Measured rather than argued**, on one config run through `validate_config` under both trees: 24
units in two arms of 12, six clusters nested inside each arm, `cluster_by: cl`, a `by_attribute`
`arm` axis, `holdout: {method: random, frac: 0.2, seed: 1}`, `resample: {method: bootstrap, n: 2000}`.

| `limits.min_clusters` | At `main` `dfc6b7d` | At this branch |
|---|---|---|
| 3 | no `W-STATS-RESAMPLE-CLUSTERS` (flat test side: 6 units, **3** clusters) | warns (per-cell test side: 4 units, **2** clusters) |
| 5 | warns, naming **3** clusters | warns, naming **2** clusters |

So the figure moves in **both** directions — a warning that did not fire now does, and one that fired
now names a different count. (At `main` that config also earned `E-DATA-HOLDOUT-CELLS`, retired by
this slice's task 16; `validate` collects rather than aborting, so the warning was computed beside the
refusal and the comparison is between two answers to the same question, not between an answer and
silence.)

**What survives of the paragraph above:** `_check_resample`'s own call really is byte-identical, and
the open gap this entry is *about* is untouched — the count is still roster-wide rather than per-arm
under `allocation: between`, still wrong in the direction of not firing, and Ruling LL still stands.
The forward is now pinned by
`tests/test_validate.py::test_the_resample_cluster_count_is_over_the_PER_CELL_holdout_draw`, which
asserts the per-cell count by message equality at `min_clusters: 5` and its presence at 3; before that
test, wiring the forward to the constant `None` left the whole suite green.

**Severity:** Minor. Both the roster figure and the per-arm figure are true; the warning states the
one that fires less often.

## OPEN — `k` is bounded by no per-STRATUM basis, so a stratified fold can still come out empty, and cells add a multiplier rather than a bound — **Owner: unassigned, and no slice follows this one**

**Filed 2026-08-25 by H3c-3 task 19.** `units.partition_units`' docstring has recorded this since
before H3c-3: each stratum is partitioned on its own and the per-stratum folds are merged index-wise,
so when every stratum holds fewer than `k` clusters the high-index folds hold **nothing at all** —
six units as three plus three under `{k: all, stratify_by: label}` fills folds 0–2 and leaves 3–5
empty, six executions run, three of them over no units, and `validate` is silent because the basis it
reads is not the stratum's. `replication._fold_k` refuses a fold with no units by its own route, so
core reaches by one path a state it refuses by another.

**What H3c-3 changed, and what it deliberately did not.** The basis moved: `k` is now bounded by the
thinnest **populated cell's** basis (`units.thinnest_cell`) rather than the whole roster's, and
`units.partition_within_cells` calls `partition_units` once per populated cell — so the independent
partition lists are **cells × strata** where they were strata alone. **The per-stratum bound is still
a check that does not exist**, and its denominator is now one multiplier further from the number
`validate` reads. `partition_units`' docstring says all of that in those words, so the slice cannot
read as having added a bound it did not add.

**The check that would close it** bounds `k` against `min` over the per-stratum bases, inside each
cell — which is `thinnest_cell`'s walk with a second nesting level, and a rule
`reference.md` § Validation does not state today. Inventing it in `partition_units` would be a rule no
document states, which is why the docstring records rather than fixes.

**Severity:** Minor-to-Major depending on the design — an empty fold is a paid execution over no
units, disclosed by `n.resolved: 0` rather than hidden, but nothing refuses it. Reachable only under a
declared `fold.stratify_by`, which no config in `docs/feasibility-llm-growth-studies.md` declares.

## OPEN — `input_manifest_hash`'s definition changed and only `uv.lock` carries why, so `diff` prints `input_manifest DIFFERS` for identical data — **Owner: unassigned, with the reason (the charter is complete and no remaining slice has the record's schema as its surface)**

**Filed 2026-08-26 by the whole-project review's M2 fix.** `manifest_hash` was narrowed to the content
it can address — a hashed file's `mtime` no longer reaches the digest — so
`provenance.input_manifest_hash` moves for every past run whose policy hashed at least one file.
Nothing in a record says which definition produced its figure, and
[`diff`](../reference.md#operation-commands) accordingly prints `input_manifest DIFFERS` for two runs
over byte-identical data taken on either side of the change.

**This is the same shape H6a shipped for `code_hash` and it is the same refusal, taken for the same
reason rather than by analogy.** A `provenance.hash_definition` key, a fourth hash, or a
`schema_version` bump were each considered and refused there: a bump makes
`lineage.read_record_file` reject **every record already on disk**, which is strictly worse than an
unmarked value change. The carrier is `provenance.environment.uv_lock_hash` — core's own version is
pinned in that lockfile — and the honest statement of the cost is the one H5b wrote for its own
value change: **being *able* to derive a definition change from a lockfile digest is not being
told.**

**What is measured and what is not.** Measured: the value moves under `hash_all` and under
`hash_index` whenever it named at least one file, and does **not** move under `none` (no file is
hashed, so the digest's input is byte-identical); `manifest/input.json` is byte-identical across the
change and its per-file `sha256`s are unmoved; nothing derived from `code_hash` moves, and
`provenance.upstream[]` copies `code_hash`/`parameters_hash` and never a manifest hash, so no record
can carry two manifest-hash definitions the way one can carry two `code_hash` definitions. Not
measured, and the reason this is filed rather than closed: **how many records already on disk this
affects is unknowable from here**, which is exactly what a marker would have answered.

**The check its closer must make** is not "add a marker" — that is refused above. It is whether
`diff` should grow a line distinguishing *a definition boundary* from *a data change* for **both**
hashes at once, which needs something in the record to read and therefore reopens the refusal on
different grounds than either slice argued it on: H6a refused a marker for one hash, and two
unmarked definition changes in one record's history is a different question from one.

**Severity:** Minor. No number a run publishes is wrong, and no run is refused — a reader comparing
two runs across the boundary is told the data differs when it does not, and the remedy in hand is to
compare the per-file `sha256`s in the two `manifest/input.json` copies, which are unmoved.

## OPEN — `Config.raw` is a shallow copy, so writing inside one of its values is a route around the immutability a node refuses — **Owner: unassigned, and its closer owes a re-expression of another test's claim first**

**Found 2026-08-27 by [`W4-SCOPING.md`](W4-SCOPING.md) § 2, measured against `50d1a8a`.**

`Config.raw` returns `dict(object.__getattribute__(self, "_data"))` — one level. Measured:

```
cfg.raw["parameters"] = {"hijacked": True}                 → cfg.parameters.analysis.method unchanged
cfg.raw["parameters"]["analysis"]["method"] = "kendall"     → cfg.parameters.analysis.method == "kendall"
                                                              and the document underneath changed too
```

Rebinding a top-level key is contained. Writing **inside** one is not, and it sticks: `Node.__setattr__`
refuses a write under `E-CONFIG-IMMUTABLE` with the reason *"The config is the record of what ran; change
it in the file"*, while this route changes what every later [scope](../reference.md) reads after
`parameters_hash` was computed from the file. § The importable surface now discloses it — *"treat it as
read-only"*, with the consequence spelled out — and
`tests/test_config.py::test_w4_raw_is_a_shallow_copy_which_the_document_calls_read_only` pins the
behaviour so a change fails a test rather than a reading.

**Why W4 did not close it, and this is the part to read.** The obvious fix is `copy.deepcopy` in `raw`.
Run as a mutation, it makes the new pin fail — correctly — and leaves
`test_runner.py::test_per_condition_cfgs_are_not_the_same_object` **green**, measured (109 passed, 1
failed, the failure being the new pin). That test asserts
`cfg0.raw["parameters"]["analysis"] is not cfg1.raw["parameters"]["analysis"]` in order to prove **the
resolver** deep-copies per condition, and its own docstring says *"that aliasing is exactly how an earlier
defect in this project first showed itself."* If `raw` copies, that assertion is true whatever the
resolver does. **Closing this defect by deep-copying would weaken that pin silently** — the shape this
repository names *a pin weakened quietly* — so the closure owes, first, a re-expression of the resolver's
claim that does not observe it through `raw`.

**The check its closer must make:** whether any shipped step, template or fixture depends on `raw`
handing back the document's own nested objects rather than copies. Grepped at `50d1a8a`: the readers are
ten assertions in `tests/test_runner.py` and the two new ones above, and none mutates — so the change
looks safe on today's callers and the risk is entirely the pin above.

**Severity:** Minor. No shipped code takes this route, and a step that did would be corrupting its own
run deliberately; the defect is that a documented guarantee has an undocumented way around it, now
disclosed rather than closed.

---

## OPEN — the unit table has no importable name, so a plugin annotating `aggregate` invents one and the distribution stops importing — **Owner: unassigned, and no slice follows**

**Found 2026-08-27 by the fresh feasibility re-measurement in
[`../feasibility-llm-growth-studies.md`](../feasibility-llm-growth-studies.md) § Executability on this
build, measured against `dc03ec4`.**

`BaseTemplate.aggregate` is annotated `units: "UnitTable"` in core's own source; the class lives in
`publishable.stats`; `publishable.__all__` does not carry it; and `grep -c UnitTable docs/reference.md`
returns **0**. § The importable surface is the enumerated list of what a user writes against, and the
type of `aggregate`'s first argument is not on it — the four operations the table supports are specified,
the name is not.

A real plugin did the obvious thing. `publishable-llm-screening 0.1.0` writes
`from publishable import BaseTemplate, Param, UnitTable, register_template` in all three of its
templates, and on the shipped build **nothing it registers loads**:

```
error   E-PLUGIN-LOAD        data.units
        the entry point `dspy_examples` in `publishable.resolvers`, from publishable-llm-screening
        0.1.0, raised while importing and registers nothing usable: ImportError("cannot import name
        'UnitTable' from 'publishable'")
```

The resolver does not import `UnitTable` itself — the package's template modules do, one import in a
shared chain, and the resolver's entry point dies with them.

**Two resolutions, and this filing prefers neither.** Export `UnitTable` from the import root, which
widens the public surface by a name whose *methods* the project deliberately keeps closed; or state in
§ The importable surface that the table is deliberately unnamed and `aggregate` is to be left
unannotated, which is a documentation change and costs nothing. What is not available is silence: the
surface is annotated in core's own signature, and that is where a plugin author copies from.

**Severity:** Major for anyone writing a plugin with a typed `aggregate`, which the specification's own
example encourages by showing the signature. Zero for core: no shipped code imports it, and
`mypy` is clean at this commit.

---

## OPEN — `unit-executions` does not count what a step does through `io.units.train`, while the sentence around it claims proportionality to the bill — **Owner: unassigned, and no slice follows**

**Found 2026-08-27 by the same re-measurement, measured against `dc03ec4`.**

§ Before you spend it defines the figure exactly as the code computes it — the sum of `len(io.units)`
over every planned execution — and then claims: *"where a step makes one request, one assay, or one
simulation per unit, this is the count the bill is proportional to."* Under a declared `holdout`,
`_handed_counts` hands **every** scope the test partition and `execute_plan` attaches `.train` beside it,
which changes no length. So a condition-scoped step that fits over `io.units.train` does one pass per
**training** unit and contributes the **test** count.

Measured on a 240-row roster at `frac: 0.2`, by a condition-scope step returning both numbers, from
`executions.jsonl`:

```
{"step": "step02_fit_model", "scope": "condition", ..., "returned": {"n_units": 48, "n_train": 192}}
```

against the same config's `dry-run` print of `scale:  912 unit-executions (19 executions × 48 units
handed to each)`. Four times the work, on the executions that are expensive by design: a condition-scoped
fit is where the specification itself tells an author to put anything costly that depends on the swept
parameter and not on the repeat.

**Why this is a claim defect and not an arithmetic one.** The number is faithful to its stated
definition, and `.train` genuinely is a second accessor rather than a second roster. What fails is the
proportionality sentence, which a reader checks *instead of* doing the arithmetic — that being the whole
purpose of the line. The cheapest honest closure is a sentence in § Before you spend it saying the figure
counts `io.units` and not `io.units.train`, and that a fitting step under a holdout costs the training
half on top. A closure that changed the number instead would have to decide whether a step that never
touches `.train` should be billed for it, which core cannot know without inspecting user Python — which
it never does.

**Severity:** Minor mechanically, Major for the one thing the line exists for: E1 and E2 of the LLM
growth-studies analysis are exactly this shape, and the un-counted half is $380 of E1's $548 at that
analysis' own anchors.

---

## OPEN — a correction family cannot span runs, so a family declared across several runs has no representation anywhere in the record — **Owner: unassigned, and no slice follows**

**Found by:** the `growth-chart-literacy` feasibility analysis, 2026-08-28, expressing a plan whose
pre-registered multiplicity families cross run boundaries. **Read from the specification rather than
measured** — no run was executed — so this entry is about what the documents provide, and the two
sentences it rests on are quoted below rather than paraphrased.

`statistics.correction` is computed over one run's condition set: § Sweeps and repeats defines the
family as comparisons × metrics within a run, and `correction.family_shape` counts members built
from that run's own `vs_baseline` and `statistics.contrasts`. § Studies is the mechanism for a claim
spanning runs, and it copies records — [`study add`](../reference.md#what-study-add-redacts) *"copies
a run record into the bundle under that name, with host paths redacted"* — without re-deriving any
statistic across members.

**Why that is a gap and not simply a scope boundary.** Core's whole argument about multiplicity is
that a family declared in a paper should be *checkable against the record* rather than asserted:
`family_size` and `family`'s breakout exist so *"a reader can check the level without re-deriving
it"*. That property holds inside one run and silently stops holding at the run boundary — and the
run boundary is not where a researcher's family stops, because [a roster-changing variant is a
different run](../reference.md#where-units-come-from) while remaining one family. The analysis that
found this has two such families: four arms of one experiment with four rosters, and one design
replicated across five others.

**What a study can and cannot say today.** A bundle can carry every member and `report` can render
them together, so the *numbers* are all present and a reader can see them side by side. What no
artifact holds is the claim that they form a family, how large it is, or what level each member was
corrected at — so the one thing this project builds records for, *"a number that looks handled and
isn't"*, is exactly the state a cross-run family is left in. Correcting by hand and stating the
level in prose is the available route, and it is the route core exists to replace.

**Proposed resolution, and its cost.** A `study.yaml` block declaring a family over named members
plus the metric each contributes, with `report` rendering the adjusted level beside each member's
raw interval — no recomputation of any member, only the level. That keeps [the rule that a bundle
never re-derives a member's numbers](../reference.md#studies-what-a-paper-reports) while making the
family auditable. The cost is real and is why this is recorded rather than argued as obvious: it
gives a study bundle its first *computed* field, and every argument for a bundle being a copy of
records applies against it.

**Why open.** The charter is complete and no slice follows, so this is what the project ships with:
a multiplicity family that crosses runs is a prose commitment, exactly as it was before the tool.

**AMENDED 2026-08-28 (Task 11, `growth-chart-gaps` slice): closed as a documented limitation, not
by the mechanism this entry proposed.** `reference.md` § Studies now carries its own subsection, "A
correction family does not cross a run," stating the boundary this entry found and naming the route
— the author corrects by hand and declares the family's level in the manuscript, and each run's own
members still get the within-run family `correction.family_shape` already builds. No `study.yaml`
block, no computed cross-run level, and no new artifact field exist: the "Proposed resolution" above
is not built, and nothing in the code changed. A reader who wants the mechanism this entry describes
should not go looking for it — the gap is closed by naming the limit in prose, exactly the route
the entry's own "What a study can and cannot say today" section already named as available.

## OPEN — a `compare: {to: constant}` hypothesis's bound test is never answerable under a declared correction method, for a metric recorded under BOTH `weight_by` and `cluster_by` — **Owner: unassigned, and no slice follows**

**Found by:** review of Task 9 (`compare: {to: constant, value: N}`, the third `compare` form),
2026-08-28. **Measured against commit `6e96655`** by calling `hypotheses.evaluate` directly under
`holm`, `bonferroni` and `none`, not inferred from the code.

Every other counted hypothesis — a `vs_baseline` comparison or a declared contrast — gets a
correctable `correction.Member` built for it in `cli.py`, so a real correction method can rebuild its
bound at the family's own level. A `compare: {to: constant}` observation gets none: `hypotheses.py`
reads the metric's own value straight out of `results.conditions[i].aggregated`, and no `Member` is
ever constructed from that per-condition value at all. Under `correction: none` this is invisible —
nothing is corrected for anyone in the family, constant-referenced or not, and every entry's
`observed` carries no `ci95_corrected` key. Under a real method, `hypotheses.evaluate` routes a
counted constant hypothesis through the same `corrected_unavailable` path a too-thin family uses:
`ci95_corrected: null` and `supported: null` for any `evaluate_on: ci95_lower`/`ci95_upper` verdict,
regardless of how wide or narrow the raw interval actually is. `evaluate_on: observed` is unaffected
— correction only ever tightens a bound, never the point estimate — so it stays the one usable form
for a constant-referenced hypothesis under a declared correction method.

**The honest precedent.** This is not a novel failure mode: `correction.py`'s `_level_for` already
returns `None` under `correction: fdr_bh` for every member of every family, by construction —
Benjamini-Hochberg implies no per-comparison level at all — and `_tested_number` already refuses to
paper over that with the raw bound. The constant form's gap is the same honest refusal applied to a
case where the reason is "no evidence to rebuild from" rather than "no per-comparison level exists,"
and it was the sanctioned fallback (`docs/superpowers/sdd/2026-08-28-growth-chart-gaps/task-9-report.md`,
fix round 1) against the alternative — silently deciding on the raw, uncorrected bound while still
claiming family membership, which inflates every other member's Holm level for free and is strictly
worse.

**Proposed resolution, and its cost.** Build a real `Member` for the constant form, from the same
resample pool a condition's own `t_over_units`/`percentile_of_derived` bound is built from. That pool
does not survive past `stats.summarize_step` today — only the resulting `ci95` reaches `aggregated`
— so the fix is not local to `hypotheses.py`: it means plumbing raw per-unit values or resample draws
through to `cli.py`'s hypothesis-evaluation phase for a per-condition metric, the same shape of
change `E-DATA-WEIGHT-CONTRAST`'s weighted-Welch gap and the cross-run correction-family entry above
both describe as real but not free.

**AMENDED 2026-08-28 (Task 6, `correctable-condition-metric` slice): narrowed, not closed.** The
slice's Task 5 built exactly the `Member` this entry's "Proposed resolution" called for, for three
of the four rows in the design's Decision 1 table: a recorded column with no declared `resample`
(carries its per-unit values, a `t`-construction bound), a recorded column with a declared
`resample` (carries the pool), and a derived metric with a declared `resample` (carries the pool).
For all three, `hypotheses.evaluate` now rebuilds a real corrected bound at the family's own level,
and `evaluate_on: ci95_lower`/`ci95_upper` is answerable exactly as it is for a `vs_baseline`
comparison or a declared contrast. The fourth row's conclusion holds and its stated
trigger does not. A metric with no raw interval has nothing to correct, before this slice and after
it — but a derived metric with no declared `statistics.resample` is not such a metric: core resamples
a derived metric whenever a `compute` callable and a seed exist, declared or not, so the row's named
case has a percentile interval like every other resampled one. What actually reaches the no-interval
state is a resample that produced no usable interval — every draw degenerate, or a draw count below
the floor — which is how Task 5's own row-4 test reaches it. (Corrected 2026-08-28 by the branch's
fix wave; the design spec's Decision 1 table is a dated record and is corrected by an appended
ledger note rather than an edit.)

**The residual case, and why it stays open.** A recorded column under BOTH `weight_by` and
`cluster_by` still gets no `Member`, and still comes back `corrected_unavailable`. Its raw interval
is `weighted_t_over_units_clustered`, and no paired construction of that shape exists in this build,
nor a `Member` field shape for carrying both modifiers at once (`Member.__post_init__` refuses one
that does) — Task 5 deliberately builds nothing there rather than loosening that refusal. This
combination is reachable specifically because `E-DATA-WEIGHT-CLUSTER-CONTRAST` only fires on a
contrast, and a `{to: constant}` hypothesis names no contrast, so `validate` never sees the
combination it would otherwise refuse. Closing it needs the same shape of change the "Proposed
resolution" above described — a new construction and a new `Member` field — so it is still real but
not free. The charter is complete and no slice follows, so this is what the project ships with: for
that one combination the bound test is not answerable and comes back `supported: null`, and
`evaluate_on: observed` is the usable form there. **That `supported: null` is distinguishable in the record from the two `unevaluable` causes added 2026-08-28**, and stays so deliberately: this one has an `observed` block — a real raw interval with only its corrected bound missing — where both `unevaluable` causes have no block at all, so the field is absent here and a reader is never told the metric was missing when it was not. Everywhere else — including under `correction:
none`, where nothing is corrected for anyone — the bound test works exactly as it does for a
`vs_baseline` comparison or a declared contrast. (The entry's original "Why open" paragraph said the
bound test was never answerable at all; that was true when filed and false after Task 5, so the fix
wave deleted it rather than rewriting it.)

## OPEN — `expand` numbers a `groups` × `ablate` sweep in a different order from the one `reference.md` § Expansion modes documents, and neither has been chosen — **Owner: unassigned, and no slice follows**

**Found by:** the build-claim sweep over the four documents, 2026-08-29. **Measured against commit
`4207ed2`** by calling `sweep.expand` directly on the config that section prints, not inferred from
the code.

`reference.md` § Expansion modes shows a combined group-and-ablate sweep numbering its conditions
interleaved — each group level's baseline followed by that level's ablations — and its own
[§ How artifacts are organized](../reference.md#how-artifacts-are-organized) Index row states the same
rule. `expand` emits every baseline as one leading block instead:

```
documented:  00_cohort=derivation__baseline  01_cohort=derivation__labs=false  02_cohort=derivation__notes=false
             03_cohort=validation__baseline  04_cohort=validation__labs=false  05_cohort=validation__notes=false

measured:    00_cohort=derivation__baseline  01_cohort=validation__baseline
             02_cohort=derivation__labs=false  03_cohort=derivation__notes=false
             04_cohort=validation__labs=false  05_cohort=validation__notes=false
```

**The two agree on everything except the indices.** The same six conditions, the same labels, the
same units in each — so no result depends on the difference, and the standing advice in that section
(*"Address a baseline by its label, never by its index"*) is what keeps it harmless. What it costs is
a reader who designs against the documented numbering and looks for a directory
`03_cohort=validation__baseline` that is named `01_`.

**This is filed as a defect rather than as a bug because neither side is obviously right, which is
also why it is still open.** The interleaved rule the documents state is ill-defined once a second
axis makes a cell's rows non-contiguous; the tool's rule is well-defined but is not what either
document says. Picking one is a design decision, and the reason `reference.md` states the numbering
rather than quietly matching the tool is that changing the document would settle that decision by
default.

**Both halves already say so, and this entry adds only the filing.** `reference.md` § Expansion modes
carries *"`expand` numbers this differently today, and the divergence is unresolved"* with the
measured ordering quoted beside it. That sentence was verified by running at the commit above, which
is how this entry came to exist: a documented divergence with no entry here reads as an oversight
rather than as a decision nobody has taken.

## OPEN — a config cannot say WHICH comparisons are its family, so a run with one primary quantity and several supporting ones must either correct all of them or declare no family and be warned about it — **Owner: unassigned, and no slice follows**

**Found by:** the `growth-chart-literacy` feasibility analysis, re-derived 2026-08-30 against the
plan's restructure, and **measured**: seven of its fourteen configs carry
`W-STATS-FAMILY` at `validate`, and two of them carry it into an executed run's `findings:` block.

`statistics.correction` is a single switch over the whole run, and the family it applies to is
comparisons × metrics — every non-baseline condition, every declared contrast, times every metric
with an interval. A design that concludes on **one** pre-specified quantity with several supporting
comparisons beside it has no way to say so. The two available spellings are both wrong for it:
`holm` corrects the primary interval for supporting comparisons nobody reads a claim off, and
`none` earns [`W-STATS-FAMILY`](../reference.md#warnings-core-reports), whose message — *"every
interval reported is uncorrected"* — is **true and misleading in the same sentence**, because the
design intended no family rather than forgetting one.

**Why that is a gap and not a preference.** Core's argument for recording `family_size` and its
breakout is that a family declared in a paper should be checkable against the record. Here the paper
declares a family of one, or of none, and the record cannot represent either — so a reader checking
the level finds `correction: null` on every interval and no way to tell a deliberate declaration
from an omission. It is the same failure the `W-STATS-FAMILY` warning exists to prevent, arriving
from the other direction.

**Why it matters more than the count suggests.** Seven of fourteen configs carrying a warning by
construction is the shape of *a warning readers learn to skip*, which this project names as a defect
class in its own right. A reader who has learned to skip it will also skip the instance where a
correction really was forgotten.

**Proposed resolution, and its cost.** A per-hypothesis or per-contrast marker — a `family:` name, or
a `primary: true` on one hypothesis — so that `correction` applies to the marked set and the rest are
reported uncorrected without a warning. The cost is that it gives a config a second place to say
something about multiplicity, and the current single switch is what makes `family_size` derivable
from the sweep alone.

**Why open.** The charter is complete and no slice follows. What ships is: declare `holm` and correct
things you did not mean to, or declare `none` and be warned; state the intended family in the
manuscript either way.

## OPEN — a fixed-sequence gate between two hypotheses has no expression, so the structure protecting a study-level α lives outside the record — **Owner: unassigned, and no slice follows**

**Found by:** the same analysis, 2026-08-30. **Read from the specification**, not measured — the run
that would carry both hypotheses needs a deployment.

`hypotheses` is a flat list. Each entry is evaluated on its own and each verdict is recorded on its
own, and nothing expresses that one is read **only** in the branch where another is supported. The
plan that found this concludes on one quantity through one gate — reject the physiology main effect's
null, then read the shortcut reliance index — and spends no α on the second step precisely because of
that ordering. In the record the two are coordinate confirmatory claims, and a reader who reads the
second without the first has no signal that they should not.

**Why that is a gap.** Pre-registration is the one place core takes a position on inferential
discipline: a hypothesis carries the `parameters_hash` that declared it so a later addition cannot
pass as a pre-registration. A fixed-sequence gate is the same kind of commitment — made in advance,
checkable after the fact, and worthless if it can be quietly reinterpreted — and it is the structure
doing the study-level error control in the design that found this, while the multiplicity families
core *can* express are explicitly secondary to it.

**Proposed resolution, and its cost.** A `gated_by: <id>` field on a hypothesis, with the verdict
recording `unevaluable: gate_not_met` where the named hypothesis was not supported — reusing the
[`unevaluable`](../reference.md#pre-registration) mechanism that already exists for a hypothesis
that cannot reach a verdict. The cost is ordering: hypotheses would gain a dependency graph, which
needs a cycle check and a rule for what a gate on an `exploratory` hypothesis means.

**Why open.** The charter is complete and no slice follows. What ships is a `statement` field, which
is prose, and a manuscript.
