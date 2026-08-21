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
