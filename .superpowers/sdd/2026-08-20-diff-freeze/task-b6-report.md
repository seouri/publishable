# Task report: batch 6 — tasks 9, 10, 11 (`diff`'s apparatus row; its exit code and
config side; its upstream block and CLI arm)

Dated 2026-08-21, measured against the commit each task built on. Suite: 2609 → **2614** (task 9)
→ **2618** (task 10) → **2623** (task 11), 1 skipped, 2 xfailed throughout. `uv run mypy` → clean,
**49** source files throughout. `uv run ruff check .` → clean throughout. `uv run ruff format
--check .` → **88** files throughout, unchanged.

## Status: done, all three tasks, three commits

- `8bb90c2` — task 9: `diff`'s apparatus row and its per-fact lines
- `b4be0c8` — task 10: `diff`'s exit code, and the config side's four `not comparable` rows
- `bdaccaa` — task 11: `diff`'s upstream block, and `diff` dispatches

`diff` is now a real, dispatching command: `main(["diff", a, b])` reaches `command_diff` through its
own CLI arm, and `NOT_BUILT_COMMANDS`/`reference.md` § Operation commands agree it is `built`.

## Task 9 — the apparatus row

`ROW_LABELS` gained `'apparatus'` fourth, before `'parameters_hash'` — the one authorized edit to
that list and to `test_h8b_row_order_is_pinned`'s literal. The diff, exactly:

```
-ROW_LABELS = ["code_hash", "input_manifest", "uv.lock", "parameters_hash"]
+ROW_LABELS = ["code_hash", "input_manifest", "uv.lock", "apparatus", "parameters_hash"]
```

and in the test, only the `ROW_LABELS ==` literal grew the same way — `_row_labels_in_output`'s
expectation list is **unchanged** (`["code_hash", "input_manifest", "uv.lock", "parameters_hash"]`),
because that fixture's two sides are both `run_a_project` scaffolds with `apparatus: null` on both,
which Decision 2 OMITS — nothing else in that test was reordered.

The row's verdict compares `provenance.apparatus.hash` (never the `facts` mapping directly, per
Decision 2's grounds: a mapping comparison can disagree with the hash over a canonicalization the
hash already applies). Detail lines come from `.facts`, one per `(condition, fact)` pair that
differs, always qualified by the condition key, sorted by `(condition, fact)`, never collapsed. The
row is omitted only when both sides' `provenance.apparatus` is `null`; it is `DIFFERS` with a naming
line when exactly one side has one; a condition present in one side's `facts` and not the other gets
its own line.

Two doc-agreement tests inverted, because their premise flipped the moment the row landed (their own
docstrings said as much): README/design-principles now compare against `ROW_LABELS` with
`'apparatus'` dropped (their worked pair never shows one), and `reference.md` compares against
`ROW_LABELS` whole. `reference.md` § The apparatus core can only observe's fenced `diff` example
gained the condition key on its `calibration_id` line and its ASCII `...` became `…` in the same
edit, per the brief; grepped the four documents by name afterward for the old bare-fact shape —
nothing else matched.

**Mutations, both run against the real suite and reverted by editing the file back, reverts verified
by rerunning:**

