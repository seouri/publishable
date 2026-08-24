# H9c tasks 11–15 — report

Five commits, one per task, in order.

| Task | Commit | What it is |
|---|---|---|
| 11 | `1ea639b` | Dispatch: `OPERATION_COMMANDS`, guard-pin arm B, four arity arms |
| 12 | `6b969ea` | The config-operand form (Decision 13) |
| 13 | `a69ef15` | The closing transcript and the `run.yaml` form end to end |
| 14 | `386aa3f` | `spec-defects.md` |
| 15 | `01b882d` | The four documents, `CLAUDE.md`, § Executability, both passes |

**Suite, read from each run's own summary line, full and unfiltered:**

| At | Passed | Skipped | xfailed | Added |
|---|---:|---:|---:|---:|
| baseline `caf6737` | 3218 | 1 | 2 | — |
| task 11 `1ea639b` | 3222 | 1 | 2 | +4 |
| task 12 `6b969ea` | 3226 | 1 | 2 | +4 |
| task 13 `a69ef15` | 3230 | 1 | 2 | +4 |
| task 14 `386aa3f` | 3230 | 1 | 2 | +0 (records only) |
| task 15 `01b882d` | 3230 | 1 | 2 | +0 (documents only) |

`uv run ruff check .`, `uv run ruff format --check .` and `uv run mypy` clean at every commit. Every
mutation below was run against the **full, unfiltered** suite and every count is read from that run's
own summary line. Reverts were performed by restoring a pre-mutation copy kept **outside** the
repository and verified by **re-running the tests the mutation had failed**; `git checkout -- <file>`
was never used.

---

## 1. What `reproduce new` actually does — MEASURED, not predicted

All four invocation shapes were driven through the **real console script**
(`uv run --directory <repo> publishable …`) from a scratch directory **outside this repository**,
which was empty before the four calls and empty after them (`ls -a` both times).

| Invocation | Exit | Output |
|---|---:|---|
| `publishable reproduce` | **2** | `` `reproduce` takes exactly one path and no flags `` |
| `publishable reproduce a b` | **2** | the same line |
| `publishable reproduce --json` | **2** | the same line |
| `publishable reproduce new` | **1** | `  error   E-IO-FAILED          new` / `          could not be read as YAML: [Errno 2] No such file or directory: 'new'` |

**All four match the design's disclosure item 5 exactly**, including the one it derived rather than
ran: exit `2` → `1` at `reproduce new`, and the identifier is new. Nothing was corrected. The first
measurement attempt was wrong for a reason worth recording: zsh does not word-split an unquoted
parameter, so `publishable $args` sent `"reproduce a b"` as **one** token and printed
`unknown command \`reproduce a b\``. Re-run with `${=args}`; the table above is the second run.

**Pinned, not only disclosed**, by `test_h9c_reproduce_new_reaches_real_argument_handling_not_a_roadmap_notice`,
which asserts the exit code **and** the identifier and the two absences (`unknown command`,
`is specified but not built`) — because a mutation dropping `reproduce` from `OPERATION_COMMANDS`
while leaving the handler would print `unknown command` at the *same* code as the arity arm.

**Nothing rests on `_dispatch`'s branch order** (correction 18). Every arm asserts the outcome.

## 2. Guard pins: one edited by its authorized editor, one re-run, ONE STOPPED

**Arm B — EDITED, by its sole authorized editor (plan task 11), to the advance spec and no further.**
`assert ("reproduce", "NOT BUILT") in tables["Command"]` → `("reproduce", "built")`, **plus** the new
`assert ("list-templates", "NOT BUILT") in tables["Command"]` row-presence line (correction 20). The
`set(NOT_BUILT_COMMANDS)` equalities beside it were **not** edited. Mutation M11-2 (flip the document
cell back to `NOT BUILT`) → **2 failed, 3220 passed**, arm B and
`test_reference_cli_tables_match_what_the_cli_does[Command]`.

**Honest note on the `list-templates` line:** it is an addition, and it is **dominated** by the
`set(NOT_BUILT_COMMANDS)` equality below it — any mutation that removes or re-marks that document row
fails the equality too, so no mutation fails the added line *alone*. It is carried because correction
20 requires the marked probe to survive, and reported as dominated rather than claimed as coverage.

**Arm E — re-run against the dispatching command, NOT edited.** Both parametrizations
(`test_h9c_arm_e_reproduce_writes_nothing_outside_its_destination[record]` and `[bundle_member]`)
pass at `1ea639b` and at every commit after it: ADDED / REMOVED / CHANGED **all empty** over all three
trees — the run directory, the operand's own tree, and the source repository — with the command now
cloning, checking out, recomputing `code_hash` and refusing `E-REPRODUCE-UNLOCKED` inside that window.

