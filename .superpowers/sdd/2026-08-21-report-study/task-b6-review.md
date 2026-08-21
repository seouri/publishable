# Batch 6 review (task 10): the bundle render, and its two cross-checks

Reviewed at `f3ec269` on branch `h8c-report-study`. Every mutation below was applied for real,
run with `uv run pytest` in the foreground, and reverted by editing the file back; each revert was
verified by re-running the affected tests. Temp dirs and `__pycache__` cleared before runs. **The
tree is clean** — `git status --porcelain` empty, `git diff HEAD` empty.

## Verdicts

**Spec compliance: PASS.** Decision 8's two negatives hold, and hold *structurally* rather than by
convention. Correction 17's ruling is sound and both § Warnings rows landed in the same commit as
the codes. `E-REPORT-BUNDLE-UNSUPPORTED` is retired wholesale from code and from `reference.md`.
The draft flag exists, is reachable, and **renders** — verified by instrumenting the shipped test
to print every "draft"-bearing output line under unmutated code: the
`**draft** — this run's code state is not reachable from any commit …` sentence is there. Major 5
is a document/code gap rather than a compliance failure only because the § Errors row it falsifies
was **already** false for the run form before this commit widened it; compliance is graded here on
Decision 8, correction 17 and the brief's eight steps, all of which hold.

**Task quality: FAILED.** Four of the batch's own load-bearing pins cannot fail. Three of them are
the exact shapes `CLAUDE.md` counts by name — a test whose *name* claims the guarantee, a fixture
identifying by name, a correct fix shipped unpinned — and one of them is the arm the brief singled
out and asked the report to confirm it had built (it was built; it is vacuous). The report states
these pins as evidence for properties they do not test.

## Gates, verified by running

`uv run ruff check .` clean · `uv run ruff format --check .` 90 files, unchanged · `uv run mypy`
50 source files, clean · `uv run pytest` **2776 passed, 1 skipped, 2 xfailed** — matching the
report exactly. Arm D (`tests/test_diff.py:1380`, the no-editor guard pin) passes; it did not fire.

## The negative, certified independently (attack 1)

**It holds, and on stronger grounds than the report argues.** Enumerated by reading, then confirmed
by grep, not the reverse:

- `src/publishable/report.py:13, 889` — `importlib.import_module` appears once, inside
  `render_with_override`. `src/publishable/report.py:1402,1416` — `get_template` and
  `credential_values`/`declared_credential_names_for` appear only in `command_report`'s run arm,
  **after** the bundle arm (`if form == "bundle"` at 1317) has returned at 1349. No `eval`/`exec`/`__import__`/entry-point
  resolution anywhere in the module.
- `report.py` imports nothing from `publishable.hashes` or `publishable.apparatus` at all
  (verified against lines 13-29).
- The four standard sections take `run` **only** — `conditions_section(run)`, `deltas_section(run)`,
  `hypotheses_section(run)`, `attrition_section(run)`. `BaseReport.sections`'s `io` parameter is
  therefore unreachable by construction, not merely unused; correction 13's claim is stronger than
  "no task may claim it is exercised" implies.
- Both readers are `yaml.safe_load` (`report.py:1032`, `lineage.py:70`) — no object construction
  from member bytes.

**The discovery mutation reproduced.** I wired `render_with_override(bundle_dir, record, …)` into
`render_bundle`'s per-member loop: **12 failed, 102 passed** in `tests/test_report.py` — the same
12 the report names, including both purpose-built tests. Reverted; re-ran, 114 passed.

**One qualification the report does not carry** — see Minor 1: of those 12, only
`test_bundle_render_never_calls_render_with_override` fails by the *property*. The named decoy
fixture fails by a *crash*.

## Decision 8's honesty constraint (attack 2): verified, both ways

- **`report` never calls either hash function.** Verified by grep over `report.py` (every hit read
  in context: two docstring mentions, `record.get("code_hash")` at 1099, `app.get("hash")` at 1116,
  and two local plural names) **and** by reading the import block. No `from publishable.hashes` /
  `from publishable.apparatus` line exists.
- **M3 reproduced independently.** Replacing the recorded-string set with
  `{apparatus_hash(app.get("facts") or {}) …}` fails **exactly**
  `test_bundle_apparatus_hand_edited_hash_disagrees_with_recomputation` and passes the other three
  apparatus arms — the fixture does separate the two readings, for the reason the design gives.
