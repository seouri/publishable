# Task 7 review — the entry-point metadata scan, five groups, no `.load()`

**Reviewed:** `1a0570b..e744b44` (`9d28200` is the code commit). Branch `h7b-registries`.

**Verdicts**

1. **Spec compliance: ✅**
2. **Task quality: ✅** — after two gaps found in this review were closed here, in
   `tests/test_plugins.py`. Both are recorded below with the mutation evidence. `src/publishable/plugins.py`
   is **unchanged**: the shipped implementation was correct throughout; what was missing was any test
   that could see it change.

**Verification runs.** Baseline before any edit of mine: `uv run pytest -q` → **2006 passed, 2 xfailed**,
matching the report. After the two test edits: **2006 passed, 2 xfailed** (no test added or removed).
`uv run ruff check .` clean, `uv run ruff format --check .` → **78 files already formatted**,
`uv run mypy` → **no issues in 44 source files**. Every mutation below was applied by editing the file,
`__pycache__` cleared, re-run, then reverted by hand-editing back and confirmed byte-identical with
`diff` against a pre-mutation copy — never `git checkout --`.

---

## Critical

**C1 — `test_the_scan_imports_nothing` could not fail on the guarantee it names. Closed here.**

The test's entry point targeted `no_such_module:resolve`, so it could only detect a load whose
*exception escaped*. Verified by mutation: inside `scan_group`'s loop,

```python
try:
    ep.load()
except Exception:
    pass
```

→ **all 6 tests passed** (`uv run pytest tests/test_plugins.py -q`). The scan returned normally and the
test's own trailing `.load()` still raised, so every assertion held while the module was importing every
plugin on the machine. The module docstring's "nothing here calls `EntryPoint.load()`" and the design's
decision 3 were therefore a comment claiming a guarantee no assertion provided — the shape that produced
nineteen of the previous slice's twenty-six findings, in the one module every later task in the slice
reads. The implementer's standalone `sys.modules` probe did check the right thing; the *committed suite*
did not, and only the committed suite outlives the task.

**Closed** by rewriting the test in place (no conftest change — the fixture already returns `site`): the
target is now a module that genuinely imports, written into the distribution's own directory, and the
assertion is its absence from `sys.modules` before and after the scan. The trailing `.load()` became a
positive control — it succeeds, the module then *is* in `sys.modules`, and it is popped in a `finally` so
nothing leaks to the next test. Re-ran the swallow mutation against the rewritten test →
**`test_the_scan_imports_nothing` FAILED**, 5 passed. `import pytest` was replaced by `importlib`/`sys`
(the unused `monkeypatch` parameter is gone too).

---

## Important

**I1 — claimant order was pinned by nothing at all; the reported gap was the smaller half. Closed here.**

The report names mutation (c) (`key=lambda ep: ep.value`) as non-discriminating and its arithmetic is
right — I reproduced it. But the larger mutation was not tried: **deleting the inner sort entirely**,
`{name: found[name] for name in sorted(found)}` → **all 6 passed**. Because `monkeypatch.syspath_prepend`
puts the *second* install at `sys.path[0]`, and the fixture installed `dist-two` first, walk order was
already `dist-one, dist-two` — identical to provider order. So neither ordering the design's trap row
demands be ruled out ("name order read as discovery order") was separated: the fixture had two elements
and three candidate orderings agreed on the answer. This is the repo's own "fixture too few elements to
distinguish the candidate orderings" trap, one layer deeper than the report found it.

**Closed** by two edits inside the existing test, changing no assertion:
- install `dist-one` **first**, so walk order becomes `dist-two, dist-one` — opposed to the assertion;
- give `dist-one` the value `pkg_zeta.r:resolve` and `dist-two` `pkg_alpha.r:resolve`, so value order is
  opposed to provider order.

The asserted list `["dist-one 1.0", "dist-two 2.0"]` is unchanged. Re-verified: drop-the-sort →
**FAILED**; `key=lambda ep: ep.value` → **FAILED**; unmutated → 6 passed. The test docstring now records
why each half of the fixture is arranged as it is, so the next edit cannot flatten it back.

**Judgment on routing: closed in task 7, not routed to task 8.** "Claimants in provider order" is
`scan_group`'s own shipped docstring claim and `scan_group` is this task's deliverable; task 8 asserts on
a *message*, so its tests would not pin this list's order even incidentally. "The tests are verbatim from
the brief" is not a spec constraint — the brief's Step 7(c) argues from a fixture property that does not
hold, so repairing the fixture *is* the brief's own stated methodology ("checked against the test body"),
not a departure from it. The correct instinct in the report was to refuse to alter the code; altering the
fixture the brief's own argument mis-describes costs nothing and was the whole remedy.

---

## Minor

**M1 — Five groups: verified, and the citation holds.** `GROUPS` lists five distinct correct strings, no
copy-paste duplicate. `docs/reference.md` has exactly five
`[project.entry-points."publishable.*"]` blocks at § Creating a plugin (templates, resolvers, probes,
writers, readers), so the test docstring's "one block per registry" names an authority that says what it
claims — decision 2's fifth group has landed in the document as well as the tuple.

