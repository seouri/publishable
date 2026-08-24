# H9c batches 1–3 — review, tasks 1–15

Reviewer for batches 1–7 and the whole-branch gate. Branch `h9c-reproduce`, at `ff2b8eb`.
**Nothing was fixed. Every finding is reported and routed.**

Suite at HEAD, run directly in the foreground, twice (once at the start of the review and once
after every mutation was reverted): **3230 passed, 1 skipped, 2 xfailed**. `uv run ruff check .`
→ *All checks passed!*; `uv run ruff format --check .` → *95 files already formatted*;
`uv run mypy` → *Success: no issues found in 53 source files*.

**What was established by behaviour and what by reading** is marked on every line below.
Every mutation was reverted by restoring a pre-mutation copy kept in the scratchpad outside the
repository, and every revert was verified by `git diff --stat` coming back empty **and** by
re-running the tests the mutation had failed. `git checkout -- <file>` was never used.

---

## Verdict per task

| Task | Verdict | Basis |
|---|---|---|
| 1 — the guard pin | **PASS** | Arm E proven able to fail **at HEAD**, not only against the `NOT BUILT` path (behaviour, below). Arm F's added-rather-than-cited disagreement re-checked and correct |
| 2 — the operand reader | **PASS** | `classify_operand` is structural (`run_id` / `runs` / `provenance`-or-`results` / `experiment_type`), never a basename — read, and the `endswith` proxy is named as such in the code |
| 3 — destination and clone | **PASS with a Major against the DOCUMENT** | Clone flags measured from the real argv; the checkout's argv carries none, which the document says otherwise — Major 2 |
| 4 — `code_hash` in the checkout | **PASS** | Ruling Z verified by behaviour: the verdict names the input and prints the closed candidate set. **No verdict invents a cause** |
| 5 — the lockfile ranking | **PASS with Minor 2** | Every lockfile branch reports; the bundle form refuses by name (behaviour). One silent `pyproject.toml` branch |
| 6 — Q1/Q3, the strike | **PASS** | `W-ENV-UNLOCKED` affirmed, `E-REPRODUCE-UNLOCKED` ships, the entry is struck rather than deleted |
| 7 — the config write-back | **PASS with Minor 1** | The siting is armed — by Fixtures M/O/F, **not** by arm E, contrary to two batch reports |
| 8 — `.env` and `required_env` | **PASS** | `prepare_env`'s containment, window and purge each have a mutation that fails them (batch 2's runs; spot-checked by reading the arms) |
| 9 — `run`'s probe comparison | **PASS** | The read is inside the `declared_probe` branch (read); `null → value` passes (behaviour); the record-loss fix is pinned by a mutation that fails one arm (behaviour) |
| 10 — writing the expectation | **PASS** | The write-once guard mutated to `if False:` → exactly `test_fixture_o_arm_2_…` fails (behaviour) |
| 11 — dispatch | **PASS** | All four `reproduce` invocation shapes measured through the real console script outside the repository; arm B edited by its authorized editor only |
| 12 — the config form | **PASS** | `E-GIT-NO-REPO` reuse is sound; the row that documents it is not — Major 1 |
| 13 — the closing transcript | **PASS** | Ordered-triple arms read; end-to-end arms green |
| 14 — `spec-defects.md` | **PASS** | Four OPEN filings reproduced (three by behaviour, one by grep); the closed entry is **struck, not deleted**; every owner is a fact with a reason |
| 15 — the four documents | **PASS with Majors 1 and 2** | Both consistency passes re-run by me with can-fail proofs; no worked-example figure moved; § Executability re-derivation sound and the four-row table byte-identical |
| controller ruling `ff2b8eb` | **PASS** | Every numeric literal byte-identical, one entry touched, the arm still fails when a literal moves (behaviour), and the shipped sentence is now true |

---

## Findings

### Major 1 — `E-GIT-NO-REPO`'s row is STILL narrower than its code, and the same undercount is in `CLAUDE.md`

