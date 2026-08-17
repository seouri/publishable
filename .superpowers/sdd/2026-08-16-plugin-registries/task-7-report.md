# Task 7 report — the entry-point metadata scan, five groups, no `.load()`

**Status:** done.

**Commit:** see `feat: the entry-point metadata scan, five groups, and no .load()` (created after this
report is written; sha filled in by the commit step).

**Test summary:** `uv run pytest -q` → **2006 passed, 2 xfailed** (2000 + 2 xfailed baseline + 6 new
tests in `tests/test_plugins.py`). `uv run mypy` clean over 44 source files, no `[[tool.mypy.overrides]]`
needed — `EntryPoint`/`EntryPoints` are typed in the stdlib as the brief anticipated. `uv run ruff check .`
and `uv run ruff format --check .` both clean (78 files formatted, up from the stated baseline of 76 —
the two new files).

## Files

- Created `src/publishable/plugins.py` — `GROUPS`, `scan_group`, `provider_of`, `names`, verbatim from
  the brief.
- Created `tests/test_plugins.py` — six tests, verbatim from the brief.
- Modified `tests/conftest.py` — added `import importlib` to the existing import block, appended the
  `_DIST_METADATA` constant and the `installed` fixture, verbatim from the brief, at the end of the
  file (not autouse, requested by name).
- Modified `docs/reference.md` § Package layout — removed `— not yet built` from the `plugins.py` tree
  line.
