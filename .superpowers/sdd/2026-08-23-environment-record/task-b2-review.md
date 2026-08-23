# Batch 2 review — task 3 (the write) plus controller ruling on arm S

**Verdict: PASS.**

Commits reviewed: `3b583f2` (task 3), `354bb46` (controller ruling on arm S). Full suite at HEAD,
run twice (once before mutation work, once after, foreground, caches cleared both times):
**2969 passed, 1 skipped, 2 xfailed** — exactly the expected count. Gates: `ruff check .` — all
checks passed; `ruff format --check .` — 93 files already formatted; `mypy` — success, 52 source
files. All four gates clean.

## Findings

None. No Critical, Major, or Minor findings survive verification.

## What was verified by behaviour (not by reading)

1. **Capturing the guard pin forward worked.** Diffed arm P
   (`tests/test_cli.py::test_h8b_arm_d_the_five_figures_diff_reads`) against task 1's advance spec
   (`task-1-brief.md` row P: `set(hardware) == {"cpu_count"}`, three pops, three assertions, the
   `assert environment == {...}` line byte-identical). The committed edit matches exactly, character
   for character. This is the direct counter-example to H6a's batch-2 Major (a pin captured against a
   superseded signature) — captured against the shape task 3 would produce, it required no
   round-trip.

2. **All six of task 3's prescribed mutations reproduced exactly as reported**, each applied to a
   copy, restored by editing back (never `git checkout --`), and each restoration re-verified by
   re-running the targeted tests plus `diff` byte-identity against the saved original:
   - Delete `"os"` → Fixtures A, D and arm P all fail (`KeyError`/order mismatch). Confirmed.
   - `os` as `platform.platform()` → Fixture A fails. Independently probed the brief's mechanism
     claim: `platform.system = lambda: 'X'; platform.release = lambda: 'Y'; platform.machine = lambda: 'Z'; platform.platform()`
     still returns the real `macOS-26.5.2-arm64-arm-64bit-Mach-O` on this machine, unaffected by the
     patches — confirming the report's Disagreement 2 (the brief's "patches reach `platform.platform()`"
     claim is false; its conclusion that mutation 2 fails Fixture A still holds, for the correct
     reason: no real-machine string can equal the sentinel composition either way).
   - `hostname` from `platform.uname().node` → Fixture B fails. Confirmed.
   - `hardware` as bare `os.cpu_count()` → Fixture C arm 1 fails, arm P fails, **and** Fixture C arm 2
     fails louder than the brief states, with `TypeError: argument of type 'NoneType' is not iterable`
     rather than a clean assertion failure (the bare-int mutation writes `hardware: null` under a
     patched `None` count, breaking `"cpu_count" in hardware` outright). Reproduced exactly; the
     report's "stronger than stated" claim is correct, not a miscount.
   - `os.cpu_count() or 1` → only Fixture C arm 2 fails; arm 1 (patched to `77`, truthy) passes.
     Confirmed.
   - Swap `os`/`hostname` insertion order → Fixture D fails, arm P **passes** (order-blind, confirmed
     by popping by name). Confirmed.

3. **The arm-S mutation was re-run independently.** Made `study.py::_redact`'s hostname branch
   unconditional (`if isinstance(environment, dict): environment["hostname"] = REDACTED`, dropping the
   `is not None` guard). Ran the full `test_study.py` file and the whole-suite-filtered `-k study`:
   exactly one failure,
   `test_study_add_leaves_hostname_untouched_when_absent_from_the_source`, nothing else in the file or
   in any other `study`-named test. Reverted by editing back, `diff` confirmed byte-identical, then
   re-ran `test_study.py` to confirm 42/42 pass again.

4. **The property arm S protects is unchanged; only its source of an absent key became explicit.**
   Before the controller's edit, `_real_run`'s record never wrote `hostname` at all (missing key);
   `_redact`'s guard is `environment.get("hostname") is not None`, and `dict.get` on a genuinely
   missing key and on an explicitly `del`eted key both return `None` — the code path exercised is
   identical either way. The edit changes *how* the absent state is produced, not what `_redact` does
   with it, and the mutation above proves the arm still discriminates the real defect (unconditional
   redaction). Adjudication: the ruling is sound — a legitimate, minimal, behaviour-preserving edit to
   a test whose own premise ("real records never carry hostname") was falsified by this same batch's
   write, using exactly the "STOP and report; the route is a controller ruling" process task 3's own
   brief specifies. Without the edit, this test would be permanently unwinnable once `hostname` became
   unconditional (Disagreement 1 in `task-b2-report.md`), and no task in the plan (including a
   docstring-only task 7) is authorized to touch its body otherwise.

