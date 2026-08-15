# Batch and nested repeats (S3b)

**Status:** approved.
**Deliverable:** code, on top of S3a. S3a is merged at `99d6df7` — 428 tests, a sweep expanding
into N conditions each carrying its own attrition and its own interval over one shared roster.

S3b makes a repeat structure. Until now `replication.repeats` holds at most one level and only
`seed` is honoured; after S3b a design can declare a `batch` level, nest a second level inside
it, and ask for the executions inside each batch to be shuffled.

The four documents in `docs/` remain normative and lead. Where code cannot follow them, the
document changes first and the gap goes in `docs/superpowers/spec-defects.md`.

## Why this is S3b and not S3

The S1 decomposition assigned one slice: sweeps, condition labels, the artifact tree,
`sweep.yaml`, `batch` and `fold`, nested repeats, `order: randomized`, and cross-scope reads.
S3a took the sweep half. What remained still contains two subsystems, and the seam between
them is sharper than the one that split S3.

`batch`, nesting, and `order: randomized` are **execution-plan** concerns. They change how many
executions there are, what they are called, and in what order they run. They do not change what
a step can see or how per-unit values combine.

`fold` changes three rules S2 established, all in the inference base:

| Rule as S2 built it | What `fold` requires |
|---|---|
| `io.units` is the whole roster; `.train` always raises | Returns one fold's test partition; `.train` returns data; **both raise at `run` and `condition` scope** |
| `collapse_repeats` averages per unit across repeats | Per-unit values **concatenate** — each unit is tested once per fold sweep (`reference.md` § How a metric becomes a number) |
| `attrition` intersects `completed` across **every** repeat-scoped execution | Intersects over *the repeats a unit was handed*, and `resolved` counts the partition, not the cohort |

That third one is not a refinement. `reference.md` § The per-unit tables says it outright:
intersecting over every repeat "would report `completed: 0` for any design containing a fold,
because no unit is ever in more than one of them." S2's implementation does exactly that, so
`fold` arrives with a defect already waiting for it.

| Slice | Contents | Retires |
|---|---|---|
| **S3b** | `batch`, nested levels, `order: randomized`, the `read_upstream` `shared/` fix | `E-REPL-ORDER-UNSUPPORTED`; narrows `E-REPL-KIND-UNSUPPORTED` to `fold` |
| **S3c** | `fold`: partitioning, `k: all`, `stratify_by`, test/train, the scope raise, concatenating collapse, per-unit attrition | `E-REPL-FOLD-UNSUPPORTED` |

Batch first, because nested levels land in the same plumbing `fold` needs. Building `fold`
first would mean building it once and re-plumbing it when nesting arrived.

## What S3b delivers

| Piece | Detail |
|---|---|
| The level model | `resolve_repeats` returns `list[RepeatLevel]` — kind, `n`, and its own members |
| Crossing | The runner crosses levels outer to inner into leaf executions |
| Composed labels | `batch03_seed42` — batch positional, seed by value |
| Nested directories | `conditions/<nn>_<label>/batchNN_seedNN/<step>/` |
| `batch` | A level that varies nothing the pipeline declares; `n` and nothing else |
| `order: randomized` | Shuffles `(condition × inner-repeat)` **within** each batch; batches stay fixed |
| `order_seed` | Derived from the design digest, recorded in `sweep.yaml` |
| `W-REPL-DETERMINISTIC` | Warns on a `batch` level when no step sets `nondeterministic = True` |
| `read_upstream` | No longer hard-codes `shared/` |

**Acceptance:** 2 conditions × 3 batches × 2 seeds = 12 executions in the correct nested tree;
`order: randomized` producing an order fixed across batches and shuffled within one, reproducible
from the recorded `order_seed`; `W-REPL-DETERMINISTIC` firing; and a single-level `seed` run
byte-for-byte unchanged from S3a.

## What S3b refuses

Retiring a blanket refusal must not leave what it covered silently accepted. That rule has now
caught a defect in each of the last three slices, so each unimplemented thing gets its own name:

| Declaration | Refusal | Why not now |
|---|---|---|
| `{kind: fold, …}` | `E-REPL-FOLD-UNSUPPORTED` | S3c. `k` and `stratify_by` need no separate codes — the kind refusal covers them |
| Two levels of one kind | `E-REPL-LEVEL-DUPLICATE` | Labels compose by kind and `repeat_spread` reports one entry per level; two `seed` levels make both ambiguous, and no document describes such a design |
| More than two levels | `E-REPL-LEVEL-DEPTH` | Every documented example is two deep. A third level multiplies executions cubically and the documents do not say what it means |

`E-REPL-ORDER-UNSUPPORTED` retires outright: `as_declared` and `randomized` are the whole
vocabulary and both ship. The existing `E-REPL-KIND` (for `bootstrap`, `permutation`,
`technical`, `biological`, `holdout`) is **unchanged** — those are not repeat kinds at all, and
their refusals route elsewhere rather than waiting on a slice.

The depth cap is the one judgment call here. An uncapped depth is cheap to implement, since
crossing is naturally recursive — but it would ship directory nesting, the execution-count
warning, and eventually `repeat_spread` in a configuration no document describes and no test
covers. A cap is trivially lifted later; a wrong nesting semantics baked into artifact paths is
not.

## The level model, and why structure survives

`resolve_repeats` currently returns a flat `list[Repeat]`, one label each. Nesting could keep
that shape by composing labels into the leaves, and the diff would be smaller.

