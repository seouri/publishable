## Task 4

**Ruling T binds (design Decision 3):** the gate's pathspec does not move. You wire a name; you change
no gate.

**What to build.** Three edits and one new pin.

1. `OPERATION_COMMANDS = {"validate", "run", "draft", "freeze", "report"}` and
   `handlers["draft"] = command_draft`. **Join the existing arm** — do not write a second arity
   enforcer. Its own comment argues against two enforcers of one rule, and `diff`'s separate arm is a
   different *arity*, not a second enforcer of the same one.
2. Remove `"draft"` from `NOT_BUILT_COMMANDS`.
3. `reference.md` § Operation commands: the `publishable draft` row's `Status` becomes `built`. **That
   row only.** The `dry-run` row is task 9's.

**Do not reorder `_dispatch`'s branches** (correction 16). The built branches precede the
`NOT_BUILT_COMMANDS` lookups deliberately, and the two-token arm is evaluated first. **One shipped
answer moves and belongs in your report**: `publishable draft new` reaches `_report_not_built` today
(the two-token key misses, the single-name lookup hits) and after this task reaches the arity arm,
printing `` `draft` takes exactly one path and no flags``. Assert it, so the change is pinned rather
than merely disclosed.

**The new pin, and it is the point of this task.** The shared arity arm is pinned by **nothing**:
`grep -rn "takes exactly one path" tests/` returns 0 and `grep -rn "no flags" tests/` returns 1, which
is `_DIFF_ARITY_MESSAGE`. Report both greps. Add a test asserting, for `draft`:

- `main(["draft"])` → `EXIT_INVOCATION` and the message `` `draft` takes exactly one path and no flags``;
- `main(["draft", "a", "b"])` → the same;
- `main(["draft", "--json"])` → the same. **This is the arm the `len` half cannot cover.**

**Mutation, and it is not blind:** replace the condition with a bare `len(rest) != 1`. The
`--json` case is one argument, so the two branches differ and the test must fail. Run it.

**One shipped test now drives your command and asserts only absences.**
`test_reference_cli_tables_match_what_the_cli_does` will call `main(["draft", "_probe_a", "_probe_b"])`
and assert the output holds neither `unknown command` nor `is specified but not built`, and that
nothing was scaffolded or executed. **That is a constraint, not a pin** (H8b's Minor: a CLI arm
demonstrated by one prose invocation and by nothing else). Confirm it passes and say so; it is not a
substitute for the mutation above.

**Must not touch:** `tests/test_cli.py`'s `("dry-run", "NOT BUILT")` assertion — **task 9 is its sole
authorized editor** — the `set(NOT_BUILT_COMMANDS)` equalities, which are self-maintaining, any other
§ CLI reference row, and `provenance.py`.

---

