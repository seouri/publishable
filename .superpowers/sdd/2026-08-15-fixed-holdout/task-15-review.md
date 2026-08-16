# Task 15 review: the denominators — six sites narrowed, two deliberately not

Reviewed at `fa85b26` against `d4f17d0..fa85b26`. Baseline before any mutation of mine:
`uv run pytest` → **1942 passed, 2 xfailed** (103 s).

## Verdicts

1. **Spec compliance: ✅** — exactly six call sites narrowed and no seventh; `provenance.units.n`
   and `units_hash` still read the whole `roster`; the three key-indexed maps stay whole and the
   analogy that justifies them holds in the code, not merely by pattern; `_evaluation_roster`
   returns the same object with no holdout and preserves roster order; every new test is
   mutation-sensitive except one, which is a quality finding rather than a compliance one.
2. **Task quality: ❌** — two false-guarantee findings (one in the shipped docstring, one this task
   staled in `spec-defects.md`) and one test that passes vacuously. Nothing ships a wrong number.

The ❌ does **not** rest on the letter of the brief's step 5(a): something genuinely did fail under
mutation (a), so the implementer's reading of it is defensible. It rests on the guarantee that
mutation was supposed to check, which is false, and which I proved two independent ways.

---

## Adjudication: the two "structurally inert" claims

**Both CONFIRMED**, by construction, not by reading. Script:
`scratchpad/inert.py`, run under `uv run python`.

### Site 2 — `_condition_beside_n` — CONFIRMED inert

Built a 10-unit roster with a `group` attribute and an `eval_roster` = `{u8, u9}` under an 8/2
`HoldoutPlan`, and called `_condition_beside_n(beside_n, whole, 0, amm)` against
`_condition_beside_n(beside_n, eval, 0, amm)` for four `arm_members_map` shapes: `None`, an arm map
covering the whole roster, one covering training units only, one covering the test units only.
**Output identical in all four**, `technical_n` included:

| `arm_members_map` | whole | eval |
|---|---|---|
| `None` | `technical_n` kept | `technical_n` kept |
| all keys / train-only / test-only | `technical_n` dropped | `technical_n` dropped |

The reason is stronger than "the roster is not read": `_condition_beside_n` is
`_cond_beside_n(beside_n, _cond_roster(roster, cond_index, arm_members_map), roster)` —
**both sides of the identity test come from the same argument**, so the answer is a function of
`arm_members_map is None` alone. `_arm_keys` intersects rather than raising on a narrowed key set
(`runner.py` `_arm_keys`: `set(arm_members[i]) & keys`), so no exception route makes it observable
either. And `execute_plan` asserts `holdout_train is None or arm_members is None`, so the arm branch
and a holdout cannot co-occur in a run at all.

### Site 5 — `_compute_vs_baseline(roster=)` — CONFIRMED inert, and the stated reason is the whole reason

- Confirmed at this commit: `contrasts.resolve_contrasts` builds
  `Comparison(id=c.label, of=…, against=…, declared=False)` and **never passes `within`**, whose
  dataclass default is `None` (`contrasts.py`, `Comparison.within: dict[str, str] | None = None`).
- `_compute_vs_baseline` → `_baseline_comparisons`, which returns
  `[comp for comp in resolve_contrasts(...) if not comp.declared]` — so only generated comparisons
  reach it, and every one carries `within=None`.
- Its **only** other use of `roster` is the `if roster is None: return None, []` guard, and
  `_evaluation_roster` returns `None` exactly when its input is `None`, so that guard cannot
  distinguish them either.
- By construction: ran it with `whole` vs `eval` over three `doc` shapes — `{}`, one **carrying a
  declared `statistics.contrasts` entry with a `within`** (the arm that could have broken the
  claim), and one with `limits.min_reported_n` — output and members identical in all three.

So the claim is complete, not merely contributing: within `_compute_vs_baseline` there is no other
route by which the roster argument could matter.

### Consequence — no new `spec-defects.md` entry for site 5; site 2 is already filed and its filing is now wrong

- **Site 5: decline a filing, with a reason.** The latent dependency runs in the *safe* direction. If
  `resolve_contrasts` ever sets `within` on a generated comparison, `eval_roster` is already the
  correct argument — there is no failure mode, only dead code becoming live and right. `spec-defects.md`
  is for gaps deliberately left **open**; a permanently unpinnable wiring with no failure mode, already
  recorded in a tracked task report and in a test whose docstring states it, does not belong there.
  Manufacturing an entry with a slice owner would dilute the list.
