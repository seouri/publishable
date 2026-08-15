# Task 2 + 3 report — the two document rulings

## Task 2: `blocked` beside clusters, and `auto` block size over an empty ratio

**§ Clustered units** (`docs/reference.md`): the sentence "With `method: random` or
`blocked` a cluster is drawn as a whole" no longer claims `blocked` does this. It now says
`random` draws whole clusters (still refused today as `E-DATA-ASSIGN-DRAWN`), and that
`method: blocked` beside a declared `cluster_by` is refused instead, naming the code task 11
mints: `E-DATA-ASSIGN-BLOCKED-CLUSTER`. Reason given inline: a block fills to an exact unit
count, a cluster is indivisible, and no block size honours both.

**§ Allocation**'s `blocked` paragraph got the same amendment, plus task 2 step 2: `auto`
block size is stated explicitly as **twice the number of levels** over an empty `ratio`
(equal allocation, one part per level, so the sum is the level count) — a two-arm trial
gets 4, a three-arm one gets 6.

Both edits keep naming `E-DATA-ASSIGN-DRAWN` for `random` (9/1 site count from task 1's
report is unchanged — confirmed by grep after editing). Neither edit touches the temporary
"refusal lifts" language for `E-DATA-ASSIGN-DRAWN` itself, since that code's retirement is
task 14's job, not this one's.

Commit: `704111c` — "docs: settle blocked-beside-clusters and auto block size over an empty ratio"

## Task 3: which row owns the stratum fault

Edited the two overlapping § Validation rows to name what the other covers, by row name
rather than position:

- *Stratification attribute exists* now says it covers a `fold` level's or `holdout`'s
  `stratify_by` only, and names *Allocation strata exist* as the row for
  `assign.<axis>.stratify_by` (including the axis-name case).
- *Allocation strata exist* now says it owns every `assign.<axis>.stratify_by`, including a
  target naming a group axis, unlike *Stratification attribute exists*, whose `fold`/`holdout`
  targets admit only a unit attribute.

Minted `E-DATA-ASSIGN-STRATIFY-UNKNOWN` and inserted its registry row in
§ Errors `validate` reports, in alphabetical sort order between `E-DATA-ASSIGN-MISSING` and
`E-DATA-ASSIGN-UNKNOWN` (`DRAWN` < `LEVELS` < `METHOD` < `MISSING` < `STRATIFY-UNKNOWN` <
`UNKNOWN` < `VARIES`).

Fixed `E-REPL-FOLD-STRATIFY-UNKNOWN`'s registry row, whose closing sentence previously
promised "the same § Validation row covers `holdout.stratify_by` and
`assign.<axis>.stratify_by`, each reported by its own code once its block is built" — that
promise broke under the new ruling, since `assign.<axis>.stratify_by` is now *Allocation
strata exist*'s row, not the same row `holdout.stratify_by` uses. Rewrote it to say
*Stratification attribute exists* covers `holdout.stratify_by` (own code once built), and
that `assign.<axis>.stratify_by` is the separate *Allocation strata exist* row, with its own
code `E-DATA-ASSIGN-STRATIFY-UNKNOWN`.

Commit: `98086c5` — "docs: allocation strata exist owns the assign stratum, and its code is registered"

## Verification

- `uv run ruff check .` — all checks passed (no code touched).
- `uv run pytest -q` — 1502 passed, 2 xfailed (baseline unaffected, no code touched).
- `git grep -n 'E-DATA-ASSIGN-DRAWN' docs/*.md` still returns 10 (9 reference.md / 1
  experimental-designs.md) — unchanged from task 1's count, confirming neither edit
  accidentally removed or duplicated a site.
- Table row column counts spot-checked against header and neighboring rows (4 pipe-delimited
  fields throughout, matching the 2-column table).
- No trailing whitespace introduced (checked via `git diff -U0 | grep ' $'`, empty).
- All markdown links touched (`#validation`, `#allocation-within-subjects-or-between-subjects`,
  `#expansion-modes`, `#a-fixed-holdout-split`, `#weighted-samples`) are reused existing
  anchors, not new ones.

## Follow-up fixes after an advisor pass

