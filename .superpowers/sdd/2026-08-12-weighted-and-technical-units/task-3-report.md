# Task 3 report: the input path collapses before uniqueness

**Status: DONE_WITH_CONCERNS** (two open items: `technical_n`'s onward route, § 4; two error-registry
rows now stale, § 3b — both recorded, neither guessed at).

**Commit:** `901276d` — *feat: collapse technical replicates at resolution, before n is counted*.
One commit only: the two spec-defect entries (§ 3b) went into `docs/superpowers/spec-defects.md`,
which `.gitignore:224` excludes along with all of `docs/superpowers/`, so they are on disk but not
in history.

**The brief's step 2 could not be run in order.** "Write the failing tests, confirm each fails" is
unreachable for this task: the tests cannot be written against HEAD at all, since `resolve_units`
returns a bare `UnitList` there and every new test unpacks two values. Four mutation cycles (§ 5)
were run instead, each one turning a passing test back into the failure it is supposed to detect.

**Tests:** `uv run pytest` → 1121 passed, 2 xfailed. `uv run ruff check .` clean, `uv run mypy` clean.
`ruff format .` was not run.

---

## 1. What changed

`src/publishable/units.py`

- `resolve_units(units_decl, input_dir) -> tuple[UnitList, dict[str, float] | None]`. The collapse
  runs **between building `units` and the uniqueness loop**, so under a `measurements` declaration a
  repeated key is collapsed away before `E-UNITS-KEY-DUPLICATE` could see it, and every design
  without `measurements` reaches that loop exactly as before.
- `_measurement_axis(measurements)` — reads `by` through `Mapping.get` and raises
  `E-DATA-MEASUREMENTS-INVALID` when it is missing, empty, non-string, or when `measurements`
  is not a mapping at all. See § 3 (brief defect).
- `coerce_for_rule(column, rule, values)` — the coercion contract, § 2.
- `collapse_measurements` now calls `_apply(rule, coerce_for_rule(name, rule, values))`; the
  comprehension became a loop so `rule` is computed once and passed to both.

`src/publishable/validate.py` — `_check_units` unpacks and discards `technical_n` inside its
existing `except ContractError` wrapper.

`src/publishable/cli.py` — phase 5 unpacks to `roster, _technical_n`, with a comment recording
where `technical_n` is documented to go and why it is not carried there yet (§ 4).

`partition_units` is untouched (`git diff src/publishable/units.py | grep -c partition_units` → 0).
`E-DATA-MEASUREMENTS-UNSUPPORTED` is untouched, so every new test calls `resolve_units` directly;
the two new `validate` tests are additional, not the proof.

## 2. The coercion contract

One gate, inside the collapse path, before `_apply` ever sees a value:

| Case | Result |
|---|---|
| rule not numeric (`first`, `mode`) | values untouched — the original strings survive |
| numeric rule, **every** value passes `is_measurement_numeric` | `[float(v) for v in values]` |
| numeric rule, some value fails, but the group is constant | untouched — `_apply`'s documented "constant needs no rule" shortcut answers it |
| numeric rule, some value fails, group not constant | `ContractError` `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` |

- **`is_measurement_numeric` is the gate and bare `float` is the conversion**, because the predicate
  accepts exactly `float`'s grammar. An int-first coercion would part the two answers again. The
  visible consequence — an integer-looking column collapses to `15.0`, not `15` — is pinned by
  `test_a_csv_sourced_numeric_column_collapses_to_a_number` with a comment saying so, because
  narrowing it back to `int` is the plausible "tidy-up".
- **`_apply`'s own shortcut was not widened** — task 2's reasoning stands. Keeping the constant case
  falling through to it is also what keeps `validate`'s row-243 finding reachable with the column's
  name on it for the ordinary one-row-per-unit table (e.g. task 2's
  `test_sum_over_a_csv_sourced_boolean_looking_column_is_refused`, which still passes unchanged):
  those groups are single-member, hence constant, hence not refused by resolution.
