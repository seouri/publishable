# Scoping: a downstream run cannot address an upstream's conditions

**Measured 2026-09-22 against `publishable@3650820` (v0.2.7) and the study at
`2026-08-28-gcl-measurement@f26e6dc`.** Every claim below was read off the code
or off a run record, and the line numbers are quoted from the commit named.

## The defect, as it actually happened

E4b is a 2-condition × 5-repeat arm of a growth-chart study, 2,520 metered
requests. Its `summary`-scope step read `parameters.stimulus.physiology` — a
path that arm sweeps — and `E-STEP-SWEPT-PARAM` raised at the top of the step,
after every condition had run:

    status: partial                                  # run.yaml:3
    error: 'E-STEP-SWEPT-PARAM ContractError: ...'   # run.yaml:258

That is the documented behaviour and it is correct. `reference.md` § What
`status` means says so directly: *"A `scope: "summary"` step that raises is not
one of these — every condition ran, and its own execution is one failure among
the others, so the run is `partial` and the conditions are readable without
it."* The study's own bug, fixed the same day.

**What the sentence does not say is that the summary is then unrecoverable at
any price short of re-running the arm.** Three routes were tried against the
real directory:

| Route | Outcome, measured |
|---|---|
| `publishable resume <run_dir>` | `E-RESUME-RUN-ENDED` — `run.yaml` exists, the attempt ended, and a record is never modified |
| the same, hypothetically permitted | would then meet `E-RESUME-CODE-MOVED` (`cli.py:5755`) — recovery requires the fixed step, and `resume` pins `code_hash` |
| a second run through `io.reuse_from` | `E-UPSTREAM-STEP-SCOPED` (`lineage.py:247`) — the steps holding the material are condition- and repeat-scoped |
| `publishable reproduce` | re-executes, so it re-pays all 2,520 requests |

**And the material is all on disk.** Every artifact a fixed `step04_compare`
reads survives in that run directory, for both conditions and all five repeats:

    conditions/00_baseline/seed00/step03_screen/{selection_half.json,units.parquet}
    conditions/01_physiology=concerning/seed00/step03_screen/{...}
    …

The execution block records **16 `completed` and 1 `failed`**, and the one
failure is `step04_compare` itself (`run.yaml:254`). So
`E-UPSTREAM-STEP-INCOMPLETE` would not refuse these reads either — § `reuse_from`
addresses an artifact is explicit that a `partial` upstream *run* is not refused
on that account alone, the named step's own status being what the check reads.

**Scope is the entire barrier.** A correct second run, declaring E4b as its
upstream, would recompute that summary for **zero metered requests** — if it
could name a condition.

## What core already has, and what it is missing

| | |
|---|---|
| `ReportIO` (`artifacts.py:1400`) | a **read-only**, record-driven reader over a finished run directory, exposing `conditions`, `repeats` and `read_condition` — deliberately not a `StepIO` subclass, so the write half cannot come with it |
| `derive_step_scopes_and_repeats` (`artifacts.py:588`) | derives each step's scope and the repeat labels **from a run record's `execution` block**, which is exactly what a downstream holds about an upstream |
| `read_condition`'s path resolution (`artifacts.py:569-585`) | `(index, label)` → `conditions/<nn>_<label>/[<repeat>/]<step>`, shared with `StepIO` through module-level functions rather than inheritance |
| `condition_dir_name` (`sweep.py:742`) | the single source of truth for `<nn>_<label>`, called by both the runner and `read_condition` |
| the label as a selector (`sweep.py:112-135`) | a condition label's **body** is already parsed back into axes by a hypothesis's `compare.condition`, a contrast's `of`/`against`, and a `report` filter |
| **missing** | any way for a step in run B to reach any of it for run A |

**So the traversal, the record derivation and the read-only posture all exist
and are tested.** `report` performs this exact operation — address a finished
run's condition-scoped artifacts from its record — on every run it renders. What
is absent is the policy and the addressing to offer it across runs.

## The refusal's argument is sound. A label-body selector is a different argument.

`lineage.py:210-220` states the ground plainly, and it is right:

> An upstream that is unswept today and gains a level tomorrow would relocate
> that artifact while every hash still matches, and a downstream read that
> worked before the level was added and reads a different cell after it is the
> exact failure the missing selector exists to prevent.

