## Task 1

**Ruling U binds this task (design Decision 4): the pin comes first, and every arm is captured in the
shape the design has already decided.** H6a captured arms against a superseded signature and forced a
later task into an unauthorized edit; H6b captured forward and its edit matched byte for byte. **You
are the only task in this slice that may create an arm.** Every arm below gets an authorized editor or
an explicit **NONE**, and the authorized post-edit state is already written in the design — copy it
into the arm's own docstring, because that is the only place a later implementer will read it.

**Also binding: proving an arm cannot move is NOT proof the line is pinned** (H6b whole-branch gate,
Major 2). For each arm, run a mutation in the **production** code and show the arm fails. An arm you
cannot make fail is not an arm.

Build arms **A–E** in `tests/test_cli.py`, and **cite** arms F and G rather than capturing them.

- **Arm A — a completed `run`'s whole `run.yaml`, leaf by leaf.** Drive `run_a_project` with a sweep
  (`grid` over `analysis.method`, two levels), `replication.repeats = [{kind: seed, n: 2}]`, a real
  `aggregate` metric (`aggregate_returns=`, the helper every end-to-end test here uses), and read the
  record back. Walk it into a sorted list of `(dotted_path, value)` leaves, **normalizing**: any key
  named `at`, `started_at`, `wall_seconds`, `run_id`, `hostname`; any value that is an absolute path
  under `tmp_path`; and the three hashes. Assert the normalized list equals a literal captured **by
  running**, not transcribed from `run_record.py`. The normalization list is the one § 5 of the design
  fixes in advance — do not extend it, and if you must, say so in the report as a finding.
- **Arm B — `run`'s full stdout, line by line**, for that same completed run, normalized the same way.
- **Arm C — the four exit codes**, each asserted **beside** the `status` it wrote and each in its own
  test: `completed` → 0, `partial` → 3, `failed` → 4, apparatus-unreachable → 5. H7d Part B pinned
  exit and status separately for a reason its own Fixture U states — a build deriving the code from
  the status cannot tell a truncation `partial` from an unreachable-apparatus `partial`.
- **Arm D — the `executions.jsonl` line's key set**, exactly `{step, scope, condition, repeat, status,
  started_at, wall_seconds, error}`. **This is new coverage**: the claim exists in two docstrings in
  this same file and in no assertion. Grep for `wall_seconds` and for `keys()) ==` over `tests/`
  before you write it, and report both greps with every hit attributed.
- **Arm E — the four early exits of phases 1–5**, each reached end-to-end through `main([...])`: a
  config that fails validation, a dirty `src/**`, a roster refusal, and the zero-file `E-CODE-EMPTY`.
  Assert the exit code **and** the printed code, and for the dirty case assert **no run directory was
  created**.
- **Arm F — cite.** `test_reference_cli_tables_are_parsed_at_all` already asserts
  `("dry-run", "NOT BUILT")`. Add nothing. Record in this task's report that **task 9 is its sole
  authorized editor** and copy the post-edit state from the design.
- **Arm G — cite.** Name the six existing pins listed in correction 5 and say, per arm, which claim it
  already holds. **Do not re-capture any of them.**

**Must not touch:** anything under `src/`. No `*.md`. No existing test's assertions.

**Report:** every arm, its mutation, and the failure it produced. A named arm with no test is not an
arm.

---

