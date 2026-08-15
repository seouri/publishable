# Task 7 report — `E-SWEEP-BASELINE-PARTIAL` retired, `W-SWEEP-BASELINE-CONFOUNDED` re-read

**Commit:** `eba1804` — *feat: a partial baseline is a design core accepts*
**Suite:** 1062 passed (was 1061; net +1 new test), `ruff check` clean, `mypy` clean on 40 files.
No `ruff format` run.

---

## 1. Everything the removal touched

### `src/publishable/validate.py`

| What | Change |
|---|---|
| `_check_unimplemented`, the refusal block | Deleted — 27 lines of comment plus the `unfixed` computation and the `c.error(...)` call |
| `_check_unimplemented` docstring | Its opening enumeration ("This build expands `sweep.baseline`, `sweep.grid`, …") was still accurate, but said nothing about the partial case. Now states that a baseline fixing only some swept axes is no longer refused here and names `sweep._baseline_cells` as what expands it, so the next reader of this function does not re-mint the refusal |
| The `_swept_paths` import | Removed. The refusal was validate's **only** use of it; `ruff` would have caught it, but the point is that the helper survives for its two real callers (`sweep.expand`'s labelling, `cli.command_run`'s run-scope unreadability), exactly as the brief required |
| `_check_ablate`'s "`remove` only, never `override`" comment (`validate.py:1454`) | Cited the retired identifier as the precedent for not refusing an `override` on an unfixed path. Rewritten to cite the thing that still exists — `sweep.ablated_paths` keeping ablated paths out of the axis-shaped modes' set |
| `W-SWEEP-BASELINE-CONFOUNDED`'s emit-site comment | See § 3 |
| `W-SWEEP-BASELINE-CONFOUNDED`'s **message** | See § 3 |

### `src/publishable/sweep.py` — three comments that cited the refusal

All three were stale in the present tense, and none was a one-word fix; each named the refusal as
the *reason* for a design decision that still stands for a different reason.

1. **`_swept_paths`, the defensive `sample` read (`sweep.py:444`).** Said the defensive read exists
   so "the swept-path list — which `E-SWEEP-BASELINE-PARTIAL` reads — [is not stopped] from being
   built". The named reader is gone; the defensive read is not, because `expand` still calls
   `_swept_paths` on an uncleared config (validate expands inside a `try`, since it collects
   findings rather than raising) and `label_for` shortens each path against that list. Restated to
   name `expand`/`label_for` as the reader.
2. **`ablated_paths`'s docstring (`sweep.py:518`).** Justified keeping ablated paths out of
   `_swept_paths` by what the refusal would have done with them. Restated on the surviving reason:
   an axis is a thing a baseline can leave free and `_baseline_cells` can expand over, and `ablate`
   is neither.
3. **`_baseline_cells`'s docstring (`sweep.py:631`).** Ended "whether such a config is legal at all
   is `validate`'s to say (it is refused today by `E-SWEEP-BASELINE-PARTIAL`)" — about the
   half-fixed `paired` axis. `validate` now says **nothing** about that config, so the parenthetical
   was replaced with a pointer to the spec-defects entry that records it (§ 4, shape 3).

### `docs/reference.md`

- **§ Errors `validate` reports:** the `E-SWEEP-BASELINE-PARTIAL` row is gone. **Row count: 65 → 64
  data rows**, not the brief's 60 → 59 — the brief's figure predates this slice's own additions
  (`E-SWEEP-ABLATE-BASELINE-MISSING`, `E-SWEEP-ABLATE-CROSSED`, `E-SWEEP-PATH-DUPLICATE`, and
  others). Counted mechanically from the table's own bounds rather than trusted.
- **§ Warnings core reports,** the `W-SWEEP-BASELINE-CONFOUNDED` row: see § 3.

### Grep result

```
$ grep -rn "E-SWEEP-BASELINE-PARTIAL" src/ tests/ docs/reference.md docs/design-principles.md \
      docs/experimental-designs.md docs/feasibility-llm-growth-studies.md README.md
src/publishable/validate.py:1455:            # `E-SWEEP-BASELINE-PARTIAL`).      ← fixed, see above
tests/test_validate.py:2332:    `E-SWEEP-BASELINE-PARTIAL` refused exactly this shape …
```

