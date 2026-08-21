# Batch 7 review (tasks 11-14): `study new` / `study add` — refuse before write

Reviewed at `7e5f9b9` on branch `h8c-report-study`. Every mutation below was applied for real,
run with `uv run pytest` **in the foreground against the full unfiltered suite**, and reverted by
copying the pre-mutation file back — never `git checkout`. Each revert was verified by
**behaviour**: a final full-suite run at 2821/1/2 with all four gates clean. Temp dirs
(`pytest-of-joon`) and `__pycache__` cleared before every run. **The tree is clean** —
`git status --porcelain` empty.

## Verdicts

**Spec compliance: FAILED.** Decisions 9, 10, 11 and 12 hold, and Decision 12 holds on stronger
evidence than the report offers (see below — I snapshotted mtime, which the shipped helper cannot
see). **Decision 13 does not hold.** Its second branch — the `reported: true` `Estimate`, which the
design's own table marks *"Yes — measured in r3's `results.summary`"* and rules **"listed
unconditionally when `n` is `null`"** — is unreachable on **every record this build writes**,
because `results.summary` is keyed by **step name** and the walker reads one level. Verified by
running a real `run` whose `summary` step returns two `Estimate`s (`n=4` and `n=None`) against the
record's own floor of 10: `thin_metric_lines` returns `[]`. That is Decision 13's own *Cost if
wrong* — "a walker that silently finds nothing" — realised in the branch the design says is
producible today, in the command whose entire job is to catch a disclosure nobody else will.
Separately, `E-STUDY-UNREADABLE`'s § Errors row is narrower than its code, which is correction 6's
exact shape and the whole-branch Major on both preceding sub-slices.

**Task quality: FAILED.** The three pins for that branch (`tests/test_study.py:432`, `:441`,
`:450`) all hand-build `record["results"]["summary"] = {"<metric>": {...}}` — one level, a nesting
`run` never produces — so the fixtures agree with the bug and the suite is green over a dead
branch. The `basis: "repeats"` pin sits at the same wrong nesting, so even the synthesized-fixture
ruling the design made is pinned one level off. And the step-7 join arm — created by the brief
precisely because *"NO batch owns it otherwise"* and *"a shape mismatch between them is invisible
to both reviews"* — asserts only exit `0`, the shape B7's own mandate names as passing identically
if nothing rendered.

## Gates, verified by running

`uv run ruff check .` clean · `uv run ruff format --check .` **92 files** · `uv run mypy`
**51 source files**, clean · `uv run pytest` **2821 passed, 1 skipped, 2 xfailed** (195.34 s) —
matching the report exactly. Arm D (`tests/test_diff.py:1380`) **did not fire**: `git diff --stat
6fee3fe..HEAD -- tests/` touches `test_cli.py` and `test_study.py` only.

## On the report's disclosed narrowing (assignment item 1)

The report confirmed its nine mutations against `tests/test_study.py` rather than the full suite.
I re-ran the two with genuine cross-file reach against the **full, unfiltered** suite:

