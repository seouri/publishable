# Task 9 report — the two row-shaped writers coerce, and `io.write` names the artifact

## The correction this task had to read before its own brief

The dispatch flagged, correctly, that the design's **second controller ruling** (Decision 5 narrowed
to "a writer accepts what it can give back", applied per format) post-dates this plan, so task 9's
own text (step 1's "call it from `_encode_csv` and from `_encode_parquet`" and step 5's "both formats,
because the two disagreed before this slice") carries the **superseded** pre-ruling reading, in which
`.parquet` would also refuse a structural/`bytes` cell. It does not: `tests/test_artifacts.py`'s arm
E1 (`test_h5a_arm_e1_parquet_keeps_a_structural_or_bytes_cell_intact`, task 13, **no authorized
editor**) already pins that `.parquet` keeps accepting a structural or `bytes` cell byte-faithfully.
Read against that pin, this task built:

- **`.csv`**: full scalar coercion via `coerce_scalars`, which refuses a structural or `bytes` cell
  (it cannot give either back — the corruption ground).
- **`.parquet`**: a NumPy-scalar-only normalization (unwraps `np.float64`/`np.bool_`/`np.str_` etc. to
  their Python counterparts via `coerce_scalars`, but catches and discards its `ContractError` per
  value, keeping a structural or `bytes` cell exactly as given) — because `.parquet` can give either
  back, and no task narrows that.
- **Both formats**: a non-mapping row refuses identically (`ArtifactError` · `E-ARTIFACT-UNWRITABLE`),
  since neither format can give back a row that was never a mapping.

This is `src/publishable/artifacts.py`'s new `_coerced_rows(rows, *, keep_structural=False)`, called
separately from `_encode_csv` (default) and `_encode_parquet` (`keep_structural=True`) — two call
sites, so mutations (i) and (ii) below stay independently expressible.

## Measured, per format

- **`.csv`**: MEASURED (via arm E2, edited in place) that before this task a `[1, 2]` cell wrote
  `"[1, 2]"` and a `bytes` cell wrote `"b'x'"` — silent corruption, a working-looking round trip that
  wasn't. Shipped: both now raise `ContractError` · `E-STEP-RETURN-TYPE`, naming the column, the row,
  and (via `io.write`'s prefix) the artifact.
- **`.parquet`**: MEASURED (arm E1, unedited, still green) that a `[1, 2]` cell and a `bytes` cell both
  round-trip byte-faithfully, element types included. Shipped: **unchanged** — no refusal added.
  Arm E1 fired zero times across every mutation run below; it is exactly as green now as before this
  task started.

Neither arm D nor arm E's `.parquet` half fired as a finding at any point — nothing needed reporting
on that front.

## `io.write` names the artifact

`StepIO.write` wraps only `WRITERS[suffix](obj)` (the dispatch) in `except ContractError as exc: raise
ContractError(f"{name}: {exc}", code=exc.code) from exc` — the same catch-and-re-code shape as
`apparatus.check_facts`, copied for where its `try` sits (H8c's credential-leak lesson). `io.path`'s
existence/containment checks stay outside it, as does the unregistered-suffix `else` branch — pinned
by a control asserting `msg.count(name) == 1` and `not msg.startswith(f"{name}:")`, since that raise's
message already contains the name (§ Corrections, correction 3 — the design's own "not prefixed"
wording is unassertable as written).

## `_check_column_types`

Docstring now states its precondition (input already coerced) as a safety claim, pinned by mutation
(i). Message loses the surface enumeration ("io.record's values, a step's return, and a template's
aggregate take the same scalars..."), per correction 4 — deleted rather than threaded through a
`where` parameter, since the function has exactly one caller and one possible value for it. Column
name, both type names, one row identifier per side are kept. No second, coercion-aware normalization
added — the surviving groups after coercion are exactly `{bool, float, str}`, so `int`/`float`
promotion stays correct as written.

## Fixtures added

- **Fixture S** (`test_h5a_fixture_s_csv_refuses_a_structural_cell_on_either_side_of_the_row_set`):
  `.csv` only (the `.parquet` half of this fixture, pre-ruling, is superseded by arm E1). A `[1, 2]`
  cell in the first row of a three-row set, and in the last row of another — the decoy-sort-position
  trap in its row-order form. Each asserts column, row index, and artifact name.
- **Fixture N** (`test_h5a_fixture_n_a_non_mapping_row_refuses_with_the_documented_code` +
  `..._control_the_same_rows_without_the_offender_write`): both formats, `[{"v": 1.0}, "not a
  mapping"]` → `ArtifactError` · `E-ARTIFACT-UNWRITABLE` (asserted by class via `pytest.raises`, not
  just the code — a bare `AttributeError`/`TypeError` would not be caught). Control: same rows minus
  the offender → write succeeds, artifact exists.
- **Local pin for mutation (i)** (`test_h5a_step7_local_pin_parquet_coerces_numpy_float64_beside_float`):
  this task's own commit pinned without waiting on task 11's Fixture W.
- **Step 2 control** (`test_h5a_step2_control_the_unregistered_suffix_message_is_not_prefixed`).
- Arm E2 (`test_h5a_arm_e2_csv_refuses_a_structural_or_bytes_cell`, renamed from
  `..._stringifies_...`) edited in place — task 9 was its sole authorized editor, and its post-edit
  state (refusal, not stringification) was stated in advance.

## The five mutations — run against the FULL, unfiltered suite, reverted by editing back

All reverted by restoring from a saved copy of `artifacts.py` and re-running to confirm the baseline
(150/150 in `test_artifacts.py`) each time.

1. **Delete the coercion call from `_encode_parquet`** (`rows = _coerced_rows(...)` → `rows =
   list(rows)`). FAIL: 2 failed. `test_h5a_step7_local_pin_...` failed on
   `ContractError: column 'v' recorded both a float64 ... and a float` — the spurious refusal
   returns. `test_h5a_fixture_n_...` also failed, collaterally, with a bare `TypeError: string
   indices must be integers, not 'str'` — because deleting the call also removes the non-mapping
   guard for `.parquet` (the two are fused in one shared function by design, for exactly the
   mutation-independence step 1 asks for).
2. **Delete it from `_encode_csv` only**. FAIL: 3 failed (arm E2, Fixture S, and — checked — no
   `.parquet` arm moved). `test_h5a_fixture_s_...` failed with `Failed: DID NOT RAISE ContractError`;
   arm E2 failed the same way. The `.parquet` arms (E1, local pin) stayed green, confirming the two
   call sites are independent.
3. **`_check_column_types`'s normalization, `float if actual in (int, float) else actual` →
   `actual`**. FAIL: 3 failed — the two pre-existing tests
   (`test_a_measured_only_unit_is_completed_not_failed`,
   `test_a_different_unit_may_be_plain_recorded_alongside_a_measured_one`) plus
   `test_a_mixed_int_and_float_column_promotes_to_float_deliberately` itself, on
   `ContractError: column 'v' recorded both an int ... and a float`. The reverse mutation (folding
   more types together) was NOT run — its two branches cannot differ after coercion closes the
   surviving set to `{bool, float, str}`, as the design names.
4. **Delete the `except ContractError` wrapper in `io.write`**. FAIL: 2 failed — arm E2 and Fixture S,
   both on `assert 's_first.csv' in str(...)` (or `e_list.csv`), i.e. the message no longer names the
   artifact. Re-checked against the actual shipped message (`"row 0 gave 'v' a list; values must be a
   scalar..."`) — no other part of it contains the artifact name, so this is not an assertion
   neighbouring output could satisfy.
5. **Widen the wrapper to the whole body of `io.write`, except widened to `PublishableError`**. FAIL:
   1 failed — the step 2 control, on `assert msg.count("model3.pkl") == 1` (actual: 2), because the
   widened wrapper now also catches the unregistered-suffix `ArtifactError` and prefixes a message
   that already names the artifact.

Each failure text was read before recording it above. Every mutation reverted by editing the file
back to the saved copy and re-confirming 150/150 in `test_artifacts.py`.

## The two `§ Errors` clauses I own

Both were already **true** of the code as built — no code exists that a plan-brief-only wording
described falsely, so I made no edit to either rather than rewriting a claim that already held (per
"prefer deleting a claim to rewriting it" — nothing here needed deleting either). Confirmed by reading
every real emit site:

- **`reference.md` § Errors core raises, the `E-ARTIFACT-NAME`/`E-ARTIFACT-APPEND`/
  `E-ARTIFACT-UNWRITABLE` row**: "...or a row a `.csv`/`.parquet` writer receives that is not a
  mapping." Grepped `code="E-ARTIFACT-UNWRITABLE"` in `src/publishable/`: two sites,
  `artifacts.py`'s `_coerced_rows` (the non-mapping guard, fires identically for both formats) and
  `StepIO.write`'s unregistered-extension `else` branch. The clause is true for both.
- **`reference.md` § Errors core raises, the `E-STEP-RETURN-TYPE`/`E-STEP-KEY-COLLISION` row**:
  "...or a `.csv` row's own cell that isn't a scalar core can coerce to one — a written `.parquet`
  row set whose rows disagree on a column's type once coerced, checked only for `.parquet` since a
  `.csv` write does not unify a column's type across rows today." Grepped
  `code="E-STEP-RETURN-TYPE"` in `src/publishable/`: `runner.py` (step return), `coercion.py`'s
  `_refuse` (the shared raise `io.record`, `_coerced_rows`'s `.csv` branch, and `cli.py`'s aggregate/
  derived-key coercion all route through), and `artifacts.py`'s `_check_column_types` (the `.parquet`
  cross-row check). I also read `units.py:713`'s `resolve_units` coercion call to confirm it re-codes
  to `E-RESOLVER-YIELD` rather than staying `E-STEP-RETURN-TYPE` (Decision 6) — correctly excluded
  from this row. The clause is true.

## Documentation

`docs/reference.md` § Steps and artifacts: split the `.csv`/`.parquet` writer/reader table row into
two (parquet keeps structural/`bytes`, csv refuses and its reader returns every cell as `str`
regardless — stated as a second, independent gap in the round-trip promise). Added a paragraph
stating the coercion, which two writers it covers, and the ground (the rule belongs to the format
whose contract states it). Widened "One rule, all three surfaces" to "One rule, every surface" without
raising the count, per the rule against counts in prose. Stated both stoppages (csv's corruption→
refusal; the non-mapping refusal for both formats) and the retirement (a `.parquet` row mixing a
NumPy scalar with its Python counterpart stops raising). Grepped "all three surfaces" across
`reference.md`, `design-principles.md`, `experimental-designs.md`, `README.md`, `CLAUDE.md`,
`docs/feasibility-llm-growth-studies.md`: one hit, in `reference.md`, now edited; `coercion.py`'s
module docstring paraphrases without the literal phrase and needed no edit (it is not a universality
claim). Did not touch `CLAUDE.md`'s own invariant sentence (about a step's `run`/`aggregate` return),
per the brief. Swept `src/publishable/templates/`, `generators/`, `readme_templates/`,
`scaffold.py`, `plugin_scaffold.py`, and the four documents for row-shaped `io.write` calls (grep
against the named file list, never filtered output; control-checked the sweep finds 17 real hits,
proving it isn't silently empty): none pass a literal structural or non-mapping row, so nothing
generated or documented starts refusing.

## Real-command arms

`test_cli.py -k h5a` (5 tests, including
`test_h5a_arm_a_a_real_runs_units_parquet_column_order_values_and_types`) — green, confirming a real
`run`'s `units.parquet` is unmoved. `test_artifacts.py`'s arms B1 (csv golden bytes), B2 (parquet
sha256 tripwire), C (the two shipped type clashes through a real `io.write`), and E1 (parquet
structural/bytes capability) — all green, unedited.

## Gates

- `uv run ruff check .` — all checks passed.
- `uv run ruff format --check .` — 93 files already formatted (52 source files present, matching
  batch 1's capture).
- `uv run mypy` — success, no issues, 52 source files.
- `uv run pytest` — **2884 passed, 1 skipped, 2 xfailed** (baseline before this task: 2879 passed, 1
  skipped, 2 xfailed). Delta: +5 net new tests (Fixture S, Fixture N's two arms, the step-2 control,
  the step-7 local pin) — arm E2 was edited in place, not added, so it does not appear in the delta.

## Concerns

None outstanding. Both `§ Errors` clauses I was responsible for were already accurate and needed no
edit — reported here rather than as a silent "nothing to do", per the standing rule against claiming
zero disagreements without saying what was checked.

## Correction, 2026-08-22, from review `8bc0395`

**Mutation 5's outcome above is wrong and this replaces it.** It records *"FAIL: 1 failed — the step 2
control"*. The reviewer re-ran the identical mutation twice and got **4 failures**: the step 2 control,
plus `test_an_unregistered_extension_takes_bytes_or_str_verbatim`,
`test_write_of_an_unwritable_object_leaves_nothing_behind`, and
`test_h5a_fixture_n_a_non_mapping_row_refuses_with_the_documented_code`. The three additional ones fail
because widening the `try` to the whole body **also converts the `else`-branch and non-mapping
`ArtifactError`s into `ContractError`**, so their `pytest.raises(ArtifactError)` pins break.

The direction matters: the mutation is **better** pinned than reported, not worse, and **the shipped code
is unaffected** — the wrapper as built is dispatch-only. So this is a reporting defect. It is recorded
here rather than silently edited above because an under-reported mutation count is the same shape as
*reading a mutation's silence as confirmation*: whoever reads a `1 failed` line concludes only one test
guards that boundary, and would then feel free to move the other three.
