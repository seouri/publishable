# Task 1 report — The documents first

**Status:** Complete.
**Commit:** `f9eecb7` — `docs: name the arm checks the code is about to implement` (`docs/reference.md` only; `docs/superpowers/` is gitignored, so the spec-defects entry below is uncommitted by design).
**Tests:** `uv run pytest` → **1391 passed, 2 xfailed** in 76.7s — unchanged, as required. No `src/` or `tests/` file touched.

---

## Step 1 — the two rows written from nothing

Read both siblings first (*Cluster is constant within a unit*, *Weight is constant within a unit*)
and phrased the new rows as they are. Neither row existed, and no differently-titled row in
§ Validation covered either case — checked by grepping every `assign.` mention in the table.

**`assign.<axis>.from` constancy**, placed immediately after *Attribute assignment resolves*:

> | Arm is constant within a unit | `assign.arm.from: arm`, and `p1`'s [measurement rows](#what-isnt-a-repeat) declare `control` and `treatment` — the collapse would file `p1` under whichever the file lists first, so the order the file happens to be in would decide which condition `p1` is measured in |

The consequence clause is deliberately **not** the weight sibling's. `sum` over a weight column
yields a number no row declared; an arm column is a string, `mean` is rejected for it, and only
`first`/`mode` are available — so the collapse always picks a value *some* row declared. The
arm-specific harm is the one that discriminates this row from its two siblings: cluster decides
which side of a split a unit lands on, weight decides how much it counts for, `from` decides
**which condition it is measured in**. The row says that and nothing stronger.

**`assign.<axis>.method` presence and enum**, placed after *Arms need allocation* and before the
three rows that depend on the discriminator (`ratio`, `block_size`, `by_attribute`):

> | Assignment names a method | `assign.arm` declares `stratify_by` and no `method`, or a `method` of `by_column` — the methods are random, by_attribute, blocked, and which of the block's other fields are read follows from which one it is. That a block must exist at all under `allocation: between` is the "Allocation needs arms" and "Every axis is assigned" rows above, between them, so it earns no row of its own |

Enum order and spelling are `random | by_attribute | blocked`, matching § The one config file's
inline comment, § Allocation's, and `experimental-designs.md`'s prose. The "the methods are a, b, c"
phrasing copies the existing *Sample is drawable* row rather than inventing a form.

**Answering the brief's question: `assign` REQUIRED-when-`between` needs no row of its own.**
Two existing rows already cover it between them — *Allocation needs arms* (`between` with no
`groups` axis to name the arms) and *Every axis is assigned* (a declared axis with no block). An
empty `assign: {}` under `between` is caught by the second; `between` with no axes at all by the
first. A third row would restate their conjunction. Stated inline in the new row so the next
reader doesn't re-derive it.

## Step 2 — the two rows this slice breaks

**Grid size sane.** The example was fine; the *rule* was silent about where the condition count
comes from, and `expand` ignoring `groups` is exactly what makes that silence wrong. Added:
"conditions counted over every axis the sweep expands, a group axis included, since a group level
is a condition that executes like any other."

**Baseline leaves contrasts confounded.** This row was the real defect. Its example was
`arm: control` + `analysis.method: pearson` — a group axis crossed with a parameter axis — while
its implemented twin `W-SWEEP-BASELINE-CONFOUNDED` states in its own row that the check reads
"`sweep.grid`'s axes alone — no other mode's". Once `groups` is real, the row's own example
describes a warning that never fires. Two things were also arithmetically stale: "2 of 3
contrasts" is not what that shape gives.

Rewrote it to a grid-only example and recomputed the count **against `expand` itself** rather than
by hand. Baseline `{analysis.method: pearson, analysis.min_samples: 30}` over
`method: [spearman, kendall] × min_samples: [30, 50]` expands to 5 conditions — `expand` emits the
baseline as its own leading condition and does *not* merge a grid cell that coincides with it — so
4 contrasts, of which `spearman/50` and `kendall/50` differ on both axes: **2 of the 4**. The grid
values are named in the row so the number is auditable rather than trusted. Both paths are real
`generic` parameters and § Expansion modes already uses that exact baseline pair with grid values
excluding the baseline's, which is the convention followed here — deliberately, since a grid
*including* the baseline's values produces a duplicate cell and a count a reader would misread.
The row now also states that a baseline fixing a group axis is outside the check and that the
contrast is still marked where it is formed.