**H5a arm D / H6b arm R — STOPPED, REPORTED, AND NOT EDITED. This is the finding of task 15.**
`test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text[REFERENCE]` pins, **byte for byte and
whole-line**, every line of `reference.md` carrying a worked-example literal. § Reproducing on another
device's **step 2** is one of those lines, because it carries the run ID
`my-study_run_2026-08-06T14-02-11Z_8e21ab3`. Correction 13 requires that sentence's
*"it can't collide with an existing checkout"* to be narrowed — and its authorized editor is **NONE**,
and my brief does not name me.

Measured, not reasoned: the first cut of task 15 edited that line and the full suite came back
**1 failed, 3229 passed**, the single failure being that arm's `REFERENCE` parametrization.

**What was done instead**: the line was restored **verbatim**, and both narrowings were written as
their own paragraph immediately after item 7, saying what they replace. The arm is green and was not
touched. **The post-edit state a controller would need to authorize**, if it prefers the sentence
corrected in place, is:

```
2. Clones into a directory derived from the repository name and run ID
   (`my-study_run_2026-08-06T14-02-11Z_8e21ab3/`), under the directory you're standing in, and
   checks out that exact commit as a detached HEAD. *The only git you didn't type* — it is two
   invocations, a clone and a detached checkout, each passing `-c core.autocrlf=false`. No
   `--into`: the destination is derived, so you never name it. Derived is not unique: a second
   `reproduce` of the same record derives the same name and refuses rather than overwriting
   (`E-REPRODUCE-DEST-EXISTS`), and a destination inside a git repository is
   `E-REPRODUCE-DEST-IN-REPO`.
```

with `_H5A_ARM_D_REFERENCE_LINES`' matching entry replaced. **No literal moves** — the run ID is
byte-identical in both — which is why the arm's *stated* property (the worked example's own numbers)
is not what would move; what would move is the whole-line capture that arm deliberately uses.

## 3. Every § Errors row touched, its every-emit-site check, and the table's scope sentence

**The count is thirteen and it carries its noun** (correction 29): twelve `E-REPRODUCE-*` codes and
one `E-APPARATUS-*`, thirteen rows. Verified as a **bijection**, mechanically, not by counting:

```
$ grep -rho 'E-REPRODUCE-[A-Z-]*\|E-APPARATUS-UNEXPECTED' src/publishable/ | sort -u        # 13
$ grep -o 'E-REPRODUCE-[A-Z-]*`* |$\|E-APPARATUS-UNEXPECTED`* |$' docs/reference.md \
      | grep -o 'E-[A-Z-]*' | sort -u                                                        # 13
$ diff  →  IDENTICAL
```

**Can-fail proof:** the same row extractor run for `E-REPRODUCE-NOSUCH` returns `0`, so the extractor
is capable of reporting a code with no row.

### 3a. Placement — and it DISAGREES with design Decision 14

Decision 14 rules *"all twelve go to § Errors **core raises** — none is reported by `validate`."*
**Eleven of the twelve are never raised.** They are appended to a fresh `Collector` and printed;
`grep -n 'raise' src/publishable/reproduce.py` returns only the `KeyboardInterrupt` re-raise and the
`raise` inside the `E-GIT-NO-REPO` catch. Decision 14 read the section **title** rather than either
table's **scope sentence**:

- § Errors core raises' own intro: *"**Two rows in this table are not raises**, and the `Type` cell
  says so"* — and it justifies exactly those two, the dirty gate and the empty-file-list gate, **both
  inside the run command's own sequence**. Adding twelve more would make that sentence read *fourteen*
  and would strand its justification.
- § Errors `validate` reports' own intro: *"these are the codes a **command** reports."* That is where
  H8b's eight `E-FREEZE-*`, H9b's fourteen `E-RESUME-*` and `diff`'s config-operand row **already
  live** — every one of them a command-level refusal through a fresh `Collector`, at a command that is
  not `validate`.

**Followed the scope sentence and the nearest sibling.** Twelve `E-REPRODUCE-*` rows are in § Errors
`validate` reports; `E-APPARATUS-UNEXPECTED`, which **is** raised (`ContractError`, in
`apparatus.check_expected`), is in § Errors core raises beside the other five `E-APPARATUS-*` rows.
That section's scope sentence gained four sentences saying so explicitly, so the next reader does not
re-derive it.

### 3b. The thirteen new rows, each checked against every emit site

Sites read out of the code, not out of the brief.