After the fix, the only surviving mention in tracked, non-gitignored files is that one test
docstring, which names the identifier in the **past tense** to explain why the test asserts both
halves (clean validate *and* correct expansion) rather than only the first. Kept deliberately: the
reason that test has two halves is that a clean `validate` over a wrong expansion is precisely what
the retired refusal existed to prevent, and deleting the history deletes the reason.

The remaining hits are all in `docs/superpowers/` (gitignored working notes: `spec-defects.md`,
`CHECKPOINT-AGENDA.md`, `plans/`, `specs/`, `H1-SCOPING.md`). Plans and specs are dated records of
what a slice was asked to do and are correct as history. The two ledgers were amended — § 5.

---

## 2. Tests whose behaviour changed, and why each is correct

The refusal was the only thing preventing these configs from reaching task 6's expansion, so every
test that asserted the code *fires* had to become a test of what now happens instead. **Converted,
not deleted** — in every case the config is unchanged and the assertion moved from "this code is
present/absent" to "this is the expansion".

| Test (new name) | Before | After | Why this is not a regression |
|---|---|---|---|
| `test_a_baseline_that_leaves_a_grid_axis_free_validates_and_expands` | asserted `E-SWEEP-BASELINE-PARTIAL` fires, naming the free axis and "not implemented in this build" | asserts `codes(path) == set()` **and** the full 6-condition label list, `is_baseline` pattern, and that baseline `00` carries both the fixed value and its own cell | This is § Expansion modes' second row — the row the document tells a reader to *prefer*. Both halves are asserted on one config because a clean `validate` over a single `00_baseline` is the exact failure the refusal stood in for |
| `test_a_baseline_that_leaves_a_paired_axis_free_validates_and_expands` | asserted the code fires naming both `paired` paths | asserts clean, 2 baselines + 4 product rows, and that baseline `01` carries **both** of its cell's paths | A `paired` cell sets several paths at once; the assertion that the baseline row carries the whole cell is what proves the expansion is over *cells*, not over keys crossed |
| `test_a_baseline_that_leaves_a_sampled_axis_free_doubles_the_draws` (was `…_is_refused`) | asserted the code fires | asserts clean, `[True]*6 + [False]*6`, and that the 6 baselines' drawn values are the 6 draws | This is one of the two shapes the brief flagged. Pinning it as *the behaviour that ships* is the alternative to refusing it (§ 4), and the docstring says so and names the spec-defects entry |
| `test_a_baseline_fixing_every_axis_including_paired_is_one_condition` (was `…_is_supported`) | asserted the code is *absent* | asserts clean **and** one baseline labelled `baseline`, 5 conditions | A test whose only assertion is that a now-nonexistent code is absent passes vacuously forever. Re-pointed at the observable the row is actually about |
| `test_a_baseline_fixing_every_axis_is_one_condition` | same | same shape | same |
| `test_a_bare_baseline_with_no_grid_is_one_condition` | same | asserts `[("baseline", True)]` | same |
| `test_an_empty_baseline_beside_a_grid_yields_no_baseline_condition` | same | asserts the two product rows and **no** baseline condition | Load-bearing beyond tidiness: `baseline: {}` is falsy, so it must *not* be read as "a baseline fixing no swept path" and expanded over every axis. Without this test the truthiness guard in `expand` is unpinned, and losing it would double every grid whose author declared no reference at all |
| `test_a_baseline_value_is_not_subject_to_the_nameability_check` | third assertion: code not in found; docstring explained why it could not fire | assertion dropped, docstring clause dropped | The two directions the test exists for (`Param` check applied, nameability check not) are untouched |
| `test_a_crossed_grid_whose_cells_each_differ_once_is_not_confounded` | `assert "E-SWEEP-BASELINE-PARTIAL" not in found  # the baseline fixes both axes` | that line dropped; the trailing comment moved onto the surviving `W-SWEEP-BASELINE-CONFOUNDED` assertion, which is what it was explaining | — |
| `test_ablate_crossed_with_a_parameter_axis_is_refused` | inline comment said the baseline fixes the grid axis so the retired code "would otherwise make this test pass" | comment restated: the baseline no longer *has* to fix it, but the config is kept as written so the exact-set assertion still proves `ablate`'s composition is the only fault | Changing the config would weaken an exact-set assertion for no gain |
| `_error_codes` helper docstring | cited the identifier as the historical reason the composition tests assert an exact set | "a since-retired refusal on the config's `baseline`" | — |
| `test_ablated_paths_are_not_axis_shaped_paths` (`test_sweep.py`) | docstring said `E-SWEEP-BASELINE-PARTIAL` reads `_swept_paths` "to ask which axis a baseline leaves free" | now cites `_baseline_cells`, which is what asks that question | The assertions are unchanged; only the named reader was wrong |

