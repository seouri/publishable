# Task 5 report — `ratio` validation, and the live `by_attribute` gap closed

## What shipped

Two new codes in `src/publishable/validate.py`'s `_check_assign`:

- **`E-DATA-ASSIGN-RATIO`** — *Ratio names levels*. Checked beside
  `E-DATA-ASSIGN-DRAWN` in the `random`/`blocked` branch (not instead of it): a
  non-empty `ratio` whose keys are not exactly the axis's declared
  `sweep.groups` levels — a partial mapping or a key naming no declared level —
  is refused. An empty `ratio`, or one whose keys already equal the level set,
  earns nothing. This row was dead in every prior build (the `elif` chain
  stopped at `E-DATA-ASSIGN-DRAWN` before anything else ran); it is still
  reachable only in the sense that the check now executes and can produce a
  second finding beside the temporary refusal — real execution of a drawn
  method is still unbuilt.
- **`E-DATA-ASSIGN-NO-DRAW`** — closes the live gap: under `method:
  by_attribute`, a non-empty `ratio` or a non-empty `stratify_by` is refused
  outright, one finding per offending field, since § Allocation calls the two
  "the same fault" (a field describing a draw that never happened). An empty
  `ratio: {}` / `stratify_by: []` — what `init` writes — is accepted. This is
  the one that was reachable *today*: `by_attribute` is the only method that
  executes, and nothing read `ratio` anywhere in `src/` before this change.

Extracted `_declared_levels(sweep, axis)` as a shared helper — the existing
`by_attribute`/`arms_of` branch and the new `random`/`blocked` ratio check both
need an axis's declared `sweep.groups` levels, read the same way (entry by
entry, since `levels` isn't a `by`-path `selector_paths` collects).

`docs/reference.md`: added the `E-DATA-ASSIGN-NO-DRAW` and `E-DATA-ASSIGN-RATIO`
rows to § Errors `validate` reports (alphabetical position preserved: after
`E-DATA-ASSIGN-MISSING`, before `E-DATA-ASSIGN-STRATIFY-UNKNOWN`), added one new
§ Validation row ("Ratio and strata need a draw", right after "Ratio names
levels", mirroring § Allocation's own sentence order), and named both codes
inline in § Allocation's existing prose (no wording changed, only the two
`E-DATA-ASSIGN-*` citations added).

## Tests

Seven new test *functions* in `tests/test_validate.py` (corrected from an
earlier draft of this report that said nine — that count double-counted two
second assertions inside existing test bodies as separate tests), all using
`_check_assign` directly (plus `write_config`/`_error_codes` for the two that
need the `-DRAWN` + `-RATIO` pairing through the real envelope): the five the
brief named (partial ratio, undeclared-level ratio, non-empty ratio under
`by_attribute`, empty-ratio control, full-ratio-under-drawn-method control),
plus two more for the ruling's second half (non-empty `stratify_by` under
`by_attribute` refused, empty `stratify_by` control).

`uv run pytest` — 1516 passed, 2 xfailed (unrelated, pre-existing).
`uv run ruff check .` and `uv run mypy` — clean.

## Mutation testing

Five mutations applied, run, confirmed FAIL, reverted, confirmed PASS,
`__pycache__` cleared between each:

1. Disable the `random`/`blocked` ratio-levels check (`if False:`) — killed
   `test_a_partial_ratio_is_refused` and
   `test_a_ratio_naming_an_undeclared_level_is_refused`; the drawn-method
   accept control stayed green.
2. Invert the set-inequality (`!=` → `==`) — killed all three of those tests
   at once (expected: the comparison is shared by refuse and accept paths).
3. Swap `keys_repr`/`levels_repr` in the `E-DATA-ASSIGN-RATIO` message — killed
   both refuse tests once the partial-ratio test's assertion was tightened
   from a weak "`'control'`/`'treatment'`/`'arm'` all appear somewhere" (which
   the mutation survived, since `levels_repr` also contains those words) to
   `"has key 'control';"` — recorded in the test's own docstring why the
   tighter assertion was needed.