5. **`hostname`'s and `hardware`'s sources checked directly, no double-definition.** Grepped
   `src/publishable/*.py` for `gethostname`/`socket\.`: two call sites,
   `run_identity.py:73` (`socket.gethostname()` for the run lock, pre-existing) and
   `cli.py:3827` (`socket.gethostname()`, new). Both call the *same* stdlib function directly — this
   is not "two sources for one fact" in the sense the repo's own history warns about (two different
   functions that can drift, e.g. `socket.gethostname()` vs. `platform.uname().node`); it is the same
   one-line call made from two places, which cannot diverge. `os.sched_getaffinity` confirmed absent
   on this machine (`hasattr(os, "sched_getaffinity")` → `False`), ruling it out as Decision 8 claims.

6. **Fixtures discriminate against the stated wrong implementations** — confirmed by literally
   building each wrong implementation above and watching the correct fixture fail while the others
   stay green (mutations 1–6). No fixture passed against its named wrong implementation.

7. **`cpu_count: null` downstream, checked by reading every reader.** Grepped
   `"environment"`/`.get("environment")` across `src/publishable/*.py`: exactly two readers exist —
   `diff.py:234` reads only `uv_lock_hash`, `study.py:149` reads only `hostname`. Nothing reads
   `hardware`/`cpu_count` anywhere in `report.py`, `study.py`, or `diff.py`, so a `null` count is
   inert downstream — confirmed structurally (matches Correction 10) rather than assumed.

8. **Ruling Q's activation, verified end-to-end through the installed console script**, independently
   of the report's own run: scaffolded a fresh project outside this repo
   (`publishable new` / `generate experiment` / `run`), read the raw `run.yaml`:
   ```
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
   then built a bundle with `study new` / `study add --as main` outside any repository and read the
   bundled member's raw YAML:
   ```
   hostname: <redacted by study add>
   os: Darwin-25.5.0-arm64          (unredacted, byte-identical to source)
   hardware: {cpu_count: 8}          (unredacted, byte-identical to source)
   ```
   Matches the report's claim exactly, confirmed independently rather than re-reading the report's
   own transcript.

9. **Pre-edit grep re-run.** `git show 2b18435:src/publishable/cli.py | grep -cE '\bos\.|\bplatform\.|\bsocket\.|^import os\b'` → `0`, confirming the "zero hits before this task" claim.

10. **Arms Q, R, T, U — confirmed unmoved and still able to fail.** `git diff 9fa86b4..354bb46 --stat`
    shows only `src/publishable/cli.py`, `tests/test_cli.py`, `tests/test_study.py`, and the report —
    nothing else in `tests/` touched. Ran
    `test_h8b_arm_c_the_records_key_lists_status_and_exit` (Q),
    `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text` ×3 (R),
    `test_h6a_arm_b_an_excluded_env_file_moves_the_hash_today` and
    `test_h6a_arm_c_the_seven_other_present_figures_are_unmoved` (U), and
    `test_h6b_arm_t_the_git_layers_two_codes_at_the_cli` (T, from batch 1) — all pass, all unedited.

11. **Test-count reconciliation.** Baseline 2964 (batch 1) + 5 new (Fixtures A, B, C×1, C×2, D) = 2969.
    Full suite after both commits: 2969 passed, 1 skipped, 2 xfailed — reconciles exactly, no miscount.

## Verified by reading only

- `secrets.py`'s stale enumeration (*"assembled from `os`, `hostname`, `hardware` and `uv.lock`
  alone"*) and `study.py::_redact`'s docstring (*"`hostname` is never written today"*, now false)
  remain untouched — correctly so: both are Correction 9 / task 7's, scheduled for batch 4
  (§ Batching table: B4 is tasks 6–7). Task 3 must not touch them and did not.
- The controller ruling (`354bb46`) is not yet reflected in `progress.md` (still shows only batch 1)
  or in the plan's "Live overrulings" section. This is process housekeeping rather than a code
  defect — no future task's *behaviour* depends on it (task 4 only needs to observe that arm S
  currently passes, which it does), but it is exactly the pattern CLAUDE.md's own misreadings list
  flags (*"a ruling that overrules a brief has to reach the brief"*). Recommend the controller append
  this ruling to `progress.md`/the plan's overrulings list at the next available point, not a blocker
  for this batch.
- `os`/`hardware` correctly excluded from `diff`'s and `report`'s rendering per Decision 14 — matches
  reading of `diff.py`/`report.py`, no new row added, none expected at this task.

## Gates

- `uv run pytest` — 2969 passed, 1 skipped, 2 xfailed (run twice, foreground, caches cleared).
- `uv run ruff check .` — All checks passed.
- `uv run ruff format --check .` — 93 files already formatted.
- `uv run mypy` — Success: no issues found in 52 source files.

## Summary for the controller

Task 3's write, arm P's edit, and all four new fixtures are exactly as specified and verified by
mutation, not just by reading. The one disclosed blocker (arm S's second test, falsified by this
task's own write) was resolved by a controller ruling that is minimal, behaviour-preserving, and
independently re-provable — the arm still fails under the unconditional-redaction mutation and passes
otherwise, and the property it protects ("absence is not invented") is unchanged; only the mechanism
producing the absent-`hostname` state moved from accidental to explicit. Full suite, all four gates,
clean.
