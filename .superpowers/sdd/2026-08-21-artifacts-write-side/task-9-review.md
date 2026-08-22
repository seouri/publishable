# Task 9 review — the two row-shaped writers coerce, `io.write` names the artifact

**Verdict: PASS**

Suite: **2884 passed, 1 skipped, 2 xfailed** (baseline `d1ea442`: 2879 passed, 1 skipped, 2 xfailed;
delta +5, reconciles with the report). `git diff --stat` against `eeebd89` is empty after every
mutation below was reverted by editing back — the working tree matches the commit exactly.
`ruff check .`: all checks passed. `ruff format --check .`: 93 files already formatted. `mypy`: success,
52 source files.

## What was verified by behaviour (real command, installed console script) vs. by reading

**By behaviour, through `/Users/joon/src/tries/publishable/.venv/bin/publishable` invoked directly
(not `uv run`, not in-process `main()`)** — a scaffolded project (`publishable new` +
`generate experiment`), a hand-edited starter step, `git commit`, then `publishable run
configs/cohort-pilot/config.yaml`, reading `run.yaml`/`executions.jsonl` back:

- A `.csv` write of a `[1, 2]` cell fails every repeat with `E-STEP-RETURN-TYPE ContractError:
  probe.csv: row 0 gave 'v' a list; ...` — coercion refuses, and the artifact name is prefixed, exactly
  as claimed.
- A `.csv` write of a `bytes` cell fails identically, prefixed `bytesprobe.csv:`.
- A `.parquet` write of a `[1, 2]` cell **and** a `bytes` cell in the same row completes with exit 0;
  read the artifact back with `pyarrow.parquet.read_table` and got `[{'v': [1, 2], 'b': b'x'}]` —
  round-tripped byte-faithfully, confirming the second controller ruling's narrowing is what actually
  shipped, not the plan's pre-ruling text.
- A `.csv` write of `[{"v": 1.0}, "not a mapping"]` fails with `E-ARTIFACT-UNWRITABLE ArtifactError: row
  1 is a str, not a mapping; ...` — **and the message does not name the artifact.** This looked like a
  gap until checked against `docs/reference.md` § Steps and artifacts, which says a non-mapping row is
  refused "naming **the row**" (not the artifact) — deliberately, because `_coerced_rows` raises
  `ArtifactError`, and `io.write`'s new wrapper (step 2) catches only `ContractError`. Read the code:
  confirmed the wrapper's `try` is exactly `WRITERS[suffix](obj)` and nothing else, so this is by
  design, not a hole.
- `io.write` of a NumPy `float64` beside a plain `float` to `.parquet` completes with exit 0 — the
  spurious refusal's retirement, confirmed end to end, not merely by reading the design.
- An unregistered suffix (`weirdsuffixmodel3.pkl.xyz`) with a non-writable object produces `"...has no
  registered writer, so the object must be bytes or str, not list"` — the artifact name appears exactly
  once, not doubled, confirming step 2's control.

**By reading**: the design's two controller rulings (first approves the behaviour change on a
corruption ground; second narrows Decision 5 to `.csv` only after measuring `.parquet` round-trips
intact), the plan's appended 2026-08-22 correction (documents that task 9's own brief text — steps 1,
5, 7 — carries the **superseded pre-ruling** reading and that the binding rule is "a writer accepts what
it can give back," per format), `docs/reference.md`'s edited § Steps and artifacts section, and every
emit site for `E-ARTIFACT-UNWRITABLE` and `E-STEP-RETURN-TYPE`.

## The report's central deviation claim: correct and disclosed

The report's own preamble states, correctly, that it built to the **second** controller ruling rather
than the brief's/plan's pre-ruling text (steps 1, 5, 7), and names exactly what changed: `.parquet`
keeps accepting a structural/`bytes` cell (no refusal), `.csv` refuses. This is exactly what the
appended plan correction (2026-08-22) prescribes, and it is exactly what the real-command runs above
demonstrate. The deviation is disclosed at the top of the report, not silent.

## `§ Errors` clauses — re-derived, not taken on the report's word

Grepped every emit site myself:

