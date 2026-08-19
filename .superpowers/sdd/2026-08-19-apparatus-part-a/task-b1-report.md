# H7d Part A, batch 1 (tasks 18, 1, 2, 3) — report

**Status: complete.** Branch `h7d-apparatus-part-a`, four commits, in the required order.

## Commits

- `7568a34` — task 18: the guard pin
- `0113fce` — task 1: the check-placement change in `reference.md` and `experimental-designs.md`
- `4c1c0ae` — task 2: `Apparatus`, exported
- `d1590a4` — task 3: probe dispatch (`apparatus._probe_for`)

## Test summary

Final full run: `uv run pytest -q` → **2370 passed, 1 skipped, 2 xfailed**
(baseline 2363 passed + 1 [task 18] + 1 [task 1] + 2 [task 2] + 3 [task 3] = 2370). Gates clean:
`uv run ruff check .`, `uv run ruff format --check .` (82 files formatted), `uv run mypy` (46
source files, up from the 45 baseline after task 2 added `apparatus.py`).

## Task 18's literals, and how they were captured

Captured by running `run_a_project` end to end in this working tree (a throwaway `uv run python`
script driving `tests.test_cli.run_a_project` against a `tmp_path`), **before** writing the
assertion — not transcribed from `cli.py`. Output:

```
provenance keys: ['git', 'environment', 'apparatus', 'input_manifest', 'input_manifest_hash',
  'input_manifest_changed', 'publishable_version', 'plugin_versions', 'units', 'units_hash',
  'allocation', 'allocation_hash']
apparatus: None
entries: ['environment', 'executions.jsonl', 'manifest', 'run.yaml', 'seed30', 'seed40', 'seed47',
  'seed52', 'seed61', 'sweep.yaml']
```

These matched the brief's literals exactly (repeat-dir names are the `seed*` instantiation of the
brief's `<repeat dirs>` placeholder). The test as written in the brief was added unchanged. Mutation
(`"apparatus": None,` → `"apparatus": {"probe": None},"` in `cli.py`) made the new test FAIL on
`is None` as prescribed; reverted by editing the line back, confirmed green by re-running.

## Mutations, exact text and outcome

1. **Task 18** — `src/publishable/cli.py`: `"apparatus": None,` → `"apparatus": {"probe": None},`.
   Full suite: `test_a_run_with_no_declared_probe_records_a_null_apparatus_block_and_no_ledger`
   FAILED (`assert {'probe': None} is None`), nothing else affected. Reverted; re-ran, green.
2. **Task 2** — added a `__post_init__` to `Apparatus` in `apparatus.py` raising `ContractError` on
   any fact value that isn't `bool | int | float | str | None`. Full suite:
   `test_apparatus_accepts_a_shape_core_will_later_refuse` FAILED as prescribed (`facts={"nested":
   {"a": 1}}` now raises), nothing else affected. Reverted by deleting the method; re-ran, green.
3. **Task 3** — deleted the `check_registration(ep, declared_names(PROBE_GROUP, fn))` line in
   `apparatus._probe_for`. Full suite:
   `test_a_probe_whose_module_declares_a_different_name_is_E_PLUGIN_DECORATOR` FAILED (`DID NOT
   RAISE ContractError`), nothing else affected. Reverted; re-ran, green.

All three mutations produced a genuine branch difference (object returned vs. exception raised /
`None` vs. dict), not a crash or a string-literal artifact.

## Where a brief, the design, or the plan disagreed with the code

None found. Read the design's 14 decisions, the plan's "Corrections against the code" (all 14),
and the fixture sections before writing; nothing in tasks 18/1/2/3's own briefs asked for anything
the code contradicted. `plugins.py` already had `PROBES`, `register_probe`, `PROBE_GROUP`-shaped
support (as `"publishable.probes"`), and `check_registration`/`load_entry_point`/`scan_group`/
`declared_names` all had production callers through `units._resolver_for` exactly as the plan
states — `apparatus._probe_for` is a straight sibling, as prescribed, with the value contract
(Decision 5 / correction 11) deliberately left unenforced in `Apparatus.__init__` per task 2's
second test.

## Notes

- Doc edits (task 1) were verified as sited-widening rather than word-swaps: both target strings
  (`warning at \`dry-run\``, `` `dry-run` warns instead of the run failing ``) were present before
  editing (grep-confirmed) and absent after; `wherever a probe runs` appears twice in
  `reference.md` after the edit. The `grep -n "dry-run"` sweep across all four documents was read
  in full; every other hit was judged "correct, keep" per the brief's own worked list (CLI
  reference row, § Before you spend it, § Exit codes cost ordering, § One execution at a time, the
  `apparatus/probes.jsonl` ledger-phases line, etc.) — none needed a change beyond the three sited.
- No mechanical issues found on the two edited documents (no trailing whitespace/tabs introduced,
  no headings changed so no anchors moved).
- `docs/reference.md` § Package layout's `apparatus.py` row now reads without the `— not yet built`
  marker, per task 2 step 2 — description text ("per-condition facts, the change gate, `Apparatus`")
  left as-is since later Part A tasks build the rest of that file.
