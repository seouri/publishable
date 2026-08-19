# H4d batch 4 review — tasks 16, 17+10, 18, 19, 20

Reviewed at `d93622f` on branch `h4d-null-test`. Gates re-run here: `ruff check` clean,
`ruff format --check` 80 files, `mypy` 45 files clean, `uv run pytest` → **2348 passed, 1 skipped,
2 xfailed**. Every mutation below was reverted by editing the file back and re-verified by rerunning;
the tree is clean and the final full-suite run above was made with it clean.

## Verdict 1 — spec compliance: **FAILS on one point**, with one documented divergence

Decisions 1–5 and 7, and § Corrections 1–7, are delivered as written, and I re-derived the load-bearing
arithmetic independently rather than reading it: BH's suffix `min`, Holm's per-member level, Bonferroni's
α/m and the clip all match the spec's fixture-D table to the last digit. The failure is **M1**:
a metric block carries the resolved `null_test` echo without the `null_draws` sibling
§ Statistical reporting requires beside it, and nothing files the gap. The divergence is **M5** — the
derived-null write gated on `clusters is None` — which is a real spec defect found by the implementer,
correctly reported rather than forced, and filed; the gating decision is right on the number and
incomplete on disclosure.

## Verdict 2 — task quality: **strong on the correction family, weak on diagnostics**

The core of the batch is the best-pinned work on this slice. Batch 1's guard pin was **not edited at
all** — `git diff 0d9b500..d93622f -- tests/test_correction.py` has **zero deleted lines**, pure
appends — so the question of whether it was weakened does not arise, and its inner-key-set assertion
still fails on a spurious `p_value_corrected: None` (verified: I dropped the `if adjusted is not None`
guard and all three method pins failed, plus two more tests). Every prescribed mutation I re-ran failed
through an assertion. Against that: a **new warning code ships with no test at all**, one disjunct of the
narrowed warning is **unfailable**, the one ruling § Corrections 8 adds is **unpinned at the call site it
rules about**, and task 18's "end to end" merge pin is built on a record shape production cannot
construct.

No Critical findings: nothing in this batch publishes a wrong number, and every wiring path is gated by
a refusal that is still alive (`validate.py:4033`; confirmed by suite and grep).

---

## Major

