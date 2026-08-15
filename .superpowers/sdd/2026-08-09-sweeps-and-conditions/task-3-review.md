# Task 3 review: retire one refusal, add four

## Verdicts

- **Spec compliance: ✅**
- **Task quality: approved**

## What was checked

**The core question — what now validates clean and does nothing.** Before this diff
(`e2c9a21`), `SWEEP_AXIS_KEYS` included `baseline` and `grid` alongside the four
unimplemented modes, so declaring `sweep.grid` tripped the blanket `E-SWEEP-UNSUPPORTED`
even though `src/publishable/sweep.py::expand` (landed in `919e128`) already executes it,
and that expansion is wired into `cli.py`/`run_record.py`, not dead code. The diff's actual
job is narrower than "add four refusals" — it also *stops* refusing two modes that were
already safe to run. Confirmed `expand()` handles `baseline` and `grid` for real, so lifting
the refusal for those two does not open a silent-no-op path. The four new refusals
(`paired`, `ablate`, `sample`, `groups`) are structurally independent `if sweep.get(mode):`
branches — one per mode, each with its own code — so there is no shared conditional a typo
could route through, and no way for one mode's declaration to satisfy or suppress another's
check.

**Shape guard.** `_check_shape` runs first (`validate_config` returns `None` when it fails,
before `_check_unimplemented` is ever called) and covers `sweep` as a whole via
`_MAPPING_BLOCKS`. The diff adds no second guard inside the loop — correct, since a
non-mapping `sweep` never reaches this code, and a within-block garbage value (e.g.
`sweep.paired: "oops"`) still correctly refuses via the truthy check even though nothing
validates *its* shape (that's the same pre-existing, correctly-scoped gap the report flags,
not a new one).

**Message register vs. `docs/reference.md`.** Grepped `E-SWEEP` across all four documents —
zero hits, confirming these four (and the pattern's precedent, `E-REPL-ORDER-UNSUPPORTED`,
`E-DATA-RESOLVER-UNSUPPORTED`) are correctly absent from § Errors core raises: that section
is explicitly the raise-time `ContractError`/`ArtifactError` hierarchy only
("covers exactly the run-time surface, where there is a step to raise into"), and `validate`
findings are diagnostics, not raises. No duplicate-code-different-wording risk, because no
prior code claims this space. The four messages in the diff are verbatim what the brief
specified; nothing paraphrased or drifted.

**The retired identifier.** `SWEEP_AXIS_KEYS` is gone with no orphaned references anywhere
in `src/`, `tests/`, or `docs/`. `E-SWEEP-UNSUPPORTED` appears nowhere. Docstring updated
accurately — no longer claims "hardcodes one condition," and the `as_declared` repeats
sentence the report says was dropped-then-restored is present in the current file.

**Task 4's assignment (`E-SWEEP-KEY-UNKNOWN`).** Confirmed genuinely absent, not
half-done: no code anywhere validates `sweep`'s own key set against the six-key closed set,
so `sweep: {gird: {...}}` validates clean both before and after this diff. Correctly flagged
rather than fixed — it's a shape/typo-detection concern, orthogonal to
`_check_unimplemented`'s job of refusing *known, unimplemented* modes.

**Tests as evidence, not just presence.** Walked through what would break under plausible
mutations:
- Swapping which code fires for which mode (e.g. assigning the `ablate` code to the `paired`
  branch): caught by `test_each_unimplemented_mode_is_refused_on_its_own`, since each
  parametrize case declares exactly one mode and asserts exactly its own code appears —
  a swapped pairing produces a different code than asserted, and the wrong one showing up
  isn't checked for but the right one's absence is, which is sufficient to fail.
- A refusal firing on `is not None` instead of truthiness (over-firing on `paired: []`,
  `ablate: None`): caught by `test_an_empty_or_null_mode_is_not_a_declaration`, which sets
  all four modes to their falsy generated-by-`init` shapes at once and asserts no
  `-UNSUPPORTED` code appears.
- Omitting one mode from the loop entirely: caught by the same parametrized test, which
  covers all four independently.
- A message that scolds instead of defers, or drops the "later slice" language: caught by
  `test_every_sweep_refusal_message_defers_rather_than_scolds`.
- `baseline`/`grid` accidentally still refused, or accidentally added to the four-mode loop:
  caught by `test_baseline_and_grid_are_now_accepted`, and structurally impossible per the
  diff since `baseline`/`grid` are not in the four-tuple at all.

One test gap worth naming for the record, not a blocker: no test declares *two* unimplemented
modes at once (e.g. `paired` and `groups` together) and asserts both codes fire independently
without cross-suppression. Given the loop's structure (four independent `if` statements over
distinct keys, no shared state, no `return`/`break`), this is not exploitable — but it is the
one plausible defect class the current test suite doesn't exercise directly.

**Mechanical verification (re-confirmed, matches prior run).** `uv run ruff check` clean on
both changed files; `uv run pytest tests/test_validate.py -k sweep -q` → 7 passed.

**Scope of the commit.** `docs/superpowers/` and `.superpowers/sdd/` are gitignored by
design in this repo; the report's explanation for why only `validate.py` and
`test_validate.py` are tracked is correct, not an omission.

## Findings

None — no Critical or Important findings. The one gap noted above (no combined-declaration
test) is Minor and does not block approval given the loop's structural independence.
