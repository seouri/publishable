## Task 2: Mint the `resample.method` table and fix the inline enum comment

**Files:** Modify `docs/reference.md`. No code, no test file.

**Interfaces:**
- Consumes: nothing.
- Produces: the normative statement that `resample.method`'s enum is exactly `bootstrap`, which Task 4's `E-STATS-RESAMPLE-METHOD` check enforces.

**The decision being written down (spec decision 1).** `bootstrap` is the **whole** enum — a closed, one-value enum. It is the only value the schema shows, the only construction that exists, and § Statistical reporting's existing construction table (`percentile_over_units`, `paired_percentile_over_units`, …) lists method strings core **emits**, not inputs a config may name. A one-value enum is a legitimate answer and an unstated one is not: closing it makes adding a second value a documented change rather than a silent one, and makes `method: bootstap` a diagnostic rather than a shrug.

- [ ] **Step 1: Write the failing test** — the test here is a mechanical grep, written as a throwaway and run in Step 2, not kept:

```bash
# Every value the new table defines must appear in the inline comment, and vice
# versa. Filter the FILE LIST, never the output of a sweep whose job is to find
# a string (a matching line can itself contain the excluded path).
cd /Users/joon/src/tries/publishable
grep -n 'resample:.*# ' docs/reference.md          # the inline comment, `# a | b | c` form
grep -n 'Resample methods' -A 6 docs/reference.md  # the new table
```

- [ ] **Step 2: Run it, confirm it fails** — today `grep -n 'Resample methods' docs/reference.md` returns nothing, and the inline comment at § The one config file reads `resample: null                         # NOT BUILT; {method: bootstrap, n: 2000, stratify_by: []}` — an *example expansion*, not an enum comment. Both greps failing is the confirmation.

- [ ] **Step 3: Implement** — two edits to `docs/reference.md`.

  (a) In § Statistical reporting, immediately after the paragraph beginning "**A derived metric is resampled whether or not you declare `statistics.resample`.**", add:

```markdown
**Resample methods.** `statistics.resample.method` names how the draws are taken, and the vocabulary is closed:

| `method` | What one draw is |
|---|---|
| `bootstrap` | Units drawn with replacement to the original count, or whole [clusters](#clustered-units) when `cluster_by` is declared, or within each [stratum](#weighted-samples) when `stratify_by` is — the statistic recomputed on each draw |

One value is the whole enum today. It is stated as an enum rather than left implicit so that adding a second is a documented change rather than a silent one, and so `method: bootstap` is refused (`E-STATS-RESAMPLE-METHOD`) rather than ignored. The method strings in the two construction tables above — `percentile_over_units`, `paired_percentile_over_units` and their `_clustered` forms — are what core **emits** into `run.yaml`, not values a config may name here.
```

  (b) In § The one config file, replace the `resample:` line with:

```yaml
  resample: null                         # bootstrap
                                         #   {method: bootstrap, n: 2000, stratify_by: []}
```

  Keep the two following comment lines (`# ... metrics resample either way`) exactly as they are, and delete `NOT BUILT;` from this line only — the rest of Task 12 handles the `NOT BUILT` prose in the § The one config file paragraph.

- [ ] **Step 4: Run, confirm it passes** — re-run both greps from Step 1; both now return their lines. Then the full mechanical pass: check that no heading added here duplicates an existing anchor (`grep -n '^#' docs/reference.md | sort` — the new block adds no heading, so this must be unchanged), that the new table's every row has 2 columns matching its header, that no added line has trailing whitespace (`grep -n ' $' docs/reference.md`), and that no `x` was used for multiplication in the added text. Then `uv run pytest` — the docs are read by `tests/test_materialize.py`, which pins the generated config's comment text, so confirm whether that test covers this line and update `materialize.py` if and only if it does (it writes no `resample` key, so it should not).

- [ ] **Step 5: Mutate** — change `bootstrap` to `boostrap` in the new table's first column only. Re-run `grep -n 'Resample methods' -A 6 docs/reference.md` and confirm the table row and the inline comment now disagree — this is the § Enum comments consistency class, caught by reading the two together, which is why both greps are in Step 1. Revert in place by editing the word back.

- [ ] **Step 6: Commit** — `docs: close resample.method at one value, and give it the enum comment CLAUDE.md requires`.

---

