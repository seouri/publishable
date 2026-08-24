# H9c tasks 1–6 — report

Six commits, one per task, in order. Full suite green at the last of them:
**3183 passed, 1 skipped, 2 xfailed** (baseline before this batch: 3132/1/2, verified
by running it at `6ff19de` before anything moved).

| Task | Commit | What it is |
|---|---|---|
| 1 | `0346f2d` | The guard pin: arms E and F built, A/B/C/D/G cited |
| 2 | `3b13c2d` | `reproduce.py`'s operand reader (Ruling Y) |
| 3 | `36a22ca` | The destination and the clone (Rulings Y, Z) |
| 4 | `fdeda99` | `code_hash` in the checkout (Ruling Z) |
| 5 | `e6d5dd6` | The lockfile ranking (Ruling AA) |
| 6 | `8606984` | Q1 and Q3 decided; the footnote and the strike |

Every mutation below was run against the **full, unfiltered** suite and every count is
read from that run's own summary line. Reverts were performed by restoring a
pre-mutation copy kept outside the repo (never `git checkout --`), verified **twice** —
by `md5` against that copy and by **re-running** the tests the mutation had failed. Two
of the six task-1 reverts were performed by editing the line back rather than by
restoring a copy; both were verified the same two ways. `git checkout -- <file>` was
never used.

---

## 1. The absent delta figures

**The dispatch says "each brief states a delta". None of the six briefs states one** —
grepped: `grep -n "delta" .superpowers/sdd/2026-08-24-reproduce/task-*-brief.md` returns
nothing in any of the six. Rather than invent a figure, the measured before/after counts
are stated per commit:

| After | Passed | Added |
|---|---:|---:|
| baseline `6ff19de` | 3132 | — |
| task 1 | 3135 | +3 (arm E ×2 parametrizations, arm F) |
| task 2 | 3150 | +15 |
| task 3 | 3166 | +16 |
| task 4 | 3172 | +6 |
| task 5 | 3183 | +11 |
| task 6 | 3183 | +0 (documents and one branch that already shipped with task 5) |

Skipped and xfailed never moved: 1 and 2 throughout.

---

## 2. The brief-versus-appendix disagreements — I followed the appendix

**Corrections 26–29 reached the plan and reached none of the six briefs.** Each is a
place where a brief, read alone, would have produced the wrong thing.

| Brief | What it says | What the appendix says | What I built |
|---|---|---|---|
| 4 | "Fixtures C, **D**", D being *the rewritten file* | **Correction 26: Fixture D is not constructible.** A commit SHA is a hash over its own tree; an amend makes a new SHA and leaves the original's tree intact, so the recorded SHA still checks out to the recorded bytes and the comparison **passes** | **D1** (record's `code_hash` set to the every-file figure, computed in-test) and **D2** (an arbitrary digest) |
| 3 | Twelve codes; no commit-unreachable code | **Correction 26: a thirteenth code**, `E-REPRODUCE-COMMIT-UNREACHABLE` at exit `5`, for a commit the remote no longer holds | Built, with the `--no-local` bare-intermediate recipe |
| 3 | Fixture A's local-path remote | **Correction 26's named trap:** a local-path clone hardlinks the object database, unreachable objects included, so Fixture A's own remote **cannot** reproduce that state | The intermediate is cloned `--no-local`; the fixture asserts its own claim with `git cat-file -e` before the arm runs |
| 5 | "The byte copy is reachable — `environment/uv.lock` **beside the operand**, i.e. the run-directory form" | **Correction 28: it is a filesystem probe, not a structural fact**, and the docstring must say so | `restore_environment`'s docstring states the probe, states that a bundle inside a run directory would take the run-directory branch, and states that the digest check is what makes the probe safe rather than a proxy |
| 15 (not mine) | "twelve" | **Correction 29: thirteen, and it carries its noun** | Not my task; recorded here because my code's count has to agree with it — see § 6 |

---

## 3. Task 1 — the guard pin: every arm, its editor, and the shape captured against

