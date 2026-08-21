# Task 3 (batch 3): override discovery — report

Branch `h8c-report-study`. This batch is alone: task 3 is the slice's proxy risk, and its review
must certify three separate "not a proxy" answers without also certifying a renderer. Suite run
directly in the foreground throughout — no monitor, no background wait.

## What was built

`src/publishable/report.py`: `render_with_override(run_dir, record, render)` — the discovery
function. `render` is `Callable[[type[BaseReport] | None], T]`, invoked with the resolved subclass
or `None`, and the call happens **inside** the same `sys.path` window opened to import the
override, never after.

**The direct question this predicate asks:** *which module does this run's own
`config.entrypoint` name?* Nothing else is consulted. Concretely:

- `_read_repo_root(run_dir)` reads `environment/repo_root.txt` from the run directory (never
  `provenance.git.repo_root`, never a walk-up from the argument), checked for shape — missing,
  empty, or not a directory is `E-REPORT-OVERRIDE-REPO`, not a silent "no override".
- `_root_package(record)` reads `record["config"]["entrypoint"]`, requires a non-empty string
  shaped `<module>:<attribute>`, and returns the module's root package. Absent, empty, non-`str`,
  or malformed is `E-REPORT-OVERRIDE-ENTRYPOINT` — a distinct code from `E-ENTRYPOINT-IMPORT`,
  because discovery does **not** call `base_experiment.load_experiment`; it re-implements that
  window (purge `sys.modules` for the root package, insert `<repo_root>/src`, import, pop in a
  `finally`) by calling the same two steps in the same order, since it needs `<root_pkg>.report`,
  not the entrypoint's own attribute. That choice — call vs. re-implement — is stated in the
  function's own docstring, per the brief's instruction not to leave it for a diff reader to
  infer.
- `render_with_override` then purges `sys.modules` for `root_pkg` and `root_pkg.*`, inserts
  `<repo_root>/src`, and tries `importlib.import_module(f"{root_pkg}.report")`. A
  `ModuleNotFoundError` whose `.name` equals that exact module name is "no override" —
  `render(None)`. Any other exception (including a `ModuleNotFoundError` for a *different*
  module, e.g. a missing dependency the override itself imports) is `E-REPORT-OVERRIDE-IMPORT`.
  Otherwise, the module's own namespace is filtered for classes that are `BaseReport` subclasses,
  are not `BaseReport` itself, and are defined **in that module** (`obj.__module__ ==
  module.__name__`, so an imported-but-not-defined name can't be mistaken for the project's own
  report); exactly one is required, or `E-REPORT-OVERRIDE-CLASS`. The resolved class is passed to
  `render` before `sys.path.pop(0)` runs in the `finally`.

`docs/reference.md` § Errors `validate` reports gains four rows in alphabetical position
(`E-REPL-SEED-COLLISION` → the four new `E-REPORT-OVERRIDE-*` rows → `E-RESOLVER-UNKNOWN`):
`E-REPORT-OVERRIDE-CLASS`, `E-REPORT-OVERRIDE-ENTRYPOINT`, `E-REPORT-OVERRIDE-IMPORT`,
`E-REPORT-OVERRIDE-REPO` — landed in this commit per correction 6, since these two are minted here
and the other two (`E-REPORT-OVERRIDE-IMPORT`, `E-REPORT-OVERRIDE-CLASS`) were already named in
Decision 15's table but had no row here yet.

`tests/test_report.py` (+20 tests, one parametrized ×8): the three ordinary refusals (no module,
raises on import — including the "missing dependency inside the override" sub-case — no subclass,
two subclasses), three repo-root shape refusals, eight entrypoint-shape refusals (missing
`config`, missing `entrypoint`, `None`, `""`, a list, no colon, empty module half, empty attribute
half), and the four fixtures below. Every fixture drives a REAL project through
`main(["new"/"run", ...])` — never a hand-built record — because the property under test is about
what a real `environment/repo_root.txt` and a real `config.entrypoint` say.