| Mutation | Full-suite result |
|---|---|
| `_is_thin_checkable_entry` → `isinstance(value, Mapping) and "value" in value` (the report's own self-caught defect) | **2 failed**, 2819 passed — `..._vs_baseline_contrast_entry_is_not_silently_skipped`, `..._unpaired_contrast_either_side_below_floor`. Both in `test_study.py`. Genuinely pinned. |
| `_dispatch_study_new`'s arity/`--title` refusal removed | **2 failed**, 2819 passed — `..._refuses_missing_title_before_touching_disk`, `..._probe_arity_from_the_cli_table_test_writes_nothing_here`. Both in `test_study.py`. |

**The narrowing hid no failure.** It did hide something else: under the second mutation
`test_reference_cli_tables_match_what_the_cli_does` **passed**, and the surviving failure was
`assert 1 == 2` with stderr `E-STUDY-IN-REPO`. So the cross-file constraint both the brief and
`cli.py`'s own docstring invoke does not exist (Minor 1).

## Findings

### CRITICAL 1 — `results.summary` is nested by step name, so no `reported: true` `Estimate` is ever seen; Decision 13's second branch is dead on every real record

`src/publishable/study.py:266-270` (`_floor_metric_entries`'s `summary` loop).

```python
summary = results.get("summary")
if isinstance(summary, Mapping):
    for metric, entry in summary.items():
        if _is_thin_checkable_entry(entry):
```

`entry` here is `summary[<step_name>]` — a step-name→metric mapping, which carries neither `basis`
nor `reported`, so `_is_thin_checkable_entry` is `False` and the whole block is skipped.
`src/publishable/run_record.py:145` is the producer: `summary[e.step_name] =
summary_values(r.returned)`.

**Verified by running.** A real `run_a_project` with a `summary` step returning
`Estimate(value=0.041, ci95=[0.012,0.070], n=4, method="mixed_model")` and
`Estimate(value=0.5, ci95=[0.1,0.9], n=None, method="hand")`. The record holds:

```
{"step02_report": {"site_adjusted_delta": {"value":0.041,"reported":true,"ci95":[...],"n":4,...},
                   "no_denominator":      {"value":0.5,  "reported":true,"ci95":[...],"n":null,...},
                   "converged": true}}
```

`_floor_metric_entries` returned only the two `aggregated` entries — neither `Estimate` — and
`thin_metric_lines(run, 10)` returned **`[]`**. An `n=4` interval below a declared floor of 10 and
an interval with **no denominator at all** both pass `study add` silently, with no prompt and no
TTY check.

This defeats the exact property `W-STEP-ESTIMATE-N`'s shipped message names —
*"an interval with no stated denominator is the disclosure risk `limits.min_reported_n` exists to
catch, and `study add` cannot check what it cannot see"* — and correction 11 re-read that message
and judged it **still true** on the grounds that Decision 13 lists such an `Estimate`
unconditionally. It does not.

**Also affected:** the `basis: "repeats"` branch. `tests/test_study.py:450` places its synthesized
entry at `record["results"]["summary"]["slow_metric"]`, one level up from where `run` writes
`summary[step][metric]`. So the branch H8c deliberately shipped-and-filed against a hand-built
record is pinned at a nesting no producer would ever use, which makes the filing's own promise —
*"it becomes reachable the day a producer lands"* — false as written.

**Fix shape:** the `summary` loop must descend one level (`for step, block in summary.items(): for
metric, entry in block.items()`), and the three pins must be rebuilt at the real nesting. Note
`src/publishable/report.py:439-443` already reads `execution["summary"]` with the correct
step-then-entry nesting, so the right idiom is in-repo.

### MAJOR 1 — `E-STUDY-UNREADABLE`'s § Errors row is scoped to `report`, and `study add` now raises it

`src/publishable/study.py:96` (`_load_study_doc`), against `docs/reference.md:580`, whose row opens
*"A [`study.yaml`](#building-one) **`report` was pointed at** is absent, not valid YAML, does not
parse to a mapping…"*. The row names one emitter and `study add` is now a second.

**Verified by running.** `study_add(bundle_with_no_study_yaml, run_yaml, "main")` →
`ContractError` code `E-STUDY-UNREADABLE`, message *"no study.yaml at … — run `study new` first"*.
That message describes a fault the row's own wording excludes: it is not a `study.yaml` `report`
was pointed at.

This is correction 6's shape (*"a § Errors row narrower than its code was the whole-branch Major on
both preceding sub-slices"*) and `CLAUDE.md`'s *§ Errors carries one row per code, not per emit
site*. It is not a task-16 audit item: correction 6 rules that the row lands in the commit that
raises. Aggravating — `git show <sha> -- docs/reference.md` for **all four** commits shows the
`E-STUDY-UNREADABLE` row as a context line in each diff. It was on screen every time.

### MAJOR 2 — the step-7 join arm asserts only exit `0`, the one shape the brief and B7's mandate both forbid

`tests/test_study.py:592` (`test_study_new_add_report_join_through_main_end_to_end`), last line:
`assert main(["report", str(bundle / "study.yaml")]) == EXIT_OK`.

Brief step 7 required *"asserting the render succeeds at exit `0` **and names both runs**"*, and B7's
own review mandate says an exit-code-only assertion *"passes identically if the section rendered
nothing."* This is the arm the brief created because **no other batch owns the writer/reader loop**
— B6 certified a reader against synthetic bytes, B7 a writer against no reader.

**Verified by running.** The render does name both today: `## main` and `## sensitivity` headers,
each with `run_id`, and I separately confirmed the writer/reader shapes agree by rendering the same
run twice — once directly (`report <run.yaml>`) and once out of the bundle — and diffing the
Conditions blocks: identical, including `ci95`, `method`, the `n` mapping, `basis` and
`repeat_spread`. So the loop closes; nothing in the suite would notice if it stopped.

### MINOR 1 — `_dispatch_study_new`'s docstring credits a test with a guarantee that test does not provide

`src/publishable/cli.py:3825`: *"`test_reference_cli_tables_match_what_the_cli_does` probes this arm
from inside this very repository with two junk positionals and no `--title`, so the arity/`--title`
check must fire before `study_new` ever touches disk."*

**Verified by running.** With the arity check removed, that test **passed**. Reading
`tests/test_cli.py:9280-9288`: for a row that is not `NOT BUILT` the test asserts only that stderr
carries neither `unknown command` nor `is specified but not built` — no exit code, no disk check.
And the failure it *did* produce, `tests/test_study.py:113`, was `assert 1 == 2` with
`E-STUDY-IN-REPO` on stderr — so the companion assertion on line 114,
`assert not Path("_probe_a").exists()`, is satisfied by the **neighbouring repo guard**, not by the
arity check its docstring credits. `CLAUDE.md`'s *an assertion satisfied by neighbouring output*,
the shape this batch was warned about. The exit-code half does discriminate, which is why this is a
Minor rather than a vacuous pin.

### MINOR 2 — the disclosure prompt's own labels are wrong in two ways, on every real record

`src/publishable/study.py:241` and `:233`. Verified by running through `main`, no TTY:

```
The following reported metrics fall below `limits.min_reported_n`:
  condition None.aggregated.step01_summarize_units.by.by[cohort=a].pred: n.completed=6 < 10
```

Two defects. `condition.get("label", condition.get("index"))` returns the **present** `None` rather
than falling back to `index` — `.get`'s default fires only on a *missing* key, and a real
unswept condition records `label: null` — so every such line reads `condition None`. And the `by`
segment doubles: `metric` is already the literal string `"by"` while line 233 appends
`.by[{attribute}={level}]`. The report calls this "cosmetic only, the label is never asserted on";
it is the entire text a person makes an irreversible disclosure decision from, and "never asserted
on" is the reason it shipped wrong.

### MINOR 3 — quitting the prompt exits `0` and says nothing

`src/publishable/cli.py:3905-3910` prints only the notices `study_add` returns, and
`src/publishable/study.py:402` returns `[]` on a quit. **Verified by running** through
`main(["study","add",...])` with `isatty` true and `input` → `"n"`: exit `0`, no further output, no
`main.run.yaml`. Decision 13 rules "quitting writes nothing" and that holds; it rules no exit code,
so this is a gap rather than a violation — but a caller cannot distinguish a quit from a completed
add, and nothing tells the person at the terminal that the record was not added.

### MINOR 4 — `_refuse_if_in_repo`'s "every other `ContractError` propagates" is an unpinned safety claim

`src/publishable/study.py:47-48, 55-58`. The docstring states it and the code implements it, but no
fixture makes `find_repo_root` raise anything other than `E-GIT-NO-REPO`. `CLAUDE.md`: *a safety
argument in a comment is a claim, and needs a mutation like any other.* Cheap to close with a
monkeypatch raising a differently-coded `ContractError` and asserting it reaches the caller.

### MINOR 5 — two substring assertions rest on single common words

`tests/test_study.py:381-382` and `tests/test_cli.py`'s rewritten
`test_a_command_group_with_no_subcommand_gets_a_usage_error_naming_both`: `assert "new" in err` and
`assert "add" in err`. Read against the message they hold today they pass for the right reason, but
`"add"` and `"new"` are substrings of many plausible rewordings. This is the weakest of the
substring assertions I checked; **every other one discriminates** — I checked each against the
actual captured output (the `E-STUDY-CONFIRM-REQUIRED` stderr, the `W-STUDY-COMMIT-MISMATCH`
notice, `n_of=3` against a record also carrying `n_against=40`, and the `by[cohort=` lines against
the whole-condition entries in the same record).

## What holds, and what I verified it by

**Decision 12 (the load-bearing refusal) — holds, on stronger evidence than the report gives.**
`_snapshot` (`tests/test_study.py:21`) captures path + bytes only, so it cannot see an mtime touch.
I built my own snapshot over `(st_size, st_mtime_ns, bytes)` and took it around a refused
`study_add` on a used name: **byte-for-byte and mtime-for-mtime identical**, same two-file key set
(`main.run.yaml`, `study.yaml`) before and after. Both halves check out: the `study.yaml`-keys arm
and the file-on-disk arm with `study.yaml` hand-edited to drop the entry (`study.py:387`,
`name in (doc.get("runs") or {}) or target.exists()`), and the check precedes `read_record_file`,
so not even the source record is opened.

**Decision 10 (redaction) — holds, verified exhaustively by running.** I walked a real record's
full leaf-path set before and after `_redact` and diffed. Exactly the documented fields change:
`.config.data.input_dir`, `.config.data.output_dir`, `.provenance.git.repo_root`,
`.provenance.input_manifest`. **Six** hash paths exist in a real record —
`.parameters_hash`, `.code_hash`, `.provenance.environment.uv_lock_hash`,
`.provenance.input_manifest_hash`, `.provenance.units_hash`, `.provenance.allocation_hash` — and
**every one is unchanged** (the shipped test asserts three of the six; all six hold). Two states,
one marker string: present → marker, absent or `null` → untouched, with `grep -n "redacted"
src/publishable/study.py` finding one literal. `provenance.environment` on a real record is
`{manager, python_version, uv_lock, uv_lock_hash}` — **`hostname` is genuinely unwritten**, so four
redactable rows is right and the fifth is exercised only over `_fixture_y_record`, whose docstring
says so.

Two things worth recording while I was there: `provenance.units` is `{n, key}` — a count and a
key-*field* name, no identities — so Decision 14's reason 2 (*"there is nothing of it in a bundle to
scrub"*) is confirmed rather than assumed; and `provenance.allocation` travels as the bare filename
`"allocation.json"` beside its hash, exactly as reason 3 rules.

**The walker's other three blocks — hold, verified on one real record carrying them together.**
A real run with `statistics.report_by: [cohort]` **and** `sweep.grid`/`sweep.baseline` produced 14
metric-shaped entries in one pass: both conditions' `aggregated` top-level metrics, both
conditions' four `by` strata, and the non-baseline condition's two `vs_baseline` delta entries
(`basis: units`, no `n` mapping, `n_paired: 12`). The `"value" in entry` defect the report
self-caught is genuinely gone and genuinely pinned.

**`vs_baseline` and `results.contrasts[]` carry no `by` strata — verified absent, not assumed.**
This was my leading Critical candidate and it is not one. `_comparison_step_blocks`
(`src/publishable/cli.py:1037`) computes `sorted((set(of_summary) & set(against_summary)) - {"by"})`
with the reason in a comment, my real run's `vs_baseline[step]` keys were exactly
`["metric", "pred"]`, and `tests/test_cli.py:10274-10275` already pins `"by" not in step_block` for
every condition. So the walker's non-recursing `vs_baseline` loop is correct rather than lucky. A
contrast entry's non-metric keys are exactly `id`/`of`/`against`
(`src/publishable/cli.py:1807-1813`), which is exactly the walker's skip set.

**Correction 12 — holds, and the refusal is pinned by the property.** `find_repo_root` raises;
`_refuse_if_in_repo` catches `E-GIT-NO-REPO` as the pass branch. `study new` refuses inside a repo
(`E-STUDY-IN-REPO`, exit 1) and `tests/test_study.py:74-76` asserts **`not (bundle /
"study.yaml").exists()` and `not bundle.exists()`**, not just the exit code — so the
check-after-write mutation is caught by the property. The pass branch is exercised by every other
test in the file (all bundles under `tmp_path`, outside any repo), so it is not a
guard-tested-by-accident. The walk-up form is correctly rejected as a mutation.

**Corrections 4 and 5 — both directions asserted, and the arms moved with their cells.**
`git show c84a820 -- src/publishable/cli.py` confirms task 11 routed `add` to
`_report_not_built("study add", NOT_BUILT_COMMANDS["study add"])`; task 13 (`3b24652`) replaced it.
Both directions are live: `tests/test_cli.py:9239` asserts set equality between the document's
`NOT BUILT` rows and `NOT_BUILT_COMMANDS`, and the table test's `else` branch asserts a `built` row
prints neither diagnostic. The shipped group test was **replaced** rather than patched, which is
the right call for a docstring whose premise went false.

**Decision 15's rows landed in the right section and the right commits.** All four new `E-STUDY-*`
rows sit in § Errors `validate` reports (`docs/reference.md:581-584`, between the section at 409
and § Errors core raises at 1070) and `W-STUDY-COMMIT-MISMATCH` in § Warnings (`:402`), per
Decision 15's ruling that the table is the registry. Per commit: task 11 → `E-STUDY-IN-REPO` +
`E-STUDY-EXISTS`; task 12 → `W-STUDY-COMMIT-MISMATCH`; task 13 → `E-STUDY-NAME-EXISTS`; task 14 →
`E-STUDY-CONFIRM-REQUIRED`. § Exit codes' creation-command sentence gained `study new` /
`E-STUDY-EXISTS`; `E-REPORT-EXISTS`, the second member Decision 15 names, is task 15's and
correctly absent here.

**Decision 13's third branch and its filing — the ruling is honoured.** No code or test claims
`basis: "repeats"` is producible: `thin_metric_lines`'s docstring, `_fixture_y_record`'s docstring
and `tests/test_study.py:451-453` all say the opposite. The filing
(`docs/superpowers/spec-defects.md`, last entry) states the measurement dated and pinned to
`ebf642a`, names the affected passages by section plus `W-HYPOTHESIS-INFERENCE-BASE`'s own message,
carries **`Owner: unassigned`** — the file's established convention, used by 18 entries, and here
with the reason attached rather than bare — argues why H8c and the closed H4 family are both wrong
to name, and poses the disposition question rather than pre-deciding it. Note the interaction with
Critical 1: the branch's pin is at the wrong nesting, so the filing's *"it becomes reachable the
day a producer lands"* does not currently follow.

**Mechanical pass on the two edited documents — clean.** No trailing whitespace, no tabs, no
invisible unicode on any added line. All 17 `(#anchor)` targets in the added `reference.md` rows
resolve against that file's own headings (checked by generating the slug set with an `awk` pass and
matching), and `design-principles.md#design-goals` resolves. No `x`-for-`×` in added document
prose. No config-count claim entered any document; no feasibility file was touched.

## Prose and pins

Arm D did not fire and was not touched. No count phrase and no positional locator (*"the row
above"*, *"further up"*) appears in the added `reference.md` rows — each names its sibling by what
that sibling does, which is the convention. The `E-STUDY-IN-REPO` row's phrase *"the walk-up
`provenance.find_repo_root` performed over `input_dir`/`output_dir` **succeeding**"* names the
mechanism by its existing use rather than the operand (the walk-up runs over the **bundle path**);
it reads correctly on the second pass and I am **not** raising it, but a tighter wording would
help.

## Notes for task 16, not findings against this batch

- § Exit codes' creation-command enumeration now names `E-STUDY-EXISTS` but not
  `E-STUDY-NAME-EXISTS`, which is also *"a creation command refusing to overwrite an existing
  file"* — arguably the family's most load-bearing member. Decision 15 named only two members for
  that sentence, so this batch is per-spec; the audit should rule.
- `study add` itself performs no `_refuse_if_in_repo`. The plan's global constraint asserts
  *"`study add` writes only inside the bundle, which is refused inside any git repo"* — true only
  transitively through `study new`, so a bundle created outside a repo and later moved inside one
  accepts adds. Nothing in the four documents requires otherwise; recording it because the
  constraint's wording reads as a checked property.

## What I could not check

- Whether the `basis: "repeats"` branch's *arithmetic* is right against a real producer — none
  exists, by construction, which is the filing's subject.
- Whether `W-STUDY-COMMIT-MISMATCH`'s `Collector.warn(code, positional[0], message)` convention
  (the bundle path as the "path" field, on a single-run command) matches practice beyond
  `report.py`'s `_bundle_cross_checks`. Read only; the rendered output is correct and legible.
- Seven of the report's nine mutations were re-confirmed only from its own text. I re-ran the two
  with cross-file reach; the other seven are confined to `study.py` internals whose only callers
  are `study.py` and the `study` CLI arm, so `test_study.py` is the whole blast radius by
  construction — but I state that as read, not run.

## Addendum: two items the assignment named explicitly

**M12's vacuity is genuinely fixed — verified by reading, not by re-running the mutation.**
`tests/test_study.py:569` (`test_study_add_uses_the_bundled_records_own_floor_not_a_cwd_config`)
supplies two floors that give **different** verdicts on the identical 6-unit `by` strata — the
record's own `10` and a cwd `cwd_config.yaml` declaring `1` — with `isatty` false, and asserts the
**raise** (`E-STUDY-CONFIRM-REQUIRED`) plus `not (bundle / "main.run.yaml").exists()`. So the honest
code refuses and a mutant consulting the cwd floor finds nothing thin and writes. The vacuous first
draft the report discloses (TTY-confirm plus `input` → `"y"`, asserting only that the file was
written) is gone from the file: `grep -n "isatty" tests/test_study.py` shows this arm patches it to
`False`. The M8 arm at `:553` uses the same discipline.

**MINOR 6 — `E-STUDY-CONFIRM-REQUIRED`'s § Errors row promises a print that nothing asserts.**
`docs/reference.md:583` claims *"Prints the offending metrics before refusing, and writes nothing:
not even a partial copy of the record."* The write half is pinned (`tests/test_study.py:566-568`,
snapshot plus file absence). The **print** half is not: that test takes no `capsys` and no test in
the suite asserts the four `n.completed=6 < 10` lines reach stdout. I confirmed by running through
`main` that they do — stdout carries the header and the four lines, stderr carries the coded
refusal, exit `1` — so the row is true and unpinned. Same family as Minor 4.
