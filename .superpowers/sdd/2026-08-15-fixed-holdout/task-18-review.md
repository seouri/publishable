# Task 18 review: Retire `E-DATA-HOLDOUT-UNSUPPORTED`, and the five end-to-end pins

Reviewed `30376a1` (`14944bf..7b0cd14`) against `task-18-brief.md`, `task-18-report.md`, and `CLAUDE.md`.

**Baseline re-measured, not trusted:** `uv run pytest` → **1953 passed, 2 xfailed**, matching the report.
`uv run ruff check .` clean, `uv run mypy` clean (42 files). Every mutation below was reverted by editing
the file back (never `git checkout --`), `__pycache__` deleted between runs, and each revert verified by
**re-running** the affected tests; `git diff --stat` is empty at the end of this review.

`.superpowers/sdd/.gitignore` was found clobbered to a bare `*` again (by `task-brief` for this review, not
by the implementer) and restored; this file needs `git add -f`.

---

## Verdict 1 — Spec compliance: ✅

The retirement itself is complete and correct.

- `_check_unimplemented`'s `for field, code in (...)` loop and its `if units.get(field):` body are gone; the
  only `-UNSUPPORTED` codes left anywhere in `src/` are `E-DATA-RESOLVER-UNSUPPORTED` (validate.py:3550) and
  `E-STATS-NULLTEST-UNSUPPORTED` (validate.py:3627). **Verified** by `grep -rno '"E-[A-Z-]*-UNSUPPORTED"' src/`.
  No other family member was collaterally retired.
- **`holdout` is still refused as a repeat KIND.** `REJECTED_KINDS` holds all five names the `CLAUDE.md`
  invariant lists (`bootstrap`, `permutation`, `technical`, `biological`, `holdout`). **Verified by probe:**
  deleting the `holdout` entry made `test_a_holdout_repeat_kind_still_routes_to_the_built_field` FAIL on the
  message assertion; reverted and re-run green.
- **The sweep.** `grep -rn 'E-DATA-HOLDOUT-UNSUPPORTED'` over the repo, filtering the *file list* and not the
  output, leaves: the deliberate `not in` pin (`tests/test_validate.py:917`), two descriptive mentions in
  `tests/test_cli.py`, `docs/superpowers/**` (never retro-edited), and `docs/feasibility-llm-growth-studies.md`
  (see disagreement 4). § Errors carries no row for the code and never did; the `E-DATA-HOLDOUT-*` rows are all
  present. The § CLI reference `Status` column names no holdout-related row. `README.md`,
  `design-principles.md` and `experimental-designs.md` carry no "holdout is unbuilt/refused" claim.
- **The self-maintaining count survives.** § The one config file now says "**Two** declarations above are not
  yet built, and each is marked `NOT BUILT` where it appears", and the fenced schema holds **exactly two**
  `NOT BUILT` markers, on the `{resolver: <name>}` and `null_test` lines. The count was not replaced by an
  enumeration, as the brief required.
- The five closed `holdout` keys the new prose enumerates (`method`, `frac`, `from`, `stratify_by`, `seed`)
  match `envelope.py`'s `LEAF_TYPES` entries exactly.
- "`allocation.json`'s fourth key" is accurate (`artifacts.build_allocation_document`: `arms`/`seed`/`strata`/
  `holdout`).

---

## Verdict 2 — Task quality: ❌

The mechanical work is sound and the three prescribed mutations all reproduce. What fails is the commentary
discipline and two pins that cannot fail: **two false build claims in `src/`**, an internal contradiction
inside the very comment this task rewrote, a same-file contradiction it created by editing one site of a
two-site claim, one brief-mandated end-to-end property that no test in the repo can detect, and one
"deliberate regression pin" that is vacuous while its docstring says it is not. Every one is a small fix.

---

## The re-verification, done rather than trusted

The report claims 28 mentions removed (23 asserts + 5 comments) and every affected test re-checked for
discrimination. **I did not take the blanket `_check_holdout` mutation as sufficient**: the affected tests
assert positive codes from four *different* emit sites, so a pass under a dead `_check_holdout` would be
uninterpretable (CLAUDE.md, "a mutation applied to a proxy"). I mutated each site separately.

### Probe A — `_check_holdout` dead (`return` at the top of the body)

`uv run pytest tests/test_validate.py tests/test_cli.py` → **37 failed**. Of the tests that lost a companion
assertion, these FAILED (i.e. they discriminate on their own):

