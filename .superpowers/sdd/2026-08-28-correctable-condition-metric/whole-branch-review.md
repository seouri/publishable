# G2 whole-branch review — `correctable-condition-metric` (`b5eb0ef..6f4853b`)

**Verdict: Issues — 3 Important, 3 Minor. The CODE is right; the DOCUMENTS this slice rewrote are
where every Important finding is.** Three prose statements the slice introduced are false against
the build it describes, and two of them sit in `reference.md` (normative) and `spec-defects.md`
(live). No pool escape route was found beyond the one Task 4's review already closed.

---

## Important

### I1 — `reference.md` now promises a real corrected bound under `fdr_bh`, and there is no such bound

§ What a hypothesis is tested against, rewritten by Task 6:

> Under a real method (`holm`, `bonferroni`, `fdr_bh`), evaluating it on `ci95_lower` or
> `ci95_upper` reads a real corrected bound, **except in two cases** …

`correction._level_for` returns `None` for `fdr_bh` ("BH implies no per-comparison level at all"),
so `corrected_for` sets `bounds = None` and writes `ci95_corrected: null` for **every** member,
constant-referenced or not. `fdr_bh` is a *third* case, not covered by either named exception.

**Evidence (run, not read).** A project with `statistics.correction: fdr_bh`, two conditions and two
`compare: {to: constant}` hypotheses on a recorded column with a real `t_over_units` interval:

```
FDR: a None {'value': 19.5, 'ci95': [15.7612…, 23.2387…], 'method': 't_over_units', 'ci95_corrected': None}
FDR: b None {'value': 19.5, 'ci95': [15.7612…, 23.2387…], 'method': 't_over_units', 'ci95_corrected': None}
```

The same document contradicts itself about this: § Statistical reporting's `supported` paragraph —
edited in the *same commit*, three→four reasons — still lists "`correction: fdr_bh` leaves it unmet
by construction" as one of the four ways `ci95_corrected` can be `null`. The pre-slice sentence was
true for all three methods (`… reads supported: null and ci95_corrected: null`); the rewrite
inverted it and did not re-check the `fdr_bh` arm it kept naming.

### I2 — Decision 1's fourth row names a trigger that cannot occur, and the falsehood was carried into `spec-defects.md` and into `hypotheses.py`

The design's row 4 is "Derived, no `resample` → **none at all** — `derived_interval` is `None`". Task
6 propagated that reading:

- `spec-defects.md`: "The fourth row — a derived metric with no declared `resample` — was never this
  gap: **it has no raw interval either**."
- `hypotheses.py` (new comment, first bullet): "the metric's own raw interval is `null` — **a derived
  metric that was never resampled**, or a step that returned no numeric value for it".

A derived metric is resampled **whether or not `statistics.resample` is declared**. `cli.py:4232`
builds a `resample_fns` closure for *every* key `aggregate` returned, `resample_seed_value` is always
set, and `stats.summarize_step`'s derived branch gates on `compute is not None and seed is not None`
— never on `resample_columns`. `stats.py`'s own docstring says so from the other end: a recorded
column "has a `t_over_units` fallback available, so resampling it is a CHOICE … the asymmetry with a
derived metric, which has no fallback and **is resampled either way**".

**Evidence (two probes, run against HEAD).** A project with a derived `mean_pred` and **no**
`statistics.resample`:

```
step01_summarize_units mean_pred ci95= [16.275, 23.2875] method= percentile_over_units resample_draws= 2000
```

and with two `compare: {to: constant}` hypotheses on it under `holm`:

```
a True {'value': 19.5, 'ci95': [16.025, 23.025], 'ci95_corrected': [15.4, 23.45]}
b True {'value': 19.5, 'ci95': [16.025, 23.025], 'ci95_corrected': [16.025, 23.025]}
```

So that case is row **3**, gets a pool member, and is correctable. Row 4's described state does not
exist. The *behaviour* is right and the *test* is right — Task 5's
`test_a_condition_metric_with_no_raw_interval_still_gets_no_member` reaches the row through
all-degenerate draws (`resample_draws: 0`), not through an undeclared resample, and its docstring
even says "It is the reachable end-to-end shape of the row". The implementer found the discrepancy
and routed around it; nobody went back and fixed the three sentences. This is CLAUDE.md's *assuming
a documented rule has code behind it*, inverted: a documented state with no code that produces it.

(The design spec itself is a dated record and is corrected by appending, not editing. The live
`spec-defects.md` entry and the `hypotheses.py` comment are not.)

### I3 — the feasibility analysis's finding #2 names the wrong metric and contradicts the § Executability entry appended to the same file by the next task

Task 6 rewrote finding #2 to say of E2:

> The claim can be written directly on `step03_compare.auroc_count_only` rather than routed through
> a `summary`-step `Estimate`.

`step03_compare.auroc_count_only` **is** the summary-step `Estimate`. Task 7's own appended
§ Executability paragraph, ~300 lines below in the same file, says exactly that: E2's `h1` "names
`metric: step03_compare.auroc_count_only` with no `compare` block at all, because that metric is the
`summary`-step `Estimate` `step03_compare.py` computes". Confirmed against the source config,
`/Users/joon/src/tries/2026-08-28-gcl-measurement/configs/e02-utilization-baseline/config.yaml`
lines 59–66: `metric: step03_compare.auroc_count_only`, no `compare:`, `evaluate_on: ci95_lower`.
The condition-scoped metric finding #2 means is `growth_label.aggregate`'s `auroc`
(`templates/growth_label.py:82`).

The ledger records Task 7 ruling that the *brief's* E2 reading was wrong. That ruling reached Task
7's new section and did not reach the sentence Task 6 had already written — CLAUDE.md's *sweep for
the claim, not for the file the claim was first noticed in*, and *a ruling that overrules a brief has
to reach the brief*.

