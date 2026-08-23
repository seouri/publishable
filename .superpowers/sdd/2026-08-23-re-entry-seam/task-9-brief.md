## Task 9

**Ruling R binds this task (design Decision 1).** You edit § Operation commands' `dry-run` row, and its
`Does` cell carries the promise Ruling R narrows. The row's two halves — `Status` and `Does` — are one
fact seen from two ends and are edited in **one commit**.

**Ruling U binds (design Decision 4): you are the sole authorized editor of guard-pin arm F**, and its
post-edit state was written before you existed. `tests/test_cli.py::test_reference_cli_tables_are_parsed_at_all`:
the line `assert ("dry-run", "NOT BUILT") in tables["Command"]` becomes
`assert ("dry-run", "built") in tables["Command"]`, **and** a line
`assert ("resume", "NOT BUILT") in tables["Command"]` is added so that table keeps a marked
row-presence probe — the device that test's own docstring says exists to rule out a parser finding
some rows but not the ones a reader would look for. `("validate", "built")` is untouched. **The
`set(NOT_BUILT_COMMANDS)` equalities are self-maintaining and must not be edited.** Your report must
show the diff is exactly those two lines with nothing reordered.

**What to build.** `OPERATION_COMMANDS` gains `"dry-run"`; `handlers["dry-run"] = command_dry_run`;
`NOT_BUILT_COMMANDS` loses `"dry-run"`. **Do not reorder `_dispatch`'s branches** (correction 16).
§ Operation commands' `dry-run` row: `Status` → `built`, and `Does` → *"Validates, expands the sweep
and repeat plan, builds the input manifest, probes the apparatus, prints the step directories and the
fixed files a run would write, and the unit-execution count. **Does not** list the artifact files
inside those directories: their names are `io.write` arguments in step code, which core never inspects
— see [design-principles.md § Greenfield only]. Creates nothing."* — wording yours, that content
mandatory, the link resolved.

**Add the end-to-end tests this slice's batching order defers to here**: `main(["dry-run", cfg])` over
a real project, exit `0`, the transcript on stdout, and the arity trio (`no argument`, `two
arguments`, `--json`) for `dry-run` as task 4 built it for `draft`.

**Must not touch:** § Before you spend it's transcript (task 12), § The apparatus files (task 13),
§ Draft runs (task 6), any other `Status` cell, `provenance.py`.

---

