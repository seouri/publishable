## Task 8: `n` gains `clusters`

**Files:** Modify `src/publishable/runner.py`, `src/publishable/stats.py`, `src/publishable/cli.py`; Test `tests/test_runner.py`, `tests/test_cli.py`

§ The three-part `n`: each part is *"present only when it applies so a design that never skips reads as it always did"*. H3a built the route and this task follows it rather than inventing a second one: **a key that joins `n` travels in `summarize_step`'s `counts`; a key that sits beside `n` travels in `beside_n`.** `clusters` joins `n`, so it is `counts` work — the same slot `effective` took.

**The regression test is a run that declares no `cluster_by`** — write it first. Everything else is easy to get right while quietly breaking it, which is exactly how H3a's `effective` nearly shipped unconditional.

- [ ] **Step 1–6:** Failing tests (`clusters` present and exact; **absent** without `cluster_by`); implement across all three `n`-building sites in `runner.py`; mutate to make it unconditional and confirm the regression test fails; commit.

---

