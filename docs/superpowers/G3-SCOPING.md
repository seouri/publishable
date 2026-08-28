# G3 scoping — persisting a run's findings

**Measured on 2026-08-28 against commit `d8c268b`.** Every number here came from reading or running
the code, not from the [filing](spec-defects.md) that prompted it — and two of that filing's claims
did not survive the measurement.

## What the defect is

Core reports 37 distinct warning codes. None of them reaches `run.yaml`. The record keeps the
consequence — a null bound, an absent metric block, a `delta: null` beside two healthy side counts —
and drops the sentence explaining it. `design-principles.md` § Design goals opens by naming the
failure this project exists to prevent: a record "scattered across a shell history". A warning that
lives only in scrollback is that shape, reintroduced by core.

## Measured surface

| Fact | Measured |
|---|---|
| Distinct `W-` codes in core | **37** |
| `.warn()` call sites | 39, in 5 modules |
| `Collector()` constructions | ~55, across 9 modules |
| `.warn()` sites **in the run path** | **18** — 14 in `_execute_prepared`, 1 in `_prepare_run`, 3 in `_comparison_step_blocks` (which receives its collector) |
| `print(c.render())` sites **in the run path** | **12** — 7 in `_execute_prepared`, 5 in `_prepare_run` |
| Run-path collectors carrying `credentials` | 7 of 7 in `_execute_prepared`; 1 of 5 in `_prepare_run` |
| Run-path warnings interpolating a host path | **1** — `W-ENV-UNLOCKED` interpolates `repo_root` |
| Run-path **errors** interpolating a path | **1** — `E-INPUT-CHANGED`, and `verify_manifest` returns **relative** paths, so nothing host-identifying reaches it |
| `.error()` sites in the run path | 8 — so a record **can** be written beside errors (`status: partial`) |

**The run path is two functions.** That is the finding that makes this tractable: `_prepare_run` and
`_execute_prepared` between them hold every finding a run produces, and every one is already printed
through `Collector.render()` at one of 12 sites. This is not a 55-collector change.

## Two claims from the filing that did not survive

- **"`run.yaml` is compared field-by-field by `diff`."** False. `diff` reads five named rows
  (`ROW_LABELS`) and recurses only into `covered_config(...)` — the *config*, never the whole record.
  A new top-level key in `run.yaml` is invisible to `diff`. Verified by reading `diff._diff_values`
  and its single caller.
- **"Persisting findings would be a new way for a credential to reach a file."** Overstated. A step's
  error message is **already** redacted and written to `executions.jsonl` — `runner.py:859` calls
  `redact(...)` before the write. The precedent exists; what is needed is to follow it.

The third claim held: the bit-stability oracle pins the whole normalized `run.yaml`, so it moves
once. That is the oracle doing its job, not an obstacle.

## The credential question, bounded

Two facts bound it:

1. **`secrets.py` is the only module that reads `os.environ`.** Core obtains credential *values*
   through `credential_values()` alone, called once in `_prepare_run`. Findings rendered *before*
   that call cannot contain a value core has not yet read — the ordering is itself the guarantee, not
   an argument about diligence.
2. **Every collector rendered in `_execute_prepared` already carries `credentials`.** All 7. The 4 in
   `_prepare_run` that do not are all rendered before `credential_values()` runs.

## A record IS written beside an error, measured

`E-INPUT-CHANGED` (`cli.py` ~5200) sets `status = "failed"`, renders an **error** through a collector,
and execution continues to write `run.yaml`. So a persisted block cannot be called `warnings` without
either lying or dropping the most consequential disclosure a failing run makes. This was measured
because the first pass of this scoping only swept `.warn(` sites and would have missed it.

## The host-path question, and why it closes cleanly

Exactly one run-path warning interpolates a host path: `W-ENV-UNLOCKED` names `repo_root`.
`study.py::_redact` already treats `git.repo_root` as one of four host-identifying fields it removes
from a bundle member — so that value would travel inside a message while being redacted out of the
field beside it.

The remedy is to stop interpolating it, not to redact it: the reader of that message is standing in
the repository. `apparatus.py:188` is the precedent — "so this refuses rather than redacting it into
the record". After that one change, **no persisted message contains a host path at all**, which is a
stronger and cheaper invariant than a second redaction pass over prose.

## Two under-counts looked for and not found

`CLAUDE.md` says every re-scoped charter here was stale in the same direction — under-counted, missing
surface — so both candidates were measured rather than assumed:

- **`draft` and `resume` are not separate surface.** All three record-writing commands funnel through
  `_prepare_run` → `_execute_prepared` (`cli.py` 5415/5435/5582). `command_resume` renders twice on its
  own, and **both are error paths that `return EXIT_WRONG` before any record exists** — nothing to
  persist into, rather than surface overlooked.
- **No strict reader of `run.yaml` exists.** `reproduce`, `study` and `lineage` read named fields;
  none enumerates or rejects unknown keys. A new top-level block breaks no consumer.

## What is out of scope, and why

- **`validate`, `report`, `freeze`, `diff`, `study`, `docs`, `reproduce` findings.** They belong to
  commands that write no run record. `validate`'s findings are also re-derivable: the run directory
  holds the `config.yaml` that produced them.
- **Persisting to a side file** (`findings.jsonl` beside `executions.jsonl`). Considered and refused
  in the design; see Decision 1.
- **Changing any message other than `W-ENV-UNLOCKED`'s.**