**M2 — The no-import invariant survives attack on every attribute the code touches.** Read
`importlib.metadata`'s source on this interpreter (CPython 3.13.7) rather than assuming:
`EntryPoint.load()` is the **only** method calling `import_module`; `.name`/`.value`/`.group` are
instance vars set in `__init__`; `.dist` is a plain attribute stamped by `_for(dist)`; `.module`/`.attr`/
`.extras` are regex over `.value`; `Distribution.name`/`.version` parse the `METADATA` *file*. `str()`
and `repr()` reach none of it. A grep of `src/` for `.load()` finds one hit — the prose in the docstring
— and `provider_of`'s claim that `entry_points()` never hands back an unattached object is accurate for
the same reason (`_for` runs on every entry point the API yields), so the `# pragma: no cover` branch is
correctly described rather than over-claimed.

**M3 — Fixture isolation: verified, in both the ways that could have failed.** `installed` is a plain
fixture requested by name; `grep -rn autouse tests/` finds exactly one autouse fixture, `_restore_environ`,
so the fixture docstring's claim about being the only one is true. Two distributions do produce two
independent scans — the collision test returns two claimants, which the `FastPath` cache would have
collapsed had they shared a directory; confirmed the cache mechanism is real (`FastPath.search` is
`self.lookup(self.mtime).search(name)` over an `lru_cache`d instance per root), so the "own directory per
call" rule is load-bearing rather than defensive. Leakage across tests: ran the two-distribution test and
the `== {}` control together in one process, control second → both pass, so `syspath_prepend`'s teardown
really does clear the scan.

**M4 — The "companion registry fixture" the review brief asks about does not exist in this task.**
Neither the task brief nor the diff adds one; `tests/conftest.py` gains only `_DIST_METADATA` and
`installed`, and no process-global registry is touched — `templates/registry.py`'s `_BUILTIN` is not
mutated by anything here, and `_merged` builds fresh per call. Recorded as N/A rather than left looking
unchecked; the process-global surface that *is* live is `importlib.metadata`'s path cache, checked in M3.

**M5 — Nothing describes the resolver as working; one docstring line is close.** No test, docstring or
document in this diff claims a resolver resolves or that `E-DATA-RESOLVER-UNSUPPORTED` is retired; the
§ Package layout edit removes exactly one `— not yet built` marker, on the line for the module this task
built, alignment and trailing whitespace unchanged. The one line worth noting is `plugins.py`'s opening
"Every name a config can write for a plugin artifact resolves through this module" — today the module has
**zero** callers in `src/` (grep: only `tests/test_plugins.py` imports it) and the wholesale refusal still
stands. It reads as specification present-tense, which is the repo's convention for `src/` prose and is
what the surrounding paragraph's citation of § Creating a plugin makes clear, so it is not a false build
claim — but it is the sentence to re-read when Part B lands, since it will become checkable then.

**M6 — `git checkout --` on `.superpowers/sdd/.gitignore`, disclosed in the report.** Restoring a tracked
file to its committed content is the sanctioned repair for that clobber and the report says so plainly, so
no finding — noted only because CLAUDE.md's warning is about a *different* use of the same command.
The file was clobbered to a bare `*` again before this review; restored from `HEAD` while here — the
restore is byte-identical to the committed content, so it appears in no commit of mine.

---

## What no mutation reaches — the report's list, corrected

The report's first three residuals stand and are correctly stated: `GROUPS` is a constant pinned only by a
literal; `provider_of`'s `dist is None` branch is unreachable; and **the no-`.load()` prohibition binds
only `scan_group`** — a *caller* added in task 8 or later that loads is still caught by nothing here, and
that is now the only unpinned half of the invariant rather than the whole of it. The report's fourth
entry — the sort-key gap — is **closed** by I1 and should be read as history.

Two residuals the report did not name, both accepted:

- The fixture does not exercise a build backend translating a `pyproject.toml` entry-points table into
  `entry_points.txt`. The brief names this and core reads no `pyproject.toml`, so nothing here could pin it.
- `test_the_scan_imports_nothing` proves the scan imports no *plugin*. The "core loads, but the module was
  already imported" reading is ruled out by the **pre**-scan assertion, not merely by the unique target
  name — both are present, and the pre-assertion is the one doing the work.

**The single-line mutation for every test in the file**, so the obligation is discharged rather than
implied. `test_the_groups_core_reads_are_the_five_the_document_declares`: none — a constant pinned by a
literal, as the report says. `test_an_absent_group_is_empty_and_a_present_one_is_not`,
`test_a_scan_selects_its_own_group_only` and `test_names_are_sorted_and_the_sort_is_not_the_install_order`
are all pinned by dropping the group filter (`entry_points()` for `entry_points(group=group)`) — run, **3
failed, 3 passed**, so group selection is genuinely checked and not merely described; the sort test is
additionally pinned by walk-order return (run in the report, re-verified here).
`test_two_distributions_claiming_one_name_both_arrive` by either sort mutation in I1.
`test_the_scan_imports_nothing` by the swallowed `.load()` in C1.
