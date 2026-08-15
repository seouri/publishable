# Whole-branch review — S4b `contrasts` (branch `s4b-contrasts`)

> **RE-REVIEW at `d082a36` — VERDICT: APPROVED FOR MERGE.** See
> [§ Re-review](#re-review-at-d082a36). The original review below is retained unedited as the
> record of what was found at `fba4040`.
>
> **REVIEW OF `d9e3f7f` (N9/N10 fixes) — VERDICT: CHANGES REQUIRED.** One regression, one-line
> fix. See [§ Review of d9e3f7f](#review-of-d9e3f7f).
>
> **CONFIRMATION AT `f786b79` — VERDICT: APPROVED FOR MERGE.** R11 closed; no findings remain.
> See [§ Confirmation of f786b79](#confirmation-of-f786b79) at the end of this file.

---

# Original review (0fc2a6f..fba4040)

**VERDICT: CHANGES REQUIRED**

One Critical (a contrast whose `ci95` cannot contain its own `delta`, reproduced end to end
through `main(["run", ...])`), three Important, three Minor.

Gate commands, run on a clean tree at `fba4040`:

```
uv run pytest      679 passed
uv run ruff check .  All checks passed!
uv run mypy        Success: no issues found in 35 source files
```

Purity holds. `contrasts.py` imports only `dataclasses`/`typing`, with `Condition` and `UnitList`
under `TYPE_CHECKING`; `stats.py`'s new functions touch no filesystem and import nothing from
`config`/`artifacts`/`runner`/`cli`; `sweep.py` is untouched by the diff. `validate.py`'s
`_check_contrasts` collects and never raises — its `expand(doc)` call is unguarded, but
`_check_sweep` already calls `expand(doc)` unconditionally at `validate.py:908` immediately
before it, so `_check_contrasts` adds no new raise path. Nothing was found wrong with
`paired_keys`, `paired_t_over_units`, `cohens_dz`, or `paired_percentile_of_derived` itself; the
one-draw-both-sides pairing and the `compute_of`/`compute_against` split are correct and are
pinned by tests that would fail against the wrong spellings.

All findings below were reproduced against `fba4040` with the tree clean. Two mutations were
applied and reverted with `git checkout --`; `git status --porcelain` is empty.

---

## Critical

### C1. A derived metric's `delta` is a difference of the two conditions' whole-sample aggregates, not a paired estimate over the intersection — so a `within` contrast reports a point estimate outside its own interval

`src/publishable/cli.py:250-257`

```python
                of_value = of_summary[metric_key].get("value")
                against_value = against_summary[metric_key].get("value")
                delta = (
                    float(of_value) - float(against_value)
                    if of_value is not None and against_value is not None
                    else None
                )
```

`of_summary` is `aggregated[comp.of][step_name]` (`cli.py:224-225`) — the value `aggregate`
produced over **that condition's own completed units**, the full roster, with no knowledge of
`comp.within` and no knowledge of the other side's completions. The interval on the very next
lines is built by `paired_percentile_of_derived(of_collapsed, against_collapsed, base_keys, ...)`
where `base_keys = paired_keys(of_collapsed, against_collapsed, allowed)` (`cli.py:223`) — the
intersection, narrowed by the stratum. The two halves of the same record entry are computed over
different unit sets.

The column branch fifteen lines below gets this right — `"delta": mean_of(diffs)` over
`col_keys ⊆ base_keys` (`cli.py:268-280`) — which is what makes this a defect rather than a
design choice: two branches of one function disagree about what a contrast is computed over.

`docs/reference.md`:2087 is the indictment verbatim: *"a paired comparison exists only for units
that completed in **both**. Differencing the two condition means instead would not be a paired
comparison at all, however carefully `paired: true` was derived."* And CLAUDE.md's invariant
list: *"a contrast … is computed over the intersection of both sides' completed units, recorded
as `n_paired` — and its interval is its own construction over that intersection."* The interval
obeys this; the point estimate does not.

**Failure scenario (reproduced).** Probe run through `run_a_project` → `main(["run", ...])`:
20 units, `cohort` alternating `a`/`b`, a step recording `pred = 0.0` for cohort `a` and `100.0`
for cohort `b`, a template `aggregate` returning `score = k · mean(pred)` with `k = 1.0` under
`analysis.method: pearson` and `2.0` under `spearman`, and one declared contrast
`{id: stratum_a, of: "method=spearman", against: baseline, within: {cohort: a}}`. The run
completed `EXIT_OK` and wrote:

```yaml
results:
  contrasts:
    - id: stratum_a
      of: 01_method=spearman
      against: 00_baseline
      step01_summarize_units:
        score:
          delta: 50.0                 # 2·mean(pred over ALL 20) − 1·mean(pred over ALL 20)
          basis: units
          paired: true
          method: paired_percentile_over_units
          n_paired: 10                # the cohort-a half
          ci95: [0.0, 0.0]            # correct for the stratum: pred is 0.0 on every cohort-a unit
          cohens_d: null
          correction: null
```

The stratum-restricted delta is exactly `0.0` (every cohort-`a` unit has `pred = 0.0`, so
`2·0 − 1·0 = 0`). The record states `delta: 50.0` with `ci95: [0.0, 0.0]`. An interval that
cannot contain its point estimate — the same class as, and a sibling of, the Critical
`progress.md` records at Task 7, which fixed the *interval* side and left the *point estimate*
side untouched.

Three distinct manifestations, one root cause:

1. **`within` derived contrast** — reproduced above. Whole-sample delta beside a stratum-only
   interval.
2. **Unequal completion** — two conditions completing on different units (a transform not
   constructible for every unit, an arm whose eligibility differs) give a delta over
   `completed(of) ∪̸ completed(against)` and a `ci95` over the intersection. This is exactly the
   case `reference.md`:2087 exists for.
3. **Empty intersection** — `base_keys == []` ⇒ `n_paired: 0`, `ci95: null`, but `delta` is still
   the nonzero whole-sample difference. `reference.md`:2087: *"A contrast whose intersection is
   empty is reported as such rather than as a delta of zero."* It is reported as worse than zero:
   a confident nonzero number with no denominator.

**Fix.** Compute the derived delta from the paired intersection, not from `aggregated`: evaluate
`compute_of` over `_unit_table_from_rows([{"unit": k, **of_collapsed[k]} for k in base_keys])`
and `compute_against` over the same keys on `against_collapsed`, and difference those — the
draw-zero case of what `paired_percentile_of_derived` already does internally. When
`base_keys` is empty or either side's `compute` is unavailable, `delta` is `None`, not a number.
Note this removes the derived branch's dependence on `aggregated` **for the point estimate only**
— `of_summary`/`against_summary` still drive the metric loop at `cli.py:229`
(`sorted(set(of_summary) & set(against_summary))`) and must stay there.

**Test to add.** The probe above, asserting `entry["delta"] == pytest.approx(0.0)` and
`low <= delta <= high`. `tests/test_cli.py:840` (`test_a_derived_contrast_resamples_each_side_
with_its_own_formula`) cannot catch this: it uses no `within` and both conditions complete on all
40 units, so the whole-sample delta and the paired delta coincide at 19.5. That is precisely a
test that stays green against the wrong implementation.

---

## Important

### I2. A documented `validate` refusal was skipped: a contrast whose two sides are the same condition

`src/publishable/validate.py:983-1020`

`reference.md`:270, in the § Validation table, three rows above the two rules `_check_contrasts`
*did* implement (`:269` → `E-STATS-CONTRAST-UNKNOWN`, `:272` → `E-STATS-CONTRAST-WITHIN`):

> | Contrast has two distinct sides | `statistics.contrasts[1]` sets `of` and `against` to the same condition |

`_check_contrasts` checks `of` and `against` independently and never compares them.

**Failure scenario (reproduced).** `statistics.contrasts: [{id: selfie, of: baseline, against:
baseline}]` over a two-condition sweep validates clean (`0 errors`), the run exits `EXIT_OK`, and
`run.yaml` carries:

```yaml
results:
  contrasts:
    - id: selfie
      of: 00_baseline
      against: 00_baseline
      step01_summarize_units:
        pred: {delta: 0.0, basis: units, paired: true, method: paired_t_over_units,
               n_paired: 20, ci95: [0.0, 0.0], cohens_d: null, correction: null}
```

A perfect null over 20 units with a zero-width confidence interval, published as a finding. Under
S4c it will also consume a slot in the correction family and tighten every other interval in the
run. The refusal that would have prevented it is one line of the same function that already
resolves both labels.

**Fix.** In `_check_contrasts`, after both sides resolve, refuse `entry["of"] == entry["against"]`
(compare resolved labels, not raw strings, so the same condition named two ways is caught too).
Mint the identifier only after grepping `docs/reference.md` — `reference.md`:270 states the rule
but names no code, so this needs the same `docs/superpowers/spec-defects.md` entry
`E-STATS-CONTRAST-WITHIN` got at `spec-defects.md`:1526. Pin it with a
`tests/test_validate.py` case through `validate_config`.

### I3. A malformed `statistics.contrasts` entry validates clean and crashes `run` with a traceback

`src/publishable/contrasts.py:60-68`

```python
        out.append(
            Comparison(
                id=str(entry.get("id")),
                of=by_label[entry["of"]],
```

`_check_contrasts` skips anything that is not a dict — `if not isinstance(entry, dict): continue`
(`validate.py:990-991`) — and nothing else in `validate.py` type-checks the `statistics` block
(grepped: `statistics` appears at `validate.py:25, 34, 622-736, 939, 948-1016`, none of it a
shape check). `resolve_contrasts` then calls `.get`/`__getitem__` on whatever the list holds.

Before this branch the whole block was refused by `E-STATS-CONTRASTS-UNSUPPORTED`, so this path
did not exist. Retiring the refusal (Task 6) opened it and Task 7 did not close it.

**Why Important and not Critical.** This is a regression on a path this branch opened, which is
the Critical class the brief names — but it is graded one step down deliberately: the failure is
*loud*. `run` aborts with a traceback and a nonzero exit, no `run.yaml` is written, and no wrong
number is published. The Criticals this project has shipped are the opposite shape — a plausible
number in a completed record that nobody can tell is wrong. If a reviewer prefers the class over
the consequence, promote it; it must be fixed before merge either way.

**Failure scenario (reproduced).** `statistics: {contrasts: ["method=spearman"]}` — a plausible
YAML slip, a list of labels instead of a list of mappings. `validate` reports
`1 problem (0 errors, 1 warning)`; `run` then dies:

```
AttributeError: 'str' object has no attribute 'get'
src/publishable/contrasts.py:62: AttributeError
```

An uncaught traceback out of `publishable run`, which is the shape every other check in
`validate.py` exists to prevent, and the reason `contrasts.py:56-59`'s own comment says the
`KeyError` is acceptable "only because validate refuses that at validate time" — the guard the
comment relies on does not cover this entry.

**Fix.** In `_check_contrasts`, replace the silent `continue` on a non-dict entry with an error
(reuse `E-STATS-CONTRAST-UNKNOWN` with a shape message, or mint one and record it in
`spec-defects.md`). Refuse a non-list `statistics.contrasts` the same way. Add a
`tests/test_validate.py` case for each.

### I4. `W-STATS-CONTRAST-THIN` is applied more broadly than the spec scopes it, and the identifier is pinned by no test

`src/publishable/cli.py:289-295`, `tests/test_cli.py:995-1009`

Two problems in one place.

**(a) Scope.** `reference.md`:2068: *"`limits.min_reported_n` applies to a `within` contrast's
`n_paired`, since a stratified paired comparison is where a small denominator is easiest to miss
and most disclosive."* `reference.md`:155 says the same in the config comment (*"a stratum or
`within` contrast this small"*), and `reference.md`:273 gives the example as a `within` row. The
implementation warns for **every** comparison, per step, per metric:

```python
            if min_reported_n is not None and n_paired < min_reported_n:
                findings.warn("W-STATS-CONTRAST-THIN", ...)
```

`materialize.py:153` writes `min_reported_n: 10` into every generated config, so any ordinary
baseline sweep over fewer than 10 completed units — the default `run_a_project` fixture size, and
a normal pilot — emits a disclosure warning for a comparison the spec never scoped it to. Worse,
`tests/test_cli.py:995` (`test_a_thin_pairing_warns`) uses **no** `within` at all, so the test
pins the over-broad behaviour: narrowing to `comp.within is not None` would turn it red.

Per CLAUDE.md the document leads, so the fix is to gate the warning on `comp.within is not None`
and rewrite the test to declare a `within` stratum. If the broader scope is judged better, it is
a document change first plus a `spec-defects.md` entry — but it cannot stay as an undiscussed
divergence from three passages.

**(b) The identifier is untested.** `test_a_thin_pairing_warns` asserts only:

```python
    assert "min_reported_n" in doc["stdout"] or "N_PAIRED" in doc["stdout"]
```

Both the `where` field (`"limits.min_reported_n"`) and the message body contain the substring
`min_reported_n`, so the assertion never touches the code. **Mutation verified:** I renamed
`"W-STATS-CONTRAST-THIN"` → `"W-STATS-CONTRAST-XYZZY"` in `cli.py:291` and ran the full suite —
**679 passed**, unchanged. Reverted with `git checkout -- src/publishable/cli.py`;
`git status --porcelain` empty. Any other diagnostic mentioning `limits.min_reported_n` would
also keep it green.

This violates the plan's Global Constraint *"Every `E-`/`W-` identifier must have a test that
produces it."* Separately, `W-STATS-CONTRAST-THIN` appears in **no document at all** — not
`reference.md` (whose diagnostic listing at `:2616` carries `W-STATS-FAMILY`), and not
`spec-defects.md`, which the branch correctly used for `E-STATS-CONTRAST-WITHIN` at `:1526`. A
new `W-` code with no home in the four documents and no spec-defects entry is exactly the drift
CLAUDE.md's "the document changes first" rule exists to catch.

**Fix.** Assert the literal `"W-STATS-CONTRAST-THIN"` in the test; scope the warning to `within`
contrasts; add the identifier to `spec-defects.md` (or to `reference.md`'s diagnostic listing)
saying which document sentence it implements.

---

## Minor

### M5. `confounded: true` is documented on a contrast entry and is emitted by nothing

`src/publishable/cli.py:243-287` builds every metric entry without a `confounded` key.
`reference.md`:2070 (*"A contrast crossing two axes is marked `confounded: true`"*), `:953` (the
worked entry shape), `:1444`, and `:268` (a documented `validate` **warning**) all describe it.
Multi-axis grids are expressible today — `sweep.expand` takes `itertools.product` over
`grid.items()` (`sweep.py:151-159`) — so `sweep: {baseline: {a: x, b: y}, grid: {a: [...],
b: [...]}}` produces conditions differing from the baseline on two axes, and this branch now
emits a `vs_baseline` entry for each of them with no marker and `paired: true`. The design spec
(`docs/superpowers/specs/2026-08-10-contrasts-design.md`:21) does not list `confounded` in S4b's
scope, which is a defensible call — but CLAUDE.md's *"unimplemented must mean refused"* means it
needs a `spec-defects.md` entry naming the slice that closes it, not silence. Graded Minor only
because the omission predates the entry shape rather than corrupting a number.

### M6. `statistics.contrasts` assigned work in `spec-defects.md` was neither done nor reassigned

`docs/superpowers/spec-defects.md`:1521 assigns `limits.max_ineligible_fraction` to **S4b**
("with the rest of the limits work") and notes that `min_reported_n` was unreachable only because
`within` was refused. This branch made `within` reachable and closed `min_reported_n`, but
`max_ineligible_fraction` is still written by `materialize.py:150` and read by nothing (grepped:
it appears in exactly one `src/` line). The entry was not updated. Either close it or move the
assignment to S4c in the same file.

### M7. A missing `id` becomes the literal string `"None"` in the record

`src/publishable/contrasts.py:62`: `id=str(entry.get("id"))`. `_check_contrasts` never requires
`id`. **Reproduced:** `statistics: {contrasts: [{of: "method=spearman", against: baseline}]}`
validates clean and `run.yaml` carries `results.contrasts: [{id: 'None', of: 01_method=spearman,
against: 00_baseline}]`. Two such entries collide on the same id. `progress.md` records this as a
deferred Task 1 minor; it is recorded there as *deferred*, not fixed, and it now reaches a
published artifact, so it is re-raised here. Refuse a missing or non-string `id` in
`_check_contrasts`.

### M8. `is_derived` is true when a metric is derived on only one side

`src/publishable/cli.py:230`: `is_derived = metric_key in of_derived or metric_key in
against_derived`. If a metric is a template-derived value under one condition's `cfg` and a
recorded column under the other's, the derived branch is taken, `compute_against` is `None`
(`cli.py:234-236`), and the entry records `method: null` / `ci95: null` beside a computed `delta`.
Likely unreachable with core's single `generic` template and only reachable via an `aggregate`
that returns a key conditionally on `cfg`, which is why this is Minor — but the condition should
be `and`, or the mismatch should be a `W-` finding rather than a silently interval-less entry.

---

## Things checked and found sound

- **The pairing itself.** `paired_percentile_of_derived` draws once (`drawn = [keys[rng.randrange(n)] for _ in range(n)]`) and applies the single draw to both sides; the `compute_of`/`compute_against` split fixes the Task 7 Critical correctly and `tests/test_cli.py:840` pins the call site through `main(["run", ...])`, not only `stats.py`.
- **`paired_keys`** is the sorted intersection, narrowed by `allowed`; the union and either side alone are all separately pinned in `tests/test_stats.py`.
- **`cohens_d`** is `None` on every derived entry (`cli.py:275`) and a real float on every column entry, matching CLAUDE.md's `cohens_d: null` rule for `r`.
- **`n_paired`** for a column metric counts `col_keys` (units where the metric exists on both sides), not `base_keys` — correctly narrower.
- **Absent, not empty.** `_compute_vs_baseline`/`_compute_declared_contrasts` return `None` rather than `{}`/`[]`, `run_record.py:108-118` and `:148-153` omit the keys, and `tests/test_cli.py:974` exercises the discriminating case (a baseline exists but every metric block is empty) rather than only the no-baseline one.
- **`Comparison.declared`** is a real flag read by both callers, and `tests/test_cli.py:927`/`:944` pin both placement and the non-displacement of the unrestricted `vs_baseline` block.
- **`E-STATS-CONTRASTS-UNSUPPORTED`** is gone from `src/`, `tests/`, and the four documents; the surviving hits are in plans and spec files, which is correct.
- **`test_the_delta_interval_matches_this_fixture_s_own_arithmetic`** (`tests/test_cli.py:1060`) asserts an exact hand-derived half-width of 0.0907577 rather than `hi > lo`, and `test_a_paired_delta_is_narrower_than_the_conditions_it_compares` uses a `/10` ratio with a measured ≈70× margin. Both are genuinely discriminating.

---

# Re-review at `d082a36`

**VERDICT: APPROVED FOR MERGE**

`git diff fba4040..d082a36` — one commit, `d082a36` "Compute a derived contrast's estimate where
its interval lives", 415 insertions across `cli.py`, `stats.py`, `validate.py` and three test
files. (`docs/superpowers/` is gitignored in this repo — `git check-ignore` confirms — so the
`spec-defects.md` changes are real on disk but absent from the diffstat. I read them directly.)

Gate commands at `d082a36`, clean tree:

```
uv run pytest      691 passed
uv run ruff check .  All checks passed!
uv run mypy        Success: no issues found in 35 source files
```

Two mutations applied and reverted with `git checkout --`; `git status --porcelain` empty at the
end of each and at the close of this review.

## Per-finding disposition

| # | Finding | Disposition |
|---|---|---|
| C1 | Derived delta over a different unit set than its interval | **ADDRESSED** — verified on all three manifestations, one of which no test covers |
| I2 | Self-contrast not refused | **ADDRESSED** |
| I3 | Malformed entry crashes `run` | **ADDRESSED** |
| I4 | `W-STATS-CONTRAST-THIN` over-broad and untested | **ADDRESSED** — mutation now goes red |
| M5 | `confounded: true` emitted by nothing | **ADDRESSED** (recorded, assigned to S4c) |
| M6 | `max_ineligible_fraction` assigned to S4b and untouched | **ADDRESSED** (reassigned to S4c, S4a carry row updated) |
| M7 | Missing `id` published as `'None'` | **ADDRESSED** (folded into `E-STATS-CONTRAST-SHAPE`) |
| M8 | `is_derived` uses `or` | **NOT ADDRESSED, accepted** — the recorded reasoning (`and` routes the same case to a null entry by another route) is correct; either spelling yields an entry with no interval, so nothing is silent |

### C1 — ADDRESSED, all three manifestations verified

`stats.paired_delta_of_derived` (`stats.py:248-288`) evaluates each side's `compute` over the
same `keys` list the interval is built from and returns `None` — never `0.0` — on an empty
`keys`, a raising compute, a `None` compute, or a nan. It is pure (no filesystem, no
`config`/`artifacts`/`runner`/`cli` import). `cli.py:255-276` calls it and
`paired_percentile_of_derived` from one guarded block over the same `base_keys`, and the old
`of_summary`/`against_summary` differencing is gone. `of_summary`/`against_summary` correctly
remain at `cli.py:229` driving the metric loop — the scoping caveat in my C1 fix instruction was
respected.

**(1) `within` stratum — verified.** Re-ran my original C1 reproduction verbatim (20 units,
`pred = 0.0` on cohort `a` and `100.0` on cohort `b`, `score = k·mean(pred)`, contrast
`within: {cohort: a}`). At `fba4040` this recorded `delta: 50.0` beside `ci95: [0.0, 0.0]`. At
`d082a36`:

```yaml
score: {delta: 0.0, n_paired: 10, ci95: [0.0, 0.0], method: paired_percentile_over_units,
        cohens_d: null, correction: null}
```

`low <= delta <= high` now holds.

**(2) Unequal completion — verified, and this is the manifestation no test covers.** Probe: 20
units, `pred = float(i)` under both conditions, but the step calls `io.skip` on roster indices
0-9 under `spearman` only, so the two conditions complete on different unit sets;
`score = k·mean(pred)`. The record:

```
aggregated  00_baseline        score: 9.5   (n.completed 20)
aggregated  01_method=spearman score: 29.0  (n.completed 10, ineligible 10)
vs_baseline 01_method=spearman score: {delta: 14.5, n_paired: 10, ci95: [12.7, 16.3]}
```

`14.5` is the correct paired value (`2·14.5 − 1·14.5` over the ten shared units) and the interval
brackets it. The old code would have recorded `29.0 − 9.5 = 19.5`, which is **outside** `[12.7,
16.3]` — so this case was a live point-estimate-outside-its-interval defect and is now closed.

**(3) Empty intersection — verified.** Same fixture with `within: {cohort: z}`:
`{delta: null, n_paired: 0, ci95: null, method: null}` for every metric, plus a
`W-STATS-CONTRAST-THIN` warning. `reference.md`:2087 ("reported as such rather than as a delta of
zero") is satisfied — `None`, not `0.0`.

**Mutation check on the call site.** I changed `cli.py`'s delta call from `base_keys` to
`sorted(of_collapsed)` — the minimal reintroduction of the whole-sample bug — and the suite went
**689 passed, 2 failed**, killing both `test_a_stratified_derived_delta_is_computed_over_its_own_
intersection` and `test_a_derived_contrast_over_an_empty_stratum_reports_no_delta`. Reverted;
tree clean. The two new end-to-end tests are genuinely discriminating: the fixture's stratum
delta is 10.0 against a whole-sample 509.5, a 51× separation, so no rounding or seed choice can
make them coincide.

### I2 — ADDRESSED

`validate.py:1048-1056` adds `E-STATS-CONTRAST-SAME-SIDES`, guarded on `entry.get("of") in
labels` so an unresolvable side still gets the more specific `E-STATS-CONTRAST-UNKNOWN`, which
`tests/test_validate.py`'s `test_a_contrast_with_an_unresolvable_side_is_unknown_not_same_sides`
pins with a positive *and* a negative assertion. Verified end to end: my `of: baseline, against:
baseline` probe now exits nonzero from `publishable validate` with the code in the diagnostic
text, where at `fba4040` it validated clean and published `delta: 0.0, ci95: [0.0, 0.0],
n_paired: 20`.

### I3 + M7 — ADDRESSED

`E-STATS-CONTRAST-SHAPE` at `validate.py:983-990` (non-list block, with an early `return` so
nothing downstream iterates it), `:1015-1021` (non-mapping entry) and `:1022-1029` (missing or
non-string `id`). Verified all three refuse at `validate` with a nonzero exit: `contrasts:
["method=spearman"]`, which crashed `run` with `AttributeError: 'str' object has no attribute
'get'` at `fba4040`; a mapping-valued `contrasts` block; and an entry with no `id`, which
published `id: 'None'` at `fba4040`. The `if not entries: return` that precedes the isinstance
check is correct — a falsy block is an undeclared one.

### I4 — ADDRESSED, both halves

Scope: `cli.py:309` now reads `if comp.within is not None and min_reported_n is not None and
n_paired < min_reported_n`, matching all three `reference.md` passages, with the reason recorded
in the docstring at `cli.py:222-229`. Both directions are pinned — `test_a_thin_within_contrast_
warns` and `test_an_unstratified_contrast_below_min_reported_n_does_not_warn`, on the same 6-unit
roster against a floor of 10, so the pair isolates the stratum as the cause.

Identifier: I re-ran the exact mutation from the original review — `"W-STATS-CONTRAST-THIN"` →
`"W-STATS-CONTRAST-XYZZY"` in `cli.py`. At `fba4040` this left **679 passed**. At `d082a36` it
gives **1 failed, 690 passed**, failing `tests/test_cli.py::test_a_thin_within_contrast_warns` at
`test_cli.py:1130`. Reverted; tree clean.

## New findings

Both are consequences of the fix round rather than regressions of it, and neither blocks merge.

### N9 (Important) — `W-STATS-FAMILY` still counts only baseline comparisons, understating the family by every declared contrast

`src/publishable/validate.py:936-944`

```python
    if len(conditions) > 1:
        c.warn(
            "W-STATS-FAMILY",
            "statistics.correction",
            f"{len(conditions)} conditions form a family of {len(conditions) - 1} baseline "
            "comparisons per metric, ...
```

`reference.md`:2070: *"Declared contrasts join the correction family alongside baseline
comparisons, because a reader shown both is exposed to both,"* and :2066: *"six declared subgroup
contrasts widen the correction by six."* The count is `len(conditions) - 1` and never consults
`statistics.contrasts`.

This is a sibling of C1 in exactly the class the sweep was asked to look for: a number computed
over one set (conditions) sitting beside the thing it claims to describe (the comparisons a
reader is exposed to). Observed in a probe — a 2-condition run with **two** declared contrasts
printed *"2 conditions form a family of 1 baseline comparisons per metric"* while the run
published three comparisons. It was correct before this branch, because declared contrasts were
refused wholesale; making them real is what made the disclosure understate the family.

Not a merge blocker: the correction family itself is S4c's, the message is a disclosure rather
than an applied correction, and every entry still records `correction: null`. But S4c must not
inherit an undercount that was accurate when it was written. **Fix:** count declared entries
alongside baseline comparisons, or add a `spec-defects.md` line assigning it to S4c explicitly.

### N10 (Minor) — duplicate contrast `id`s are permitted, and the new diagnostic says they aren't

`src/publishable/validate.py:1026-1028`, the `E-STATS-CONTRAST-SHAPE` message for a missing `id`:

> `id` is how the contrast is named in `results.contrasts` and in a hypothesis, so two entries
> cannot share one

Nothing enforces that. Verified: two entries both with `id: dup` validate clean (`0 errors`), and
`_compute_declared_contrasts` (`cli.py`) appends unconditionally, so both land in
`results.contrasts` under one name. Closing M7 removed the `'None'` collision but not the general
one, and the message now asserts a rule the code does not hold. **Fix:** refuse a repeated `id`
under the same code, or drop that clause from the message.

## Sweep for further C1 siblings — nothing else found

Checked every place in the diff where a point estimate, an interval, an `n`, or a threshold could
be computed over a different unit set than the number beside it:

- **Column branch** (`cli.py:288-307`): `delta`, `ci95`, `cohens_d` and `n_paired` all derive from
  the same `col_keys`. Consistent.
- **Derived branch**: `delta`, `ci95` and `n_paired` all derive from `base_keys`. At
  `n_paired == 1` the delta exists and the interval is `null` — honest, not a mismatch.
- **`W-STATS-CONTRAST-THIN`** reads the same `n_paired` that lands in the record, inside the same
  loop iteration. Consistent.
- **The `min_reported_n` narrowing opens no silent no-op**: an unstratified thin comparison still
  records its `n_paired` in `run.yaml`, so the denominator is disclosed; only the warning the
  document never scoped there is gone.
- **The new `validate` checks open no silent no-op**: every one of the four codes
  (`-SAME-SIDES`, and `-SHAPE`'s three faults) is produced through `validate_config` by a test in
  `tests/test_validate.py`, and each aborts the run rather than admitting a config nothing
  computes. The non-list `return` short-circuits only checks that could not run on that shape
  anyway.
- **Purity holds** at the new HEAD: `paired_delta_of_derived` touches no filesystem and imports
  nothing from `config`/`artifacts`/`runner`/`cli`; `contrasts.py` and `sweep.py` are unchanged by
  this commit; `_check_contrasts` still only collects.

## Verdict

**APPROVED FOR MERGE.** The Critical is closed at the call site and pinned by two mutation-killing
end-to-end tests, including the unequal-completion case that was a live
point-estimate-outside-its-interval defect and that I verified by hand since no test covers it.
All three Importants and all four Minors are addressed or explicitly and correctly declined. N9
should be fixed or assigned to S4c before that slice builds on the family count; N10 is a one-line
message or check fix. Neither justifies holding the branch.

---

# Review of `d9e3f7f`

**VERDICT: CHANGES REQUIRED** — one regression (R11), a one-line fix. N9 and N10 are themselves
correctly fixed; the regression is a side effect of where N9's fix was placed.

`git diff d082a36..d9e3f7f` — one commit, `src/publishable/validate.py` and
`tests/test_validate.py`. Gates at HEAD, clean tree: **693 passed**, ruff `All checks passed!`,
mypy `Success: no issues found in 35 source files`. One temporary `git checkout d082a36 --
src/publishable/validate.py` and two throwaway probe files under `tests/`, all reverted/removed;
`git status --porcelain` empty at the end of every step and now.

## N10 — ADDRESSED

`validate.py:1035-1044`. Verified by probe, all four interactions the brief asked about:

| Config | Result |
|---|---|
| two entries with `id: x` (plus a third) | `[1].id` and `[2].id` each report *"repeats `x`, which an earlier entry already uses"*; `[0]` is not flagged |
| two entries with **no** `id` | two *"is missing or not a string"* errors, **no** duplicate error |
| two entries with `id: ""` | same — no duplicate error |
| two entries with `id: 5` | same — no duplicate error |

**(b) is correct, and the reason is the `elif`.** `seen_ids` is only ever added to under
`isinstance(entry.get("id"), str) and entry.get("id")`, so `None`, `""` and non-strings never
enter the set; `None in seen_ids` is therefore always `False` and two missing ids cannot report as
duplicates. The duplicate check preceding the missing-`id` check is also right: a value that is in
`seen_ids` is by construction a non-empty string, so the two branches are mutually exclusive in
practice and each fault gets exactly one diagnostic.

## N9 — ADDRESSED

`validate.py:936-957`. `test_declared_contrasts_are_counted_in_the_uncorrected_family` asserts
`"family of 3" in warning.message` for 2 conditions + 2 declared contrasts, which pins the
arithmetic rather than the code alone.

**(a) The trigger change adds and drops nothing that matters.** `expand` returns ≥ 0 conditions
(0 only for a declared-but-empty `sweep`). Enumerated exhaustively — `before` is
`len(conditions) > 1`, `after` is `max(len - 1, 0) + declared > 0`:

| `len(conditions)` | `declared` | before | after | verdict |
|---|---|---|---|---|
| 0 | 0 | no | no | unchanged |
| 0 | > 0 | no | **yes** | new, but the config is already error-refused: with no conditions no label resolves, so every side is `E-STATS-CONTRAST-UNKNOWN` |
| 1 | 0 | no | no | unchanged — the no-sweep single-condition case keeps its silence |
| 1 | > 0 | no | **yes** | new, and likewise already refused: one condition offers at most one label, so a contrast is `-SAME-SIDES` or `-UNKNOWN` |
| ≥ 2 | 0 | yes | yes | unchanged |
| ≥ 2 | > 0 | yes | yes | unchanged |

No shape that had a `W-STATS-FAMILY` loses one, and the two shapes that gain one cannot validate
cleanly for unrelated reasons, so the warning never appears alone on a config a reader could act
on. The `max(..., 0)` guard is what makes the `len == 0` row safe.

**(d) The reworded message breaks nothing.** Grepped every tracked `*.md`, `tests/` and `src/` for
the old wording: no test and no document quotes the string. `reference.md`:280 and :1660 describe
the family rule in prose ("a family of 15 baseline comparisons" for 6 conditions × 3 metrics),
which remains correct for a config declaring no contrasts and does not contradict the new text —
`reference.md`:2070 is what the new count implements. Two cosmetic notes, not defects: the message
now reads "and 0 declared contrasts" in the overwhelmingly common case, and "a family of 1
comparisons".

**(c) Both new tests fail against the pre-fix code.** With `d082a36`'s `validate.py` restored:
`test_declared_contrasts_are_counted_in_the_uncorrected_family` fails on `assert 'family of 3' in
'2 conditions form a family of 1 baseline comparisons per metric...'`, and
`test_two_contrasts_cannot_share_one_id` fails outright — `2 failed, 168 deselected`. Restored
afterwards.

## Regression

### R11 (Important) — a scalar `statistics.contrasts` now makes `validate` raise, undoing the fix this branch shipped one commit earlier

`src/publishable/validate.py:946`

```python
    declared = len(((doc.get("statistics") or {}).get("contrasts")) or [])
```

There is no `isinstance` guard, and this line lives in `_check_sweep`, which `validate_config`
calls **before** `_check_contrasts` — so it runs ahead of the very `isinstance(entries, list)`
check added in the previous round for exactly this input.

**Verified, both directions.** `statistics: {contrasts: 5}` and `statistics: {contrasts: true}`:

- at `d082a36`: `CODES: {'E-STATS-CONTRAST-SHAPE', 'W-STATS-FAMILY'}` — refused cleanly, collected
  as a finding.
- at `d9e3f7f`: `TypeError: object of type 'bool' has no len()` at `validate.py:946`, an uncaught
  traceback out of `publishable validate`.

This violates the hard constraint in both CLAUDE.md and the plan's Global Constraints —
*"`validate.py` **collects** findings and never raises to report one"* — and it is the same class
as the original I3 (`AttributeError` out of `run` on a malformed block), reintroduced at
`validate` time by the fix for N9. A YAML slip of `contrasts: 1` or a commented-out list reduced
to a scalar reaches it.

**Fix:**

```python
    declared_block = (doc.get("statistics") or {}).get("contrasts")
    declared = len(declared_block) if isinstance(declared_block, list) else 0
```

**Test:** a `tests/test_validate.py` case asserting `E-STATS-CONTRAST-SHAPE` in `codes(...)` for
`{"statistics": {"contrasts": 5}}` — which also closes the gap that let this land, since the
existing non-list test uses a *mapping*, and `len()` happens to work on a mapping.

## On the deliberate non-fix of the baseline overcount — the deferral is fine, the stated reason is not

Deferring it to S4c is the right call and it is properly recorded in
`docs/superpowers/spec-defects.md`. But the reasoning attached to it — *"narrowing it removes the
warning entirely for that shape, and this build does still owe the reader the 'multiplicity
correction is not implemented' disclosure"* — does not hold, and it is worth correcting now so S4c
does not preserve a false positive on its authority.

A grid-only sweep with no `sweep.baseline` and no declared contrasts publishes **no comparison at
all**. This branch's own `test_a_run_with_no_baseline_has_no_vs_baseline_block` asserts that
`run.yaml` contains no `vs_baseline` block for exactly that shape, and `resolve_contrasts` returns
`[]`. There is nothing to correct, so no correction disclosure is owed: the warning tells the
reader they are exposed to a family of `len(conditions) - 1` uncorrected comparisons when they are
exposed to none. That is a false positive on the warning's own terms, not a backstop.

Recommendation for S4c: derive the count from `resolve_contrasts` — the one place that already
knows which comparisons exist — and let the warning disappear for a shape that forms no family.
Amend the `spec-defects.md` entry's reasoning accordingly; the assignment itself needs no change.

## Verdict

**CHANGES REQUIRED.** N9 and N10 are correct, well-tested, and their tests are verified to fail
against the pre-fix code. R11 is a one-line guard plus one test, but it is a hard-constraint
violation and a regression of a fix this same branch made one commit earlier, so it should not
merge as-is. With R11 fixed the branch is approved — nothing else in this commit is outstanding,
and the deferral of the baseline overcount is acceptable once its recorded reasoning is corrected.

---

# Confirmation of `f786b79`

**VERDICT: APPROVED FOR MERGE.** R11 is closed with no new path: the `isinstance(contrasts_block,
list)` guard at `validate.py:948-949` is the only `len()` in `_check_sweep` reading a raw config
value (the others read `conditions` from `expand`, and `budget` is already `isinstance`-guarded),
a non-list block still reaches `E-STATS-CONTRAST-SHAPE` for `5`, `True` and a bare string, and
`test_a_scalar_contrasts_block_is_refused_without_raising` fails against `d9e3f7f` with the
reported `TypeError` at `validate.py:946`. The amended `spec-defects.md` entry is accurate.
Gates at HEAD: **694 passed**, ruff clean, mypy clean; tree clean.

One non-blocking note for S4c, recorded rather than requested: `statistics.contrasts` is exactly
the "nested shape a later check indexes into directly" category `_check_shape` exists for, whose
own comment (`validate.py:88-93`) warns that an unguarded container means "the crash just moves
one level down, into whichever `_check_*` reads it next" — which is what R11 was. Adding it there
would refuse it once as `E-CONFIG-SHAPE` and gate every downstream reader via the
`if not _check_shape(doc, c): return None` early exit, instead of requiring a guard in each
reader. The two guards shipped here are correct and sufficient; the next reader of the block
(S4c's `report_by`/`resample`/hypotheses work) is the one that would otherwise inherit the same
crash.
