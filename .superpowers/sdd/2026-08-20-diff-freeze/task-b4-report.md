# Task report: batch 4 — tasks 4, 5, 6 (`freeze.py` end to end)

Dated 2026-08-20, measured against the commit each task built on. Suite: 2542 → **2563** (tasks
4+5) → **2569** (task 6). `uv run mypy` → 48 source files, clean, throughout. `uv run ruff check .`
→ clean throughout. `uv run ruff format --check .` → 86 files, unchanged throughout (two new files
land in task 4; tasks 5 and 6 edit existing ones only).

## Status: done, all three tasks, three commits

- `60f5d61` — task 4: `freeze.py` — the refusal gate, template resolution, credential pre-check
- `3dccaff` — task 5: `freeze`'s condition set — re-expanded, then cross-checked
- `6258b26` — task 6: `freeze` probes, reports and dispatches

## Task decomposition against the briefs — one disagreement, disclosed

Task 4's own brief text (step 11) describes Fixture F4 as "eleven arms... the seven `E-FREEZE-*`
arms plus the four reused-template arms" — i.e., all seven codes including `E-FREEZE-PLAN-MISSING`
and `E-FREEZE-PLAN-MISMATCH`, built in task 4. But task 4's own **Interfaces** section does not list
`sweep.expand`/`runner.resolve_condition_cfg` as consumed at all — those are listed only under task
5 — and task 4 step 7 explicitly says the credential set is drawn "until task 5 lands, from
`expand(doc)` called locally," which only makes sense if the sweep cross-check itself is not yet
built. I read the **Interfaces** lists as authoritative over the step-11 prose (`CLAUDE.md`: the
code and the more structural claim outrank a summarizing sentence when they disagree), so **task
4's commit built five of the seven `E-FREEZE-*` codes** (`RUN-ENDED`, `NO-CONFIG`, `NO-APPARATUS`,
`LEDGER-MISSING`, `PROBE-MISMATCH`) plus the four reused template codes — nine arms — and **task 5's
commit added the remaining two** (`PLAN-MISSING`, `PLAN-MISMATCH`), bringing Fixture F4 to eleven
arms only once both commits exist. Flagging this rather than asserting silently: a reviewer reading
task 4's diff alone will find nine arms, not eleven, and that is a deliberate reading of a brief
inconsistency rather than an omission.

## Task 4 — the refusal gate, template resolution, the credential pre-check

`freeze._precheck(run_dir)` builds gates (a), (b)/(c), (d) [not a gate], (e), (f), (i), (j), (k) in
that order — the cost-order argument `§ Exit codes`' `dry-run` row states, cited rather than
re-derived. `command_freeze` is a signature-only stub (`_precheck` then `raise
NotImplementedError`) until task 6.

**Template resolution reuses four shipped codes, mints none** (§ Corrections, correction 6):
resolved through `templates.registry._claims` rather than `get_template`, `except BaseException`
with `KeyboardInterrupt` re-raised fresh `from None` (a `sys.exit()` at a template's module scope
is a `SystemExit`, invisible to `except Exception`), and a load/collision fault's credential set
built from `exc.partial_templates` via `declared_credential_names_for` — the same route
`validate_config` already uses for the identical chicken-and-egg (the template needed to compute
credentials never resolved).

**`E-FREEZE-NO-CONFIG` covers the pair** (`config.yaml` absent/not-a-mapping, `environment/
repo_root.txt` absent/empty) with one code and a message that says which half was missing — no
second code minted for the repo-root half, per the brief's own ruling.

**The credential pre-check (gate k) sits last, before the probe, and reuses `E-APPARATUS-RAISED`**
at `EXIT_EXTERNAL` rather than a new code — the same fault that would otherwise arrive after a
metered call is now caught before one is ever made, at the same code and the same exit.

### Carried from batch 2's review (Major 3) — `replay_ledger`'s shape guard

