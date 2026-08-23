## Task 2: the guard pin — six arms, captured before anything moves

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Runs before every code task. Surface: direct calls to `hashes.code_hash` for arms A, C, D and E; a real
`run` through `main` for arms A and B's `run_id` halves; `validate` through a `Collector` for arm F.**

**Three arms have no authorized editor at all, so a passing arm is itself the proof.** This device is the
answer to five slices weakening a pin quietly, and to the two that pinned one list twice and edited both.

**Files:** `tests/test_hashes.py` (add), `tests/test_cli.py` (add), `tests/test_validate.py` (add).

| Arm | The claim | Sole authorized editor | State specified in advance |
|---|---|---|---|
| **A** | The base tree — no excluded file under either tree — hashes to `sha256:71bf339cc9463f4c776c711f3d65ccf9b3bc1e18d383b78ae7d4e5170b526c2b`, and an end-to-end `run` over it produces a `run_id` ending `_71bf339` | **NONE** | unchanged, byte for byte |
| **B** | The base tree plus a git-excluded `src/pkg/.env` hashes to `sha256:ebc5ee53ac39bbab63d5270475271068dc67e6f34ead9db648bad114845b1cce` and its `run_id` ends `_ebc5ee5` | **task 5 only** | **exactly two literals move**, both written now: `ebc5ee53…` → `71bf339c…` and `_ebc5ee5` → `_71bf339` |
| **C** | The **other seven present figures** a record carries are unmoved for arm B's project, asserted as literals: `parameters_hash`, `input_manifest_hash`, the per-file digests in `manifest/input.json`, `uv_lock_hash`, `units_hash`, `allocation_hash`, `design_digest` | **NONE** | zero lines changed. This is the arm that makes *"exactly one hash moves"* a pin rather than a sentence |
| **D** | Fixtures D and E: a tracked `.pyd` matching `*.py[cod]` is hashed, and a tracked file inside `__pycache__` is not — both asserted on the **after** value `sha256:eec1541edde45c11c395e788000f719a48965a8f6fd2b3772a56de92cca18dc2`, which is also their today value | **NONE** | unchanged. A passing arm after task 5 **is** the proof; there is no editor who could make it pass another way |
| **E** | `tests/test_hashes.py`'s two negative controls still resolve `code_hash` of a nonexistent directory to `sha256:e3b0c442…` | **task 3 only** | task 3 adds the literal `None` argument to **13** call sites and changes **no assertion** |
| **F** | `W-TEMPLATE-VERSION`'s full message string, including its unset-and-defaulted clause | **task 11 only** | **zero characters change** |

- [ ] **Step 1: capture arm A. NO AUTHORIZED EDITOR.** Build the base tree in a `tmp_path` git repository
      and assert `code_hash(base) == "sha256:71bf339c…"` (the full 64 hex characters, written out). Then
      run the same tree end to end through `main(["run", …])` and assert the run directory's name ends
      `_71bf339`. **State in the docstring that a task which finds this arm failing has found the
      ordinary path moving, which this slice says it does not** — the response is to stop, not to edit
      the literal.
- [ ] **Step 2: capture arm B, with its two moving literals named IN THE DOCSTRING.** Same tree plus
      untracked `src/pkg/.env` = `OPENAI_API_KEY=sk-live-1\n`. Assert `ebc5ee53…` and a `run_id` ending
      `_ebc5ee5`. The docstring says: **task 5 is the sole editor, exactly two literals move, and they
      are `ebc5ee53…` → `71bf339c…` and `_ebc5ee5` → `_71bf339`. An edit to anything else in this arm is
      a finding.**
- [ ] **Step 3: capture arm C — the seven unmoved present figures, as literals. NO AUTHORIZED EDITOR.**
      Read them off arm B's real `run.yaml` and `manifest/input.json` and assert each. **Three of the ten
      figures § The value change enumerates are ABSENCES on this project** — `apparatus.hash` (no probe
      is declared under `generic`), the copied upstream `code_hash`/`parameters_hash` (no `io.reuse_from`
      here), and the derived seeds (never published as digests) — so they are **deliberately not in this
      arm**: *a control asserting only absences passes identically if nothing ran.* Say so in the
      docstring and name Fixture M as what covers the upstream pair.
      **Say explicitly that arm B carries NO copy of these seven figures.** The design puts them in arm B
      *and* arm C; this plan puts them in **C only**, so **no list is pinned twice** and task 5 — arm B's
      sole editor — has nothing of arm C's to edit. Two slices pinned one list twice and edited both;
      this is the answer to that, and it is stated rather than left as a silent shrinkage a reviewer
      diffing against the design would query.
- [ ] **Step 4: capture arm D. NO AUTHORIZED EDITOR.** Fixture D's tree and Fixture E's tree, both
      asserted at `eec1541e…`. **The docstring states the coincidence and why the arm is built on the
      after value**: the untracked-`.pyd` tree has the *same* today value, so an assertion on the today
      column would pass under a mutation that drops tracked files too.
- [ ] **Step 5: capture arm E.** Assert that `hashes.code_hash` of a directory that does not exist
      returns `sha256:e3b0c442…`, as a standalone claim, and name the two existing tests that depend on
      it as negative controls: `test_code_hash_skip_list_matches_relative_path_not_absolute` and
      `test_code_hash_handles_a_dot_git_intermediate_path_component`. **Task 3 is the sole editor and its
      only edit is adding `None` to 13 call sites.**
- [ ] **Step 6: capture arm F.** Assert `W-TEMPLATE-VERSION`'s **full message string** for a config that
      declares a moved `template_version` and omits `analysis.confidence`. The docstring states that
      **task 11 is the sole editor and zero characters change** — task 11 extracts a comprehension into a
      shared helper, and if the message moves, the extraction was not behaviour-preserving.
- [ ] **Step 7: grep before claiming.** Before writing *"no existing test asserts X"* for any arm, grep
      for it and **report what you grepped, not a count**. `run.yaml`'s top-level and `provenance` key
      lists are already asserted somewhere in the suite; find those assertions and say so rather than
      duplicating them. Six consecutive slices reported zero disagreements and all six were wrong, and
      every one hid in a claim about **other** tests.

**Delta:** +6 tests (one per arm; arms A and B each carry their direct-call and end-to-end halves in one
test).

**What this task must NOT touch.** Any file under `src/`. Any existing test. Any document.

---