**Shape captured against:** the design's § 1 and § 2 as written, i.e. **forward**, in the
shape H9c has already decided. Arms B and C are captured at their **pre-edit** state with
their post-edit state written out in advance, in a comment block above the two arms I
built and in this report. **No arm needed to move**, so nothing was left red.

| Arm | Built or cited | Authorized editor | Where |
|---|---|---|---|
| **A** | **Cited** | **NONE** | `test_h9a_arm_a_a_completed_runs_whole_run_yaml_leaf_by_leaf`, `test_h9a_arm_b_runs_full_stdout_line_by_line`, `test_h9b_arm_a_the_straight_through_golden` (+ its two siblings `test_h9b_arm_a_the_crash_fixture_is_really_crashed`, `test_h9b_arm_a_crash_and_resume_equals_straight_through`) |
| **B** | **Cited, pre-edit** | **plan task 11 only.** Post-edit state written now: the line becomes `("reproduce", "built")` **and** a new `assert ("list-templates", "NOT BUILT") in tables["Command"]` is added (correction 20). The `set(NOT_BUILT_COMMANDS)` equalities beside it are self-maintaining and must not be edited | the `assert ("reproduce", "NOT BUILT") in tables["Command"]` line inside `test_reference_cli_tables_are_parsed_at_all`, `tests/test_cli.py` |
| **C** | **Cited, pre-edit** | **plan task 9 only.** Post-edit set: `{"E-APPARATUS-RAISED", "E-APPARATUS-CHANGED", "E-APPARATUS-UNEXPECTED"}` — one member added, none removed, nothing reordered | the `STOP_CODES == {...}` line inside `test_stop_codes_holds_exactly_the_two_codes_execute_plan_breaks_on`, `tests/test_apparatus.py` |
| **D** | **Cited** | **NONE** for both shipped assertions. Task 9 may **add** a sibling `assert "E-APPARATUS-UNEXPECTED" not in APPARATUS_CODES`; adding is not editing | the two `APPARATUS_CODES` membership assertions, in the **same function** as arm C |
| **E** | **BUILT** | **NONE** | `test_h9c_arm_e_reproduce_writes_nothing_outside_its_destination[record]` and `[bundle_member]`, `tests/test_cli.py` |
| **F** | **BUILT** (see § 3.2) | **NONE** | `test_h9c_arm_f_w_env_unlocked_names_reproduce_in_its_own_message`, `tests/test_cli.py` |
| **G** | **Cited, each by name** | **NONE** | `test_h8b_arm_b_environments_contents`, `test_h8a_arm_a_a_clean_run_top_level_shape_status_and_exit`, `test_h8a_arm_b_the_provenance_key_list_and_upstream_empty`, `test_h8b_arm_a_the_run_directorys_root` (= H9b arm B), the `and 8 fixed files` line in `test_h9a_dry_run_prints_the_plan_and_creates_nothing` (= H9b arm D), `test_h8b_arm_e_the_recorded_sweep_plan`, `test_h9a_arm_c_*` and `test_h9a_arm_e_*` |

**Arms C and D are co-located in one test function.** Recorded rather than papered over:
task 9's authorization is scoped to the set-equality **line** plus an added sibling, and
to nothing else in that body. The two mutations below are distinguished by *which
assertion* fails, not by node id.

### 3.1 Arm E — and the finding that the prescribed mutation was blind against its first build

Arm E snapshots three whole trees as `{path → sha256}` — the run directory, the operand's
own tree, and the source repository — before and after the command, asserting ADDED,
REMOVED and CHANGED all empty over each. Established **by snapshotting**, never by reading
for absent `mkdir` calls.

Four things stated in the arm's own docstring because a reader would otherwise have to
re-derive them:

- **The working directory is a fourth tree and is deliberately not snapshotted.** Decision 9
  creates the destination *relative to the working directory*, so the command is driven from
  a scratch directory outside all three snapshotted trees. Had the cwd sat inside any of
  them, the arm would pass today and fail the moment task 11 built the command.
