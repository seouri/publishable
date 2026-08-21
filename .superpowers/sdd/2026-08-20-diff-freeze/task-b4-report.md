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
