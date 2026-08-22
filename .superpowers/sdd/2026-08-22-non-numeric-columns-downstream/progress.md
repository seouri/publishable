# H5b — non-numeric columns downstream to `aggregate` — the ledger

Branch `h5b-non-numeric-downstream`, off `main` at `5ee3a0c` + the docs commits above it. 16 tasks in
five batches, every batch reviewed. The slice's central fact, measured before it started: **it is not
additive.** Admitting a unit widens the inference base, so values move in columns holding no non-numeric
data at all — and the numbers it moves are **wrong on the record's own terms today**, one mapping
publishing `completed: 4` while `attrition` over the same executions says `completed: 6`.

## Batch 1 — tasks 1, 2, 3 — the pin captured before anything moves, and the document decisions

Commits `23b79a9` (the pin), `bc4e56e` (§ Templates), `2e9f5e4` (§ The per-unit tables, § Statistical
reporting, `W-STATS-REPEATS-DISAGREE`, one filing), `31a5f31`, review `20289d2` (**task 3 FAIL, one
Critical**), fix round `f0c4f2f`. Suite 2891 → **2895**.

**Arm E reproduces, and the reviewer re-measured it rather than reading the claim.** Plan correction 9
said the two-condition Holm half reproduces at `ee8085e` and moves **two keys the design does not name**;
independently re-measured with a fresh script, every literal matched — `n_paired` 4 → 6, the
`correction_level` swap, both `ci95_corrected` shifts, both unnamed extra keys, and every *must not move*
literal. **A non-reproduction would have been a finding rather than a fixture to repair**, which is why
it was re-measured; it is the one claim in this slice that everything downstream rests on.

**The Critical, and it is a controller defect before it is an implementer one.** Task 3 shipped a
§ Statistical reporting sentence codifying **all-or-nothing**: a column earns a block *"only when every
value carried for it is a real number"*, so one `None` costs the column its block for every unit — the
exact reading controller ruling 1 rejects, and **the silent-drop shape this slice exists to end**, traced
to reachable live code rather than argued.

**The root cause is structural.** The ruling was appended to the plan under a preamble asserting *"a brief
extracted from this plan carries these paragraphs"* — **and that was false**: `task-brief` extracts one
`## Task N` section and nothing else. So the ruling reached the controller and the reviewers and **never
the implementer**, which is this repo's own named failure mode, hit inside the slice whose plan documents
it. Fixed the only way that holds: **every one of the sixteen task sections now opens with a pointer
saying the rulings post-date it and win where they disagree**, and ruling 1 gained an amendment naming the
three mixtures — which is the second finding.

**The all-or-nothing sentence was right about one case and wrong about another**, which is why it read as
plausible and passed its own task:

- **non-numeric for every unit** — no metric block, and correct: there is no mean of strings;
- **a number for some units, `None` for others** — a block over the contributors, with **the contributing
  count reported rather than `completed`**, because an interval over five values published beside a
  `completed` of two hundred is a precision claim no later reader can catch;
- **`str` beside a number** — **cannot occur.** `_check_column_types` refuses it at `finalize`, measured.
  A read rule for it describes an unreachable state, and stating one invites a later reader to build
  against it.

**Two more things worth carrying.** Arms C and D were found to **already exist verbatim**, which is the
claim a reviewer should distrust most — an existing test may pin something *adjacent* — so the reviewer
mutated the production code each arm is said to guard and confirmed both fail; **arm D has no authorized
editor, so its passing is the proof.** And mutation (iv), reversing Holm's rank order, was disclosed as
moving only 2 of 3 correction-level assertions — **the argument is sound** (arm E's `mean_score` sits at
the median rank of a three-member family, and reversing an order cannot move a median) and the reviewer
verified it by running, then found the same mutation **also fails arm A**, an undisclosed side effect
rather than a weakness.

## Batch 2 — tasks 4, 5, 6 — the behaviour change

