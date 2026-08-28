# G2 — a correctable member for a condition's own metric: plan

Executes [the design](../specs/2026-08-28-correctable-condition-metric-design.md), which decides
against [`G2-SCOPING.md`](../G2-SCOPING.md)'s measurement of `main` at `b3d1d06`.

**Baseline to hold against:** `uv run pytest -q` → 3531 passed, 1 skipped, 2 xfailed.

**Two standing rulings every task inherits.** A member is built only under a declared
`statistics.resample` — a `t`-interval metric keeps `corrected_unavailable`, and no task may
synthesise a pool for it. And no pool reaches `run.yaml`.

---

## Task 1 — capture the bit-stability oracle, before anything moves

Run a project to completion at `b3d1d06` with a declared `statistics.resample`, a multi-condition
sweep, a declared contrast and at least one confirmatory hypothesis on a bound, so the record
carries real `ci95_corrected` values and a real `family_size`. Store its `run.yaml`.

- **Store the whole record, not a digest of it.** A digest tells you something moved; the record
  tells you what. `CLAUDE.md`'s guard-pin row is explicit that a digest over a document that
  legitimately changes is a proxy that fails whenever the document does its job.
- The oracle's own assertion is that this run's corrected bounds are byte-identical after the
  slice. Write it as a test now, watch it pass now, so a later green is evidence rather than
  coincidence.
- **This task ships nothing else.** A pin captured in the same commit as the change it guards is a
  pin over the change.

## Task 2 — `percentile_of_derived` and its clustered sibling return the pool

`stats.py:1574` and `stats.py:1747`. Both compute a pool, sort it, read `interval_at` off it, and
drop it.

- Return it. No arithmetic, no seed, no draw count changes.
- **19 call sites name these functions** across `src/` and `tests/`; the unpaired form has one
  production caller (`stats.py:3298`). Update every one, and confirm by grep after — this is a
  return-shape change, so a missed site is a `TypeError` rather than a silent wrong answer, which
  is the good direction but still has to be swept for.
- **The pool must be the one the interval was read off**, not a re-drawn one. Decision 2.
- Mutation: return a re-sorted copy of a *differently seeded* pool and confirm a test catches it. If
  nothing does, the pool is unpinned and the slice's whole premise is untested.

## Task 3 — `percentile_over_units` does the same for a recorded column

`stats.py:1148`. Same shape, same rules. It returns a bare `Interval | None` today, so its change is
the more invasive of the two — read every caller before editing.

## Task 4 — `summarize_step` carries the pool out

`stats.py:2843`. The pool travels beside the interval it belongs to.

- **It stops at `cli.py`.** `Member`'s docstring states pools may not reach `run.yaml`; a test must
  assert the record contains no pool, and that test has to be able to fail — write it, then put a
  pool in the record deliberately and watch it go red.

## Task 5 — `cli.py` builds the member

At the site that assembles a condition's `aggregated` metric block.

- **Exactly one of `pool`/`diffs`/`sides`**, and it is `pool`. `Member.__post_init__` refuses
  otherwise, which is the guard working — do not loosen it.
- **Only under a declared `resample`.** Decision 1. A `t`-interval metric builds nothing.
- `where` must be the same key `hypotheses.py` looks a member up by — read `_comparison_step_blocks`
  and the `(where, step, metric)` tuple before choosing it, rather than inventing a key that looks
  right.

## Task 6 — narrow the branch, amend the filing

`hypotheses.py:412`.

- The branch now fires for a counted hypothesis with no member **and no pool to have built one
  from**. Its comment currently explains the old, wider condition — rewrite it to the new one rather
  than leaving a sentence that describes what the code used to do.
- **Amend, do not delete, the `spec-defects.md` entry.** It closes for the declared-resample case
  and stays open for the `t` case, so it is a narrowing rather than a closure. A reader who finds it
  gone will conclude the whole limitation lifted.
- The feasibility analysis's finding #2 says the limitation "bites in practice". After this slice
  that is true only without a declared resample — correct it, and say what changed it.

## Task 7 — close the branch

- **Whole-branch re-run**, and the oracle from Task 1 re-checked. Not a formality: the branch under
  Tasks 2 and 3's mutations changed after those mutations were written.
- The consistency passes over the four documents; § Statistical reporting and § Pre-registration
  both describe when a corrected bound exists and may now be wrong.
- **Re-validate the fifteen** in `2026-08-28-gcl-measurement/`, and re-record the analysis's
  § Executability entry. E2's above-chance hypothesis is the live case: it declares
  `statistics.resample`, so it should now be answerable on a bound — **and if it is not, that is a
  finding about this slice, not about the config.**