A second pass (prompted by the advisor, before declaring done) found three things the
first pass missed, all now fixed:

1. **`docs/experimental-designs.md` § "Resolve the three declarations" had a stray site.**
   It said declaring `cluster_by` "constrains how `fold` splits and how `between` allocation
   assigns" — true for `random`, no longer true for `blocked`, which the task-2 ruling
   refuses outright beside a declared `cluster_by` rather than constraining. Task 1's
   reconnaissance enumerated `E-DATA-ASSIGN-DRAWN` sites, not every site describing
   cluster-vs-`blocked` interaction, so this one wasn't on that list. Fixed to name `random`
   specifically and state the `blocked` refusal. Commit `77ee13a`.
2. **My own two task-3 edits disagreed with each other.** *Allocation strata exist* said it
   "Owns every `assign.<axis>.stratify_by`" with no method gate, while the
   `E-DATA-ASSIGN-STRATIFY-UNKNOWN` registry row I minted opened "Under `method: random` or
   `blocked`" — so under `by_attribute` a reader following the row to its code would find a
   code that declines to fire, breaking § Validation's own promise that "a row here and a
   code there are the same check seen from the two ends." Tightened the Validation row to
   name the same gate (`stratify_by` "means nothing" under `by_attribute`, per § Allocation),
   so the two now agree. Commit `6923b07`.
3. Re-ran the count-phrase sweep the advisor pointed at (`git grep` for number words near
   "code"/"row"/"E-DATA-ASSIGN"/"registry" across the four documents, `CLAUDE.md`, and
   `spec-defects.md`) — no phrase anywhere counts *how many* `E-DATA-ASSIGN-*` codes exist,
   how many § Validation or § Errors rows there are, or otherwise totals something my
   insertion changed the count of. The nearby count claims that do exist (`E-RUN-*`'s "six",
   `§ auto derives from`'s per-row list, `docs/superpowers/H3c-2-SCOPING.md`'s "9×/1×/ten")
   are all either unaffected by my edits or are planning-doc text outside this task's file
   list. Confirmed `E-DATA-ASSIGN-DRAWN` is still 9 (`reference.md`) / 1
   (`experimental-designs.md`) after every edit.

Re-ran `uv run ruff check .` (all checks passed) and `uv run pytest -q` (1502 passed, 2
xfailed) after these fixes; both stayed green throughout, as expected since no code changed.

## Concerns / open items (not fixed here, out of scope for tasks 2–3)

1. **`docs/reference.md` line 280, "Stratification is forward-only"** (`assign.sex.stratify_by:
   [arm]` declared after `arm`) has no corresponding row in § Errors `validate` reports at
   all — task 1's recon didn't flag this, and it surfaced while placing the new
   `E-DATA-ASSIGN-STRATIFY-UNKNOWN` row next to its neighbors. This is a pre-existing gap
   unrelated to either brief's ruling (it's about *order*, not *existence*) and I left it
   alone; flagging in case task 10/11/12/13 needs a code for it and finds none registered.