**One test added:** `test_a_baseline_fixing_no_swept_path_expands_over_every_axis` (`test_sweep.py`)
— the other shape from § 4, pinned cell-for-cell.

---

## 3. `W-SWEEP-BASELINE-CONFOUNDED`

H1's ledger tied this warning's shape to the refusal's existence at **three** layers. The brief
named one; leaving the other two would have stranded the ruling in a smaller place. All three are
closed, and **the warning's firing condition is untouched** — the `all(axis in baseline_fixed …)`
guard, the "more than one differing axis" threshold, the one-finding-per-declaration choice, and all
four of the suite's assertions on it are exactly as they were.

### 3a. The registry row (`reference.md` § Warnings core reports)

**Before:**

> … Checked at `validate` over the declared axes alone, and only for a baseline that fixes every one
> of them — a baseline leaving an axis free is refused outright by `E-SWEEP-BASELINE-PARTIAL` until
> per-cell baselines land, **so the warning's own alternative is not yet a config core accepts**

**After:**

> … Checked at `validate` over the declared axes alone, and only for a baseline that fixes every one
> of them — a baseline leaving an axis free is the [remedy](#expansion-modes), not the fault, since
> it expands to one baseline per cell and every comparison then differs in exactly one place

The clause was not merely deleted: the row still has to say why the check is narrower than run time,
and the surviving reason is now stated positively — a free axis is the shape where nothing is
confounded *by construction*, which is why the `all(...)` guard routes such a config past the
warning rather than warning about a design that already fixed the fault.

### 3b. The emit-site comment (`validate.py`)

**Before:** *"…which is the row's own 'fixes a value on every axis', and is also the only
baseline-plus-grid shape this build admits at all (`_check_unimplemented`'s
`E-SWEEP-BASELINE-PARTIAL` refuses a baseline that leaves an axis free, since per-cell baseline
expansion is specified but not implemented)."*

That second clause went **false** with this commit, and it was doing real work — it was half the
justification for the check's narrowness. Deleting only the parenthetical would have left "is also
the only baseline-plus-grid shape this build admits at all", which is worse than the original.
Restated on the surviving reason, in the same terms as the row.

### 3c. The message

H1's entry recorded, in as many words, that *"the warning's message states the fact rather than
offering the remedy"* **because** a reader who followed the row's advice met an error. That reason is
gone, so the message now ends:

> … Fix only the axis you are measuring and leave the rest out of `sweep.baseline`: the baseline
> then expands to one condition per cell of the free axes, and every comparison differs in exactly
> one place

This is an addition, not a weakening — nothing about when the warning fires changed, and the four
existing assertions (the "2 of 4 baseline comparisons" count, the example label, both axis names)
still hold. Judgement call, flagged in § 6.

---

## 4. The two gated shapes — **recorded, not refused** (and there are three)

Recorded in `docs/superpowers/spec-defects.md` under **"Three baseline shapes per-cell expansion
makes reachable"**, with owners. Two corrections to how they had been written down, both found by
running the configs rather than reading them.

| Shape | What executes (verified) | Owner |
|---|---|---|
| A truthy `baseline` fixing **no** swept path, `{analysis.drop_missing: true}` over a four-cell grid | Every axis unfixed → 4 baselines beside the 4 product rows. 8 conditions for a four-cell design; the correction family doubles | **Task 8** |
| The same over a `sample` axis, `n: 6` | 6 baselines beside the 6 draws, each baseline carrying its own draw | **Task 8** |
| **Third, not in the brief** — a `baseline` naming **one** path of a multi-path `paired` cell | The axis counts as fixed, so it does not expand; the baseline row carries `min_samples` and lets `analysis.confidence` fall to the **base config's** value, which may be neither declared cell's. A cell the axis never produces, and **nothing catches it** — verified with a probe: `validate` reports zero findings | **the `groups` slice** |

The third was found because `sweep.py:631`'s comment (§ 1) said in as many words that a
mix-and-match "the axis never produces" was not caught by the refusal either, since resolving a
baseline against actual cells was task 6's feature. It is the same class as the other two, so it is
one entry with three rows rather than a fourth thing to rediscover.

### Two corrections to the prior record

The task 6 entry described shape 1 as `baseline: {z.unknown: 9}` producing "four baseline conditions
whose `values` equal the four product rows". Both halves are wrong:

- **`z.unknown` never reaches the expansion.** `validate._check_sweep` resolves every
  `sweep.baseline` path against `parameter_spec` (`validate.py:1350-1351`), so an undeclared path is
  `E-SWEEP-PATH-UNKNOWN` first. The shape needs a **declared** non-swept path to be live at all.
- **The `values` are not equal.** Each baseline row is `cell` then `fixed` laid over it, so it
  carries the baseline's own paths on top of the product row's.

### The sharp version, which is narrower and worse

The `values` differ, but the **resolved parameters coincide** whenever the baseline's fixed value
equals the base config's own — `{analysis.drop_missing: true}` over a config whose `parameters`
already say `true` gives four baseline conditions whose resolved config, and therefore whose
`parameters_hash`, is identical to the product row in the same cell. The run pays twice for one
answer and the correction family counts it twice. That is the degenerate case; the count doubling is
the general one.

### Why recorded rather than refused

1. **The rule the document states is unconditional.** "The baseline expands over whichever axes it
   doesn't fix — group axes and parameter axes alike", plus "Prefer the second row whenever the
   levels are peers." Carving the all-axes-unfixed case out of that is a change to a normative
   document with an argument attached, and this repo's rule is that the document changes first. A
   refusal minted here would be code diverging from `reference.md` in the same commit that stopped
   code from diverging from `reference.md`.
2. **The shape is legitimate under a non-degenerate reading.** A baseline fixing a declared
   non-swept path to a value the config does *not* already hold is a per-cell **reference arm**:
   every cell measured once at `drop_missing: false` and once at the config's own setting. Refusing
   it is the same error `sweep.ablated_paths` exists to avoid — refusing a legal config with a
   message about cells. Nothing separates the two readings structurally; the only difference is
   whether the fixed value equals the config's, which is a `parameters_hash` fact, not a
   declaration one, so a `validate`-time refusal cannot draw the line where the harm is.
3. **The harm is expressed in comparisons, and comparisons are task 8's.** Doubling the correction
   family and deciding which baseline a `vs_baseline` targets are one question. The brief explicitly
   fences those off from task 7, so a refusal minted here would have to be re-argued there.

No identifier was minted, so nothing was grepped-then-added; the entry instead records that
`W-SWEEP-BASELINE-` is unminted and must be grepped if task 8 decides a warning is right.

**All three shapes are pinned by tests in tracked files** — `spec-defects.md` is gitignored, and
this slice has already lost a prose-only record once:
`test_a_baseline_fixing_no_swept_path_expands_over_every_axis` and
`test_a_baseline_that_leaves_a_sampled_axis_free_doubles_the_draws` were written for this purpose
and say in their docstrings that they record what ships rather than what is wanted.

**CORRECTED in round 2 — shape 3's pin was overclaimed.**
`test_a_baseline_naming_one_path_of_a_paired_entry_fixes_that_whole_axis` is **task 6's** test, and
its docstring explained the mechanism (why a half-fixed axis counts as fixed) while saying nothing
about the shape being open, unrefused, or owned later. It was a change-detector, not a record — and
shape 3 is the one I call least defensible. Its docstring now carries the record: what falls to the
base config, that `validate` reports nothing, that task 7 made it reachable, and **owner: the
`groups` slice**.

---

## 5. Ledger amendments (`docs/superpowers/`, gitignored)

| Entry | Amendment |
|---|---|
| "New error identifier: `E-SWEEP-BASELINE-PARTIAL`" | Heading struck through, **CLOSED**, with what was removed and which tests now pin the three configs it listed as supported |
| "New warning identifier: `W-SWEEP-BASELINE-CONFOUNDED`", second bullet | **CLOSED**, naming all three layers of § 3 and stating explicitly that the message was changed and the firing condition was not |
| "Per-cell baseline numbering …" | Its **"Not reachable today"** header was false as of this commit — this is the entry task 8 builds on, and it told a reader the question was theoretical. Amended to "now reachable"; the argument is unchanged, its status is not |
| "Two minors riding along", row 1 | Struck through and pointed at the new entry, which corrects its example and its `values` claim |
| `cli.command_run` swept-path union entry | "the same union `label_for` and `E-SWEEP-BASELINE-PARTIAL` already build from" → present-tense claim about a retired code; now names `label_for` and the retirement |
| `CHECKPOINT-AGENDA.md` rows 26 and 683 | Marked **CLOSED 2026-08-12 (H2 tasks 6, 7)**. Both said the owner was "when per-cell expansion lands" |

Two mentions were **left** deliberately: the struck-through `E-SWEEP-ABLATE-UNSUPPORTED` window
record and the row-216 record both describe, in the past, a window in which the refusal could have
masked another fault. They are accurate history inside already-closed entries.

---

## 6. Mutation testing

Both mutations were run against the **committed** tree (`eba1804`) and reverted with
`git checkout`.

**Mutation 1 — re-add the refusal** (the `unfixed` computation, the `_swept_paths` import, and a
`c.error("E-SWEEP-BASELINE-PARTIAL", …)` with a stub message):

```
FAILED tests/test_validate.py::test_a_baseline_that_leaves_a_grid_axis_free_validates_and_expands
FAILED tests/test_validate.py::test_a_baseline_that_leaves_a_paired_axis_free_validates_and_expands
FAILED tests/test_validate.py::test_a_baseline_that_leaves_a_sampled_axis_free_doubles_the_draws
3 failed, 384 passed
```

Each failed on `assert codes(path) == set()` with `{'E-SWEEP-BASELINE-PARTIAL'}` on the left — i.e.
on the removal itself, not incidentally.

**Mutation 2 — the expansion half is load-bearing too.** A test that only asserted a clean
`validate` would pass against the pre-task-6 single baseline, which is the exact defect the refusal
was standing in for. `_baseline_cells`' `unfixed` list was forced to `[]` (the old behaviour: one
baseline, always):

