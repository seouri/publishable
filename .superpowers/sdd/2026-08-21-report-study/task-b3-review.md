# Task 3 (batch 3) review — override discovery, the three proxies, M15

Branch `h8c-report-study`, reviewed at `12f853d`. Batch is alone, so nothing here certifies a
renderer. Suite run directly in the foreground throughout; no monitor, no background wait. Every
mutation applied to a saved copy, reverted by writing the copy back, and confirmed byte-identical by
`diff` before the next one. Tree left clean (`git status --porcelain` empty, `report.py` and
`test_report.py` byte-identical to their committed state).

## Verdicts

- **Spec compliance: PASS.** Decision 3's direct question is asked directly, all three of H7a's
  proxies are structurally impossible here, `report <study.yaml>` is correctly left to task 10,
  four codes are minted with one § Errors row each covering every emit site in this commit
  (correction 6), and the `load_experiment` call-versus-re-implement choice is stated in the
  docstring and is **accurate against the shipped function** (same purge predicate, same order,
  same pop mechanism).
- **Task quality: PASS with findings.** Three Majors and three Minors, all closable in a fix round.
  Two Majors are missing pins on behaviour this commit relies on — one of them on a claim the report
  itself offers as one of its three certified answers. The third is a fixture sized to rule out one
  candidate answer where two are live, which is a trap `CLAUDE.md` names by shape.

## Gates, run

`uv run ruff check .` → all checks passed. `uv run ruff format --check .` → 90 files already
formatted. `uv run mypy` → 50 source files, no issues. `uv run pytest` → **2685 passed, 1 skipped,
2 xfailed**. The one skip is `tests/test_cli.py:11740` (needs real network), unrelated. **The guard
pin's arm D did not fire**: `test_h8c_arm_d_readme_worked_diff_block_rows`,
`..._design_principles_...` and `..._reference_...` in `tests/test_diff.py` all pass, none skipped.
The stronger statement the diffstat supports: **task 3 edited no guard-pin file at all** — the commit
touches `docs/reference.md`, `src/publishable/report.py`, `tests/test_report.py` and the batch's own
records, and none of arms A, B, C or D lives in any of them. Arm D therefore needed no editor, as the
ledger says, and the clause about arms A and C not being this task's is satisfied by the diff rather
than by an argument.

**Tree state.** No tracked file is modified — `git diff --stat HEAD` is empty, and both
`src/publishable/report.py` and `tests/test_report.py` are byte-identical to their committed state by
`diff`. The sole untracked addition is this review file, which `.superpowers/sdd/.gitignore` keeps
**tracked** (it ignores only `task-*-brief.md`, `*.diff` and `*.txt`), so it wants `git add -f` when
the controller commits it. Every mutation and probe lived in the scratchpad; nothing was reverted with
`git checkout`.

---

## Findings

### Major 1 — `sys.path` restoration is pinned by nothing, and the pop answers with a position rather than the fact

`src/publishable/report.py:247` (`finally: sys.path.pop(0)`).

**Verified by running.** Replacing the `finally` body with `pass` leaves the **full, unfiltered**
suite at **2685 passed, 1 skipped, 2 xfailed** — no test anywhere asserts `sys.path` is restored, on
the success path or on any of the refusal paths. The brief's step 2 prescribes the `finally`
explicitly, so this is a prescribed guard with no mutation behind it.

The positional pop is separately reachable, and it is the same shape as H7a's third fail-open.
`pop(0)` answers *"which entry did I insert?"* with a position. User code runs inside this window by
design — the module body at import, and `sections()` at render — and an override whose `sections()`
does `sys.path.insert(0, ...)` (an ordinary Python idiom for reaching a vendored directory) makes
the pop remove *its* entry and leak `<repo_root>/src` permanently. Verified by probe: the leak
happens, and then a **second** project's override resolved a top-level sibling module it never
shipped from the **first** project's `src/`, rendering `'PROJECT-A'` into project B's report. That
is Decision 3's own *Cost if wrong* sentence — "render one experiment's figures for another's run" —
reached by a route other than a directory scan.

Reachability, stated honestly: the shipped CLI renders once per process, so the cross-project half
needs two renders in one process — which is exactly the condition M15's `sys.modules` purge exists
to defend against, and which this repo's own suite creates. The `sys.modules` half of the window is
guarded; the `sys.path` half is not.

