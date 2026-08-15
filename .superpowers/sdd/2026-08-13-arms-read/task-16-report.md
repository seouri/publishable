# Task 16 report — the `assign.seed` digest fix

## What was done

`hashes.design_digest` canonicalised `data.units` wholesale, so a pinned `assign.seed` moved
the digest it is itself derived from — the exact self-referential defect
`docs/reference.md` § What `auto` derives from already documented as excluded ("`data.units`
(every field except `assign.seed` itself) and `sweep.groups`").

Added `_units_excluding_assign_seed(units)` in `src/publishable/hashes.py`: given `data.units`,
it drops `seed` from each `assign.<axis>` block — per axis, not the whole `assign` subtree and
not just the first axis found — leaving every other field (`method`, `from`, `stratify_by`,
`ratio`, `block_size`) inside. `design_digest` now calls it before canonicalising.

Per the addendum's correction, the function never raises on a shape it does not expect: a
non-mapping `units`, a non-mapping `assign`, or a non-mapping axis block is returned/kept as
given rather than unpacked with `.items()`. This matters because `validate` reaches
`design_digest` indirectly (via `expand` → `sweep.sample_seed_for`'s `auto` path) before a
config is known to be well-formed, and the addendum flagged that a naive per-axis carve-out
would raise `AttributeError` there (uncaught by `sweep.py`'s existing `except TypeError`).
Guarding by `isinstance` throughout avoids needing any new exception handling in `sweep.py`.

## Tests added (`tests/test_hashes.py`)

- `test_design_digest_excludes_assign_seed_with_a_control` — reseeding `assign.arm.seed`
  doesn't move the digest; changing `data.units.key` does (control).
- `test_design_digest_exclusion_is_surgical_not_the_whole_assign_block` — three cases the
  addendum required, each of which **must** move the digest: `assign.arm.from` changing,
  `assign.arm.stratify_by` changing, and adding a second axis to `assign`. Without these,
  "excluded `assign.seed`" and "excluded `assign`" (or "excluded `data.units.assign`") would be
  indistinguishable — a mutation that drops the whole block would still pass the first test.
- `test_design_digest_exclusion_is_per_axis_not_first_found` — a second axis's own `seed`
  changing must **not** move the digest either, proving the drop is per-block rather than
  "clear the first `seed` key encountered".
- `test_design_digest_does_not_raise_on_malformed_assign_shapes` — non-mapping `assign`,
  non-mapping axis block, non-mapping `units`, and a `seed: None` value all pass through
  `design_digest` without raising.

## Mutation testing

Mutated `design_digest` to use the raw (unfiltered) `units` instead of the carved-out version
(i.e., reverted the fix in place). Result: the two seed-exclusion tests
(`test_design_digest_excludes_assign_seed_with_a_control`,
`test_design_digest_exclusion_is_per_axis_not_first_found`) failed; the control-shaped tests
(`test_design_digest_exclusion_is_surgical_not_the_whole_assign_block`,
`test_design_digest_does_not_raise_on_malformed_assign_shapes`) still passed — confirming the
controls are independent of the thing under test, as the addendum required. Deleted
`__pycache__` between mutation and revert; reverted by restoring the file from a saved copy and
re-running the full `test_hashes.py` suite (all 14 tests passing) rather than trusting
`git status`.

## Digest literal check

Checked as instructed: no test in the repo pins a `design_digest`/`sweep.yaml` digest value as a
literal string. The three tests that touch digests (`test_design_digest_covers_units_and_groups_only`
plus the two I added under that name category) compare digests computed twice within the test,
never against a hardcoded hex string. Confirms the addendum's own claim; no expected-string
updates were needed anywhere in the suite.

## Full verification

- `uv run pytest` — 1486 passed, 2 xfailed.
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — success, no issues in 40 source files.
- Did **not** run `ruff format .` (out of scope per instructions).

## Documentation

`docs/reference.md` § What `auto` derives from already stated the post-fix behavior verbatim
(confirmed against task 1's decision) — no doc edit was needed or made there.

Marked the matching entry in `docs/superpowers/spec-defects.md` ("`design_digest` includes
`assign.seed`...") as `RESOLVED (H3c-1, task 16)`, with a closing note describing the fix,
consistent with how other closed entries in that file are recorded. That file is gitignored
(`docs/superpowers/` is in `.gitignore`), so this edit is not part of the commit and has no
bearing on the tracked-repo diff — noting it here since the brief's global constraints ask for
grepping tracked `*.md` after removing/renaming strings; nothing tracked needed updating.

The entry's own "one field over" note (`data.units.holdout.seed` has the same latent defect,
scoped to a `NOT BUILT` feature) is left open and unaddressed — it belongs to whatever future
slice builds `data.units.holdout`, not this task.

## Concerns / defects found in the brief or addendum

None that block the task. Both documents' factual claims held up under verification:

- "No test pins a digest literal" — verified true.
- `validate`'s only path to `design_digest` is via `expand` → `sample_seed_for`, and only when
  `sweep.sample` is declared with an `auto` seed — confirmed by reading `sweep.py`.
- The addendum's self-correction (AttributeError vs. TypeError) was itself correct, and the
  chosen implementation strategy (guard by shape, never call `.items()` on anything not
  verified to be a `dict`) sidesteps the need for `sweep.py` to catch a new exception type at
  all — I did not need to touch `sweep.py`.

One minor observation, not a defect: the brief's Step 2–6 checklist ("Fail, implement, pass,
mutate, commit") reads as a single task, and the addendum's five required cases (assign.seed
control, `from`, `stratify_by`, second axis, second-axis-seed-not-first-found) map cleanly onto
that without tension. Nothing in either document needed to be reopened.

Task 16b (the contrast-refusal task) is out of scope for this report — it has its own
`task-16b-addendum.md` in this directory and was not touched.

## Status

DONE.