```
FAILED …test_a_baseline_that_leaves_a_grid_axis_free_validates_and_expands
FAILED …test_a_baseline_that_leaves_a_paired_axis_free_validates_and_expands
FAILED …test_a_baseline_that_leaves_a_sampled_axis_free_doubles_the_draws
3 failed
```

All three failed on the `is_baseline` / label assertions, with `validate` still clean — so each test
independently catches both halves of the divergence.

Restored: `git status --short` empty, full suite 1062 passed.

---

## 7. Questionable / worth a reviewer's eye

1. **I changed `W-SWEEP-BASELINE-CONFOUNDED`'s message** (§ 3c), and it is the right call rather
   than an open question. The brief said "do not weaken the warning" and "remove whatever clause
   said [the remedy] was not [reachable]". The message carried no such clause, but H1's ledger
   recorded that the message's *shape* — fact, no remedy — was chosen **because** the remedy was
   refused. That reason is gone, and the layer a user actually reads is the message, so leaving it
   would strand the ruling where it matters most. The firing condition is unchanged line for line
   and all four assertions on it still pass. Flagged because it exceeds the brief's literal step 3,
   not because it is unsettled; nothing else depends on it, so it reverts in one edit.
2. **The brief's row count was wrong** (60 → 59; actually 65 → 64). Counted mechanically. Nothing in
   `reference.md` states a row count in prose, so nothing else needed updating — but if a later
   audit cites "60 rows" it is citing the brief, not the document.
