# H5a — whole-branch review

**Verdict: MERGE.**

Reviewed as a fresh pass over the whole branch (43 commits), not a re-read of the nine batch reviews.
No Critical or Major found beyond what the batches already caught and closed. No cross-batch
interaction defect of the shape this gate exists to catch (a Critical reachable only end-to-end; a
guard made dead or falsified by a later batch) was found.

## Suite and gates

- `uv run pytest`, run directly, tree cleared first: **2891 passed, 1 skipped, 2 xfailed** — matches the
  slice's own target and is 56 above `main`'s 2835 baseline this branch reports elsewhere.
- `uv run ruff check .`: all checks passed.
- `uv run ruff format --check .`: 93 files already formatted.
- `uv run mypy`: no issues found in 52 source files.
- `git status --porcelain`: clean before and after this review's own probes; every mutation reverted by
  editing back and re-run to confirm.

## What was verified by behaviour (not just by reading the ledger/reports)

1. **End-to-end through the installed console script**, in three scratch projects built with `publishable
   new` + `generate_experiment` and committed to their own git repos, run with `uv run publishable
   validate|run` (not a direct-call probe):
   - `data.units.attributes: [cohort, unit]` → `validate` reports `E-UNITS-ATTR-COLUMN` naming `unit`,
     alongside the pre-existing `E-META-REQUIRED` findings — confirms the refusal fires at `validate` for
     a table source, through the real CLI.
   - A step recording a plain `measurement` column → `run` exits `4` (contained per-execution failure),
     `E-STEP-KEY-COLLISION` in every execution's `run.yaml` entry, and **no `units.parquet` written** for
     that step directory.
   - A step recording `by` and `measurements` (plural) columns, with no collision → `run` exits `0`, and
     the real `units.parquet` decodes to `{'unit': 'p1', 'present': True, 'by': 'STRAT', 'measurements':
     'plural_ok'}` — both survive, confirming the guard's precision (only exact-name `measurement`
     refuses).
   - A step calling `io.write("structural.parquet", [{"v": [1, 2]}, {"v": [3]}])` followed by
     `io.write("structural.csv", ...)` with the same rows → `.parquet` writes and decodes back to the
     exact structural rows (`[{'v': [1, 2]}, {'v': [3]}]`); `.csv` raises `E-STEP-RETURN-TYPE` with the
     artifact name prefixed (`"structural.csv: row 0 gave 'v' a list; ..."`), and the run's overall exit
     is `4` — confirming the per-format capability split end-to-end, not just at the encoder level.

2. **The per-format capability matrix**, driven directly against `_encode_csv`/`_encode_parquet` (both
   real encoders, not a synthetic stand-in), for every case the hunt named: `bytes`, `list`, `dict`,
   `None`, `np.float64` vs `float`, `np.str_`, `bool` vs `int`, a non-`str` column key. Every result
   matched what the design, the plan's corrections, and `spec-defects.md`'s three OPEN entries already
   state — including the two already-filed lossy/uncoded gaps (`.csv`'s `None → ''`, and a non-`str`
   column key writing silently through `.csv` while raising a bare `TypeError` through `.parquet`). No
   undisclosed fourth case found.

3. **A pyarrow `ArrowInvalid` escapes uncoded for a fully unencodable object** (a bare custom class
   instance with no `__len__` and no numeric protocol) written through `_encode_parquet`, caught by
   `_coerced_rows`'s `except ContractError` and passed through raw under `keep_structural=True`, then
   failing inside `pa.table(...)`. **Checked against `main`'s unmodified `_encode_parquet` and
   `_check_column_types`** (same code path — a homogeneous column of one non-scalar type never trips the
   two-group clash check) — this is **pre-existing on `main`, not introduced or worsened by H5a's
   decisions**, and is a narrower instance of the general shape `reference.md`'s own `2**53` int-overflow
   disclosure and the two already-filed "bare traceback" `spec-defects.md` entries already name. Not a
   new finding; not routed, since it predates the branch and no H5a decision touches it.

4. **Arm E1/E2 editor authorization**, re-derived from `git log -p` rather than trusted from the ledger's
   prose: `test_h5a_arm_e1_parquet_keeps_a_structural_or_bytes_cell_intact` appears only in its creating
   commit (`295c6e3`) and once more as unmodified diff *context* in `eeebd89` (task 9) — its body was
   never edited. `test_h5a_arm_e2_...` was edited only in `eeebd89`, the task named as its sole authorized
   editor. The "no authorized editor" pin on arm E1 held for the whole slice.