| Code | Emit sites in `src/` | Row covers |
|---|---|---|
| `E-REPRODUCE-OPERAND` | `_refuse_operand` called from **four** branches (directory; non-mapping parse; `run_id`-less mapping carrying `provenance`/`results`; neither) | all four, named as *"four sites, one code"* with the remedy stated once |
| `E-REPRODUCE-BUNDLE` | 1 | + the member listing |
| `E-REPRODUCE-NO-REMOTE` | 1 | + exit `1` and why it is not `5` |
| `E-REPRODUCE-DEST-EXISTS` | 1 | + the second-`reproduce` route |
| `E-REPRODUCE-DEST-IN-REPO` | 1 | + the walk-up is from the destination's parent |
| `E-REPRODUCE-COMMIT-UNREACHABLE` | 1 | + **exit `5`**, read off `Refused(EXIT_EXTERNAL)` and not off Decision 14's table, which does not carry this code at all |
| `E-REPRODUCE-CODE-HASH` | 1 | + the checkout is kept, + the `draft` decline |
| `E-REPRODUCE-UNLOCKED` | 1 | + the checkout is kept |
| `E-REPRODUCE-LOCKFILE-EDITED` | 1 | + the clone's lockfile is left untouched |
| `E-REPRODUCE-LOCKFILE-UNREACHABLE` | 1 | + the bundle route |
| `E-REPRODUCE-CONFIG-WRITEBACK` | 1 | + why the check is blind to the blanking |
| `E-REPRODUCE-EXPECTED-EXISTS` | 1 | + the **only** reachable route is a committed file |
| `E-APPARATUS-UNEXPECTED` | `apparatus.py` (the raise) + `cli.py`'s run-start containment | both: the raise, the `1`/`4` split, the resume case, and `E-APPARATUS-CHANGED` winning when both would fire |

### 3c. FOUR EXISTING rows were narrower than their code and were widened

This is the half the brief's "thirteen rows" does not cover, and it is where the whole-branch Majors on
four sub-slices have lived. Found by extracting every `c.error(...)` first argument in `reproduce.py`
plus task 9's new `cli.py` site, then grepping `reference.md` for each one's row.

1. **`E-IO-FAILED` — and the brief's instruction names something that does not exist.**
   `grep -n 'E-IO-FAILED' docs/reference.md` returns **exactly one** hit, and it is **not a table
   row**: it is one sentence in § Exit codes and diagnostics reading *"is reported as `E-IO-FAILED`
   and exits `1`."* Commit `142d3e1`, which the task-14 amendment says "already widened that row",
   edited **the plan**, not the document. The sentence is now **false at three sites** — a failed
   `git clone`, and `uv sync --locked` failing in either operand form, all `EXIT_EXTERNAL` at exit
   `5`. Widened to name every site rather than a count: ten in `reproduce.py` (six at exit `1`, three
   at exit `5`, plus the `read_record_file` fallback) and **one on the shipped `run`/`draft`
   command** — a malformed `configs/<name>/apparatus.expected.json`, at exit `1`. **No fourteenth code
   minted.** Whether it also earns a table row is a judgement; the sentence was widened rather than a
   row minted, because a row would be a second place for one code, and this is reported so a reviewer
   can rule the other way.
2. **`E-GIT-NO-REPO` — *"Six paths reach it"* → seven; *"Two sites catch it by code"* → three.**
   `reproduce`'s config form catches it by code and **re-reports it under the same code** through its
   own `Collector` at exit `1`. **And its closing sentence went false in the same edit**: *"This is
   why a config outside every repository prints `✓ config valid` and refuses only at `run`"* — it
   refuses at `reproduce` too. Corrected in the same edit rather than left as a displaced antecedent,
   which is the shape H9a's Major 1 was.
3. **`E-UPSTREAM-RECORD-MISSING`/`-UNREADABLE`/`-VERSION` — *"all four call the identical reader"* →
   five.** `classify_operand` is `read_record_file`'s fifth caller and **re-reports whichever code the
   reader raised, under its own code**, rather than flattening it into `E-REPRODUCE-OPERAND` — pinned
   by the shipped `test_a_record_whose_schema_version_this_build_cannot_read_keeps_its_own_code`.
