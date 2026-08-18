# H4b-2 batch 1 (tasks 1, 4, 2, 3, 5) — whole-batch review

Reviewed at `ce77241` on branch `h4b2-clustered-contrasts`, 2026-08-17. Gates re-run in the
foreground: `ruff check` clean, `ruff format --check` 80 files, `mypy` 45 source files, `pytest`
**2163 passed, 1 skipped, 2 xfailed** — the expected numbers.

## Verdicts

**Spec compliance: PASS except one Major.** All five rulings match the design's decisions 3, 4, 5, 6
and 7, the ordering constraint *4 before 2* was honoured and its dependency is real, the payoff
figure is stated as zero everywhere and nowhere as an unblocked config, and the minted identifier is
a documented narrow refusal (reserved only — no § Errors row minted ahead of its emit). The
exception is Major 1: a normative sentence in `docs/reference.md` states a df provenance for
`n_paired_clusters` that one of the two constructions carrying that key cannot have.

**Task quality: PASS with two Majors.** Every mutation I re-ran discriminates, including the one the
brief's own text left unpinned; the report's two brief-vs-code disagreements are both accurate and
both were adjudicated in the implementer's favour on the facts. Against that: task 4's *grounds* are
measured at a proxy surface (`aggregated`) and are stronger than what the code holds (Major 2), and
one new test carries a quantifier in its name that no assertion checks and duplicates the test
directly above it (Minors 1–2).

Neither Major blocks anything that ships today; both become reachable at task 14. **Owners named
below rather than dated**, since a deadline is not an owner.

---

## Findings

### Major 1 — a normative df claim the percentile construction cannot honour

`docs/reference.md` § Contrasts, in the `n_paired_clusters` paragraph task 2 added — the clause is
self-locating:

> It is the count the interval's df was taken from, so a reader can check `clusters − 1` against the
> interval rather than take it on trust.

The clause is general over `n_paired_clusters`, and the paragraph's own first sentence makes both
clustered constructions carry that key. `paired_percentile_over_units_clustered` has no degrees of
freedom at all: per the design's **§ Corrections against the code, item 1**, it is not a function but
a third `method` string on `stats.paired_percentile_of_derived`, a resampling draw. **Verified by
reading** `src/publishable/stats.py::paired_percentile_of_derived` (no df anywhere in it or its
siblings) and the design's correction table.

This is the *"comment or docstring claiming a guarantee the code does not provide"* shape, in the
normative document rather than a comment. The implementer flagged it (report, disagreement 2) and
followed the brief verbatim, which was the right call mid-task — but the deferral to task 13/15 is
not accepted here: `reference.md` leads the code, and a spec sentence the code will not honour is the
same defect class task 1 exists to close (a build-hedged sentence). `CLAUDE.md` prefers **deleting a
claim to rewriting it**; the surrounding two sentences stand on their own without it.

**Owner: this batch's fix round, in `docs/reference.md`, before task 6 starts** — not task 13 or 15.
The sentence is already in the normative document, and every construction task from here reads that
paragraph as its specification.

### Major 2 — "the derived branch is unreachable in a clustered run" is measured at a proxy

`docs/superpowers/spec-defects.md`, task 4's entry *"RULED by H4b-2 task 4 — `E-DATA-CLUSTER-DERIVED`
is re-owned to H4c"*, in its **"H4b-2 does not need it"** paragraph; and, resting on it,
`docs/reference.md` § Contrasts — *"**Every** clustered contrast records a `method` carrying the
`_clustered` suffix"*.

The filing reasons from `aggregated` and concludes about a **predicate**. They disagree at exactly one
point: `cli._comparison_step_blocks` computes `is_derived = metric_key in of_derived or metric_key in
against_derived` from **`derived_by_key`**, while the loop it sits in iterates
`set(of_summary) & set(against_summary)` from **`aggregated`**. A name in both takes the derived
branch.

That state is producible in a clustered run, by three steps I **verified by reading**:

- in `stats.summarize_step`, the `E-STEP-KEY-COLLISION` raise for a derived key shadowing a recorded
  column sits **before** the `clusters is not None and seed is not None` guard that raises
  `E-DATA-CLUSTER-DERIVED`;
- in `cli.command_run`'s per-step block, `collapsed_by_key`, `derived_by_key` and
  `resample_fns_by_key` are assigned **before** the `summarize_step` call they feed;
- that call's `except ContractError` handler re-summarizes with no `derived` — the retry whose long
  comment enumerates the raises it must be gated against — but **never clears** those two mappings.