`base_experiment.load_experiment:50` pops by index too, so the docstring's "same two steps in the
same order" is *accurate* — but the footprint inside the window is much smaller there (an import and
a `getattr`, no user render), so the precedent does not carry the exposure. One fix closes both
parts: remove by value, and assert restoration after a success and after a refusal.

### Major 2 — the `obj.__module__ == module.__name__` filter is behaviour-changing and entirely unpinned, and the report offers it as one of its three certified answers

`src/publishable/report.py:237`.

**Verified by running.** Deleting that clause leaves the **full, unfiltered** suite at **2685
passed, 1 skipped, 2 xfailed**. The report's § The three "not a proxy" answers, answer 2, cites
exactly this clause as what replaces H7a's marker-on-the-class — *"a class merely imported into the
namespace … is excluded on the direct fact instead"* — so an unmutated safety claim is doing the
work of a certification. `CLAUDE.md`: *a safety argument in a comment is a claim, and needs a
mutation like any other.*

The clause is **correct and load-bearing**, which is why the missing pin matters. I built the
discriminating fixture: a `report.py` that imports a sibling `BaseReport` subclass
(`<pkg>/shared_report.py`) and defines its own resolves to the locally defined class on shipped code,
and under the deletion earns a **wrong** `E-REPORT-OVERRIDE-CLASS` — *"defines 2 `BaseReport`
subclasses, not exactly one"*. That is the shape `reference.md` § A report override names as the
supported route (*"A renderer several experiments share is an ordinary import from a plugin, called
by each one's override"*), so the deletion breaks a documented route silently. A ~15-line test
closes it.

### Major 3 — M1's fixture rules out first-wins scans only, while the report and the design both claim "any pick is observable"

`tests/test_report.py:416` (`aaa_decoy_pkg`); the claim at
`.superpowers/sdd/2026-08-21-report-study/task-b3-report.md` (M1 bullet) and in the design's
mutation table (*"a scan finds both and must pick, and any pick is observable"*).

**Verified by running.** A scan mutation picking the alphabetically **first** candidate fails the
fixture (`'DECOY' == 'ENTRYPOINT-NAMED'`). A scan mutation picking the alphabetically **last**
candidate — the same defect, the other arm — leaves `tests/test_report.py` at **29 passed**, because
the decoy was renamed to sort *before* `cohort_pilot`, so last-wins resolves the right package by
coincidence. This is `CLAUDE.md`'s named trap in full: *a fixture with too few elements to
distinguish the candidate orderings* — two packages only ever distinguish two answers, and here they
distinguish one.

**Remedy verified:** with a decoy on **each** side (`aaa_decoy_pkg` and `zzz_decoy_pkg`), shipped
code passes and **both** scan mutations fail (`'AAA_DECOY_PKG' == 'ENTRYPOINT-NAMED'` and
`'ZZZ_DECOY_PKG' == 'ENTRYPOINT-NAMED'`). Three packages, and no pick a scan can make is right. The
claim in the report and in the design should either be sized to what the fixture rules out or the
third package added — the third package is cheaper and makes the broad claim true.

### Minor 4 — `report.py`'s module docstring says override discovery arrives in a later task

`src/publishable/report.py:5`: *"Nothing here dispatches: the real `report` command, **override
discovery**, and the standard sections arrive in later tasks. This module builds **only** the API
every override is written against."* Override discovery arrived in this commit, in this module. Read,
not run. `CLAUDE.md` lists this as the repo's most-repeated habit; **prefer deleting the clause to
rewriting it.**

### Minor 5 — a shipped test comment claims every fixture drives a real project, directly above eleven that do not

`tests/test_report.py:223`: *"Every fixture below runs a REAL project through `main(["run", …])` —
never a hand-built record."* The eleven shape tests immediately beneath it build records by hand
(`{}`, `{"config": {"entrypoint": None}}`, …) over hand-made run directories, and the M2 fixture
hand-edits a record — which the report itself says. The claim is true of the four named fixtures and
false as written. `tests/test_report.py:8` is stale from batch 2 onward for a second reason: *"there
is no `run`/`io` construction yet"*, while the M11 fixture constructs a `ReportIO`.

### Minor 6 — the report's own test count disagrees with its own arithmetic

`task-b3-report.md` § What was built, the `tests/test_report.py` paragraph: *"(+21 tests, one
parametrized ×8)"*, against the same document's breakdown of
5 + 3 + 8 + 4 = **20** and its own 2665 → 2685. Measured: `tests/test_report.py` holds **29** tests,
against 9 before this commit. 20 landed.

---

## What I certified, and how

**Attack 1 — the direct question, three ways. All three proxies verified impossible, by running.**