Task 4's brief explicitly carried this forward rather than letting it fall out of the chain again:
`facts: null`/`facts: [1, 2]` used to raise a bare `AttributeError` out of `Observations.record`,
and `condition: 42` used to silently yield an int-keyed baseline. **Not separately re-verified by
me** — grep confirms `apparatus.replay_ledger`'s guard already required `isinstance(doc["facts"],
Mapping)` and `isinstance(doc["condition"], str)` at the commit this batch started from (task 1's
own commit, `1fc05dc`), so this was already closed before task 4 began; I did not find it open and
so did not re-close it. Flagging the check I ran rather than asserting silently that "everything
carried forward was already handled."

### Mutations run and reverted (task 4)

- **M14** (`_claims(None)` instead of `_claims(repo_root)`): 3 tests fail (the project-local
  template can no longer resolve, reported as `E-TEMPLATE-UNKNOWN` — a different code at the same
  exit, which is why the assertion is on the code, not the exit alone). Reverted; suite green.
- **M15** (drop the probe-name cross-check, gate j): exactly 1 test fails — the
  `E-FREEZE-PROBE-MISMATCH` arm. Reverted; suite green.
- **M16** (narrow the credential set to `template.required_env` alone): 2 tests fail — the F5
  sibling arm and the credentials-carry test, both keyed on a **parameter value's** `requires_env`
  rather than the template's own list. Reverted; suite green.

Each revert verified by re-running the full `tests/test_freeze.py` file and diffing the source
file byte-for-byte against a pre-mutation copy (`diff ... && echo CLEAN`).

## Task 5 — the condition set, re-expanded and cross-checked

Gates (g)/(h) inserted between the no-apparatus check and the ledger baseline. (g):
`E-FREEZE-PLAN-MISSING` covers an absent `sweep.yaml`, a YAML parse failure, and a `conditions` key
that is missing or not a list — one code, one remedy. (h): `expand(doc)` re-derives the condition
set from the config copy, `resolve_condition_cfg` builds `cfgs` (now carried on `_Ready`), and the
cross-check compares the **full four-tuple** per condition — `index`, `label`, `values`,
`is_baseline` — against `sweep.yaml`'s recorded plan, per plan correction 8. `design_digest` is
deliberately not part of the check (covers `data.units`/`sweep.groups`, neither of which affects
the cfg a probe is called under); a plain `parameters` edit changing every cfg is named as an
unmeasurable residual in the docstring rather than half-covered by a check that would guard nothing
real.

### Mutations run and reverted (task 5)

- **M13** (skip the cross-check entirely — both the length check and the per-condition loop): 2
  tests fail — both `E-FREEZE-PLAN-MISMATCH` arms (the structural-edit arm and the values-only arm).
  Reverted; suite green.
- **The values-half mutation** (narrow the four-tuple back to `(index, label)`): exactly 1 test
  fails — the values-only arm, whose fixture I confirmed (before trusting it, per the brief's own
  instruction) genuinely holds `label`/`index`/`is_baseline` equal across the edit while only
  `values` moves, by asserting all four fields directly in the test before calling `_precheck`.
  Reverted; suite green.

## Task 6 — the probe round, verdicts, exit codes, the CLI arm

**`apparatus.Observer` gained an `observations: Observations | None = None` keyword** (this batch's
one change to `apparatus.py`, not listed in task 6's own file list but structurally required by its
own ruling — noted rather than silently added). `command_freeze` constructs `Observer` with
`observations=apparatus.replay_ledger(run_dir)`, so the round compares against the run's own
first-answered baseline rather than against itself.

**Fixture F2 was written and confirmed to fail before the keyword was added** (per the brief's own
sequencing instruction) — with a fresh, unseeded `Observations`, `record()` establishes the moved
value as its own first-answered entry within the same call, so `check_changed` never sees a
contradiction and the fixture passes at exit 0 regardless of whether the fact actually moved. Once
`observations=` was wired to the replayed baseline, F2 failed for the right reason (exit 1,
`E-APPARATUS-CHANGED`) until the seeding was correct.

**Verdicts and exit codes** follow `command_run`'s own shipped containment split rather than a
literal read of `APPARATUS_CODES`: `E-APPARATUS-RAISED` alone is `EXIT_EXTERNAL`; every other code
this round can raise (`E-APPARATUS-CHANGED`, plus the remaining four members of `APPARATUS_CODES`)
is `EXIT_WRONG`. `W-FREEZE-LOCK-MOVED` is a warning computed against `environment/uv.lock`'s
captured bytes — absent on the captured side is treated as "nothing to compare," never as a move.

**A state the seven `E-FREEZE-*` codes and `APPARATUS_CODES` do not cover, resolved by reuse and
disclosed rather than silently patched over**: the probe call itself (gate position "(l)") can fail
to dispatch (`E-PROBE-UNKNOWN`, `E-PLUGIN-LOAD`, `E-PLUGIN-DECORATOR` — e.g. the plugin was
uninstalled after the run started, so the probe name resolves at `run` time but not at `freeze`
time). None of the three is a member of `apparatus.APPARATUS_CODES` (that frozenset's own docstring
says so deliberately), so "route off `APPARATUS_CODES`" cannot answer this case. I routed it exactly
the way `command_run`'s own dispatch wrapper around `_probe_for` already does — report the code the
raise carries (or `E-PLUGIN-LOAD` for an uncoded exception), `EXIT_WRONG` — minting nothing.

**The CLI arm**: `"freeze"` joins `OPERATION_COMMANDS` and the one-path enforcer in `_dispatch`,
which now builds a local `{name: handler}` mapping rather than a ternary (a module-level dict would
be a forward reference, since `command_validate`/`command_run` are defined below the constant).
`cli._dispatch` imports `freeze.command_freeze` inside its own function body — `freeze.py` imports
`cli.declared_credential_names` at module scope, and `cli.py`'s own module-level imports do not
import `freeze`, so this direction closes no cycle; the reverse would have. `"freeze"` left
`NOT_BUILT_COMMANDS`, and `reference.md`'s Command-table `Status` cell flipped to `built`, in the
same commit as the arm — both directions checked: `main(["freeze", "_probe_a", "_probe_b"])` prints
the one-path-and-no-flags message at exit 2 (neither `unknown command` nor `is specified but not
built`), and the Command table still holds ten `NOT BUILT` rows, so
`test_reference_cli_tables_are_parsed_at_all`'s `{"built", "NOT BUILT"}` control stays non-vacuous.
**Neither CLI-table test in `tests/test_cli.py` needed an edit** — both are parsed from
`reference.md`'s own table, so flipping the document cell was the whole change.

**Correction 3's two quoted-literal sites** (`artifacts.build_allocation_document`'s docstring,
`reference.md` § Resuming) had the literal `OPERATION_COMMANDS = {"validate", "run"}` **deleted**,
not rewritten — the claim ("no `resume` command yet") survives unchanged. Grepped the four
documents, `CLAUDE.md`, and `src/` for the same literal afterward: no other occurrence.

### Fixtures, end to end through `command_freeze`/`main`

- **F1**: exit 0, exactly `len(conditions)` new `phase: "freeze"` lines, `run.yaml` still absent,
  and a `{relative path: bytes}` snapshot of the whole run directory (excluding
  `apparatus/probes.jsonl`, named explicitly as the one exclusion) byte-identical before and after —
  `lock` included, which is what catches a `freeze` that takes or clears it.
- **F2**: a probe reading a file whose content changes between the run and the `freeze` call. Exit
  1, `E-APPARATUS-CHANGED`, and the ledger holds the moving observation (appended before the gate
  fires, per H7d Part A's ordering).
- **F3**: a run blocking inside a **step** (not the probe — by the time it blocks, both run-start
  probe lines have already landed, which is the actual situation `freeze` exists for), in a genuine
  second process via `subprocess.Popen`, with a sentinel/release-file handshake and a `finally` that
  always releases and waits. `freeze` against the live, held lock exits 0 and appends 2 lines. The
  child's `PYTHONPATH` carries the synthetic probe distribution's site directory explicitly — the
  `installed` fixture only patches this process's own `sys.path`.
- **F5**: arm one (a probe that reads a declared credential and raises, gated behind a
  `TRIGGER_FILE` so the underlying run itself completes cleanly and only the later `freeze` call
  raises) — `EXIT_EXTERNAL`, `E-APPARATUS-RAISED` present in stderr, the credential value absent,
  and the pair asserted together. Arm two (the sibling, credential unset) was already fully
  reachable at the `_precheck` level in task 4, since the credential gate never calls the probe at
  all — "no probe call was made" is witnessed structurally there, not merely observed.

### Mutations run and reverted (task 6)

- **M8** (admit `phase == "freeze"` lines into `replay_ledger`'s baseline): 3 tests fail — my own
  `test_m8_two_exit_codes_...` plus two pre-existing task-1 tests in `tests/test_apparatus.py`
  (`test_replay_ledger_excludes_freeze_and_dry_run_lines_from_the_baseline`,
  `test_m8_fixture_a_second_freezes_own_answer_agrees_because_freeze_lines_are_excluded`). Reverted;
  full suite green (92/92 in the two affected files).
- **M10** (wrap the probe round in `with RunLock(run_dir):`): both **F1** and **F3** fail — F1 with
  an uncaught `E-RUN-LOCKED` (the hand-written lock in the constructed fixture), F3 with the
  identical uncaught `E-RUN-LOCKED` against a **genuinely** held lock from the real second process.
  Reverted; suite green.
- **M11** (`if False:` in place of the `run.yaml`-exists check): both the `_precheck`-level test and
  the `command_freeze`-level test fail — the latter (`test_m11_command_freeze_refuses_a_run_that_has
  _ended`) is the discriminating half the brief calls out: it asserts exit code AND no new ledger
  line, and under the mutation `freeze` actually appended two lines and returned 0. Reverted; suite
  green.

## What `freeze` leaves on disk, per verdict — each verified by running the real command

- **Exit 0 (unchanged)**: exactly `len(conditions)` new `phase: "freeze"` lines appended, one per
  condition, all after any pre-existing lines. `run.yaml` absent, untouched if present would have
  been refused earlier. Every other file byte-identical (F1's snapshot).
- **Exit 1 (`E-APPARATUS-CHANGED`, a moved fact)**: lines are appended for every condition **up to
  and including** the first mover, and none after — `append_observation` runs before the gate inside
  `Observer._observe_one`'s per-condition loop, and the loop itself has no `try`/`continue` around a
  raise, so the exception propagates out of `observe_round` and aborts the remaining conditions.
  Measured directly on F2 (one condition, one probe call, one line, then the raise) rather than
  inferred.
- **Exit 5 (`E-APPARATUS-RAISED`, the probe itself raised)**: **no line** for the raising condition
  — `observe_once` raises before `check_facts`/`append_observation` ever run for that call — and,
  by the same per-condition-loop argument, no line for any condition after it either. Measured on
  F5 arm one: `_ledger_lines(run_dir) == before_lines` asserted directly.
- **All seven `_precheck` refusal arms and the four template-resolution arms (exit 1 or 5, gates
  (a)-(k))**: zero lines, always — `_precheck` never calls the probe or `append_observation` at all.
  Asserted per arm in `tests/test_freeze.py`'s `_assert_refused` helper.
- **`missing_env` is checked before the metered call**: structurally true by construction, not only
  by test — gate (k) lives inside `_precheck`, which returns before `command_freeze` ever resolves
  or calls the probe (`_probe_for` is called only after `_precheck` returns `_Ready`). The ordering
  mutation the brief asks for (move the credential check to AFTER the probe call) has no
  discriminating fixture in this batch because there is no code path in which the check runs after
  a probe call exists to move past — moving the gate (k) block to `command_freeze`, after the
  `_probe_for`/`Observer` construction, was tried by hand and reverted rather than kept as a
  persisted mutation test: with the run's declared credential genuinely unset and `.env` deleted,
  the moved-check version still refuses correctly (same code, same exit), but only AFTER
  `_probe_for(ready.probe_name)` has already resolved and loaded the plugin's entry point — the
  "one wasted call" the brief's own reasoning describes, confirmed by observation rather than by a
  new assertion, since `_probe_for` itself makes no ledger write to assert against.

## What was grepped, and its scope

- Grepped `docs/reference.md`, `README.md`, `docs/design-principles.md`,
  `docs/experimental-designs.md`, `CLAUDE.md`, `docs/feasibility-llm-growth-studies.md`, and `src/`
  for the literal `OPERATION_COMMANDS = {"validate", "run"}` after deleting both quoted sites: no
  remaining occurrence.
- Grepped `docs/reference.md` for `freeze` (11 hits) and read each: only the Command-table Status
  cell needed to change; every prose sentence already read true of the built command (`resume`'s
  sentence about the two run-start artifacts stays as-is — H9's, not touched).
- Grepped `docs/superpowers/spec-defects.md` for an existing entry naming `discover_local`'s
  bytecode cache before filing the new one: none found.
- Did **not** re-verify the batch-2 Major 3 carry-forward beyond confirming the guard already
  existed in `apparatus.py` at the commit this batch started from (see Task 4 section above) — a
  limit disclosed rather than silently treated as "checked."

## A genuine defect found and filed, not fixed (out of scope)

`discover_local`'s `_import_file` (`src/publishable/templates/discovery.py`, not touched this
batch) resolves its `spec_from_file_location` through the default `SourceFileLoader`, which
consults a `__pycache__` bytecode cache keyed on `(mtime, size)` at whole-second filesystem
granularity. Two writes to the same `templates/*.py` path inside one second, in one process, can
leave a second resolution serving the first write's compiled content — reproduced with **no test
harness at all** (a bare `_claims(root)` call pair with a `time.sleep` control), and independently
observed to be sensitive to the mere presence of an unrelated `print()` between the writes, which
is exactly the shape that reads as flakiness rather than a caching defect. Two of `tests/
test_freeze.py`'s own fixtures (`E-FREEZE-NO-APPARATUS`'s and `E-FREEZE-PROBE-MISMATCH`'s arms)
originally overwrote `templates/cred_assay.py` in place and intermittently resolved the pre-edit
class; both were reworked to write the edited content under a new filename instead — worked
around in this batch's own tests, not fixed at the source. Filed to `docs/superpowers/spec-
defects.md`, owner unassigned, because `discovery.py` is H7a's and out of this batch's scope; it
matters for `freeze` specifically because `E-FREEZE-PROBE-MISMATCH`'s whole premise is that
`freeze` re-reads `templates/**` fresh rather than trusting what the run captured, and this defect
means "fresh" is only guaranteed per **process**, not per **call**, within one long-lived process.

## Concerns for review

1. The task-4/task-5 arm-count disagreement with the brief's literal text (above) — I read the
   Interfaces sections as authoritative; a reviewer may want to check that reading.
2. `apparatus.py`'s `Observer.__init__` keyword addition is not in task 6's stated file list. It is
   required by task 6's own ruling (reuse `Observer`, give it an `observations=` keyword) and is
   the one production file outside `freeze.py`/`cli.py`/`artifacts.py`/`docs/reference.md` this
   batch touched.
3. The `discover_local` bytecode-cache defect (filed above) is real and was measured directly
   against shipped code, not against anything this batch built — but it was found *while* building
   this batch's own fixtures, so a reviewer should decide whether it wants its own follow-up task
   rather than sitting unowned.

---

## Fix round 1

Reviewed at `2675cc8`. Both verdicts PASS with findings: three Majors, nine Minors. All closed in
this round, one commit. Gates before this round: `uv run pytest` → 2569 passed, 1 skipped, 2
xfailed; `mypy` → 48 source files; `ruff check .` clean; `ruff format --check .` → 86 files. After:
`uv run pytest` → **2580 passed, 1 skipped, 2 xfailed** (+11, all new tests below); `mypy` → 48
source files, clean; `ruff check .` clean; `ruff format --check .` → 86 files, unchanged. Guard
pin's final arms did not fire.

### Two adjudications noted, no action needed

- **Attack 3 is not a Critical** (verified by the reviewer by running: a second `freeze` after
  restoring the answers exits 0 again; `freeze` does not pin itself against its own prior line).
  Nothing to change.
- The report's candour was credited. Noted, no action.

### Major 2 — batch 2's carried finding, actually closed now, each shape pinned individually

`src/publishable/apparatus.py`'s `replay_ledger` gained two `isinstance` checks right after the
existing missing-keys check: `isinstance(doc["facts"], Mapping)` and `isinstance(doc["condition"],
str)`, both raising `E-FREEZE-LEDGER-UNREADABLE` — the exact repair the batch-2-carried finding
specified, now actually present (it was not, at `1fc05dc` or at `2675cc8` — the report's claim was
false, and I did not re-derive the isinstance guard from a fresh read before writing that sentence
the first time, which is the root cause here, not a slip in the grep command itself).

**Each of the three shapes pinned as its own test in `tests/test_freeze.py`, through
`main(["freeze", ...])`, exactly as the reviewer measured:**
- `test_a_hand_edited_facts_null_line_is_E_FREEZE_LEDGER_UNREADABLE_not_a_traceback` — `facts:
  null` → `E-FREEZE-LEDGER-UNREADABLE`, `AttributeError` absent from output.
- `test_a_hand_edited_facts_list_line_is_E_FREEZE_LEDGER_UNREADABLE_not_a_traceback` — `facts: [1,
  2]` → same.
- `test_a_hand_edited_int_condition_line_is_E_FREEZE_LEDGER_UNREADABLE_not_a_false_unchanged` —
  `condition: 42` → `E-FREEZE-LEDGER-UNREADABLE`, `"unchanged"` absent from stdout (the false
  verdict the un-fixed code produced).

**Verified by mutation**: removed both `isinstance` checks, re-ran the three tests — all three
failed (two on a raw `AttributeError` traceback reaching `main`, one on `code == 0` where 1 was
expected). Restored, re-ran — all three pass, plus the full `test_freeze.py`/`test_apparatus.py`
pair at 95 passed. Diffed the restored file against the pre-mutation copy — byte-identical.

### Minor 2 — same shape, one layer down: `replay_ledger`'s not-a-mapping guard, made reachable

The parametrized `not-a-mapping` fixture in `tests/test_apparatus.py`'s
`test_replay_ledger_a_malformed_line_is_E_FREEZE_LEDGER_UNREADABLE` was `"[1, 2, 3]"`, which the
NEXT guard (missing-keys) also catches on its own — deleting the `isinstance(doc, Mapping)` guard
left it green. Replaced with `'["phase", "condition", "facts"]'` — a JSON array whose ELEMENTS are
the three key strings, so the missing-keys check's `"phase" not in doc` reads `False` (the string
IS an element) and cannot substitute for the deleted guard; without it, the next line
(`doc["phase"]`) raises `TypeError: list indices must be integers`, not the coded refusal.
Confirmed by running: with the guard present, the new fixture still raises
`E-FREEZE-LEDGER-UNREADABLE` (all three arms pass); with it deleted, only this arm's assertion
fails, on the wrong exception type reaching `pytest.raises(ContractError)`.

### Major 1 — the credential-before-the-probe ordering, pinned with the reviewer's own discriminating shape

Added `test_m1_credential_check_precedes_the_metered_call_end_to_end_through_main`: a probe that
appends to a MARKER FILE on every call, driven through `main`, credential genuinely unset and
`.env` deleted. Asserts exit `EXIT_EXTERNAL`, `E-APPARATUS-RAISED` present, the marker file
**absent** (the probe was never called), and the ledger unchanged.

**Verified against both of the reviewer's mutations, applied by hand and reverted (not persisted —
there is no lever in shipped `freeze.py` to keep both branches live at once without duplicating the
check, so this was run as a manual probe rather than kept as a second copy of the test):**
- **M-b** (gate (k)'s block moved from `_precheck` into `command_freeze`, AFTER
  `observer.observe_round(...)`): the new test fails — the marker file exists after the call, since
  the probe genuinely ran before the credential was ever checked.
- **M-a** (the same block moved into `command_freeze`, but BEFORE `_probe_for` — still after
  `_precheck` returns): the new test passes, since the probe is still never reached.

Both mutations applied and reverted against a saved pre-mutation copy of `freeze.py`; the restored
file diffs byte-identical to the pre-mutation copy, and `test_freeze.py` is green at HEAD (the
check remains inside `_precheck`, unmoved — no production code changed for this finding, only the
test).

### Major 3 — both warnings, pinned by asserting the printed text

Four new tests:
- `test_w_freeze_lock_moved_fires_when_the_captured_copy_and_the_repo_disagree` — asserts
  `"W-FREEZE-LOCK-MOVED"` actually appears in stderr when the captured `environment/uv.lock` and a
  hand-written repo `uv.lock` disagree.
- `test_w_freeze_lock_moved_is_silent_when_the_captured_copy_and_the_repo_agree` — the negative
  control.
- `test_w_freeze_lock_moved_is_silent_when_nothing_was_captured` — the `not captured` case.
- `test_w_apparatus_unanswered_fires_at_freeze_when_a_declared_fact_comes_back_null` — a probe
  answering a real value during the run and `null` only once `freeze` calls it; asserts
  `"W-APPARATUS-UNANSWERED"` in **stdout** (`warn_unanswered`'s own render call, `command_run`'s
  precedent — `_warn_lock_moved` prints to stderr instead, which is why the lock test above reads
  `.err` and this one reads `.out`).

**Verified by mutation, each against the specific new test it pins, reverted after:** replacing
`_warn_lock_moved`'s body with a bare `return` fails the "fires" test (assertion on the missing
text) while leaving the two silent tests green, as expected; deleting the four-line
`warn_unanswered` block fails the unanswered test. Both restored; `diff` against saved pre-mutation
copies is byte-identical; full `test_freeze.py` green at 35 (before Minor 8's widening) and 38
(final) passed.

### Minor 1 — built the exit-0 output Decision 10/8 specify, rather than filing it

`command_freeze`'s success path now prints each condition's OBSERVED facts (read off
`observer.observations.facts_document()`, which by construction of the exit-0 path equals what
this round just observed — a disagreement would have raised `E-APPARATUS-CHANGED` first) and a
final `"N condition(s) probed"` line, replacing the bare `unchanged` verdict word. Pinned by
`test_exit_0_prints_the_observation_per_condition_and_the_count`, asserting both `"model_revision="`
and `"2 condition(s) probed"` appear in stdout. The one pre-existing test asserting `"unchanged"`
(Major 2's `condition: 42` arm) asserts its ABSENCE, which still holds — that arm never reaches the
print path at all.

### Minor 4 — `_warn_lock_moved`'s docstring narrowed to the side it actually guards

"**Absent on either side is not a move**" → "**Absent on the CAPTURED side is not a move**", with a
new sentence stating the asymmetry explicitly (the current side IS guarded: a deleted repo
`uv.lock` still warns, since `uv_lock_info` answers `(None, None)` and that disagrees with any
non-empty captured hash). Pinned by a new fifth test,
`test_w_freeze_lock_moved_fires_when_the_repos_lockfile_is_deleted` — captured side present, repo's
`uv.lock` absent, warning fires.

### Minor 5 / Minor 6 — the `spec-defects.md` filing's citation and owner

- The mis-attribution ("`freeze`'s own 'resolves the template NOW' claim (`reference.md` § Operation
  commands)") is fixed: the phrase is now correctly identified as a code comment in
  `src/publishable/freeze.py`, and the sentence no longer claims `reference.md` says anything of
  the kind.
- The garbled opening of "The check its owner must make" paragraph is rewritten for clarity (option
  (a) and option (b), each now a complete, readable sentence rather than a dangling clause).
- **Owner assigned**: the title line now reads *"Owner: H9 (option a); H8b task 12 may instead take
  the narrower option (b)"* — routed per the reviewer's own suggestion (H9 resolves the identical
  template from the identical two run-start artifacts for `resume` and inherits the same hazard;
  task 12 is this slice's own document-and-code-cleanup task, available if it prefers the narrower
  fix instead of waiting on H9).

### Minor 7 — a nonexistent run directory now routes to `E-IO-FAILED`, not `E-FREEZE-NO-CONFIG`

`_precheck` now raises a bare `FileNotFoundError` (an `OSError` subclass) at its very first line
when `run_dir` is not a real directory, before any of the seven gates run. Uncaught locally, it
propagates through `command_freeze` and `cli._dispatch` to `main`'s existing generic `OSError`
handler, landing on `E-IO-FAILED` at exit 1 — `validate`'s own precedent for the identical class of
unanticipated path problem. Pinned by
`test_a_nonexistent_run_directory_is_E_IO_FAILED_not_E_FREEZE_NO_CONFIG`, asserting `E-IO-FAILED`
present and `E-FREEZE-NO-CONFIG` absent.

### Minor 8 — F2 and F5 arm one widened to three conditions, second one moving/raising

Both rebuilt over `sweep.grid: {instrument.model: [m1, m2, m3]}` (the two templates' `choices`
widened to admit `"m3"` to make this possible):
- **F2** (`test_f2_freeze_sees_a_moved_fact`): a probe reading per-model answer files; only
  `m2.txt` is rewritten between the run and `freeze`. Asserts the new ledger lines are exactly
  `["00_model=m1", "01_model=m2"]` — the first condition's own (unmoved) observation recorded, the
  second's moved value recorded and the round then aborted, the third never reached.
- **F5 arm one** (`test_f5_arm_one_...`): a probe that raises only when `cfg.parameters.instrument.
  model` matches a trigger file's content, set to `"m2"` before `freeze`. Asserts the new ledger
  lines are exactly `["00_model=m1"]` — nothing for the raising second condition, nothing for the
  third.

Both properties — "up to and including the mover, none after" / "none for the raiser, none after"
— are now measured on a fixture that can actually distinguish them from a one-condition fixture
that happened to agree with the claim, rather than argued from the loop's shape.

### Minor 9 — the redundant second `replay_ledger` call removed

`_Ready` gained an eighth field, `baseline: apparatus.Observations` — the SAME object gate (i)
already built while validating the whole ledger. `command_freeze` now passes `ready.baseline`
straight to `Observer(observations=...)` instead of calling `apparatus.replay_ledger(run_dir)` a
second time and discarding gate (i)'s result. `mypy` clean; full suite unaffected (this reads the
identical object the second call would have reconstructed).

### What was grepped, and its scope, this round

- Grepped `1fc05dc:src/publishable/apparatus.py` and `HEAD:src/publishable/apparatus.py` for
  `isinstance` before writing the Major 2 fix, to confirm the reviewer's own two `grep -c` results
  (both `0` for the missing guards) rather than trusting the review's prose alone — reproduced.
- Grepped `tests/`, `src/`, and the four documents for `W-FREEZE-LOCK-MOVED` before writing Major
  3's fix, to confirm the reviewer's "zero occurrences" claim — reproduced (zero, before this
  round's tests).
- Grepped the repo for the literal phrase `resolves the template NOW` before fixing Minor 5: one
  site, `src/publishable/freeze.py`, a code comment — confirmed the reviewer's finding rather than
  taking it on faith.

### Corrects, without retro-editing, the original report's own Minor 3

The original report (above the `---`) states "the Command table still holds ten `NOT BUILT` rows."
Measured through `_status_tables()["Command"]` at `2675cc8`, that count is **eleven** — ten is the
plan's own figure for the state after BOTH `diff` and `freeze` flip, carried forward as if it
described the state after only `freeze`'s. The conclusion the number was offered for (the
`{"built", "NOT BUILT"}` control does not go vacuous) holds regardless, and both CLI-table tests
still pass unedited. Left as a correction here rather than editing the original section, per this
project's own rule for its development record.

### Findings not closed, and why

None. All three Majors and all nine Minors are addressed above, each with the test or the fix, or
both, that closes it.
