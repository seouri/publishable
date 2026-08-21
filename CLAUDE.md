# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status: specification and implementation

This repository holds both the normative specification and the tool it specifies.

- `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md` and
  `docs/reference.md` are **the four documents**. They are normative and they lead.
- `src/publishable/` is the implementation. It follows the documents. Where it cannot
  follow them, **the document changes first** — record the gap in
  `docs/superpowers/spec-defects.md` rather than diverging silently.

**Commands:**

| Task | Command |
|---|---|
| Tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Types | `uv run mypy` |

`docs/reference.md` § Package layout describes a tree that now **partially** exists.
Modules not yet built are still planned, and the slices that build them are listed in
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md`.

**Order of the slices that remain: H8c, H9, and H3c-3's remaining 14 — the H4 and H7 families
are complete, and H8a and H8b are.** Amended twice on 2026-08-14
against outside evidence — all nine experiments in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) were run through `validate`, and
**none executed**. The gate was the **template registry**, not the plugin system: `get_template` read a
builtin dict, so every config stopped at `E-TEMPLATE-UNKNOWN` before any other check — but § Templates
gives a template three homes, and a **project-local** one in `templates/` is *discovered by path*, not
through an entry point. **H7a was that subset** — `register_template` exported, `templates/**` discovered
by path, `generate template` — and it needed none of entry-point resolution, probes or the change gate.
**It merged on 2026-08-15 and that gate is gone.** **H4a (`resample`) merged the same day** — one refusal
retired that 8 of 9 configs hit, a regression preserved, and **zero experiments newly executing**, which
is the honest form of that number. **H3d (`holdout`) merged on 2026-08-16, in the identical honest form**:
one refusal retired that 6 of 9 configs hit (`E-DATA-HOLDOUT-UNSUPPORTED`), one live defect closed (a
`fold` beside a cell structure validated clean and produced empty per-arm folds; both that and a holdout
beside the same structure are now a named refusal, `E-REPL-FOLD-CELLS` / `E-DATA-HOLDOUT-CELLS`), and
**zero experiments newly executing** — all nine still declare a resolver and still earn
`E-DATA-RESOLVER-UNSUPPORTED`, which is H7b's. A re-measurement dated 2026-08-16 is in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) § Executability on this build. That
prediction for H4b was written when all nine still declared a resolver; **H7b has since landed and H4b
split**, so what H4b-1 actually delivered is the entry below — the refusal retired, three configs' last
core-side blocker gone, and the executable count unmoved all the same.

**H7b Part A (plugin registries and entry points) merged on 2026-08-17.** A plugin installed on the
machine can register a template, resolver, probe, reader and writer, and `validate` resolves any of
their names **without importing the package** — verified by probe with a positive control, not by
reading. It retires no refusal and executes nothing new: `E-DATA-RESOLVER-UNSUPPORTED` stays alive,
and **Part B** owns the resolver's dispatch, its read-only `io`, attribute projection,
`provenance.plugin_versions`, `plugin new`, and a credential leak Part A deliberately did not narrow —
`command_run` computes its credential set long after `resolve_units` with no enclosing `try`, so once
a resolver runs user code an exception can carry a credential to `main`'s un-redacted printer. The
measurement is [`H7b-SCOPING-2.md`](docs/superpowers/H7b-SCOPING-2.md), which re-measured its own
predecessor a day later and found **seven of its conclusions did not survive**.

**H7b Part B (resolver dispatch) merged on 2026-08-17.**
`E-DATA-RESOLVER-UNSUPPORTED` is retired. A resolver dispatches at `validate` and `run`, projects onto
declared attributes, must yield the field a declared `measurements.by` names, and may not read a swept
parameter. This is the project's **first non-zero executable count**: **three of nine — E1, E2, E5 —
have no remaining core-side blocker**, measured by running each config's `data`/`statistics` blocks
through `validate_config` rather than re-derived from emit sites, in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) § Executability on this build. Both
qualifications stay attached to that number: the plugin must exist and be installed, and a declared
apparatus probe is neither executed nor recorded (`cli.py` writes `apparatus: null` unconditionally
regardless of what a template declares — filed, owned by H7d, **which H7d Part A has since built** —
see the entry below, where the executable count stays unmoved all the same). Six stayed blocked on two causes neither
of which is H7b's: `io.reuse_from` (unbuilt, unowned) for E3, E4, E6, and `E-DATA-WEIGHT-CONTRAST`
for C1–C3, **which H4b-1 has since retired** — see the entry below, where C1–C3 stay non-executable on
`io.reuse_from` alone. Also closed: `hash_index` was broken for every source, table and glob included,
not only the resolver's, and had no filing — closed and struck in the same entry; and the credential leak
Part A left open — a resolver's raise now becomes a redacted diagnostic at both `validate` and `run`,
except a `KeyboardInterrupt`, which is deliberately re-raised as a traceback carrying no message so
Ctrl-C still stops the command.

**H4b-1 (weights through contrasts) merged on 2026-08-17.** `E-DATA-WEIGHT-CONTRAST` is retired. A
`data.units.weight_by` declared beside a comparison now computes a weighted contrast over the paired
intersection, its interval is its own construction there, and the record carries `weighted_by` and
`n_paired_effective`. **No-remaining-core-side-blocker was said to go three → six** here — C1, C2 and C3
joining E1, E2 and E5 — measured the same way, by running each config's blocks through `validate_config`. **The
executable count stays at three**, because C1–C3 also need `io.reuse_from`, still unbuilt and unowned.

**CORRECTED 2026-08-20 by H8's scoping: that phrase answers no consistent question, and every later
entry below repeats it.** The contradiction is verbatim in one table cell of the feasibility analysis —
C1 reads *"blocked on `io.reuse_from` (no remaining core-side blocker either)"* while E3/E4/E6 read
*"blocked on `io.reuse_from`"* and are excluded from the six. **One dependency, two treatments.** If
`io.reuse_from` counts as a core-side blocker the answer is **three**; if it does not, E3/E4/E6 qualify
too and the answer is **nine**. Six is really the count of configs that **validate clean while still
needing `io.reuse_from`** — E3, E4, E6, C1, C2, C3 — a useful number wearing the wrong name, which
followed C1–C3 out of the *refused* column when H4b-1 retired `E-DATA-WEIGHT-CONTRAST` without anyone
re-asking what it meant. **And "three" did not survive either** — H8a's design measured the
`report_by`-under-`resample` gap live on **seven of nine** configs (E1, E2, E4, E6, C1, C2, C3) while the
record charges it to C1–C3 alone, so **E1 and E2 sit inside the three carrying the gap E3/E4/E6 are
excluded for.** One dependency, two treatments, again. **So quote no single number for this analysis'
executability: quote the table** in the last two entries of
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) § Executability on this build, **or
name the dependency** — `io.reuse_from` for six, the `report_by` gap for seven, and **8 of 8 validating
clean, which is the only figure `validate` can see.** Both wrong figures were made the same way: a slice
retired one blocker, moved configs out of the *refused* column, and **carried the summary phrase forward
without re-deriving what it counted.**
Three things worth carrying. The refusal's own message, its § Errors row and the charter all named
`paired_t_over_units` as the estimator needing weights, and **all three C configs declare `resample`**,
so the payoff actually runs through `paired_percentile_of_derived` — a slice built from that charter
would have shipped a payoff that never runs. **The four documents gave a weighted contrast no `method`
string at all**, so the vocabulary was minted in `reference.md` before any code emitted it. And a
weighted contrast **whose metric is derived** is the exception: core hands the template the weight
column and does not weight the delta itself, so the `method` stays unweighted and `cohens_d` is `null`
while `weighted_by` and the effective size travel regardless. Out of scope with their routes: clusters
through contrasts, **which H4b-2 has since retired** — see the entry below; the unpaired forms,
**which H4c has since retired** — see its entry below too; and `null_test`, **which H4d has since
built** — see its entry below, the last of the four.

**H4b-2 (clusters through contrasts) merged on 2026-08-18.** `E-DATA-CLUSTER-CONTRAST` is retired,
and `E-DATA-WEIGHT-CLUSTER-CONTRAST` is minted for the one combination still refused: a design
declaring both `weight_by` and `cluster_by` beside a comparison, because a weighted clustered
interval's df comes from the cluster count rather than from Kish's effective size and the two
constructions coincide in any fixture not built to separate them. **It unblocks zero configs**, and
both counts stay exactly where H4b-1 left them — six with no remaining core-side blocker, three
executable — because no config in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) declares `data.units.cluster_by`
at all; a retired refusal nothing hits is not an execution. A clustered comparison now records
`paired_t_over_units_clustered` or `paired_percentile_over_units_clustered`, with `n_paired_clusters`
beside `n_paired`. One live defect closed for every config regardless of cluster: a contrast draw
whose every stratum's rows are identical now reports `ci95: null` rather than a zero-width interval.
A `report_by` level's recorded-column interval staying `t_over_units` under a declared `resample`
stays live on C1–C3, created by neither a weight nor a cluster, declined in writing and re-owned to
H4c rather than folded in. **The whole-branch review found a Critical no per-task review could**: with
the refusal gone, a derived key colliding with a recorded column's name published an *unclustered*
contrast interval — half-width 2.0 beside per-condition cluster-robust values at 10.31, `validate`
reporting zero errors — reachable because `derived_by_key` and `resample_fns_by_key` are both built
before the `summarize_step` call whose `except ContractError` retry clears neither. **That one corner
was given four wrong grounds in four separate commits**, each an answer from a proxy rather than from
the state the code branches on, and the last of them cited a row rewritten in the same breath. Only an
end-to-end `run` exposed it; every direct-call probe hand-built the maps and so never reached it.

**H4c (unpaired contrasts) merged on 2026-08-18.** `E-DATA-ALLOCATION-CONTRAST` is retired: a contrast
across a declared `sweep.groups` axis is computed. § Statistical reporting had named unpaired
constructions **in the present tense that did not exist** — `welch_t_over_units`,
`unpaired_percentile_over_units` and their `_clustered` spellings now do, with `cohens_ds`.
`E-DATA-WEIGHT-ALLOCATION-CONTRAST` is minted for the weighted unpaired pair, deliberately not built.
**It unblocks zero configs** and both counts stay where H4b-1 left them — six with no remaining
core-side blocker, three executable — because the nine configs declare `allocation: within` with
`groups: []`. Four things worth carrying. **`Member` gained a third evidence *kind*, `sides`** — the
exactly-one rule became a count over three, where both prior slices had added modifiers instead;
a Welch interval's evidence is two per-side value vectors, neither a pool nor differences.
**`paired` is now derived**, which was the last hard-coded claim in the contrast record, and the
regression pin guarding that change was captured **before** anything moved and covers each cell's α
*and* its own df — the hole H4b-1 left. **`n_paired` is absent, not null, on an unpaired entry** —
the first conditional write of a record key here, because `0` already means *pairing failed* — with
`n_of`/`n_against` and `n_clusters_of`/`n_clusters_against` beside it. And the unpaired clustered df
is **Welch-Satterthwaite over two cluster-robust per-side variances**, each contributing `G_s − 1`;
`min(G)−1` and `G_total−2` are named as rejected readings, and a real `run` confirmed a non-integer
df of 3.735 rather than either. **The derived-collision corner was given a fifth wrong ground here**,
in a comment asserting `sides` was unreachable from a function that builds it fifty lines later —
five wrong grounds across two slices, every one an answer from a proxy.

**H4d (`statistics.null_test`) merged on 2026-08-19 — the last of the H4 family, and the last
`NOT BUILT` block in the `statistics` family.** `E-STATS-NULLTEST-UNSUPPORTED` is retired. A permutation
null runs at `rows`, `within_cluster` and `whole_cluster` level, over a recorded column, a derived metric
and a contrast; a p-value is corrected **alongside** the intervals at the level its member's interval was
computed at and **adds no place in the family**; and **`fdr_bh` is built rather than refused**, ranked on
ascending p-value — sound because under `fdr_bh` the evidence ratio orders nothing, so there is one
method and one ordering. **It unblocks zero configs** — all eight `statistics` blocks in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) carry `null_test: null`, which the
truthy guard treats as undeclared, and none declares `fdr_bh` — so **six with no remaining core-side
blocker and three executable both stay exactly where H4b-1 left them.** Four things worth carrying.
**One code that returned for five distinct faults became five named refusals** plus
`E-STATS-NULLTEST-REPORTBY`: the schema was closed one level in first, on `resample`'s and `holdout`'s
precedent, because a whole-leaf entry is *why* a typo, an out-of-enum `method`, a `shuffle` naming
nothing, a sub-floor `n` and a rosterless declaration were indistinguishable. **`Member` gained a
p-value field rather than a fourth evidence kind** — modifiers change the draw, not the estimator, so a
null does not replicate across the axes the three preceding slices filled six-fold — and
`family_members` widened to admit a member with a p-value and no interval, which made
`_evidence_ratio`'s assert reachable and forced a tiered rank key. **`holm` withholds
`p_value_corrected` from such a member**, because its rank is a sort tie-break rather than evidence:
without that, two entries with bit-identical p-values got corrected values differing only by
declaration order. And **six fixtures across this slice failed their own constraints** — one asserting
`b = 0` where 66 hits were expected, one asserting the very value it existed to reject — every one
caught by computing rather than by reading, which is what *a fixture is a claim too* means in practice.

**H8a (lineage and `io.reuse_from`) merged on 2026-08-20 — the first of H8's three.** `io.reuse_from`
exists: a step reads a named artifact out of a **prior run**, addressed either as `<output_dir>/<run_id>/`
or by absolute path, and every read is accumulated into `provenance.upstream`. `lineage.py` ships the
`run.yaml` reader **nothing in `src/` had**, eleven `E-UPSTREAM-*` refusals, and a containment rule now
enforced on **three** readers — `reuse_from`, `read_upstream` and `read_condition`, the last two having
enforced **no name rule at all**. **It moves exactly one row of the feasibility analysis' table, 6 → 0**,
and mints no new number; the `report_by`-under-`resample` gap still meets **seven** configs and is H4's.
**H8 was scoped at 30 tasks against a one-row charter**, split 10/8/12 — H8b is `diff`/`freeze`, H8c is
`report`/`study`, and **`BaseReport` is H8c's** (§ Package layout makes `report.py` *be* `BaseReport`).

Four things worth carrying. **Two config figures were wrong and both were carried, not derived.** "Six
with no remaining core-side blocker" answered no consistent question — one table cell read *"blocked on
`io.reuse_from` (no remaining core-side blocker either)"* beside another reading *"blocked on
`io.reuse_from`"* and **excluded** from the six — and "three" then fell the same way, since E1 and E2 sat
inside it carrying the `report_by` gap E3/E4/E6 were excluded for. **The analysis now carries a table
rather than a number**, and the shape is the finding: a slice retires one blocker, moves configs out of
the *refused* column, and **carries the summary phrase forward without re-deriving what it counted.**
**A guard's rule may be narrower than the gap it closes**: `read_upstream` would resolve
`../../secret/x.json`, but a `name` is documented as a **relative path** with
`programs/gpt-4.1__seed29.json` as a worked legal example, and a step can `open()` anything regardless —
so the rule is **containment only**, forward separators stay legal, and **a mutation widening it must fail
a positive control.** **A pin that must move can be moved once, by a named task**: arm B of the guard pin
was captured with task 7 named as its sole editor and the post-edit state specified in advance, the
review then found the same list pinned **twice**, and task 7 edited both with one appended key and
nothing reordered — **the answer to five earlier slices weakening a pin quietly.** And **a mutation placed
one line off tests a different property** — a claim that a failed read leaves the ledger untouched
survived its own batch's mutation, which stopped above the existence check rather than above the read.

**H8b (`diff` and `freeze`) merged on 2026-08-21 — the second of H8's three.** `diff` compares two runs,
or a run and a config, hash by hash — five rows over a run-vs-run pair with a declared apparatus (four
when both sides' apparatus is `null`), an `upstream` block when either side consumed one — and exits `0`
on every comparison it renders, `1` only when an operand can't be read. `freeze` re-reads a run's
environment and re-probes its apparatus mid-run without executing anything, appending to the same ledger
`run` writes and reporting a moved fact as a failure rather than deciding one — the gate at the next
execution is what stops the run. **It retires no refusal and unblocks ZERO configs**; the feasibility
analysis's four-row table is repeated unchanged, because neither command runs at `validate` and no config
in it declares an `apparatus_probe` a real plugin backs. `run` gains two artifacts —
`config.yaml` and `environment/repo_root.txt` — so `freeze` can resolve a project-local template's
`apparatus_probe` by path after the fact. **Decision 7 is a behaviour change to a shipped command, and
unlike H7d Part B's it is additive only**: no existing key, verdict, status, or exit code moves: two new
files land in a run directory nothing already iterates.

Three things worth carrying. **A subprocess probe stood in for a pin again** — `diff`'s CLI arm (exactly
two paths, no flags) was demonstrated correct by one prose invocation and by nothing else; replacing its
arity-and-flag guard with a one-line arity check left the full suite green, closed in the batch's own
fix round. **A seam named in the design had code and no fixture**: Decision 2's rule that a condition key
present in one side's `apparatus.facts` and absent from the other gets its own line, rather than being
skipped, was implemented and untested — a bare `continue` in its place passed every test. And **`diff`'s
`apparatus` row and the run-time change gate were ruled two questions, not one contradiction**: the gate
asks whether the apparatus moved *during* this run, so a fact answered for the first time
(`null → value`) passes; `diff` asks whether two runs measured through the same apparatus, so that same
transition is a real difference and prints `DIFFERS` — no behaviour changed, and `reference.md` § The
apparatus core can only observe now says so beside the worked example.

**H7d Part B (the apparatus: gate and stop) merged on 2026-08-20 — the apparatus is complete.** A fact
that moves from its **first *answered*** observation fails the run (`E-APPARATUS-CHANGED`), an
unreachable apparatus stops it, `EXIT_EXTERNAL` gains its first reader with **5 winning over 3 and 4**,
and the ledger keeps the moving observation so a stop is legible from the artifacts. **It unblocks zero
configs** — six with no remaining core-side blocker and three executable stay where H4b-1 left them, and
the only direction this slice could move a count was down. Four things worth carrying. **A neighbouring
guard's semantics were deliberately NOT adopted**: `max_failed_fraction`'s truncation reports `completed`
at exit 0, which `run_status` could have been widened to change — and that behaviour is **pinned with a
written justification in a shipped test's docstring**, so editing the assertion *and* the argument for it
in a slice about the apparatus is indistinguishable from weakening a pin to pass. It is **filed**, with
its owner told to argue against that justification rather than discover it. From which: **a document may
not be made self-consistent by widening a behaviour change** — § What status means **cannot** be made
fully consistent without further code change, and saying so was the deliverable. **`reference.md`
contradicted itself three ways about a truncated plan while the code answered a fourth**, and an
all-completed truncation is described by **no row at all**. And **two defects were interactions between
batches that no per-batch review could see** — a reflexivity guard added for `nan` made a later batch's
prescribed ordering mutation unreachable, and one batch's wiring turned a containment arm added in the
previous batch into dead code carrying a false safety claim.

**H7c (credentials and secrets) merged on 2026-08-16**, out of charter order and for a measured reason: the
feasibility analysis's own plugin declares `Param(requires_env=)`, and `Param` rejected that keyword, so the
plugin H7b's registry would resolve **could not be written**. The spine design calls H7c order-independent;
that is the claim [its scoping](docs/superpowers/H7c-SCOPING.md) falsified. It retires no refusal and newly
executes nothing — there was no refusal in that family to retire — and it closes the defect § Misreadings
named by hand, `BaseTemplate.required_env` being declarable and unread.

A second amendment the same day scoped all five remaining slices against the code. **Every charter was
stale in the same direction**: H4 is ~54 tasks split four ways, H7's remainder 38 split three ways, H3d
16 against a charter saying "3 rows", H3c-3 17 against a charter saying 6. Two consequences worth
carrying: `statistics.resample` for the unclustered case is **wiring, not construction** (two percentile
constructions are built with zero production callers), and **H3c-3 contains a 3-task refusal that closes
a live defect** — `groups` + `between` + `fold` validates clean today and produces empty folds per arm,
because `fold_basis` answers over the whole roster. That refusal ships with H3d; the other 14 tasks wait
for a design that needs folds inside cells.

The cost is that H3d now precedes the cells work it was scheduled to consume, so **H3c-3 owns
retrofitting the holdout to cells and retiring `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS`, both
already named on H3d's branch, once drawing within a cell is built** — acceptable only because no
experiment in that analysis declares a group axis. The reasoning lives in the spine design's *Order,
amended against outside evidence*, which is now tracked — cite it rather than restating it.

**H7d Part A (the apparatus: observe and record) merged on 2026-08-19.** A template declaring an
`apparatus_probe` no longer writes a false `apparatus: null` — core resolves the declared probe
through the same three-step dispatch a resolver already uses, calls it at run start and before
every execution, projects its facts onto a declared `apparatus_facts` set, refuses a fact that is a
credential core read or a value core cannot encode, records every observation in an append-only
ledger, and assembles `provenance.apparatus`'s five sub-keys from what it observed. **It retires no
refusal and unblocks ZERO configs; six with no remaining core-side blocker and three executable both
stay exactly where H4b-1 left them** — the nine configs in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) declare no `apparatus_probe` at
all, since `generic` is the template they validate against. Five error codes are minted
(`E-APPARATUS-RAISED`, `-RETURN`, `-FACT-TYPE`, `-FACT-MISSING`, `-FACT-CREDENTIAL`) plus one
warning (`W-APPARATUS-UNANSWERED`), and this closes the filing named above —
*"`cli.py` writes `apparatus: null` unconditionally regardless of what a template declares"* — which
is now stale and struck in `docs/superpowers/spec-defects.md` rather than left to mislead. A
whole-branch review held the merge on two Majors, both closed the same day: a fact value
*containing* a declared credential (not merely equal to one) was published verbatim in
`provenance.apparatus.facts` and the ledger, because the credential check matched by exact equality
while `secrets.redact`, over the identical value set, matches by substring — fixed by matching the
way `redact` already matches; and a non-`str` `apparatus_probe` (`["a_probe"]` being the plausible
mistake, since `apparatus_facts` sits on the very next line and *is* a list) silently read as "no
probe declared" at both `validate` and `run`, reproducing the just-closed filing's defect through a
different route — fixed at the one place both surfaces share, `validate._check_probe`, which is
also what closes `run`'s copy of the same guard without touching it, since `command_run` validates
first.

## The documents

| File | Role |
|---|---|
| `README.md` | The pitch and the whole arc, for someone deciding whether to use it |
| `docs/design-principles.md` | **Normative.** Why each rule is what it is |
| `docs/experimental-designs.md` | How each experimental design is expressed; what core prevents and refuses |
| `docs/reference.md` | Config schema, CLI, `io` API, templates, sweeps, artifact layout |
| `docs/feasibility-*.md` — currently [`llm-growth-studies`](docs/feasibility-llm-growth-studies.md) | **Non-normative.** One feasibility analysis each; carries its own examples — see § Feasibility analyses |

The first four are *the four documents* everywhere below: the invariants, the consistency passes, and the worked example govern those and only those. A `feasibility-*.md` is analysis output, not specification, and nothing in it is authoritative over them.

`design-principles.md` is the tiebreaker. Read it before proposing a change to any rule — if a rule looks arbitrary, that file explains it, and if it doesn't, that gap is itself worth fixing.

## The development record

The four documents say what `publishable` **is**. These say how it got there, and they are **tracked** — read them before re-deriving anything.

| Where | What it is | Read it when |
|---|---|---|
| `docs/superpowers/specs/<date>-<slice>-design.md` | A slice's design: its decisions, each with grounds, and what it refuses | Before planning or changing that slice |
| `docs/superpowers/plans/<date>-<slice>.md` | The same slice as numbered tasks, with code and per-task mutations | While executing it |
| `docs/superpowers/*-SCOPING.md` | What was **measured against the code**, dated and pinned to a commit | Before trusting any charter |
| `docs/superpowers/spec-defects.md` | Gaps found and deliberately not closed, with the owner | Before filing a "new" gap |
| `.superpowers/sdd/<plan>/progress.md` | The ledger: every ruling, its reason, and what it costs if wrong | To learn why something is the way it is |
| `.superpowers/sdd/<plan>/task-N-report.md`, `task-N-review.md` | What was built, what the brief got wrong, what each finding was verified by | Before repeating a task's work |

**A scoping expires; a spec does not.** Every charter re-scoped so far was stale **in the same direction** — under-counted and missing surface — so a scoping is dated and pinned to a commit, and a claim carried from one without re-checking is worse than one omitted. Re-measure rather than trust.

**The plan argues from the spec, and the code outranks both.** Where they disagree, the code wins and the *document changes first* — six of six implementers on the most recent slice found a real disagreement, so finding one is expected, not exceptional.

Two things stay untracked because git already holds them: task briefs (extracted from the plan by `scripts/task-brief`) and every `.diff` (regenerable from the two commits in its filename).

**`scripts/sdd-workspace` rewrites `.superpowers/sdd/.gitignore` to a bare `*` every time it runs, and `task-brief` calls it.** Already-tracked files stay tracked, so the damage is only to records created after a clobber. Restore that file's content when you notice, and use `git add -f` when committing new records.

## Invariants a change must not quietly break

These are load-bearing across all four documents; contradicting one in a single section creates a real inconsistency, not a wording nit.

- **Operation commands take paths and nothing else.** No parameter flags, no selectors, no behavior-changing env vars. Modes get their own command names (`dry-run`, `draft`, `resume`) rather than `--dry-run`/`--allow-dirty`. Only creation commands (`new`, `plugin new`, `generate`/`init`, `study new|add`) take arguments beyond a path. (`design-principles.md` § Everything is in the file)
- **Three hashes, split on purpose.** `code_hash` covers `src/**` and `templates/**` only — the code your repo supplies, a plugin's being pinned by `uv.lock` instead — separate from `parameters_hash` and `input_manifest_hash`. That split is what makes "same code, different parameters" provable across unrelated commits — unrelated meaning outside the two hashed trees, since another experiment's package is inside them.
- **`input_dir`/`output_dir` may never resolve inside the git repo**, checked at generate, at validate, and by every command that executes (`run`, `draft`, `resume`). Which repo is decided by a walk-up from the path the command was given, not from the working directory.
- **Condition vs. repeat.** A condition is a difference being measured; a repeat is a difference being averaged over. Statistics aggregate *within* a condition and compare *across* conditions — never the reverse.
- **A repeat is an execution, so the kinds are exactly the three things a re-execution can change: `seed` (RNG state), `fold` (which units it sees), `batch` (the state of the apparatus it measures through — see § The apparatus core can only observe).** A `batch` takes no field but `n`, executes in order with `order: randomized` shuffling inside it, and `validate` warns when no step sets `nondeterministic = True`. Resampling and permutation are `statistics.resample`/`statistics.null_test` over the unit table (thousands of executions otherwise, and an all-permuted design has no unpermuted value to test); technical replication is `data.units.measurements`, collapsed at unit resolution (re-running an identical step recomputes the same answer); a fixed holdout is `data.units.holdout`. `validate` rejects `bootstrap`, `permutation`, `technical`, `biological`, and `holdout` as kinds by name.
- **Units are the inference base; repeats never are.** Every interval core reports is computed from the per-unit table, `n` counts units (`resolved`/`completed`/`ineligible`/`failed`, where `io.skip` declares the third and `max_failed_fraction` guards only the fourth), and repeat dispersion is reported separately as `repeat_spread`. A metric that exists only as a step-returned scalar is `basis: repeats` and gets **no** `ci95`; the one interval core stores without computing is an `Estimate` returned by a `summary` step, marked `reported: true`, outside the correction family and never recomputed. A hypothesis may name one — it takes no `compare` — and the verdict records `verdict_rests_on: reported` rather than `computed`. Pairing is over units, never over repeats, and a contrast — `vs_baseline` or a declared `statistics.contrasts` entry — is computed over the intersection of both sides' completed units, recorded as `n_paired` — and its interval is its own construction over that intersection (`paired_t_over_units`, `paired_percentile_over_units` drawing once for both sides, or the `welch_`/`unpaired_` counterparts), never a difference of the two sides' intervals. Holm ranks on the point estimate over half the raw `ci95` width, because the family often carries no p-value at all, which is also why `fdr_bh` over such a family warns. `data.units.weight_by` weights an enriched sample's estimates and records `weighted_by`; `statistics.report_by` repeats metrics over strata without adding executions or joining the correction family; a subgroup you want to *test* is a contrast with `within`, which does join it. Contrasts compare conditions and do not nest: anything comparing two contrasts — a dose-response ordering, a difference-in-differences, a nested mean over cells — is an interaction and stays a `summary`-step `Estimate`. The table `aggregate` receives supports exactly four operations — row iteration, column access, `len`, `columns` — deliberately not a `DataFrame`, so core can change what backs it without breaking every plugin. (`reference.md` § The unit table is the inference base, § Templates)
- **One import root, one registration, one return shape.** Everything a user writes against is imported from `publishable` itself — `publishable.templates` and every other submodule are implementation detail, and `reference.md` § The importable surface is the enumerated list. The entry-point key *is* a plugin artifact's registered name and the `@register_*` argument is checked against it (so `validate` resolves a name without importing the package); a collision or a shadow of a core name fails at load rather than being resolved by install order. `io.write` dispatches on the longest registered suffix of the name's last component, and each core writer takes exactly what its reader gives back — rows as mappings for `.csv`/`.parquet`/`.jsonl`, any parsed structure for `.json`/`.yaml`, `bytes` or `str` for everything else, never a `DataFrame` or an object core would have to guess at. A step's `run` and a template's `aggregate` both return a flat mapping of scalars — the same set `io.record` takes — with a NumPy scalar coerced, anything structural a `ContractError`, and an `Estimate` at `summary` scope the one exception. Core raises `PublishableError` → `ContractError` / `ArtifactError` → `ArtifactExistsError`, each carrying the same stable `E-` identifier a diagnostic prints. (`reference.md` § The importable surface, § Steps and artifacts, § Creating a plugin)
- **What core hands a step is minimal and immutable on purpose.** `io.units` supports three operations — iterate, `len`, index — plus `.train`, on the same argument `aggregate`'s four-operation table rests on; a `Unit` is frozen and hashable by `key`, because one roster is resolved per run and shared across every condition. `cfg` is dot-access with no methods at all (so no parameter name can be shadowed) — the one exception being the root node's single `raw` accessor, which `validate` and a template's `validate(config)` need and which costs the one top-level name core already owns — raising `ContractError` on a path the config doesn't hold and `AttributeError` on an underscore-prefixed name. `self.rng` is the generator to draw from — core also seeds the `random` and legacy `numpy.random` globals, but only so an unreachable library is covered, and a concurrent step must give each worker its own stream. `scope` is read from the class before any instance exists, and `__init__` is core's. (`reference.md` § The importable surface, § The unit list is three operations, § Randomness)
- **`parameter_spec` is the single source of truth** for what `init` writes, what its inline comments say, and what `validate` enforces. There is deliberately no separate defaults file. `Param` types are `str`/`int`/`float`/`bool`/`list` (with `item_type`); omitting `default` is what makes a parameter required, and `default=None` requires `nullable=True`. `requires_env` is the one thing a `Param` carries that isn't a constraint on its value — it needs `choices` and must be total over them, and it stays out of the closed constraint vocabulary for that reason.
- **Core vs. plugin test:** would it be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark? If not, it's a plugin. Core ships exactly one template, `generic`. A template *reads* the whole config in `validate` (cross-block rules are properties of what its steps do) but declares nothing outside `parameters`.
- **Greenfield only** — no `adopt` command, ever. Core validates *declarations* and verifies *effects*; it never inspects the body of user Python.
- **`uv` and git are mandatory**, not optional paths.

The stated non-promises — adaptive/sequential designs, per-condition pipeline variation, factorial main effects and interactions, bit-identical reruns, scientific validity — are deliberate refusals with reasons attached, not gaps waiting to be filled. Treat a request to add one as a design change requiring an argument against `design-principles.md`, not a feature request.

## Misreadings this repo has made more than once

Every one of these was made by someone competent, reading carefully, more than once. They are not
carelessness — each is a reasonable reading that happens to be wrong here, so knowing the rule is what
prevents it. The slice ledgers hold the instances; this section is the short form worth carrying into
every session.

### Reading the documents

| Misreading | The rule |
|---|---|
| Taking a § Validation row's own wording as its whole scope | Several rows read as method-independent while the **surrounding prose carries the gating** — *Ratio names levels* and *Allocation strata exist* apply only under `random`/`blocked`. Read the section, not the cell |
| Treating a row's example as its definition | An example can be a fault under *every* candidate reading, so the row looks settled and is not. *Attribute assignment resolves* showed a disjoint value set, which fails whether the rule is set equality or subset tolerance — the ambiguity survived until someone needed the answer |
| Citing a sentence whose job is to **contrast** as if it supported the claim | "An arm no unit resolves to is already refused" exists to distinguish that case from `min_units_per_cell`'s thin-but-nonzero gap. It was read as licence to route a hard refusal into a warning-shaped gap |
| Assuming a documented rule has code behind it | Five § Validation rows described checks with no emit site, no check and no test. **Grep for the code before building on the row**; a row and a code are the same check seen from two ends, and either end can be missing |
| Reading a temporary refusal as permanent, or the reverse | A `-UNSUPPORTED` suffix is the undocumented build family, retired wholesale and absent from the registry. A *narrow* refusal of a combination is documented, carries rows, and outlives the slice that minted it |
| Scoping a diagnostic by the helper it calls | `E-TEMPLATE-UNKNOWN` had **two** emit sites; a task scoped by `template_names()`'s single call site missed the second, which went on claiming "no installed template registers" under a § Errors row just rewritten to say otherwise. **§ Errors carries one row per code, not per emit site**, so a diagnostic's unit of work is every site that raises *or* reports it |
| Reading a subprocess probe as a pin | A probe proves the moment; a test proves tomorrow. H7b Part B's credential-leak fix was verified through the real console script for every shape at both commands — and the reviewer's combined mutation then left the suite **unchanged**, because the fix commit added one test. **Five times in three slices a correct fix shipped unpinned.** Verify by probe, then pin by mutation |
| Reading a mutation's **silence** as confirmation | A mutation that changes nothing is evidence about the **tests**, not about the code. Twice in one slice a task emptied a payload, watched the suite stay green, and concluded the payload was unreachable — while a discriminating test was available both times and a reviewer built it. "No mutation reaches this" and "no mutation *can* reach this" are different claims, and only the second justifies leaving a thing unpinned |
| Reporting **zero disagreements** with the code | **Six consecutive slices' reports claimed it and all six were wrong** — and every one hid in a claim about **other tests or other rows**, never in the implementer's own reasoning about its own code: a docstring asserting *"no existing test asserts this"* when one did, a § Errors row asserted that did not exist, a fixture named that was absent, a brief's *"no fixture can reach it"* that a bare call falsified. **Brief-supplied prose is where zero hides**, because it reads as established rather than as a claim. The check is mechanical and catches all six: **before writing "no existing test asserts X", or repeating any claim a brief makes about the code, grep for it.** Report what you grepped, not a count |
| Inferring "this path does not run" from "this config is refused" | **`validate` collects rather than aborting**, so a refusal elsewhere never makes a later check unreachable. Two independent readers — a plan author and an implementer — both recorded a mutation as blind on that reasoning, and a reviewer disproved it by building the fixture. Ask what `validate` *reports*, in full, rather than whether it refuses |
| Reading an unbuilt reader as a defect | An unbuilt reader of an **unbuilt** surface is specification — present tense is correct, and § Package layout's `— not yet built` carries it. An unbuilt reader of a **shipped** surface is a defect: `BaseTemplate.field_convention` is declarable today on a class that ships, and nothing reads it. (`required_env` was this row's example until H7c gave it a reader at `validate`; `apparatus_probe` was the next until H7b Part A's `_check_probe` gave it a metadata-name reader — not an executed probe; `apparatus_facts` was the next until H7d Part A's `check_facts` gave it a reader. `field_convention` is now the sole remaining example, owned by nobody) |

### Writing checks that can fail

**Sixteen checks across the two H3c slices could not fail**, and roughly a dozen more in H7a — every one
caught by a mutation and none by reading. Run the mutation before believing the test, **and run it where
the behaviour lives** — not where the test happens to look. The shapes, each seen more than once:

| Shape | Why it passes anyway |
|---|---|
| A fixture whose numbers agree with the bug | An "undeclared level" ratio that was *also* partial; a 13-unit apportionment that matched a reverse-order mutant by coincidence; a cluster fixture where correct and buggy cluster counts were both 3 |
| A dimension no assertion can see | Per-stratum arm counts are **forced** by apportionment, so no count assertion can detect an RNG change. Deleting the shuffle, and replacing the seeded generator with `Random(0)`, both left the suite green — the second while `ArmPlan.seed` still *recorded* the ignored seed |
| An assertion implied by another in the same test | Arm sizes summing to the roster is arithmetic, not a check, once the sizes are pinned |
| A control asserting only absences | Passes identically if nothing ran. Pair it with something that must report |
| A parametrized test asserting a **failure** for both arms | Proves nothing about either arm's **success** path — `blocked`'s stratified draw was fully threaded and never exercised |
| Testing the refusal, never the honouring | `validate` refused bad `block_size` values while nothing checked the draw *used* a good one, so ignoring it entirely passed the suite |
| A mutation applied to a proxy | The extracted helper's body rather than the call site; the fixture rather than the wiring |
| Varying config **shape** when the property is about roster **content** | Nineteen adversary configs over one roster made every refusal roster-incidental. **A refusal that happens to fire must be attributed before it is counted** |
| A test whose **name** claims the guarantee | `test_..._message_matches_validates` compared each of two messages against **its own** hard-coded literal, so mutating one site failed one test and nothing compared the two. The name and docstring asserted an agreement no assertion made — and a reader greps for exactly that name and stops looking |
| A test that **iterates the thing under test** | A vocabulary test looped over `sorted(PHASES)` — the very frozenset under test — so removing a member changed the expectation and the actual together: all four removals failed on `assert 3 == 4` rather than through the guard, and the test's second assertion went **vacuous** under every mutation. **Enumerate the literals the set should contain**, or the test measures only that the set equals itself |
| A fixture with too few elements to distinguish the candidate orderings | Both documented orderings survived reversal with the suite green: one colliding name and one broken file cannot tell name order from import order. **Two elements only ever distinguish two answers** — with two names the reverse of insertion order *is* sorted order for one arrangement. Count the orderings you must rule out, then size the fixture so each yields a different answer |
| A monkeypatch left aimed at a name the code no longer calls | Rerouting a call site through a new helper silently defused a patch on the old name; the test kept passing while testing nothing. **When you move a call site, grep the suite for patches aimed at what you moved** |
| A seam named in the brief and instantiated by no fixture | Twice in one slice a distinction was described precisely — `declared` versus `n`, strata threaded into the clustered call — and **the mutation passed all 1700+ tests**, because no config made the two readings differ. Naming a seam is not testing it: ask what config separates the readings, then check it exists |
| The test's **reader** normalising the defect away | A resolved-values echo shipped as a YAML alias — one anchor, five `*id001` pointers — and **both tests used `yaml.safe_load`, which resolves aliases**. The defect lived in the serialization and the reader undid it before the assertion. When a defect could live in *how* a value is written, assert on the raw text |
| A **mutation** whose two branches cannot differ | A reviewer proposed proving a distinction by swapping to a value derived from the same source — a mathematical no-op no fixture could ever catch; a controller's proposed mutation was blind for a different reason. **A mutation is a claim too**: before trusting "this would prove X", check the two branches can actually produce different results |

### Answering a question with a proxy

Both fail-opens in H7a's "is this template local?" predicate came from the same move: answering with
something *correlated* rather than with the fact. First the class's module-name prefix — a scheme built
for **anti-aliasing** (two repos both holding `templates/my_assay.py`) and applied only to non-`__`
files, so a class defined in a sibling helper read as foreign and got core's `template_version` written
against it. Then a marker stamped on the class — right about where the class was *defined*, wrong about
who *owns* it, so registering a class the repo merely imported stamped a **shared** object process-wide
and permanently. **When a predicate keeps failing open, the proxy is the bug, not the guard.** Both were
closed by asking the direct question — does this class's defining file sit under *this* repo's
`templates/` — with a helper that already existed.

A corollary that cost its own round: **state read at the wrong moment is a third proxy.** The first fix
was placed where `sys.modules` had already been restored, which inverts the answer — a genuinely local
class's module is gone, while an external one is still cached.

**A grep for one spelling is a fourth**, and it shipped a credential leak. H7c's redaction was sited by
measuring every place an exception reaches a stream with `grep 'type(exc).__name__'` — which answers
*where does this spelling appear*, not *where does this happen*. A site formatting a bare `{exc}` matched
nothing, and a declared credential reached stderr through it. Enumerate by **reading** where a thing can
happen, then confirm with greps; the reverse order is the substitution this section is about, and it was
made by the author of the rule forbidding it, while measuring for it.

### Habits that cost real work

- **A comment or docstring claiming a guarantee the code does not provide** — at least a dozen instances,
  including one that explicitly promised "any other `method` string takes the `by_attribute` path" (the
  fail-open defect written down as if intended), and three overreaching claims inside a single commit
  that was itself fixing overreaching claims. When you change a guard, re-read its justification. A
  sentence can also contradict **the argument that justifies the thing it describes**: "a collision among
  the files that *did* load is still found rather than masked" appeared at four sites including a
  normative § Errors row, while the reason load-failure is checked first is precisely that a collision
  verdict computed then would be computed over a partial set of claims. Both properties cannot hold.
- **A fix that carries its own justification is not thereby verified**, and the justification is written
  from the intent while the behaviour has already moved. Closing H7c's "core honours an undocumented
  environment variable" gap by swapping `load_dotenv(override=False)` for `dotenv_values` **broke "a
  shell value wins"** — that helper hardcodes `override=True`, which is the flag deciding whether a
  `${VAR}` reference resolves from the shell or the file. The new docstring claimed "`setdefault` is
  exactly `override=False`" and justified it with *"a stale `.env` cannot silently redirect a run to the
  wrong account"* — the precise property the change had just broken. Probe the property the sentence
  names, not the intent behind it.
- **Prefer deleting a claim to rewriting it.** A round closing a false-owner comment closed it by
  **propagating the claim to two more sites**, one of which contradicted a third comment in the same
  commit. A rewrite invents; a deletion cannot.
- **A safety argument in a comment is a claim, and needs a mutation like any other.** A retry inside an `except` was widened, and its new comment argued the retry could never raise because the faults it handles "surface on the first call". **The first call was inside the `try`.** Patching the widened function to raise gave exit 1 with no `run.yaml` and no run directory — every execution paid for, the record lost. Written by someone whose task was closing findings about false comments, and it passed a review. If a comment says *this cannot happen*, make it happen.
- **Sweep for the claim, not for the file the claim was first noticed in.** Three sweeps in one slice stopped one file short — one covered `src/` and `docs/` but not `tests/`, one fixed a sentence in `correction.py` and missed the same sentence in the function that falsified it, one stopped at the file its brief happened to name.
- **Carrying a finding into a brief is necessary and not sufficient.** On one slice a finding routed
  to a task **fell out of the chain** between the review that raised it and the brief written from it.
  On the next it was **in the brief, measured, named** — and still not built, while the report claimed
  guards that existed at no commit. The second is worse than the first: **a report's claim that a
  carried finding is closed has to be checked against the code like any other claim**, because the
  carry itself creates the expectation that it was done.
- **A ledger line saying "filed" is not a filing.** A gap recorded as "registered against \<owner\>" existed only in the ledger; the defects file had no such entry. And an entry naming its owner as *"whichever slice does X"* points at a closed slice once X lands — **re-owner a deferral when the slice that filed it finishes**, or it reads as live work nobody holds. A filing's claims about the code go stale like any other comment; when you change code a `spec-defects.md` entry describes, re-read the entry.
- **Rewriting a sentence when a table row was the thing that was wrong.** "Importing one raises
  `ImportError` today" was false only while `register_template` sat in a row marked `not yet built` —
  splitting the row repaired it, because the sentence **derives** its claim from the `Status` column.
  Replacing it with an enumeration of names would have converted a self-maintaining statement into a
  maintenance obligation nobody owns, and a second source of truth for build state.
- **Locating a table row by position** ("the two rows above", "further up") — at least seven instances,
  wrong twice, once in a row no diff touched, falsified by an insertion that moved it. Name what a
  sibling row *does*. When you insert or remove a row, check every row it **moved**, and every count
  phrase near it.

### Two mechanical traps

- **Never filter the output of a sweep whose job is to find a string** — filter the file list. A reviewer
  checking this exact rule lost a true hit to `grep -v superpowers`, because the matching line contained
  that path. Prove each sweep can fail by running it against a string known to be present. This matters
  more now that the [development record](#the-development-record) is tracked: a sweep over the four
  documents must **name** them, since `*.md` no longer means what it used to.
- **`git checkout -- <file>` destroys uncommitted work**, twice mistaken for reverting a mutation. Keep a
  copy before mutating, and verify a revert by **behaviour**, never by `git status`.
- **`ruff format` does not touch `*.md`** — it processes `.py`, `.pyi` and `.ipynb`, and this repo adds no
  `extend-include`. **Two agents on two slices have blamed it for rewriting a document's fenced Python
  block**, and both then reverted files on that reading; measured both times by copying the file, running
  `uv run ruff format .`, and diffing — **byte-identical**. Neither lost work, which is the point: the
  revert was performed on a diagnosis that was never checked. Whatever moved those bytes, it was
  something else, so **find it rather than restoring on a story.** The general rule this sharpens: a
  revert is verified by **behaviour**, never by `git status`, and least of all by an account of what
  caused the change.

## Checking consistency after any `*.md` edit

Editing one document is almost never a one-file change. Both passes below run before an edit is finished; the second is the one that catches real defects, and no tooling substitutes for it. The **cross-document** pass governs the four documents only — a [feasibility analysis](#feasibility-analyses) is exempt from it and subject to the mechanical pass in full.

**Mechanical.** Write these as throwaway greps or a short script each time rather than keeping a checker around — the repo ships no tooling, and each pass wants slightly different checks. Verify that every relative link and `#anchor` resolves, that no two headings in a file produce the same anchor, that every table's rows match its header's column count and no row is empty, and that no line carries trailing whitespace, a tab, or invisible unicode. Skip fenced code blocks in all of these: the docs contain markdown inside markdown, and a `##` or `|` there is content, not structure. After removing or renaming any string, grep the four documents, this file, and any feasibility analysis for what should no longer exist.

**Both passes govern those files only — never the [development record](#the-development-record).** A spec records what was decided when it was written and a scoping what was measured on its date; retro-editing either destroys the evidence they exist to hold. Correct one the way this repo corrects a published claim: append the correction and say what it replaces. The one exception is `spec-defects.md`, a live list, where a closed gap is struck rather than left to mislead.

**Cross-document.** These are the classes that actually drift, and none of them is visible to a mechanical check:

| Class | The rule |
|---|---|
| **The shared worked example** | README, `design-principles.md`, and `reference.md` describe *one* experiment. Changing a value in one means changing it everywhere it appears — see § The worked example below |
| **Config completeness** | Every config field documented anywhere in `reference.md` must appear in § The one config file, whose fenced example calls itself "the config schema for template `generic` ... at full expansion: every parameter `publishable init` materializes, plus the optional blocks it leaves empty or undeclared." Adding one can invalidate downstream `run.yaml` examples that were correct under the previous default |
| **Enum comments** | An inline `# a \| b \| c` comment must list every value its corresponding table or section defines |
| **Schema fields in prose** | A field named in prose must exist in the `config.yaml` or `run.yaml` example, and vice versa |
| **Declared vs. derived** | If one passage says a value is derived, no other may show it as a settable input. This is how `replication.design` contradicted four passages at once |
| **Versions** | Version numbers in examples must agree with `CITATION.cff` and the README's v0.x notice |
| **Prevented mistakes** | Anything in `experimental-designs.md` § Mistakes core prevents must be structurally impossible in the schema, not merely discouraged |

### The worked example

One experiment runs through README, `design-principles.md`, and `reference.md`: config `cohort-pilot`, package `cohort_pilot`, template `generic`. (`experimental-designs.md` deliberately uses varied domain examples instead — `stimulus.contrast`, `drug.dose`, `samples.csv`, `cell_id` — because its job is to show many designs, not one pipeline.) The steps and scopes are `step01_load_cohort` (run) → `step02_fit_model` (condition) → `step03_analyze` (repeat) → `step04_compare_methods` (summary). It sweeps `analysis.method` over pearson/spearman/kendall — 3 conditions × 5 seed repeats — against 240 units, of which 228 complete and 12 fail. Results are r = 0.581 baseline (ci95 [0.488, 0.661]), 0.607 spearman ([0.517, 0.683]), 0.412 kendall ([0.347, 0.477]); delta 0.026 with a paired ci95 of [−0.007, 0.059] (kendall's is −0.169, [−0.213, −0.125]), and a seed `repeat_spread` std of 0.014. **Those intervals were checked numerically against a synthetic 228-unit table and must not be narrowed back.** The two r intervals agree with both Fisher-z and a percentile bootstrap; kendall's is a percentile bootstrap of τ, because Fisher-z on τ is the wrong transform and is what the earlier [0.298, 0.514] came from — no 228-unit dataset gives τ = 0.412 a half-width above 0.087. The deltas come from a joint resample over the paired intersection, whose half-width does not go below ≈0.033 for a linear-versus-rank contrast at this n, so the earlier ±0.009 was unreachable. A consequence to preserve rather than tidy away: the spearman delta's interval spans zero while `h1` is supported on `observed`, and `reference.md` § Pre-registration turns that into the point of `verdict_evaluated_on`. `cohens_d` is `null` throughout: `r` is derived by `aggregate(units)`, and Cohen's d needs a per-unit value to difference — don't reintroduce an effect size for it. The per-condition intervals are deliberately much wider than the delta's — that contrast *is* what `allocation: within` buys, and flattening it would reintroduce the defect this scheme fixed. Hash prefixes are `8e21` (code), `1a2b` (parameters), `3d8a` (input manifest), `6b1f` (uv.lock), and the run IDs are `run_2026-08-06T14-02-11Z_8e21ab3` and `run_2026-08-07T09-14-03Z_8e21ab3`. README uses `~/data` and `~/results` paths where `reference.md` uses `/secure/...`, and README's `demo` walkthrough reuses the same statistics under a separate `correlation_pilot` experiment, and carries its own code hash prefix `2f5c8d0` — a different `src/` cannot share one, since `code_hash` covers the tree. Those differences are deliberate, the rest is not.

## Feasibility analyses

A **feasibility analysis** asks whether a real research project could be run on `publishable` as specified: which of its experiments the schema expresses, what each config actually looks like, what executing it costs, and — the load-bearing half — which parts core refuses and where each refusal routes. It is the main way this repo gets evidence from outside itself, because the spec is otherwise validated only against its own worked example.

One analysis per file, at `docs/feasibility-<subject>.md`, kebab-case matching its title. Link it from § The documents above.

**These files are exempt from the cross-document passes**, and that exemption is deliberate rather than laziness: an analysis carries the subject project's own cohorts, statistics, and hash prefixes, and reconciling them with `cohort-pilot` would destroy the thing being analyzed. The **mechanical** pass still applies in full — links, anchors, tables, whitespace, `×` for multiplication, hyphens in anchors.

### The procedure

1. **Read the source project for its goal, not its implementation.** State in one sentence what each source repository is trying to learn. Do not replicate its file layout, CLI, or artifact names — those are the parts `publishable` is meant to replace.
2. **Name what the source hand-rolled that core already owns**, as a table. Manifests, run ledgers, timestamped directories, split records, usage reports, and reproduce commands are the recurring ones. This is both the strongest adoption argument and the list of things a proposed plugin must not rebuild.
3. **Express each experiment in the spec's vocabulary**, in this order: the problem in two sentences, the design decision (which axis, which repeat kind, which allocation, where the units come from), then the actual YAML.
4. **Every YAML must be checkable against `reference.md` § The one config file**, whose fenced example is the config schema for template `generic` at full expansion — every parameter `publishable init` materializes, plus the optional blocks it leaves empty or undeclared. Any field you show must exist there or in the proposed template's `parameter_spec`; a template declares nothing outside `parameters`, so there is no top-level block of a plugin's own.
5. **Do the arithmetic before writing the YAML, not after.** Every config states its condition count, its repeat structure, its execution count against `limits.max_executions`, its unit-executions (which is what a metered run is billed by, and what `dry-run` prints), and its cost and runtime from anchors the source itself observed. A feasibility section without execution counts is decorative — and a repeat structure chosen without them is how a translated design silently costs several times the original.
6. **Name every refusal with its route.** Interactions, dose-response orderings, differences-in-differences, adaptive selection, model fitting, counterbalancing, roster-changing variants. `experimental-designs.md` § What core will not do for you is the list to check against; the route is usually a `summary`-step `Estimate`, a separate run joined in a `study`, or a `report_by` stratum.
7. **Separate what is not an experiment at all.** Reference-standard adjudication, governance firewalls, and human decisions made between runs are not pipelines core executes. Say so explicitly — treating them as runs is the failure mode this step exists to catch.
8. **Propose the plugin last, from what the designs actually needed.** Apply the core-vs-plugin test to every piece, keep the registered artifacts to the five registries, and say which of them the domain does *not* need. Watch the correction family: every metric a template's `aggregate` returns is comparisons × metrics, so a template returning twenty diagnostics corrects every interval in the run for numbers nobody reads.
9. **Record the gaps the analysis found in the spec**, separately from the analysis itself. These are the deliverable's second output — a real project pressing on the schema is where an under-specified rule shows up.
10. **Never state a build fact undated.** A claim about what the tool *does today* — that a config validates, that a command dispatches, that a slice has landed — is perishable in a way a spec claim is not, so it must be dated and pinned to a commit where it is made, and kept in a section of its own so a reader can see at a glance what has an expiry date. `feasibility-llm-growth-studies.md` § Executability on this build is the shape: one section, "Measured on \<date\> against commit \<sha\>", and every refusal named by its code. Anything you are not willing to date belongs in the present tense of the specification instead — write it as what `publishable` specifies, not as what it does. This is the same distinction `reference.md` § CLI reference marks with its `Status` column, and it exists because an undated build claim reads as a spec claim a month later, which is how an unbuilt command was once asserted as fact.

### Traps this repo has already hit

| Trap | The rule |
|---|---|
| A roster-changing variant written as a sweep axis | `data.units` is one roster per run. A different sampling ratio, cohort cap, or eligibility population is a different run, joined in a `study` — not a condition |
| An eligibility change written as a roster change | When the superset roster is shared, a condition that admits fewer units uses `io.skip`, landing in `ineligible`. Eligibility must be constant across a condition's repeats, or the unit is counted `failed` |
| A path or a slashed identifier as a swept value | A swept value must render as `[A-Za-z0-9._+-]+`. Sweep an alias or an ID and resolve it inside the step |
| A metric averaged, ordered, or combined across two contrasts | Contrasts do not nest. It is an interaction, and it is a `summary`-step `Estimate` |
| A mean *absolute* difference read as a contrast | A contrast is the mean of the differences. Two one-sided bounds, or an `Estimate` |
| A model fitted where the split does not exist | `optimizer`-style configs need a `holdout` or a `fold`; this is exactly the cross-block rule a template's `validate` is for |
| Per-request measurements written to a side report | Tokens, latency, and attempts are per-unit measurements. Through `io.record` they become `basis: units` with intervals; in a usage report they have no denominator |
| A repeat structure copied from the source without costing it | Repeats multiply metered work. Put expensive fitting at `condition` scope, and say in `replication.rationale` what the repeat count bought |

## Documentation conventions

- Filenames are kebab-case, matching the doc's title.
- **Hyphen, never an en dash, in anything that becomes a filename or an anchor.** Headings use `dose-response` and `case-control`, not `dose–response` — GitHub's slugger strips an en dash entirely, so `Dose–response` silently becomes `#doseresponse`, an anchor nobody would guess when hand-writing a cross-reference. This overrides the Unicode preference below, which applies to prose and diagrams only.
- Cross-references between the four documents are dense and anchor-based. Renaming a heading breaks links elsewhere — grep the other files for the old anchor.
- Cite another file by section — `reference.md` § "Package layout" — never by line number. Line numbers go stale on the next edit above them.
- `×`, not `x`, for multiplication, including inside fenced blocks. Unicode is already the house style there (`├──`, `←`, `·`).
- README writes bare `publishable <cmd>`; `reference.md` writes `uv run publishable <cmd>` for commands run inside a project and bare for `new`, `demo`, and `study`. Both are correct — README installs globally at its Try it step. Describing this so it isn't "fixed" in either direction.
- `<!-- publishable:begin ... -->` / `publishable:end` regions in the docs are examples of *machine-managed* README regions in generated projects, rewritten by `publishable docs`. Text outside them is hand-written.
- Prose style is declarative and reason-giving: state the rule, then why it exists. Tables carry the dense material.
