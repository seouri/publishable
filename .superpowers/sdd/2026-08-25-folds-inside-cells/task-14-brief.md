## Task 14

**Corrections that bind this task: C6, C7, C9, C22.**

Two things, both of which neither scoping names.

**(a) `validate._holdout_test_roster` gains the cells (C6).** It realizes the holdout through
`holdout_for` over the whole roster and feeds `limits.min_clusters`. Once task 13 draws per cell,
these are two answers to one declaration — the exact defect `holdout_for`'s purity exists to prevent.
It takes `_resolved_cells`' answer and loops the same way task 13 does, through **one shared helper**
so that `validate` and `run` cannot drift; the helper lives in `units.py` beside `holdout_for` and
both callers call it. **Grep for a helper that already exists before writing one.**

**(b) `E-DATA-HOLDOUT-EMPTY` is bounded by the smallest non-empty cell (C7).** `_check_holdout`'s
`holdout_sizes(len(roster), frac)` becomes `holdout_sizes(len(smallest non-empty cell), frac)` when
cells resolve, and the message names that cell. **Both of the code's rows move** — § Errors `validate`
reports and § Errors core raises — and **each is checked against its OWN table's scope sentence**.
This is a **widening of one code, not a new one**: the remedy is unchanged, and a second code would
give one remedy two names.

**Fixture F7:** 20 units split **18/2**, `frac: 0.2`. `holdout_sizes(20, 0.2) == (16, 4)` clears;
`holdout_sizes(2, 0.2) == (2, 0)` does not → `E-DATA-HOLDOUT-EMPTY` at `validate`, naming the 2-unit
cell. **Can-fail control:** the same 20 units split 10/10 validates clean.

**Mutation MU-13:** leave the bound at `len(roster)` — F7 must fail.

**Report must state:** the grep for every `E-DATA-HOLDOUT-EMPTY` site and each hit attributed, and
which table's scope sentence put each row where it is.

**Must not touch:** any other `_check_holdout` finding; the ten-finding enumeration in its docstring
must be **updated**, not left stale.

