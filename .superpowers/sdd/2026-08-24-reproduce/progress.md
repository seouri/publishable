# H9c — `reproduce` — the ledger

Branch `h9c-reproduce`, off `main` at the H9b merge. **15 tasks in seven batches, every batch reviewed.**
This is the command the whole slice order was built around: the spine design put H9 last because
*"`reproduce` is what reads the environment back, so it decides the unresolved lockfile questions."*
Everything upstream had landed — H6a's `code_hash`, H6b's environment record, H9a's seam, H9b's
`identity.json` — and H9c is the reader all four were writing for.

Four controller rulings: **Y** (`reproduce` takes a path and nothing else, run **on** the other device),
**Z** (**a hash that differs says WHICH input moved and never guesses WHY**), **AA** (two lockfile sources
are both real and neither is preferred silently), **BB** (`apparatus.expected.json` is a comparison, not a
gate). Suite 3132 → **3230**, +98 fully attributed.

**The plan carried TWENTY-NINE corrections against the code — the most of any plan in this project** —
and three of them killed prescribed work outright: a fixture that was **impossible** (a tree cannot live
at the same SHA, and a rewritten history is caught at the **checkout**), a step **unbuildable for
plugins** (`get_template` returns `None` for an installed template), and a `changed` call that **raises
`AssertionError` on `null → value`** — the very case the document requires to **pass**.

## Ruling Z held, and the verdict says what it cannot tell apart

Verified by behaviour on the H6a-boundary case: the refusal **names the input, both digests, the file
count and the file list**, then prints a **closed candidate set** prefaced by *"cannot tell these apart,
and does not guess between them."* And the cause the scoping feared a step would invent — *"a rewritten
or force-pushed history"* — is **caught elsewhere by name** (`E-REPRODUCE-COMMIT-UNREACHABLE`) before any
hash runs. **No verdict in the command invents a cause.** *A confident wrong diagnosis is worse than an
honest unknown*, and this repo had shipped four sentences that invented one.

**Correction 3 is the cost of H6a's Ruling M surfacing, and it is stated rather than blamed on the tree:
a faithful clone's `code_hash` depends on `core.autocrlf`** — a machine-local setting Ruling M
deliberately left alive, because neutralizing it reported unedited files dirty. Both git invocations now
run with the setting pinned, and **a tracked `.gitattributes` makes the hash depend on materialization in
a way no flag fixes** — filed, unassigned, with the reason.

## Ruling AA: two lockfiles, and the bundle form cannot reach one of them

The recorded `uv_lock_hash` is the authority and the run directory's **byte copy** is the carrier. **In
the bundle form the byte copy is unreachable** — measured: a member's `uv_lock` is a dangling relative
path — so the clone's committed lockfile is used **iff its digest matches**, else a named refusal.
`pyproject.toml` is a **third** input, compared and reported. **Every comparison is a reported fact:
absent, identical, or DIFFERS.**

## A record loss found after the fact, and closed

A **resume** whose run-start round contradicted the expectation exited `1` with **no `run.yaml`**, losing
completed executions — **terminally**, since the fact stays contradicting. `execute_plan` already
published in the mid-plan case; only the run-start branch named a code by hand. Widened and pinned, no
vocabulary minted. **That is the second slice running to find *every execution paid for, the record lost*
in a branch nobody suspected**, and both times it was reachable only by running the real command.

## The controller ruling: a false normative sentence frozen by a pin

§ Reproducing step 2 said the derived destination *"can't collide with an existing checkout."* **It can,
and `reproduce` refuses.** The sentence was pinned **byte for byte and whole-line** by an arm whose
authorized editor is **NONE** — and batch 3 **stopped and reported rather than self-authorize**, which is
the fourth slice running where that route was used correctly.

**The ruling: a pin exists to stop the worked example's NUMBERS drifting, not to freeze prose errors.**
Post-edit state was specified before the edit — every numeric literal byte-identical, no other entry
touched, the arm still failing when a literal moves — and proven by moving `8e21ab3` to `9999999`, which
fails that arm alone. **Keeping a false normative sentence because a pin captured it is the tail wagging
the dog**, and the paragraph the batch had written to correct it from outside was folded back into
ordinary prose, since *a paragraph saying what it replaces is redundant once the sentence it replaced is
gone.*

## The gate: two Majors, both one sentence, and one of them a row this slice had just widened

**`E-GIT-NO-REPO`'s row was widened six paths → seven in this very slice and still undercounted**: the
**eighth** is `prepare_checkout`'s walk-up from the derived destination's parent — a **third** by-type
catch, and the one where **a raise IS the ordinary case**, so the exception path is the pass branch and
the quiet return is the refusal. **A row widened in the slice that then undercounts it** is the
one-row-per-code shape producing a whole-branch Major on **five** sub-slices now. And the document said
the two git invocations *"each pass `-c core.autocrlf=false`"* — **measured from the real argv, both flags
are on the clone**, which writes the setting into the new repository's `.git/config`, so the checkout
needs none.

**Placement was decided from each table's own scope sentence rather than the design's instruction** —
twelve `E-REPRODUCE-*` rows to § Errors `validate` reports, whose scope is *"the codes a command
reports"*, and the one code actually **raised** to § Errors core raises. That is the correction of the
mistake a design made two slices earlier, applied without being told. **`E-IO-FAILED` turned out to have
no row at all** — one sentence in § Exit codes saying it *"exits `1`"*, false at three sites, widened
rather than a fourteenth code minted.
