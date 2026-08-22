## Task 7: Ruling C written — no marker, `uv.lock` is the carrier — and the boundary pinned

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: documents, plus one pin over two hand-written records through the shipped `diff`.**

**Files:** `docs/reference.md`, `tests/test_diff.py` (add).

**The ruling, and it is not re-argued here.** Nothing is minted to mark which definition produced a
record's `code_hash`, and `run.yaml`'s `schema_version` is **not** bumped. `run_record.SCHEMA_VERSION`
is `"1.0"` and `lineage.read_record_file` **refuses** any other value, so bumping it would make
`io.reuse_from` refuse **every record already on disk** — strictly worse than an unmarked value change.
The carrier that already exists is `uv.lock`: core's own version is pinned there, which is precisely why
`code_hash` covers only the repo's two trees, and `provenance.environment.uv_lock_hash` is written by
`cli.py` and read by `diff.py`'s `uv.lock` row. This is the ruling H5b shipped under, on the same
carrier.

**Because nothing is minted, the disclosure obligation is HEAVIER, not lighter.** This task discharges
it in the documents; task 12 discharges it in `CLAUDE.md` and the ledger.

- [ ] **Step 1: enumerate, in § How the three are computed beside the four-case table, every hash whose
      value moves and every record field that carries it.** **Exactly one hash moves: `code_hash`.** The
      other ten figures a record carries are unmoved, and they are **enumerated rather than counted** so
      a reviewer can check them: `parameters_hash`, `input_manifest_hash`, the per-file `sha256`s in
      `manifest/input.json`, `uv_lock_hash`, `units_hash`, `allocation_hash`, `apparatus.hash`,
      `design_digest`, the copied upstream `parameters_hash`, and every derived seed. **Ruling B is what
      keeps that list at ten.**

| Field carrying the moved hash | Where |
|---|---|
| `code_hash` | `run.yaml`, top level (`run_record.py`) |
| `run_id` | `run.yaml`, and the run **directory's name** — `allocate_run_dir` uses `short(code_hash)`, the first 7 hex characters |
| `provenance.upstream[].code_hash` | `lineage.py`, **copied** from an upstream record, so one record can carry two definitions |
| the bundled copy of each of the above | `study add` copies a run's `run.yaml` into `runs/<name>/` verbatim |
| the `latest` pointer's target | `point_latest`, which names the run directory |

- [ ] **Step 2: state the consequence plainly, in the document, in the words a reader needs.**
      **Two runs of the same config over the same data at the same commit, on either side of this
      change, publish different `code_hash` values and different `run_id`s whenever the repo carries an
      excluded file under the two trees — which the scaffold's own `.gitignore` makes the common case.
      `diff` prints `code_hash DIFFERS` for identical code.** `report study.yaml` over a bundle spanning
      the boundary prints `W-STUDY-CODE-HASH-MISMATCH`, whose message names three candidate causes and
      **will still name three, none of which is a build boundary** — the row is not widened, because
      widening it would document a transient. The carrier is `uv.lock`, and the honest statement is
      H5b's: **the change is visible as a dependency change and is not visible as a hash-definition
      change.**
- [ ] **Step 3: state Ruling C's sharpest cost, which is this ruling's specifically.** A post-change run
      that consumes a pre-change upstream through `io.reuse_from` publishes **one record carrying two
      hash definitions** — its own under the new rule and `provenance.upstream[].code_hash` copied
      verbatim from the old one — **with nothing marking which is which.** Stated, not mitigated.
- [ ] **Step 4: build Fixture N, the pin the controller requires. Do NOT hand-write two records from
      scratch.** `tests/test_diff.py` already imports `run_a_project` from `tests/test_cli.py` and calls
      **`command_diff(run_a, run_b)`** directly on two run directories — that is this fixture's shape.
      Produce one real run, copy its directory, and edit the copy's `run.yaml` so the pair is identical
      in every field except `code_hash` — one `ebc5ee53…`, one `71bf339c…` — with each `run_id`'s suffix
      matching its own digest. Then call `command_diff` over the pair and assert the rendered output contains `code_hash` and `DIFFERS` on
      the same row and that the exit code is **0** (`diff` exits 0 on every comparison it renders, 1 only
      when an operand cannot be read). **The docstring says what the test is for in one sentence: this is
      what a reader sees across the H6a boundary for identical code, and it is the cost Ruling C accepts
      rather than a defect to fix.**
- [ ] **Step 5: the can-fail control.** A second pair of records identical in `code_hash` must print
      `identical` on that row. Without it the assertion passes on any render that happens to contain the
      word.
- [ ] **Step 6: mechanical pass** on every `reference.md` edit, as task 1's step 6 specifies.

**Delta:** +2 tests.

**What this task must NOT touch.** Any file under `src/`. `diff`'s code — **no `diff` code changes in
this slice**. `W-STUDY-CODE-HASH-MISMATCH`'s three candidate causes. The `uv.lock` row's detail lines,
which are **H9's** and are re-affirmed as H9's in writing by design Decision 12.

**Guard-pin arms this task may edit: NONE.**

---

