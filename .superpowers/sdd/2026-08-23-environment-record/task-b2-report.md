# Task 3 report — the write: `os`, `hostname`, `hardware`

**Status: complete, with one blocker for the controller — not clean.** The write, arm P's edit, and all
four new fixtures are done, committed, and verified by mutation and by the installed console script.
But this task's own write makes an existing, unauthorized test (`test_study.py`'s arm S, second test)
fail, and no task in the plan is positioned to fix it without an unauthorized edit. Full suite is
**2968 passed, 1 failed, 1 skipped, 2 xfailed** — not the clean gate the global constraints require.
Reporting this as found rather than absorbing it or editing around it.

## The write

`src/publishable/cli.py`: added `os`, `platform`, `socket` to the stdlib import block (alphabetical,
after `json`, before `sys`); `command_run`'s `provenance["environment"]` dict gained `os`, `hostname`,
`hardware` in the key order `manager, python_version, os, hostname, uv_lock, uv_lock_hash, hardware`,
exactly the literal, comments and all, given in the brief.

**Pre-edit grep, re-run and confirmed** (`git stash` to the pre-task-3 tree): `\bos\.|\bplatform\.|\bsocket\.|^import os\b`
over `cli.py` → **zero hits**, matching the brief's claim exactly.

## End-to-end, through the installed console script, outside this repo

