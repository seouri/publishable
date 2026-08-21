# Batch 6 (task 10): the bundle render, and its two cross-checks

Branch `h8c-report-study`. Ran `uv run pytest` directly, in the foreground, every time — no
monitor, no background wait, temp dirs cleared before each run.

## Status

Landed. Suite: baseline **2753 passed, 1 skipped, 2 xfailed** → **2776 passed, 1 skipped, 2
xfailed** (+23). mypy **50** (no new source file — task 10 adds no module). `ruff check .` and
`ruff format --check .` clean (90 files formatted, unchanged from batch 5). H8c moves no config
count: the four-row table stays 8 of 8 · 0 · 7 · 1.

## Commit SHA

- `a828ee9` — H8c task 10: the bundle render, and two cross-checks over recorded figures

## Test summary

2753/1/2 → 2776/1/2. 23 new tests: `read_bundle`'s refusal shapes (missing/invalid/non-mapping
`study.yaml`, non-mapping `runs`/entry, missing/absolute/escaping/absent `file`, a present-but-
corrupt member distinguished by code, declared order preserved); the full render through `main`
(all four standard sections per member plus the combined Hypotheses table, tagged by run name);
Fixture T's bundle arm (flags a draft member, exit 0, sibling sections still render); the two
Decision 8 cross-checks in all their named shapes (agree/differ/hand-edited-hash/null-excluded for
apparatus; same-commit-agree/hand-edited-mismatch/different-commit-no-notice for `code_hash`); the
"no discovery" negative both as a direct monkeypatch proof and as the fixture the plan names
(bundle beside a directory holding a real `report.py`). One pre-existing test
(`test_major_1_report_of_a_bundle_path_is_report_s_own_refusal_not_a_false_claim`) was rewritten in
place: its premise (`E-REPORT-BUNDLE-UNSUPPORTED`) no longer exists, so it now pins the same
property — `report`'s own coded refusal, never the CLI's generic diagnostic, never exit 2 — over
`E-STUDY-UNREADABLE` instead.

## What the task did

`report <study.yaml>` is real. `read_bundle(path)` parses `study.yaml` and every member it names,
in declared order, resolving each `runs.<name>.file` relative to the bundle directory
(`_resolve_bundle_member`, a `relative_to`-based containment check — the same shape
`artifacts.StepIO._contained` uses, restated because it is scoped to a run directory's own layout).
`render_bundle(bundle_dir, members)` builds every member's identity line (`run_id`, `status`, and a
`draft` label when the record carries one) plus its four standard sections via
`BaseReport().sections(record, io)` — **never** `render_with_override`, which stays the run form's
sole entry point into override discovery — then appends one combined `Hypotheses` table tagged by
run name. Always markdown: a bundle has no override to declare `format`. `_bundle_cross_checks`
groups members by `provenance.git.commit` and, within a group of two or more, compares recorded
`code_hash` strings and recorded `provenance.apparatus.hash` strings (excluding a `null` apparatus
from that second comparison) — never calling `hashes.code_hash` or `apparatus.apparatus_hash`.
`command_report`'s bundle branch wraps `read_bundle` + `render_bundle` in one `except ContractError`
(covering `E-STUDY-UNREADABLE`, the shipped `E-UPSTREAM-RECORD-*` family, and
`E-REPORT-RECORD-INCOMPLETE` for a member missing/malformed downstream of a clean parse), then
prints the two notices (if any) through a `Collector`, then the rendered text, and returns
`EXIT_OK` — no `Collector.credentials` populated, since the bundle path runs no user code.

`E-REPORT-BUNDLE-UNSUPPORTED` is deleted from the code and its `docs/reference.md` row struck —
retired wholesale, not narrowed, per `CLAUDE.md`'s "-UNSUPPORTED suffix" rule. `E-STUDY-UNREADABLE`
is minted for the bundle document's own shape faults; `E-REPORT-RECORD-INCOMPLETE`'s row widens to
name a bundle member (Decision 15's "the row widens" precedent for a fault with more than one
caller) rather than reminting a fifth code for the same shortfall. **Correction 17** (added to the
plan's § Corrections) rules the open identifier question: two new `W-` codes,
`W-STUDY-CODE-HASH-MISMATCH` and `W-STUDY-APPARATUS-MISMATCH`, with their § Warnings rows landing
in this commit, distinct from `study add`'s own `W-STUDY-COMMIT-MISMATCH` (a different notice, a
single run against `code.commit`, at add time — not built until task 13).

## Confirming the two things the brief asked for directly

**No override discovery happens on the bundle path.** Confirmed three ways. (1) By reading:
`render_bundle` never calls `render_with_override`, `get_template`, or `importlib.import_module`;
`command_report`'s bundle branch returns (`EXIT_OK` or `EXIT_WRONG`) before the function ever
reaches the run-form code that does call them — verified structurally by grep plus reading the
control flow (the bundle `if` returns before `get_template`/`render_with_override`'s single call
sites at lines 1402/1446). (2) By a direct monkeypatch test
(`test_bundle_render_never_calls_render_with_override`) that makes `render_with_override` raise if
called at all, then renders a bundle successfully through it. (3) By the plan's own named fixture
(`test_m_discovery_bundle_beside_a_report_py_shows_no_extra_section`): a bundle sits beside a real
project holding a `report.py` with a distinctly-titled extra section, and the title never appears.
**The discovery mutation** — wiring `render_with_override` into the per-member loop — was applied
for real and reverted: it failed 12 of the 24 bundle-scoped tests (every one that renders a bundle
at all, since a bundle member carries no `environment/repo_root.txt` and discovery raises
`E-REPORT-OVERRIDE-REPO`), including both of the tests built specifically to catch it. Reverted by
editing the file back (removing the inserted helper and the `render_with_override` call, restoring
`sections.extend(BaseReport().sections(record, io))`); verified by rerunning the same 24 tests,
all passing again; `git diff --stat` and a grep for the mutation's own text both confirmed nothing
was left applied.

