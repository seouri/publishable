# Batch 1 review — H5b tasks 1, 2, 3

**Commits reviewed:** `23b79a9` (task 1), `bc4e56e` (task 2), `2e9f5e4` (task 3), `31a5f31` (report).
Baseline `main`/`ee8085e`, HEAD suite re-run **2895 passed, 1 skipped, 2 xfailed** — matches the claim
(2891 + 4 new). Gates re-run: `uv run ruff check .` clean, `uv run ruff format --check .` — 93 files
unchanged, `uv run mypy` — 52 source files clean.

## Verdicts

- **Task 1 (the guard pin): PASS.**
- **Task 2 (§ Templates): PASS.**
- **Task 3 (§ per-unit tables / § Statistical reporting / `W-STATS-REPEATS-DISAGREE` / spec-defects
  filing): FAIL — one Critical.**

## Arm E — reproduced

Re-ran arm E's fixture independently (not the committed test — a fresh scratch script driving
`run_a_project` with `GenericTemplate.aggregate` monkeypatched to `_arm_e_aggregate` **and**
`publishable.cli.collapse_repeats` monkeypatched to `_arm_e_widened_collapse`, exactly as the report
describes but built from scratch rather than read). Every AFTER literal reproduced exactly:
`n_paired` 4→6; `mean_score.correction_level` 0.025→0.05; `score.correction_level` 0.05→0.025;
`score.ci95_corrected` → `[-0.10000000000000017, -0.09999999999999995]`; `mean_score.ci95`/
`ci95_corrected` (own contrast) → `[-0.10000000000000053, -0.09999999999999964]`; baseline
`mean_score.ci95` → `[0.8333333333333334, 3.1666666666666665]`; spearman `mean_score.ci95` →
`[0.7333333333333334, 3.0666666666666664]`; and the "must not move" set (`score.n_paired` stays 4,
`score.ci95` unmoved, `n_rows.correction_level` stays `0.016666666666666666`) held. **Reproduced,
verified by an independently-written script, not by reading the committed test.** The two extra
moving keys the design's paragraph does not name, per correction 9, are: the derived contrast's own
`ci95`/`ci95_corrected` (`mean_score`'s `vs_baseline` block) and both conditions'
`aggregated…mean_score.ci95`.

## Task 1 — verified by mutation, not just by reading

All five arms and all five prescribed mutations were run directly (each source file copied before
mutating, restored after, restoration confirmed `diff`-identical):

- **Arms C and D genuinely pre-exist, byte-for-byte.** `git diff ee8085e HEAD -- tests/test_cli.py`
  and `-- tests/test_stats.py` show zero touched lines anywhere near
  `test_a_recorded_column_named_by_keeps_its_metric_and_warns`,
  `test_a_recorded_by_column_warns_even_with_no_report_by_declared`,
  `test_an_unknown_column_raises`, or
  `test_a_derived_key_colliding_with_a_recorded_column_is_refused` — none of the four appears in
  either diff's hunks at all. Read all four bodies: they match the report's description exactly
  (`by["value"] == pytest.approx(39.0)`, `UnitTable({"u1": {"pred": 1.0}}).nope` raising
  `E-STEP-COLUMN-UNKNOWN`, a numeric `{"r": float(i)}` collision raising `E-STEP-KEY-COLLISION`).
- **Mutation (i)** (`collapse_repeats`: delete `or not _is_numeric(value)`): arm B's TODAY assertion
  failed as claimed (`narrow` gained `valid: 1.0` on every unit); arm A passed unaffected. Confirmed.
- **Mutation (ii)** (`summarize_step`: `if not raw:` in place of `if not raw or not all(_is_numeric...)`):
  arm B's `"valid" not in after` assertion failed (a `valid` metric block appeared). Confirmed.
- **Mutation (iii)** (`cli.py`'s `by` gate → `if False:`): both arm C tests failed
  (`W-STATS-STRATUM-SHADOWED` no longer in stdout). Confirmed.
- **Mutation (iv)** (reverse Holm rank ordering in `correction.py`): `score.correction_level`
  assertion failed (`0.05` expected, got `0.016666666666666666`, matching the report's own number);
  `mean_score.correction_level`'s assertion did **not** fail (stayed `0.025`) — confirming the
  report's own disclosed median-rank-fixed-point argument for a 3-member family
  (`α/(m−rank+1)` at `m=3` maps rank 2 to itself under reversal). **One thing the report did not
  disclose:** this same mutation also fails arm A (a 2-member family has no fixed rank, so both
  `correction_level`s swap) — not a defect, since it only *strengthens* coverage, but the report's
  mutation-4 narrative describes only arm E's effect.
- **Mutation (v)** (`UnitTable.__getattr__` returns an all-`None` column instead of raising): arm
  D(i) failed (`DID NOT RAISE ContractError`). Confirmed.

All five source files verified byte-identical to `ee8085e`-derived state after each restore, and the
whole suite (re-run at the end) is back to 2895/1/2. Task 1 is a well-built pin.

## Task 2 — PASS

`docs/reference.md` diff matches the brief exactly: one paragraph edited under
`## Templates: where parameters are defined` (anchor `#templates-where-parameters-are-defined`,
confirmed correct heading — the `my_assay` `## Templates` section is untouched), the four-operation
contract table untouched, links to `#what-isnt-a-repeat` (verified at line 2055,
`#### What isn't a repeat`) and `#warnings-core-reports` (verified at line 369,
`### Warnings core reports`) both resolve. Mechanical pass clean (no trailing whitespace/tabs on the
edited line).

## Task 3 — FAIL

**Critical: the document contradicts binding Controller Ruling 1, and states the exact behaviour the
ruling was written to reject.**

Ruling 1 governs "a column that is numeric for some units and `None` for others" and is explicit:
*"the mean over the units that recorded a value, and `n` reports the number that contributed — not
`completed`"*, with the alternative named and rejected in so many words — *"Dropping the column
because one unit recorded `None` IS the defect this slice exists to end."*

The sentence task 3 shipped in § Statistical reporting reads: *"A column in `units.parquet` earns a
block in `aggregated` only when every value carried for it is a real number ... so a column that is
`str` for even one unit, or that a repeat-level disagreement collapsed to `None`, reaches
`aggregate`'s table but publishes no metric block of its own."* This is an unconditional "drop the
whole column if any cell isn't a real number" rule — precisely the reading Ruling 1 names as the
defect to end, not the mean-over-contributors-with-a-named-`n` rule the ruling requires. Nowhere in
either edited document does any sentence say "mean over the units that recorded a value" or that `n`
reports a contributing count distinct from `completed`; grepped for `contributing`, `mean over`, and
`n reports` in `docs/reference.md` — the only pre-existing hits at unrelated lines (789, 794), none
introduced by this commit.

**Root cause, verified by reading the brief against the plan:** task 3's brief (Step 1, Step 2)
instructs exactly the sentence that shipped — *"This is the total rule over however a mixed column
arises"* — which is Decision 11/correction 5's pre-ruling framing, extracted from the plan body
**before** the controller's rulings were appended at the end of the same plan file. This is the
repo's own named failure mode (*"A ruling that overrules a brief has to reach the brief... the ledger
reaches the controller and the reviewers; it reaches no implementer"*), recurring inside the very
slice whose plan documents it. Task 3 followed its brief literally and did not cross-check it against
the controller rulings section of the same plan file, which explicitly states it binds "every task
below."

**Verified this is not merely academic:** traced the live code path this documents
(`summarize_step`'s column loop, `src/publishable/stats.py` ~line 3002):
`carried = [(key, cols[column]) for key, cols in collapsed.items() if column in cols]` already
excludes units that never recorded the column at all (so a genuinely *absent* key, like arm B's
`score` on `u4`/`u5`, is unaffected either way — this is why arm B does not detect the gap). The gate
`if not raw or not all(_is_numeric(v) for v in raw): continue` is reached, and drops the whole metric,
specifically when a unit's row **explicitly carries `None`** for that column (a legal recorded value,
and exactly what a disagreement-driven `_across_repeats` resolution or a step's own explicit `None`
write produces) while another unit's row carries a real number for the same column — the design's own
probe `p3` ("one `None` cell and five floats … publishes no metric block at all") is precisely this
case. **Task 4 (batch 2), reading the shipped document as the spec it is supposed to implement, would
build the `all-or-nothing` gate exactly as it is today — leaving Ruling 1 unbuilt — unless it notices
the plan's controller-rulings section independently of the brief.**

**Not this batch's bug to have caught by its own tests:** no fixture in task 1's guard pin exercises
an explicit `None` cell mixed with real numbers in the same column (arm B's gap is absence, not an
explicit `None`), so the suite staying green is not evidence this is fine — it is the "config that
separates the readings was never built" shape.

**Everything else in task 3 checked out:**
- `W-STATS-REPEATS-DISAGREE` — one production call site confirmed
  (`grep -n 'collapse_repeats(' src/publishable/*.py` → one in `cli.py` plus the definition in
  `stats.py`), row placed alphabetically between `W-STATS-NULLTEST-FAMILY` and
  `W-STATS-REPORTBY-THIN` by grepping the codes (confirmed by direct grep in `reference.md`).
  Ruling 2 compliance: the row's condition text names `data.units.measurements` only as the declared
  **remedy** ("the declared route for a within-unit collapse is..."), not as the `where` locator,
  which Ruling 2 explicitly permits.
- The three named § Errors rows (`E-STEP-KEY-COLLISION`, `E-STEP-COLUMN-UNKNOWN`,
  `E-STEP-RETURN-TYPE`) — read each at its cited line, none moved, matches the report.
- **spec-defects filing reproduces exactly**: `git show ee8085e:docs/superpowers/spec-defects.md |
  grep -c 'more forgiving\|mixed column'` → 0; `grep -c 'E-STEP-RETURN-TYPE'` at the same commit → 4;
  at HEAD, `E-STEP-RETURN-TYPE` count → 7 and the phrase now appears once (the new entry). The
  control (a count that *can* hit) and the target (a count that was 0 and is now present) both
  reproduced independently. The owner is stated as a fact with a reason (no remaining slice charters
  the write side; H5a merged) — not a "whichever slice" deferral.
- Mechanical pass on both edited files: no trailing whitespace/tabs (`grep -nP ' $|\t'` clean), table
  row column counts consistent on the edited rows.

## Suite / gates

- `uv run pytest` → **2895 passed, 1 skipped, 2 xfailed** (re-run at HEAD after every mutation was
  reverted and verified byte-identical). Matches the report's claim exactly.
- `uv run ruff check .` → clean.
- `uv run ruff format --check .` → 93 files, unchanged.
- `uv run mypy` → 52 source files, no issues.

## What was verified by behaviour vs. by reading

**By behaviour (ran it):** arm E's full re-measurement (independent script, not the committed test);
all five task-1 mutations (i–v) applied to the actual source, run against the actual arms, reverted
and diff-verified; the full suite; all three gate commands; the spec-defects grep counts at both
`ee8085e` and HEAD; the anchor-existence checks for task 2's two links.

**By reading (not run, since no code exists yet to run against):** the consequence of task 3's
shipped sentence for `summarize_step`'s cross-unit gate — traced the exact line
(`src/publishable/stats.py` ~3002) the sentence describes and confirmed its current behaviour matches
what the sentence states (i.e., the sentence is an accurate description of **today's** code), but that
today's code is precisely what Controller Ruling 1 requires to change, and the document does not say
so.