`reproduce` added **two** call sites of `provenance.find_repo_root`, and the widening counted one.

```
$ grep -rn "find_repo_root" src/publishable/ | grep -v "^src/publishable/provenance.py"
src/publishable/reproduce.py:373:        enclosing: Path | None = find_repo_root(dest.parent)   ← NOT NAMED
src/publishable/reproduce.py:1391:        repo = find_repo_root(operand.path.parent)            ← named
src/publishable/validate.py:511, :1221 · src/publishable/study.py:54
src/publishable/cli.py:235, :2501, :5784
```

`reproduce.py:373` is `prepare_checkout`'s destination walk-up. It catches the raise **by type**
(`except ContractError`) as the pass branch of `E-REPRODUCE-DEST-IN-REPO` — the same shape
`validate.validate_config` has. Established by behaviour that the raise is real:

```
find_repo_root(<a tmp dir outside any repo>)  →  RAISED code= E-GIT-NO-REPO
```

So the true figures are **eight paths** and **three sites catching it by type**. Two documents
now state otherwise:

- `docs/reference.md:1215` — *"Seven paths reach it… Two more catch it **by type**, testing no
  code: `validate.validate_config` … `cli._preloaded_experiment`"*.
- `CLAUDE.md`'s H9c entry — *"which makes it a **seventh** path to that code and a **third** site
  catching it by code"*.

This is the class batch 3's own § 3c calls *"where the whole-branch Majors on four sub-slices have
lived"*, found by the method that section says it used. Note the by-**code** count (three) is
correct; it is the **path** count and the by-**type** count that are short.

**Routed: H9d**, with both sites named — the § Errors row and the `CLAUDE.md` entry — and with
the instruction to derive by reading the call sites and then confirm by grep, not the reverse.

### Major 2 — a normative sentence about a shipped command is false: the detached checkout passes no `-c`

`docs/reference.md` § Reproducing on another device, the paragraph the controller ruling `ff2b8eb`
rewrote three commits ago:

> **And *"the only git operation"* is right about what you typed, while the count underneath it is
> two** — a clone and a detached checkout, **each passing `-c core.autocrlf=false`** so the tree is
> materialized the way the recorded hash expects.

**Measured** — a throwaway probe recording every `reproduce._git` argv on a real clone-and-checkout
(written, run, deleted; not a pin):

```
GIT ARGV: git -c core.autocrlf=false clone -c core.autocrlf=false <remote> <dest>
GIT ARGV: git -C <dest> checkout --detach 71e240a0…
```

Both flags sit on the **clone**, at its two placements. The detached checkout passes none — it
relies on the `core.autocrlf=false` that `clone -c` **persisted into `<dest>/.git/config`**, which
is exactly the mechanism batch 1's own § 4.1 measured and named load-bearing. `_CLONE_CONFIG`'s
docstring says *"passed at BOTH placements"* and is right; the document turned "both placements"
into "both invocations".

Confirmed independently by the shipped structural arm, which asserts the flags on `clone_argv`
alone (`tests/test_reproduce.py:595`, `test_fixture_e_arm_3_the_flag_list_is_exactly_one_flag_at_both_placements`)
and asserts nothing about the checkout's argv.

This is not cosmetic: a reader following the sentence would believe the checkout re-materializes the
tree under the flag, and would conclude a later refactor moving the flag off the clone is safe.

**Routed: H9d.** The honest repair is to say *two placements on the clone, persisted for the
checkout*, or simply to delete the "each passing" clause — **prefer deleting a claim to rewriting
it**, per `CLAUDE.md`. This is the same fault class `ff2b8eb` ruled on, four lines away.

### Minor 1 — arm E's coverage claim is false in TWO batch reports; the behaviour is armed elsewhere

Batch 1's concern 2 and batch 2's § 1 both state that arm E is what stands between task 7's config
write-back and a silently modified run directory:

> *"if that write is ever sited relative to the **operand** rather than the destination, arm E is
> the only thing standing between it and a silently modified run directory."*

**Measured.** Mutation: `config_dir_in` returns `operand.path.parent / "configs" / name` instead of
`dest / "configs" / name` — i.e. exactly the hazard named.

```
$ uv run pytest tests/test_cli.py -q -k "arm_e_reproduce_writes_nothing"
2 passed, 542 deselected                      ← ARM E IS GREEN UNDER THE HAZARD
$ uv run pytest -q                            ← full suite, same mutation
9 failed, 3221 passed, 1 skipped, 2 xfailed
  test_fixture_m_arm_1_… (×2), test_fixture_m_arm_2_…, test_fixture_o_arm_1_…,
  test_fixture_o_arm_2_…, test_the_bundle_form_writes_the_expectation_…,
  test_fixture_f_the_bundle_member_form_end_to_end,
  test_the_closing_transcript_is_the_document_s_own_block,
  test_the_apparatus_block_is_printed_when_the_record_carries_facts
```

The cause is structural and stated in arm E's own (accurate) docstring: its fixture records no
lockfile, so the command stops at `E-REPRODUCE-UNLOCKED` and **never reaches `write_config`,
`write_expectation` or `prepare_env` at all**. Arm E's stated scope is right; the reports' claim
about its scope is not.

**Arm E is not dead**, which was the first thing checked: a stray `mkdir` sited before the refusal
(`(path.parent / "H9C_STRAY_MB").mkdir()` immediately above `prepare_checkout`) fails **both**
parametrizations at HEAD — `2 failed, 542 deselected`. So the guard is live; it is its advertised
reach that is overstated.

**Routed: H9d**, as a correction to append to the batch reports' claim rather than a code change —
the write-back siting is genuinely armed, by Fixtures M, O and F.

### Minor 2 — a silent branch in `restore_environment`'s `pyproject.toml` comparison

`src/publishable/reproduce.py`, step 4:

```python
if recorded_pyproject.is_file() and clone_pyproject.is_file():   # identical / DIFFERS
elif not recorded_pyproject.is_file():                            # "not reachable, so not compared"
```

The case **recorded copy present, the commit's absent** falls through with **no line printed**, in
the one function whose ruling (AA) is that *"every absence and every disagreement is printed rather
than resolved quietly."* Established by reading the branch structure. Unreachable in practice for a
`uv` project, which is why it is Minor rather than Major — but it is an unstated absence, and the
sibling branch two lines above prints one. **Routed: H9d.**

### Minor 3 — `expectation_from`'s `code` parameter is configurability no caller uses

`apparatus.expectation_from(path, *, code: str = "E-IO-FAILED")` uses `code` at all five of its
raise sites (read), but has **one** caller —

```
$ grep -rn "expectation_from" src/publishable/ tests/ | grep -v "def expectation_from"
src/publishable/cli.py:3253:  expected = apparatus.expectation_from(expected_path)
```

— which passes no `code` and then re-codes the caught exception anyway
(`expectation_c.error(exc.code or "E-IO-FAILED", …)`). The docstring's *"the refusal is the
caller's `code`"* describes a seam nothing exercises. `replay_ledger`'s identical parameter is the
precedent it copies, so this is carried rather than invented. **Routed: H9d**, as *delete the
parameter or exercise it*.

### Minor 4 — a test name asserting a false count, with eight citations

`test_stop_codes_holds_exactly_the_two_codes_execute_plan_breaks_on` pins **three** codes at HEAD.
Batch 2 declined the rename deliberately and disclosed it in a comment beside the assertion, having
grepped the eight citations. That is the right call for a batch and the wrong state to leave
permanently: *a reader greps for exactly that name and stops looking*. **Routed: H9d**, with the
eight citation sites named in batch 2's § 6 so the rename is mechanical.

---

## Adjudications the dispatch asked for

