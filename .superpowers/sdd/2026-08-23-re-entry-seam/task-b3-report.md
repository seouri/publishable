# H9a tasks 3 and 4 — report

**Status: both PASS. Full suite green after each commit.**

Commits:
- Task 3 — `137d55e` — `command_draft` — the gate relaxed, the pathspec unchanged
- Task 4 — `d4af219` — wire `draft` into `_dispatch`

Test summary: `uv run pytest` — **2992 passed, 1 skipped, 2 xfailed** (baseline before
this batch was 2984 passed, 1 skipped, 2 xfailed; task 3 added 4 tests → 2988; task 4
added 4 more → 2992). Gates clean throughout: `ruff check .`, `ruff format --check .`,
`mypy` all pass with no findings.

## Task 3 — `command_draft`

Built exactly the function the brief specified, inserted after `command_run` and before
`_dispatch`. `_prepare_run(config_path, allow_dirty=True)`, a stderr-only notice when
`prepared.git.code_dirty`, then `_execute_prepared(prepared, draft=True)`.

**The mutation proving `draft` is READ, not merely accepted.** `_execute_prepared`
already took a `draft` parameter (batch 2's extraction, per progress.md) but never
forwarded it to the `assemble_run_yaml` call at what is now cli.py:4075 — that call is
task 3's actual wiring point. Fixed by adding `draft=draft` to that call. Proven live by
mutation (a): reverting `command_draft`'s call to `_execute_prepared(prepared,
draft=False)` and running the **full, unfiltered suite** produced exactly **2 failures**
(`test_h9a_fixture_q_a_draft_on_a_dirty_tree`, `test_h9a_fixture_q_a_draft_on_a_clean_
tree_records_code_dirty_false` — both `record["draft"] is True` assertions), 2986
passed. Reverted by editing back; diff against a pre-mutation copy was byte-identical;
re-ran the four Fixture-Q-family tests green.

**Both directions of the gate relaxation**, each with its own test:
- `test_h9a_fixture_q_a_draft_on_a_dirty_tree` — a tree dirtied under `src/**` after
  commit, outside this repo: `command_draft` returns `EXIT_OK`, records
  `draft: true` and `provenance.git.code_dirty: true`, notice on stderr only.
- `test_h9a_a_dirty_tree_still_refuses_plain_run` — the identical dirtied tree, run
  through `main(["run", ...])`: still `EXIT_WRONG` with `E-CODE-DIRTY`, no run directory.

**Proof the pathspec did not widen (Ruling T).** `test_h9a_fixture_q_draft_pathspec_
does_not_widen_to_the_repo_root` dirties a file *outside* `src/**`/`templates/**` — a
new file at the repo root — and asserts both `command_draft` and `main(["run", ...])`
proceed with `code_dirty: false`. `git diff` on `src/publishable/provenance.py` is
empty: `git_provenance`, its `-c` flags and `HASHED_TREES` are byte-unchanged, and
`provenance.py` was never opened for editing.

**What § Draft runs now says about `code_dirty`:** nothing yet — task 3's brief and
correction 12 both name **task 6** as the owner of that document fix, and task 3's own
"must not touch" list bars any `*.md`. `docs/reference.md` is untouched by task 3 (only
task 4 touched it, and only the one `draft` row's Status cell — see below). The
docstring on `command_draft` states the corrected rule in code (measurement, not a
forced value) so a reader lands on the right answer before task 6 lands.

Mutation (c) — delete the notice print — run against the full suite: exactly **1
failure** (`test_h9a_fixture_q_a_draft_on_a_dirty_tree`, the stderr assertion), 2987
passed. The assertion is `"notice" in err` (the stderr-only capture), never a combined
stream, per the brief's own named trap. Reverted and re-verified.

Mutation (b) — forcing `code_dirty=True` under `draft` on an actually-clean tree — is
**declared here and owed to task 6's Fixture R**, per the brief's explicit instruction
("declare it here, build it there"); not run against this branch, since the code and
fixture it targets don't exist yet on this branch.

`Prepared`, `Callable`, task 1's arms, `run_record.py`, and the H7d Part B
`max_failed_fraction` pin were not touched.

## Task 4 — wiring

Three edits, exactly as scoped:
1. `OPERATION_COMMANDS = {"validate", "run", "draft", "freeze", "report"}` and
   `handlers["draft"] = command_draft`, joining the existing one-path arity arm.
2. `"draft"` removed from `NOT_BUILT_COMMANDS`.
3. `docs/reference.md` § Operation commands: only the `publishable draft` row's
   `Status` cell changed, `NOT BUILT` → `built`. `git diff docs/reference.md` shows
   exactly that one line changed; the `dry-run` row is untouched (task 9's).

`_dispatch`'s branch order was not touched (correction 16) — confirmed by grepping the
diff for the function: only the `handlers` dict gained a line.

**The shipped-answer move, pinned rather than disclosed:**
`test_h9a_draft_new_now_reaches_the_arity_arm_not_the_not_built_diagnostic` asserts
`main(["draft", "new"])` no longer prints `is specified but not built` (the two-token
key `"draft new"` used to hit `NOT_BUILT_COMMANDS` before this task) and no longer
prints `unknown command` either — it is a single-path invocation now routed into
`command_draft`, which then fails for an unrelated reason (`"new"` isn't a readable
config), asserted via `code != EXIT_INVOCATION` to keep the test about routing, not
about `_prepare_run`'s own error surface.

**Grep report, run before writing the new pin (as instructed):**
- `grep -rn "takes exactly one path" tests/` → **0 hits** before this task's tests
  were added.
- `grep -rn "no flags" tests/` → **exactly 1 hit**, `tests/test_cli.py:324`:
  `_DIFF_ARITY_MESSAGE = "` + "`" + `diff` + "`" + ` takes exactly two paths and no
  flags"` — `diff`'s own two-*path* rule, a different arity than the shared one-path
  arm `draft`/`run`/`freeze`/`report`/`validate` share. Neither grep hit pinned the
  shared arm before this task.

Added the shared arm's first pin, using `draft` as the probe (three tests: no path,
two paths, one flag-shaped argument `--json`). Mutation — replace the guarded
condition with a bare `len(rest) != 1` — run against the **full, unfiltered suite**:
exactly **1 failure**
(`test_h9a_draft_with_a_flag_is_an_invocation_error`), 2991 passed — the `--json` case
is exactly one argument, so `len(rest) != 1` alone can't catch it, while the no-path and
two-path tests stayed green because `len` alone already covers those. Not blind, as the
brief said. Reverted by editing back; diff against a pre-mutation copy was
byte-identical; re-ran clean.

Confirmed (ran, not merely read) that the shipped
`test_reference_cli_tables_match_what_the_cli_does[Command]` passes with the `draft`
row now `built` — it drives `main(["draft", "_probe_a", "_probe_b"])` and asserts
neither `unknown command` nor `is specified but not built` appear, and nothing is
scaffolded or executed. Per the brief, this is a constraint the change must satisfy,
not a substitute for the arity mutation above, and is reported as such rather than
counted toward the pin.

`tests/test_cli.py`'s `("dry-run", "NOT BUILT")` assertion, the
`set(NOT_BUILT_COMMANDS)` equalities, every other § CLI reference row, and
`provenance.py` were not touched — `git diff --stat` for those confirms it.

## Concerns

- None outstanding for tasks 3/4 themselves. Mutation (b) (forcing `code_dirty=True`
  under a clean-tree `draft`) is explicitly deferred to task 6's Fixture R per the
  brief; it is declared, not built, here.
- `.superpowers/sdd/.gitignore` was found clobbered to a bare `*` before task 3's
  commit (a `scripts/sdd-workspace` side effect per CLAUDE.md) and was restored from
  `HEAD` before that commit; it stayed clean through task 4.
- § Draft runs' `draft: true` AND `code_dirty: true` conjunction in `reference.md`
  is still unedited on this branch — correctly so, since correction 12 and the task 3
  brief both name task 6 as its sole owner and task 3's own scope bars `*.md`.
