## Task 1

**Pointer: Rulings V, W and X all bind this task (design Decisions 1–3), through § The guard pin.
Read that section of the design before writing a line.**

**Ruling U's discipline from H9a still binds and this task is where it lands: the pin comes first, in
the shape the design has already decided, and every arm gets an authorized editor or an explicit
NONE.** H6a captured arms against a superseded signature and forced a later task into an unauthorized
edit; H6b and H9a captured forward and their edits matched byte for byte. **You are the only task in
this slice that may create an arm.** Two shipped arms are **re-authorized** here — one whose current
editor is a closed slice's task and one whose current editor is **NONE** — and the re-authorization is
a controller ruling recorded in the design, not something you may extend.

**Also binding: proving an arm cannot move is NOT proof the line is pinned.** For each arm, run a
mutation in the **production** code and show the arm fails, against the **full suite**, and report the
count as full-suite. An arm you cannot make fail is not an arm.

Build arms **A** and **G** in `tests/test_cli.py`; **re-authorize** arms B, C, D and E by editing only
their docstrings' editor clauses; **cite** arms F and H.

- **Arm A — a crash-and-resume round trip equals a straight-through run, leaf by leaf.** `resume` does
  not exist yet, so **capture the `run` half now** as a normalized golden and leave the resume half as
  a test marked `xfail(strict=True)` naming task 9 as what makes it pass. Walk the record into a sorted
  list of `(dotted_path, value)` leaves, normalizing exactly: any key named `at`, `started_at`,
  `wall_seconds`, `run_id`, `hostname`, `attempts`; any absolute path under `tmp_path`; and the three
  hashes. **Do not extend that list**, and if you must, say so in the report as a finding — *a
  normalization decided after seeing a diff is a normalization chosen to hide it*.
- **Arm G — the takeover's mutual exclusion, deterministically.** Two threads, one run directory whose
  `lock` names a dead pid, a `threading.Barrier` released **between the liveness verdict and the lock
  replacement**. Assert exactly one holder and exactly one `E-RUN-LOCKED`. The takeover does not exist
  yet, so this too is `xfail(strict=True)` naming task 14. **Cite the five-process probe in your
  report as the discovery instrument and do not use it as the pin** — a probe proves the moment, a test
  proves tomorrow.
- **Arm B — re-authorize.** `test_h8b_arm_a_the_run_directorys_root`. Replace its editor clause with:
  *SOLE AUTHORIZED EDITOR: H9b task 4.* Copy the post-edit list from the design verbatim into the
  docstring: `['conditions', 'config.yaml', 'environment', 'executions.jsonl', 'identity.json',
  'manifest', 'run.yaml', 'sweep.yaml']`. **Change no assertion.**
- **Arm C — re-authorize.** `test_h9a_arm_d_the_executions_jsonl_line_key_set`, whose clause reads
  **SOLE AUTHORIZED EDITOR: NONE**. Replace it with *SOLE AUTHORIZED EDITOR: H9b task 6, by controller
  ruling recorded in the H9b design's Decision 5*, and copy the post-edit set verbatim:
  `{step, scope, condition, repeat, status, started_at, wall_seconds, error, returned,
  recorded_columns}`. **Change no assertion.** Say in your report that this is a NONE arm being
  re-aimed, and by what authority.
- **Arm D — re-authorize.** The shipped `assert "and 7 fixed files in that directory:" in out`. Add a
  comment naming *SOLE AUTHORIZED EDITOR: H9b task 4*, post-edit `8`, and stating that the set-to-set
  comparison beside it is **self-maintaining and must not be edited**.
- **Arm E — re-authorize.** `test_reference_cli_tables_are_parsed_at_all`'s
  `assert ("resume", "NOT BUILT") in tables["Command"]`. Comment: *SOLE AUTHORIZED EDITOR: H9b task
  15*, post-edit `("resume", "built")` plus a new `("reproduce", "NOT BUILT")` row-presence line; the
  `set(NOT_BUILT_COMMANDS)` equalities are self-maintaining.
- **Arm F — cite.** H9a arm A and arm B. Name them and say which claim each holds. **Do not
  re-capture** — that recreates H8a's *same list pinned twice*.
- **Arm H — cite.** H8b arm B, H8a arms A and B, H8c task 17 arm A, `sweep.yaml`'s key list, H9a arms
  C and E. Per arm, one line saying what it already holds.

**Must not touch:** anything under `src/`. No `*.md`. **No existing test's assertions** — only the four
editor clauses named above.

**Report:** every arm, its mutation, the full-suite failure count it produced, and the two
re-authorizations stated as re-authorizations.

---

