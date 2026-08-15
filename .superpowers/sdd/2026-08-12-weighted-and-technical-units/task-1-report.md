# Task 1 report: the collapse function

**Status: DONE**

**Commits:**
- `193957b` — "feat: collapse rows sharing a key into one unit"
- `a8f59c9` — "fix: add median and sum to COLLAPSE_RULES, pin mode's tie-break" (fix round 1)
- `d1d2026` — "fix: gate the constant-collapse shortcut against corrupting sum" (fix round 2)

**Tests:** `uv run pytest` → 1085 passed, 2 xfailed. `uv run ruff check .` clean. `uv run mypy` clean (40 source files). `partition_units` untouched across all three commits (verified by diff each time).

## Fix round 2

**CRITICAL — the constant-column shortcut silently corrupted `sum`.** The round-1 shortcut (`if all(v == values[0] for v in values): return values[0]`) fired unconditionally, so `_apply("sum", [5, 5])` returned `5` instead of `10` — correct for `mean`/`median`/`first`/`mode` (all idempotent on constant input) but silently wrong, and data-dependent, for `sum`. Fixed exactly as specified: gated the shortcut to exclude the case where the rule is numeric (`in NUMERIC_COLLAPSE_RULES`) **and** the values are genuinely numeric (`isinstance(v, (int, float))`, `bool` excluded explicitly since `isinstance(True, int)` is `True`). The reasoning is now in the code comment: the shortcut's job is narrower than "all values equal" — it exists to let a *non-numeric* rule survive constant values it has no operation for, not to short-circuit a numeric aggregation.

Tests added: `test_the_constant_shortcut_does_not_corrupt_a_numeric_aggregation` — `sum([5,5])==10`, `sum([1000,1000])==2000`, `mean([5,5])==5`, `mean(["A","A"])=="A"` (round-1 behaviour, confirmed it survives). These call `_apply` directly (imported alongside the other private-function precedent already in the test suite: `test_cli.py` imports `_apply_execution_order`, `test_validate.py` imports `_check_contrasts`).

Mutation-tested by removing the `not (...)` gate (reverting to the round-1 unconditional shortcut): `test_the_constant_shortcut_does_not_corrupt_a_numeric_aggregation` failed (`5 != 10`), confirming the gate is load-bearing. Reverted, `__pycache__` deleted, confirmed passing by behaviour.

Recorded in `docs/superpowers/spec-defects.md` (new entry: "The constant-collapse rule and `sum`'s numeric membership are each stated; their interaction isn't") — the document states both the constant-collapse rule and `sum`'s membership in the numeric group, but never states how they interact, which is exactly why the naive reading was reachable. Note: `docs/superpowers/` is gitignored in this repo (confirmed via `git check-ignore -v`), so this entry is saved to disk but does not appear in the git diff/commit — consistent with how the rest of that directory is handled.

**IMPORTANT — `E-UNITS-COLLAPSE-RULE` needed a validate-time row too.** Added a row to `docs/reference.md` § "Errors `validate` reports" (not instead of, alongside the raise-time row added in round 1), positioned alphabetically among the other `E-UNITS-*` rows, citing the `E-REPL-SEED-COLLISION` dual-listing as precedent for a code that's raised inside code `validate` also calls (`resolve_units`, once task 3 wires the collapse in).

**MINOR — the ordering claim ("rule-name check before constant shortcut") was asserted in a comment but untested.** Added `test_a_bogus_rule_raises_even_over_a_single_trivially_constant_value`: `_apply("bogus", ["A"])` must raise `E-UNITS-COLLAPSE-RULE` even though `["A"]` is trivially constant. Mutation-tested by moving the shortcut above the rule-name check: the test failed (`DID NOT RAISE ContractError` — the bogus rule silently returned `"A"` instead). Reverted to the original order, `__pycache__` deleted, confirmed passing by behaviour.

## Hand-off to task 3 (not fixed here, per instruction — recording only)

**`resolve_units` builds attributes through `csv.DictReader`, so a table-sourced numeric column arrives as `str`, not `int`/`float`.** Once task 3 wires `collapse_measurements` into `resolve_units`, a `collapse: sum` (or `mean`/`median`) declared over a table-sourced column will call `sum(["10", "20"])`, which raises a bare `TypeError` — not a `ContractError`. Since `validate` only catches `ContractError` (`except ContractError as exc: c.error(...)`), this `TypeError` **propagates out of `validate`**, violating the hard invariant that `validate` collects findings and never raises.

This module's own `Unit`-constructing tests (`Unit(..., attributes={"depth": 10, ...})`) build attributes with native Python types directly, so they cannot reach this path — it only appears once real CSV-sourced rows flow through `resolve_units` into `collapse_measurements`. Task 3's brief should account for this: either coerce numeric-rule columns before collapsing, or catch/wrap the arithmetic `TypeError` as a `ContractError` with a stable code before it can escape `validate`.

## Concerns carried from earlier rounds (resolved, kept for the record)

1. The original brief's Step 3 code crashed on its own Step 1 test (`mean` applied blanket-wise over the non-numeric constant `site` column). Fixed in `193957b` per the doc's "constant needs no rule" sentence, inside `_apply` so task 5's direct callers get the same behaviour.
2. The brief's Step 5 mutation #1 (`first` branch) was unkillable via the verbatim Step 1 test because `site`'s two values are identical there. Added `test_a_column_absent_from_the_collapse_map_falls_back_to_first` to exercise that branch on genuinely differing values instead of editing the verbatim test.
3. Step 5 mutation #2 (recomputing `counts` in a separate walk) does not change behaviour today — reported honestly, not manufactured, per the brief's own instruction.

## What was not touched

`partition_units` and `_seed_from` are untouched across all three commits — verified via `git diff` on `src/publishable/units.py` after each, which shows only additive/localized hunks between `resolve_units` and `partition_units`.
