# Batch 7 (tasks 11-14): `study` — bytes on disk, outside every repo

Branch `h8c-report-study`. Ran `uv run pytest` directly, in the foreground, every time — no
monitor, no background wait, temp dirs cleared before each run (and `__pycache__` cleared too).
Each task committed separately, in order 11 → 12 → 13 → 14.

## Status

Landed, all four tasks. Suite: baseline **2783 passed, 1 skipped, 2 xfailed** →
**2821 passed, 1 skipped, 2 xfailed** (+38, all in `tests/test_study.py`, new). mypy stayed at
**51 source files** through tasks 12-14 (`study.py` already existed after task 11; no new module),
`51` after task 11 as the plan's own gate literal states. `ruff check .` clean throughout.
`ruff format --check .` stayed at **92 files**, formatted, unchanged since task 11 (no new file
added after it). H8c moves no config count: the four-row table stays 8 of 8 · 0 · 7 · 1.

## Commit SHAs

- `c84a820` — H8c task 11: study new, outside any repo, refusing an existing bundle
- `35586e8` — H8c task 12: study add copies, redacts four fields, and names one run's commit
- `3b24652` — H8c task 13: study add refuses a used name before writing, and the study group
  answers for itself
- `30b69df` — H8c task 14: the min_reported_n prompt over the record's own entries, and the
  basis: repeats filing

## Test summary

2783/1/2 → 2821/1/2 (+38). Per task, counted from each commit's diff on `tests/test_study.py`:
11 added 11 tests; 12 added 9; 13 added 8 and removed 2 (the two task-11-time placeholders whose
"still not built until task 13" premise task 13 itself made false), net +6; 14 added 12
(`test_study.py` grew across all four commits rather than getting new files per task).

## What each task did

**Task 11 — `study new`.** New module `src/publishable/study.py`. `study_new(bundle, title)`
writes `<bundle>/study.yaml` with `title`, `authors: []`, `runs: {}` and no `code` block. Two
refusals, both before any write: `E-STUDY-IN-REPO` (`_refuse_if_in_repo`, using
`provenance.find_repo_root` and catching only `E-GIT-NO-REPO` as the pass branch — every other
`ContractError` propagates), then `E-STUDY-EXISTS` (checked against the `study.yaml` **file**, not
the directory). `cli.py` gained a `study` arm ahead of the `NOT_BUILT_COMMANDS` fallback,
`_dispatch_study_new` parsing `--title` explicitly and refusing an unrecognized option or a missing
title at exit 2 before touching disk. `"study new"` came out of `NOT_BUILT_COMMANDS` in the same
commit as the arm, and `"study add"` still routed to `_report_not_built` in this commit. Docs:
§ Creation commands' `study new` cell flipped to `built`; two new § Errors rows
(`E-STUDY-IN-REPO`, `E-STUDY-EXISTS`); the creation-command-family sentence in § Exit codes gained
`study new`.