| Test | Positive code it rests on | Bucket the report put it in |
|---|---|---|
| `test_a_malformed_holdout_declaration_is_refused` (15 params) | `-METHOD`/`-FRAC`/`-FROM`/`-NO-DRAW`/`-SEED` | still asserts something real ✓ |
| `test_a_holdout_stratum_naming_no_declared_attribute_is_refused` | `-STRATIFY-UNKNOWN` | still asserts something real ✓ |
| `test_a_holdout_stratum_that_names_no_attribute_at_all_is_refused` (5 params) | `-STRATIFY-UNKNOWN` | ✓ |
| `test_a_holdout_stratum_naming_the_measurement_axis_is_refused` | `-STRATIFY-UNKNOWN` | ✓ |
| `test_a_holdout_beside_a_fold_repeat_is_refused` | `-FOLD` | ✓ |
| `test_a_by_attribute_holdout_column_must_hold_exactly_train_and_test` (4 params) | `-VALUES` | ✓ |
| **`test_a_by_attribute_holdout_column_holding_exactly_the_two_literals_is_accepted`** | `-SEED` | ✓ (**not rewritten** — required sample) |
| `test_a_holdout_stratum_must_be_constant_within_a_cluster[varies]` | `-STRATIFY-VARIES` | ✓ |
| `test_a_holdout_that_apportions_the_test_side_no_units_is_refused` | `-EMPTY` | ✓ |
| **`test_the_same_frac_over_a_larger_roster_is_accepted`** | `-SEED` | ✓ (**not rewritten** — required sample) |
| **`test_the_empty_test_partition_refusal_is_not_reported_for_a_clustered_split`** | `-SEED` | ✓ (**not rewritten**) |
| **`test_the_empty_test_partition_refusal_is_not_reported_for_a_stratified_split`** | `-SEED` | ✓ (**not rewritten**) |
| `test_the_empty_test_partition_refusal_is_not_stacked_on_a_frac_already_refused` | `-FRAC` | ✓ |

The four bolded rows are the required "at least two the implementer did not rewrite" sample, and then some:
each is an *acceptance* test whose only positive attribution is `E-DATA-HOLDOUT-SEED`, a code only
`_check_holdout` emits — exactly the substitute the task-7 review demanded when it found three controls
resting on `-UNSUPPORTED`. All four FAIL under a dead check.

Tests that **passed** under probe A are all in the report's declared "absence-only, paired with a can-fail
sibling" bucket, and I checked each named sibling exists in the same file and itself fails:
`test_a_well_formed_holdout_declaration_earns_none_of_the_five` (sibling: the malformed parametrize, fails),
`test_a_declared_holdout_stratum_is_accepted` (sibling: the undeclared-name test, fails),
`test_a_holdout_beside_a_seed_repeat_is_not_refused` (sibling: the fold test, fails). **No test silently
became absence-only without a control.**

### Probe B — the cells site dead (`return` at the top of the `allocation`/`groups` block)

`test_a_holdout_beside_a_cell_structure_is_refused` **FAILED** (as did the fold and both-codes twins). Its two
absence-only controls — `test_an_empty_group_axis_alone_does_not_trigger_the_refusal` and
`test_an_evaluation_split_without_a_cell_structure_is_not_refused`, both rewritten by this diff to drop the
`-UNSUPPORTED` framing — pass, which is correct: their named control is now proven can-fail.

### Probe C — the resample-cluster site (`fold_basis(holdout_test if ... else roster)` → `fold_basis(roster)`)

`test_the_resample_cluster_warning_counts_the_holdout_s_test_partition` **FAILED**. It does not merely assert
the warning fires; it discriminates *which roster was counted*. Its sibling
`test_a_holdout_wide_enough_to_keep_the_clusters_does_not_warn` passes, as an absence control should.

### Probe D — the envelope closure (`data.units.holdout` excluded from `_KNOWN_CONTAINERS` descent)

`test_a_misspelled_holdout_child_is_reported` **FAILED** on `E-CONFIG-KEY-UNKNOWN`. The rename from
`..._alongside_the_wholesale_refusal` is honest: what remains is a real, independently-attributed check.

### The four rewrites

All four are genuine, not assertions moved around:

1. `test_holdout_is_refused_on_its_own` → **`test_a_plain_holdout_declaration_is_now_accepted`**. Absence-only
   by nature — but its target *is* the retirement, and it is falsifiable: **verified by probe** (re-adding a
   two-line `if units.get("holdout"): c.error("E-DATA-HOLDOUT-UNSUPPORTED", ...)` to `_check_unimplemented`
   makes it FAIL). The 20-unit roster override is necessary and correctly justified.
