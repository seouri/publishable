# H5b batch 5 — tasks 15 and 16 — the records and the § Executability entry

**Commits:** `56aad22` (task 15), `da31016` (task 16). Suite **2931 passed, 1 skipped, 2 xfailed**
(191 s, foreground, one run — this batch moves no file under `src/` or `tests/`, so one run covers both
tasks). `ruff check`, `ruff format --check`, `mypy` all clean before each commit.
`.superpowers/sdd/.gitignore` **was clobbered to a bare `*` when the briefs were extracted** and was
restored from `HEAD` before anything else; this report is added with `git add -f`.

**Disagreements found: five, none of them zero.** They are in § Disagreements below rather than buried,
because *six consecutive slices reported zero and all six were wrong*, and the two that matter changed
what task 15 wrote.

---

## Task 15 — the records

### Step 1 — the three strikes, each checked against the code

**(a) *a unit whose only recorded column is non-numeric is silently dropped* — STRUCK.** Heading marked
`~~OPEN~~ STRUCK 2026-08-22 (H5b task 15)`, its `**Owner: H5b**` struck, and a closing note appended
below its own *Cost while unclaimed* paragraph — the body is not retro-edited. The note states:

- **Which of the four options was taken:** the **first** — the unit is admitted *and* the non-numeric
  column is carried with it.
- **Why each of the other three was rejected, a reason each rather than an elimination.** *Carried with
  the column omitted*: repairs `n` and throws the value away, leaving `aggregate`'s table describing
  something no artifact holds while `units.parquet` beside it holds the value. *Refused loudly*: `None`
  is a legal recorded value and an annotation beside numbers is ordinary — it would refuse the step
  `publishable init` generates, which records `{"present": True}` and nothing else. *The silent drop*:
  the entry's own ground stands.
- **The fourth question the entry did not ask, answered:** such a unit **does** enter `paired_keys`,
  `n_paired` and the resample pool — Decision 6, documented by task 8 in `reference.md` § Statistical
  reporting, quoted in the note; a recorded column's contrast narrows again at the subtraction, so its
  count and its difference vector are the same set by construction.
- Symptom re-verified rather than asserted: `n_valid` reads `{value: 6.0, ci95: [6.0, 6.0]}` where the
  entry measured `0.0` / `[0.0, 0.0]`, pinned as arm B
  (`tests/test_stats.py::test_a_bool_only_column_widens_exactly_seven_moving_keys`).

**(b) *the `aggregate` table omits declared unit attributes and non-numeric columns* — non-numeric half
STRUCK.** That entry is a **table row** in the `AMENDED 2026-08-11` table under § Carried out of the S4a
whole-branch review, so the row's non-numeric clause is wrapped in `~~…~~` and carries
`**STRUCK 2026-08-22 (H5b task 15): … see the note below this table. The attributes half was already
closed by S5 task 13 and is not re-struck.**`, with the substantive note appended **after** the existing
`AMENDED 2026-08-22 (H5a task 12)` paragraph — the same shape the empty-level-gate row already uses. The
note also records that the forward-pointing sentence under § `units.parquet` type unification (*"see the
S4a residue table entry below for that question's own status"*) needs **no** edit: it points at the row,
and the row now carries the answer. **No positional locator is used** — the note names the table by its
own heading.

**(c) *the second empty-level gate in `cli`'s stratum loop* — CONFIRMED already struck by task 11, and
NOT struck again.** Verified: `grep -n "STRUCK 2026-08-22 (H5b task 11)" docs/superpowers/spec-defects.md`
→ **2** lines, both task 11's (the row's own strike and the note below the table), and nothing was added
by this task. *An entry struck twice reads as two gaps.*

### Step 2 — the three things filed nowhere

