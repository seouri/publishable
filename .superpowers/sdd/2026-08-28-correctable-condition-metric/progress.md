# SDD ledger — plan: docs/superpowers/plans/2026-08-28-correctable-condition-metric.md

Spec: docs/superpowers/specs/2026-08-28-correctable-condition-metric-design.md (read; binding)
Scoping: docs/superpowers/G2-SCOPING.md (measured against b3d1d06, 2026-08-28)
Branch: **main**, by explicit instruction ("run it the way G1 went", and G1 ran on main).
Baseline at b5eb0ef: 3531 passed, 1 skipped, 2 xfailed.

Ruling: work proceeds directly on `main` with commit+push per task, as G1 did on the same
instruction. Costs if wrong: a bad task is reverted on a public branch rather than abandoned.

Ruling: `scripts/sdd-workspace` clobbers `.superpowers/sdd/.gitignore` to a bare `*`; restored from
a copy each run, and every record committed with `git add -f`. Costs if wrong: records untracked.

## Pre-flight scan

### Pair rows — every pair sharing a file or an interface

| Pair | Produces → consumes | Found |
|---|---|---|
| T2 → T4 → T5 | `percentile_of_derived` returns a pool → `summarize_step` carries it → `cli.py` builds the Member | Consistent, and strictly ordered. T5 cannot run before T4, T4 not before T2 |
| T3 → T4 → T5 | same chain for `percentile_over_units` (recorded columns) | Consistent. T3 and T2 both edit `stats.py` but different functions |
| T2, T3 | both edit `stats.py`; T2's functions return `(Interval, int)`, T3's returns `Interval \| None` | **Different return shapes, so different call-site edits.** T3 is the more invasive and its brief says so |
| T5 → T6 | `cli.py` builds the member → `hypotheses.py` narrows its branch | Consistent: the branch can only narrow once members exist |
| T1 → T7 | oracle captured → oracle re-checked | Consistent, and T1 must be first |
| T6, T7 | both touch `spec-defects.md` and the feasibility analysis | T6 amends the entry and the analysis' finding #2; T7 re-records § Executability. Sequential, no collision |

### Self-consistency rows — one per task

| Task | Its own text agrees with itself? |
|---|---|
| T1 | Yes — capture, assert, ship nothing else |
| T2 | Yes |
| T3 | Yes |
| T4 | Yes |
| T5 | Yes, after the Decision 1 correction the plan's preamble points at |
| T6 | Yes |
| T7 | Yes |

### Rulings from the scan

Ruling: **no batching.** Every task here feeds the next through a changed signature, so a batched
dispatch would review two shapes at once and lose the ordering the chain depends on. G1 batched two
pairs of prose-only tasks; this plan has none. Costs if wrong: seven review surfaces instead of five.

Ruling: **T1 ships alone and first, and its commit contains no production change.** The plan says a
pin captured with the change is a pin over the change; that only holds if T1 is its own commit.
Costs if wrong: the oracle proves nothing and the slice's central safety claim is unfounded.

## Progress
Task 1: implemented (commits b5eb0ef..3f6b5b6); review dispatched.

Ruling: **the brief's `b3d1d06` is stale by one docs-only commit and the oracle at `b5eb0ef` stands.**
The implementer flagged it. `b5eb0ef` is the Decision 1 correction — three files under
`docs/superpowers/`, no `src/` and no `tests/` change — so no input to a corrected bound moved
between the two. The scoping's baseline figure (3531 passed) was measured at `b3d1d06` and still
holds at `b5eb0ef`, which is the check that matters. Costs if wrong: the oracle pins a tree one
commit off the one the scoping measured, and any divergence would have to be in documentation.
Task 1: review — SPEC ✅, quality Approved with 1 Important + 2 Minor (commits b5eb0ef..3f6b5b6).
The reviewer independently mutated PRODUCTION code (`_level_for(..., rank)` → `rank + 1` in
`correction.py`), saw the oracle go red, and restored it green — so the pin is real. The Important
finding is that the REPORT's own evidence mutated the golden literal instead, which proves only that
the comparison reads that element.

