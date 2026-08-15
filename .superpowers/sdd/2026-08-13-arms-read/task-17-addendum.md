# Task 17 — controller additions

These are requirements, with the same force as the brief file they accompany.

## The 24 masked items are enumerated — go and read them

`docs/superpowers/H3c-SCOPING.md` § 1 "The three refusals" is the list. **Check each item off against
the code as it now stands, and say in your report which task closed it.** The brief says "check them off
rather than assuming" because this project has retired a refusal three times and each time the
retirement made a latent defect live: H3a's `measurements` × `weight_by`, H3b's `measurements` ×
`cluster_by`, and H3b's `k: all` budget.

The scoping names the two that would **ship silently rather than crash**, which are the ones your
check-off exists to catch:

- **the phantom parameter** (§ 5) — `runner.resolve_condition_cfg` writing a group cell's value into
  `parameters`, so `{arm: control}` becomes a parameter no template declares and flows into
  `parameters_hash`. Task 4 owned this; verify it, do not assume it
- **the invented arm membership** (§ 9) — a `measurements` collapse choosing an arm no row declared.
  Task 11 owned this; verify it

An item you cannot find a closing task for is a finding, not a rounding error. Report it rather than
retiring on top of it — the retirement is the irreversible half of this task.

## The refusals mask each other, so retire and re-run, not retire and reason

`E-SWEEP-GROUPS-UNSUPPORTED`, `E-DATA-ALLOCATION-UNSUPPORTED` and `E-DATA-ASSIGN-UNSUPPORTED` fire
together on the configs this slice's tests use, so **a check that was never reached may look implemented
because the suite is green**. After removing all three, run the full suite and read what newly fails —
and if nothing does, that is itself suspicious enough to say out loud in your report, because sixteen
tasks of new behaviour behind three refusals should leave some seam.

Note specifically that `E-DATA-ALLOCATION-UNSUPPORTED`'s message asserts group axes "are not implemented
either" — **task 5 falsified that** and the ledger routed the message to you. It goes with the code.

## The `NOT BUILT` count: seven → four

§ The one config file carries the count. The seven are `sweep.groups`, `data.units.assign`,
`data.units.holdout`, the `{resolver:}` form, non-`within` `allocation`, `statistics.resample`, and
`statistics.null_test`; this task removes the **first, second and fifth**. Four remain.

**The count appears in prose as a number.** Grep for the spelled word and the digit both — this repo has
already shipped "three phrases counting a table that grew". Anywhere the seven are *enumerated* rather
than counted, the enumeration changes too.

## Step 6's grep must be shown able to fail

"Grep every tracked `*.md` for all three codes; **prove the grep can fail** against one that exists."
That second clause is the whole point: a grep with a typo'd pattern, a wrong path, or a `--include` that
matches nothing reports zero hits for a code that is still there, and reads identically to success. Run
it against a code you know is present (`E-DATA-HOLDOUT-UNSUPPORTED` is still live) and show the non-empty
output in your report before trusting the empty one.

Grep **every tracked markdown file**, not just the four documents: `CLAUDE.md` and any
`docs/feasibility-*.md` are tracked and mention codes. `docs/superpowers/` is gitignored and does not
count — but do not "clean" it either; it is the working record.

## What must remain refused

Do not retire anything else while you are in that loop. `E-DATA-HOLDOUT-UNSUPPORTED` (H3d) and
`E-DATA-RESOLVER-UNSUPPORTED` (H7) stay, as do the narrow refusals this slice and its predecessors
minted: `E-DATA-ASSIGN-DRAWN`, `E-SWEEP-SAMPLE-BASELINE`, `E-DATA-WEIGHT-CONTRAST`,
`E-DATA-CLUSTER-CONTRAST`, `E-DATA-CLUSTER-DERIVED`. A refusal of a **combination** is not a refusal of a
**declaration** and none of them is in the five-field loop.

## Documentation

**Never write a phrase locating a table row by position.** Tasks 9, 10 and 11 did it five times and were
wrong twice, once in a row the diff did not touch. Name what a sibling row *does*; when you **remove** a
row, check every row your removal moved — that is the same hazard in the other direction, and this task
removes three.


## Corrections from the pre-flight audit — these override what is written above

**1. There is no "three refusals in the five-field loop", and that phrase describes an edit you cannot
make.** The loop in `validate.py` is a **two-entry** tuple — `("assign", E-DATA-ASSIGN-UNSUPPORTED)` and
`("holdout", E-DATA-HOLDOUT-UNSUPPORTED)` — with comments recording that `cluster_by`, `weight_by` and
`measurements` left it in earlier slices. `E-DATA-ALLOCATION-UNSUPPORTED` is a standalone `if
units.get("allocation") not in (None, "within")` above the loop, and **`E-SWEEP-GROUPS-UNSUPPORTED` is
emitted from a different function entirely** (`_check_unimplemented`). Three sites, not one loop. The
plan's verified-interfaces table is wrong on this; read the code.

