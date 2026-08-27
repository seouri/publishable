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

**NOTHING REMAINS ON THE CHARTER. Every hardening slice — H1 through H9, and every sub-slice of H3, H4,
H5, H6, H7, H8 and H9 — has merged**, the last of them (H3c-3) on 2026-08-25. H6a, H6b and H9a merged on
2026-08-23; H9b, H9c and H9d on 2026-08-24. **The command surface is finished**: every row of
`reference.md` § CLI reference reads `built`.

**What that changes for anyone reading this file next.** There is **no later slice**, so a
`spec-defects.md` entry owned by *unassigned* is not deferred work — **it is what this project ships
with**, and every such entry now says so in those words. A gap found from here is a new slice's charter,
scoped and designed the way every one of these was: **a dated scoping measured against the code first**,
because every charter re-scoped in this project was stale in the same direction — H8 at 30 tasks against
one row, H5 at 19, H6 at 20, H9 at **49**, and H3c-3's own remainder at 23 against a charter of 14.
H5 split two ways on the write/downstream seam, and the split's own framing was corrected twice: the
exposure was never H5b's alone (H5a's task 9 changed a shipped surface too), and what the split actually
rested on is narrower — **H5b changes what an existing key may contain and report (`aggregated`), and
H5a's change was additive to what `io.write` accepts.** **H6 was chartered as independent** in the spine
design and was omitted from this sentence for several slices while it was narrowed around the families
being worked; `spec-defects.md` carried live entries owned by it, which is how the omission was caught —
and **H6a's appended correction to that charter narrowed the verdict in one direction, H6 before H9**,
since `reproduce` re-derives an identity claim and so had to be built against the hash definitions
rather than before them. That ordering is settled now that H6 is complete and H9 is next. **The spine
design's own nine-row charter table was never amended for either H8's three-way split or H5's two-way
one** — it read as nine slices while the work had become fourteen, and an appended amendment dated
2026-08-22 now records both; **a second correction the same day records H6's two-way split too**, so
the omission ran to three splits, and *fourteen* is the spine's own figure written before H6's split
reached that table — quote it rather than re-deriving it. Amended twice on 2026-08-14
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
beside the same structure are now a named refusal, `E-REPL-FOLD-CELLS` / `E-DATA-HOLDOUT-CELLS` — **both
retired by H3c-3 on 2026-08-25, which built the drawing-within-a-cell the refusals were waiting for**), and
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
of which is H7b's: `io.reuse_from` (**which H8a has since built** — see the entry below) for E3, E4, E6, and `E-DATA-WEIGHT-CONTRAST`
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
executable count stays at three**, because C1–C3 also need `io.reuse_from`, then unbuilt and unowned and **since built by H8a**.

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

**H3c-3 (folds and holdouts inside cells) merged on 2026-08-25 — the last slice in the project.** A
`{kind: fold}` level's partitions and a `data.units.holdout` are now drawn **inside each cell** rather
than across the roster, so every cell contributes the declared fraction of **itself** and `k` is bounded
by the **thinnest populated cell**; `E-REPL-FOLD-CELLS` and `E-DATA-HOLDOUT-CELLS` are both retired, and
`limits.min_units_per_cell` gains its first reader as **`W-DATA-CELL-THIN`**. It **unblocks zero configs**
— no experiment in the feasibility analysis declares a group axis, which is why H3d was allowed to precede
it in the first place.

Five things worth carrying, and the first is the one to read twice.

**Retiring a refusal can open a defect the refusal was silently holding shut.** `runner.execute_plan`
composed an **arm-narrowed test side** with a **roster-wide train side**, and the only thing preventing a
model from being trained on units it is then evaluated against — **across arms, with no diagnostic** — was
one assert whose own comment justified it by `E-DATA-HOLDOUT-CELLS`. The fold path fifty lines below got
it right. **So the ordering was ruled before any task ran**: *no commit exists in which the assert is gone
and the train side still comes from the roster*, and that was checked **commit by commit**, not claimed.
**A guard whose correctness depends on a refusal nobody plans to keep is a defect with a delay on it.**

**A ruling's premise can be false while the ruling is right.** Ruling HH ordered the slice built because
two normative documents described the behaviour *in the present tense* — measured, **all three sites read
"not built"**, so the documents and the code already agreed and *an unbuilt reader of an unbuilt surface
is specification*. The decision was **re-grounded rather than rewritten**, on three grounds that survive.
**Append the correction; do not retro-fit the argument.**

**The accepted-and-never-forwarded defect landed TWICE in one slice — the fourth and fifth instances in
four slices.** A `cells` parameter was added to `_resolved_holdout`, documented at length, and wired to
`cells=None`; the same shape then turned up at `validate._holdout_test_roster`, forwarded and **pinned by
nothing**. **Both were caught only by fixtures built to discriminate two readings rather than exercise a
path** — the first because it asserts **membership** where a per-arm count would have passed by chance
with probability **≈0.42**, the second because the gate wired the argument to a constant and watched the
whole suite stay green. **A count is not a discriminator; a path exercised is not a property pinned.**

**The oracle was measured against the other tree, not read off an arm.** 336 no-cell cases — folds and
holdouts across rosters, digests, `k`, clusters, strata, methods and seeds — run under both HEAD and a
real `main` worktree and compared **byte for byte**, with the comparison proven able to fail. *That is what
"bit-identical where nothing should change" costs to actually know.*

**And a guard pin can expire rather than break.** H9d's arm C hashed two live documents to assert a fact
about a **past merge**, so it had to go red the first time a later slice legitimately edited either — and
it did, when this slice replaced a sentence that was **false against the code**. The investigation it
forced **retired half of it**: a digest over a document whose job is to describe behaviour slices change
is a **proxy that fails whenever the document does its job**, while the half over `design-principles.md`
stays, because for a file that should not move a digest **is** the direct question. **The arm worked
exactly as designed — its firing was information, and the information was about itself.**

**H9d (`demo`, `docs`, `list-templates`) merged on 2026-08-24 — the last of H9's four, and the last of
the command surface.** `demo` walks the whole arc and **prints what it actually prints**: `run`'s stdout is
its warning block plus `run.yaml → <path>`, and README's transcript had described a results table, progress
bars and a banner that **no command produces** — along with a `dry-run` count of 15 where the real answer
is 19 and a `validate` line that was fiction outright. `docs` gained the **region parser that existed
nowhere in `src/`**, with a missing or malformed region a **named refusal** rather than a silence, because
*a command that silently rewrites nothing looks identical to one that worked*. `list-templates` was found
**orphaned**: its only chartered home was H7, which closed without it, and the one live routing was a
design sentence saying *"H9's list"* — **a command orphaned by a closed family is found by re-reading the
charter against the code, not by waiting for someone to notice.** It retires no refusal and **unblocks
zero configs.**

Five things worth carrying. **The plan carried THIRTY-THREE corrections against the code, the most of any
in this project**, and the largest cluster was a documented walkthrough describing output that does not
exist — which is the *documented rule with no code behind it* defect landing on **the one page a new user
reads first.** **A guard pin whose golden is a SCAN RESULT rather than a literal list can be edited without
becoming a transcript**: arm D's post-edit state was specified **procedurally** — re-scan with the
unmodified helper, expect the pre-edit tuple minus exactly four named entries, and *any other survivor is a
finding, not a literal to refresh* — and both the batch and the gate ran it. **A ruling's escape clause
firing is not a ruling ignored**: ruling GG required `self.rng` to become a `numpy.random.Generator`
because two normative sentences said so and **zero tests mentioned it**, and when no task turned out to own
`base_step.py` the batch **filed the change and made the documents true of the code instead** — which is
the honest interim, and the gate then caught that **one of the four sentences was still false**, so the
seed claim was corrected and **`random.Random(0)` shared by every non-repeat execution** was filed.
**`E-GIT-NO-REPO`'s row has now been widened and then undercounted in three consecutive slices** — six →
seven → eight → **ten (two uncaught, four by code, four by type)** — which is why it now states the
**breakdown rather than a total**: a number is a claim nobody can check, an enumeration is one anybody can.
And **a design can prescribe an implementation that is a measured no-op**: its bytecode remedy handed
`spec_from_file_location` an explicit `SourceFileLoader`, which is what it already returns, so the batch
shipped the substance and said so rather than shipping a change that looks correct and does nothing.