4. Change `E-DATA-ASSIGN-RATIO`'s code string to `E-DATA-ASSIGN-DRAWN` —
   killed both refuse tests (exact-set assertion catches the collapse).
5. Disable the `by_attribute` `ratio` check, then separately the `stratify_by`
   check (`if False:`) — each killed exactly its own test
   (`test_a_non_empty_ratio_under_by_attribute_is_refused` /
   `test_a_non_empty_stratify_by_under_by_attribute_is_refused`) and no other.
6. Swap the `ratio`/`stratify_by` finding paths in the `by_attribute` branch —
   killed the ratio test's `path ==` assertion.

Six mutation runs total. Five of the six each killed exactly one test and
left every other green; #2 is the exception and is reported as one, not
folded into the "each kills only its own" claim an earlier draft of this
report made incorrectly — inverting the shared set-comparison operator
necessarily breaks both the refuse tests that depend on it being false and
the accept test that depends on it being true, so three tests dying to one
mutation there is the expected shape of that particular mutation, not a
sign the tests are non-independent.

## Concerns / judgment calls to flag

- **The brief's five tests, as written, cannot all pass without deciding a
  method for tests 1–2 the brief doesn't state.** *Ratio names levels* only
  means anything for a method that draws (§ Allocation, task-1 report's own
  reading), so "two levels, one entry" and "names an undeclared level" had to
  be run under `random`/`blocked`, not `by_attribute` — otherwise they'd
  collide with the *outright* by_attribute rejection (test 3) and never
  exercise the keys-vs-levels comparison at all. I read this from task 1's
  ambiguity note ("gate accordingly rather than re-deriving it from the row
  alone") rather than the brief itself, which doesn't name a method for these
  two. I'm confident in the reading, but it's an inference, not a literal
  instruction.

- **Whether the two `by_attribute` refusals need their own code or share
  one — sharing, and here's the argument.** § Allocation's own prose calls
  `stratify_by`'s rejection under `by_attribute` "the same fault" `ratio`'s
  is, twice (once in § Allocation, once again in § Manifest, both verbatim
  "the same fault"). The two firings are structurally identical: same
  triggering condition (`method: by_attribute`, field present and non-empty),
  same remedy (remove the field, or switch to a drawing method), same
  reasoning (a field that describes a draw where none happened) — differing
  only in *which* field. This mirrors an existing precedent in the same
  function: `E-DATA-ASSIGN-LEVELS` already covers two directions of one fault
  (a value naming no declared level, *or* a declared level no value names)
  under one code, specifically because both are "one code" per the doc's own
  language. A split code (e.g. a `-RATIO`-flavored one for `ratio` and a
  `-STRATIFY`-flavored one for `stratify_by`) would say two different things
  where the spec says one, and would also collide in spirit with
  `E-DATA-ASSIGN-STRATIFY-UNKNOWN`, which is reserved for a *different*
  `stratify_by` fault (target existence, under `random`/`blocked`) that a
  later task still owns. One code, two paths, one finding per offending
  field — that's what shipped, as `E-DATA-ASSIGN-NO-DRAW`.

- **No requirement here rests on a false premise.** The live-gap claim in the
  brief was verified directly against the code before writing anything: a
  full-file grep for `ratio` in `validate.py` found only comments before this
  change, confirming the brief's "nothing reads `ratio`" was accurate, not
  stale.

## Review response

Two fixes made after review, both mutation-proved; report corrections above
are also from that review.

### 1. Untested direction on *Ratio names levels* — fixed

`test_a_ratio_naming_an_undeclared_level_is_refused`'s fixture
(`{control: 1, f: 2}` against levels `[control, treatment]`) is simultaneously
partial (missing `treatment`) and extra-keyed (`f`), so it can't isolate the
direction its own name claims: a check reading only "every declared level has
an entry" (`not set(levels) <= set(ratio)`) passes it identically to the real
`set(ratio) != set(levels)`. Added
`test_a_ratio_with_every_level_plus_an_extra_key_is_refused`, using
`{control: 1, treatment: 1, f: 2}` — a strict superset of the declared levels,
every level present plus one that isn't — which only the real two-directional
equality check catches.

Mutation: replaced `set(ratio) != set(levels)` with
`not set(levels) <= set(ratio)`. Before the new test, this mutation survived
the whole suite green (confirmed independently, matching the review). After
the new test: `1 failed, 1518 passed, 2 xfailed` — the new test is the one
and only failure. Reverted, confirmed `1519 passed, 2 xfailed`.

### 2. Wrong-typed `ratio`/`stratify_by` under `by_attribute` — absorbed under `E-DATA-ASSIGN-NO-DRAW`

Changed both `by_attribute`-branch checks from an `isinstance` type gate to a
structural presence test:

```python
ratio = block.get("ratio")
if ratio is not None and ratio != {}:
    ...
stratify_by = block.get("stratify_by")
if stratify_by is not None and stratify_by != []:
    ...
```

so `ratio: 3` and a bare `stratify_by: site` are now "present and non-empty"
by the same test a well-formed non-empty value is, rather than silently
passing an `isinstance` check tuned for the well-formed case. Rationale
corrected in both the code comment, the `_check_assign` docstring, and
`docs/reference.md`'s `E-DATA-ASSIGN-NO-DRAW` row: the borrowed line ("carries
no meaningful key set to report on") was `E-DATA-ASSIGN-RATIO`'s reasoning,
not this row's — `-RATIO`'s fault is the *keys*, `-NO-DRAW`'s fault is
*presence*, and a bare string is exactly as present as a populated mapping.
Also fixed the docstring's stale "four rows" (it lists three § Validation
rows — *Ratio and strata need a draw* covers both `ratio` and `stratify_by`
in one row — an artifact of merging the two fields into a single row after
the paragraph was first drafted for four separate fields).

