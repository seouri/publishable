## Task 2: Documents, part B — the two rulings

**Files:** Modify `docs/reference.md`

Both are settled. Write them down **before any code**, because tasks 10 and 11 implement them.

- [ ] **Step 1: `blocked` beside a declared `cluster_by` is refused.** *Settled by the user.* § Where units come from makes `blocked` the one declaration reading roster order as data; § Clustered units says a cluster is drawn whole under `blocked`. **Block size counts units and a cluster is indivisible, so no block size honours both.** Amend § Clustered units' sentence — which currently says "With `method: random` or `blocked` a cluster is drawn as a whole" — so it claims only what will be true: `random` draws whole clusters, and `blocked` beside `cluster_by` is refused. Amend § Allocation's `blocked` paragraph the same way. Name the code task 11 mints.
- [ ] **Step 2: `block_size: auto` when `ratio: {}`.** *Settled by the controller.* `auto` is "twice the sum of `ratio`", and `{}` **is** equal allocation, so the implied ratio is 1 per level and its sum is the level count: `auto` is **twice the level count**. Say it in § Allocation rather than leaving it inferable — it is the value `init` writes and the one most designs carry.
- [ ] **Step 3: Mechanical pass over the edited passages, then commit.**

```bash
git commit -am "docs: settle blocked-beside-clusters and auto block size over an empty ratio"
```

---