**§ Errors placement (check 8) — the shipped placement is CORRECT, and design Decision 14 is
rightly overruled.** Adjudicated against each table's own scope sentence, read verbatim rather than
taken from the design:

- § Errors `validate` reports: *"these are the codes a **command** reports"*, and the section's
  intro now adds *"**Read that scope sentence literally rather than the heading**"* and names the
  `E-RESUME-*`, `E-FREEZE-*` and `E-REPRODUCE-*` families plus `diff`'s config operand.
- § Errors core raises: *"**Two rows in this table are not raises**"*, justified by exactly the
  dirty gate and the empty-file-list gate.

Counted, not assumed: `grep -c "no exception; a \`Collector\` diagnostic"` over the section returns
**3** — two rows plus the intro's own sentence — so the "Two rows" claim is still exactly true after
the insertion. Eleven of the twelve `E-REPRODUCE-*` codes are never raised (`grep -n 'raise'
src/publishable/reproduce.py` returns only the `KeyboardInterrupt` re-raise), and
`E-APPARATUS-UNEXPECTED`, which **is** raised, went to § Errors core raises beside the six other
`E-APPARATUS-*` rows. Moving the twelve as Decision 14 instructs would have stranded a
justification. **No finding.**

**`E-IO-FAILED`'s widening (check 8, second half) — COMPLETE.** All ten emit sites in
`reproduce.py` were enumerated by reading (`:143`, `:174`, `:403`, `:671`, `:740`, `:750`, `:848`,
`:1230`, `:1423`, `:1433`) plus `cli.py:3257`, and every one is described by the widened § Exit
codes paragraph at `docs/reference.md:3851`. Six at exit `1`, three at `5`, plus the
`read_record_file` fallback and the shipped-`run` site. **No finding.** That the code has a
paragraph and no table row is disclosed by the batch and is a defensible judgement, not a defect.

**`E-UPSTREAM-RECORD-*` four → five (check 9) — CORRECT.** `grep -rn "read_record_file"` gives five
call sites: `lineage.py:106`, `report.py:1058`, `report.py:1386`, `study.py:431`,
`reproduce.py:172`. The row's five `through …` clauses map onto them.

**`E-TEMPLATE-LOAD` (check 9) — CORRECT.** The fallback the widened row describes is real:
`reproduce.py:1095`, `code = exc.code if isinstance(exc, PublishableError) else "E-TEMPLATE-LOAD"`.

**Guard-pin arm B's "dominated" disclosure (check 10) — HONEST and CONSERVATIVE.** Measured by
re-marking `list-templates` in `docs/reference.md` from `NOT BUILT` to `built`:

```
FAILED tests/test_cli.py::test_reference_cli_tables_are_parsed_at_all
      >  assert ("list-templates", "NOT BUILT") in tables["Command"]   ← the ADDED line raised
FAILED tests/test_cli.py::test_reference_cli_tables_match_what_the_cli_does[Command]
2 failed, 1 passed, 541 deselected
```

The added line is the assertion that raises first, and a **second** test fails on the same
mutation — so "no mutation fails it alone" is true, and reporting it as *carried, not coverage* is
the correct posture. **No finding.**

**Ruling Z (check 1) — HONOURED. NO VERDICT INVENTS A CAUSE.** Established by behaviour, on the
H6a-boundary case the dispatch names — a record whose `code_hash` is an every-file-era digest over
identical code:

```
error   E-REPRODUCE-CODE-HASH <dest>
        does not reproduce the recorded code_hash: the record says sha256:0000…,
        this checkout hashes sha256:436cab24… over 6 files. The checkout is kept
code_hash: the 6 files folded were:  [six paths listed]
`reproduce` cannot tell these apart, and does not guess between them:
  - the code at that commit really is different: a rewritten or force-pushed history;
  - the record predates the redefinition of WHICH files are hashed…;
  - this machine's git materialized the tree differently: `core.autocrlf`… or a tracked
    `.gitattributes`, which it may not.
```