It should not, because two artifacts want the levels rather than the leaves. `sweep.yaml`
records `repeats` grouped by kind with a resolved `seeds` list, and separately a composed
`labels` array. `repeat_spread` — S4's, not this slice's — reports one entry per level, outer
to inner, which is the entire reason the `batch` kind exists: how much the *world* moved and how
much the *RNG* moved are two numbers, and averaged into one the larger is mislabelled as
randomness the tool controls.

Both of those are level-shaped. Flattening to leaves and recovering the levels by splitting
label strings is derived-by-parsing, and it drifts the first time a label format changes.

So the level list is what `resolve_repeats` returns, and the runner crosses it:

```
RepeatLevel(kind="batch", n=3, members=[...])     # outer
RepeatLevel(kind="seed",  n=2, members=[...])     # inner
    ↓ crossed, outer to inner
batch01_seed17  batch01_seed42
batch02_seed17  batch02_seed42
batch03_seed17  batch03_seed42
```

Labels follow the specification's spelling exactly: a batch is positional (`batch03`), a seed
carries its value (`seed42`), matching the `seed{n:02d}` derivation S1 already ships and the
collision handling that widens it when two seeds would render alike.

## `order: randomized` shuffles inside a batch, never across

A `batch` is a position in time. Shuffling batches against each other would destroy the thing
being declared, so core fixes the outer batch order and randomizes the `(condition,
inner-repeat)` pairs inside each one.

That is also the design an operator wants: every condition met once per batch, in an order that
does not confound it with position. `reference.md` § A `batch` says *when*, not *what* states
both halves.

`order_seed` derives from the design digest — not from `parameters_hash`, because editing any
parameter would otherwise redraw the order of a run that varied nothing about it. It is
recorded in `sweep.yaml` beside the realized `execution_order`: the seed so the plan is
derivable, the order because what happened is not a thing to re-derive. `started_at` is already
recorded per execution, which is what makes "were the batches actually separated?" answerable
from the record rather than from someone's memory.

**With no `batch` level declared, the whole run is one block.** The documents describe the
shuffle only in terms of batches, so this case has to be pinned rather than left to fall out of
the implementation: `order: randomized` under a bare `seed` level shuffles the
`(condition, seed)` pairs across the entire run, because there is no batch boundary to shuffle
inside. That is the reading consistent with the rule above — a batch bounds the shuffle when one
exists, and bounds nothing when it does not — and it is the one an operator asking for a
randomized order without blocks would expect. It gets its own test.

Core does not schedule the separation. It has no wall clock to enforce, and inserting one would
be a tool deciding when your instrument is free.

## The warning a `batch` needs

`validate` warns when a `batch` level is declared and no step in the pipeline sets
`nondeterministic = True`. Under a fully deterministic pipeline a `batch` re-computes the same
answer *n* times, and its dispersion is a row of zeros that cost *n* times the compute.

This is a declaration-level check — the declared kind against the declared attribute — so core
can make it without looking at what any step does, which keeps it on the right side of
[greenfield only](../../design-principles.md#greenfield-only). The `nondeterministic` attribute
already exists on `BaseStep`; nothing reads it yet.

## Modules

| Module | Responsibility |
|---|---|
| `replication.py` | The level model: `RepeatLevel`, `resolve_repeats` returning a list of them, the three new refusals |
| `runner.py` | Crossing levels into leaf executions; nested directory paths; the within-batch shuffle |
| `validate.py` | The three refusals as diagnostics, and `W-REPL-DETERMINISTIC` |
| `artifacts.py` | `read_upstream` no longer hard-coding `shared/` |
| `cli.py` · `sweep.py` | `order_seed` and the realized `execution_order` into `sweep.yaml` |

`sweep.py` stays pure — it composes the `sweep.yaml` payload and writes nothing. `stats.py` is
untouched by this slice, which is the clearest single sign the boundary is in the right place.

## Testing

- **The crossing gets a table-driven suite**: one level, two levels, the outer-to-inner order,
  and the composed label spelling. The last axis varies fastest, as it does for conditions.
- **`order: randomized` is tested for what it must *not* do** as much as what it does: batches
  appear in declared order, the pairs inside one batch are shuffled, and the same `order_seed`
  reproduces the same realized order. A test asserting only "the order differs from declared"
  would pass on an implementation that shuffled batches too.
- **Every new `E-`/`W-` identifier has a test that produces it** — the project's coverage bar,
  which has caught unexercised codes in three consecutive slices.
- **A single-level `seed` run is unchanged.** Introducing a level that appears where it should
  not is this slice's main regression risk, exactly as it was for `conditions/` in S3a.
- **The `read_upstream` fix is tested through a repeat-scoped step reading a condition-scoped
  step**, which is the case that fails today.

## Explicitly out of scope

- `fold` in every part — refused by name above.
- `repeat_spread` — S4. S3b makes the level structure available; S4 reports dispersion from it.
  This slice adds no statistics at all.
- Three or more levels, and two levels of one kind — refused above.
- Scheduling or enforcing batch separation. Core records `started_at` and nothing more.
- Per-cell baseline expansion (`E-SWEEP-BASELINE-PARTIAL`). It is a sweep feature, not a repeat
  one; naming it here would pull scope sideways. It stays in the ledger.

## Ledger entries this slice should retire or answer

- *"`read_upstream` hard-codes `shared/`"* — retired by this slice.
- *"New error identifiers: `E-REPL-KIND-UNSUPPORTED` / `E-REPL-ORDER-UNSUPPORTED`"* — the order
  code retires; the kind code narrows to `fold`. Update rather than delete.
- *"A single repeat has no dispersion, and the documents don't say what is reported"* — still
  deferred, and now clearly S4's, since dispersion is what `repeat_spread` reports.
- *"`per_repeat`'s shape when a run has no repeats is unspecified"* — untouched, still open.
