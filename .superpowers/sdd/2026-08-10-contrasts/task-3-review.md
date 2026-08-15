# Task 3 review: `paired_keys`

## Verdicts

- **Spec compliance:** ✅
- **Task quality:** approved

## Detail

**Signature and body** match the brief verbatim: `paired_keys(of, against, allowed) -> list[str]`,
intersection via `set(of) & set(against)`, narrowed by `allowed` only when not `None`, returned
`sorted(...)`. `src/publishable/stats.py:361-378`.

**Purity.** No new imports were added; the diff touches only `stats.py` and `tests/test_stats.py`.
No filesystem access, no runtime import of `config`/`artifacts`/`runner`/`cli`.

**Scope discipline.** The function returns keys only — no values, no differences, no arithmetic
beyond set operations. Correctly leaves the difference table to Task 4.

**Placement.** Landed directly after `collapse_repeats` (`stats.py:361`, `collapse_repeats` ends
at 359), which is its natural producer — `paired_keys` consumes exactly the
`dict[str, dict[str, float]]` shape `collapse_repeats` returns. Reasonable choice; not dropped
arbitrarily. It sits ahead of the unrelated `_is_anonymous_level`/`repeat_spread` block, so it
doesn't get lost among repeat-dispersion code either.

**Tests, one by one** (`tests/test_stats.py:481-527`):

- `test_the_pairing_is_the_intersection` — catches a union or single-side implementation
  directly (asserts `["u2", "u3"]` against a case where union, left-only, and right-only would
  all differ from that value).
- `test_the_union_and_either_side_alone_all_differ` — the discriminating test the brief calls
  out. It asserts equality to `["u2"]` *and* inequality to the union, to `sorted(of)`, and to
  `sorted(against)`, so all three plausible wrong implementations (union, left side, right side)
  are each pinned as distinguishable from the correct answer, not just asserted away from a
  single alternative. Does what the brief asked.
- `test_a_within_stratum_narrows_the_intersection` — catches a missing/ignored `allowed`
  parameter, or `allowed` applied as a union/replacement instead of a further intersection.
- `test_the_result_is_sorted` — uses out-of-order dict insertion (`u3` before `u1`) on both
  sides. Whether it reliably catches a dropped `sorted()` depends on Python's set iteration
  order for these two short strings, which is hash-seed dependent (`PYTHONHASHSEED`) rather than
  insertion-order dependent. A `list(keys)` (no sort) implementation could coincidentally pass
  under some hash seeds. That said: a `set` is never `==` to a `list` in Python regardless of
  order, so *any* implementation that forgets to convert to a list at all (leaves `keys` as a
  `set`) is caught deterministically by every test in the file that asserts `==` against a list
  literal — the class of bug most likely to result from a careless refactor. The narrower bug
  (converts to a list but skips the actual sort) has non-deterministic coverage from this test
  alone; this is inherited from the brief's own test, not something the implementer weakened.
- `test_an_empty_allowed_set_yields_no_pairing` (added beyond the brief) — asserts
  `paired_keys(of, against, set()) == []` **and**, in the same test,
  `paired_keys(of, against, None) == ["u1"]` on the identical `of`/`against`. That second
  assertion is what pins the `None`-vs-`set()` distinction rather than merely checking the
  empty-set behavior in isolation — a implementation that treated `allowed=None` as
  `allowed=set()` (or vice versa) would fail here, not just an implementation that mishandles
  empty sets generically. Meets the brief's ask.

**Import list.** `paired_keys` added alphabetically to the `from publishable.stats import (...)`
block in the test file, consistent with existing style.

## Minor

- None beyond the sort-test hash-order caveat above, which is inherited from the brief's own
  test rather than introduced by the implementer.
