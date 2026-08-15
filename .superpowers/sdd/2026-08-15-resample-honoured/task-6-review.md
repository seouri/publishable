# Task 6 review — `W-STATS-RESAMPLE-FAMILY`, the comparisons-only bound

**Spec compliance: ✅**
**Task quality: approved with findings** — 2 Important, 5 Minor. Nothing Critical; nothing that
should block the merge, but Important 1 and 2 are both one-line fixes and both are the repo's
named defect classes.

Verified at `5c744bd`, tree clean: `uv run pytest` 1717 passed + 2 xfailed, `ruff check` and `mypy`
clean. `ruff format --check` flags 2 of the ~39 pre-existing files touched here (`validate.py`,
`test_validate.py`) — out of scope, and the new hunks are no worse than their neighbours.

---

## The correctness property, checked against the functions rather than the brief

`min_honest_draws(c) = ceil(2.0/((1.0-c)/2.0))`, run directly: 80 / 160 / 240 / **321** / 400 / 481
for `k = 1..6` comparisons at `ALPHA = 0.05` — the 321 is the float artifact, not a typo, and the
80/400/800/1601 anchors at 0.95/0.99/0.995/0.9975 reproduce.

- Real requirement: `interval_at(pool, 1 - level)` returns `None` below `min_honest_draws(1 - level)`;
  the tightest `level` is `ALPHA/m` for `bonferroni` (every member) and for `holm` at rank 1
  (`_level_for` = `ALPHA/(m - rank + 1)`), with `m = family_shape` = comparisons × metrics.
- Shipped bound: `min_honest_draws(1 - ALPHA/comparisons)`. Since `metrics ≥ 1` whenever the family
  is non-empty, and `min_honest_draws` is monotone in confidence (float rounding is monotone at each
  step), the shipped threshold is **≤** the real one, with equality at `metrics = 1`. **Always true
  when it fires, silent when it might not be — confirmed.**
- The bound is conservative twice over on the other axis too: surviving draws ≤ declared `n`
  (`W-STATS-RESAMPLE-THIN`), so a pool that fails the bound at `n` fails it at the realized count.
- `correction: none` / `fdr_bh`: `_level_for` returns `None` for `fdr_bh` and `corrected_for`
  returns `{}` for `none` — no corrected level exists, and the guard returns before warning.
  Confirmed by mutation, below.
- Unset `correction`: `statistics.get("correction") or "holm"` matches `cli`'s own default. The
  no-key test covers it; a mutant gated on key *presence* fails that test.

Attribution, run directly rather than inferred (the "a refusal that happens to fire must be
attributed" rule): the emitted message on the 3-level fixture reads *"is 200, and this design
resolves to 3 comparisons … needs at least 240 draws"*, and adding one declared
`statistics.contrasts` entry moves it to *"4 comparisons … 321 draws"*. The count is the resolved
family, not the condition count and not a constant.

## Mutations (all in `validate.py`, `__pycache__` cleared between runs, reverted **in place**;
final `md5` identical to the pre-mutation copy, and the full suite re-run green)

