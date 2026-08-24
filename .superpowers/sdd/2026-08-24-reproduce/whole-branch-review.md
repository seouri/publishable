# H9c `reproduce` — whole-branch gate

**Branch:** `h9c-reproduce` at `ff2b8eb` · **Base:** `main` at `6ff19de`
**Suite:** 3230 passed, 1 skipped, 2 xfailed — run directly in the foreground, twice: once before
any mutation and once after every mutation was reverted, both times the same three figures.
**Gates:** `ruff check` clean · `ruff format --check` clean (95 files) · `mypy` clean (53 files).

# VERDICT: **HOLD**

**Two Majors, both one sentence of `docs/reference.md` and one of `CLAUDE.md`. No code change is
required and no behaviour is at risk.** The hold is on the normative documents, and it is the hold
this project's own precedent demands: the controller ruled three commits ago, in `ff2b8eb`, that a
false normative sentence must be corrected in place rather than shipped with a note beside it. Both
Majors are that same shape, and one of them is **four lines below the sentence that ruling fixed**.

Everything else on this branch passes. The implementation is unusually well armed: fifteen tasks,
90 new test functions, zero removed, four authorized assertion edits and no unauthorized one; every
guard-pin arm proven able to fail **at HEAD** rather than at the commit that built it; Ruling Z,
Ruling AA, Ruling BB, the `null → value` case, the record-loss fix and all four `reproduce new`
shapes each established **by behaviour**, not by reading. Clear the two sentences and this merges.

---

## The findings

| # | Severity | Finding | Routed |
|---|---|---|---|
| 1 | **Major** | `E-GIT-NO-REPO`'s § Errors row was widened six paths → seven and misses the **eighth**: `reproduce.py:373`, `prepare_checkout`'s destination walk-up, a **third** site catching it **by type**. `CLAUDE.md`'s H9c entry repeats the undercount | H9d |
| 2 | **Major** | `reference.md` § Reproducing step 2's paragraph says the two git invocations are *"a clone and a detached checkout, **each passing** `-c core.autocrlf=false`"*. Measured from the real argv: both flags are on the **clone**; the checkout passes none | H9d |
| 3 | Minor | Batch 1's concern 2 and batch 2's § 1 claim arm E is *"the only thing standing between"* the config write-back and a modified run directory. Its fixture stops at `E-REPRODUCE-UNLOCKED`; it never reaches `write_config`. The behaviour is armed — by Fixtures M/O/F | H9d |
| 4 | Minor | `restore_environment`'s `pyproject.toml` comparison prints nothing when the record's copy exists and the commit's does not, in the function whose ruling is that every absence is printed | H9d |
| 5 | Minor | `apparatus.expectation_from`'s `code=` parameter has one caller, which uses the default and re-codes the exception anyway; the docstring describes a seam nothing exercises | H9d |
| 6 | Minor | `test_stop_codes_holds_exactly_the_two_codes_execute_plan_breaks_on` pins three. Deliberately not renamed, with eight citations grepped and disclosed — right for a batch, wrong to leave | H9d |

Each finding's exact command and output is in `task-b3-review.md`; the two Majors are reproduced
below because they are the hold.

### Major 1 — the widened row is still narrower than its code

```
$ grep -rn "find_repo_root" src/publishable/ | grep -v "^src/publishable/provenance.py"
src/publishable/reproduce.py:373:   enclosing: Path | None = find_repo_root(dest.parent)   ← UNNAMED
src/publishable/reproduce.py:1391:  repo = find_repo_root(operand.path.parent)             ← named
src/publishable/validate.py:511 :1221 · src/publishable/study.py:54
src/publishable/cli.py:235 :2501 :5784
```

`reproduce` added **two** call sites and the widening counted one. `:373` catches the raise **by
type** (`except ContractError`) as the pass branch of `E-REPRODUCE-DEST-IN-REPO`, exactly as
`validate.validate_config` does. That the raise is real, established by behaviour:
`find_repo_root(<tmp dir outside any repo>)` → `RAISED code= E-GIT-NO-REPO`.

True figures: **eight paths**, **three by-type catches**. `docs/reference.md:1215` says *"Seven
paths reach it… Two more catch it by type"*; `CLAUDE.md` says *"a **seventh** path… and a **third**
site catching it by code"* (the by-code figure is right; the path count and the by-type count are
short). This is the very class batch 3's § 3c calls *"where the whole-branch Majors on four
sub-slices have lived"*.

### Major 2 — a false normative sentence about a shipped command

Throwaway probe recording every `reproduce._git` argv on a real clone-and-checkout:

```
GIT ARGV: git -c core.autocrlf=false clone -c core.autocrlf=false <remote> <dest>
GIT ARGV: git -C <dest> checkout --detach 71e240a0…
```

Two placements, one invocation. The checkout relies on the value `clone -c` **persisted into
`<dest>/.git/config`** — which is precisely batch 1's own § 4.1 finding, and which
`_CLONE_CONFIG`'s docstring states correctly. The document turned *both placements* into *both
invocations*. Corroborated by the shipped structural arm, which asserts the flag list on
`clone_argv` alone and nothing about the checkout's.

Repair, per `CLAUDE.md`'s *prefer deleting a claim to rewriting it*: drop the *"each passing"*
clause, or say *two placements on the clone, persisted for the checkout*.

---

## What the gate found that no per-batch review could

**The Majors are both cross-batch by construction**, which is the pattern the gate exists for:

- Major 1 is an **interaction between batch 1 and batch 3**. Batch 1 (task 3) added the
  `prepare_checkout` walk-up; batch 3 (task 15) widened the row. Task 15 derived the widening from
  *its own* task's new site — the config form, task 12's — and the earlier batch's site was never in
  view. Batch 1 filed nothing about it because at that commit the row was not being edited; batch 3
  edited the row without re-deriving over the whole branch. Both reviews would pass; the branch
  ships a false count.