The input that moved is named (`code_hash`, both digests, the count and the list). The set is
closed and prefaced by *"cannot tell these apart, and does not guess between them"*. And the
scoping's feared step — *"a rewritten or force-pushed history"* asserted as the cause — is not only
absent, it is **caught elsewhere and by name**: a commit the remote no longer holds fails the
checkout as `E-REPRODUCE-COMMIT-UNREACHABLE` before any hash runs.

**Correction 3 (check 2) — MEASURED MYSELF, and the design's cost is stated rather than blamed on
the tree.** Outside the repository, ambient `core.autocrlf = true` via `GIT_CONFIG_GLOBAL`,
`git version 2.50.1 (Apple Git-155)`, `md5` of `src/pkg/mod.py`:

| clone | digest | stored `core.autocrlf` |
|---|---|---|
| the original working tree | `26149c8e…` | — |
| `git clone` (plain) | **`da5d665f…`** | `true` |
| `git -c core.autocrlf=false clone` | `26149c8e…` | `true` |
| `git clone -c core.autocrlf=false` | `26149c8e…` | **`false`** |
| both, as shipped | `26149c8e…` | **`false`** |

So a faithful clone's `code_hash` **does** depend on `core.autocrlf`; `clone -c` is the placement
that persists it for a later checkout, which is precisely batch 1's § 4.1 finding and it reproduces
on my machine. The shipped command passes both, `reference.md` step 3's candidate set names
`core.autocrlf` *"which the clone neutralizes"* and `.gitattributes` *"which it may not"*, and the
residue is **filed** rather than blamed on the tree — filing reproduced:

```
* text eol=crlf  in a tracked .gitattributes, cloned with BOTH -c flags
orig  : 26149c8ef04aa975339a9a5898d28636      b'x = 1\ny = 2\n'
clone : da5d665f762851a81554363c76eae0de      b'x = 1\r\ny = 2\r\n'
```

The digits differ from the filing's and from the design's, as the filing itself says they will —
the **inequality** is the claim. **No finding.**

**Ruling AA (check 3) — HONOURED, both forms, by behaviour.** Every branch of
`restore_environment` either appends a transcript line or raises a named refusal; there is no
silent preference (read, branch by branch — with Minor 2 the one exception). The bundle form was
driven end to end on a real `study add` bundle whose member's `uv_lock` is a dangling
`environment/uv.lock`:

```
uv.lock: the run's own copy is not reachable from <bundle>/main.run.yaml
error   E-REPRODUCE-LOCKFILE-UNREACHABLE <dest>
        holds no uv.lock at all, and the record's environment is sha256:d981385a… —
        no lockfile matching the record is reachable… A bundle carries no lockfile of its own;
        the checkout is kept at <dest>
```

Absent → printed then refused by name. Identical / DIFFERS / edited-copy / clone-only are each a
printed line or a named code, read at the branch.

**Ruling BB and the behaviour change (check 4).** The read is **gated**, established by reading the
site: `expected_path = config_path.parent / "apparatus.expected.json"` is built **inside** the
branch that has already resolved `declared_probe` through `apparatus._probe_for`, so a config whose
template declares no probe never reaches it and a stray file beside such a config is inert. Every
other `cli.py` hunk on this branch is `OPERATION_COMMANDS`, the dispatch entry, `Observer(expected=…)`
threading, and the run-start containment widening — each gated on `expected is not None` or on
`exc.code in ("E-APPARATUS-CHANGED", "E-APPARATUS-UNEXPECTED")`, neither reachable without a
declared probe. `apparatus.py`'s whole delta is `expectation_from`, `check_unexpected`, one
`STOP_CODES` member and `Observer.expected`, all additive. Batch 2's 93-leaf both-worktrees
measurement is therefore consistent with what the code can do; I re-derived the gating rather than
re-running the two worktrees. **Correction 11's hazard is armed**: `check_unexpected` calls
`record` on the **expectation** object, never the run's own, and Fixture Q pins
`provenance.apparatus.unobserved` equal to a no-file control's — green at HEAD.

