# H9b batch 1+2 review — tasks 1, 2, 3 and 4

**Reviewed 2026-08-23** on branch `h9b-resume` at `a0f2f64`, against `main` at `f2e545d`.
**Real-command review**: two `git worktree`s, two `uv sync` venvs, two projects scaffolded and run
through the installed console script **outside this repository**, `run.yaml` read leaf by leaf.
Every mutation below was applied by editing, reverted by editing back, and each revert verified by
**re-running the full suite** — never by `git status`, never by `git checkout --`.

## Verdicts

| Task | Verdict |
|---|---|
| 1 — the guard pin | **PASS** (one Major, in the report's evidence for arm B, not in the arm) |
| 2 — `identity.json`'s document and readers | **PASS** |
| 3 — the write site | **PASS** |
| 4 — the two-sided real-command review | **PASS** |

**Suite at HEAD, unfiltered: `3053 passed, 1 skipped, 4 xfailed` (221–235 s).** `ruff check` clean,
`ruff format --check` clean (93 files), `mypy` clean (52 files). Tree clean after every revert.

**+34 / +2 reconciled by collection count, not by trust**: `main` collects **3022**
(3019+1+2), the branch **3058** (3053+1+4) — **+36**. Per file: `tests/test_run_identity.py`
**8 → 36** (+28) and `tests/test_cli.py` **479 → 487** (+8, of which 5 are task 1's three live arms
plus two `xfail`s and 3 are task 3's). The report's 3 + 28 + 3 + 2 is exact.

---

## 1. The normalization list, and my own two-sided comparison

**Committed before the comparison — verified two ways.** By commit order: `f70f63f`
(16:16:38) carries the list, `61532a1` (16:22:02) carries the comparison. By content:
`git show f70f63f:…/task-b1-report.md` is **byte-identical** to the first 43 lines of the file at
HEAD, so neither `61532a1` nor the fix round `b9e1560` retro-edited it.

**My own comparison, run independently.** Positive control first — each side's
`publishable.__file__` resolves inside its own worktree, so this is two builds and not one build
run twice. One config per side, identical apart from its own absolute paths, scaffolded and
committed through `publishable new` / `generate experiment` and executed through
`publishable dry-run` / `publishable run`. `index.csv` was copied with `cp -p` **before** the runs.

| Comparison | My result | Report's claim |
|---|---|---|
| `run.yaml`, leaf by leaf, in order | **94 leaves each, ZERO differing leaves**, key order identical | 94 leaves, one difference (`input_manifest_hash`) |
| Run-directory tree, path by path | **`identity.json` on the branch side only.** Nothing else added, removed or moved | same |
| Shared paths' size + sha256 | 4 differ: `config.yaml`, `environment/repo_root.txt`, `executions.jsonl`, `run.yaml` — every one on the pre-declared list. `manifest/input.json` **identical** | 5 differ, including `manifest/input.json` |
| `sweep.yaml` | **byte-identical**, and identical as parsed documents with no normalization | identical |
| `executions.jsonl` | 5 lines each, key sets identical line for line (8 keys), `(step, condition, repeat, status, error)` tuples identical, every value but `started_at`/`wall_seconds` identical | same |
| `run` stdout / stderr / exit | **identical** after path normalization; exit `0` both sides | same |
| `dry-run` transcript | **exactly two differences**: `and 7 fixed files` → `and 8`, and one new line `  identity.json`, in **sorted** position between `executions.jsonl` and `manifest/input.json`. Nothing else on either stream; exit `0` both | same |

**The `input_manifest_hash` attribution reproduces, and my run is the control for it.** I read
`manifest.py` first: `build_manifest` records **relative** paths plus `size`, `st_mtime_ns` and
`sha256`, and `manifest_hash` digests that document — so mtime is the only path-independent input
that can move. Because I `cp -p`'d the roster **before** the runs, my two `manifest/input.json`
documents are byte-identical and my `input_manifest_hash` leaves are **equal without
normalization**. That is the same fact the report reached by re-running after `cp -p`. Attribution
confirmed; and my run independently reproduces the report's own figures
`code_hash sha256:436cab24…` / `parameters_hash sha256:fff9b0cb…`.

**The artifact change is FULLY ATTRIBUTED.** One added file, no leaf moved, no hash moved, no
stream moved, and `dry-run`'s two lines.

## 2. `identity.json`'s round trip through a strict reader

**Established by behaviour.** `test_the_document_round_trips_through_a_reader_that_can_fail` and
`test_h9b_identity_json_records_the_runs_own_figures` both use
`json.loads(text, parse_constant=reject)` **and both prove the reader can fail** on
`{"code_hash": NaN}` inside the same test — so the round trip is not vacuous, and correction 22's
killing of *"serializable by invariant"* is answered by performance rather than argument. My own
strict parse of the branch side's real `identity.json` succeeded, and its `code_hash`,
`parameters_hash` and `uv_lock_hash` equal that run's own `run.yaml`, with `config_path` resolving
to the config the command was given.

**The reading the report does not name (Minor 4).** Production `read_identity` calls **bare**
`json.loads` and checks key **presence** only, so a hand-written document is accepted with
non-finite values and with any type:

```
read_identity accepts non-finite: {'code_hash': nan, 'parameters_hash': inf,
                                   'uv_lock_hash': None, 'config_path': 'c.yaml', 'draft': False}
```

No writer can produce that — `Prepared.ch`/`.ph` are `str`, `lock_hash` is `str | None`,
`config_path` is a `Path` and `draft` is a `bool`, read from the annotations — so this is not a
defect in this batch. It is an operand task 8's comparator will be handed, and it is not filed.

## 3. `config_path` is containment-checked on read — the attack, built

Built outside the repo: a repo at `atk/repo`, a real `atk/secret/config.yaml`, a
`run/environment/repo_root.txt` naming the repo, and an `identity.json` per candidate.

```
REFUSED  '../secret/config.yaml'                     -> E-RESUME-NO-CONFIG
REFUSED  'configs/../../secret/config.yaml'          -> E-RESUME-NO-CONFIG
REFUSED  '<abs>/atk/secret/config.yaml'              -> E-RESUME-NO-CONFIG
REFUSED  '<abs>/atk/repo/configs/config.yaml'        -> E-RESUME-NO-CONFIG   (absolute, inside)
OK       'configs/config.yaml'                       -> <abs>/atk/repo/configs/config.yaml
REFUSED  'configs/link.yaml'  (symlink out)          -> E-RESUME-NO-CONFIG
REFUSED  '' / None / 5 / 'configs' (a directory)     -> E-RESUME-NO-CONFIG
```

Forward separators stay legal; the escape, the absolute-inside case and a **symlink** leading out
are all refused, which is more than the docstring had to promise. Pinned in both directions by
mutation: `if False:` in place of the containment test gives **2 failed, 3051 passed** on the full
suite (`test_a_recorded_path_escaping_the_repo_root_is_refused`,
`test_an_absolute_recorded_path_is_refused_even_inside_the_repo`).

**The guard is a restatement of an existing one, and that is the right call.** `StepIO._contained`
is the rule; it raises `ArtifactError` against a step's directory and cannot be called for a
`ContractError` against a repo root, and `report.py`'s study-member resolver already made the same
move. **Adjudicating the third `repo_root.txt` reader: NOT CONSOLIDATING IS CORRECT.** I read all
three. `freeze` (`E-FREEZE-NO-CONFIG`) returns an exit code through its own `_refuse` and so is not
usable as a predicate; `report._read_repo_root` (`E-REPORT-OVERRIDE-REPO`) raises;
`run_identity.read_repo_root` (`E-RESUME-NO-CONFIG`) raises. All three refuse
absent / empty / not-a-directory. Sharing one would change what two **shipped** commands print, and
`freeze.py` is out of task 2's reach. The filing names the shape a consolidation should take
(`_contained`'s one-predicate-plus-`code=`). **One divergence the filing does not mention — Minor 3
below.**

## 4. The NONE arm — arm C

**Verified by diff that no assertion moved.** `git show 811feee -- tests/test_cli.py` deletes
**seven** lines in total and every one is docstring or comment prose; there is not a single `-`
line carrying an `assert`. Arm C's clause went from *SOLE AUTHORIZED EDITOR: NONE* to *H9b task 6,
by controller ruling recorded in the H9b design's Decision 5*, and the ledger key set it asserts is
still the shipped eight — which my own real-command run confirms is eight
(`condition, error, repeat, scope, started_at, status, step, wall_seconds`).

**Adjudication: re-aiming an editor clause is NOT an edit to a NONE arm, on these facts.** The
authority is the design, in writing, before the batch ran (§ The guard pin's arm C row says *"SOLE
AUTHORIZED EDITOR: NONE at HEAD, and Decision 5 re-authorizes it"*, with the post-edit set written
in advance), the brief restates it, and the docstring copies the post-edit set verbatim rather than
paraphrasing. The device protects **assertions**, and no assertion moved. The alternative — leaving
the clause reading NONE while a controller ruling has already named an editor — would put the
contradiction into the file the next implementer greps.

**Arm C still fails under the mutation it exists to catch:** not re-run here, because no code in
this batch touches the ledger writer and the arm's assertion is byte-unchanged from H9a, where it
was captured with its own mutation. Stated as reading, not as behaviour.

## 5. The two moved arms — B and D

`git show c7bbd64 -- tests/test_cli.py` touches exactly two existing lines:

```
+        "identity.json",
-    assert "and 7 fixed files in that directory:" in out
+    assert "and 8 fixed files in that directory:" in out
```

**Both match the post-edit state written in advance.** Arm B's list is
`['conditions', 'config.yaml', 'environment', 'executions.jsonl', 'identity.json', 'manifest',
'run.yaml', 'sweep.yaml']` — the design's § The guard pin table, character for character, one entry
appended in sorted position, nothing reordered. Arm D's literal is `8`. Nothing else in
`tests/test_cli.py` was edited; the three new tests are appended.

**Arm D can fail: confirmed.** Omitting `"identity.json"` from `_DRY_RUN_FIXED_FILES` gives
**4 failed, 3049 passed** on the full suite — and the report's claim that **two different
assertions** catch it is exact: arm D's count literal
(`test_h9a_dry_run_dispatches_end_to_end_and_prints_the_transcript`) plus the set-to-set comparison
in `_h9a_fixture_u`'s three arms.

**Arm B can fail — but NOT under the mutation the report cites. See Major 1.**

## 6. The two disagreements the batch filed — both verified

**Fixture B's prescribed collision is unreachable: CONFIRMED.** `artifacts.py` raises
`E-STEP-KEY-COLLISION` for a recorded column shadowing a declared attribute in **both** `io.record`
branches — the `measurement=` branch at the `collision = self._declared_attributes() &
values.keys()` guard and the plain branch at its mirror — six raise sites of that code in the file,
and `docs/reference.md` documents the refusal at § The per-unit tables, § Errors and § Reporting
strata. So plan correction 6 is right about `finalize`'s merge loop and wrong about reachability
from a step, and design § Fixtures as claims' fixture B cannot be built as written. **Task 8's
by-name-versus-structural mutation needs a new plan, and the report's Concern 2 is the right
escalation.**

**`_DRY_RUN_FIXED_FILES`' ordering clause was already false at HEAD: CONFIRMED against `main`, not
against the current file.** At `f2e545d` the comment read *"The seven a run always writes, in the
order `_execute_prepared` writes them in"* while the tuple ran
`config.yaml, sweep.yaml, manifest/input.json, environment/pyproject.toml,
environment/repo_root.txt, executions.jsonl, run.yaml` and `_execute_prepared` writes
`manifest/input.json` first and `sweep.yaml` sixth. **Deleting the clause rather than rewriting it
is the right call** — `_dry_run_fixed_files` ends `return sorted(files)`, so no order in the tuple
is load-bearing, and my own transcript diff shows `identity.json` printed in **sorted** position,
not in the tuple's.

## 7. Counts and lists — my own greps, every hit attributed

Filtered the file list, never the output; the four documents named individually.

`grep -rn "fixed file" README.md docs/{design-principles,experimental-designs,reference}.md
docs/feasibility-llm-growth-studies.md src/ tests/ CLAUDE.md` → 12 hits.
`reference.md:368`, `:3706`, `:3789`, `feasibility:1471`, `feasibility:2092`, `CLAUDE.md:208`,
`CLAUDE.md:220` — prose about what `dry-run` prints, no count. `cli.py:4494` — a docstring, no
count. `cli.py:4611` — the f-string that computes the count. `test_cli.py:21139` —
`_H9A_DRY_RUN_FIXED_HEADER`, self-maintaining. `test_cli.py:21184` — prose.
**`test_cli.py:21716` — arm D's literal, edited, `8`.** One hit needing an edit; it was made.

`grep -rn "and 7 fixed\|and 8 fixed"` over the same set → **2 hits**: arm D's (`8`, correct) and
**`docs/reference.md:3109`, the worked `dry-run` transcript, which reads `and 8 fixed files` and
lists eight names.** That block declares a lockfile, so its count is `_DRY_RUN_FIXED_FILES` plus
`environment/uv.lock`: it **must become `9` with `identity.json` in the list, and it is wrong on the
branch right now.** No test parses it — confirmed by grep, the three `"would create"` hits in
`tests/` are all assertions on the **command's** output — which is why the suite is green over a
wrong document.

`grep -n "^<run_dir>/" docs/reference.md` and the tree at `:840` → **both `<run_dir>/` trees omit
`identity.json`**; the § Steps and artifacts one also omits `config.yaml` and
`environment/repo_root.txt`, so it is behind H8b too. `reference.md:882`'s *"`sweep.yaml`,
`allocation.json`, `config.yaml` and `environment/repo_root.txt` are settled before the first
execution and never touched again"* and `:890`'s *"Together the pair holds exactly the two facts a
mid-run command cannot otherwise obtain and cannot compute"* are both live and both now false of
the tree. The report names every one of these. **Status: correctly deferred, incorrectly
un-briefed — Major 2.**

## 8. The two new `xfail`s

**Both `strict=True`, both name their remover, both fail for the right reason — read by behaviour,
under `--runxfail`.**

- `test_h9b_arm_a_crash_and_resume_equals_straight_through`, reason names **task 9**. Fails at
  `assert main(["resume", str(crashed)]) == EXIT_OK` → `assert 2 == 0`.
- `test_h9b_arm_g_the_takeovers_mutual_exclusion`, reason names **task 14**. Fails at
  `assert hits, "the liveness hook never fired"`.

So neither is silently green on a broken fixture, and both currently fail on `resume` being
unbuilt. Independently confirmed through the console script:
`publishable resume <run dir>` prints ``  `publishable resume` is specified but not built in this
version`` and **exits 2**.

**The declaration that the two `xfail` mutations are blind is correct and is the right disclosure.**
`xfail(strict=True)` absorbs every failure reason, so a production mutation proves nothing about
either. What was built in their place — two **live** fixture-state halves asserting positive
presences — is the right substitute, and both fail under a real production mutation:
`RunLock.__enter__`'s `"pid": os.getpid()` → `os.getppid()` gives **2 failed, 3051 passed** on the
full suite, exactly `test_h9b_arm_a_the_crash_fixture_is_really_crashed` and
`test_h9b_arm_g_the_dead_holder_fixture`.

## 9. Every mutation, re-run at HEAD, counts read off a FULL unfiltered run

The report's counts were taken at each task's own commit; mine are at HEAD (total 3053). Every one
reconciles.

| Mutation | Mine, at HEAD | Report's | Caught by |
|---|---|---|---|
| `run_record.py`: `cond["is_baseline"] = not meta.get(...)` | **9 failed, 3044 passed** | 9 failed, 3013 passed (total 3022) | `test_h9b_arm_a_the_straight_through_golden` **and** H9a arm A, 2 × `test_acceptance`, 4 × `test_report`, 1 × H5b — the exact list reported |
| `run_identity.RunLock.__enter__`: `os.getpid()` → `os.getppid()` | **2 failed, 3051 passed** | 2 failed, 3020 passed (total 3022) | arm A's and arm G's fixture-state halves, nothing else |
| `config_path_for`: containment test → `if False:` | **2 failed, 3051 passed** | 2 failed, 3048 passed (total 3050) | the `../../secret` positive control and the absolute-inside refusal |
| `_IDENTITY_KEYS` drops `"draft"` | **1 failed, 3052 passed** | 1 failed, 3049 passed (total 3050) | `test_a_document_missing_any_one_key_is_refused[draft]` |
| the write moved **outside** `with RunLock` | **1 failed, 3052 passed** | 1 failed, 3052 passed | `test_h9b_identity_json_exists_while_the_lock_is_held` only — **arm B stayed green, confirming the report's advance check** |
| `"identity.json"` omitted from `_DRY_RUN_FIXED_FILES` | **4 failed, 3049 passed** | 4 failed, 3049 passed | arm D's literal **and** `_h9a_fixture_u`'s three set-to-set arms |
| **added by this review** — the write statement deleted entirely | **7 failed, 3046 passed** | not run | **`test_h8b_arm_a_the_run_directorys_root` (arm B)**, `_h9a_fixture_u` ×3, and task 3's three new tests |

**Writer/reader agreement is pinned on both sides against literals**, which is what makes the
`draft`-drop mutation meaningful: `test_the_document_is_five_keys_in_one_order` enumerates the five
names as a literal list against `identity_document`, and
`test_a_document_missing_any_one_key_is_refused` parametrizes the same five literals against
`_IDENTITY_KEYS`. Neither test iterates the thing under test.
`test_a_written_document_reads_back_key_for_key` round-trips through **production `read_identity`**,
not through the test's own reader, and asserts key order as well as equality.

All seven mutations were reverted **by editing back**, each verified byte-identical against a
pre-mutation copy **and** by re-running: the final unfiltered run is `3053 passed, 1 skipped,
4 xfailed`, and `git status --porcelain` is empty. No `git checkout --` was used.

## 10. Claims the report makes about other tests, other rows or other code — grepped

- *"`identity.json` is a free name"* — `git grep -lF "identity.json" f2e545d -- src/ docs/ tests/`
  returns **only** this slice's own plan and design; over `src/`, `tests/` and the four documents
  plus the feasibility analysis it is **0**. The claim holds; plan correction 7's flat "0 hits" is
  loose about the development record, the report's *"no hit naming the artifact"* is not.
- *"`git diff src/publishable/provenance.py` is empty"* — `git diff f2e545d..HEAD --stat -- src/`
  shows **only** `cli.py` (+62/−3) and `run_identity.py` (+185). `provenance.py` untouched.
- *"§ Corrections 19's 36-field unpack block is byte-identical"* —
  `git diff f2e545d..HEAD -- src/publishable/cli.py | grep -c "^[-+].*= prepared\."` → **0**.
- *"`lock` holds two keys"* — one write site, `json.dump({"host": socket.gethostname(), "pid":
  os.getpid()}, fh)`. Two. Arm G's live half asserting a **subset** is therefore the right shape
  for an arm whose editor is NONE.
- *"no arm can see the write's position"* — not accepted as reading; **re-measured**, arm B green
  under the out-of-lock mutation.
- *"no existing assertion holds `reference.md`'s `dry-run` count"* — grepped (§ 7 above), and
  corroborated by the omit mutation, under which the document's `8` was untouched while the code's
  list changed.
- *"`artifacts.py` raises that code at six sites"* — `grep -c` → **6**.
- *"the two shipped `repo_root.txt` readers are `freeze` and `report._read_repo_root`"* — all three
  read, all three carry the same triple. Confirmed.
- **The report makes no zero-disagreements claim** and files two disagreements of its own. Both
  verified above.

## 11. Undisclosed drops — each brief diffed against what shipped

- **Task 1**: arms A and G built (each half live, half `xfail`); B, C, D, E re-authorized by
  docstring/comment only; F and H cited per arm with what each holds. Touched only
  `tests/test_cli.py`; no `src/`, no `*.md`, no assertion. **One undisclosed departure — Minor 2.**
- **Task 2**: every prescribed symbol exists. The brief's ambiguity (`config_path_for` handed a
  `repo_root` yet assigned the `repo_root.txt` refusals) is resolved by splitting out
  `read_repo_root`, **disclosed as a resolution with its reason**, both halves keeping one code.
  Touched only `run_identity.py` and `test_run_identity.py`; the one deletion in the test file is an
  import line. `cli.py`, `provenance.py`, `freeze.py`, `*.md` untouched.
- **Task 3**: one statement, immediately after `environment/repo_root.txt`'s and before
  `sweep.yaml`'s `mode = …`, inside `with RunLock(run_dir)` — read at `cli.py` and confirmed by the
  out-of-lock mutation. Nothing recomputed, no local added. The brief's *"you may edit nothing else
  in `tests/test_cli.py`"* was read as forbidding edits to other **tests** while allowing the new
  pin the same brief's mutation clause demands; **disclosed, and I agree** — the clause would
  otherwise contradict itself. `draft: true` is covered with both arms in one test, so a hardcoded
  flag fails either way.
- **Task 4**: touched nothing but the report. Confirmed by `git show --stat`.

---

## Findings

### Major 1 — the report's arm-B row cites a mutation that leaves arm B green, and the mutation that fails it was never run

`task-b1-report.md` line 75: *"| **B** — `test_h8b_arm_a_the_run_directorys_root` | … | edited by
task 3; **the mutation that proves it can fail is task 3's M6** | **4 failed, 3049 passed** under
M6 |"*. **Arm B is not among M6's four failures.** My own full-suite run of that exact mutation:

```
FAILED tests/test_cli.py::test_h9a_fixture_u_the_two_lists_match_a_real_runs_tree
FAILED tests/test_cli.py::test_h9a_fixture_u_the_conditional_fixed_files_uv_lock_and_allocation
FAILED tests/test_cli.py::test_h9a_fixture_u_the_conditional_fixed_file_apparatus_probes_jsonl
FAILED tests/test_cli.py::test_h9a_dry_run_dispatches_end_to_end_and_prints_the_transcript
4 failed, 3049 passed, 1 skipped, 4 xfailed
```

Arm B lists a **completed run directory's root**; M6 changes only `dry-run`'s printed tuple, which
that arm never reads. The report's own two other rows say as much — line 77 enumerates M6's four
failures and arm B is absent from the list, and the task 3 section states *"arm B **CANNOT** see the
write's position … under the mutation arm B stayed green."* So the report holds both claims at once,
which is precisely what design § 7 warns against: *"an arm offered as evidence that an edit is safe
because it cannot see the edit is two opposite facts wearing one sentence."* Arm B's assertion
**moved** in this batch and the batch reports no mutation that fails it.

**The arm is real — I established that rather than leaving it open.** Deleting the write statement
entirely gives **7 failed, 3046 passed** on the full suite, with
`test_h8b_arm_a_the_run_directorys_root` first in the list. So the defect is in the **evidence**,
not in the pin: the honest mutation for a moved list entry is *omit the artifact*, and it was never
run. Fix by correcting the row to that mutation and its count.

### Major 2 — the documents work is filed in a report and has not reached task 17's brief, and `reference.md` is wrong on the branch right now

The report's Concern 4 is right and specific, and the plan was not amended. Plan § Task 17 names
**§ The other files a run writes** and the *"exactly the two facts"* sentence. It does **not** name:

- `docs/reference.md:3109`, the worked `dry-run` transcript — `and 8 fixed files` must become `9`
  and gain a list line. **This is a shipped-wrong fenced example on the branch today**, green only
  because no test parses that block.
- `docs/reference.md:840`'s `<output_dir>/` tree and `:2529`'s second `<run_dir>/` tree — neither
  lists `identity.json`.
- `reference.md:882`'s settled-before-execution list.
- The § The other files a run writes table-of-contents line, which names the files it covers.

CLAUDE.md's own rule is the one at stake: *"a ruling that overrules a brief has to reach the
brief… the ledger reaches the controller and the reviewers; it reaches no implementer."* The design
was appended to for the arm B/D editor slip (`a0f2f64`) and not for this. **Append these five items
to plan § Task 17 before batch 8 is dispatched**, or task 17 will be scoped to the artifact-layout
tree alone — which is exactly what Concern 4 predicts.

Also for that task: `E-RESUME-NO-IDENTITY` and `E-RESUME-NO-CONFIG` now raise from shipped `src/`
and have **no § Errors row** in `reference.md` (`grep -c` → 0). Task 17's § Resuming bullet names
the first code; neither is named as an § Errors row.

### Minor 1 — the design's arm-B row is wrong about HEAD in a second way, and the batch flagged only the first

Design § The guard pin, arm B: *"the run directory's sorted root list, **editor NONE at HEAD** and
re-authorized here."* At `f2e545d` that docstring read *"ONE OF TWO ARMS AN AUTHORIZED TASK MAY
EDIT, and task 3 is that task"* — an editor, not NONE. The task 1 brief has it right (*"one whose
current editor is a closed slice's task and one whose current editor is NONE"*) and the batch's own
docstring has it right (*"The H8b-era clause this replaces read 'task 3 is that task'"*), so the
implementer knew the HEAD state and reported only the *"plan task 4"* half of the same row's error.
Worth appending to the design correction that already exists, so the row is not read as evidence
that arm B was a NONE arm.

### Minor 2 — arm A's normalization list is extended and the extension is disclosed in code but not in the report, which the brief asked for by name

The task 1 brief: *"normalizing **exactly**: any key named `at`, `started_at`, `wall_seconds`,
`run_id`, `hostname`, `attempts`; any absolute path under `tmp_path`; and the three hashes. **Do not
extend that list**, and if you must, **say so in the report as a finding**."* `_h9b_run_yaml_leaves`
delegates to H9a's `_h9a_run_yaml_leaves`, whose `_H9A_NORMALIZED_LEAF_KEYS` includes **`commit`**.
The delegation's docstring discloses it in as many words, with its measurement, and H9a disclosed it
first — so this is inherited and honest, not hidden. But the report's arm-A row says only *"185
normalized leaves"*, and the word "extension" appears nowhere in the report
(`grep -n "extension\|EXTENSION\|extend"` → 0 hits). The brief named the report as the place. One
sentence closes it.

### Minor 3 — the third `repo_root.txt` reader diverges from both precedents on encoding, and the filing does not say so

`freeze` and `report._read_repo_root` both read `repo_root_path.read_text(encoding="utf-8")`.
`run_identity.read_repo_root` reads `path.read_text().strip()` — **locale-default encoding**. The
new docstring and the report both claim it carries *"the same three refusals"*, which is true of the
refusals and not of the read. The sibling that already got it right is in the file the docstring
cites. Also a shape difference worth recording in the same place: the two shipped copies gate on
`is_file()` while this one catches `OSError`, which reaches the same three verdicts by a different
route. Neither changes an answer I could produce, so this is a Minor and not a defect — but the
consolidation filing should carry it, because a consolidation that silently picks one spelling would
be changing behaviour it did not know it was changing.

### Minor 4 — `read_identity` validates presence only, and the report does not name what that hands task 8

`read_identity` calls bare `json.loads` and checks that the five keys are **present**. A hand-edited
document with `"code_hash": NaN`, or with an integer where a hash string belongs, is returned
intact (probe output in § 2 above). **No writer can produce one** — the five values come from
`Prepared`'s typed fields and `_execute_prepared`'s `draft` parameter — so this is not a defect in
this batch, and I am not filing it as one. It is an operand: task 8's comparator will be handed
whatever this returns, and the batch that built the reader is the cheapest place for that sentence
to exist. Say in the report which of the two readings the round-trip pin covers (the **writer's**
output, not an arbitrary file's).

### Minor 5 — `c7bbd64`'s commit subject claims a behaviour `resume` does not have

*"H9b task 3: run, draft **and resume** write identity.json at run start."* `resume` writes nothing:
through the console script it prints ``  `publishable resume` is specified but not built in this
version — see docs/reference.md § Resuming`` and exits **2**, which I confirmed against the branch
build. The code comment and the report are both accurate; only the subject line overreaches. Not
worth a rewrite of history, worth not repeating.

### Minor 6 — the fix round retro-edited two of the report's own claims instead of appending the correction

`b9e1560` rewrites the task 4 table cell (*"in write order"* → *"in **sorted** position…"*) and
deletes a `grep -rn "seven"` sentence, in place. The **timestamped normalization list is
untouched** — verified byte-identical to `f70f63f` — and the commit message discloses both changes,
so nothing is concealed and git holds the prior text. But a task report is development record, and
this repo's rule for a published claim is *append the correction and say what it replaces*. The
same commit's third change gets this right, adding a **FINDING** paragraph rather than editing the
comment's history.

---

## What was verified by behaviour versus by reading

**By behaviour** (a command run, a mutation applied, or a probe executed): the full suite at HEAD
and after each of seven mutations, all counts read off unfiltered runs; the three gates; both
collection counts reconciling +36; the two-sided real-command comparison in full (tree, `run.yaml`'s
94 leaves, `sweep.yaml`, `executions.jsonl`, three streams, `dry-run`'s transcript); the
`input_manifest_hash` attribution, with `cp -p` as the control; the containment attack across ten
recorded values including a symlink; `read_identity`'s acceptance of non-finite tokens; both new
`xfail`s' actual failure reasons under `--runxfail`; `resume`'s unbuilt exit `2` through the console
script; arm B's failure under the omitted write; arm B's green state under the out-of-lock and
omit-from-tuple mutations; every revert.

**By reading** (with the file named): the diffs establishing that no assertion moved in `811feee`
and that exactly two moved in `c7bbd64`; the write site's position inside `with RunLock`; the
`f2e545d` state of `_DRY_RUN_FIXED_FILES`' comment and tuple; both `io.record` collision guards;
all three `repo_root.txt` readers; `manifest.py`'s digest inputs; `Prepared`'s field annotations;
the two `<run_dir>/` trees and the four `reference.md` sentences; plan § Task 17's contents; the
design's § The guard pin and § Fixtures as claims; every grep in § 7 and § 10.

**Neither, and said so**: that arm C still fails under its own mutation — its assertion is
byte-unchanged from H9a and nothing in this batch touches the ledger writer, so I relied on H9a's
capture rather than re-running it.
