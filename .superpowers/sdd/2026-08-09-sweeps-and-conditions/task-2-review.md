# Task 2 review: the label grammar

## Verdicts

- **Spec compliance:** ✅
- **Task quality:** approved

## What was checked

Read `docs/reference.md` § "How artifacts are organized" directly (not the brief's
paraphrase) for the grammar table (separator, axis order, key, value, index), then read
the diff (`1f63311` label grammar, `e2c9a21` the `__`-in-value refusal) against it line by
line. Ran `uv run ruff check`, `uv run mypy`, and `uv run pytest tests/test_sweep.py -q`
myself rather than trusting the report's numbers — all pass (18 tests in the file, no
lint/type errors).

### Key-uniqueness algorithm (`_keys_for`)

Traced by hand against the cases the review brief calls out:

- **Shared leaf** (`analysis.method` / `scoring.method`): both fall back to keeping a
  segment — matches spec's own example verbatim.
- **Unequal depth / proper suffix** (`method` vs `x.method`): `method`'s only candidate
  (depth 1) collides via the `p.endswith("." + candidate)` branch, so it falls back to its
  own full path (`"method"`, unchanged); `x.method` collides at depth 1 too, then resolves
  at depth 2 to `"x.method"`. Final keys `"method"` / `"x.method"` are distinct — correct,
  no de-dup bug.
- **Substring off a dotted boundary** (e.g. a path ending in `...xmethod` vs one ending in
  `...method`): the `"." + candidate` check requires a dot immediately before the
  candidate, so `xmethod` does not falsely collide with `method`. Verified by construction,
  not just by inspection.
- **Three-way chains** (`a.method` / `x.a.method` / `b.a.method`-style): every path's
  candidate search bottoms out at that path's own full dotted string, which is guaranteed
  globally unique because `grid`'s keys are themselves distinct dict keys — so even when
  the fallback branch fires, the result never collides with another axis's key. Confirmed
  this holds independent of how many segments overlap.
- **Order:** `_keys_for(list(grid))` and the join in `label_for` both walk `values.items()`
  / `grid` in insertion order; Python dicts preserve declaration order, and nothing sorts
  in between. `test_axes_appear_in_declaration_order_never_sorted` (`z.one` before `a.two`)
  is a real test of this, not a tautology — a `sorted()` regression would flip it.

### Value rendering

`render_value`: bool checked before float (bool is an `int`/could shadow float paths but
not float itself; order is irrelevant here since bool and float are disjoint anyway), float
via `repr()` — Python's `repr(float)` has been the shortest round-tripping form since 3.1,
matching "shortest round-trip form" in the spec table exactly, not just by convention.
Plain `str()` for everything else, so ints render as `5` not `5.0`. Matches the spec row.

### The second commit (settled decision, implementation reviewed)

`AXIS_SEPARATOR = "__"` is a single named constant referenced by both `label_for`'s join
and `check_swept_value`'s refusal, which is exactly the thing that must not drift apart —
verified there is no second `"__"` literal left anywhere in the file. `check_swept_value`
runs the existing pattern check first and only then checks for the separator substring, so
it's additive over the Task-1/2 pattern check rather than a replacement (the report's own
test `test_values_already_refused_by_the_pattern_are_still_refused` exercises this, and it
would fail if the ordering were reversed and the pattern check discarded).

Correctly **not** wired into `validate.py` — the brief's Task 4 owns that, and the report is
explicit that `_check_sweep` doesn't exist yet. Nothing in this task's scope needed an
`E-`/`W-` identifier, so the coverage bar (every identifier has a test producing it) isn't
implicated — `check_swept_value` returns a plain message string for a future caller to wrap.

The `spec-defects.md` entry ("The swept-value pattern and the label separator contradict
each other on `_`") accurately states the conflict, both candidate resolutions, and which
one this build implements. No trailing whitespace or other mechanical issues in the added
section.

### Scope check: per-cell baseline labels

`reference.md`'s example `00_cohort=derivation__baseline` (composite baseline label, one
per cell, when another axis is left free) is **not** handled — `label_for` returns the bare
string `"baseline"` unconditionally when `is_baseline`. This is correctly out of scope:
Task 1's `expand()` only implements the `baseline`/`grid` schema (confirmed by reading
`task-1-brief.md`), with no `groups`/multi-cell expansion mode yet in this sprint. Flagging
here only so a future task wiring up per-cell baselines remembers that `label_for`'s
baseline branch will need the free axis's `key=value` prefixed, not just replaced.

### Test quality

The six brief-mandated tests plus three added for the second commit are not
implementation-mirroring: each encodes a concrete labelling outcome taken from the spec's
own worked examples (shared-leaf disambiguation, three-segment minimal disambiguation,
declaration order, boolean/float rendering, and the round-trip pattern check), and each
would fail under a plausible regression — reverting to "last segment always" breaks the
shared-leaf and three-segment tests; sorting axes breaks the declaration-order test;
`str(True)` instead of `"true"` breaks the boolean test. The separator tests directly probe
the new refusal's boundary (`_` legal, `__` refused, pattern-violations still refused
underneath). No table-driven test here just restates `_keys_for`'s internals back at it.

## Findings

None — no Critical or Important findings.

### Minor

- `src/publishable/sweep.py:114` — `label_for`'s fallback
  `keys.get(path, path.rsplit('.', 1)[-1])` is dead code under the current `expand()`
  callers (every non-baseline `values` key is a `grid` key, so `_keys_for` always has an
  entry), acknowledged as defensive in the report. Harmless, but a `mypy`/coverage
  purist would flag it as an unreachable branch if branch coverage were ever enforced.
