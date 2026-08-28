# G2 — a correctable member for a condition's own metric: design

Written against [`G2-SCOPING.md`](../G2-SCOPING.md), which measured `main` at `b3d1d06` on
2026-08-28 and found the blocker to be one discarded value. **Read the scoping first**; this file
decides.

---

## Decision 1 — a member carries whatever evidence its OWN raw interval was built from

**CORRECTED 2026-08-28, before any task ran.** The first version of this decision said a member is
built *only* under a declared `statistics.resample`, and refused every `t`-interval case for want of
a pool. That was wrong, and it was wrong because it reasoned from `Member.pool` alone instead of
reading `_corrected_bounds`. What the code actually says (`correction.py:349`): **"What decides the
construction is which field the member carries, not what kind of metric it is."** A member carrying
`diffs` re-runs a `t` construction at the smaller α; a member carrying a pool reads a second rank
pair off it. Both are exact. There was never one privileged form of evidence.

So the rule is the one core already states, applied one surface over:

| A condition's metric | Raw interval | Member carries | Correctable? |
|---|---|---|---|
| Recorded column, no `resample` | `t_over_units` over the per-unit values | those values | **yes** |
| Recorded column, declared `resample` | percentile off a pool | the pool | **yes** |
| Derived (`aggregate`), declared `resample` | percentile off a pool | the pool | **yes** |
| Derived, no `resample` | **none at all** — `derived_interval` is `None` | nothing | no, and nothing to correct |

The fourth row is not a refusal this slice makes. A derived metric with no declared resample has no
raw interval either, so there is no bound to correct and `evaluate_on: ci95_lower` was already
answerable by nothing. The honest `corrected_unavailable` stays exactly there and nowhere else.

**What the first version got right, and keeps:** the corrected bound must rest on the *same*
evidence as the raw one. `cli.py:1644` records that defect being caught once in a column contrast —
a `ci95` from a percentile beside a `ci95_corrected` from a `t`, where *"Nothing raises and no reader
can tell."* That hazard is real; the mistake was concluding it forbids the `t` case rather than
requiring each case to carry its own evidence.

**Why this matters beyond tidiness.** Under the first version, E2 — the live config that prompted the
slice — would have been *fixed by accident*: it declares `statistics.resample`, so it lands in row 3.
A recorded-column metric with no resample would have kept failing, and the filing would have been
amended to claim a closure narrower than the one shipped. The slice would have worked and the
document would have been wrong about why.

---

## Decision 2 — the three constructions return their pool; nothing else about them moves

`percentile_of_derived`, `percentile_of_derived_clustered` and `percentile_over_units` each gain the
pool in their return. **No arithmetic changes**, no seed changes, no draw count changes, and every
existing caller keeps the value it already reads.

**Returned rather than recomputed at the member site**, and the reason is Decision 1's hazard read
from the other end: a second call with the same seed *ought* to give the same pool, and a slice that
relied on "ought" would be asserting reproducibility rather than using it. Handing back the pool the
interval was actually read off makes the raw and corrected bounds the same evidence *by
construction* rather than by argument.

**The clustered form returns a cluster-drawn pool**, which is correct without special handling: a
cluster bootstrap's pool is a pool, and the corrected bound must rest on the same draws as the raw
one whatever the draw unit was.

---

## Decision 3 — `summarize_step` carries the pool, and it does NOT reach `run.yaml`

The pool travels from `stats.py` to `cli.py` through `summarize_step`'s return, alongside the
interval it belongs to. It stops there.

**`Member`'s own docstring states the invariant this preserves**: `pool`, `diffs` and `sides`
*"may not reach `run.yaml`: they are tuples ... so a member cannot be mutated into the record by
accident."* Two thousand floats per metric per condition in a run record would be a record nobody
reads, in a file whose whole value is that a person can.

---

## Decision 4 — `hypotheses.py` narrows its branch and keeps its three states

The `corrected_unavailable` branch stays; what changes is when it fires. Today it fires for every
counted hypothesis with no member. After this slice it fires for one whose metric **has no raw
interval to correct** — Decision 1's fourth row, a derived metric with no declared resample, where
`evaluate_on: ci95_lower` was already answerable by nothing.

**The three states of `supported` do not change**, and neither does the rule that correction reaches
a verdict only through a bound. A hypothesis on `observed` is unaffected in every case, as it is
today.

---

## Decision 5 — the bit-stability oracle is captured first, and it is the whole-run record

Before any code moves, a completed run's `run.yaml` is stored — corrected bounds, family sizes,
levels and all. Every one of those must be byte-identical afterwards for a design that declares no
constant-referenced hypothesis, because such a run's members are exactly the members it has today.

**Captured first because a pin taken after the change is a pin over the change**, which this
project's record already names as a defect it has shipped.

**What may move**: a run that *does* declare `compare: {to: constant}` under a declared resample
gains a `ci95_corrected` where it had `null`, and its verdict may move from `supported: null` to
`true` or `false`. That is the slice working. Nothing else may move at all.

**AMENDED 2026-08-28 (Task 6): one more thing may move, and it is kept.** `correction.corrected_for`
assigns Holm levels by `enumerate(rank_family(family))`. A counted constant hypothesis used to
contribute no member, so every co-family hypothesis ranked over a shorter list than the one
`family_size` actually counted. Task 5's member changes that: the constant hypothesis now takes a
rank in `rank_family`'s own list, which can push a co-family member down a place — widening its Holm
level and, because a wider level is a narrower α-adjustment, narrowing its own corrected bound. This
is Holm step-down done more correctly, not a second effect layered on top of it: the family always
had this member in it (`family_size` already counted it, per Decision 2), and only its *rank*, not
its membership, was missing an entry to sort. It is a deliberately kept exception to "nothing else
may move at all" above, named rather than left for the next reader to discover as a silent
contradiction — the design's Decision 5 promise holds for a run declaring no constant-referenced
hypothesis; where one exists and correction is real, its co-family members' Holm levels and corrected
bounds may move too.

---

## What this design refuses

- **No evidence borrowed from a different construction.** A member carries what its own raw
  interval was built from, and never a pool synthesised to stand in for per-unit values or the
  reverse. Decision 1.
- **No change to `_is_counted` or `family_shape`.** The hypothesis is already in the family; this
  makes it correctable, not counted.
- **No pool in the record.** Decision 3.
- **The cross-run correction family stays open**, and this slice must not be read as narrowing it.
