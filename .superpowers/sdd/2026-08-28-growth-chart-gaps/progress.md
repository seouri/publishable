# SDD ledger — plan: docs/superpowers/plans/2026-08-28-growth-chart-gaps.md

Spec: docs/superpowers/specs/2026-08-28-growth-chart-gaps-design.md (read; binding authority)
Scoping: docs/superpowers/G1-SCOPING.md (measured against 84e6802, 2026-08-28)
Branch: **main**, by explicit instruction.

Ruling: work proceeds directly on `main` with commit+push per task — the human partner
instructed "directly commit/review/fix/push on main until all of them are fully executed",
which is the explicit consent the skill's Setup requires. Costs if wrong: no isolation, so a
bad task is reverted on a public branch rather than abandoned on a private one.

Ruling: `scripts/sdd-workspace` clobbered `.superpowers/sdd/.gitignore` to a bare `*` on its
first run, as CLAUDE.md warns. Restored from a copy taken beforehand; every record committed
this session uses `git add -f`. Costs if wrong: newly created records silently untracked.

## Pre-flight scan

### Pair rows — every pair sharing a file or an interface

| Pair | Produces → consumes | Found |
|---|---|---|
| T2, T3, T4, T6, T9, T10 | all edit `docs/reference.md` | **No section collision**: § Repeat kinds, § The one config file, § Errors + § Templates, § Warnings, § Pre-registration + § What a hypothesis is tested against, § Studies. Sequential execution keeps them from racing |
| T4 → T5 | T4 mints `E-TEMPLATE-PARAM-PATH` and its row; T5 pins both arms | Consistent. T5 cannot run before T4 |
| T6 → T7 → T8 | T6 mints `W-SWEEP-CONDITION-DUPLICATE`; T7 writes its message; T8 pins | T7 has no independent test surface and no independent commit value. **Batched with T6** — see ruling |
| T6, T9 | both edit `src/publishable/validate.py` | Different checks, different functions. Sequential execution avoids the conflict |
| T4, T9 | both may touch a `reference.md` error/warning table | T4 adds an `E-` row, T9 amends `compare`'s row. Different tables |
| T1 → T11 | T1 rewrites analysis gap 4; T11 re-records § Executability in the same file | Consistent; T11 runs last |
| T10 → T11 | T10 writes the § Studies paragraph; T11 amends the matching `spec-defects.md` entry | Consistent |

### Self-consistency rows — one per task

| Task | Its own text agrees with itself? |
|---|---|
| T1 | Yes |
| T2 | Yes |
| T3 | Yes |
| T4 | **No — ruled below.** "raised as a `ContractError` where the `ValueError` is today" and "at template load rather than at `generate experiment`" name two different sites |
| T5 | Yes |
| T6 | Yes |
| T7 | Yes — but see the T6/T7 batching ruling |
| T8 | Yes |
| T9 | Yes (delegates the code choice to implementation, with a record requirement) |
| T10 | Yes |
| T11 | **No — ruled below.** "strike the three G1 entries that closed" contradicts the same sentence's "amend rather than strike the correction-family one" |

## Rulings from the pre-flight scan

Ruling: **T4's check goes at template load, not in `materialize._parameters_block`.** The design's
two clauses conflict; the load site wins because `reference.md` § Templates already puts a malformed
`Param` declaration there — "a `Param` declaring `default=None` without `nullable=True` is rejected
when the template loads, rather than at the first config that leaves it alone" — and a spec whose
paths are malformed is malformed for `list-templates` and `validate` too, not only for the one
command that materializes it. `_parameters_block`'s own `ValueError` stays as an unreachable guard.
Costs if wrong: the refusal fires earlier than a reader expects, and a template that is never loaded
is never checked.

Ruling: **T6 and T7 are one dispatch.** T7 is the message text of the check T6 builds; splitting
them would produce a commit whose diagnostic is deliberately wrong. Batched per the skill's
same-shape rule. Costs if wrong: one larger review surface instead of two small ones.

Ruling: **T11 strikes TWO spec-defects entries and amends ONE.** Gap 1 closes by code (T4/T5) and
gap 3 by code (T6–T8), so both are struck; gap 2 closes as a documented limitation (T10), so it is
amended with the closure named as a paragraph rather than as a mechanism. The plan's "three ... that
closed" is its own arithmetic error. Costs if wrong: a reader looks for code behind gap 2's closure.

