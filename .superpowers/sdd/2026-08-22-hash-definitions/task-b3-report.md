# H6a batch 3 — tasks 5 and 6 — the value change

Commits `9685ae0` (task 5) and `c98b24e` (task 6). Suite **2945 → 2951 passed**, 1 skipped,
2 xfailed. `ruff check`, `ruff format --check`, `mypy` all clean.

**After this batch `code_hash` computes a different digest for an unchanged tree.** A file
under `src/**` or `templates/**` that git excludes is no longer read, so a repo carrying the
scaffold's own `.env`, `.venv/` or `*.py[cod]` files publishes a different `code_hash` and a
different `run_id` than it did yesterday for byte-identical code.

## The disclosure — every hash whose value moves, and what it moves from

`schema_version` is **not** bumped (bumping makes `lineage.read_record_file` refuse every
record on disk), so **`uv.lock` is the carrier** and the obligation lands here and on the
record.

| Figure | Moves? | From → to, on the trees this batch measured |
|---|---|---|
| `code_hash` | **yes**, whenever an excluded file sits under the two trees | base tree + `src/pkg/.env`: `ebc5ee53…` → `71bf339c…`; the runnable pin project + `.env`: `a74f3d44…` → `f6a935cf…`; the probe project + three excluded files: `09a843b1…` → `f6a935cf…`; base tree + untracked `loose.pyd`: `eec1541e…` → `71bf339c…`; Fixture C's tree: `1947d2a2…` → `71bf339c…` |
| `run_id` | **yes**, it carries `short(code_hash)` | `…_a74f3d4` → `…_f6a935c`; the probe's would have been `…_09a843b` and is `…_f6a935c` |
| `parameters_hash` | no | Decision 9 / Ruling B: no code changed |
| `design_digest`, `input_manifest_hash`, `units_hash`, `allocation_hash`, `uv_lock_hash`, `apparatus.hash`, every derived seed | no | guard-pin arm C, unedited and green |
| a tree with **no** excluded file under either hashed tree | no | arm A, unedited and green — `71bf339c…` and `f6a935cf…` before and after |

**A `diff` across this boundary prints `code_hash DIFFERS` for identical code.** That claim is
arm N's (`tests/test_diff.py`, no authorized editor); it was **not touched and it passes** —
verified by running the full suite, not by reading the file.

**The five carriers of the moved hash (§ Corrections 12), pinned or derived:**

* `run.yaml`'s own `code_hash` — **pinned**, arm B and Fixture C's end-to-end test.
* `run_id` and the run directory's name — **pinned**, arm B's suffix literal.
* `provenance.upstream[].code_hash` — **pinned**, Fixture M, and it is the copied *upstream*
  value, which does **not** move: `lineage.py` copies the string a prior record holds.
* the bundled copy in a `study` — **derived**: `study add` copies a run's `run.yaml`
  verbatim, so the record's own pin covers it.
* the `latest` pointer — **derived**: `point_latest` names the run **directory**, so the
  `run_id` arm covers it. Also **observed** in the console-script probe below, where
  `results/latest` resolves to `run_2026-08-23T00-37-18Z_f6a935c`.

## Task 5 — the wiring

`cli.command_run`'s hashing site is now

```python
def _include(candidates: list[str]) -> set[str]:
    return unignored_under_hashed_trees(repo_root, candidates)

hashed = hashed_files(repo_root, _include)
ch = code_hash_of(hashed)
```

built and called at **phase 5**, where the hash is taken — not at the phase-3 dirty gate.
`cli.py` gained `code_hash_of`/`hashed_files` from `publishable.hashes` and
`unignored_under_hashed_trees` from `publishable.provenance`; `code_hash` is no longer
imported there, because it has no caller left in `src/`. The site did not move: it still sits
after unit resolution and before `allocate_run_dir`.

**`hashes.code_hash`'s docstring claim, ruled task 5's by batch 2's review, is closed by
deletion rather than rewriting.** *"Read from the working tree, not from git"* became false
the moment `command_run` passed a git-backed predicate. What replaced it says what is still
true — contents are read from the working tree — and points at `hashed_files` and
§ How the three are computed for **which** files, rather than restating the rule.