2. `test_an_unrelated_unsupported_field_does_not_suppress_a_real_roster_defect` → now asserts
   `E-STATS-NULLTEST-UNSUPPORTED` **and** `E-UNITS-KEY-DUPLICATE`. Two positive codes; the property is intact.
3. `test_every_unsupported_message_defers_rather_than_scolds` → parametrize switched from `units` to
   `overrides` so the second case is `statistics.null_test`. Still asserts a non-empty `-UNSUPPORTED` set and
   the "later slice" wording. Sound.
4. `test_a_misspelled_holdout_child_is_reported` → verified can-fail at probe D.

---

## Findings

### Important

**I1 — `_check_holdout`'s own docstring still describes the loop this commit deleted.**
`src/publishable/validate.py:2726`: *"`holdout: {}` and `holdout: null` declare nothing and partition
nothing; **`_check_unimplemented`'s truthiness test is false for both**, and a misspelled child …"*. There is
no truthiness test on `holdout` in `_check_unimplemented` at HEAD. **Verified** by reading the function at
HEAD and by `grep -rn "_check_unimplemented"`. It survived because the sweep was scoped to the string
`E-DATA-HOLDOUT-UNSUPPORTED` rather than to the *claim* — the exact habit CLAUDE.md names ("sweep for the
claim, not for the file the claim was first noticed in"), and it landed in the very function whose
neighbouring commentary this task rewrote.

**I2 — the rewritten `_check_unimplemented` comment contradicts itself.**
It opens *"No `data.units` sub-field is refused wholesale any more"* and closes, ten lines later,
*"**One `data.units` sub-field remains read by nothing**: a `resolver` source (checked above, under
`E-DATA-RESOLVER-UNSUPPORTED` …)"*. Under the comment's own vocabulary both cannot hold: the resolver source
*is* refused wholesale and the comment says so. The function's docstring (validate.py:3448) states the correct
version — "one `data.units` sub-field … is still read by nothing" — so the opening line is the overreach.
**Verified** by reading both paragraphs of the same comment block at HEAD. Fix: scope the opening to
`data.units`' *blocks* (`allocation`/`assign`, `cluster_by`, `weight_by`, `measurements`, `holdout`), or say
"no `data.units` sub-field **other than a `resolver` source**".

**I3 — `envelope.py` now contradicts itself across 100 lines, created by editing one of two sites.**
The rewritten comment at line 30 says `holdout` is closed one level in *"the same way `resample` was: the
shape was checked ahead of the block's wholesale refusal lifting"*. The comment at line 130, untouched, says
of `resample`: *"— **unlike `holdout` above**, this was deliberately closed *before* that refusal retired, not
after"*. After this commit both blocks were closed before their refusal retired, so "unlike `holdout`" is
false and directly denies the sentence the same diff wrote. **Verified** by reading both sites at HEAD.

**I4 — the brief's pin 1 seed clause is not pinned, and the wiring is mutation-blind.**
The brief required *"its `seed` equals `holdout_seed_for` over the run's own digest"*. The delivered test
asserts `alloc["holdout"]["seed"] == 4321`, the **declared** seed, which never reaches `holdout_seed_for`'s
derivation branch. **Verified by mutation:** replacing `digest` with the literal `"sha256:constant"` at
`cli.py:1517` (`_resolved_holdout(units_decl, roster, digest, clusters)`) leaves the **entire suite green —
1953 passed, 2 xfailed**. `holdout_seed_for` itself is unit-tested (`tests/test_units.py:3631-3642`), so the
function is covered and only the *call-site* wiring is not; a run's auto-derived holdout seed could stop
depending on the run at all and nothing would notice. Reverted and re-verified. One extra assertion on a
config with `seed: auto` closes it.

**I5 — the "deliberate regression pin" cannot fail, and its docstring says it can.**
`tests/test_validate.py:917`, `assert "E-DATA-HOLDOUT-UNSUPPORTED" not in by_code`, sits on `_holdout(None)`
— a config writing `holdout: null`, which the retired refusal's `if units.get(field):` gate never fired on.
**Verified by probe:** with the refusal restored, `test_a_plain_holdout_declaration_is_now_accepted` FAILED
and this test PASSED. So it is a deliberate pin rather than a leftover — but a vacuous one, and its docstring
overclaims: *"Both halves asserted, because the route being correct and **the destination existing** are two
claims"*. The assertion establishes only the route. The destination's existence is genuinely pinned, but by
`test_a_plain_holdout_declaration_is_now_accepted`, which the docstring does not name. Either declare a real
holdout block in this test or point the docstring at the test that actually carries the second claim.

