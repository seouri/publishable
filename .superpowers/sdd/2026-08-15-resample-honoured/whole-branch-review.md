# H4a whole-branch review — `statistics.resample` honoured

Branch `h4a-resample-honoured`. Reviewed at **`d59316d`**, one docs-only ledger commit past the
`faaa016` named in the brief; `git diff faaa016..d59316d` touches only
`.superpowers/sdd/2026-08-15-resample-honoured/progress.md`. Recorded here rather than filed as a
finding.

**Verdict: findings** — no Critical. Three Important, four Minor. None of the three Importants is a
wrong number in a run that validates clean; all three are record-consistency or ownership gaps of the
exact classes this branch set out to police. The acceptance property holds.

---

## What was verified, and how

**1. The acceptance property, both directions, by running configs — not by reading.**

A worktree at `eaf3605` (`git worktree add`, nothing destroyed) and the branch tree ran the *same*
config through `main(["run", …])`: 40 units, `sweep.baseline` + `sweep.grid` over `analysis.method`,
a condition-scaled recording step, a template `aggregate` returning a derived metric, `correction:
holm`, **no `statistics.resample`**. `run.yaml` from each, diffed as raw text.

The only differences are the volatile fields — `run_id`, `input_dir`/`output_dir`, `repo_root`, the
generated project's own commit sha, `input_manifest_hash` (path-driven), `started_at`,
`wall_seconds`. **`config`, `aggregated`, `vs_baseline`, `correction`, `family`, `family_size`,
`correction_level` are byte-identical.** `code_hash` is identical too, since it covers the generated
*project's* `src/**`, not this repo's. The undeclared run carries no `resample` key in any metric
block and `resample_draws: 2000` on derived metrics only — exactly the frozen shape the spec pins.

**Repeated in the two shapes the new threading passes through most code**, because one shape is not
the property: (a) undeclared + `report_by: [cohort]` beside a baseline comparison — the level-path
`summarize_step` call; (b) undeclared + `cluster_by` + `weight_by` with a derived metric and no
comparison — which fires `E-DATA-CLUSTER-DERIVED` and so exercises the **retry** path of I1 below
with `resample` undeclared. Both diffed as raw text against `eaf3605`. Enumerating every differing
line's key in each: `run_id`, `input_dir`, `output_dir`, `repo_root`, `commit`,
`input_manifest_hash`, `started_at`, `wall_seconds` — **and nothing else, in either.** Three shapes,
zero divergence under `aggregated`/`vs_baseline`/`correction`. The regression this slice exists to
preserve is preserved.

Declared: the same roster with `resample: {method: bootstrap, n: 500, stratify_by: [site]}` moves
every column to `percentile_over_units` / `percentile_over_units_clustered` with `resample_draws:
500`, moves a column contrast to `paired_percentile_over_units` with a real `cohens_dz`, and echoes
the resolved block per metric block. Method, draw count and strata all move.

**2. Aliasing.** Six generated `run.yaml` files (undeclared, declared, clustered+weighted,
`report_by`, `report_by`+cluster, contrast) swept as **raw text** for `&anchor` / `*alias`: zero hits
in all six, including the `report_by` shape that produced 1 anchor + 5 aliases before task 17's fix.
`_beside_n_copy`'s `copy.deepcopy` is deep enough to cover `stratify_by`'s nested list, which the
first shallow attempt was not.

**3. The zero-width sweep.** Probed every construction directly:

| construction | constant pool, no strata | constant pool, strata/clusters |
|---|---|---|
| `t_over_units` | `Interval(5,5)` (pre-existing) | — |
| `percentile_over_units` | `Interval(5,5)` | `None` (refuses) |
| `percentile_over_units_clustered` | — | `None` (refuses) |
| `percentile_of_derived` | `(Interval(5,5), 200)` | `(None, 0)` (refuses) |
| `paired_t_over_units([0.0]*40)` | `Interval(0,0)` (pre-existing) | — |
| `paired_percentile_of_derived` | zero-width, **no refusal** | — |

Tasks 9/10/15's refusals are real and fire. The fourth path — `paired_percentile_of_derived` — does
**not** refuse, and is filed as a deferral whose stated non-regression premise I confirmed
empirically: `paired_t_over_units([0.0]*40)` already returned `Interval(0.0, 0.0)`, so the same
design published the same zero-width interval before this branch. The deferral's reasoning is true
today. See Minor 1 for the scope qualification the "all three now refuse" claim needs.