| Mutation | Result |
|---|---|
| `needed = min_honest_draws()` (brief's #1) | **4 tests fail** — the brief predicted 2; the two extra come free from the 200- and 100-draw fixtures |
| `if correction_method not in (...)` guard deleted (brief's #2) | **both** parametrized cases fail (`none`, `fdr_bh`) |
| `comparisons` → `len(conditions)` (mine — the count that is 4 where the answer is 3) | boundary + scaling tests fail. The fixture genuinely distinguishes conditions from comparisons |
| `n < needed` → `n <= needed` (mine) | boundary test fails on `n=240` |
| `n < floor` clause dropped from the guard (mine) | **nothing fails** — see Minor 3 |

Degradation checked by behaviour, not by reading: a `sweep.grid` axis of `null` (the shape that makes
`expand` raise) yields `E-SWEEP-AXIS-EMPTY` and silence from this check — no traceback, `validate`
still collects.

## Precedent for the re-derivation (the thing the earlier reviews flagged)

`_check_sweep` really does return `None` and hand nothing over; the new code re-derives. The
`try: conditions = expand(doc) / except Exception` **plus** `try: resolve_contrasts(doc, conditions)
/ except (TypeError, KeyError, AttributeError, ValueError)` pair is copied exactly from
`_check_sweep`'s own `W-STATS-FAMILY`/`E-DATA-WEIGHT-CONTRAST` block (`validate.py`, the
`resolved_contrasts` assignment) — same two guards, same except tuple, same "a block that cannot be
resolved counts as no resolvable family here" reasoning. **Not a fourth pattern.** The narrow tuple
is right: `resolve_contrasts` raises bare `KeyError` on an unresolvable declared label by design.

## `interval_at` attribution

Both halves confirmed. `interval_at` is defined in `stats.py` (line ~448) and `correction.py`
imports it (`from publishable.stats import interval_at`) and calls it in `_corrected_bounds`. The
brief's supplied comment said `correction.interval_at`; the shipped comment says
"`stats.interval_at`, which `correction` calls". The report's claim is accurate and the correction
was the right call.

---

## Findings

### Important

**I1. The comment names three precedents; only two exist.** The shipped comment (and the brief's
§ *Re-derive `conditions`, do not hoist*) says `expand(doc)` is re-derived "behind the same guard
`_check_sweep`, `_check_contrasts` and `_check_hypotheses` each use." `grep -n "expand(doc)"` finds
four call sites: `_check_sweep`, `_check_contrasts`, `_condition_labels`, and this one.
**`_check_hypotheses` never calls `expand` and does not use this guard** — it calls
`_condition_labels`, whose guard returns **`None`**, a different degradation shape that its callers
branch on. Two real precedents still justify the pattern; the finding is the miscount, in a comment
the brief itself designates as interface documentation for tasks 7 and 8 — this repo's #1 defect
class, inherited verbatim from the brief. Fix: name `_check_sweep` and `_check_contrasts`, and
`_condition_labels` separately if wanted.

**I2. A § Validation passage in the same section is now contradicted by the inserted row.**
`reference.md`'s "Six things deliberately absent from that table" paragraph says "a reporting
stratum's thinness *among completed units* **and a corrected interval's draw floor** are both
reported once a run has executions to count them from, as `W-STATS-STRATUM-THIN` and
`W-STATS-CORRECTED-THIN` — distinct from the *Reporting stratum is populated* row above, whose
`W-STATS-REPORTBY-THIN` counts the roster `validate` can already see." The stratum half carries its
"distinct from the row above" clause precisely because it has a validate-time counterpart. The
corrected-draw-floor half has now acquired one — the new *Resample draws fit the family* row — and
the passage still reads as if it is run-time only. This is the cross-document half of the row
insertion (the mechanical pass cannot see it). Fix: add the parallel clause naming the new row and
saying what it does not cover (the metric count), which is also the natural place to link the sizing
rule from the residue ruling below.

### Minor

**M3. The `n < floor` clause in the guard is untested.** Dropping it fails nothing — no shipped test
uses `n < 80`. Harmless today (a sub-floor `n` is already `E-STATS-RESAMPLE-N`, and the family bound
is ≥ 80 so it would fire redundantly rather than wrongly), but it is a clause whose comment asserts
an intent no test holds. One assertion — `n: 50` with 3 comparisons reports `E-STATS-RESAMPLE-N` and
**not** `W-STATS-RESAMPLE-FAMILY` — would pin it. (Also: `isinstance(n, bool)` is subsumed by
`n < floor`, since `True == 1`, so no mutation can distinguish it. Fine to leave; worth knowing.)

**M4. The default-`n` path is silent by construction and is not in the filed residue.** An absent
`n` (or an absent `resample` block) returns at that guard with the comment "already refused above,
or defaulted; nothing to bound" — but there *is* something to bound: `cli`'s
`derived_metric_draws = 2000` means any design above ~26 comparisons nulls its rank-1 corrected
interval with no validate-time signal at all. Verified: a 30-comparison config with `resample:
{method: bootstrap}` and no `n` reports nothing. The comment's "nothing to bound" overstates; "the
resolved default is task 12's to bound" would be accurate. This gap is the same shape as the filed
residue and is not filed.

**M5. The residue as filed is incomplete: there is a *second* correction family.**
`corrected_for` is called twice — `correction.corrected_fields` at comparisons × metrics, and
`hypotheses.py` at `{"hypotheses": size}`, over **the same `Member`s and therefore the same pools**.
So `H` counted confirmatory hypotheses demand `min_honest_draws(1 - ALPHA/H)` off the same draws,
entirely outside this warning's bound: 2 comparisons + 10 hypotheses is silent at `n = 200` while
the hypothesis family needs ~800. Worth recording precisely because it is *also* not safely
buildable — the declared hypothesis count is an **upper** bound on `len(counted)`, so bounding on it
would produce exactly the false alarm this design avoids. Neither the comment, the reference row nor
the `spec-defects.md` entry mentions it.

**M6. Two small overclaims in the comment and the message.** (a) "a corrected interval is read off
the SAME pool the raw one was" is universal, but only pool-backed members work that way — a
`diffs`-backed column contrast is recomputed by `paired_t_over_units`, exact at any α and
independent of `n` (task 15 is what makes column contrasts pool-backed under a declared resample).
True after the slice, not stated as such. (b) The message's "`ci95_corrected` would be null" is
unqualified; under `holm` only the rank-1 member sits at `ALPHA/m`, so at the bound exactly one — the
strongest — loses its corrected interval. Under `bonferroni` all do.

**M7. Fixture noise, and the docstring.** The 3-level fixture sweeps `theil`, which is not in
`analysis.method`'s `choices`, so those configs also report `E-PARAM-VALUE` while the 1-comparison
fixture does not — an asymmetry in the scaling test's two halves. Using `pearson` as the third level
produces the same warning with no `E-PARAM-VALUE` (verified). Attribution is unaffected, since the
message names the comparison count. Separately, `_check_resample`'s docstring still enumerates
"`method` enum, its `n` floor, and its `stratify_by` names" — the family bound is not in it, and
tasks 7 and 8 read that docstring.

**M8 (pre-existing, out of scope, but load-bearing for the residue argument).**
`W-STATS-CORRECTED-THIN`'s run-time message prints `values['family_size']` as
"`{family_size}` comparisons" — but `family_size` is the **product**, comparisons × metrics. The
run-time disclosure the residue is routed to mislabels itself as the very quantity validate could
not compute.

### Checks explicitly cleared

- No implication anywhere that resample is honoured yet — `E-STATS-RESAMPLE-UNSUPPORTED` still fires
  on every one of these fixtures, and the warning coexists with it rather than replacing it.
- Mechanical pass on `reference.md`: both inserted rows are 3-pipe, 2-column, matching their headers;
  no trailing whitespace, tab or invisible unicode outside fences; the warnings row sorts correctly
  between `W-STATS-REPORTBY-THIN` and `W-STATS-RESAMPLE-THIN`; the code string appears in exactly one
  tracked `*.md` row; no count phrase ("N rows/checks/warnings") sits near either insertion; every
  positional reference in the repo's `*.md` (`row above`, `rows above`, `further up`) names the row it
  means and still resolves — the one substantive consequence of the insertions is I2, which is a
  claim rather than a position.

---

## The residue question: does it need a durable home in the four documents?

**Ruling: the *decision* is already durably recorded and should stay where it is; the *rule a user
needs* is missing from all four documents and should be added.** Filing alone is not enough — but the
missing piece is a spec sentence, not a defect record.

*Why filing is arguably enough.* The candidate the slice already took is the third one on your list:
the `W-STATS-RESAMPLE-FAMILY` row itself says, in the tracked document, "a **lower** bound, since the
family is comparisons × metrics and the metric count is not knowable before the run." That is the
admission, in the four documents, surviving `docs/superpowers/` being gitignored. The
`spec-defects.md` entry adds only archaeology — which scoping asked for the full bound, which
invariant closes it — and archaeology is exactly what that file is for.

*Why it is not enough.* What no tracked document states is the **actionable consequence**, and it is
a present-tense spec fact rather than a build fact: a corrected interval is read off the same pool as
the raw one, so an interval at `α/m` needs `min_honest_draws(1 − α/m)` ≈ **80 m** draws, and
`resample.n` must therefore be sized against the whole family — comparisons × metrics — not against
the 80-draw floor. A reader today can meet the floor, clear the new warning, and still get `null`
everywhere, and nothing they can read tells them why or what number to pick. Three facts sharpen
this: the default-`n` path warns about nothing at all (M4), the hypothesis family is corrected
separately by its own count (M5), and the run-time disclosure it all routes to calls the product
"comparisons" (M8). A rule that no validate-time check can enforce is precisely the kind that has to
be written down.

**Where, and roughly what.** § Statistical reporting, beside the correction-level table — it already
defines the family as comparisons × metrics, carries Holm's `α/(m−i+1)` and the `fdr_bh`
"no interval that means anything of the kind" paragraph, and ends with "the same standard the family
count is held to below." Two sentences: a corrected interval is a second rank pair off the same pool,
so at `α/m` the pool must hold `min_honest_draws(1 − α/m)` ≈ 80 m draws or `ci95_corrected` is
`null`; size `resample.n` against the whole family, and note that a confirmatory-hypothesis family is
corrected separately and sized by its own count. Then the clause I2 already requires beside
"Six things deliberately absent", pointing at it. Not a clause beside `W-STATS-CORRECTED-THIN` — that
row states the condition, and a sizing rule stated only in a warnings table is a rule you find after
you have already spent the run.
