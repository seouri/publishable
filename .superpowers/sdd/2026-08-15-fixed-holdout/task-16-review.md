# Task 16 review: `W-STATS-RESAMPLE-CLUSTERS` against the test partition

Reviewed `b4e49e5..cfd5672` (`30f18b2` fix, `cfd5672` report). All mutations below were applied by
editing the file in place, `__pycache__` deleted between runs, every revert verified by RE-RUNNING
the affected tests (never by `git status`). Working tree left clean; full suite re-run green at the
end (`1945 passed, 2 xfailed`), `uv run ruff check .` and `uv run mypy` clean.

## Verdicts

1. **Spec compliance — ✅.** The narrowing is correct, single-emit-site, threaded once, inert when
   no holdout is declared, and the § Errors row was updated with it.
2. **Task quality — ❌.** Two Important findings: the boundary control is vacuous and a
   discriminating fixture *is* constructible at this commit (verified, below), and the warning's
   emitted sentence now makes a false statement about the roster with nothing pinning the new count.

---

## The adjudication asked for: is the discriminating fixture constructible?

**Yes. Verified empirically, and the honest negative is therefore not the correct final answer.**

**How verified.** I appended a temporary probe to `tests/test_validate.py` that resolves the
fixture's roster and calls `clusters_of` + `holdout_seed_for` + `holdout_for` exactly as
`_holdout_test_roster` does, for the shipped control's own config (40 units, `a{i//2}` clusters,
`frac: 0.2`, `seed: 1234`). Output:

```
TEST CLUSTERS  ['a12', 'a13', 'a2', 'a6']
TRAIN CLUSTERS ['a0', 'a1', 'a10', 'a11', 'a14', ... 'a9']   (16 clusters)
```

The draw is deterministic and **independent of the `label` column**: `holdout_seed_for` returns a
pinned integer literally and *does not consult the digest at all* on that path (its own docstring,
and `hashes.design_digest` strips `holdout.seed`), and `clusters_of`/`holdout_for` read only the
key and the cluster attribute. So the stratum values can be rearranged freely without moving the
split.

**The fixture.** One line of the shipped test changes — `label` becomes `"y" if i == 1 else "x"`,
so the *only* cluster that varies is `a0`, which lands on the **training** side.

