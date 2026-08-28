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
