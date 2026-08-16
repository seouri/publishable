# H3d — whole-branch review

Reviewed: branch `h3d-fixed-holdout` (72 commits, 20 tasks) against `main` at `78bb794`,
on 2026-08-16.

**Verdict: ready to merge**, with four Important findings that should be closed on this
branch first. None is a wrong number shipping to a user; all four are documentation
completeness or a missing pin. No Critical finding.

Baseline verified before any mutation: `uv run pytest` → **1954 passed, 2 xfailed**;
`uv run ruff check .` → clean; `uv run mypy` → clean (42 source files). Every mutation
below was reverted by editing the file back and re-verified by re-running the affected
tests — never by `git status`, never with `git checkout --`. Tree confirmed clean at the
end of the review (`git diff --stat HEAD` empty).

---

## Critical

None.

---

## Important

### I1. Two `E-DATA-HOLDOUT-*` run-time raises are documented by no § Errors row — and one is reachable on a config that validates clean

`units.holdout_for` raises two coded `ContractError`s:

- `E-DATA-HOLDOUT-VALUES` — `units.py:1407`
- `E-DATA-HOLDOUT-EMPTY` — `units.py:1493`

Neither appears in `reference.md` § Errors core raises. That table is the enumerated
per-code list of what core raises at run time, and this is the exact trap `CLAUDE.md`
records as already made once: *"§ Errors carries one row per code, not per emit site, so
a diagnostic's unit of work is every site that raises **or** reports it."*

`EMPTY` is not a theoretical second site. `validate._check_holdout`'s zero-test-side
check is deliberately gated to the **unstratified, unclustered** draw
(`validate.py:3004-3011`, with a comment saying so, and § Errors row 487 saying so). The
clustered and stratified draws are checked **only** at run time — so a clustered holdout
can validate clean and then abort the run, with no normative document naming that
surface.

**Verified** by direct execution over a 12-unit roster:

```
clusters=1 frac=0.1 validate_sizes=(11, 1) -> RAISED E-DATA-HOLDOUT-EMPTY
clusters=1 frac=0.2 validate_sizes=(10, 2) -> RAISED E-DATA-HOLDOUT-EMPTY
clusters=1 frac=0.3 validate_sizes=(8, 4)  -> RAISED E-DATA-HOLDOUT-EMPTY
```

`holdout_sizes(12, 0.1) = (11, 1)` — a non-zero test side, so `validate` reports nothing
— while the clustered draw over the same roster raises. That is the
validate-clean-then-fail gap the surrounding rows exist to close.

The fix's shape is settled by an immediately adjacent precedent written for the identical
situation: `E-DATA-ASSIGN-LEVELS` carries **both** a § Errors `validate` reports row
(line 467) and a § Errors core raises row (~line 993), the latter reading *"raised here
for the three draws that pass validate-time: a clustered one, whose empty arm depends on
the seed, and a stratified one of either kind."* `E-DATA-HOLDOUT-EMPTY` needs the same
second row; `E-DATA-HOLDOUT-VALUES` needs one beside it.

**The existing validate-side row 487 needs no companion edit.** I compared it against how
`E-DATA-ASSIGN-LEVELS`'s validate row (467) handles the same split. Row 467 does not
cross-link its core-raises sibling either; it states the residue in prose — *"All three
therefore still reach this code at the draw rather than at `validate`"* — and row 487 does
the same thing in its own words: *"a stratified or clustered split is checked where the run
performs it, because a cluster is the smallest thing that can move and only the draw knows
what it moved."* So the pointer is already carried on the validate side in the house style,
and two new § Errors core raises rows are the whole of the fix.

**Blocks merge:** no. Two table rows, no code change. Close it here rather than filing —
the slice that minted the codes is the cheapest place, and this is a known repeat trap.

### I2. `E-DATA-HOLDOUT-VARIES` is missing from § Errors `validate` reports, while its own row asserts `validate` reports it, and all three siblings carry that row

`reference.md` line 990 (§ Errors core raises) documents `E-DATA-HOLDOUT-VARIES` and
states it is *"also [reported by `validate`](#errors-validate-reports) under the same
code, reaching it through the resolution it performs, same as the other three."*