- On HEAD: `E-STATS-RESAMPLE-STRATIFY-VARIES` is reported — test passes.
- Under the implementer's own mutation (c) (`stratum_varies_within_cluster(holdout_test if
  holdout_test is not None else roster, ...)` at `validate.py:5744`): **FAILS** —
  `assert 'E-STATS-RESAMPLE-STRATIFY-VARIES' in {'E-DATA-HOLDOUT-UNSUPPORTED'}`.
- Under that same mutation, the **shipped** `test_the_stratum_constancy_check_still_reads_the_whole_roster`
  still **passes** (`1 passed`).

Mutation reverted in place and both re-run green afterwards.

So: `E-DATA-HOLDOUT-UNSUPPORTED` does not block the config (it is collected alongside, as the
shipped tests already rely on), the seeded draw is arrangeable rather than luck, and the cost is a
one-line fixture edit. The implementer's investigation was correct as far as it went — the fixture
really does vary on every cluster, and correcting the docstring was the right *immediate* move over
leaving a false claim standing — but stopping there leaves the boundary named and unpinned, which
is precisely the "a seam named in the brief and instantiated by no fixture" shape in CLAUDE.md.

---

## Findings

### Important 1 — the boundary control cannot fail; a fixture that can is constructible

`tests/test_validate.py::test_the_stratum_constancy_check_still_reads_the_whole_roster` asserts a
property (`the check reads the WHOLE roster`) that no assertion in it can distinguish from the
opposite. **Verified** as above: the discriminating fixture exists, differs by one expression, and
fails under the narrowing mutation while the shipped one does not.

*Recommended:* swap the fixture to the training-side-only variant, restore a docstring that states
the guarantee the assertion now actually makes (naming `a0` as the training-side cluster and the
seed that puts it there), and keep the corrected note about *why* the seed pins it.

### Important 2 — the emitted message says "this roster" while counting the test partition

`src/publishable/validate.py:5728-5731` still reads:

```
f"is {min_clusters}, and `data.units.cluster_by: {cluster_by}` puts this "
f"roster in {groups} clusters — ..."
```

**Verified** against the task's own fixture: under `frac: 0.2` over 50 clusters the user is told
"puts this **roster** in 10 clusters" when the roster falls in 50. The § Errors row was corrected
for exactly this behaviour change; the sentence the code prints was not. Same shape as CLAUDE.md's
"a comment or docstring claiming a guarantee the code does not provide", moved to a user-facing
string — and it misdirects the remedy, since the reader will look for the missing 40 clusters in a
roster that has them.

**What this finding does NOT claim.** The count itself cannot regress invisibly: the message prints
`{groups}`, the same variable the guard compares (`if groups is not None and groups < min_clusters`),
so a `50` in the message means the warning never fired and test 1 fails. The defect is the *wording*
alone — the noun "roster" naming something the number is no longer over. The pre-existing message
test (`tests/test_validate.py:3759-3761`) pins `"4"`/`not "12"` for the non-holdout case; the holdout
case has no counterpart, so nothing would notice the sentence continuing to say "roster" after a fix.

*Recommended:* name the partition in the message ("puts this holdout's test partition in 10
clusters"), and pin the **wording** — that the message names the partition — rather than the count.

### Minor 3 — `_holdout_test_roster`'s "**Never raises.**"

The docstring states an unconditional guarantee that a five-element `except` tuple provides only for
those five types. **Verified not live**: I ran 12 adversarial holdout blocks through `validate_config`
(unknown `stratify_by`, `frac` as dict/list/`0.0`/`1.0`/`1e-9`, `seed` as a list, `by_attribute` with
a missing and an absent attribute, an out-of-enum method, a method-less block, a string
`stratify_by`) — all 12 collected findings and none escaped. No defect today; the sentence overclaims
by one word and should read "never raises for the faults `validate` can already see", or list them.

### Minor 4 — the § Errors row states unconditionally what the code does conditionally

`docs/reference.md:385` says the count is over the test partition "when one is declared, the roster
otherwise". The code also falls back to the roster when a holdout **is** declared but the draw could
not be performed (the `except` path returning `None`). Harmless in practice — every such config
carries its own error beside it — but the row reads as a rule with no exception. Row itself is
otherwise correct and covers the **single** emit site (`grep` confirms `W-STATS-RESAMPLE-CLUSTERS`
is raised in exactly one place, `validate.py:5726`), so the "one row per code, not per site" trap is
not hit here.

### Minor 5 — stale lead in `_check_resample`'s enumeration

The bullet still opens `- W-STATS-RESAMPLE-CLUSTERS — **reads the roster:**` and only qualifies the
narrowing two lines later, and the summary sentence "**Two of the seven read `roster`, not one**"
now means "roster or its narrowing". Not false, but the bold lead is the part a skimmer keeps.

### Minor 6 — a third derivation of the same narrowing

`cli._resolved_holdout` + `cli._evaluation_roster` already realize the plan and narrow to
`plan.test` with a body identical to `_holdout_test_roster`'s last two lines. `validate` cannot
import `cli`, so the duplication is structural rather than avoidable, but neither site names the
other. A cross-reference in both docstrings would keep them from drifting; `_holdout_test_roster`
currently cites `cli.command_run` only for the purity argument.

---

## Confirmations requested

**Item 3 — the brief was wrong about mutation (b): CONFIRMED.** I applied it
(`test = set(plan.train)`) and got `2 failed` — both `..._counts_the_holdout_s_test_partition` and
`..._holdout_wide_enough_...`, not the one the brief predicted. The implementer's reported reason is
right: at `frac: 0.2` the train side is ~40 clusters, above `min_clusters: 20`, so the warning goes
silent where the test needs it. Reverted; both green.

**Are both tests still earning their place? Yes — neither is redundant.** Mutation (b) fails both,
but I ran a third: `return UnitList([])` from `_holdout_test_roster` — the "warn whenever a holdout
is declared" fix the brief's second test exists to rule out. Result: `1 failed, 1 passed` — test 1
passes, test 2 fails. So test 2 is the only guard against that mutant, and test 1 is the only guard
against mutation (a). Reverted; both green.

**Item 4 — `E-STATS-RESAMPLE-STRATIFY-VARIES` staying whole-roster: correct on the merits.**
Constancy within a cluster is a property of the unit rows, not of which partition the unit lands in,
and constancy over the roster implies it over any subset, so the wide read is the strictly stronger
one. Noted rather than filed: the wide read can hard-refuse a config whose *realized* resample is
coherent (a stratum varying only inside a training-side cluster). That is defensible here — the
training half is real data a step can see through `io.units.train`, and an incoherent declaration
about it is worth refusing — and it is what the new discriminating fixture would pin. **Nothing else
in `_check_resample` reads a roster that should have narrowed**: I enumerated every `roster`
reference in the function body (lines 5490-5830); exactly two checks read it, the clusters count
(now narrowed) and this one.

**Item 5 — threading: CONFIRMED correct.**
- Computed **once**, at `validate.py:629`, and `_holdout_test_roster` has exactly that one call site.
- `None` for `roster is None`, for an absent `holdout`, for a non-dict `holdout`, and for `{}` —
  the same four shapes `cli._resolved_holdout` calls `None`, so the two readings of "is a holdout
  declared" agree.
- `None` leaves pre-existing behaviour **byte-identical**: the only consumer is the ternary at
  `validate.py:5708`, whose else-branch is the original `fold_basis(roster, cluster_by)` expression.
  Confirmed by the whole pre-existing `W-STATS-RESAMPLE-CLUSTERS` test block (`tests/test_validate.py`
  lines 3735-3923, all non-holdout) staying green, plus the new test's own `without` control.
- **Realization parity with the run: CONFIRMED at HEAD, not assumed.** `cli.command_run` derives the
  seed as `digest = design_digest(doc)` (`cli.py:1300`) over the same document, and gates the cluster
  map on `isinstance(cluster_by, str) and cluster_by` (`cli.py:1392-1393`) — identical to
  `validate_config`'s `usable_cluster`. So `validate` narrows against the same partition the run
  draws.

**Item 1 — the document, swept for the claim rather than for the code.** `grep -n "min_clusters"`
over all four documents returns four sites, not one:
`reference.md:170` (the config comment, "warns when `resample` would draw fewer than this" — still
true), `reference.md:251` (§ Validation, *Clusters enough to resample* — states the rule
method-independently and names no roster, so it is untouched by the narrowing),
`reference.md:385` (the § Errors row, edited here), and **`reference.md:1334`** (§ A fixed holdout
split), which already said "`limits.min_clusters` is checked against the **test** partition's cluster
count … a roster of 50 clusters under a `frac: 0.2` holdout resamples roughly 10". That passage
predates the code (`3b5e942`), so this task is the code catching up to the spec and the § Errors row
was the one remaining site. **The sweep is clean: no normative passage now describes the count as
over the roster**, and the row does not overclaim in the no-holdout direction ("the roster
otherwise").

**The premise the task rests on — that a resample draws over the test partition — CONFIRMED at the
code, not inferred.** `cli.py:1522` binds `eval_roster = _evaluation_roster(roster, holdout_plan)`
and every resample-bearing computation is handed that object, not `roster`: `units=eval_roster`
(`cli.py:1652`) and `roster=eval_roster` into `_compute_vs_baseline` and
`_compute_declared_contrasts` (`cli.py:2480`, `2493`), which carry `resample_fns_by_key` and the
resample seed. `roster` itself stays whole below that line only for `provenance.units.n` and
`units_hash`. So `validate` now warns against the denominator the run actually resamples over.

## (a) A mutation that makes each new test fail

| Test | Single-line mutation | Result |
|---|---|---|
| `..._counts_the_holdout_s_test_partition` | `groups = fold_basis(roster, cluster_by)` (drop the ternary) | **FAIL**, verified by me |
| `..._holdout_wide_enough_to_keep_the_clusters_does_not_warn` | `return UnitList([])` in `_holdout_test_roster` | **FAIL**, verified by me (test 1 passes) |
| `..._stratum_constancy_check_still_reads_the_whole_roster` | **None short of deleting the check.** Narrowing it to `holdout_test` leaves it green — verified by me, and by the implementer as mutation (c) | Vacuous for the property its name claims — see Important 1 |

## (b) Comments and docstrings claiming a guarantee the code does not provide

Every sentence in the diff was read. Three flagged: the "Never raises" overclaim (Minor 3), the
message string (Important 2 — a user-facing instance of the same shape), and the § Errors row's
unconditional phrasing (Minor 4). **The implementer's corrected docstring is accurate**: I verified
each of its claims independently — every cluster in that fixture does carry one `x` and one `y`, and
narrowing the check does leave the assertion passing. Its closing sentence ("the positive claim in
this function's name rests on the code and on task 16's report, not on an assertion in this file") is
honest, but it is a description of the gap in Important 1 rather than a resolution of it, and a
reader who greps for the test name and stops looking is exactly the failure CLAUDE.md warns about —
the name still claims what nothing checks.

## Process note

`.superpowers/sdd/.gitignore` was clobbered to a bare `*` again during this review (the standing
`task-brief` behaviour). Restored; it carried no uncommitted content of its own.