3. **`tests/test_validate.py:2332` still names the retired identifier**, in the past tense, in a
   docstring. Deliberate (§ 1). If the convention is that a retired identifier appears nowhere in
   `src/` or `tests/`, this is the one line to cut — the test's assertions do not depend on it.
4. **Three shapes now validate clean that arguably should not** (§ 4). I am confident refusing them
   was not task 7's call, and confident the third is the least defensible of the three (the baseline
   row runs a `paired` combination the axis never declares, silently, with the base config filling
   the gap). It is `groups`-slice work because resolving it needs a baseline matched against actual
   cells — the same machinery as the numbering question — but it is the one I would raise first if
   the slice's reviewer wants something refused now.
5. **`docs/superpowers/spec-defects.md` and `CHECKPOINT-AGENDA.md` are gitignored**, so § 4's and
   § 5's records are not in commit `eba1804`. The tracked handle for all three shapes is the tests.
6. **Not touched, per the brief:** `vs_baseline` targeting, the comparison count, and § Expansion
   modes' own circular second-row example (task 8 owns it). The § Expansion modes two-row table
   needed no edit — it already described what now happens.

   **CORRECTED in round 2.** This item originally read "recorded by task 6", which misattributes
   the record. Task 6 did file the circular *example* as task 8's. It did **not** file the contrast
   **targeting** gap as an open item — it recorded the opposite, that the window would not open,
   because `E-SWEEP-BASELINE-PARTIAL` would stay. Task 7 removed that refusal, so task 7 opened the
   window and owed the handle. See § 9.