- **Site 2: already filed**, as the OPEN `technical_n` entry — same function, same mechanism. But that
  entry's remediation sentence is now false because of this task; see Important 2. Correcting it is the
  filing this task owes, and it is better than a parallel entry.

---

## Findings

### Important 1 — `_evaluation_roster`'s docstring claims a guarantee the code does not provide

**Claim (shipped, `src/publishable/cli.py`, `_evaluation_roster` docstring):**

> **The same object, not a copy, when no holdout is declared.** `_cond_beside_n` decides whether
> `technical_n` survives by IDENTITY (`cond_roster is roster`), so a copy here would silently
> withhold it from every run in the build.

**This is false.** `_cond_beside_n`'s only production call site is inside `_condition_beside_n`, which
passes **its own** roster argument as both the source of `cond_roster` and the identity reference. So
`cond_roster is roster` is self-referential and `_evaluation_roster`'s object identity never enters the
decision. A copy is harmless, not dangerous.

**Verified two independent ways:**

1. *By construction* (the site-2 table above): `_condition_beside_n(beside_n, eval, 0, None)` — where
   `eval` is a **different object** from the roster it was derived from — **kept** `technical_n`.
2. *By mutation.* Applied the brief's mutation (a) verbatim
   (`return UnitList(list(roster)) if roster is not None else None`), deleted `__pycache__`, ran the
   full suite: **1 failed, 1941 passed, 2 xfailed** — and the single failure was
   `test_the_evaluation_roster_is_the_test_partition_and_preserves_roster_order` on
   `assert _evaluation_roster(roster, None) is roster`, i.e. the tautological identity assertion added
   by this task. **Nothing about `technical_n` failed**, in the whole suite. Reverted by editing the
   file back, `diff` against a pre-mutation backup reported the file **identical**, and the five
   relevant tests re-run green.

The implementer read that one failure as confirming the docstring. It doesn't: the assertion that
failed is a restatement of the return statement, not of the causal claim. The brief anticipated
exactly this ("If nothing fails … weaken the docstring") and the anticipation was right for a reason
the brief itself did not know.

**The same false claim appears a second time**, in
`tests/test_cli.py::test_the_evaluation_roster_is_the_test_partition_and_preserves_roster_order`'s
docstring ("so returning a copy here would silently withhold it from every unswept run").

**Fix — three sites, and one deliberate non-site:**

- `cli._evaluation_roster` docstring, the "same object, not a copy" paragraph.
- the test's docstring, same sentence.
- the `spec-defects.md` entry (Important 2 — the same mechanism stated from the other end).
- **Do NOT edit the plan** at `docs/superpowers/plans/2026-08-15-fixed-holdout.md` (the same wording
  sits at its task-15 section). That file is the development record; CLAUDE.md forbids retro-editing
  it, and `spec-defects.md` is the single live-list exception. A "complete the sweep" instinct here
  destroys evidence.

**Do not use the brief's own fallback wording verbatim** — "returning the same object is what keeps
this function out of that decision" is still a false mechanism. The accurate statement is: *the
identity `_cond_beside_n` tests is between `_cond_roster`'s return and the roster it was given, both
derived from `_condition_beside_n`'s single roster argument, so which object this function returns
never reaches that decision. The same object is returned because there is nothing to copy, not
because anything downstream depends on it.*

**The `is roster` assertion should stay.** The brief specified identity, the code delivers it, and
pinning a documented return contract is fine. The defect is the justification, not the assertion.

### Important 2 — this task staled `spec-defects.md`'s remediation for the filed `technical_n` gap

`docs/superpowers/spec-defects.md`, OPEN — *`technical_n` is a whole-roster figure beside a
test-partition `n`*:

> The mechanism is cheap when it is wanted: `_cond_beside_n` already takes the un-narrowed roster as
> its third argument and decides by identity.

**Verified false as of this commit.** `grep -n "_cond_beside_n(" src/publishable/cli.py` returns one
production call, line 691, and its third argument is `_condition_beside_n`'s own `roster` parameter —
which `command_run` now passes as **`eval_roster`**. After this task the third argument is the
*narrowed* roster, so the identity check can no longer see a holdout narrowing, and the filed fix no
longer works as written. Closing that gap now additionally requires `command_run` to thread the
un-narrowed `roster` through as a separate identity reference (a fourth parameter on
`_condition_beside_n`, or the whole roster passed alongside).

