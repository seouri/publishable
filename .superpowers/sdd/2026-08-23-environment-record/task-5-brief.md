## Task 5: Ruling N — two § Errors rows, one per code, covering every reach path

> **Bindings that reach this task:** **Ruling N** and design Decisions 2, 3 and 4, all restated below.

**RULING N, restated here in full:** the charter widens to **TWO** of the nine undocumented codes, not
three and not nine. The scoping recommended *"take these three, leave six"*, but **H6a already gave
`E-CODE-DIRTY` its row** in its batch-4 follow-up — verified here by reading, not by the ledger:
`grep -n "E-CODE-DIRTY" docs/reference.md` returns one hit and it is a full § Errors core raises row.
So what remains is `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT`. **Take both.** Grounds: H6's surface is
hashes and provenance, and both are raised by the git layer H6a just rewrote — **a code whose emit site
this slice's own work touched is inside the charter.** The others belong to their own surfaces;
**each is filed with an owner that is a fact with a reason**, never *"whichever slice next touches X"*
— that is task 8's. **The ruling as it arrived said *"the other six"*; § Corrections 18 re-derives it
to FIVE, and task 8 uses five.** **One row per code covering EVERY emit site** — that shape was the whole-branch
Major on two sub-slices, shipped twice in a third, and miscounted twice in H5b. **And check each
table's own SCOPE SENTENCE, not this plan's instruction**: H6a's batch 4 put a row in a table whose
scope did not admit it, and its batch review settled the question by **citing the design**, which is
answering from a proxy.

**The scope check, done here so the task confirms rather than re-derives — and confirms by reading the
table, not by reading this paragraph.** § Errors core raises' header is `| Raised by | Type · code |`,
over a preamble that introduces the exception hierarchy and then says *"Two rows in this table are not
raises, and the `Type` cell says so"*, siting `E-CODE-DIRTY` and `E-CODE-EMPTY` there because
*"`validate` does not report them … a reader who meets one at `run` looks for it here."* **Both new
codes ARE raises and both carry `ContractError`**, so neither needs an invented `Type` cell and neither
widens the table's scope. **Read the preamble and the header yourself and report what they say.**

**Decision 2 — what `E-GIT-NO-REPO`'s row must carry.** One raise, in
`provenance.find_repo_root`, and **six** paths that reach it. Measured at the console script:

| Reached from | What happens |
|---|---|
| `cli.command_run` | **uncaught** — `main`'s `except PublishableError` prints it to **stderr**, exit 1 |
| the `generate`/`init` dispatch, `find_repo_root(Path.cwd())` | **uncaught**, same printer, exit 1, and the walk-up starts at the **working directory** |
| `validate._check_data` | caught by code, `return`s quietly — *"not in a repo, so inside-the-repo doesn't arise"* |
| `validate.validate_config` | caught by a **bare `except ContractError`**; `repo_root` becomes `None` and local template discovery is skipped |
| `cli._load_experiment_for` | caught by `except Exception`, returns `None` |
| `study._refuse_if_in_repo` | caught by code as the **pass branch** of `E-STUDY-IN-REPO` |

The row must carry four things: the single raise; that `run` and the creation commands **surface** it at
exit 1 on stderr; that the creation commands walk up from the **cwd**, being the commands with no path
argument to walk up from — **the one place `CLAUDE.md` § Invariants' *"a walk-up from the path the
command was given, not from the working directory"* does not apply, and a reader who compares the two
without that sentence concludes one is wrong**; and that `validate` and `study` catch it **by code** as
the pass branch of a rule of their own, which is why a config outside every repository prints
`✓ config valid` and then refuses at `run`.

**Decision 3 — what `E-GIT-NO-COMMIT`'s row must carry.** Raised by `provenance.git_provenance` on a
repository with no `HEAD`; **one** reach path, `cli.command_run`
(`grep -rn "git_provenance" src/` → the definition, one import, one call); and raised **while
computing** the `GitInfo` the dirty gate reads, so it **precedes** `E-CODE-DIRTY` — a fresh `git init`
with two untracked trees reports this code, not the gate's. Measured. The row also records why the
check exists, which is in the code's own comment: `--verify` is used because plain
`git rev-parse HEAD` writes the literal string `HEAD` to stdout as part of its usage hint on a
commitless repo, which `_git`'s `check=False`/`strip()` convention would read back as a commit.

**Decision 4 — where the rows go.** Beside **the row whose subject is `src/**` or `templates/**`
carrying uncommitted changes when a command that executes starts** — named by what it does, never by
position, never as *"the two rows above"*. **When you insert a row, check every row it moved and every
count phrase near it**: § Errors core raises' preamble says *"Two rows in this table are not raises"*,
and adding two rows that **are** raises must leave that count at two.

**Steps**

- [ ] Read § Errors core raises' preamble and column header and **report what they say** before writing
      either row.
- [ ] Write the two rows, one per code, each carrying everything Decisions 2 and 3 name.
- [ ] **Check the preamble's *"Two rows"* count is still true**, and every count phrase near the
      insertion point.
- [ ] **Fixture G — one row per code, checked mechanically.** Extract every code from § Errors core
      raises' `Type · code` column, **and independently** grep `src/publishable/` for
      `code="E-GIT-NO-REPO"` and `code="E-GIT-NO-COMMIT"`. Assert each code appears in **exactly one**
      table row and has **exactly one** raise site. **Both ends are read** — a test that compares the
      table with itself measures only that the table equals itself.
- [ ] **Run both mutations:** **9** delete `E-GIT-NO-REPO`'s row → Fixture G fails on the table side
      while the `src/` grep still finds the raise. **10** add a second row for `E-GIT-NO-COMMIT` →
      exactly-one becomes two.
- [ ] **Named blind in advance, and owed a replacement:** a mutation to either row's **prose** is
      caught by nothing — no test reads a row's sentence. The replacement is **Fixture G plus arm T**:
      G pins that the row exists exactly once and the code is raised exactly once, T pins the behaviour
      the row describes (code, stream, exit code, ordering). The residue — a row whose English is wrong
      while its code, count and behaviour are right — is the batch review's, named here rather than
      discovered there. **Report that you left it, do not report zero.**
- [ ] Run arm T and report it passes **without an edit** — this task documents behaviour and changes
      none.
- [ ] Mechanical pass on the edited file.
- [ ] Four gates. **Delta: +1 test.** Commit.

**What this task must NOT touch.** `src/` — no code, no comment. The other seven undocumented codes
(task 8 files them). `E-CODE-DIRTY`'s existing row. § Exit codes and diagnostics. Arm T.

---