---

## Minor

### M1 — `pools_by_key` is written and never read

`grep -rn pools_by_key src/ tests/` → three hits: the declaration (`cli.py:4089`), the single write
(`cli.py:4403`), and a mention inside the `report_by` pop's comment. Nothing reads it. Its declaring
comment claims the job the member loop actually does off the `step_pools` **local** two lines later
("Kept here rather than discarded so a condition's own metric can later have a `correction.Member`
built…"). It is a dead carrier that also keeps every pool in every condition × step alive for the
whole run. CLAUDE.md's *a parameter added, documented, and wired to a constant*, one shape over.

### M2 — the `declaration_index` offset is unpinned, and so is the Holm re-rank Decision 5's amendment names

Mutated `cli.py:5080` `declaration_index=len(comparison_members) + i` → `declaration_index=i` (which
collides with `comparison_members`' own reassigned `0..n−1` from `cli.py:5022`) and ran
`tests/test_cli.py tests/test_hypotheses.py tests/test_correction.py`:
**702 passed, 1 skipped** — fully green. Restored from a pre-mutation copy and re-verified by
behaviour (`-k "condition_metric or pool or oracle"` → 12 passed), not by `git status`.

The ledger deferred this as a Task 5 minor, but it is worth restating at branch close for a reason
the deferral did not give: **no test anywhere puts a comparison member and a condition member in the
same hypothesis family.** `grep -n 'to.*constant' tests/test_cli.py` finds constant hypotheses only
in pure-constant families. That is also why the design's *amended* Decision 5 — the Holm re-rank that
widens a co-family member's level and narrows its corrected bound, the one behaviour change the
slice explicitly permits itself beyond the intended one — has no test. Task 5's ruling said "what it
needs is a sentence in the record and a test, both of which land in Task 6/7"; the sentence landed,
the test did not.

### M3 — `spec-defects.md`'s narrowed entry still carries its old "Why open" paragraph in the present tense

The heading was narrowed to the weighted+clustered case and an amendment appended, but the body
between them still reads: "under a declared correction method, a `compare: {to: constant}`
hypothesis's bound test **is never answerable** and comes back `supported: null`; only
`evaluate_on: observed` is usable there." That is now false and it sits above the amendment that
corrects it, so a reader who stops at the body reads a false claim about what ships.

---

## What I checked and found clean — and how

"Clean" is a claim, so here is what backs each one.

**Pool escape routes.** `grep -rn summarize_step src/` → exactly three call sites in `src/`, all in
`cli._execute_prepared`: the main call (4265), the containment retry (4356) and the `report_by` level
call (4875). The single pop at 4399 sits after the `try/except/else` has converged (so it covers both
the main and retry outcomes) and before `aggregated[cond.index][step_name] = step_summary` at 4701;
the level pop at 4908 sits before `levels_block[level] = level_summary`. `by_block` is spliced into
`aggregated` at 4969, after both. `grep -n '"pool"' src/publishable/*.py` finds the key at exactly
five sites — two writes in `stats.py`, the two pops and the `Member` field in `cli.py` — plus
`correction.py`'s `__post_init__` tuple. No production caller of the four widened functions exists
outside `stats.py` (`grep percentile_over_units\|percentile_of_derived` over `src/` returns only the
unrelated `paired_*`/`unpaired_*` spellings and comments), so no second carrier was created. I found
no fourth path.

**Decision 1's evidence pairing (rows 1–3).** Read the bodies rather than the comments:
`paired_t_over_units` delegates to `t_over_units`, `weighted_paired_t_over_units` to
`weighted_t_over_units`, `paired_t_over_units_clustered` to `t_over_units_clustered`, each rewriting
only `method` — so a `diffs` member really does rebuild the same arithmetic at a smaller α. And
`cli`'s `carried` predicate (`metric_key in cols and _is_numeric(cols[metric_key])`, over
`collapsed.items()`) is the same predicate `summarize_step` filters with, in the same order, so the
`diffs` are the values the raw interval was built from and the `weights`/`clusters` vectors are
indexed off the same `column_keys`.

**Row 4 is genuinely uncorrectable, not silently skipped for another reason.** `if not raw: continue`
fires only where `ci95` is `null`; a pool that exists with no interval (`percentile_over_units`'s
below-floor `pool=sorted(values)`, its structural refusal's `pool=[]`) never reaches the member build
because the interval is `None` in both. Reachability is real via all-degenerate draws, which is what
the Task 5 test uses.

**The weighted+clustered carve-out is pinned against a SILENT wrong number, not merely a crash.**
Removing the `continue` alone would raise from `Member.__post_init__`, which proves little. I mutated
it to keep the clustered-only construction (`pass`, plus `weights` forced to `None` when `clusters`
is set) — a perfectly valid `paired_t_over_units_clustered` bound — and
`test_a_weighted_clustered_condition_metric_gets_no_member` failed on
`assert [-0.6085205135210412, 7.608520513521041] is None`. Restored; re-run green.

**`family_shape`, `_is_counted` and `corrected_for` agree about who is in which family.**
`corrected_fields` is still called on `comparison_members` alone (`cli.py:5025`), so the sweep
family's `comparisons × metrics` product is unmoved; condition members reach only
`evaluate_hypotheses`, where `size = len(counted)` over declared hypotheses and `family_members_`
picks `by_key` entries for counted keys only. `const:<index>` cannot collide with `cond:`/`contrast:`
in `by_key`. `family_members()` cannot drop a condition member for want of evidence, because `cli`
builds one only where `ci95` exists.
