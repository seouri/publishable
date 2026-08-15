# Task 2 report: `paired` joins the product

## Fail-then-pass evidence

**Step 2 (write the failing test, then run it):**

```
$ uv run pytest tests/test_sweep.py::test_paired_is_one_axis_not_a_product_of_its_keys -v
...
>       assert len(conditions) == 4
E       AssertionError: assert 2 == 4
E        +  where 2 = len([Condition(index=0, label='method=pearson', ...), Condition(index=1, label='method=spearman', ...)])
FAILED tests/test_sweep.py::test_paired_is_one_axis_not_a_product_of_its_keys
1 failed in 0.04s
```

Confirmed FAIL for the stated reason: `_axes` ignores `paired`, so only the 2-value `grid` axis expands.

**After adding the axis (Step 3):**

```
$ uv run pytest tests/test_sweep.py -v
... 28 passed in 0.04s
```

## What was added

### `_axes` (`src/publishable/sweep.py`)

```python
    paired = sweep.get("paired") or []
    if paired:
        # One axis, not one per key: a paired entry is a single setting that
        # happens to set several paths. Treating its keys as separate axes is
        # exactly the combinatorial reading § Expansion modes rejects.
        axes.append([dict(entry) for entry in paired])
    return axes
```

Appended after the grid loop, exactly as the brief specified: `paired` contributes **one** axis whose cells are the whole entry dicts (not one axis per key), so `grid × paired = 2 × 2 = 4`, never `2 × 2 × 2`.

### `_swept_paths` (`src/publishable/sweep.py`)

Extended to walk every `paired` entry's keys, adding each path at most once, in first-seen order:

```python
    paths = list(sweep.get("grid") or {})
    for entry in sweep.get("paired") or []:
        for path in entry:
            if path not in paths:
                paths.append(path)
    return paths
```

Verified the dedup is load-bearing, not defensive dead code, with a dedicated test (`test_swept_paths_lists_a_paired_path_once_even_when_every_entry_names_it`): the brief's own example has `analysis.min_samples` and `analysis.confidence` recurring across both `paired` entries, and without the `if path not in paths` guard they would be appended twice — which would make `_keys_for` compare a path against itself (trivially "unique" since its own `p != path` filter excludes it), silently under-disambiguating any other path sharing that suffix.

Also added a label assertion to the axis test, pinning `_keys_for`'s output over the combined grid+paired swept set:

```
method=pearson__min_samples=30__confidence=0.95
method=pearson__min_samples=50__confidence=0.99
method=spearman__min_samples=30__confidence=0.95
method=spearman__min_samples=50__confidence=0.99
```

Computed directly and matches what the test now asserts:

```
$ uv run python -c "
from publishable.sweep import expand
conds = expand({'sweep': {'grid': {'analysis.method': ['pearson','spearman']}, 'paired': [{'analysis.min_samples':30,'analysis.confidence':0.95},{'analysis.min_samples':50,'analysis.confidence':0.99}]}})
for c in conds: print(c.index, c.label, dict(c.values))
"
0 method=pearson__min_samples=30__confidence=0.95 {...}
1 method=pearson__min_samples=50__confidence=0.99 {...}
2 method=spearman__min_samples=30__confidence=0.95 {...}
3 method=spearman__min_samples=50__confidence=0.99 {...}
```

