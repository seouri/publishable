# H9d whole-branch gate — `demo`, `docs`, `list-templates`

**Branch `h9d-demo-and-docs`, reviewed at `7f441a9`, 25 commits ahead of `main`.**

## Verdict: **HOLD** — two Majors, both closable by document edits, no code change required

Neither Major is in the code. The branch's code is in good shape: I could not break a claim `demo`,
`docs` or `list-templates` makes about its own behaviour, and every guard I mutated failed loudly. The
two Majors are a **document sentence that is false of the shipped code in the one place a controller
ruling asked for it to be checked**, and **a missing § Repository status paragraph for the last slice
of the command surface** — after which no slice's surface would ever bring a reader back to it.

## Gates

| Gate | Result |
|---|---|
| `uv run pytest` (foreground, unfiltered) | **3338 passed, 1 skipped, 2 xfailed** in 368s |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 101 files already formatted |
| `uv run mypy` | no issues in 56 source files |
| Delta vs. `main`'s 3230 | **+108**, accounted for in `task-b3-review.md` (82 new test functions, 0 net removals) |

## Findings

| # | Severity | Finding | Routed to |
|---|---|---|---|
| 1 | **Major** | § Randomness' *"`self.rng` is exactly `random.Random(self.derive_seed("<this step>"))`"* is false of the code under **both** readings of *no repeat* — `runner.py` binds `seed = 0` for every non-`repeat` scope (`self.rng` is `random.Random(0)`, verified by draw), and a design declaring no repeats gets `_seed_for(digest, 0)`, not `derive_seed`. Ruling GG's fourth obligation was to check exactly these statements against the code; the constructor half was corrected and the argument half was not. Batch 6's report (*"All four are corrected to what the code does"*) and the `spec-defects.md` GG entry both assert otherwise | Task 14's owner / controller — correct the sentence and both claims about it |
| 2 | **Major** | `CLAUDE.md` § Repository status has **no H9d paragraph** and its order sentence (line 28) still reads *"Order of the slices that remain: H9d, then H3c-3's remaining 14"*. H9a, H9b and H9c each have one; no task owned writing H9d's, and H3c-3's surface is `units.py`/`stats.py`, so nothing later would add it | Controller, before merge |
| 3 | Minor | README's `run` block hard-wraps `W-ENV-UNLOCKED`'s message over two lines; `demo` prints it as one, and nothing in the diagnostics printer wraps. README discloses the `~` path elision and not this, so the transcript still holds one line no command emits | Task 12's owner |
| 4 | Minor | `demo --into <occupied dir>` refuses (correctly, exit `1`) with a message that says *"`new` never overwrites an existing project"* — the wrong command for the invocation typed | Fix round 2's owner |
| 5 | Minor | The dated § Executability entry is pinned to `ebe58ca`; fix round 2 (`9c31d88`) then retired three `E-DEMO-*` identifiers and moved `demo`'s refusal from exit `2` to `1`. Re-date or append the amendment | Task 14's owner |
| 6 | Minor | Two pre-existing document facts positioned squarely under this slice's own sweeps: § Errors' `E-CODE-DIRTY` row still says *"`resume` when it is built"* though `resume` reads `built`; § Package layout lists `examples/generic/`, which does not exist and carries no `— not yet built` marker | Unowned — file |

**No Critical.** Nothing was found that loses a record, publishes a credential, or reports a wrong
number.

## Does README's transcript match what `demo` prints?

**Yes, with one wrap (Minor 3).** Run end to end through the installed console script in a scratch
`HOME` outside this repository: 129 lines, exit `0`. README's stop-1 block (including the
`template  templates/correlation.py` line), its stop-3 block including the whole commentary
paragraph, and its stop-5 block from the warning through the six-member correction-family paragraph
are **verbatim** what `demo` prints. `[Enter] to run it · q to stop here` is printed verbatim under a
pty and correctly absent unattended. The only text README shows that `demo` does not emit is the
second half of the hard-wrapped `no uv.lock found …` line.

**And the numbers are reproducible.** Two independent invocations in two scratch homes agree on every
printed digit; normalized for `$HOME` and run id, the **only** difference between the two 129-line
captures is the two lines naming the working directory.

## What the gate checked that a per-batch review could not

- **The scaffold's blast radius, against `main`'s own binary.** Built a `main` worktree, `uv sync`'d
  it, ran `publishable new` from each build, `diff -rq --exclude=.git`: **exactly one file differs,
  `README.md`** — and `main`'s `reference.md` already documented three of the four regions the code
  did not write, so the change closes a doc-vs-code gap rather than opening one.
- **Arm B's procedural re-scan, redone independently** with the unmodified helper and the unmodified
  literals: `pre` 15 → `post` 11, `post` equal to the shipped golden, removals exactly the four named
  entries, **zero** lines appearing that were not in `pre`.
- **`E-GIT-NO-REPO` enumerated by reading before grepping**, and the count reconciled site by site
  with the § Errors row's breakdown: 2 uncaught, 4 by code, 4 by type, with `provenance.py`'s internal
  call correctly excluded on the strength of `git_provenance` having exactly one caller.
- **Both consistency passes and the development-record rule**: 0 mechanical problems over the four
  documents named individually plus the feasibility analysis (links, anchors, duplicate anchors, table
  column counts, empty rows, whitespace, invisible unicode), with a can-fail control; the § Executability
  table byte-identical across the last eleven entries; all three touched records **pure appends**
  (`15 0`, `25 0`, `32 0`, zero deleted lines).
- **Three earlier-batch guards mutated**, each failing loudly: the region parser's duplicate check
  (2 failed), `credentials_body` emptied (9 failed across `test_docs.py` and `test_cli.py`), and
  `FreshSourceFileLoader.get_code` delegated back to the cache (3 failed, one per call site). Every
  mutation reverted by copying the backup back and each revert **verified by re-running**.

Checks not reached are listed at the end of `task-b3-review.md`.