4. **`E-TEMPLATE-LOAD` — *"every command resolving a template meets `discover_local` at load"*.**
   True and now incomplete: `reproduce` resolves the template of the checkout **it just made**, in
   that checkout's own `templates/`, and its fallback (`exc.code if isinstance(exc, PublishableError)
   else "E-TEMPLATE-LOAD"`) makes this code stand for a fault `discover_local` did not itself name.
   Both stated.

**Two more codes were checked and needed nothing.** `E-PLUGIN-LOAD` — not reached from `reproduce.py`
(grepped: no hits). `E-CODE-DIRTY` — `reproduce` does not gate on a dirty tree; it *reports* an
uncommitted `pyproject.toml` and does not refuse, and § Errors' row is about the run command.

### 3d. Exit code `5`

The brief says *"gains its first reader"*; correction 29 says *second*; § Errors' shipped
`E-APPARATUS-RAISED` row already names **four** surfaces reaching `5`. **So no count is quoted.**
§ Exit codes now names the sites: `reproduce` reaches `5` at three — a failed `git clone`, a recorded
commit the clone does not hold (`E-REPRODUCE-COMMIT-UNREACHABLE`), and `uv sync --locked` failing in
either operand form — and says *"first reader"* would be right about the **clause** and wrong about
the **code**. **No exit code is minted.**

## 4. Every filing, its reproduce command, and its owner

All in `docs/superpowers/spec-defects.md`, commit `386aa3f`. Each heading quoted.

### Filed (four)

1. **`## OPEN — a tracked `.gitattributes` carrying a `text`/`eol` attribute makes `code_hash` a
   property of how a working tree was MATERIALIZED rather than of the commit — **Owner: unassigned,
   with the reason (no remaining slice has `hashes.py` or § How the three are computed as its
   surface)**`**
   **Reproduced by this task**, outside the repository, on `git version 2.50.1 (Apple Git-155)`:
   ```bash
   mkdir -p ga/orig/src/pkg && cd ga/orig
   printf 'x = 1\ny = 2\n' > src/pkg/mod.py
   printf '* text eol=crlf\n'  > .gitattributes
   git init -q . && git add -A && git commit -qm init
   cd .. && git -c core.autocrlf=false clone -c core.autocrlf=false -q ./orig ./clone
   # code_hash(orig)  = sha256:6bac8c5…   b'x = 1\ny = 2\n'
   # code_hash(clone) = sha256:80ffbc4…   b'x = 1\r\ny = 2\r\n'
   ```
   **The digits are NOT the design's.** Design § 0.5 records `d37416e` against `0cc6ddd` from its own
   fixture; batch 1's sibling measurement got `79baf6d`/`62f7769` from a third. The filing states its
   own two, labels them as this fixture's, and makes the **inequality** the load-bearing claim — a
   filing whose recipe yields different numbers than it states is a false claim about the code.
2. **`## OPEN — a study bundle carries no lockfile, so a bundle member whose project never committed
   one cannot be reproduced from the bundle alone — **Owner: unassigned, with the reason (`study
   add`'s bundle contents are H8c's surface, and H8c is complete)**`**
   Reproduce: `uv run pytest tests/test_reproduce.py -k bundle` — `_bundle_member` asserts the state
   (the member's `uv_lock` reads `environment/uv.lock`, no `environment/` exists beside it,
   `uv_lock_hash` is non-null) before every arm that uses it. The check its closer must make is
   stated: copy the lockfile in, or **redact** `provenance.environment.uv_lock` the way
   `input_manifest` already is.
3. **`## OPEN — `provenance.environment` names no `pyproject.toml`, though `run` writes
   `environment/pyproject.toml` — **Owner: unassigned, with the reason (H6 is complete and no
   remaining slice has `provenance` as its surface)**`**
   Reproduce, both halves: `grep -n "pyproject.toml" src/publishable/cli.py` (the run-start write and
   the fixed-file list) against `grep -n "uv_lock\|pyproject" src/publishable/provenance.py` (**no
   hits**). A fourth environment key is refused by ruling (H6a Ruling E), so what is filed is the
   **naming** gap, not a hash.
4. **`## OPEN — `templates/registry.py`'s `_claims` docstring says *"the two cross-module imports are
   the whole set"* and there are **three** — **Owner: unassigned, with the reason (no remaining slice
   has the template registry as its surface)**`**
   Reproduce: `grep -rn "_claims" src/publishable/` — three real imports (`validate.py:43`,
   **`freeze.py:42`**, `generators/experiment.py:10`); `reproduce.py:951` and `:1028` are **prose**,
   so H9c is not a fourth. Remedy is **deletion**, not `two`→`three`.

### Amended, declined and re-owned (five)

5. **`## OPEN — two specified readers of `required_env` belong to unbuilt commands`** — **AMENDED**,
   not struck: the `reproduce` half is discharged for core `generic` and a project-local
   `templates/**`, and **narrowed** for an installed template.
6. **`## `UpstreamLedger.record` copies a missing hash as `None` rather than refusing it`** —
   **DECLINED and RE-OWNED to unassigned, with the reason.** Its ground is false:
   `grep -n "upstream\|UpstreamLedger\|read_upstream" src/publishable/reproduce.py` → **no hits**.
7. **`## OPEN — `diff`'s `uv.lock` row prints two digests and never names the package whose pin moved
   — **Owner: H9**`** — **RE-OWNED to H9d**, per design § 4; Decision 3 supplied the input it waited on.
8. **`## RESOLVED in S4c Task 9: `statistics.contrasts` added to `_check_shape`'s nested pass …`** —
   its `resolve_contrasts` precondition's **third and last** command discharged:
   `grep -n "resolve_contrasts\|_prepare_run\|_execute_prepared" src/publishable/reproduce.py` → no
   hits at all.
9. **`## OPEN — `_dispatch`'s branch order is documented as load-bearing and is constrained by no
   test …`** — amended: `NOT_BUILT_COMMANDS` is down to three keys, the order is still unpinnable, and
   the obligation now falls to **H9d alone**.
10. **`## NOT A DEFECT — this file holds **eight** H9-owned entries …`** — an appended amendment
    naming what happened to each of H9c's four rows.

Every owner is a **fact with a reason**; the *"whichever slice next touches X"* form is used nowhere.
Nothing was deleted; every closure is a strike or an appended amendment.

## 5. § Executability on this build — the re-derivation, and the design's own reason is FALSE

One dated entry, *"Measured on 2026-08-24 against commit `386aa3f`"*.