Ruling: **the Important finding enters the fix loop even though the code is correct.** It is a claim
in a test docstring that outran what was measured, and the docstring's "or, symmetrically, in a
fresh record" reads as having been done when it was not. This repo's most expensive recurring defect
is exactly that shape, and the corrected evidence already exists — the reviewer produced it. Costs
if wrong: one round spent on a docstring while the code stands.

Task 1: minor (deferred): the two pre-assertions (`corrected` non-null, `max(family_sizes) > 1`) are
implied by the whole-list equality that follows; harmless, and useful as failure-message signal.
Task 1: minor (deferred): the hypothesis block's own `family_size` is 1, so its `ci95_corrected`
equals its raw `ci95` — that arm alone could not distinguish corrected from uncorrected. The
`vs_baseline` bounds do differ from raw, so the oracle as a whole is unaffected.
Task 1: noted, no action: a leaf walk cannot see an empty dict or list appear. No live consequence.
Task 1: fix round 1/5 (1 addressed; commits 3f6b5b6..5d69fb8). The implementer ran the production
mutation and rewrote the docstring to name it, deleting the untried "or, symmetrically" claim.

Ruling: **the implementer's own concern — that `rank + 1` crashes rather than miscomputing — is
answered, by me, and needs no further round.** A `ZeroDivisionError` proves the oracle notices *an*
error; it does not prove the oracle notices a WRONG BOUND, which is what the slice will risk. So I
mutated `_level_for`'s holm branch to `ALPHA / family_size` — a flat Bonferroni level, a perfectly
valid float, silently wrong under holm — and the oracle failed (`1 failed, 582 deselected`);
restored, `1 passed`. The pin catches a wrong number, not merely an exception. Recorded here rather
than sent back because the evidence is now in the ledger and the code needed nothing. Costs if
wrong: the strongest evidence for the oracle lives in the ledger rather than in the test's docstring.
Task 1: fix round 1/5 re-review — ADDRESSED, no new breakage. Round 2 dispatched to move the silent-miscomputation mutation from the ledger into the docstring, on the re-reviewer's judgment that it is the evidence this pin's purpose actually needs.
Task 1: fix round 2/5 (1 addressed; commits 5d69fb8..5661b90) — the flat-Bonferroni mutation is now
the docstring's primary evidence, attributed to the controller and not claimed as re-run.
Task 1: complete (commits b5eb0ef..5661b90, 2 fix rounds, review clean; suite 3532 passed, 1
skipped, 2 xfailed; ruff and mypy clean). THE ORACLE IS LIVE — every later task must keep it green,
and a task that reddens it has moved a bound the slice promised not to move.
Task 2: implemented (commits 1abc3df..98cd061) — reused the existing PairedResample dataclass; 21 call sites; oracle reported green. Review dispatched.
Task 2: review — SPEC ✅, quality Approved, 3 Minor (commits 1abc3df..98cd061). The reviewer verified
line by line that no arithmetic moved, that `pool=values` IS the list `interval_at` indexed, that
`PairedResample`'s three fields carry the same meaning here (not a near-fit), and that the Task 1
oracle is green with its golden literal untouched.

Ruling: **the stale `spec-defects.md` claim is fixed by me, now, rather than entering a fix round.**
Line ~3455 said in the PRESENT tense that `percentile_of_derived` returns `(Interval, int)`, which
task 2 made false. It is one sentence in a file the implementer was never pointed at, and this
slice's remaining tasks widen the same signature again — so a round spent on it would be re-opened
by task 3 anyway. I amended it to say the entry's premise is expiring under G2 and to re-read it
against the code. The sibling at line ~801 is a DATED past-tense account of what H4a did and is
correct as history; left alone. Costs if wrong: a controller edit skipped review, in a development
record rather than in code.