### Arm B — the four literals in their post-edit state, and the one edit they entailed

| What | Before | After |
|---|---|---|
| `_H6A_BASE_WITH_ENV_DIGEST` | `sha256:ebc5ee53ac39…` | `sha256:71bf339cc946…` |
| `_H6A_RUN_WITH_ENV_DIGEST` | `sha256:a74f3d44dc1d…` | `sha256:f6a935cfc291…` |
| the run directory suffix | `_a74f3d4` | `_f6a935c` |
| the recorded `code_hash` | — | the same constant as the second, unedited |

**Both constant NAMES survive and only their values changed.** That is what arm C's own
docstring promised — it reads `_H6A_RUN_WITH_ENV_DIGEST` by name — and arm C therefore passes
with **zero lines of it changing**. Swapping arm B's assertion to reference `_H6A_BASE_DIGEST`
instead would have broken that promise; grepped before editing:
`grep -rn "_H6A_BASE_WITH_ENV_DIGEST\|_H6A_RUN_WITH_ENV_DIGEST" tests/` names arm B, arm C and
nothing else. `tests/test_diff.py`'s `_H6A_OLD_DEFINITION_HASH` is arm N's own separate
literal, over hand-written records, and is untouched.

**One edit beyond the four, entailed by them and disclosed rather than absorbed.** Arm B's two
direct halves called `code_hash(tree, None)`, and `None` bypasses `include` entirely: with it,
literals 1 and 2 **cannot** move at all, and the assertion would be a claim about *hash every
file these trees hold* — true on both sides of this slice and therefore not a pin of anything
it changed. Both halves now take `_h6a_live_include`, a new helper that builds `command_run`'s
own predicate. Arm B's docstring records this; the stale sentence *"Task 3's touch is the same
mechanical `None` as arm A's"* was **deleted**, not rewritten. Arm A keeps `None` and passes
unchanged, because its tree has nothing excluded and the two predicates agree there.

### No arm without an editor needed to move

Arms A, C, D, E, F and N were **not opened and not edited**; all pass. The proof is the full
suite, run after the batch: had any of them needed to move, it would be failing rather than
reported.

### The disagreements with the brief

1. **Fixture C, D and M cannot be run end to end over the plan's base tree.** `templates/t.py`
   holding `b = 2` is discovered as a project-local template and `validate` refuses with
   `E-TEMPLATE-LOAD` — the same disagreement batch 1 recorded for arms A and B, and any file
   that makes the tree runnable changes the digest. So step 4's *"assert `1947d2a2…` is not
   what the run records"* and step 9's *"the new record's own `code_hash` is `71bf339c…`"* are
   unreachable as written. What shipped instead: the **direct** half over the plan's tree with
   the plan's literals (`tests/test_hashes.py`), and the **end-to-end** half over a runnable
   project of task 5's own whose hashed trees hold exactly `src/pkg/step.py`, digest
   `f6a935cf…` computed by building it. `_h6a_t5_project` is deliberately a second builder
   rather than a use of the pin's `_h6a_pin_project`: that helper is shared by three arms, two
   with no editor, and these fixtures need their own experiment source.
2. **A resolver that writes into `src/**` on its FIRST call cannot be the mutation-7 fixture.**
   `command_run` validates first and `validate` dispatches the resolver too, so the write lands
   *before* the dirty gate and the run refuses with `E-CODE-DIRTY` — measured, it is what the
   first version of the fixture did. The shipped resolver counts its calls in a file outside
   the repository and writes `src/pkg/generated.py` from the **second** call on, which is the
   window the mutation is about. The test asserts the counter reached 2, so the window is a
   measurement rather than a story.
3. **Task 6's delta is +1 −1, not +2 −1.** Fixture J is one new test; the twin's removal is
   one; the tracked arm went **into the survivor**, as the brief's own step 2 required, rather
   than becoming a second test. Suite total is unaffected either way.

## The end-to-end evidence, through the installed console script

