# Task 1 report — prose sites naming `E-DATA-ASSIGN-DRAWN`, and the four rows this slice implements

## Step 1: the enumeration, and proof it can fail

`grep -n 'E-DATA-ASSIGN-DRAWN' docs/*.md` returns 10 hits: 9 in `docs/reference.md`, 1 in
`docs/experimental-designs.md`. Matches the brief's expected 9/1 split.

Control probes on the same command:
- present code (`E-DATA-ASSIGN-LEVELS`) — returns 2 hits (`docs/reference.md` lines 439, 1197). Non-empty, so the grep can find something.
- absent code (`E-DATA-NOTHING`) — returns nothing, exit status 1. So the grep can also find nothing — the tool is not vacuously "always hits."

### The 10 sites that name the code, by file and containing section heading

`docs/reference.md`:
- § "Errors `validate` reports" — the `E-DATA-ASSIGN-DRAWN` table row itself, and a clause inside the neighboring `E-DATA-ASSIGN-METHOD` row that cross-references it (two hits, same section)
- § "Where units come from" — one sentence noting that `assign.method: blocked` reads the roster's order, "refused in this build as `E-DATA-ASSIGN-DRAWN`"
- § "Allocation: within-subjects or between-subjects" — three hits: the paragraph refusing `random`/`blocked` outright, the `blocked` block-size paragraph ("neither executes until `E-DATA-ASSIGN-DRAWN`'s refusal lifts"), and the `E-DATA-ASSIGN-VARIES` paragraph noting `from` isn't checked under `random`/`blocked` because both "are refused before execution as `E-DATA-ASSIGN-DRAWN` regardless"
- § "Clustered units" — one hit, in the paragraph on `assign.stratify_by` under `allocation: between`
- § "Expansion modes" — two hits: the group-level definition paragraph, and the closing sentence of the crossed-axes table's discussion ("the other two describe `random`, refused as `E-DATA-ASSIGN-DRAWN`")

`docs/experimental-designs.md`:
- § "Between-subjects / parallel-arm trial" — one hit, the paragraph immediately below that design's YAML

## The brief's undercount: two more sites describe the refusal without naming the code

Sweeping for the refusal's *description* rather than the code string (`git grep -n -e 'refused in this build' -e 'the refusal lifts' -e 'carries the same refusal' -e 'runs today' -- '*.md'`, filtering the file list only, never the matched lines) turns up two additional sentences that assert the same `random`/`blocked`-are-refused fact and that task 14 must also delete, but that the Step-1 grep is structurally blind to because they never spell the code:

- `docs/reference.md` § "Expansion modes", line 1719: "`arm`'s `method: random` carries the same refusal as the single-axis example above — `sex`'s `by_attribute` is unaffected."
- `docs/experimental-designs.md` § "Crossed group axes" (the 2×2 factorial example), line 121: "The `arm` axis's `method: random` carries the same refusal named above — `sex`'s `by_attribute` is unaffected, since it reads a column rather than drawing."

Both are direct restatements of the refusal in a second worked example and read as dead prose the moment drawing is built, exactly like the 10 code-naming sites. **So: 10 sites name the code, 2 more describe the refusal without naming it — 12 total for task 14 to touch, not 10.** Proof this sweep can also fail: the same phrase list run with `-e 'no such refusal phrase exists here 12345'` added returns nothing beyond the two above (confirmed by re-running without that impossible clause and diffing — the two lines above are stable across both runs).