**Design § 7 argues:** *"None of the nine configs is a run record, so none of them is an operand
`reproduce` accepts."* **That is false at HEAD.** Task 12 built Decision 13's config form, and
`reproduce` accepts a **config file** — all nine of those configs *are* config files. The design and
the entry cannot both be right, so the entry derives the verdict from four things instead:

- `reproduce` runs at no `validate` and is invoked from no step, so row 1 (8 of 8) cannot move.
- **The behaviour change to `run` was checked in the code, not cited from the handover.** `cli.py`
  builds `expected_path = config_path.parent / "apparatus.expected.json"` **inside** the branch that
  has already resolved a declared `apparatus_probe` — read at `cli.py`'s run-start probe block. None
  of the nine declares a probe (`generic` is the template they validate against), so none reaches the
  read at all, and `E-APPARATUS-UNEXPECTED` is unreachable for all nine.
- Rows 2 and 3 are untouched, and both were grepped rather than asserted:
  `grep -n "upstream\|UpstreamLedger\|read_upstream" src/publishable/reproduce.py` and
  `grep -n "resolve_contrasts\|_prepare_run\|_execute_prepared" src/publishable/reproduce.py` — **no
  hits** either time.
- Row 4 does not move because **accepting a config as an operand is not a config executing**:
  `reproduce` prepares an environment and stops, executing no step and reporting no result.

**The four-row table is repeated character for character.** Extracted by the two independent methods
the H8a and H9a entries describe — the walk from the last `| Figure | Count | Visible to` header, and
a fixed six-line slice from the same index — both six lines, `diff`-ed to **empty**, and verified
after the append: `lines[idx_prev:idx_prev+6] == lines[idx_new:idx_new+6]` is `True`. Its cells still
name **H8a**. **No fifth number is minted.** `docs/feasibility-llm-growth-studies.md` is the only file
H9c touched there, and only in that section.

## 6. Every sweep: command, file list, and can-fail proof

**No sweep's output was filtered. Every sweep names its files.** The file list for the document sweeps
is the four documents named individually, plus `CLAUDE.md` and the feasibility analysis where stated —
`*.md` no longer means what it used to.

### Sweep A — the mechanical pass

A throwaway script (written for this pass, not kept) over
`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`,
`docs/feasibility-llm-growth-studies.md`. Checks: `#anchor` resolution, relative-link and
cross-file-anchor resolution, duplicate anchors within a file, table row/separator column counts,
empty rows, trailing whitespace, tabs, and seven invisible code points. **Fenced blocks skipped.**

**Result: 3 hits, all three attributed and none a defect** —
`docs/reference.md:630`, `:1839`, `:3773` report `ROW COLS n != m`. Each is a row whose cell carries an
inline `|` inside a backticked span (` \| `, `` ` | any | ` ``, a `generate` invocation). **All three
are pre-existing**: the identical three rows report at `HEAD` before this task's edits
(lines 625, 1821, 3753, shifted only by insertions above them).

**Can-fail proof, by injection and revert, six check kinds:**

| Injected | Reported |
|---|---|
| `[a broken link](#no-such-anchor-here)` | `BAD ANCHOR #no-such-anchor-here` |
| `[a broken file](docs/nope.md)` | `BAD LINK docs/nope.md` |
| a line with a trailing space | `TRAILING WS` |
| a tab | `TAB` |
| a second `## CLI reference` heading | `DUPLICATE ANCHOR #cli-reference (also line 3755)` |
| a 3-column header with a 2-column separator | `SEP COLS 2 != header 3` |

Reverted from a copy kept outside the repository and re-run: back to the same 3.

### Sweep B — is `reproduce` still described as unbuilt anywhere?

```
grep -n -E 'NOT BUILT|not yet built|specified but not built|unbuilt' \
  README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md \
  CLAUDE.md docs/feasibility-llm-growth-studies.md
```
**Every hit attributed.** `reference.md:3765/3788/3789` are `demo`, `docs`, `list-templates` — the
three names still in `NOT_BUILT_COMMANDS`. `reference.md:4271`/`:4321` are § Package layout's
`docs.py` marker and the sentence that reads it. `reference.md:437`, `:1123`, `:3816`, `:3960`,
`:3972-3974` are about generators, the importable surface, and exit code `2`. `CLAUDE.md:25/100/177/
469/860/991/1066` are the slice history and § Misreadings. Every
`feasibility-llm-growth-studies.md` hit is inside a **dated** entry describing an earlier commit, plus
its own `io.reuse_from` history — the development record is appended to, never retro-edited. The only
two hits that name `reproduce` are **this slice's own new entries** describing the change.
**Can-fail proof:** the same command with `-c` for `reproduce` returns 4/4/1/54/8/23 — non-zero in
every file, so the file list and the reader are live.

### Sweep C — the code↔row bijection

Given in § 3 above, with its can-fail proof (`E-REPRODUCE-NOSUCH` → `0`).

### Sweep D — did any worked-example figure move?