- **The exit code is deliberately not asserted.** It is `EXIT_INVOCATION` today and task 11
  moves it; an arm whose editor is NONE must not hold a value a later task has to change.
- **The fixture writes a real bare-repo remote into the record** so that at task 11 this same
  call clones, checks out, recomputes `code_hash` and refuses `E-REPRODUCE-UNLOCKED`.
  Without it, `run_a_project` records `remote: null` and the command would stop at
  `E-REPRODUCE-NO-REMOTE` before deriving a destination — the arm would pass by never
  reaching the code it guards.
- **`.git` is excluded**, with the reason stated: git rewrites its index, objects and reflog
  on its own schedule, so including it would make the arm intermittent rather than stricter.

**The finding.** The prescribed mutation is *make the `NOT BUILT` path `mkdir` one directory
under the operand's parent*. Against arm E's **first** build — a map of **files** only — that
mutation left the suite at **3135 passed, 0 failed**: an empty directory has no files in it.
The helper was widened to record a directory as `"<dir>"`, and the mutation then failed
**both parametrizations and nothing else**. The measurement is written into
`_h9c_tree_map`'s docstring, because a later reader tempted to simplify it back to files
needs the number.

Also corrected: the brief says to apply that mutation to `cli._report_not_built`. That
helper takes a command name and a section string and **never sees the operand**, so a
`mkdir` "under the operand's parent" cannot be written there at all. Applied at
`_dispatch`'s `NOT_BUILT_COMMANDS` branch instead, and said so in the arm's docstring.

### 3.2 Arm F — added, not cited, and the design-versus-code disagreement that made it so

§ 8 calls arm F a **shipped** assertion that **must not move**. Grepped
newline-insensitively for the clause across `src`, `tests` and `docs`
(`grep -rn "restore it" src tests docs`), every hit attributed:

| Hit | What it is |
|---|---|
| `src/publishable/cli.py` | the production message itself |
| `tests/test_cli.py` | **one entry of `test_h9a_arm_b_runs_full_stdout_line_by_line`'s whole-stdout list literal**, spelled across an implicit string concatenation |
| `docs/reference.md` § Warnings core reports | the `W-ENV-UNLOCKED` row |
| `docs/superpowers/H9-SCOPING.md`, the H9c plan (×2), the H9c design (×2) | prose about this arm |

So **no standalone assertion existed**. The task 1 brief authorizes exactly this case
(*"if the phrase is asserted only as a substring of a longer literal, add an arm that
asserts that clause on its own"*), so arm F is **added**. It reads the clause out of the
`W-ENV-UNLOCKED` diagnostic's **own** rendered message — located by its header line — rather
than out of stdout as a whole, so a neighbouring line carrying the same words could not
satisfy it. **This is a disagreement with § 8's wording, not a stop condition.**

Its own first draft was wrong and its own control caught it: `run_a_project` consumes
`capsys` internally, so `capsys.readouterr()` in the test body returned empty and the arm
failed on `len(headers) == 1`. Fixed to read the driver's returned `doc["stdout"]`.

### 3.3 The six mutations, each full-suite

| # | Mutation (production code) | Full-suite result | Arms that failed |
|---|---|---|---|
| 1 | delete the write of `config.yaml` from `_execute_prepared` | **47 failed, 3088 passed** | of the arms: `test_h8b_arm_a_the_run_directorys_root` and `test_h9b_arm_a_the_crash_fixture_is_really_crashed` |
| 2 | remove `reproduce` from `NOT_BUILT_COMMANDS` | **2 failed, 3133 passed** | **arm B** (`test_reference_cli_tables_are_parsed_at_all`) + `test_reference_cli_tables_match_what_the_cli_does[Command]` |
| 3 | delete `E-APPARATUS-RAISED` from `STOP_CODES` | **3 failed, 3132 passed** | **arm C** (`test_stop_codes_holds_exactly_the_two_codes_execute_plan_breaks_on`) + `test_g_fixture_u_unreachable_mid_plan`, `test_a_stop_signal_records_the_reason_and_the_contract_error_does_not_escape` |
| 4 | add `E-APPARATUS-CHANGED` to `APPARATUS_CODES` | **1 failed, 3134 passed** | **arm D**, and confirmed to be arm D's own line rather than arm C's: the reported assertion was `assert "E-APPARATUS-CHANGED" not in APPARATUS_CODES` |
| 5 | `mkdir` one directory under the operand's parent on the `NOT BUILT` path | **2 failed, 3133 passed** | **arm E**, both parametrizations, and nothing else |
| 6 | change `W-ENV-UNLOCKED`'s clause | **2 failed, 3133 passed** | **arm F** (`test_h9c_arm_f_w_env_unlocked_names_reproduce_in_its_own_message`) + `test_h9a_arm_b_runs_full_stdout_line_by_line` |

**Mutation 1 is the one that does not do what the brief says it does.** The brief calls it
"arm A's cited arms". Measured: it does **not** fail `test_h9a_arm_a_*` or
`test_h9a_arm_b_*` or `test_h9b_arm_a_the_straight_through_golden` — `config.yaml` is a
run-**directory** artifact, and none of those three reads the run directory's file list. It
reaches arm A only through H9b arm A's **fixture-state** half (a resume needs the byte
copy), and it otherwise lands on `test_h8b_arm_a_the_run_directorys_root`, which § 8 cites
under arm **G**. So the "run tree path by path" half of arm A's description is held by an
arm G citation, and that is where the mutation lands. Arm A can fail; the attribution in
the brief is wrong.