---

# Round 2 — review response

**Commit:** `b61c054` — *fix: the confounded row states silence, not a verdict*
**Suite:** 1062 passed, **2 xfailed**, ruff clean, mypy clean on 40 source files. No `ruff format`.
Sanity checks the review asked for: `E-SWEEP-GROUPS-UNSUPPORTED` still fires
(`_check_unimplemented` untouched in that loop; its test passes), and the worked example still gives
3 conditions (`method=pearson`, `method=spearman`, `method=kendall`).

## 8. Critical 1 — the clause was false, and I wrote it into three places

The review is right and the proof it gives is the one that settles it without any document
semantics: my own comment block claimed the free-axis shape "is the shape where nothing is
confounded by construction" four lines above a surviving sentence saying "this never fires where a
run would not mark the comparison". The run does mark it. Measured:

```
method=spearman__sex=m vs sex=f__baseline   differs_on ['analysis.method','data.sex']  confounded True
```

I over-read § Expansion modes' *design intent* ("every contrast differs in exactly one place") as a
statement about what this build reports. It is the intent of a design whose contrast targeting is
**task 8's and not yet built**, so asserting it as current behaviour is exactly the direction
`CLAUDE.md` forbids — and § 4 of this report invokes "the document changes first" to justify *not*
refusing three shapes, which makes the asymmetry the review names entirely fair.

**The fix is the same claim at all three layers: the check's silence is silence, not a verdict.**
The message change is kept — it was right in kind — but it no longer promises a property the build
does not deliver.

| Layer | Now says |
|---|---|
| `reference.md` § Warnings core reports | "…a baseline leaving an axis free is a different shape rather than this fault, expanding to [one baseline per cell](#expansion-modes) of the free axes instead of one reference for the whole run, so the row's condition does not hold and nothing is reported. **Silence there is not a verdict that such a design confounds nothing:** what each comparison is taken against is `vs_baseline`'s question, not this row's" |
| `validate.py` emit-site comment | The row's condition does not hold, so the `all(...)` guard skips it — "silence rather than a verdict — and **NOT** a claim that nothing is confounded there", then names the actual reason: `contrasts.resolve_contrasts` still targets the first baseline, so a run over such a design *does* mark cross-cell comparisons `confounded`. Points at the two strict xfails. The self-contradiction with "this never fires where a run would not mark the comparison" is gone — the two paragraphs now describe one under-warning direction rather than opposite claims |
| The warning **message** | "…The design that avoids this is a baseline fixing only the axis you are measuring: it expands to one baseline per cell of the axes it leaves free, which is the row § Expansion modes tells you to prefer when the levels are peers — **though in this build each comparison still resolves against the run's first baseline, so those per-cell references are not yet what its contrasts are taken from**" |

The message hedge is deliberately the longest of the three: it is the layer a user acts on, and
without the caveat it routes them out of a warned-but-honest design into an unwarned wrong one.
Task 8's checklist in the ledger includes **deleting** that caveat, the matching docstring
paragraph, and the `resolve_contrasts` sentence in the comment — all three exist only because the
window does, and a caveat nobody retires is its own defect.

## 9. Critical 2 — the window, and its tracked handle

Reproduced exactly as reported, on the shape § Expansion modes tells a reader to prefer:

