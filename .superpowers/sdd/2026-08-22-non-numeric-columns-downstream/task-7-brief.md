## Task 7: the contrast guard — the naive fix destroys a run record, and this is the pin that makes it happen

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a direct call and a real `run`.** Design Decision 7. **This is the task the controller singled
out**: *a non-numeric value reaching the contrast subtraction hits an unguarded subtraction in `cli.py`,
`TypeError` outside every `try`, no `run.yaml`* — every execution paid for, the record lost.

**A rule enforced only by another function's output is not a guard.** Measured: a non-numeric column
cannot become a `metric_key` today, because `_comparison_step_blocks` iterates
`sorted((set(of_summary) & set(against_summary)) - {"by"})` and `of_summary` is `aggregated`'s step block.
So after task 6 the subtraction is unreachable **by convention at another function's output** — and the
scoping measured what happens when that convention breaks: `TypeError: unsupported operand type(s) for
-: 'str' and 'str'` at `of_collapsed[k][metric_key] - against_collapsed[k][metric_key]`, run directory
complete, **no `run.yaml`.**

**Files:**
- Source: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: import the predicate.** Add `_is_numeric` to `cli.py`'s
      `from publishable.stats import (…)` block. **`cli.py` does not import it today** (§ Corrections 4);
      the precedent for a private cross-module import is `_arm_keys` from `runner`, already in this file.
      It sorts first in the block, as `_arm_keys` does in its own.

- [ ] **Step 2: the paired arm.** In `_comparison_step_blocks`' recorded-column branch, the `col_keys`
      comprehension that already filters by membership gains the narrowing:

```python
                    col_keys = [
                        k
                        for k in base_keys
                        if metric_key in of_collapsed[k]
                        and metric_key in against_collapsed[k]
                        # The guard at the subtraction, not at another function's
                        # output. Today the only thing keeping a non-numeric value
                        # out of `metric_key` is that `of_summary` is `aggregated`'s
                        # step block and `summarize_step` publishes numbers only —
                        # a convention, not a guard, and when it breaks the
                        # subtraction below raises `TypeError` outside every `try`,
                        # losing a completed run its `run.yaml`.
                        and _is_numeric(of_collapsed[k][metric_key])
                        and _is_numeric(against_collapsed[k][metric_key])
                    ]
```

      **`col_keys` and not `of_values` is the right place** because `diffs`, `col_weights`, `col_clusters`
      and `n_paired` are **all** derived from `col_keys` — the one-pass discipline this function already
      states. A narrowing applied further down would leave a count and a cluster mapping describing a
      different set than the vector beside them.

- [ ] **Step 3: the unpaired arm — and it goes in `of_col`/`against_col`, NOT in
      `of_values`/`against_values`.** § Corrections 2. The design's text says the value vectors; measured,
      `n_of` is `len(of_col)`, `n_against` is `len(against_col)`, and `of_clusters`/`against_clusters` are
      built by keying off `of_col`/`against_col`. Filtering only the value vectors would publish a count
      and group a cluster set that the difference did not come from — *a vector filtered or ordered
      differently*, this project's one recurring version of that fault.

```python
                    of_col = [
                        k
                        for k in of_side_keys
                        if metric_key in of_collapsed[k]
                        and _is_numeric(of_collapsed[k][metric_key])
                    ]
                    against_col = [
                        k
                        for k in against_side_keys
                        if metric_key in against_collapsed[k]
                        and _is_numeric(against_collapsed[k][metric_key])
                    ]
```

- [ ] **Step 4: it SKIPS, it never raises — and skipping is not silence.** No new error or warning code
      (design Decision 7: the path is unreachable from a validated config, and a § Errors row that can
      never fire misleads). The two existing core-bookkeeping guards in this function raise `ValueError`
      and both sit in code reached **before** any interval is built; a raise **here** loses the `run.yaml`
      this guard exists to protect. A unit dropped this way is dropped exactly as a unit missing the
      column is dropped today, and `n_paired` reports what remains — `0` already means *pairing failed*,
      so an all-dropped metric publishes `n_paired: 0` and `ci95: null`, a shape a reader can already
      read. **Write that reasoning as a comment at the guard and nowhere else** — do not restate it at the
      unpaired arm, which is the same claim in a second place.

- [ ] **Step 5: Fixture G, both ends.**
      *Direct call:* `_comparison_step_blocks` driven with an `aggregated` carrying a `str`-valued metric
      key and a `collapsed` carrying `str` values for it. Assert it returns **without raising** and
      publishes **no entry** for that key. Today that call is the measured `TypeError`.
      **Its docstring says in so many words that it drives a state production cannot reach, and why the
      guard exists anyway** — a rule enforced by another function's output is not a guard, and the
      scoping measured the cost when it broke.
      *Unpaired arm:* the same, over a declared `sweep.groups` axis, asserting the published `n_of` and
      `n_against` are the **narrowed** counts and that `cohens_d` is not computed over a mixed vector.
      **Two separate assertions on two separate comprehensions**, because a mutation in one must be caught
      by an assertion on that one.
      *End to end (the honest half):* a real run recording a non-numeric column asserts `run.yaml`
      **exists**, `vs_baseline` holds **no entry** for that column, and exit is `0`. That is the claim
      about production, stated separately from the direct-call claim about the guard.
      **The `run.yaml`-exists assertion is the one the controller asked for**: it is the shape that makes
      *every execution paid for, the record lost* observable, and it must be asserted on the file rather
      than on the exit code.

- [ ] **Step 6: the mutations — two, and they must be run separately.**
      (i) Delete the two `_is_numeric` clauses from the paired arm's `col_keys`. **Fixture G's
      direct-call paired arm must FAIL** with the measured `TypeError`. *Why the branches differ:* the
      unguarded subtraction raises on `str` operands, measured.
      (ii) Delete them from the unpaired arm's `of_col`/`against_col`. **Fixture G's unpaired arm must
      FAIL.** *Why the branches differ:* the two arms are separate comprehensions, so a mutation in one is
      invisible to an assertion on the other — which is why this fixture has both.
      **A third, and it is the one that pins § Corrections 2:** move the unpaired narrowing from
      `of_col`/`against_col` into `of_values`/`against_values`. **The unpaired arm's `n_of` assertion must
      FAIL** while the interval still computes. *Why the branches differ:* `n_of` is `len(of_col)`, so the
      count and the vector disagree under the mutant and agree under the fix. **Without this mutation the
      correction is prose, and prose in a corrections section prevents nothing.**

- [ ] **Step 7: run** the four commands. **Delta:** Fixture G's three arms. **Commit:** `H5b task 7: the
      contrast guard sits at the subtraction, and skips`.

**What this task must NOT touch.** `paired_keys`/`unpaired_keys` (task 8 documents the ruling; no code
changes). The derived branch's `base_keys` — Decision 6 rules that a unit with no numeric column **does**
enter the intersection and the resample pool, because narrowing `paired_keys` would make `n_paired`
describe a different set than the pool `paired_percentile_of_derived` draws from. Pin arms A–E.

---