`spec-defects.md` is the one live list this repo corrects in place. Append the correction to that
entry, saying what it replaces — this is the "sweep for the claim, not for the file the claim was
first noticed in" habit, and the claim moved because of this diff.

### Minor 3 — the site-5 non-pin test passes vacuously

`test_compute_vs_baseline_roster_argument_never_affects_the_auto_generated_family` asserts only
`_run(roster) == _run(eval_roster)`. It never asserts either side reported anything — the "control
asserting only absences" shape CLAUDE.md names.

**Verified:** inserted `return None, []` immediately after `_compute_vs_baseline`'s
`if roster is None` guard (a one-line early return), deleted `__pycache__`, ran
`pytest -k never_affects` → **1 passed**. The test survives the function computing nothing at all.
Reverted in place; `diff` against the backup identical; re-ran green.

**Fix:** one line — assert the shared output is non-empty and carries the concrete figure, e.g.
`assert _run(roster)[1]["s"]["r"]["n_paired"] == 4` beside the equality.

### Minor 4 — `reproduce` in the provenance comment is imprecise, not false

The new comment at the `provenance["units"]` site ends "…which is what `units_hash` pins and what
`reproduce` checks". `reference.md` § Reproducing on another device enumerates seven steps;
step 3 verifies **`code_hash`**, and `units_hash` appears nowhere in them. § CLI reference marks
`publishable reproduce` **NOT BUILT**, so this is a spec claim, not a build claim — and `reference.md`
line 1220 gives it partial cover: a roster that changes is "*detected* when a reproduction runs, not
prevented". So the tail is loose rather than wrong. Suggest: *"…which is what `units_hash` pins, and
what makes a roster that resolved differently detectable when the run is reproduced."*

The rest of that comment **is** checkable and is sourced from the spec almost verbatim —
`reference.md` § A fixed holdout split: "`provenance.units.n` and `units_hash` stay whole-roster
regardless — they are the roster's identity, not a metric's denominator, which is why `240` there and
`48` in a metric's `n` are two true numbers rather than a contradiction." It states the distinction,
the two concrete numbers, and the consequence of narrowing (a hash over a subset the config never
described). It meets the brief's requirement.

### Minor 5 (non-blocking) — the added `assert eval_roster is not None` is a crash route after the money is spent

The line is beyond the brief but its comment is true and the invariant holds
(`_evaluation_roster` returns `None` only for a `None` roster), so this is not a false-guarantee
finding. Worth one line of awareness only: it sits **after** `execute_plan`, so if that invariant ever
broke, an `AssertionError` there is an uncaught crash with every execution already paid for and no
`run.yaml` — the shape of commit `4b1aebf`'s "the retry CAN raise" finding. Not a restructure this
task should carry.

---

## What I checked and found correct

**Exactly six sites, and nowhere else.** Grepped every `roster` occurrence in `command_run`
(lines 1271–2655). `eval_roster` appears at exactly seven places: the one assignment, the six call
sites named by the brief (`execute_plan(units=…)`, `_condition_beside_n`, `_condition_counts`,
`_condition_report_by_levels`, `_compute_vs_baseline(roster=)`, `_compute_declared_contrasts(roster=)`),
plus the type-narrowing `assert`. Every remaining whole-`roster` read is deliberate:

| Whole-roster read | Why it is right |
|---|---|
| `provenance["units"]["n"]`, `units_hash(roster)` | roster identity, per `reference.md` § A fixed holdout split |
| `holdout_train=UnitList([u for u in roster if u.key in train])` | the training partition **is** the complement; `execute_plan`'s own docstring says "when `holdout_train` is given, `units` is the test partition and `io.units.train` is `holdout_train`" — so site 1 is required wiring, not a choice |
| `weights`, `clusters_of(roster, …)`, `unit_attributes`, `resample_strata` | key-indexed (below) |
| `fold_basis`, fold strata, `build_allocation_document`, `_resolved_group_axes`, `_resolved_holdout` | all partition or record the whole roster by definition; `execute_plan` asserts holdout ⊥ fold and holdout ⊥ arms |
| `technical_n` | filed as an OPEN `spec-defects.md` entry; brief says do not fix here |

**The key-indexed analogy holds — checked in the code, not by pattern.**

