## Task 13

> **AMENDED 2026-08-25 by the controller, from batch 4's concern 1.** `test_reference_cli_tables_match_what_the_cli_does` binds a `NOT BUILT` row to the unbuilt diagnostic for **every** invocation of the name, wrong-arity ones included — so while a dict key exists, a wrong-arity invocation **defers** to `_report_not_built`. Both halves are pinned. **You must delete the two commented lines AND the two `…_defers…` tests together**: deleting either alone leaves the branch red or the pin lying.

**Binding corrections: 25, 26, 27. You are guard-pin arm F's sole authorized editor.**

**The `NOT BUILT` retirement, and the `E-GIT-NO-REPO` row.**

Empty `NOT_BUILT_COMMANDS`, flip all three `Status` cells to `built`, and handle what that creates.

> **RULING CC (binding, restated here):** `list-templates` **is H9d's**, and the spine design's H9 row
> is amended by **appending** a dated note to its *Order, amended against outside evidence* section —
> **never** by editing the row in place. Say in that note that a command orphaned by a closed family is
> found by **re-reading the charter against the code**, not by waiting for someone to notice: four H7
> scopings said *"it is still H7's"*, each was right when written, and none re-owned it when H7 merged.

**Decision 12 binds you.** `_report_not_built`, the dict, the three `Status` columns and § Creation
commands' paragraph **all stay**, deliberately unreachable. Correction 26: emptying the dict makes the
binding test's `if status == "NOT BUILT"` branch **dead**, so add the companion — `NOT_BUILT_COMMANDS
== {}` **and** a direct call to `_report_not_built` with a name and a real § heading asserting the exact
diagnostic. **Both claims in one place**, so they cannot drift apart. § Creation commands' paragraph
gains one sentence saying no row carries the marker today and why the machinery is retained.

**`E-GIT-NO-REPO`'s row is widened, and its enumeration is RE-DERIVED BY READING, never incremented.**
Correction 27: the row says *"Eight paths reach it"* and enumerates two uncaught, three caught by code,
three caught by type. `docs` adds a **by-code** site; `list-templates` adds a **by-type** site — two
additions of **different kinds**, so no single digit repairs the sentence. **Enumerate every call site
by reading `src/`, then confirm with a grep** — the reverse order is the substitution `CLAUDE.md`
§ Answering a question with a proxy names, and it once shipped a credential leak. Report what you
enumerated and what each site does.

**And check the neighbours you moved.** § Errors carries **one row per code covering every emit site**.
Task 3 edited `scaffold.py`, so re-check `E-PROJECT-EXISTS`' row against the code rather than assuming
it. **A row widened in the slice that then undercounts it has produced a whole-branch Major on five
sub-slices** — check each table's own **scope sentence**, not only its cells.

**Must not touch:** the four documents' other sections (task 14's), guard-pin arms you are not named on.

---