**Mutation 4's assertion identity was confirmed by reading the failure**, not inferred.
Mutation 3's was not re-confirmed the same way: the two assertions run in order and
`STOP_CODES == {...}` is first, so under mutation 3 it is the one that raises. That is a
deterministic argument, not a measurement, and it is labelled as such.

---

## 4. My own measurement of the `core.autocrlf` dependence

Run outside the repository, on a two-file `src/` tree at one commit, with an ambient
`core.autocrlf = true` installed through `GIT_CONFIG_GLOBAL`. `git version 2.50.1 (Apple
Git-155)`. Digests are the `code_hash` fold (`sha256(path)\0sha256(contents)\n`), truncated
to 7 hex characters here; the absolute values are this fixture's, not the design's.

| Tree | Digest | `src/pkg/mod.py` bytes |
|---|---|---|
| the original working tree | `79baf6d` | `x = 1\ny = 2\n` |
| a plain clone | **`62f7769`** | `x = 1\r\ny = 2\r\n` |
| `git -c core.autocrlf=false clone` | `79baf6d` | `x = 1\ny = 2\n` |
| `git -c core.eol=lf clone` | **`62f7769`** | `x = 1\r\ny = 2\r\n` |

**So a faithful clone's `code_hash` depends on `core.autocrlf`, a machine-local setting.**
`code_hash` is therefore **not reproducible across platforms** without the override, and
that is a property of the machine rather than of the tree — which is why `reproduce` says
so (Decision 2's candidate set) rather than blaming the tree. `core.eol=lf` is **not
load-bearing** and is not passed. Both facts reproduce the design's § 0.4 relationally.

### 4.1 Where my measurement DISAGREES with the design, and what it cost

Decision 7 and plan correction 1 state: *"Measured: `clone -c` alone stored `false` and
still produced CRLF, because the ambient value won for the initial checkout — so neither
placement is redundant."* **On git 2.50.1 that is false.** Measured, same ambient setting:

| Invocation | `.git/config` `core.autocrlf` | initial checkout | after `rm` + `git checkout -- <file>` |
|---|---|---|---|
| `git -c core.autocrlf=false clone` (leading only) | **`true`** | LF | **CRLF** |
| `git clone -c core.autocrlf=false` (`clone -c` only) | `false` | **LF** | LF |
| both | `false` | LF | LF |

So the load-bearing placement here is **`clone -c`**, whose stated job — persisting the
setting so a later `git checkout` in the prepared tree does not re-convert — is real and
provable; and the **leading `git -c`** cannot be armed by any hash on this git, because
`clone -c` alone already fixes the initial checkout.

Consequences, all disclosed in the code and in the arms:

- **Both placements are still passed**, as decided, and the docstring says which one this
  build could prove.
- **Fixture E arm 2 is re-aimed**, and the prescribed mutation (*drop the leading `git -c`,
  keep `clone -c`*) is **named blind in advance** with the git version. Arm 2 now asserts
  the destination's stored `core.autocrlf` **and** that a re-materialized hashed file still
  yields the recorded digest — which is what fails when `clone -c` is dropped.
- **The owed replacement is arm 3**, a structural assertion on the invocation's flag list,
  captured from the real call rather than read off the constant. Measured: mutation 3b
  (drop the leading `git -c`) failed **arm 3 alone** — 1 failed, 3165 passed — confirming
  both the blindness and the replacement in one run.

---

## 5. Every lockfile comparison, and where it is reported

Ruling AA's rule is that neither source is preferred silently. Every comparison
`restore_environment` makes is a **printed line** or a **named refusal**; there is no
silent branch.

| Situation | What is reported, and where | Arm |
|---|---|---|
| `uv_lock_hash` is `null` | `E-REPRODUCE-UNLOCKED`, exit `1`, checkout kept, plus the transcript line `uv sync: not run — the record pinned no environment` | Fixture L |
| byte copy reachable, digest matches, **clone has none** | line: `uv.lock: the commit carries none; restored from the run's own copy` | `test_the_byte_copy_is_restored_and_a_commit_with_no_lockfile_is_reported` |
| byte copy reachable, **clone's copy identical** | line: `uv.lock: the commit's copy is identical to the run's` | `test_a_commit_whose_lockfile_matches_the_record_is_reported_identical` |
| byte copy reachable, **clone's copy differs** | line: `uv.lock: DIFFERS — the commit carries <digest> and the run used <digest>; the run's own copy is what is restored`, then `uv.lock: restored from <path>` | Fixture I |
| byte copy reachable, **digest does not match the record** | `E-REPRODUCE-LOCKFILE-EDITED`, exit `1`, naming both digests; the clone's lockfile asserted **untouched** | `test_a_byte_copy_edited_after_the_run_is_lockfile_edited_and_is_not_used` |
| byte copy **unreachable** (bundle), clone's matches | two lines: `uv.lock: the run's own copy is not reachable from <operand>` then `uv.lock: the commit's own copy matches the recorded <digest>, so it is what the environment is restored from` | Fixture H |
| byte copy unreachable, clone has **none** | `E-REPRODUCE-LOCKFILE-UNREACHABLE`, exit `1`, naming the recorded digest **and** `no uv.lock at all` | Fixture G |
| byte copy unreachable, clone's **differs** | same code, naming the recorded digest **and** the clone's digest | `test_a_bundle_whose_committed_lockfile_disagrees_with_the_record_is_unreachable` |
| `pyproject.toml`, reachable, identical | line: `pyproject.toml: identical to the run's` | `test_an_unmoved_pyproject_is_reported_identical` |
| `pyproject.toml`, reachable, differs | line beginning `pyproject.toml: DIFFERS`, asserted **and asserted to precede** the `uv sync` line; the commit's own manifest asserted unchanged on disk | Fixture J |
| `pyproject.toml`, **not reachable** (bundle) | line: `pyproject.toml: the run's own copy is not reachable from <operand>, so it is not compared` | reached by Fixtures G and H |
| `uv sync --locked` fails | `E-IO-FAILED`, exit `5`, with git's/uv's own text | `test_a_real_uv_sync_failure_is_exit_five` |

**`uv_support.uv_lock_info` was not called and not touched**, as the brief requires: it
answers *what does this repo hold now*, taking a repo root, which is a different question
from *what is this particular file's digest*. `_sha256_of` reproduces only its **spelling**
(`sha256:` prefix) so the two answers are comparable.

### 5.1 The narrowing of Fixture H's claim, stated rather than reinterpreted

Correction 22 forbids any recipe from running `uv lock`, so **every fixture lockfile in
this slice is written, not resolved** — and a written lockfile cannot satisfy a real
`uv sync --locked` resolve. Confirmed by the arm that lets the real call run: it fails,
which is why that arm is the exit-`5` arm.

So the design's *"step 3's success arm"* can only mean **reached the sync step with the
right lockfile in place**, never **synced**. The sync is therefore its own function,
`_uv_sync`, and the success arms observe its argv and cwd. `_stub_sync`'s docstring carries
the whole argument. **This is a narrowing of the design's wording and it is reported, not
quietly assumed.**

---

## 6. The other disagreements with the design and the code, each attributed

**Not a count — every one is named.** Each was grepped or measured, and what I grepped is
stated.

1. **The bundle root's key is `runs`, and neither `study` nor `members` appears in
   `study.py` at all.** The task 2 brief's sketch reads
   `if "study" in doc or "members" in doc: # read study.py for the real key`. Read:
   `study_new` writes `{"title", "authors", "runs"}` and `study_add` sets
   `runs[<name>] = {"file", "run_id"}` plus an optional `code` block. Grepped
   `grep -n "members" src/publishable/study.py` → no hits. Built on `"runs" in doc`, and
   the member names are `runs`'s keys.

2. **`endswith("run.yaml")` is a blind mutation as literally spelled.** The design and the
   task 2 brief both name it. Measured: `"main.run.yaml".endswith("run.yaml")` is `True`,
   so the mutation would still accept the bundle member and the arm it is aimed at could
   not fail. Applied as `path.name == "run.yaml"`, which is the actual reserved-name proxy;
   it failed the bundle-member arm (2 failed, 3148 passed).

3. **A failed clone has no code in Decision 14's table while Decision 7 promises it exit
   `5`.** Counted Decision 14's rows: 11 `E-REPRODUCE-*` + `E-APPARATUS-UNEXPECTED`;
   correction 29 adds `E-REPRODUCE-COMMIT-UNREACHABLE` to reach **thirteen**. A fourteenth
   for a failed clone would contradict correction 29, which task 15 owns. **Decision:
   `E-IO-FAILED` at exit `5`**, on Decision 14's own stated device (*"`E-IO-FAILED` covers
   an unreadable operand path, joining `diff`'s and `resume`'s precedent rather than getting
   a thirteenth code"*) and on the shipped `EXIT_EXTERNAL` precedent — grepped
   `grep -rn "EXIT_EXTERNAL" src/publishable/*.py`, and every existing site returns `5`
   under an **already-existing** code (`E-APPARATUS-RAISED` at `cli.py`'s probe wrapper and
   `run_status`, `freeze.py`'s credential refusal), never under one minted for the exit.
   **The count stays at thirteen.** The same code and exit are used for a failed
   `uv sync --locked`, which is the other half of code `5`'s documented clause. Flagged for
   task 14/15: § Errors will need this stated, since a reader of Decision 14's table alone
   would not find it.

4. **The `include=None` mutation cannot be exhibited by any checkout `reproduce`
   produces.** The design says a *Fixture C arm carrying a git-ignored file under `src/`*
   separates the git-aware predicate from `include=None`. Measured, twice, outside the
   repo: `git check-ignore` **without `--no-index`** — which is exactly what
   `unignored_under_hashed_trees` runs — reports **nothing** for a **tracked** path, and a
   fresh clone holds only tracked files. So end to end the two predicates agree on every
   `reproduce` checkout and the mutation would be blind. The divergence is built where it
   is reachable: an untracked ignored `src/<pkg>/.env` is dropped into the checkout before
   the comparison, and the helper that does it **asserts git really excludes it**, so the
   arm cannot go quietly blind. Both digests are computed and asserted **different** before
   either is compared against the record. The mutation then failed two arms (2 failed,
   3170 passed).

5. **§ 8 calls arm F a shipped assertion; no standalone assertion existed.** § 3.2 above,
   with every grep hit attributed.

6. **Decision 7's `clone -c` measurement does not hold on git 2.50.1.** § 4.1 above, with
   the table.

7. **Fixture L is written in the task 6 brief and its branch in the task 5 brief.** Built
   together, in task 5's commit, because they are one function and one file; task 6's
   commit carries the ruling, the footnote and the strike. Said here so a reviewer looking
   for Fixture L under task 6 finds it.

8. **`E-REPRODUCE-UNLOCKED` is deliberately not named in `design-principles.md`.** Its
   § Errors row is task 14's, and `CLAUDE.md`'s cross-document rule is one row per code; a
   code named in a normative document before its row exists is a forward reference the
   consistency pass would flag. The footnote names the behaviour and `W-ENV-UNLOCKED`,
   which does have a row (`docs/reference.md` § Warnings core reports). **Task 14 should add
   the code to that sentence when the row lands.**

9. **A fixture caught itself, twice, and both are recorded in the code.** The
   credential-redaction arm's first draft put the secret on line 1 and the YAML fault on
   line 2 — `yaml`'s error quotes one line, so the secret never reached the message and the
   arm's own `assert secret in message` control failed. And the commit-unreachable
   fixture's first draft used a fresh commit rather than `--amend`, which leaves the
   recorded SHA reachable as its own parent; its `git cat-file -e` control failed. Both are
   what *a fixture is a claim too* means in practice, and both reasons are written beside
   the fixtures rather than only here.

---

## 7. Every added assertion, and the mutation that fails IT

No existing assertion was moved or edited in any of the six tasks, and that is
**measured, not inferred** — the first draft of this paragraph asserted it from memory,
which is the *claim about other tests stated as established fact* shape:

```
$ git diff --stat 6ff19de..HEAD
 .../sdd/2026-08-24-reproduce/task-b1-report.md     |  398 ++++++
 docs/design-principles.md                          |    2 +-
 docs/superpowers/spec-defects.md                   |   24 +-
 src/publishable/reproduce.py                       |  688 ++++++++++
 tests/test_cli.py                                  |  251 ++++
 tests/test_reproduce.py                            | 1343 ++++++++++++++++++++
 6 files changed, 2703 insertions(+), 3 deletions(-)

$ git diff 6ff19de..HEAD -- tests/test_cli.py | grep -E '^-[^-]'
(no output)
```

`tests/test_cli.py` is **append-only**: zero removed lines, so no pre-existing assertion
moved. The three deletions are all in `docs/`: one replaced line in
`design-principles.md` (§ Design goals' `uv` bullet) and two in `spec-defects.md` (the
struck heading and its table row). Two of my **own** new arms were corrected mid-task
before being committed — arm F's stdout source and arm E's tree map — and both by their
own controls, which is why neither shows as a deletion. So there is no weakened-pin
question to answer: every figure below is **new**.

| Added arm | Mutation that fails it, and only it |
|---|---|
| arm E (both parametrizations) | `mkdir` one directory under the operand's parent on the `NOT BUILT` path — 2 failed, 3133 passed |
| arm F | change `W-ENV-UNLOCKED`'s clause — fails arm F **and** the pre-existing whole-stdout arm; arm F's own node id is in the run, which is what makes it the arm rather than the count |
| bundle-member acceptance | `path.name == "run.yaml"` — 2 failed, 3148 passed |
| Fixture S arm 3 | read every `run_id`-less mapping as a config — **1 failed**, 3149 passed |
| Fixture S arm 2 | print the member count instead of the names — **1 failed**, 3149 passed |
| Fixture E arm 1 + arm 2 + arm 3 | `_CLONE_CONFIG = ()` — 3 failed, 3163 passed |
| Fixture E arm 3 alone | drop the leading `git -c` (blind for arms 1–2, named in advance) — **1 failed**, 3165 passed; and add `core.eol=lf` — **1 failed**, 3165 passed |
| Fixture T arm 2 | walk up from the operand rather than the destination's parent — **1 failed**, 3165 passed |
| the git-aware-predicate arm + D1 | `hashed_files(dest, None)` — 2 failed, 3170 passed |
| D1 + D2 | replace the candidate set with a single invented cause — 2 failed, 3170 passed |
| the draft arm | refuse a draft instead of declining — **1 failed**, 3171 passed |
| Fixture I (+ its identical and edited siblings) | prefer the clone's lockfile over the byte copy — 3 failed, 3180 passed |
| the edited-byte-copy arm | use the byte copy without checking its digest — **1 failed**, 3182 passed |
| the disagreeing-bundle arm | accept the clone's lockfile in the bundle form without comparing digests — **1 failed**, 3182 passed |
| Fixture J + its control | skip the `pyproject.toml` comparison — 2 failed, 3181 passed |
| Fixture L | discard the checkout on `E-REPRODUCE-UNLOCKED` — **1 failed**, 3182 passed |

Arms with no mutation of their own, and why: Fixture K's *no directory created*, Fixture T
arm 1's *the pre-existing directory is untouched*, the commit-unreachable arm, the failed-clone
arm, the three honouring arms of Fixture S, and the negative controls
(`test_a_destination_outside_any_repository_proceeds`,
`test_a_non_draft_record_is_not_given_the_draft_line`,
`test_an_unmoved_pyproject_is_reported_identical`,
`test_a_commit_whose_lockfile_matches_the_record_is_reported_identical`). Each of these is
the **other branch** of an arm that does have one, and each was written because *testing the
refusal and never the honouring* is the shape it guards against — a control asserting only
absences would pass if nothing ran, so every one of them asserts something positive.

---

## 8. Concerns to carry forward

1. **§ Errors owes a row for a failed clone and a failed `uv sync`.** Both report
   `E-IO-FAILED` at exit `5` and Decision 14's table anticipates neither. Task 14/15.
2. **Task 11 must keep arm E passing, and this was VERIFIED rather than reasoned about.**
   A throwaway probe (written, run, deleted — not a pin) drove
   `classify_operand → prepare_checkout → verify_code_hash → restore_environment` in
   sequence against arm E's own fixture, from the same scratch cwd, for **both** operands.
   Measured: the clone happens, the checkout happens, `code_hash` reports
   `matches the record over 6 files`, `restore_environment` refuses
   `E-REPRODUCE-UNLOCKED` at exit `1` with the checkout kept — and all three tree maps stay
   byte-identical, ADDED/REMOVED/CHANGED empty, for the record operand and the bundle
   member alike. So arm E holds at task 11, including the case where the operand is a
   bundle member and the bundle directory is one of the snapshotted trees.

   **But it is a warning rather than a reassurance.** Tasks 7 and 8 write into the
   *checkout*, which is inside the destination and so invisible to the arm by design —
   and task 7's write-back is the dangerous one: Decision 11 verifies the written config
   with `parameters_hash`, and if that write is ever sited relative to the **operand**
   rather than the destination, arm E is the only thing standing between it and a silently
   modified run directory. Its editor is NONE, so a failure there is a finding to report,
   not an assertion to relax.
3. **The leading `git -c core.autocrlf=false` is unarmed by any hash on this git version.**
   Arm 3 asserts it structurally. A future slice tempted to drop it should read § 4.1
   rather than conclude from a green suite that it does nothing.
4. **`_uv_sync` is stubbed in every success arm.** Nothing in this batch proves a real
   `uv sync --locked` ever succeeds, and nothing can until `publishable` is published —
   which is the sibling `spec-defects.md` entry deliberately left open.
5. **`prepare_checkout` now takes the `Record`, not the record dict.** Tasks 7, 8 and 13
   need `operand.path` for the same reason task 5 does; the signature was widened in task 3
   so that the wrong-walk-up mutation was buildable at all.
