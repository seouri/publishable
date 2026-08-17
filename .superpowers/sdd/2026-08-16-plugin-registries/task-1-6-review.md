# Tasks 1-6 review — H7b Part A documentation debt

Reviewed at `208dfc8` on branch `h7b-registries`, against the six briefs, the report, the design
(`docs/superpowers/specs/2026-08-16-plugin-registries-design.md`), the plan's tasks 7, 8, 13, 14, 15,
16 and 17, and `CLAUDE.md`.

**Gates, re-run rather than trusted:** `uv run pytest` → **2000 passed, 2 xfailed**;
`uv run ruff check .` → all checks passed; `uv run ruff format --check .` → 76 files already
formatted; `uv run mypy` → no issues in 43 source files. All match the report.

**Mechanical pass, run as a throwaway script over the four documents and `spec-defects.md`:** every
relative link and `#anchor` resolves (one unchecked cross-file anchor, `../README.md#is-this-for-you`,
verified by hand); no duplicate heading anchors; every table row matches its header's column count
(pipe-split respecting `\|`); no trailing whitespace, tab, NBSP or zero-width character anywhere,
inside fences or out. Clean.

**Cross-document pass:** the sweep for `four registries` / `Four registries` / `four plugin
registries` / `four entry-point groups` over README, `design-principles.md`,
`experimental-designs.md`, `reference.md`, `CLAUDE.md` and the feasibility analysis returns exactly
one live hit — `CLAUDE.md` line 275 (see gap (a) below). Control: the same sweep for `registries`
returns strictly more (8 in `reference.md`, 1 in `CLAUDE.md`). Config completeness, enum comments and
declared-vs-derived: task 5's line is the only enum touched and it is verified below against a real
generated config.

---

## Verdicts

| Task | Spec compliance | Task quality |
|---|---|---|
| 1 | **Pass with reservations** — four rows minted as the brief specified; § Validation untouched (confirmed by diff); `E-PROBE-UNKNOWN` verified true of plan task 13's `_check_probe` (metadata-only, reported at path `experiment_type`, silent when the template declares none) | **Pass with reservations** — the `bbfe9d7` self-correction was right to make; but the placement violates the sort the correction's own argument asserts, and one row carries a positional locator that is now false |
| 2 | **Fail** — `E-PLUGIN-COLLISION`'s row states a message and a mechanism that are false of one of the two conditions it enumerates (I1); the code it mints will be reported by `validate` with no row in the table that governs what `validate` reports (I2); and two rows describe emit sites no task in Part A *or* Part B builds, in flat present tense (I4). The Fail rests on I1 and I2, which are falsehoods about behaviour the plan does build | **Pass with reservations** — both count phrases the brief named were correctly left alone and verified; three *other* count phrases in the table the task edited were not checked and are now stale |
| 3 | **Fail** — the fifth group, fifth decorator, TOML block, row split and defects entry all land as specified, but the sentence added to justify them states a refusal at a time, and under a code, that plan task 15 explicitly does not build and says should not exist | **Pass with reservations** — the `spec-defects.md` filing is genuinely novel (verified), and the sweeps were run; the entry's heading claims a strike its own body says has not happened |
| 4 | **Pass** — `plugins.py` marked `— not yet built` and `src/publishable/plugins.py` verified absent, so the marker is on the specification side of `CLAUDE.md`'s line; tree alignment matches its `manifest.py` neighbour exactly; deferral of the retirement to task 7 matches task 7 step 5 | **Pass with reservations** — the added § The importable surface paragraph closes on an analogy that does not hold |
| 5 | **Pass** — verified end to end: a real `publishable generate experiment` at HEAD writes `from: index.csv                # index.csv \| {glob: "*.dcm"} \| {resolver: <name>} (NOT BUILT)`, byte-identical to § The one config file's line; `E-DATA-RESOLVER-UNSUPPORTED` still live (5 sites in `src/`); the deleted clause leaves exactly one surviving `no entry point is resolved in this build`, in `E-TEMPLATE-UNKNOWN`'s row, which is task 11's | **Pass** — the prescribed mutation was re-run by me: dropping the second fragment fails `test_the_generated_units_block_carries_its_comments` at line 177 and nothing else; reverted by editing back and re-verified green (22 passed) |
| 6 | **Pass** — probe re-run at HEAD, not at `ba87aae`: exit 0, `plugin: null` in the generated config, `grep -rn "uv add" src/` → 0 hits, control `grep -rln "uv_lock" src/` → `cli.py`, `uv_support.py`. All three markings are honest and the `Status` cell for `generate` correctly stays `built` | **Pass with reservations** — "the flag parses and is dropped" is true of the mechanism but overstates recognition (see Minor below) |

