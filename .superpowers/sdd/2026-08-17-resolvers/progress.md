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
