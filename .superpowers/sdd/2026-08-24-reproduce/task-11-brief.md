## Task 11

**Dispatch.** `reproduce` joins `OPERATION_COMMANDS` and leaves `NOT_BUILT_COMMANDS`. **Guard-pin arm B's
sole authorized editor is this task.**

```python
OPERATION_COMMANDS = {"validate", "dry-run", "run", "draft", "resume", "reproduce", "freeze", "report"}
```

and `"reproduce": command_reproduce` in `handlers`, function-local-imported the way `command_freeze` and
`command_report` are.

**Arm B's edit, to the design's advance spec and no further:** the shipped
`assert ("reproduce", "NOT BUILT") in tables["Command"]` becomes `("reproduce", "built")`, **and** a new
line `assert ("list-templates", "NOT BUILT") in tables["Command"]` is added. Correction 20: that line is a
**marked row-presence probe**, so flipping it without adding another deletes coverage the comment beside it
names. The `set(NOT_BUILT_COMMANDS)` equalities are **self-maintaining and must not be edited**.

**Four arity tests, as additions** (correction 17) — no path, two paths, a flag, and `reproduce new`.
The flag test is the arm the `len` half alone cannot cover. `reproduce new` is **disclosure item 5** and
must be **pinned, not only disclosed**: `new` is a single token, so the arity arm is never reached and the
two-token `NOT_BUILT_COMMANDS` lookup never happens, so the call dispatches with `new` as its path and
prints `E-IO-FAILED` at exit **1** — **exit `2` → `1`, and the identifier is new.** H9a got the analogous
`draft new` claim wrong three ways and H9b then measured its own; **measure all four shapes through the
real console script, outside this repository, and correct the disclosure if any differs.**

**Do not rest anything on `_dispatch`'s branch order** (correction 18): the built branches precede the
`NOT_BUILT_COMMANDS` lookups, and that order is **filed as unpinned** — hoisting the lookups leaves the
suite green. Assert the outcome (the code and the identifier), not the order.

**Guard-pin arm E becomes meaningful here.** It was captured in task 1 against the `NOT BUILT`
invocation; re-run it against the dispatching command and report that ADDED/REMOVED/CHANGED are still
empty over all three trees. **You may not edit arm E** — if it fails, that is a finding.

**Must not touch:** `NOT_BUILT_COMMANDS`'s other three entries, the `set(...)` equalities, any other arm.

---