- Restored `.superpowers/sdd/.gitignore` — `scripts/task-brief` had clobbered it to a bare `*` before
  this task started (per CLAUDE.md's documented hazard); restored to its tracked content with
  `git checkout --` (safe here: reverting a tracked file to HEAD, not destroying uncommitted work).

## The invariant: confirmed by direct probe that the scan imports nothing

Ran a standalone script (outside pytest, so no fixture machinery could be laundering the answer):
installed a real `dist-info` directory whose one entry point is `plate_wells = no_such_module:resolve`,
prepended it to `sys.path`, called `importlib.invalidate_caches()`, snapshotted `sys.modules` before and
after `from publishable.plugins import scan_group; scan_group("publishable.resolvers")`.

Result: the only modules newly present in `sys.modules` were stdlib (`importlib.metadata._adapters`,
`email.*`, `csv`, `hashlib`, etc. — `importlib.metadata`'s own machinery for parsing `METADATA`) and
`publishable`'s own package (`publishable`, `publishable.plugins`, `publishable.units`,
`publishable.templates.*`, etc. — the ordinary cost of `import publishable.plugins` pulling in the
package `__init__.py`). **`no_such_module` never appeared**, and a subsequent
`found["plate_wells"][0].load()` raised `ModuleNotFoundError: No module named 'no_such_module'` —
proof the entry point was returned unresolved. `test_the_scan_imports_nothing` in the committed suite
asserts the same thing inside pytest; the standalone script is the independent check that no test
fixture (autouse `_restore_environ`, `monkeypatch.syspath_prepend`, etc.) was masking an import.

## Mutations run

All three from Step 7, each reverted by hand-editing the file back (never `git checkout --` on
`plugins.py`), `__pycache__` cleared before each run, green re-confirmed by re-running (not by
`git status`).

**(a) Walk order instead of name order** — changed `scan_group`'s return to
`{name: found[name] for name in found}`.
Ran `tests/test_plugins.py` → **`test_names_are_sorted_and_the_sort_is_not_the_install_order` FAILED**
(`AssertionError: assert ['zz_first', ... 'mm_third'] == ['aa_second', ... 'zz_first']`), 5 passed.
Matches the brief exactly: the three-name fixture (`zz_first`, `aa_second`, `mm_third`, declared in
that order) is neither sorted nor reverse-sorted, so the mutant's walk-order output diverges from the
asserted sorted list under either reading. Reverted; re-ran; 6 passed.

**(b) One claimant per name** — changed the accumulation to `found[ep.name] = [ep]`.
Ran `tests/test_plugins.py` → **`test_two_distributions_claiming_one_name_both_arrive` FAILED**
(`assert ['dist-two 2.0'] == ['dist-one 1.0', 'dist-two 2.0']` — the mutant kept only the
second-installed claimant), 5 passed. Matches the brief. Reverted; re-ran; 6 passed.

**(c) Sort claimants by `ep.value` instead of `provider_of`** — changed the inner sort key to
`lambda ep: ep.value`.
Ran `tests/test_plugins.py` → **all 6 passed. The brief's prediction is wrong; see below.** Reverted
anyway (the shipped code sorts by `provider_of`, per the brief's Step 3 implementation, unaffected by
this finding); re-ran; 6 passed.

## Disagreement with the brief: mutation (c) does not discriminate

The brief argues mutation (c) must fail `test_two_distributions_claiming_one_name_both_arrive` because
"the fixture's values are `pkg_two.r:resolve` and `pkg_one.r:resolve`, whose sort order is the reverse
of the providers' (`dist-one 1.0` before `dist-two 2.0`)."

That's incorrect. The test installs `dist-two` (value `pkg_two.r:resolve`) first, then `dist-one`
(value `pkg_one.r:resolve`). Sorting the two entry points by `.value` lexicographically gives
`pkg_one.r:resolve` before `pkg_two.r:resolve` — i.e. `dist-one`'s entry point first, `dist-two`'s
second. Sorting by `provider_of` (`"dist-one 1.0"` before `"dist-two 2.0"`) gives the **same** order.
The two sort keys are not opposed here; they agree, because `pkg_one` < `pkg_two` and `dist-one` <
`dist-two` alphabetically track each other. So mutation (c) is silently absorbed by this test — I
verified it directly (`uv run pytest tests/test_plugins.py -v` showed all 6 green with the mutation
applied).

Per the brief's own methodology ("checked against the test body" for every prescribed mutation), this
one fails that check: no test in the file distinguishes "sort by provider" from "sort by entry-point
value" for this fixture. I did not add a new test or change the values, since the task's tests are
specified verbatim and mutation (c) not discriminating doesn't make the shipped implementation wrong
(it still sorts by `provider_of`, matching the module's docstring and § the brief's Step 3 code) — it
just means this particular assertion set has a live gap where a `sorted(..., key=ep.value)` regression
would go unnoticed. Filing this as a fact about the test suite, not fixing it, since Step 8 of the
brief already names one comparable gap ("nothing catches a caller that loads") and the brief's own
convention is that gaps get named rather than silently patched over by the task that finds them.

## What no mutation reaches (Step 8, restated, plus the one above)

- `GROUPS`' membership is pinned only by a set-equality test against a literal; a group added to both
  the tuple and the test in one edit would pass silently. Unavoidable for a constant.
- `provider_of`'s `dist is None` branch (`# pragma: no cover`) is unreachable through `entry_points()`
  and nothing exercises it.
- The no-`.load()` guarantee is pinned only for `scan_group` itself by `test_the_scan_imports_nothing`;
  no test here would catch a caller added later (task 8+) that calls `.load()`.
- **New finding:** the sort-key mutation (c) is not caught by any test in this file — see above. The
  provider-vs-value ordering only diverges when a distribution's name and its entry-point target
  string sort in different relative orders, which this fixture's values don't produce.

## Other brief/spec vs. code notes

- Format baseline: brief says "76 files, 0 to reformat" before this task's tests; confirmed — after
  adding the two new files, `ruff format --check .` reports 78 files, still 0 to reformat, consistent.
- Test count baseline: brief says "2000 passed + 2 xfailed" before this task; confirmed exactly, and
  2006 + 2 xfailed after (6 new tests, no regressions).
- No mypy override was needed, as the brief's own "probed... and it is" claim anticipated; not
  contradicted.
- The `.superpowers/sdd/.gitignore` clobber CLAUDE.md documents was present at the start of this task's
  session (visible in `git status` before any of my edits) — restored per that document's instructions,
  unrelated to this task's deliverable but noted since CLAUDE.md asks it be restored "when you notice."

No other disagreement between the brief/spec and the code found. The five-group count, the fixture
layout, the mypy typing, and the two already-passing mutations all matched the brief exactly.