`/Users/joon/src/tries/publishable/.venv/bin/publishable run configs/t5/config.yaml`, over a
committed project holding `src/pkg/step.py` plus three untracked excluded files
(`src/pkg/.env`, `src/.venv/lib/site.py`, `src/pkg/loose.pyd`), exit **0**, read key by key
out of the written `run.yaml`:

```
top-level keys : schema_version run_id status draft config parameters_hash code_hash
                 provenance layout execution results
schema_version : 1.0                     (unchanged — Ruling C: no bump, no marker)
run_id         : run_2026-08-23T00-37-18Z_f6a935c
status         : completed
draft          : False
parameters_hash: sha256:a1718a2974…      (Ruling B: not normalized, not moved)
code_hash      : sha256:f6a935cfc291…
provenance     : git environment apparatus input_manifest input_manifest_hash
                 input_manifest_changed publishable_version plugin_versions units
                 units_hash allocation allocation_hash upstream
upstream       : []
results/latest → run_2026-08-23T00-37-18Z_f6a935c
```

The same tree under the **pre-slice** definition (`code_hash(root, None)`) is
`sha256:09a843b15e23…`, so that run would have been `run_…_09a843b` yesterday. The files
actually hashed are exactly `['src/pkg/step.py']`. This is the probe; the pins are the tests
below it.

## Mutations — every one against the FULL, unfiltered suite, with the count read

| # | Mutation | Failures **read** | Which |
|---|---|---|---|
| 2 | `hashed_files` computes `include` and ignores it | **8** | arm B, arm C, Fixture C (both halves), Fixture D/D′, Fixture J, `test_code_hash_delegates_to_code_hash_of_over_hashed_files`, Fixture F |
| 4 | `check-ignore --no-index` | **3** | Fixture D (`eec1541e…` → `71bf339c…`), task 6's survivor, Fixture I |
| 5 | ask git **before** the fixed skip set | **1** | task 6's survivor — and only it, which is the catch the plan assigned to task 6 |
| 7 | evaluate the predicate at phase 3, reuse at phase 5 | **1** | the resolver fixture; the digest differed by one file |
| P2 | `hashed_files(...)` then `code_hash(repo_root, _include)` — the naive shape | **1** | the count pin, reading `2` `check-ignore` invocations |
| task 6 step 3 | `__pycache__` out of `_SKIP_DIRS` | **2** | task 6's survivor and guard-pin arm D |

**A property-preserving arm of each leaves the suite green**, checked in advance rather than
asserted: for 2, applying `include` by any other equivalent expression; for 4, any flag that
does not change git's answer (`-z` stays); for 5, moving the skip set's *test* while still
applying it before git is asked; for 7, constructing the closure early and **calling** it late
(this one matters — building `_include` at phase 3 is a no-op, since the subprocess fires on
call, and a mutation that only moved the `def` would have been blind); for P2, folding the same
one list by any route; for step 3, reordering `_SKIP_DIRS`' members.

**Each mutation was checked against the body of the test it names before it was run.** Every
revert was done by **editing the file back**, `diff`-ed against a pre-mutation copy
(`REVERT-IDENTICAL` each time), `__pycache__` cleared, and re-run.

## The tests

`tests/test_cli.py` (+4): Fixture C end to end; the phase-5 predicate against a resolver that
writes into `src/**` during resolution; the one-`check-ignore`-per-run count; Fixture M.
`tests/test_hashes.py` (+2 for task 5): Fixture C direct, both branches; Fixtures D and D′.
`tests/test_hashes.py` (+1 −1 for task 6): Fixture J; the survivor's tracked arm; the twin
removed.

**The removed test, by its full name: `test_code_hash_ignores_pycache`** (`tests/test_hashes.py`).
It was byte-identical in body to `test_code_hash_still_skips_a_genuine_pycache_dir_inside_the_tree`.
`grep -rn "test_code_hash_ignores_pycache" tests/ src/ docs/reference.md docs/design-principles.md
docs/experimental-designs.md README.md CLAUDE.md` → one hit, the survivor's own docstring naming
what it absorbed.