The claim is **true** — but the table it links to has no such row. § Errors `validate`
reports carries eleven `E-DATA-HOLDOUT-*` rows (lines 478-488) and `VARIES` is not among
them, while each of the three siblings the sentence names does have one:
`E-DATA-ASSIGN-VARIES` (477), `E-DATA-CLUSTER-VARIES` (492), `E-DATA-WEIGHT-VARIES`
(503). The cross-reference resolves to a table that does not contain the code it sends
the reader to look up.

The plan (`plans/2026-08-15-fixed-holdout.md:329`) said *"check which table those three
live in and put it there."* Those three live in **both** tables; the implementer put
`VARIES` in only one. This is a cross-task drift: task 2 wrote the row, and no later task
re-checked the sibling set it claims parity with.

**Verified** two ways:

1. `grep -nE '\| `E-DATA-HOLDOUT-[A-Z-]+` \|$' docs/reference.md` returns eleven rows,
   none `VARIES`.
2. A temporary test appended to `tests/test_validate.py`, modelled on the existing
   `test_an_arm_varying_within_a_units_rows_is_reported`, over a roster whose
   `holdout.from` column disagrees across one unit's measurement rows:
   `CODES: ['E-DATA-HOLDOUT-VARIES']`, 1 passed. So `validate` does report it and the
   missing row is the defect, not the sentence. (Probe removed by editing the file back —
   `tests/test_validate.py` is 12175 lines before and after — and the removal verified by
   re-running `uv run pytest tests/test_validate.py -q` → 675 passed.)

**Secondary, same finding — a check that does not exist rather than one that cannot
fail:** `E-DATA-HOLDOUT-VARIES` has **no validate-surface test**. It appears in
`tests/test_units.py` only (2930, 3529, 3610 — the raise), while each of its three
siblings has both a validate-surface test and an explicit "validate reports rather than
raising" test in `tests/test_validate.py` (~7920, ~7946, ~8057). The behaviour is correct
today, as the probe shows, but nothing holds it there.

**Blocks merge:** no. One table row, one test.

### I3. `provenance.units_hash` narrowing to the test partition passes the entire suite — half of the spec's own Trap 1 is pinned by nothing

The slice's spec names this as trap 1: *"`provenance.units.n`/`units_hash` **stay
whole-roster**, with a comment saying why 240-here and 48-there is not a bug."*
`cli.py:2622-2630` carries that comment and ends *"Narrowing this would make the hash
cover a subset the config never described."*

**Verified by mutation.** Two mutations at `cli.py:2631-2636`, each reverted in place and
re-verified by re-running:

| Mutation | Result |
|---|---|
| `{"n": len(roster), ...}` → `{"n": len(eval_roster), ...}` | **FAILS** — `test_a_declared_holdout_now_validates_and_runs` at `tests/test_cli.py:8220` |
| `units_hash(roster)` → `units_hash(eval_roster)` | **PASSES — full suite green, 1954 passed + 2 xfailed** |

So the `n` half is pinned and the `units_hash` half is not. The end-to-end holdout test
asserts `run["provenance"]["units"]["n"] == 20` beside `metric["n"]["resolved"] == 4`
(`tests/test_cli.py:8220-8225`) and asserts nothing about `units_hash` at all.

This is a live instance of the shape the ledger itself flagged at task 1 and thought it
had closed. The ledger (progress.md:69-71) records: *"units_hash pinned as a SHAPE
(`startswith("sha256:")`) on one of the two values task 15 must not touch... Ruled:
recompute and compare, not a literal digest."* That fix landed — but in
`test_a_run_without_a_holdout_pins_its_denominators_and_artifacts`, a **no-holdout** run,
where `eval_roster` **is** `roster` (the same object; `_evaluation_roster` returns it
unchanged, `cli.py:547-548`). The distinction the pin exists to hold cannot appear on
that fixture. This is `CLAUDE.md`'s *"a dimension no assertion can see"* combined with
*"a fixture whose numbers agree with the bug"*: the pin was strengthened correctly and
sited where the property is invisible.

`units_hash` is load-bearing beyond tidiness — it is what makes a roster that resolved
differently detectable on reproduction, and narrowing it silently rebases that identity
on a seed-dependent subset.

**Fix:** one assertion in `test_a_declared_holdout_now_validates_and_runs` — recompute
`units_hash` over the whole 20-unit roster and compare, beside the existing `n == 20`.

**Blocks merge:** no, but this is the finding I would most want closed before merge. It
is one line, and it guards an invariant `CLAUDE.md` names explicitly.

