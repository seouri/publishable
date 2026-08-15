# Task 3 report: retire one refusal, add four

## What changed

`src/publishable/validate.py`, `_check_unimplemented`:

- Removed the blanket `E-SWEEP-UNSUPPORTED` block (and the now-unused `SWEEP_AXIS_KEYS`
  constant, whose comment was the only record that the `sweep` block has exactly six keys —
  confirmed against `docs/reference.md`'s `sweep:` example, which lists `baseline`, `groups`,
  `paired`, `ablate`, `sample`, `grid` and nothing else).
- Added a loop over `paired` / `ablate` / `sample` / `groups`, each emitting its own error code
  (`E-SWEEP-PAIRED-UNSUPPORTED`, `E-SWEEP-ABLATE-UNSUPPORTED`, `E-SWEEP-SAMPLE-UNSUPPORTED`,
  `E-SWEEP-GROUPS-UNSUPPORTED`) with the exact reasoning text and "later slice" deferral
  language from the brief. `baseline` and `grid` now fall through with no refusal.
- Fixed the function's docstring, which previously said the build "hardcodes one condition" —
  no longer true now that `baseline`/`grid` expand. Restored the `as_declared` repeats mention
  that got dropped in my first pass (caught by review before committing) so the docstring still
  explains why `E-REPL-ORDER-UNSUPPORTED` is emitted a few lines below it.

`tests/test_validate.py`:

- Replaced `test_a_declared_sweep_axis_is_refused_not_silently_ignored` and
  `test_an_empty_sweep_block_is_not_a_sweep` (both asserted on the now-retired blanket code
  using a `grid` sweep, which is exactly the case that now must validate clean) with the five
  tests from the brief: `test_baseline_and_grid_are_now_accepted`,
  `test_each_unimplemented_mode_is_refused_on_its_own` (parametrized over the four modes),
  `test_an_empty_or_null_mode_is_not_a_declaration`, and
  `test_every_sweep_refusal_message_defers_rather_than_scolds`.
- Dropped a stale `assert "E-SWEEP-UNSUPPORTED" not in found` line from
  `test_a_config_without_unimplemented_blocks_still_validates_clean` (redundant with the
  generic `-UNSUPPORTED` suffix check already in that test).

`docs/superpowers/spec-defects.md`: appended the "New error identifiers: the four sweep modes"
entry per the brief (this directory is gitignored — see below).

## Fifth-key check

Per the brief's closing instruction, checked whether `sweep` has any sub-key besides the six
axis keys the blanket refusal used to cover. `docs/reference.md`'s `sweep:` block (§ The one
config file) enumerates exactly `baseline`, `groups`, `paired`, `ablate`, `sample`, `grid` — no
seventh key. So there is no undiscovered axis to report.

One adjacent, pre-existing gap, **not introduced by this change and left alone**: nothing
validates that `sweep`'s own keys are among these six. `E-PARAM-UNKNOWN` (the typo detector
exercised by `test_an_unknown_key_is_a_typo_by_construction`) checks `parameters` against
`parameter_spec`, not the `sweep` block's own key set. A typo like `sweep: {gird: {...}}` would
validate clean both before and after this change — the old blanket refusal only ever checked
the six known keys too, so this isn't a door this task reopened. Flagging it rather than fixing
it, since it's outside Task 3's scope (retiring one refusal and splitting it into four) and
touches the shape-checking layer, not `_check_unimplemented`.

## Verification

- `uv run pytest -v`: 357 passed (352 baseline + 7 new − 2 retired).
- `uv run ruff check .`: clean.
- `uv run mypy`: clean, 33 source files.
- `grep -rn "E-SWEEP-UNSUPPORTED" src/ tests/`: no matches.
- `grep -n -A40 "^sweep:" docs/reference.md`: confirmed the six-key closed set (see above).

## Note on `docs/superpowers/` and commit scope

`docs/superpowers/` is gitignored (`.gitignore:224`), and so is `.superpowers/sdd/`. The
brief's Step 5 says `git add docs/superpowers/`, but that path is ignored in this repo — `git
add` on it is a no-op (and `-f` would fight a deliberate `.gitignore` entry, which the git
safety protocol says not to do without being asked). The spec-defects.md edit was made as
instructed but will not appear in `git status` or the commit; only `src/publishable/
validate.py` and `tests/test_validate.py` are tracked changes to commit.