- **The exclusion mutation reproduced.** Folding a `null` apparatus in as `{}` fails **exactly**
  `test_bundle_null_apparatus_excluded_not_counted_a_mismatch`. That fixture does separate
  "excluded" from "counted a mismatch": under shipped code `len(apparatus_present)` is 1, so the
  comparison is skipped outright.

## Findings

### Major 1 — the code-hash *agreement* arm asserts nothing about the notice
`tests/test_report.py:2550` (`test_bundle_two_runs_same_commit_same_code_hash_no_notice`)

The test takes no `capsys` and its only assertion about `report` is `code == EXIT_OK` — which
`command_report`'s own docstring guarantees is unchanged by either notice. **Verified by running:**
I made `_bundle_cross_checks` emit `W-STUDY-CODE-HASH-MISMATCH` unconditionally for every
same-commit group (`report.py:1100`, `if len(code_hashes) > 1` → `if True`) and **all 114 tests in
`tests/test_report.py` passed.** The sibling
`test_bundle_no_code_hash_notice_across_two_different_commits` does assert absence but is blind to
this mutation, because its two members sit in groups of one and never reach the comparison.

So half of `W-STUDY-CODE-HASH-MISMATCH`'s pin is missing: nothing anywhere in the suite can see a
false code-hash mismatch on two honest runs of one tree. Note the asymmetry the report does not:
the *apparatus* agree-arm does assert `"W-STUDY-APPARATUS-MISMATCH" not in out`.

Remedy: add `capsys` and `assert "W-STUDY-CODE-HASH-MISMATCH" not in out`.

### Major 2 — the Hypotheses `run` tag is pinned by nothing; the test's name is the only place the property is asserted
`tests/test_report.py:2420` (`test_bundle_hypotheses_table_tags_each_row_with_its_run_name`)

The assertions are `"baseline_run" in text` and `"second_run" in text`. Both are satisfied by
`_bundle_header_section` (`report.py:1146`), which returns `Section(title=name, …)` and so renders
each member name as a `##` heading regardless of what `_bundle_hypotheses_rows` does. **Verified by
running:** changing `row: dict[str, Any] = {"run": name}` to `{}` at `report.py:1163` — deleting
the `run` column from every hypotheses row — leaves **all 114 tests passing.** This is `CLAUDE.md`'s
"a test whose **name** claims the guarantee": a reader greps for exactly this name and stops looking.

Remedy: assert on the combined table's own rows — e.g. that the `run` header column exists and that
the row carrying `h1` also carries `baseline_run` — rather than on the name appearing anywhere.

### Major 3 — Fixture T's bundle arm cannot see the draft flag; it matches the member's own *name*
`tests/test_report.py:2439` (`test_fixture_t_bundle_flags_a_draft_member_at_exit_0`)

This is the arm the brief carried forward from task 9 by name and asked the report to confirm. It
was built, and it is vacuous. `assert "draft" in out` is satisfied by the fixture's own member name,
`draft_run`, which renders as the `## draft_run` heading. **Verified by running:** neutering the flag
in `_bundle_header_section` (`report.py:1140`, `if record.get("draft") is True:` → `if False:`) leaves
**all 114 tests passing**; I then instrumented the test to print every line of `out` containing
"draft" under that mutation, and the two surviving lines are `## draft_run` and the hypotheses row
tagged `| draft_run | h1 | …`. Both come from the name the test chose. **The behaviour itself is
correct** — the same instrumentation under unmutated code shows the flag's own sentence in `out` —
so this is a vacuous pin over a working feature, not a broken feature.