### I4. `holdout`'s two remaining fields never appear in § The one config file, breaking the config-completeness rule against its closest sibling

`CLAUDE.md` § Checking consistency: *"Every config field documented anywhere in
`reference.md` must appear in § The one config file, whose fenced example ... [is] every
parameter `publishable init` materializes, plus **the optional blocks it leaves empty or
undeclared**."*

§ The one config file shows (reference.md:91-93):

```
    holdout: null                          # {method: random, frac: 0.2} or {method: by_attribute,
                                           #   from: split}; optional single fixed train/test
                                           #   split — see "A fixed holdout split"
```

`method`, `frac` and `from` appear. **`stratify_by` and `seed` do not** — anywhere in
that section. Both are real fields: `envelope.py:92-122` closes the block at exactly five
keys; `validate` enforces both under their own codes (`E-DATA-HOLDOUT-STRATIFY-UNKNOWN`,
`E-DATA-HOLDOUT-SEED`, and `E-DATA-HOLDOUT-NO-DRAW` for a `stratify_by` under
`by_attribute`); § A fixed holdout split's own fence (reference.md:1317-1322) shows all
five; and § What `auto` derives from (line 2751) names `holdout.seed` beside
`assign.seed` and `sweep.sample.seed`.

The asymmetry is sharpest against the sibling closest in kind. `assign: {}` is also an
optional block `init` leaves undeclared, and it is shown at **full expansion in its inline
comment**, including `stratify_by: []` and `seed: auto` (reference.md:94-102) —
`envelope.py:61-62` even cites *"§ The one config file's full expansion of an `assign`
axis block"* as the authority for that block's closed key set. The identical citation
cannot be made for `holdout`.

**Verified** by reading both fences and cross-checking against `envelope.py`'s
`LEAF_TYPES` entries and `validate._check_holdout`'s emit sites.

**Blocks merge:** no. Two comment lines in the fence.

---

## Minor

### M1. `allocation_hash`'s docstring speaks of H3d's holdout half in the future tense, after this branch built it

`artifacts.py:337-341`: *"A **future** reader adding H3d's `holdout` half should draw the
same conclusion: `holdout_hash` (if one is ever needed) belongs beside whatever builds
the holdout partition's document…"*

