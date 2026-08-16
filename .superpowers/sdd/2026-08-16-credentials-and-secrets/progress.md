# SDD ledger — plan: docs/superpowers/plans/2026-08-16-credentials-and-secrets.md

Spec: docs/superpowers/specs/2026-08-16-credentials-and-secrets-design.md
Branch: h7c-credentials, from main at d86290c. Baseline: 1957 passed + 2 xfailed; ruff check, ruff
format --check (74 already formatted, 0 to reformat) and mypy all clean.

Standing authorization from the user, recorded because it changes what I stop for: subagent-driven
execution, and **merge without stopping to ask**. After merging, update CLAUDE.md,
docs/superpowers/spec-defects.md and docs/feasibility-llm-growth-studies.md. Push is NOT covered by
that authorization and is asked once at the end.

## Pre-flight conflict scan

Run before task 1, against the plan as committed at 878a862. Rows are pairs sharing a file or an
interface, plus one row per task for self-consistency.

| Tasks | Shared | What I checked | Finding |
|---|---|---|---|
| 1, 2, 5, 6, 12 | `docs/reference.md` | Whether an insertion by one moves a row or a count phrase another depends on | **Clean, and non-obviously so.** Task 2 owns two count phrases ("Five faults", "two today") and its Step 1 RE-READS and re-counts both rather than trusting them. Its ruling that both stay unchanged is correct: this slice's new codes are `validate` reports, not early-return load faults, so the enumeration task 1 adds to is a different one |
| 8, 9, 10 | `src/publishable/validate.py` | Whether two tasks write the same emit site or reorder findings | Clean. 9 produces `_check_required_env`, 10 produces `_check_requires_env` — separate functions, separate call sites. 8 adds a load site and touches neither |
| 8, 11 | `tests/test_validate.py` | Helper collisions | Clean, verified by name rather than by reading: all six helpers the plan defines (`_check_required_env`, `_check_requires_env`, `_files_under`, `_findings_of`, `_joined`, `_union_project`) return zero hits in `src/` and `tests/`, with a control (`messages_by_code`) that does fire. This is the trap that authored a name collision in the previous slice's plan |
| 3, 4 | `src/publishable/param.py` | Ordering | Clean. 3 adds the keyword-only argument, 4 renders it. `requires_env` is keyword-only so no positional contract moves |
| each task | itself | Tests specified against code specified; files created before touched | Clean. `Condition(index, label, values, is_baseline, selectors)` confirmed at `sweep.py:44-49` exactly as task 10 and 11 state it |

**No conflict required a ruling.** Recorded rather than omitted, because "the scan is clean" without
the rows is not a scan that was run.

## Rulings made before execution

Ruling: the plan's finding 2 was wrong and I measured it before dispatching. It reported ONE
exception-text construction site from `grep -rn "\.error\b"` — a grep that finds assignments to an
attribute, not constructions. `grep -rn 'type(exc).__name__' src/publishable/*.py` returns FIVE. Three
are `W-STATS-AGGREGATE-FAILED` warnings that never reach `run.yaml` (`run_record.py` mentions
diagnostics zero times, checked) but ARE in scope, because task 12's leak sweep covers stdout and
stderr. Redaction moved from a construction site to the two SERIALIZATION BOUNDARIES, so a sixth
construction cannot diverge from the policy. Cost if wrong: one more edit site than strictly needed
today.
Ruling: my own correction named the boundary `Diagnostic.render()`. It is `Collector.render()` —
`Diagnostic` is a frozen four-field dataclass with no methods. I misjoined a class list and a method
line read from the same file in two separate greps. The plan author read `diagnostics.py` and caught
it, and the ruling is strengthened by the correction: redacting per-`Diagnostic` would need the values
at construction, which is what the ruling exists to avoid. Both the spec and the plan carry the
correction rather than a silent fix.