**Fixture M's top-level key set is asserted as a literal**, eleven keys, so a future slice that
mints a marker fails there and has to come back and read Ruling C. Its upstream is genuinely
produced by `_build_fixture_f_upstream` with only `code_hash` rewritten in place; `run_id` is
deliberately left carrying the digest the upstream really computed, stated in the docstring
rather than quietly inconsistent.

## Existing tests whose expectation moved

**Exactly one: guard-pin arm B**, `test_h6a_arm_b_an_excluded_env_file_moves_the_hash_today`.
It is a **correct move, not a weakened pin**: the arm was captured with its post-edit state
written out in advance, task 5 is its named sole editor, the four literals moved to exactly the
values the docstring specified, and the fifth edit is disclosed above with the argument that
literals 1 and 2 are unreachable without it. Nothing was deleted from the arm except a sentence
that had become false, and no assertion was removed.

**No other test moved.** That is measured, not claimed: the full suite went 2945 → 2951 with
zero failures, so every other pin — arms A, C, D, E, F, N included — holds unedited.

## Claims about other tests and other code, and what was grepped for each

* *"arm C reads arm B's constant by name"* — `grep -rn "_H6A_BASE_WITH_ENV_DIGEST\|_H6A_RUN_WITH_ENV_DIGEST" tests/`
  → arm B's definitions and arm C's single reference; nothing else.
* *"the removed twin was byte-identical in body"* — both bodies read side by side before the
  removal: same file written, same `.pyc` written, same assertion.
* *"arm D calls `code_hash(..., None)`, so git is never asked there"* —
  `grep -n "code_hash(e_tree, None)\|code_hash(d_tree, None)" tests/test_hashes.py` → both hits.
* *"`_build_fixture_f_upstream` reads its step name back out of its own `run.yaml`"* — read.
* *"`code_hash` has one production call site"* — `grep -rn "code_hash(" src/publishable/*.py`
  → the definition in `hashes.py` and nothing in `cli.py` any more.
* *"no live reference to the removed test"* — the grep above, over `tests/`, `src/`, the four
  documents and `CLAUDE.md`.
* *"`E-CODE-FILE-LIST` has one emit site"* — `grep -rn "E-CODE-FILE-LIST" src/ tests/ docs/*.md`
  → one `raise` in `provenance.py`, its assertions in `tests/test_provenance.py`, **no § Errors
  row**. The row is task 8's by plan (Batching, item ii), unchanged by this batch — but note
  that **`run` is now a live surface for that code**: a submodule under `src/**` refuses at
  `run` from today, where before this batch nothing in `src/` reached the helper with a real
  predicate. Task 8's row must cover that, and it already names `run` as the command.
* **The two-case sweep.** The rule with more than two cases here is *which files are hashed*.
  It is enumerated **once**, in `reference.md` § How the three are computed (task 1's table);
  every site this batch wrote links to it rather than restating — `cli.py`'s comment,
  `hashes.code_hash`'s docstring. Swept newline-insensitively with a regex over the four
  documents, `hashes.py`, `provenance.py`, `cli.py`, `tests/test_hashes.py` and
  `tests/test_provenance.py` for any sentence combining *hash* with *exclude/ignore*: the only
  enumerations found are the § How the three are computed table, its links, and Fixture J's
  docstring, which states the **four** gate/hash states task 6's step 1 asked for. No two-case
  version.

## Concerns for the reviewer

1. **The entailed fifth edit to arm B** is the thing to check first. It is disclosed, argued and
   confined to the second argument of two direct calls; a reviewer who disagrees can ask whether
   arm B should instead have kept `None` and left literals 1 and 2 unmoved — that reading makes
   the arm's own advance specification unsatisfiable, which is why it was not taken.
2. **`_h6a_t5_project` is a second project builder** beside the pin's. Deliberate (no arm's
   helper moves), but it is duplication a reviewer should price.
3. **The resolver fixture's call counter** is the load-bearing trick: if a future change makes
   `validate` stop dispatching resolvers, the write moves to the first call and the fixture
   refuses with `E-CODE-DIRTY` rather than silently passing. It fails loudly, which is the right
   direction, but it is a coupling worth knowing about.
4. **`E-CODE-FILE-LIST` is now reachable from `run`** and still has no § Errors row until task 8.