Commits `06fdd3d` (the collapse), `8ffab8a` (the disagreement disclosed from the rows), `252774b`
(`summarize_step`'s clause and Ruling 1's gate), review `4edd98d` (**task 4 PASS, tasks 5 and 6 FAIL —
seven Majors, three Minors**), fix round `ad67a75` / `a9b6340` / `bb74d04` / `ab1d18a`. Suite 2895 →
**2920**, and no existing test was edited or removed in the fix round.

**Ruling 1 behaves as ruled, verified end-to-end through the installed console script on a scaffolded
project outside the repo, for all three mixtures**: a column non-numeric for every unit publishes no block
and still reaches `aggregate`'s table; a column three of six units carry a number for publishes
`n: {resolved: 6, completed: 3, …}` — **the contributing count, which is the whole point**; and `str`
beside a number is refused at `finalize` at exit 4, so the read rule for it stays undocumented because the
state is unreachable.

**Task 6 widened its own scope, correctly and with disclosure, and that is the good news in this batch.**
Its brief said *no code change*; it shipped one, because task 4 had introduced a regression that Ruling 1
forbids — the reviewer built the three-way comparison (pre-batch `n=3` → task 4+5 `{}` → HEAD `n=3`) rather
than accepting the account. **A task that quietly widens its scope is a finding even when the code is
right**; this one did not do it quietly.

**The most consequential thing in the batch is a crash it deliberately left live.** Ruling 1's gate makes
task 7's unguarded subtraction reachable: measured end-to-end, a contrast over a ragged `None` column
gives a raw `TypeError`, **run directory complete, ten executions paid for, no `run.yaml`.** It ships as a
`xfail(strict=True)` asserting the **correct** post-fix behaviour and naming task 7 as its remover — so it
fails for the right reason now and flips to a strict `XPASS` failure the moment the gate moves. The
reviewer verified both halves of that device rather than the intent behind it.

**Ruling 5 is where a binding ruling was amended rather than enforced, and the amendment came from the
code.** Ruling 1 had called the coverage warning *not optional*, arguing an interval over five values
beside a `completed` of two hundred is a precision claim no reader can catch — **but the shipped count
made that claim impossible**, since `run.yaml` now publishes the contributing count. So the warning's job
shrank from *preventing a lie* to *telling the person who never opens `run.yaml`*, and an unconditional
warning would fire on runs with nothing wrong. It became **`W-STATS-COLUMN-THIN`**, per
(condition, step, column), against **`limits.min_reported_n`** — the floor three shipped rows already use
at `run` time against a realized denominator. **A second threshold for the same hazard would have been a
second source of truth.**

**Two properties of that mint worth keeping.** Its footprint was measured **before** any pin was written:
the suite was **unchanged** with the emit site live, because the scaffold's floor is 10 and its roster is
10, so a full column sits *at* the floor and `<` does not fire. **An emit site no default run reaches is
exactly where a dead check hides**, which is why it got three tests rather than a control. And unlike both
its siblings it has **no declaration gate** — that is Ruling 5 as written, recorded as a property rather
than absorbed silently.

**A false premise had three homes, and the sweep found the one nobody named.** The warning's message and
its § Warnings row both said a mixed numeric/string column *"is not a number"* and that *"those units
carry no value for it"* while the record published values for them. The dispatch named a third site —
`repeats_disagreeing`'s docstring — which turned out to be the one that was **already right**, and
sweeping for the **claim** rather than the file turned up a real third in § Statistical reporting. **Both
were deleted rather than rewritten**, and so was `_across_repeats`'s ground that task 6's own gate change
had falsified three paragraphs above its own contradiction.

**And two live behaviours had never been pinned at all** — the empty-record admission (`n_rows` 4.0 → 6.0)
and `_repeats_disagree`'s `(is-numeric, value)` tuple, both removable with the suite green. That is the
*pin weakened quietly* shape arriving in its other form: **never pinned in the first place.** The
`report_by` stratum path was a **ninth** moving-key class the design's enumeration missed, carrying a
**third** distinct `resample_draws` literal; it has an arm now. **Four distinct seed-dependent
`resample_draws` values are now labelled across the pin's arms** — which is the reason correction 7 said
that number is not a constant.
