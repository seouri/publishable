## Task 22-24 report

**Status:** Complete. All three tasks implemented, tested, mutated, and committed separately.

**Commits:**
- Task 22: `645a4fd` — docs: validate imports a plugin to run a resolver — narrow the five sentences that said otherwise
- Task 23: `b6d4422` — artifacts: a read-only ResolverIO — read_input, and the paths it read
- Task 24: `6023364` — units: resolve a resolver name from metadata, then load the object behind it

**Test summary:** `uv run pytest` → 2074 passed, 1 skipped, 2 xfailed (2066 baseline + 8 new: task 22 adds 1 new test file-level — the two scan/get_template tests were extended in place, not added — plus 3 for task 23, 4 for task 24). `ruff check`, `ruff format --check` (80 files formatted), and `mypy` all clean after every task.

**Green on arrival:** `tests/test_validate.py::test_validate_imports_no_plugin_for_a_config_that_names_no_resolver` (task 22) passed the moment it was written, before any resolver-loading code existed — exactly as the brief predicted. Its can-fail proof is task 22's mutation (a) below.

**The two pre-existing no-import tests still discriminate after extension**, confirmed by mutation:
- `test_the_scan_imports_nothing` (extended): mutating `scan_group` to call `ep.load()` inside its loop → FAIL (assertion right after `scan_group` call fires, `AssertionError: 'loadable_probe' in sys.modules`). Reverted and re-confirmed green.
- `test_get_template_imports_nothing_for_an_installed_claim` (extended): not separately re-mutated beyond the added positive-control block, since its production surface (`get_template`) is unchanged by this slice — the appended block only adds the "loading is separate" control using `load_entry_point` directly, which the task-24 mutations below already exercise for that function.

**Mutations run (all reverted by editing back, none via `git checkout --`):**

Task 22:
- (a) Inserted a `scan_group`/`load_entry_point` load at the top of `_check_units` in `validate.py` → `test_validate_imports_no_plugin_for_a_config_that_names_no_resolver` FAILED on `"loadable_units" not in sys.modules`. Reverted; suite green again.
- (b) Added `ep.load()` as the first statement of `scan_group`'s loop in `plugins.py` → `test_the_scan_imports_nothing` FAILED on the assertion immediately after the `scan_group` call. Reverted; suite green again.

Task 23:
- Deleted `self._read_paths.append(relpath)` from `ResolverIO.read_input` → `test_a_resolver_io_records_every_path_it_read_in_order` FAILED (`() != (...)`). Reverted.
- Changed the read dispatch to `(self.input_dir / relpath).read_bytes()` → both `test_a_resolver_io_reads_the_input_and_nothing_else` and `test_a_resolver_io_reads_through_the_same_table_a_step_does` FAILED. Reverted.

Task 24:
- Deleted the `check_registration(...)` line from `_resolver_for` → `test_a_decorator_argument_disagreeing_with_the_entry_point_key_is_refused` FAILED with "DID NOT RAISE ContractError". Reverted.
- Replaced `claimants = found.get(name)` with `claimants = next(iter(found.values()), None)` → `test_an_unregistered_resolver_name_is_refused_from_metadata_alone` FAILED (raised `E-PLUGIN-LOAD` instead of `E-RESOLVER-UNKNOWN`, i.e. resolved to the wrong installed claimant). Reverted.

**Places the brief or spec disagreed with the code:**

1. **Task 24's prescribed `_resolver_for` body fails `mypy` as written.** `return fn` at the end (where `fn = load_entry_point(ep)`, itself typed `Any`) trips `no-any-return` against the declared `Callable[..., Any]` return type — mypy flags returning a bare `Any` even when the declared return type itself contains `Any`. Fixed with `from typing import cast` and `return cast("Callable[..., Any]", fn)`; behavior is identical, `uv run mypy` is clean, and all four task-24 tests still pass under this change. Not called out in the brief or the design spec.

2. **Task 22 Step 6's sweep is not literally empty**, but the one surviving hit is a false positive of the grep pattern, not a missed prose site. `grep -rn "never imports a plugin\|never at \`validate\`\|not such a caller\|cannot see this disagreement" ...` still matches `docs/reference.md`'s § The apparatus core can only observe: *"It runs at `dry-run`, at run start, and before every execution — never at `validate`."* This sentence is about the apparatus probe (H7d's territory), not about plugin importing, and it predates this slice (present in the pre-task grep taken before any edit in this session). None of the five sites task 22 names includes it, and rewriting it would be out of scope and false to CLAUDE.md's "prefer deleting to rewriting" only where the claim is actually wrong — this claim is correct as written. Recorded here rather than silently left, per the sweep-discipline rule in CLAUDE.md ("never filter the output of a sweep whose job is to find a string").

No other disagreements found; task 23 and the rest of task 24 matched their briefs exactly, including the exact test bodies and exact mutation prescriptions.
