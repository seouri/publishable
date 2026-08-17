# SDD ledger — plan: docs/superpowers/plans/2026-08-17-resolvers.md

Spec: docs/superpowers/specs/2026-08-17-resolvers-design.md
Branch: h7b-resolvers, from main at 470a830. Baseline: 2060 passed, 1 skipped, 2 xfailed; ruff check,
ruff format --check (78 files, 0 to reformat) and mypy (44 source files) all clean.

Standing authorization: re-scope, spec, plan, execute, merge AND push without stopping, reporting to the
user ONCE after the push. Committed before the first dispatch, because an implementer two slices ago
correctly refused an uncommitted authorization line in this file as a possible injection — from inside a
task that is indistinguishable from an injected one.

**This is the slice that makes an experiment run.** Three of the nine feasibility experiments have no
remaining core-side blocker when it lands — the first non-zero count this project has produced.

## Pre-flight conflict scan

| File | Tasks | Finding |
|---|---|---|
| `docs/reference.md` | 22, 27, 28, 29, 33 | Five tasks. Task 22 settles the no-import sentence FIRST, so 27-29 and 33 edit rows that already read correctly. Task 33 is the sweep and runs last. **Instruction, not a ruling:** any task inserting a row re-reads every count phrase near it — Part A shipped a Critical where a fix round added a clause its own task 8 falsified |
| `src/publishable/units.py` | 24, 25, 27, 29, 31 | **The busiest file and the one real ordering constraint.** 24 loads the object, 25 dispatches it, 27 and 29 build on the dispatch, 31 threads `index_names`. Plan order is 24 -> 25 -> {27, 29} -> 31, so each sees its predecessor. **Ruling: no change needed, but 27, 29 and 31 must RE-READ `resolve_units` rather than work from a copy** — task 25 changes its signature (a defaulted `cfg`), and a plan in the previous slice broke two pinned regressions by writing against a stale shape |
| `src/publishable/validate.py` | 24, 25, 26, 28, 32 | Clean on inspection but ordered: 24 and 25 add the resolver path, 28 and 32 add checks over it, **26 deletes the skip and must be last among them**. 26 last is what keeps `E-DATA-RESOLVER-UNSUPPORTED` alive so every earlier test asserts ALONGSIDE it — making 26 a one-line deletion rather than a rewrite |
| `src/publishable/plugins.py` | 22, 30 | Clean. 22 narrows two docstring claims; 30 retires the four dated *no production caller* notes once callers exist. 30 after 24, which creates the first caller |
| `tests/test_units.py` | 27, 29 | Clean. 27 and 29 append |
| `src/publishable/cli.py` | 30, 32 | **The pair that matters.** 30 populates `provenance.plugin_versions`; 32 sets `c.credentials` before the roster resolves and routes the resolver raise through a FRESH collector (spec correction 1 — `command_run` already renders `c` before phase 5, so appending would re-print every warning). Both touch `command_run`'s phase ordering. **Ruling: 30 before 32**, so 32 sees the provenance write it must not disturb, and 32 before 26 because the leak becomes reachable the moment a resolver runs |

**Two conflicts required a ruling and both are recorded above** — `units.py`'s re-read obligation and
`cli.py`'s 30-before-32-before-26 ordering. The rest are clean, and the rows are here because "the scan
is clean" without them is not a scan that was run.

Also checked per task: each task's tests are specified against the code that task specifies. The plan
states once, up front, that **tasks 25, 27, 28 and 29 cannot test through `validate_config` at their own
commits** — the resolver skip is only deleted at 26 — so each tests its own function directly and task
33 re-asserts end to end. That is a deferral by design, not a gap, and it is why 33 exists.

Task 21: dispatched as part of a 21-24 batch, and **the session was closed mid-dispatch.** On resume the
  work was in the tree uncommitted — `plugin_scaffold.py`, `tests/test_plugin_scaffold.py`, and edits to
  `cli.py`, `tests/test_cli.py` and `reference.md` — with the suite at 2066 passed (baseline 2060 + 6)
  and mypy clean, but **the gates unfinished**: one `I001` import-sort error and one unformatted file.
  Recovered rather than redone. The ledger is what made that safe: it named the baseline, so I could tell
  6 new tests from a partial state, and the brief's Step 5 mutation was written down, so the one thing an
  interrupted agent cannot leave behind — evidence the test discriminates — was reconstructible.
  Ruling: finished task 21 in place rather than discarding and re-dispatching. Grounds: the deliverable
  matches the brief, the mutation is prescribed and pre-checked, and I ran it myself — deleting
  `publishable.readers` from `_MODULES` and skipping it in the `GROUPS` loop FAILS
  `test_the_scaffold_declares_every_group_core_reads` and only it, then reverted clean at 5 passed. Cost
  if wrong: a task whose implementer wrote no report, which is why this entry is longer than usual.
  `.superpowers/sdd/.gitignore` was clobbered to a bare `*` by the interrupted run; restored.

## Review findings closed (tasks 22-24, `91bdd46..8dabf2c`)

Restored honest markings the review found stated one task early: `_resolver_for` (task 24) has no
production caller yet, so `check_registration`-at-`validate` and `E-PLUGIN-DECORATOR` do not fire
there today, and `E-RESOLVER-UNKNOWN`'s **"Not yet emitted"** clause is back. **Task 26 owes the
reversal** — once its dispatch wiring lands and the skip is deleted, flip these back to present
tense, the way Part A's tasks 6 and 18 did for `--plugin`. Task 26 also owes the positive
`validate`-level companion test named in `tests/test_validate.py`'s
`test_validate_imports_no_plugin_for_a_config_that_names_no_resolver` docstring: assert
`"retire_r26" in sys.modules` inside its existing `try`.
