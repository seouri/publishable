# H9d — `demo`, `docs`, `list-templates` — the ledger

Branch `h9d-demo-and-docs`, off `main` at the H9c merge. **14 tasks in six batches, every batch reviewed.**
**The last slice of the command surface**: after it, every row of § CLI reference reads `built`, and the
only remaining slice's surface is `units.py`/`stats.py`.

Four controller rulings with the design — **CC** (`list-templates` is H9d's; the charter row is amended),
**DD** (`demo` produces its own numbers and README's `correlation_pilot` walkthrough changes to match),
**EE** (`docs` rewrites only what a region encloses, and a region it cannot find is a **refusal**), **FF**
(`docs` and `list-templates` take no path, reusing the documented exception rather than minting a second) —
plus **GG**, issued before the batches: **`self.rng` becomes a `numpy.random.Generator`**, the code
following the documents. Suite 3230 → **3338**.

**The plan carried THIRTY-THREE corrections against the code, the most of any plan in this project**, and
the biggest cluster is the one that matters most: **README's walkthrough described output no command
produces.** `run` prints its warning block and `run.yaml → <path>` — no results table, no progress bars,
no banner; `dry-run` prints **19** where two documents said 15; and **stop 3's block was fiction outright**
(`validate` prints `✓ config valid · <path>`). That is the *documented rule with no code behind it* defect
landing on **the one page a new user reads first**, and closing it was most of `demo`'s work.

## What the slice built

`demo` walks the whole arc and its transcript is now **measured, not composed** — verified end to end by
the gate through the installed console script in a scratch `HOME` outside the repo: **129 lines, exit 0,
stops 1, 3 and 5 verbatim**, the `[Enter] to run it · q to stop here` prompt present under a pty and
correctly absent unattended, and **two independent invocations agreeing on every printed digit.** `docs`
gained the **region parser that existed nowhere in `src/`**, with a missing or malformed region a **named
refusal** — *a command that silently rewrites nothing looks identical to one that worked* — and
hand-written prose outside a region proven to survive, with a positive control. `list-templates` was
**orphaned**: chartered only to H7, which closed without it, with the one live routing a design sentence
saying *"H9's list"*. **A command orphaned by a closed family is found by re-reading the charter against
the code, not by waiting for someone to notice.**

## Five things worth carrying

**A guard pin whose golden is a SCAN RESULT rather than a literal list can be edited without becoming a
transcript.** Arm D's post-edit state was specified **procedurally**: re-scan with the *unmodified* helper
and literals, expect the pre-edit tuple **minus exactly four named entries**, and *any other survivor is a
finding, not a literal to refresh.* Both the batch and the gate ran it — 15 → 11, the four named removals,
**zero survivors outside the remainder and zero new lines** — and `cohort-pilot`'s numbers did not move,
with `design-principles.md` and `experimental-designs.md` byte-identical to `main`.

**A ruling's escape clause firing is not a ruling ignored.** GG required the `self.rng` type change
because two normative sentences said `numpy.random.Generator`, **zero tests mentioned `self.rng`**, numpy
is already a hard dependency, and a step calling `self.rng.normal(...)` **fails at exit 3**. When no task
turned out to own `base_step.py` — verified, `git log main..HEAD -- base_step.py` empty — the batch
**filed the change and made the documents true of the code instead.** That is the honest interim. **And
the gate then caught that one of the four sentences was still false**: both said the seed is `derive_seed`
of the step's own name where there is no repeat, and the code binds **`0`**. So `self.rng` is
`random.Random(0)` — **the same stream for every non-repeat execution in a run**, which is precisely the
correlation § Randomness argues against, three paragraphs from where it argues it. Corrected where it is
stated, **filed where it can be fixed**, beside the type filing: *both are the same accessor promising more
than it delivers, and closing either without the other leaves § Randomness half true.*

**`E-GIT-NO-REPO`'s row has been widened and then undercounted in THREE consecutive slices** — six → seven
→ eight → **ten (two uncaught, four by code, four by type)**. It now states the **breakdown rather than a
total**, which is the actual lesson: *a total is a claim nobody can check; an enumeration is one anybody
can*, and every one of the three undercounts came from adding to a number instead of re-enumerating by
reading.

**A design can prescribe an implementation that is a measured no-op.** Its bytecode remedy said to hand
`spec_from_file_location` an explicit `SourceFileLoader` — **which is what it already returns**, so the
filing's own recipe still reproduced under it. The batch shipped the **substance** (forcing recompilation
through a `get_code` override) and **said so**, rather than shipping a change that looks correct and does
nothing. *Anyone re-deriving from that sentence would have shipped the no-op.*

**And the last slice of a family is where its own record goes missing.** `CLAUDE.md` had **no H9d
paragraph** and an order sentence still naming H9d as remaining, because **no task owned that file** —
found by the gate, closed by the controller. H9a, H9b and H9c each had one; the slice that finishes a
family is the one with nothing after it to notice.