- **The identifier is reused, not minted.** Resolution raises the same
  `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` `_check_measurements` reports, with the same message shape —
  one problem, one code, from either surface.
- **Empty `values` is unreachable, not guarded**: `names` in `collapse_measurements` is built from
  the members' own attribute keys, so every group has at least one member carrying the column. The
  short-row probe (`test_a_column_one_row_lacks_collapses_over_the_rows_that_have_it`) pins that the
  missing-in-one-row case collapses over the rows that have it rather than producing an empty list.
  I did **not** add an `E-`-coded empty guard to `_apply`, since minting a code needs a
  `reference.md` row and nothing reaches it.

Adversarial probes, all pinned: mixed `["10","north"]`, an empty cell, a short row (`None`), a
column absent from one row, a single-member group, `nan`, an over-long row, `mode`/`median`/`sum`
variants, `by` naming the column being collapsed, and an omitted `collapse`.
`test_nothing_but_a_contract_error_escapes_resolve_units` sweeps 5 tables × 6 declarations and
asserts that anything raised is a coded `ContractError` — anything else fails the test by escaping.

## 3. Brief defect found (as the advisor predicted, and confirmed against the code)

The brief's snippet does `str(measurements["by"])` behind `if measurements:`. Both halves escape as
non-`ContractError`: `measurements: {collapse: mean}` → `KeyError`; `measurements: "yes"` →
`AttributeError`. This is not theoretical — `validate_config` calls `_check_units` (line order:
`_check_data`, `_check_units`, `_check_measurements`), so **resolution reaches a malformed block
before `_check_measurements` can report it**, and `_check_units` catches `ContractError` only. Fixed
by `_measurement_axis`, raising the same `E-DATA-MEASUREMENTS-INVALID` the shape check reports;
`test_a_malformed_measurements_block_is_a_contract_error_not_a_crash` covers all four shapes.

Consequence worth knowing for later tasks: a config with a malformed `by` now draws
`E-DATA-MEASUREMENTS-INVALID` **twice** (once at `data.units` from resolution, once at
`data.units.measurements.by` from the check). Two findings sharing one code beat one misleading
code (`E-UNITS-KEY-DUPLICATE` for a design whose repeated keys are the point), which is what
skipping the collapse instead would have produced. No existing test asserts an exact finding set,
so nothing broke; if task 6 or task 12 wants that deduplicated, the place is `_check_units`.

### 3b. Two error-registry rows are now stale (recorded, not guessed at)

`resolve_units` now raises `E-DATA-MEASUREMENTS-INVALID` and `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`,
which task 2 introduced as `validate` findings. I checked both rows in `reference.md` § Errors
`validate` reports: neither carries the dual-surface clause this repo uses for exactly this case.
`E-UNITS-COLLAPSE-RULE`'s row is the model — "raised where technical replicates are collapsed,
which `validate` also resolves and reports under the same code" — and it also has a row in § Errors
core raises. The two `measurements` codes have neither.

I did **not** edit `reference.md`: the rows sit in the same two sections task 6 rewrites when it
retires `E-DATA-MEASUREMENTS-UNSUPPORTED`, and splitting one section's consistency pass across two
commits is how a row gets edited twice into disagreement. Recorded in
`docs/superpowers/spec-defects.md` with the wording to mirror, and named here as task 6's to close.

The same entry's neighbour records a second gap found in passing: **`measurements.by` is not checked
against the declared attributes**, so `{by: read_id}` with `attributes: [depth]` collapses on the key
alone and succeeds. `_check_measurements` is the home — it already holds the resolved roster — and
it is task 6's block too.

## 4. `technical_n`'s onward route — the open item

**I did not wire it into the record**, and I think that is the correct call rather than a shortfall:

- `reference.md` § What isn't a repeat shows `technical_n` **beside a metric's `n`** in `run.yaml`
  (the `r:` block, next to `n`, `repeat_spread`, `ci95`) — i.e. per metric, not per run. The route
  to a metric is `runner.attrition`'s `counts` dict → `stats.summarize_step(collapsed, counts, …)`.
- **Task 9 owns that plumbing** and is explicitly scoped to decide the shape question for a
  sibling-of-`n` value: "`weighted_by` needs its own way through; decide which and say so, rather
  than widening `counts` with a key that is not a count." `technical_n` is the identical problem
  (it is not a count of units), and building it here would pre-empt a decision another task was
  scoped to make, in a file (`runner.py`, `stats.py`) task 3 does not list.
- **`provenance.units` is documented as exactly `{n: 240, key: patient_id}`.** Parking it there
  would invent a `run.yaml` field no document describes — the drift class task 12's completeness
  pass exists to catch, and CLAUDE.md says the document changes first.

So this is a **scope/sequencing gap, not a document decision**: the document already states both the
shape and the location. What is unsettled is which task builds the path from phase 5 to a metric.
The cli.py comment records all of this at the site. **Recommendation:** fold it into task 9, whose
`counts`/`summarize_step` decision it shares, or give it a task of its own before task 12 — as it
stands, the slice can collapse technical replicates without ever reporting `technical_n`, which is
half of what § What isn't a repeat promises.

Note also that the *step* path (task 5, `io.record(measurement=)`) will produce its own measurement
counts, and those are genuinely per-step — another reason the metric-level attachment is better
made once, downstream, than twice.

## 5. Mutation testing

Four cycles. Each: apply, delete every `__pycache__`, run, confirm FAIL, restore from a pre-mutation
copy, delete `__pycache__` again, confirm PASS **by re-running the same tests** (never `git status`).

| Mutation | Result |
|---|---|
| Collapse moved **after** the uniqueness loop (the brief's) | `test_duplicate_keys_collapse_when_measurements_is_declared` FAILED with `E-UNITS-KEY-DUPLICATE`, plus 5 more. Ordering is load-bearing. |
| Coercion returns values uncoerced | 5 FAILED, including `TypeError: unsupported operand type(s) for +: 'int' and 'str'` from `_apply`'s `mean` — literally the escape this task exists to close |
| Refusal branch replaced by `return values` | 4 unit FAILED **and** `test_a_mixed_column_under_mean_is_a_finding_rather_than_an_escaping_type_error` FAILED by erroring out of `validate_config` — the `validate`-never-raises invariant, observed breaking |
| `_measurement_axis` guard removed (`measurements["by"]`) | all 4 malformed-block cases FAILED with `KeyError`/`TypeError` |

Mutation 1 was **re-run over `tests/test_validate.py` as well**, because
`test_a_repeated_key_is_not_a_duplicate_once_measurements_is_declared` asserts two codes are
*absent* — the assertion shape that passes when the path never ran. Under the mutation it FAILS
(7 failures, not 6), so the negative assertion is load-bearing rather than decorative.

Post-revert verification after the last cycle: full suite 1121 passed, 2 xfailed; ruff and mypy clean.

## 6. Notes for later tasks

- `coerce_for_rule` is public alongside `rule_for` and `is_measurement_numeric`. **Task 5 should
  call it**, not re-derive the coercion: `io.record` coerces its own values, so recorded rows are
  already numbers and the gate is a no-op there — but a `mode`/`first` column mixing types, or a
  future recorded string column, hits the same fork. Calling it costs nothing and keeps the two
  paths from drifting, which is decision 4's whole point.
- The brief's `write_index` helper does not exist. Tests use the existing `input_dir` fixture plus a
  local `_write_reads` that writes CSV **text**, deliberately: what is under test is exactly what
  `csv.DictReader` hands back (every value a `str`, a short row's missing column a `None`), and a
  row-builder taking Python values would hide it.