**2. Your Files list is incomplete, and the omission is load-bearing.** The three codes appear outside
`validate.py` — in `sweep.py` and at several places in `cli.py`. **Three of those are unreachability
claims your retirement falsifies**, one of which says in so many words that it holds "until the slice
that retires it lands". The most important is `cli._vs_baseline_block`'s hard-coded `"paired": True`,
justified by exactly the two codes you remove — **task 16b now owns that one and lands before you**;
verify it did, and do not leave the docstring naming a code that no longer exists. Grep the whole of
`src/` for all three codes **before** removing anything, list every hit in your report, and say what
each one becomes.

**3. `sweep.groups` has no `_check_shape` guard, and it is yours.** `validate.py` says so in prose —
the slice that retires `E-SWEEP-GROUPS-UNSUPPORTED` owes it — and the ledger recorded the debt twice,
routed from tasks 5 and 6. A malformed `groups` block currently budgets the parameter-only product
silently. Add the guard in this task; retiring the refusal without it is retiring the only thing that
catches a malformed block.

**4. The `NOT BUILT` count IS stated in prose, spelled out, with all seven enumerated.** § The one config
file says *"Seven declarations above are not yet built, and each is marked `NOT BUILT` where it appears"*
and then lists them. It predates this branch, so it is not something the slice added. Update the
sentence, the spelled number, and the enumeration — three edits, not one.

## The full sweep, measured by the controller at task 16b — verify it, do not trust it

`grep -rn` for the three codes across `src/` and `tests/`, before your task ran. **Re-run it yourself
first**: tasks 16b and any fix rounds landed after this was taken.

**`src/` — 5 emit sites and 7 prose mentions.** The emit sites are all in `validate.py`:
`E-SWEEP-GROUPS-UNSUPPORTED` in `_check_unimplemented`, `E-DATA-ALLOCATION-UNSUPPORTED` as a standalone
`if`, and `E-DATA-ASSIGN-UNSUPPORTED` in the two-entry loop. **Three sites, not one loop** — the plan's
verified-interfaces table is wrong about this, as the corrections above say.

The prose mentions are the dangerous half, because each is a **claim that stops being true when you
remove the code**:

| File | What it claims |
|---|---|
| `validate.py`, near the `groups` shape discussion | that the slice retiring `E-SWEEP-GROUPS-UNSUPPORTED` owes the missing `_check_shape` guard — **that is you** |
| `validate.py`, in the allocation enum branch | that an out-of-enum `allocation` is "left to `E-DATA-ALLOCATION-UNSUPPORTED`'s blanket refusal to catch" — **false the moment you remove it**, and task 12's registry row was marked temporary for exactly this |
| `validate.py`, in the confounded-check region | a parenthetical naming the code |
| `cli.py` ×4 | four separate "no `run` can reach this line with a group axis" claims |
| `sweep.py` | that group axes are "still refused at `validate` … until the rest of" the mechanism lands |

Each is either deleted, rewritten to name what actually holds now, or — where the code becomes genuinely
reachable — backed by a check that makes the claim true again. **Say which of the three you did for each
one, in your report.** A claim left standing is the "comments claiming guarantees this branch does not
provide" failure, which this repo has a commit about and which this slice has now hit three times.

**`tests/` — roughly 40 assertions name at least one of the three**, most as members of an exact expected
set. Every one of those sets changes. That is mechanical, but it is also where a weakened assertion hides:
**do not convert an exact set to a membership test to make it pass.** If removing a code leaves a set
empty, that test now asserts a config validates clean — check that it should, and say so.

Three call out for attention:

- `tests/test_cli.py`'s end-to-end narrowing test (task 13) and the allocation tests reach `command_run`
  by monkeypatching **only** `validate._check_unimplemented`. **After your retirement that patch is
  unnecessary for the group-axis half.** The test's docstring says so and asks whoever retires the code
  to simplify it. Do that, and confirm the test still fails under the Step 5 mutation afterwards — a
  simplification that also removes the test's teeth is worse than leaving it.
- `tests/test_validate.py` carries a comment block stating all three "stay until the slice that retires
  them". Delete it with them.
- The two parametrized refusal tables (one listing `("groups", …)`, one listing `("allocation", …)` and
  `("assign", …)`) are the tests *of* the refusals. They go; check what remains of each table still has
  entries, and that no table is left with one row where it documents a family.
