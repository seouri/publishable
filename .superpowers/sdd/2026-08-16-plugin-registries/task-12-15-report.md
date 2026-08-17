# Tasks 12–15: plugin registries — report

**Status:** All four tasks complete, committed, and verified. Full suite is green.

## Commits

| Task | SHA | Message |
|---|---|---|
| 12 | `433a29f` | `feat: register_resolver, exported — and the registry-restoring fixture the next three tasks use` |
| 13 | `98eb381` | `feat: register_probe, and the Probe-is-installed check that reads apparatus_probe` |
| 14 | `0ad8327` | `feat: register_writer feeds io.write's own table, and refuses a suffix core writes` |
| 15 | `e3a1d96` | `feat: register_reader, and a suffix with no reader is a coded refusal rather than a KeyError` |

## Test summary

Baseline before this slice: 2021 passed, 2 xfailed. After each task: 2023 (+2), 2027 (+4), 2030 (+3),
2034 (+4) — matching every brief's predicted delta. Final: **2034 passed, 2 xfailed.**
`ruff check`, `ruff format --check`, and `mypy` are clean throughout.

All 13 prescribed mutations were run (2 for task 12, 3 for task 13, 3 for task 14, 3 for task 15 —
task 14 lists 3 lettered mutations and task 15 lists 3, task 13 lists 3, task 12 lists 2 = 11 total,
plus the extra discriminating assertion task 14(b) required before its mutation could be trusted).
Each was checked against the body of the test it targets before being trusted, reverted by editing
the file back (never `git checkout --`), and confirmed green afterward with `__pycache__` cleared.
One mutation (task 14b) was **blind as first written** — the brief names this explicitly — and was
made discriminating by adding the second-registration assertion the brief prescribes, run only after
that addition.

One deviation from a brief's stated outcome, not a defect: task 12 mutation (a) (`return None`) was
expected by the brief to fail on the `resolve(None, None) == [...]` line with `TypeError`. It
actually fails one line earlier, on `RESOLVERS["plate_wells"] is resolve`, because decorating with
`@register_resolver(...)` rebinds the name `resolve` itself to the decorator's return value — so
`resolve` in the test's local scope is already `None` before the second assertion runs. The mutation
still fails, and for the reason the brief's docstring gives ("a `None` return leaves the plugin's own
module holding `None` under the name it just defined"); only the specific assertion line differs.

## Task 13 — reader for what it exports

**Confirmed.** `register_probe` and `validate._check_probe` land in the same commit (`98eb381`).
`_check_probe` reads `BaseTemplate.apparatus_probe` — the first reader that attribute has ever had —
against the `publishable.probes` entry-point metadata scan, and emits `E-PROBE-UNKNOWN` when no
installed distribution registers the declared name. It does **not** read `plugins.PROBES` (the
decorator's own mapping): that mapping is populated only once a plugin module is imported, which
would defeat the whole point of answering from metadata. This narrower claim — a reader for the
*name*, not for the *registered object* — is stated in the brief's step 9 and preserved in the
docstrings and the spec-defects amendment.

## Task 15 — where the refusal fires

**At the read, not at registration.** `StepIO._read` (`src/publishable/artifacts.py`) raises
`ArtifactError` · `E-ARTIFACT-UNREADABLE` when `_suffix_for` resolves a suffix that `WRITERS` holds
and `READERS.get(suffix)` returns `None`. `register_writer` does **not** check for a missing reader
at registration time — it cannot, since a plugin may register the reader later in the same module —
and `register_reader`'s own registration-time refusal (a suffix `CORE_SUFFIXES` holds) raises
`ContractError` · `E-PLUGIN-COLLISION`, the same mechanism and code as `register_writer`'s
core-suffix refusal from task 14, but answering a different question (is this suffix core's, not is
this suffix paired). The two mechanisms — read-time symmetry enforcement vs. registration-time
core-suffix shadow — are kept distinct in code, docstrings, and `reference.md`.

## Places a brief or the spec disagreed with the code

1. **Task 12, mutation (a):** as noted above, the brief predicted a `TypeError` on the second
   assertion; the actual failure is an `AssertionError` on the first, one line earlier, because
   `@register_resolver(...)` rebinds `resolve` to `None` before either assertion runs. The mutation
   still discriminates and fails for the stated reason — this is a discrepancy in *which line* fails,
   not in whether the mutation is caught.

2. **Task 15's own brief and the `spec-defects.md` entry it names disagreed with what task 15 was
   told to build.** The brief instructs: "Read the `## STRUCK 2026-08-16 — publishable.readers had no
   entry-point group` entry task 3 wrote and confirm every claim in it is now true... If any is not,
   fix the code rather than the entry." Two things did not match:
   - The entry's actual heading, as written by task 3, was `## OPEN — ...`, not `## STRUCK ...` — no
     `STRUCK` heading convention exists anywhere else in `spec-defects.md` (only `CLOSED`/`CLOSED
     HERE`). I renamed the heading to `## CLOSED 2026-08-17 — ...`, following the file's own existing
     convention, rather than inventing a `STRUCK` heading style that appears nowhere else.
   - The entry's own "Closed by specification" paragraph claimed `register_writer` would refuse "a
     suffix that has no reader" — i.e., that the invariant would be enforced at *registration*. This
     is exactly the corrected reading the coordinator's brief for task 15 calls out ("An earlier
     document sentence said otherwise and was corrected in this slice's tasks 1–6 review"): the
     invariant is enforced at the *read*, never at registration, and deliberately so (task 15's own
     step 8: "nothing closes it and nothing should" — registering the pair is the plugin author's
     obligation). I did not "fix the code" to match that stale claim; I corrected the entry's prose to
     say what task 15 actually built, per the coordinator's explicit correction.

3. Several `reference.md` passages the briefs describe as needing edits were already correct at the
   time each task reached them — e.g., task 13's fenced import example at line 928
   (`from publishable import BaseStep, Estimate, Unit, register_resolver`), task 14's
   `E-PLUGIN-COLLISION` § Errors row (already named the core-suffix case), and task 13's CLAUDE.md
   misreading row (already names `field_convention`, not `apparatus_probe`, as its worked example).
   Each brief anticipated this ("confirm no change is needed" / "leave it and say so in the report")
   and no edit was made in those spots.

## Files touched

- `src/publishable/plugins.py` — `RESOLVERS`, `PROBES`, `register_resolver`, `register_probe`,
  `register_writer`, `register_reader`.
- `src/publishable/artifacts.py` — `CORE_SUFFIXES`, `StepIO._read` rewritten for the coded refusal.
- `src/publishable/__init__.py` — four new exports, alphabetized into `__all__`.
- `src/publishable/validate.py` — `_check_probe`, wired in after `_check_requires_env`.
- `src/publishable/generators/template.py` — corrected comment now that `apparatus_probe` has a
  reader.
- `docs/reference.md` — Status cells for all four decorators moved to `built`; the
  `E-ARTIFACT-UNREADABLE` § Errors row.
- `docs/superpowers/spec-defects.md` — amended the `field_convention` entry; closed the
  `publishable.readers` entry with a corrected claim.
- `tests/conftest.py` — the `registries` fixture (task 12).
- `tests/test_plugins.py`, `tests/test_validate.py`, `tests/test_artifacts.py` — new tests per brief,
  each run to failure before implementation and to green after.