`docs/reference.md` § Expansion modes and § How artifacts are organized show no directory-name example specific to a `grid × paired` composition to check this against, so this is pinned by the test rather than by a pre-existing document figure; no discrepancy found (none of the three paths share a leaf, so all three keep their shortest suffix — the "shared leaf forces a longer key" case doesn't arise here).

## Grep for `E-SWEEP-PAIRED-UNSUPPORTED`

```
$ grep -rn "E-SWEEP-PAIRED-UNSUPPORTED" src/ tests/ docs/ README.md
src/publishable/validate.py        (before edit — refusal tuple, now removed)
tests/test_validate.py             (before edit — 2 parametrize rows, now removed)
docs/superpowers/spec-defects.md                              (3 hits — historical, untouched)
docs/superpowers/plans/2026-08-09-sweeps-and-conditions.md    (multiple — historical, untouched)
docs/superpowers/specs/2026-08-09-sweeps-and-conditions-design.md:65  (design table row — historical, untouched)
docs/superpowers/plans/2026-08-12-sweep-expansion-modes.md    (this task's own plan text — untouched)
```

**Zero hits in the four documents** (`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`) or in `CLAUDE.md`. This confirms the brief's expectation: standing policy keeps `-UNSUPPORTED` codes out of the four documents (`reference.md`: "That whole family is deliberately absent from the validate-time registry"), so there was **no error-table row to remove** — the code only ever appeared in `src/`, `tests/`, and non-normative planning/history docs under `docs/superpowers/`, which this task leaves alone (they are historical records of prior slices, not the four documents governed by the cross-document consistency pass — rewriting them would misrepresent what those slices actually did at the time).

**What was removed/changed, by location:**

- `src/publishable/validate.py`: the `("paired", "E-SWEEP-PAIRED-UNSUPPORTED", "couples parameters into one axis")` tuple removed from `_check_unimplemented`'s refusal loop. Docstring and per-refusal message text updated from "expands `sweep.baseline` and `sweep.grid` only... `sweep.paired`, `.ablate`, `.sample`, and `.groups` are read by nothing yet" to "expands `sweep.baseline`, `sweep.grid`, and `sweep.paired` only... `.ablate`, `.sample`, and `.groups` are read by nothing yet", and the per-mode error message's "this build expands `baseline` and `grid` only" to "...`baseline`, `grid`, and `paired` only".
- `tests/test_validate.py`: removed the `paired` row from `test_each_unimplemented_mode_is_refused_on_its_own`'s parametrize list and from `test_every_sweep_refusal_message_defers_rather_than_scolds`'s loop. Added `test_paired_is_accepted_and_expands_for_real` (Step 5): asserts `E-SWEEP-PAIRED-UNSUPPORTED` is absent and no `E-SWEEP*` code fires for a `grid` + `paired` config.
- `docs/reference.md`: removed the `NOT BUILT` marker from the `sweep.paired` line in § The one config file's config example (`paired: []  # NOT BUILT; optional coupled settings, ...` → `paired: []  # optional coupled settings, ...`), and updated "Fourteen declarations above are not yet built... `sweep.groups`, `sweep.paired`, `sweep.ablate` and `sweep.sample`..." to "Thirteen declarations..." with `sweep.paired` dropped from the enumerated list. Recount: 4 sweep entries → 3 (`groups`, `ablate`, `sample`) + 5 `data.units` fields + 1 resolver form + 1 non-`within` allocation + 1 `stratify_by` + 2 `statistics` blocks = 13. The § Expansion modes narrative (lines ~1505–1538) already described `paired` as a fully working, composing mode with no `NOT BUILT` marker there — it needed no change. Grepped both documents afterward for any other place claiming "expands `baseline` and `grid` only" or similar — none found outside the two spots just fixed.

## A gap the `paired` change opened, found and closed (not in the original brief)

The brief's four steps cover `_axes`, `_swept_paths`, and the refusal retirement, but not `E-SWEEP-BASELINE-PARTIAL` — the check in `_check_unimplemented` refusing a baseline that fixes only *some* swept axes (because `expand` emits a single `00_baseline` row, so an unfixed axis means the declared design isn't the executed one). Before this task, that check computed `unfixed` over `sweep.get("grid")`'s keys only, which was complete: `grid` was the only axis-shaped mode that actually expanded.

Once `paired` composes into the same product as a real axis, that check's grid-only computation is no longer complete: a config declaring `baseline: {analysis.method: pearson}` plus the brief's own `paired` example validated clean (no `E-SWEEP-BASELINE-PARTIAL`) while `expand` still emitted a single `00_baseline` that fixes neither `analysis.min_samples` nor `analysis.confidence` — the exact declared-vs-executed mismatch the check exists to catch, just via a different axis-shaped mode than the one it was written to watch.

Checked the full plan (`docs/superpowers/plans/2026-08-12-sweep-expansion-modes.md`) for task ownership before fixing this: Task 6 ("The baseline expands over unfixed axes") is where full per-cell baseline *expansion* lands, and Task 7 is where `E-SWEEP-BASELINE-PARTIAL` itself is retired — neither is about keeping the existing refusal's `unfixed` computation correct against the axes this build already supports in the meantime. Since Task 2 is what turned `paired` into a real supported axis, and the file is already open for other reasons, fixed it here rather than leaving the introduced hole for four tasks:

```python
baseline = sweep.get("baseline") or {}
unfixed = [path for path in _swept_paths(sweep) if path not in baseline]
```

(`_swept_paths` imported from `publishable.sweep` alongside the existing `check_swept_value`, `expand` import.) This is a minimal, mechanical fix — reading the same "every axis-shaped mode's paths" set `_swept_paths` already exists to provide — not an implementation of per-cell expansion, which stays Task 6's job.

**Deliberately left untouched:** `W-SWEEP-BASELINE-CONFOUNDED`'s emit site (a different function, further down in `validate.py`) still computes `swept_axes = list(grid)` — `grid`-only, unchanged. The plan explicitly assigns re-reading that exact warning to Task 7 ("H1's review ruled 'do not touch row 271' explicitly because H2 would make its remedy expressible... Read the row and the warning's emit site... **Do not weaken the warning itself**"), and its own surrounding comment documents that the narrower-than-run-time `grid`-only scope there is deliberate until `E-SWEEP-BASELINE-PARTIAL` is retired. Widening it now would be exactly the premature move that comment warns against.

