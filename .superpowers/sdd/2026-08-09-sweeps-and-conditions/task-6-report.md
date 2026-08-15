# Task 6 report: `sweep.yaml`

Implemented `sweep_document(conditions, repeats, digest, order, execution_order, order_seed=None) -> dict[str, Any]`
in `src/publishable/sweep.py`, matching `docs/reference.md` § "`sweep.yaml` — the resolved
plan" exactly. `Repeat` is imported only under `TYPE_CHECKING`, so `sweep.py` remains free
of a runtime dependency on `replication` (and of any dependency on
`config`/`artifacts`/`runner`/`cli`) — the module takes no filesystem action and returns
plain data; whoever writes `sweep.yaml` to disk is a different module.

**Revision note:** the brief's Step 3 shape (`repeats` as one flat `{kind, label, seed}`
record per repeat, `order` as a list of realized `[index, label]` pairs) did not match the
document. This was caught in review, not by me at brief-reading time — it should have been:
the moment the brief's shape diverges from `reference.md`, that's the signal to stop and
check the document rather than transcribe the brief. Per the standing rule, the document is
normative and led here; the code was rewritten to match it, and nothing needed to change in
`reference.md`. This is not a spec defect (the document was right, the brief text was wrong)
so nothing is logged in `spec-defects.md`, but it is recorded here as a defect in the task
brief.

Final shape, matching the document:
- `repeats`: grouped by kind, each entry `{kind, seeds: [...]}` with seeds resolved in
  encounter order — the shape before fold membership (a later slice) adds `partitions`.
- `labels`: a separate top-level list of each repeat's composed label, outer to inner.
- `order`: the scalar mode (`as_declared` | `randomized`) — the rule.
- `execution_order`: the realized sequence, `[{condition: int, repeat: label}, ...]` — the
  fact, recorded rather than re-derived.
- `order_seed`: written only when passed (i.e. under `order: randomized`); its absence
  under `as_declared` means nothing was shuffled, not that a seed was lost.

Added six tests to `tests/test_sweep.py`:
- `test_the_sweep_document_records_the_resolved_plan` — asserts the full documented shape:
  grouped `repeats`, top-level `labels`, scalar `order`, `execution_order` as
  `{condition, repeat}` mappings, and `order_seed` absent under `as_declared`.
- `test_a_randomized_order_records_its_seed` — `order_seed` present and correct under
  `order: randomized`.
- `test_the_document_is_plain_yaml_safe_data` — round-trips through
  `yaml.safe_dump`/`safe_load`.
- `test_the_document_round_trips_a_float_and_a_boolean_condition_value` — a swept `float`
  and `bool` value must round-trip as the same Python type (`isinstance` checks, not just
  equality), and the nested `repeats`/`labels`/`execution_order` structures round-trip too,
  not only the top-level keys.

All 386 tests pass (382 pre-existing + 4 net new after the revision), `ruff check .` and
`mypy` both clean.