---

## Findings

### Critical

**C1 — task 3. The sentence minting the fifth group states a refusal that will not exist.**
`reference.md` § Creating a plugin now ends the "Five registries" paragraph with: *"A writer
registered without its reader is refused **at load** for that reason, the same breath in which a
suffix core already writes is."* Plan task 15 builds the opposite on all three counts: the refusal is
raised **at the read** (`StepIO._read`), under **`E-ARTIFACT-UNREADABLE`** (an `ArtifactError`, minted
by task 15 in § Errors core raises), and task 15's own step 8 states — as a design consequence, not a
gap — *"The invariant is enforced at the read, not at registration … a registration-time check would
have to know whether the reader is merely registered later in the same module, which it cannot.
**nothing closes it and nothing should.**"* The core-suffix claim it is paired with *is* a
registration-time `ContractError · E-PLUGIN-COLLISION` (task 14), so "the same breath" glosses two
different mechanisms, two different times and two different codes as one. **Verified by** reading plan
task 15 steps 3, 4 and 8 and task 14 step 3 against the sentence. This is the repo's signature defect —
prose claiming a guarantee the code does not provide — and it is load-bearing, because it is the
sentence that justifies minting the group.

### Important

**I1 — task 2. `E-PLUGIN-COLLISION`'s row is false of one of the two conditions it enumerates.** The
row covers *"One entry-point key claimed by two installed distributions … **or a writer claiming a
suffix core itself writes**"*, then asserts of the whole: *"Decided over the **complete** claim set for
the group and reported in **name order** … The message names every distribution that claimed the key,
as `<distribution> <version>`, which is what a reader uninstalls."* Plan task 14's `register_writer`
raise is `if suffix in CORE_SUFFIXES:` with the message *"a writer claims `.csv`, which core itself
writes … Claim a suffix of your own"* — no claim set, no name order, **no distribution named**, and
the remedy is renaming rather than uninstalling. The first half of the row is true of task 8's
`_check_plugin_collisions` (I verified `scan_group` returns keys in name order and claimants in
provider order, plan task 7 step 3), so only the writer arm is wrong. **Verified by** reading plan task
14's decorator body and task 8 step 5 against the row.

**I2 — task 2. `E-PLUGIN-COLLISION` will be reported by `validate` and has no row in § Errors
`validate` reports.** That section's preamble defines itself as *"the codes a **command** reports, and
a code raised at load can be in both, reported here and raised there"*, and every other dual-surface
code (`E-TEMPLATE-COLLISION`, `E-TEMPLATE-LOAD`, `E-DATA-CLUSTER-UNKNOWN`, `E-DATA-WEIGHT-INVALID`)
carries a row in each table and says it is dual-surface. Plan task 8 adds
`validate._check_plugin_collisions`, which calls `c.error("E-PLUGIN-COLLISION", …)` — a finding, not a
raise — and task 8 step 6 amends only `E-TEMPLATE-COLLISION`'s row. No task in the plan gives
`E-PLUGIN-COLLISION` a validate-side row. A reader who sees the code in `validate` output and looks it
up in the table that governs `validate` output finds nothing, and the row they do find describes a
`ContractError`. This is mandate 2 read forward: **a new code that will need a second row later.**
**Verified by** grepping the plan for every `E-PLUGIN-COLLISION` occurrence (lines 207, 1218, 1349-1385,
1522, 2719-2854, 3020-3080) and reading task 8 step 6.