**4. Cross-task seams, run end to end.** `cluster_by` + `stratify_by` + `weight_by` + declared
`resample`, with and without `report_by`; and the same without clustering so a contrast exists.
`_check_resample`'s six emission sites plus `W-STATS-RESAMPLE-FAMILY` all read cleanly against the
composites. One real gap found, Important 1.

**5. A cross-task mutation at the behaviour site.** `stats.py:1921`, `strata=strata` → `strata=None`
on the derived draw: **2 tests fail**, one in `test_cli.py` (end to end) and one in `test_stats.py`
(unit). Reverted by editing in place, `__pycache__` deleted, revert verified by re-running both tests
green and by `diff` against a pre-mutation copy.

**6. Mechanical doc pass** over the six `*.md` the four documents plus the feasibility analysis
comprise: every relative link and `#anchor` resolves (0 broken, once the slugger is corrected to
strip en/em dashes the way GitHub's does), no duplicate anchors, no trailing whitespace, no tabs, no
invisible unicode, every table row matches its header (4 apparent mismatches are all escaped `\|`
inside code spans). `CLAUDE.md` § The worked example is **untouched** — `git diff eaf3605..HEAD --
CLAUDE.md` shows no hunk anywhere near it; every number (0.581/0.488/0.661, 0.607, 0.412, 0.026,
[−0.007, 0.059], −0.169, 0.014, 240/228/12, the hash prefixes) is unchanged.

**6b. Cross-document pass** (the one no tooling substitutes for), run over the three documents this
branch did **not** edit:

- `README.md`, `design-principles.md`, `experimental-designs.md` describe `resample` nowhere as
  unbuilt or refused — `experimental-designs.md` § Mistakes core prevents already stated it in the
  present tense ("`statistics.resample` produces percentile intervals"), and its § What core will not
  do for you never listed it. `reference.md`'s retirement of the `NOT BUILT` marker **removes** a
  contradiction rather than creating one. The `cluster_by`-follows-the-draw rule at
  `experimental-designs.md`:284 agrees with `percentile_over_units_clustered`'s behaviour as shipped.
- **Declared vs. derived, versions, prevented mistakes, enum comments:** no drift. The
  `resample: null # bootstrap` inline comment lists the whole one-value enum, which is what § Enum
  comments requires.
- **Config completeness:** no new config field was added, so no downstream `run.yaml` example was
  invalidated. One count phrase in the same paragraph did go stale — Minor 4.

**7. Bidirectional registry sweep on the eight new/newly-real identifiers** —
`E-STATS-RESAMPLE-{UNITS,METHOD,N,STRATIFY-UNKNOWN,STRATIFY-VARIES}`,
`W-STATS-RESAMPLE-{CLUSTERS,FAMILY,THIN}`. Every one has a registry row in `reference.md` and a live
emit site in `src/`, and no new § Validation row lacks an emit site. `E-STATS-RESAMPLE-METHOD` is the
only one with no § Validation row; **checked, not a finding** — `E-STATS-CORRECTION-UNKNOWN` and
`E-STATS-REPORTBY-UNKNOWN`'s not-a-string half are the same shape and are likewise registry-only, and
the method enum is documented from its other end by § Statistical reporting's new *Resample methods*
table, which the registry row cites by name.

**7b. Sweeps, filtering the file list and never the output.** `E-STATS-RESAMPLE-UNSUPPORTED` survives
in exactly two places outside the development record: the feasibility analysis's dated
§ Executability section (correctly, as the code that *was* retired) and two `test_validate.py`
assertions that check its absence. `W-STATS-RESAMPLE-STRATIFY-UNHONOURED`, minted by task 14 and
retired by task 15, appears nowhere outside the record. Each sweep proved able to fail by being run
against a string known present.

**8. Payoff count.** The feasibility analysis states it correctly and at length: "one refusal retired
that 8 of 9 configs hit, a regression preserved, and zero experiments newly executing," with the
`holdout`/`weight_by`/resolver blockers each named, and an explicit paragraph that a retired-refusal
count is not an executable-run count. `CLAUDE.md`'s "H4a and H3d then unblock six" is the third,
different figure and is labelled as such in the spec. **No overstatement found anywhere.**

**9. Tree state.** `1800 passed, 2 xfailed`. `ruff check` clean. `mypy` clean, 42 files. Working tree
clean apart from this review file. `ruff format --check`'s 62 files not raised, per instruction.

---

## Critical

None.

---

## Important

### I1 — A contained `summarize_step` fault silently downgrades every recorded column out of its declared resample, and the record still claims one

`cli.py`'s retry after a `ContractError` from `summarize_step` deliberately omits `resample_columns`
and `strata`. The comment there says the retry's "job is to reproduce the recorded columns exactly as
the first call built them" and that passing `resample_columns` would be "inert right now". **The
first half is false whenever `resample` is declared**, and the path is reachable from two ordinary
designs: `E-DATA-CLUSTER-DERIVED` (a template deriving anything under `cluster_by`) and
`E-STEP-KEY-COLLISION`.

Verified end to end. Identical config, identical roster, `resample: {method: bootstrap, n: 500,
stratify_by: [site]}` with `cluster_by` + `weight_by`:

- template `aggregate` returns `{}` → `method: percentile_over_units_clustered`, `resample_draws: 500`.
- template `aggregate` returns one derived metric → `E-DATA-CLUSTER-DERIVED` fires, the retry runs,
  and the same column reports `method: weighted_t_over_units_clustered`, **no `resample_draws` key**,
  **and the `resample: {method, n, stratify_by}` echo still present**.

The resulting block is self-contradictory by `reference.md`'s own rules: § How a metric becomes a
number says the `resample` echo is "present in every metric block of a run that declared one" and
that a column's `resample_draws` is absent *only* when nothing was declared, `null` when `ci95` is,
and otherwise the requested `n`. Here the echo says declared and the absent `resample_draws` says
undeclared, beside a non-null `ci95`. `W-STATS-AGGREGATE-FAILED` fires, but its message says "the
recorded columns keep their clustered intervals" — true of the clustering, silent about the
construction the columns just lost.

The `report_by` level path has the same shape and **is** filed (spec-defects.md, "…and a report_by
asymmetry deferred beside it", owner H4 Statistics, amended after task 17 to re-check the disclosure
premise against real `run.yaml`). **The retry path is a second, unfiled site of the same class.**
Either close it (pass `resample_columns`/`strata`/`seed` on the retry, or drop the echo when the
column did not resample) or file it beside the level-path entry with the same owner. The comment must
stop claiming reproduction it does not perform either way.

### I2 — `_check_resample`'s docstring undercounts its checks and names the wrong sole roster reader

The docstring enumerates the function's checks as "`method` enum, its `n` floor, the comparison-family
lower bound on that same `n`, its `stratify_by` names, whether a roster was declared at all, and — **the
one check here that reads the roster** — `limits.min_clusters`". The inline comment above the
no-`return` gate repeats it: "The `limits.min_clusters` check further down is **the one exception** —
it DOES read `roster`".

Both are false. `E-STATS-RESAMPLE-STRATIFY-VARIES` (the `stratum_varies_within_cluster` composition
check, task 10) is a **second** roster-reading check, and the docstring's enumeration omits it
entirely — five checks listed for seven emission sites. No behaviour bug: that check carries its own
`roster is not None` guard. But this is precisely the two defect classes this branch names — a comment
claiming a guarantee the code does not provide, and a count phrase near an inserted row that nobody
re-read — surviving in the one function the brief singled out as historically carrying five of them.
The inline comment's own hedge ("not to promise every check below is roster-independent, which the next
reader must re-verify") mitigates the risk without making the sentence true.

### I3 — Two of the five deferrals are not durably filed with a live owner

The brief asks that each be "genuinely filed with an owner" and that its reasoning be "true today".
Three of the five are exemplary. Two are not:

**(a) The non-finite column values gap** (`spec-defects.md`, "A column resample is only ever defined
given finite inputs…") names its owner as "**whichever slice wires column resample into
`summarize_step` (task 12/14)**". That slice is H4a, and both tasks landed. The ledger records task 14
explicitly declining it ("the entry already named task 12/14 as the owner and this task explicitly
declines"), and `stats.py`'s docstring and `reference.md` were both correctly hedged to disclose the
gap. **But the defect entry itself was never amended.** Its named owner has shipped, so the durable
record now points at a closed slice — the entry is effectively ownerless, which is the failure mode
`spec-defects.md`'s own "a deferral must name a slice" ruling exists to prevent. It needs one line
naming a successor.

**(b) Contrast entries getting no resolved-values echo** is recorded **only in the ledger**, which
says it was "registered against H4's contrast-side hardening, same owner as task 16's filed items". It
was not: `spec-defects.md`'s task-16 entry ("The contrast path discloses nothing about its resample…")
covers the missing thin-pool warning and the missing zero-width sweep, and carries no amendment about
the echo. Confirmed empirically that the gap is real — a `vs_baseline` entry under a declared
`resample` carries `method: paired_percentile_over_units` and no `resample` block, while every
`aggregated` block beside it carries one. `progress.md` is now tracked, so the ruling is not lost, but
`CLAUDE.md` names `spec-defects.md` as the place to look "before filing a 'new' gap", and this one is
not there.

The other three verified sound: the `report_by` level's unresampled column (owner H4 Statistics,
premise re-checked and **amended** after task 17 changed what a level block discloses — the one
deferral whose premise went stale and was caught); the declared-`resample`-nulls-a-column-contrast
gap; and `paired_percentile_of_derived`'s missing zero-width sweep, whose non-regression argument I
reproduced directly.

---

## Minor

### M1 — "All three now refuse" is true of the stratified and clustered branches only

The refusals tasks 9/10/15 added fire on a per-stratum or per-cluster constant pool. An
**unstratified** constant pool still publishes a zero-width interval from `percentile_over_units` and
`percentile_of_derived`. Not a regression — `t_over_units` on the same column returns `Interval(5,5)`
too, so the design published a zero-width interval before H4a — and defensible, since an unstratified
bootstrap of a constant column genuinely has no sampling variance. Worth stating so the next reader
does not infer a general "core never publishes a zero-width percentile interval" guarantee: within one
run, a constant column is refused with `stratify_by` declared and published without it.

### M2 — "H4's contrast-side hardening" is a description, not a slice

Two filed deferrals name that as their owner. Compare the sibling entry, which names "H4 Statistics"
and cites the existing entry that already uses it. `spec-defects.md` has a prior ruling on exactly
this ("the ledger's deferrals fell back on descriptions of a slice… and none was"). H4b or H4c would
be the concrete names.

### M3 — `_check_resample`'s docstring carries a perishable build claim in the present tense

"Resampling itself had not been honored by `cli.command_run` as of that commit… Check
`cli.command_run`'s `derived_metric_draws` directly for whether that gap is still open." Honest,
dated to a commit, and self-invalidating by design — but it is now false as of two tasks later within
the same branch, and a reader hitting it in `validate.py` has to go and check. One sentence saying
tasks 13–15 closed it would retire the errand.

---

### M4 — "the one *built* block shown as a `null` with its shape in a comment" is now two

`reference.md` § The one config file's paragraph below the schema was edited by this branch —
"**Four** declarations above are not yet built" correctly became "**Three**", and a sentence was added
saying `statistics.resample` left that list. Two sentences later the same paragraph still reads:
"`data.units.measurements` is **the one** *built* block shown as a `null` with its shape in a comment
rather than expanded". `statistics.resample` is now built and is shown in exactly that form —
`resample: null` with `{method: bootstrap, n: 2000, stratify_by: []}` in the comment beside it. One
count in the paragraph was updated and the other, four lines away, was not: the count-phrase-near-an-
edited-row class, in the paragraph the edit landed in.

Adjudicated rather than assumed, because the sentence has an escape clause: its stated *reason* is
"because `init` materializes it as `null`", and `materialize.py` writes no `resample` key at all
(task 1 pins exactly this). So `measurements` does remain the one block `init` **materializes** as a
null. But the sentence's subject is what the schema **shows**, not what `init` writes, and on that
reading it is now false. The fix is a clause, not a rewrite.

## What I did not find

- No divergence in the undeclared-config record. This is the property the slice exists to preserve and
  it holds byte for byte over `aggregated`, `vs_baseline` and `correction`.
- No YAML aliasing anywhere in the record, in any of six shapes including the one that produced five
  aliases before the fix.
- No overstated payoff figure. The three circulating numbers are each stated with what they count.
- No change to `CLAUDE.md` § The worked example.
- No check I sampled that could not fail; the one cross-task mutation I ran was caught by two tests at
  two levels.