**Task 12 — `study add` part 1 (copy, redaction, `code`).** `study_add` (no CLI arm yet) reads the
source through `lineage.read_record_file` (the file entry, not `read_run_record`'s directory one),
redacts four fields (`_redact`) and sets/compares the bundle's `code` block (`_apply_code_block`).
A field **present** in the source becomes the literal marker `<redacted by study add>`; absent or
`null` is left untouched — the two states carry the distinction, not two marker strings. Every
hash (`code_hash`, `parameters_hash`, `input_manifest_hash`) is untouched. `code.commit`/
`code.remote` are written on the bundle's first add (regardless of name) or replaced by a later
`--as main` add; any other later add leaves it and returns a `("W-STUDY-COMMIT-MISMATCH", message)`
pair rather than raising. Docs: § Warnings gained the `W-STUDY-COMMIT-MISMATCH` row.

**Task 13 — `study add` part 2 (duplicate-name refusal, CLI completion).** `study_add` gained
`E-STUDY-NAME-EXISTS`, checked against **both** `study.yaml`'s `runs` keys and the file on disk,
before the source record is even read. `cli.py` gained `_dispatch_study_add` (parses `--as`
explicitly, same discipline as `study new`'s `--title`) and `_dispatch_study` now dispatches both
subcommands directly; a missing/unrecognized subcommand is a usage error naming both `new` and
`add` rather than the old not-built diagnostic. `"study add"` came out of `NOT_BUILT_COMMANDS` in
this commit. The shipped `test_a_command_group_answers_for_its_unbuilt_subcommands` — whose
premise ("every subcommand it could name is unbuilt") was now false — was replaced outright
(renamed, docstring and body rewritten) rather than patched, per "prefer deleting a claim to
rewriting it." Task 12's own `test_apply_code_block_fixture_b_third_run_replaces_only_under_as_main`
had to change too: it originally re-added the name `"main"` twice, which task 13's refusal now
forbids — rebuilt with three distinct names (`aux`, `other`, `main`) so the "replaces only under
`--as main`" property still has a fixture that can show it.

**Task 14 — the `min_reported_n` prompt, and the filing.** `thin_metric_lines(record, floor)`
walks `_floor_metric_entries` — every metric-shaped entry (`_is_thin_checkable_entry`: carries
`basis`, or `reported: true`) across `results.conditions[].aggregated` (top-level AND `by` strata),
`vs_baseline`, `results.contrasts[]`, and `results.summary` — and compares each against `floor`
per Decision 13's three branches. `_confirm` prints the list to stdout and asks proceed-or-quit;
with no TTY it raises `E-STUDY-CONFIRM-REQUIRED` after printing the list but before any write.
`study_add` reads `floor` from the **bundled record's own** `config.limits.min_reported_n`, never
from a config in the working directory, and calls the prompt between reading the record and
writing anything — quitting returns `[]` having written nothing. Step 7's join test
(`test_study_new_add_report_join_through_main_end_to_end`) runs `study new` → `study add` ×2 →
`report <study.yaml>`, all through `main`. The filing
(`docs/superpowers/spec-defects.md`, new entry) records that no build path writes a
`basis: "repeats"` metric entry — Owner: unassigned, with the H8c/H4-both-wrong reasoning and the
disposition question stated rather than pre-decided.

## A defect found and fixed while building task 14

My first draft of `_floor_metric_entries` used the same `"value" in entry` structural test
`report.py`'s Conditions section uses to tell a real metric entry apart from a `by`-strata
sub-mapping. That test is right for `aggregated` entries (which carry `value`) but wrong for
`vs_baseline`/`results.contrasts[]` entries, which carry `delta` instead of `value` — so the first
version silently produced **zero** entries from either block, exactly the "silently skips `by`
strata and `vs_baseline`" failure Decision 13's own *Cost if wrong* names. Two tests I wrote
against hand-built `vs_baseline`/contrast entries caught it immediately (both failed with `assert
False` before the fix). Fixed by testing `"basis" in entry or entry.get("reported") is True`
instead — true of every shape in Decision 13's table, including the two `delta`-carrying ones —
and both tests pass under the corrected code. This was caught by my own tests before I ran any
prescribed mutation; noting it because the advisor consultation before writing flagged the same
risk from the design brief alone, and building the discriminating fixture first is what surfaced
the real bug rather than the advisor's prediction alone.

## Mutations run — exact text and outcome, against the full `test_study.py` (and targeted `test_cli.py` rows), reverted by editing back and re-run after each

**Task 11, step 5, mutation 1 — treat an existing directory as "existing."** Changed
`if (bundle / "study.yaml").exists():` to `if bundle.exists():` in `study_new`. **FAIL** (as
required): `test_study_new_onto_a_bare_directory_with_no_study_yaml_succeeds` failed with
`E-STUDY-EXISTS` where it expected success. Property-preserving arm: every other test in the file
(bundle never pre-existing as a bare directory) is unaffected, since `bundle.exists()` and
`(bundle/"study.yaml").exists()` agree whenever no directory was made first. Reverted; re-ran
`test_study.py` — 11/11 passed.

**Task 11, step 5, mutation 2 — check `E-STUDY-IN-REPO` after writing.** Moved the
`_refuse_if_in_repo` call to after `study.yaml` is written. **FAIL** (as required):
`test_study_new_refuses_inside_a_git_repo_and_writes_no_study_yaml` failed on
`assert not (bundle / "study.yaml").exists()` — exit code was still `EXIT_WRONG` (an exit-code-only
assertion would have passed), but the file was left behind. Property-preserving arm: an in-repo
check that still runs, just later, produces the identical refusal for every existing test that
doesn't inspect the bundle's own contents afterward. Reverted; re-ran — 11/11 passed.

**Task 12, step 6, mutation 1 — write the marker for an absent field too.** Changed
`if isinstance(environment, dict) and environment.get("hostname") is not None:` to
`if isinstance(environment, dict):` in `_redact`. **FAIL** (as required):
`test_study_add_leaves_hostname_untouched_when_absent_from_the_source` failed —
`'hostname' in {...}` where the test asserts absence. Property-preserving arm: Fixture Y's own
test (`hostname` present) is unaffected either way, since both branches redact a present value
identically — this is exactly why the fixture needs BOTH the present and absent case. Reverted;
re-ran — 20/20 passed at that commit.

**Task 12, step 6, mutation 2 — recompute `code.commit` as "the commit all runs share."** Replaced
`_apply_code_block`'s first-add/`--as main` branching with: always write on the first add; on any
later add whose commit differs from the existing one, set `doc["code"]["commit"] = None` instead
of leaving it alone. **FAIL** (as required), on both discriminating tests:
`test_apply_code_block_second_add_under_another_name_does_not_replace_and_notices` (expected the
first run's commit, got `None`) and `test_apply_code_block_fixture_b_third_run_replaces_only_under_as_main`
(same). Property-preserving arm: a bundle whose every add shares one commit can't tell the two
branches apart at all — which is why Fixture B needed three *pairwise-different* commits, not
one shared one. Reverted; re-ran — 20/20 passed.

**Task 13, step 4, mutation "M9" — let `study add` overwrite an existing name.** Removed the
`E-STUDY-NAME-EXISTS` check block entirely. **FAIL** (as required), on three tests at once:
both direct-refusal tests (`..._refuses_a_name_already_in_study_yaml_before_any_write`,
`..._refuses_a_name_whose_file_exists_even_if_study_yaml_was_hand_edited`) failed on
"DID NOT RAISE", and the through-`main` duplicate test failed on exit code (0 instead of 1).
Property-preserving arm: every test adding a fresh, never-before-used name is unaffected, since the
removed check never fires for those. Reverted; re-ran — 26/26 passed at that commit.

**Task 13, step 4, mutation 2 — check only `study.yaml`'s keys, not the file.** Changed the guard
to `if name in (doc.get("runs") or {}):`, dropping `or target.exists()`. **FAIL** (as required):
`..._refuses_a_name_whose_file_exists_even_if_study_yaml_was_hand_edited` failed with
"DID NOT RAISE" — the hand-edited `study.yaml` (entry deleted, file left in place) no longer
tripped the guard. Property-preserving arm: every test where the two sources agree (the ordinary
case) is unaffected, which is exactly why this fixture hand-edits `study.yaml` to make them
disagree. Reverted; re-ran — 26/26 passed.

**Task 14, step 6, mutation "M7" — list every metric.** Added an unconditional
`lines.append(f"{label}: MUTANT ...")` before the floor comparisons in `thin_metric_lines`.
**FAIL** (as required): `..._fixture_n_lists_only_the_thin_strata_a_proper_subset` failed,
`len(lines) == 10` where `4` was expected — the whole-condition `pred`/`metric` entries
(`n.completed: 12`, at the floor) leaked in alongside the four genuinely thin `by`-stratum entries.
Property-preserving arm: `test_thin_metric_lines_is_empty_when_nothing_is_thin` would also have
failed under this mutant (not run separately since the fixture-N test already demonstrates it);
the point of "proper subset" is that a record with SOME metrics above the floor and some below is
the only fixture that can tell "all" from "the thin ones" apart. Reverted; re-ran — 38/38 passed.

**Task 14, step 6, mutation "M8" — proceed silently with no TTY.** Short-circuited the
`E-STUDY-CONFIRM-REQUIRED` raise (`if False and not sys.stdin.isatty():`) and returned `True`
whenever `isatty()` is false instead. **FAIL** (as required):
`test_study_add_refuses_with_no_tty_and_writes_nothing` failed on "DID NOT RAISE". Property-
preserving arm: every TTY-attached test (`monkeypatch`'d `isatty` to `True`) is unaffected, since
the mutant's short-circuit only fires on the `False` branch. Reverted; re-ran — 38/38 passed.

**Task 14, step 6, mutation "M12" — compare against a working-directory config's floor.** Read
`Path.cwd() / "cwd_config.yaml"` and used its `limits.min_reported_n` when present, falling back to
the record's own otherwise. My first version of the discriminating test did not actually catch
this (see below); rewritten, it does. **FAIL** (as required) on the rewritten
`test_study_add_uses_the_bundled_records_own_floor_not_a_cwd_config`: with no TTY attached and a
cwd config declaring floor `1` (versus the record's own `10`), the honest code finds the `by`-
stratum metrics thin (6 < 10) and raises `E-STUDY-CONFIRM-REQUIRED`; the mutant finds nothing thin
(6 ≥ 1) and proceeds to write, so "DID NOT RAISE" is the failure. Property-preserving arm: a test
where both floors give the same verdict (e.g., both floors above or both below the data) can't
distinguish the two — which is exactly the "one floor makes the branches identical" trap the brief
names, and why the floors have to be chosen (10 vs. 1) rather than arbitrary. Reverted; re-ran —
38/38 passed.

**A vacuous-test near-miss, caught before it shipped.** My first draft of the M12 test set
`isatty` to `True` and monkeypatched `input` to `"y"` for both the honest and mutant code, then
asserted only that the file was written. Both branches wrote the file (with floor 10, the honest
code prompts and "y" answers it; with floor 1, the mutant finds nothing thin and never prompts at
all) — an assertion satisfied by neighbouring behavior in exactly the CLAUDE.md-documented shape.
Running it against the M12 mutant first (before trusting it) showed it passing under the mutant,
which is how I caught it; rewritten to use no TTY and assert the refusal, it now fails correctly
under the mutant and passes under the honest code.

## Verifications requested in the assignment

**Nothing is written on the duplicate-name refusal path.** Two direct tests snapshot the bundle
(path + bytes of every file) before a refused `study_add` call and assert the snapshot is
unchanged after — one hitting the `study.yaml`-keys check, one hitting the hand-edited-`study.yaml`
case that only the file-existence check catches. A third test drives the identical refusal through
`main(["study", "add", ...])` and snapshots around that call too. All three pass; the M9 and
"study.yaml-keys-only" mutations above are the ones that would have broken this guarantee, and both
were caught.

**The redaction marker distinguishes redacted from never-captured by the two STATES.** There is
exactly one marker string (`REDACTED = "<redacted by study add>"`); a field is either replaced by
it (present in the source) or left exactly as it was (absent, or explicitly `null`) — no second
marker exists anywhere in `study.py`. `test_study_add_leaves_null_fields_exactly_null_not_marked_redacted`
and `test_study_add_leaves_hostname_untouched_when_absent_from_the_source` (a real, un-synthesized
record) pin the "absent/null" side; `test_study_add_redacts_the_four_present_fields_but_keeps_every_hash`
and `test_study_add_redacts_hostname_when_present_on_a_synthesized_record` pin the "present" side.

**Every hash stays.** `test_study_add_redacts_the_four_present_fields_but_keeps_every_hash` asserts
`code_hash`, `parameters_hash`, and `provenance.input_manifest_hash` in the copied record are
byte-equal to the source record's.

**The prompt's third branch ships behind a synthesized record that says so, and the filing names
its owner.** `_fixture_y_record`'s docstring states it is "synthesized by hand, not one a real
`run` produced," names the exact measurement (`provenance.environment` is `{manager,
python_version, uv_lock, uv_lock_hash}` today), and the `basis: "repeats"` test's own docstring
repeats "Nothing in this build writes this shape." The filing in `spec-defects.md` is
`Owner: unassigned`, states why H8c cannot close it (writing into `aggregated` is `run`'s work) and
why H4 cannot be named (the family is complete, per this plan's own ledger sentence quoted in the
entry), and poses the disposition question (emitter owed vs. documents owed a rewrite) rather than
answering it.

## What I grepped, and its scope

- `grep -n '"basis"' src/publishable/` (the filing's own measurement) — five sites, all
  `"basis": "units"` (`cli.py` ×3 at the `vs_baseline`/contrast delta-entry construction,
  `stats.py` ×2 at the recorded-column and derived-metric construction in `summarize_step`).
  Scope: every occurrence of the literal string `"basis"` under `src/publishable/`, not filtered.
- `grep -n "W-STUDY-COMMIT-MISMATCH\|E-STUDY-" docs/reference.md` before and after each doc edit,
  to place new rows next to their siblings and confirm no duplicate code was minted.
- `grep -n "study_add(bundle" tests/test_study.py` after adding task 13's duplicate-name refusal,
  to find and fix the one place (Fixture B) that had been re-adding the name `"main"` twice and
  would now be refused by the very code that commit was adding.
- `grep -n ' $'` / `grep -nP '\t'` over `docs/reference.md` and `docs/superpowers/spec-defects.md`
  (the two files this batch edited) for the mechanical trailing-whitespace/tab check — none found.
- No claim above is broader than what these five greps actually covered; I did not sweep the whole
  four documents or `tests/` for either check.

## Concerns / things a reviewer should look at

- `_apply_code_block`'s notice is surfaced through `cli.py`'s own `Collector`, printed with
  `positional[0]` (the bundle path as given) as the "path" field — matches `report.py`'s own
  `_bundle_cross_checks` printing convention, but worth a second look since this is the first time
  a **single-run** `study add` (rather than a whole-bundle `report`) prints a warning this way.
- `_floor_metric_entries`' condition label uses `condition.get("label", condition.get("index"))`,
  which reads as `None` in several hand-built fixtures (no `"label"`/`"index"` key set) — cosmetic
  only, the label is never asserted on beyond substring checks in tests, but a real record's label
  would always be present.
- The `basis: "repeats"` filing states a disposition question rather than resolving it; whoever
  claims that entry should re-check whether the H4 family's completion still holds before choosing
  a side.

## Fix round 1

Review at `7e5f9b9` (`.superpowers/sdd/2026-08-21-report-study/task-b7-review.md`): both verdicts
FAILED — one Critical, three Majors (report named two explicitly; folding Major 1 and Major 2 as
findings below, consistent with the review's own numbering), six Minors. All closed in one commit.
Gates before this round: mypy 51, format 92, suite 2821/1/2. After: mypy 51, format 92, suite
**2823/1/2** (+2 net: the Critical's real-run pin and Minor 4's propagate-a-different-code pin;
every other change edited an existing test in place).

### CRITICAL 1 — `results.summary`'s nesting

Fixed in `_floor_metric_entries` (`src/publishable/study.py`): the `summary` loop now descends
`for step, block in summary.items(): for metric, entry in block.items():`, matching
`run_record.py`'s own producer (`summary[e.step_name] = summary_values(r.returned)`) and the
sibling idiom already in-repo at `report.py`'s `_execution_rows` (`execution.get("summary")`,
step-then-entry). Entry labels changed from `summary.{metric}` to `summary.{step}.{metric}`.

**Rebuilt the three fixtures the review named** (`tests/test_study.py`): the two `reported: true`
pins and the `basis: "repeats"` pin all moved their hand-built entry one level deeper, under a
`"step02_report"` key, so they exercise the corrected nesting rather than agreeing with the bug.

**Added a real-run pin**, `test_thin_metric_lines_finds_reported_estimates_on_a_real_run`: a
genuine `summary` step (`_SUMMARY_ESTIMATES_STEP`, run through `run_a_project`) returns two
`Estimate`s — `n=4` (below the floor) and `n=None` (no denominator at all) — and the test asserts
both `set(summary) == {"step02_report"}` (pinning the nesting itself against the real producer,
not just against a hand-built shape) and that both show up in `thin_metric_lines`'s output.

**Verified by running against the full, unfiltered suite, twice.** First, with the pre-fix code
restored and the real-run step source reproducing the review's own repro exactly (an `Estimate`
with `n=4` and one with `n=None`): `thin_metric_lines` returned `[]` before the fix — confirmed
independently, not just taken from the review. Second, after landing the fix, I re-broke it as a
regression check — reverted the `summary` loop to the one-level-short reading and ran the full
suite: **4 failed, 2819 passed** (the three rebuilt fixtures plus the new real-run pin, all and
only in `test_study.py`), then reverted by copying the pre-mutation file back and re-ran to confirm
2823/1/2. **Property-preserving arm:** any test whose record carries no `results.summary` at all
(every `aggregated`/`vs_baseline`/`contrasts`-only fixture in the file) is unaffected either way,
since the mutant only changes what happens when a `summary` block is present.

**Corrected the `basis: "repeats"` filing claim** (`docs/superpowers/spec-defects.md`, amended
entry, dated 2026-08-21): the fix closes the reachability gap for the `reported: true` branch
(now genuinely wired to what `run` writes) but the amendment is explicit that this does **not**
touch the entry's substance — `basis: "repeats"` is still written nowhere, the disposition
question is unchanged, and the entry stays OPEN, Owner: unassigned. The entry is amended rather
than rewritten, per this file's own convention for a correction against a live record.

### MAJOR 1 — `E-STUDY-UNREADABLE`'s § Errors row

Widened the row (`docs/reference.md`) to name both callers: `report <study.yaml>` reading the
whole bundle document, and `study add` reading the bundle it is about to add into
(`_load_study_doc`) before checking anything else. No code change — this is purely correction 6's
"the row lands in the commit that raises the code," applied one batch late.

### MAJOR 2 — the join arm's exit-code-only assertion

`test_study_new_add_report_join_through_main_end_to_end` now captures stdout around the `report`
call and asserts `"## main"` and `"## sensitivity"` (the exact heading `_bundle_header_section`
writes) both appear, plus each run's own `run_id` line. **Verified by running against the full
suite, both ways.** Confirmed the strengthened assertions pass today. Then mutated
`report.py`'s `render_bundle` (a one-line change: dropped the `sections.append
(_bundle_header_section(...))` call, restored by copying the pre-mutation file back afterward,
never `git checkout`) and ran the full suite: **3 failed** — the join test itself (on the new
`"## main" in out` assertion) plus two pre-existing `test_report.py` bundle tests. Confirms the
exact shape the review named: an exit-code-only assertion would have passed this mutant, since
`main(["report", ...])` still returns `0` when the render is missing its per-member headers.
Reverted; full suite back to 2823/1/2. **Property-preserving arm:** a mutation that reorders the
two `study add` calls, or renames a run, leaves both headers present under different labels — the
assertion would still discriminate correctly on content, just against different names; not tested
separately since the review's own repro (omitting the header) is the direct hit on what changed.

### MINOR 1 — the docstring crediting the wrong test

Rewrote `_dispatch_study_new`'s docstring (`src/publishable/cli.py`) to state plainly that
`test_reference_cli_tables_match_what_the_cli_does`'s `built`-row branch checks neither exit code
nor disk state, that removing the arity/`--title` check still passes it (falling through to
`_refuse_if_in_repo` instead, since the probe path resolves inside this repo), and that
`tests/test_study.py`'s own direct `main(...)` calls are what actually pin the property. No test
change: the existing `test_study_new_probe_arity_from_the_cli_table_test_writes_nothing_here`
already asserts the exit code directly, which the review confirmed does discriminate.

### MINOR 2 — the prompt's labels

Two independent fixes in `_floor_metric_entries` (`src/publishable/study.py`): the condition label
now tests `is None` explicitly (`.get("label", default)`'s default fires only on a *missing* key,
never on a present `null`) before falling back to `index`; and the `by`-strata label no longer
folds `metric` (which is already the literal string `"by"`) into the path a second time, closing
the `...by.by[cohort=a]...` doubling. Verified by re-running the no-TTY refusal test with `-s` and
reading the printed lines directly — confirmed clean (`condition 0.aggregated...by[cohort=a]...`)
where before they read `condition None.aggregated...by.by[cohort=a]...`.

### MINOR 3 — quitting the prompt is silent

`study_add` now prints `"Quit — nothing was added to the bundle."` (stdout) on the quit path,
before returning `[]`. `test_study_add_writes_nothing_when_quit_at_a_tty` gained a `capsys`
assertion for it. Decision 13's own rule ("quitting writes nothing," no exit code specified) is
unchanged — this only makes the outcome legible at the terminal.

### MINOR 4 — the unpinned "every other `ContractError` propagates" claim

New test, `test_refuse_if_in_repo_propagates_any_other_contracterror_unexamined`: monkeypatches
`publishable.study.find_repo_root` to raise a `ContractError` coded `E-SOMETHING-ELSE` and asserts
`study_new` lets it through unchanged. No code change — the claim already held; it needed a
mutation-shaped fixture, not a fix.

### MINOR 5 — the two weak substring assertions

Both `"new" in err` / `"add" in err` pairs (`tests/test_study.py` and `tests/test_cli.py`)
replaced with an exact-string comparison against the full usage message. Verified by running: both
pass against the real message today, and — being exact-string rather than substring — no longer
pass for "many plausible rewordings" the way the review characterized the original pair.

### MINOR 6 — the unpinned print half of `E-STUDY-CONFIRM-REQUIRED`'s § Errors row

`test_study_add_refuses_with_no_tty_and_writes_nothing` gained a `capsys` assertion: the header
line and all four `n.completed=6 < 10` entries must reach stdout even though the refusal itself is
printed to stderr by `main`'s own `except PublishableError`. Verified by running — both streams
checked in the same test.

### What I did not close, and why

Nothing from the review is left open. The two "Notes for task 16, not findings against this
batch" items (§ Exit codes' creation-command sentence omitting `E-STUDY-NAME-EXISTS`; `study add`
performing no `_refuse_if_in_repo` of its own, holding transitively through `study new`) are
explicitly scoped by the review to task 16's audit, not to this batch — left untouched.
