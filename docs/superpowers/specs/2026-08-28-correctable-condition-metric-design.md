# G2 — a correctable member for a condition's own metric: design

Written against [`G2-SCOPING.md`](../G2-SCOPING.md), which measured `main` at `b3d1d06` on
2026-08-28 and found the blocker to be one discarded value. **Read the scoping first**; this file
decides.

---

## Decision 1 — a member is built ONLY under a declared `statistics.resample`

**The pool is the evidence, and where there is no pool there is no member.**

A condition's own derived metric has two possible intervals. Under a declared
`statistics.resample` it is a percentile read off a pool of draws — that pool is exactly what
`Member.pool` is documented to hold, *"already sorted ascending"*, and rebuilding a bound at a
corrected level is reading different ranks off the same pool. Under no declared resample it is a
`t` interval over the unit table, computed from a mean and a standard error, with no pool anywhere.

So the rule is: **a declared resample earns a member; nothing else does.** A `t`-interval metric
keeps today's `corrected_unavailable` and its honest `supported: null`.

**Refused, and recorded: synthesising a pool for the `t` case.** Core could draw one — it has the
unit table — but that pool would not be the evidence the *raw* interval came from, and the run would
publish a `ci95` from a `t` construction beside a `ci95_corrected` from a percentile one. `cli.py`'s
own comment records that exact defect being caught once, in a column contrast: *"Nothing raises and
no reader can tell."* Reproducing it deliberately, one surface over, would be the worse half of this
slice.

**What a reader gets is therefore two states rather than one**, and both are honest: declare a
resample and a constant-referenced bound test is answerable; declare none and it comes back `null`
with the same disclosure it has today. That is a narrower fix than the filing asked for, and the
narrowing is the point.

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
counted hypothesis with no member. After this slice it fires for one with no member *and no pool to
have built one from* — the `t`-interval case Decision 1 leaves alone.

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

---

## What this design refuses

- **No synthesised pool for a `t` interval.** Decision 1.
- **No change to `_is_counted` or `family_shape`.** The hypothesis is already in the family; this
  makes it correctable, not counted.
- **No pool in the record.** Decision 3.
- **The cross-run correction family stays open**, and this slice must not be read as narrowing it.