Ruling: **T2 and T3 are one dispatch.** Both are single-sentence edits to `reference.md` by the same
rule, in different sections, with no test surface. Same-shape batching. Costs if wrong: one review
surface instead of two.

## Progress
Task 1: complete (commits 79e3a9b..25d4fb6, review clean)
Task 2+3: complete (commits 25d4fb6..85bdfcf, review clean)

Ruling: `.superpowers/sdd/<plan>/` reports and `progress.md` are TRACKED here — the workspace's own
`.gitignore` says so and ignores only briefs and `.diff`s — but Task 1's implementer left its report
untracked and the ledger was untracked too. Both are committed now with `git add -f`, and every later
dispatch says to commit its own report. Costs if wrong: a record CLAUDE.md calls part of the
development record exists only on this machine.

Task 4: review found 2 Important, 4 Minor (commits e40b9e2..a2074be)

Ruling: **Minor 3 is upgraded into the fix loop.** The review classes "raises at class-definition
time, before `@register_template` is ever reached" as imprecision rather than a false guarantee,
and on the guarantee it is right. It enters anyway because the claim is WRONG IN FOUR HOMES and this
repo's most expensive recurring defect is a sentence that describes a mechanism the code does not
have — "sweep for the claim, not for the file the claim was first noticed in". A correct sentence
already exists at `reference.md` § Templates; normalising to it is cheaper than leaving four copies
of a wrong one. Costs if wrong: one extra fix round for a wording change.

Task 4: minor (deferred): the message embeds its own `E-` code while the CLI also prefixes
`exc.code`, so the direct-raise path prints it twice — justified and earned by a real red, but the
consequence is undocumented.
Task 4: minor (deferred): the `isinstance(..., dict)` skip is pinned only incidentally by
`test_cli.py`'s non-dict `parameter_spec` assertion; nothing names the guard.
Task 4: minor (deferred): `..._is_a_diagnostic_not_a_traceback` is proven at `discover_local` level,
not through the CLI — a name that overclaims its own body.
Task 4: carried to T11: `feasibility-growth-chart-literacy.md` gap 1 still asserts the traceback and
"no `E-` code covers the refusal", stale as of a2074be.
Task 4: freeze.py `claim.cls()` — reviewer judged it out of scope and needing nothing now, AND
judged the implementer's reasoning about it wrong. Not carried; the exposure is pre-existing and
unrelated to this code.
Task 4: fix round 1/5 (2 addressed, 1 open — the wrong-mechanism claim survives at a fifth home,
`reference.md` line ~4274, consciously skipped as "a different established topic"; commits
a2074be..e5d2816)

Ruling: **Finding 1 counts as ADDRESSED on judgment, not on mechanism.** The re-review verified that
`GenericTemplate` is the only live unwrapped class definition outside `discover_local` and that its
own paths are valid, so the narrowed sentence is true of exactly the surface that exists — but it
calls the no-core-raises-row decision "defensible but disputable". Accepted: a raise nothing can
reach needs no row, and adding one would document a surface a reader cannot produce. Costs if wrong:
§ Errors core raises is missing a code that some future core template could emit.

Ruling: **the duplicated clause the fix introduced rides along in round 2.** It is Minor and Minor
findings do not enter the loop, but it is one line in the same row round 2 must edit anyway, and
leaving a mechanical find/replace artifact in a normative table is worse than the round it costs.
Costs if wrong: a trivially larger round-2 diff.
Task 4: fix round 2/5 (1 addressed + ride-along, 1 open — a SIXTH home in validate.py, missed because its wording is 'call is reached'/'runs' rather than 'ever reached'; commits e5d2816..eaa1de9)
Task 4: fix round 3/5 (1 addressed; commits eaa1de9..48e9ea4)

Ruling: **Finding 3 is ADDRESSED, and round 3's re-review is overruled on its two new homes.** It
flagged `reference.md:4274`, `tests/test_plugins.py:526` and (by the same shape) `plugins.py:350` as
the false mechanism claim. Read whole, they are not. Each says a class body finishes running before
its own `@register_template` **registers the class**, so a file raising *after* that point still
leaves a class core can read `required_env` off — an ordering claim about registration that is TRUE,
and the argument it supports is correct. The false claim was the opposite one: that a raise *inside*
a class body happens before the decorator line is "reached". The same paragraph at 4274 carries both,
and its second sentence is the corrected wording round 2 landed — the two do not contradict, they
cover a raise after the class exists and a raise inside the body.

