# Task 20 — the consistency passes and the slice's exit criterion

**Status: DONE_WITH_CONCERNS. Commits `3059ed1`, `c6ef6e1`.** The exit criterion (step 6) **holds**: no config reaches a state
where two conditions on a group axis are handed the same roster. Two concerns are carried forward,
neither of them that one — a code finding routed to me by task 19 that I deliberately did not fix,
and a user-reachable traceback I did fix.

Every step below states the command, its output, and a **deliberately-failing control** in the same
shape. Nothing here reports "clean" without first showing the check failing.

---

## Step 1 — the three retirements, both directions

`__pycache__` deleted first, everywhere outside `.git`, because stale bytecode has produced a false
positive on this exact check:

```
find . -name __pycache__ -type d -not -path './.git/*' -exec rm -rf {} +
```

**Live code.** The literal-string grep — an emission, not a mention:

```
$ grep -rn --include='*.py' -E '"E-(SWEEP-GROUPS|DATA-ALLOCATION|DATA-ASSIGN)-UNSUPPORTED"' src
(no string-literal occurrences in src)
```

**Control, same command, a code known present:**

```
$ grep -rn --include='*.py' -E '"E-DATA-ALLOCATION-METHOD"' src
src/publishable/validate.py:1400:            "E-DATA-ALLOCATION-METHOD",
```

The remaining `src/` hits for all three retired codes are comments and docstrings explaining what
was retired (`cli.py:290`, `cli.py:1147`, `validate.py:1396`) — history, not emission.

**Tracked markdown.** The file list is filtered, never the output — the addendum's trap. First run:

```
$ git ls-files '*.md' | xargs grep -n E-SWEEP-GROUPS-UNSUPPORTED
docs/reference.md:1841: … **Reachable now**: a declared group axis no longer draws
`E-SWEEP-GROUPS-UNSUPPORTED` at `validate` … recorded in `docs/superpowers/spec-defects.md` …
```

**This is exactly the trap the addendum names.** The one true hit is a line that also contains the
string `docs/superpowers/spec-defects.md`, so a sweep piped through `grep -v superpowers` would
have reported zero. **Finding, fixed:** the sentence now says "is no longer refused wholesale at
`validate`" and names no dead code — a reader can no longer meet an identifier with no registry row.

After the fix:

```
E-SWEEP-GROUPS-UNSUPPORTED       (no hits)
E-DATA-ALLOCATION-UNSUPPORTED    (no hits)
E-DATA-ASSIGN-UNSUPPORTED        (no hits)

=== CONTROL: same sweep, a code known present ===
docs/experimental-designs.md:1
docs/reference.md:6
```

## Step 2 — the `NOT BUILT` count reads four, and exactly the three left

Markers in the fenced config example: **4**, at `data.units.from`'s `{resolver: <name>}`,
`data.units.holdout`, `statistics.resample`, `statistics.null_test`. (`grep -c` reports 6 lines for
`docs/reference.md`; the other two are the prose at § The one config file and at § Errors `validate`
reports that *talk about* the marker.) No marker in any other tracked markdown file.

The addendum's correction was right and its original claim was wrong: the count **is** stated in
prose, spelled out and enumerated. Task 17's edit landed —

> **Four declarations above are not yet built, and each is marked `NOT BUILT` where it appears**:
> `data.units.holdout`, the `{resolver: <name>}` form of `data.units.from`, and
> `statistics.resample` and `statistics.null_test`.

— word, marker count, and enumeration all agree at four, and `sweep.groups`, `data.units.assign`
and `data.units.allocation` are named in the same paragraph as having *left* the list.

**The loose end I chased rather than left.** That paragraph also claims "A config declaring any of
them is refused today, naming the `-UNSUPPORTED` code its slice will retire." Verified against
source — four blocks, four codes:

```
$ grep -rn 'UNSUPPORTED' src/publishable/*.py | grep '"'
validate.py:2127: "E-DATA-RESOLVER-UNSUPPORTED",
validate.py:2172: ("holdout", "E-DATA-HOLDOUT-UNSUPPORTED"),
validate.py:2204: "E-STATS-RESAMPLE-UNSUPPORTED",
validate.py:2209: "E-STATS-NULLTEST-UNSUPPORTED",
```

The sentence is true. No edit needed.

## Step 3 — registry integrity, both directions

**Left-hand side reproduces the addendum's baseline exactly.** `src/publishable/*.py` yields
**134** distinct emitted codes. Widening to the subdirectories yields **137** — three more, and the
addendum's own command structurally could not see them:

```
$ comm -13 flat.txt with-subdirs.txt
E-EXPERIMENT-EXISTS
E-EXPERIMENT-UNKNOWN
E-STEP-EXISTS
```