H3d's holdout half is added — task 17 gave `build_allocation_document` its fourth key in
this same file, thirty lines above. The advice is still correct; the framing is stale, and
it is the one surviving cross-task forward reference of its kind. **Verified** by grepping
`src/` for slice names: `grep -rn 'H3d\|H3c\|H7a\|H7b\|H4a\|H4b' src/` returns 20 hits,
19 of which are correct past-tense records of landed work (`H4a task 12`, `H4a task 14`,
`validate.py:3061`'s H3c-3 ownership note), and this one.

**Blocks merge:** no.

### M2. `tests/test_validate.py:925` asserts the absence of a code that no longer exists anywhere

`assert "E-DATA-HOLDOUT-UNSUPPORTED" not in by_code` — after task 18, the identifier is
gone from `src/` entirely, so this assertion can never fail. It is paired with two
positive assertions in the same test, so the test as a whole is not vacuous, and as a
deliberate retirement regression guard it is defensible. Noting it only so a later reader
does not mistake it for a live check. **Verified** by
`grep -rn 'HOLDOUT-UNSUPPORTED' src/` → no hits.

**Blocks merge:** no.

---

## What I checked and found sound

Recording these so the next reader does not re-derive them.

- **The `E-DATA-HOLDOUT-*` family as a family.** Twelve codes minted (thirteen counting
  the retired `-UNSUPPORTED`). Every code has at least one emit site — none was minted and
  left unemitted. Enumerated by `grep -rn '"E-DATA-HOLDOUT-' src/` — 22 emit sites across
  `validate.py` and `units.py`. **Reachability I spot-checked rather than proved for all
  twelve**: `EMPTY` (the clustered-draw probe under I1) and `VARIES` (the `validate` probe
  under I2) I demonstrated by execution; the other ten I read against their guards without
  executing each. No two codes overlap in what they refuse: `FRAC`/`FROM` own value shape
  under their own method, `NO-DRAW` owns presence under the *wrong* method, `EMPTY` owns a
  realized zero side, `VALUES` owns the `by_attribute` literal set, `STRATIFY-UNKNOWN` /
  `STRATIFY-VARIES` split name-existence from cluster-constancy, `FOLD` and `CELLS` are
  two different co-declarations. The only family-level gaps are I1 and I2, both
  documentation.
- **The § Errors row/emit-site correspondence for the ten validate-side codes.** Site
  counts per code: `METHOD` ×3, `FRAC` ×2, `FROM` ×2, `NO-DRAW` ×3, `SEED` ×1,
  `STRATIFY-UNKNOWN` ×4, `FOLD` ×1, `VALUES` ×1, `STRATIFY-VARIES` ×1, `EMPTY` ×1. I read
  the **multi-site** ones against their rows for coverage rather than diffing each site's
  message. The one worth recording is `STRATIFY-UNKNOWN`, where row 483 lists five
  predicates against four sites and the mapping is therefore not one-to-one: site 1
  (`validate.py:2891`) covers a declaration normalizing to no names — the row's "an empty
  string, or an empty list", and also `0`/`False`/`{}` under its "is not the name of an
  attribute at all"; site 2 covers a non-string or empty entry *inside* the list; site 3
  covers a name `attributes` does not declare; site 4 covers a name `measurements.by` also
  holds. All five row predicates land on a site and all four sites land in the row. Site 4
  is reachable only when the same name is declared under **both** `attributes` and
  `measurements.by` (otherwise site 3 fires first and `continue`s) — and that exact config
  is what `test_a_holdout_stratum_naming_the_measurement_axis_is_refused` builds, so the
  narrow site is genuinely exercised. The two branches sharing a code are separated by
  **message fragment** in the parametrized test, explicitly because asserting the code
  alone had left the second branch deletable (task 6 review, F1).
- **`_check_holdout`'s "ten findings at this commit" docstring** (validate.py:2692) is
  accurate — ten codes, and the enumeration matches the emit sites one for one. Its
  "three of the ten read `roster`" claim is also accurate (`VALUES`, `STRATIFY-VARIES`,
  `EMPTY`), each carrying its own `roster is not None` guard as stated.
- **`stratum_varies_within_cluster`'s caller count.** The spec flagged it stale at
  "two rows" with three real callers. It now says *"four callers today, under four
  codes"* (units.py:2292) and there are exactly four call sites
  (`validate.py:2081, 2664, 2976, 5758`) under exactly the four codes named. The trap was
  closed correctly.
- **`CLAUDE.md` invariants.**
  - *A repeat is one of three kinds; `holdout` rejected as a kind.* Intact.
    `{kind: holdout}` still earns `E-REPL-KIND` and the message still routes to
    `data.units.holdout` — now a real destination
    (`test_a_holdout_repeat_kind_still_routes_to_the_built_field`). § Validation's row
    *Holdout isn't a repeat kind* (reference.md:275) is unchanged.
  - *`io.units` is three operations plus `.train`.* Intact — `UnitList` exposes
    `__iter__`, `__len__`, `__getitem__` and `train` and nothing else
    (`units.py:127-163`); a non-int index still earns `E-STEP-UNITS-CONTRACT`, and
    `.train` without a fold or holdout still earns `E-STEP-UNITS-UNAVAILABLE` with a
    message now correctly naming both routes.
  - *Units are the inference base; `n` counts units.* The holdout narrows the
    denominator, not the basis: `eval_roster` feeds `execute_plan`, `_condition_counts`,
    `_condition_beside_n` and both `_compute_*(roster=)` sites, while `provenance.units`
    stays whole-roster with a comment that is true of the code beside it. Verified by
    mutation (see I3 for the one unpinned half).
  - *Three hashes, split on purpose.* Untouched — `code_hash`, `parameters_hash`,
    `input_manifest_hash` all unchanged; the holdout's seed rides `design_digest` and is
    excluded from it (task 4), which § What `auto` derives from documents at line 2751,
    and `allocation_hash` needed no change exactly as decision 6 predicted.
  - *Operation commands take paths and nothing else.* Unchanged — no flag, selector or
    env var added; `OPERATION_COMMANDS` is still `{"validate", "run"}`.
- **Task 18's five end-to-end pins.** I re-ran mutation (a) myself:
  `execute_plan(units=eval_roster)` → `units=roster` fails **both** new tests —
  `test_a_declared_holdout_now_validates_and_runs` (on the `split.json` membership check)
  and `test_max_failed_fraction_is_measured_against_the_test_partition` (on
  `assert 5 < 5`). Reverted in place, re-verified: 8 passed. The report's accounting is
  honest, including its statement that **task 13's siting has no mutation** because the
  property (realize once, outside every per-condition loop) is behaviourally invisible —
  I agree; a call inside the loop draws the same partition from the same seed and roster,
  so no assertion can separate them, and reading the call site is the only instrument.
- **Task 16's wiring is properly pinned, with attribution.**
  `test_the_resample_cluster_warning_counts_the_holdout_s_test_partition` runs two configs
  differing **only** in whether a holdout is declared, asserts the control is silent, and
  asserts the message names "test partition" and not "roster" — so the warning's presence
  is attributable to the holdout rather than to the roster. This is the shape
  `CLAUDE.md` asks for under *"a refusal that happens to fire must be attributed before
  it is counted."*
- **Task 17's `allocation.json` fourth key is pinned.** Mutating away
  `block["strata"] = list(holdout.strata)` fails
  `test_a_drawn_holdout_writes_its_own_seed_and_strata_inside_its_block`. Reverted,
  re-verified: 101 passed.
- **The two draw constructions are pinned against each other, honestly.**
  `test_the_clustered_and_unclustered_constructions_are_not_the_same_draw` asserts
  MEMBERSHIP difference only and states in its docstring why a size comparison would be
  pinning a coincidence — backed by `holdout_for`'s docstring recording a sweep that found
  90 seeds where the two disagree on size, including legality disagreements. The
  cluster-integrity test is built with clusters of two *specifically* so that sizes cannot
  distinguish correct from buggy and the integrity assertion has to do the work, and it
  carries a positive companion (`assert train and test`) against the all-to-one-side draw.
  This is the trap the spec named, closed properly.
- **Mechanical documentation pass over the four documents plus the feasibility analysis.**
  Clean: no broken relative links, no unresolvable `#anchor`, no duplicate heading
  anchors, no table row/header column mismatch, no trailing whitespace, no tabs, no
  invisible unicode. (Run with a GitHub-compatible slugger; a naive one produces ~18 false
  positives on headings containing `&` or `/`, which is worth knowing before re-running.)
- **The worked example.** § A fixed holdout split's *"a 20% holdout over 240 units reports
  `resolved: 48`"* agrees with the 240-unit `cohort-pilot` roster and with `cli.py`'s own
  "48 where this says 240" comment. No worked-example value was disturbed.
- **`CLAUDE.md`'s own edits.** The dropped citation is correct: `reference.md` has no
  § What core will not do for you — only `experimental-designs.md:387` does. The rewritten
  order line and the H3c-3 ownership sentence are consistent with `validate.py:3061`,
  which names H3c-3 as the owner of `E-DATA-HOLDOUT-CELLS`'s retirement.
- **`spec-defects.md`'s `technical_n` entry is correctly maintained** — see R2 below.

---

## The three flagged residues

### R1. `uv run ruff format .` rewrites the normative documents — confirmed, and worse than the ledger's count

**Confirmed and quantified.** `uv run ruff format --check .` reports **71 files would be
reformatted** (the ledger's 67 plus this slice's four new records), of which **53 hits are
in Markdown**. Two of the four normative documents are among them:

- `README.md:189` — collapses the aligned trailing comments in the `Step` fence.
  `io.record(...)  # the per-unit table —` / `#   what every interval is over` becomes a
  **dangling comment on its own line**, which then reads as annotating the *next*
  statement. The same happens to the `io.write(...)` continuation.
- `docs/reference.md:1032` and `:1139` — same damage, plus it explodes the `analyze(...)`
  call across five lines and splits `io.write("scores.parquet", result.rows)` from its
  trailing comment.

It also rewrites **every tracked plan and every `.superpowers/sdd/**` record**, which
`CLAUDE.md` states must never be retro-edited: *"a spec records what was decided when it
was written and a scoping what was measured on its date; retro-editing either destroys the
evidence they exist to hold."* A documented Format command that silently rewrites the
evidence files is a sharper problem than the README damage.

**Judgment.** This is **pre-existing, not introduced by H3d** — the affected fences in
`README.md` and `docs/reference.md` are untouched by this branch, and the file list
includes records from five earlier slices. H3d's contribution is that four of its own new
lines sit inside would-reformat hunks, which is why the ledger noticed. **It does not
block merge**: the damage is only realized if someone runs the command, and `ruff format
--check` is what the plan's verification steps actually call (commit `b477297` fixed 19
plan steps that said `ruff format .` where they meant `--check`).

