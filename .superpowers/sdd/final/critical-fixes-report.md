# Pre-merge fix wave: declared-but-unimplemented blocks, path handling

## What was fixed

1. **Silent no-ops → refusals.** Added `validate._check_unimplemented`, called from
   `validate_config`, raising:
   - `E-SWEEP-UNSUPPORTED` for a non-empty `sweep.{baseline,grid,paired,ablate,sample,groups}`
   - `E-DATA-UNITS-UNSUPPORTED` for a non-empty `data.units`
   - `E-REPL-ORDER-UNSUPPORTED` for `replication.order` other than `as_declared`

   Each message states the block is specified but not implemented in this build and will
   be honored in a later slice. Pattern mirrors the existing `E-REPL-KIND-UNSUPPORTED`.

2. **Relative `input_dir`/`output_dir`.** Added `E-DATA-NOT-ABSOLUTE` in `validate._check_data`,
   checked after `expanduser()` and before the `E-DATA-IN-REPO` containment check (which now
   only ever receives absolute, resolved paths). `generate_experiment` is deliberately left
   writing the raw string it's given — resolving there too would mean `generate` silently
   rewrites user input against its own cwd; `validate` stays the single place that enforces
   absoluteness, and a scaffolded relative path fails fast on the next `validate`.

3. **Hoisting completed.** `E-DATA-REQUIRED` and `E-DATA-UNREADABLE` moved above the
   `E-GIT-NO-REPO` early return in `_check_data`, alongside the already-hoisted policy check.
   Only `E-DATA-IN-REPO` still depends on a resolved repo root and stays behind it.

4. **Deduplicated in-repo check.** Extracted `provenance.resolves_inside_repo(resolved, root)`;
   called by both `validate._check_data` and `generators.experiment.generate_experiment`, each
   keeping its own error code/message as instructed.

5. Added 8 new tests in `tests/test_validate.py`: one positive + one clean-config test per new
   identifier area, plus the repo-less `E-DATA-REQUIRED` regression test, plus two
   `E-DATA-NOT-ABSOLUTE` tests (input_dir, output_dir).

6. Appended a new-identifiers entry to `docs/superpowers/spec-defects.md`.

## Reproduction verified fixed

A config with `sweep.grid: {analysis.method: [pearson, spearman]}` run via
`publishable run configs/cohort-pilot/config.yaml` now exits 1 with
`E-SWEEP-UNSUPPORTED`, instead of exit 0 with one condition silently executed.

## Verification

- `uv run pytest -q` → 194 passed (was 186; +8 new tests)
- `uv run ruff check .` → All checks passed
- `uv run mypy` → Success: no issues found in 30 source files

## Not applied / left as-is

- `README.md` untouched, per explicit instruction.
- `cli.py`'s `conditions=[(0, None)]` hardcode itself is untouched — validate now refuses
  before `command_run` ever reaches it, which is the requested fix surface.
- `generate_experiment` does not resolve/validate absolute paths at generation time (see
  point 2's rationale) — only `validate` enforces it.