The non-literal check the addendum asked for: one site, `units.py:807`'s `code=code`, whose values
come from `CONSTANT_COLUMN_RULES` — string literals the grep already sees. 137 is complete.

**Right-hand side is two tables, and my first membership test was too loose — I caught it and say
so.** Matching any `E-` code anywhere in a row falsely counted `E-DATA-HOLDOUT-UNSUPPORTED` as
registered, because it is *named inside another row's prose* (`E-CONFIG-KEY-UNKNOWN`'s). Restricted
to the code column:

```
validate registry: 88   raises registry: 43   union: 122
REGISTRY not in source: (none)
SOURCE not in registry: 15
```

Every registry row's code is emitted somewhere — **the reverse direction is clean**. The 15 are:

- **4 `-UNSUPPORTED`** (`DATA-HOLDOUT`, `DATA-RESOLVER`, `STATS-RESAMPLE`, `STATS-NULLTEST`) —
  deliberately absent, and § Errors `validate` reports says so in its own words.
- **11 command-level codes** (`E-CODE-DIRTY`, `E-EXPERIMENT-EXISTS`, `E-EXPERIMENT-UNKNOWN`,
  `E-GIT-NO-COMMIT`, `E-GIT-NO-REPO`, `E-INPUT-CHANGED`, `E-IO-FAILED`, `E-PROJECT-EXISTS`,
  `E-RUN-ID-EXHAUSTED`, `E-RUN-LOCKED`, `E-STEP-EXISTS`). All eleven are pre-existing and **all
  eleven are already recorded** in `docs/superpowers/spec-defects.md` (grep count per code: 5, 7,
  2, 4, 4, 5, 2, 7, 4, 4, 6). Not this slice's, and already on the record where CLAUDE.md says such
  a gap belongs. None of the codes minted this slice is among them.

**The known sort violation is fixed.** `E-SWEEP-ABLATE-BASELINE-GROUP` sat after
`E-SWEEP-ABLATE-CROSSED`; it now sits before `E-SWEEP-ABLATE-BASELINE-MISSING`, and the whole
88-row column is verified sorted:

```
rows: 88 violations: 0
```

The slice's own insertions introduced no others.

## Step 4 — H3c-1's rows by title, and the row count I measured

**The "95 rows" in the plan and the scoping documents is stale, and so is the addendum's 109.**
Measured, skipping fenced blocks:

- § Validation's checks table: **101 check rows** (103 lines including header and separator).
- The step-time table below it: **8 rows**.
- Total non-separator lines in the section: 111 — two more than the 109 measured at task 12.

I cite by title everywhere below and state no positional count in any document.

**The positional-phrase audit, re-run over every tracked `*.md`** (`rows above`, `row above`, `rows
below`, `row below`, `further up`, `immediately above`, `immediately below`, `the two above`,
`preceding row`, `next row`, plus `last row` and `first row`). Nine hits after excluding the
feasibility file's table cell:

| Where | Phrase | Verdict now |
|---|---|---|
| § Validation, *Assignment names a method* | "the 'Allocation needs arms' and 'Every axis is assigned' **rows above**" | correct — both titles exist and both sit above it |
| § Validation, *Assignment method isn't drawn* | "the enum 'Assignment names a method' **above**" | correct |
| § Validation intro | "**Six** things deliberately absent from that table" | correct — the paragraph enumerates six, and its own "the first five"/"the sixth" split still holds |
| § Validation intro | "the batch row **above**" | correct — *Batch has something to measure* |
| § Warnings core reports | "`W-ENV-UNLOCKED` is the one **row above**" | correct |
| § Errors core raises | "That **last row** … those **six**" | correct — still the last row, and it still carries exactly six codes (`E-RUN-SEED-MISSING`, `E-RUN-CFG-MISSING`, `E-RUN-ORDER-MISMATCH`, `E-REPL-ORDER-UNRESOLVED`, `E-RUN-FOLD-UNRESOLVED`, `E-RUN-ARM-UNRESOLVED`) |
| § Allocation | "The **last row** is the one to design around" | correct |
| § Expansion modes (crossed axes) | "The **first row**'s two `by_attribute` axes" | correct |
| § Validation, *Allocation deltas aren't computed* | "Unlike **the two rows below**" | **WRONG — finding, fixed** |

**The one that had gone stale is one this slice wrote.** *Allocation deltas aren't computed* was
inserted at commit `6c7dcea` saying "Unlike the two rows below, read per comparison rather than for
the whole design". The two rows below it are *Cluster attribute exists* and *Cluster is constant
within a unit*, which have nothing to do with the contrast. The intended pair is *Clustered deltas
aren't computed* and *Weighted deltas aren't computed*, eight and twenty rows down and not adjacent
to each other. Fixed by naming both by title.