I deliberately did **not** extend the check to group axes: that would state a rule no task in this
slice owns, and `W-SWEEP-BASELINE-CONFOUNDED` commits to grid-only with a long rationale.

**A fifth edit, reported rather than shipped quietly.** `W-SWEEP-BASELINE-CONFOUNDED`'s own row
said "**That mechanism is the `grid` case only, and the other two are silence for a narrower
reason**" — a phrase counting the modes outside the check, which `groups` makes three. That is the
trap commit `e91cf0d` fixed elsewhere. Dropped the count ("every other mode") rather than bumping
it. The same row's closing claim that the remedy "names an outcome only a free `grid` axis
delivers" is also false once `groups` is real — § Expansion modes says the baseline expands over
whichever axes it doesn't fix, "group axes and parameter axes alike", so a free group axis
delivers it too. Reworded to say a free `grid` axis delivers it and a free `paired` one does not,
and that a free group axis does deliver it but is silent here because the check reads neither a
group axis nor a baseline fixing one. That silence is **labelled rather than left bare** — the row
now says it is deliberate, the run-time `confounded: true` marking being the disclosure and this
warning a `grid`-only convenience over it, so nothing is owed. § Expansion modes already argues
that position ("the expansion doesn't distinguish group axes from parameter axes"). Also changed "Silence in any of the three" → "Silence under
any of them", the same countable-phrase defect one sentence later.

## Step 3 — the `assign.seed` digest inconsistency: **the document is right**

§ What `auto` derives from: digest over "`data.units` (every field except `assign.seed` itself)".
`hashes.design_digest` canonicalises `{"units": units, "groups": groups}` wholesale, so a pinned
`assign.seed` is inside it.

**The document is right; the code changes in task 16.** The section's own argument settles it:
pinning a seed is "the deliberate act", and every `auto` value in its table mixes the digest — so
with `assign.seed` inside, pinning the `arm` axis's seed would move every repeat seed, every fold
boundary, every `sweep.sample` draw, and every *other* axis's allocation. That is precisely the
"one visible change and two invisible ones" confounding the section exists to refuse. It is also
what keeps the table row *An axis's `assign.seed` | digest + the axis name + the resolved roster*
honest: a value derived *from* the digest must not feed it.

The fix is one line — drop `seed` from each `assign.<axis>` block before canonicalising, keeping
`method`, `from`, `stratify_by`, `ratio`, `block_size` inside, since those describe what is being
randomized over. **No document change is owed.** `src/` untouched, per the brief.

Recorded in `docs/superpowers/spec-defects.md` (CLAUDE.md's channel for a live code-diverges gap;
existing entries are shaped exactly this way), naming task 16 as owner.

## Identifiers

**No new identifier was introduced, and none is owed here.** § Validation's main table is
two-column and codeless, and there is no `E-DATA-ASSIGN-*` code anywhere in the repo: the whole
`assign` block is refused today as `NOT BUILT`, and § Errors `validate` reports says the
`-UNSUPPORTED` family is deliberately absent from that registry. The eight existing `assign` rows
in § Validation are codeless for the same reason, and the two new rows match that precedent
exactly. Task 17 owns retirement and whatever registry rows come with it. Nothing was retired and
the `NOT BUILT` count is unchanged (still seven, § The one config file untouched).

## Passes run

**Mechanical** — one throwaway script over `README.md`, `CLAUDE.md`, `design-principles.md`,
`experimental-designs.md`, `reference.md`, `feasibility-llm-growth-studies.md`; fenced blocks
skipped for headings/tables/links. Result **CLEAN, 0 findings**.

Each check was proved able to fail by planting a fault in a scratchpad copy of `reference.md`:

| Check | Planted fault | Flagged |
|---|---|---|
| Table column count | extra `\|` cell on the new *Arm is constant* row | `table row has 3 cells, header has 2` |
| Empty table row | inserted `\|  \|` | `table row has 1 cells` + `empty table row` |
| Anchor resolution | `#expansion-modes` → `#expansion-modez` in *Grid size sane* | `unresolved anchor #expansion-modez` |
| Duplicate anchor | renamed `### Warnings core reports` → `### Validation` | `duplicate anchor #validation (also line 204)` |
| Trailing whitespace / tab / invisible unicode | two spaces on the new *Assignment names a method* row | `trailing whitespace` |
| En dash in an anchor | `(#expansion–modes)` | `en dash in a heading or anchor` + unresolved anchor |

The slugger was itself corrected mid-pass: it initially stripped `_` and produced six false
"unresolved anchor" hits on `#a-step-that-partitions-needs-a-seed-and-derive_seed-...`, which
GitHub keeps.

**Cross-document**, over the classes the brief called most plausibly disturbed:

- **Enum comments** — grepped every tracked `*.md` for `by_attribute`. The assign enum is
  `random | by_attribute | blocked` in § The one config file (line-free cite: the `assign` comment),
  § Allocation's YAML, and `experimental-designs.md`'s "Three choices sit below an answer". The new
  row lists all three in that order. `holdout`'s narrower `random | by_attribute` is untouched.
- **Schema fields in prose** — both fields the new rows name (`assign.<axis>.method`,
  `assign.<axis>.from`) already appear in § The one config file's `assign` comment and in
  § Allocation's two YAML blocks. No config field was added, so § The one config file needed no edit.
- **Removed-string grep** — the deleted `arm: control` example. Every surviving `arm: control` /
  `arm=control` occurrence was checked: § Expansion modes' baseline table row still says a contrast
  differing on two axes is *marked* `confounded: true` (marking at run time, not warning at
  validate), which my edit affirms rather than contradicts; `experimental-designs.md`'s
  "nothing is confounded" passage is the free-axis per-cell case and is unaffected. `2 of 3` appears
  nowhere else.
- **Declared vs. derived** — the digest verdict above is exactly this class; the document's claim
  stands and the code is the divergent side.
- **Worked example** — untouched. `cohort-pilot`'s 3 conditions, 240/228/12 units, and every
  interval are unchanged; § Validation rows are illustrative failures, and the one I rewrote uses
  the same `{analysis.method, analysis.min_samples}` pair § Expansion modes already uses.
- **Prevented mistakes** — checked `experimental-designs.md` § Mistakes core prevents: it carries no
  row for the cluster or weight constancy checks either, so the arm one needs no mirror there.

## Concerns

1. **`holdout.seed` is the same defect one field over.** The document excludes only `assign.seed`
   from the digest, so as written it endorses `data.units.holdout.seed` perturbing every other
   derived draw. `holdout` is `NOT BUILT`, so nothing exhibits it; the slice that builds it owes
   either the same exclusion or a stated reason the two seeds differ. Recorded in `spec-defects.md`;
   not edited, since that slice owns the block.
2. **A third § Validation row this slice pressures, which the brief did not name.**
   *Leave-one-out is affordable* counts `{kind: fold, k: all}` over the roster, but under
   `allocation: between` folds are drawn **within each cell** — the *Folds fit inside the cells* row
   says so — making `k: all` the cell's unit count, not the roster's. Its example is a `within`/grid
   one, so the example stays true and only the rule is unstated. Left alone deliberately; flagging
   it for whichever task owns the between-subjects fold budget.
3. **`W-EXEC-BUDGET` was deliberately left alone.** It says "conditions × repeat total", which
   post-`groups` includes group cells by definition — less specific than the *Grid size sane* row
   but not contradicted by it. Editing it would have bought nothing.
4. **The new rows are forward-looking**, like the eight `assign` rows already beside them: they
   describe checks no build performs yet, because the whole block is refused. That is the intended
   shape here (documents lead code), but it means tasks 2–20 are the only thing that makes them
   true, and nothing in this repo will detect it if one of them is never implemented.
5. **`docs/superpowers/` is gitignored**, so the spec-defects entry is not in the commit. Worth
   knowing if the digest decision is expected to travel with the branch.