- `E-ARTIFACT-UNWRITABLE`: `artifacts.py:88` (`_coerced_rows`'s non-mapping guard, both formats) and
  `artifacts.py:973` (`io.write`'s unregistered-suffix `else`). `reference.md`'s row covers both.
- `E-STEP-RETURN-TYPE`: `runner.py:783` (step return), `coercion.py:263` (`_refuse`, the shared raise
  reached by `io.record`, `_coerced_rows`'s `.csv` branch, and `cli.py`'s aggregate/derived-key
  coercion), `artifacts.py:181` (`_check_column_types`, the `.parquet` cross-row check). `reference.md`
  §1116's row states the `.csv`-cell clause and the `.parquet`-cross-row clause each bound to the
  correct format ("checked only for `.parquet` since a `.csv` write does not unify a column's type
  across rows today"). Both clauses are true of the code; no edit was owed, matching the report.

## Mutations — all five re-run independently, reverted by editing back

1. Delete `_encode_parquet`'s `_coerced_rows` call → **2 failed** (local pin, Fixture N — the latter
   collaterally, because the non-mapping guard is fused into the same call). Matches report.
2. Delete `_encode_csv`'s call only → **3 failed** (arm E2, Fixture S, Fixture N's `.csv` half via the
   non-mapping guard) — `.parquet` arms stayed green. Matches report (report's count of 3 lists arm E2
   and Fixture S by name and confirms no `.parquet` arm moved; consistent).
3. `_check_column_types`'s `float if actual in (int, float) else actual` → `actual` → **3 failed**
   (the two pre-existing promotion tests plus the dedicated one). Matches report exactly.
4. Delete the `except ContractError` wrapper in `io.write` → **2 failed** (arm E2, Fixture S), both on
   the artifact-name assertion. Matches report exactly.
5. Widen the wrapper to the whole body of `io.write`, `except` widened to `PublishableError` →
   **the report claims 1 failed** (the step 2 control only). **Re-running the mutation exactly as
   specified — `try` around the entire `if/elif/else`, `except PublishableError as exc: raise
   ContractError(f"{name}: {exc}", code=exc.code) from exc`, unchanged raise line — produces 4
   failures**: `test_h5a_step2_control_the_unregistered_suffix_message_is_not_prefixed` (as the report
   says), plus `test_an_unregistered_extension_takes_bytes_or_str_verbatim`,
   `test_write_of_an_unwritable_object_leaves_nothing_behind`, and
   `test_h5a_fixture_n_a_non_mapping_row_refuses_with_the_documented_code` — all three because widening
   the `try` to the whole body also wraps the pre-existing `else`-branch `ArtifactError` and the
   non-mapping `ArtifactError` from `_coerced_rows`, converting both into `ContractError` and breaking
   every `pytest.raises(ArtifactError)` assertion against them. Reproduced twice for certainty; reverted
   by restoring the saved file and re-confirmed 150/150 in `test_artifacts.py` both times.

## Findings

### Major — mutation (v)'s reported failure count is wrong: report says 1, actual is 4

**File:** `.superpowers/sdd/2026-08-21-artifacts-write-side/task-9-report.md`, "The five mutations"
section, item 5.

**Failure scenario:** A reader trusts the report's claim that widening `io.write`'s wrapper to the
whole body breaks only the step 2 control, and concludes the unregistered-suffix and non-mapping
`ArtifactError` paths are unaffected by that class of change. They are not: the same widening also
flips two pre-existing behavioural pins (`test_an_unregistered_extension_takes_bytes_or_str_verbatim`,
`test_write_of_an_unwritable_object_leaves_nothing_behind`) and Fixture N's own arm, because a `try`
spanning the whole `if/elif/else` catches every `ArtifactError` the `else` branch and `_coerced_rows`
raise, not only the `WRITERS[suffix](obj)` dispatch's `ContractError`. Read literally, the report's
"1 failed" implies these three pins are not sensitive to the containment boundary the design calls
for — they are, and that sensitivity is exactly what makes the containment rule (`try` = dispatch only)
load-bearing rather than cosmetic. The shipped code is unaffected — the wrapper as built is
dispatch-only — so this is a reporting defect, not a code defect, but it is the exact shape `CLAUDE.md`
warns about repeatedly: a mutation's failure text recorded without being fully read. Reproduced twice
independently; reverted both times by restoring from a saved copy and re-confirming 150/150 in
`test_artifacts.py`.

### No other findings

- Real-command behaviour for every documented stoppage (`.csv` structural/`bytes` refusal, `.parquet`
  acceptance, non-mapping refusal for both formats, the artifact-name prefix, the retirement) matches
  the report and the design's second ruling exactly, verified through the installed console script.
- Mutations 1–4 reproduce exactly as reported, with the same tests failing for the same reasons.
- The two `§ Errors` clauses were re-derived from every emit site and are both true of the code as
  built; no edit was owed.
- Arm C (no authorized editor) is untouched by the diff. Arm E1 (`.parquet`, no authorized editor) is
  untouched; arm E2 (`.csv`, task 9's sole edit) was edited exactly as disclosed, in place, with its
  post-edit state stated in advance. Arm D (the worked-example raw-text arm, no authorized editor in
  H5a at all) and `test_cli.py -k h5a` (5/5, including arm A) are unmoved — confirmed by running, not
  only by diffstat.
- `io.write`'s `try` is confirmed by reading to enclose exactly the `WRITERS[suffix](obj)` dispatch and
  nothing else — `io.path`'s existence check and `_resolve`'s containment refusal sit outside it, per
  the `check_facts` precedent the brief named.
- The sweep for row-shaped `io.write` calls in generated code (`templates/`, `generators/`,
  `readme_templates/`, `scaffold.py`, `plugin_scaffold.py`) found zero hits, confirmed independently —
  no generated project code calls `io.write` at all, so nothing generated starts refusing.
- Documentation matches the shipped code exactly: the `.csv`/`.parquet` table row split, the coercion
  paragraph, "one rule, every surface" (count dropped, not raised), and the `E-STEP-RETURN-TYPE`/
  `E-ARTIFACT-UNWRITABLE` § Errors rows all read true against the code as built.
- Decoy check on the artifact-naming assertions: filenames used in the fixtures (`e_list.csv`,
  `s_first.csv`, `probe.csv`, etc.) are arbitrary strings not derivable from the message's own
  enumeration, so there is no risk of the assertion being satisfied by neighbouring output the way
  H8's `RESERVED_COLUMNS`-join defect was.