| Item | Where it landed |
|---|---|
| The mixed `str`/`float` question H5a's design called *"Filed, not built, owner H5b"* | **Task 3's entry exists and no second one was written.** Confirmed by heading: `## OPEN — whether `E-STEP-RETURN-TYPE` should ever be forgiving for a genuinely mixed `.parquet` column — **Owner: unassigned, with the reason**`, which itself records *"There was no such filing"* with its own two greps and their control. Discharged on the read side by Decision 11 in `reference.md`; the write-side residual is the filing |
| A derived key colliding with a non-numeric recorded column is not refused | **Already recorded by task 10** as *found and closed in the same slice* (`## STRUCK 2026-08-22 (H5b task 10) …`). Confirmed, not duplicated |
| A non-numeric recorded `by` column draws no `W-STATS-STRATUM-SHADOWED` | **Written by this task**, in task 10's form: `## STRUCK 2026-08-22 (H5b task 9) — CLOSED in the slice that found it …`. Carries the proxy diagnosis (`step_summary` answered *did the column earn a block?* for a question about *was the column recorded?*), the pin and its mutation, the end-to-end console-script result, the two `report.py` docstrings that stood in for the filing, and the § Warnings row as the third home of the two-case sentence |

**Recorded as this batch requires: *a design line saying "Filed" is not a filing* — second instance in
one slice pair**, the first being H5a's own `.csv`-null question, which was a ledger line and a dispatch
line. Both are now entries in the file rather than claims in a design.

### Step 3 — the H9 filing, with both halves verified and the gap reproduced

**Landed as** `## OPEN — `diff`'s `uv.lock` row prints two digests and never names the package whose pin
moved — **Owner: H9**` at the end of `spec-defects.md`.

**Both halves of the controller's ruling, grepped and reported:**
`grep -rn "uv_lock_hash" src/publishable/*.py` → `src/publishable/cli.py:3769` writes it inside the
`"environment"` mapping (beside `"uv_lock": "environment/uv.lock"`), and `src/publishable/diff.py:234`
reads exactly `provenance.environment.uv_lock_hash` for the `uv.lock` row in `ROW_LABELS`
(`diff.py:36`). So the ruling holds: `uv.lock` **is** the carrier, and the smaller true claim is that the
row pointing at the change is the one a reader is least likely to read.

**Reproduced, not reasoned.** Scratch test built on `tests/test_diff.py`'s own `build` helper — scaffold,
commit a `uv.lock`, `run`, rewrite the lockfile so exactly one package's pin moves, commit, `run` again,
`command_diff(run_a, run_b)`:

```
PYTHONPATH=. uv run pytest <scratchpad>/test_h9_repro.py -s -q
  uv.lock            DIFFERS
    sha256:45cd… → sha256:2d84…
```

`pkg-a` — the only thing that changed in the lockfile — appears nowhere, at exit `0`. The assertion
`"pkg-a" not in out` **passes**, which is the gap. The filing also records the route that *does* exist
(each run archives `environment/uv.lock`, `cli.py:2393`), and that `parameters_hash`'s own `DIFFERS`
detail already prints per-parameter deltas rather than two digests — so a per-package delta is the shape
this row's sibling has and it does not. **Owner: H9** with the surface reason (`reproduce` reads the
environment back). **Nothing minted**, and the refusal of a fourth hash / a core-version key / a `diff`
row of its own is recorded as a decision.

**One correction to my own first draft of that filing**: I named the shipped test as
`test_h8b_fixture_l_uv_lock_identical_and_differs`, which does not exist. Corrected before commit to
`test_h8b_fixture_l_the_lockfile_rows_non_null_path` (`tests/test_diff.py:252`), with the true and
load-bearing fact beside it: **it takes no `capsys`**, so the missing detail was never visible to it.

### Step 3b (not in the brief) — five stale *reasons*, re-owned in one appended note

`grep -n "H5b, H6, H9, H3c-3's remaining 14" docs/superpowers/spec-defects.md` → **3** lines, plus one
spine-citing variant and one under § Carried out of the S4a whole-branch review: **five entries name H5b
inside the enumeration that justifies their `unassigned` verdict.** At merge each asserts a closed slice
is pending. Filed as one appended note — `## RE-OWNED 2026-08-22, as H5b completes …` — on the
`RE-OWNED 2026-08-19` / `RE-OWNED 2026-08-21` precedent (five bodies edited would destroy what each
recorded on its date), naming the five **by their question, not by position**, and stating the corrected
form as *"no remaining slice (H6, H9, H3c-3's remaining 14)"* — **copied from task 3's own entry**, which
already omits H5b, rather than invented. **No owner changes**; none of the five is H5b's surface.

