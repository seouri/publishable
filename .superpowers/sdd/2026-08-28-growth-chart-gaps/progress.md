# SDD ledger — plan: docs/superpowers/plans/2026-08-28-growth-chart-gaps.md

Spec: docs/superpowers/specs/2026-08-28-growth-chart-gaps-design.md (read; binding authority)
Scoping: docs/superpowers/G1-SCOPING.md (measured against 84e6802, 2026-08-28)
Branch: **main**, by explicit instruction.

Ruling: work proceeds directly on `main` with commit+push per task — the human partner
instructed "directly commit/review/fix/push on main until all of them are fully executed",
which is the explicit consent the skill's Setup requires. Costs if wrong: no isolation, so a
bad task is reverted on a public branch rather than abandoned on a private one.

Ruling: `scripts/sdd-workspace` clobbered `.superpowers/sdd/.gitignore` to a bare `*` on its
first run, as CLAUDE.md warns. Restored from a copy taken beforehand; every record committed
this session uses `git add -f`. Costs if wrong: newly created records silently untracked.

## Pre-flight scan

### Pair rows — every pair sharing a file or an interface

| Pair | Produces → consumes | Found |
|---|---|---|
| T2, T3, T4, T6, T9, T10 | all edit `docs/reference.md` | **No section collision**: § Repeat kinds, § The one config file, § Errors + § Templates, § Warnings, § Pre-registration + § What a hypothesis is tested against, § Studies. Sequential execution keeps them from racing |
| T4 → T5 | T4 mints `E-TEMPLATE-PARAM-PATH` and its row; T5 pins both arms | Consistent. T5 cannot run before T4 |
| T6 → T7 → T8 | T6 mints `W-SWEEP-CONDITION-DUPLICATE`; T7 writes its message; T8 pins | T7 has no independent test surface and no independent commit value. **Batched with T6** — see ruling |
| T6, T9 | both edit `src/publishable/validate.py` | Different checks, different functions. Sequential execution avoids the conflict |
| T4, T9 | both may touch a `reference.md` error/warning table | T4 adds an `E-` row, T9 amends `compare`'s row. Different tables |
| T1 → T11 | T1 rewrites analysis gap 4; T11 re-records § Executability in the same file | Consistent; T11 runs last |
| T10 → T11 | T10 writes the § Studies paragraph; T11 amends the matching `spec-defects.md` entry | Consistent |

### Self-consistency rows — one per task

| Task | Its own text agrees with itself? |
|---|---|
| T1 | Yes |
| T2 | Yes |
| T3 | Yes |
| T4 | **No — ruled below.** "raised as a `ContractError` where the `ValueError` is today" and "at template load rather than at `generate experiment`" name two different sites |
| T5 | Yes |
| T6 | Yes |
| T7 | Yes — but see the T6/T7 batching ruling |
| T8 | Yes |
| T9 | Yes (delegates the code choice to implementation, with a record requirement) |
| T10 | Yes |
| T11 | **No — ruled below.** "strike the three G1 entries that closed" contradicts the same sentence's "amend rather than strike the correction-family one" |

## Rulings from the pre-flight scan

Ruling: **T4's check goes at template load, not in `materialize._parameters_block`.** The design's
two clauses conflict; the load site wins because `reference.md` § Templates already puts a malformed
`Param` declaration there — "a `Param` declaring `default=None` without `nullable=True` is rejected
when the template loads, rather than at the first config that leaves it alone" — and a spec whose
paths are malformed is malformed for `list-templates` and `validate` too, not only for the one
command that materializes it. `_parameters_block`'s own `ValueError` stays as an unreachable guard.
Costs if wrong: the refusal fires earlier than a reader expects, and a template that is never loaded
is never checked.

Ruling: **T6 and T7 are one dispatch.** T7 is the message text of the check T6 builds; splitting
them would produce a commit whose diagnostic is deliberately wrong. Batched per the skill's
same-shape rule. Costs if wrong: one larger review surface instead of two small ones.

Ruling: **T11 strikes TWO spec-defects entries and amends ONE.** Gap 1 closes by code (T4/T5) and
gap 3 by code (T6–T8), so both are struck; gap 2 closes as a documented limitation (T10), so it is
amended with the closure named as a paragraph rather than as a mechanism. The plan's "three ... that
closed" is its own arithmetic error. Costs if wrong: a reader looks for code behind gap 2's closure.

Ruling: **T2 and T3 are one dispatch.** Both are single-sentence edits to `reference.md` by the same
rule, in different sections, with no test surface. Same-shape batching. Costs if wrong: one review
surface instead of two.

## Progress
Task 1: complete (commits 79e3a9b..25d4fb6, review clean)
Task 2+3: complete (commits 25d4fb6..85bdfcf, review clean)

Ruling: `.superpowers/sdd/<plan>/` reports and `progress.md` are TRACKED here — the workspace's own
`.gitignore` says so and ignores only briefs and `.diff`s — but Task 1's implementer left its report
untracked and the ledger was untracked too. Both are committed now with `git add -f`, and every later
dispatch says to commit its own report. Costs if wrong: a record CLAUDE.md calls part of the
development record exists only on this machine.