**Cause, diagnosed rather than assumed.** This is **default behaviour of the installed
Ruff**, not a setting anyone turned on: `uv run ruff --version` → **ruff 0.16.2**, and
`grep -rn 'docstring-code-format\|extend-include\|preview\|include' pyproject.toml`
returns nothing, with no `.ruff.toml`/`ruff.toml` in the tree. Recent Ruff formats Python
code blocks embedded in Markdown. Nothing in this repo asked for that; it arrived with a
version bump.

**Recommended fix — configuration, not reformatting, and I ran it before recommending
it.** Do not reformat 71 files inside a merge. Append to `pyproject.toml`:

```toml
[tool.ruff.format]
exclude = ["*.md"]
```

`[tool.ruff.format].exclude` rather than a top-level `extend-exclude`, so `ruff check`
keeps its reach. **Verified**: with that stanza applied, `uv run ruff format --check .`
drops from *"71 files would be reformatted"* to *"39 files would be reformatted"*, and
Markdown hits go to **zero** (`grep -cE '^\s*-->.*\.md'` → 0; every remaining hit is
`.py`). `pyproject.toml` was restored from a copy afterwards and the revert verified by
re-running — the count is back to 71 and `git status --porcelain` shows only this review
file.

**A larger finding the fix exposes, which the ledger's framing hides.** Excluding Markdown
does **not** make the documented command safe. The residual 39 are all Python: **17 files
in `src/publishable`, 2 in `src/publishable/generators`, 20 in `tests`**. So
`uv run ruff format .` — `CLAUDE.md`'s documented Format command — would rewrite roughly
40 % of core's own source on top of the docs. The repo has evidently never been
format-clean, which is why the ledger's "several tasks' new lines sit in would-reformat
hunks, deliberately not reformatted" reads as a local choice when it is actually the
standing state of the tree.

