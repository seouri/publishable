# Task 2 report

**Status:** done
**Commit:** d5a3a19

**Summary:** Added the "Resample methods" table to § Statistical reporting closing `statistics.resample.method` to the one-value enum `bootstrap`, and fixed the § The one config file `resample:` inline comment to the `# a | b | c` enum form — while overriding the brief's Step 3(b) instruction to delete `NOT BUILT;` (kept it, per the task instructions' explicit override, since `E-STATS-RESAMPLE-UNSUPPORTED` still fires on every declared `resample` until task 12).

## Concerns

1. **Deviated from the brief's exact prose, deliberately.** The brief's Step 3(a) text said `method: bootstap` "is refused (`E-STATS-RESAMPLE-METHOD`) rather than ignored" — a present-tense guarantee. Nothing reads `resample.method` yet and `E-STATS-RESAMPLE-METHOD` doesn't exist until task 4, so as written this would have been exactly the "comment claiming a guarantee the code does not provide" defect class CLAUDE.md flags with eight prior instances. I caught this via advisor review before committing and rewrote the sentence to state the closed-enum decision without asserting the diagnostic fires today: "so a misspelled `method` is a refusal the schema can name rather than a value silently ignored." No code identifier is named in the new paragraph. Task 4 should add the `E-STATS-RESAMPLE-METHOD` reference (with its `#errors-core-raises` link, matching sibling codes in the same section) once it's real.

2. **Sibling asymmetry, left alone.** The `null_test:` line directly below (`# NOT BUILT; e.g. {method: permutation, n: 5000, shuffle: label}`) uses a different comment shape (`e.g.` — an open example, not a closed enum) from the new `resample:` line (`# NOT BUILT; bootstrap` — a closed enum). This is expected: `null_test`'s method vocabulary isn't being closed by this task. Flagging so a reviewer doesn't read it as an inconsistency I missed.

3. **Task 12 has two things to do, not one.** Per the override, task 12 must (a) drop `NOT BUILT; ` from the `resample:` line leaving `# bootstrap`, and (b) revisit the new "Resample methods" paragraph to add the `E-STATS-RESAMPLE-METHOD` reference once task 4 has minted it and registered it in § Errors core raises.

## Verification

- `grep -n 'resample:.*# '` and `grep -n 'Resample methods' -A 6` both now return the new lines (Step 1/4 greps).
- Headings list before/after is byte-identical (no anchor added or moved).
- No trailing whitespace, no tabs, no en dash introduced in the diff; em dashes used per house style.
- Mutation test: changing `bootstrap` → `boostrap` in the table's first column made the table and inline comment visibly disagree; reverted and confirmed match.
- `uv run pytest` → 1691 passed, 2 xfailed (matches required baseline; `tests/test_materialize.py` unaffected since materialize writes no `resample` key).
- `uv run ruff check .` → all checks passed.
- `uv run mypy` → no issues found in 42 source files.

**File touched:** `docs/reference.md` (§ Statistical reporting, § The one config file). No code, no test file.
