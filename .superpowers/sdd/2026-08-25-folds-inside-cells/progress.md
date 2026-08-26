# H3c-3 — folds and holdouts inside cells — the ledger

Branch `h3c3-folds-inside-cells`, off `main` at the H9d merge. **23 tasks in six batches. THE LAST SLICE
IN THE PROJECT** — which changed how everything in it had to be written: **every gap declined here ships**,
and *"routed to whichever slice next touches X"* resolves to a closed slice the moment anyone reads it.

Five controller rulings — **HH** (build it in full; the re-scoping's recommendation to ship the refusal
instead is recorded and overruled), **II** (the ordering constraint on the cross-arm leak), **JJ**
(`min_units_per_cell` must be *decided*, not declined), **KK** (`_resumed_allocation`'s safety argument
re-derived, not patched), **LL** (`fold_basis`' three questions named). Suite 3338 → **3417**.

**This ledger is written by the controller after the merge**, because no task owned it and the gate found
its absence — *the last slice of a family is where its own record goes missing*, which H9d had just
demonstrated and this slice then repeated. The rulings and their grounds live in the tracked design and
plan; the five batch reports carry the measurements.

## Ruling HH's own premise was false, and the correction is the entry that matters most

HH argued the slice must be built because *"two normative documents describe folds and holdouts inside
cells in the present tense"*, so shipping the refusal would mean a larger document change than building
it. **Correction C2 measured that all three sites are marked "not built"** — the documents and the code
already agreed, and *an unbuilt reader of an unbuilt surface is specification*, this project's own rule,
cited against the ruling that forgot it.

**The decision stood on three grounds that survive**: it is the work that was asked for and **scaling that
down is the requester's call**; **Ruling II's fix is correct code either way** — *a guard whose correctness
depends on a refusal nobody plans to keep is a defect with a delay on it*; and a refusal a design cannot
route around is worse than one it can. **A ruling whose premise is falsified is not thereby wrong — but it
has to say so**, and the correction is appended rather than the ruling rewritten.

## Ruling II — the worst defect this project could have shipped, and it was never open

Retiring `E-DATA-HOLDOUT-CELLS` **opens a cross-arm training leak that was already written**:
`runner.execute_plan` composed an **arm-narrowed test side** with a **roster-wide train side**, and one
assert — justified in its own comment by that very refusal — was all that held it back. The fold path
fifty lines below got it right.

**The invariant held, verified commit by commit rather than claimed**: at task 14 the assert is present; at
task 15 it is **gone and the train side is narrowed in the same commit**, via `_arm_keys` over **the train
side's own keys**. **No commit on the branch has the assert absent and the train side roster-wide.** And
the leak is **pinned end to end**: a real `groups × holdout` run through `main(["run", …])` whose *step*
reads `io.units.train`, which **fails alone** when the narrowing is reverted.

**The brief for that task was wrong in a way that would have shipped an empty train side** — it filtered by
`arm ∩ test`, disjoint from train — and only its own non-emptiness assertion surfaced it.

## The accepted-and-never-forwarded defect, twice in one slice

**Task 13's interrupted work added a `cells` parameter to `_resolved_holdout`, wrote the docstring
explaining that the split is drawn inside each cell, and wired the call site to `cells=None`.** Its own
fixture caught it — **only because that fixture asserts MEMBERSHIP rather than a per-arm count**: at
`frac: 0.2` over two arms of ten, a flat draw lands 2/2 by chance with probability **≈0.42**, so a count
assertion would have passed with the wiring dropped.

**And the gate found the same shape a second time**, at `validate._holdout_test_roster`: forwarded,
documented, **and pinned by nothing** — wiring it to `None` left the whole suite green. The fix round built
the discriminating fixture (per-cell test side in **2** clusters where flat spans **3**) and proved it
fails alone. **Four slices in a row have shipped a parameter nothing reads**, and the only thing that has
ever caught it is a fixture built to tell two readings apart.

## The bit-stability oracle, and what a gate is for

**336 no-cell cases** — folds and holdouts, four rosters × three digests × `k ∈ {2,3,5}` × clusters ×
strata, three holdout methods × two seeds — run under both HEAD and a **real `main` worktree**:
**byte-identical**, and proven able to fail (mutating the two reduction lines produced 13021 differing
lines). *That is the pin the whole slice rests on*, and it was measured against the other tree rather
than read off an arm.

**Two guard-pin arms fired, and both firings were the device working.** H9d's arm C went red because task
21 replaced a sentence that was **false against the code** — and the investigation it forced **retired
half of it**: a digest over a document whose job is to describe behaviour slices change is a proxy that
fails whenever the document does its job, while `design-principles.md`'s half stays, because for a file
that should not move a digest **is** the direct question. And a filing written in this slice **misdescribed
the code it filed** — `cells` does reach the `min_clusters` denominator — which made it a **disclosure of
something the slice moved**, not a gap someone else would close.

## What ships open, and it ships open on purpose

Every remaining `spec-defects.md` OPEN entry now says plainly that **no slice follows**. Three were filed
here: a cluster spanning two cells under `by_attribute`, which breaks the between-sides independence a
clustered Welch df assumes and would have needed a statistics-family refusal minted inside a partitions
slice on an argument nobody made; `limits.min_clusters`' denominator; and the per-stratum fold bound.
**`limits.min_reported_n` and `max_ineligible_fraction` ship unread.** *The reason each was declined stops
being a reason and becomes a fact* — which is the honest form of a project's last day.
