# SDD ledger — plan: docs/superpowers/plans/2026-08-16-plugin-registries.md

Spec: docs/superpowers/specs/2026-08-16-plugin-registries-design.md
Branch: h7b-registries, from main at ba87aae. Baseline: 1999 passed + 2 xfailed; ruff check, ruff
format --check (76 files, 0 to reformat) and mypy (43 source files) all clean.

Standing authorization: plan, execute, merge AND push without stopping, and report to the user ONCE
after the push. No halfway report. Recorded because it changes what I stop for — nothing but the four
things the skill names (an irreversible operation, a security-sensitive action, an outward-facing side
effect beyond the merge and push already authorized, or a plan too broken to proceed on).

Ledger writes are committed BEFORE the dispatch that follows them. An H7c implementer correctly refused
an uncommitted line in this file as a possible prompt injection, and it was right to: from inside a
task, an uncommitted authorization in the working tree is indistinguishable from an injected one.

## Pre-flight conflict scan

| File | Tasks | Finding |
|---|---|---|
| `docs/reference.md` | 1, 2, 3, 4, 5, 6, 16, 17, 20 | **Nine tasks, the usual insertion risk.** Tasks 1-6 are the documentation debt and run first, so the rows tasks 16, 17 and 20 touch are already in place. Each of 1-6 owns a distinct section. Carried as an instruction rather than a ruling: any task inserting a row re-reads every count phrase near it, which is how H7c task 2 kept two counts honest |
| `src/publishable/plugins.py` | 7, 12, 13, 14, 15, 16, 17 | **Clean and strictly sequential.** Task 7 creates it; 12-17 each add one registry or check on top. No two tasks write the same function. 7 before all of them, which the plan sequences |
| `src/publishable/templates/registry.py` | 8, 9, 11, 20 | **The one pair worth a ruling.** Task 9 rewrites `_merged` to take a third source and make provenance three-valued; task 20 extends the `PartialLoadError` payload `_merged` builds. Task 20 must be written against task 9 s `_merged`, not today s. Plan order is 8 -> 9 -> 11 -> 20, so 20 is last and sees 9 s shape. **Ruling: no change needed, but task 20 s brief must say the payload line it edits is task 9 s, not `main` s** — the plan report already records that `local.values()` is a proxy task 9 makes wrong |
| `tests/test_plugins.py` | 7, 16, 17 | Clean. Task 7 creates it with the installed-distribution fixture; 16 and 17 append |
| `src/publishable/validate.py` | 8, 11, 19 | Clean. 8 (collision reporting), 11 (`E-TEMPLATE-UNKNOWN` hint), 19 (envelope closure + mutual exclusion) touch three unrelated regions |
| `src/publishable/__init__.py` | 12, 13 | Clean. Both add exports; 12 then 13. **Decision 8 of the H7c spec does not apply here** — this slice DOES move the import root, and § The importable surface s three-name row is task 3 s and 4 s to split |
| `src/publishable/artifacts.py` | 14, 15 | Clean, and the pair is the point: 14 adds `register_writer`, 15 makes `WRITERS`/`READERS` symmetry an enforced invariant over it. 15 must follow 14 |

**No conflict required a ruling beyond the `registry.py` note above.** Recorded with its rows rather
than as a verdict, because "the scan is clean" without the rows is not a scan that was run.

Also checked, per task: each task s tests are specified against the code that task specifies, and no
task touches a file a later task creates. Task 3 precedes task 7 because decision 2 s fifth group must
be settled before the scan enumerates groups — a reordering against the scoping s numbering that the
plan already carries.
