# Task 2 report — row 243, the collapse rule fits the column

**Status:** DONE — reviewed and approved; fix round 1 (below) closed the three follow-up items.

**Commits:**
- `41de16c` — "feat: check the collapse rule against the column it collapses" (`src/publishable/validate.py`, `tests/test_validate.py`, `docs/reference.md`)
- `e863830` — "fix: share the numeric predicate, and stop misrouting an omitted collapse" (`src/publishable/units.py`, `src/publishable/validate.py`, `tests/test_validate.py`, `docs/reference.md`)

**Tests:** `uv run pytest` — 1100 passed, 2 xfailed (final). `uv run ruff check .` and `uv run mypy` both clean. Seven mutations total (five in the original submission, two in the fix round) applied and each killed by a named test, then reverted with `__pycache__` deleted between mutate and revert, verified by re-running the killing test rather than by `git status`.

## What was built

`_check_measurements(units, roster, c)` in `validate.py`, called from `validate_config` right after `roster = _check_units(doc, c)`. It checks `data.units.measurements` in two halves:

1. **Shape** (`E-DATA-MEASUREMENTS-INVALID`): the block is present and not a mapping, or is empty; or its `by` is missing or not a non-empty string. Runs regardless of roster.
2. **Type** (`E-DATA-MEASUREMENTS-COLLAPSE-TYPE`): for each resolved attribute column (excluding `by`), the effective collapse rule (per-column map entry, its `first` fallback, or the flat scalar) is checked against the roster's actual values when the rule is `mean`/`median`/`sum`. Skipped when the roster does not resolve.

An unknown collapse rule name (any type, not the type check above) draws `E-UNITS-COLLAPSE-RULE` — **not** a third `E-DATA-MEASUREMENTS-*` code. `reference.md` § Errors `validate` reports already dual-lists `E-UNITS-COLLAPSE-RULE` for exactly this fault (the same code `units._apply` raises, which `validate` will also reach once task 3 wires `collapse_measurements` into `resolve_units`). Minting a second code for the same fault would recreate the "one problem, two codes" pattern `_check_units`'s own docstring calls out as the thing to avoid. This is a deliberate deviation from the brief's literal skeleton (which used `E-DATA-MEASUREMENTS-INVALID` for this branch) — flagged per "if anything in the brief is wrong, say so."

## Decisions the brief asked me to pin

**Numeric-looking CSV strings (the flagged risk area).** `resolve_units` builds attributes through `csv.DictReader`, so every table-sourced value is a `str` today — task 3 owns coercion, not this task. Decision: a `str` that parses as `float` counts as numeric for this check (`_measurement_value_is_numeric`); a `str` that doesn't (`"north"`) does not. This is what lets `collapse: mean` over an ordinary numeric CSV column (`"10"`, `"20"`) validate clean instead of every real config being forced onto `first`/`mode`, while still catching row 243's actual case. Pinned by `test_a_numeric_looking_csv_string_column_is_accepted_under_mean`.

**Consequence left open, not closed here:** `units._apply`'s `sum`/`median`/`mean` on these same uncoerced strings (`sum(["10","20"])`) raises a bare `TypeError` at run time — nothing coerces yet. Once task 3 wires `resolve_units` → `collapse_measurements`, that call site needs to coerce a numeric-looking string before dispatch, or a config this check now accepts crashes instead of computing. Recording this as a cross-task finding for task 3/6 rather than working around it here, since attribute typing is explicitly out of this task's scope.

**Constant string column.** `units._apply`'s constant-column shortcut would let `mean` over a *constant* `site` string survive at run time without dispatching. `_check_measurements` refuses it anyway — it does not special-case constant groups at all, so this falls out of the design rather than needing an explicit carve-out. Pinned by `test_a_constant_string_column_is_refused_despite_surviving_at_run_time`.

