# Task 1 report: `Comparison` and contrast resolution

Implemented exactly per the brief, verbatim.

## Files

- Created `src/publishable/contrasts.py`: `Comparison` frozen dataclass
  (`id`, `of`, `against`, `within`) and `resolve_contrasts(config, conditions)`.
  Pure — no filesystem, no runtime import of `config`/`artifacts`/`runner`/`cli`;
  `Condition` is imported only under `TYPE_CHECKING`.
- Created `tests/test_contrasts.py` with the five test cases from the brief,
  using the `Condition(index=i, label=label, values={}, is_baseline=baseline)`
  idiom confirmed in `tests/test_sweep.py`.

## Behavior

- No baseline and no `statistics.contrasts` → `[]` (no `vs_baseline` block is
  ever fabricated).
- Every non-baseline, labelled condition yields one `vs_baseline` comparison
  (`id` = the condition's own label, `of` = its index, `against` = the
  baseline's index), in condition order.
- Each `statistics.contrasts` entry then yields one more comparison, in the
  order declared, after all the `vs_baseline` ones — resolving `of`/`against`
  by label via a `by_label` map built from all labelled conditions.
- `by_label[entry["of"]]` / `by_label[entry["against"]]` raise `KeyError` on an
  unresolvable label. Documented in the code comment: this is acceptable only
  because validate (Task 6) refuses an unresolvable `of`/`against` at validate
  time, and `cli` always validates before running — `resolve_contrasts` itself
  does not guard it.

## Verification

```
uv run pytest -q          → 637 passed
uv run ruff check .       → All checks passed!
uv run mypy               → Success: no issues found in 35 source files
```

Full suite (not just the new file) passes; nothing pre-existing broke.

## Commit

`1d24fb43b99bc8fae214c4cd6168903ee74922f7` — "Resolve which comparisons a config asks for"
