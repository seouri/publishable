# Task 4 review — `_check_resample`, the `method` enum and the 80-draw floor

**Spec compliance: ✅**
**Task quality: findings** — 1 Important, 5 Minor. Nothing Critical.

Verified at `28c257e`: `uv run pytest` → **1702 passed, 2 xfailed**; `ruff check .` clean; `mypy` clean
(42 files). Tree left clean; every mutation below was reverted by editing in place and the full suite
re-run afterwards.

## What was verified by behaviour

| Claim | How checked | Result |
|---|---|---|
| Call site is after `_check_sweep`, before `_check_contrasts` | read `validate_config` | Placed as specified |
| Floor is exactly 80 | `min_honest_draws(0.95)` = `ceil(2/0.025)` = 80 | ✓ |
| Boundary tested on both sides | `n < floor` → `n <= floor` mutation | `test_a_resample_n_at_the_floor_is_accepted` FAILS — the off-by-one is caught |
| Brief's own mutation | `n < floor` → `n < 1` | `[79]` and the message test FAIL, `[0]`/`[-1]` pass — as designed |
| New checks reachable at this commit | deleted the `_check_resample(...)` call | 5 of 8 resample tests FAIL |
| `n` type guard bites | `isinstance(n, int) and not isinstance(n, bool)` removed | `TypeError` at validate.py:5032, wrong-type test FAILS |
| Implementer's double-report claim | reverted the guard to the brief's `not isinstance(method, str) or ...` | `E-STATS-RESAMPLE-METHOD` fires on `method: 5` alongside `E-CONFIG-TYPE` — the double-report was **real**, and the corrected test **bites** |
| Implementer's "the original test passed vacuously" claim | `git show 28c257e -- tests/test_validate.py` | The `60e7aab` body asserted only `E-CONFIG-TYPE` + `E-STATS-RESAMPLE-UNSUPPORTED`; the `assert "E-STATS-RESAMPLE-METHOD" not in found` line is new in `28c257e`. Claim confirmed |
| `n: true` really is `E-CONFIG-TYPE` (the bool comment's premise) | probe config | `envelope._is_type` special-cases `bool` (`if isinstance(value, bool): return bool in allowed`), so codes are `['E-CONFIG-TYPE', 'E-STATS-RESAMPLE-UNSUPPORTED', ...]`. The comment is accurate and the guard opens no hole |
| Nothing claims resample is honoured | read both docstrings and the call-site comment | Docstring explicitly says `E-STATS-RESAMPLE-UNSUPPORTED` still refuses the block wholesale; probes confirm every resample config still carries it |
| Fixture defect touched this task? | probe printed codes for four resample configs | `E-UNITS-ATTR-MISSING` present in all → `roster is None` confirmed. `_check_resample` never reads `roster`; the floor and enum findings still fire (e.g. `{"resample": {"n": 50}}` → `E-STATS-RESAMPLE-N`). **No assertion in this task depends on a resolved roster** |
| Unguarded reads remaining | read the function | None. `resample` (dict), `method` (str), `n` (int, non-bool) are the only values read |
| Citations resolve | `reference.md` line 2331 | The *Resample methods* table both docstrings and the Errors row cite **exists**; `#statistical-reporting` resolves |

Mechanical pass on `reference.md`: both new rows are 2-column, matching their headers; no trailing
whitespace, tabs or invisible unicode introduced; the two Errors rows sort correctly
(`E-STATS-REPORTBY-UNKNOWN` < `E-STATS-RESAMPLE-METHOD` < `E-STATS-RESAMPLE-N` < `E-SWEEP-*`); the
§ Validation row sits beside *Clusters enough to resample*. Read the full prose above both tables
rather than grepping: the Errors intro's only count phrase ("Five faults return `validate_config`
early") names early-return codes, untouched by the insertion; the § Validation intro carries no count
and no positional row reference. `-UNSUPPORTED` correctly **not** added to the registry.

## Findings

### Important

**1. The call-site comment justifies the placement with two dependencies the placement does not
create — and spec decision 5 carries the identical claim.** This is the interface documentation
tasks 5–8 will read.

```
# ... the strata check needs the resolved roster and the declared attributes,
# and the `n` bound needs the resolved comparison family, which `_check_sweep`
# is the first thing to compute.
```

Both halves are false as stated:

- `roster` comes from `_check_units` and is already handed to `_check_fold_stratify_by`, which runs
  **three calls earlier** (`_check_fold_stratify_by` → `_check_replication` → `_check_unimplemented`
  → `_check_sweep`). Roster availability does not discriminate this position from any position after
  `_check_units`.
- `_check_sweep(doc, template, c, *, fold_basis) -> None` returns nothing and stores nothing on `doc`.
  The "resolved comparison family" is **not** handed to `_check_resample`; task 6 must recompute it
  (`expand(doc)` / the same derivation `_check_sweep` uses), which is position-independent.

The placement itself is harmless and I would not move it — grouping with the other `statistics.*`
checks and ordering the findings sensibly is a real, if smaller, reason. The defect is the stated
justification, which is exactly the repo's recurring "comment claiming a guarantee the code does not
provide" class, aggravated by being read as instruction by four downstream tasks: a task-6 implementer
reading it may expect the family to be in hand. Fix the comment **and** the spec's decision-5 row to
say what the position actually buys, and to state that the family must be recomputed locally.

### Minor

**2. `test_a_resample_n_at_the_floor_is_accepted` is absence-only.** Deleting the `_check_resample`
call site leaves it green (verified). It does catch the `n <= floor` off-by-one, so it is not a check
that cannot fail — but the repo's rule puts the positive companion *in the same test*, and both
wrong-type tests in this same block do carry one (`assert "E-STATS-RESAMPLE-UNSUPPORTED" in found`).
One line fixes it.

**3. The `bool` exclusion is untested.** Changing the guard to `isinstance(n, int) and n < floor`
(dropping `not isinstance(n, bool)`) leaves all 9 resample tests green (verified). That branch guards
against precisely the defect task 4's own fix commit was about — a leaf already flagged
`E-CONFIG-TYPE` also driving this code — so it deserves the same test `method: 5` got:
`n: true` → `E-CONFIG-TYPE` present, `E-STATS-RESAMPLE-N` absent.

**4. `method: null` / absent-method acceptance is documented and untested.** The Errors row promises
"Unset (`null`) is accepted and takes the documented default" and the code comment says only a value
actually named is checked. Behaviour is correct (probe: `{"resample": {"n": 50}}` yields no
`E-STATS-RESAMPLE-METHOD`), but no test pins it; a mutation dropping `method is not None` would be
caught only incidentally, since `None not in RESAMPLE_METHODS`.

**5. Docstring: "the same division `_check_report_by` keeps with the envelope: this checks values,
not types" is half true.** `_check_report_by` reports a *non-string* `report_by` entry under its own
`E-STATS-REPORTBY-UNKNOWN` — it type-checks under its own code. The claim holds only for
envelope-typed leaves (`limits.min_reported_n`), which is the case the envelope covers because
`statistics.report_by`'s *elements* are not in `LEAF_TYPES` while `statistics.resample.method` is.
The sentence is defensible in spirit but reads as a stronger symmetry than exists; narrowing it to
"a leaf the envelope types" would be exact.

**6. The change is not reflected in § The one config file's `statistics.resample` line.** The schema
block shows `resample: null  # NOT BUILT; bootstrap / {method: bootstrap, n: 2000, stratify_by: []}`.
Two cross-document classes touch it now that `method` is a stated, validate-enforced enum and `n` has a
refusal floor: *Enum comments* (an inline comment must list every value its section defines — here one
value, so a `# bootstrap` enum marker in the style of `correction: none | bonferroni | holm | fdr_bh`)
and the fact that nothing near the schema, or near § Statistical reporting's "Declaring `resample` then
changes the method or the count rather than switching the behaviour on", says the count has a minimum.
The floor is stated only under *Below 80 surviving draws core reports no interval*, which is about
*surviving* draws at run time, not about a declared `n` validate now refuses.

### Cross-document sweep run for this review (clean)

- `grep -n resample` over all five tracked docs: **no example anywhere declares `n` below 80** — every
  one is `n: 2000`, including all six configs in `feasibility-llm-growth-studies.md`. The new refusal
  contradicts no dated build claim in § Executability on this build (which reports
  `E-STATS-RESAMPLE-UNSUPPORTED` for 8 of 9, still true).
- Count-phrase sweep over `git ls-files '*.md'` (file list filtered, never the output) for
  `<number> (codes|rows|checks|refusals|errors|identifiers|entries)`: no hit counts either table the two
  insertions grew. `reference.md`'s "two codes" (line 405) names a specific pair, and "apart from those
  same two envelope rows" counts envelope rows, not table rows.

### Confirmed, not a finding for this task

The `_RESAMPLE_UNITS` fixture defect is real (`index.csv` is `patient_id\np1\n`, `attributes:
["cohort"]` → `E-UNITS-ATTR-MISSING`, `roster is None` in all eight tests) and **is** harmless here:
verified by probe that no assertion in this task's tests reads a roster-derived finding, and that the
enum and floor checks fire identically. The implementer flagged it unprompted for tasks 5 and 8, where
it would make the declared-attribute and cluster-count checks pass vacuously. That hand-off is correct
and should be honoured before task 5 starts.