That is the identical judgment round 3's own reviewer made about the `test_cli.py` match, applied
inconsistently to three siblings. A pattern-based sweep cannot separate "finishes before the
decorator is APPLIED" (true) from "reaches the decorator line" (false); only reading can, which is
why this is adjudicated here rather than sent to a fourth round. Costs if wrong: three true
sentences keep a loose word.

Task 4: minor (deferred): those three homes say "before its own `@register_template` call" where
*application* or *registration* is meant. The claim is true; the word "call" is what keeps drawing
false positives, and sharpening it would stop the next sweep re-finding them.
Task 4: complete (commits e40b9e2..48e9ea4, 3 fix rounds, review clean after adjudication; suite 3488 passed, 1 skipped, 2 xfailed; ruff and mypy clean)
Task 5: complete (commits b831bcc..5da4986, review clean)
Task 5: minor (deferred): traceback-absence asserted on both stdout and stderr rather than only the
stream a traceback goes to — harmless, since stdout is independently pinned to the diagnostic.

Task 6+7: review found 1 Critical, 2 Important, 2 Minor (commits 7161ae5..7df4772)
Task 6+7: minor (deferred): `reference.md` row 636 under-describes coverage — "a known gap, recorded
here rather than closed" is no longer true for the no-groups form.
Task 6+7: minor (deferred): report-once is pinned only through `messages_by_code`'s dict collapse
rather than by counting findings; it did go red, so it has power.
Task 6+7: fix round 1/5 (2 addressed, 1 open — the exclusion moved from per-config to per-axis and is still too broad; shapes F and J silenced; commits 7df4772..ce5f10d)
Task 6+7: fix round 2/5 (1 open — X1 and P1 over-silenced; commits ce5f10d..2ee69af)

Ruling: **X1 and P1 are PARKED, and the predicate is accepted as correct for every reachable
config.** Both shapes the round-2 re-review found require `groups: [{by: arm, levels: [c, c]}]` — a
level declared twice on one axis — and that is `E-SWEEP-LEVEL-DUPLICATE`, emitted by `c.error`
(`validate.py:4797`). Such a config does not run. A warning withheld from a config that already
fails with an error tells a reader nothing the error does not already force them to fix, and once
they fix it the warning fires on whatever duplication remains. The exclusion's remaining breadth is
therefore invisible from outside. Costs if wrong: if a later slice ever downgrades
`E-SWEEP-LEVEL-DUPLICATE` to a warning, these two shapes become live silences and this ruling is the
thing to re-read.

Ruling: **round 3 is narrowed to the false justification sentences only, not the predicate.** The
same claim — that the exclusion covers "the pair those checks already report" — has now been false
after every round, and is currently false in THREE homes. A false sentence in a normative document
is what this repo punishes hardest, and it is cheap; the predicate is not being touched again.
Costs if wrong: one more round spent on prose while the code stands.
Task 6+7: fix round 3/5 (1 addressed, 0 open — 7 homes corrected, predicate confirmed untouched;
commits 2ee69af..664b21d)
Task 6+7: minor (deferred): the report says "six homes" and lists seven — a slip in ledger prose,
not in governed spec or code.
Task 6+7: complete (commits 7161ae5..664b21d, 3 fix rounds, review clean, 2 parked;
suite 3499 passed, 1 skipped, 2 xfailed; ruff and mypy clean)
Task 8: review found 1 Important (fixture distinguishes 3 of 4 candidates while its docstring claims 4), 1 Minor judged not-a-gap; commits fddf329..4492018
Task 8: fix round 1/5 (1 addressed, 0 open — all four candidate behaviours now observationally
distinct, verified by independent derivation; commits 4492018..59297df)
Task 8: complete (commits fddf329..59297df, review clean)