**Boolean under a numeric rule.** `bool` is excluded from "numeric" (`isinstance(value, bool)` checked before the `int`/`float` branch), matching `_apply`'s own gate exactly. Two tests: a direct-call test with a hand-built `UnitList`/`Unit` carrying a genuine `bool` (CSV cannot produce one), and a CSV-reachable variant with `"True"`/`"False"` strings under `sum` (refused because they don't parse as `float` — no bool-specific string handling needed).

**Empty `collapse: {}`.** Accepted: an empty per-column map names no column, so every column falls back to `first` — the same fallback `units._rule_for` already uses for an unlisted column, making `collapse: {}` a vacuous-but-coherent restatement of `collapse: first`, unlike `measurements: {}` itself (which names neither `by` nor `collapse` and is refused). Pinned by `test_an_empty_collapse_map_defaults_every_column_to_first_and_is_accepted`.

## Brief corrections

- **Call site.** The brief said "call it from `_check_data`'s existing roster-resolving path." `_check_data` never resolves a roster — only `_check_units` does. Wired the call into `validate_config` after `roster = _check_units(doc, c)` instead.
- **Crash guard the skeleton lacked.** The brief's `sorted({...} - {by})` is unhashable for a list/dict `by`. Added `valid_by = by if isinstance(by, str) and by else None` before the set difference, and a dedicated test (`test_a_non_string_by_is_reported_rather_than_crashing`) with a resolvable roster to exercise it.
- **Unknown-rule code**, covered above.
- Confirmed the three named-but-nonexistent fixtures were never used; `write_config`/`codes` (real, from `tests/test_validate.py`) plus `tmp_path`, hand-written `Unit`/`UnitList`, and a direct `Collector()` call covered every case, including the ones CSV cannot produce.
- The registry table was at 66 rows before this task (confirmed by direct count of lines 405–470), not 65 as the brief's own "Global Constraints" stated — matches the parent task's correction. Two new rows land it at 68 (also directly counted after the edit).

## Test coverage added (14 new tests in `tests/test_validate.py`)

Shape: missing block, empty block, missing `by`, malformed `by` (crash guard). Type: `mean` over a string column, a per-column map sparing it, a constant string column, real `bool` under `sum`, CSV `"True"`/`"False"` under `sum`, numeric-looking CSV string under `mean`. Edge shapes: unknown rule name → `E-UNITS-COLLAPSE-RULE` (and explicitly not `-INVALID`), empty `collapse: {}` accepted. Roster-skip: an unreadable `input_dir` still yields the shape finding and not the type finding (through `validate_config`), and a direct `_check_measurements(..., None, ...)` call confirms the same behaviourally, satisfying "the skip must be reachable in a test with the roster resolvable" together with the unreadable-`input_dir` case, which exercises it with the roster genuinely unresolvable.

Five mutations were run against distinct branches (the `NUMERIC_COLLAPSE_RULES` gate, the `bool` exclusion, the empty-mapping shape check, the unknown-rule-name check, the missing-`by` check) — each killed a specific named test, then was reverted and reverified by rerunning that test (not by `git status`), with `__pycache__` cleared each time.

## Concerns (why DONE_WITH_CONCERNS, not DONE) — as of the original submission

1. The CSV-numeric-string acceptance decision (above) is sound for *this* task but leaves a real run-time crash reachable once task 3 wires collapse execution, until task 3 also adds coercion. This is named above and should be checked against task 3's actual plan before that task is marked done.
2. `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`'s row in `reference.md` and this check both treat the effective per-column rule via the same fallback-to-`first` logic as `units._rule_for` — this duplicates that one piece of logic (not the full `COLLAPSE_RULES`/`NUMERIC_COLLAPSE_RULES` sets, which are imported per the brief) rather than importing `_rule_for` itself, since `_rule_for` is a private (underscore-prefixed) helper in `units.py` not exported for reuse. Worth a look at whether task 3 should export it too, for the same reason `COLLAPSE_RULES` was exported.

