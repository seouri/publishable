# Task 13 — controller additions

**Mint `E-DATA-ASSIGN-STRATIFY-FORWARD`.** *Stratification is forward-only* has **no code at all** —
pre-existing, confirmed at the fork point and in the scoping. Task 3 deliberately narrowed
`E-DATA-ASSIGN-STRATIFY-UNKNOWN` to **existence** so that order would be yours: one code answering to
two § Validation rows breaks that section's own promise that "a row here and a code there are the same
check seen from the two ends".

**This is a sequencing requirement, not a check** — that is the whole point and the thing most likely to
be got wrong. Axis 2's draw consumes axis 1's **realized** membership as its stratum column. Nothing
today establishes any per-axis draw order: `cli._resolved_group_axes` builds a dict in declaration order
**by accident of construction, not by contract**.

So the third test is the load-bearing one: **pin the draw order itself**, so a later refactor into an
unordered mapping fails here rather than silently reordering draws.

**The mutation that decides whether the feature is real:** reverse the draw order and confirm the
earlier-axis test fails. **If it passes, axis 2 is not consuming axis 1's membership and the feature is
decorative.**