**M1. `null_draws` is absent from the contrast entry that carries `p_value` and the `null_test`
echo — a normative record key this slice's own task 3 specified.** `src/publishable/cli.py:1398–1427`
writes `p_value` and the four-key echo and nothing else. `docs/reference.md:2560–2565`:
*"`null_draws` is what the p-value actually rests on … a metric-block sibling of `null_test`, not a key
inside it … **Equal for a recorded column by construction**"*, and `:2554` makes the echo *"present in
every metric block carrying a `p_value`"*. **Verified by running**: `_fixture_c1_call()`'s entry keys are
`basis, ci95, cohens_d, correction, delta, method, n_against, n_clusters_against, n_clusters_of, n_of,
null_test, p_value, paired` — no `null_draws`. Two notes for whoever closes it: `stats.permutation_over_contrast`
returns `float | None` and carries no survivor count, so this needs a signature change rather than a
write; and the document's *"equal by construction"* is itself false for the clustered case — in
`permutation_over_units_clustered` a draw whose relabelling empties an arm is `continue`d while the
estimator still divides by `n + 1`, so drawn-and-dropped is neither counted nor excluded (pre-existing,
task 13's surface, named here only because it decides what `null_draws` must be).

**M2. `W-STATS-NULLTEST-FAMILY` ships with zero tests.** `src/publishable/validate.py:5145–5165`.
**Verified by mutation**: changing `if effective_n < needed:` to `if False:` left
`tests/test_validate.py` at **747 passed**; the code appears nowhere under `tests/` (grep). A minted
warning that cannot be shown to fire — or to stay silent above the bound — is the "correct fix shipped
unpinned" shape, and § Warnings now carries a row for it (`docs/reference.md:390`) that no test stands
behind.

**M3. Disjunct 2 of the narrowed `W-STATS-CORRECTION-INAPPLICABLE` is unfailable.**
`src/publishable/validate.py`, the `elif shuffle not in crossed_by_any_comparison:` branch.
**Verified by mutation**: replacing it with `elif False:` left `tests/test_validate.py` at **747
passed**. The two new tests cover disjunct 1 (no `null_test`, with its control) and disjunct 3
(parameter-axis family, empty crossed set); the middle disjunct — a group axis exists and `shuffle`
names something else — has no fixture, and it is the one the § Errors/§ Warnings row and the
`reference.md:2187` sentence were rewritten for.

**M4. § Corrections 8's ruling is unpinned at the site it rules about.** The ruling is about
`cli.command_run`'s per-`report_by`-level `summarize_step` call (`src/publishable/cli.py:3163`) passing
no `null_test`/`labels`/`null_fns`. **Verified by mutation**: adding all three to that call left the
**full** suite at 2348 passed. `tests/test_stats.py`'s
`test_a_report_by_level_block_carries_no_p_value_while_its_condition_does` asserts only that
`summarize_step` behaves differently when handed different keywords — trivially true — while its
docstring claims it is *"pinned here at the two `summarize_step` calls directly, in the shape
`command_run` actually makes them"*. That first clause is the overclaim; the same docstring's later
sentence honestly defers the `run` verification to task 25, and the report's concern 2 flags the wiring
as unexercised, so this is a mis-stated pin rather than a hidden one — but the ruling is carried by
nothing today.

**M5. The `clusters is None` gate: adjudicated correct on the number, incomplete on disclosure, and
its filing claims a disclosure the code does not make.** The finding itself is real and well made — I
confirmed `stats.permutation_of_derived` takes no cluster argument, and fixture C2's prescribed
`1/5001` under a declared `cluster_by` is unreachable; publishing ≈0.48 beside `level:
"within_cluster"` would have been the spec's own wrong-stratum row shipped as a result. **Gating is the
right call on the number.** What is wrong is the record: `p_value`, `null_draws` and the echo are all
**absent**, and absent is the shape reference.md reserves for *"a run that declared none"* — so a user
who declared `null_test` beside `cluster_by` gets a run whose record is indistinguishable from one that
declared no null test at all. There is no run-level echo either (verified: `null_test` reaches only
`_comparison_step_blocks` and `summarize_step`; nothing in `assemble_run_yaml`). Decision 8's own
precedent is the available honest shape — `p_value: null` beside the echo, which *"says the test ran and
produced nothing"* — and `docs/superpowers/spec-defects.md`'s new entry asserts exactly that has
happened: *"a `null` disclosing the gap outranks a plausible number that hides it."* **No `null` is
written.** Per CLAUDE.md, delete that sentence rather than rewriting it. Two more defects in the same
entry: its **heading says `Owner: H4d task 21 or unassigned` while its body says `Owner: unassigned`**,
and task 21 (the hypothesis family's exposure to a p-value) has nothing to do with a clustered derived
draw — the heading is both self-contradictory and the *"whichever slice does X"* form this file rejects
by name. The body's own statement of unownedness, with its reason and with the check the owner must make
(draw `G` clusters' worth of labels as one unit; gate on the construction existing rather than on
`clusters is None`), is correct and should be all that survives.

**M6. Task 18's merge pin is built on a shape production cannot construct, and the only real home has
no pin.** `tests/test_cli.py:12420` calls `_entry_for(vs_baseline, None, "cond:1", …)` against a
`vs_baseline` entry carrying `p_value: 0.02`. But `_compute_vs_baseline` takes **no `null_test`
parameter** (`src/publishable/cli.py:1637`, deliberately, per decision 6, and its docstring says so),
so a `cond:` entry can never carry a `p_value` in a real run. `_entry_for`'s `contrast:` branch
(`cli.py:1878–1883`) — the *only* family-joining p-value home decision 6 leaves — is exercised by no
test that merges `p_value_corrected`. Verified by reading both functions and by grepping every
`_entry_for` call in `tests/`.

**M7. Task 17's owed measurement was not made.** What the report offers is § Corrections 7's claim —
one field moves, `observed.ci95_corrected` absent → `null` — which is a different question and is
properly tested. The owed question was whether **BH over `hypotheses.py`'s partial member set with the
larger `m`** is right, and it is still answered only by transferring `family_shape`'s conservatism
argument. Verified by reading: `hypotheses.evaluate` (`src/publishable/hypotheses.py:284–306`) reads
only `ci95_corrected` off `corrected_for`'s output and **never records `p_value_corrected`**, so the
adjusted value BH computes there is unobservable in this build; and the only `fdr_bh` test in
`tests/test_hypotheses.py` (`:727`) exercises a family with no p-values at all. The ruling may well be
right — larger `m` with smaller `k` is conservative — but nothing in this batch measures it, and the
report's *"Measured by reading … and confirmed by a new direct test"* reads as though it did.

**M8. The disclaimed non-monotonicity is instantiated by no fixture, and the test named for it asserts
the monotone relation.** `docs/reference.md:2174` states normatively that *"a member with a smaller raw
p can carry a larger adjusted one"*. **Verified by running**: on fixture D, Holm's adjusted order is
`X, Y, Z, W` — **identical to the raw p order** — so no inversion exists there;
`test_holms_adjusted_p_is_the_p_at_this_members_own_level_and_is_not_monotone` asserts
`adjusted["cond:Y"] < adjusted["cond:Z"]`, which *is* the monotone relation, under a docstring claiming
*"the non-monotonicity is asserted, not merely tolerated"*. The report repeats it (*"Y's 0.88 below
Z's 0.93 despite a smaller raw p"* — 0.88 below 0.93 with a smaller raw p is agreement, not a
*despite*). Fixture D puts the strongest evidence at the second-smallest p, which just misses the
inversion; an instance needs e.g. p = 0.2 at evidence rank 1 (→ 0.8) against p = 0.3 at rank 4 (→ 0.3).
The guard against a later slice ranking Holm on p **does** survive independently — I mutated Holm's
factor to use the p-rank and the four literals failed — so the fix is deleting the claim from the test
docstring and the report, not adding an assertion to make the sentence true. (The spec is exempt from
retro-edit; `reference.md` says *"can"*, which is correct as a possibility claim.)

## Minor

**m1. "until task 21" is the wrong task, in shipped source.** `src/publishable/cli.py:803`
(*"`E-STATS-NULLTEST-UNSUPPORTED` gates every declaration until task 21"*),
`tests/test_stats.py:5382` (which contradicts itself in one sentence: *"until task 21; that
verification is task 25's"*), and the report at three places. The refusal is retired by **tasks 25+26**
(`docs/superpowers/plans/2026-08-18-null-test.md:4145`).

**m2. `units.null_test_level`'s docstring names one caller and there are now two.** It says *"The
caller, `validate._check_null_test`, enforces the restriction by construction: it calls this only when
`shuffle in declared`"*. `cli.command_run:2466–2468` calls it for **any** non-`None` `shuffle`,
including an axis-only name. I could not find a reachable fail-open — an axis-only name with no
`cluster_by` returns `("rows", None)` before any attribute is read, and axis-only **with** `cluster_by`
is refused by `E-STATS-NULLTEST-LEVEL` — but that safety rests entirely on a `validate` refusal the new
call site does not name, where the `summarize_step` retry handler a few hundred lines away names each of
its gates explicitly. Either name the gate or state the two callers.

**m3. `_resolved_null_test`'s `"declared"` key is dead.** `src/publishable/cli.py:1838–1848`: the
function returns `None` for an undeclared block, so `declared` can only ever be `True`, and nothing
reads it (grep: every `["declared"]` read is `resample_spec`'s). Prefer deleting the key to keeping a
field whose docstring explains why its `False` case does not exist.

**m4. The `thin` narrowing is pinned for `holm` only.** `tests/test_correction.py`'s
`test_a_p_only_member_does_not_report_a_thin_correction` uses `holm`. **Verified by direct call** that
both halves of § Corrections 5 are genuinely closed: with `and member.ci95 is not None` removed, the
p-only member reports `thin: True` under **both** `holm` and `bonferroni` (and `False` under `fdr_bh`,
where `level` is `None`). The fix is method-independent so the risk is small, but this is the same
asymmetry round 1 of batch 1 fixed by adding the bonferroni and fdr_bh regression pins beside the holm
one.

**m5. The report's blanket claim about the refusal is false as written.** `task-b4-report.md:123`:
*"Every test in this batch calling into `validate` asserts its own code **alongside** that refusal."*
The batch's two `validate` tests
(`test_the_inapplicable_correction_warning_is_silent_where_a_p_value_can_be_carried`,
`..._still_fires_for_a_parameter_axis_contrast`) assert two allocation-code absences and the warning;
neither mentions `E-STATS-NULLTEST-UNSUPPORTED`. The refusal *is* alive — that part is true, and
verified — but not by these tests.

**m6. `null_test` is read twice in `_check_sweep`**, once inside the `fdr_bh` branch and once at the
enclosing level immediately after, shadowing the first. Harmless, one expression.

**m7. Carry-forward, not this batch's fault.** `docs/reference.md:253` § Validation still reads
*"`statistics.null_test` requires `shuffle` to name a unit attribute"* while the shipped check accepts
`data.units.attributes` **∪** `sweep.groups` axis names — which is the union the slice's own design
calls load-bearing. Task 7's surface, task 28's sweep; recorded here so it is not re-derived.

## Verified by running vs. read

**By running:** the guard pin's response to a spurious `p_value_corrected: None` (5 failures, three of
them the method pins); the eager-key crash and the sentinel-key mis-rank (the latter caught by an
assertion, not a crash); BH's suffix-`min` collapse; BH ranked on the evidence ratio; Holm ranked on
the p-value; the `thin` narrowing under all three methods; `_make_null_fn`'s erasure property (`merged`
→ `attrs` fails on `-10.0`); the contrast-side wrong-stratum mutant (`of_clusters=None` → fails) and
wrong-level mutant (`whole_cluster` → fails); the `report_by` level-call mutation (full suite green);
`W-STATS-NULLTEST-FAMILY` and disjunct 2 neutered (test_validate green); fixture D's four adjusted
values recomputed independently in a standalone script; the contrast entry's key list; fixture D's Holm
order against its raw order; all four gates.

**By reading:** decision 6's `vs_baseline` omission; `hypotheses.evaluate`'s three-state logic and its
non-recording of `p_value_corrected`; `null_test_level`'s domain argument and `validate`'s two guards;
`clusters` being `None` exactly when `cluster_by` is undeclared (which is what makes `summarize_step`'s
*"the echo below cannot lie"* comment true); the mechanical pass over `reference.md` and the other three
documents (links, anchors, duplicate anchors, table column counts, trailing whitespace, tabs, invisible
unicode — all clean; `×` used correctly in every added line; no positional locator added, and the
§ Warnings insertion moved no positionally-cited row).

## Could not check

- **Any of tasks 19's and 20's `cli` wiring end to end.** `E-STATS-NULLTEST-UNSUPPORTED` gates every
  declaration, so the spec's own ordering constraint — *"tasks 19 and 20 by `run`, never by direct
  call"*, written against a corner with five wrong grounds — is unmet by construction and deferred to
  task 25. The batch says so; I am restating it because it is the batch's largest unverified surface and
  the constraint was the spec's, not the brief's.
- **Whether the C2 gap would be better served by a `validate` refusal than by a record-level `null`.**
  `validate` cannot know a template's `aggregate` produces a derived metric, so a declaration-time
  refusal would have to refuse `null_test` + `cluster_by` outright; deciding that is a design call
  outside this review.