**Correction 27 / the `null → value` case (check 5) — PASSES, measured directly:**

```
changed alone (null->value): AssertionError  record() runs before changed() for the same `facts`…
record then changed:        None            ← passes
moved value:                ('model', 'A', 'Z')
```

and the shipped `check_unexpected` does `expected.record(...)` then `expected.changed(...)`, which
is `Observer._observe_one`'s own ordering.

**The record-loss defect (check 6) — FIXED AND PINNED, verified by mutation at HEAD.** Narrowing
the run-start branch back to `exc.code == "E-APPARATUS-CHANGED"`:

```
FAILED tests/test_cli.py::test_h9c_a_resume_whose_run_start_contradicts_the_expectation_keeps_the_record
1 failed, 3232 deselected
```

The arm is discriminating rather than incidental: it asserts `EXIT_FAILED`, the identifier present,
`E-APPARATUS-CHANGED` **absent**, `run.yaml` **present**, `status == "failed"`, and
`results.conditions` **non-empty** — the record-loss half, not just the exit code. Reproducing the
defect at `7a9268d` was not needed once the mutation at HEAD came back red.

**The controller ruling `ff2b8eb` (check 7) — CLEAN.** `git show ff2b8eb -- tests/test_cli.py`
touches exactly one entry of `_H5A_ARM_D_REFERENCE_LINES`. The run ID
`my-study_run_2026-08-06T14-02-11Z_8e21ab3` is byte-identical on both sides; a diff over the four
documents filtered for every worked-example literal returns that one `-`/`+` pair and nothing else.
The arm still fails when a literal moves — `8e21ab3` → `9999999` gives
`FAILED …test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text[REFERENCE]`, `1 failed, 2
passed`, and the `SUMMARY` and `README` parametrizations stay green. And the shipped sentence is now
**true**: a second `reproduce` of the same record derives the same destination and refuses with
`E-REPRODUCE-DEST-EXISTS` (read at `reproduce.py:360-370`).

**`reproduce new` (check 12) — MEASURED, all four shapes**, through the real console script from an
empty scratch directory outside the repository, which was empty before and after:

| Invocation | Exit | Output |
|---|---:|---|
| `publishable reproduce` | `2` | `` `reproduce` takes exactly one path and no flags `` |
| `publishable reproduce a b` | `2` | the same line |
| `publishable reproduce --json` | `2` | the same line |
| `publishable reproduce new` | **`1`** | `error   E-IO-FAILED          new` / `could not be read as YAML: [Errno 2] No such file or directory: 'new'` |

Matches the report exactly, including the derived `2` → `1`.

**The filings (check 13) — all four OPEN entries reproduced.** `.gitattributes` by the recipe
(above); the bundle-lockfile gap by driving `_bundle_member` and reading the state its own asserts
pin (`uv_lock: environment/uv.lock`, no `environment/` beside it, `uv_lock_hash` non-null);
`provenance` naming no `pyproject.toml` by `grep -c "pyproject" src/publishable/provenance.py` →
**0**; and `_claims`' docstring by `grep -rn "_claims" src/publishable/ | grep -v registry.py` →
**three** importers (`freeze.py:42`, `validate.py:43`, `generators/experiment.py:10`) against a
docstring reading *"the two cross-module imports are the whole set"* at `registry.py:69`. The
closed entry is **struck in place** — the only deletions in `spec-defects.md` are the two lines
replaced by their `~~struck~~` versions.

**§ Executability (check 14) — the re-derivation is SOUND and the table is byte-identical.**
Verified programmatically: eleven `| Figure | Count | Visible to` headers in the file; the six-line
block at each of the last **ten** is identical to the new one, and only the pre-H8a block differs.
No fifth number is minted. The design's stated reason **is** false at HEAD and the entry says so:
`reproduce` accepts a config, and all nine are configs. The replacement grounds — `reproduce` runs
at no `validate`, is invoked from no step, and preparing an environment is not executing a config —
are each checkable and each hold.