```
git diff -- README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md \
  | grep -E '^[-+]' | grep -E '0\.581|0\.488|0\.661|0\.607|0\.517|0\.683|0\.412|0\.347|0\.477|0\.026|8e21|1a2b|3d8a|6b1f|2f5c8d0|228|240|run_2026-08-0'
```
**Two hits, one line, attributed**: the `-`/`+` pair for § Reproducing step 2 during the first cut.
That edit was **reverted** (§ 2), and the sweep now returns nothing. **Can-fail proof:** the same
filter over the whole of `reference.md` returns **30** lines. **No interval was narrowed and no hash
prefix moved.**

### Sweep E — `×` versus `x`

`git diff | grep '^+' | grep -E '[0-9] x [0-9]'` over all six files — **no hits**. No line this task
added uses an ASCII `x` for multiplication.

### Sweep F — `reproduce` mentions in the four documents, all 60-odd read

Two **defects found and fixed**, both pre-existing:
- `reference.md` § The two files: *"a mid-run command (`freeze`, and `resume` **when it lands**)"* —
  `resume` landed with H9b. Clause **deleted**, not rewritten.
- `reference.md` § The two files: *"`reproduce` accepts either — a config to run fresh, or a
  `run.yaml` to **re-run** exactly what that run did."* `reproduce` **stops** rather than running, per
  § Reproducing's own sentence and § CLI reference's `Does` cell. Rewritten to say what each operand
  gets and that it stops either way.

One framing corrected after the first cut, on review: the appended paragraph originally called both
of its items *narrowings*. **Plan correction 1 says the document's *"the only git operation"* is about
what the USER typed and that the design keeps that reading** — so that sentence is not wrong, and
framing the two-invocation count as a correction of it would have been correcting a true claim. The
paragraph now reads *"one narrowing and one addition"*, and the addition says in as many words that it
corrects nothing.

One hit checked and **left alone, deliberately**: `reference.md` § Warnings core reports'
`W-ENV-UNLOCKED` row, *"`reproduce` will not be able to restore it"* — that clause is **guard-pin
arm F**, editor NONE, and it is now true rather than aspirational (`E-REPRODUCE-UNLOCKED` ships).
Deleting a true claim is not licensed.

## 7. Cross-document pass — each class, and what it found

| Class | Result |
|---|---|
| The shared worked example | **Nothing moved** — Sweep D, plus the H5a arm D pin, which is the mechanical enforcement of exactly this class and which stopped one edit |
| Config completeness | No config field was added, removed or renamed by this slice. `apparatus.expected.json` is a file beside the config, not a config key |
| Enum comments | None touched; no enum gained or lost a value |
| Schema fields in prose | `provenance.git.remote`/`.commit`, `provenance.environment.uv_lock_hash`, `config.metadata.name`, `provenance.apparatus.facts` are the fields the new prose names — all four exist in § What `run.yaml` records' example |
| Declared vs. derived | The **destination** is derived and is named nowhere as an input; the new prose says so at every mention and no passage shows a `--into` |
| Versions | Untouched |
| Prevented mistakes | Untouched — `experimental-designs.md` § Mistakes core prevents gained and lost nothing |
| The `Status` column | Moved in **task 11**, of necessity (§ 8 below), and bound in both directions by `test_reference_cli_tables_are_parsed_at_all` and `test_reference_cli_tables_match_what_the_cli_does[Command]` |

## 8. Where the briefs, the design and the plan disagree with the code

**Not a count. Six, each named, each measured.**

**(a) Task 15 could not own § CLI reference's `reproduce` row, and task 11 had to.** The brief gives
task 15 that row. Guard-pin arm B's authorized post-edit state is
`assert ("reproduce", "built") in tables["Command"]`, which **parses that document table** — so the
`Status` cell had to flip in the dispatch commit or the branch was red. Measured: flipping it back at
`1ea639b` gives **2 failed, 3220 passed**. Task 11 took the `Status` cell only; task 15 took the
`Does` cell.

**(b) `command_reproduce` did not exist, and task 11's brief assumes it.** Built in task 11 as the
real chain rather than a stub — batch 1's concern 2 and batch 2's § 1 had both driven that chain as
throwaway probes. The `ConfigOperand` arm was an explicit `NotImplementedError` naming plan task 12
for exactly one commit — **never a silent fall-through returning `EXIT_OK`** — and no assertion pinned
it. Replaced in `6b969ea`.

**(c) Decision 13's *"Decision 3's ranking"* cannot run in the config form.** That ranking's authority
is the recorded `uv_lock_hash` and its preferred carrier is the run directory's byte copy; a config
has **neither**. `restore_environment` takes a `Record` and reads `operand.doc`. So the config form
reports the repository's own lockfile, its computed digest, and **the absence of anything to rank it
against** — a fourth honest absence beside the three not-verified lines, on Ruling AA's own terms
(neither source preferred silently). Both branches are armed.