## Step 5 — the worked example, both directions

### 5a. Did a number move? (a real temporary commit, not a working-tree edit)

`scratchpad/worked_example_check.py` checks two halves: every pinned token still present across the
four documents, and no line **removed** by `merge-base..HEAD` carrying one.

```
$ uv run python worked_example_check.py cb96c7d
PASS: 0 finding(s) over cb96c7d..HEAD
```

**The failing control, as a real commit** — `git stash`, edit `0.581` → `0.582`, `git commit`:

```
B. REMOVED line carries ['0.581']: -          r: {value: 0.581, basis: units, method: percentile_over_units,
FAIL: 1 finding(s) over cb96c7d..HEAD
exit=1
```

then `git reset --hard HEAD~1` and `git stash pop`.

**And the silent-pass the brief warned about, demonstrated.** The *same* edit left in the working
tree and not committed:

```
=== working-tree-only edit (NOT committed): the two-dot diff sees nothing ===
PASS: 0 finding(s) over cb96c7d..HEAD
```

That is the shape in which this check has passed while running nothing.

One calibration note: my first token list included a bare `12` and it reported a **false** positive
on an unrelated `12 units` example in the checks table. Dropped, because 240/228 pin the triple
without it.

### 5b. The direction this branch actually risks — a number that should have moved and did not

Diffed § The one config file's fenced example against what `materialize.py` writes, field by field
and comment by comment.

**Config completeness: clean.** Every key `init` materializes appears in the fenced example; every
doc-only key is one of the optional blocks line 185's prose already accounts for
(`data.units.assign`, the four `statistics` sub-blocks, the six `sweep` modes):

```
INIT keys missing from doc example: (none)
DOC-only keys: data.units.assign, statistics.{contrasts,null_test,report_by,resample},
               sweep.{ablate,baseline,grid,groups,paired,sample}
```

Task 17's two edits both landed correctly: no `NOT BUILT` marker on `allocation`, `assign` or
`sweep.groups`, and `allocation`'s enum comment reads `# within | between` on both sides.

**Comment by comment found two stale claims in `materialize.py` — both fixed.** These are the
"should have moved and did not" defect, and no task in this slice was told to look:

1. `init` wrote `this build expands `baseline` and `grid` only`. **False.** `sweep.SWEEP_MODES` is
   `grid, paired, sample, groups, baseline, ablate` — all six built, `groups` by this very slice,
   and the fenced example shows all six with no `NOT BUILT` marker. Now reads
   `the modes are baseline | grid | paired | sample | ablate | groups`.
2. `init` wrote `# seed  (fold: later slice)`. **False.** `replication.SUPPORTED_KINDS` is
   `("seed", "batch", "fold")` — and the comment also omitted `batch` entirely. Now reads
   `# seed | batch | fold`, matching the fenced example exactly.

`tests/test_materialize.py::test_no_enum_comment_names_a_value_validate_or_run_would_refuse`
caught the second edit immediately (`expected a '(...: later slice)' marking for each of ['kind']`)
— that check can fail, and it did. `kind` left `_MARKED_FIELD_PATHS` for exactly the reason
`allocation` left it at task 17: the marking names a value core no longer refuses. The registry is
left empty rather than deleted, so the loop still refuses an unregistered marking.

No document pins either stale phrase (`grep` over all tracked `*.md` finds them only in
`materialize.py`), so the code was moved to follow the documents rather than the reverse.

## Step 6 — § Mistakes core prevents: the exit criterion

**The row exists and task 18 wrote it.** `experimental-designs.md` § Mistakes core prevents,
*Two identical measurements reported as two arms*, resting on `E-DATA-ALLOCATION-WITHIN-ARMS`,
`E-DATA-ALLOCATION-NO-ARMS` and `E-DATA-ALLOCATION-CONTRAST`.

**I did not take task 18's reviewer on trust.** I built a real project per case and drove each
through `expand`, `validate_config`, and `main(["run", ...])` to a real `run.yaml`, against an 8
control / 3 treatment roster so narrowing is visible in the counts. **19 adversaries**, the six the
addendum named plus thirteen more:

| # | Config | Result |
|---|---|---|
| A | `by: ""`, no matching `assign` | **refused** `E-DATA-ASSIGN-MISSING` |
| B | `levels: []` | **refused** `E-SWEEP-EXPANDS-EMPTY` |
| C | `levels: [control]` (one element) | **refused** `E-DATA-ASSIGN-LEVELS` (3 of 11 units in no arm) |
| D | `levels: [control, control]` (duplicate) | **refused** `E-DATA-ASSIGN-LEVELS` |
| E | `by: 1` (non-string) | **refused** `E-CONFIG-SHAPE` |
| F | `groups: ["arm"]` (entry not a mapping) | **refused** `E-CONFIG-SHAPE` |
| G | `levels: [1, 2]` — task 12's adversary | **refused** `E-CONFIG-SHAPE` ×2. The fix held |
| H | two entries sharing `by: arm` — task 17's catch | **refused** `E-SWEEP-PATH-DUPLICATE`. The fix held |
| I | entry with no `by` | **refused** `E-DATA-ALLOCATION-NO-ARMS` + `E-SWEEP-EXPANDS-EMPTY` |
| J | `groups` as a mapping | **refused** `E-CONFIG-SHAPE` + `E-CONFIG-TYPE` |
| K | `by: null` | **refused** (as I) |
| L | `levels: null` | **refused** `E-SWEEP-EXPANDS-EMPTY` |
| M | `levels: "control"` (not a list) | **refused** `E-CONFIG-SHAPE` |
| N | control: a well-formed axis | **expands and narrows correctly** — `arm=control` n.resolved 8, `arm=treatment` n.resolved 3 |
| O | levels naming values no unit holds | **refused** `E-DATA-ASSIGN-LEVELS` |
| P | `by: " "`, no matching `assign` | **refused** `E-DATA-ASSIGN-MISSING` |
| Q | `by: ""` **with** a matching `assign` block | **validated clean, then `run` raised an uncaught `KeyError: ''`** |
| R | `by: " "` **with** a matching `assign` block | **validated clean, ran to a green `run.yaml`, narrowed correctly** (8 / 3) |
| S | two group axes over the same column | validates, runs; four cells, two of them empty — **each narrowed, none whole** |

**No case lands in "expands and hands back the whole roster."** The Critical the addendum
pre-labelled does not occur, before or after my change. The bar holds, and the row is not
overclaiming.

**`by: ""` — the decision the addendum asked for: yes, refuse it, and I did.** Task 17 was asked to
cite it in a comment, and on the shape the reviewer looked at (case A) it is caught late by
`E-DATA-ASSIGN-MISSING`. Case Q is the shape nobody had tried: `data.units.assign` is a bare
mapping no schema closes, so a block literally keyed `""` is accepted, both derivations stay
disagreed, `validate` reports **zero findings**, and `run` dies on `units.arm_members`' bare
`KeyError('')` — a traceback out of a command rather than a diagnostic, from a config that
validated clean. Case R is milder and the same root cause: it runs correctly but names condition
directories `00_ =control`.

`validate._check_shape` now refuses a blank `by` (empty or all-whitespace) as `E-CONFIG-SHAPE`,
which needed no new code and no new registry row — § Errors `validate` reports' `E-CONFIG-SHAPE`
row was widened to state the one value that fails it while being of the right type. Re-probed:

```
Q: validate -> [('error','E-CONFIG-SHAPE')]  "is blank ('') ; expected an axis name…"  run exit -> 1
R: validate -> [('error','E-CONFIG-SHAPE')]  "is blank (' ')  ; expected an axis name…"  run exit -> 1
```

`tests/test_validate.py::test_a_blank_group_axis_name_is_a_shape_fault` pins it over `""`, `" "`,
`"\t"`, `"\n"`, with two controls that must *not* report (a well-formed `arm`, and `"study arm"` —
a name merely containing a space, which is not this rule's business).

**A review catch on my own fix, in commit `c6ef6e1`.** My first version set `ok = False`, which is
what makes `validate_config` **return early** — and § Errors `validate` reports frames that early
return as a *container*-shape fault, because every later check indexes into a block already known
to be the wrong kind. A blank `by` is a well-typed string with bad content: nothing downstream
indexes into it, `_check_assign` runs against the same config and reports `E-DATA-ASSIGN-MISSING`
without incident, so returning early bought no protection and cost `validate` its
collect-everything contract — one finding reported over a config that had earned several. It now
reports and keeps going, and both the registry row and the early-return paragraph say so, since a
non-container `E-CONFIG-SHAPE` is a **third** exception to "every other row fires only once all
three have passed" and that paragraph named only two.

**Mutation-proven, twice.** Restoring `ok = False` fails the test (the both-codes-in-one-pass
assertion); replacing the branch with `elif False:` fails it (the refusal assertion). Restored, it
passes.

## Step 7 — mechanical, then cross-document

**Mechanical: 0 findings across all 6 tracked files** — relative links and `#anchor`s resolve, no
duplicate anchors, every table row matches its header's column count, no empty rows, no trailing
whitespace, tabs, or invisible unicode. Fenced blocks skipped throughout.

**Two false positives I chased down rather than filed**, both mine: my slugger collapsed runs of
spaces (GitHub does not — `## Secrets & credentials` is `#secrets--credentials`), and my cell
splitter counted escaped `\|` inside code spans as separators. Both fixed in the checker.

**The control — six deliberate defects, one per class:**

```
docs/reference.md:223 trailing whitespace
docs/reference.md:224 tab
docs/reference.md:225 duplicate anchor #validation (also line 206)
docs/reference.md:221 row has 3 cols, header had 2
docs/reference.md:222 broken anchor #no-such-heading-anywhere
docs/reference.md:226 broken link path docs/nope.md
6 mechanical finding(s)  exit=1
```

then restored, back to 0.

**Cross-document drift classes:**

- **Config completeness** — step 5b. Clean, two code comments fixed.
- **Enum comments** — `assign.<axis>.method`'s `# random | by_attribute | blocked` checked against
  `validate.ASSIGN_METHODS = ("random", "by_attribute", "blocked")` **in the source**, not against
  another comment: same three values, same order. The subtlety the addendum names holds: the enum
  is three, and the refusal of two of them by value is prose — § Validation's *Assignment method
  isn't drawn* names `random` and `blocked`, matching `DRAWN_ASSIGN_METHODS = ("random",
  "blocked")`. `allocation`'s `# within | between` matches `ALLOCATION_MODES`. Repeat kinds and
  sweep modes fixed as above.
