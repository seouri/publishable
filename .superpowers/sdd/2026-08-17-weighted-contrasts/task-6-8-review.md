# Tasks 6-8 review

Reviewed at `dbc0830` on branch `h4b-weighted-contrasts`, 2026-08-17. Working tree clean before and
after; every mutation below was applied by editing the file, reverted by restoring a byte-identical
copy taken before the first mutation (`md5` compared each time), `__pycache__` cleared between runs,
and the revert verified by re-running the affected tests.

## Verdicts

**Spec compliance: PASS.** The design's binding decisions are honoured where these three tasks own
them. Decision 2 — the payoff runs through `paired_percentile_of_derived` with the `_column_mean`
closure, not `paired_t_over_units`. Decision 3 — `weighted_paired_percentile_over_units` is the
minted spelling and is emitted only for a recorded column, verified against `reference.md`'s own
construction table rather than a second literal. Decision 5 — `strata` reaches **both** percentile
branches. Decision 1's derived/column split holds: a derived metric under a declared weight keeps
`paired_percentile_over_units`, an unweighted delta and `cohens_d: null`. The corrections appended to
the spec are all satisfied: Kish is over the paired intersection, `weighted_cohens_dz` exists with the
`Σw − Σw²/Σw` denominator, the discriminating fixture is present with the controller's exact numbers
(6.0/8.0, 1.3416407864998738/2.0, 6/4.8), and the second fixture separates the three Kish readings
(6.0 mapping / 3.0 intersection / 4 count) with the intersection and count reading both asserted.
`CLAUDE.md`'s contrast invariant holds: `col_keys` is the intersection of both sides' completed
units, `n_paired` records it, `delta`, `cohens_d`, the draw pool and the Kish size are all taken over
that same set, and the interval is one joint draw over it rather than a difference of two intervals.
`E-DATA-WEIGHT-CONTRAST` is untouched and still fires (`validate.py:5020`); every new test calls the
comparison functions directly, so retirement at task 13 stays a per-test deletion.

**The one consumed-interface claim the record verdict rests on, checked against the code rather than
the brief.** Every new test stops at `_comparison_step_blocks`, so nothing exercises the trip to
`run.yaml`; task 8's brief asserts `assemble_run_yaml` "attaches a comparison block verbatim and
filters no keys". *Verified by reading:* `src/publishable/run_record.py:152` assigns the whole block
(`… ["vs_baseline"] = block`) and `:185` assigns the whole list (`out["contrasts"] = contrasts`) —
no key list, no reconstruction. *Corroborated:* `confounded`/`differs_on`, added conditionally at the
same site, are asserted in a parsed `run.yaml` at `tests/test_cli.py:2837-2846`, so a conditionally
added metric key surviving the trip has precedent rather than only a brief's say-so. `weighted_by`
and `n_paired_effective` will reach the record.

**Task quality: CHANGES REQUIRED.** Four Majors. Two are unpinned production threading discovered by
mutations the briefs did not prescribe, one of them under a test whose name claims exactly the
guarantee it does not make; one is a verification claim in the report that a one-line probe
falsifies; one is a stale docstring standing over the material tasks 7 and 8 changed — the same
family as the previous round's three Majors. Nothing found is a wrong answer in shipped arithmetic:
every mutation aimed at the weighting itself was caught, including one sharper than any brief
prescribed.

## Gates (run)

`uv run ruff check .` clean; `uv run ruff format --check .` 80 files; `uv run mypy` 45 source files
clean; `uv run pytest` **2145 passed, 1 skipped, 2 xfailed** — the expected counts.

## Findings

### Major 1 — `_compute_declared_contrasts`' `weights` threading is unpinned, under a test whose name claims it is pinned

*Verified by running.* `src/publishable/cli.py:1264` (`weights=weights` in the inner
`_comparison_step_blocks` call). Changed to `weights=None` and ran the **full** suite: **2145 passed,
1 skipped, 2 xfailed** — silent. `strata` on the same call site is unpinned for the same reason.

`tests/test_cli.py:9614` is named `test_the_three_comparison_functions_accept_weights_and_strata` and
its docstring says "The threading itself, at all three signatures". Its `_compute_vs_baseline` arm
does pin it (delta 6.0 vs 8.0), but its `_compute_declared_contrasts` arm asserts only
`out[0]["s"]["m"]["n_paired"] == 6` (`tests/test_cli.py:9656`) — true under any weighting, and true
if both keywords are dropped on the floor. This is `CLAUDE.md`'s "a test whose **name** claims the
guarantee" verbatim, and a reader greps for that name and stops looking.

