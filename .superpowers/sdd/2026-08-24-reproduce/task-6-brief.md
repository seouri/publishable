## Task 6

**Ruling AA's two remaining questions, decided.** Q1 (the missing lockfile) and Q3 (`uv_lock: null`) —
design Decisions 5 and 6. This is a decision-and-documents task with one branch of code.

> **RULING AA** as restated in task 5. Q1 and Q3 are the two questions the spine's charter row said this
> slice exists to decide, and the scoping's § 3 named them.

**Q1: affirm `W-ENV-UNLOCKED`, do not promote it.** Re-measured 2026-08-24 and you must re-measure it
again yourself and report the output: `uv lock` inside a `publishable new` project fails — *"Because
publishable was not found in the package registry"* — so promoting the warning would refuse **every run
of every scaffolded project**. The constraint is a bootstrapping fact about this repository's publication
state, not a principle.

`docs/design-principles.md` § Design goals gains the footnote **the filing itself proposes**: *"not
optional" describes `reproduce`'s obligation, not `run`'s.* That sentence becomes true only because of
Q3's answer, so write them together.

**Q3: `uv_lock_hash: null` → `E-REPRODUCE-UNLOCKED`, exit `1`, after the clone, checkout kept**, closing
transcript printed with the `uv sync` line replaced by the stated gap. Exit `1` because nothing outside
the machine refused and `5`'s class is the one you retry. The checkout is kept because a stop that
discards its own artifacts is the fault H9b closed at exit `4` — H7d Part B's *a stop must be legible from
the artifacts*.

**The strongest available ground, and you must cite it rather than re-argue it:** `W-ENV-UNLOCKED`'s
shipped message already reads *"`reproduce` will not be able to restore it"*, and it is asserted in
`tests/test_cli.py`. Decision 6 is that sentence coming true. **Guard-pin arm F pins it and you may not
edit arm F.**

**`spec-defects.md`:** strike *Whether a missing `uv.lock` should refuse the run instead of warning is
unresolved* — the oldest H9-owned entry — with the decision and its date. **Leave the sibling entry open**
(*a scaffolded project cannot resolve a lockfile until `publishable` is published*): its retirement
condition is a release, not a slice. **Task 14 owns every other filing; this one is yours because the
decision and the filing are one act.**

**Fixture L**: asserts the code, exit `1`, **and that the destination exists and holds the checked-out
tree**. A refusal arm asserting only the code would pass identically if the checkout were discarded, which
is the behaviour this decision exists to specify.

**Mutation:** discard the checkout on `E-REPRODUCE-UNLOCKED` (Fixture L — the existence assertion is what
sees it).

**Must not touch:** `W-ENV-UNLOCKED`'s message or condition, guard-pin arm F, `reference.md` § Warnings
core reports.

---

