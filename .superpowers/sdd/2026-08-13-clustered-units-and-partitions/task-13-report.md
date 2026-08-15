# Task 13 report: the consistency passes and the exit criterion

**Status:** complete. `uv run pytest` 1391 passed, 2 xfailed; `ruff check` clean; `mypy` clean
(40 source files). `ruff format` was not run. Two commits, `c0ccd8d` and `e91cf0d`, documents
only — no `src/` change was needed.

**The brief was accurate.** Every claim it made that I checked held: the two surviving `src/`
references are comments, the `NOT BUILT` count reads seven, the row titles it listed are the
right ones, and its correction of its own row-3 attribution (the refusal, not the construction)
is right. No defect found in it. Two things it did not name turned up in step 8 and are fixed.

---

## Step 1 — both retirements, both directions

`__pycache__` deleted before the greps, per the brief's warning.

```
grep -rn --include='*.py' -E 'E-DATA-CLUSTER-UNSUPPORTED|E-REPL-FOLD-STRATIFY-UNSUPPORTED' src/
git ls-files '*.md' | xargs grep -n -E '<same two codes>'
```

| Direction | Result |
|---|---|
| `src/**/*.py` | `E-DATA-CLUSTER-UNSUPPORTED` **zero**. `E-REPL-FOLD-STRATIFY-UNSUPPORTED` **two**, both the disclosed comments |
| tracked `*.md` | **zero** for both |

**The two survivors are comments, verified by reading them, not by their line numbers.**
`src/publishable/validate.py` § `_check_fold_stratify_by`'s docstring ("Before task 12 retired
… no config reached the partition at all") and `src/publishable/cli.py`'s strata-comprehension
comment ("task 12 retired that code, which made it reachable"). Neither is a `raise`, a
`code=` argument, nor a member of any code list — `REPL_DECLARATION_CODES` and every other
tuple/list of codes was covered by the same grep, which returned only these two lines.
Citing a task number in a `src/` comment is house practice here, not a slip: 16 such
citations exist across seven modules.

**Both controls report.** The same `--include='*.py'` grep for `E-DATA-CLUSTER-UNKNOWN` returns
12 hits over three modules; the same `git ls-files` grep returns `docs/reference.md`. A grep that
found nothing for a live code would have been the false-negative the brief warned about.

**One more grep than the brief asked for**, because `--include='*.py'` is the right defense
against bytecode but cannot see a retired code in a tracked non-`.py` file — a
`readme_templates/` fragment, a generator's scaffold, a `templates/` config:

```
git grep -n -E 'E-DATA-CLUSTER-UNSUPPORTED|E-REPL-FOLD-STRATIFY-UNSUPPORTED'
```