**`report` never calls `apparatus_hash`.** Grepped `apparatus_hash` and `code_hash` across
`report.py`: the only hits are the docstring's own prose naming what is deliberately never called,
and two *local* names (`apparatus_hashes`, `code_hashes` — plural, the sets `_bundle_cross_checks`
builds from recorded strings) that are not calls to `publishable.apparatus.apparatus_hash` or
`publishable.hashes.code_hash` at all. Grep scope: `src/publishable/report.py` only — the module
this task owns; `diff.py`'s own real call to `apparatus_hash` (inside `Observer.block()`, a
different module entirely) is untouched and irrelevant to this claim.

## Mutations, run for real, reverted by editing back, reverts verified by rerunning

**M3 — recompute `apparatus_hash` over `facts` instead of comparing recorded `hash` strings.**
Applied by importing `apparatus_hash` and replacing the comparison set's construction with
`{apparatus_hash(app.get("facts") or {}) for _, app in apparatus_present}`. Result: **FAIL** on
exactly `test_bundle_apparatus_hand_edited_hash_disagrees_with_recomputation` (the hand-edited-hash
arm), **PASS** on the other three apparatus tests (agree / differ-under-one-commit /
null-excluded). This matches the design's own claim precisely: on every honest record the recorded
hash equals a recomputation, so the two readings are identical on every fixture except the one
whose recorded `hash` was deliberately edited to disagree with its own `facts`. A
property-preserving arm (any of the three untouched apparatus tests) is unaffected because its
members' facts and recorded hashes were never made to disagree in the first place — there is
nothing for the two readings to differ over. Reverted by restoring the original set comprehension
and removing the added import; verified by rerunning the 4 apparatus-scoped tests, all passing.

**The exclusion mutation — count a `null` apparatus as a mismatch.** Applied by dropping the
`isinstance(app, Mapping)` filter and folding a `null` apparatus into the hash set as `None`.
Result: **FAIL** on exactly `test_bundle_null_apparatus_excluded_not_counted_a_mismatch` (asserted
absence of the notice; the mutated code now emits it, naming `'None'` as one of the two disagreeing
hash values), **PASS** on the other three. A property-preserving arm (e.g. the agree/differ tests,
where both members already carry a non-null apparatus) is unaffected because the mutation only
changes behavior when a `null` enters the set at all. Reverted by restoring the `isinstance` filter
and the two-step build; verified by rerunning the 4 apparatus-scoped tests, all passing.

**The discovery mutation — perform override discovery on a bundle.** Described above under "no
discovery". Reverted and verified the same way (24 bundle-scoped tests, all passing after revert).

All three reverts additionally verified by a clean `__pycache__` sweep and rerun, and by
`git diff --stat src/publishable/report.py` returning to its post-commit shape before the final
full-suite run (2776/1/2, clean gates) that preceded this report.

## Fixture T's bundle arm

Built here, as task 9's own brief carried it forward by name:
`test_fixture_t_bundle_flags_a_draft_member_at_exit_0` hand-edits `draft: true` onto a real,
completed record (the shipped key; the `draft` command stays H9's and unbuilt), places it in a
two-member bundle beside a clean copy, and asserts exit 0, the word "draft" present, and the clean
member's own Conditions section still rendering — the pair that catches "refuse the whole bundle"
as well as "flag but print nothing".

## What was NOT built, and why

- **`generate report`'s decoy fixture** for the discovery test reuses `_build_project`/`_write_report`
  from task 3's own section rather than the full Fixture O/P apparatus machinery — sufficient for
  this task's negative claim (no discovery on the bundle path) without re-deriving task 3's own
  positive claims about the run form.
- **Fixture B's and Fixture A's full shape** (a real probe-registering plugin) was not built. Since
  `report` never calls `apparatus_hash` at all, only the two record fields it reads (`hash`,
  `facts`) matter to the code under test, so the apparatus tests hand-construct
  `provenance.apparatus` blocks with `apparatus.apparatus_hash` computed directly in the test for
  an honest baseline, and hand-edit one string where Fixture A's design calls for exactly that.
  Each such fixture's docstring says so.
- **`study new`/`study add` do not exist yet** (tasks 11/13) — every bundle in this file is written
  by hand (`_write_bundle`), the exact bytes `study add` will eventually produce, matching
  reference.md § Building one's own tree shape.

## Grep scope, stated rather than implied

- `apparatus_hash` / `code_hash`: `src/publishable/report.py` only, by name, both matched against
  every hit rather than filtered.
- `render_with_override` / `get_template` / `importlib.import_module`: `src/publishable/report.py`
  only, every hit read in context (not filtered to only the ones expected).
- `E-REPORT-BUNDLE-UNSUPPORTED`: repo-wide (`*.py`, `*.md`), confirming the only surviving hits are
  this task's own test (documenting the retirement) and prior dated ledger/report files (dev
  record, correctly left untouched).

No count phrase, positional row locator, or line-number citation appears above; document citations
are by section.