**This scoping initially read that as broader than its own argument, on the
theory that an upstream pinned by `run_id` cannot gain a level. That reading is
wrong and is recorded here rather than dropped.** `io.reuse_from(run_id, step,
name)` is a call in step code, and its locator has two forms — a bare `run_id`
and an absolute path, the latter permitting **`latest`** (`reference.md` §
Errors core raises, `E-UPSTREAM-RUNID-MISMATCH`). Under `latest` the locator
literal lives in `src/**`, so `code_hash` is *identical* across two downstream
runs while the upstream underneath them relocates. The hazard is real, it is
reachable today, and an index selector walks straight into it.

**The opening is not that the refusal is too broad. It is that an index selector
and a label-body selector fail differently:**

| Selector | An axis is added upstream | Failure mode |
|---|---|---|
| index (`01`) | `01` still exists, naming a different cell | **silent** — wrong numbers, every hash matching |
| label body (`physiology=concerning`) | the label becomes `physiology=concerning__format=digit`; the old body names nothing | **loud** — the read refuses |

Core already committed to the second form everywhere else a condition is named,
and `E-SWEEP-VALUE-UNNAMEABLE` exists to keep those bodies parseable — a swept
value rendering `__` is refused precisely because *a label is also a selector*.
A cross-run read addressed by label body inherits that guarantee. That is the
charter's actual claim, and it is narrower and better founded than "the refusal
is too broad."

## What a slice would have to decide

1. **The surface.** A fourth reader beside `read_upstream`/`read_condition`/
   `reuse_from` — plausibly `io.reuse_condition(locator, condition, step, name,
   repeat=None)` — or a `condition=`/`repeat=` pair on `reuse_from` itself. The
   argument for a separate name is that `reuse_from`'s refusal is documented,
   tested and load-bearing, and quietly widening it rereads every existing
   message.
2. **The unswept upstream, which a label selector does not reach.** `artifacts.py:584`
   shows an unswept run carries `label is None` and writes directly under the run
   directory — the very case `lineage.py:210` calls *"the one case where the
   ambiguity does not actually exist"* and refuses anyway. A label-addressed read
   has nothing to name there. Still refused, or a sentinel? **This does not fall
   out of the design and the slice must answer it.**
3. **Whether `latest` is admissible at all for a condition-addressed read**, given
   the section above. Refusing the combination is cheap and defensible.
4. **What the downstream records.** `provenance.upstream[]` already copies the
   upstream's hashes; a condition-addressed read should plausibly record *which*
   conditions were consumed, or the record understates the lineage.
5. **Whether this reopens the missing-selector argument generally.** It should not:
   the claim is about a *label body*, not an index, and § `reuse_from` addresses
   an artifact's reasoning against an index selector survives intact.

## What changes

- `docs/reference.md` § `reuse_from` addresses an artifact, § Lineage between
  runs, § Step scope, and the two `E-UPSTREAM-STEP-SCOPED` error rows.
- § What `status` means gains the clause this defect is actually about: what a
  `partial` costs when the failure is at `summary` scope. **Deliberately not
  edited in the PR that files this scoping** — a normative edit made on the
  strength of an unread scoping inverts the order this repo works in.
- `src/publishable/lineage.py`, `src/publishable/artifacts.py`.
- `tests/test_lineage.py:347,418` pin the current refusal and would move.

## How it would be shown to work, and to be able to fail

The real E4b run directory is the acceptance test and it is already on disk: a
second run declaring it upstream must reproduce `summary_basis.json` for both
conditions at **zero metered requests**. The mutation that matters is the loud
one — rename a condition's label body in a copied record and assert the read
refuses rather than landing in a neighbouring cell. A test asserting only that
a correct read succeeds proves nothing about the property the whole design rests
on.

## What this does not do

- Not a mutable record, and not a `resume` that accepts a terminal run. Both
  would let one record carry two `code_hash` values, which is what the three-hash
  split exists to prevent.
- Not a core check that a summary step reads a swept parameter. *Greenfield only*
  — core never inspects the body of user Python, and that rule is not negotiable
  for a convenience.
- Not an index selector on `reuse_from`.
- **Not a recovery of anything but E4b-shaped cases.** A run whose condition
  artifacts were never written is unreachable by any of this.