Eight hits: the two known `src/` comments and six in `tests/` — all historical framing in
docstrings and section comments ("was live when these were written", "the retirement … made
reachable"), which is the framing task 12's report says it kept deliberately. **Nothing under
`src/publishable/readme_templates/`, `generators/` or `templates/`**, so no scaffolded project
can carry either code.

## Step 2 — the `NOT BUILT` count reads seven

`grep -c 'NOT BUILT' docs/reference.md` → 9, of which **7 are markers inside the fenced config**
(`sweep.groups`; `data.units.assign`, `.holdout`, the `{resolver: <name>}` form of `.from`, a
non-`within` `allocation`; `statistics.resample`, `.null_test`) and 2 are the prose that counts
them. The prose reads "**Seven** declarations above are not yet built" and enumerates exactly
those seven. Control: `grep -E '(Nine|Eight|Ten) declarations above'` → nothing, so no stale
count word survives anywhere.

**Exactly two markers left the list**, proven against the branch point rather than asserted:
`git diff fc98a09..HEAD -- docs/reference.md | grep -E '^[-+].*NOT BUILT'` shows two removals
and no additions — `cluster_by: null # NOT BUILT …` and the `repeats` comment's
"a fold's `stratify_by` is NOT BUILT" — and nothing else.

## Step 3 — registry integrity, both directions

Scripted over every tracked `src/*.py` and `docs/reference.md`, and run **twice**: at `HEAD` and
in a worktree at `fc98a09`, so the question answered is "did this slice introduce a gap", not
"does the repo have one".

- **Documented but not emitted: empty.** No documented code has lost its emit site. A stronger
  variant of the same check — documented codes whose only `src/` appearances are unquoted prose —
  is also empty, so nothing is documented that survives merely as a comment.
- **Emitted but undocumented: 18 at `HEAD`, 19 at `fc98a09`.** The `HEAD` set is the branch-point
  set **minus `E-DATA-CLUSTER-UNSUPPORTED`** and nothing else. Every member is either the
  deliberately-unregistered `-UNSUPPORTED` family (§ The one config file names them instead of
  § Errors, by that section's own argument), a retired code surviving as a comment
  (`E-SWEEP-BASELINE-PARTIAL`, `E-REPL-FOLD-STRATIFY-UNSUPPORTED`), or a pre-existing
  creation-command/provenance gap already recorded in `spec-defects.md` § "Nine undocumented
  run-time and creation-command `E-` codes". **This slice added none.**
- **Every code the slice minted is documented**: `E-DATA-CLUSTER-UNKNOWN`, `-VARIES`,
  `-CONTRAST`, `-DERIVED`, `W-DATA-CLUSTER-UNDECLARED`, `E-REPL-FOLD-STRATIFY-UNKNOWN`,
  `-VARIES`, `E-DATA-WEIGHT-VARIES`.
- **The codeless § Validation rows an identifier grep cannot see** were checked separately, by
  title, in step 4 — including the sibling task 12 added, *Clustered deltas aren't computed*,
  which carries no code and pairs with `E-DATA-CLUSTER-CONTRAST`.

**Both directions proved able to fail.** The emitted-but-undocumented direction reported a
difference for real (the `fc98a09` run names `E-DATA-CLUSTER-UNSUPPORTED`, the `HEAD` run does
not). For the other direction I appended `E-FAKE-CONTROL-CODE` to `reference.md`, re-ran, and it
was reported as documented-but-not-emitted; the file was restored and `git status` confirmed
clean.

## Step 4 — H3b's § Validation rows, by title

Every row located by its title, never by number. Each has an implemented check, an emitted
identifier, and a test that produces it.

| Row (by title) | Identifier | Check | A test producing it |
|---|---|---|---|
| *Clustering looks undeclared* | `W-DATA-CLUSTER-UNDECLARED` | `validate._check_cluster_by` | `test_a_cluster_looking_column_warns_when_nothing_declares_it` |
| *Cluster attribute exists* | `E-DATA-CLUSTER-UNKNOWN` | `validate._check_cluster_by`, `units.clusters_of` | `test_a_cluster_by_naming_no_attribute_is_reported` |
| *Folds fit inside the clusters* | `E-REPL-FOLD-K-TOO-LARGE` | `replication._fold_k` over `units.fold_basis` | `test_k_above_the_cluster_count_is_refused_through_validate` |
| *Stratification attribute exists* (`fold.` half only) | `E-REPL-FOLD-STRATIFY-UNKNOWN` | `validate._check_fold_stratify_by` | `test_a_fold_stratify_by_naming_no_attribute_is_reported` |
| *Fold strata survive clustering* | `E-REPL-FOLD-STRATIFY-VARIES` | `validate._check_fold_stratify_by` | `test_a_fold_stratum_varying_within_a_cluster_is_reported` |
| *Leave-one-out is affordable* (corrected) | `W-EXEC-BUDGET` | `_check_sweep` → `_repeat_total` → `_level_count`, on `fold_basis` | `test_leave_one_cluster_out_is_costed_in_clusters` |

```
uv run pytest tests/test_validate.py tests/test_units.py tests/test_replication.py \
  tests/test_cli.py -q -k "cluster or stratum or stratif or costed or budget or leave_one_out"
→ 127 passed, 594 deselected
```

**Task 2's `-k` near-miss applied as a habit**: I did not trust the selection. `--collect-only`
output was dumped and each of the eight names above (plus both budget controls and
`test_leave_one_out_draws_one_fold_per_cluster`) was checked for membership by exact match. All
present; nothing that matters was deselected.

**One mutation, spent on the only row no earlier task pinned end-to-end.** The ledger records
that the budget half reaches the fold count through `_check_sweep → _repeat_total → _level_count`
and never through `_fold_k` — a different path from the other five. Mutating
`validate_config`'s call to cost by the roster instead:

```
_check_sweep(..., fold_basis=(len(roster) if roster is not None else basis))
→ FAILED test_leave_one_cluster_out_is_costed_in_clusters (W-EXEC-BUDGET fired)
   passed test_leave_one_out_is_costed_in_units_when_nothing_is_clustered
```

The probe discriminates and its control still reports. Restored from a pristine copy and
re-verified by re-running, not by `git status`.

## Step 5 — `partition_units`' contract, where H3c and H3d will read it

**Ruling: the assignment order is a promise, and it is now in `reference.md` § Clustered units.**

The ledger's own evidence decides it. Task 7 *already* composed on the order — partition within
each stratum by task 4's rule, then merge index-wise — and recorded that the sorted-merge
mutation is **unkillable by a balance assertion**, because permuting a stratum's pieces leaves the
size multiset unchanged. So a later slice that reads only the docstring can reorder the assignment
and break nothing visible. H3c rewrites the function for cells and H3d for an uneven two-way
split; both will re-derive the rule from whatever they read. A promise two slices build on and no
test can defend by property belongs in a document.

Landed in the `k`-is-bounded bullet, which already said "as evenly as whole clusters allow": the
digest-seeded shuffle, then largest-first to the fold holding the fewest units, **with the reason
each half exists** (without the shuffle, equal-sized clusters are ordered by the input file;
without the largest-first pass, a big cluster arrives last with nowhere balanced to go). The
absent promise is stated too — **no bound on the unevenness**, per task 7's finding (a), so no
later reader can mistake the balance language for a guarantee. The `stratify_by` bullet now says
why the composition is sound and that the constancy rejection is what makes it so, which is task
7's docstring caveat promoted to the document that a slice removing the check would be read
against.

**Amended in `e91cf0d`, and this was the weak half.** The first wording said core "merges the
per-stratum folds", which leaves the merge *order* free — and the merge order is exactly the part
task 7 measured as **invisible to any assertion about fold sizes**, since permuting a stratum's
pieces leaves their sizes alone. Leaving it unstated would have reproduced, one level down, the
gap that justified stating the assignment order at all. It now says **index-wise**: fold *i* of
each stratum's partition becomes fold *i* of the result, with the reason it cannot be tested by
size recorded beside it.

## Step 6 — the worked example did not move

Verified with a **real temporary commit** (`git commit --allow-empty`, diff, `git reset --soft
HEAD~1`), because a working-tree edit is invisible to a two-dot diff.

`git diff fc98a09..HEAD --stat -- README.md docs/design-principles.md docs/reference.md` touches
`reference.md` only. Every figure was then counted in `git show <rev>:<file>` at both revisions —
240 / 228 / 12, r = 0.581 / 0.607 / 0.412 and their three `ci95`s, delta 0.026 with
[−0.007, 0.059], kendall −0.169 with [−0.213, −0.125], `repeat_spread` 0.014, `8e21` / `1a2b` /
`3d8a` / `6b1f`, README's `2f5c8d0`, both run IDs, `cohort-pilot` / `cohort_pilot` /
`correlation_pilot`.

**Exactly one count changed: `240` in `reference.md`, 25 → 26.** Read it rather than reported it:
§ Repeat kinds' `k: all` paragraph gained "while the same 240 units clustered into 20 animals is
60", a new sentence *using* the existing figure consistently (20 × 3 = 60). **No figure changed
value.** Control: mutating one `0.581` moves its count 1 → 0, so the probe reports a real move.

## Step 7 — the four prevented mistakes, one at a time

| Row | Closed by, checked as behaviour |
|---|---|
| **Ignored clustering** | **Both halves live.** `W-DATA-CLUSTER-UNDECLARED` is emitted and tested; the intervals are cluster-robust *in a real run* — `tests/test_cli.py` asserts `method == "t_over_units_clustered"` at four separate run sites and `weighted_t_over_units_clustered` at a fifth. Task 8's transient state (`n.clusters` printing beside non-robust intervals) is **gone**, which is why the ledger said to check this row only after task 9 |
| **A cluster split across train and test** | **Both halves, separately.** *Partition route:* `cli.command_run` passes `clusters=clusters` to `partition_units`, and `test_a_clustered_fold_puts_no_cluster_in_two_folds` pins **exact fold membership over a real run** (7/4/4 from clusters 7/3/3/1/1 at k = 3) plus the no-split property independently — not sizes, which task 4 proved coincide across both partitioners. *Input-file route:* `E-DATA-CLUSTER-VARIES` from `units.collapse_measurements`, tested on both surfaces. *And the `k` bound* the row also names is `E-REPL-FOLD-K-TOO-LARGE`. A cluster mis-collapsed at resolution is in the wrong place before any partition runs, so neither half substitutes for the other |
| **Resampling clustered rows as if independent** | **The refusal, per the ledger's correction — not task 10's construction.** Confirmed there is no live path to a unit-level draw over clustered data: the only percentile caller in `src/` is `percentile_of_derived` (plus `paired_percentile_of_derived`), and `E-DATA-CLUSTER-DERIVED` refuses it under `cluster_by` at run time (`stats.py`, asserted in `test_cli.py` and `test_stats.py`); the paired form is reachable only through a contrast, which `E-DATA-CLUSTER-CONTRAST` refuses at `validate`; `percentile_over_units` has **no caller at all**, `statistics.resample` still being `E-STATS-RESAMPLE-UNSUPPORTED`. The mistake is impossible **by refusal rather than by construction** — see the note below |
| **A permutation that shuffles away the matching** | **Confirmed, not assumed.** `E-STATS-NULLTEST-UNSUPPORTED` is raised from `validate.py` and asserted in three `test_validate.py` places. Out of scope; nothing built |

**One thing worth saying plainly about rows 3 and 4.** Both describe a *design* — the cluster as
the bootstrap draw, the within-cluster permutation — that this build refuses outright. The row's
requirement is that the mistake be structurally impossible, and it is; the mechanism is a refusal,
not the construction the row narrates. That is not a new class introduced by this slice: it is how
`experimental-designs.md` already treats `assign`, `allocation: between`, `sweep.groups`,
`statistics.resample` and `statistics.null_test` throughout.

## Step 8 — the passes, and a precedent judged rather than inherited

**Mechanical, over all six tracked `*.md`.** Written fresh as a throwaway script. Links and
`#anchor`s resolved, duplicate anchors, table column counts against the header, empty rows,
trailing whitespace, tabs, invisible unicode, `x`-for-`×` — all skipping fenced blocks.
**0 findings at `HEAD`; 0 findings at `fc98a09`**, so the pass is clean and was clean, and the
edits below did not disturb it.

The script needed two fixes before it could be trusted, both of the false-positive class task 12
hit: my slugger stripped `_` (GitHub keeps it, so `#…derive_seed…` looked dead) and my table
counter counted escaped `\|` inside cells. **Control:** injecting a duplicate `## Secrets &
credentials` heading and a trailing-whitespace line reported both; restored, `git status` clean.

**Cross-document.** *Declared vs. derived* — `clusters` is derived, and no passage shows it as a
settable input: the only `clusters:`-shaped keys in any tracked document are `limits.min_clusters`
(a real threshold) and `n: {…, clusters: 10}` (a reported figure). *Config completeness* —
`cluster_by` is in § The one config file; a `fold`'s `stratify_by` correctly is not, for the same
reason a `fold`'s `k` is not, and the prose now says so. *Enum comments* — the `repeats` comment
`# seed | batch | fold` is total over § Repeat kinds' three rows. *Versions*, *prevented
mistakes*, *worked example* — steps 6 and 7 and no version change in this slice.

**Four findings, all in `reference.md`, all fixed in `c0ccd8d`:**

1. **Three `method` strings core writes had no row** in § Statistical reporting's first table —
   the table whose stated purpose is that "two readers of one `run.yaml` agree on what they're
   holding". Found by enumerating every `method="…"` literal in `src/` and grepping each against
   the document: `percentile_over_units_clustered` (task 10), `weighted_t_over_units_clustered`
   (task 11) and — **not in the brief and not in `spec-defects.md`** —
   `weighted_t_over_units`, H3a's own construction, which the table never named at all
   (§ Weighted samples describes it as "a weighted `t_over_units` interval", so the string
   appears nowhere). All three landed together; a row for the weighted clustered form reads as an
   exception to a row that must exist first. **All eight strings `src/` writes are now in the
   table, checked both directions.** The two `spec-defects.md` entries are marked resolved.
2. **§ Statistical reporting's "a derived metric is resampled whether or not you declare
   `statistics.resample`" was unconditional**, and `E-DATA-CLUSTER-DERIVED` refuses exactly that
   case. This is the class task 3 established — a document describing the *unchecked* outcome
   after the check lands — and CLAUDE.md's prevented-mistakes rule requires the fix. A clause now
   states the refusal, why it is run-time rather than `validate`, and links the registry row.
   **Amended in `e91cf0d`:** the first wording said core "says so, as `E-DATA-CLUSTER-DERIVED`",
   which names the wrong signal. `cli` *contains* the `ContractError` and re-reports it as
   `W-STATS-AGGREGATE-FAILED` with the code in its message, so the identifier alone is not what
   the record holds. Both are named now, with the containment that keeps the recorded columns and
   the `run.yaml`. My own concern 2 sat on the other side of this and the prose had to agree
   with it.
   **A fifth finding, produced by fix 1 rather than found alongside it:** growing the method
   table from four rows to seven pushed three counting phrases — "the two rows above", "that
   third row", "which of the four" — further from the table they actually point at, which is
   § The unit table is the inference base's `basis` table, *not* the one that grew. Checked one
   at a time: **none was falsified.** All three now name their referent instead of counting to
   it, so a later row cannot falsify them either. This is my own step-2 class — a number in prose
   no mechanical check catches — turned on my own edit.
3. **The § Clustered units and § Repeat kinds contract additions** (step 5).
4. **A dangling cross-reference:** the § The one config file paragraph said a `fold`'s
   `stratify_by` "carries no marker" in "its comment in the `replication` block above" — but task
   12 removed that clause entirely, so the comment it points at no longer exists. It never needed
   one, and the replacement says why (the block shows what `init` writes; a level's fields belong
   to the kind, as `k` already demonstrates) and points at § Repeat kinds, which does enumerate
   `k` and `stratify_by`.

**The § Case-control (matched) precedent: judged, and the conclusion stands on different
evidence than task 12 gave.** Task 12 cited `experimental-designs.md`'s weighted-samples row as
the H3a precedent. **That citation is wrong** — that row says `weight_by` "weights the estimate
and records `weighted_by`", which is built, and it describes no weighted *contrast*, so it is not
an instance of the class at all. The conclusion is nonetheless right, on stronger evidence the
document supplies itself: it annotates unbuilt state **nowhere** (grep for `NOT BUILT`, "not yet
built", "this build" → zero), and two of its own four cluster rows (*Resampling clustered rows*,
*A permutation that shuffles away the matching*) already narrate refused machinery unannotated,
as does § Case-control's own reliance on `assign` — itself `NOT BUILT`. Annotating line 328 would
single out one refusal in a document that marks none, and `reference.md`'s § Validation row
*Clustered deltas aren't computed* already records the refusal where refusals are recorded.
**Left unchanged, deliberately.**

## Step 9 — commit

Two commits, `docs/reference.md` only: `c0ccd8d` (the four findings) and `e91cf0d` (the three
amendments above). `docs/superpowers/` is gitignored, so the
`spec-defects.md` resolutions are working notes and are not in it — which is also why the
"tracked `*.md`" scope in steps 1 and 8 legitimately excludes that file. **No empty commit was
created**; steps 1, 2, 3, 4, 6 and 7 found nothing to fix, and that is recorded as a result
rather than dressed up as work.

## Concerns for the whole-branch review

1. **`percentile_over_units_clustered` is now documented with no caller.** `spec-defects.md`
   proposed the row land "with the slice that wires it"; the ledger asked task 13 to land it.
   I landed it, because it shares an edit with the two rows that *are* reachable and because the
   table's purpose is defeated by naming a construction only once something reaches it. But a
   reader can look up a `method` no `run.yaml` can currently contain. H4 decides.
2. **The derived-metric refusal is still a warning where a reader expects a pre-run refusal**
   (task 12's concern 2). The document now says so, which narrows the surprise but does not
   remove it: a clustered run with a deriving template spends its whole budget and then loses
   every derived metric with only `W-STATS-AGGREGATE-FAILED`.
3. **Task 7's finding (b) is undocumented and unchecked**: `validate` bounds `k` only by the whole
   roster's `fold_basis`, so a legal `k` can leave a fold holding none of a stratum, silently
   defeating stratification. It needs a new § Validation row and a new code — code work no brief
   in this slice owned, so out of scope here. Deliberately *not* papered over with a document
   sentence.
4. **Task 4's concern (2) likewise stands**: a cluster larger than n/k unbalances the split with
   no warning. § Clustered units now *states* that no unevenness bound is promised, which makes
   the behaviour documented rather than surprising, but a `validate` warning may still be worth
   minting.
5. **Two `src/` comments name the retired fold code** (task 12's concern 1). Verified benign
   here; a future retirement sweep over `src/` will hit them again.