Remedy is one line, and I confirmed it discriminates: calling `_compute_declared_contrasts` directly
with `weights=_W_WEIGHTS, weighted_by="sw", resample_columns=False` returns
`{'delta': 8.0, 'cohens_d': 2.0, 'weighted_by': 'sw', 'n_paired_effective': 4.8}`. Add
`assert out[0]["s"]["m"]["delta"] == pytest.approx(8.0)` beside the `n_paired` assertion.

### Major 2 — task 6's recorded "silent, task 13 catches it" is excused by a blocker that does not apply

*Verified by running.* `src/publishable/cli.py:2657` and `:2673`. Both `strata=resample_strata` →
`strata=None`, **full** suite: **2145 passed** — silent, as the report says. The report's and both
briefs' reason is that no weighted contrast reaches `run` until `E-DATA-WEIGHT-CONTRAST` retires at
task 13.

**That reason is false for the `strata` half.** `strata` reaches `paired_percentile_of_derived`
independently of `weights`, and the refusal's emit site (`src/publishable/validate.py:5020`) is gated
on `isinstance(weight_by, str) and weight_by` — so an **unweighted** config declaring
`statistics.resample.stratify_by` with a baseline, two conditions and a recorded numeric column
validates clean and runs today. Its contrast interval is precisely what decision 5 exists to fix, and
the suite already runs stratify_by configs through `run_a_project` with no `weight_by`
(`tests/test_cli.py:7318`, `:7389`) — adding a sweep to one of those shapes builds the missing pin.
So decision 5's production call sites are unpinned **now**, and the deferral is recorded against a
task that does not own it. Decision 5's own grounds call this the `hash_index` shape.

Two consequences: the report's mutation table entry is wrong on its reasoning (not on its observed
outcome), and the report's supporting evidence — 29 tests selected by `-k "weighted or strata or
resample"` — is filtered output offered as a silence claim, which is the one place `CLAUDE.md` says a
filter is not evidence. I re-ran it unfiltered; the silence is real, the excuse is not.

### Major 3 — the report's "structurally unreachable" for `weighted_cohens_dz`'s zero-denominator branch is false, and two docstrings claim a refusal no assertion makes

*Verified by running.* `src/publishable/stats.py:453-455`. The report says
"`weighted_cohens_dz([1.0, 2.0], [1, 0])` raises `ContractError` … so no fixture can reach that line."
That probes **one** candidate input and generalizes — the proxy shape `CLAUDE.md` § Answering a
question with a proxy names. Two legal weights (both positive and finite, so `checked_weights`
admits them) reach it through floating point:

```
weighted_cohens_dz([1.0, 2.0], [1e17, 1.0])   → None   (total 1e17, Σw²/total 1e17, denominator 0.0)
weighted_cohens_dz([1.0, 2.0], [1e300, 1e-300]) → None (Σw² overflows, denominator -inf)
```

