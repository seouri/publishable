## Task 3

**Pointer: Ruling V binds this task (design Decision 1), and this task is the one that changes what a
shipped command writes. Read § Is this additive? — the disclosure too.**

**Ruling V, restated: `run` must make its identity claims durable BEFORE it executes, extending H8b's
pattern rather than inventing a second one — and copying WHERE those calls sit, not only what they
call.** H8b's `config.yaml` and `environment/repo_root.txt` are written **inside
`with RunLock(run_dir)`, before `sweep.yaml`**. Write `identity.json` in the same block, immediately
after `environment/repo_root.txt`, from `Prepared`'s own `ch`, `ph`, `lock_hash`, `config_path` and
`_execute_prepared`'s `draft` parameter. **Compute nothing a second time**: a second derivation is a
second answer.

`config_path` is recorded **relative to `repo_root`**, POSIX-separated. When
`config_path.resolve().relative_to(repo_root)` raises, record the absolute path and say so in a
comment — but note in your report whether any test can reach that branch, and if none can, say so
rather than claiming it is unreachable.

**Then add `"identity.json"` to `_DRY_RUN_FIXED_FILES`**, in the write order — after
`environment/repo_root.txt`. That tuple's own comment says every entry is answered by the structural
fact that decides it in `_execute_prepared`; `identity.json` is unconditional, like `config.yaml`, so
it needs no guard.

**You are the SOLE AUTHORIZED EDITOR of guard-pin arms B and D** (task 1 re-aimed them at you). Their
post-edit states are written in their own docstrings; **your diff must be exactly one appended entry
per arm with nothing reordered**, and your report must show that diff. You may edit nothing else in
`tests/test_cli.py`.

**Must not touch:** `provenance.py` — the dirty gate's pathspec does not move, and H6b Decision 12
declined widening it. Your diff must show `git_provenance` unchanged. No other arm. No `*.md`.

**Appended 2026-08-23, before dispatch — binding on this task.** **Task 9 rewires this same phase-6
block.** Your write must be **one statement**, placed immediately after
`environment/repo_root.txt`'s, that task 9 can guard without moving — otherwise task 9's diff will
contain your line and neither review can tell the two edits apart. Say in your report which single
line it is.

**Mutations:** write `identity.json` **outside** the lock (caught by arm B? **check in advance** — if
no arm can see the difference, say so and pin it by asserting the file exists at the moment the
apparatus run-start probe is called, which is inside the lock); omit `identity.json` from
`_DRY_RUN_FIXED_FILES` (caught by arm D and by the set-to-set comparison beside it, which are two
different assertions and both must be reported).

---