```
6 conditions, 2 baselines → 5 comparisons (§ Expansion modes says four)
  sex=m__baseline        of=1 against=0     ← a reference compared against a reference
  method=pearson__sex=m  of=3 against=0     ← cross-cell: differs on method AND sex
  …
```

`correction.family_shape` counts `len({m.where for m in members})`, so `family_size` is 5 × metrics
instead of 4 × metrics and every corrected interval in the run rests on the wrong denominator with
no diagnostic anywhere. The review's framing of my failure is accurate and worth restating plainly:
in the same commit I pinned three shapes *I* discovered with tracked tests, three times, describing
each as "the behaviour that ships, not the behaviour that is wanted" — and the one window handed to
me by the previous task got a note in a gitignored file.

**Two handles added to tracked `tests/test_contrasts.py`**, both `@pytest.mark.xfail(strict=True)`,
both built from real `expand` output rather than hand-written `Condition`s so the count under test
cannot drift from the expansion:

| Test | Assertion | Cites |
|---|---|---|
| `test_two_per_cell_baselines_are_four_comparisons_not_five` | `len(resolve_contrasts({}, conditions)) == 4` | § Expansion modes: "six conditions under two per-arm baselines are four comparisons in the correction family, not five" |
| `test_no_comparison_has_a_baseline_condition_as_its_subject` | no comparison's `of` is a baseline index | § Expansion modes: "Baseline conditions are references rather than comparisons, so they never count as one" |

I took the review's refinement over copying task 4's form, and the distinction is real: task 4's
`xfail` stood in for a *missing refusal*, where the assertion could only be "some error". This is a
wrong **number** and the specification states the number, so it is assertable today. The second test
is the sharper of the two — a baseline appearing as a comparison's subject is one reference measured
against another, `sex=m__baseline` vs `sex=f__baseline`, which is precisely the confounded cross-cell
contrast per-cell baselines exist to avoid.

**Mutation (against committed `b61c054`, reverted after):** filtering baselines out of
`resolve_contrasts`' subject loop makes both assertions pass, and `strict=True` turns that into
`FAILED … [XPASS(strict)]` for both. So they flip loudly the moment task 8 lands and cannot be
merged away silently. Restored; `git status --short` empty, full suite green.

The ledger entry — **"Per-cell baselines reach `resolve_contrasts`, which targets the first baseline
for every condition"** — records the reproduction, the family-size arithmetic, the two handles, and
a four-item checklist for task 8 (match unfixed-axis values not positions; delete the message
caveat; delete the docstring paragraph; re-read the § Warnings row once silence *becomes* a verdict).
It also states plainly that task 7's commit opened the window, rather than leaving that to be
inferred.

## 10. The two "Important" corrections

- **§ 4's tracked-handle claim** was overclaimed for shape 3 and is corrected in place, above.
  The substantive fix is not report wording: task 6's
  `test_a_baseline_naming_one_path_of_a_paired_entry_fixes_that_whole_axis` docstring now records
  the shape as open — what falls through to the base config, that `validate` reports nothing, that
  task 7 made it reachable, and **owner: the `groups` slice** — instead of only explaining the
  mechanism. It is now a record, not a change-detector.
- **§ 7.6's misattribution** is corrected in place. Task 6 recorded that the window would *not*
  open because the refusal would stay; task 7 removed the refusal, so the window and its handle are
  task 7's, not an item task 6 filed.

## 11. Minor

`validate._check_unimplemented`'s docstring: my inserted paragraph had orphaned "Both declared
orders are honored — `randomized`" mid-paragraph on a short line. Reflowed into three paragraphs —
the modes-and-orders sentence intact, then the partial-baseline paragraph (which now also says that
what those baselines are compared *against* is unsettled, pointing at the xfails), then the
`sweep.paired` material.

## 12. Concerns after round 2

1. **The `W-SWEEP-BASELINE-CONFOUNDED` message now carries a build-state caveat**, which is a
   different kind of sentence from the rest of the diagnostic surface. I judged an accurate long
   message better than a short one that misroutes, but if the house rule is that a message never
   describes what a later slice will change, the honest alternative is to drop the remedy clause
   entirely and go back to fact-only — the ledger's reason for adding it is closed either way, since
   the row and the comment now carry the remedy.
