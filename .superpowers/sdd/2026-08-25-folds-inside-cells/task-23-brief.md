## Task 23

**Corrections that bind this task: C11, C27.**

**An end-to-end `resume` over a `groups × fold` run with `method: random`** — the fixture § 6.2 of
the re-scoping says H9b could not build. The lever is **roster order** (C11): the second attempt must
resolve the same keys in a different sequence, which moves `units_hash`, hence `assign_seed_for`,
hence the fresh draw — while `_resumed_allocation`'s set-equality guards pass.

**The risk, stated in advance rather than discovered.** The cheapest lever, reordering the rows of
`index.csv` between attempts, may be blocked by the input-manifest gate, since the manifest covers
file contents. **Check that first.** If it is blocked, the end-to-end lever is a **plugin resolver**
whose returned order varies while it reads no file (so the manifest is unchanged), and if that also
fails, this task's end-to-end arm is **declined in writing** and task 17's direct-call fixture F5
stands as the proof — which it already is. **Do not report success on an arm that did not run.**

**Also run an end-to-end `resume` over a `groups × holdout` run** (a separate fixture, C27),
asserting the recorded holdout is honoured rather than redrawn.

**Must not touch:** `_resumed_allocation` (task 17 owns it); guard-pin arm C.

**Report must state:** which lever worked, measured, and — if the end-to-end arm was declined — that
it was, and that **there is no later slice** to take it up.
