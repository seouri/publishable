# Units and the inference base (S2)

**Status:** approved.
**Deliverable:** code, on top of S1. S1 is merged at `36f9a0d` — 25 modules, 194 tests,
`new` → `generate experiment` → `validate` → `run` producing a real `run.yaml`.

S2 makes `n` mean something. Until now every number a run reports is a scalar a step
returned; after S2 a metric recorded per unit carries an interval computed from the units
themselves, and the four attrition counts reconcile.

The four documents in `docs/` remain normative and lead. Where code cannot follow them,
the document changes first and the gap goes in `docs/superpowers/spec-defects.md`.

## What S2 delivers

| Piece | Detail |
|---|---|
| Unit resolution | `from: index.csv` and `from: {glob: ...}`; resolved order preserved; `provenance.units` and `units_hash` |
| `Unit` | Frozen, hashable by `key`; fields `key`, `paths`, `attributes`; declared attributes readable directly as `unit.<name>` |
| `io.units` | Iterate, `len`, integer index, plus `.train` |
| `io.record(unit_key, values)` | Appends a row to this step's per-unit table |
| `io.skip(unit_key, reason)` | Declares a unit ineligible by design |
| Per-execution files | `units.parquet` (one row per completed unit) and `ineligible.jsonl` |
| Attrition | `resolved` / `completed` / `ineligible` / `failed`, reconciling exactly |
| `max_failed_fraction` | Enforced as the run goes — the runner's one named early stop |
| Repeat collapse | Per-unit averaging across a condition's repeats |
| `basis` split | `units` when the metric is a recorded column, `repeats` otherwise |
| `t_over_units` | Student's *t* on the per-unit values, df = completed − 1 |

**Acceptance:** a 240-unit fixture in which some units are skipped and 12 go unrecorded
reports `resolved: 240`, `completed: 228`, counts that reconcile, and a recorded column
metric carrying a `t_over_units` interval verified independently of its own implementation.

## The counting rule

`docs/reference.md` § The per-unit tables settles this, and it is the conceptual centre of
the slice: **a failed unit has no row anywhere.** `completed` is a row in `units.parquet`,
`ineligible` is a line in `ineligible.jsonl`, and

```
failed = resolved − completed − ineligible
```

Failure is *derived*, never signalled. A step does not report that a unit failed; it simply
does not record one, and core notices. That is what makes the count honest under a step that
crashes halfway through its loop, and it is why the tests assert the reconciliation identity
as an invariant rather than checking three numbers that could drift apart.

Across repeats, a unit counts as `completed` for the condition only if it completed in
**every** repeat it was handed to. § What isn't a repeat gives the reason: intersection
rather than union, because the collapse averages per unit before any interval is computed,
and a unit present in three of five seeds would otherwise enter that average on a different
number of observations than its neighbours — a ragged table dressed as a rectangular one.

## What S2 refuses

S1's hardest lesson was that "out of scope" must mean **refused**, never silently ignored.
A declared `sweep` was being dropped on the floor while the run reported success, and the
record described an experiment nobody ran.

S2 retires `E-DATA-UNITS-UNSUPPORTED`, which is the blanket refusal S1 raised for the whole
block. Retiring it must not re-open that door one level down, so **each sub-field S2 does
not implement gets its own refusal**:

| Declaration | Refusal | Lands in |
|---|---|---|
| `allocation: between` | `E-DATA-ALLOCATION-UNSUPPORTED` | needs `sweep.groups`, so S3 at the earliest |
| `assign` | `E-DATA-ASSIGN-UNSUPPORTED` | same |
| `cluster_by` | `E-DATA-CLUSTER-UNSUPPORTED` | hardening — changes the interval construction |
| `weight_by` | `E-DATA-WEIGHT-UNSUPPORTED` | hardening |
| `measurements` | `E-DATA-MEASUREMENTS-UNSUPPORTED` | hardening |
| `holdout` | `E-DATA-HOLDOUT-UNSUPPORTED` | hardening |

`allocation: within` is accepted: it means every unit appears in every condition, which with
a single condition is a no-op.

`from: {resolver: <name>}` is also refused (`E-DATA-RESOLVER-UNSUPPORTED`) — resolvers are
plugin artifacts and the registry arrives with plugins in hardening.

**`io.units.train` always raises in S2.** § Steps and artifacts specifies that it raises when
neither a `fold` repeat nor a `holdout` is declared, because an empty list would let a fit run
on nothing and write a plausible model. Neither can exist in S2, so the raise is the specified
behaviour rather than a stub.

## Modules

Two new, five modified. `docs/reference.md` § Package layout already names both new ones.

| Module | Responsibility |
|---|---|
| `units.py` *(new)* | Resolution from a table or a glob; the frozen `Unit`; the `UnitList` supporting exactly iterate / `len` / index / `.train` |
| `stats.py` *(new)* | **Pure.** A collapsed table in; values, `basis`, `n`, `ci95` and `method` out. No filesystem, no config parsing, no git |
| `artifacts.py` | Gains `io.record`, `io.skip`, `io.units`; writes `units.parquet` and `ineligible.jsonl` when an execution ends. Remains the only module that writes inside a run directory |
| `runner.py` | Recomputes attrition after each execution; owns the one named early stop |
| `validate.py` | Retires one refusal, adds seven; resolves the roster so key-uniqueness and attribute checks are real rather than deferred |
| `materialize.py` | Restores the `data.units` block to the generated config |
| `cli.py` · `run_record.py` | Resolve and hash the roster; carry `n`, `basis`, `ci95` and `method` into the record |

