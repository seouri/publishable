# Batch B6 report — tasks 9, 10, 11 (the slice's last three)

**Commits:** `0e40403` (task 9), `70c2283` (task 10), `db7f187` (task 11).

**Test summary:** 2453 passed, 1 skipped, 2 xfailed (baseline) → 2455 (task 9, +2) → 2456 (task 10,
+1) → 2456 (task 11, documents only, unchanged). Final: **2456 passed, 1 skipped, 2 xfailed.**
`ruff check .`, `ruff format --check .`, `uv run mypy` (46 source files) all clean at each commit.

## Task 9 — no policy knob (Decision 7)

Arm (a) (`tests/test_validate.py`, `_validate_with`): `limits.allow_apparatus_change: true` earns
`E-CONFIG-KEY-UNKNOWN` at that exact path; the same config without the key does not. Uses
`_validate_with` deliberately (not `write_config`) because its directory name is never
`cohort-pilot`, so both configs earn an incidental `E-NAME-DIR` — asserted alongside, on the
difference in `E-CONFIG-KEY-UNKNOWN` paths, never a total code set.

Arm (b) (`tests/test_cli.py`): Fixture G1's own by-call schedule (a probe whose `pinned` fact
changes on call 4), reused under new distribution/module names, with every existing `limits` key at
its most permissive value (`max_failed_fraction: 1.0` load-bearing, since that guard fires on `>`
and can never fire at `1.0`). The run still stops at 2 of 4 executions, `status: failed`, exit 4.

**What this pins, stated in both docstrings and here again**: only that TODAY's schema and TODAY's
most-permissive config don't soften the gate. Neither arm, nor any test, can pin the absence of a
field nobody has written — a docstring claiming otherwise would itself be the kind of overclaim
`CLAUDE.md`'s misreading table warns against.

**Mutation (step 5), run and reverted**: made the gate return early whenever `cfg.raw.get("limits")`
is truthy (`apparatus.py`, `Observer._observe_one`). Arm (b) FAILED as predicted — exit 0 instead of
4, 4 executions instead of 2 (required extending the probe schedule by one entry so the run could
reach full completion rather than hitting `IndexError` from the schedule running out, a different
and uninteresting failure I did not want the pin resting on). Arm (a) is blind to it, as stated — a
schema check cannot see a code-path mutation. Reverted by copying back a pre-mutation backup and
verified byte-identical via `git diff` (no diff on `apparatus.py`).

## Task 10 — `batch` and the apparatus stay independent (Decision 8)

Two arms in `tests/test_cli.py`, `{kind: seed, n: 4}` vs. one `{kind: batch, n: 4}`, equal `n` as the
design requires. I initially built this with a probe that never varies its fact — that measures
nothing, since a gate that never has anything to disagree about cannot distinguish a repeat-aware
key from a condition-only one. Caught this before committing (nothing in the design's own "Computed
expectations" — `len(executions.jsonl) == 2` in both arms — was consistent with a constant-fact
probe running to completion) and rebuilt it on G1's own schedule shape instead: the fact changes on
call 4, so the gate stops **both** arms at the same execution index (2 of 4) if `batch` and the
apparatus are genuinely independent. Asserted on the ordered `(phase, condition)` ledger sequence,
`provenance.apparatus.facts`/`.hash`, and `len(executions.jsonl)` — never on whole stdout/stderr,
since the `batch` arm earns `W-REPL-DETERMINISTIC` and the `seed` arm does not.

**Mutation (step 4), run and reverted**: threaded `execution.repeat_label` through
`Observer.observe_round`/`_observe_one` (`apparatus.py`, `runner.py`) and keyed the gate's
`Observations` calls on `f"{key}:{repeat_label}"`. Confirmed the predicted divergence: the `seed`
arm's four distinct labels never contradict each other and the run completes (exit 0), while the
`batch` arm's single label still stops (exit 4) — two different execution counts, not a crash.
Reverted both files from pre-mutation backups; `git diff` confirmed byte-identical.

## Task 11 — documents and filings

