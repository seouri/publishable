# Sweeps and conditions (S3a)

**Status:** approved.
**Deliverable:** code, on top of S2. S2 is merged at `152f0bf` — 23 modules, 334 tests, a real
240-unit run reporting `resolved: 240 / completed: 226 / ineligible: 2 / failed: 12` with a
`t_over_units` interval verified independently.

S3a makes a run compare things. Until now every run executes exactly one condition; after
S3a a declared sweep expands into N conditions, each measured over the same roster, each
carrying its own attrition and its own interval.

The four documents in `docs/` remain normative and lead. Where code cannot follow them, the
document changes first and the gap goes in `docs/superpowers/spec-defects.md`.

## Why this is S3a and not S3

The S1 decomposition assigned one slice: sweeps, condition labels, the artifact tree,
`sweep.yaml`, `batch` and `fold`, nested repeats, `order: randomized`, and cross-scope reads.
That is two subsystems. § Expansion modes is 161 lines of normative specification and
§ Repeat kinds is 259.

The decisive argument is that `fold` is not a sibling of `seed`. Under a declared `fold`,
`io.units` returns only that fold's test partition, `io.units.train` starts returning data
instead of raising, and **both must raise at `run` and `condition` scope** — because a
`condition`-scoped step that fitted a model there would fit on units that later folds test on.
That is a change to the contract S2 just established, and pairing it with the first
introduction of multi-condition execution puts two reshapings of the same object in one slice.

| Slice | Contents | Retires |
|---|---|---|
| **S3a** | `baseline` + `grid`, the label grammar, the `conditions/` level, `sweep.yaml`, N-condition execution, per-condition stats, `io.conditions` / `io.read_condition`, `read_upstream` direction checks, a real `max_executions`, `W-STATS-FAMILY` | `E-SWEEP-UNSUPPORTED` |
| **S3b** | `batch`, `fold` (partitioning, test/train, the scope raise), nested levels, `order: randomized` | `E-REPL-KIND-UNSUPPORTED`, `E-REPL-ORDER-UNSUPPORTED` |

Sweeps first: folds are drawn *within each cell*, so `fold` is cleaner to build once conditions
exist — and S3a is what finally exercises the `condition_index` plumbing S2 built.

## What S3a delivers

| Piece | Detail |
|---|---|
| Expansion | `sweep.baseline` prepended as condition `00`; `sweep.grid` as a cartesian product |
| Label grammar | `<nn>_<key>=<value>`, `__` between axes; key is the **shortest unique suffix** of the dotted path; last declared axis varies fastest |
| Artifact tree | `conditions/<nn>_<label>/…` — present whenever a sweep is **declared**, not when N > 1 |
| `sweep.yaml` | Resolved conditions with their values, the repeat plan, seeds, realized order, design digest |
| Per-condition `cfg` | Each execution receives a `Config` overlaid with its condition's swept values |
| Per-condition results | Attrition, collapse, and intervals computed per condition over the shared roster |
| Summary reads | `io.conditions`, `io.read_condition(condition, step, name, repeat=None)` — `summary` scope only |
| Direction check | `io.read_upstream` raises when the named step is narrower than the caller |
| `max_executions` | Conditions × repeats checked for real against `limits.max_executions` |
| `W-STATS-FAMILY` | Warns on a multi-condition enumerated sweep, naming the family size |

**Acceptance:** `3 conditions × 5 seed repeats = 15 executions` in the correct tree; each
condition reporting its own attrition and its own interval over the same 240-unit roster;
`sweep.yaml` recording the resolved plan; `W-STATS-FAMILY` firing; and two conditions producing
genuinely different numbers — asserted on values that differ starkly, so a regression cannot
hide in rounding.

## What S3a refuses

Retiring `E-SWEEP-UNSUPPORTED` is the moment the door S1 and S2 each slammed could reopen one
level down. So **each unimplemented mode gets its own refusal**:

| Declaration | Refusal | Why not now |
|---|---|---|
| `sweep.paired` | `E-SWEEP-PAIRED-UNSUPPORTED` | A coupled axis; mechanically close to `grid` but a distinct expansion |
| `sweep.ablate` | `E-SWEEP-ABLATE-UNSUPPORTED` | `1 + n`, reads the baseline rather than re-emitting it; has its own cross-checks |
| `sweep.sample` | `E-SWEEP-SAMPLE-UNSUPPORTED` | Continuous ranges, sobol/LHS draws, and a distinct `NN_sample` label form |
| `sweep.groups` | `E-SWEEP-GROUPS-UNSUPPORTED` | An axis over **units**, not parameters — needs `allocation` and `assign`, which are hardening |

Each message says the mode is specified but not implemented in this build and will be honored
later, matching the register the other `-UNSUPPORTED` messages now use.

`E-REPL-KIND-UNSUPPORTED` and `E-REPL-ORDER-UNSUPPORTED` are **unchanged** — S3b retires those.

## Three rules taken from the specification rather than invented

**The label key is the shortest unique suffix of the dotted path.** `analysis.method` swept
alone becomes `method`; swept beside `scoring.method`, both keep a segment and become
`analysis.method` and `scoring.method`. § How artifacts are organized states this, and the
reason is that a label is also a selector — a hypothesis's `compare.condition` and a contrast's
`of`/`against` name conditions by the label's body, so it has to be something a person can
write down without seeing the directory.