Two new tests: `test_a_wrong_typed_ratio_under_by_attribute_is_refused`
(`ratio: 3`) and `test_a_wrong_typed_stratify_by_under_by_attribute_is_refused`
(`stratify_by: "site"`), both asserting the exact single-finding set, the
path, and a message substring.

Mutation, ratio half: reverted the condition to
`isinstance(ratio, dict) and ratio`. Result: `1 failed, 3 passed` on the
four-test filter — only `test_a_wrong_typed_ratio_under_by_attribute_is_refused`
died; the wrong-typed-`stratify_by`, non-empty-well-formed-ratio, and
empty-ratio-control tests stayed green. Reverted, confirmed green.

Mutation, `stratify_by` half: same treatment
(`isinstance(stratify_by, list) and stratify_by`). Result: `1 failed, 3
passed` — only `test_a_wrong_typed_stratify_by_under_by_attribute_is_refused`
died. Reverted, confirmed green.

Full suite after both fixes: `uv run pytest` — 1519 passed, 2 xfailed.
`ruff check .` and `mypy` — clean.

### Recorded for task 10 (not fixed here — out of this task's scope)

`ratio` *values* are unchecked: `{control: 0, treatment: 1}` passes every
check in this slice (both keys are declared levels, so *Ratio names levels*
has nothing to say about the values `0`/`1` themselves). Nothing in the four
documents promises a value-level check, so this is not a divergence — but
*Block size fills the arms* (§ Validation, still unimplemented) sums
`ratio`'s values to test `block_size`'s divisibility, and a zero or negative
entry will need its own decision there (whether `E-DATA-ASSIGN-RATIO`'s row
grows a values check, or `-block-size`'s row absorbs it, or a new code):
flagging now so task 10 doesn't discover it mid-implementation.