Task 2: minor (deferred): `assert got.pool == sorted(got.pool)` is implied by the `interval_at` call
in the same test, which asserts sortedness internally.
Task 2: minor (deferred): nothing pins the new `pool=sorted(values)` on the below-floor branch
(interval `None`, pool non-empty). Task 4 consumes it.
Task 2: minor (noted): `PairedResample`'s NAME now overreaches — it serves unpaired constructions
too. Renaming touches every paired call site; not worth a round mid-slice.
Task 2: the report under-counted call sites (21 claimed, 26 actual: 2 in `stats.py`, 24 in
`test_stats.py`). All updated, mypy clean, zero tuple-unpacks remain — a miscount in prose, not a
missed site.
Task 2: complete (commits 1abc3df..98cd061, review clean; suite 3534 passed, 1 skipped, 2 xfailed)
Task 3: implemented (commits 67cf737..e6a916f) — percentile_over_units and its clustered sibling return PairedResample; a pre-existing test pinning the 'stays bare' decision was rewritten, which the review is judging. Review dispatched.
Task 3: review — SPEC ✅, quality Issues: 1 Important, 1 Minor (commits 67cf737..e6a916f).

Ruling: **the rewritten test is ACCEPTED, on the reviewer's reading rather than the implementer's.**
The deleted `test_percentile_over_units_still_returns_a_bare_interval` did pin a deliberate decision
— but its stated reason was about refusing to CLAIM SURVIVORS ("a survivor filter would count a nan
draw as a survivor and report the same false claim with an extra field"), not about refusing a
wrapper. Task 3 keeps that refusal: `draws_used` is `len(means)` == the requested `draws` on every
success path, never a survivor count, and the new docstring restates decision 2 explicitly. The
reason still holds and is honoured. Costs if wrong: a prior slice's judgment was reversed on a
reading of its intent rather than its letter.

Task 3: minor (deferred): the new docstring says `draws_used` "is always the REQUESTED n", which is
false on the five refusal paths that return 0 — consistent with its siblings, but a guarantee the
code does not provide.
Task 3: fix round 1/5 (2 addressed, 0 open; commits e6a916f..b5346f9). The re-reviewer re-ran the
seed mutation itself and reproduced both reds; the diff is one docstring paragraph and two `.interval`
insertions, with `tests/test_cli.py` untouched and the oracle green.

Ruling: **on the refusal-path count, the IMPLEMENTER was right and the first reviewer was wrong.**
The round-1 finding said five; the corrected docstring says three. The re-reviewer counted the code:
`percentile_over_units` has exactly 3 `draws_used=0` returns (too few values, too few draws for the
confidence level, all-strata-constant), and its clustered sibling has 4 — no combination yields 5.
A plain miscount in a review, corrected here rather than propagated into the docstring, which is
what a fix round is for. Costs if wrong: a docstring undercounts a refusal path in one function.
Task 3: complete (commits 67cf737..b5346f9, 1 fix round, review clean; suite 3536 passed, 1 skipped, 2 xfailed; ruff and mypy clean)
Task 4: implemented (commits 24d9a9f..0eef18b) — the pool rides inside each metric block and is popped in cli.py before the block is written. One pop site. Review dispatched with the carrier choice as its first question.
Task 4: review — SPEC ❌ (1 constraint failed), 2 Important, 2 Minor (commits 24d9a9f..0eef18b).
The reviewer enumerated the four write paths itself, replaced the stratum pop with `pass`, found the
targeted suite STILL GREEN, then built the missing fixture (report_by + declared resample) and
watched the pool reach `run.yaml` at three paths. A real, reachable leak with no test guarding it.

Ruling: **the carrier shape is ACCEPTED as-is and not re-opened, and the ledger records why so the
next reviewer does not relitigate it.** Putting the pool inside the recorded dict makes the no-leak
guarantee procedural (two pop sites) rather than structural. The reviewer named a better option the
implementer did not consider — an out-parameter `pools_out: dict | None = None` that `summarize_step`
fills, which has zero call-site churn AND cannot leak by construction — so the implementer's stated
"~80 call sites" justification does not hold. I am keeping the shape anyway: tasks 5 and 6 are
already written against a carrier that exists, the leak is closable by a test rather than by a
redesign, and re-shaping the seam mid-slice costs more than the invariant it buys at this size.
**Costs if wrong: a future path that writes a metric block without popping leaks two thousand floats
into a run record, and only a test stands between.** If G2 gains an eighth task, converting to the
out-parameter is the first candidate.

Task 4: minor (deferred): `derived_pool = list(...)` copies while the column branch stores the pool
by reference. No live aliasing bug; the two branches should agree, and `Member.pool` is a tuple.
Task 4: noted: the Task 1 oracle is NOT an independent check of the leak — it reddens under the same
mutation, because a leaked pool changes the `run.yaml` it digests. Its independent value is over
arithmetic. For this invariant, one check twice.
Task 4: fix round 1/5 (3 addressed, 0 open; commits 0eef18b..8e57ec6). The re-reviewer re-ran the
stratum-pop mutation itself and reproduced the leak at the same path, verified the new arm pairs its
absence check with a must-be-present `resample_draws == 500`, and traced by-reference safety: each
pool is a freshly-constructed local list owned by one `PairedResample`, and nothing appends, sorts
or truncates it in place between construction and the pop.
Task 4: complete (commits 24d9a9f..8e57ec6, 1 fix round, review clean; suite 3538 passed, 1 skipped, 2 xfailed; ruff and mypy clean)
Task 5: implemented (commits c4ccf02..5570533) — all three correctable Decision 1 rows, row 4 left
without a member, plus a carve-out the design's table did not anticipate: a column under BOTH
`weight_by` and `cluster_by` (reachable with no comparison, so `E-DATA-WEIGHT-CLUSTER-CONTRAST`
never fires) has no paired counterpart construction, so it builds nothing rather than loosening
`Member.__post_init__`. Oracle reported byte-identical green. Review dispatched on opus with the
evidence pairing, the `diffs` repurposing, the carve-out and family-size stability as its four
first questions.
Task 5: review — SPEC ✅ on all four Decision 1 rows, quality Approved, 2 Important + 2 Minor
(commits c4ccf02..5570533). Verified by reading: the evidence pairing is percentile-beside-percentile
and t-beside-t at every branch; `grep '\.diffs\b'` over `src/` returns ONLY `correction.py`, and only
the guard's `len()` checks and the three `paired_*` calls — no Cohen's dz, no derived `n`, no sign
convention — so values-as-`diffs` is semantically inert and is now on the record as checked;
`corrected_fields` still takes `comparison_members` alone, so no family size moves; the oracle is
byte-identical green with its golden untouched.

Ruling: **the Holm re-ranking is REAL, is more correct than what it replaces, and must be disclosed
rather than fixed.** `corrected_for` assigns levels by `enumerate(rank_family(family))`, and a
counted constant hypothesis previously contributed no member — so its co-family hypotheses ranked
over a shorter list. Now it takes a rank and pushes some of them down, widening their levels and
NARROWING their corrected bounds. Design Decision 5 says "nothing else may move at all", which is
now false in this one named way. I am not reverting it: a counted hypothesis that ranks in its own
family is the correct Holm step-down, and the previous behaviour was the anomaly the slice exists to
remove. What it needs is a sentence in the record and a test, both of which land in Task 6/7 rather
than in a fix round here. **Costs if wrong: a run mixing a constant hypothesis with other counted
ones reports slightly narrower corrected bounds for the others than 0.2.0 did, and only the ledger
and the amended Decision 5 explain why.**

Task 5: carried to Task 6's dispatch (NOT just this ledger): the residual open case in the
`spec-defects.md` entry is WEIGHTED+CLUSTERED, not the `t` case — Task 5 closed the `t` case. The
Task 6 brief's "stays open for the `t` case" is stale and must not be copied forward.
Task 5: minor (deferred): `delta=summary_block.get("value") or 0.0` swallows a `None` into `0.0`,
feeding `_evidence_ratio` and the rank. Unreachable today (a block with `ci95` always has a numeric
`value`); `is None` would say what is meant.
Task 5: minor (deferred): `declaration_index` uniqueness across the two member lists is correct but
unpinned — no test separates `len(comparison_members) + i` from a colliding `i`.
Task 5: complete (commits c4ccf02..5570533, review clean, 0 fix rounds; suite 3543 passed, 1 skipped, 2 xfailed; ruff and mypy clean)