**And it widens the missing check's shape:** the `RE-OWNED 2026-08-21` entry proposed a test that parses
each entry's `Owner:` line — **none of these five names H5b in an `Owner:` line**, so the check as
proposed would not have caught them. The note says the check wants the `Owner:` line *and* the
*"no remaining slice (…)"* enumeration. Still unassigned, with the reason.

### Step 4 — the spine correction, appended, nothing edited

Appended after the existing *Correction to this amendment, same day, from H5b's scoping*, as
**Second correction to this amendment, 2026-08-22**. It records: the § The hardening slices row sizes
H5b at **(10)**; the slice **shipped 16 tasks**
(`grep -c '^## Task ' docs/superpowers/plans/2026-08-22-non-numeric-columns-downstream.md` → **16**);
the design's own *"The scoping's 15 stand"* disagrees too, so the count is stale in the same direction as
H5a's 9-versus-13 the correction above it was already about. And the exposure is **the design's
§ The behaviour change enumeration**, not a phrase: seven keys in one direct-call fixture, a whole
correction family in a second, a derived metric's `p_value` in a third, every `report_by` level's keys in
a fourth, and four things that newly stop or newly warn.

### Step 5 — `CLAUDE.md`

**Every occurrence of "H5b" reconciled; the list, as required.** Before this task: lines 28, 29, 30
(the order line and its H5-split sentence) and line 191 (the H5a entry's *"the first of H5's two"*).
After: the order line reads **H6, H9, then H3c-3's remaining 14**, with H4/H5/H7/H8 named complete and
both H5 sub-slices dated; the H5-split sentence no longer claims *"only H5b carries behaviour-change
exposure"* — **the claim is deleted, not rewritten**, and replaced by the narrower form the spine's own
first correction already established (H5b changes what an existing key may contain and report; H5a's was
additive to what `io.write` accepts); the H5a entry's *"the first of H5's two"* stays true and is
untouched. `grep -n "H5b" CLAUDE.md` after the edit → the order-line block plus the new entry.

**The new entry carries the disclosure the controller ruled stands, as an enumeration.** Nine classes,
not eight — see § Disagreements. Seven keys with computed before/after literals from arm B
(`n_valid.value` `0.0 → 6.0`, `.ci95` `[0.0, 0.0] → [6.0, 6.0]`; `n_rows.value` `4.0 → 6.0`, `.ci95`
`[4.0, 4.0] → [6.0, 6.0]`; `mean_score.n.completed` `4 → 6`; `mean_score.ci95`
`[0.5, 2.5] → [0.3333333333333333, 2.5]`; `mean_score.resample_draws` `2000 → 1998`), with
`mean_score.value` staying `1.5` named as the load-bearing unmoved one; the eighth class (`p_value`
`0.846307385229541 → 0.812375249500998`, and `p_value_corrected` through the family, § Corrections 16);
the ninth (`report_by` levels, Ruling 8); the correction family's `n_paired` `4 → 6` and the Holm level
swap; **four** things that newly stop or newly warn including `W-STATS-RESAMPLE-THIN` on a purely numeric
metric with **no § Warnings row moving**; and **two** warnings minted, not one — see § Disagreements.
`resample_draws` is stated as seed-dependent with **four** distinct measured literals (`1998`, `1999`,
`1997`, `1927`), two of them pinned. `uv.lock` is named as the carrier, with *being able to derive the
change from a lockfile hash is not being told*.

**One invariant reconciled, minimally.** § Invariants' *Units are the inference base* bullet ended its
`aggregate`-table clause at the four operations; it now also says the table carries **every** recorded
column (a non-numeric one included, earning no block) beside every declared attribute, and that a metric
over a partially covered column reports **that** contributing count as its own `n.completed` while the
four-way `n` is **not** widened. Both sentences exist in `reference.md` § Statistical reporting and
§ Templates already; nothing new is claimed here.

### Step 6 — both consistency passes

**Mechanical**, over the four documents **by name** plus the analysis, skipping fenced blocks, with one
throwaway script (`<scratchpad>/mech.py`, not kept in the repo):
`uv run python mech.py` over `README.md docs/design-principles.md docs/experimental-designs.md
docs/reference.md docs/feasibility-llm-growth-studies.md` → **`MECHANICAL: clean (5 files checked)`**.
Checks: relative links, local `#anchor`s, cross-file `file.md#anchor`, duplicate anchors, table row width
against the header, trailing whitespace, tabs, invisible unicode.

**Proven able to fail, per class, and this is where the pass earned its keep twice.** First run reported
**three** table-width hits in `docs/reference.md` — all false, because `\|` inside a cell was being
counted as a separator; fixed and re-run. Then, on a copy at `docs/_probe_can_fail.md` with seven faults
injected and deleted immediately after:

```
:7 TRAILING WHITESPACE   :8 TAB   :13 INVISIBLE U+200B
:222 DUPLICATE ANCHOR #validation (also line 6)
:12 TABLE COLS 1 != header 2
:9 BROKEN LOCAL ANCHOR #no-such-anchor-at-all   :9 MISSING FILE does-not-exist.md
```

and a second probe for the eighth class: `docs/_probe2.md:2 BROKEN CROSS ANCHOR
reference.md#nope-not-here`. Both probe files removed (`ls` confirms absent).

**`×` not `x`:** `grep -nE '[0-9] ?x ?[0-9]'` over the five files → **0 hits**; the identical pattern
with `×` → 21 hits across three files, so the sweep can hit.
**Hyphen not en dash in anything that becomes an anchor:** `grep -nE '^#+ .*–'` over the five files plus
`CLAUDE.md` → **0**; control `grep -n '–'` over the same list → many (C1–C3 etc.), so the sweep can hit.
Em dashes in headings are the established house style (`### E1 — Metric calibration`) and are not flagged.

**Removal sweep — and it caught the newline trap this repo has already recorded.** Run over
`README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md
docs/feasibility-llm-growth-studies.md CLAUDE.md`, **filtering the file list and never the output**, for
the strings this slice deleted or replaced. My first pass used `grep -rF` and reported `0` for
*everything* — including a string that is present — because **zsh does not word-split an unquoted array
variable** and every file name was being treated as one path (`ugrep: warning: … No such file or
directory`). Re-run with a proper array, then re-run again **newline-insensitively** in Python (whitespace
collapsed), because a phrase-level `grep` cannot match a line-wrapped sentence — the exact shape the
batch-3 ledger records as *"a 'two lines' grep could not have found the site whose docstring was
line-wrapped."*

| String | Hits |
|---|---|
| `keeps its value but gets no contrast delta` | 0 |
| `even one dropped above for being non-numeric` | 0 |
| `only H5b carries behaviour-change exposure` | 0 |
| `those units carry no value for it` | 0 |
| `H5b, H6 Hashes and provenance` | 0 |
| `sub-slice H5b` | 0 |
| `Owner: H5b` | 0 |
| `is silently dropped` | **1** — `docs/feasibility-llm-growth-studies.md`, inside the **dated** H5a entry |
| `owned by H5b` | **1** — same sentence, same dated entry |
| `W-STATS-COLUMN-THIN` (**can-fail control, known present**) | 5 — `reference.md`×3, `CLAUDE.md`×2 |

The two surviving hits are a **dated build claim in a dated entry**, which is superseded by appending and
never by editing; task 16's entry quotes that sentence and says what it replaces. The naive `grep`
would have missed both.

**Cross-document**, over the four only:

- **The shared worked example — zero hits, shown by `git diff` as the brief requires.**
  `git diff main..HEAD --stat -- README.md docs/design-principles.md docs/reference.md` → **only
  `docs/reference.md`, 23 insertions / 4 deletions**; `README.md` and `docs/design-principles.md` are
  untouched by the whole branch. `git diff main..HEAD -- <those three> | grep -E '^[+-].*(0\.581|0\.488|
  0\.661|0\.607|0\.517|0\.683|0\.412|0\.347|0\.477|0\.026|-0\.007|0\.059|-0\.169|-0\.213|-0\.125|0\.014|
  8e21|1a2b|3d8a|6b1f|2f5c8d0|228|240)'` → **0**. Can-fail proof for that exact command shape:
  substituting `non-numeric` for the literal alternation → **4** hits. No worked-example interval is
  narrowed, and no hash prefix moves.
- **Config completeness:** no config field is added or renamed anywhere on this branch — the 23 added
  `reference.md` lines are three § Warnings rows, § The per-unit tables / § Statistical reporting /
  § Templates prose, § Statistical reporting's two intersection paragraphs, and § Reporting strata's
  absent-not-empty rule. Nothing owes § The one config file.
- **Enum comments:** no `# a | b | c` comment and no enumerated value set changes on this branch.
- **Schema fields in prose:** every field named in the added prose (`n.completed`, `n_paired`,
  `resample_draws`, `by`) already appears in the `run.yaml` examples; no new key is named.
- **Declared vs. derived:** the per-column contributing count is derived and is shown as settable
  nowhere — `limits.min_reported_n` is the only settable thing in the neighbourhood and is documented as
  a floor read at `run`.
- **Versions:** `CITATION.cff` `version: 0.1.0` and README's `v0.x` notice both unchanged and consistent;
  README is untouched by the branch.
- **Prevented mistakes:** `experimental-designs.md` § Mistakes core prevents is checked and **owes no
  row**: every entry there is a mistake made *structurally impossible by the schema*, and this slice's
  four stoppages are refusals and warnings at `run`, not schema impossibilities. Recorded as a check
  performed rather than left silent.

### Step 7 — named blind, and what replaces it

No mutation: nothing executable moved. The replacement is this batch's filing-and-sweep review plus the
can-fail proofs pasted above, each run against a string or a fault known to be present.

---

## Task 16 — the § Executability entry

Appended as `### Measured on 2026-08-22 against commit `56aad22` — after H5b`, dated and pinned; the entry
says the pin names the branch tip the figures were derived against and that tasks 15/16 move no file under
`src/` or `tests/`, so it names the same executable tree as the batch-4 tip that shipped the behaviour.
`docs/feasibility-llm-growth-studies.md` is the only file this task touched, and only in that section.

**Rows 1–3 (and the header, and row 4's cell text) are character for character the preceding entry's.**
Not retyped — extracted from the H5a entry programmatically, re-inserted, and **diffed line by line**
against the source: `rows in new entry: 5 old: 5`, all five `SAME`. **The table is four rows wide. No
fifth number is minted.** Row 3 is stated as H4 Statistics' and is not folded in.

**Row 4's re-derivation, `1 → 0 → 1`.**

- **The named dependency:** a non-numeric recorded column vanishing between the write and `aggregate`.
- **It meets all nine**, because all nine record through one request step whose payload carries `valid`
  (a bool), `invalid_reason` and `finish_reason` (strings) — quoted from the analysis' own § The request
  step, and the *"one request step"* fact is this section's own, in the 2026-08-20 correction.
- **Reached in the analysis' own shown `aggregate`, not merely in principle:** its first statement is
  `rows = [r for r in units if r.get("valid")]`, so with `valid` dropped that filter selects nothing and
  every binary metric returns `None` for a run in which every unit answered. Under
  `output.kind: probability` the same defect is louder: `units.truth` is a bool column, and a column no
  row holds is `E-STEP-COLUMN-UNKNOWN`, contained as `W-STATS-AGGREGATE-FAILED`, costing the whole
  `derived` mapping.
- **The set arithmetic, shown rather than asserted:** E5 is the only config in neither row 2's six
  (E3, E4, E6, C1, C2, C3) nor row 3's seven (E1, E2, E4, E6, C1, C2, C3) — so the `1` is E5, and the
  dependency this slice closes was in neither row and met all nine, E5 included. Hence `0` from H5a's
  landing until this slice, and `1` again now.
- **The published figure named and replaced:** the entry above, dated 2026-08-22 against `71f3c6e`, left
  row 4 at `1` **while its own closing paragraph named the dependency that falsified it**. This entry
  says so and appends; it edits nothing.
- **Row 4's cell text is repeated unchanged, and the entry says why that is not a no-op:** same
  character, different derivation, and the earlier entry is where the wrong one was published.

**This slice's own four stoppages were checked against the nine before the row was written, and none is
met** — reported in the entry: `grep -c '"by"'` over the analysis → **0** (and every `report_by` target
it declares is a declared **attribute**), so `W-STATS-STRATUM-SHADOWED` cannot fire; no `aggregate` return
key (`sensitivity`, `specificity`, `ppv`, `invalid_rate`, `auroc`, `brier`, `cost_usd`) collides with a
recorded column (`pred`, `prob`, `truth`, `valid`, `invalid_reason`, `prompt_tokens`,
`completion_tokens`, `reasoning_tokens`, `latency_ms`, `attempts`, `finish_reason`); and the
contained-raise case is not met, because the shown `aggregate` reads `r.get("valid")` rather than indexing
and one `io.record` call writes every payload key for a unit.

**The pre-emption question, decided and named as decided.** E5's `"truth": unit.consensus_label` against
the E-family's declared `truth` attribute is `E-STEP-KEY-COLLISION` — an **analysis-side obligation**,
fixable by renaming one key with no change to core, named separately and changing no core-side count, the
treatment the H8a entry gave E3's `summary`-step obligation. **What was established and what was not** is
in the entry: the payload, the attribute list and the `aggregate` body were **quoted**; **the plugin was
never run, because it does not exist.**

**The two things the corrections require, in the entry's own words:** do not quote a single figure —
quote the table; and name the dependency (`io.reuse_from`'s plugin-side call for six, the `report_by`
gap for seven, the non-numeric drop for nine before this slice and none after, and 8 of 8 validating
clean as the only figure `validate` can see). The entry adds one observation of its own: row 4's wrong
`1` is the first figure this analysis got wrong by **repeating a table** rather than by rewriting a
phrase — character-for-character repetition protects a row from drift and not from having been wrong when
it was written.

**Mechanical pass on this file in full:** `MECHANICAL: clean (1 files checked)`; the two same-date
headings produce distinct anchors (`…-71f3c6e--after-h5a` vs `…-56aad22--after-h5b`), verified by
computing both slugs; `grep -nE '[0-9] ?x ?[0-9]'` over the new entry → 0.

---

## The per-code emit-site check — all four, re-derived by grep

**One row per code, covering every emit site.**

| Code | Emit sites (`grep -rn` over `src/publishable/`) | Row(s) | Verdict |
|---|---|---|---|
| `W-STATS-REPEATS-DISAGREE` | **1** — `cli.py:2934`. The other hit (`cli.py:3307`) is a comment | one § Warnings row, `reference.md:394` | Row says *"once per (condition, step, recorded column)"*; the site sits inside `for column, units_count in repeats_disagreeing(...).items()` — **per column, as Ruling 6 requires** |
| `W-STATS-COLUMN-THIN` | **1** — `cli.py:3333`. Other hits (`cli.py:1200`, `:3284`) are comments | one § Warnings row, `reference.md:387` | Row says per (condition, step, recorded column) and names `limits.min_reported_n`; the site sits inside `for column in sorted(recorded_columns)` under the floor check — matches |
| `W-STATS-STRATUM-SHADOWED` | **1** — `cli.py:3603`. The two `report.py` hits (`:91`, `:112`) are docstrings, not emit sites | one § Warnings row, `reference.md:399` | Row covers a `by` column **whatever it holds**, over all three of Ruling 1's mixtures; the site is `if "by" in recorded_columns` — one site, and the row claims no granularity it does not have |
| `E-STEP-KEY-COLLISION` | **8** — `stats.py:3262` (reserved metric name `by`), `stats.py:3270` (derived vs recorded column), `artifacts.py:746`/`778` (recorded `unit`), `:752`/`797` (recorded `measurement`), `:760`/`805` (recorded column shadowing a declared attribute) — each of the last three in both the measured and the unmeasured branch of `io.record` | one row, `reference.md:1118`, plus § Steps and artifacts' reserved-`by` paragraph (`:1249`) and `:1004` | The row's **five** collision phrases — *derived key against a recorded column · derived key taking the reserved name `by` · recorded column against a unit attribute · recorded column named `unit` · one named `measurement`* — cover all eight, with the two branches collapsing pairwise. **No row change owed**; the same sites see a wider input |

---

## Disagreements

**Five, and two of them changed what shipped.**

1. **The moving-key enumeration is NINE classes, not the eight the brief prescribes.** Task 15's brief
   says *"Add the eighth moving-key class"*; **Ruling 8** (second set, binding) and the batch-2 review's
   M7 establish the `report_by` stratum path as a **ninth**, with arm G added for it and a third distinct
   `resample_draws` literal. The brief predates Ruling 8. `CLAUDE.md` states nine — *an enumeration that
   omits a class is the carried-summary failure in miniature*, which is § Corrections 16's own sentence.
2. **TWO warnings are minted, not one.** The brief says *"one warning is MINTED,
   `W-STATS-REPEATS-DISAGREE`"*; Ruling 5 minted **`W-STATS-COLUMN-THIN`** in batch 2, after the brief
   was written. `CLAUDE.md` names both. Verified by grep: two codes, two § Warnings rows, one emit site
   each.
3. **Three different task counts for H5b, and the entry states the shipped one.** The spine says
   **(10)**, the design says **15** (*"The scoping's 15 stand"*), the plan ships **16**
   (`grep -c '^## Task '` → 16). The brief says 16, which is right; the design's 15 is a fourth figure
   nobody reconciled and the spine append names both disagreements.
4. **A shipped docstring contradicts itself about its own literal's ordinal.** Arm G's docstring
   (`tests/test_cli.py`) says `1927` is *"the **fourth** distinct such literal measured in this slice"*
   in its prose and *"The third distinct `resample_draws` literal of this slice"* in the inline comment
   twenty lines below. Four is right (`1998`, `1999`, `1997`, `1927`). **Not fixed here** — this batch
   touches no test file, and a records task editing a pin arm's docstring is indistinguishable from
   weakening it. Reported for the whole-branch gate.
5. **The brief's *"`grep -rF` over the four documents"* sweep shape cannot find a line-wrapped phrase**,
   and two of this task's own removal-sweep strings are line-wrapped in the analysis. Re-run
   newline-insensitively; both surviving hits are in a dated entry and are correctly superseded rather
   than edited. Reported because the sweep instruction as written would have returned a clean `0` for a
   string that is present — the same shape the batch-3 ledger already records.

**What I grepped for every claim I make about other tests, rows or code** (rather than a count):
`W-STATS-REPEATS-DISAGREE`, `W-STATS-COLUMN-THIN`, `W-STATS-STRATUM-SHADOWED`, `E-STEP-KEY-COLLISION`
over `src/publishable/` and `docs/reference.md`; `uv_lock_hash` and `ROW_LABELS` over
`src/publishable/`; `"by"` and `report_by` over the analysis; `arm [A-G]` over `tests/test_cli.py` and
`tests/test_stats.py`; `1999`/`1997` over `tests/` (**absent — neither is pinned**, which is why
`CLAUDE.md` labels the four literals by where each was measured rather than implying all four are
pinned); `H5b` over `CLAUDE.md` and `docs/superpowers/spec-defects.md`;
`STRUCK 2026-08-22 (H5b task 11)` (2 lines, both task 11's);
`grep -c '^## Task '` over the plan. The `test_h8b_fixture_l_…` name in the H9 filing was grepped **after**
I first wrote it wrong, which is how the wrong name was caught.

## Concerns

1. **Arm G's docstring ordinal (disagreement 4)** is the only claim defect I found and deliberately did
   not fix. It wants the whole-branch gate or a one-line follow-up, not a records task.
2. **Task 16's pinned sha is `56aad22`, task 15's commit**, not task 16's own (`da31016`) — an entry
   cannot pin the commit that contains it. The entry says which tree the pin names and that no
   executable file moves between them; if the reviewer prefers the batch-4 tip (`f84c7da`) that is a
   one-word change with the same meaning.
3. **The consolidated re-owner note (step 3b) is out of brief.** It is filed rather than silent because
   the advisor's reading is right that five entries' *reasons* go stale at merge, and because the
   precedent for one appended note over five edits already exists in this file. If the controller judges
   it premature — H5b has not merged to `main` yet — the honest fix is another appended line, not an
   edit.
4. **No `src/` or `tests/` file moved in this batch**, so the suite figure is evidence about the branch
   rather than about these two commits; that is stated rather than implied.

---

## Fix round, 2026-08-22 — appended after an advisory review, editing nothing above

Commit `<this round>`. No test file, no `src/` file, no gate figure moves.

**1. The H9 filing's reproduce was a scratch path, and a scratch path is not a reproduce.** The filing
cited a session-scoped file under `/private/tmp/.../scratchpad/`, which will not exist for a reader —
every other reproduce in `spec-defects.md` is a direct call, a grep, or a shipped test name. The recipe
is now **inlined as executable text**: the `build` call, the two lockfile writes with the package pin
that moves, the two commits (a `uv.lock` must be committed *before* each run or the row takes
`not captured` rather than `DIFFERS` — stated, because it is the part that silently defeats the recipe),
the two `run`s, `command_diff(a, b)`, and the assertion whose **passing** is the gap. It also names the
import trap I hit myself: `command_diff` is `publishable.diff`'s, not `publishable.cli`'s.

**2. Two claims in task 16's row-4 paragraph were derived rather than run, and both are narrowed.**

- **The `units.truth` / `E-STEP-COLUMN-UNKNOWN` clause is DELETED, not rewritten.** It was reasoned from
  the code path and it is very likely **false**: `truth` is a **declared attribute** in the E-family, and
  `cli._attributed` merges each unit's declared attributes into the rows `aggregate` receives — read at
  `src/publishable/cli.py:721`, whose own docstring says the roster is merged in *"at the one boundary
  where `aggregate` is called"* — so `units.truth` can resolve from the attribute regardless of the
  recorded column. The `r.get("valid")` half carries the whole argument alone. *Prefer deleting a claim
  to rewriting it*, and this one sat in the paragraph justifying a corrected published figure, which is
  where this analysis' wrong claims have historically lived.
- **"one `io.record` call writes every payload key for a unit, so an admitted row carries every column
  the others do"** overstated what the shown code shows. Narrowed to *the shown step has exactly one
  `io.record` call site, writing a fixed key set — so nothing in the code this analysis shows indexes a
  column some rows may lack.*

**3. The `CLAUDE.md` invariant edit is now checked against the CODE, not against `reference.md`'s prose.**
A document sentence agreeing with my sentence is not the code agreeing. Read at
`src/publishable/stats.py`: `collapse_repeats`'s docstring — *"`_gather_repeats` decides which units are
admitted and **carries every value, raw**"* — and `_across_repeats`, which writes **`None` rather than
omitting the key** precisely so the column stays visible in `summarize_step`'s `columns`. So *"the table
carries every recorded column"* is true of the collapse, and *"beside every declared unit attribute"* is
true of `_attributed`. Both halves of the invariant clause hold against the code.

**4. The slugger my mechanical pass depends on is corroborated rather than assumed.** "Clean" is a claim
about my slug function unless it agrees with GitHub's on the shapes this repo uses. The corroboration is
volume: **1,100 relative/anchor links** across the five files resolve under it, including the shapes most
likely to diverge (backticks, parentheses, dots and underscores — e.g.
`## Creating a plugin (`publishable plugin new`)` → `#creating-a-plugin-publishable-plugin-new`, the
target reference.md's own links use). A divergence would surface as a broken anchor rather than as
silence, and there are none.

**5. A sixth disagreement, which belongs in the list rather than only in a count.** The design's
§ The records this slice owes instructs the spine append to record *"its H5b row says '(10)' and this
slice is **15**"*. **I wrote 16 and overrode that instruction**, because 16 is what shipped
(`grep -c '^## Task '` over the plan → 16) and the design's own body says *"The scoping's 15 stand"*
before the plan split one of them. Recorded here as an **overruled brief/design instruction** rather than
as a bare count discrepancy — the append names both figures and which one shipped.

**Re-verified after these edits:** mechanical pass `MECHANICAL: clean (5 files checked)`;
`ruff check` / `ruff format --check` clean; `mypy` clean. No test moved, so the suite figure above stands
(2931 passed, 1 skipped, 2 xfailed).