**How I enumerated the codes and confirmed emit sites**: read `apparatus.py` top to bottom first
(`check_facts`'s four raises, `check_changed`'s one, `observe_once`'s one), then grepped
`docs/reference.md` for each of the five existing rows plus `E-APPARATUS-CHANGED` to confirm which
already existed and which didn't — reading first, confirming by grep second, per `CLAUDE.md`'s own
rule about the order that shipped a credential leak when reversed.

**Rows written**: a new `E-APPARATUS-CHANGED` row, sited immediately after `E-APPARATUS-FACT-MISSING`
(the gate runs after `check_facts`'s four checks, so that's the sibling row whose job placement
decides), stating the comparison, what the message names, and the outcome. `E-APPARATUS-RAISED`'s
row rewritten in place to cover both outcomes — run-start (ends the command, exit 5, no record) and
mid-plan (stops the plan, `status: partial`, exit 5, record kept) — one row per code as the design
requires.

**Two carried findings, both fixed**: `reference.md`'s "its record is kept rather than discarded"
(§ The apparatus core can only observe) is now qualified for the moved-with-zero-results corner,
which has none; § Exit codes' `1` row now names that corner. `experimental-designs.md`'s apparatus
row said "first observation" where `reference.md` says "first *answered* observation" (batch 1's
correction 6) — tightened to match, with a clarifying phrase to avoid reading "first answered
observation" as itself "a prior observation" (caught this ambiguity on a second read of my own edit
and fixed the wording before committing).

**Three filings, against what the brief named** — enumerated here as the brief's step 6 requires:

1. **`EXIT_EXTERNAL` — struck**, own entry, heading rewritten with strikethrough per this file's
   existing convention (`~~...~~` — CLOSED by ...), body kept as the historical record with a closing
   paragraph naming what closed it and citing the two tests that pin it now.
2. **The four fact-contract refusals' lost record — new entry**, own entry (not a clause), because
   the brief named it as a filing in its own right. Includes a measurement I ran myself rather than
   trusting the design's transcription: a probe whose declared fact goes missing on call 3 gives
   exit 1, `E-APPARATUS-FACT-MISSING`, no `run.yaml`, and exactly one execution's artifacts on disk
   (`executions.jsonl` with one `completed` line) — built as a throwaway test, run once, removed
   before committing (confirmed `git diff tests/test_cli.py` empty afterward).
3. **`max_failed_fraction`'s truncation status — new entry**, own entry, explicitly stating it is
   also where task 1's remainder goes (both halves are one document-versus-code disagreement about
   one guard). Both faces of the `§ What status means` contradiction are in this one filing: the
   `failed` paragraph's clause the code contradicts (already reported by batch 1) and the `partial`
   paragraph's "one thing produces that" claim, which batch 1's review found also false (a
   `max_failed_fraction` stop over a mixed result set is a second early-stopping-`partial` producer)
   and which the earlier report had not named. I did not re-derive these two measurements from
   scratch — I identified and read the two shipped, already-passing tests that already establish
   them (`test_max_failed_fraction_is_measured_against_the_test_partition`,
   `test_a_mixed_truncation_is_partial_at_exit_3`) rather than building new fixtures for facts the
   suite already pins.

**Where a brief/design/plan disagreed with the code, after grepping what each asserted**: I found no
new disagreement in the docs I touched. Two things I checked specifically because the plan warns
about exactly this shape: the "non-`str` credential carve-out... surface includes `run.yaml`" item
the brief lists among "the remaining filings the design names" turned out to already have its own
complete entry (batch 5 review, Minor 3, appended 2026-08-20) — I verified this by reading the full
entry rather than trusting the brief's characterization of it as still owed, and made no edit there.
Everything else in the design's own "Corrections against the code" section (`run_status` living in
`run_record.py`, the bare `assert` rather than a coded error, `run_a_project`'s widened guard, the
`STOP_CODES`/`APPARATUS_CODES` split, Fixture T's mixed arm, the two-comparison-rules divergence, the
truncation reachability) was already landed in earlier batches and is untouched by this batch.

**Untouched and named, per the brief's step 7**: `BaseTemplate.field_convention` and `io.reuse_from`
— neither is apparatus, and no sentence in my edits implies otherwise.

## Mutation discipline

Both prescribed mutations (task 9 step 5, task 10 step 4) were run against the **full** suite before
being judged, not just the target test. Both were reverted by copying back a pre-mutation file
backup and confirmed reverted with `git diff` (empty) rather than by trusting `git status`, per
`CLAUDE.md`'s own rule about verifying a revert by behaviour. Neither mutation was caught by a crash
— both failed on ordinary assertions with a real, predicted divergence (execution count and/or exit
code), not an exception.

## Concerns / residue for whoever finishes the branch

- This report and its commits do not update `CLAUDE.md`'s own running log with an H7d Part B merge
  entry — that's a finishing-the-branch action, not part of tasks 9–11's brief, and I left it alone.
- The two new `spec-defects.md` filings are both `unassigned`, each with a reason stated as the brief
  requires — no ledger-line placeholder was written in their place.