## The three "not a proxy" answers, and what makes each proxy impossible here

1. **Module-name prefix / directory scan (H7a's first fail-open).** `_root_package` never touches
   `src/`; it derives the package name from `record["config"]["entrypoint"]` alone.
   `test_fixture_o_m1_two_packages_one_named_by_entrypoint` puts TWO packages side by side in one
   `src/` — the real one (named `cohort_pilot`, sorts alphabetically after) and a decoy named
   `aaa_decoy_pkg` (sorts first) — each with its own titled `BaseReport` override. A scan-based
   implementation has to pick one; picking the alphabetically-first one is the plausible-looking
   bug and is exactly what the fixture is built to expose (below).
2. **A marker stamped on the class (H7a's second fail-open).** Discovery never inspects a marker;
   it filters `vars(module)` for `BaseReport` subclasses **defined in that module**
   (`obj.__module__ == module.__name__`), so a class merely imported into the namespace — which a
   marker-based check could mistake for "owned" — is excluded on the direct fact instead.
3. **State read at the wrong moment (H7a's third fail-open, M15's costume here).** The
   `sys.modules` purge for `root_pkg`/`root_pkg.*` runs **before** `sys.path` is inserted, on
   every call, so a second call for a *different* project sharing the same package name reads
   fresh rather than a cached module from the first. `test_fixture_o2_m15_...` builds two separate
   projects, both scaffolded from `cohort-pilot` (identical package name `cohort_pilot`), and
   renders both in sequence in one process, asserting each gets its OWN title.

## M15's fixture, confirmed both ways

Ran the honest code first — `uv run pytest tests/test_report.py -q -k fixture_o2_m15` → 1 passed.
Then applied the mutation by hand (deleted the purge loop entirely) and re-ran the same test:
**it failed** — `title_1` came back `'SECOND-PROJECT'` instead of `'FIRST-PROJECT'` (not
`title_2`, as a naive reading might expect: `_build_project`'s own internal `main(["run", ...])`
calls `base_experiment.load_experiment` for the SECOND project during its build, which caches
`cohort_pilot`'s package object with its `__path__` pointing at the second project's `src/` before
either `render_with_override` call runs — so importing `cohort_pilot.report` resolves through
that stale cached package for BOTH calls, corrupting the first render, not the second). Also
tried the narrowed form the brief explicitly allows — purge only the bare `root_pkg`, dropping
`root_pkg + "."` — and it failed the same test the same way (`title_2` came back
`'FIRST-PROJECT'` under that variant), since `cohort_pilot.report`, once cached, survives a purge
that deletes only `cohort_pilot` itself. Reverted by copying back a saved pre-mutation copy of
`src/publishable/report.py` and confirmed **byte-identical** by `diff`, then re-ran
`tests/test_report.py` in full: 29 passed. On a single project alone, the honest code and both
mutated forms are indistinguishable — no fixture without a second, same-named project could ever
see this.

**A property-preserving arm** — one that does not discriminate this mutation despite looking
related — would be: two projects with *different* package names rendered in sequence. Since
`sys.modules` keys never collide, the purge is a no-op either way and both mutated variants pass
identically to the honest code. That is exactly why `test_fixture_o2_m15_...` insists (and
asserts, via `first["pkg"] == second["pkg"]`) that both projects share one package name — the
fixture would be vacuous without that assertion holding.

M1, M2 and M11 were each confirmed the same way (apply by hand, observe the named test fail for
the stated reason, revert, `diff` byte-identical against a saved copy, re-run clean):

- **M1** (scan `src/*/report.py`, pick alphabetically first): the honest fixture originally used
  `decoy_pkg`, which happens to sort AFTER `cohort_pilot` — so my first version of the mutation
  passed the test by accident (both branches picked `cohort_pilot`). Caught this by running the
  mutation immediately rather than trusting the fixture; renamed the decoy to `aaa_decoy_pkg` (sorts
  first), re-ran the mutation, and it failed as intended (`'DECOY' == 'ENTRYPOINT-NAMED'`
  assertion error). This is exactly the "check the two branches can actually differ" discipline
  the plan's global constraints require, and it caught a real vacuous-fixture risk in my own
  first draft.
- **M2** (read `provenance.git.repo_root` instead of the file): hand-edited `target`'s in-memory
  record so `provenance.git.repo_root` names `other`'s real repo (both scaffolded from
  `cohort-pilot`, same package name, different real repos). Mutated code returned `'OTHER-
  PROJECT'`; honest code returns `'TARGET-PROJECT'`.
- **M11** (call `render` after `sys.path.pop(0)`, moving only the success path's return outside
  the `try`/`finally`): Fixture V's override lazily imports a **top-level** sibling module
  (`report_helper.py`, sitting directly in `src/`, not inside the package, so it has no
  `__path__` of its own to fall back on) and uses it to read a real condition artifact via
  `ReportIO.read_condition`. Deferred, this raised `ModuleNotFoundError: No module named
  'report_helper'` from inside the override's own `sections()`; inside the window it returns
  `{"m": "pearson"}`, the real artifact's contents.

The walk-up mutation (replacing the `repo_root.txt` read with `provenance.find_repo_root`) was
deliberately not attempted, per the brief: it is rejected by name because it is caught by a crash
(`E-GIT-NO-REPO`) rather than by the property, on a correctly configured project where
`output_dir` is outside any repo.

## Gates, confirmed by running

`uv run ruff check .` → all checks passed. `uv run ruff format --check .` → 90 files already
formatted (unchanged — no new file). `uv run mypy` → 50 source files (unchanged — no new module).
`uv run pytest -q` → **2685 passed, 1 skipped, 2 xfailed** (baseline 2665 + 20 new: 5 ordinary-
refusal tests + 3 repo-root-shape tests + 8 parametrized entrypoint-shape cases + 4 fixtures
[M1, M2, M15, M11]).

## What was grepped, and its scope

- `grep -rn "E-REPORT-OVERRIDE-REPO\|E-REPORT-OVERRIDE-ENTRYPOINT\|E-REPORT-REPO\|E-REPORT-
  ENTRYPOINT" .` (whole repo, `--include="*.py" --include="*.md"`) before minting the two new
  codes — no hits, confirmed no collision.
- `grep -rn "repo_root.txt\|environment/repo_root" src/publishable/` — found `freeze.py`'s three
  read/check sites and `cli.py`'s single write site (`command_run`), confirming the artifact is
  written unconditionally at run start and giving `freeze.py`'s shape-check the precedent
  `_read_repo_root` follows (one code covering missing/empty/not-a-directory, the way
  `E-FREEZE-NO-CONFIG` does for the identical three conditions).
- `grep -n "E-ENTRYPOINT-REQUIRED\|E-ENTRYPOINT-IMPORT" src/publishable/*.py` — confirmed
  `E-ENTRYPOINT-REQUIRED` is `validate.py`'s own pre-check on `cfg.entrypoint` (a live config,
  before `load_experiment` ever runs) and is a genuinely separate mechanism from what discovery
  reads (a finished record's embedded `config.entrypoint`), which is why `E-REPORT-OVERRIDE-
  ENTRYPOINT` is a new code rather than a reuse of either existing one.
- `sed -n` over `docs/reference.md` §  Errors `validate` reports to confirm the table's ordering
  is alphabetical by code (`E-REPL-*` immediately preceding `E-RESOLVER-*`, `E-DATA-*` preceding
  `E-ENTRYPOINT-*`), before choosing where the four new rows land, and confirmed via `awk -F'|'`
  that each inserted row has the same column count as its neighbours.
- Did **not** grep for every existing use of `sys.modules`/`sys.path` elsewhere in `src/` beyond
  `base_experiment.py` — scope was the one window this task re-implements, not a repo-wide audit
  of every place that manipulates either.

## Concerns

- `_root_package`'s malformed-entrypoint check (`not module_name or not attr`) treats
  `"pkg.mod:"` (empty attribute half) and `":attr"` (empty module half) both as
  `E-REPORT-OVERRIDE-ENTRYPOINT`, mirroring `load_experiment`'s own shape check exactly — both are
  covered by a parametrized test case, but I did not separately verify whether a report record
  could ever legitimately arrive with a malformed-but-non-empty `entrypoint` (e.g. containing two
  colons) reaching a different, wrong branch; `str.partition(":")` on `"a:b:c"` yields
  `("a", ":", "b:c")`, both halves truthy, so it would resolve to root package `"a"` without
  complaint. Not exercised by name; flagging rather than asserting it is fine.
- `render_with_override`'s "no override" branch (`render(None)`) is called while `sys.path` is
  still inserted, inside the same `try`, even though nothing was imported — harmless, but worth a
  reviewer's eye since it means `render(None)` always executes with the window open, not only when
  there is something to import from it.

## Fix round 1

Review at `.superpowers/sdd/2026-08-21-report-study/task-b3-review.md`. Spec compliance PASS;
task quality PASS with findings — three Majors, three Minors, all closed below. Every mutation
run against the **full, unfiltered** `uv run pytest -q`, in the foreground; reverted by copying a
saved pre-mutation file back and confirming byte-identical by `diff` before the next one.

### Major 1 — `sys.path` restoration pinned by nothing, and removed by position

**Changed:** `render_with_override` now captures `src_entry = str(repo_root / "src")` once, and
the `finally` removes it **by identity** (`if src_entry in sys.path: sys.path.remove(src_entry)`)
rather than `sys.path.pop(0)`. The `if` guards a refusal raised *before* the insert (never
reached) and an override that removed or cleared `sys.path` itself, so cleanup never raises a
second, unhandled exception on top of whatever the window already failed on.

**Pinned by three new tests:**
`test_sys_path_is_restored_after_a_successful_render`, `test_sys_path_is_restored_after_render_
raises` (captures `sys.path` before, calls with a `render` that raises `RuntimeError`, asserts
`sys.path` unchanged after `pytest.raises`), and
`test_sys_path_entry_is_removed_by_identity_not_by_position` — an override whose `sections()`
does `sys.path.insert(0, <vendored>)` (the "ordinary idiom" the review's probe used), which pushes
`src_entry` to index 1.

**Verified by running, both directions:**
- `finally: pass` (no restoration at all) → all three fail: the two "restored" tests find
  `src_entry` still on `sys.path`, and the identity test fails the same way.
- `sys.path.pop(0)` (positional, restored code's own predecessor) → only the identity test fails
  (`src_entry` leaked, because the override's vendored entry sat at index 0 and got popped
  instead); the two plain "restored" tests still pass, since neither of their overrides touches
  `sys.path` itself — confirming the identity test is what actually distinguishes position from
  identity, not the other two.
- Reverted, full suite: 2689 passed, 1 skipped, 2 xfailed (2685 + 4 new tests this round).

### Major 2 — the `obj.__module__ == module.__name__` filter, unpinned

**Pinned by one new test:** `test_a_base_report_merely_imported_does_not_count_as_a_second_
definition` — a `report.py` that does `from <pkg>.shared_report import SharedReport` (a separate
module defining its own `BaseReport` subclass) **and** defines its own local `Report` subclass.
Asserts the resolved class is `Report` and its section renders.

**Verified by running:** deleted the `and obj.__module__ == module.__name__` clause — the new test
fails with `ContractError: '...report' defines 2 \`BaseReport\` subclasses, not exactly one`,
exactly the wrong refusal the review's own probe found, breaking the documented "an ordinary
import from a plugin, called by each one's override" route. Reverted, re-ran: passes. No code
change was needed here — the clause was already correct; only the pin was missing.

### Major 3 — M1's fixture ruled out first-wins scans only

**Changed:** `test_fixture_o_m1_two_packages_one_named_by_entrypoint` now writes **two** decoy
packages, `aaa_decoy_pkg` (sorts before `cohort_pilot`) and `zzz_decoy_pkg` (sorts after), each
with its own titled section, instead of one. The docstring states the reason in the words the
review asked for: a single decoy only ever rules out ONE ordering, and a decoy that happens to
sort on the scan's own biased side passes by coincidence rather than by the fixture ruling that
reading out.

**The reusable lesson, stated as such (also true of my own first draft):** what made the original
`decoy_pkg` fixture blind to a scan-last mutation was not the element count but **the decoy's sort
position agreeing with the bug** — `decoy_pkg` sorted after `cohort_pilot`, so "pick last" landed
on the honest answer by accident. The identical shape closed the *disclosed* vacuous first draft
(`decoy_pkg` sorting after, defeating a naive scan-first reading) and then reopened, unnoticed, as
a scan-last blind spot in the very fixture built to close it — catching a sort-position coincidence
once does not immunize the next fixture against the same coincidence recurring in the other
direction.

**Verified by running, both directions:** a scan-first mutation (`sorted(...)[0]`) fails with
`'AAA_DECOY_PKG' == 'ENTRYPOINT-NAMED'`; a scan-last mutation (`sorted(...)[-1]`) fails with
`'ZZZ_DECOY_PKG' == 'ENTRYPOINT-NAMED'`. Neither alphabetical pick a scan can make now resolves to
the honest answer. Reverted, re-ran: passes. Left the design's own broader phrasing ("any pick is
observable") as the design's — not this task's document to retro-edit — and closed the gap the
cheaper way the review named: a third package, not a narrower claim.

### Minor 4 — stale module docstring

`src/publishable/report.py`'s module docstring no longer says override discovery "arrive[s] in
later tasks" (deleted the clause rather than rewriting it, per `CLAUDE.md`); it now states the true
fact instead — `render_with_override` is called by nothing outside this module's own tests, task 8
wires it into `report`.

### Minor 5 — stale/false test-file claims

`tests/test_report.py`'s module docstring no longer claims "there is no `run`/`io` construction
yet" (false since batch 2's `ReportIO`). The task-3 banner comment now names the four fixtures
(O, the M2 fixture, O2, V) as the ones that run a real project, and says explicitly that the
shape-refusal tests immediately below build records and run directories by hand **on purpose** —
that is what those tests are for.

### Minor 6 — test-count arithmetic

Fixed in § What was built above: `tests/test_report.py` gained **20** tests in the original
commit (5 + 3 + 8 + 4, matching the stated breakdown and the 2665 → 2685 delta), not 21. This fix
round adds 4 more (33 tests in the file total; 2685 → 2689).

### Not acted on, per the review's own adjudication

- The extra-colon entrypoint: **leave, do not file** — no real record can hold one
  (`E-ENTRYPOINT-IMPORT` fires at both `validate` and `run`), and `partition(":")`'s first-colon
  split resolves the correct root package anyway even if one somehow existed.
- Guard-pin arm D: did not fire, and could not have — this task's diff touches only
  `docs/reference.md`, `src/publishable/report.py`, `tests/test_report.py` and this record; no
  guard-pin file is among them.

### Gates, confirmed by running (after all fixes)

`uv run ruff check .` → all checks passed. `uv run ruff format --check .` → 90 files already
formatted. `uv run mypy` → 50 source files, no issues. `uv run pytest -q` (full, unfiltered,
foreground) → **2689 passed, 1 skipped, 2 xfailed**.