- Major 2 is an **interaction between batch 1's measurement and the controller ruling**. Batch 1
  measured the two placements correctly and disclosed them in `_CLONE_CONFIG`'s docstring. The
  document sentence describing them was written in task 15, rewritten by `ff2b8eb`, and at neither
  point was it checked against the argv — the ruling was scoped to the *destination* clause four
  lines above.
- Minor 3 is a **claim propagating across two batch reports.** Batch 1 wrote the arm-E safety
  claim as concern 2; batch 2 quoted it back and reported it discharged. Neither ran the mutation
  that would have shown arm E green under the hazard — batch 2 used a throwaway probe of the write's
  *siting*, which is a different question from *what fails if the siting is wrong*.

**The shape worth carrying:** all three are a claim about a guard or a count travelling forward
across a batch boundary and being re-asserted rather than re-derived. It is the same shape
`CLAUDE.md` already records for the executability figures — *"a slice retires one blocker… and
carries the summary phrase forward without re-deriving what it counted"* — appearing here in three
new currencies: a call-site count, a flag placement, and a pin's reach.

---

## What was checked and found sound

Established **by behaviour** unless marked otherwise. Full commands and outputs in
`task-b3-review.md`.

- **Ruling Z. No verdict invents a cause.** A real `code_hash` mismatch on the H6a-boundary case
  names the input, both digests, the file count and the file list, then prints the closed set
  prefaced by *"cannot tell these apart, and does not guess between them"*. The cause the scoping
  feared — *"a rewritten or force-pushed history"* — is not asserted anywhere, and is caught by name
  elsewhere (`E-REPRODUCE-COMMIT-UNREACHABLE`) before any hash runs.
- **Correction 3, measured on my own machine.** A plain clone under ambient `core.autocrlf = true`
  gives a different digest (`da5d665f…` vs `26149c8e…`); `clone -c` is the placement that persists.
  The `.gitattributes` residue reproduces, the filing states its own digits and makes the
  inequality the claim, and the cost is stated in the document rather than blamed on the tree.
- **Ruling AA, both forms.** Every comparison is a printed line or a named refusal. The bundle
  member with a dangling `environment/uv.lock` prints the unreachability and refuses
  `E-REPRODUCE-LOCKFILE-UNREACHABLE` naming the recorded digest and *"no uv.lock at all"*. One
  silent branch found — Minor 4.
- **Ruling BB and the behaviour change.** The expectation read is built **inside** the branch that
  already resolved a declared probe (read), so a config declaring no probe is unchanged and a stray
  file beside it is inert. Every `cli.py` and `apparatus.py` hunk on the branch is additive or gated
  the same way. Correction 11's hazard is armed: `check_unexpected` records onto the **expectation**
  object, and Fixture Q pins `unobserved` against a no-file control.
- **`null → value` passes.** `changed` alone raises `AssertionError`; `record` then `changed`
  returns `None`; the shipped path does the latter.
- **The record-loss fix is real and pinned.** Narrowing the branch back fails exactly
  `test_h9c_a_resume_whose_run_start_contradicts_the_expectation_keeps_the_record`, and that arm
  asserts the `run.yaml`, the `status`, and non-empty `results.conditions` — the record-loss half,
  not just the exit code.
- **The controller ruling is clean.** One entry touched, every numeric literal byte-identical, and
  the arm still fails when `8e21ab3` moves. The shipped sentence is now true of the command.
- **All four `reproduce new` shapes** measured through the real console script from a scratch
  directory outside the repository that was empty before and after: `2`, `2`, `2`, and `1` with
  `E-IO-FAILED`.
- **§ Errors placement is correct and Decision 14 is rightly overruled** — adjudicated against each
  table's own scope sentence, with *"Two rows in this table are not raises"* re-counted and still
  exactly true after the insertion.
- **`E-IO-FAILED`'s widening covers every site** — ten in `reproduce.py`, enumerated by reading,
  plus `cli.py:3257`.
- **Both consistency passes re-run by me**, over the six files named individually, with the file
  list filtered and never the output, and with each check proved able to fail by injection and
  revert. **HITS 0.** No worked-example figure moved; `cohort-pilot`'s intervals are untouched.
- **The development record was not retro-edited** — eight lines appended to the plan, none removed;
  `spec-defects.md`, the sole exception, strikes rather than deletes.
- **The four filings reproduce**, each owner a fact with a reason, the closed one struck.
- **§ Executability's four-row table is byte-identical** to all ten prior entries', verified
  programmatically; no fifth number minted; the design's own reason is correctly reported false and
  the verdict re-derived on grounds that hold.
- **Every earlier-batch guard mutated at HEAD still kills something.** No dead guard was found.
- **The delta is accounted for**: 3132 → 3230 = +98 = 90 new test functions (0 removed), three of
  them parametrized at 2, 4 and 5 cases. The only four removed lines under `tests/` are the three
  authorized assertion edits and one docstring clause.

---

## To clear the hold

1. `docs/reference.md:1215` — `E-GIT-NO-REPO`'s row: seven → **eight** paths, and a **third**
   by-type catch named (`reproduce.prepare_checkout`'s destination walk-up). Derive by reading the
   call sites, then confirm by grep — not the reverse.
2. `CLAUDE.md`'s H9c entry — the same correction, appended rather than rewritten in place if the
   entry is treated as record.
3. `docs/reference.md:4232` — delete or repair the *"each passing `-c core.autocrlf=false`"* clause.

Nothing under `src/` needs to move, and no test needs to move. Re-run the mechanical pass after
each edit, since all three sit inside long single-line table rows and paragraphs.
