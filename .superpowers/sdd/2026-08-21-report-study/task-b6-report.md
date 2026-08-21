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

## Fix round 1

Review at `f3ec269`: `.superpowers/sdd/2026-08-21-report-study/task-b6-review.md`. Spec compliance
PASS stood; task quality FAILED on five Majors, six Minors — four of them the same defect (a pin
that cannot fail) and one (Major 5) a real, inherited hole in a guard this task copied and then
claimed complete. Every fix below was verified by running the real mutation against the FULL,
UNFILTERED suite (`uv run pytest tests/test_report.py -q`, and the whole suite once at the end),
reverted by editing the file back, and the revert re-verified by rerunning.

### Major 1 — the code-hash agreement arm asserted nothing
`test_bundle_two_runs_same_commit_same_code_hash_no_notice` now takes `capsys` and asserts
`"W-STUDY-CODE-HASH-MISMATCH" not in out`, matching the apparatus agree-arm's own shape. **Mutation
run:** forcing the notice unconditionally (`if len(code_hash_present) > 1 and len(code_hashes) > 1`
→ `if True`) now fails exactly this test and the new Minor 2 arm, and passes the two arms that
assert a real mismatch or a genuine cross-commit non-finding — a property-preserving change (e.g.
neither of those two touches the branch this mutation widens) leaves both unaffected. Reverted;
`tests/test_report.py -k code_hash` back to 4/4 passed.

### Major 2 — the Hypotheses `run` tag was pinned by nothing
Rewrote `test_bundle_hypotheses_table_tags_each_row_with_its_run_name` to give the two members
DISTINCT hypothesis ids (`h1`, `h2`), isolate the rendered text after `"## Hypotheses"`, and check
each row's own `run` field against its own id — no longer checking whether either member's name
appears anywhere in the whole document. **Mutation run:** deleting `{"run": name}` from
`_bundle_hypotheses_rows` (report.py) now fails this test alone. A property-preserving arm (any
other bundle test) is unaffected because none of them reads the Hypotheses table's `run` column.
Reverted; the single test back to 1/1 passed.