### Minor

**M1 — the same stale "truthiness test" claim in a test docstring.**
`tests/test_validate.py:11320` (`test_an_empty_or_null_holdout_validates_clean`): "`_check_unimplemented`'s
truthiness test is false for both of these". Same defect as I1, same cause.

**M2 — a live false build claim in `src/`, pre-existing but now conspicuous.**
`validate.py`'s `HOLDOUT_METHODS` docstring: "a third named here and realized nowhere would … reach
`units.holdout_for`, which refuses what it cannot draw — **not yet built at this commit; task 10 of this
slice is where it lands**." `holdout_for` is built at `units.py:1295`. **Verified** by grep; introduced at
`638639e` (task 5's fix commit), so it is not this diff's, but this task's own sweep instruction ("`src/`
carries no stale comment") is where it should have been caught, and it is the last commit at which the
sentence could still be read as merely early.

**M3 — `envelope.py:32-33` misattributes the honouring.** "so the slice that honours the block (**task 18**)
reads values whose shape a check already approved." Task 18 retires the refusal; the block is honoured by
tasks 10 and 13–17 (`units.holdout_for`, `cli._resolved_holdout`, `io.units.train`, the denominator
narrowing). Also conflates a task with a slice.

**M4 — a dangling referent in a normative document.** `docs/reference.md` § The one config file: "`data.units.
holdout` left it with **this slice**", where the immediately preceding sibling clause names its slice
("`statistics.resample` left this list with **H4a**"). `reference.md` is not slice-scoped; name H3d.

**M5 — the task-14 pin reads one of five artifacts at random.** `next(doc["run_dir"].rglob("split.json"))`.
**Verified:** the run writes **5** `split.json` files (one per seed repeat: `seed200813058/`, `seed480127828/`,
… ). Collecting all five and asserting they agree costs one line and is the *only* behavioural instrument
available for a mis-siting that re-realizes the partition per repeat off the repeat's RNG — the current
`next()` would catch such a regression only by luck. (It remains true that a same-seed re-realization inside
the loop is invisible; see the task-13 answer below.)

**M6 — the task-15 denominator pin is a guarded loop with no counter.** **Verified live today**: changing the
asserted value to `999` makes the test FAIL, so the body does execute. But **also verified**: changing the
guard key to `metric.get("nn")` leaves the test PASSING with zero assertions executed. If `aggregated` ever
stops carrying a dict `n`, this pin goes silent rather than red. `asserted = False … asserted = True …
assert asserted` closes it. This matters more than usual because this loop is the *substitute* the implementer
chose for the brief's ledger check (disagreement 1).

---

## The three prescribed mutations, re-run rather than trusted

| Mutation (`src/publishable/cli.py`) | Result |
|---|---|
| (a) `execute_plan(units=eval_roster)` → `units=roster` | **Both** new tests FAIL. `..._now_validates_and_runs` on the task-14 `split.json` comparison; `..._max_failed_fraction...` on `assert len(ledger) < _planned_execution_count(doc)` → `assert 5 < 5`, i.e. the guard genuinely does not fire un-narrowed |
| (b) `holdout_train=(…)` → `holdout_train=None` | **Both** FAIL (on `expect_exit`; `io.units.train` raises `E-STEP-UNITS-UNAVAILABLE`) |
| (c) `build_allocation_document(group_axes, holdout_plan)` → drop the arg | `..._now_validates_and_runs` FAILS on `alloc_path.exists()` |

All three reverted in place and re-verified green.

### (a) A check that could not fail — the single-line mutation per added test

| Added/rewritten test | Mutation that makes it fail | Confirmed |
|---|---|---|
| `test_a_declared_holdout_now_validates_and_runs` | drop `holdout_plan` from `build_allocation_document` | yes |
| `test_max_failed_fraction_is_measured_against_the_test_partition` | `units=eval_roster` → `units=roster` | yes |
| `test_a_holdout_repeat_kind_still_routes_to_the_built_field` | delete the `"holdout"` entry from `replication.REJECTED_KINDS` | yes (its *third* assertion is separately vacuous — see I5) |
| `test_a_plain_holdout_declaration_is_now_accepted` | re-add the `if units.get("holdout"): c.error("E-DATA-HOLDOUT-UNSUPPORTED", …)` refusal | yes |
| `test_a_misspelled_holdout_child_is_reported` | exclude `data.units.holdout` from the envelope closure's container descent | yes |

---

## The four disagreements

**1. `executions.jsonl` carries no `n` key — CONFIRMED, and the substitute mostly holds.**
`runner.execute_plan`'s ledger write (runner.py:700-714) emits exactly `step`, `scope`, `condition`, `repeat`,
`status`, `started_at`, `wall_seconds`, `error`. The brief's `record["n"]["resolved"]` could never have
passed. The substitute pins the ruling's two numbers side by side —
`run["provenance"]["units"]["n"] == 20` and every metric's `n.resolved == 4` — and mutation (a) does drive the
metric side to 20, so it discriminates. Two caveats: the brief also wanted `n.completed`/`n.failed` pinned and
only `resolved` survives; and the metric loop is uncountered (M6).

**2. The brief's `_ALWAYS_FAILING_STEP` could never trip the guard — CONFIRMED from the code, not the
docstring, and the replacement genuinely discriminates.** `_units_failed_anywhere` builds
`recording_steps = {r.execution.step_name for r in results if r.execution.scope == "repeat" and r.rows}` and
`continue`s on any step outside that set. A step that raises before `io.record` has `r.rows` empty in every
execution, is never "recording", and contributes nothing to `failed` — so `max_failed_fraction` cannot fire
under either denominator. The replacement (train partition recorded every execution, test partition once)
discriminates: under mutation (a) the guard's assertion failed with `assert 5 < 5`, i.e. the plan ran to its
full length un-narrowed and stops short narrowed. `max_executions: 100` against a 5-execution plan rules out
the other way a plan can stop short. Two residual nits: the report's "3–4 of 4" is stated as a range without
saying why it is not fixed at a pinned seed (it does not matter here — both 3/4 and 4/4 exceed 0.5 and both
3/20 and 4/20 fall short — but the margin should be stated as an argument, not a range); and
`len(ledger) < planned` pins *stopped short*, which is one inference away from *this guard fired*.

**3. The `E-REPL-KIND` test's move to `test_validate.py` — JUSTIFIED.** `write_config`, `_holdout` and
`messages_by_code` are all `test_validate.py`'s, the check is pure validate-time, and it now sits beside
`test_an_unknown_repeat_kind_is_refused_through_validate`. The brief's second half — "the config it
recommends now validates" — **is** carried, but by `test_a_plain_holdout_declaration_is_now_accepted`, not by
this test, whose `holdout: null` config makes its third assertion unfalsifiable (I5). The requirement is met
across two tests; the docstring should say so.

**4. The feasibility-file deferral — CORRECT, and it is a real filing rather than a ledger line.** Every one
of the three `E-DATA-HOLDOUT-UNSUPPORTED` mentions in `docs/feasibility-llm-growth-studies.md` sits at lines
957/961, **inside § Executability on this build**, whose opening reads "Measured on 2026-08-15 against commit
`2fdc957`". A dated measurement is not falsified by later work; procedure step 10 and the append-not-edit
convention both apply, and editing it would destroy the evidence. **Verified** that no undated prose anywhere
else in that file makes the claim, and that task 20 exists in the tracked plan
(`docs/superpowers/plans/2026-08-15-fixed-holdout.md:4363`) with `docs/feasibility-llm-growth-studies.md`
first in its **Files** line and an explicit instruction to say `E-DATA-HOLDOUT-UNSUPPORTED` no longer appears.
The same task also owns `experimental-designs.md`, `reference.md` and `CLAUDE.md`, so CLAUDE.md's
"H3d (`holdout`) then unblocks six" is likewise task 20's, not a gap here.

---

## Task 13's siting: does the end-to-end pin add anything?

**Almost nothing; reading remains the instrument, and the report is right to say so — with one correction.**
A re-realization *inside* a per-condition loop draws the same partition from the same seed and roster, so no
assertion over `allocation.json` can see it. But this run writes **five** `split.json` files (verified), one
per repeat, and the test reads an arbitrary one. Asserting all five agree would rule out one adjacent
mis-siting — a realization drawing off the repeat's own RNG — that the current `next()` cannot see. So the pin
adds the *train/test membership* and *allocation hash* guarantees (real, and mutation-proven) but adds nothing
for "realized once outside every loop", and could cheaply add a little. Separately, the pin does **not** cover
pin 1's seed-derivation clause at all (I4).

---

## Recommended before merge

I1, I2, I3 and M1–M4 are one-line-to-one-sentence comment corrections. I4 wants one assertion on a `seed:
auto` config; I5 wants either a declared holdout block in the `E-REPL-KIND` test or an honest docstring; M5
and M6 are one line each. None requires rework of the retirement itself.