Added two tests pinning both directions:
- `test_a_baseline_that_leaves_a_paired_axis_free_is_refused` — the failure mode above, refused.
- `test_a_baseline_fixing_every_axis_including_paired_is_supported` — the mirror case, where the baseline names every grid and paired path, stays clean.

Mutation-tested this fix the same way as the two required mutations: reverted `_swept_paths(sweep)` back to `sweep.get("grid") or {}` and re-ran the new refusal test —

```
$ uv run pytest tests/test_validate.py::test_a_baseline_that_leaves_a_paired_axis_free_is_refused -v
>       assert "E-SWEEP-BASELINE-PARTIAL" in found
E       AssertionError: assert 'E-SWEEP-BASELINE-PARTIAL' in {}
FAILED
```

then reverted back to `_swept_paths(sweep)` and confirmed `git diff --stat src/publishable/validate.py` showed the fix restored (17 insertions / 13 deletions against the pre-task-2 file, matching the intended diff) and the full suite green again.

## Mutation table (brief's required mutations, on `_axes`)

| Mutation | Applied to | Test run | Observed result |
|---|---|---|---|
| `_axes` appends `paired` as one axis **per key** instead of one axis total | `src/publishable/sweep.py` `_axes` | `pytest tests/test_sweep.py::test_paired_is_one_axis_not_a_product_of_its_keys -v` | **FAILED**: `assert len(conditions) == 4` → `AssertionError: assert 8 == 4` (2 grid × 2 min_samples-values × 2 confidence-values = 8 conditions, each carrying only one of the two paired keys per axis) |
| `_axes` appends nothing for `paired` (the pre-task behavior) | `src/publishable/sweep.py` `_axes` | same command | **FAILED**: `assert len(conditions) == 4` → `AssertionError: assert 2 == 4` (only the grid axis expands) |

Both mutations were applied one at a time via `Edit`, run, confirmed to fail for the expected reason, then reverted with `Edit` back to the exact original text. After each revert, `git diff --stat` was checked and showed only the five intended files (`docs/reference.md`, `src/publishable/sweep.py`, `src/publishable/validate.py`, `tests/test_sweep.py`, `tests/test_validate.py`) with no stray mutation residue — `git status --porcelain` was not meaningfully checkable mid-task since those five files are legitimately modified and uncommitted throughout; the emptiness check that matters (no *extra* diff beyond the intended change) was done via `git diff --stat` comparison instead, and confirmed clean both times.

## Full verification

```
$ uv run pytest
960 passed in ~50-58s

$ uv run ruff check .
All checks passed!

$ uv run mypy
Success: no issues found in 40 source files
```

**Correction (review follow-up):** the arithmetic explanation above was wrong. `pytest`'s parametrize rows **are** separately collected test cases — removing the `paired` row from each of the two parametrized tests (`test_each_unimplemented_mode_is_refused_on_its_own`, `test_every_sweep_refusal_message_defers_rather_than_scolds`) dropped one collected test, not zero. The correct reconciliation is 956 − 1 + 5 = 960, which matches the observed count exactly. (The reviewer verified this independently and confirmed it reconciles.)

`E-SWEEP-GROUPS-UNSUPPORTED` was left untouched in the refusal loop (only the `paired` tuple was removed from it) and confirmed still firing:

```
$ uv run pytest tests/test_validate.py -k "groups" -v
tests/test_validate.py::test_each_unimplemented_mode_is_refused_on_its_own[groups-value2-E-SWEEP-GROUPS-UNSUPPORTED] PASSED
1 passed, 256 deselected
```

## Mechanical pass on the `docs/reference.md` edit

Per CLAUDE.md, ran after the doc edit:

```
$ grep -rn "and \`grid\` only\|baseline\` and \`grid\`\|not yet built" docs/reference.md docs/design-principles.md docs/experimental-designs.md README.md
```

Only hit relevant to this change was the "Fourteen declarations" sentence itself, already fixed to "Thirteen"; the other `not yet built` hits are unrelated module/CLI rows (§ Package layout, § The importable surface) using the same phrase for a different concept (unbuilt modules, not unbuilt config declarations) and don't need to change. No trailing whitespace or tabs on either touched line (`paired: []` line, "Thirteen declarations" paragraph) — checked directly.

## Files touched

- `src/publishable/sweep.py` — `_axes`, `_swept_paths`
- `src/publishable/validate.py` — `_check_unimplemented` (refusal tuple removed, docstring and message text updated, `unfixed` computation widened from `grid` to `_swept_paths(sweep)`); new import of `_swept_paths`
- `tests/test_sweep.py` — `test_paired_is_one_axis_not_a_product_of_its_keys` (with label assertion), `test_swept_paths_lists_a_paired_path_once_even_when_every_entry_names_it`
- `tests/test_validate.py` — 2 parametrize rows removed, `test_paired_is_accepted_and_expands_for_real`, `test_a_baseline_that_leaves_a_paired_axis_free_is_refused`, `test_a_baseline_fixing_every_axis_including_paired_is_supported`
- `docs/reference.md` — `NOT BUILT` marker removed from `sweep.paired`; "Fourteen declarations" → "Thirteen declarations", `sweep.paired` dropped from the enumerated list