| Mutation | Text | Outcome |
|---|---|---|
| M2 | Compare `.facts` via `json.dumps(...)` (no `sort_keys`) instead of `.hash` | **FAIL** — caught by a dedicated pin (`test_h8b_apparatus_identical_survives_a_facts_key_reorder`): two Fixture-P runs with the SAME `calibration_id`, one record's `facts` hand-reordered before comparison. Real code: `identical`. Under M2: `DIFFERS`. Property-preserving arm: the genuine-`DIFFERS` fixture (Fixture A1) passes under both branches — `json.dumps` without `sort_keys` still disagrees when the content genuinely disagrees, so only the reordered-but-equal arm distinguishes the two, which is why that arm exists separately |
| M3 | Drop the condition qualifier from a detail line (`f"{fact}"` instead of `f"{condition}.{fact}"`) | **FAIL** — caught by Fixture A1 (`test_h8b_fixture_a1_apparatus_differs_two_conditions_moving`): two conditions, two keys expected; under M3 the per-condition qualified-line search finds none. Property-preserving arm: a single-condition move could not tell a dropped qualifier from a collapsed pair (the design's own stated reason), so Fixture A1's second condition is what makes the mutation non-blind |

Fixtures A1 (two conditions moving) and A2 (identical arm plus its by-hand facts-reorder variant,
and the one-sided arm naming which side recorded none, in both operand orders) run against a real
installed probe plugin (Fixture P's shape: synthetic distribution, project-local template, an
env-var-driven probe so the same registration serves two independently-scaffolded projects with two
different answers — avoiding a `sys.modules` caching collision across tests, which the first attempt
hit and is noted in the code comment).

## Task 10 — the exit code and the config side

A config supplies exactly one of the five rows — `parameters_hash`, computed fresh via
`hashes.parameters_hash` over the config's own parsed document — and the other four print
`not comparable  <reason>`, verbatim from the design's table, as one rule regardless of whether the
other side is a config or a run (config-vs-config and config-vs-run share the same branch in
`command_diff`). `_NOT_COMPARABLE_REASONS` is the one dict both the code and the tests read.

Decision 4's exit-code ruling — `0` whenever a comparison renders, `1` only when a side cannot be
loaded — was **already the shape** `command_diff`'s unconditional `return EXIT_OK` gave tasks 7-9;
this task's own job was the mutation that pins it, not a behaviour change.

**Mutations, both run and reverted, reverts verified by rerunning:**

| Mutation | Text | Outcome |
|---|---|---|
| M5 | Return `EXIT_WRONG` when any rendered line contains `"DIFFERS"` | **FAIL** — caught by both the run-vs-run `test_h8b_fixture_r2_the_documented_payoff` (asserts `EXIT_OK` with a `DIFFERS` row present) and the new `test_h8b_config_vs_config_same_shape`. Property-preserving arm: an all-`identical` fixture would exit `0` under both branches — the `DIFFERS`-present half is what makes each fixture non-vacuous, exactly as the design names |
| — (refusal side) | Return `EXIT_OK` on `E-DIFF-CONFIG-UNREADABLE` | **FAIL** — caught by the existing `test_h8b_a_config_that_is_not_a_mapping_is_e_diff_config_unreadable` and the new `test_h8b_a_config_that_is_not_a_mapping_still_yields_no_render`. Property-preserving arm: n/a — no comparison renders in either branch, so the exit code is the only observable, which is why asserting on it is what keeps "0-on-difference" from becoming "0-on-everything" |

Fixtures: config-vs-run (one row computed, four `not comparable`, reason text asserted verbatim),
config-vs-config (same shape, `parameters_hash DIFFERS` with a real delta line), and the control —
an ordinary run-vs-run pair asserted to print `not comparable` **nowhere** (without it, a build that
printed `not comparable` unconditionally would pass the first two). A fourth test distinguishes
`not captured` from `not comparable` from a third path entirely: a config that fails to parse to a
mapping renders **nothing** (`E-DIFF-CONFIG-UNREADABLE`, exit `1`) — neither word appears.

**Discrepancy to disclose, resolved toward the controller's instruction over the task brief's own
text:** task 10's brief step 2 says to delete § Exit codes' `diff` clause in this task. The
controlling brief for this batch states that document change is task 12's, and only the *behaviour*
is task 10's. I followed the controller and left § Exit codes untouched; § Operation commands gained
the sentence naming what a config side cannot supply and all four verdict strings
(`identical`/`DIFFERS`/`not captured`/`not comparable`), which is task 10's own obligation per
Decision 5 part 4 and was not previously present anywhere in the four documents.

## Task 11 — the upstream block and the CLI arm

The arm, the `NOT_BUILT_COMMANDS` key removal, and the `reference.md` Status-cell flip landed in one
commit (§ Corrections, correction 1). `diff` gets its own arm — exactly two paths, no flags, same
leading-`-` rejection `OPERATION_COMMANDS`'s arm uses — rather than joining that arm, which enforces
one path. Measured directly:

```
$ main(["diff", "_probe_a", "_probe_b"])
  error   E-IO-FAILED          No such file or directory
exit code: 1
```

confirming a built row reaches real argument handling (`E-IO-FAILED`, not `unknown command` or
`specified but not built`), which is what `test_reference_cli_tables_match_what_the_cli_does`
requires for a `built` row. `NOT_BUILT_COMMANDS` now holds 10 entries (measured:
`len(NOT_BUILT_COMMANDS) == 10`), so `test_reference_cli_tables_are_parsed_at_all`'s
`statuses == {"built", "NOT BUILT"}` control stays non-vacuous. Both CLI-table tests pass; neither
was edited — their assertions simply now exercise `diff`'s `built` direction, which is the "exactly
two shipped tests may change, only in the `diff` row's direction" the brief names, achieved by the
document/constant edit rather than a test edit.

The upstream block prints after the five rows, only when either side's `provenance.upstream` is
non-empty, and is **not** a sixth row (its own `"upstream"` header line, asserted separately from
`ROW_LABELS`, which stayed unchanged). Each entry renders under its side letter with its `run_id` and
its two short hashes; a `None` hash (§ Corrections, correction 7 — `UpstreamLedger.record` copies
`record.get(...)`, so either figure can be absent on a legitimately honest record) renders
`not captured`, reusing Decision 1's vocabulary. **This is a defensive render, not a disposition**:
the OPEN `spec-defects.md` entry naming H9 as owner and H8b as the secondary consumer was not struck
and is not addressed by this rendering — grepped for by name after the commit to confirm it is still
present and OPEN.

**Fixture U**, built to satisfy the brief's literal demand ("its five `identical`s are the
discriminating half"): a real committed `uv.lock` (Fixture L's mechanism) plus a Fixture-P apparatus
probe answering the same `calibration_id` both times, both established on one commit before either of
the two compared runs, so `code_hash`/`input_manifest`/`uv.lock`/`apparatus`/`parameters_hash` are
**all five** `identical` by construction. Which of the two runs consumes the upstream is decided by
an **environment variable** the starter step reads at call time — never a source or config edit —
which is exactly what keeps every row identical; a step with two different SOURCE forms (one calling
`reuse_from`, one not) would move `code_hash` itself and defeat the fixture. The two runs are resolved
through `<output_dir>/latest`, never a glob, per the brief's own warning about `Path.glob`'s undefined
order over a directory that will hold more than one `run_*`.

**Two things reported rather than resolved, as the brief asks:**
- The "differ only in their upstreams" line's gate treats every one of `ROW_LABELS` as needing a
  literal `identical` verdict (not `not captured`) — Fixture U had to be built with a genuinely
  non-null `uv.lock` to reach it, rather than relying on the "not captured, but agreeing" reading a
  looser gate would have accepted. Both readings were considered; the stricter one is what the brief's
  own words ("all five rows read identical") ask for, and it is what shipped.
- The draft label is pinned against a **hand-set** `draft: true` on a real record's `run.yaml`, read
  back through `_load_side`/`_header_line` — not against a genuine draft run, since `draft` itself is
  H9's and this task cannot produce one.

**Mutations, both run and reverted, reverts verified by rerunning:**

| Mutation | Text | Outcome |
|---|---|---|
| step 9 | Print the upstream block unconditionally (`_upstream_block_lines(...) or ["upstream"]`, gate replaced with `if True`) | **FAIL** — caught by an ordinary two-run pair (`test_h8b_mutation_unconditional_upstream_block_caught_by_fixture_r2`): `[]` on both sides is what every such pair writes, so the mutation prints a bare `upstream` header where the real code prints nothing. Property-preserving arm: n/a — `[]` and "absent" are both falsy, which is why the assertion is on emitted text, not a truthiness check, per the brief |
| step 10 | Print "these runs differ only in their upstreams" whenever the block prints, dropping the `_all_five_rows_identical` gate | **FAIL** — caught by a dedicated fixture (`test_h8b_the_differ_only_line_absent_when_a_row_also_differs`): upstreams differ AND `parameters_hash` differs; real code omits the line, mutation prints it beside a `DIFFERS` row. Property-preserving arm: Fixture U alone (all-identical) cannot catch this mutation, since both branches print the line there — which is exactly why the brief calls for a second, non-identical fixture |

## Gates and gap-check

`uv run ruff check .` clean; `uv run ruff format --check .` → 88 files, unchanged; `uv run mypy` →
49 source files, clean — all three held at every commit. Full suite: 2609 → 2614 → 2618 → 2623
passed, 1 skipped, 2 xfailed throughout — no shipped test other than the two named CLI-table tests
changed outcome, and neither of those was edited.

**Task 12 remains**: § Errors rows, § Package layout, the remaining `EXIT_EXTERNAL`/§ Exit codes
document edits (including the `diff` clause task 10's brief asked for and the controller reserved),
and the § Executability re-measurement. This batch moved no config's executable count — the table
stays 8 of 8 · 0 · 7 · 1, unchanged by any of the three tasks, consistent with "H8b moves NO config
count."

## Fix round 1

Against `.superpowers/sdd/2026-08-20-diff-freeze/task-b6-review.md`. Both verdicts were PASS with
findings (four Majors, twelve Minors); every Major closed, twelve Minors closed or disposed of
below. Gates before this round: `mypy` 49, `ruff format` 88, suite 2623 passed/1 skipped/2 xfailed.
After: `mypy` 49, `ruff format` 88, suite **2631 passed, 1 skipped, 2 xfailed** (+8 tests: four for
the CLI arm, one for the one-sided-condition line, one for the upstream `not captured` render, two
for the empty-string render).

### Major 1 — `diff`'s CLI arm was entirely unpinned

Added four tests to `tests/test_cli.py` (`test_diff_with_no_paths_is_an_invocation_error`,
`_with_one_path_`, `_with_three_paths_`, `_rejects_a_leading_dash_on_either_path`), each asserting
**both** `EXIT_INVOCATION` and the exact stderr message — the review's own named defect being a
control that asserted only absences. **Verified by mutation**: replaced the guard with
`if len(rest) < 1:` (dropping both the arity rule and the flag rejection, the review's exact
mutation) — all four new tests failed, one of them (`test_diff_with_one_path_is_an_invocation_error`)
on the bare `IndexError` the review named as load-bearing, not merely a wrong exit code. Reverted by
editing the file back; reran the four tests green. Property-preserving arm: none needed — this
mutation has no reading under which any valid-arity, no-flag invocation behaves differently, so
there is no property-preserving counterpart to report; the four new tests are the first pins on this
arm at all.

### Major 2 — Decision 2's third sub-ruling had no fixture

Added `test_h8b_a_condition_missing_from_one_side_s_facts_gets_its_own_line` (`tests/test_diff.py`),
on the review's own repro: two hand-built `provenance.apparatus` records built through
`apparatus.apparatus_hash` (never a literal digest), one holding a condition the other's `facts`
lacks entirely, checked in both operand orders. **Verified by mutation**: replaced the branch with a
bare `continue` (the review's exact mutation) — the new test failed (`assert False` on the "any line
names the missing condition" check). Reverted by editing the file back; reran green.
Property-preserving arm: Fixture A1 (both conditions present on both sides) and Fixture A2's
one-sided arm (`apparatus: null` entirely) both still pass under the same mutation, because neither
puts the two sides' condition-key SETS in disagreement — which is exactly why a third fixture was
missing rather than redundant.

### Major 3 — Fixture U's section comment licensed the edit that would have destroyed it

Deleted the comment's claim (*"a deliberate, reported relaxation; see the batch report"*) — the
report says the opposite, and the comment cited it as authority for the opposite. Replaced with an
accurate description: all five rows read `identical` by construction, including `uv.lock`, which
needed a real committed lockfile precisely because the relaxation the old comment invited would have
destroyed the fixture's discriminating half. No code changed under this finding — the fixture and
its assertions were already correct, per the review's own "keep it."

### Major 4 — the upstream block's `not captured` render was unreachable

Added `test_h8b_an_upstream_entry_with_a_missing_hash_renders_not_captured`, on hand-built `_Side`
objects (no real `reuse_from` needed) checking both fields independently — `code_hash: None` in one
entry, `parameters_hash: None` in another. **Verified by mutation**: replaced `_upstream_hash_repr`'s
body with `return _truncated(value)` (the review's exact mutation) — the test failed on the exact
`AttributeError: 'NoneType' object has no attribute 'partition'` the review predicted. Reverted by
editing the file back; reran green. Property-preserving arm: none — every existing upstream fixture
(Fixture U, Fixture F-style) writes a `run_id` through `UpstreamLedger.record`'s own machinery, which
always supplies both hashes when the upstream's own `run.yaml` has them, so no existing fixture could
have caught this without a hand-built entry.

### Minor 1 — the `Does` cell's "five rows" claim

Fixed: now reads "each row that applies — five over a run-vs-run pair with a declared apparatus,
four when both sides' apparatus is `null`" and "every printed row agrees" rather than "all five".

### Minor 2 — the garbled § Operation commands sentence

Rewritten: "`diff` is not one of the four places a probe runs … so it cannot answer `apparatus`
either" — same argument (Decision 5's grounds), parseable prose.

### Minor 3 — § Exit codes contradiction

No action — already recorded as task 12's in the original report, and the review confirms the
implementer's call to follow the controller over the brief was right. Left exactly where it was.

### Minor 4 — `_truncated`'s "all three worked outputs" claim

Swept `docs/design-principles.md`'s fenced example (the file the original sweep stopped short of):
`sha256:8e21...` / `3d8a...` / `6b1f...` → `…`. Grepped all four documents afterward for the ASCII
form beside `identical`/`DIFFERS` — none remain. The remaining ASCII `...` elsewhere in
`reference.md` (run.yaml/sweep.yaml examples, `design_digest`, etc.) are a different claim entirely —
not `diff`'s own worked output — and are out of this finding's scope.

### Minor 5 — the `not captured`/`not comparable` control was one-directional

Added `assert "not captured" not in out` to `test_h8b_config_vs_run_one_row_computed_four_not_comparable`,
closing the converse of the existing run-vs-run control.

### Minor 6 — nothing asserted `apparatus` prints fourth in real output

Added `assert _row_labels_in_output(out) == ROW_LABELS` to the Fixture U test — the one fixture where
`apparatus` actually prints (Fixture R2/L's pairs omit it), so it is the one place able to pin
position for all five labels against the real emitted text rather than the constant.

### Minor 7 — a report claim was not about the same thing as its evidence

The original report's § Gates sentence ("no shipped test other than the two named CLI-table tests
changed outcome") is corrected here rather than edited in place, per the development-record's own
append-a-correction convention: those two tests did not change outcome (both passed before and after
the flip); what changed is which branch each exercises, which the task-11 section two paragraphs
above it already said correctly.

### Minor 8 — the closing config-count claim was reasoned, not measured

Not restated here. The expectation stands ("H8b moves no config count"); the table itself is task
12's to re-measure and state.

### Minor 9 — `_render_apparatus_row`'s unused `letter_a`/`letter_b` parameters

Dropped. The function now hardcodes `"A"`/`"B"` at its one branch that needs a letter, since its one
caller (`_render_row`) never supplies anything else and `command_diff` always compares exactly two
sides under those two labels.

### Minor 10 — the M2 fixture's per-condition reorder was a no-op

Removed the inner per-fact reversal (each condition here holds exactly one fact, so reversing a
one-entry mapping changes nothing) and kept only the outer condition-order reversal, which is the
one that does real work. Updated the "confirm the reorder survives" assertion to match — it no
longer claims to check a per-fact order that was never exercised.

### Minor 11 — `apparatus DIFFERS` on a `null → value` transition the gate permits

**Filed, not fixed.** Appended an OPEN entry to `docs/superpowers/spec-defects.md` (owner:
unassigned) naming the divergence between `diff`'s row (compares the full `.hash`, which moves on
any `null ↔ value` transition) and the run-time gate's documented tolerance for exactly that
transition. Verified by running a probe answering `None` then a real value across two runs and
reading `diff`'s own output, reproducing the review's repro. Ruling: changing `diff`'s behavior to
share the gate's tolerance is a real design decision — it needs its own fixture pair distinguishing
a tolerated `null↔value` move from a genuine value move, the same two-fixture shape Major 2 needed —
and minting it inside a review fix round would be deciding a design question under review pressure
rather than through the process `CLAUDE.md` describes for one. The filing names both readings (fix
`diff`, or add one sentence to `reference.md`) and leaves the choice to whoever takes it.

### Minor 12 — an empty-string fact/parameter value rendered as nothing

Fixed in `_render_leaf`: `value == ""` now renders `""` explicitly, on the same false-appearance
reasoning `null`/`(absent)` already get their own words for. Two new tests
(`test_h8b_an_empty_string_apparatus_fact_renders_visibly`,
`test_h8b_an_empty_string_parameter_value_renders_visibly`) pin both the apparatus-detail path and
the parameter-delta path, since `_render_leaf` is shared between them.

### What was verified sound and left untouched

The review's own "what I verified by running and found sound" section — Decision 4's three exit
outcomes and its mutation pins, the `ROW_LABELS` edit and the emitted-order literal's reasoning, both
doc-agreement inversions, Decision 2's four shapes, the `not captured`/`not comparable` distinction,
Fixture U's honesty, the safe `entry['run_id']` direct index, and the document-scope check — none of
these needed a change and none was touched.

### Findings not closed, and why

None. All four Majors and all twelve Minors were either fixed, filed (Minor 11, deliberately, as a
design question this fix round should not decide alone), or disposed of with a stated reason (Minors
3 and 8, both already correctly scoped to task 12 by the original report).
