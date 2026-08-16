# Task 13 report: realize the holdout once in `cli.command_run`

## Status

DONE

## What was built

`src/publishable/cli.py`: added `HoldoutPlan`, `holdout_for`, `holdout_seed_for` to the
`publishable.units` import list. Added `_resolved_holdout(units_decl, roster, digest, clusters)
-> HoldoutPlan | None`, placed immediately after `_resolved_group_axes` and before `_cond_roster`,
verbatim from the brief. In `command_run`, immediately after the
`group_axes = _resolved_group_axes(...)` line, added
`holdout_plan = _resolved_holdout(units_decl, roster, digest, clusters)`. `holdout_plan` is
unused at this commit (task 14 consumes it), so `ruff` flags it as F841 — confirmed by removing
the suppression and re-running `ruff check` — and I marked it with a narrow `# noqa: F841`
naming what consumes it next, per the brief's Step 4 instruction.

**The digest local passed is `digest = design_digest(doc)`** (`cli.py` line 1199, "phase 5: pin
hashes"), the same local `_resolved_group_axes` and `resolve_repeats` already consume — not a
neighbour. Confirmed by reading the function body between the `digest = design_digest(doc)`
assignment and the `group_axes = _resolved_group_axes(...)` call: no other `digest`-named local
is introduced in between, and `_resolved_holdout` is called with that same name in the same
scope, three lines after `_resolved_group_axes`'s call using it.

`tests/test_cli.py`: added `_resolved_holdout` to the `publishable.cli` import list (no collision
— grepped for `_cli_roster` first, per the standing warning; it does not exist elsewhere in the
file). Appended `_cli_roster` and three tests verbatim from the brief, at the end of the file:

- `test_the_holdout_is_realized_once_and_returns_none_when_undeclared`
- `test_the_realized_holdout_uses_the_derived_seed_and_the_cluster_map`
- `test_a_pinned_holdout_seed_reaches_the_realization`

## Test summary

`uv run pytest` — 1927 passed, 2 xfailed (1924 + 3 new). `uv run ruff check .` and `uv run mypy`
clean. `uv run ruff format --check .` (run scoped to `src/publishable/cli.py` and
`tests/test_cli.py` only, per the standing "never run ruff format bare" instruction) shows the
same pre-existing drift confirmed present on the pre-task commit (`git stash` + re-check) —
nothing this task introduced changed that baseline.

## Mutations — four run, not two

All reverted by editing the file back (never `git checkout --` on `cli.py`); each revert verified
by re-running the targeted test, `__pycache__` deleted between runs, and a final `diff` against
a pre-mutation backup copy of `cli.py` confirmed byte-identical restoration before commit.

**(a)** brief's — `if not isinstance(block, dict) or not block:` → `if not isinstance(block, dict):`.
Result: **FAIL**, exactly as predicted —
`test_the_holdout_is_realized_once_and_returns_none_when_undeclared` failed, but not with an
assertion failure: the `{"holdout": {}}` row now reaches `holdout_for`, whose `block["method"]`
lookup on an empty dict returns `None`, and `None` is not in `HOLDOUT_METHODS_REALIZED`, so it
raised `NotImplementedError` inside the test (`data.units.holdout.method: None is not realized
here`). The test still fails under this mutation, consistent with the brief.

**(b)** brief's — dropped `clusters=clusters` from the `holdout_for` call.
Result: **FAIL** — `test_the_realized_holdout_uses_the_derived_seed_and_the_cluster_map` failed
on its clustered assertion: `clustered == holdout_for(roster, decl["holdout"], seed=seed,
clusters=clusters)` compared unequal (`train`/`test` tuples differ — the mutated `_resolved_holdout`
now returns the unclustered draw for both calls).

**(c)** mine — made the composition derive the seed unconditionally, ignoring a pin: called
`holdout_seed_for({k: v for k, v in block.items() if k != "seed"}, digest, roster)` instead of
`holdout_seed_for(block, digest, roster)`.
Result: **FAIL** — `test_a_pinned_holdout_seed_reaches_the_realization` failed:
`plan.seed == 4321` was false (`2650036925 == 4321`). Confirmed the docstring's claim that this
mutation "would pass every other assertion in the file" — re-ran the other two tests under this
same mutation and both passed.

**(d)** mine — deleted the `roster is None` guard (the `if roster is None: return None` at the
top of `_resolved_holdout`).
Result: **FAIL**, but *not* by the last assertion of
`test_the_holdout_is_realized_once_and_returns_none_when_undeclared` returning a non-`None`
value — the call `_resolved_holdout({"holdout": {"method": "random", "frac": 0.2}}, None,
"sha256:aaa", None)` instead **raises** `TypeError: 'NoneType' object is not iterable` inside
`units.units_hash`, because `holdout_seed_for` iterates `roster` before `holdout_for` is even
reached. So this mutation discriminates the test, but for a different reason than a wrong return
value: the guard's removal surfaces as a crash three calls deep rather than as a returned
`HoldoutPlan`, confirming the brief's "check this can discriminate before trusting it" concern —
it does discriminate, just not via the mechanism a naive reading of the assertion would suggest.

## Where the brief disagreed with the code

None found. `holdout_for`'s signature, raise conditions (`ContractError`/`E-DATA-HOLDOUT-EMPTY`,
`NotImplementedError` for unrealized methods), and `holdout_seed_for`'s pin predicate
(`isinstance(seed, int) and not isinstance(seed, bool)`) all matched the brief's description
exactly, verified by reading `src/publishable/units.py` before writing the composition. The
`digest` local at the call site in `command_run` is `design_digest(doc)`, matching what task 12's
reviewer asked to have confirmed.

## Process notes

`.superpowers/sdd/.gitignore` was clobbered to a bare `*` (the standing `scripts/sdd-workspace`
behavior). Restored via `git checkout -- .superpowers/sdd/.gitignore` before committing — safe
here because that file had no uncommitted content of its own being destroyed; it reverted the
auto-clobber back to the last commit's tracked content.