- **(a) Root package from the record, not a scan or a prefix.** `_root_package` reads
  `record["config"]["entrypoint"]` and touches nothing else. Positive half built and run: with two
  packages in one `src/`, repointing **only** the record's `entrypoint` at the decoy moves the answer
  from `ENTRYPOINT-NAMED` to `DECOY` — so the fact genuinely steers, rather than the predicate
  reading nothing. Negative half: the scan-first mutation fails M1's fixture (scope limited — see
  Major 3).
- **(b) Repo fact from `environment/repo_root.txt`, not `provenance.git.repo_root`, not a walk-up.**
  Negative half: substituting `provenance.git.repo_root` returns `'OTHER-PROJECT'` where shipped code
  returns `'TARGET-PROJECT'`. Positive half built and run: rewriting **only**
  `environment/repo_root.txt` to name a second project with the same package name moves the answer
  from `A` to `B`. No walk-up exists in the module, and I re-measured the brief's premise at **this**
  commit rather than trusting `ebf642a`: `find_repo_root(run_dir)` raises `E-GIT-NO-REPO` from inside
  `output_dir`, so a walk-up genuinely has nothing to find and the rejection of that mutation stands.
- **(c) The purge happens at the right moment.** `report.py:210-214` purges then inserts; read
  against `base_experiment.load_experiment:38-40`, the predicate is character-for-character the same
  (`name == root_pkg or name.startswith(root_pkg + ".")`), the order is the same, and the restoration
  mechanism is the same. The docstring's "re-implements by calling the same two steps in the same
  order" is therefore accurate. The *incomplete* half of that window is Major 1.

**Attack 2 — M15 reproduced in both forms, and its subtlety confirmed.** Deleting the purge fails
`test_fixture_o2_m15_...` with `'SECOND-PROJECT' == 'FIRST-PROJECT'`; narrowing it to the bare root
package fails the same test with `'FIRST-PROJECT' == 'SECOND-PROJECT'` — both exactly as the report
describes, including which title moves under which form. (I did not independently confirm the
report's `__path__`-caching *explanation* of why the first render is the one corrupted; the observed
failure is consistent with it.) **The blindness is real**: I built a single-project probe — one
render, and a second one of the same project — and it passes identically on shipped code and under
**both** mutated forms. No fixture without a second, same-named project can see this. Shipped code
passes.

**Attack 3 — the first draft's vacuity reproduced, and the reusable part named.** I renamed the decoy
back to `decoy_pkg` (its disclosed first-draft name) and applied the scan-first mutation:
`test_fixture_o_m1_...` **passes**. The disclosure is accurate and the current fixture does close
first-wins — two *packages*, one title observable. What made the first draft blind is not the count
but the **name**: `decoy_pkg` sorts after `cohort_pilot`, so the fixture's own naming agreed with the
bug — `CLAUDE.md`'s *a fixture whose numbers agree with the bug*. That the same fault survives
half-open for last-wins scans is Major 3.

**Attack 4 — four codes, individually reachable, individually pinned, rows covering every emit
site.** Each guard deleted in turn; every deletion is caught, and since each caught it inside
`tests/test_report.py` the full suite necessarily fails too:

| Deleted guard | What failed | How it failed |
|---|---|---|
| `repo_root.txt` missing | the missing-file test | **by a crash** — `FileNotFoundError` out of `read_text`, not a coded refusal |
| `repo_root.txt` empty | the empty test | falls through to no-override, then `E-REPORT-OVERRIDE-ENTRYPOINT` (`Path("")` is `PosixPath('.')`, a directory) |
| `repo_root` not a directory | the non-directory test | falls through to no-override, then `E-REPORT-OVERRIDE-ENTRYPOINT` |
| entrypoint shape | 4 of the 8 parametrized cases | the empty-string case is still caught by the malformed guard |
| entrypoint malformed | 3 of the 8 parametrized cases | as expected |
| `ModuleNotFoundError` branch | the no-module test | `E-REPORT-OVERRIDE-IMPORT` for an absent module — the fail-open's mirror image |
| `.name == module_name` narrowing | the missing-dependency test | a broken override read as "no override" |
| generic `except Exception` | the raises-on-import test | `RuntimeError` escapes uncoded |
| the exactly-one check | both class tests | as expected |