2. **`E-DATA-ASSIGN-BLOCKED-CLUSTER` (task 2's new code) is now named in prose at two sites
   with no § Errors `validate` reports row and no § Validation row of its own** — a fair
   reading of "name the code task 11 mints," since task 2's brief asks only for the prose
   amendment. But task 11 owes *two* rows, not one, or the next mechanical pass finds a code
   named nowhere in either registry table — the same shape as concern 1 above.
3. Both briefs' rulings were internally consistent and matched task 1's reconnaissance
   exactly (the quoted rows, the code family, the sort-order neighbors). Nothing in either
   brief looked wrong, unsatisfiable, or resting on a false premise.

## Coordinator review pass — two more rulings, one gap resolved

The coordinator's review (after the advisor pass above) made two rulings and asked for two
mechanical fixes. All four are now in `docs/reference.md`.

**Ruling A — `assign.<axis>.stratify_by` under `by_attribute` is refused, same as `ratio`.**
§ "who went where" already called this "the same fault" `ratio`'s by-`attribute` refusal
names, without the refusal itself existing for the stratify half — stated non-coverage being
a harder claim than the ambiguity it replaced. Added a sentence to § Allocation, phrased to
match the `ratio` sentence exactly: "The same is true of `assign.<axis>.stratify_by`: under
`method: by_attribute` it would describe how a draw was balanced when none was — the same
fault — so `validate` rejects a non-empty one there too rather than recording a balance the
data may not honour." No code named — same as `ratio`'s own refusal, which names none either
(a pre-existing gap task 1 flagged as "Already false / already disagreeing", not this
task's to close). **Recording for the brief that implements it: task 5, which implements the
`ratio` half of this refusal, now owns the `stratify_by` half too — not a new task.**

This also ratifies the method gate I added to *Allocation strata exist* during the advisor
follow-up (`stratify_by` "means nothing" under `by_attribute`): it was the reviewer's own
flag that the gate was a decision neither brief made outright, and it reads as correct now
that `by_attribute` gets its own explicit refusal to route to instead of silence.

**Ruling B — dropped "earlier-resolved" from `E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s registry
row.** As I'd first written it, the row's forward-only clause duplicated a fault that
belongs to a *different* § Validation row, *Stratification is forward-only* — whose own
example (`assign.sex.stratify_by: [arm]` with `arm` declared after `sex`) is exactly the
shape my clause described. One code answering to two rows breaks § Validation's stated
promise that "a row here and a code there are the same check seen from the two ends."
Reworded the registry row to existence-only ("neither a unit attribute … nor a
`sweep.groups` axis at all") and added a sentence routing the order question to
*Stratification is forward-only* by name, under its own code, rather than describing the
order rule inline.

**Recording for the brief that implements it: *Stratification is forward-only* has no
code at all today** — confirmed again at this fork point: `git grep -n
'Stratification is forward-only\|forward-only'` on `docs/reference.md` finds the one
Validation-table row (line 280) and no matching § Errors `validate` reports entry.
**Task 13 mints `E-DATA-ASSIGN-STRATIFY-FORWARD`** for it; this is now the second gap of
this shape recorded in this report (the first being concern 1 above, which this ruling
does not resolve — the forward-only row still has no code, it simply isn't
`E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s job to be one).

**Minor — the two inline `block_size: auto` schema comments were still wrong after task 2.**
Both read "twice the ratio's sum" beside the `ratio: {}` `init` writes, which is literally
zero without the § Allocation sentence in hand. Both now read "twice the ratio's sum, or
twice the level count when ratio is `{}`" — the config-schema fenced example near line 100,
and § Allocation's own fenced block at line 1192.

**Recorded, not fixed, per the coordinator's instruction:** `E-DATA-ASSIGN-BLOCKED-CLUSTER`
(task 2's code) still has no § Errors `validate` reports row and no § Validation row —
task 11 owes *both*, not one, or a later mechanical pass finds a code named in prose and
registered nowhere. (Already noted above as concern 2; restating per the coordinator's
explicit ask.) The three forward references now in the doc — `E-DATA-ASSIGN-BLOCKED-CLUSTER`,
`E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s own row (reachable only once tasks 10/12 build the block
it checks), and `E-DATA-ASSIGN-STRATIFY-FORWARD` (not yet minted anywhere, only named here
for task 13's brief) — are left as forward references with no "not built in this build"
marker, per the coordinator's explicit instruction not to add one.

Re-verified after all four changes: `uv run ruff check .` (all checks passed), `uv run
pytest -q` (1502 passed, 2 xfailed), `git grep -c 'E-DATA-ASSIGN-DRAWN' docs/reference.md
docs/experimental-designs.md` still 9/1, no trailing whitespace introduced (`git diff -U0 |
grep ' $'`, empty), and the one edited table row (line 442) still carries 4 pipe-delimited
fields matching its header.

Commit: `64d5b1b` — "docs: refuse assign stratify_by under by_attribute, and narrow the new code to existence only"

(One wording correction after writing this section: the registry row first said the
forward-only fault is "reported under its own code" — overclaiming, since that code doesn't
exist until task 13 mints it. Reworded to "a different fault instead … order is not this
row's question," which doesn't assert a code that isn't there yet, before this commit.)