5. **§ Errors emit-site counts, re-derived by grep against the shipped `src/`**, independent of the
   batch-9 review's own numbers: `E-STEP-KEY-COLLISION` — 8 raise sites (6 in `artifacts.py`, 2 in
   `stats.py`) — matches the batch-9 fix round's corrected count. `E-UNITS-ATTR-COLUMN` — 3 sites
   (`_from_table`, `_from_glob`, `_from_resolver`), one emit path through `validate`'s gate, as documented.
   `E-ARTIFACT-UNWRITABLE` — 2 sites. `E-STEP-RETURN-TYPE` — 3 sites (`runner.py`, `coercion.py`,
   `artifacts.py`). `E-RESOLVER-YIELD` — 2 sites. All match `reference.md`'s corresponding rows.

6. **One independent discriminating mutation**, built at the call site rather than trusted from the
   report: deleted the roster-attribute-coercion rebuild loop in `units.resolve_units` (reverting to
   `return UnitList(units), technical_n, columns`) and re-ran
   `test_arm_o1_a_structural_resolved_attribute_pays_for_nothing_before_it_refuses`. **Result: the run
   completes at exit 0 with a real `run.yaml` written**, instead of refusing before the first execution —
   reproducing exactly the "every execution paid for, the record lost" hazard Decision 6 exists to
   prevent. Reverted by editing back (not `git checkout`), confirmed by `git diff` being empty and by
   re-running the arm and its positive control (`test_arm_o2_...`), both green.

7. **Development-record integrity**: `git diff main...HEAD -- docs/feasibility-llm-growth-studies.md` is
   empty — the feasibility analysis is untouched, as required. The design and plan's only in-branch edits
   to already-existing prose are appended corrections (`## Correction, 2026-08-22 — ...` as a new section
   in the design; a task-text amendment in the plan's own consistency-sweep bullet, correcting an
   under-stated home list before task 4 runs) — no retro-edit of a decision's original text found.
   `spec-defects.md` diffs are amendments and strikes, consistent with it being the one live-list
   exception.

8. **Mechanical consistency pass** over the four documents: no trailing whitespace/tabs found; anchor
   checks that first appeared to fail (`#secrets--credentials`, `#within-subjects--repeated-measures`)
   were traced to GitHub's slugger not collapsing multiple consecutive hyphens from stripped punctuation
   (`&`, `/`) — confirmed by reading the actual heading text; not a real broken link. `README.md` and
   `docs/design-principles.md` have a zero-line diff on this branch, so the worked example's pinned
   intervals are untouched by construction.

## What was verified by reading only

- The full task-by-task commit sequence, all nine batch reports/reviews, the design's two appended
  controller rulings and the appended Fixture-E correction, the plan's twelve corrections and its own
  appended correction, and every `spec-defects.md` entry this branch opened, closed, or re-owned. All
  ledger claims about counts and closures that I independently re-derived (§4, §5 above) matched; I did
  not re-derive every one of the ~30 individual mutation claims listed across the nine task reports —
  those were each caught by their own batch review, and the ledger records which miscounts (three, all in
  reporting rather than in code) were found and corrected.

## Assessment of the "defect no per-task review could see" hunt

The one candidate cross-batch interaction with real teeth — **task 9's `.parquet` capability landing
after task 6's mutation was written, changing where task 6's pin surfaces without weakening it** — was
already found and disclosed by batch 8's own review (recorded in the ledger under "a mutation's
prediction can go stale under a later task in its own slice"), and I independently re-confirmed the pin
still holds post-task-9 via the mutation in item 6 above. I looked for a second instance of the same
shape (a guard from an early batch made dead, or falsified, by a later one) across arm authorization
(§4), the `RESERVED_COLUMNS` single-reader rule (re-read against `units.py`'s current source — still one
reader, the three attribute call sites, matching correction 1), and the `by`-survival guarantee (re-run
end-to-end in item 1) and found none outstanding.

## Routed / not routed

Nothing new to route. The three OPEN `spec-defects.md` entries this branch left (the `.csv`/`.json`/
`.yaml`/`.jsonl` nested-NumPy-scalar gap, the non-`str` column-key gap, the direct-`Unit`-construction
`unit`-shadow residual, and the `.csv` `None → ''` gap) all reproduced exactly as filed, with correct
owners ("unassigned, with the reason" — no remaining slice charters any of them). The pre-existing
`ArrowInvalid`-for-an-unencodable-object gap found in this review (§3) is not routed: it predates the
branch, no H5a decision touches it, and it is a narrower instance of an already-disclosed/filed class.