## Anything questionable

1. **`docs/superpowers/*` still name `E-SWEEP-PAIRED-UNSUPPORTED` extensively** (`spec-defects.md`, the two plan/spec files under `plans/`/`specs/`). These are historical records of prior slices' plans and defect logs, not the four normative documents — CLAUDE.md's cross-document consistency pass does not govern them, and rewriting history there would misrepresent what those slices actually did at the time. Left untouched deliberately.
2. **`paired` entries get no per-entry validation in `_check_sweep`** — no `E-SWEEP-PATH-UNKNOWN` if a paired entry names a parameter the template doesn't declare, no `E-PARAM-VALUE` if a value fails its `Param`'s own check, no `E-SWEEP-VALUE-UNNAMEABLE` if a value would break the `__` label separator. `grid` gets all three (`_check_sweep`, the `grid.items()` loop). Checked both the task-2 brief and the full plan's Task 2 section explicitly — neither lists any of these three checks for `paired`, and no later task in the plan claims them either (`grep -n "paired" plans/2026-08-12-sweep-expansion-modes.md` shows `paired` named only in Task 1's composition table and Task 2 itself). This looks like a genuine gap across the whole plan rather than a deferred-to-a-later-task item, but implementing it wasn't part of this task's stated interface (`Produces: nothing new`) and no test in the brief calls for it, so I did not add it — flagging it here rather than silently expanding scope. If it's wanted, the natural home is a loop next to the existing `for path, values in grid.items():` block in `_check_sweep`, iterating `sweep.get("paired") or []` and calling `_path_resolves`/`_value_checks` (with `nameable=True`) per entry per key.
3. **Fixed one gap not in the brief**: `E-SWEEP-BASELINE-PARTIAL`'s `unfixed` computation was `grid`-only and became incomplete once `paired` started composing as a real axis (see section above) — widened it to `_swept_paths(sweep)`, added two tests, mutation-tested the fix, and confirmed `W-SWEEP-BASELINE-CONFOUNDED` (explicitly assigned to Task 7, "do not touch") was left untouched.

---

## Review follow-up (commit `54cdac7`)

Task review came back spec-not-met: one Critical, three Important, three Minor. Addressed all seven; commit `54cdac7` stacks on `268f37c`.

### What the review upheld

The `E-SWEEP-BASELINE-PARTIAL` widening (item 3 above) was confirmed correct on all three counts the reviewer checked: the grid-only computation genuinely gives `unfixed == []` on a `grid`+`paired` baseline that fixes only `grid`, the hole was genuinely unreachable before this task (so this task caused it), and deferring the fix to Task 6/7 would have been wrong — four tasks of a silently-wrong design running. `paired`-is-one-axis, `_swept_paths` ordering, and the 13-count doc edit were each independently re-verified by the reviewer and confirmed correct.

**Correction to my own report:** my explanation of "956 → 960" above was wrong. Parametrize rows *are* separately collected pytest cases — removing the `paired` row from `test_each_unimplemented_mode_is_refused_on_its_own` (a `@pytest.mark.parametrize` test) dropped one collected test, not zero. `test_every_sweep_refusal_message_defers_rather_than_scolds` is a *different* shape — a single test with an internal Python `for` loop, not `@pytest.mark.parametrize` — so removing one loop iteration there changes 0 collected tests. Correct reconciliation: 956 − 1 (dropped parametrize case) + 5 (new test functions) = 960. Matches observed exactly; the reviewer verified this independently too.

### Critical — a malformed `paired` validated clean and crashed `run`

Reproduced the reviewer's exact repro before fixing: `sweep: {grid: {...}, paired: ["notadict"]}` gave zero `validate_config` findings, and `expand(doc)` raised `ValueError: dictionary update sequence element #0 has length 1; 2 is required` from `dict(entry)` inside `_axes`'s `paired` branch — a bare, uncoded exception past `main`'s `PublishableError`/`OSError` handler. This is the same class of hole `ad6cf3d` closed for `sweep.grid`/`sweep.baseline`, reopened for `sweep.paired` by this task, exactly as the review said.

**Fix**, in `_check_shape` (`src/publishable/validate.py`), beside the existing `sweep.grid` guard:

```python
paired = sweep.get("paired")
if paired is not None and not isinstance(paired, list):
    _bad("sweep.paired", paired, "list")
elif isinstance(paired, list):
    for i, entry in enumerate(paired):
        if not isinstance(entry, dict):
            _bad(f"sweep.paired[{i}]", entry, "mapping")
```

