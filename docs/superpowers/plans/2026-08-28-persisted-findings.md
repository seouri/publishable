# G3 plan — persisting a run's findings

**Design:** [`specs/2026-08-28-persisted-findings-design.md`](../specs/2026-08-28-persisted-findings-design.md).
**Scoping:** [`G3-SCOPING.md`](../G3-SCOPING.md).

## Global constraints

- Every number already in `run.yaml` is unchanged. This slice adds one optional block and alters one
  message; it changes no verdict, no interval, and no exit code.
- `absent, not null`: no `findings:` key on a clean run.
- Every new test is proven able to fail by mutating **real code**, with the revert verified by
  behaviour rather than by `git status`.
- The suite, `ruff check`, `ruff format --check` and `mypy` are clean at every commit.

## Task 1 — `W-ENV-UNLOCKED` stops naming the repository path

**First, and alone, because it is the safety precondition.** Until it lands, any commit that
persisted findings would write a host path into the record.

`cli.py` ~3119: `f"no uv.lock found at {repo_root}; ..."` becomes a message that names no path. Then
the invariant becomes testable: **no run-path warning message interpolates a host path.**

Tests: the message no longer contains the repo path (mutation: restore the interpolation, watch it
fail); and a source-level sweep over `_prepare_run`/`_execute_prepared` asserting no `.warn(` **or
`.error(`** message interpolates `repo_root`, `input_dir`, `output_dir` or a `Path`. The sweep covers
both because the first scoping pass swept only `.warn(` and missed `E-INPUT-CHANGED` — which turns out
to carry *relative* paths and is fine, but was found by looking rather than by luck.

## Task 2 — `_disclose`, and the list every run-path finding lands in

A module-level helper in `cli.py`:

```python
def _disclose(c: Collector, into: list[dict[str, str]]) -> None:
    """Print a collector exactly as before, and keep what it said."""
```

It prints `c.render()` and appends `{level, code, path, message}` per finding, the message through
`redact(f.message, c.credentials)` — the same call `render` makes.

`Collector.disclosed()` lands in `diagnostics.py` beside `render`, applying the same `redact` call —
one implementation, read by both surfaces. `Prepared` gains a `findings` field; `_prepare_run` fills
it and `_execute_prepared` extends it, so nothing new is threaded.

Replace all **12** `print(<collector>.render())` sites in `_prepare_run` and `_execute_prepared`.

**The pin is source-level**, because a missed site is invisible to every assertion about the record:
a test asserting neither function contains `print(` applied to a `.render()`. Mutation: revert one
site to a bare print and watch it fail.

**One comment this task falsifies.** `cli.py` ~5190 says the aggregate findings are "printed to
stdout only: `run.yaml` has no diagnostics channel to carry a finding that isn't a metric, an
interval, or a status." That is an accurate description of the defect and becomes false here. Rewrite
it rather than leaving a comment that argues against the code beneath it.

## Task 3 — `run_record` assembles the block

`run_record.assemble(...)` gains a `findings` parameter and emits `findings:` **only when non-empty**.
`run_record` "assembles only — computes nothing", so the list arrives ready; the redaction and the
ordering are Task 2's.

Tests: a run with warnings carries them in order with all four fields; a clean run has no `findings`
key at all (mutation: emit `[]` unconditionally, watch it fail); the entries survive a YAML round trip.

## Task 4 — `report` renders the findings

`report` builds rows behind a `kind` discriminator; add `{"kind": "finding", ...}` and its render arm.
Without it the record carries the disclosure for a reader who never opens `run.yaml` by hand, which is
two of the three readers the defect names.

Tests: a record with findings renders them; a record without the key renders as before (mutation:
drop the render arm, watch the first fail).

## Task 5 — the bit-stability oracle moves once

`test_task1_bit_stability_oracle_over_the_correction_machinery` pins the whole normalized `run.yaml`.
**Whether its fixture emits any finding is not yet measured** — determine it first. If it does, the
literal gains a `findings:` block; if it does not, this task is a no-op and says so. Either way:
**read the diff; do not regenerate the literal.** The task's report must state which keys moved and why each was expected.

## Task 6 — the documents

- `reference.md`: the `findings:` block in the `run.yaml` shape, its rendering by `report`, and a
  sentence in § Exit codes and diagnostics saying which commands persist findings and which do not.
- `spec-defects.md`: the OPEN entry filed today is **closed by code** and therefore **removed**, per
  that file's own rule; the preamble's count moves with it.
- `docs/feasibility-growth-chart-literacy.md`: gap 10's closing sentence said the general form was
  filed rather than closed. It is closed now.

## Task 7 — close the branch

Full gate; both consistency passes over the four documents; re-run E1, E2 and E6 in
`2026-08-28-gcl-measurement` and confirm each record now carries the findings its run printed;
re-measure § Executability.