- `unit_attributes`: `_attributed` reads `attributes.get(row["unit"], {})` per row of the table, so
  only keys the table carries are looked up. (Implementer's empirical check; confirmed by reading.)
- `resample_strata`: `stats.py` does `pools.setdefault(strata[key], []).append(key)` over the
  **collapsed table's own keys**, and its docstring states the contract — "`strata` is indexed by key,
  not `.get`-ed … must be total". A whole-roster map is a superset of the test partition, so totality
  holds and surplus keys are never indexed. Narrowing would be equally total, and change nothing.
- `weights`: consumed as `weights[k]` over the **completed** units in `runner._counts`, and
  `stats.summarize_step`'s docstring says outright that weights arrive "typically over the whole
  roster". `checked_weights` takes a positional sequence already selected by key, so an invalid
  training-unit weight is never reached — same before and after.

**`_evaluation_roster` drops no state.** `UnitList.__init__(self, units, train=None)` carries exactly
`_units` and `_train`; the `roster` at this point has no `train` (it is `execute_plan` that attaches
one per step), so `UnitList([u for u in roster if …])` loses nothing. Order is preserved by
construction (comprehension over `roster`), and the test pins it against a deliberately shuffled
`HoldoutPlan.train`/`test` — a real check, since a `set`-ordered implementation would fail it.

**The narrowing survives folds.** `runner.attrition` computes
`handed = {k for s in fold_members.values() for k in s} & keys`, intersected with the roster it was
given — so a narrowed roster is respected under a fold too, not bypassed. (Moot today, since
`execute_plan` asserts the two never co-occur, but it is the property that would matter.)

**Mutations I ran myself** (all reverted by editing the file back — never `git checkout --` —
`__pycache__` deleted between runs, each revert verified by **re-running**, and a final `diff`
against a pre-mutation copy confirming `src/publishable/cli.py` byte-identical):

| # | Mutation | Expected | Observed |
|---|---|---|---|
| 1 | `test = set(holdout.test)` → `set(holdout.train)` | the narrowing tests fail | **3 failed** — the two brief tests **and** `test_condition_report_by_levels_omits_a_level_confined_to_training_units` (`'early' in {…}`), 2 passed |
| 2 | `allowed = units_matching(roster, comp.within)` → `units_matching(roster, None)` | the declared-contrast test fails | **1 failed** — `test_compute_declared_contrasts_within_is_narrowed_by_the_test_partition`; the site-5 non-pin test passed, as it must |
| 3 | brief's (a): return a copy | per brief, a `technical_n` test fails | **1 failed**, the tautological identity assert only — see Important 1 |
| 4 | `_compute_vs_baseline` early `return None, []` | the site-5 test should fail | **passed** — see Minor 3 |

**The single-line mutation that fails each added test:**

| Test | Mutation that kills it |
|---|---|
| `…evaluation_roster_is_the_test_partition_and_preserves_roster_order` | `set(holdout.test)` → `set(holdout.train)` (verified); also any copy-returning early return (verified) |
| `…narrowed_roster_is_what_attrition_counts_against` | `set(holdout.test)` → `set(holdout.train)` (verified) |
| `…report_by_levels_omits_a_level_confined_to_training_units` | `set(holdout.test)` → `set(holdout.train)` (verified) |
| `…declared_contrasts_within_is_narrowed_by_the_test_partition` | `units_matching(roster, comp.within)` → `units_matching(roster, None)` (verified) |
| `…vs_baseline_roster_argument_never_affects_the_auto_generated_family` | **none exists** — that is the finding it records, and Minor 3 is that it does not even pin the function computing anything |

"No end-to-end test" is not counted against this task: `E-DATA-HOLDOUT-UNSUPPORTED` is alive until
task 18, and the implementer's own experiment (reverting all six call sites at once, full suite still
green at 1942) is the honest measurement of that, correctly reported rather than papered over.

## Required before this task is done

1. Correct the `_evaluation_roster` docstring and the test docstring (Important 1) — **not** the plan file.
2. Append a correction to `spec-defects.md`'s OPEN `technical_n` entry (Important 2).
3. One line added to the site-5 non-pin test so it cannot pass vacuously (Minor 3).
4. Optional: reword the `reproduce` clause (Minor 4).

## Process note

`.superpowers/sdd/.gitignore` was found clobbered to a bare `*` again during this review (the standing
`scripts/sdd-workspace` behaviour). Restored from `git show HEAD:` content. This file needs
`git add -f` if it was created while the clobber was in place.