One deliberate divergence from the `grid`-axis-value pattern I copied it from: a `grid` axis value is allowed to be `null` (treated as a param-value question, not a shape one, since the value is used as-is), but a `paired` entry is fed straight into `dict()`, so `dict(None)` itself is the crash — writing `entry is not None and not isinstance(...)` (my first draft) would have let `paired: [None]` straight through to the same `TypeError`. Caught this against my own draft by actually running `expand({"sweep": {"grid": {...}, "paired": [None]}})` before trusting the guard, saw `TypeError: 'NoneType' object is not iterable`, and dropped the `entry is not None` exception.

Four new tests: `test_a_non_list_paired_is_a_diagnostic_not_a_traceback`, `test_a_paired_entry_that_is_not_a_mapping_is_a_diagnostic_not_a_traceback` (the reviewer's exact repro), `test_a_null_paired_entry_is_a_diagnostic_not_a_traceback`, `test_a_null_whole_paired_block_is_absent_not_malformed` (the block-level `sweep.paired: null` case, which correctly stays absent-not-malformed, distinct from a `null` *entry inside* a present list).

### Important — `grid`/`paired` naming the same path silently duplicated conditions

Reproduced first: `grid: {analysis.min_samples: [30, 50]}` + the brief's own `paired` example (both entries also naming `analysis.min_samples`) gave 4 conditions from `expand`, but `expand`'s product loop applies each axis's cell to `values` in declared order (`for cell in combo: values.update(cell)`), and `paired` is always appended after `grid` in `_axes` — so `paired`'s value for the shared path always wins, and grid=30/paired-entry-30 and grid=50/paired-entry-30 both resolve to the *same* `values` dict. Two of the four conditions were byte-identical, `validate_config` reported nothing, and `_condition_labels` (a `set`) structurally couldn't see the duplicate label either.

**Fix**: minted `E-SWEEP-PATH-DUPLICATE` (grepped `src/`, `docs/reference.md` first — no collision) in `_check_sweep`, refusing any path named by both `sweep.grid` and `sweep.paired`:

```python
paired_paths: dict[str, list[int]] = {}
for i, entry in enumerate(sweep.get("paired") or []):
    if isinstance(entry, dict):
        for path in entry:
            paired_paths.setdefault(path, []).append(i)
for path in sorted(set(grid) & set(paired_paths)):
    ...
    c.error("E-SWEEP-PATH-DUPLICATE", f"sweep.paired.{path}", ...)
```

Added the registry row to `docs/reference.md` § Validation's error table (alphabetically between `E-SWEEP-PATH-DUPLICATE` and the existing `E-SWEEP-PATH-UNKNOWN` — checked the existing rows are code-sorted before inserting). Filed the underlying underspecification — § Expansion modes never states a path belongs to at most one axis-shaped mode — as a new entry in `docs/superpowers/spec-defects.md` (gitignored, per this repo's rule for recording spec gaps), marked "partially closed": the refusal is in, the composition-rule sentence in § Expansion modes itself is left for Task 3 or Task 9, since both still have that section open for other reasons and the exact generalization (does this extend to `groups` once built?) is a real decision, not just wording.

Two new tests: `test_grid_and_paired_naming_the_same_path_is_refused` (asserts the finding's `path` is `sweep.paired.analysis.min_samples` — via `Collector`/`validate_config` directly rather than `messages_by_code`, since the path detail lives in `Finding.path`, not `.message`), and `test_grid_and_paired_on_disjoint_paths_is_not_a_duplicate` (the brief's own worked example, confirmed still clean).

### Important — `docs/reference.md` misdescribed the widened refusal

Fixed the `E-SWEEP-BASELINE-PARTIAL` error-table row: "leaves at least one of `sweep.grid`'s axes unfixed" → "leaves at least one of the swept axes unfixed", matching the code's actual (widened) behavior. One line, as the review said.

### Declined items, confirmed still correctly declined

The review explicitly agreed that `E-SWEEP-PATH-UNKNOWN`/`E-PARAM-VALUE`/`E-SWEEP-VALUE-UNNAMEABLE` for `paired` entries are plan-wide omissions, correctly left to a routed follow-up rather than invented here. No change made; item 2 in "Anything questionable" above stands.

### Three Minors

1. Reworded the widened baseline-partial check's comment: it's path-granular ("does every swept path have some baseline value"), not axis/cell-granular ("does the baseline supply a whole `paired` cell") — a baseline naming half of one `paired` entry's paths is refused pointing at the still-unfixed path, same as two independent `grid` axes, and a mix-and-match value that matches no declared `paired` cell is not itself caught by this check (that needs Task 6's actual per-cell resolution).
2. Fixed `_check_unimplemented`'s docstring: removed the mangled wrap (`It\n    resolves a\n    unit roster`) and merged the two separate mentions of `paired` no longer being refused into one paragraph that also names the new `_check_shape`/`E-SWEEP-PATH-DUPLICATE` guards.
3. Noted, not changed: `from publishable.sweep import _swept_paths` is this package's first cross-module import of a name with a leading underscore. Left as-is per the review's own call — Task 7 removes the only use when `E-SWEEP-BASELINE-PARTIAL` retires — but flagging it here so it isn't rediscovered as an oversight.