2. **The two xfails are the only thing standing between a merge and a wrong correction family.** If
   task 8 slips, this branch ships 5-comparison families for any per-cell design with no
   user-visible diagnostic. A `W-` on a multi-baseline run would be the belt-and-braces version; I
   did not add one because the brief fences the comparison count off from task 7 and minting an
   identifier here would be re-argued in task 8. Worth an explicit decision rather than inheriting
   mine.

---

# Round 3 — the message is fact-only

**Commit:** `d53b702` — *fix: the confounded message states the fact and stops*
**Suite:** 1062 passed + 2 xfailed, ruff clean, mypy clean on 40 source files. No `ruff format`.

## 13. The residual, and why cutting the clause removes it entirely

The re-review is right, and the measurement is the part I should have made myself before defending
the hedge. My message's lead clause said *"The design that avoids this is a baseline fixing only the
axis you are measuring"* — and taking that advice does not avoid it:

```
method=spearman__sex=m vs sex=f__baseline   differs_on ['analysis.method','data.sex']  confounded True
```

My trailing caveat retracted the **mechanism** ("those per-cell references are not yet what its
contrasts are taken from") while saying nothing about the **outcome** the reader actually sees, which
is that the verdict is still reported. So the reader was still promised an escape that does not
exist — Critical 1's defect class reduced in degree rather than eliminated. Two rounds of hedging a
clause that cannot be made true in this build is itself the signal that the clause does not belong.

**The remedy clause and its caveat are cut. The message is now byte-identical to its pre-task-7
text** — verified against `eba1804^`, not by eye:

```
$ git show eba1804^:src/publishable/validate.py | grep "no amount of correct pairing"
                "and no amount of correct pairing separates them",
```

So this slice's net change to `W-SWEEP-BASELINE-CONFOUNDED` is: the § Warnings row rewritten, the
emit-site comment rewritten, and **the message untouched**. That is a cleaner outcome than either of
my previous two attempts, and it accepts the convention the reviewer surveyed: build-state language
belongs in a message when the build gap *is* the finding (`fold.stratify_by`, the resolver refusals,
the `-UNSUPPORTED` family), and there is no precedent for appending another subsystem's build state
to a message whose subject is a substantive fault in the user's own config.

**One addition, so this is not re-litigated a fourth time.** The remedy now lives in exactly two
places — the `reference.md` row and the emit-site comment — and the comment now records *why the
message does not carry it*, at the point where someone would add it back: that a message telling the
reader to free an axis would promise an outcome this build does not deliver, that the only hedge
which would make it true is another subsystem's build state, and that the remedy goes back in once
per-cell targeting makes it true. Without that sentence the message reads as an oversight and the
next reader repeats my mistake.

## 14. Ledger correction that followed

The task-8 checklist in **"Per-cell baselines reach `resolve_contrasts`…"** told task 8 to delete a
message caveat that no longer exists. Rewritten: the message is *not* one of the places to edit, it
is byte-identical to pre-task-7, and **adding the remedy back is task 8's** once targeting makes it
true. The two places that do still carry window-only text — the `resolve_contrasts` sentence in the
emit-site comment and the "compared *against* is not settled" paragraph in
`_check_unimplemented`'s docstring — remain on the checklist.

## 15. Rulings accepted, and the gate

- **No temporary `W-`** on a multi-baseline run. Accepted, and the reasoning is stronger than my
  own framing: a new identifier would land on the enumerated warnings surface and be deleted next
  task, and `strict=True` already means task 8 cannot land silently.
- **The merge gate is the coordinator's:** this branch must not reach `main` while the two xfails
  are still xfailing, because a `main` carrying task 7 without task 8 ships 5-comparison correction
  families with no diagnostic. Recorded here so the gate is written down in the task's own report
  and not only in the thread. Nothing in this report asks for it to be waived.
- **Two nits left as-is** on the reviewer's ruling: three `#expansion-modes` links in one row cell
  (valid, verbose), and the new `test_sweep.py` docstring citing gitignored `spec-defects.md` (repo
  convention — thirteen tracked files already do).

## 16. Concerns after round 3

None outstanding on task 7's own surface. Both concerns I raised in § 12 were ruled on and both
rulings are implemented; the only live risk is the merge gate above, which is owned and recorded.