Whole-tree check (not just `docs/*.md`): `git grep -n 'E-DATA-ASSIGN-DRAWN' -- .` also hits `src/publishable/artifacts.py:199`, `src/publishable/cli.py:316`, `src/publishable/units.py:388`, `src/publishable/validate.py:1321,1327,1376,1544`, `tests/test_cli.py:448`, and `tests/test_validate.py:8170,8187,8396,8401,8407`. None of these are docs, so they're outside this task's file list (`docs/reference.md`, `docs/experimental-designs.md` only, per the brief's own "Files" line) — but task 14 (or whichever task retires the code end-to-end) needs this list too, since the code itself and its tests still name the string in eight places across three source files and two test files. Recording it here rather than letting it be re-discovered.

`README.md`, `docs/design-principles.md`, and `docs/superpowers/spec-defects.md` were also checked directly for `E-DATA-ASSIGN-DRAWN` — none contain it (all three greps returned nothing, exit 1). `docs/superpowers/` planning files (`H3c-2-SCOPING.md`, `plans/2026-08-14-arms-drawn.md`, `specs/2026-08-14-arms-drawn-design.md`) do name the code, but those are this slice's own working documents, not "the four documents," and are outside this task's and (presumably) task 14's file list.

## Step 2: the "Assignment method isn't drawn" row vs. `DRAWN_ASSIGN_METHODS`

`docs/reference.md` § "Validation": *Assignment method isn't drawn* — "`assign.arm.method: random` or `blocked` — both are in the enum ... and both draw an arm rather than reading one already assigned, which is specified, not built in this build; only `by_attribute` executes."

`src/publishable/validate.py:1324`: `DRAWN_ASSIGN_METHODS = ("random", "blocked")`, checked at line 1542 (`elif method in DRAWN_ASSIGN_METHODS`), raising `E-DATA-ASSIGN-DRAWN` at line 1544.

Matches exactly: the tuple is `("random", "blocked")` and the row names both, in the same order, and the row's enum-ordering claim ("random, by_attribute, blocked") matches `ASSIGN_METHODS = ("random", "by_attribute", "blocked")` at `validate.py:1308`. Left as-is per the brief — task 14 removes this row.

## Step 3: the four rows this slice implements — exact quoted fault, and which method(s) each governs

All four quotes below are copied verbatim from `docs/reference.md` § "Validation." None of the four is implemented today: `validate.py`'s `elif method in DRAWN_ASSIGN_METHODS` (line 1542) raises `E-DATA-ASSIGN-DRAWN` and `continue`s before any `ratio`/`block_size`/`stratify_by` check for that axis runs, so none of these four checks is reachable under `random` or `blocked` in the current build, and none of the four is currently implemented for `by_attribute` either (no `ratio`, `block_size`, or `assign.<axis>.stratify_by` handling exists anywhere in `validate.py` today — confirmed by grep).

1. **Ratio names levels** — quoted in full: "`assign.arm.ratio` has key `f`; expected one entry per level of axis `arm` (`control`, `treatment`)". This is a check on `random`/`blocked`'s `ratio` (one entry per declared level). It is **not** the check that governs `ratio` under `by_attribute` — see "Already false" below; that's a separate, currently-undocumented-in-this-table rule.

2. **Block size fills the arms** — quoted in full: "`assign.arm.block_size: 3` with `ratio: {control: 1, treatment: 1}` — a block must be a whole multiple of the ratio's sum, or it can't hold each arm's share". Applies only under `method: blocked` (the only method with a `block_size` field).

3. **Stratification is forward-only** — quoted in full: "`assign.sex.stratify_by: [arm]`, but `arm` is declared after `sex`; an axis may only stratify on one already resolved". Applies to `assign.<axis>.stratify_by` under `random`/`blocked` (`by_attribute` axes carry no meaningful `stratify_by` per § "Where units come from" line 805: "left out of both `seed` and `strata`").

4. **Allocation strata exist** — quoted in full: "`assign.arm.stratify_by: [site]` but `site` is neither a unit attribute nor a group axis". Same scope as row 3 — `random`/`blocked` only, since `stratify_by` "means nothing" under `by_attribute` (§ "Allocation," the `E-DATA-ASSIGN-VARIES` paragraph).

**Ambiguity flagged for tasks 5/10/12/13 rather than resolved here:** rows 1 and 4 read as method-independent from their own wording (neither sentence says "under `random`/`blocked`"), but the surrounding prose (§ "Allocation" line 1211, § "Manifest" line 805) makes clear `ratio` and `stratify_by` are meaningless under `by_attribute`. Whoever implements rows 1 and 4 should gate them the same way row 2 is implicitly gated (only reachable once `method` is `random`/`blocked`), not attempt to apply them under `by_attribute` — where a *different*, currently-unimplemented rule (see below) applies instead.

## Already false / already disagreeing

**A live, reachable doc/code divergence, not gated behind the temporary `E-DATA-ASSIGN-DRAWN` refusal:**

`docs/reference.md` § "Allocation: within-subjects or between-subjects" (line 1211): "Under `method: by_attribute` a `ratio` describes a draw that didn't happen, so `validate` rejects a non-empty one instead of recording a proportion the data may not honour."

This is restated at § "Manifest" (line 805): "the same fault § Allocation names when it says a `ratio` under `by_attribute` 'describes a draw that didn't happen.'"

Checked against `src/publishable/validate.py`: no code path reads `assign.<axis>.ratio` at all under any method — a full-file grep for `ratio` inside `validate.py` finds only comments/docstrings, never a check. `by_attribute` is the one method that executes today, so this claimed rejection is reachable in the current build right now, not merely a description of unbuilt future behavior the way the four Step-3 rows are. No § "Validation" row asserts it either — *Ratio names levels* is about key-set coverage against declared levels, not about rejecting `ratio` outright under `by_attribute` — and no test in `tests/test_validate.py` asserts a non-empty `ratio` under `by_attribute` is rejected (grep for `ratio` combined with `by_attribute`/"describes a draw" in that file returns nothing). This is not recorded in `docs/superpowers/spec-defects.md` either (grep for the phrase there returns nothing). **This is a genuine defect independent of the `E-DATA-ASSIGN-DRAWN` retirement this slice is otherwise about** — a design/prose claim with no implementing code and no test, reachable today. Recommend a `spec-defects.md` entry; out of scope for this task to fix.

No other disagreement was found between the four Validation rows and the surrounding § Allocation / § Manifest / § Expansion-modes prose — the ratio/block_size/stratify_by mechanics they describe (one entry per level, block size a whole multiple of the ratio sum, forward-only stratification order, stratify target must be a unit attribute or an earlier group axis) all match the fuller explanatory paragraphs word-for-word in substance.

## Step 4: commit

No document text was changed — this task is reconnaissance only, and the brief says not to rewrite the refusal's prose (task 14 does that). Only this report file and the plan's `progress.md` (if updated separately) are new/changed, so `git commit -am` (stage-tracked-only) would not pick up this new report file; committing via explicit `git add` of the report path instead.