**Both consistency passes (check 15) — RE-RUN BY ME, not taken from the report.** A throwaway
script (not kept) over the **named** file list — `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md`,
`docs/feasibility-llm-growth-studies.md` — checking `#anchor` resolution, cross-file anchors,
relative links, duplicate anchors, table separator/header column counts, empty rows, trailing
whitespace, tabs and seven invisible code points, skipping fenced blocks and using GitHub's own
slugger rules (en/em dashes stripped, not transliterated). **HITS 0.** The **file list** was
filtered, never the output. Can-fail proved by injection into `docs/reference.md` and reverted from
a copy kept outside the repo:

```
DUPLICATE ANCHOR docs/reference.md:4349 #cli-reference
BAD ANCHOR       docs/reference.md:4346 #no-such-anchor-here
BAD LINK         docs/reference.md:4346 docs/nope.md
TRAILING WS      docs/reference.md:4347
TAB              docs/reference.md:4348
HITS 4      → after revert: HITS 0
```

Cross-document: **no worked-example figure moved** — the literal sweep over the four documents
returns exactly the one step-2 `-`/`+` pair whose run ID is byte-identical on both sides, and the
same filter over the whole of `reference.md` returns 31 lines, so the sweep is live.
`cohort-pilot`'s intervals are untouched. `×` versus `x`: `git diff main...HEAD | grep '^+' | grep
-E '[0-9] x [0-9]'` over all six files → **no hits**. The `Status` column moved in task 11 and is
bound in both directions — proved by the arm-B mutation above, where flipping the document cell
fails both the pin and `test_reference_cli_tables_match_what_the_cli_does[Command]`. No config field
was added, no enum touched, no version moved.

**The development record (check 16) — NOT retro-edited.** `git diff main...HEAD --
docs/superpowers/plans/ docs/superpowers/specs/ docs/superpowers/H9-SCOPING.md` adds **eight lines
and removes none**: one appended `> **AMENDED 2026-08-24 by the controller…**` block on the plan.
`spec-defects.md`, the sole exception, strikes rather than deletes.

**Cross-batch interactions (check 11).** Each earlier-batch guard mutated at HEAD and confirmed
still to kill something:

| Earlier guard | Mutation at HEAD | Result |
|---|---|---|
| batch 1, arm E | stray `mkdir` under the operand's parent before the refusal | **2 failed** — both parametrizations |
| batch 1, Ruling Z's candidate set | `lines += []` in `verify_code_hash` | **failed** `test_fixture_d1_a_pre_redefinition_code_hash_is_refused_with_the_candidate_set` |
| batch 2, `write_expectation`'s write-once | `if target.exists():` → `if False:` | **1 failed, 624 passed** — `test_fixture_o_arm_2_…` alone |
| batch 2, task 7's write siting | `config_dir_in` returns `operand.path.parent/…` | **9 failed** — see Minor 1 |

No earlier guard was found dead. One earlier **claim** about a guard was found false (Minor 1).

**Gates and the delta (check 17).** `ruff check`, `ruff format --check` and `mypy` clean at HEAD.
`main` is 3132 and HEAD is 3230 — **+98**, accounted for: `git diff main...HEAD -- tests/ | grep -c
"^+def test_"` returns **90** new test functions and `grep -c "^-def test_"` returns **0**; three
of the 90 are parametrized, at 2, 4 and 5 cases (collected and counted), giving
90 − 3 + 11 = **98**. The only removed lines under `tests/` are **four**: guard-pin arm C's
set-equality and its docstring clause, arm B's status tuple, and the `_H5A_ARM_D_REFERENCE_LINES`
step-2 entry — each an authorized edit, each accounted for above.