Both concerns were confirmed correct by review. Concern 2 (the `rule_for` duplication) was already fixed upstream of this fix round, in `cc6fb3f` — `validate.py` now imports and calls `units.rule_for` rather than re-deriving the per-column fallback.

## Fix round 1 — commit `e863830`

**IMPORTANT 1 — shared numeric predicate.** `is_measurement_numeric` moved out of `validate.py` (where it was private, `_measurement_value_is_numeric`) into `units.py` as a public function, beside `_apply`. `validate.py` now imports it instead of holding its own copy. Its docstring states it is the single authority both the check and a future run-time coercion step must read, and records the two reviewer-supplied facts verbatim as guidance for whoever adds that coercion:
- `_apply("mean", ["10", "10"])` returns the *string* `"10"` today, because `_apply`'s own constant-column shortcut gate is a narrower isinstance-only check that this predicate deliberately does not feed — coercion has to happen *before* `_apply` sees the values, not by widening `_apply`'s own gate to accept numeric-looking strings (I checked: doing that instead converts the silent-wrong-value bug into an unhandled bare `TypeError` inside the arithmetic branch, which is worse, not fixed — so `_apply`'s gate is deliberately left untouched here).
- Whatever coercion task 3 adds must accept exactly `float`'s grammar, or the predicate's "numeric-looking" and the coercion's "successfully converted" part ways again.

Mutation-tested by disabling the predicate's `bool` exclusion at its new home in `units.py`: `test_sum_over_a_real_boolean_column_is_refused` failed as expected, confirming the moved function is still the one under test (not a stale duplicate). Reverted, `__pycache__` cleared, reverified by rerunning the test rather than `git status`.

**IMPORTANT 2 — omitted `collapse` no longer misroutes.** `measurements: {by: read_id}` with `collapse` omitted now reports `E-DATA-MEASUREMENTS-INVALID` at `.collapse` ("is missing; `collapse` is required alongside `by`") instead of `E-UNITS-COLLAPSE-RULE`. New test `test_an_omitted_collapse_draws_invalid_not_the_named_rule_code`, mutation-tested by disabling the new `if collapse is None:` branch — the test failed with `E-UNITS-COLLAPSE-RULE` appearing instead, confirming the branch is what the test actually exercises. Reverted, `__pycache__` cleared, reverified by rerunning the test.

**MINOR 3 — row 411 wording.** Now reads "is declared (non-null) and is not a mapping, or is an empty mapping ... or its `collapse` is missing" — states the branch the code takes (skip on `None`) and the new omitted-`collapse` condition, rather than describing a state (`init`'s own `measurements: null` output) that the code doesn't actually refuse.

`reference.md` row 410 (`E-DATA-MEASUREMENTS-COLLAPSE-TYPE`) updated to name `units.is_measurement_numeric` explicitly and to stop claiming it is "the same gate `units._apply` uses" — it isn't, by design: it additionally accepts a numeric-looking string, which `_apply`'s own narrower gate does not.

Full suite after this round: `uv run pytest` — 1100 passed, 2 xfailed (351 → 352 in `test_validate.py`). `ruff check .` and `mypy` both clean.

## Ledger items (per the coordinator, deferred — not fixed, noted so they aren't rediscovered)

- `collapse: {typo_column: mean}` and `collapse: {7: "mean"}` validate clean and do nothing, in tension with the rationale used to refuse `measurements: {}` ("a declaration that changes no behavior is the failure this refusal exists to prevent").
- `float()`'s grammar accepts `"nan"`, `"inf"`, `"1_000"`, `" 10 "`, `"+5"`, and unicode digits — doc and code agree, so this is a slice decision, but `mean` over a `"nan"` column yields a silently meaningless number, which is the outcome row 243's own rationale objects to.
- The cascade on a malformed `by` (reporting `-INVALID` and then `-COLLAPSE-TYPE`) is noise, not misdirection, since the root cause reports first — left as is.