Task 9: review found 2 Critical, 3 Important, 2 Minor (commits ae21f78..80a4c37)
Task 9: minor (deferred): `test_a_constant_hypothesis_where_clashes_with_no_vs_baseline_member`
names a `by_key` collision pin but never calls `evaluate` or builds a member, and its `!= "cond:1"`
assertion is implied by `== "const:1"` in the same test.
Task 9: minor (deferred): `test_a_compare_to_constant_with_a_numeric_value_is_not_flagged` asserts
only absences — it can fail, but it should be paired with something that must report.
Task 9: fix round 1/5 (4 addressed, 1 open + 1 new — two residual doc homes for the corrected-bound
promise, and a surviving mutant on the new guard's `_is_counted` conjunct; commits 80a4c37..6e96655)

Ruling: **the `corrected_unavailable=True` fallback is accepted over building a `Member`.** The
feature is now honest — counted, and openly uncorrectable under a declared method — rather than
counted-and-silently-uncorrected. The reviewer confirmed the direction of error is conservative
(tighter, never over-support) and that `_level_for` already returns `None` under `fdr_bh` for every
member of every family, so the honest-null state is precedented rather than minted here. Building a
`Member` from the condition's own resample pool is real statistical work and the charter was to
close a gap, not to add statistics. Costs if wrong: a bound test on a constant reference is
unusable under `holm`, and the motivating E2/E6 claims stay on the `Estimate` route.
Task 9: fix round 2/5 (all addressed; commits 6e96655..7c19472)

Ruling: **round 2 was verified by the controller directly, not by a dispatched re-reviewer.** The
subagent session limit was reached mid-review. Verified by running rather than reading: both
`reference.md` homes read correctly in their whole paragraphs, and the surviving "two routes" count
phrase nearby is a different count that stays true; the `_is_counted` mutant was re-applied and
killed exactly the two intended tests (2 failed, 46 passed), restored to 48 passed; the new
`spec-defects.md` entry is accurate, owned *unassigned*, says the project ships with it, names the
`fdr_bh` precedent and costs the real fix; the docstring overclaim is gone; and no assertion was
removed anywhere in the test diff. Costs if wrong: this round had one pair of eyes instead of two,
and the whole-branch review at T11 is the net.

Task 9: complete (commits ae21f78..7c19472, 2 fix rounds, review clean, 1 new spec-defects filing)
Task 10: complete (commits fc6413c..40f1663, review clean)
Task 11: complete (commits 6bac09a..6d99a88, review clean; suite 3524 passed, 1 skipped, 2 xfailed)

Whole-branch review (79e3a9b..6d99a88, 27 commits): 1 Important, 1 Minor. Every deferred minor and
both parked findings triaged as STANDS; one was already fixed at HEAD.
Whole-branch: minor (deferred): `_group_axes_already_erred`'s three defensive skips
(`validate.py` ~4245-4275) have no test — direction of error is safe (more warnings, not fewer), and
`expand` raises first on a malformed `sweep`, verified by probe, so the branch is unreachable.

Whole-branch fix wave 1 (6d99a88..1fbfd32): NOT ADDRESSED, and it introduced a blocking regression.

Ruling: **a second fix wave is authorized, against the skill's "there is no second fix wave"
guidance.** That guidance governs RESIDUAL findings — things the wave failed to fix. This wave
introduced a new correctness bug: `verdict_for` subtracts `compare.value` gated only on
`compare["to"] == "constant"`, never on which branch `resolve` took, so a contrast-resolved
observation now has the constant subtracted from it. Measured through `evaluate()`: a contrast delta
of 0.04 against `threshold: 0.0, direction: greater` emits `observed: {delta: 0.04, ci95: [0.01,
0.07]}` and `supported: false` — every number in the record clears the threshold and the verdict
says otherwise, decided on a −0.46 that appears nowhere. Pre-fix the record was
coherent-but-incomplete; post-fix it is self-contradictory, and since
`E-HYPOTHESIS-COMPARE-VALUE` requires a numeric `value`, every writable instance of the pairing is
corrupted. Shipping that is not a residual-finding call. Costs if wrong: one more round.

Ruling: **the refusal is taken over "contrast wins".** The implementer's symmetry argument is
falsified: `to: baseline` has no consumer outside `resolve` and is a validate gate only, while
`to: constant` carries a payload with a SECOND consumer in `verdict_for` — so the two pairings are
not the same shape and refusing one leaves no identical fault legal under the other. Refusal is also
the smaller change: keeping "contrast wins" additionally requires gating the subtraction, and then
re-justifying a code that demands a number nobody reads, which is this repo's *parameter wired to a
constant* row. Costs if wrong: a combination someone wanted is refused rather than resolved.