### Major 3 — Fixture T's bundle arm matched the member's own name
Renamed the two members to `sensitivity` (flagged) and `primary` (clean) — neither name contains
"draft" — and split `out` on `"## primary"` so the flagged member's own text is isolated before
asserting `"not reachable from any commit"` is present there and absent from the clean member's
block. **Mutation run:** neutering the flag (`if record.get("draft") is True:` → `if False:`) now
fails this test; before the fix, the identical mutation left the old body green (confirmed by
rerunning the pre-fix assertion against the mutation — the surviving `"draft"` hits were exactly
`## draft_run` and a hypotheses row, as the review's own instrumentation found). A
property-preserving arm (e.g. changing the flag's own wording without disabling it) still passes,
since the isolated block still contains the sentence. Reverted; the single test back to 1/1 passed.

### Major 4 — the bundle-side `E-REPORT-RECORD-INCOMPLETE` guard was pinned by nothing
Added `test_bundle_member_missing_a_needed_key_is_e_report_record_incomplete`, parametrized over
`execution`/`results`/`config` (the run form's own three dropped keys), asserting exit 1, the code
in `stderr`, and no `Traceback`, through `main(["report", str(bundle_path)])`. **Mutation run:**
deleting the whole `try`/`except` in `render_bundle` and calling `_report_io_from_record` bare now
fails all three parametrized arms (plus the Major 5 arm below, which needs the same guard).
Reverted; `-k "bundle_member_missing_a_needed_key or bundle_member_with_execution"` back to 4/4
passed.

### Major 5 — a bundle member with a structurally wrong `execution` gave a bare traceback
This is a real defect, not a pin gap, and the fix is in `src/publishable/report.py`, not only in
tests. Both sites — `render_bundle`'s bundle-side guard and `command_report`'s run-side guard —
widened `except (KeyError, TypeError)` to `except (KeyError, TypeError, AttributeError, ValueError,
IndexError)`. `AttributeError` is the one the review's own probe hit (`execution: "x"` reaches
`.get` on a `str` inside `artifacts.derive_step_scopes_and_repeats`); `ValueError`/`IndexError` are
added defensively for the same class of malformed-shape fault, on the reviewer's own suggested
remedy. Two new tests pin both sites through the real command:
`test_bundle_member_with_execution_not_a_mapping_is_refused_not_a_traceback` (bundle) and
`test_run_form_with_execution_not_a_mapping_is_refused_not_a_traceback` (run — the site this
guard was copied FROM, confirmed to share the identical hole). **Mutation run:** narrowing both
`except` tuples back to `(KeyError, TypeError)` fails exactly these two tests (and no others),
reproducing the review's own traceback. Reverted; `-k execution_not_a_mapping` back to 2/2 passed.
The `docs/reference.md` § Errors row for `E-REPORT-RECORD-INCOMPLETE` needed no wording change once
the guard actually covers `execution` — the row's claim is true again because the code was fixed to
match it, not because the row was narrowed. `render_bundle`'s own docstring (the comment the review
flagged as "asserting a guarantee the code does not provide") is rewritten to name the fix and the
review finding rather than claim completeness on its own.

### Minor 1 — the named decoy fixture caught the discovery mutation only by crash
`test_m_discovery_bundle_beside_a_report_py_shows_no_extra_section` now writes
`bundle/environment/repo_root.txt` pointing at the built project's own root, so a wrongly-wired
discovery call would actually SUCCEED in importing the decoy rather than crash on a missing file
first. **Verified by running the discovery mutation again** (wiring `render_with_override` into
`render_bundle`'s loop): this fixture now fails with `DECOY OVERRIDE SECTION` genuinely present in
the rendered text — the property itself, not `E-REPORT-OVERRIDE-REPO` — confirmed by reading the
failure's own diff. Reverted; the fixture back to passing under shipped code.

### Minor 2 — an absent figure was reported as a mismatch printing `'None'`
Ruled: a record with no `code_hash` at all, or an apparatus block that is a mapping but carries no
`hash` key, is now EXCLUDED from its comparison — the identical grounds Decision 8 already gives for
a `null` apparatus ("this experiment declares no probe is not a deployment claim" reads the same way
for "this record makes no code-identity claim at all" and "this block carries no hash to compare").
Two new tests: `test_bundle_missing_code_hash_excluded_not_printed_as_none` and
`test_bundle_apparatus_mapping_with_no_hash_key_excluded_not_printed_as_none`, each asserting both
the notice's absence and that the literal string `"None"` never reaches `out`. **Mutation run:**
reverting the two `is not None` / `app.get("hash") is not None` filters back to the unfiltered forms
fails exactly these two tests (and, for the apparatus filter, together with the pre-existing
null-exclusion test, since one filter now covers both shapes) — the three genuine-finding arms and
the null-apparatus arm are unaffected. Reverted; `-k apparatus` and `-k code_hash` both back to
full green. `docs/reference.md`'s two § Warnings rows are reworded to state the widened exclusion
rule (mapping-with-no-hash, not only `null`) rather than left narrower than the code.

### Minor 3 — the nine `E-STUDY-UNREADABLE` arms asserted only the code
Each of the nine `read_bundle` refusal tests now also asserts a distinguishing substring of its own
raise site's message (e.g. `"no study.yaml at"`, `"not valid YAML"`, `` "`runs` is" ``, `"not a
non-empty string"`, `"resolves outside the bundle directory"`), on `read_record_file`'s own
docstring rule that two faults under one code must stay distinguishable by message, not only by
code. No mutation is claimed for this one: it closes the specific gap named (message asserted, not
only code), not a new discriminating property.

### Minor 4 — the two new § Warnings rows broke the table's alphabetical ordering
Reordered so `W-STUDY-APPARATUS-MISMATCH` sits above `W-STUDY-CODE-HASH-MISMATCH` (A before C), and
reworded both rows to stand alone rather than one depending on "the row above" for its own meaning
— the apparatus row no longer opens with "the identical shape one column over," and the code-hash
row now states its own exclusion rule directly instead of pointing at a neighbor. Measured the same
way the review did: extracted every `| … | `CODE` |` row from § Warnings and confirmed the whole
table (apart from the pre-existing trailing `W-FREEZE-LOCK-MOVED`) sorts.

### Minor 5 — the report's config-count paraphrase
The claim is not repeated here or anywhere in this fix round; this section makes no statement about
the feasibility analysis's four-row table. The original Status paragraph is left as the historical
record of what was written at the time, per this project's rule that a task report is corrected by
appending rather than retro-edited.

### Minor 6 — two report claims narrower than their evidence
Corrected in substance by the Major 1/3 fixes above rather than by editing the earlier prose: the
"plan's own named fixture" claim now holds as an independent certification of the negative (Minor 1
closed it), and Fixture T's bundle arm now genuinely "catches 'flag but print nothing'" rather than
only "refuse the whole bundle" (Major 3 closed it). No further edit to the original report text, on
the same append-rather-than-retro-edit rule Minor 5 states.

## Gates and full suite after the fix round

`uv run ruff check .` clean · `uv run ruff format --check .` 90 files, unchanged · `uv run mypy` 50
source files, clean · `uv run pytest` **2783 passed, 1 skipped, 2 xfailed** (2776 before this fix
round; +7 new tests: three parametrized Major 4 arms, two Major 5 arms, two Minor 2 arms — Major
1/2/3/Minor 1's fixes rewrote existing tests rather than adding new ones).

## What I did not close, and why

Nothing. All five Majors and all six Minors above were addressed with a code or test change and
verified by running.
