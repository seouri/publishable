# H5a — write-side integrity and the reserved-column namespace — ledger

Scoping: `docs/superpowers/H5-SCOPING.md` (H5 measured at **19 tasks against a one-row charter**, split
9/10). Design: `docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md` (11 decisions, **plus
two appended controller rulings**). Plan: `docs/superpowers/plans/2026-08-21-artifacts-write-side.md`
(**13 tasks**, nine batches, **twelve corrections**).

Baseline at `219b0a0`: **2835 passed, 1 skipped, 2 xfailed.**

## The defect that gives H5 its priority, filed before the design

**`collapse_repeats` over six units each recording only `valid: True` returns `{}`** — zero units, not six
with a column dropped. On a real run that published `n_valid: {value: 0.0, ci95: [0.0, 0.0],
resample_draws: 2000}` at **exit 0 with no diagnostic.** I verified the mechanism myself by direct call.
**Filed at once rather than at slice end**, because a silently wrong published number is the one class that
cannot wait — and **the boundary was invented rather than inherited**: an existing filing reasoned that
*"whoever writes `aggregate` should inherit this reasoning"*, and `collapse_repeats` chose a **third**
option that entry describes nowhere. **It is H5b's.**

## Two rulings, and the second overturns the first

**H5a IS a behaviour change to `run`, and the design said so loudly against the scoping's own split
ground.** A design that had quietly inherited *"only H5b changes behaviour"* would have shipped four
stoppages under a sentence saying there were none. **Approved** on the distinction it drew — **H5a refuses
corrupting input; H5b changes what an existing key may contain** — with four requirements attached, of
which **Decision 6 is load-bearing**: coercing roster attributes at `resolve_units` exists to stop a
**completed** run becoming a `ContractError` inside `finalize` **after every execution is paid for.**

**Then the plan's correction 3 overturned my ground, and it was right.** I approved refusing a structural
or `bytes` cell because it *"converts silent corruption into a loud refusal"* — **measured true of `.csv`
and false of `.parquet`**, which round-trips a list and a `bytes` cell **intact**. And **`io.record`
already refuses both**, so `units.parquet` — the inference base this charter is about — **was never the
exposure**; everything Decision 5 would newly refuse is an arbitrary `io.write` artifact.

**Re-ruled: "a writer accepts what it can give back", applied per format — one rule, different answers.**
`.csv` refuses; **`.parquet` keeps its capability and gains a pin**, because a documented capability left
unpinned is this project's seventh recurring failure. Stoppage 1 shrinks to the `.csv` half and **the
count must not be carried forward.**

**I generalized from one format's measurement to both without measuring the second** — the
*answering from a proxy* move, sixth instance on this project, **made by the person enforcing the rule
against it.** The plan caught it by measuring what I asserted, which is what *the code outranks both*
exists to produce.

## The plan's sharpest correction stands independently

**Re-pointing three guards at `RESERVED_COLUMNS` would break a legally recorded `by` column** — `record`
refusing it, and the collapse and `finalize` **silently dropping** it from `units.parquet`. That is
**Decision 4 applied against Decision 3**, and exactly the hazard my first ruling named: the refusal
removes one **producer** of a `by` column, not the **possibility**. Task 5's pin on that column's survival
in both `record` branches is the enforcement.