**The last declared axis varies fastest**, so the numbering reads like nested loops written in
declaration order. Axis order is `groups` axes first, then parameter axes, each in declaration
order — never sorted, because the config's order is the one the reader already has.

**The `conditions/` level appears when a sweep is declared, not when N > 1.** § How artifacts
are organized says degenerate levels collapse and that "no sweep means no `conditions/` level",
and separately that `00_baseline/` is "present only when `sweep.baseline` is declared". So a
bare `sweep.baseline` with no `grid` yields ONE condition *with* the level. S2's collapse logic
keys off a count and must not be extended by analogy here.

## The central new mechanic: `cfg` is resolved per condition

A step reads `cfg.parameters.analysis.method` and receives *this* condition's value. That is
what makes the specification's promise true — steps never mention sweeps, and "adding a sweep
later changes nothing here."

So the runner builds one `Config` per condition, from the base config overlaid with that
condition's swept values, and hands it to every execution in that condition.

Its mirror image is a refusal. **A swept parameter is unreadable at `run` and `summary` scope**,
where it has no single value: a `"run"`-scoped step reading `analysis.method` would produce
output silently wrong for every condition but one, and a `"summary"`-scoped step reading it
would be picking a value no single condition owns. `E-STEP-SWEPT-PARAM` is already in the
specification's registry; S3a is where it becomes reachable.

This is an effect check, not an inspection of user code: core owns `cfg` and declines to hand
over a value that could only be the wrong one.

## The multiplicity family, and a record that must not overclaim

S3a produces N conditions each reporting an interval. That is a multiplicity family, and
§ Sweeps and repeats is blunt that reporting one uncorrected "is how a sweep feature turns into
a p-hacking feature." `statistics.correction` is S4 work.

So S3a **warns**: `W-STATS-FAMILY` on any multi-condition enumerated sweep, naming the family
size and saying correction is not implemented in this build. A warning does not change the exit
code, so the run still works.

One consequence must be closed rather than absorbed. The config `init` generates declares
`correction: holm` by default. Warning alone would mean a run emits a warning, reports
uncorrected intervals, and embeds a config claiming `holm` — a record a reader could reasonably
take as corrected. **So each aggregated metric records `correction: null` explicitly.** The
warning tells the person; the null tells the record. Neither is left to inference.

## Modules

| Module | Responsibility |
|---|---|
| `sweep.py` *(new)* | Expansion to an ordered condition list; the label grammar; `sweep.yaml`'s content. Pure: a config dict in, conditions out — no filesystem |
| `validate.py` | Retire one refusal, add four; real `max_executions`; `W-STATS-FAMILY`; swept paths resolve; swept values render as `[A-Za-z0-9._+-]+` |
| `cli.py` | Expand, write `sweep.yaml`, loop conditions, aggregate per condition |
| `artifacts.py` | `io.conditions` / `io.read_condition` at `summary` scope; the `read_upstream` direction check |
| `runner.py` · `run_record.py` | Per-condition `cfg`; per-condition entries |

`sweep.py` is pure for the same reason `hashes.py` and `stats.py` are: expansion is a function
of the config alone, and it can then be tested exhaustively without a repository or a run
directory.

## What this finally exercises

S2 gave `attrition`, `collapse_repeats`, and `assemble_run_yaml`'s `aggregated` a required
`condition_index`, specifically so cross-condition pooling could not be written by omission.
Every caller has passed `0` ever since.

S3a is the first slice where those parameters carry differing values, and therefore the first
real test that the pooling defect is closed rather than merely unwritable. "Two conditions
produce genuinely different numbers over the same roster" is a headline test of this slice, not
an incidental one.

## Testing

- **The label grammar gets a table-driven suite** straight from § How artifacts are organized:
  the shortest-unique-suffix rule in both its forms, `__` between axes, declaration order,
  the last axis varying fastest, and a per-cell baseline landing at the head of its cell.
- **Per-condition isolation** asserted on starkly different values, so a regression cannot hide
  in rounding — and asserting the two `aggregated` blocks are not the same object, since that
  aliasing is how the S2 defect first showed itself.
- **The swept-parameter refusal** tested at both `run` and `summary` scope, and confirmed NOT to
  fire for an unswept path, which reads normally at every scope.
- **Every new `E-`/`W-` identifier has a test that produces it** — the project's coverage bar,
  which has now caught codes nothing exercised in two consecutive slices.
- **A single-condition run is unchanged**: no `conditions/` level, same tree S2 produced. The
  regression risk of introducing a level is that it appears where it should not.

## Explicitly out of scope

- `paired`, `ablate`, `sample`, `groups` — each refused individually above.
- `batch`, `fold`, nested repeat levels, `order: randomized` — S3b, refusals unchanged.
- `vs_baseline` deltas, contrasts, corrections, `repeat_spread`, `cohens_d`, `Estimate` — S4.
  S3a marks the baseline condition `is_baseline: true` and computes no deltas.
- The leaf-type `validate` crashes recorded in the defect ledger. Still pre-existing, still
  needing a config-envelope schema, still not this slice.

## Ledger entries this slice should retire or answer

- *"New error identifiers: `E-SWEEP-UNSUPPORTED` …"* — narrowed; that code retires, four
  replace it, and the entry should be updated rather than deleted.
- *"The generated config calls itself 'the complete parameter set' before it is one"* — S3a
  restores `sweep`, leaving only the `statistics` sub-keys absent. Narrow it again.
- *"`validate` findings are not ordered by config position"* — untouched, still open.