I confirmed the denominator values directly, not only the `None`. The branch behaves correctly; what
is wrong is the claim about it, in three places: the report's mutation list, `weighted_cohens_dz`'s
docstring (`src/publishable/stats.py:440-442`, "and `None` for a zero denominator, which is all the
weight concentrated on one unit" — the stated cause is not the reachable one), and
`tests/test_stats.py:4046`, whose docstring says "Plus the one the weights add: a denominator of
zero" above two assertions covering only `len < 2` and zero dispersion. One line —
`assert weighted_cohens_dz([1.0, 2.0], [1e17, 1.0]) is None` — makes the docstring true. Task 8's
brief asked for exactly this check ("check that before adding a test that cannot fail"); the check
was made against one input and stopped.

### Major 4 — `_comparison_step_blocks`' docstring still describes the pre-task-7/8 column branch

*Verified by reading, and by running the direct call above.* `src/publishable/cli.py:799-804`: "A
recorded column takes `paired_t_over_units` over the per-unit differences, with `cohens_d =
cohens_dz(diffs)` … while `cohens_d` keeps computing from the local `diffs` list regardless." Under a
weight `cohens_d` is `weighted_cohens_dz(diffs, col_weights)` (`cli.py:1049-1053`), the delta is a
weighted mean (`:1035-1039`), and the `method` becomes `weighted_paired_percentile_over_units`
(`:1020-1024`). The direct call above returns `cohens_d: 2.0` — not `cohens_dz(diffs)` = 1.3416… —
so the sentence is false as written. The paragraph task 6 added says what `weights` **is** and never
what it **does** to the block, and none of the three record keys is mentioned in the docstring of the
function that writes them. Prefer deleting the `cohens_d = cohens_dz(diffs)` clause and naming the
weighted/unweighted split once, rather than layering a second sentence over it.

### Minor 5 — a comment names a variable that does not exist, and locates it positionally

`src/publishable/cli.py:1064-1065`: "**Kish is over the PAIRED INTERSECTION**, whose weights are
`entry_weights` below". There is no `entry_weights` anywhere in the file (grepped), and "below" is a
positional locator `CLAUDE.md` forbids. The brief shipped the text and the implementer copied it
unread. Remedy is deletion of the clause; the sentence is true and complete without it.

### Minor 6 — the `delta` comment still says "The mean"

`src/publishable/cli.py:1030-1034`. Its identity claim (point estimate and pool on the same roster)
survives weighting; its opening noun does not.

### Minor 7 — the amended task 6 docstring pins a half-delivered record shape without saying so

`tests/test_cli.py:9614-9628`. **The amendment itself is legitimate, and I checked it the way the
mandate asked.** Task 7's brief prescribes the weighted `delta` in prose ("The point estimate moves
too") and its Step 3 snippet carries no `resample_columns` condition; task 6's own brief scoped the
weights mutation to task 7 and said `weights` reaches nothing "at this commit". So the 6.0 assertion
rested on a premise its own brief flagged as temporary, and the edit made the test **stronger** — I
mutated `delta` back to bare `mean_of(diffs)` and this test now fails alongside
`test_a_weighted_column_contrast_weights_its_delta_and_its_draws`, i.e. it is the only pin on the
weighted delta at `resample_columns=False`. Not a failing test edited to match the code.

What the rewritten docstring does not say is that the path it now pins emits a weighted `delta` and a
weighted `cohens_d` beside an **unweighted** `paired_t_over_units` interval and `method` — the exact
combination `reference.md` § Contrasts forbids ("All four move together or none of them does"). Task
10's brief owns and names that gap, and it is unreachable through `run` while the refusal stands, so
it is not a shipped defect; but the pin should say which half is still owed and by whom.

### Minor 8 — `weighted_by`'s value is threaded correctly and pinned by nothing

*Verified by running.* `src/publishable/cli.py:1071` replaced with a literal
`"sampling_weight"`; **full** suite **2145 passed** — silent, because every fixture uses that one
string. The production threading is correct (the direct call above returns the `"sw"` I passed), so
this is an unpinned guarantee, not a wrong answer. One fixture naming a different attribute closes
it. Briefs 11-13 do not exist, so nothing schedules it.

### Minor 9 — the stratified-weighted test's docstring claims more than its floor discriminates

*Verified by running.* `tests/test_cli.py:9736` (`test_a_weighted_stratified_column_contrast_weights_inside_the_strata`) says "A closure built before the strata decision would weight over the wrong pool
and miss this bound." Under the mispairing mutation — the weight vector taken from `col_keys` instead
of the drawn keys, which is precisely weighting over the wrong pool — this test **passed**; only the
payoff test caught it. Its 7.0 floor separates weighted-stratified from unweighted and from
unstratified, which is what it is for, and not a mispaired vector. Non-blocking, since the sibling
test discriminates; the docstring should claim the two separations it actually makes.

### Minor 10 — task 8's brief predicted the wrong test count

Its Step 4 says "2138 + 5 = 2143" while prescribing six tests (three in `test_stats.py`, three in
`test_cli.py`). The report's 2139 → 2145 is the correct arithmetic. Noted so the next brief author
does not carry the 2143.

## Mutations I ran myself (eight; outcome, then what it proves)

| Mutation | Site | Result |
|---|---|---|
| `strata=strata` → `None` in the `_column_mean` call *(task 6's prescribed)* | `cli.py:1019` | **FAIL** — `test_a_contrasts_column_draw_honours_resample_stratify_by` and `test_a_weighted_stratified_column_contrast_weights_inside_the_strata`. As predicted |
| both `strata=resample_strata` → `None` *(task 6's prescribed second)* | `cli.py:2657`, `:2673` | **SILENT** on the full suite — Major 2 |
| `drawn = [1 for _ in column]` *(task 7's prescribed)* | `cli.py:998` | **FAIL** on `weighted["ci95"][0] > plain["ci95"][0]`, 3.0 > 3.0. As predicted |
| `drawn` built from `col_keys` instead of `table.unit` *(mine — the sharp one)* | `cli.py:998` | **FAIL**, 2.333 > 3.0. The closure's central claim — the vector follows the **drawn** keys, not the roster — is genuinely pinned, and by more than the uniform mutation |
| `delta` back to bare `mean_of(diffs)` *(task 7's prescribed)* | `cli.py:1035` | **FAIL** — both the payoff test and the amended task 6 test |
| Kish argument → `list(weights.values())` *(task 8's prescribed)* | `cli.py:1073` | **FAIL** — `test_kish_is_taken_over_the_paired_intersection_not_the_weight_mapping` (6.0 vs 3.0), while `test_a_weighted_contrast_entry_carries_the_three_documented_keys` stayed green. Exactly as the brief predicted, and why the second fixture exists |
| `if weights is not None:` → unconditional key writing *(mine)* | `cli.py:1070` | **FAIL** — but only `test_a_weighted_contrast_entry_carries_the_three_documented_keys`, on `"weighted_by" not in plain`. The derived-branch test does **not** discriminate it (mandate item 4); adequate only because the emit site is shared by both branches, which it is |
| delete the sorted-`keys` guard *(mandate item 6)* | `stats.py:1272-1279` | **FAIL** — `test_an_unsorted_key_list_with_strata_is_a_core_defect`. Task 5's two properties both survive task 7's edit: `paired_percentile_of_derived` still takes `strata`, and the contract is enforced, not merely documented |

`weighted_by` hardcoding (Minor 8) and the `_compute_declared_contrasts` drop (Major 1) were the two
further mutations, both run against the full suite because a silence claim admits no filter.

**Three of the report's mutations I accepted by reading the named test's body rather than by
running**, and each is decidable in a sentence: task 7's derived-branch `method` mutation — the
derived test (`tests/test_cli.py:9695`) asserts the exact unweighted spelling and, separately, the
unweighted delta, so the failure is attributable to the string; task 8's `cohens_d` → bare
`cohens_dz(diffs)` — `tests/test_cli.py:9764` holds 2.0 and 1.3416407864998738 apart **in the same
test**, so the mutation collapses two readings the test separates; task 8's `denominator` → `total` —
at w ≡ 1 the mutant divides by 6 where the oracle needs 5, a 9.5 % gap far outside `pytest.approx`'s
default tolerance, so `test_a_weighted_dz_at_equal_weights_is_the_unweighted_one` cannot survive it.
The eight above are what I ran; these three are what I checked by reading.

## Mandate item 4, answered directly

The report's claim is confirmed by reading: task 8's brief writes
`test_a_weighted_derived_contrast_carries_the_record_keys_without_a_weighted_method` calling
`_comparison_step_blocks` **directly**, so `_weighted_contrast_block`'s `setdefault` never applies,
`weighted_by` defaults to `None`, and the brief's own `entry["weighted_by"] == "sampling_weight"`
cannot pass. The implementer's fix (adding the keyword) is right. With the keyword supplied that test
does **not** by itself discriminate a record that writes the keys unconditionally — proven by the
mutation above. Its sibling at `tests/test_cli.py:9764` does, via `"weighted_by" not in plain`, and
one shared emit site means one guard is enough. No change required, but the derived test's docstring
should not be read as covering absence.

## Could not check

- **Whether the `weighted_by` key can be written as `null` in a real record.** `command_run` passes
  `weighted_by=weight_by if weights else None` (`cli.py:2658`, `:2674`) while the emit site guards on
  `weights is not None` (`:1070`); the two disagree for an empty mapping. I could not construct a
  config that both builds `weights = {}` and reaches a metric block, and I do not believe one exists.
  Recorded rather than filed.
- **Task 9's and task 10's obligations** (the corrected bound under a weight, and the weighted
  general-case interval) are out of this batch's scope and were not assessed beyond confirming their
  briefs name the gaps Minor 7 describes.
- **No file among the four documents was touched by these three commits** (the diff is `cli.py`,
  `stats.py`, the two test files, and two records), so neither consistency pass had anything to run
  against. The `reference.md` text the new tests parse — the `weighted_paired_percentile_over_units`
  construction row and § Contrasts' `n_paired_effective` prose — was verified present and consistent
  with what the code emits.