**H9c (`reproduce`) merged on 2026-08-24 — the third of H9's four.** `reproduce` takes one path and
**does not resolve a target device**: *"reproducing on another device"* names where the user is, not an
argument, so it runs **on** the other device against a record it is given — which is what makes the
**bundle-member form a first-class arm** rather than a note. Given a run record it clones the recorded
remote into a **derived** destination (the remote's last component, `_`, the `run_id`), checks out the
recorded commit detached, recomputes `code_hash` with `run`'s own predicate, restores the environment
against the recorded `uv_lock_hash`, writes the config back **re-serialized from the record** and
self-checked with `parameters_hash`, writes `configs/<name>/apparatus.expected.json` when the run
measured through an apparatus, lists `required_env`, and **stops** — both remaining inputs need a
person. Given a config it does the same from step 4 onward, in the repository the config sits in, and
names the three things it did not verify. **It retires no refusal and unblocks ZERO configs** — so the
four-row table in [the feasibility analysis](docs/feasibility-llm-growth-studies.md) § Executability on
this build is repeated character for character; quote that table rather than any number from this
paragraph. **Thirteen codes are minted — twelve `E-REPRODUCE-*` and one `E-APPARATUS-*` — thirteen
§ Errors rows, and no exit code**; `5` gains readers for its *"a clone or `uv sync` that failed"*
clause at three sites.

**Two behaviour changes, and a wrong disclosure would be worse than none, so both are measured.**
`run` and `draft` gain **one comparison**: the first probe round now checks
`configs/<name>/apparatus.expected.json` when that file sits beside the config *and* the template
declares a probe — `E-APPARATUS-UNEXPECTED`, exit `1` before the first execution and `4` once there
are results. Measured on both worktrees through the console script: with no such file, 93 `run.yaml`
leaves compared and every difference in the normalization list written in advance. And
`publishable reproduce <path>` stops printing *"specified but not built"* at exit `2` and starts
dispatching, while **`publishable reproduce new` prints `E-IO-FAILED` at exit `1` — exit `2` → `1`,
and the identifier is new** — all four invocation shapes measured through the real console script
outside the repository rather than predicted, which is what H9a got wrong three ways for `draft new`.
A `resume` whose run-start round contradicts the expectation, with a prior attempt's executions on
disk, **keeps its record**: exit `4` with a `run.yaml` rather than `1` with none.

Five things worth carrying. **A design's own derivation can go false inside its own slice.** Design
§ 7 argued the executability verdict from *"none of the nine configs is a run record, so none is an
operand `reproduce` accepts"* — and Decision 13's config form, built two tasks later, accepts a config,
which all nine are. The verdict holds on a different ground (`reproduce` runs at no `validate`, is
invoked from no step, and **accepting a config as an operand is not a config executing**), and the
entry derives it rather than repeating the sentence. **A brief's task boundary can be impossible.**
§ CLI reference's `reproduce` row was task 15's, but guard-pin arm B's authorized post-edit state
**parses that table** — so the `Status` cell had to flip in the dispatch commit or the branch was red;
measured, flipping it back fails arm B and the document-versus-code bind. **A shipped comparison can
degenerate rather than transfer.** Decision 13 says the config form runs Decision 3's lockfile
ranking; it cannot — that ranking's authority is the recorded `uv_lock_hash` and its carrier is the
run directory's byte copy, and a config has neither — so the form prints the repository's own lockfile
and its digest **and the absence of anything to rank it against**, a fourth honest absence beside the
three not-verified lines. **`E-GIT-NO-REPO` was reused rather than a fourteenth code minted** for a
config outside every repository, which makes it a **seventh** path to that code and a **third** site
catching it by code — **and the gate then found an eighth**, `prepare_checkout`'s walk-up from the derived
destination's parent, where a raise IS the ordinary case, so the exception path is the pass branch and the
quiet return is the refusal; the row had been widened six → seven and still undercounted — and its row's closing sentence, *"a config outside every repository prints
`✓ config valid` and refuses only at `run`"*, went false in the same edit and was corrected in it.
And **`E-IO-FAILED` has no § Errors row at all** — it lives as one sentence in § Exit codes saying it
*"exits `1`"*, which is now false at three sites; the sentence was widened to name every site rather
than a fourteenth code being minted for the clone and the sync.

**H9b (`resume`) merged on 2026-08-24 — the second of H9's four, and NOT additive.** `resume` is a
second entry into phases 6-10 of a run that stopped without writing `run.yaml`. It compares recorded
against recomputed and the recorded side is a **new run-start artifact**: `identity.json`, five keys
(`code_hash`, `parameters_hash`, `uv_lock_hash`, `config_path`, `draft`), written inside the lock
before `sweep.yaml`, because a crashed directory holds no `run.yaml` to read a claim from —
`input_manifest_hash` is deliberately absent, `manifest/input.json` being the operand rather than a
hash of one. It reads `sweep.yaml`'s plan and recorded order, `allocation.json`'s memberships and
`apparatus/probes.jsonl`'s baseline **back** rather than re-deriving any of them, reconstitutes a
**full** `ExecutionResult` for every triple it skips (phase 8 reads results, not the disk — the
scoping's *"`aggregated` survives, it is recomputed from `units.parquet`"* is false, and that one
falsification is why the slice came to eighteen tasks), may **take over** a lock whose holder is
provably dead, and refuses fourteen named ways. **It retires no refusal and unblocks ZERO configs** —
`resume` runs at no `validate` and from no step, and a crashed run directory is a property of an
operator's history rather than of a config — so the four-row table in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) § Executability on this build is
repeated character for character; quote that table rather than any number from this paragraph.

**Six things move, and the disclosure enumerates them with a seventh appended**: `identity.json` in
every run directory; two keys on `executions.jsonl`'s line (`returned`, `recorded_columns`);
`dry-run`'s printed fixed-file count; `run.yaml`'s `attempts` becoming a **count of ledger records**;
`resume`'s four invocation shapes; `freeze`'s new `E-FREEZE-CONFIG-EDITED`; and, appended,
`apparatus.replay_ledger`'s defaulted code parameter. **Item 3 is the under-read one** — `dry-run`'s
transcript is what a user reads before spending money, and a reviewer finds that item by *running*
rather than by reading, which is why it is listed third rather than as "a test literal moves".

Five things worth carrying. **A stop that discards work already done is worse than the change it
protects against.** A resume whose apparatus had moved while the run was down exited non-zero with no
`run.yaml`, and repeated identically for as long as the fact stayed moved — *every execution paid for,
the record lost*, this repository's most expensive defect class, made real and pinned by the task that
created it and closed by the next. It now publishes `status: failed` with the reconstituted executions
aggregated and the moving observation in the ledger the record names. **The exit code was decided by
§ Exit codes' own qualifying clause rather than by the two the brief offered**: `1` is for a changed
fact *"caught before the first execution ran, which leaves nothing to mark `failed` at all"*, which is
exactly false once there are results to mark, and `5` is the class you retry — so it is `4`, from the
shipped status fold, no code minted. **And the closure is scoped by a fact about the artifact, not by
convenience**: writing `run.yaml` *ends* the run, so the same treatment for an *unreachable* apparatus
would convert a recoverable state into a permanently truncated one. That half is filed with the
terminality as its reason.

**A lock is the one thing here that cannot be pinned by a mutation alone, and the criterion is where
the earlier measurement went wrong.** Two candidate protocols were falsified on trial 0 by
five-process probes; the shipped one is an exclusive `O_CREAT|O_EXCL` token as the mutex, the holder
dead **only** on `ProcessLookupError` from `os.kill(pid, 0)` for a pid recorded against this
`gethostname()`, then the ordinary lock — whose exclusive create stays the only claim. Re-raced
against the **shipped** code: **0 violations in 60 trials × 5 processes, and 0 in 120 × 5** with a
stagger inside the residual window, against **36 of 60 violated** with the token deleted and **60 of
60** with no exclusion at all. But *"two winners in a trial"* — the criterion the earlier probe used —
**flags the shipped protocol too**, and did, on 3 of 3 trials: a winner releases the lock when its run
ends, so a second `resume` winning afterwards is legitimate. The violation is **two holders at one
time**, and a control that cannot fail is not a control: without the stagger, the token-less variant
violated nothing either. `lock` gains `started_at` for the diagnostic and the liveness test
deliberately does not read it, so PID reuse refuses rather than guesses.

**A mutation is a claim, and so is a pin.** The two-thread mutual-exclusion test's first version
released both threads together inside the liveness syscall — and deleting the token's `O_EXCL` left it
**green**, because two threads that unlink before either creates still meet the real claim and exactly
one wins. The violation needs a **stale verdict**: one thread judging the old holder dead, the other
taking the lock, the first waking to unlink a *live* holder's lock. The barrier is asymmetric now, and
that was found by running the prescribed mutation rather than by reading the test. **A brief's mutation
can also go blind under the very change it is prescribed for**: *"move the two-token arm above the
built branches"* was to be caught by a `resume <path>` fixture — true only while `"resume"` was still a
`NOT_BUILT_COMMANDS` key. Measured after the dispatch landed: full suite **green**, zero failures,
because none of the four remaining keys has a built branch or a two-token form. What binds that
invariant is the self-maintaining document-versus-CLI pair, measured by putting `resume` in both
places, which fails nine tests.

**And a pin can be honoured by not colliding with it.** Guard-pin arm R (editor NONE) pins every line
of the four documents carrying a worked-example literal, so a new `identity.json` example showing
`8e21…`/`1a2b…`/`6b1f…` and a ledger line showing `0.607` **added four lines and failed it**. The
digests are elided in the example instead — with a sentence saying the run record is the one place a
reader compares them — and the ledger's `returned` is `{}`, which is what the worked example's
repeat-scope step actually returns, the correlation being derived by the template's `aggregate`. No arm
moved, and the collision was better information than the edit would have been.

**H9a (the re-entry seam, `draft` and `dry-run`) merged on 2026-08-23 — the first of H9's four, and
NOT additive.** `command_run`'s ten phases are split at the seam every second entry needs: phases 1-5
are `cli._prepare_run`, returning a frozen `Prepared` of **thirty-six** values or the exit code the run
would have returned, and phases 6-10 are `cli._execute_prepared`. `draft` relaxes the dirty gate for a
mode and nothing else — the pathspec `E-CODE-DIRTY` covers is byte-unchanged, H6b's declined widening
still declined — records `draft: true` unconditionally while `git.code_dirty` stays a **measurement**,
and prints a notice to stderr when it relaxed. `dry-run` runs phases 1-5 plus a probe round of its own
and prints the resolved conditions, the repeat plan, the step list with scopes, the execution and
**unit-execution** counts, the step directories and the fixed files — and says what it omits and why.
**It retires no refusal and unblocks ZERO configs**, and the reason is structural rather than
incidental: both commands are *second entries into a sequence these configs already reach or do not*,
neither runs at `validate` nor from a step, and all nine validate against `generic`, whose
`apparatus_probe` resolves to `None`, so the probe round never fires for any of them. The four-row
table in [the feasibility analysis](docs/feasibility-llm-growth-studies.md) § Executability on this
build is repeated unchanged — quote that table rather than any number from this paragraph.

Four things worth carrying. **A promise that can only be kept by breaking a stated non-promise is the
document being wrong** (Ruling R): § Operation commands promised `dry-run` prints *"every artifact path
that would be written"*, which needs the `io.write` names inside step bodies — and `reference.md`
itself promises core never inspects them. Two artifacts are conditional on *runtime* facts on top of
that. So the promise narrowed to step directories and fixed files, **the counting rule went into the
document beside the number** (one directory per planned (step, condition, repeat) triple — 20 for the
worked example), and **the 20 was verified by running a real 4-scope, 3-condition, 5-seed project**
rather than by trusting the arithmetic. A narrowed promise that does not say what it dropped is worse
than the wrong one it replaces, so the output names its own omission. **A prescribed mutation was
blind on every shipped arm, and only building the arm showed it**: the design's Fixture Y mutation is
*"add `append_observation` to `dry-run`'s round"*, and all three shipped *creates nothing* arms drive a
`generic` project, whose `apparatus_probe` is `None` — so the round returns at its first guard and
there is no round to add to. Spliced in for real, the three shipped arms **pass** and only the new
probe-declaring arm fails. *Naming a seam is not testing it*, one layer up: the mutation was named,
checked for two differing branches, and still could not reach the code. **Thirteen § Errors / § Warnings
rows were narrower than their code, each narrowed by this slice itself** — `dry-run` is a new emit
surface for six apparatus and plugin codes (`E-APPARATUS-RAISED`'s *three* outcomes became four,
`W-APPARATUS-UNANSWERED`'s *second* surface a third), and the extraction plus two new commands made
`run`, `draft` and `dry-run` all meet the six dual-surface roster rows that said *"`command_run` … at
`run`"*. § Errors carries one row per code covering **every** emit site, and each table's own scope
sentence limits no command — so a slice that adds a command owes that sweep whether or not it minted
a code, and this one minted none. **A fourteenth row moved in the same fix round and is a different
fact, not a fourteenth narrowing**: `E-CODE-DIRTY`'s row had gone wide in an earlier batch and was
corrected back narrower — a widening caught and closed, not a row this slice's own additions made too
narrow — so it does not join the thirteen. And **an amendment to a sweep is a claim like any other**: the fix
round that corrected task 12's sweep target — because the old target had zero homes — re-measured the
new one at **three** homes for `would write` when it had **four**, and the missed hit was a line that
same round's own report quoted. Caught by attributing every hit individually rather than reconciling
against the amendment's table, which is the rule the amendment was written to enforce.

**H6b (the environment record and the diagnostic debt) merged on 2026-08-23 — the last of H6's two,
and ADDITIVE throughout.** `provenance.environment` gains the three keys § The two files has always
shown and nothing wrote: `os` (`platform.system()`-`release()`-`machine()`, three components on every
platform — **not** `platform.platform()`, which measures the marketing name, `macOS-26.5.2-arm64-arm-64bit-Mach-O`
against `Darwin`/`25.5.0`/`arm64`), `hostname` (`socket.gethostname()`, the spelling `run_identity`
already uses for the run lock, because two spellings of one fact is how the two drift), and `hardware`
(`{cpu_count: …}`, a mapping, with `os.cpu_count()`'s own `None` written through rather than
substituted). **The additive claim is measured rather than framed**: no hash reads the record —
`grep -n "hash(provenance\|hash(run_doc\|hash(record" src/publishable/*.py` returns nothing, and the
`provenance` mapping is built after every hash has run — and only two readers of
`provenance.environment` exist, neither of which iterates it (`diff._figure` reads `uv_lock_hash`,
`study._redact` reads `hostname`). **It retires no refusal and unblocks ZERO configs.** § Executability
in [the feasibility analysis](docs/feasibility-llm-growth-studies.md) does not move, and the derivation
is written ahead of the table there rather than asserted: nothing in this slice emits at `validate`, and
`provenance.environment` is written for every run regardless of config, so no config gains or loses a
dependency. **Quote no single number for it** — name the dependency instead: `io.reuse_from`'s
plugin-side call for six, the `report_by`-under-`resample` gap for seven, and 8 of 8 validating clean,
which is the only figure `validate` can see.

**CONTROLLER RULING O's trade is the one to carry: `hardware` carries `cpu_count` and NOT `gpu`, and
the shared worked example lost a line for it.** Core cannot probe a GPU without a dependency or a
subprocess, and a GPU is not universal, so it is an **apparatus** fact — § The apparatus core can only
observe. The cost is real and is not hidden: **a bundle reader can no longer tell what hardware produced
a number unless the producing project declared a probe**, and `cohort-pilot` declares none by
construction (its example records `apparatus: null`). The rejected alternative would have sourced `gpu`
from the apparatus *inside* that example, which would have given the worked example a probe and
contradicted § The apparatus core can only observe — **a ruling that fixes one document's example can
contradict another document's claim about the same example**, and only sweeping for the *claim* rather
than for the key `gpu` finds it. **RULING Q**: `os` and `hardware` are **not** redacted from a bundle
and `hostname` is, because redaction is for identity and credentials while a bundle reader needs the
platform that produced a number — and **the pin is the point**, since H8c wrote `hostname`'s redaction
against a key nobody wrote, so until this slice there was nothing to pin. A real bundle built outside
the suite carries `hostname` redacted and `os`/`hardware` verbatim, and extending the redaction to cover
`os` fails the new fixture. **RULING N** gives `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT` their own § Errors
core raises rows — taken because both are raised by `provenance.py`, the file H6a rewrote, which is a
fact about the emit site rather than an argument from the word *provenance* — and each row covers **every
reach path, not the raise**: `E-GIT-NO-REPO` has one raise and six reaches, three of them deliberate
swallows, which is why a config outside every repository prints `✓ config valid` and refuses only at
`run`. **The undocumented-codes filing's heading goes from nine to five, derived rather than carried**:
nine, minus `E-CODE-DIRTY` (H6a batch 4), minus `E-EXPERIMENT-UNKNOWN` (H8c task 16), minus H6b's two —
and `E-STEP-EXISTS` was **never one of the nine**, which is what filled the sixth slot in both the
design's and the plan's first drafts. The five that stayed filed were `E-INPUT-CHANGED`, `E-RUN-LOCKED`,
`E-RUN-ID-EXHAUSTED`, `E-PROJECT-EXISTS` and `E-EXPERIMENT-EXISTS`, **unassigned with the reason**: no
remaining chartered slice had `run_identity.py`, the manifest path or `generators/` as its surface.
**CORRECTED 2026-08-26 by the whole-project review — that list named the wrong codes, and it is now
empty.** `E-RUN-LOCKED` and `E-RUN-ID-EXHAUSTED` gained § Errors rows under H9b's Ruling X and
`E-EXPERIMENT-EXISTS` gained one too, so three of the five were already documented when the list was
written; and `E-PROJECT-EXISTS` was never undocumented at all, because **§ Exit codes documents the whole
generator-refusal family in one passage** — `new`/`plugin new`, `generate experiment`/`step`/`template`/
`report`, `study new` — deliberately, with an argument against minting *"a namespace per command"*. **Only
`E-INPUT-CHANGED` was genuinely uncovered, and it now has a row of its own** as the third `Collector`
refusal beside `E-CODE-DIRTY` and `E-CODE-EMPTY`. **The lesson is this file's own: row-presence is a proxy
for documented-ness, and here the proxy is wrong** — a class documented as a class has no row per member
by design, so an audit counting rows finds five defects where there is one.
**RULING P: no seat** — § Templates' *"goes dirty at `validate`"* sentence measures **true** and gains
no `W-` code, because a `W-` is a registry seat and `E-CODE-DIRTY` already catches the condition at
`run`. **And DECISION 12 DECLINES** the root-`.gitignore` filing H6a's gate left with H6b's name on it,
re-owned unassigned with the reason: widening the dirty gate's pathspec to the repository root is a
behaviour change to a shipped command — every uncommitted root file becomes a candidate the gate must
rule on, and a false positive there stops a run carrying no identity defect — and **a slice chartered
additive cannot widen a shipped gate's pathspec.** Answering it *widen* while Ruling P answers the
neighbouring question *add nothing* would decide one shape of question in opposite directions in a
single slice, on no argument.

Four things worth carrying. **The charter was stale in the same direction again, and one of its gaps
could not have been in it**: three of `H6-SCOPING.md`'s eight rows were wrong (`E-CODE-DIRTY` already
documented, task 18 a confirmation rather than a change, and three key-writing tasks that are one task
because they write one dict literal and each would edit the same shipped pin), and **a fourth item was
filed by H6a's own whole-branch gate after the scoping was written** — 8 rows became 11 tasks. **A pin
that must move can be moved once, by a named editor, with its post-edit state written before anything
moves** — the direct answer to H6a's batch-2 Major, where arms captured against a superseded signature
forced a later task to choose between a broken import and an unauthorized edit. Arm P was captured in
batch 1 against the shape task 3 would produce, specified as
`isinstance(hardware, dict) and set(hardware) == {"cpu_count"}` rather than as "a type assertion", and
the diff matched byte for byte. **The other half held too, and it is the more valuable half**: task 3's
write falsified the premise arm S rested on — *today's real records never carry `hostname`* — and with
no authorized editor for arm S the task **left the branch red and reported** rather than
self-authorizing; the ruling then kept the property and changed only its source, and the reviewer
re-ran the mutation the arm exists to catch. **A fixture that recomputes the implementation cannot
fail**, which is why `os` is pinned with installed sentinels rather than with the composition itself.
**And a false enumeration was DELETED rather than rewritten**: `secrets.py`'s docstring enumerated
`provenance.environment`'s keys inside a structural claim, was already false before this slice and
more false after, and the structural claim (*nothing here imports `provenance`*) stands alone —
while `study.py`'s *"never written today (measured at `ebf642a`)"* was **corrected rather than
deleted**, because the measurement was true on its date and **deleting a true claim is not licensed by
prefer-deletion**. The distinction cost a follow-up commit when a third site substituted new prose
where a deletion was specified.

**H6a (the two hash definitions) merged on 2026-08-23 — the first of H6's two, and a VALUE CHANGE.**
`code_hash` no longer folds a file the repo's own committed exclude rules skip, so **one published
identity claim moves for an unchanged tree at an unchanged commit**. Measured end to end through the
installed console script on a byte-identical project: `09a843b1…` before, `f6a935cf…` after, with
`run_id` and `results/latest` following. **Exactly one hash moves and the other ten the record carries
do not** — `parameters_hash`, `input_manifest_hash`, the per-file manifest digests, `uv_lock_hash`,
`units_hash`, `allocation_hash`, `apparatus.hash`, `design_digest`, the copied upstream
`parameters_hash`, and every derived seed — enumerated rather than counted, and pinned as literals by
a seven-arm guard pin whose arm C exists to make *"exactly one hash moves"* a pin rather than a
sentence. Two errors are minted (`E-CODE-EMPTY`, `E-CODE-FILE-LIST`, one emit site each) and one
warning (`W-PARAM-UNSET`, at `validate`, for the `parameters` block only). **It retires no refusal and
unblocks ZERO configs**: § Executability's four-row table in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) is repeated character for character,
because row 1 counts *errors* and `W-PARAM-UNSET` is a warning, both new errors are raised by
`command_run` rather than by `validate`, rows 2 and 3 name dependencies this slice does not touch, and
`code_hash` is computed for every run regardless of config. **`parameters_hash`'s code did not change**
— the charter's normalization clause is rejected with grounds rather than deferred.

Four things worth carrying. **The disclosure is `uv.lock` and nothing else, by ruling.** A
`provenance.hash_definition` key, a fourth hash, a `schema_version` bump and a `diff` row of its own
were each *refused* rather than merely unbuilt — a bump makes `lineage.read_record_file` reject every
record on disk — so **`diff` prints `code_hash DIFFERS` for identical code across this boundary**, and
the only machine-readable carrier of *why* is the lockfile's `publishable` version. That claim is the
guard pin's seventh arm, with **no authorized editor**, because it reads like a defect and is a
consequence, and is therefore precisely the claim a later slice will want to soften. **Ruling C's
sharpest cost is that one record can carry two hash definitions at once**: `provenance.upstream[]`
copies an upstream run's `code_hash` verbatim, so a record written after this slice can hold its own
digest under the new rule beside a copied one under the old, **with nothing marking which is which** —
the reader's route is the two runs' `uv_lock_hash`. **The exclude chain is narrowed rather than
disclosed as machine-dependent**: every `check-ignore` runs with `-c core.excludesFile=` — *a rule
that does not travel with the tree cannot define the tree's identity* — and **the whole-branch gate
then extended that to the dirty gate (Ruling L, 2026-08-23)**, reversing the design's argument that a
gate asking *may this run proceed here* is local by nature: a file a global `core.excludesFile` hides
is **untracked and ignored by nothing a clone carries**, so leaving the gate alone meant it reported
clean while the hash folded the file in, and *"the gate and the hash now consider the same set of
files"* was shipped as a normative sentence that measured **false**. Both gates now ask one git, and a
repo relying on a machine-level rule to keep a file out of `src/**` **fails `E-CODE-DIRTY` where it
used to run** — disclosed in § How the three are computed. **What the narrowing does NOT buy is a
tree-only answer**: `check-ignore` reads the **working tree**, so an uncommitted root `.gitignore`
decides too and the gate cannot see it (its pathspec is the two hashed trees), which is why *"the only
machine-dependent input left"* was struck rather than narrowed — filed, owner H6b. `.git/info/exclude`
remains the residue no flag can disable. **CONTROLLER RULING M (2026-08-23) then replaced the
mechanism itself**: the fix round's total environment neutralization
(`GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM=/dev/null`) discarded far more than exclude rules — a global
`core.fileMode = false` or `core.autocrlf` made an **unedited** tracked file read `code_dirty True`,
measured — so it is replaced by exactly two `-c` overrides, `core.excludesFile=` and (for the gate)
`status.showUntrackedFiles=normal`, and nothing else. That closes the `safe.directory` fail-open the
fix round had filed as a consequence of the neutralization: a legitimate global `safe.directory`
allowlist entry is no longer discarded, so the check it exists to pass now succeeds, re-measured with
the identical fixture — struck rather than left open in `spec-defects.md`, because it was that
mechanism's own defect rather than a gap in the rule. **And an implementer may not self-authorize an edit to a guard-pin arm with no
authorized editor, even a mechanical one that turns out clean** — batch 2 did, and that was its own
batch's only Major; batch 3 met the same need, took the route instead, and the controller's ruling
named the post-edit state in advance, which is the whole difference. **Three sentences went false
under this slice's own change and each was caught rather than shipped**: `code_hash`'s docstring
saying it reads the tree *not from git*, an arm's docstring asserting a call-site count **the batch
holding it falsified**, and a shipped test's docstring asserting an exclusivity `W-PARAM-UNSET` had
just removed.

**H5b (non-numeric columns downstream to `aggregate`) merged on 2026-08-22 — the last of H5's two, and
the first behaviour change since H7d Part B to what an existing key *reports*.** A recorded column that is
not a number is carried through `collapse_repeats` into the table a template's `aggregate` receives, and
**every unit the collapse is handed is admitted** — where a unit whose every recorded value was
non-numeric used to vanish from the unit table entirely, so six units all recording `valid: True`
published `n_valid: {value: 0.0, ci95: [0.0, 0.0], resample_draws: 2000}` at exit 0 with no diagnostic.
A column earns a metric block when it carries a real number for at least one unit, computed over the
units that carried one and reporting **that** contributing count as its own `n.completed`; a column no
unit carries a number for earns none and still reaches `aggregate`'s table, where a template that knows
what the values mean can read it. **It retires no refusal and no config's declaration changes** — and it
is the first slice in a while to **move a row** of
[the feasibility analysis](docs/feasibility-llm-growth-studies.md)' four-row table rather than repeat it:
row 4 is re-derived **`1 → 0 → 1`**, rows 1–3 are repeated character for character, and **the table stays
four rows wide.** Quote that table or name the dependency; do not quote one number for that analysis'
executability.

**The exposure is an enumeration, not a phrase, and a count is not an enumeration.** Nine classes of key
move, each pinned in a guard pin arm captured before anything moved. **Seven keys in one direct-call
fixture** (`seed=7`, `draws=2000`, six units of which four recorded a `score`): `n_valid.value`
`0.0 → 6.0` and `.ci95` `[0.0, 0.0] → [6.0, 6.0]`; `n_rows.value` `4.0 → 6.0` and `.ci95`
`[4.0, 4.0] → [6.0, 6.0]`; `mean_score.n.completed` `4 → 6`; `mean_score.ci95`
`[0.5, 2.5] → [0.3333333333333333, 2.5]`; `mean_score.resample_draws` `2000 → 1998` — while
`mean_score.value` stays `1.5` and every `score.*` literal stays put, which is what lets that fixture
tell *the table widened* from *the metric changed*. **An eighth class:** a derived metric's `p_value`
(`0.846307385229541 → 0.812375249500998` at `seed=7, n=500`) and, through the family, its
`p_value_corrected` — a `permutation_of_derived` draw rebuilds its table from whole rows, so admitting
units widens the null too. **A ninth:** every `report_by` level's own keys, a projection with no code path
of its own, found by a review rather than by the design's own enumeration. **And a correction family
moves in a two-condition run**: `n_paired` `4 → 6`, with `mean_score` and `score` trading Holm's levels
(`0.025`/`0.05`), so **a column holding no non-numeric value anywhere gets a different `ci95_corrected`**
— the least intuitive thing here and the reason it is a pin arm rather than prose.
`resample_draws` is **seed-dependent and not a constant**: four distinct literals were measured in this
slice (`1998`, `1999`, `1997`, `1927`), two of them pinned, and no literal is reused across arms.

**Five things newly stop or newly warn, and two warnings are minted.** (i) a derived key colliding with a
**non-numeric** recorded column is refused (`E-STEP-KEY-COLLISION`, re-reported as
`W-STATS-AGGREGATE-FAILED`), where both were published under one name; (ii) a step recording a
non-numeric column named `by` loses that step's `report_by` strata and earns
`W-STATS-STRATUM-SHADOWED`, where the strata were published silently beside the recorded column; (iii) an
`aggregate` that assumes every row carries its numeric column now meets rows that do not and **may
raise** — contained, costing that step's `derived` mapping; (iv) a **purely numeric** derived metric newly
draws `W-STATS-RESAMPLE-THIN`, because admitting units creates degenerate draws (`2000 → 1998` on the
direct-call fixture, `2000 → 1927` per level on a two-level `report_by` run) — an existing code at an
existing site (`cli.py:3257`) seeing a wider input, so **no § Warnings row moves**; (v) a **comparison's**
declared `resample` newly draws `W-STATS-CONTRAST-RESAMPLE-THIN` at a different existing site
(`cli.py:1659`), for the same reason — admitting units widens the contrast's own resample too, and
`reference.md`'s row for it already rules the two are two facts, since neither the `n_paired`
denominator nor a thin pool is the other's fact — so this too moves no § Warnings row. Minted: **`W-STATS-REPEATS-DISAGREE`**
(a recorded column disagreeing across one unit's repeats) and **`W-STATS-COLUMN-THIN`** (a contributing
count below `limits.min_reported_n`, per condition, step and column) — two things that newly *fire*, so
the list does not read as if nothing new appears. **`uv.lock` is the carrier of all of it**: two runs of
one config across the upgrade have `code_hash`, `parameters_hash` and `input_manifest_hash` all
`identical`, and the one row that moves prints two digests and never names the package — filed against H9,
because being *able* to derive a statistics change from a lockfile hash is not being told.

Four things worth carrying. **A rule with three cases invites a two-case sentence at every site that
mentions it, because two cases sound complete** — this slice shipped one three times, as a Critical then
two Majors and then a whole-branch Major, in **five** different files across four rounds, each caught by
someone sweeping for the *claim* rather than for the file it was first noticed in — **and the fifth home
was reachable only by a newline-insensitive sweep**, because `grep -rF` cannot match a phrase that
wrapped, which is also how the third home hid. The round that closed the fourth home swept `reference.md`
and the plan and **not `spec-defects.md`**, where the same commit had written the same sentence. The three mixtures, and the amendment table is now the single authority
every site links to instead of restating: non-numeric for **every** unit (no block, the column still
reaching the table), a number for some units and `None` for others (a block over the contributors, with
the contributing count and `W-STATS-COLUMN-THIN` below the floor), and `str` **beside** a number, which
**cannot occur** — `_check_column_types` refuses it at `finalize`, so a read rule for it would describe an
unreachable state and invite someone to build against it. **A binding ruling reached the reviewers and
never the implementer**, because it was appended to the plan under a preamble asserting that a brief
carries it — and `task-brief` extracts one `## Task N` section and nothing else; fixed by opening every
task section with a pointer saying the rulings post-date it and win. **And a ruling was then amended by
the code**: Ruling 1 called the coverage warning *not optional* because an interval over five values
beside a `completed` of two hundred is a precision claim no reader can catch — the shipped contributing
count made that claim impossible, so the warning became conditional on `limits.min_reported_n`, the floor
three shipped rows already read at `run` time against a realized denominator. **A strict `xfail`
asserting the CORRECT post-fix behaviour is a disclosure that cannot be forgotten**: batch 2's gate made
an unguarded subtraction reachable — a contrast over a ragged `None` column gave a raw `TypeError` with a
complete run directory, ten executions paid for and **no `run.yaml`** — so it shipped as
`xfail(strict=True)` naming its remover, and the suite goes red the moment the gap closes; the conversion
kept both assertions byte-identical and added one. And **two live behaviours were never pinned at all**
while a ninth moving-key class appeared in no arm — the *pin weakened quietly* shape arriving as *never
pinned in the first place* — alongside five false grounds and clauses **deleted rather than rewritten**,
in `report.py`'s two structural predicates, `cli._attributed`'s docstring, a warning's own message and a
normative § Warnings row. *A rewrite invents; a deletion cannot.*

**H5a (write-side integrity and the reserved-column namespace) merged on 2026-08-22 — the first of
H5's two.** Scalars are coerced on the write side; `RESERVED_COLUMNS` splits the *fields on `Unit`* from
the *names an attribute may not take* (adding `unit`, `measurement`, `by`) and `E-UNITS-ATTR-COLUMN`
refuses a collision at `validate`; roster attribute values are coerced at `resolve_units`; `io.record`'s
plain branch refuses a `measurement` column, closing an asymmetry with the branch three lines away that
already refused it; `finalize`'s `columns` list is deduped by name; and the slice's one behaviour change,
both row-shaped writers coerce, a non-mapping row is refused, and `io.write` names the artifact in the
diagnostic. **It retires no refusal and unblocks ZERO configs** — every check it adds refuses a config
that is corrupt today, so the feasibility analysis' four-row table is repeated character for character for
the third consecutive entry, and the direction that had to be checked rather than assumed is that a slice
shipping new refusals moved no config **into** the refused column either: the eight still validate clean.

Five things worth carrying. **A capability question is answered per format, and the ruling had to be
issued mid-plan.** Decision 5 read *"a writer accepts what it can give back"*; the controller generalized
`.csv`'s answer to `.parquet` **while enforcing the rule against answering from a proxy**, and the plan
caught it. Measured: `.csv` returns `b"x"` as `"b'x'"` and `[1,2]` as `'[1, 2]'`, so it **refuses**;
`.parquet` round-trips both, so it **keeps the capability and gains a pin**. **Four entries of one shape
are now filed** from that ruling's fallout — a bare traceback for nested NumPy scalars through
`.yaml`/`.json`/`.jsonl`, a non-`str` column key, an unencodable object through `.parquet`, and a `None`
cell silently becoming `''` through `.csv` — each a place where the promise is true of the writer's
**named** refusals and silent or uncoded outside them.

**A design's own fixture description was false of one format**, found by the whole-branch matrix rather
than by reading: Fixture E claimed a `None` column round-trips as `None` in *both* formats, and
`csv.DictWriter` has no null. Corrected by **appending** to the design, with the live half filed.

**Three miscounts in three consecutive batches**, each in a mutation-result column whose own framing is
*counts read, not estimated* — a mutation reported as 1 failure against a true 4, a `375` against a `376`,
and *"six raise sites"* against eight. **None changed a conclusion, which is exactly why they are
recorded**: a reader who trusts one is the reader who later moves a pin it was supposed to guard. And the
first of them was **better** pinned than reported, not worse — widening a `try` broke three
`pytest.raises` pins nobody had looked for.

**A mutation's prediction can go stale under a later task in its own slice.** Task 6's mutation was written
when deleting roster coercion raised inside `finalize`; once task 9 gave `.parquet` its capability, the same
mutant **completes at exit 0 and silently publishes a structural attribute** into `units.parquet`. The pin
still holds and the mutation still fails — but *where* it surfaces moved, which is why a whole-branch
re-run is not a formality: the branch under each mutation changed after the mutation was written.

**And a finding can reach the dispatch without reaching the brief.** The `.csv`-null gap was measured in one
batch, recorded in the ledger as *"filed for task 12"*, and **named in the controller's dispatch as a
carry-forward** — then neither filed nor reported open, caught only by that task's review. *A ledger line
saying "filed" is not a filing*, **and neither is a dispatch line**: a report that lists five carry-forwards
and discharges four reads as complete. This is also the third instance in one slice of a carried finding
reported closed while undischarged.

**H8c (`report` and `study`) merged on 2026-08-21 — the last of H8's three.** `report` renders a run's
or a bundle's standard sections — the condition table, deltas, hypothesis verdicts, attrition — from
any `run.yaml`, with a project's own `src/<pkg>/report.py` override free to add or reorder sections and
never to change a number; `study new`/`study add` assemble a self-contained, redacted bundle of run
records outside any repo, and `report study.yaml` cross-checks a bundle's own recorded
`code_hash`/`apparatus.hash` figures against each other rather than recomputing either, flagging a
draft member rather than refusing the whole render. **It retires no refusal and unblocks ZERO
configs** — neither command runs at `validate` or from a step, and none of the nine configs in
[the feasibility analysis](docs/feasibility-llm-growth-studies.md) declares a `study`, so its four-row
table stays exactly where H8a left it, repeated character for character rather than restated.

Four things worth carrying. **A bundle never carries `allocation.json`, ruled rather than left open**:
`study add` takes a run's `run.yaml` **path**, not a run directory, so the one run-directory artifact
that is a list of unit identities is not reachable from the argument the command takes — the route for
a reader who wants to verify the split is `allocation_hash`, attached the same way `input_manifest_hash`
already travels without the manifest itself. **A report override's `io` sentence was false of the code
and is now named for what it is**: a `summary`-scope `StepIO` is not read-only, so `ReportIO` —
`conditions`, `repeats`, `read_condition`, `read_input` — is documented as the read half of one rather
than as the same accessor. **A generated override's own worked block had drifted from what the
generator writes**, labelled `— generated` while shipping an extra `yield` and an undefined
`render_scatter`; the block now matches the generator's own output. And **the three worked `diff`
blocks predating the per-side header, filed OPEN against this slice by name, are closed**: each gained
the two header lines its own concreteness calls for, inserted only above `code_hash`, and the guard pin
proving nothing below it moved needed no editor to pass.

**H8a (lineage and `io.reuse_from`) merged on 2026-08-20 — the first of H8's three.** `io.reuse_from`
exists: a step reads a named artifact out of a **prior run**, addressed either as `<output_dir>/<run_id>/`
or by absolute path, and every read is accumulated into `provenance.upstream`. `lineage.py` ships the
`run.yaml` reader **nothing in `src/` had**, eleven `E-UPSTREAM-*` refusals, and a containment rule now
enforced on **three** readers — `reuse_from`, `read_upstream` and `read_condition`, the last two having
enforced **no name rule at all**. **It moves exactly one row of the feasibility analysis' table, 6 → 0**,
and mints no new number; the `report_by`-under-`resample` **limitation** still meets **seven** configs. It
was H4's, and the 2026-08-19 re-owning after H4d merged moved it, along with four others, to *unassigned
with a reason*: no remaining slice has the `statistics` block as its surface. **RECONCILED 2026-08-26:
this is a documented limitation, not pending work**, and `reference.md` § Statistical reporting says so in
those words. The two grounds it rests on both measure true — a level's block carries **no
`resample_draws` key at all** when `resample_columns` is false (`stats.py` calls the absence deliberate,
because *"a `null` there would claim otherwise"*), so a reader can see which construction produced which
number; and **a level joins no correction family**, which is a § Invariants rule, so the asymmetry cannot
reach an interval a verdict rests on. **The count stays** — seven configs really do meet it, and that is a
useful figure — but the word *gap* was doing work the facts do not support.
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
or a run and a config, hash by hash — each applicable row as `identical`, `DIFFERS` with its detail
lines, `not captured`, or `not comparable` (a config side), an `upstream` block when either side
consumed one — and exits `0` on every comparison it renders, `1` only when an operand can't be read.
`freeze` re-reads a run's environment and re-probes its apparatus mid-run without executing anything,
appending to the same ledger `run` writes and reporting a moved fact as a failure rather than deciding
one — the gate at the next execution is what stops the run. **It retires no refusal and unblocks ZERO
configs**; the feasibility analysis's four-row table is repeated unchanged, because neither command
runs at `validate` and no config in it declares an `apparatus_probe` a real plugin backs. `run` gains
two artifacts — `config.yaml` and `environment/repo_root.txt` — so `freeze` can resolve a
project-local template's `apparatus_probe` by path after the fact. **Decision 7 is a behaviour change
to a shipped command, and unlike H7d Part B's it is additive only**: no existing key, verdict, status,
or exit code moves: two new files land in a run directory nothing already iterates.

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

The cost is that H3d now precedes the cells work it was scheduled to consume, so **H3c-3 owned
retrofitting the holdout to cells and retiring `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS`, both
already named on H3d's branch, once drawing within a cell is built** — acceptable only because no
experiment in that analysis declares a group axis. **Discharged: H3c-3 merged on 2026-08-25 and both
refusals are retired**, so a fold or a holdout beside a cell structure is now drawn per cell rather than
refused. The reasoning lives in the spine design's *Order,
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
| [`docs/releasing.md`](docs/releasing.md) | **Non-normative.** The maintainer's runbook for a PyPI and Homebrew release, with each step's reason attached |

The first four are *the four documents* everywhere below: the invariants, the consistency passes, and the worked example govern those and only those. A `feasibility-*.md` is analysis output, not specification, and nothing in it is authoritative over them.

`design-principles.md` is the tiebreaker. Read it before proposing a change to any rule — if a rule looks arbitrary, that file explains it, and if it doesn't, that gap is itself worth fixing.

## The development record

The four documents say what `publishable` **is**. These say how it got there, and they are **tracked** — read them before re-deriving anything.

| Where | What it is | Read it when |
|---|---|---|
| `docs/superpowers/README.md` | What the record is, what governs it, and why it is tracked | Before reading anything else in it, or before adding to it |
| `docs/superpowers/specs/<date>-<slice>-design.md` | A slice's design: its decisions, each with grounds, and what it refuses | Before planning or changing that slice |
| `docs/superpowers/plans/<date>-<slice>.md` | The same slice as numbered tasks, with code and per-task mutations | While executing it |
| `docs/superpowers/*-SCOPING.md` | What was **measured against the code**, dated and pinned to a commit | Before trusting any charter |
| `docs/superpowers/spec-defects.md` | Gaps found and deliberately not closed, with the owner | Before filing a "new" gap |
| `.superpowers/sdd/<plan>/progress.md` | The ledger: every ruling, its reason, and what it costs if wrong | To learn why something is the way it is |
| `.superpowers/sdd/<plan>/task-N-report.md`, `task-N-review.md` | What was built, what the brief got wrong, what each finding was verified by | Before repeating a task's work |

**A scoping expires; a spec does not.** Every charter re-scoped so far was stale **in the same direction** — under-counted and missing surface — so a scoping is dated and pinned to a commit, and a claim carried from one without re-checking is worse than one omitted. Re-measure rather than trust.

**The plan argues from the spec, and the code outranks both.** Where they disagree, the code wins and the *document changes first* — six of six implementers on the most recent slice found a real disagreement, so finding one is expected, not exceptional.

Two things stay untracked because git already holds them: task briefs (extracted from the plan by the installed `superpowers` plugin's `task-brief`) and every `.diff` (regenerable from the two commits in its filename).

**The plugin's `sdd-workspace` rewrites `.superpowers/sdd/.gitignore` to a bare `*` every time it runs, and `task-brief` calls it.** Both scripts live in the installed `superpowers` plugin and **not in this repository — `scripts/` does not exist here**, and this file described them as repo paths for several slices, which is the *assuming a documented rule has code behind it* row applied to its own author. Already-tracked files stay tracked, so the damage is only to records created after a clobber. Restore that file's content when you notice, and use `git add -f` when committing new records.

## Invariants a change must not quietly break

These are load-bearing across all four documents; contradicting one in a single section creates a real inconsistency, not a wording nit.

- **Operation commands take paths and nothing else.** No parameter flags, no selectors, no behavior-changing env vars. Modes get their own command names (`dry-run`, `draft`, `resume`) rather than `--dry-run`/`--allow-dirty`. Only creation commands (`new`, `plugin new`, `generate`/`init`, `study new|add`, `demo`) take arguments beyond a path — `demo`'s is `[--into DIR]`, and it is one rule with `reproduce`'s refusal of the same flag rather than two: **`reproduce` derives its destination from the record, and `demo` has no record to derive from.** (`design-principles.md` § Everything is in the file)
- **Three hashes, split on purpose.** `code_hash` covers `src/**` and `templates/**` only — the code your repo supplies, a plugin's being pinned by `uv.lock` instead — separate from `parameters_hash` and `input_manifest_hash`. That split is what makes "same code, different parameters" provable across unrelated commits — unrelated meaning outside the two hashed trees, since another experiment's package is inside them.
- **`input_dir`/`output_dir` may never resolve inside the git repo**, checked at generate, at validate, and by every command that executes (`run`, `draft`, `resume`). Which repo is decided by a walk-up from the path the command was given, not from the working directory.
- **Condition vs. repeat.** A condition is a difference being measured; a repeat is a difference being averaged over. Statistics aggregate *within* a condition and compare *across* conditions — never the reverse.
- **A repeat is an execution, so the kinds are exactly the three things a re-execution can change: `seed` (RNG state), `fold` (which units it sees), `batch` (the state of the apparatus it measures through — see § The apparatus core can only observe).** A `batch` takes no field but `n`, executes in order with `order: randomized` shuffling inside it, and `validate` warns when no step sets `nondeterministic = True`. Resampling and permutation are `statistics.resample`/`statistics.null_test` over the unit table (thousands of executions otherwise, and an all-permuted design has no unpermuted value to test); technical replication is `data.units.measurements`, collapsed at unit resolution (re-running an identical step recomputes the same answer); a fixed holdout is `data.units.holdout`. `validate` rejects `bootstrap`, `permutation`, `technical`, `biological`, and `holdout` as kinds by name.
- **Units are the inference base; repeats never are.** Every interval core reports is computed from the per-unit table, `n` counts units (`resolved`/`completed`/`ineligible`/`failed`, where `io.skip` declares the third and `max_failed_fraction` guards only the fourth), and repeat dispersion is reported separately as `repeat_spread`. A metric that exists only as a step-returned scalar is `basis: repeats` and gets **no** `ci95`; the one interval core stores without computing is an `Estimate` returned by a `summary` step, marked `reported: true`, outside the correction family and never recomputed. A hypothesis may name one — it takes no `compare` — and the verdict records `verdict_rests_on: reported` rather than `computed`. Pairing is over units, never over repeats, and a contrast — `vs_baseline` or a declared `statistics.contrasts` entry — is computed over the intersection of both sides' completed units, recorded as `n_paired` — and its interval is its own construction over that intersection (`paired_t_over_units`, `paired_percentile_over_units` drawing once for both sides, or the `welch_`/`unpaired_` counterparts), never a difference of the two sides' intervals. Holm ranks on the point estimate over half the raw `ci95` width, because the family often carries no p-value at all, which is also why `fdr_bh` over such a family warns. `data.units.weight_by` weights an enriched sample's estimates and records `weighted_by`; `statistics.report_by` repeats metrics over strata without adding executions or joining the correction family; a subgroup you want to *test* is a contrast with `within`, which does join it. Contrasts compare conditions and do not nest: anything comparing two contrasts — a dose-response ordering, a difference-in-differences, a nested mean over cells — is an interaction and stays a `summary`-step `Estimate`. The table `aggregate` receives supports exactly four operations — row iteration, column access, `len`, `columns` — deliberately not a `DataFrame`, so core can change what backs it without breaking every plugin, and it carries **every** recorded column — a non-numeric one included, which earns no metric block because there is no mean of strings — beside every declared unit attribute. A metric over a column only some units carry a number for is computed over those units and reports **that** contributing count as its own `n.completed`, which is what makes the interval honest; the four-way `n` above is not widened by it. (`reference.md` § The unit table is the inference base, § Templates)
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
| Reading an unbuilt reader as a defect | An unbuilt reader of an **unbuilt** surface is specification — present tense is correct, and § Package layout's `— not yet built` carries it. An unbuilt reader of a **shipped** surface is a defect. **This row now has NO live example, and the way it ran out is the point.** (`required_env` was its example until H7c gave it a reader at `validate`; `apparatus_probe` was the next until H7b Part A's `_check_probe` gave it a metadata-name reader — not an executed probe; `apparatus_facts` was the next until H7d Part A's `check_facts` gave it a reader; **`field_convention` was the last until H9d's `docs.template_details` printed it**. `EXIT_EXTERNAL` was the same fault outside `BaseTemplate` until H7d Part B task 8 gave it its reader. Every clause is kept deliberately: **the row's evidence is its own attrition**, and it retires an entry each time a reader lands. Keep the rule and add the next example when one appears — **an empty example list is not a reason to delete a row that took five slices to empty**, and a declarable field with no reader is exactly what this project keeps producing) |

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
| An assertion satisfied by **neighbouring output** | `assert "draft" in out` passed because the member was named `draft_run`; a `run` tag's pin passed on the bundle header's `##` heading; and a no-notice control took no `capsys` and asserted only an exit code the notice never changes. Three in one batch, all green with the behaviour neutered. **When you assert a substring, ask what else in the output could produce it** — and when you assert an absence, assert it on the stream the thing writes to |
| A decoy whose **sort position agrees with the bug** | Twice in one task a scan-versus-lookup fixture ruled out only *first*-wins: the decoy sorted before the real package, so scan-first failed and **scan-last passed**. The second instance came after the first had been caught and disclosed — **catching it once does not immunize the next fixture.** Put a decoy on **each side** (`aaa_`/`zzz_`), or the fixture tests the ordering it happens to have |
| A fixture with too few elements to distinguish the candidate orderings | Both documented orderings survived reversal with the suite green: one colliding name and one broken file cannot tell name order from import order. **Two elements only ever distinguish two answers** — with two names the reverse of insertion order *is* sorted order for one arrangement. Count the orderings you must rule out, then size the fixture so each yields a different answer |
| A monkeypatch left aimed at a name the code no longer calls | Rerouting a call site through a new helper silently defused a patch on the old name; the test kept passing while testing nothing. **When you move a call site, grep the suite for patches aimed at what you moved** |
| A seam named in the brief and instantiated by no fixture | Twice in one slice a distinction was described precisely — `declared` versus `n`, strata threaded into the clustered call — and **the mutation passed all 1700+ tests**, because no config made the two readings differ. Naming a seam is not testing it: ask what config separates the readings, then check it exists |
| The test's **reader** normalising the defect away | A resolved-values echo shipped as a YAML alias — one anchor, five `*id001` pointers — and **both tests used `yaml.safe_load`, which resolves aliases**. The defect lived in the serialization and the reader undid it before the assertion. When a defect could live in *how* a value is written, assert on the raw text |
| A sweep whose **triage** discards a true hit | Two sweeps of one file missed a false clause **eight lines** from one they found, because the hits were reconciled against a design decision's table of *three known homes* instead of being attributed one at a time — so a fourth hit in an already-accounted-for file read as noise. *Every hit must be attributed before it is counted*, which this repo first wrote about refusals that fire and which applies identically to grep hits |
| Proving an arm **cannot move** offered as proof the line is **pinned** | A change to the shared worked example was declared safe because a guard-pin arm was *measured unable to see the edited line* — and that is exactly why nothing pinned it: reinstating the removed value left **626 doc-reading tests green**. Those are opposite facts wearing one sentence. **Ask what fails if the value comes back**, and prove it by neutering the new pin's own assertions and watching the suite stay green |
| A parameter **added, documented, and wired to a constant** | Four slices in a row shipped one: `draft` accepted and never forwarded to `assemble_run_yaml`; `cells` documented as *drawn inside each cell* and passed `None`; the same again one function away, **forwarded and pinned by nothing** — wiring it to a constant left the whole suite green. **The docstring is not the wiring**, and *an unread parameter is an unbuilt reader of a shipped surface*. Grep every new parameter's call sites for a literal |
| A **count** where the property needs **membership** | A proportional holdout over two arms of ten lands 2/2 **by chance with probability ≈0.42**, so `len(test ∩ arm) == 2` passes with the per-cell wiring dropped. The fixture that caught it asserts **which units**. **Before asserting a number, ask what fraction of wrong implementations produce that same number** |
| A sweep that has never been shown to fail | Two of three sweeps written in one batch were **incapable of failing** when first run — by their authors, while checking for exactly that; one had inverted fence-skip logic, one a broken slugger. A third could not match its target because the phrase wrapped. **Run every sweep against a string you know is present before believing a zero**, and report that proof rather than the zero |
| A mutation's **result** reported as a count nobody read | Three batches of one slice recorded `1 failed` against a true 4, `375` against 376, and *"six raise sites"* against eight. None changed a conclusion — and the first was **better** pinned than reported, because widening a `try` broke three `pytest.raises` pins nobody had looked for. **A number offered as verification evidence has to be the number the command printed**, or the reader who trusts it is the one who later moves a pin it was supposed to guard |
| A mutation whose **prediction** went stale under a later task in its own slice | Deleting roster coercion once raised inside `finalize`; after a later task gave `.parquet` its capability, the same mutant **completed at exit 0 and silently published a structural attribute**. The pin still failed, so nothing was weakened — but the *shape* the brief predicted was gone. **A whole-branch re-run is not a formality**: the branch under each mutation changed after the mutation was written |
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

**A reserved NAME standing in for a structural fact is another.** A `report_by` stratum was excluded
from a render by testing the string `by` — and a recorded column legitimately named `by` was silently
dropped, its value, interval, method and `repeat_spread` all present in the record. The design's ground
— *"the record `report` reads can never hold a metric called `by`"* — was false against a real run.
A stratum is identifiable by **where it sits**, not by what it is called.

**Copying a recipe's calls without its containment is a fifth.** `freeze`'s credential wiring was
cited as the precedent for `report`'s, and the calls were lifted while **the `try` they sit inside was
not** — so a project-local template raising at import escaped to `main`'s un-redacted printer and a
declared credential reached stderr verbatim, in a case § Secrets explicitly promises to redact. The
same file already had it right. **A recipe is its calls PLUS where they sit**; the reviewer's positive
control was `validate` over the identical project printing `<redacted:…>`.

**Removing by position is a fourth-and-a-half — the same fault as the grep, in a different currency.** A `sys.path` entry inserted at index 0 was removed with `pop(0)` —
which answers *which entry did I add?* with a **position** rather than with the entry. User code runs
inside that window by design, so an override doing its own `sys.path.insert(0, …)` made the pop remove
the wrong entry and leak one project's `src/` into the next render. The precedent cited in its defence —
`load_experiment` pops by index too — **held for the mechanism and not for the exposure**: only an import
runs inside that window, and a whole render runs inside this one. Remove by identity, and pin the
restoration on the failure path.

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
- **A batch with no review is where the findings will be.** Twice a controller ran a slice's final
  batch straight into the whole-branch gate without a task review. Both times the gate caught the
  omission itself; the second time **three of its four Majors lived in exactly that unreviewed
  task** — two § Errors rows narrower than their code and a docstring asserting a filing that does
  not exist. A documents-and-codes task looks like the safest one to skip and is the one whose
  output no later batch reads, so **nothing else will find its errors.**
- **A ruling that overrules a brief has to reach the brief.** A plan correction was overruled when
  the plan landed, the overruling was recorded in the slice ledger, and the plan was left carrying
  it — so the brief extracted from that plan still said *delete*, and the task deleted. **The ledger
  reaches the controller and the reviewers; it reaches no implementer.** Append the correction to
  the plan when the ruling is made, or restate every live overruling in the dispatch.
- **The sibling that already got it right is the first place to look.** Four defects in one slice were
  each fixable by reading a file that already had the answer: `freeze`'s credential containment (copied
  as calls without its `try`), a structural metric test rather than a reserved name, identity-based
  `sys.path` removal rather than `pop(0)`, and `report`'s own `results.summary` walk while `study`
  invented a shallower one that was **dead on every real record**. **Before writing a walk, a guard or
  a containment, grep for one that already exists** — and if you cite it as precedent, copy where it
  sits, not only what it calls.
- **Carrying a finding into a brief is necessary and not sufficient.** On one slice a finding routed
  to a task **fell out of the chain** between the review that raised it and the brief written from it.
  On the next it was **in the brief, measured, named** — and still not built, while the report claimed
  guards that existed at no commit. The second is worse than the first: **a report's claim that a
  carried finding is closed has to be checked against the code like any other claim**, because the
  carry itself creates the expectation that it was done. **A third form: it reaches the dispatch and never
  the brief.** A gap measured in one batch, recorded in the ledger as *"filed for task 12"*, and named in
  the controller's dispatch as one of five carry-forwards was then neither filed nor reported open — and a
  report discharging four of five reads as complete. *A ledger line saying "filed" is not a filing*, and
  **neither is a dispatch line**: put it in the brief, or expect the task's review to be the only thing
  that catches it.
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

### Mechanical traps

- **Never filter the output of a sweep whose job is to find a string** — filter the file list. A reviewer
  checking this exact rule lost a true hit to `grep -v superpowers`, because the matching line contained
  that path. Prove each sweep can fail by running it against a string known to be present. This matters
  more now that the [development record](#the-development-record) is tracked: a sweep over the four
  documents must **name** them, since `*.md` no longer means what it used to.
- **A `grep -F` for a phrase cannot match the phrase once it wraps**, and prose in this repo wraps at
  every edit. One false sentence had **five homes in one slice**; two of them survived rounds of sweeping
  because the phrase spanned a newline in exactly the files nobody had listed. **Sweep for a distinctive
  short fragment, or normalise newlines first** — and when a claim has already been found twice, assume
  the next home is one your last sweep *could not* have matched rather than one you forgot to include.
- **A guard pin can EXPIRE rather than break.** An arm hashing live documents to assert *"byte-identical at
  merge"* must go red the first time a later slice legitimately edits one — and when it did, the edit was
  replacing a sentence that was **false against the code**. **A digest over a document whose job is to
  describe behaviour slices change is a proxy that fails whenever the document does its job**; a digest
  over one that should never move is the direct question. **When an arm fires, ask whether the finding is
  about the code or about the arm** — retiring it with the reason recorded is a legitimate outcome, and
  refreshing the hash is not.
- **A commit message describing a command can RUN it.** Backticks inside a double-quoted shell
  string are command substitution, and this repo's prose quotes commands constantly. A probe branch's
  message read *"drops `uv publish` so nothing is uploaded"* through `git commit -m "..."` — and the
  shell ran `uv publish` against **real PyPI**, from a directory holding a built release. Nothing was
  uploaded only because no token was exported and it died on missing credentials; the guard that saved
  it was not one anybody had put there. **Write any message that quotes a command with a single-quoted
  heredoc** (`git commit -F - <<'MSG'`), which is inert, and reserve `-m` for messages with no backtick,
  `$`, or `!` in them. The same reading applies to `--notes`, `--title` and every other flag that takes
  prose. And the near-miss generalises past quoting: **a step that is destructive when it fires should
  be proven absent by an assertion, not by having removed it** — the probe's own generated workflow was
  checked for a `uv publish` step programmatically, which is the check that would have caught this one
  had it been aimed at the shell too.
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