So `aggregated` holds the recorded column, `derived_by_key` still holds the same name, and the
contrast takes the derived branch. **Verified by running** a direct call to `_comparison_step_blocks`
(the suite's own idiom, three existing sites) with `aggregated` and `derived_by_key` sharing one name:

```
entry: {'delta': 0.6, 'basis': 'units', 'paired': True,
        'method': 'paired_percentile_over_units', 'n_paired': 12, 'ci95': [0.6, 0.6], ...}
```

— an **unsuffixed** `method`, which is precisely the case task 2's "no `clustered_by` sibling needed"
argument says cannot exist. (The `ci95: [x, x]` beside it is task 3's zero-width shape, incidentally
confirming that defect is live.)

**Major, not Critical:** nothing ships broken, because `E-DATA-CLUSTER-CONTRAST` still refuses
cluster + contrast at `validate`, so this is unreachable end-to-end until task 14. What is wrong is
the **grounds**, and a normative universal now rests on them.

**The ruling itself survives** — re-own `E-DATA-CLUSTER-DERIVED` to H4c by name and do not build the
clustered derived draw stands on the construction being a per-condition clustered percentile draw for
a recomputed metric, which is H4c's family. This finding is not "task 4 was wrong to re-own." What
needs narrowing is the reachability claim, and with it the § Contrasts quantifier.

**Owner, split and both by name:** the reachability sentence in **task 4's `spec-defects.md` entry**
is narrowed in this batch's fix round (append a correction; do not retro-edit the ruling); the
§ Contrasts quantifier and the collision case's record shape are **task 13's**, which is where
`n_paired_clusters` is written and where the derived branch would have to disclose or refuse. If task
13 declines it, it is filed against **task 14** — the commit that makes it reachable — and not left
to "whichever slice".

Also checked, per the review brief: the re-owner **is by name** — "**Owner from here:** H4c",
"**H4c inherits the composition itself**" — never "whichever slice does X". Clean.

### Minor 1 — a test name asserting a quantifier no assertion checks

`tests/test_validate.py`'s `test_every_unpaired_comparison_shape_still_earns_the_allocation_refusal`
exercises **one** shape: a declared contrast across a `groups` axis beside `cluster_by`. The other
route to an unpaired comparison — a baseline-generated cross-arm one — is not in it. **Verified by
reading** the two pre-existing tests that do cover it
(`test_a_generated_cross_arm_comparison_is_refused_and_the_within_arm_one_is_not` and
`test_a_declared_contrast_across_arms_is_refused`, both in the same file), so the guarantee holds in aggregate and this
is Minor rather than Major — but the name is what a future reader greps for and stops at, which is the
documented *"test whose name claims the guarantee"* shape.

### Minor 2 — that test is a near-duplicate of the one above it

The test immediately above it, `test_a_contrast_beside_groups_and_cluster_by_draws_both_refusals`, uses
the same `_groups_cluster_doc`/`_groups_cluster_csv` fixture, the same contrast, and asserts the same
two codes by set equality. **Verified by running** task 5's prescribed `validate.py` guard inversion
against the full suite: 87 tests fail, both of these among them — the new test adds no discriminating
power for the mutation it was written for. Its stated value is that task 14 can delete one line from
it, but the spec's own task 15 requires the co-reporting tests to be **narrowed rather than deleted**,
so the pre-existing test is edited at 14 regardless and is the stronger pin once narrowed.

### Minor 3 — the literal pin is scoped to one function body

`test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch` reads `inspect.getsource(_comparison_step_blocks)`. Extracting either
`"paired": True` write into a helper passes both assertions with the guarantee gone. Worth one line in
the docstring or the filing; task 5's `spec-defects.md` entry says the test "fails the moment
either literal becomes conditional", which is true and not the only way it can be defeated.

Both assertions do discriminate, which the brief asserted from its description only — **verified by
running**: the prescribed `"paired": bool(True)` mutation fails assertion 1 alone (full suite: 1
failed, 2162 passed), and an added third `"paired": is_paired` write fails assertion 2 with assertion
1 passing (`assert 3 == 2`).

### Minor 4 — the insertion orphans the weighted paragraph that followed the weighted example

The `n_paired_clusters` block was inserted, per the brief, immediately after the weighted
`arm_sensitivity` fence — which puts it between that example and the *"Whatever core weighted
moves together, and `weighted_by` and the effective size travel beside it either way…"*, a paragraph
that reads as continuing from the weighted example. The consequence is that the new closing paragraph
forward-references *"the same obligation a weighted entry carries"* to a statement that now appears
**after** it. Prose only; no claim is wrong.

---

## Checked and clean — stated explicitly so it is not re-filed

- **The `"in this build"` hedge is still present** in `docs/reference.md` § Statistical reporting (*"does not compose with either weighted form in this
build"*), and that is
  correct-by-design: decision 3 and task 1's brief both assign the de-hedge to **task 8, "in the same
  commit as the emit."** Task 1 is a ruling and touches no document but `spec-defects.md`. Not a
  finding.
- **`E-DATA-WEIGHT-CLUSTER-CONTRAST` was free at the commit claimed.** `git grep` at `8e26727` over
  `src docs tests README.md` → exit 1; the same sweep at `HEAD` over the four documents, `src/` and
  `tests/` → exit 1; the control (`E-DATA-CLUSTER-CONTRAST`, same rev, same file list) → hits in ten
  files, so the sweep can fail. Today the identifier appears **only** in the development record
  (`spec-defects.md`, the plan, this batch's report) — no § Errors row minted ahead of its emit.
- **Task 1's claim that such a config earns `E-DATA-CLUSTER-CONTRAST` alone is true.** **Verified by
  running** a `weight_by` + `cluster_by` + declared-contrast config through `validate_config` (probe
  test appended to `tests/test_validate.py`, run, then removed): `CODES: ['E-DATA-CLUSTER-CONTRAST']`.
  So the hedged sentence is indeed enforced by nothing else, and the refusal is alive.
- **`E-DATA-CLUSTER-CONTRAST` is alive and untouched**, and the one new test naming it asserts it
  **alongside** (`in`), not as a total code set.
- **No sentence anywhere claims this slice unblocks a config.** Swept the changed documents by **file
  list** for `unblock|newly execut|executable count|blocker count` with a can-fail control: every hit
  says zero / "unblocks nothing", and six-and-three are stated as unchanged.
- **Task 3's amend-rather-than-strike is coherent with the convention.** The entry it amended
  (*"OPEN — a stratified paired draw can publish a zero-width contrast interval"*) is **OPEN** and not closed — the code lands at task 9 — and a live list
  strikes only a *closed* gap. The stale amendment decision 6 orders **struck** is a different row,
  the sorted-pool precondition row in `spec-defects.md`'s deferral table, owned by task 16; the design's own
  § Corrections says so. The new amendment claims only that the rule is now specified and names task 9
  as the closer, which is true of the document today.
- **The report's disagreement 1 reproduced exactly.** Task 4's guard mutation
  (`seed is not None` → `seed is None`, full unfiltered suite): the pin fails on
  `assert "total" not in aggregated`, one assertion earlier than the brief predicted, plus exactly the
  three collateral tests the report names and no others (4 failed, 2159 passed). The brief's predicted
  failure line was wrong; the discrimination is real and stronger. The implementer's account is
  accurate.
- **The report's disagreement 2 is accurate and is upgraded to Major 1 above.**
- **Doc mutations both discriminate** (**verified by running**): renaming `n_paired_clusters` in prose
  *and* fence fails `test_the_clustered_contrast_record_key_is_documented`, and rewording
  "reports no interval rather than a zero-width one" fails its own test, with the controls untouched.
- **Mechanical pass on `docs/reference.md`**: no duplicate heading anchors, no new broken `#anchor`
  (the 13 my slugger flags are pre-existing `&`-in-heading false positives, none in the edited
  region), no trailing whitespace or tabs, no `x` for multiplication, no new tables.
- **Blind-mutation claims**: the three the plan records as blind belong to tasks 7, 10 and 11 and were
  not touched by this batch, so none was re-derived or re-checked.

## Could not check

- That the Major 2 corner is producible **through `run` end-to-end** — `E-DATA-CLUSTER-CONTRAST`
  refuses cluster + contrast at `validate` today, so `command_run` returns `EXIT_WRONG` before
  `_comparison_step_blocks`. Established instead by reading the three code paths above plus a
  direct-call probe. It becomes runnable at task 14, which is where the check belongs.

## Tree state

Clean. Four mutations were applied and reverted **by editing the file back** (`stats.py` guard,
`cli.py` `"paired"` literal twice, `validate.py` allocation guard), plus a temporary probe test in
`tests/test_validate.py` and a temporary doc rename, each reverted and each revert **verified by
re-running** the affected tests, not by `git status` alone. `git status --porcelain` is empty,
`__pycache__` cleared, pytest temp directories cleared (host had 3.1–3.6 GiB free throughout; no
`ENOSPC`).