**Judgment on what should happen — deciding it once, as asked.** Two separable things,
and they should not be bundled:

1. **The Markdown exclusion should land** — as its own commit, on this branch or straight
   on `main`, either is fine. It is one stanza, it is verified, and it removes the only
   part of this that damages normative documents and untouchable evidence files.
2. **The 39 Python files should not be reformatted now, and `CLAUDE.md` should stop
   claiming otherwise until they are.** A 39-file whitespace commit landing beside or
   inside a 20-task slice is exactly the "burying small diffs" cost the tasks were right
   to avoid. Until someone runs that reformat deliberately, on an empty branch, with
   nothing else in flight, `CLAUDE.md`'s Format row should read `uv run ruff format
   --check .` — which is what the plan's own verification steps call (commit `b477297`
   fixed 19 steps that said `ruff format .` where they meant `--check`), and which is the
   only form of the command that is currently true.

### R2. Task 15 falsifying a filed `spec-defects.md` remediation — **already handled correctly; no action needed**

The residue as flagged is closed. `spec-defects.md`'s OPEN `technical_n` entry
(lines 5643-5674) carries an appended block:

> **Correction (H3d task 15, `fa85b26`), replacing the "mechanism is cheap" sentence
> above:** task 15 narrowed `_condition_beside_n`'s call into `_cond_beside_n` to pass
> `eval_roster` … Closing this gap now needs a fourth parameter carrying the un-narrowed
> roster as a separate identity reference … not merely reading the existing third
> argument.

That is exactly the form `CLAUDE.md` prescribes for correcting a published claim — append
the correction and say what it replaces — applied to the one file it names as a live list.
**I verified the correction's own claim is true**: `cli.py:1885` reads
`_condition_beside_n(beside_n, eval_roster, cond.index, arm_members_map)`, so both the
`cond_roster` argument and the identity reference now derive from the same narrowed value
and the `cond_roster is roster` check can no longer distinguish the two narrowings. The
entry's **Owner** line is also correctly re-ownered (*"whichever slice next changes
`_cond_beside_n`, or H3c-3 … re-owner this entry when that slice finishes rather than
leaving it pointing at a closed one"*), which is the other habit `CLAUDE.md` records.

**The general lesson is worth one line in `CLAUDE.md` and no more.** A filed gap is not
inert: it makes claims about the code, and those claims go stale exactly like a
docstring's. The existing bullet *"A ledger line saying 'filed' is not a filing"* is the
right home — extend it with "and a filing's claims about the code go stale like any other
comment; when you change code a `spec-defects.md` entry describes, re-read the entry."
The mechanical hook already exists: `CLAUDE.md`'s sweep rule already says to grep
`spec-defects.md` after removing or renaming a string.

**Blocks merge:** no.

### R3. Task 20's withdrawn `W-REPL-DETERMINISTIC` — **the withdrawal is adequate, and I can make the determination it declined to make; do not re-run before merge**

The published text (feasibility-llm-growth-studies.md:997) withdraws the warning and
states the contradiction rather than guessing which sentence was false:

> `validate.py`'s only emit site for that code requires a `batch` level in
> `replication.repeats`, `materialize.py` writes a default `{kind: seed, ...}` repeat, and
> the scope statement two paragraphs up says `replication` was not carried over for any of
> the nine — so the code cannot fire under the scope this measurement declares, whatever
> the scratch run actually did.

**I verified both halves of that reasoning independently.** `validate.py:3382-3384` gates
the warning on `"batch" in kinds`; `materialize.py:145` writes
`- {kind: seed, n: INIT_REPEATS}`.

**The determination task 20 declined to make, made here from the evidence.** The false
sentence was **the reported `W-REPL-DETERMINISTIC` on E5**, not the scope statement. The
two candidates are not symmetrically supported: the scope statement is corroborated by two
independent facts in the source — `materialize.py` writes a `seed` repeat by default, and
the warning's sole emit site requires a `batch` level — while the reported warning is
corroborated by nothing at all beyond its own appearance in a draft. A claim backed by two
independent code facts outranks a claim backed by none. That is a determination from
evidence, not a coin-flip between two sentences, and it is what makes a re-run unnecessary
rather than merely inconvenient.

**And the residual uncertainty is provably inconsequential, which is the second reason no
re-run is needed.** Even granting the alternative — that the scratch run silently carried
a `replication` block the scope statement disclaims — no claim the section makes would
move. The section states its own answer-scope explicitly: *"does the
`data.units.holdout`/`weight_by`/`from` block and the `statistics.resample`/`contrasts`
block … earn `E-DATA-HOLDOUT-UNSUPPORTED`, `E-DATA-RESOLVER-UNSUPPORTED`, or
`E-DATA-WEIGHT-CONTRAST` on this build."* **None of those three codes reads
`replication`**, and neither does the `W-DATA-CLUSTER-UNDECLARED` the same paragraph
attributes to the fixture. The one holdout code that *would* be sensitive to `replication`
— `E-DATA-HOLDOUT-FOLD` — is correctly absent, which is exactly what a default
seed-repeat predicts.

**Judgment: adequate as it stands; do not re-run before merge.** The withdrawal was the
right call at the time — task 20 was correct not to guess under time pressure — and the
published text is honest about what it did and did not establish. The remedy is not a
re-run and not another hedge: replace *"Which of the two claims was originally at fault was
not re-run to check; only that they cannot both stand is established"* with the
determination above — the reported warning was the false one, on the asymmetry of evidence
— plus the clause that the ambiguity could not have reached the three codes the
measurement answers for. That closes the thread instead of leaving a later reader to
reopen it. It is a documentation edit to a **dated** section, so per `CLAUDE.md` it should
be appended as a correction saying what it replaces, not written over the original.

I also confirmed the section's commit pin is still honest: `git diff --stat
d72724b..HEAD -- src/ tests/` is **empty**, so no code changed after the commit the
measurement names, and the four documents' claims about the build are still true of
`HEAD`.

**Blocks merge:** no.

---

## Would anything make merging this a mistake?

No. Ranked by what I would want closed first:

1. **I3** — one assertion, guards a named `CLAUDE.md` invariant that a full-suite mutation
   proves is currently unguarded.
2. **I1** — two § Errors rows; a run-time refusal reachable from a clean `validate` is
   undocumented, and this is a repeat of a trap already recorded.
3. **I2** — one § Errors row plus one validate-surface test, restoring parity with the
   three sibling codes the row itself claims parity with.
4. **I4** — two comment lines in § The one config file.
5. **R1** — a `pyproject.toml` stanza; can equally land separately on `main`.

Everything else — the draw constructions, the denominators, the seed derivation and its
digest exclusion, the cells refusal and its named owner, `allocation.json`'s fourth key,
the retirement and its pins, the mechanical documentation pass, and the dated measurement
— I checked and found sound.