Built a fresh project under the scratchpad (`/private/tmp/.../scratchpad/h6b-e2e/my-study`), scaffolded
with `publishable new`, generated `cohort-pilot` against an `input_dir`/`output_dir` outside both the
new project and this repo, filled the required `metadata` fields, committed, and ran
`publishable run configs/cohort-pilot/config.yaml` through the venv's installed `publishable` script
(not a direct call — the brief's own distinction: "the value is written by `command_run` and read by
nothing, so only a real record proves it lands"). Read `run.yaml`'s `provenance.environment` key by key
from the raw file:

```yaml
  environment:
    manager: uv
    python_version: 3.13.7
    os: Darwin-25.5.0-arm64
    hostname: macbookair.lan
    uv_lock: null
    uv_lock_hash: null
    hardware:
      cpu_count: 8
```

Exact key order matches the brief. `os` is the composed three-part form (not `platform.platform()`'s
marketing string). `hostname` is the real machine name via `socket.gethostname()`. `hardware` is a
one-key mapping with a real `cpu_count`.

**Where each of the three values comes from, and why that source:**
- **`os`**: `f"{platform.system()}-{platform.release()}-{platform.machine()}"` (Decision 6). Not
  `platform.platform()`, which on this machine returns `'macOS-26.5.2-arm64-arm-64bit-Mach-O'` — the
  marketing name/version, not the kernel `uname()` reports (`Darwin`/`25.5.0`), and whose component
  count varies by platform. Verified independently (see Disagreement 2 below) that `platform.platform()`
  does not even route through the three patched functions on this machine, strengthening rather than
  weakening the case against it.
- **`hostname`**: `socket.gethostname()` (Decision 7), the same call `run_identity.py` already uses for
  the run lock (`json.dump({"host": socket.gethostname(), ...})`). Not `platform.uname().node`, a second
  spelling of the identical fact — the "two sources for one fact is how the two drift" argument
  `report`'s `repo_root` row already establishes.
- **`hardware`**: `{"cpu_count": os.cpu_count()}` (Ruling O, Decision 8). Not `gpu` (apparatus fact, not
  provenance). Not `len(os.sched_getaffinity(0))` — confirmed absent on this platform:
  `python3 -c "import os; print(hasattr(os, 'sched_getaffinity'))"` → `False`. Not `os.process_cpu_count()`
  (3.13+, project targets ≥3.11).

## The `None`-`cpu_count` behaviour

`os.cpu_count()`'s documented `None` return is written through, not substituted. Fixture C arm 2
monkeypatches `os.cpu_count` to return `None` and asserts the **key is present with a `None` value**,
distinct from the key being absent — verified against the raw file, not just `yaml.safe_load`
(`safe_load` would silently equate an omitted key with an explicit `null`; the raw text at
`hardware:\n      cpu_count: null` confirms the key is written).

## Bundle-redaction check for `hostname` (Ruling Q's activation)

Built a bundle under the scratchpad, outside any repository, via `publishable study new`/`study add`
through the installed console script. `study.py::_redact`'s existing `hostname` wiring — written against
a key nobody wrote before this task — now activates:

```yaml
  environment:
    manager: uv
    python_version: 3.13.7
    os: Darwin-25.5.0-arm64
    hostname: <redacted by study add>
    uv_lock: null
    uv_lock_hash: null
    hardware:
      cpu_count: 8
```

`os` and `hardware` travel **unredacted**, byte-identical to the source record; `hostname` is redacted.
This is the correct behaviour per Ruling Q and confirms the activation the brief flagged as a real
behaviour change even though `study.py` itself was not touched by this task.

## Arm P — exactly three pops, three assertions, nothing else

`git diff` on the arm:

```diff
     python_version = environment.pop("python_version")
+    os_value = environment.pop("os")
+    hostname = environment.pop("hostname")
+    hardware = environment.pop("hardware")
     assert environment == {"manager": "uv", "uv_lock": None, "uv_lock_hash": None}
     assert isinstance(python_version, str) and python_version
+    assert isinstance(os_value, str) and os_value
+    assert isinstance(hostname, str) and hostname
+    assert isinstance(hardware, dict) and set(hardware) == {"cpu_count"}
```

The `assert environment == {...}` line is byte-identical to what task 1 captured. `python_version`'s pop
and assertion are untouched. No other line in the test moved.

## Fixtures A–D

- **Fixture A** (`test_h6b_arm_a_os_is_composed_from_installed_sentinels`): monkeypatches
  `platform.system`/`release`/`machine` to sentinels, runs end to end, asserts the exact composed
  string. Sentinels, not a recomputed comparison — a recomputing test cannot distinguish implementations.
- **Fixture B** (`test_h6b_arm_b_hostname_is_socket_gethostname`): monkeypatches `socket.gethostname`,
  asserts the record carries it verbatim.
- **Fixture C**, two arms: arm 1 (`..._arm_1`) monkeypatches `os.cpu_count` → `77`, asserts
  `{"cpu_count": 77}`; arm 2 (`..._arm_2_none`) monkeypatches it → `None`, asserts the key is **present**
  with value `None`.
- **Fixture D** (`test_h6b_arm_d_environment_key_order`): asserts the exact enumerated key-order list
  read via `yaml.safe_load`, never iterating the collection under test.

## Mutations — full unfiltered suite reasoning per mutation, restored and re-verified each time

All six run against a copy (`/tmp/cli.py.orig`), restored with `cp` (not `git checkout --`), each
restore verified **byte-identical** by `diff` and then **by re-running** the targeted tests (not by
`git status`).

1. **Delete `"os"`** → `test_h6b_arm_a` fails (KeyError), `test_h6b_arm_d` fails (order/membership),
   `test_h8b_arm_d` (arm P) fails (KeyError on `.pop("os")`). Matches the brief exactly.
2. **`os` computed as `platform.platform()`** → `test_h6b_arm_a` fails:
   `assert 'macOS-26.5.2-arm64-arm-64bit-Mach-O' == 'Fixtureos-9.9.9-fixarch'`. **Disagreement with the
   brief's stated mechanism, reported rather than absorbed**: the brief argues the patches to
   `platform.system`/`release`/`machine` "reach" `platform.platform()` through module-global lookup.
   Verified directly:
   ```
   uv run python -c "import platform; platform.system=lambda:'X'; platform.release=lambda:'Y'; platform.machine=lambda:'Z'; print(platform.platform())"
   ```
   → prints the real machine string (`macOS-26.5.2-arm64-arm-64bit-Mach-O`), unaffected by the patches.
   CPython's `platform.platform()` does not call the three module-level functions the same way `os`'s
   f-string does; it derives the string through `uname()`/a cache. **The brief's mechanism claim is
   false; its conclusion (mutation 2 fails Fixture A) still holds**, because no real-machine
   `platform.platform()` output can equal the sentinel composition either way.
3. **`hostname` from `platform.uname().node`** → `test_h6b_arm_b` fails:
   `assert 'macbookair.lan' == 'pinhost.example.invalid'` (unaffected by the `socket.gethostname` patch,
   as designed). Matches the brief.
4. **`hardware` as the bare int** (`os.cpu_count()` instead of `{"cpu_count": os.cpu_count()}`) →
   `test_h6b_arm_c_hardware_carries_cpu_count_arm_1` fails (`77 == {"cpu_count": 77}` false),
   `test_h8b_arm_d` (arm P) fails (`isinstance(hardware, dict)` false). Arm 2 also failed, more loudly
   than the brief states — a `TypeError: argument of type 'NoneType' is not iterable` on
   `"cpu_count" in hardware` when `os.cpu_count()` is patched to `None`, since the bare-int mutation
   under a `None` count writes `hardware: null` rather than a dict. The brief names only arm 1 and arm P
   for this mutation; arm 2 failing too is consistent (not a disagreement, just a stronger result than
   stated) since the mutation breaks the mapping shape in every branch, not only the populated one.
5. **`os.cpu_count() or 1`** → **only** `test_h6b_arm_c_hardware_carries_cpu_count_arm_2_none` fails
   (`assert 1 is None`); arm 1 (patched to `77`, truthy) passes identically. Exactly the brief's claim —
   this is the mutation arm 2 exists to catch.
6. **Swap `os`/`hostname` insertion order** → `test_h6b_arm_d_environment_key_order` fails (order
   mismatch at index 2); `test_h8b_arm_d` (arm P) **passes**, confirmed order-blind as the brief claims
   (arm P only pops by name and checks the residual set, never list order).

## Arms Q, R, S, U — run, not edited

- **Q** (`test_h8b_arm_c_the_records_key_lists_status_and_exit`) — pass.
- **R** (`test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text`, ×3 parametrized) — pass.
- **U** (`test_h6a_arm_b_an_excluded_env_file_moves_the_hash_today`,
  `test_h6a_arm_c_the_seven_other_present_figures_are_unmoved`) — pass.
- **S** — `test_study_add_redacts_hostname_when_present_on_a_synthesized_record` passes.
  **`test_study_add_leaves_hostname_untouched_when_absent_from_the_source` FAILS**, and this is the
  blocker — see next section.

## Disagreement 1 (the blocker): arm S's second test cannot pass without an edit no task is authorized to make

`test_study_add_leaves_hostname_untouched_when_absent_from_the_source` asserts, over a **real**
`run_a_project` record, `"hostname" not in redacted["provenance"]["environment"]`. Its own docstring's
premise — "today's real records never carry `hostname` at all" — is exactly what this task's write makes
false: `socket.gethostname()` is unconditional, so every real run now carries a `hostname` string, and
`study.py::_redact`'s existing branch (`if ... environment.get("hostname") is not None: environment["hostname"] = REDACTED`)
fires and sets the key to the redaction marker rather than leaving it absent. The key is very much `in`
the dict afterward (with value `<redacted by study add>`), so the assertion fails.

**Checked, not assumed:**
- **This is not what Correction 9 names.** Correction 9 says `_redact`'s and `_fixture_y_record`'s
  *docstring* measurements go stale at task 3, owned by task 7 — a docstring edit, not an assertion
  fix. It does not name this test's assertion.
- **Both task 3's own brief and task 4's step list affirmatively claim this arm passes without an edit
  after task 3, and independently after task 4** ("Run arms Q, R, S and U and report that each passes
  without an edit" here; "Run arm S and report that both its tests pass without an edit" in task 4).
  Both claims are wrong for this one test, checked directly rather than repeated.
- **No task in this plan changes `_redact`'s behaviour or this test's body.** Task 4's own Ruling Q
  states the `hostname` redaction wiring "already exists" and is being **pinned**, not changed — Fixture
  E is additive, beside this test, not in place of it. Task 7 touches only `secrets.py`'s docstring and
  `_fixture_y_record`'s docstring (explicitly not a body edit). This test's body has **no authorized
  editor** anywhere in the plan.
- **Not self-fixed by editing the arm**, per this task's explicit instruction: arm S has no authorized
  editor for task 3, and "if one must move, STOP and report it; the route is a controller ruling, not a
  justified edit."

**Options for the controller, named without choosing one:**
1. Re-source the test from a hand-built record (like `_fixture_y_record`, but with `hostname` omitted)
   rather than a real run — preserves the actual property under test ("absence in, absence out"; H6b
   didn't ask this test to assert anything about *presence*), and stops depending on an environment fact
   that H6b's own charter makes universally present.
2. Retire the test as unreachable from a real run now that `hostname` is unconditionally written, on the
   grounds that its real-run half is now permanently subsumed by Fixture E's positive-control read.
3. Authorize an edit to this one assertion (not the whole arm) under a named task, restating the docstring
   to match.

**Not implemented here** — arm S's test bodies have no authorized editor for task 3 or (per its own step
list) for task 4 either, and an unauthorized edit is exactly the failure mode `CLAUDE.md`'s guard-pin
device exists to prevent.

## Disagreement 2 (mechanism, not conclusion): `platform.platform()` does not read through the patched functions

Covered under mutation 2 above. The brief states `platform.platform()` "resolves `system`/`release`/
`machine` through module-global lookup, so Fixture A's patches reach it." Measured directly: they do
not. `platform.platform()`'s output on this machine is unaffected by patching all three functions. The
brief's **conclusion** — mutation 2 fails Fixture A — is still correct, just for a different reason (the
unaffected real string can never equal the sentinel composition either way, not because the patches
"reach" the call and produce a longer string).

## Test summary

Foreground `uv run pytest -q`, clean caches before each run:
- Before this task (from batch 1): 2964 passed, 1 skipped, 2 xfailed.
- After this task's write and fixtures: **2968 passed, 1 failed, 1 skipped, 2 xfailed.**
- Reconciliation: 2964 + 5 (Fixtures A, B, C×2, D) = 2969 = 2968 passed + 1 failed. The delta is exactly
  **+5 as specified**; the sole failure is the pre-existing arm S test broken by this task's write
  (Disagreement 1), not a miscount.
- `ruff check .` — All checks passed. `ruff format --check .` — 93 files already formatted.
  `mypy` — Success: 52 source files. **`pytest` is the one gate not clean**, for the reason above.

## `.superpowers/sdd/.gitignore`

Found clobbered to a bare `*` (by `task-brief`/`sdd-workspace`, as `CLAUDE.md` warns) before committing;
restored from `HEAD` (content verified against `git show HEAD:.superpowers/sdd/.gitignore`, diffed
clean after restore) rather than left broken.

## Files touched

- `src/publishable/cli.py` — three imports, three keys in `command_run`'s `provenance["environment"]`.
- `tests/test_cli.py` — arm P's three pops/three assertions; four new tests (Fixtures A, B, C×2, D).
- `.superpowers/sdd/2026-08-23-environment-record/task-b2-report.md` — this report.

## Concerns

**One blocker, stated above**: `tests/test_study.py::test_study_add_leaves_hostname_untouched_when_absent_from_the_source`
fails after this task's write and has no authorized editor anywhere in the plan as written. The full
suite is not green (2968 passed, 1 failed, 1 skipped, 2 xfailed) as a direct, disclosed consequence.
Everything else this task owns — the write, arm P, Fixtures A–D, all six mutations, the console-script
end-to-end read, and the bundle-redaction activation check — is verified and committed.