**(d) A config outside every repository needed an answer no decision gives.** `find_repo_root`
**raises** `E-GIT-NO-REPO` rather than returning `None`. Reused that existing code — caught **by
code**, the way `validate._check_data` and `study._refuse_if_in_repo` catch it, and re-reported
through the collector so the redaction pass still applies. **Nothing minted**; the count stays at
thirteen. Cost: `E-GIT-NO-REPO`'s row needed three separate corrections (§ 3c item 2).

**(e) Design § 7's executability reason is false at HEAD.** § 5 above.

**(f) `E-IO-FAILED` has no § Errors row, so *"widen the row"* names nothing.** § 3c item 1.

Two smaller ones. **Batch 2's handover item 2 says Decision 12's document narrowing is "task 13's
prose"; task 15's brief owns § Reproducing on another device.** Written in task 15, resting on batch
2's measurement (`get_template` returns `None` for an installed template, and the plugin is installed
in the clone's environment). **And the dispatch's "Task 15 (filings)" heading lists four filings while
task 15's brief says *Must not touch: `spec-defects.md` (task 14)*.** All filings are in task 14's
commit.

## 9. Every added or moved assertion, and the mutation that fails IT

**One shipped assertion moved: guard-pin arm B, by its authorized editor.** Everything else is an
addition. `git diff caf6737..HEAD -- tests/ | grep -E '^-[^-]'` returns **two** lines, both accounted
for: arm B's edited line, and `_prepare_env`'s unpack of `prepare_env`'s now-three-value return (a
helper call, not an assertion — every arm below it is unchanged and all pass).

| Assertion | Mutation that fails it |
|---|---|
| **ARM B (MOVED)** `("reproduce", "built")` + the `list-templates` probe | **M11-2** flip the document cell back to `NOT BUILT` → **2 failed, 3220 passed** |
| the four arity/dispatch arms | **M11-3** remove `reproduce` from `OPERATION_COMMANDS`, handler kept → **5 failed, 3217 passed**: all four, plus `test_reference_cli_tables_match_what_the_cli_does[Command]`. The `reproduce new` arm failed on `assert 2 == 1` — `unknown command` at `EXIT_INVOCATION` instead of `E-IO-FAILED` at `EXIT_WRONG`, which is the code-**and**-identifier claim |
| `test_h9c_reproduce_with_a_flag_is_an_invocation_error` | **M11-1** replace the guard with a bare `len(rest) != 1` → **5 failed, 3217 passed**. **Attributed, not counted**: the other four (`test_operation_commands_take_no_flags`, `draft`, `dry-run`, `resume`) are pre-existing siblings on the **same shared arm**, so this mutation is not evidence the new arm adds coverage — it is evidence the new arm is wired to the rule |
| Fixture N (three not-verified lines, each asserted separately) | **T12-1** print two of the three → **1 failed, 3225 passed**, Fixture N alone |
| the record-form and config-form closing triples | **T13-1** print `validate`/`dry-run`/`run` in the wrong order → **2 failed, 3228 passed**. Both assert an **ordered triple** of whole lines, which no membership or substring assertion could fail |
| the end-to-end apparatus arm | **T13-2** omit the block for a non-null `provenance.apparatus` → **2 failed, 3228 passed** (this arm and Fixture O arm 1) |
| H5a arm D | **not mutated — it FAILED for real** (§ 2), which is stronger evidence than a mutation |

**Arms with no mutation of their own, and why.** The walk-up arm (driven from a second, unrelated git
repository) and the no-repo arm are the two branches of one decision and each asserts the other's
negative; the lockfile-present and lockfile-absent arms are likewise a pair, and the digest in the
present branch is **computed in the test**. Fixture F's clone/HEAD/`environment`-absent assertions are
covered by the shipped `path.name == "run.yaml"` mutation from batch 1 (the bundle form would not be
accepted at all).

## 10. Every claim about other code or other tests, with what was grepped

Reported as hits, attributed. **Not a count.**

