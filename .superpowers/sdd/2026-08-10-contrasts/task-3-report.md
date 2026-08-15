# Task 3 report: `paired_keys`

## What was done

Added `paired_keys(of, against, allowed) -> list[str]` to `src/publishable/stats.py`,
placed immediately after `collapse_repeats` (its natural caller/producer pairing).
Implementation matches the brief verbatim:

```python
def paired_keys(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    allowed: set[str] | None,
) -> list[str]:
    keys = set(of) & set(against)
    if allowed is not None:
        keys &= allowed
    return sorted(keys)
```

Added the four brief test cases verbatim to `tests/test_stats.py`, plus one extra
(`test_an_empty_allowed_set_yields_no_pairing`) covering the `None` vs. `set()`
distinction called out in the assignment, since the brief's own cases only exercise
`None` and a non-empty `allowed`. Added `paired_keys` to the `from publishable.stats
import (...)` block, alphabetically ordered.

## Verification

- `uv run pytest -q` → 647 passed (642 pre-existing + 5 new).
- `uv run ruff check .` → All checks passed.
- `uv run mypy` → Success: no issues found in 35 source files.

## Empty `allowed` vs. `None`

Distinguishable. `allowed=None` skips the `&= allowed` narrowing entirely (unrestricted);
`allowed=set()` intersects with the empty set, which zeroes out the result regardless of
what `of`/`against` share. Verified explicitly by the added
`test_an_empty_allowed_set_yields_no_pairing`.

## Commit

`c15f3c1` — "Pair two conditions over the units both completed" on branch `s4b-contrasts`.