**`stats.py` is pure** for the same reason `hashes.py` is: it can then be tested exhaustively
without a repository, a run directory, or a config, and a statistical claim is the last thing
that should be entangled with I/O.

## The early stop, and the guarantee it qualifies

S1's runner guarantees that **a failed execution never stops the run** — the plan is executed
to its end, because abandoning it throws away every execution still pending and `resume` cannot
un-abort a plan that was never attempted.

`max_failed_fraction` is the one exception, and § What isn't a repeat argues it: unit failures
only accumulate, so once the fraction is past the threshold no later execution can bring it
back, and spending the remaining compute to confirm that is waste.

So `execute_plan` gains exactly one documented early-stop condition. After each execution it
recomputes **distinct units that failed in at least one execution, over the resolved roster**,
and stops when that exceeds `limits.max_failed_fraction`, marking the run `failed`. The
guarantee is restated in the module, in full: *a failed execution never stops the run; only
crossing the attrition threshold does.*

The fraction is distinct-units-over-roster rather than failures-over-executions because that
is the only reading that means the same thing under a single condition, under folds, and under
a group axis — a threshold set once has to survive all three.

## Data flow

1. **`validate`** resolves the roster. § Where units come from is explicit that resolution runs
   at validate and `dry-run`, not only at `run`, because every unit check is a question about
   the resolved table. Keys unique, declared attributes present, reserved names (`key`, `paths`,
   `attributes`) rejected.
2. **`run` phase 5** resolves again, hashes the list in resolved order into
   `provenance.units_hash`, and records `provenance.units`.
3. **Phase 7**, per execution: `io` exposes the `UnitList`; the step calls `io.record` and
   `io.skip`; on execution end `io` writes `units.parquet` and, when anything was skipped,
   `ineligible.jsonl`.
4. **After each execution**, the runner recomputes attrition and may stop.
5. **After the loop**, repeats collapse per unit into a condition-level table — held in memory
   for S2, since only S4's `aggregate` needs it on disk — and `stats.py` produces the reported
   value, `basis`, `n`, `ci95` and `method`.

`units.parquet`'s columns are the unit key under the name `data.units.key` gives it, then every
declared attribute, then the union of every key any row recorded, with a column absent from a
row reading as null.

## Dependencies

`numpy`, `scipy` and `pyarrow` join PyYAML. The stdlib-only spine ends here, deliberately.

`scipy.stats.t.ppf` is the reference implementation of the Student's *t* quantile. The
alternative considered and rejected was hand-rolling it: roughly forty lines of incomplete-beta
inversion that must be right at df = 1 and df = 1000, whose subtle errors produce intervals
that look plausible and are wrong. That is the exact failure this project refuses, and it is
not worth two fewer dependencies. `numpy` is needed by S4 regardless; `pyarrow` is what
`units.parquet` means.

## Testing

**The interval is verified three ways, none of them circular.** Checking `t_over_units`
against `scipy.stats.t.ppf` would test nothing, since the implementation calls it. Instead:

- against **published critical values** — *t*(0.975, df = 9) = 2.262;
- against a **hand-computed** interval on a small fixed dataset, with the arithmetic written
  out in the test so a reader can follow it;
- by the **property** that the interval is strictly wider than the normal approximation at
  small *n* and converges toward it as *n* grows. This is the check that would catch shipping
  *z* by mistake.

**Attrition tests assert the reconciliation identity** — `resolved == completed + ineligible +
failed` — as an invariant in every scenario, rather than asserting three numbers separately and
letting them drift.

**The early stop is tested from both sides:** a run that crosses the threshold stops, reports
`failed`, and leaves the executions it did finish recorded; a run that stays under it runs to
completion even with failures present.

**Every new `E-`/`W-` identifier has a test that produces it** — the project's coverage bar,
carried forward from S1, which caught three codes nothing exercised.

## Explicitly out of scope

- Every `data.units` sub-field in the refusal table above, and resolvers.
- Sweeps, `batch`/`fold` repeats, and `order: randomized` — S1's refusals for those stay exactly
  as they are.
- `aggregate`, derived metrics, percentile intervals, contrasts, corrections, `repeat_spread` —
  all S4. S2 computes one interval construction, `t_over_units`, over recorded columns only.
- The full scalar-coercion rule for returned values. S1 ships a shape gate; S2 adds `io.record`,
  which is the second of the three surfaces that rule governs. Unifying all three is worth doing
  once `aggregate` exists, so it stays deferred and stays in the ledger.
- Writing the collapsed condition-level table to disk.

## Ledger entries this slice should retire or answer

- *"S1 omits `data.units` from the materialized config"* — retired by this slice.
- *"The generated config calls itself 'the complete parameter set' before it is one"* — partially
  addressed; `sweep` and the `statistics` sub-keys remain absent, so the entry stays with its
  scope narrowed.
- *"A single repeat has no dispersion, and the documents don't say what is reported"* — S2 hits
  this the moment it computes over a collapsed table, and must answer it rather than defer again.
- *"`per_repeat`'s shape when a run has no repeats is unspecified"* — **not** triggered by S2
  after all. On review this was an overclaim: S2 changes `aggregated`, not `per_repeat`, and
  the `""` key arises only when no `replication` block is declared, which the collapse handles
  without needing a rule. The entry stays deferred, unchanged.