**I3 — task 2. Three count phrases in the edited table are now stale.** § Errors core raises says, in
`E-TEMPLATE-COLLISION`'s row, *"One of **three** load-time raises, beside
`E-STEP-NAME-COLLISION`/`E-STEP-SCOPE-UNKNOWN` and `E-TEMPLATE-LOAD`"*; in `E-TEMPLATE-LOAD`'s row,
*"The **third** of the load-time raises"*; and in the paragraph beneath the table, *"like the **three**
load-time rows (`E-STEP-NAME-COLLISION`/`E-STEP-SCOPE-UNKNOWN`, `E-TEMPLATE-COLLISION`,
`E-TEMPLATE-LOAD`)"*. Task 2 inserted three rows into that table whose faults are all met before any
step exists — `E-PLUGIN-LOAD` is by definition an import failure, `E-PLUGIN-DECORATOR` is reached
"where the object behind a key is actually loaded", and `E-PLUGIN-COLLISION`'s writer arm is raised
when a plugin module executes its decorator. The section preamble's own definition of the class is
*"the load-time refusals a command meets before any step exists"*. The brief told the implementer to
insert here and `CLAUDE.md` says *"when you insert or remove a row, check every row it moved, and every
count phrase near it"*; the report checked the two count phrases the brief named (both correctly
unchanged — I verified `validate.py`:534's "two codes" comment and § Errors `validate` reports' "That
is five *codes*") and did not check these three. **Verified by** `grep -n "load-time" docs/reference.md`
and reading all four hits.

Checked one at a time against the preamble's definition — *a refusal a command meets before any step
exists*, paired in the post-table paragraph with "none … is raised inside an execution, so it stops the
run instead of failing one step" — **all three of the new rows qualify**: `E-PLUGIN-LOAD` is an entry
point failing to import; `E-PLUGIN-DECORATOR` fires where the object behind a key is loaded;
`E-PLUGIN-COLLISION`'s writer arm fires when a plugin module executes its `@register_writer`. **The
corrected count is six, not three**, and the enumerations should read `E-STEP-NAME-COLLISION` /
`E-STEP-SCOPE-UNKNOWN`, `E-TEMPLATE-COLLISION`, `E-TEMPLATE-LOAD`, `E-PLUGIN-COLLISION`,
`E-PLUGIN-DECORATOR`, `E-PLUGIN-LOAD`. **Whose:** task 2 inserted the rows, so the omission is task 2's;
but task 8 lands `_check_plugin_collisions` and touches this same table, so the recount is cheapest
there and task 8 should own the edit rather than repeat it.

**I4 — task 2. `E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` describe emit sites no planned task builds.**
Both rows say, in unhedged present tense, that they are *"Reached … at `run` and `dry-run`"*. Plan task
16 step 7: *"`check_registration` has **no production caller in this slice and no task in Part A or
Part B gives it one**."* The same holds for task 17's containment helper (its brief line: "no
production caller in Part A"). These are the two rows in this batch furthest from being emitted and
they are the two carrying no build-state disclosure, while the three `E-RESOLVER-*` rows — which Part B
*does* emit — carry "Not yet emitted". See the marker judgment below. **Verified by** reading plan task
16 steps 3-7 and the plan's code table at lines 207-210.

**I5 — task 2. `E-TEMPLATE-COLLISION`'s two rows now state different condition sets, undisclosed.**
Step 3 deleted the validate-side row's closing clause but left its opening hedge: *"A template name is
claimed twice **where this build can see both claimants**: two project-local … or a local registration
of a name core itself registers"* — while the § Errors core raises twin now enumerates all five cases
including the three installed ones flatly. The hedge's explanation was the deleted clause, so it now
dangles, and one code's two rows disagree until task 8 step 6 lands. This is structurally the same
interval the implementer *did* flag for `E-TEMPLATE-UNKNOWN` (gap (b)), on a code where § Errors' whole
convention is one row per code; that it went unflagged while its twin was flagged is the finding.
**Verified by** reading both rows at `reference.md`:577 and :1022 and plan task 8 step 6.

**A second site of the same interval, in the same task.** Step 4 replaced § Creating a plugin's
closing sentence *"The two local cases are the ones this build checks … the plugin cases arrive with
entry-point resolution"* with a flat statement of which code each group carries, and the brief
forbade adding a hedge. The paragraph's pre-existing opening — *"Two installed plugins registering
`plate_wells`, a plugin registering `generic` … **all fail at load**, naming both providers"* — was
carried by that removed sentence and now stands unqualified (`reference.md`:3435). Until task 8, no
installed claim reaches any merge. The brief's instruction was defensible (task 5 owned the sweep,
task 8 owns the check) but the effect is that the same interval is undisclosed at two sites, not one.