**The full-suite half of this attack is a measurement, not an inference.** `render_with_override` is
defined once and called from **nowhere outside `tests/test_report.py`** (`grep -rn` over `src/` and
`tests/` returns only its own definition) — task 8 has not wired it yet. So no test outside that file
can be reached by any of these deletions, and a deletion caught there is a deletion caught by the
full, unfiltered suite. I also ran two full unfiltered suites for the two mutations that came back
**green**, where a filtered run could have hidden a pin elsewhere (Majors 1 and 2): both 2685 passed,
1 skipped, 2 xfailed.

Rows: exactly one row per code in `docs/reference.md` § Errors `validate` reports, alphabetically
placed between `E-REPL-SEED-COLLISION` and `E-RESOLVER-UNKNOWN`, column counts matching neighbours,
no trailing whitespace, the `#a-report-override-renders-one-experiments-own-figures` anchor resolving.
Each row's wording covers **every** emit site of its code — REPO's three conditions, ENTRYPOINT's
two, IMPORT's two, CLASS's two — which is the check both preceding sub-slices failed.

Worth carrying rather than filing: `E-REPORT-OVERRIDE-REPO`'s three sites share one code and one
single-assertion test each, so a mutation that swaps *which* of the three fires is invisible, and the
missing-file arm is caught by a crash rather than by the property — the shape plan correction 12
rejects a mutation for. Asserting a message fragment rather than only the code would close both.

**The cited `freeze.py` precedent holds, checked against the code rather than the report's grep.**
`freeze.py:173-209` performs the identical three checks in the identical order under **one** code
(`E-FREEZE-NO-CONFIG`), with the same `Path(text)` / `.is_dir()` shape and no `resolve()` — so
`_read_repo_root` is a faithful copy, and the "three indistinguishable sites" note above is a
carry-forward rather than a finding, because the precedent shares it. The one exposure that shape
carries — a **relative** path in `repo_root.txt` resolving against the cwd rather than the run
directory — is hand-edit-only and shared with `freeze`: `cli.py:2350` writes the value
`provenance.find_repo_root` returned, and that function `resolve()`s its start, so every run this
build writes records an absolute path. Not a finding.

**Attack 5 — the extra-colon entrypoint: LEAVE, do not file.** Adjudicated by measurement, not by
reading. An entrypoint with a second colon earns `E-ENTRYPOINT-IMPORT` at **both** `validate` and
`run`, exit 1 at each, so **no record a real run writes can hold one** — the only route is a hand
edit. And silent resolution is the *right* answer anyway: `partition(":")` splits at the **first**
colon, so `"pkg.mod:Attr:extra"` yields root package `pkg`, which is correct; the extra colon
pollutes only the attribute half, which discovery does not use. Discovery also matches
`load_experiment`'s shipped shape exactly here, and minting a stricter check than the one gating the
config would be a second source of truth. Filing it would file a non-defect.

**Attack 6 — the `finally`, and the comment that does not exist.** There is **no** comment claiming
the window cannot leak; the docstring claims only *ordering* ("the render happens before `sys.path`
is popped … never after"), and that claim **is** pinned — M11 (moving only the success return outside
the `try`/`finally`) fails Fixture V with `ModuleNotFoundError: No module named 'report_helper'`. So
there is no unmutated "cannot happen" sentence to report. What the `finally` does on the failure path
I verified by probe rather than by reading — it does pop, on both the success and the refusal path —
and that behaviour is pinned by nothing, which is Major 1.

**Attack 7 — prose and pins.** Arm D did not fire. No positional locators, no bare `x` for
multiplication, no config-count claim, no trailing whitespace in the report. The report's build
claims check out against measurement: 90 formatted files, 50 mypy sources, 2685/1/2. Its M2 and M11
accounts reproduce exactly as written, including the observed titles. Two claim-versus-evidence
mismatches, both Minor above: the test count (Minor 6) and the "every fixture drives a real project"
comment (Minor 5). One report claim is broader than its evidence and is a Major because the design
carries it too (Major 3).

## What I could not check

- The report's **mechanism** account of why `title_1` rather than `title_2` moves under a deleted
  purge (the second project's own `main(["run"])` caching `cohort_pilot` with `__path__` at the
  second project's `src/`). The observed failure matches the claim; I did not instrument
  `sys.modules` to confirm the intermediate state.
- Whether the four new § Errors rows stay in step with the code: this repo has no test asserting that
  every `E-` code in `src/` carries a row, so the rows are pinned by review only. Consistent with
  prior slices, not a finding on this task.
- Anything about the renderer, `report`'s dispatch, or `report <study.yaml>` — out of this batch by
  construction. Brief step 4 is a statement here and is enforced in task 10.