### Re-verification

```
$ uv run pytest
966 passed

$ uv run ruff check .
All checks passed!

$ uv run mypy
Success: no issues found in 40 source files
```

`E-SWEEP-GROUPS-UNSUPPORTED` reconfirmed firing:

```
$ uv run pytest tests/test_validate.py -k "groups" -v
tests/test_validate.py::test_each_unimplemented_mode_is_refused_on_its_own[groups-value2-E-SWEEP-GROUPS-UNSUPPORTED] PASSED
1 passed, 264 deselected
```

### Files touched in this follow-up

- `src/publishable/validate.py` — `_check_shape` (new `sweep.paired` container/entry guards), `_check_sweep` (new `E-SWEEP-PATH-DUPLICATE` refusal), `_check_unimplemented` (docstring cleanup), the widened baseline-partial check's comment (clarified path-vs-cell granularity)
- `tests/test_validate.py` — 6 new tests: `test_a_non_list_paired_is_a_diagnostic_not_a_traceback`, `test_a_paired_entry_that_is_not_a_mapping_is_a_diagnostic_not_a_traceback`, `test_a_null_paired_entry_is_a_diagnostic_not_a_traceback`, `test_a_null_whole_paired_block_is_absent_not_malformed`, `test_grid_and_paired_naming_the_same_path_is_refused`, `test_grid_and_paired_on_disjoint_paths_is_not_a_duplicate`
- `docs/reference.md` — `E-SWEEP-BASELINE-PARTIAL` row wording fixed; new `E-SWEEP-PATH-DUPLICATE` row added
- `docs/superpowers/spec-defects.md` (gitignored) — new entry recording the grid/paired path-collision underspecification, partially closed

---

## Second review follow-up (commit `1c5ed66`)

Scoped re-review: six of seven prior findings addressed; `E-SWEEP-PATH-DUPLICATE` and the `spec-defects.md` scoping were both specifically upheld (the reviewer traced `_axes` and confirmed grid axes are always appended before the single `paired` axis, so the row's claim about which mode's value wins is a structural fact, not an artifact of one example; and confirmed the two normal cases — two `paired` entries sharing a path with each other, and disjoint `grid`/`paired` paths — correctly stay silent).

**The Critical was only partly addressed — same class, reached one level deeper.** My `_check_shape` guard checked `isinstance(entry, dict)` but not each entry's *keys*. A `paired` entry with a non-string key is a well-formed `dict` (YAML permits `123: oops` and `1.5: oops` as mapping keys), so it passed the guard clean, then crashed in `_keys_for`'s `path.split(".")` — reproduced directly before fixing:

```
$ uv run python -c "
from publishable.sweep import expand
expand({'sweep': {'grid': {'analysis.method': ['pearson','spearman']}, 'paired': [{123: 30}, {123: 50}]}})
"
AttributeError: 'int' object has no attribute 'endswith'

$ uv run python -c "... 'paired': [{1.5: 30}, {1.5: 50}] ..."
AttributeError: 'float' object has no attribute 'endswith'
```

Both are the exact "validates clean, crashes `run` with a bare traceback" failure the original Critical named, through a different malformed shape.

**Fix, in `_check_shape`** — a third guard nested inside the entry-is-a-mapping branch:

```python
for key in entry:
    if not isinstance(key, str):
        _bad(f"sweep.paired[{i}]", key, "string")
```

**Route chosen, and why:** `E-CONFIG-SHAPE` (fatal), not `envelope.py`'s coerce-to-`str`-and-report route (`E-CONFIG-KEY-UNKNOWN`). Read `envelope.py:136-165` before deciding: its `_check_unknown_keys` faces the identical "YAML permits a non-string key" fact, and resolves it by coercing to `str` and reporting the coerced name as not matching the schema's known vocabulary — which works there specifically because every leaf sits under a **closed, known set of names** a coerced string can be compared against and reported as unmatched, with a `difflib` hint. A `paired` key is not a member of any closed set `_check_shape` knows: it's an open dotted path into `parameters`, and deciding whether a given *string* path resolves is `_check_sweep`'s job (`E-SWEEP-PATH-UNKNOWN`), reached only once the key is confirmed to be a string. Coercing a non-string key to `str` here and letting validation continue would just move today's crash one frame deeper (into `_check_sweep`, or `expand` if `_check_sweep` didn't crash first) with no reporting benefit — there's no known-name list to compare the coerced string against and no better message to give than "this must be a string." So it stays a shape fault, consistent with every other guard in `_check_shape` (container types, entry types), rather than adopting `envelope.py`'s route.