This is `CLAUDE.md`'s "identifying by name is a proxy" — the seventh instance on this project — and
it lands on the one test whose whole existence is Decision 7's asymmetry. As shipped, `report
study.yaml` could stop flagging drafts entirely and the suite would not notice.

Remedy: name the member something without "draft" in it (`sensitivity`, say) and assert on the flag's
own sentence, not the substring.

### Major 4 — the bundle-side `E-REPORT-RECORD-INCOMPLETE` is documented in this commit and pinned by nothing
`src/publishable/report.py:1199-1209`; `docs/reference.md` § Errors `validate` reports (the
`E-REPORT-RECORD-INCOMPLETE` row, widened here to say "Also raised over a bundle member")

`grep -n "E-REPORT-RECORD-INCOMPLETE" tests/` returns exactly one hit, at `tests/test_report.py:2198`
— inside `test_major_2_a_record_missing_a_needed_key_is_refused_not_a_traceback`, which goes through
the **run** form. The bundle arm has its own `except`, its own distinct message ("bundle member
{name!r} parses and has a `run_id` …"), and a § Errors row widened for it **in this commit**, with
no test reaching it. **Verified by running:** deleting the whole `try`/`except (KeyError, TypeError)`
in `render_bundle` and calling `_report_io_from_record` bare leaves **all 114 tests passing.** I
confirmed the arm *is* reachable by probe — a bundle whose member holds only `run_id` and
`schema_version`, through the real console script, gives
`error E-REPORT-RECORD-INCOMPLETE … bundle member 'main' parses and has a run_id, but is missing or
malformed at KeyError('execution')` at exit 1.

This is the row-and-no-pin sibling of correction 6: the row landed in the right commit, the pin did
not land at all. `CLAUDE.md` counts a correct fix shipped unpinned six times in three slices; this
is seven.

### Major 5 — a bundle member with a structurally wrong `execution` gives a bare traceback out of a built command
`src/publishable/report.py:1201` (`except (KeyError, TypeError)`), reached through
`artifacts.py:460`

**Verified by running, through the real console script**, not reasoned. A bundle whose member is a
clean-parsing record (`run_id`, correct `schema_version`, `results.conditions`,
`config.data.input_dir`) with `execution: "x"` or `execution: []`:

```
  File ".../report.py", line 1200, in render_bundle
    io = _report_io_from_record(bundle_dir, record)
  File ".../artifacts.py", line 460, in derive_step_scopes_and_repeats
    for step in execution.get("shared") or {}:
AttributeError: 'str' object has no attribute 'get'
```

`AttributeError` escapes `render_bundle`'s `except (KeyError, TypeError)`, escapes
`command_report`'s `except ContractError`, and escapes `main`'s `except PublishableError` /
`except OSError` — a raw traceback out of a built command.

**The sharper form: the § Errors row widened in this commit is false for a shape it enumerates by
hand.** `E-REPORT-RECORD-INCOMPLETE`'s row says the code fires when a record "is still missing or
malformed at `execution`, `results.conditions`, or `config.data.input_dir`". `execution: "x"` is
malformed at `execution` — the first of the three the row names — and produces a traceback rather
than that code. So this commit widened a row to cover a bundle member while the row was already
false for one of its own enumerated shapes. That is the row-versus-code class `CLAUDE.md` tracks,
arriving through the document rather than through the code. `render_bundle`'s own docstring makes it
worse by asserting `KeyError`/`TypeError` *is* "the identical fault" set — a comment claiming a
guarantee the code does not provide.

**Attribution, stated because it changes the remedy:** the run form has the *same* hole — I ran the
identical record through `report run.yaml` and got the same traceback — so task 10 inherited the
narrow guard rather than introducing it. It is graded here because this task copied the guard, wrote
a docstring claiming it is complete, and widened a § Errors row over it. Not Critical: no user code
runs on this path, so nothing credential-bearing reaches stderr (checked — the traceback carries
only filesystem paths). Remedy: widen both sites to `except (KeyError, TypeError, AttributeError,
ValueError, IndexError)`, or guard `derive_step_scopes_and_repeats`'s own argument shape once.

### Minor 1 — the named decoy fixture catches the discovery mutation only by *crash*, never by its own assertion
`tests/test_report.py:2494` (`test_m_discovery_bundle_beside_a_report_py_shows_no_extra_section`)

Its docstring claims "under shipped code the extra title never appears, because nothing on the
bundle path ever imports `<pkg>.report`". But the bundle directory holds no
`environment/repo_root.txt`, so any discovery call from there raises `E-REPORT-OVERRIDE-REPO` before
reaching an import — the fixture cannot distinguish "no discovery" from "discovery that crashes".
**Verified by running:** under the discovery mutation, adding
`bundle/environment/repo_root.txt` pointing at the built project makes `DECOY OVERRIDE SECTION`
render for real (that probe test failed); under shipped code the same probe passes. This is the
plan's own rejected-mutation rule ("caught by a crash rather than by the property") applied to a
fixture rather than a mutation. The negative is carried by
`test_bundle_render_never_calls_render_with_override` alone. Remedy: write the `repo_root.txt` into
the fixture, which costs two lines and makes the assertion load-bearing.

### Minor 2 — an absent figure is reported as a mismatch naming the string `'None'`, and Decision 8 rules only the `null`-apparatus case
`src/publishable/report.py:1099, 1116`

Verified by calling `_bundle_cross_checks` directly on two same-commit members, one lacking
`code_hash` and one whose `provenance.apparatus` is a mapping with no `hash` key:

```
W-STUDY-CODE-HASH-MISMATCH | runs a, b all record commit c1 and their code_hash differs (['None', 'sha256:aa'])
W-STUDY-APPARATUS-MISMATCH | runs a, b all record commit c1 and their provenance.apparatus.hash differs (['None', 'h1'])
```

Two things: the notice prints Python's `None` repr where a reader expects a hash; and the apparatus
exclusion's own reason ("this experiment declares no probe is not a deployment claim") arguably
covers a block with no `hash` too, which the `isinstance(app, Mapping)` filter admits. Both need a
hand-edited record, which is why this is Minor. It is unruled and untested either way — the
discriminating question is whether a *missing* figure is a mismatch or an exclusion, and Decision 8
answers it for one of the two shapes only.

### Minor 3 — the nine `E-STUDY-UNREADABLE` arms assert only the code, never a message
`tests/test_report.py:2286-2382`

`E-STUDY-UNREADABLE` now covers eight distinguishable faults (absent, invalid YAML, non-mapping doc,
non-mapping `runs`, non-mapping entry, `file` absent/non-string, `file` escaping, `file` not there),
and each raise site does carry its own message — I read all eight. But every test asserts
`excinfo.value.code` and nothing else. The rule against this is written in the docstring of the very
function these tests call: `lineage.read_record_file` argues that two faults under one code "stay
distinguishable by MESSAGE, not only by code — since a single assertion catching both would be the
same defect as one code covering two faults (H8a's batch-1 review)". Any two of these raise sites
could be given the same message and the suite would not notice.

### Minor 4 — the two new § Warnings rows break that table's own ordering
`docs/reference.md` § Warnings core reports

Measured mechanically, by extracting every `| … | \`CODE\` |` row per section and comparing to its
sort: § Warnings is alphabetical for its whole length apart from the **pre-existing** trailing
`W-FREEZE-LOCK-MOVED`, and this commit inserts `W-STUDY-CODE-HASH-MISMATCH` **above**
`W-STUDY-APPARATUS-MISMATCH`. This slice already has a commit whose whole subject is this convention
(`ca4e47a`, "alphabetize E-REPORT-FORM/-FORMAT rows before E-REPORT-OVERRIDE-*"). Remedy with care:
the apparatus row's prose opens "The identical shape one column over", which *depends* on the
code-hash row sitting above it — so reword the second row rather than swapping the two blind.

**Nothing is owed for `E-STUDY-UNREADABLE`'s position**, and I am recording that rather than
claiming a violation I could not support: the same measurement shows § Errors `validate` reports is
**not** alphabetized as a rule (153 rows, first divergence at `E-DATA-HOLDOUT-METHOD`, and the
adjacent `E-RESOLVER-*` block itself runs UNKNOWN → MEASUREMENT-FIELD → SWEPT-PARAM → YIELD →
RAISED). A position in an unsorted table is not a convention breach.

### Minor 5 — the report carries a config-count claim, as a paraphrase, against its own brief
`.superpowers/sdd/2026-08-21-report-study/task-b6-report.md` § Status

"H8c moves no config count: the four-row table stays 8 of 8 · 0 · 7 · 1." The brief says *no
config-count claim*; and the feasibility analysis's own H8b entry states the rule this violates —
that table is "repeated rather than restated, because a paraphrase is exactly the failure mode
'carried claim' names elsewhere in this section: the table's own words are what a later reader
should quote, not this entry's gloss on them." Compressing four labelled rows to `8 of 8 · 0 · 7 · 1`
is that gloss. Nothing was re-measured for it in this task.

### Minor 6 — two report claims are about something narrower than their evidence
`.superpowers/sdd/2026-08-21-report-study/task-b6-report.md`