- **Declared vs. derived** — no new derived-value/settable-input contradiction.
- **Schema fields in prose** — every field named in prose exists in the fenced example, and the
  reverse (step 5b's key diff).
- **Versions** — `CITATION.cff` `0.1.0`, README's `v0.x` notice, `generic v1.0.0` in the fenced
  header. Consistent.
- **Prevented mistakes** — step 6.
- **The worked example** — step 5a.

### The `expand` index-order divergence routed from task 19 — settled, as a code finding

**I probed the actual order first rather than reasoning from `spec-defects.md`, which is the
artifact under suspicion.** § Expansion modes' own printed config, run through `expand`:

```
00_cohort=derivation__baseline      01_cohort=validation__baseline
02_cohort=derivation__labs=false    03_cohort=derivation__notes=false
04_cohort=validation__labs=false    05_cohort=validation__notes=false
```

The document prints `00_cohort=derivation__baseline`, `01_cohort=derivation__labs=false`, …
`03_cohort=validation__baseline`. The leading-block numbering shows up at **one** group axis too.

The addendum's reading is right and the entry's sentence is subtler than either: it says the
*rule* and the *example* agree at one axis, which is true of the two documents and says nothing
about the code. What it invites — that the single-axis case is outside the divergence — is wrong.
And the entry's argument for changing the document ("the interleaved rule is ill-defined once a
second axis exists") is sound in general and is **not** a defence of the code at one axis, where
the rule is well-defined and merely unimplemented.

**Decision: outcome 1 — the printed example and the Index row are right, the code is wrong, and I
am reporting it rather than fixing it in a documentation pass.** Renumbering conditions changes
condition directory names, `sweep.yaml` indices, and everything downstream; that is not a change to
make on the way past, and editing the example to match would bless an ordering nobody decided.
`reference.md` is left alone; `spec-defects.md`'s entry is amended with the measured reproduction,
with the reason its own argument does not reach this case, and with the fact that its named owner
("the groups slice") was never assigned — H3c-1 was not scoped to it and did not do it.

## Step 8 — what changed

`docs/reference.md`
- § Statistical reporting: dropped the name of the retired `E-SWEEP-GROUPS-UNSUPPORTED` (step 1).
- § Validation, *Allocation deltas aren't computed*: the stale positional phrase now names the two
  rows by title (step 4).
- § Errors `validate` reports: `E-SWEEP-ABLATE-BASELINE-GROUP` moved into sort order.
- § Errors `validate` reports: `E-CONFIG-SHAPE`'s row widened for the blank `by` (step 6).

`src/publishable/validate.py` — refuse a blank `sweep.groups[i].by`, without taking
`_check_shape`'s early return with it (`c6ef6e1`).
`src/publishable/materialize.py` — two stale enum comments (sweep modes; repeat kinds).
`tests/test_validate.py` — `test_a_blank_group_axis_name_is_a_shape_fault`, mutation-proven.
`tests/test_materialize.py` — `kind` out of `_MARKED_FIELD_PATHS`, with the reason.
`docs/superpowers/spec-defects.md` (gitignored working record) — the ordering amendment.

```
uv run pytest    1497 passed, 2 xfailed
uv run ruff check .    All checks passed!
uv run mypy      Success: no issues found in 40 source files
```

`ruff format` was not run.

---

## Concerns

1. **`expand`'s condition index order for `ablate × groups` contradicts `reference.md`
   § Expansion modes and § How artifacts are organized' Index row, at one group axis, where the
   recorded excuse does not reach.** Major, not Critical: nothing is mismeasured, but a reader
   designing against the printed example looks for `03_cohort=validation__baseline` and gets `01_`.
   Open, unowned, reproduction recorded.
2. **`data.units.assign` is a bare `dict` with no per-axis-key closure**, which is what let case Q
   accept a block keyed `""`. Already an open gap in `spec-defects.md`; my fix closes the route from
   the `sweep.groups` side, not the `assign` side. A misspelled field inside an axis block is still
   ignored silently.
3. **A group axis name containing a space (`by: "study arm"`) still validates** and produces a
   condition directory with a space in it. § Validation's *Swept values are nameable* constrains
   swept *values*, not axis names. Deliberately out of scope for my one-line blank check; worth a
   rule if anyone cares.
4. **11 command-level `E-` codes are emitted by source and appear in neither registry table.**
   Pre-existing, all 11 already recorded in `spec-defects.md`, none minted by this slice.
5. Two counts in scoping documents are stale and I did not chase them into those files: the
   § Validation checks table is **101 checks**, not 95 and not 108.

---

# Addendum — the coordinator's review round (commit `87b3ff7`)

**The Critical is real, I missed it, and the reason I missed it is worth more than the fix.**
Status stays DONE_WITH_CONCERNS; the Critical is **closed**.

## The Critical, reproduced before the fix

```yaml
sweep: {groups: [{by: arm, levels: [control, treatment, control]}]}
```

over the 8-control/3-treatment roster, driven end to end through `main(["run", …])`:

```
expand -> [(0,'arm=control'), (1,'arm=treatment'), (2,'arm=control')]
validate -> []                       # ✓ config valid, no warning
run exit -> 0
condition 0 label='arm=control'   n={'resolved': 8, 'completed': 8, …}
condition 1 label='arm=treatment' n={'resolved': 3, 'completed': 3, …}
condition 2 label='arm=control'   n={'resolved': 8, 'completed': 8, …}
*** BYTE-IDENTICAL CONDITION DIRECTORIES: ['00_arm=control', '02_arm=control'] ***
distinct condition trees: 2 of 3
```

The digest is over every file in each condition tree, so it covers all five seed repeats'
`units.parquet` and `ineligible.jsonl`. § Mistakes core prevents, *two identical measurements
reported as two arms*, verbatim.

**Why none of that row's three codes reaches it.** All three read the `within`-versus-arms
question, and this config answers it correctly: `allocation: between`, a real axis, an `assign`
block. `E-SWEEP-PATH-DUPLICATE` compares axis *names* across entries and never values inside one
entry's `levels`. And `arms_of`'s set equality is satisfied because `{control} == {control}` — the
two arms are **equal**, not overlapping, so nothing downstream has anything to disagree about.

**Fixed.** `E-SWEEP-LEVEL-DUPLICATE`, minted, with a § Validation check row (*Levels are distinct*,
next to *Axis names are distinct*) and a registry row in sort order. Post-fix, on every roster:

```
CRIT_dup_level @ all_one   validate -> [E-DATA-ASSIGN-LEVELS, E-SWEEP-LEVEL-DUPLICATE]  refused
CRIT_dup_level @ mixed     validate -> [E-SWEEP-LEVEL-DUPLICATE]                        refused
CRIT_dup_level @ subset    validate -> [E-DATA-ASSIGN-LEVELS, E-SWEEP-LEVEL-DUPLICATE]  refused
```

No byte-identical directories anywhere. Two tests: the finding
(`test_a_group_axis_repeating_a_level_is_refused`) and the property that actually matters, that no
run directory is created at all (`test_a_group_axis_repeating_a_level_never_reaches_a_run`).

## The methodology correction — which of my 19 verdicts were roster-incidental

**This is the finding I should have made myself.** I enumerated over config *shape* while the exit
criterion is a property of *roster content*, and ran all 19 against one roster. Re-run over three —
`mixed` (8 control / 3 treatment), `all_one` (11 control), `subset` (declared levels a strict
superset of the values present) — with the pre-fix code:

| Case | mixed (my original) | all_one | subset | Verdict |
|---|---|---|---|---|
| `levels: [control, treatment, control]` | not in my set | refused `E-DATA-ASSIGN-LEVELS` | refused `E-DATA-ASSIGN-LEVELS` | **green + byte-identical on `mixed`. The Critical** |
| **D** `levels: [control, control]` | refused `E-DATA-ASSIGN-LEVELS` | **green, byte-identical `00_arm=control`/`01_arm=control`** | **green, byte-identical** | **roster-incidental — D was the same Critical, and I reported it "refused"** |
| **C** `levels: [control]` | refused `E-DATA-ASSIGN-LEVELS` | green, 1 condition, 11 units | green | roster-incidental. Not a defect, but the verdict moves |
| **N** well-formed control | green, narrows 8/3 | refused (`treatment` names no unit) | refused | roster-incidental — even the *control* changes verdict |
| **O** levels naming nothing | refused | refused | refused | **structural** |

**Structural vs. roster-incidental, stated plainly.** Cases A, B, E, F, G, H, I, J, K, L, M, P and
Q/R are **structural**: every one is a shape or name check in `_check_shape`/`selector_paths` that
never reads the roster, so no roster can change the verdict. Case O is structural for a different
reason — no unit names *any* declared level, which no roster in the family repairs. Cases **C, D
and N are roster-incidental**, and D's incidental refusal is what concealed the Critical: my table
recorded the right outcome for the wrong reason and I called the sweep complete.

The transferable rule, in the form it was learned: **enumerating over config shape does not test a
property of roster content.** A refusal that happens to fire needs to be attributed before it is
counted — my case D refused on `E-DATA-ASSIGN-LEVELS`, a code about the data, and I read it as the
design being refused.

## Important 2 — `by: "arm."`, and why my first refusal was the wrong predicate

`label_for` renders `path.rsplit('.', 1)[-1]`. `by: "arm."` renders to nothing and passes
`by.strip()`. End to end with a matching `assign` block, pre-fix:

```
expand -> [(0,'=control'), (1,'=treatment')]     validate -> []     run exit -> 0
```

directories `00_=control`, `01_=treatment` — precisely what my own registry row cited as the reason
to refuse an all-whitespace name. The check now tests the name **as `label_for` renders it**, and
`test_a_group_axis_name_that_renders_blank_is_a_shape_fault` pins `arm.`, `a.b.`, `arm. ` and `.`
with `cohort.arm` as the control. Post-fix: `validate -> [E-CONFIG-SHAPE]`, `run exit -> 1`.

## Important 3 — the index-order divergence now has a durable record

`docs/superpowers/spec-defects.md` is gitignored (`.gitignore:224`, and `git ls-files
docs/superpowers/` is empty), so my record would not have survived the merge — the exact failure
task 18 existed to prevent. The disposition is unchanged (**do not renumber**), but the note is now
in `reference.md` at **both** printed sites: a paragraph under § Expansion modes' `ablate × groups`
example giving the six indices the tool actually produces, and a clause on § How artifacts are
organized' Index row pointing at it. Both say the divergence is unresolved, that only the indices
differ, and that a baseline should be addressed by label rather than by index.

## Minor 4 and 5

- The widened `E-CONFIG-SHAPE` row said the fault "does not trigger the early return **below**";
  that paragraph is above it. **My own step 4's defect class, introduced by the commit that ran the
  positional audit** — which is the sharpest possible demonstration that the class is not about
  carelessness. Now phrased as "the early return this section's intro describes", with no direction
  at all.
- `init`'s sweep-modes comment now reads `grid | paired | sample | groups | baseline | ablate`,
  matching `sweep.SWEEP_MODES`' order, as the `allocation` and `assign.method` comments match
  theirs.

## Recorded, not fixed

A **parameter** axis repeating a value (`grid: {analysis.method: [pearson, pearson]}`) expands to
two identical conditions and is deliberately not refused. Recorded durably in `reference.md`, on
`E-SWEEP-LEVEL-DUPLICATE`'s registry row, with the reason: on a parameter axis it is a wasted
execution; on a group axis a level is a claim about *which units*, which is why only the group axis
is checked.

## Mutations, all four

| Mutation | Result |
|---|---|
| duplicate-level check disabled (`if False:`) | both new tests fail |
| per-entry tally hoisted out of the entry loop | the two-axes-sharing-a-level control fails |
| `by` check reverted to `by.strip()` | the renders-blank test fails |
| blank-`by` check disabled | the blank test fails (from the round before) |

## Counts that moved

The § Validation checks table is now **102 checks** (was 101 when I measured it, 95 in the plan,
109 in the addendum). § Errors `validate` reports is **89 rows**, still fully sorted. Registry
both-directions re-run: no registry row lacks a source emitter; the 15 source codes outside both
tables are the same 4 `-UNSUPPORTED` + 11 command-level as before.

```
uv run pytest    1500 passed, 2 xfailed
uv run ruff check .    All checks passed!
uv run mypy      Success: no issues found in 40 source files
mechanical pass  0 findings
worked example   PASS over cb96c7d..HEAD
```

---

# Addendum 2 — second review round (commit `438ef92`)

Both findings addressed. Nothing about *what is refused* changed except the third spelling of the
blank-name fault.

## Major — a false consequence recorded for a deliberate gap

`E-SWEEP-LEVEL-DUPLICATE`'s registry row justified leaving the parameter-axis duplicate open by
saying it "costs a wasted execution, while a group level is a claim about which units". **The first
half is false in the crossed case**, and I wrote it while looking only at the uncrossed one.
Reproduced:

```
groups: [{by: arm, levels: [control, treatment]}] × grid: {analysis.method: [pearson, pearson]}
-> 00_arm=control__method=pearson    01_arm=control__method=pearson     (same digest)
   02_arm=treatment__method=pearson  03_arm=treatment__method=pearson   (same digest)
   exit 0
```

Byte-for-byte the outcome the group-axis check refuses. Worse than "wasted compute" in a way the
uncrossed case hides: the duplicated label bodies **carry the arm**, so they are selectors, and a
selector over a duplicated body resolves silently to the later of the pair — a contrast naming one
reports against a condition the reader did not pick, with no ambiguity diagnostic.

**The gap stays open, as authorised; the reason is now the honest one.** The line is about what a
duplicate *means* — a group level is a claim about which units, a parameter value is not — not
about what it costs. Corrected in all three places that carried the claim: the registry row, the
source comment, and the test docstring. The crossed case is now **pinned as unrefused** in
`test_a_group_axis_repeating_a_level_is_refused`, so the recorded gap is visible in the suite and a
later slice closing it has one assertion to change, with the registry row named in the comment.

This is the same defect class as my own step 4 finding, one level up: a justification that was true
of the case in front of me and false of the general claim I wrote.

## Minor — the blank-name check was a denylist, and had already lost twice

Three spellings of one fault, in order: `""` and `" "` caught by `.strip()`; `"arm."` **not** caught
(renders to nothing after the last `.`); and a zero-width space not caught either, because
`'​'.isspace()` is `False` — `by: "​"` and `by: "arm.​"` validated clean and named directories
`00_​=control`.

**Inverted to an allowlist**, as directed. `sweep.NAMEABLE_CHAR` is now the single source the
project's existing rule is built from:

```python
NAMEABLE_CHAR = r"[A-Za-z0-9._+-]"
SWEPT_VALUE_PATTERN = rf"^{NAMEABLE_CHAR}+$"
```

One alphabet, two strictnesses — a swept *value* must be made **entirely** of it
(`check_swept_value`), a group axis's rendered *name* must contain **at least one**
(`_check_shape`). That is the rule § How artifacts are organized already states, reused rather than
a second one invented, and the reason is in the comment: there is an unbounded supply of invisible
codepoints and one alphabet of legal ones, so a denylist loses by construction.

Deliberately *at least one* rather than the full match: `study arm` and `arm\xa0` render, resolve
and narrow correctly, and refusing them is a separate rule about label hygiene nobody has argued
for. Verified over the class:

```
''  ' '  '\t'  '\n'  '​'  'arm.'  'arm.​'  '.'  '​.​'  '﻿'  '⁠'  -> refused
'arm'  'cohort.arm'  'study arm'  'arm\xa0'  'a'  '0'  '_x'                                    -> accepted
```

`test_the_blank_axis_name_rule_is_an_allowlist_not_a_denylist` asserts the class over four
invisibles, each also in its post-`.` form, and **first asserts that `.strip()` would not have
caught each one** — so the test discriminates the allowlist from the denylist it replaced rather
than merely re-passing.

**Mutations, both directions:**

| Mutation | Result |
|---|---|
| revert to `.strip()` (denylist) | the allowlist test fails |
| check `by` whole instead of the rendered name | two tests fail |
| widen to `SWEPT_VALUE_PATTERN`'s full match (over-refusal) | the must-not-refuse controls fail |

## Confirmed non-finding, for the record

**Case S** — two group axes over the same column, producing empty crossed cells — runs green with
zero units, identical empty trees, `aggregated: {}` and no warning. **No measurement is reported**,
so it is not *two identical measurements reported as two arms*, and § Validation's *Cells are
populated* already records `min_units_per_cell` as specified-not-built. It confirms the document
rather than contradicting it. I am recording it as a non-finding rather than dropping it, because
an empty-tree outcome that looks like the Critical is exactly the shape a later reviewer will
re-find.

## The sentence to keep

**The wrong positional phrase was introduced by the commit that ran the positional audit.** That is
the strongest evidence in this slice that the defect class is structural rather than a matter of
care — the pass that exists to catch it was running, by an author holding it in mind, and it landed
anyway.

```
uv run pytest    1501 passed, 2 xfailed
uv run ruff check .    All checks passed!
uv run mypy      Success: no issues found in 40 source files
mechanical pass  0 findings
worked example   PASS over cb96c7d..HEAD
registry         89 rows, sorted; no registry row without a source emitter
```