Two new tests, one per crash shape from the review: `test_a_paired_entry_with_a_non_string_int_key_is_a_diagnostic_not_a_traceback`, `test_a_paired_entry_with_a_non_string_float_key_is_a_diagnostic_not_a_traceback`.

### The two probes

**`paired: [{}, {"analysis.min_samples": 50}]` (an empty entry) — verdict: acceptable, no code change.** Ran it: no crash, four conditions, with the empty-entry cells' labels correctly omitting the component nothing sets (`method=pearson` vs `method=pearson__min_samples=50`). `label_for` iterates `values.items()`, not the full swept set, so a condition missing a swept path simply doesn't render that component — mechanically sound, and `_keys_for`'s suffix computation is unaffected since it disambiguates over the declared path set, independent of which conditions happen to populate each path. Semantically this is unusual but not invalid: an empty `paired` cell means "this arm of the coupled axis touches nothing," which is a legitimate (if easy to write by mistake) design — e.g., "compare the template's own defaults against one specific override," structurally different from `ablate`'s `1 + n` but reaching a similar comparison by hand. Nothing in § Expansion modes requires a `paired` cell to be non-empty, and `E-SWEEP-AXIS-EMPTY` refuses only a `grid` axis with **no cells at all** (an empty list), not a cell that is itself empty — a different condition. Left unrefused.

**`paired: [{"analysis.min_samples": {"a": 1}}, ...]` (a nested dict as a value) — verdict: a fault, but not a new one; it's the already-flagged plan-wide gap made concrete, and stays out of scope for the same reason it did before.** Ran it: no crash — `render_value` falls through to `str(value)` for anything that isn't `bool`/`float`, so the label component becomes `min_samples={'a': 1}` verbatim. Checked directly whether the label rules admit this: `check_swept_value({"a": 1})` returns `"swept value \"{'a': 1}\" does not match ^[A-Za-z0-9._+-]+$"` — so no, the rules do **not** admit it; this value would be refused as `E-SWEEP-VALUE-UNNAMEABLE` if the check ran. It doesn't run, because — as already recorded in "Anything questionable" item 2 above, and confirmed correctly declined by the first review — `_check_sweep` calls `_value_checks`/`check_swept_value` for `grid` and `baseline` entries only, never for `paired`. This probe is that exact gap surfacing concretely rather than a distinct new issue, so no code was added here; it stays routed to the same follow-up item 2 already on record, now with a live reproduction attached to it if that follow-up is picked up.

### Re-verification

```
$ uv run pytest
968 passed

$ uv run ruff check .
All checks passed!

$ uv run mypy
Success: no issues found in 40 source files
```

`E-SWEEP-GROUPS-UNSUPPORTED` reconfirmed firing:

```
$ uv run pytest tests/test_validate.py -k "groups" -v
tests/test_validate.py::test_each_unimplemented_mode_is_refused_on_its_own[groups-value2-E-SWEEP-GROUPS-UNSUPPORTED] PASSED
1 passed, 266 deselected
```

Did not run `ruff format` — confirmed via `git diff --stat` that only `src/publishable/validate.py` and `tests/test_validate.py` changed, and only by the intended additions (22 and 37 lines respectively, both pure insertions), leaving the reviewer-noted pre-existing unformatted block in `tests/test_validate.py` untouched.

### Files touched in this follow-up

- `src/publishable/validate.py` — `_check_shape`'s `sweep.paired` guard gains a per-key `isinstance(key, str)` check nested inside the entry-is-a-mapping branch
- `tests/test_validate.py` — `test_a_paired_entry_with_a_non_string_int_key_is_a_diagnostic_not_a_traceback`, `test_a_paired_entry_with_a_non_string_float_key_is_a_diagnostic_not_a_traceback`

---

## Third review follow-up (commit `2d30836`)

Scoped re-review: **ADDRESSED**, class closed for `paired`. The reviewer enumerated every operation touching paired-derived data (`_axes`, `_swept_paths`, `label_for`, `_keys_for`, `render_value`) and confirmed `isinstance(key, str)` is an exhaustive gate — no type both passes it and lacks `.split`/`.endswith`. It also upheld the `E-CONFIG-SHAPE`-vs-`envelope.py` route choice with a sharper framing than either of us gave first: `envelope.py` coerces because its keys sit under a **closed vocabulary** (`LEAF_TYPES`) a coerced string can be compared against, and that check is non-fatal by design; `_check_shape`'s guard is a shape guard and fatal like every other guard in that function. Same underlying rule — fatal for shape, non-fatal for vocabulary membership — applied to two different questions, not an inconsistency.

Two items to close before shipping.