**I6 — task 3. The new sentence cites, as its authority, a passage that contradicts it.** The added
clause is *"[`io.write` dispatches on the writer table and `io.read_upstream` indexes the reader
table](#steps-and-artifacts)"*. § Steps and artifacts still reads *"Every reader — `io.read_upstream`,
`io.read_condition`, `io.reuse_from`, `io.read_input` — **inverts the same table**"* — which is the
exact false claim the `spec-defects.md` entry this task filed quotes as the defect. No task in the plan
amends that sentence: task 15 corrects `_read`'s **docstring** and adds the § Errors row, and its
`reference.md` edits stop there. So the document will contain both statements after the slice.
**Verified by** reading `reference.md`:1095 and plan task 15 steps 3-4.

**I7 — task 3. The `spec-defects.md` entry is headed `STRUCK` while its body says it is not struck.**
*"**Closed by specification** … The code is owed by tasks 14 and 15 of the same slice; this entry is
struck when task 15 lands, not before."* Every other heading in that file uses `OPEN`, `CLOSED`,
`CONFIRMED CLOSED` or `MARKED FOR THE NEXT SLICE`; `STRUCK` appears once, in this entry, and
`CLAUDE.md` treats striking as what a *closed* gap gets. A reader scanning headings for live gaps —
which is what the file is for — will not see this one. The brief prescribed the wording, so the defect
is upstream, but it landed here. **Verified by** `grep -n "^## " docs/superpowers/spec-defects.md`.

### Minor

**M1 — task 1. The four rows' placement violates the sort the correction's own argument asserts.** The
report justifies `bbfe9d7` by "the table is sorted by code prefix throughout: CONFIG → CRED → DATA →
ENTRYPOINT → HYPOTHESIS → META → NAME → PARAM → REPL → STATS → SWEEP → TEMPLATE → UNITS". I extracted
all 123 code cells in file order and that sort holds exactly. Under it, `E-PROBE-UNKNOWN` belongs
between PARAM and REPL and the three `E-RESOLVER-*` between REPL and STATS; they sit between TEMPLATE
and UNITS. Keeping the `E-TEMPLATE-*` family contiguous was right; the new block's own position is not
what the stated rule gives. Not worth another move on its own, but the grounds as written are
self-falsifying and task 8's author is being pointed at them.

**M2 — task 1. A positional locator inside `E-RESOLVER-MEASUREMENT-FIELD`'s row is false.** It reads
*"Separate from the attribute check **next to it**"*. The attribute check is `E-UNITS-ATTR-MISSING`,
which is now three rows away (`…-MEASUREMENT-FIELD`, `…-SWEPT-PARAM`, `E-PROBE-UNKNOWN`,
`E-UNITS-ATTR-MISSING`). `CLAUDE.md` names locating a row by position as a repeated, twice-wrong habit.
Name what the sibling *does* instead.

**M3 — task 2. The added early-return sentence mischaracterises two of the three codes it names.** *"The
identifiers a plugin registry mints for its other groups (`E-PLUGIN-COLLISION`, `E-PLUGIN-DECORATOR`,
`E-PLUGIN-LOAD`) are **reported by checks that do not return early**"* — true of `E-PLUGIN-COLLISION`
(task 8 adds a non-returning `validate` check); false of the other two, which `validate` does not
report at all, as their own rows say two sections later (*"`validate` cannot see this disagreement"*).
The conclusion — none reaches the five — is right; the reason given for two of them is not.

**M4 — task 4. The closing analogy in the new § The importable surface paragraph does not hold.**
*"That is the same boundary `cfg` and `io` sit on: constructed by core, handed to you, never
imported."* `cfg` and `io` are handed to your `run`; the entry-point scan is handed to you never — it
is core's internal machinery. The paragraph's own preceding sentence already makes the correct point
("reaches you through no import at all"); the analogy weakens it by asserting a similarity that is half
false.

**M5 — task 6. "`experiment` accepts `--plugin` (NOT BUILT — the flag parses and is dropped)"
overstates recognition.** `cli._dispatch_generate` collects *any* `--key value` pair into an `opts`
dict and reads only `template`, `input-dir`, `output-dir`, `name`. I probed it: `generate experiment p3
--template generic --nonsense-flag zzz …` also exits 0 and scaffolds. So `--plugin` is not accepted in
any sense specific to it — it is one instance of every unknown option being silently swallowed. The
marking is not false (the flag does parse in the loose sense, and is dropped), and correcting it is not
this task's job, but "accepts `--plugin`" reads as recognition the CLI does not have. Worth a line in
task 18's brief, which will make the recognition real.

---

## The build-state marker asymmetry — a principled difference, misapplied twice

The report's premise is wrong: it states that "task 1's four new rows (`E-RESOLVER-*`,
`E-PROBE-UNKNOWN`) each carry an explicit **Not yet emitted:** clause." `grep -c "Not yet emitted"
docs/reference.md` → **3**. `E-PROBE-UNKNOWN` carries none, in the brief's prescribed block and in the
landed row. That changes the answer, because it makes the actual line a coherent one:

- rows for codes **this slice emits** (`E-PROBE-UNKNOWN` by task 13, `E-PLUGIN-COLLISION` by tasks 8
  and 14) carry no marker;
- rows for codes only **Part B** emits (the three `E-RESOLVER-*`, tasks 24-26) carry "Not yet emitted".

That is a defensible rule, and it is reinforced by table convention: § Errors `validate` reports has an
established practice of in-row build-state disclosure (nine instances of "in this build" / "not yet
checked" / "specified but not implemented"), while § Errors core raises has one row using the softer
"Temporary … does not exist" and no marker convention at all. Inventing a marker convention mid-slice
in a table that has never had one would be the worse move.

**So: a principled difference, not an inconsistency — except for `E-PLUGIN-DECORATOR` and
`E-PLUGIN-LOAD`, where it is misapplied.** Those two are further from emission than the rows that *are*
marked: no production caller in Part A **or** Part B (plan task 16 step 7 says so outright), yet their
rows assert in flat present tense that they are "Reached … at `run` and `dry-run`". That is finding I4,
and the remedy is a disclosure in those two rows only — not a marker convention for the whole table,
and not markers on `E-PROBE-UNKNOWN` or `E-PLUGIN-COLLISION`.

---

## The two disclosure gaps

**(a) `CLAUDE.md`'s "keep the registered artifacts to the four registries" — real, and it is this
batch's, not out of scope. Owner: task 3.** `CLAUDE.md` § Checking consistency after any `*.md` edit:
*"After removing or renaming any string, grep the four documents, **this file**, and any feasibility
analysis for what should no longer exist."* `CLAUDE.md` is named as in scope for the sweep regardless
of a brief's file list, and the implementer's own sweep found the hit and then declined it on file-list
grounds. My sweep confirms it is the only surviving instance anywhere. **Severity: Important.** Fix in
task 3's lane — one word.

**(b) The `E-TEMPLATE-UNKNOWN` interval between task 5's deletion and task 11's landing — real,
correctly owned by task 11, and correctly handled. Severity: Minor.** Deleting rather than propagating
is right: `CLAUDE.md` records a previous round that closed a false-claim finding by copying the claim
to a second site. I verified the interval is exactly as described — one surviving
`no entry point is resolved in this build`, in `E-TEMPLATE-UNKNOWN`'s row. Naming it as a live interval
is the right treatment and no action is owed here. It should, however, be read beside **I5**, which is
the same shape on a code with **two** rows and was not named.

---

## Things I verified that came back clean

- § Validation untouched by task 1 (`git diff 1c208ac..208dfc8 -- docs/reference.md` shows no hunk in
  it); its no-code-in-the-table convention preserved.
- The `E-TEMPLATE-*` family is contiguous after `bbfe9d7` (positions 109-112 of 123).
- `E-PROBE-UNKNOWN`'s row is true of plan task 13's `_check_probe`: read from metadata, reported at
  path `experiment_type`, and silent when `apparatus_probe` is `None` (its second control test).
- § The importable surface's `Status` column is honest at HEAD: I imported `publishable` and confirmed
  `register_template` is present and `register_reader`/`register_writer`/`register_resolver`/
  `register_probe` are all absent, so "Importing one raises `ImportError` today" survives the row split.
- The `spec-defects.md` filing is genuinely novel — no prior entry covers the `WRITERS`/`READERS` key
  asymmetry (`grep -n "READERS\|read_upstream" docs/superpowers/spec-defects.md`, 20 hits, all other
  subjects).
- Task 5's generated output matches § The one config file byte for byte, verified against a real
  `publishable new` + `generate experiment` at HEAD rather than against the fixture.
- Task 5's prescribed mutation re-run by me and confirmed discriminating (one test red, at the
  three-value literal); reverted by editing the file back, `__pycache__` cleared, suite green.
- Only `materialize.py` and `test_materialize.py` changed under `src/` and `tests/` across all six
  tasks — no unintended production change.
- `.superpowers/sdd/.gitignore` was found clobbered to a bare `*` (the known `sdd-workspace` behaviour)
  and restored from `HEAD` during this review.