(a) "the plan's own named fixture … a bundle sits beside a real project holding a `report.py` … the
title never appears" is offered as one of three independent certifications of the negative; it is
Minor 1's crash, not a property check. (b) "Fixture T's bundle arm … asserts exit 0, the word 'draft'
present … the pair that catches 'refuse the whole bundle' as well as 'flag but print nothing'" —
verified false by mutation (Major 3): it catches the first and not the second.

## What I checked and found sound

- **Correction 17's ruling is the right shape.** § Exit codes' "each diagnostic carries a stable
  identifier" reaches a bare print exactly as it reaches a raise, and `W-APPARATUS-UNANSWERED` is
  the standing precedent for a notice that leaves the exit code alone. Both codes are reachable (I
  reached both by probe), both § Warnings rows landed in the same commit as the code, and the
  `report`-of-a-`partial`-run precedent makes exit 0 consistent rather than lenient: a read command
  reports whether it could read. Three of the four resulting pins discriminate; the fourth is
  Major 1.
- **`E-REPORT-BUNDLE-UNSUPPORTED` is gone.** Swept with `--include` on the *file list*, never
  filtering output, with a positive control (`E-REPORT-FORM`) proving the sweep can hit. The only
  live-file survivors are two lines in `tests/test_report.py` — a docstring recording the retirement
  and an `assert … not in err` beside a positive `assert "E-STUDY-UNREADABLE" in err`, so that test
  is not absence-only. Dev-record hits correctly untouched.
- **Bundle containment works, including a shape no test covers.** A member reached through a symlink
  pointing outside the bundle is refused `E-STUDY-UNREADABLE` — verified by probe through the
  console script. The `..` and absolute-path tests pin the same `relative_to` branch.
- **The three unreadable/corrupt/missing member shapes.** Missing member and corrupt member are
  pinned and correctly distinguished (`E-STUDY-UNREADABLE` vs `E-UPSTREAM-RECORD-UNREADABLE`). A
  `chmod 000` member and a `chmod 000` `study.yaml` both give `E-IO-FAILED` at exit 1 through
  `main`'s `OSError` arm — verified by probe. The escape that *does* exist is Major 5.
- **Notices go to stdout, ahead of the render — and that is house style, not a defect.** I checked
  before grading: `diff.py:574` prints its own `Collector` to stdout, `cli.py:2313`/`3706` print
  warnings to stdout, and `reference.md` § freeze already records a stream split "as shipped rather
  than as decided". Worth someone's attention that `report study.yaml > paper.md` embeds a `W-`
  block in the cited document, but no document rules otherwise and the precedent is consistent.
- **+23 tests are not variations of one shape.** Ten `read_bundle` refusal arms (each a distinct
  fault — see Minor 3 for the assertion weakness, not the shape), two render-through-`main` arms,
  the draft arm, two discovery negatives, and seven cross-check arms across two codes and four
  readings. Two of the ten refusal arms (`..` and absolute) share one branch, which is fine and is
  argued for in the docstring.
- **Arm D did not fire**, and the `reference.md` edits touch § Building one and the two code tables
  only — not the three worked `diff` blocks.

## What I could not check

- **Whether the bundle render is "the four standard sections and nothing else."** No test asserts
  the *absence* of a fifth section or the exact section count for a member; I confirmed the four are
  present and that no override path can add one, but "nothing else" is asserted by nothing and I did
  not build a fixture for it.
- **The full-suite effect of Mutations A, B, E and F.** Each was run against
  `tests/test_report.py` in full (114 tests), not against all 2776. Bounded by sweep instead: the
  whole `tests/` tree holds no assertion on either new `W-` code or on `E-REPORT-RECORD-INCOMPLETE`
  outside that file; every `"draft"` hit outside it is about `diff`'s own draft column or a record's
  `draft` key (`test_diff.py:531,1179-1187`, `test_acceptance.py:51`, `test_runner.py:243`) or the
  unbuilt `draft` command's CLI-table row (`test_cli.py`), none about the bundle render's flag; and
  no test outside it asserts on the combined Hypotheses table's `run` column. So the four findings
  hold suite-wide by sweep, not by 200s × 4 of pytest.
- **`study new`/`study add` producing these exact bytes.** Every bundle here is hand-written
  (`_write_bundle`); whether tasks 11/13 emit the same shape is unverifiable in this commit, as the
  report says.