### 1. The identical crash was reachable through `sweep.grid`, unguarded

Verified first, per the coordinator's instruction, that this wasn't already covered somewhere I hadn't looked: `grep -n "grid.items\|grid\["` on `validate.py` showed exactly the two sites already known — the `_check_shape` value-shape loop (which never inspected `path`, only `values`) and `_check_sweep`'s own `grid.items()` loop (which reports `E-SWEEP-PATH-UNKNOWN` for a string path that doesn't resolve, but never rejects a non-string one). Confirmed the crash directly before adding anything:

```
$ uv run python -c "
from publishable.sweep import expand
expand({'sweep': {'grid': {123: ['a','b']}}})
"
AttributeError: 'int' object has no attribute 'split'
```

Pre-existing, and outside the finding I was originally given for `paired` — but with the `paired` guard now in place one function away, leaving `grid` open was the worse of the two states (a reader who sees the `paired` guard reasonably infers `grid` already has one). Closed the same way, in the same `elif isinstance(grid, dict):` branch, right beside the existing per-axis value-shape check:

```python
for path, values in grid.items():
    if not isinstance(path, str):
        _bad("sweep.grid", path, "string")
        continue
    if values is not None and not isinstance(values, list):
        _bad(f"sweep.grid.{path}", values, "list")
```

Two new tests, mirroring the `paired` ones: `test_a_grid_with_a_non_string_int_key_is_a_diagnostic_not_a_traceback`, `test_a_grid_with_a_non_string_float_key_is_a_diagnostic_not_a_traceback`.

### 2. The `paired` value-checking gap is now recorded in `spec-defects.md`, not only in this report

Added a full entry to `docs/superpowers/spec-defects.md` (gitignored, but the durable location CLAUDE.md designates — this report file is deleted when the plan finishes, which is exactly the loss mode the coordinator flagged and H1 already hit once). The entry:

- States the gap precisely: `_check_sweep` runs `_path_resolves` (`E-SWEEP-PATH-UNKNOWN`), `_value_checks`'s `Param.check` (`E-PARAM-VALUE`), and `check_swept_value` (`E-SWEEP-VALUE-UNNAMEABLE`) over every `grid` axis value (the first two also over `baseline`), but none of the three loops was extended to `sweep.paired`'s entries.
- Gives three concrete, verified-not-hypothetical reproductions: a typo'd path silently planted into a condition's config; a value violating its `Param`'s own constraint (e.g. `ge=2`) surfacing only wherever a step first reads it, not at `validate`; and a value that can't render into a label (`check_swept_value({"a": 1})` — re-verified directly — returns a real message) producing a condition label no selector can parse back into axes.
- Names an owner: checked the H2 charter amendment in `specs/2026-08-08-implementation-spine-design.md` ("H2 scoping") first — it names exactly six § Validation checks H2 owns beyond the modes existing at all (ablation targets, ablation needs a baseline, ablation composition, ablation-baseline-vs-group-level, sample ranges, axis names distinct), and per-entry `paired` value-checking is not among them, nor assigned to any task in the current plan. Since `paired` is an H2 Sweeps mode, the entry assigns **H2** as owner of the gap in its own charter, rather than inventing an owner or leaving it unassigned.
- States explicitly that it is out of scope for H2 Task 2 (this task) — the shape guards this task added close every crash; this gap is about silent semantic acceptance after the shape is already confirmed good, a different and larger question (extending two existing loops to a third case) than this task's stated interface (`Produces: nothing new`) covers.

### Re-verification

```
$ uv run pytest
970 passed

$ uv run ruff check .
All checks passed!

$ uv run mypy
Success: no issues found in 40 source files
```

`E-SWEEP-GROUPS-UNSUPPORTED` reconfirmed firing:

```
$ uv run pytest tests/test_validate.py -k "groups" -v
tests/test_validate.py::test_each_unimplemented_mode_is_refused_on_its_own[groups-value2-E-SWEEP-GROUPS-UNSUPPORTED] PASSED
1 passed, 268 deselected
```

Did not run `ruff format`. `git diff --stat` for this follow-up shows only `src/publishable/validate.py` (+11) and `tests/test_validate.py` (+17), both pure insertions — the pre-existing unformatted block in `tests/test_validate.py` the previous review noted is untouched.

### Files touched in this follow-up

- `src/publishable/validate.py` — `_check_shape`'s `sweep.grid` loop gains the same `isinstance(path, str)` guard `sweep.paired` already has
- `tests/test_validate.py` — `test_a_grid_with_a_non_string_int_key_is_a_diagnostic_not_a_traceback`, `test_a_grid_with_a_non_string_float_key_is_a_diagnostic_not_a_traceback`
- `docs/superpowers/spec-defects.md` (gitignored) — new entry: "`sweep.paired` entries get none of `grid`'s three per-entry checks", owned by H2, explicitly out of scope for this task
