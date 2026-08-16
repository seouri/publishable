# Task 19 review: the owned prose sweep

Reviewed `review-49e4a41..538376d.diff` (one commit, `538376d`) against
`task-19-brief.md`, `task-19-report.md` and `CLAUDE.md`.

**Verdicts**

1. **Spec compliance — ❌**
2. **Task quality — ❌**

The sweep found every site. Two of the four *replacement* sentences are themselves
false — which is the failure mode the brief was written to avoid, and which the
task's stated deliverable ("no false present-tense claim about `holdout` anywhere in
`src/`") forbids.

---

## Critical

### C1. `validate.py:2560` — "Three checks answer to one row" is false; it is two, and the causal clause is false too

**The new text** (`_check_fold_stratify_by`'s docstring, lines 2555–2561):

```
    ... and its `data.units.assign.<axis>.stratify_by` and
    `data.units.holdout.stratify_by` halves are `_check_assign`'s and
    `_check_holdout`'s, under their own codes
    (`E-DATA-ASSIGN-STRATIFY-UNKNOWN`, `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`), so
    neither is discharged by this. Three checks answer to one row, and the row
    carries no code for that reason.
```

The row it cites is `reference.md` § Validation's *Stratification attribute exists*.

**How verified — primary source, twice, from both ends:**

- `docs/reference.md:273`, the row itself: "A `fold` level's **or `holdout`'s**
  `stratify_by: label` … Neither reads a group axis, so *Allocation strata exist* is
  `assign.<axis>.stratify_by`'s row instead, a target an axis name is also legal
  against."
- `docs/reference.md:526`, the § Errors row for `E-REPL-FOLD-STRATIFY-UNKNOWN`, saying
  it independently: "*Stratification attribute exists* also covers
  `holdout.stratify_by`, reported by its own code, `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`.
  `assign.<axis>.stratify_by` is **a different row**, *Allocation strata exist*, and
  its own code, `E-DATA-ASSIGN-STRATIFY-UNKNOWN`."
- `docs/reference.md:302` confirms *Allocation strata exist* "**Owns**
  `assign.<axis>.stratify_by` under those two methods".

So **two** checks answer to that row (`_check_fold_stratify_by` and `_check_holdout`),
under two codes. `_check_assign`'s `stratify_by` half answers to a *different* row.
The docstring routes assign's half into the wrong row and then counts three.

**Second defect in the same sentence.** "and the row carries no code for that reason"
asserts a cause that does not exist. Verified at `docs/reference.md:220-221`: the
§ Validation table's header is `| Check | Example failure |` — two columns. **No**
§ Validation row carries a code, whatever number of checks answers to it. The clause
is a false causal claim wrapped around a vacuously true one, and a reader will take it
as "rows normally carry codes; this one is special."

**Pre-existing text the rewrite built on and should have caught.** The retained clause
immediately above — "the first row names no particular `stratify_by`" — is also false
against `reference.md:273`, which names exactly two: a `fold` level's and a `holdout`'s.
The diff rewrote the sentence that continues from it (`... and its ... halves`), so this
was in the edit's own field of view.

**Corrected form** (the accurate statement): the row names a `fold` level's and a
`holdout`'s `stratify_by`; the holdout half is `_check_holdout`'s under
`E-DATA-HOLDOUT-STRATIFY-UNKNOWN`, so neither is discharged by this. Two checks answer
to the one row. `assign.<axis>.stratify_by` is not this row's at all — it is
*Allocation strata exist* / `E-DATA-ASSIGN-STRATIFY-UNKNOWN`.

The verified-correct half: `_check_assign` (`validate.py:1511`) and `_check_holdout`
(`validate.py:2685`) both exist, and both emit the named codes —
`E-DATA-ASSIGN-STRATIFY-UNKNOWN` at `validate.py:2031`, inside `_check_assign` (checked
that no `def` at column 0 falls between 1511 and 2543); `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`
at `validate.py:2892`/`2900`/`2908`/`2918`, inside `_check_holdout`. Naming the two
functions and the two codes is a **fact**, not a call-site count, and will not go stale
the way `units.py`'s enumerations did. That part is fine.

### C2. `cli.py:1451` — "three declarations naming one attribute produce three codes" is four, contradicting a sibling docstring in this repo

**The new text** (`clusters_of` note, lines 1447–1453):

```
        # ... — `holdout`
        # and `assign` each read the same attribute under their own
        # (`E-DATA-HOLDOUT-STRATIFY-VARIES`, `E-DATA-ASSIGN-STRATIFY-VARIES`),
        # which is why three declarations naming one attribute produce three
        # codes rather than one shared one.
```

**How verified — an in-repo sibling states the opposite number:**

- `src/publishable/units.py:2291-2294`, `stratum_varies_within_cluster`'s docstring:
  "the caller decides which declaration to name — **four callers today, under four
  codes**: `E-DATA-ASSIGN-STRATIFY-VARIES`, `E-REPL-FOLD-STRATIFY-VARIES`,
  `E-STATS-RESAMPLE-STRATIFY-VARIES` and `E-DATA-HOLDOUT-STRATIFY-VARIES`".
- The fourth declaration is real and live: `docs/reference.md:326-327` carries both
  *Resample strata exist* and *Resample strata survive clustering*;
  `validate.py:5669`/`5766` emit `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`/`-VARIES`;
  `stats.py:863` raises the `-VARIES` at run time.

So the count is four, and the new comment is falsified by a docstring already in `src/`.
This is exactly the class `CLAUDE.md` flags — a count phrase written into a comment on a
task whose deliverable is claim accuracy.

**Supporting half — the two codes named do not answer the question the sentence asks.**
The clause the parenthetical attaches to is "*which code a **missing value** belongs
under* is a property of the declaration being served." The `-VARIES` codes are not about
a missing value; they are the cluster-constancy refusal (a stratum that *varies within a
cluster*). Verified at `validate.py:2708` ("`E-DATA-HOLDOUT-STRATIFY-VARIES` — reads the
roster: a stratum that varies within a `cluster_by` cluster") and `reference.md:486`.
And for `holdout`/`assign` a genuinely **missing** value raises no code at all —
`units._stratum_groups` (`units.py:1605-1609`) renders it "`no value` and forms its own
stratum". The fold path is the one that would `KeyError`, which is what the surrounding
comment is actually about. The old wording ("under their own") was vague and future-tense;
pinning it to the `-VARIES` pair makes it specific and wrong.

---

## Important

### I1. Both false sentences were prescribed verbatim by the brief, and the report records no disagreement

`task-19-brief.md` Step 3(a) supplies C1's text and Step 3(c) supplies C2's, character
for character (compared against the diff's added lines). `task-19-report.md`
§ "Disagreements with the brief" says "None on substance" and records only the `E501`
friction. The implementer re-verified the **sites** — thirteen of them, thoroughly and
correctly — and did not verify the **replacement text**, on the one task whose entire
deliverable is claim accuracy, in a repo whose own rule is that six of six implementers
on the last slice found a real brief/code disagreement.

Consequence for the fix: **the brief must be corrected too.** Leaving Steps 3(a) and
3(c) as written means the next re-derivation reintroduces both sentences.

---

## Minor

### M1. `.gitignore` restored with `git checkout --`

`task-19-report.md` line 38 records restoring `.superpowers/sdd/.gitignore` "via
`git checkout --`" — the operation `CLAUDE.md` names as a trap ("destroys uncommitted
work, twice mistaken for reverting a mutation"). Harmless in this instance (the file's
tracked content was the intended target), but the accompanying "no data lost" is
asserted rather than shown, and `CLAUDE.md` asks for a revert verified by behaviour.

---

## Verified clean — stated so the record shows these were checked, not assumed

- **`cli.py:2641-2647`, the provenance pairing comment (site 7) — accurate.** It claims
  `None`/`None` "exactly when `alloc_doc` was never written — which is now when NEITHER
  an arm assignment nor a `data.units.holdout` resolved, the gate
  `build_allocation_document` widened." Verified against
  `artifacts.build_allocation_document`'s actual gate, read in the source:
  `if not group_axes and holdout is None: return None` — non-`None` when *either*
  holds. Verified the variable cannot be set any other way: `alloc_doc` appears at
  `cli.py:1644` (sole assignment, unconditional), `1646`, `2642`, `2648`; the file is
  written iff `alloc_doc is not None` (`cli.py:1646-1648`), and `alloc_hash` is set on
  the same branch, so the pairing is exact. Consistent with the write-site comment at
  `cli.py:1626-1629` — no contradiction between the two.
- **`materialize.py:126-127`, the implicit concatenation — correct, no missing or
  doubled space.** Evaluated the two literals in Python: the result is
  `'    holdout: null                  # e.g. {method: random, frac: 0.2} — one fixed train/test split'`,
  98 characters (under the 100 `E501` limit the brief's single-string form breached at
  109), one space either side of the em dash.
- **Column alignment preserved.** Computed the `#` offset for the block's five
  materialized lines: `input_manifest_policy`, `cluster_by`, `weight_by`,
  `measurements` and the new `holdout` all place `#` at index 35.
- **No test pins the literal.** `grep -rn "holdout: null\|fixed train/test split" tests/`
  returns only `tests/test_validate.py:912, 11315, 11324, 11336, 11344`; the sole
  assertion (`11344`) is `assert "holdout: null" in null_path.read_text()` against a
  differently generated file, and would hold regardless. The implementer's claim that
  `tests/test_materialize.py` does not pin it is correct — it contains no `holdout`
  match at all. `uv run pytest`: 1954 passed, 2 xfailed. `uv run ruff check .`: clean.
  `uv run mypy`: no issues in 42 source files.
- **The `holdout: null` comment is consistent with what `validate` accepts and with
  `reference.md` § The one config file.** `reference.md:91-93` shows the same block as
  `{method: random, frac: 0.2}` or `{method: by_attribute, from: split}`; the generated
  line shows the first under an explicit `e.g.`, matching its `measurements` sibling's
  convention (`# e.g. {by: read_id, collapse: mean}`, itself an example of a
  multi-form block). `reference.md:1173`'s shorter excerpt is an illustrative subset of
  the block (it omits `weight_by`, `measurements`, `assign`), not the full-expansion
  schema, so it is not a second source of truth that drifted.
- **Nothing accurate was deleted or weakened.** The diff touches exactly three comment
  blocks and one generated line in `src/`, plus the new report file — no documentation
  file is in the diff at all, so `experimental-designs.md`'s and `reference.md`'s
  within-cell "not built" notes (H3c-3's, and still correct) are untouched by
  construction. The brief's eight "do not touch" forward references are untouched.
- **No third instance of the false counts.** Swept `src/` for the count phrases
  themselves rather than for the two files they were noticed in —
  `grep -rn "three checks\|three codes\|three declarations\|four codes\|four callers\|two checks\|three rows" src/`
  — twelve hits, each read: only `cli.py:1451` (C2) and `units.py:2292` (the correct
  "four callers today, under four codes") concern this family. `validate.py:2560`'s
  "Three checks" does not contain any of those phrases and was found by reading the diff.

## What must change to clear this

1. `validate.py` — replace "Three checks answer to one row, and the row carries no code
   for that reason" with the two-check statement, and stop routing
   `assign.<axis>.stratify_by` into *Stratification attribute exists*; fix the retained
   "the first row names no particular `stratify_by`" while there.
2. `cli.py` — either say **four** declarations and four codes (naming
   `E-STATS-RESAMPLE-STRATIFY-*` alongside), or drop the count and keep the qualitative
   claim; and either drop the `-VARIES` parenthetical or move it off the "missing value"
   clause it does not answer.
3. `task-19-brief.md` Steps 3(a) and 3(c) — correct both prescribed texts, so a
   re-derivation does not reintroduce them.