| Claim | Grep | Every hit |
|---|---|---|
| task 6 already wrote the § Design goals footnote | `git show 8606984 -- docs/design-principles.md` | one changed line, the `uv` bullet, carrying *"'Not optional' describes `reproduce`'s obligation, not `run`'s"*. **Task 15 owed nothing** |
| `E-IO-FAILED` has no § Errors row | `grep -n 'E-IO-FAILED' docs/reference.md` | **one** hit, § Exit codes' prose sentence. Not a row |
| `reproduce` is not a fourth importer of `_claims` | `grep -rn "_claims" src/publishable/` | three real imports; `reproduce.py:951`, `:1028` are docstring prose |
| `reproduce` walks no lineage | `grep -n "upstream\|UpstreamLedger\|read_upstream" src/publishable/reproduce.py` | **no hits** |
| `reproduce` enters no phase of `run`'s sequence | `grep -n "resolve_contrasts\|_prepare_run\|_execute_prepared" src/publishable/reproduce.py` | **no hits** |
| the expectation read is gated on a declared probe | read `cli.py`'s run-start probe block | `expected_path` is built **after** `_probe_for(declared_probe)` succeeds, inside that branch |
| `provenance.environment` names no `pyproject.toml` | `grep -n "uv_lock\|pyproject" src/publishable/provenance.py` → no hits; `grep -n "pyproject.toml" src/publishable/cli.py` → the run-start write and the fixed-file list; `grep -n 'uv_lock' src/publishable/cli.py` → the two recorded keys | claim holds |
| `E-FREEZE-*`/`E-RESUME-*` live in § Errors `validate` reports | `grep -n 'E-FREEZE-\|E-RESUME-' docs/reference.md` | every row is in that section's table; **none** is in § Errors core raises |
| the three column-count hits are pre-existing | ran the checker against `git show HEAD:docs/reference.md` | the same three rows, at 625/1821/3753 |
| the `.env` line's asserted substring survives generalizing the origin phrase | `grep -n 'env.example' tests/test_reproduce.py` | `:1677` asserts `"carries no \`.env.example\`"`, which the parameterized message preserves verbatim |
| **`prepare_env`'s three-value return has exactly two unpackers** | `grep -rn 'prepare_env' tests/ src/ docs/` | `src/publishable/reproduce.py:1526` (the new caller) and `tests/test_reproduce.py:1642` (the helper). The fifteen `_prepare_env(...)` call sites all go through that helper; `reproduce.py:931` is the `def`, `:1042`/`:1476`/`:1490` and `test_reproduce.py:1701`/`:1859`/`:1920`/`:1921` are prose, `test_reproduce.py:36` is the import, and `spec-defects.md:6901` names it in a filing. **No third unpacker exists** |

## 11. Concerns

0. **ESCALATION — this is the one item that needs a controller ruling, and it is the headline of this
   report rather than one concern among many. `reference.md` § Reproducing on another device's step 2
   still states something false** — *"the destination is derived, so it can't collide with an existing
   checkout"* — with the correction four lines below it. A document that says a thing and unsays it
   four lines later is worse than one that says it right, and shipping that was not a choice this task
   was entitled to make on its own. **Two options, both priced:**
   **(a) Authorize an edit to `_H5A_ARM_D_REFERENCE_LINES`' step-2 entry.** The replacement text is
   written out verbatim in § 2 above. **No literal moves** — the run ID
   `my-study_run_2026-08-06T14-02-11Z_8e21ab3` is byte-identical in it — so the arm's own stated
   property (*"the worked example's own numbers, as raw text"*) does not move; what moves is the
   whole-line capture, which is incidental to what the arm protects. Cost: one guard-pin arm edited by
   a task its docstring does not name, which is the thing this project's rule exists to prevent.
   **(b) Keep the correction-paragraph form as shipped.** Cost: `reference.md` carries a false
   normative sentence with its correction below it, permanently.
   **This task took (b) provisionally, because self-authorizing (a) is the one move the dispatch
   forbids outright.** It is stated here so the choice is made by whoever can make it.

1. **H5a arm D / H6b arm R is the live blocker, and it is a real one.** Correction 13's narrowing of
   § Reproducing step 2 is **not in that sentence**; it is in a paragraph below it, and the sentence
   still reads *"it can't collide with an existing checkout"*. A document that states something and
   corrects it four lines later is worse than one that states it right. **A controller ruling
   authorizing an edit to `_H5A_ARM_D_REFERENCE_LINES`' step-2 entry is what closes this** — the
   replacement text is written out in § 2 and moves **no literal**. Left as it is rather than
   self-authorized.
2. **The § Errors placement disagrees with design Decision 14** (§ 3a). If the whole-branch gate
   prefers Decision 14's reading, the twelve rows move as a block from § Errors `validate` reports to
   § Errors core raises — and that table's *"Two rows in this table are not raises"* paragraph and its
   two-gate justification must move with them, which is why the scope sentence was followed instead.
3. **`E-IO-FAILED` still has no table row**, only a widened sentence (§ 3c item 1). Ten sites in
   `reproduce.py` and one on the shipped `run` command now hang off one paragraph in § Exit codes.
   Minting a row is defensible and was not done, because it would be a second place for one code.
4. **The config form's `uv sync --locked` has never been observed to succeed**, and cannot be until
   `publishable` is published (batch 1's concern 4, unchanged): `_uv_sync` is stubbed in every success
   arm, and Fixture N observes its argv and cwd rather than its result.
5. **`prepare_env` now returns three values.** Additive in effect — one line of the test helper
   unpacks the third and no arm moved — but it is a shipped-function signature change made for the
   closing transcript's `.env` row, and a later caller reading it as a 2-tuple gets a silent
   `ValueError` rather than a type error.
6. **A stray `apparatus.expected.json` beside a config whose template declares no probe stays inert**
   (batch 2's handover item 5, re-confirmed by reading the guard for § 5's derivation). That is what
   makes the executability verdict hold, and it is a property a later slice could break by hoisting
   the read out of the probe-declared branch.
