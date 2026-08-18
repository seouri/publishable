# H4c — the unpaired contrast forms, and retiring `E-DATA-ALLOCATION-CONTRAST` — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a comparison whose two conditions differ on a declared `sweep.groups` axis stops being
refused. The delta and its interval are computed by a construction that assumes neither shared units
nor equal variances, the `method` says which, `paired: false` is **derived** rather than hard-coded,
and the record stops describing an intersection that does not exist.
`E-DATA-ALLOCATION-CONTRAST` is retired; `E-DATA-WEIGHT-ALLOCATION-CONTRAST` is minted.

**The payoff, stated as the spec's § The payoff fixes it: H4c unblocks ZERO configs.** No config in
`docs/feasibility-llm-growth-studies.md` declares a `sweep.groups` axis — all nine declare
`allocation: within` and `groups: []` — so the *no-remaining-core-side-blocker* count stays **six**
and the executable count stays **three**. Neither moves. A retired refusal is not an execution, and
the net on refusals here is **one retired, one minted** — not "a refusal narrowed", and not any
number that moves. What this slice is worth instead is a specification-integrity payoff, and it must
be argued as one: it is the gate five `spec-defects.md` filings are queued behind, it closes the
largest standing specification-versus-code gap in the statistics family, and it removes the last
hard-coded claim in the contrast record. **Nothing in the feasibility analysis gets closer to
running because H4c landed.**

**Architecture.** Four unpaired constructions, one new refusal, one new evidence kind on `Member`,
and one pairing predicate with two callers.

- **The *t* path** is a column contrast with no `statistics.resample` declared.
  `stats.welch_t_over_units(of, against)` and `stats.welch_t_over_units_clustered(of, of_labels,
  against, against_labels)` are new. Both are called from **two** places:
  `cli._comparison_step_blocks`' raw interval and `correction._corrected_bounds`' corrected one —
  and `correction.py` is a **second production call site for the contrast *t* family that no
  charter names**. `correction.py` is written **first**, exactly as H4b-1's and H4b-2's specs found.
- **The percentile path** is a column contrast under a declared `resample`, and unlike H4b-2 it is a
  **new function**. `paired_percentile_of_derived`'s whole construction is *one* draw applied to
  both sides, argued at length in its own docstring — *"would resample the two conditions apart and
  destroy the pairing"* — and § Statistical reporting defines the unpaired form as *"resampling
  within each side independently"*, which is precisely the arrangement that docstring exists to
  refuse. So the three-`method`-strings-one-function economy H4b-1 and H4b-2 built **does not extend
  here**: `stats.unpaired_percentile_of_sides` is new, and it serves its own two `method` spellings
  through its own `method=` parameter.
- **A weighted unpaired contrast is refused, not built.** `E-DATA-WEIGHT-ALLOCATION-CONTRAST` is
  minted as a documented narrow refusal carrying a § Errors row and a § Validation row, written to
  outlive this slice. **No slice inherits it as work.**
- **A derived metric's unpaired contrast is suppressed**, on a guard that reads the pairing
  derivation's own answer and names both of its grounds in one sentence. No per-side derived draw
  exists among the four constructions built here, so there is nothing to compute:
  `delta`/`method`/`ci95` all `null`, with the per-side counts beside them.
- **The record stops writing `n_paired` where it does not apply.** `n_paired` becomes **absent, not
  null**, replaced by `n_of`/`n_against`, and `n_paired_clusters` by
  `n_clusters_of`/`n_clusters_against`. **This is the first conditional write of `n_paired` in the
  codebase.**

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. No new dependency, no new module. The
changes land in `src/publishable/stats.py`, `src/publishable/contrasts.py`,
`src/publishable/correction.py`, `src/publishable/cli.py`, `src/publishable/validate.py`,
`docs/reference.md`, `docs/experimental-designs.md`, `docs/superpowers/spec-defects.md`,
`docs/feasibility-llm-growth-studies.md`, and the test modules `tests/test_stats.py`,
`tests/test_contrasts.py`, `tests/test_correction.py`, `tests/test_cli.py`,
`tests/test_validate.py`.

**Spec:** `docs/superpowers/specs/2026-08-18-unpaired-contrasts-design.md` — read it beside this
plan. **It is the binding authority and this plan argues from it.** Its § Corrections against the
code, appended by this plan's author, records the six places where the code disagreed with it.

**Measurement this plan argues from:** `docs/superpowers/H4c-SCOPING.md`, taken 2026-08-18 against
`main` at `051600c`. Every signature, guard, error code, record key, test name and file path below
was **read from the source named beside it at `e40a219`** (this branch's point), not carried from
the scoping. **Nothing is cited by line number.**

**Task count: 22**, the spec's § Task decomposition in its grain and its numbering. Task 17 has no
commit of its own — it lands in two halves inside tasks 13 and 18 — so 22 tasks make **20 commits**.

---

## Sequencing — the spec's ten ordering constraints, and where each is enforced

Presented **in execution order**, which is not numeric order. Each task states the constraint it
depends on in its own brief, because an implementer sees only their own task.

**Execution order: 1 → 2 → 3 → 21 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 (+ 17a) → 14 → 16 →
15 + 17b + 18 → 19 → 20 → 22.**

| Constraint | Why, and where it is enforced |
|---|---|
| **Task 1 before 4–12** | Decision 1 fixes whether four constructions exist or six, and with it how many arms tasks 12 and 14 have. Building first bakes the answer in by omission — H4b-1's own *5 before 7*, one axis over |
| **Tasks 2 and 3 before any code writes a key** | A record key emitted before a document names it is the pair `CLAUDE.md` says to grep for, and H4b-1's own precedent: it had to mint a whole `method` vocabulary for exactly this reason |
| **Task 2 before task 3** | § Allocation's repaired example must carry the keys task 2 mints, or the repair ships a second unreachable record |
| **Task 21 before task 4** | Its literals are captured at `e40a219` and written into its brief as literals, so the pin lands **first** and guards every task after it. A pin whose values are captured afterwards asserts the new behaviour against itself. See deviation (a) |
| **Task 4 before task 7** | `welch_t_over_units_clustered` combines two per-side dfs the same way the IID form does, and task 4 extracts the two variance helpers both rest on |
| **Task 6 before task 8** | `unpaired_percentile_over_units_clustered` is task 6's construction under a second `method=` spelling and a per-side cluster mapping, not a second function |
| **Task 9 before task 10, 13 and 18** | Task 9 **mints decision 7's shared pairing predicate** — `validate`'s new guard is its first caller and `cli`'s derivation its second. And the weighted unpaired combination must land somewhere before the refusal currently catching it is deleted. See deviation (b) |
| **Task 10 before task 13** | The key path and the record shape are one task's two halves, and taking them in the other order ships `n_paired: 0` beside `paired: false` — the exact shape decision 5 forbids. See deviation (c) |
| **Task 11 before 12 and before 14** | `_comparison_step_blocks` builds the `Member`s, so a `Member` that cannot represent an unpaired interval makes the dispatch untestable end to end |
| **Every construction before task 18** | Retiring the guard while a construction is missing routes a declared cross-arm comparison to a *paired* construction over an empty intersection, publishing `delta: null, paired: true, n_paired: 0` with `validate` reporting **zero errors**. H4b-2 hit this class for real one axis over, and only an end-to-end `run` found it |
| **Task 17's first half in task 13's commit, its second in task 18's** | Each pin fails the moment its own change lands; splitting either leaves the branch red for a reason unrelated to both |
| **Task 15's guard in task 18's commit** | `validate` gates `run` until 18, so 15 cannot be verified earlier — and landing it later leaves the retirement commit shipping an unguarded derived unpaired path. One commit, or the branch has a window. On H4b-2 the retirement commit was exactly the commit whose re-check was silently dropped, and only the whole-branch review found it |
| **Task 19 must not touch the development record** | It is evidence, not text to repair |

### Four deviations from the spec's grain, each argued

**(a) Task 21 executes fourth, not last.** The spec's constraint is *"task 21's literals captured
before task 4"*, and it is satisfiable two ways: instruct the implementer to capture at the branch
point, or capture them while the branch point **is** HEAD and write them into the brief. This plan
does the second — every literal in task 21 was captured at `e40a219` by direct calls recorded in
that task — which removes the hazard entirely and makes the pin a pure assertion task. Landing it
**before** task 4 is strictly stronger than the spec asks: the pin then guards tasks 4–20's suite
runs rather than merely reporting at the end, which is what a regression pin is for. Nothing is
dropped; the task's three pins are unchanged.

**(b) Task 9 mints decision 7's shared pairing predicate.** Decision 7 rules that the predicate is
*"ONE named function in `contrasts.py` beside `differing_axes`, called by `cli`'s derivation and by
`validate`'s new guard"*, and assigns it to **no task**. Task 9's guard executes before task 13's
derivation, so task 9 is where it is minted and task 13 is its **second** caller. `contrasts.py` is
the right home and this is stated in both briefs so nobody relocates it: `cli` imports
`publishable.validate` at module scope, so `validate` importing `cli` back is a true cycle, and
`contrasts` sits below both — `differing_axes`' own docstring already makes this argument.

**(c) Task 10 owns `is_paired`'s introduction into `_comparison_step_blocks`, the conditional record
keys and the weight bookkeeping guard; task 13 owns only the three `"paired"` literals,
`differing_axes`' docstring and pin 17a.** `H4c-SCOPING.md` § 3 measures that
`n_paired`, `n_paired_effective` and `n_paired_clusters` are **all three** computed from
`base_keys`/`col_keys` in one function, *"so the key path and the record shape are one task's two
halves, not two tasks"*. Splitting them ships `n_paired: 0` on an unpaired entry for three commits,
which decision 5 forbids by name as *"the worst-of-both this decision rejects"*. **The interim state
this leaves is stated rather than hidden**: for the three commits between tasks 10 and 13 an
unpaired entry carries `paired: true` beside `n_of`/`n_against`. That is internally odd and it is
never published — `validate` gates `run` until task 18, so the shape is reachable only by direct
call — and it is not a shape any decision forbids, where `n_paired: 0` is. **The discriminator that
makes this split safe is task 17a**: `test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch`
counts `'"paired": True'` in `_comparison_step_blocks`' source, so it is untouched by task 10 and
fails in exactly one commit — task 13's. The **weight guard** joins task 10 for a mechanical reason
stated in that brief: the `if weights is not None:` block computes `n_paired_effective` over
`col_keys`, which the unpaired arm does not bind, so without the guard task 10's own change leaves an
unbound name reachable by direct call.

**(d) Task 14 wires `cohens_ds` as well as the `method`.** The spec's task 5 builds `cohens_ds` and
**no task wires it**. Today the record computes `cohens_dz(diffs)` / `weighted_cohens_dz(diffs,
col_weights)`, and an unpaired contrast has no `diffs` at all — so a construction with no caller is
exactly the hazard the spine design flags (*"two percentile constructions built with zero production
callers"*). The `cohens_d` selection is the record's other construction-dependent field and it keys
on the **same** `is_paired` answer the `method` selection does, so it lands in the same task and the
same commit. A separate task would read the same predicate twice and could disagree with itself.

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced, because an
implementer sees only their own task brief.

**Commands.** Tests `uv run pytest` — takes about two minutes; **run it in the FOREGROUND** and wait
for it. Lint `uv run ruff check .`. Format `uv run ruff format .`. Types `uv run mypy`. All four must
pass before a commit.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this
repo wrote the bare form where it meant `--check` and rewrote 67 files. **The repo is format-clean:
`uv run ruff format --check .` reports `80 files already formatted`. Keep it that way.**

**Baseline, measured 2026-08-18 in the FOREGROUND at `e40a219`** — this branch's point, not the
scoping's `051600c`, and re-measured rather than carried:

- `uv run pytest -q` → **2200 passed, 1 skipped, 2 xfailed** in 111.55 s
- `uv run ruff format --check .` → **80 files already formatted**
- `uv run ruff check .` → **All checks passed!**
- `uv run mypy` → **Success: no issues found in 45 source files**

A task that leaves the count below its own additions has broken something. Every task states its
expected count.

**Disk is tight on this machine.** Before the first suite run, clear stale pytest temp directories:
`rm -rf /private/tmp/pytest-of-* "$TMPDIR"/pytest-of-* 2>/dev/null`. There were none at
`e40a219`; check again if a run fails on space rather than on an assertion.

**`E-DATA-ALLOCATION-CONTRAST` stays alive until task 18.** Every test written before task 18
asserts its own finding **alongside** that code, never instead of it, and **never on a total code
set** (`_error_codes(path) == {...}`) — so task 18 is a one-line deletion per test rather than a
rewrite. The pre-existing tests that *do* assert a total set are named in task 18 by test name and
are **task 18's to edit, nobody else's**.

**Tasks 4–16 test by DIRECT CALL, because `validate` gates `run`.** `cli.command_run` calls
`validate_config` and returns `EXIT_WRONG` on any error, and `E-DATA-ALLOCATION-CONTRAST` is an
error — so **no unpaired contrast reaches `_comparison_step_blocks` through `run` until task 18
retires the refusal.** Tasks 10, 13, 14 and 16 therefore call `cli._comparison_step_blocks`
directly, as `tests/test_cli.py` already does throughout its `_clustered_contrast_call` helper and
at `test_a_comparison_reads_its_own_condition_not_condition_zero`. Tasks 4–8 call `stats` directly,
tasks 11–12 `correction` directly, task 9 `validate_config` through `write_config`. **Task 18 alone
carries the `validate`-clean and `run`-through halves, and task 15 is verified inside it by an
end-to-end `run`.**

**A Welch interval that coincides with a pooled one proves NOTHING.** Equal per-side sizes make the
pooled and Welch standard errors **algebraically identical**, and near-equal variances make them
agree to several digits whatever the sizes. **Sixteen unfailable checks were found across the two
H3c slices in this repo's statistics alone.** Every fixture in this plan is sized so every candidate
reading gives a **different number**, and every task states the numbers. **No later task may
substitute a fixture that weakens § The two discriminating fixtures' four constraints.**

**Asserting `is not None` on anything unpaired is a uselessly weak discriminator.** A joint-draw
mutant routed through `paired_percentile_of_derived` returns `None` over disjoint arms — but so does
a suppressed derived contrast, a thin side, and a degenerate draw. **Every unpaired assertion needs
a positive literal or an integer count.**

**Only an end-to-end `run` exposes some corners.** On H4b-2 a Critical survived four task batches
and two direct-call pins because every probe hand-built `derived_by_key` and `resample_fns_by_key`
and so never reached the state the code branches on. **That one corner was given four wrong grounds
in four separate commits**, each an answer from a proxy rather than from the state the code branches
on, and the last of them cited a row rewritten in the same breath. Task 15 is that corner's
neighbour and inherits the discipline: **verified by `run`, never by direct call.**

**`validate` collects rather than aborting.** A refusal elsewhere never makes a later check
unreachable. **Four readers in this repo have got this wrong.** Do not infer unreachability from a
refusal; build the config and look at what `validate` *reports*, in full, as an **exact set**.

**Mutation discipline, every task.** Apply the named mutation to the file it names. Run the named
test. Confirm it **FAILS**. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert
**by editing the file back in place** — **never `git checkout -- <file>`**, which destroys
uncommitted work and has been mistaken for a revert twice in this repo. Confirm the test **PASSES**
again, and verify the revert by *behaviour*, never by `git status`. **Every mutation runs against
the full, unfiltered suite in the FOREGROUND** — H4b-1 produced a false blind-spot claim from a
self-chosen subset, and a re-reviewer who backgrounded a run stopped twice with a mutation possibly
still applied.

**A mutation is a claim too.** Before believing "this mutation must fail test X", read the *body* of
test X and check the two branches can actually produce different results. **Across the last two
slices nine mutations were claimed blind: one was overturned by a reviewer with a one-line fixture
change, one was provably unbuildable, the rest held.** This plan states, for every mutation, why its
branches differ — and it names the mutations that are **blind by arithmetic** so nobody prescribes
them later. Where a mutation cannot discriminate, the task says so and prescribes the fixture that
would. **And a mutation's silence is evidence about the TESTS, not about the code.**

**A mutation applied to a proxy proves nothing.** `t_over_units_clustered`,
`paired_t_over_units_clustered` and `paired_percentile_of_derived` are shipped and correct; breaking
any of them proves nothing about the unpaired forms. The discriminating mutation is on the **new**
construction and on the `method`-selection branch.

**A refusal that happens to fire must be attributed before it is counted.** `allocation: within`
beside a `groups` axis earns `E-DATA-ALLOCATION-WITHIN-ARMS`, and a `groups` axis with no `assign`
earns `E-DATA-ALLOCATION-NO-ARMS`. Neither is H4c's — they refuse a *declaration* a correct unpaired
config does not make. A fixture forgetting either attributes its refusal to the wrong code.
`tests/test_validate.py`'s `_groups_cluster_doc` / `_groups_cluster_csv` helpers are a real
`between` + `by_attribute` + `cluster_by` fixture that validates clean with no comparison, and they
are the ready-made shape for tasks 9 and 18.

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "Statistical reporting"), **never by line number**. **No positional locators**
("the row above", "further up"): name what a sibling row *does*, and when you insert or remove a row
check every row it **moved** and every count phrase near it. **No counts in prose or comments** and
**no call-site enumerations**: state what a set *is*. **A build fact is dated and pinned to a commit
where it is true.** **Prefer deleting a claim to rewriting it** — a rewrite invents, a deletion
cannot; on H4b-2 rewriting re-seeded a claim three times, once inside a correction that manufactured
a defect the original did not have. **When you edit a docstring, re-read the whole one.**

**Sweeps.** **Never filter the output of a sweep whose job is to find a string — filter the FILE
LIST**, and prove each sweep can fail by running it against a string known to be present. Name the
four documents explicitly, since the development record is tracked and `*.md` no longer means what
it used to. **Enumerate by READING where a thing can happen, then confirm with greps** — the
reverse order shipped a credential leak in H7c, sited by grepping for one spelling. And **read for
the claim, not for the wording**: on H4b-2 a deleted claim returned as a paraphrase no literal
search matched.

**`n_of` cannot be swept as a bare word.** `grep -rn 'n_of' src/ docs/ tests/` returns dozens of
hits, **none of them a bare `n_of`** — they are `n_of_m`, `n_off` and test-name fragments. The
greppable form is `n_of:` (0 hits at `6a1ece1`), against a can-fail control of `n_paired:` → 8.

**§ Errors carries one row per code, covering every emit site** — not one row per site. A
diagnostic's unit of work is every site that raises *or* reports it. `E-DATA-ALLOCATION-CONTRAST`
has **one** emit and `W-STATS-CONTRAST-THIN` has **two** — one at `validate` and one at `run` — and
task 16 owns both.

**The four normative documents LEAD; `src/` follows.** `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`. Where they and the code disagree, **the
document changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. The
cross-document pass governs those four **only** — never the development record under
`docs/superpowers/`, where a correction is **appended** rather than retro-edited.
`spec-defects.md` is the one exception: a closed gap is **struck** there rather than left to
mislead. **`H4c-SCOPING.md`, both H4b specs, the H4b ledgers and this slice's own spec must not be
retro-edited** — a correction to the spec goes in its § Corrections against the code, appended by
this plan and extended by no task.

**Do not touch the worked example.** `cohort-pilot` declares no group axis, so no unpaired key
belongs in § The two files' `run.yaml`, in § Statistical reporting's fenced `results:` block, or in
any of the worked example's intervals — which `CLAUDE.md` § The worked example says were checked
numerically and **must not be narrowed back**. Task 3 repairs an example that sits *in* worked-example
vocabulary: it **carries that block's existing `delta` and `ci95` unchanged** and invents only the
two per-side counts, whose sum is held to the worked example's own 228 completed units.

**§ The one config file's declaration count must not move.** It reads *"**One** declaration above is
not yet built"* — `statistics.null_test`, H4d's. Retiring or minting a *combination* refusal is not
retiring or adding a declaration, and `_check_sweep`'s own comment makes that placement argument for
both of its existing codes. Likewise **no row moves in any `Status`-carrying table**:
`tests/test_cli.py` asserts set equality between the document's `NOT BUILT` command rows and
`cli.NOT_BUILT_COMMANDS`.

**`tests/conftest.py` already has** an autouse `os.environ` restore, an opt-in `registries` fixture
and an opt-in `installed` distribution fixture. **Do not add duplicates, and do not add a second
autouse fixture of any kind.** No task in this slice needs `registries` or `installed`.

---

## The two discriminating fixtures, stated once because eleven tasks share them

**The spec records that its own first draft was UNFAILABLE** — a `min(n) − 1` df mutant landed
0.1 % from correct because one side dominated the Welch variance — and was rebalanced to n = 5 / 25
with s²/n = 1 on each side, so both fixtures now separate every candidate by **more than 4 %**.
**No later task may weaken that.** Every literal below was recomputed against the shipped
`stats._t_critical` at `e40a219` and reproduced the spec's tables exactly.

**The four constraints a substitute fixture must meet:**

1. **Unequal per-side sizes**, or pooled and Welch coincide algebraically.
2. **Unequal per-side variances**, arranged so *both* sides contribute comparably to the Welch
   variance — otherwise the Welch df collapses onto one side's own df and a `min(n) − 1` mutant
   hides. This is the constraint the spec's first draft broke.
3. **Non-singleton clusters, unequal in size, and differing in count between the two sides.**
4. **Values constant within a cluster**, so the within-side variance is entirely between-cluster and
   CR1 cannot approximate the IID form.

### Fixture A — the IID unpaired contrast

`of` is **5 units**, `[17, 19, 20, 21, 23]` — mean **20**, s² **5**, s²/n **1**.
`against` is **25 units**, twelve at `5`, twelve at `15`, one at `10` — mean **10**, s² **25**,
s²/n **1**. **Delta = 10.** Welch SE = √2 = `1.4142135623730951`; Welch-Satterthwaite df = 96/7 =
`13.714285714285714`.

**The single unit *at* the mean is deliberate, not padding.** It contributes zero to the variance, so
the side's **count and its variance are independently mutable** — an off-by-one dropping it leaves
s² at 25 while moving n to 24, which shifts the df and the half-width by ~0.5 %. Small, but a
literal assertion still catches it, where a fixture with no such unit would let a count mutation
hide inside a variance change.

| What computes it | Half-width | Ratio to correct |
|---|---|---|
| **Correct** — Welch variance, Welch-Satterthwaite df | **3.039125537798091** | 1.0000 |
| Mutant: pooled variance, df = `n_of + n_against − 2` = 28 | 4.722138614325821 | 1.5538 |
| Mutant: Welch variance, df = `min(n) − 1` = 4 | 3.9264863229551143 | 1.2920 |
| Mutant: Welch variance, df = `max(n) − 1` = 24 | 2.918793337216675 | 0.9604 |
| Mutant: Welch variance, df = `n_of + n_against − 2` = 28 | 2.8968851611887434 | 0.9532 |
| `paired_t_over_units` over two disjoint arms | `None` — the intersection is empty | — |

**Five distinct numbers, the tightest 4.7 % from the correct one**, which no rounding produces. Two
qualifications, stated so nobody over-claims: the last two mutants sit **0.75 % apart from each
other**, so a literal assertion catches both but cannot say which fired; and the paired mutant
returns `None`, which is never sufficient on its own.

**`cohens_ds` is separately assertable, and it pins a documented asymmetry nothing else does.** The
pooled sd is `4.705619740571601`, so *d*s = **2.1251185925162073**, while a mutant standardizing by
the interval's own Welch denominator (`1.4142…`) gives **7.0710678118654755** — a factor of 3.33.
§ Statistical reporting states that asymmetry deliberately — *"*d*s pools where `welch_t_over_units`
deliberately doesn't, and that isn't an inconsistency"* — and this is the assertion that makes it
more than a sentence.

### Fixture B — the clustered unpaired contrast

`of` is **9 units in 3 clusters** of sizes 2, 3, 4, constant within cluster at `0`, `15`, `30` —
mean `18.333333333333332`. `against` is **12 units in 4 clusters** of sizes 2, 3, 3, 4, constant
within cluster at `2`, `4`, `6`, `8` — mean `5.5`. **Delta = 12.833333333333332.** Per-side CR1
variances `67.07818930041152` (G = 3) and `1.5879629629629628` (G = 4), SE `8.286504224543332`,
Welch-Satterthwaite df over `G_s − 1` = `2.0950313633473936`.

| What computes it | Half-width | Ratio to correct |
|---|---|---|
| **Correct** — CR1 per side, df combined over `G_s` − 1 | **34.14810237373095** | 1.0000 |
| Mutant: `min(G) − 1` = 2, equivalently `G_of − 1` | 35.653950021811816 | 1.0441 |
| Mutant: `G_against − 1` = 3 | 26.371354753115764 | 0.7723 |
| Mutant: `G_total − 2` = 5, the pooled reading | 21.301137240534675 | 0.6238 |
| Mutant: CR1 meat, df = `n_of + n_against − 2` = 19 | 17.343852668925262 | 0.5079 |
| The IID Welch form on the identical data (df `8.399133841827005`) | 9.647234756296374 | 0.2825 |

**Six distinct answers, and the correct one is not the extreme of any single dimension** — 35.65
sits above it — so an assertion on the number discriminates every failure mode, which an assertion
on "is it wider" does not. The tightest separation is 4.4 %.

**The two integer cluster counts are the strongest discriminator on this fixture and must be
asserted alongside the half-width.** `n_clusters_of: 3` and `n_clusters_against: 4` are integers
that cannot coincide, so a construction reading one side's count, or a pooled count of 7, writes a
wrong **integer** into `run.yaml` even where a float assertion might be argued about. This is the
documented *"a cluster fixture where correct and buggy cluster counts were both 3"* failure, closed
by construction.

### The percentile forms, and the corrected bounds

**The percentile discriminator is the per-replicate draw size, and it must be asserted rather than
inferred from the interval.** An independent per-side draw takes **exactly 5 rows and exactly 25
rows, every replicate** on fixture A — a mutant drawing once from the pooled 30 and splitting, or
drawing `min(n)` for both, returns different sizes. On fixture B the cluster sizes 2/3/4 and 2/3/3/4
make the `of`-side row count **vary between 6 and 12 across replicates** while a unit-drawing mutant
returns a fixed 9. **This only works if the construction admits an observable**, so task 6 builds
its tests around a compute closure that appends `len(table)` per replicate and asserts the set of
row counts.

**No percentile half-width literals are stated here**: the constructions do not exist yet, so a
literal would be invented rather than computed, which is the failure `CLAUDE.md` names for a
regression pin captured after the change. Each percentile task captures its own endpoints from its
first green run and writes them in as literals in the same commit.

**The corrected bound is pinned by its ratio at the entry's own df, not by a field being threaded.**
A corrected half-width must equal the raw one times `t(df, 1 − level) / t(df, 0.95)` **at the same
df** — so at Bonferroni over a family of 2 that ratio is `1.1706821500146336` on fixture A (df
13.714286) and `1.4227764722656022` on fixture B (df 2.095031). **The two differ by 21 %, which is
the point**: a corrected bound built at an unpaired-IID df, at a paired df, or at the unclustered df
produces a visibly different ratio. Both ratios were recomputed at `e40a219`.

---

## Identifiers, record keys and rows this slice touches

| Name | What it is | State at `e40a219` | Task |
|---|---|---|---|
| `stats.welch_t_over_units` | function and `method` string | **absent from `src/`**; has a § Statistical reporting row already | 4 |
| `stats.cohens_ds` | function | **absent** — `stats.py` has `cohens_dz` and `weighted_cohens_dz` only | 5 (built), 14 (wired) |
| `stats.unpaired_percentile_of_sides` | function, serving two `method` strings | **absent** | 6, 8 |
| `unpaired_percentile_over_units` | `method` string | **absent from `src/`**; has a § Statistical reporting row already | 6 |
| `stats.welch_t_over_units_clustered` | function and `method` string | **absent**; licensed by the `_clustered` suffix rule, no row | 7 |
| `unpaired_percentile_over_units_clustered` | `method` string only | **absent**; licensed by the same suffix rule, no row | 8 |
| `stats._sample_variance`, `stats._cr1_variance` | private helpers, extracted | **absent** — the CR1 machinery is inlined in `t_over_units_clustered` and returns an `Interval` | 4, 7 |
| `stats.unpaired_keys` | function | **absent**; `paired_keys` returns the sorted intersection | 10 |
| `contrasts.crossed_group_axes` | the shared pairing predicate | **absent** — the expression is inlined in `validate._check_sweep` | 9 (minted), 10 and 13 (callers) |
| `correction.UnpairedEvidence` | frozen dataclass | **absent** | 11 |
| `correction.Member.sides` | field | **absent**; `Member` is `pool` XOR `diffs` with `weights`/`clusters` as modifiers on `diffs` | 11 |
| `n_of`, `n_against` | record keys on a contrast entry | **minted here**; `n_of:` is free | 2 (documented), 10 (emitted) |
| `n_clusters_of`, `n_clusters_against` | record keys on a contrast entry | **minted here**; both free | 2 (documented), 10 (emitted) |
| `n_paired`, `n_paired_clusters` | record keys | written **unconditionally** today; become **absent** on an unpaired entry | 2 (narrowed), 10 (conditional) |
| `E-DATA-WEIGHT-ALLOCATION-CONTRAST` | refusal | **free at `6a1ece1`** — re-proved in task 1 | 1 (ruled), 9 (minted) |
| `E-DATA-ALLOCATION-CONTRAST` | refusal | 1 emit + a 40-line guard comment + `_check_assign`'s docstring + `_check_unimplemented`'s comment + `E-SWEEP-BASELINE-GROUP`'s guard comment and emitted message + `_comparison_step_blocks`' docstring + `differing_axes`' docstring + a § Validation row + a § Errors row + `E-SWEEP-BASELINE-GROUP`'s own § Errors row + § Expansion modes' control-arm paragraph + `experimental-designs.md` § Mistakes core prevents + one feasibility refusal row and one table row + `tests/test_validate.py` and `tests/test_cli.py` assertion and docstring lines | 18 (retired), 19 (residue) |

**No new `method` table rows.** § Statistical reporting's suffix sentence is generic over the whole
contrast table — *"each of the **unweighted** forms above takes a `_clustered` suffix"* — so both
new clustered spellings are **already licensed**, and `efa13bc` repaired the opposite mistake by
narrowing a quantifier rather than enumerating. **Ruled explicitly in task 1, so no later task
helpfully adds them:** the two clustered forms get no rows of their own, and the weighted unpaired
pair gets **no spelling at all**.

---
## Task 1: rule the vocabulary and the df-combination rule, and prove the identifier free

**Runs first.** Decision 1 gates decisions 2, 3 and 5: refusing the weighted unpaired pair is what
makes `Member`'s `weights` modifier a *"never beside `sides`"* assertion rather than a fourth
construction to align, what keeps the § Statistical reporting weighted rows narrowable rather than
doubled, and what leaves `n_paired_effective` with no unpaired counterpart to invent. **Building
first bakes the answer in by omission.**

**Files:**
- Modify: `docs/reference.md`
- Modify: `docs/superpowers/spec-defects.md`

**Interfaces:**
- Consumes: `reference.md` § Statistical reporting's contrast table, whose `welch_t_over_units` row
  reads *"Welch's *t* on two independent condition means, df from Welch-Satterthwaite"* and whose
  `unpaired_percentile_over_units` row reads *"The percentiles of the difference, resampling within
  each side independently"*; the `_clustered` suffix sentence beginning *"When `cluster_by` is
  declared, each of the **unweighted** forms above takes a `_clustered` suffix"*; the paragraph
  beginning *"A weighted contrast weights a recorded column and not a derived metric"*, whose last
  sentence already refuses the weight × cluster composition by name.
- Produces: the ruling every construction task depends on — **four constructions built, two
  refused** — and the df-combination clause task 7 emits against. No code.

**The four rulings, recorded in this task's commit message and in `spec-defects.md`:**

1. **`welch_t_over_units` and `unpaired_percentile_over_units` already have rows.** Confirm them
   unchanged. They are the spellings tasks 4 and 6 emit.
2. **`welch_t_over_units_clustered` and `unpaired_percentile_over_units_clustered` get NO rows of
   their own.** They are licensed by the suffix rule. This is H4b-2's decision 5 verbatim: adding
   rows converts a self-maintaining rule into a maintenance obligation nobody owns. **Ruled
   explicitly, in writing, because without it a later task will helpfully enumerate them.**
3. **The weighted unpaired pair gets no spelling at all.** `weighted_welch_t_over_units` and
   `weighted_unpaired_percentile_over_units` are **refused** by
   `E-DATA-WEIGHT-ALLOCATION-CONTRAST`, minted in task 9 as a **standing** narrow refusal. An
   alternation grep for both stems over `src/`, `docs/` and `tests/` returned **zero** at
   `051600c`, so refusing it removes nothing and mints over vapour.
4. **The df of an unpaired clustered *t* is Welch-Satterthwaite over the two cluster-robust per-side
   variances, each side contributing df = `G_s` − 1.** The two rejected readings, named so nobody
   re-derives them: `min(G_of, G_against) − 1` discards a side's information and contradicts
   "df = clusters − 1" on the side it discards; `G_total − 2` is the **pooled** reading the
   `welch_t_over_units` row refuses by construction.

- [ ] **Step 1: prove the identifier free, with a control that can fail.** Run each of these and
      record the output in the task report:

```bash
grep -rn 'E-DATA-WEIGHT-ALLOCATION-CONTRAST' src/ docs/reference.md docs/design-principles.md \
  docs/experimental-designs.md README.md tests/
grep -rn 'weighted_welch\|weighted_unpaired' src/ docs/ tests/
grep -rn 'welch_t_over_units_clustered\|unpaired_percentile_over_units_clustered' src/ tests/
grep -rn 'cohens_ds' src/ tests/
grep -rn 'n_of:\|n_against\|n_clusters_of\|n_clusters_against' src/ docs/reference.md tests/
# the can-fail control: the same sweep shape over a string that IS present
grep -rc 'E-DATA-WEIGHT-CLUSTER-CONTRAST' src/publishable/validate.py docs/reference.md
grep -rc 'n_paired:' docs/reference.md
```

      Every sweep in the first block must return nothing (`exit 1`); the two controls must return
      hits. **Filter the FILE LIST, never the output** — a reviewer checking this exact rule once
      lost a true hit to `grep -v superpowers`. `docs/superpowers/` is excluded because it is
      evidence, not text to repair. **If any first-block sweep returns a hit, stop and report it**:
      a spelling that already exists changes decision 1 and this task does not get to decide that
      alone.

- [ ] **Step 2: narrow the two `weighted_paired_*` rows' applicability clauses.** In
      `docs/reference.md` § Statistical reporting, the contrast table. **The rows' constructions are
      already about the paired form by name; what over-claims is each row's last clause**, which
      says when the row applies. Edit only those clauses:

      - `weighted_paired_t_over_units`: `A column metric under `weight_by`, when no `resample` is
        declared` → `A **paired** column metric under `weight_by`, when no `resample` is declared`
      - `weighted_paired_percentile_over_units`: `A column metric under `weight_by` and a declared
        `resample`` → `A **paired** column metric under `weight_by` and a declared `resample``

      That is a two-word insertion each, and it is the quantifier-narrowing H4b-2's batch-1 review
      applied to *"Every clustered contrast…"* rather than the enumeration it could have been.

- [ ] **Step 3: add the composition refusal sentence beside its sibling.** In the paragraph
      beginning *"A weighted contrast weights a recorded column and not a derived metric"*, whose
      final sentence already reads *"The `_clustered` suffix does not compose with either weighted
      form: `E-DATA-WEIGHT-CLUSTER-CONTRAST` refuses a design declaring both beside a comparison,
      because a weighted clustered interval takes its df from the cluster count rather than from
      Kish's effective size and the two coincide too often to leave the choice implicit."* — append
      exactly one sentence after it:

```
Neither weighted form has an unpaired counterpart: [`E-DATA-WEIGHT-ALLOCATION-CONTRAST`](#errors-validate-reports) refuses a design declaring `weight_by` beside a comparison whose two conditions differ on a group axis, because a Welch *t* on two weighted means needs Kish's effective size **per side** — two df inputs where the paired form needed one, on the dimension where a wrong choice hides best.
```

      **The ground is standing, not build-hedged.** No form of *"until the estimators exist"*
      appears in it, and `CLAUDE.md` § Misreadings is why: a `-UNSUPPORTED` suffix is the
      undocumented build family, retired wholesale, while a *narrow* refusal of a combination is
      documented, carries rows, and outlives the slice that minted it. **The sentence ships in this
      task and the guard in task 9** — a sentence and a guard are one claim seen from two ends, and
      the eight commits between them are a window in which the document describes a refusal core
      does not make. That is deliberate and it is the lesser of the two: the alternative is a code
      emitting a message no document licenses, which is the pair `CLAUDE.md` says to grep for. Task
      9's brief carries the § Errors and § Validation rows that complete it.

- [ ] **Step 4: add the df-combination clause, scoped to the *t* forms alone.** In the same section,
      the `_clustered` suffix sentence. Insert the clause after *"over the differenced values when
      paired and over the arm-level ones when not"* and **before** the percentile clause, so it sits
      inside the *t* half of the sentence:

```
When the two sides are unpaired the *t* form's df is Welch-Satterthwaite over the two cluster-robust per-side variances, each side contributing `G_s` − 1 — the substitution the suffix rule describes happens inside each side's own variance and its own df, and combining them is what the unclustered Welch form already does.
```

      **Scoped to the *t* forms alone, and this is the whole point of adding it.** A df provenance
      generalized over the percentile form is the exact false claim H4b-2's batch-1 Major 1 deleted
      and its batch-3 Major 1 then re-seeded at three more sites — one of them a paraphrase no
      literal grep could find. **The clause needs a tripwire, and task 22's sweep is it**: task 22
      **re-reads** the percentile constructions' comments and docstrings for the same claim rather
      than grepping for this clause's wording.

- [ ] **Step 5: record the ruling in `spec-defects.md`.** Append a `## RULED by H4c task 1` section
      carrying all four rulings above, the sweep outputs from Step 1 with their controls, and the
      sentence *"No slice inherits `E-DATA-WEIGHT-ALLOCATION-CONTRAST` as work"* —
      `E-DATA-WEIGHT-CLUSTER-CONTRAST` is the precedent, a narrow refusal nobody owns retiring, and
      writing it as a deferral instead is how an entry comes to read as live work nobody holds.
      **Do not strike or amend any existing entry here** — task 20 owns the five filings.

- [ ] **Step 6: run the mechanical pass** over the two files edited: every relative link and
      `#anchor` resolves, no two headings in a file share an anchor, every table row matches its
      header's column count and none is empty, no trailing whitespace, tab or invisible unicode,
      `×` not `x` — **skipping fenced code blocks in all of them**, since the docs contain markdown
      inside markdown. Confirm `#errors-validate-reports` resolves.

- [ ] **Step 7: run the gates.** `uv run pytest` → **2200 passed**, 1 skipped, 2 xfailed
      (documents only; no test count moves). Then `uv run ruff check .`,
      `uv run ruff format --check .` (80 files), `uv run mypy`.

      **There is one test that reads these tables and it must stay green:**
      `tests/test_cli.py::test_a_clustered_contrast_method_is_one_the_document_defines` parses both
      construction tables through `_interval_method_names()` and asserts a stem is present while
      `f"{stem}_clustered"` is **not** a row. Adding a clustered row in Step 2 or 4 would break it —
      which is the mechanical half of ruling 2, and worth knowing about before editing rather than
      after.

- [ ] **Step 8: no mutation.** This task ships no behaviour, and a mutation on a document is a claim
      about a grep rather than about the code. **The tripwire that makes ruling 2 enforceable is the
      test named in Step 7**, and the tripwire for ruling 4 is task 22's re-read. Both are named
      here so this task's report does not claim a pin it does not have.

- [ ] **Step 9: Commit.**

```bash
git add docs/reference.md docs/superpowers/spec-defects.md
git commit -m "docs: H4c's method vocabulary ruled — four built, the weighted unpaired pair refused, and the unpaired clustered df given a rule"
```

---

## Task 2: document the unpaired record shape in § Contrasts and § Validation

**Runs after task 1**, whose ruling removed `n_paired_effective`'s unpaired counterpart from the
design space. **Before any code writes a key** — a record key emitted before a document names it is
the pair `CLAUDE.md` says to grep for, and H4b-1 had to mint a whole `method` vocabulary for exactly
this reason.

**Files:**
- Modify: `docs/reference.md`

**Interfaces:**
- Consumes: § Contrasts' sentence *"**`n_paired` is the intersection, and it has to be recorded.**"*
  and its closing *"A contrast whose intersection is empty is reported as such rather than as a delta
  of zero"*; the `n_paired_effective` paragraph's *"this record deliberately has no `n`"* argument;
  the `n_paired_clusters` paragraph's *"a **scalar sibling of `n_paired`**"* argument; § Validation's
  `W-STATS-CONTRAST-THIN` row, which names **two** points — at `validate` and at `run`, *"when the
  comparison's realized `n_paired` is below it"*; § Contrasts' *"`limits.min_reported_n` applies to a
  `within` contrast's `n_paired`"*.
- Produces: four documented record keys — `n_of`, `n_against`, `n_clusters_of`,
  `n_clusters_against` — the narrowed quantifier on `n_paired`, the per-side reading of
  `limits.min_reported_n` and `W-STATS-CONTRAST-THIN`, and the documented suppression of an unpaired
  **derived** contrast. Tasks 10, 14, 15 and 16 emit against these.

**Why absent and not null, stated in the document rather than only here.** § Contrasts already spends
`0` on a different meaning — *"A contrast whose intersection is empty is reported as such rather than
as a delta of zero"* — so writing `n_paired: 0` on an unpaired entry would make one number mean both
*a pairing that failed* (a defect to report) and *a design where pairing is not the concept* (nothing
wrong at all). **Absent, not null**, is the shape `weighted_by`, `n_paired_effective` and
`n_paired_clusters` already use.

**Two scalar siblings, never an `n` mapping**, on the standing argument § Contrasts makes twice:
*"this record deliberately has no `n` mapping to join"*. `n_of`/`n_against` mirror the entry's own
`of:`/`against:` keys.

- [ ] **Step 1: narrow `n_paired`'s quantifier.** Change the sentence *"**`n_paired` is the
      intersection, and it has to be recorded.**"* to *"**`n_paired` is the intersection, and a
      paired contrast has to record it.**"* — the same quantifier-narrowing H4b-2's batch-1 review
      applied rather than the enumeration it could have been. Leave the rest of that paragraph
      untouched: every clause in it is about a paired comparison already.

- [ ] **Step 2: add the unpaired record paragraph and its fenced example**, immediately after the
      `n_paired_clusters` paragraph and its fenced block, so the three modifier paragraphs stay
      together. Write:

```
**An unpaired contrast records no `n_paired` at all, and two scalar siblings in its place.** Its intersection is [empty by construction](#allocation-within-subjects-or-between-subjects) — that is what a group axis means — so `n_paired: 0` would be arithmetically true and descriptively false, and it would spend on a design where pairing is not the concept the same `0` this section already spends on a pairing that failed. `n_paired` is therefore **absent — not null** — and `n_of` and `n_against` carry the two sides' completed counts, mirroring the entry's own `of:`/`against:` keys. Under [`cluster_by`](#clustered-units) `n_paired_clusters` is absent for the same reason and `n_clusters_of`/`n_clusters_against` replace it: a cluster count is per side once the sides are disjoint, and Welch's df reads both. There is no unpaired counterpart to `n_paired_effective`, because [`E-DATA-WEIGHT-ALLOCATION-CONTRAST`](#errors-validate-reports) refuses the only composition that would produce one.

```yaml
results:
  contrasts:
    - id: arm_effect
      of: 02_arm=treatment
      against: 01_arm=control
      step03_screen:
        prob: {delta: 0.041, basis: units, paired: false,
               method: welch_t_over_units_clustered,
               n_of: 116, n_against: 112,
               n_clusters_of: 9, n_clusters_against: 8,
               ci95: [0.002, 0.080], cohens_d: 0.31,
               correction: holm, correction_level: 0.0125,
               family_size: 4, family: {comparisons: 2, metrics: 2}}
```

The interval, the `method` and the two counts move together, the same obligation a weighted or a clustered entry carries: a delta whose interval assumes neither shared units nor equal variances, beside a `method` that does not say so, or beside no per-side counts at all, is a design honoured whose record is half delivered. `cohens_d` here is *d*s, over the pooled within-condition standard deviation, which is [§ Statistical reporting](#statistical-reporting)'s own split.
```

      **`prob` and `step03_screen` are deliberate**, matching the three existing § Contrasts examples
      rather than the worked example's derived `r`: `cohens_d` is reported only for a per-unit mean,
      and a derived metric's unpaired contrast is suppressed by Step 4 below. Every number here is
      new and none collides with a pin — `CLAUDE.md` § The worked example governs `cohort-pilot`, and
      these examples are § Contrasts' own `arm_sensitivity`/`site_sensitivity` family.

- [ ] **Step 3: restate `limits.min_reported_n` per side.** Change § Contrasts'
      *"`limits.min_reported_n` applies to a `within` contrast's `n_paired`, since a stratified
      paired comparison is where a small denominator is easiest to miss and most disclosive."* to:

```
`limits.min_reported_n` applies to a `within` contrast's realized denominator — `n_paired` where the contrast is paired, and `n_of` and `n_against` separately where it is not, warning where **either** side is below the floor. A stratified comparison is where a small denominator is easiest to miss and most disclosive, and the disclosive quantity is a thin denominator anywhere: a five-unit arm compared against a five-hundred-unit one is exactly what the limit exists to catch, and a rule reading only one side or only a total would pass it.
```

      **The reason is preserved rather than replaced.** § Contrasts grounds the row in *"a stratified
      paired comparison is where a small denominator is easiest to miss and most disclosive"*, and
      firing on either side is the reading that keeps that reason true.

- [ ] **Step 4: document the unpaired derived suppression.** § Contrasts' `n_paired_clusters`
      paragraph already documents the sibling case — *"A **derived** metric whose key collides with a
      recorded column's is decided: `_comparison_step_blocks` reads the declared `cluster_by` and
      suppresses the contrast over that key"*. Append one sentence to the paragraph added in Step 2:

```
A **derived** metric's unpaired contrast is suppressed on the same shape and for a second, independent reason: no per-side draw exists for a recomputed metric, so `delta`, `method` and `ci95` are all `null` with the per-side counts beside them, exactly as [`E-DATA-CLUSTER-DERIVED`](#errors-core-raises) describes for a declared cluster.
```

      **This sentence is why task 15 has a document to honour.** Without it, code would publish a
      suppression no document names, which is the same pair Step 2 exists to avoid one key over. Note
      what it does **not** say: it does not claim one ground covers the other. Task 15's guard names
      both, and a later reader taking one as covering the other is the *fourth* wrong ground that
      corner was already given.

- [ ] **Step 5: run the mechanical pass** over `docs/reference.md`, as task 1's Step 6 specifies.
      Confirm `#errors-core-raises`, `#errors-validate-reports`,
      `#allocation-within-subjects-or-between-subjects`, `#clustered-units` and
      `#statistical-reporting` all resolve. **The new fenced block is skipped by every check** — it
      contains `|`-free YAML but the rule applies regardless.

- [ ] **Step 6: run the cross-document pass.** The classes that actually drift, checked by name:
      **Config completeness** — no config field is added, so § The one config file does not move.
      **Schema fields in prose** — the four new keys are named in prose *and* appear in the fenced
      `run.yaml`-shaped example, both directions satisfied. **Declared vs. derived** — `paired` is
      derived, and nothing added here shows it as settable. **Prevented mistakes** — nothing moves in
      `experimental-designs.md` § Mistakes core prevents (task 19 owns its one sentence). **The
      shared worked example** — untouched, and Step 2's note says why.

- [ ] **Step 7: run the gates.** `uv run pytest` → **2200 passed**, 1 skipped, 2 xfailed. Then the
      other three.

- [ ] **Step 8: no mutation** — documents only. The tripwire is task 10, which emits these four keys
      and fails if they are not what this task wrote.

- [ ] **Step 9: Commit.**

```bash
git add docs/reference.md
git commit -m "docs: the unpaired contrast record — n_of/n_against, per-side cluster counts, and n_paired narrowed to paired contrasts"
```

---

## Task 3: re-author § Allocation's unreachable `vs_baseline` example

**Runs after task 2**, whose keys this example must carry — or the repair ships a second unreachable
record.

**Files:**
- Modify: `docs/reference.md`

**Interfaces:**
- Consumes: task 2's `n_of`/`n_against`; § Allocation's fenced `vs_baseline:` block carrying
  `# 03_arm=treatment__method=spearman`, `paired: false`, `confounded: true` and
  `method: unpaired_percentile_over_units`; the paragraph above it ending *"Each contrast records its
  own `paired: true|false` in `vs_baseline`."*; the paragraph below it ending *"Fixing a value on
  every axis is the other coherent choice, and it's the one that produces contrasts like the
  above."*; § Errors' `E-DATA-ALLOCATION-CONTRAST` row, which already states the `vs_baseline`
  interaction **correctly**.
- Produces: a reachable example of an unpaired contrast record. No code.

**Why this is a repair rather than a decision, and the measurement that closes the second branch.**
`H4c-SCOPING.md` § 4 probed both branches, exact error sets at `051600c`: a `groups` axis + `grid`
with a baseline fixing `arm: control` earns
`{E-DATA-ALLOCATION-CONTRAST, E-DATA-ALLOCATION-WITHIN-ARMS, E-SWEEP-BASELINE-GROUP}`, and the same
design with a baseline fixing `analysis.method` only earns `{E-DATA-ALLOCATION-WITHIN-ARMS}` — **no
cross-arm comparison exists at all**, because a parameter-only baseline **expands over the group
axis** and gives each arm its own reference. So the first shape is the only generated route to a
cross-arm `vs_baseline` entry and it also earns `E-SWEEP-BASELINE-GROUP`, **which H4c does not
lift** — it refuses a declaration on the peers rule, grounded in § Expansion modes and in
`experimental-designs.md` § Mistakes core prevents' *two identical measurements reported as two
arms*, a structural impossibility rather than a temporary gap. **So after H4c `vs_baseline` still
never carries an unpaired entry, and the whole reachable surface is a declared `statistics.contrasts`
entry.** The § Errors row is right and the example contradicts it.

**Three sites, and the enumeration is the task.** A sweep that stops at the fenced block is the
*"sweep for the claim, not the file the claim was first noticed in"* failure, which happened three
times in one slice.

- [ ] **Step 1: re-author the fenced block** as a `results.contrasts` entry. Replace it with:

```yaml
results:
  contrasts:
    - id: arm_and_method
      of: 03_arm=treatment__method=spearman
      against: 01_arm=control__method=pearson
      step03_analyze:
        abs_error: {delta: 0.041, basis: units, paired: false, confounded: true,
                    method: unpaired_percentile_over_units,
                    differs_on: [arm, analysis.method],   # two axes at once — not a main effect
                    n_of: 116, n_against: 112,
                    ci95: [0.012, 0.070]}
```

      **Three changes and nothing else.** The `# 03_arm=treatment__method=spearman` comment — the
      thing that made it a `vs_baseline` record — becomes the entry's own `of:`, with an `against:`
      naming the other corner. `r` becomes `abs_error`, the worked example's **recorded column**,
      because `r` is derived by `aggregate(units)` and a derived metric's unpaired contrast is
      suppressed by task 2's Step 4 — showing a derived metric with a real `delta` and `ci95` here
      would ship a record the suppression rule forbids, and this is the one change the spec's task 3
      does not name. `n_of`/`n_against` join, and **their sum is 228**, the worked example's own
      completed count, so the two invented integers are consistent with the pinned arithmetic rather
      than free.

      **`delta: 0.041` and `ci95: [0.012, 0.070]` carry over unchanged**, and `differs_on` and
      `confounded: true` stay: this block illustrates the confounded row of the pairing table, which
      is why it exists, and inventing new numbers here is how a repair collides with a pin.
      **`cohens_d` is deliberately absent**, matching the § Contrasts entry that carries none —
      adding one would be inventing a number this task has no source for.

- [ ] **Step 2: repair the sentence above it, by deletion.** *"Each contrast records its own
      `paired: true|false` in `vs_baseline`."* → *"Each contrast records its own `paired:
      true|false`."* **A deletion, not a rewrite**: the boolean claim is true of both record shapes
      and only the location clause was false. A rewrite invents; a deletion cannot.

- [ ] **Step 3: repair the sentence below it, by re-grounding.** *"Fixing a value on every axis is
      the other coherent choice, and it's the one that produces contrasts like the above —
      interpretable on the single-axis ones, marked on the rest."* → replace the clause that is
      false, keeping the paragraph's point:

```
Fixing a value on every axis is the other coherent choice: one reference for the whole run, interpretable on the single-axis contrasts and marked on the rest. It does not produce the record above — where the value it fixes is a level of a group axis, [`E-SWEEP-BASELINE-GROUP`](#errors-validate-reports) refuses it outright on the peers rule, and where it fixes parameter axes only the baseline expands over the group axis anyway, so every generated comparison stays within an arm. A cross-arm record is a declared [`statistics.contrasts`](#contrasts-claims-that-arent-condition-vs-baseline) entry, which is what the block above is.
```

- [ ] **Step 4: sweep for a fourth site, by claim rather than by wording.** The three sites above
      were enumerated by reading § Allocation in full. Confirm with:

```bash
grep -n 'vs_baseline' docs/reference.md docs/experimental-designs.md docs/design-principles.md README.md
grep -n 'unpaired_percentile_over_units' docs/reference.md
```

      Read every hit and record in the task report which are about a `vs_baseline` record **carrying
      an unpaired entry** (the claim) versus merely mentioning the block. **Do not filter the
      output.** If a fourth site exists, repair it in this commit and say so — the enumeration is
      this task's deliverable and a missed site is the documented failure mode.

- [ ] **Step 5: run the mechanical pass and the cross-document pass**, as task 2's Steps 5 and 6
      specify. Confirm `#errors-validate-reports` and
      `#contrasts-claims-that-arent-condition-vs-baseline` resolve. **Check `×` is not needed here**
      — no multiplication is introduced.

- [ ] **Step 6: run the gates.** `uv run pytest` → **2200 passed**, 1 skipped, 2 xfailed. Then the
      other three.

- [ ] **Step 7: no mutation** — documents only. **The tripwire is task 18**, which runs a declared
      cross-arm contrast end to end and produces the shape this block now shows.

- [ ] **Step 8: Commit.**

```bash
git add docs/reference.md
git commit -m "docs: § Allocation's unpaired example moved to results.contrasts, where a config can produce it"
```

---

## Task 21: the regression pin, its literals captured at `e40a219`, and the boundary this slice owes

**Runs fourth, before task 4** — see deviation (a). **Every literal below was captured at
`e40a219` by direct calls to `cli._comparison_step_blocks` and `correction.corrected_for` before any
behaviour in this slice changed.** A literal recorded afterwards records the change, not the
baseline. **No later task may edit an expected value in this file**; if one of these fails, the fix
is in `stats.py`, `correction.py` or `cli.py`.

**Files:**
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `tests/test_cli.py`'s existing `_clustered_contrast_call(**extra)` helper — 12 units
  `u00`…`u11`, `of` values `1.0 ×2`, `5.0 ×4`, `9.0 ×6` against an `against` side of zeros,
  `_CONTRAST_CLUSTER_LABELS = ["a"] * 2 + ["b"] * 4 + ["c"] * 6`, `seed=7`, `draws=400`, two
  conditions differing on `analysis.method` only — read in `tests/test_cli.py`;
  `correction.corrected_for(members, method, family_size, shape)`.
- Produces: nothing. It is the pin every task after it must keep green.

**Why the corrected bounds are pinned and not only the raw ones.** `_corrected_bounds` grows two arms
in task 12, and **deriving `paired` at both branches is precisely the change that can silently move
every existing paired contrast** while `_corrected_bounds` growing two arms is precisely the change
that can silently move every existing corrected bound. A raw-interval pin alone would not see an arm
inserted above the `diffs` branch.

- [ ] **Step 1: write the three tests.** Append to `tests/test_cli.py`, immediately after
      `test_an_unclustered_contrast_entry_grows_no_cluster_count`:

```python
_H4C_BASELINE = {
    # Captured at `e40a219`, before any H4c behaviour changed, by calling
    # `_clustered_contrast_call` and `correction.corrected_for` directly. Every
    # cell is (method, ci95, cohens_d, ci95_corrected at bonferroni over a family
    # of 2). The delta is 6.333333333333333 in every cell and is asserted once.
    "plain_t": (
        "paired_t_over_units",
        [4.354794810376774, 8.311871856289892],
        2.0338284916219784,
        [4.002316360103361, 8.664350306563305],
    ),
    "plain_percentile": (
        "paired_percentile_over_units",
        [4.666666666666667, 8.0],
        2.0338284916219784,
        [4.333333333333333, 8.0],
    ),
    "clustered_t": (
        "paired_t_over_units_clustered",
        [-2.42988081030457, 15.096547476971235],
        2.0338284916219784,
        [-6.3050984446171165, 18.971765111283784],
    ),
    "clustered_percentile": (
        "paired_percentile_over_units_clustered",
        [1.0, 8.0],
        2.0338284916219784,
        [1.0, 9.0],
    ),
    "weighted_t": (
        "weighted_paired_t_over_units",
        [4.205411474977312, 8.461255191689354],
        2.0235305596718636,
        [3.8161416371442236, 8.850525029522442],
    ),
    "weighted_percentile": (
        "weighted_paired_percentile_over_units",
        [4.555555555555555, 7.888888888888889],
        2.0235305596718636,
        [4.368421052631579, 8.058823529411764],
    ),
}

_H4C_WEIGHTS = {f"u{i:02d}": 1 + i % 2 for i in range(12)}

_H4C_CELLS = {
    "plain_t": dict(clusters=None),
    "plain_percentile": dict(clusters=None, resample_columns=True),
    "clustered_t": {},
    "clustered_percentile": dict(resample_columns=True),
    "weighted_t": dict(clusters=None, weights=_H4C_WEIGHTS, weighted_by="w"),
    "weighted_percentile": dict(
        clusters=None, weights=_H4C_WEIGHTS, weighted_by="w", resample_columns=True
    ),
}


@pytest.mark.parametrize("cell", sorted(_H4C_BASELINE))
def test_every_paired_contrast_cell_is_byte_identical_across_this_branch(cell):
    """H4c derives `paired` at both metric branches and grows `_corrected_bounds`
    by two arms. Both are changes that can move a PAIRED contrast without moving
    anything a reader of one entry would notice, so all six reachable paired cells
    are pinned at once — `paired_t_over_units`, `paired_percentile_over_units`, and
    the weighted and clustered forms of each.

    **The corrected bound is pinned beside the raw one, and that is the half a
    raw-only pin misses**: an arm inserted above the `diffs` branch in
    `_corrected_bounds` leaves every `ci95` untouched and every `ci95_corrected`
    wrong, and no reader of `run.yaml` could tell.

    Every literal was captured at `e40a219` before any H4c behaviour changed. If
    one of these fails, the fix is in `stats.py`, `correction.py` or `cli.py` —
    never in the expected value."""
    from publishable.correction import corrected_for

    method, ci95, cohens_d, corrected = _H4C_BASELINE[cell]
    block, members = _clustered_contrast_call(**_H4C_CELLS[cell])
    entry = block["s"]["m"]
    assert entry["delta"] == pytest.approx(6.333333333333333)
    assert entry["paired"] is True
    assert entry["n_paired"] == 12
    assert entry["method"] == method
    assert entry["ci95"] == pytest.approx(ci95)
    assert entry["cohens_d"] == pytest.approx(cohens_d)
    fields = corrected_for(members, "bonferroni", 2, {"comparisons": 1, "metrics": 2})
    assert list(fields) == [("cond:1", "s", "m")]
    assert fields[("cond:1", "s", "m")]["ci95_corrected"] == pytest.approx(corrected)


def test_a_paired_contrast_entry_still_grows_no_unpaired_key():
    """The absent-not-null obligation read in the other direction. H4c makes
    `n_paired` conditional for the first time in this codebase, and the failure
    mode of a conditional write is writing BOTH shapes: `n_paired: 12` beside
    `n_of: 12`, which decision 5 rejects as the worst of both.

    Asserted beside a presence that must report, because a control asserting only
    absences passes identically if nothing ran."""
    block, _ = _clustered_contrast_call()
    entry = block["s"]["m"]
    assert entry["n_paired"] == 12  # the presence that must report
    assert entry["n_paired_clusters"] == 3
    for absent in ("n_of", "n_against", "n_clusters_of", "n_clusters_against"):
        assert absent not in entry


def test_an_unpaired_pass_leaves_a_summary_estimate_alone(tmp_path, capsys):
    """The boundary this slice OWES rather than merely respects. An `Estimate`
    returned by a `summary` step is `reported: true`, outside the correction family
    and never recomputed — and it is the documented route
    `E-DATA-ALLOCATION-CONTRAST`'s own message offers before task 18 deletes it, so
    retiring that message must not have moved it. A pass that walks every metric
    block to decide pairing must not reach it.

    The contrast beside it is asserted in the same record, because a control
    asserting only absences passes identically if nothing ran."""
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        aggregate_returns="score",
        replication={"repeats": [{"kind": "seed", "n": 1}], "order": "as_declared"},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        extra_steps=["summarize"],
        extra_step_source=_ESTIMATE_WITH_N_SUMMARY_STEP,
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    reported = run["results"]["summary"]["step02_summarize"]["adjusted"]
    assert reported["reported"] is True
    assert reported["method"] == "mixed model, REML"
    for absent in ("paired", "n_paired", "n_of", "n_against", "correction"):
        assert absent not in reported
    # The presences that must report: `aggregate_returns` gives this run BOTH a
    # recorded column (`pred`) and a derived metric (`score`), so the two contrast
    # branches are both exercised beside the untouched `Estimate`.
    block = next(
        c["vs_baseline"] for c in run["results"]["conditions"] if c.get("vs_baseline")
    )["step01_summarize_units"]
    assert block["pred"]["paired"] is True
    assert block["pred"]["method"] == "paired_t_over_units"
    assert block["score"]["paired"] is True
    assert block["score"]["method"] == "paired_percentile_over_units"
    assert block["pred"]["n_paired"] == 40
```

      **`_ESTIMATE_WITH_N_SUMMARY_STEP` already exists** in `tests/test_cli.py` — the
      `scope = "summary"` source returning `Estimate(value=0.031, ci95=[0.008, 0.055], n=612,
      method="mixed model, REML")`, used by the test that pins an `Estimate` carrying its own `n`.
      **Reuse it; do not add a second summary-step constant.** The `extra_steps`/`extra_step_source`
      pair is how a caller gets a non-`repeat` scope into a generated project at all, and
      `aggregate_returns` is what makes the scaffolded step record `pred` while the template's
      `aggregate` derives `score` — read `run_a_project`'s docstring for all three before writing.
      **This exact combination was run at `e40a219`** and produced the record shape asserted above,
      including the step names `step01_summarize_units` and `step02_summarize`; the `pred` and
      `score` deltas are both `0.0` there, which is why the assertions are on `paired`, `method` and
      `n_paired` rather than on a width.

- [ ] **Step 2: run and see all three pass.** `uv run pytest tests/test_cli.py -k
      "byte_identical or grows_no_unpaired_key or summary_estimate_alone"` → **8 passed** (six
      parametrized cells plus two). **That is the point of a regression pin**: their value is
      entirely in Step 3's mutations, and in the tasks after this one that must keep them green.
      **If a cell fails here, stop**: the literal is wrong, not the code, and a wrong baseline
      literal is worse than no pin.

- [ ] **Step 3: mutate — three mutations, and the first is the one that matters.**

      **Mutation 1 — the corrected arm order.** In `src/publishable/correction.py`, in
      `_corrected_bounds`, move the `if member.pool is not None:` branch **above** the
      `if member.diffs is not None:` branch. `plain_t`, `clustered_t` and `weighted_t` still pass
      (their members carry no pool), and `plain_percentile`, `clustered_percentile` and
      `weighted_percentile` still pass (their members carry no diffs) — **so this mutation is BLIND,
      and it is written down here so nobody prescribes it later believing it proves the order.**
      `Member.__post_init__` enforces exactly one of the two, which is precisely why the *order* is
      unobservable. **The fixture that would discriminate does not exist and cannot**: it would need
      a member carrying both, which `__post_init__` refuses. The order's real protection is that
      refusal, pinned in `tests/test_correction.py`, and task 11 extends it to three.

      **Mutation 2 — a corrected bound at the wrong confidence.** In `correction._corrected_bounds`,
      change the plain `diffs` arm's `confidence=1.0 - level` to `confidence=0.95`.
      `test_every_paired_contrast_cell_is_byte_identical_across_this_branch[plain_t]` must **FAIL**
      on `ci95_corrected`, seeing `[4.354794810376774, 8.311871856289892]` — the raw interval —
      where it expects `[4.002316360103361, 8.664350306563305]`. **Checked against the test body:**
      the two branches differ because Bonferroni over a family of 2 is α = 0.025 and
      `t(11, 0.9875) / t(11, 0.975)` is 1.178, well outside `pytest.approx`'s tolerance.

      **Mutation 3 — a `method` string.** In `src/publishable/stats.py`, change
      `paired_t_over_units`'s returned `method` to `"t_over_units"`. The `plain_t` cell must
      **FAIL** on `entry["method"]`. This is the cheap proof the parametrization is wired to the
      right cells rather than passing six times over one.

      Run each against the **full, unfiltered** suite in the foreground; revert each by editing the
      file back in place, never `git checkout --`.

- [ ] **Step 4: run the gates.** `uv run pytest` → **2200 + 8 = 2208 passed**, 1 skipped,
      2 xfailed. Then `uv run ruff check .`, `uv run ruff format --check .` (80 files),
      `uv run mypy`.

- [ ] **Step 5: Commit.**

```bash
git add tests/test_cli.py
git commit -m "test: the paired-contrast regression pin, six cells with their corrected bounds, captured before H4c changes anything"
```

---
## Task 4: `stats.welch_t_over_units`, and the one sample-variance expression it rests on

**Runs after task 1**, whose ruling fixed that this slice builds **four** unpaired constructions and
not six — so this function takes no `weights` parameter and never will.

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `stats._t_critical(df: float, confidence: float) -> float`, the single two-sided critical
  value for every *t* interval in the module; `stats.t_over_units(values, confidence=0.95)`, which
  computes `mean = sum(values) / n` and `variance = sum((v - mean) ** 2 for v in values) / (n - 1)`
  inline — read in `src/publishable/stats.py`.
- Produces:

```python
def _sample_variance(values: Sequence[float], mean: float) -> float

def welch_t_over_units(
    of: Sequence[float], against: Sequence[float], confidence: float = 0.95
) -> Interval | None
```

  `welch_t_over_units` is called by `correction._corrected_bounds` (task 12) and
  `cli._comparison_step_blocks` (task 14), returning an `Interval` whose `method` is exactly
  `"welch_t_over_units"`. `_sample_variance` is consumed by `t_over_units` (rewired here),
  `welch_t_over_units` and `cohens_ds` (task 5).

**Why the variance is extracted, and why the extraction is safe.** `_t_critical`'s own docstring makes
this argument for itself — *"One expression rather than one per construction: two copies is how the
weighted and unweighted intervals drift apart, and a drift in a critical value is invisible in every
output that isn't compared against the other."* A Welch interval and a pooled *d*s standardizing by
different sample variances would be exactly that, and § Statistical reporting's *"*d*s pools where
`welch_t_over_units` deliberately doesn't"* asymmetry is only readable if both rest on the same
quantity. **The extraction is pure code motion** — same expression, same order of operations, so
`t_over_units` is bit-identical — and task 21's pin over the six paired cells is what says so.
`weighted_t_over_units` and `cohens_dz` are deliberately **not** rewired: their denominators are
`Σw − Σw²/Σw` and a difference vector's own, which are different quantities, and touching them is
scope this task does not have.

**The df is the construction, not a detail of it.** Two rejected readings, named so nobody
re-derives them: `n_of + n_against − 2` is the **pooled** reading this row refuses by construction,
and `min(n) − 1` discards a side's information. Both give a number on fixture A, and the fixture is
sized so neither lands within 4 % of the correct one.

- [ ] **Step 1: write the failing tests.** Append to `tests/test_stats.py`, beside the existing
      `t_over_units` tests:

```python
_WELCH_OF = [17.0, 19.0, 20.0, 21.0, 23.0]
_WELCH_AGAINST = [5.0] * 12 + [15.0] * 12 + [10.0]


def test_the_welch_t_assumes_neither_shared_units_nor_equal_variances():
    """Fixture A: `of` is 5 units at mean 20 with s² 5, `against` is 25 units at
    mean 10 with s² 25 — so s²/n is exactly 1 on each side and BOTH sides
    contribute comparably to the Welch variance. That balance is the whole design
    of the fixture: where one side dominates, Welch-Satterthwaite's df is driven
    onto `min(df_of, df_against)` and a `min(n) − 1` mutant becomes invisible. The
    spec's own first draft did exactly that — correct 17.2405 against the mutant's
    17.2614, 0.1 % apart.

    Delta 10, SE √2, df 96/7. Four wrong readings give four other half-widths and
    none is adjacent: the pooled variance at df 28 gives 4.7221, the Welch variance
    at `min(n) − 1` gives 3.9265, at `max(n) − 1` gives 2.9188, and at
    `n_of + n_against − 2` gives 2.8969. The tightest is 4.7 % from correct, which
    no rounding produces.

    **A Welch interval that coincides with a pooled one proves nothing** — equal
    per-side sizes make the two standard errors algebraically identical — so the
    unequal sizes here are load-bearing rather than incidental."""
    interval = welch_t_over_units(_WELCH_OF, _WELCH_AGAINST)
    assert interval is not None
    assert interval.method == "welch_t_over_units"
    centre = (interval.low + interval.high) / 2
    half = (interval.high - interval.low) / 2
    assert centre == pytest.approx(10.0)
    assert half == pytest.approx(3.039125537798091)


def test_the_welch_t_is_not_the_pooled_t_on_the_same_two_sides():
    """The control that must report, and the number a pooled mutant lands on. The
    pooled standard error on the same data is
    √(((4·5) + (24·25)) / 28 · (1/5 + 1/25)) and at df 28 gives a half-width of
    4.7221 — 55 % wider. A test asserting only that an interval came back, or only
    that it brackets the delta, passes under either construction."""
    pooled_variance = ((5 - 1) * 5.0 + (25 - 1) * 25.0) / (5 + 25 - 2)
    pooled_se = math.sqrt(pooled_variance * (1 / 5 + 1 / 25))
    assert _t_critical(28, 0.95) * pooled_se == pytest.approx(4.722138614325821)
    interval = welch_t_over_units(_WELCH_OF, _WELCH_AGAINST)
    assert interval is not None
    assert (interval.high - interval.low) / 2 != pytest.approx(4.722138614325821)


def test_the_welch_t_refuses_the_degenerate_inputs_its_siblings_refuse():
    """`None` below two values on EITHER side — df would be zero on that side and
    there is no dispersion to describe, which is `t_over_units`' own floor read
    across two samples. `None` also where both sides are constant: the combined
    variance is then exactly zero and Welch-Satterthwaite's df is 0/0, so the
    honest answer is a point with no interval rather than a `ZeroDivisionError`.

    One side constant is NOT refused — the other side still has dispersion, and the
    difference of two means still has a sampling distribution — which is the
    asymmetry a copied `or` guard would get wrong."""
    assert welch_t_over_units([1.0], [1.0, 2.0, 3.0]) is None
    assert welch_t_over_units([1.0, 2.0, 3.0], [1.0]) is None
    assert welch_t_over_units([2.0, 2.0, 2.0], [1.0, 1.0, 1.0]) is None
    one_side_flat = welch_t_over_units([2.0, 2.0, 2.0], [1.0, 2.0, 3.0])
    assert one_side_flat is not None
    assert one_side_flat.high > one_side_flat.low


def test_the_extracted_sample_variance_leaves_t_over_units_where_it_was():
    """The extraction is pure code motion and this is the oracle that says so.
    `t_over_units` over `_WELCH_AGAINST` must give the same half-width it gave
    before `_sample_variance` existed — mean 10, s² 25, n 25, so
    t(0.975, 24)·√(25/25) = 2.0638985616280205.

    Pinned here rather than trusted, because a `(n - 1)` that became `n` in the
    move would narrow every unweighted interval in the package by a few per cent
    and nothing else in this module would notice."""
    plain = t_over_units(_WELCH_AGAINST)
    assert plain is not None
    assert (plain.high - plain.low) / 2 == pytest.approx(2.0638985616280205)
    assert _sample_variance(_WELCH_AGAINST, 10.0) == pytest.approx(25.0)
```

      Add `welch_t_over_units`, `_sample_variance` and `_t_critical` to the
      `from publishable.stats import (...)` block at the top of `tests/test_stats.py` —
      `t_over_units` is already there — and confirm `math` is already imported in that module
      before adding it.

      **Verify the `t_over_units` literal before believing it.** `2.0638985616280205` is
      `_t_critical(24, 0.95) * 1.0`; compute it with `uv run python -c` and paste what you get
      rather than trusting this line. A regression oracle with a wrong expected value pins the
      wrong thing.

- [ ] **Step 2: run and see them fail.** `uv run pytest tests/test_stats.py -k "welch or sample_variance"`
      → `ImportError` on `welch_t_over_units`.

- [ ] **Step 3: implement.** In `src/publishable/stats.py`, add `_sample_variance` immediately after
      `_t_critical` and rewire `t_over_units` to call it; add `welch_t_over_units` immediately after
      `weighted_t_over_units_clustered`, before `paired_t_over_units`, so the per-condition forms and
      the contrast forms stay in their existing blocks:

```python
def _sample_variance(values: Sequence[float], mean: float) -> float:
    """The unbiased sample variance, Σ(v − v̄)² / (n − 1) — the one copy in this module.

    Extracted for the reason `_t_critical` gives for itself: one expression rather
    than one per construction, because two copies is how two intervals over the
    same data come to disagree about what the dispersion *is*, and a drift there is
    invisible in every output that isn't compared against the other.
    `welch_t_over_units` puts this in an interval and `cohens_ds` pools two of them
    into a standardizer, and § Statistical reporting's *d*s-pools-where-Welch-doesn't
    asymmetry is only readable if both rest on the same quantity.

    Takes the mean rather than recomputing it: every caller already holds one, and
    a variance centred on a different mean than the point estimate is the failure
    `_weighted_mean` exists to prevent one level over.

    Undefined below two values — every caller floors above that first, which is
    where the "no dispersion to describe" refusal belongs. `weighted_t_over_units`
    and `cohens_dz` deliberately do NOT call this: their denominators are
    `Σw − Σw²/Σw` and a difference vector's own, which are different quantities.
    """
    return sum((v - mean) ** 2 for v in values) / (len(values) - 1)


def welch_t_over_units(
    of: Sequence[float], against: Sequence[float], confidence: float = 0.95
) -> Interval | None:
    """Welch's *t* on two independent condition means, df from Welch-Satterthwaite.

    `reference.md` § Statistical reporting: "The unpaired counterpart of the first:
    unequal variances are assumed rather than pooled, because two arms need be
    neither the same size nor the same spread." The contrast's interval is its own
    construction over the two sides, never a difference of the two sides' own
    intervals — `paired_t_over_units`' argument, unchanged by the sides being
    disjoint.

    **There is no pooling anywhere in this construction**, and that is the whole
    content of the row. Pooling the two variances gives a plausible number that is
    wrong in a direction unequal spreads decide, and at equal per-side sizes the
    pooled and Welch standard errors are algebraically IDENTICAL — so a fixture
    with equal arms cannot tell the two apart, and no test of this function may use
    one.

    **The df is the construction, not a detail of it.** Welch-Satterthwaite over
    the two per-side variances-of-the-mean is what makes the interval honest about
    two spreads; `n_of + n_against − 2` is the pooled reading this row refuses, and
    `min(n) − 1` throws a side's information away. `cohens_ds` pools where this
    deliberately doesn't, and § Statistical reporting states that asymmetry is not
    an inconsistency: an interval is an inference and gets the assumption-light
    construction, while *d* is a descriptive standardization whose conventional
    denominator *is* the pooled one.

    Returns `None` below two values on either side, matching `t_over_units`' floor
    read across two samples: df would be zero on that side and there is no
    dispersion to describe. Reporting a point with no interval is honest; inventing
    one is not. Returns `None` where BOTH sides are constant, because the combined
    variance is then exactly zero and the df is 0/0 — one side constant is not
    refused, since the other still has dispersion and the difference of two means
    still has a sampling distribution.

    Takes two value vectors and nothing else, for the reason
    `paired_t_over_units_clustered` takes a label vector: `correction.Member`
    carries them as `UnpairedEvidence`, and both callers hold two per-side vectors
    with no roster between them.
    """
    n_of, n_against = len(of), len(against)
    if n_of < 2 or n_against < 2:
        return None
    mean_of = sum(of) / n_of
    mean_against = sum(against) / n_against
    # The variance OF THE MEAN on each side, s²/n — what Welch adds rather than
    # pools, and what Welch-Satterthwaite's df is a function of.
    var_of = _sample_variance(of, mean_of) / n_of
    var_against = _sample_variance(against, mean_against) / n_against
    total = var_of + var_against
    if total <= 0.0:
        return None
    df = total * total / (
        var_of * var_of / (n_of - 1) + var_against * var_against / (n_against - 1)
    )
    delta = mean_of - mean_against
    half = _t_critical(df, confidence) * math.sqrt(total)
    return Interval(low=delta - half, high=delta + half, method="welch_t_over_units")
```

- [ ] **Step 4: run and see them pass.** `uv run pytest` → **2208 + 4 = 2212 passed**, 1 skipped,
      2 xfailed. Then `uv run ruff check .`, `uv run ruff format --check .` (80 files),
      `uv run mypy`.

- [ ] **Step 5: mutate — four mutations, and one named blind.**

      **Do not prescribe swapping `of` and `against`.** It flips `delta`'s sign and leaves the
      half-width **bit-identical** — `var_of + var_against` is symmetric and so is the df expression
      — so it is blind to every interval assertion and caught only by the `centre` one. **Named here
      so nobody prescribes it as an interval mutation later**, which is the *"a mutation is a claim
      too"* discipline: five mutations were claimed blind on H4b-2 and one was overturned by a
      one-line fixture change, so a blindness claim needs its arithmetic stated. Here the arithmetic
      is symmetry of addition.

      **Mutation 1 — the pooled variance.** Replace the two `/ n_of` and `/ n_against` divisions and
      the df expression with the pooled form: `variance = ((n_of - 1) * _sample_variance(of, mean_of)
      + (n_against - 1) * _sample_variance(against, mean_against)) / (n_of + n_against - 2)`,
      `total = variance * (1 / n_of + 1 / n_against)`, `df = n_of + n_against - 2`.
      `test_the_welch_t_assumes_neither_shared_units_nor_equal_variances` must **FAIL** with
      4.722138614325821 — the number
      `test_the_welch_t_is_not_the_pooled_t_on_the_same_two_sides` independently pins, which is what
      makes the two tests a pair rather than a repetition.

      **Mutation 2 — the df, onto a side's own.** Change `df` to `min(n_of, n_against) - 1`. The same
      test must **FAIL** with 3.9264863229551143. **Checked against the fixture:** both sides
      contribute s²/n = 1, so the correct df 13.714 sits well above `min(n) − 1 = 4` and the two
      half-widths differ by 29 %. On a fixture where one side dominated the variance this mutation
      would be blind, which is constraint 2 of § The two discriminating fixtures.

      **Mutation 3 — the df, onto the total.** Change `df` to `n_of + n_against - 2`. The same test
      must **FAIL** with 2.8968851611887434. This and mutation 2 fail on opposite sides of correct,
      which is what says the assertion is on the number rather than on a direction.

      **Mutation 4 — the extraction.** In `_sample_variance`, change `(len(values) - 1)` to
      `len(values)`. `test_the_extracted_sample_variance_leaves_t_over_units_where_it_was` must
      **FAIL** on both of its assertions, **and** `test_every_paired_contrast_cell_is_byte_identical_across_this_branch[plain_t]`
      from task 21 must **FAIL** on `ci95` — the pair is what says the extraction is watched from
      inside `stats.py` and from the record at once.

      Run each against the **full, unfiltered** suite in the foreground; revert each by editing the
      file back in place, never `git checkout --`.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/stats.py tests/test_stats.py
git commit -m "feat: welch_t_over_units, and one sample-variance expression for the three constructions that share it"
```

---

## Task 5: `stats.cohens_ds`

**Runs after task 4**, whose `_sample_variance` this pools two of.

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `stats._sample_variance(values, mean)` (task 4); `stats.cohens_dz(diffs)`, which returns
  `None` below two differences and `None` at zero dispersion — read in `src/publishable/stats.py`.
- Produces:

```python
def cohens_ds(of: Sequence[float], against: Sequence[float]) -> float | None
```

  Called by `cli._comparison_step_blocks` (task 14). **Nothing else calls it** — `cohens_d` is
  computed at the record site from the local vectors and does not travel on a `Member`, exactly as
  `cohens_dz` does not.

**The denominator is the pooled within-condition sd, deliberately NOT the interval's.** § Statistical
reporting: *"unpaired ones report *d*s, over the pooled within-condition standard deviation … *d*s
pools where `welch_t_over_units` deliberately doesn't, and that isn't an inconsistency: an interval is
an inference and gets the assumption-light construction, while *d* is a descriptive standardization
whose conventional denominator *is* the pooled one — reporting a *d* against a Welch-style denominator
would be a number no reader could compare to another paper's."* **This is the assertion that makes
that sentence more than a sentence**, and on fixture A the two denominators differ by a factor of
3.33, so the test can tell them apart.

- [ ] **Step 1: write the failing tests.** Append to `tests/test_stats.py`, beside the
      `cohens_dz` tests:

```python
def test_cohens_ds_pools_the_two_within_condition_variances():
    """Fixture A: mean 20 over 5 units with s² 5 against mean 10 over 25 units with
    s² 25. The pooled variance is ((4·5) + (24·25)) / 28 = 22.142857…, so the
    pooled sd is 4.705619740571601 and *d*s is 10 / that = 2.1251185925162073.

    **The discriminating alternative is the interval's own denominator.**
    `welch_t_over_units` on this data has SE √2, and 10/√2 is 7.0710678118654755 —
    a factor of 3.33 out. § Statistical reporting states that asymmetry
    deliberately, and this assertion is what makes it checkable rather than
    merely written down.

    An unweighted equal-size fixture could not tell the two apart at all, which is
    why this shares fixture A rather than inventing a tidier one."""
    assert cohens_ds(_WELCH_OF, _WELCH_AGAINST) == pytest.approx(2.1251185925162073)


def test_cohens_ds_is_not_standardized_by_the_welch_denominator():
    """The control that must report, and the number the wrong denominator lands on.
    Asserted as a literal rather than as an inequality: `!=` alone passes for any
    third wrong number, and a *d* is a number readers compare across papers."""
    interval = welch_t_over_units(_WELCH_OF, _WELCH_AGAINST)
    assert interval is not None
    welch_se = (interval.high - interval.low) / 2 / _t_critical(96 / 7, 0.95)
    assert 10.0 / welch_se == pytest.approx(7.0710678118654755)
    assert cohens_ds(_WELCH_OF, _WELCH_AGAINST) != pytest.approx(7.0710678118654755)


def test_cohens_ds_refuses_what_cohens_dz_refuses():
    """`None` below two values on either side, and `None` at zero dispersion — the
    two refusals `cohens_dz` carries, kept so the pair refuses the same inputs. A
    *d* over a denominator that has rounded away is the same invention
    `t_over_units` already declines below two values."""
    assert cohens_ds([1.0], [1.0, 2.0, 3.0]) is None
    assert cohens_ds([1.0, 2.0, 3.0], [1.0]) is None
    assert cohens_ds([2.0, 2.0, 2.0], [1.0, 1.0, 1.0]) is None
```

      Add `cohens_ds` to the import block.

- [ ] **Step 2: run and see them fail.** `uv run pytest tests/test_stats.py -k cohens_ds` →
      `ImportError`.

- [ ] **Step 3: implement.** In `src/publishable/stats.py`, immediately after `weighted_cohens_dz`:

```python
def cohens_ds(of: Sequence[float], against: Sequence[float]) -> float | None:
    """The difference of two condition means over the pooled within-condition sd.

    `reference.md` § Statistical reporting: "paired contrasts report *d*z … and
    unpaired ones report *d*s, over the pooled within-condition standard
    deviation. They are different quantities from the same data and the one that
    applies follows from `paired`, which is derived rather than declared."

    **The denominator pools where `welch_t_over_units`' deliberately does not**, and
    § Statistical reporting says in terms that this is not an inconsistency: an
    interval is an inference and gets the assumption-light construction, while *d*
    is a descriptive standardization whose conventional denominator *is* the pooled
    one, and a *d* against a Welch-style denominator is a number no reader could
    compare to another paper's. So this function does not read the interval beside
    it, and must not be tidied into doing so.

    Reported only for a per-unit mean, exactly as `cohens_dz` is: a derived metric
    has no per-unit value to difference, which is why the worked example carries
    `cohens_d: null` for `r`.

    `None` below two values on either side and `None` at zero dispersion, the two
    refusals `cohens_dz` carries, kept so the family refuses the same inputs.
    """
    if len(of) < 2 or len(against) < 2:
        return None
    mean_of = sum(of) / len(of)
    mean_against = sum(against) / len(against)
    pooled = (
        (len(of) - 1) * _sample_variance(of, mean_of)
        + (len(against) - 1) * _sample_variance(against, mean_against)
    ) / (len(of) + len(against) - 2)
    sd = math.sqrt(pooled)
    return (mean_of - mean_against) / sd if sd > 0 else None
```

- [ ] **Step 4: run and see them pass.** `uv run pytest` → **2212 + 3 = 2215 passed**, 1 skipped,
      2 xfailed. Then the other three gates.

- [ ] **Step 5: mutate.**

      **Mutation 1 — the Welch denominator.** Replace the `pooled` expression with
      `_sample_variance(of, mean_of) / len(of) + _sample_variance(against, mean_against) / len(against)`.
      `test_cohens_ds_pools_the_two_within_condition_variances` must **FAIL** with
      7.0710678118654755, the number the second test independently pins.

      **Mutation 2 — the weighting of the two variances.** Change the pooled numerator to the
      unweighted mean of the two variances, `(_sample_variance(of, mean_of) +
      _sample_variance(against, mean_against)) / 2`. The same test must **FAIL** with
      `10 / math.sqrt(15.0)` = 2.5819888974716116. **Checked against the fixture:** the two sides'
      sizes are 5 and 25, so weighting by `n − 1` and not weighting give 22.14 against 15.0 — a 32 %
      difference in the variance and 21 % in the *d*. On an equal-size fixture the two are
      **algebraically identical** and this mutation would be blind, which is another reason fixture
      A's sizes are unequal.

      **Mutation 3 — the sd floor.** Change `if sd > 0` to `if sd >= 0`.
      `test_cohens_ds_refuses_what_cohens_dz_refuses` must **FAIL** with `ZeroDivisionError` on the
      two-constant-sides case rather than `None`.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/stats.py tests/test_stats.py
git commit -m "feat: cohens_ds, pooling where the Welch interval deliberately does not"
```

---

## Task 6: `stats.unpaired_percentile_of_sides` — a new construction, drawing each side independently

**Runs after task 1.** **This is a new function and not a `method` argument on an existing one**, and
the reason is written into `paired_percentile_of_derived`'s own docstring: its whole construction is
*one* draw applied to both sides, because drawing each side independently *"would resample the two
conditions apart and destroy the pairing"* — and § Statistical reporting defines the unpaired form as
*"resampling within each side independently"*, which is precisely the arrangement that docstring
exists to refuse. **The three-`method`-strings-one-function economy H4b-1 and H4b-2 built does not
extend here.**

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `stats.PairedResample(interval, draws_used, pool)`;
  `stats.unit_table_from_rows(rows) -> UnitTable`; `stats._percentile_ranks(draws, confidence)`;
  `stats.min_honest_draws(confidence)`; and `paired_percentile_of_derived`'s `items`/`pools`
  construction — the uniform draw shape H4b-2 built, a list of stratum groups each holding drawable
  key-lists, with the `keys != sorted(keys)` `ValueError` and the
  `E-STATS-RESAMPLE-STRATIFY-VARIES` `ContractError` inside it — read in
  `src/publishable/stats.py`.
- Produces:

```python
def _draw_pools(
    keys: list[str],
    strata: dict[str, str] | None,
    clusters: dict[str, str] | None,
) -> list[list[list[str]]]

def _side_content(
    item: Sequence[str], rows: Mapping[str, Mapping[str, float]]
) -> tuple[tuple[tuple[str, float], ...], ...]

def unpaired_percentile_of_sides(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    of_keys: list[str],
    against_keys: list[str],
    compute_of: "Callable[[UnitTable], float | None]",
    compute_against: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    strata: dict[str, str] | None = None,
    method: str = "unpaired_percentile_over_units",
    of_clusters: dict[str, str] | None = None,
    against_clusters: dict[str, str] | None = None,
) -> PairedResample
```

  Called by `cli._comparison_step_blocks` (task 14) under both of its `method` spellings, task 8
  supplying the second. `_draw_pools` is **extracted from `paired_percentile_of_derived`** and called
  once there and twice here.

**Why `_of_sides` and not `_of_derived`.** The paired function is named for the evidence it draws
over. This one never serves a derived metric — decision 8 suppresses an unpaired derived contrast
because no per-side derived draw exists — so `unpaired_percentile_of_derived` would be a false name
on its first day. It is not named after its `method` string either: one function serves two spellings,
per task 1's ruling.

**Why `_draw_pools` is extracted rather than copied.** The `strata` × `clusters` composition rule,
the relabelling invariance (clusters and strata both ordered by their own sorted contents, so a
relabelled roster draws the identical sequence), the sorted-keys caller contract and the
`E-STATS-RESAMPLE-STRATIFY-VARIES` refusal are **four** properties H4b-2 argued at length. A second
copy is how one of them is fixed in one place and not the other, which `CLAUDE.md` § Habits names
directly. The extraction is **pure code motion** for the paired form, and task 21's
`clustered_percentile` and `plain_percentile` cells are what say so — both pin endpoints off the
paired draw sequence.

**Delete the caller's name from the `ValueError` while moving it.** Its text names
`paired_percentile_of_derived`, which after the extraction has two callers. `tests/test_stats.py`
matches on `"sorted"` only — verified at `e40a219` — so the fix is to **delete** the function name
rather than enumerate two, which is a deletion and cannot invent.

**The degenerate rule is per side and it is AND, not OR.** `paired_percentile_of_derived` returns no
interval when every drawable thing in every stratum carries the same pair of rows, because the joint
draw is then a constant. Here there are **two** draws, and if only one side is constant the
*difference* still varies — so the refusal fires only where **both** sides cannot vary. A copied
`all(...)` check applied per side with an implicit "either" would null intervals that are fine, which
is the reverse of the defect H4b-2 closed and just as invisible.

- [ ] **Step 1: write the failing tests.** Append to `tests/test_stats.py`:

```python
def _side_rows(values, prefix):
    return {f"{prefix}{i:02d}": {"m": v} for i, v in enumerate(values)}


def _row_count_recorder():
    """A compute closure that records the row count of every table it is handed.

    The percentile discriminator is the per-replicate DRAW SIZE, and § The two
    discriminating fixtures requires it be asserted rather than inferred from the
    interval — which only works if the construction admits an observable. This is
    that observable: the closure returns the column mean, so the draw proceeds
    normally, and the sizes accumulate in a list the test reads afterwards."""
    seen: list[int] = []

    def compute(table):
        seen.append(len(table))
        column = getattr(table, "m")
        return float(sum(column) / len(column))

    return compute, seen


def test_the_unpaired_percentile_draws_each_side_independently():
    """Fixture A through the percentile form. An independent per-side draw takes
    exactly 5 rows from `of` and exactly 25 from `against` on EVERY replicate; a
    mutant drawing once from the pooled 30 and splitting, or drawing `min(n)` for
    both, returns different sizes.

    **The draw size is asserted, not inferred from the interval.** An interval
    assertion cannot tell a pooled draw from an independent one — both produce a
    plausible number centred near 10 — and `is not None` is a uselessly weak
    discriminator on this slice, where a suppressed contrast, a thin side and a
    degenerate draw all return `None` too.

    The endpoints are pinned as literals beside the sizes, captured from this
    test's first green run in the same commit, so a later change cannot move the
    draw while keeping the counts right."""
    of_rows = _side_rows(_WELCH_OF, "a")
    against_rows = _side_rows(_WELCH_AGAINST, "b")
    compute_of, seen_of = _row_count_recorder()
    compute_against, seen_against = _row_count_recorder()
    got = unpaired_percentile_of_sides(
        of_rows,
        against_rows,
        sorted(of_rows),
        sorted(against_rows),
        compute_of,
        compute_against,
        seed=7,
        draws=400,
    )
    assert set(seen_of) == {5}
    assert set(seen_against) == {25}
    assert len(seen_of) == 400 and len(seen_against) == 400
    assert got.draws_used == 400
    assert got.interval is not None
    assert got.interval.method == "unpaired_percentile_over_units"
    assert got.pool == sorted(got.pool)
    # CAPTURE-AND-PASTE: replace with this test's first green endpoints.
    assert [got.interval.low, got.interval.high] == pytest.approx([0.0, 0.0])


def test_the_unpaired_percentile_pool_is_the_evidence_a_corrected_bound_reads():
    """`interval_at` reads fixed ranks off a pool and does not sort, so a pool
    returned unsorted gives a corrected interval built from two arbitrary
    positions. Both return paths here sort, and the too-thin path sorts a partial
    pool for the same reason.

    Asserted through `interval_at` rather than on the list alone, because the
    property that matters is that a SECOND rank pair off the same pool is wider,
    not merely that a list is ordered."""
    of_rows = _side_rows(_WELCH_OF, "a")
    against_rows = _side_rows(_WELCH_AGAINST, "b")
    compute, _ = _row_count_recorder()
    other, _ = _row_count_recorder()
    got = unpaired_percentile_of_sides(
        of_rows, against_rows, sorted(of_rows), sorted(against_rows),
        compute, other, seed=7, draws=400,
    )
    assert got.interval is not None
    tighter = interval_at(got.pool, 0.975)
    assert tighter is not None
    assert tighter[0] <= got.interval.low and tighter[1] >= got.interval.high


def test_the_unpaired_percentile_refuses_only_when_both_sides_cannot_vary():
    """The AND rule, and it is the one a copied check gets wrong. Two constant
    sides make every replicate reproduce the same difference, so both percentile
    ranks land on it and the interval has zero width while looking exactly like a
    narrow one — the shape § Statistical reporting refuses in those terms. One
    constant side does NOT refuse: the other still varies, so the difference has a
    real sampling distribution, and an `or` here would null an interval that is
    fine.

    The one-sided case asserts a POSITIVE width rather than `is not None`, because
    a degenerate draw and a suppressed contrast both return `None` and only a width
    separates a real interval from either."""
    flat_of = _side_rows([3.0] * 5, "a")
    flat_against = _side_rows([1.0] * 25, "b")
    varied_against = _side_rows(_WELCH_AGAINST, "b")
    compute, _ = _row_count_recorder()
    other, _ = _row_count_recorder()
    both_flat = unpaired_percentile_of_sides(
        flat_of, flat_against, sorted(flat_of), sorted(flat_against),
        compute, other, seed=7, draws=400,
    )
    assert both_flat.interval is None
    assert both_flat.draws_used == 0
    assert both_flat.pool == []
    one_flat = unpaired_percentile_of_sides(
        flat_of, varied_against, sorted(flat_of), sorted(varied_against),
        compute, other, seed=7, draws=400,
    )
    assert one_flat.interval is not None
    assert one_flat.interval.high > one_flat.interval.low


def test_the_unpaired_percentile_refuses_a_side_below_two_keys():
    """`None` below two keys on either side, the floor every construction in this
    module shares. Asserted on both sides, because a guard reading `of_keys` alone
    passes the first case and fails nothing."""
    of_rows = _side_rows(_WELCH_OF, "a")
    against_rows = _side_rows(_WELCH_AGAINST, "b")
    compute, _ = _row_count_recorder()
    other, _ = _row_count_recorder()
    assert unpaired_percentile_of_sides(
        of_rows, against_rows, ["a00"], sorted(against_rows),
        compute, other, seed=7, draws=400,
    ).interval is None
    assert unpaired_percentile_of_sides(
        of_rows, against_rows, sorted(of_rows), ["b00"],
        compute, other, seed=7, draws=400,
    ).interval is None


def test_the_extracted_draw_pools_leaves_the_paired_draw_where_it_was():
    """The extraction is pure code motion and this is the oracle. The paired
    clustered draw over H4b-2's own 2/4/6 fixture must produce the same pool it
    produced before `_draw_pools` existed — an RNG sequence that changed by one
    call moves the percentiles without necessarily widening anything, so this
    asserts the ENDPOINTS rather than the width.

    Both raises move with the body and are re-pinned here: an unsorted `keys` under
    `strata` still raises `ValueError`, and a cluster spanning two strata still
    raises `E-STATS-RESAMPLE-STRATIFY-VARIES`."""
    keys = [f"u{i:02d}" for i in range(12)]
    values = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
    labels = ["a"] * 2 + ["b"] * 4 + ["c"] * 6
    of = {k: {"m": v} for k, v in zip(keys, values, strict=True)}
    against = {k: {"m": 0.0} for k in keys}
    compute, _ = _row_count_recorder()
    other, _ = _row_count_recorder()
    got = paired_percentile_of_derived(
        of, against, keys, compute, other, seed=7, draws=400,
        clusters=dict(zip(keys, labels, strict=True)),
    )
    assert got.interval is not None
    assert [got.interval.low, got.interval.high] == pytest.approx([1.0, 8.0])
    with pytest.raises(ValueError, match="sorted"):
        paired_percentile_of_derived(
            of, against, list(reversed(keys)), compute, other, seed=7, draws=400,
            strata={k: "s" for k in keys},
        )
    with pytest.raises(ContractError, match="E-STATS-RESAMPLE-STRATIFY-VARIES"):
        paired_percentile_of_derived(
            of, against, keys, compute, other, seed=7, draws=400,
            strata={k: ("x" if k == "u00" else "y") for k in keys},
            clusters=dict(zip(keys, labels, strict=True)),
        )
```

      Add `unpaired_percentile_of_sides` and `interval_at` to the import block;
      `paired_percentile_of_derived` and `ContractError` are already imported in that module —
      **confirm both by reading the import block rather than assuming.**

      **`[1.0, 8.0]` in the last test is the number `tests/test_cli.py::test_a_clustered_resampled_contrast_really_drew_clusters`
      already pins** for the same fixture, seed and draw count through
      `_comparison_step_blocks` — so it is a captured baseline and not an invention. Verify it holds
      by direct call before Step 3 and after.

- [ ] **Step 2: run and see them fail.** `uv run pytest tests/test_stats.py -k "unpaired_percentile or draw_pools"`
      → `ImportError` on `unpaired_percentile_of_sides`. The last test will pass, since it exercises
      only shipped behaviour — **that is correct and is the point**: it is a before-and-after oracle,
      green on both sides of the extraction, and its value is entirely in Step 5's mutation 4.

- [ ] **Step 3: extract `_draw_pools`.** Move `paired_percentile_of_derived`'s `items`/`pools`
      construction into a module-level function, verbatim including both raises and every comment
      inside them, placed immediately before `paired_percentile_of_derived`. Change only two things:
      **the `ValueError` message loses the function name** (`"paired_percentile_of_derived requires
      keys sorted ascending when strata is given, matching the contract `paired_keys` already
      satisfies"` → `"a percentile draw requires keys sorted ascending when strata is given,
      matching the contract this module's key functions already satisfy"`), and the docstring gains a
      sentence saying it has two callers and why one shape rather than two. `paired_percentile_of_derived`
      then reads:

```python
    if len(keys) < 2:
        return PairedResample(interval=None, draws_used=0, pool=[])
    rng = random.Random(seed)
    pools = _draw_pools(keys, strata, clusters)
```

      **Re-read `paired_percentile_of_derived`'s whole docstring after the move.** Its `strata` and
      `clusters` paragraphs argue for behaviour that now lives elsewhere; the claims are still true
      of the function, so **do not rewrite them** — a rewrite invents and this repo has re-seeded a
      claim three times that way. Only the `keys != sorted(keys)` paragraph's *"this function
      trusts `paired_keys`"* needs the pronoun to still have a referent.

- [ ] **Step 4: implement `_side_content` and `unpaired_percentile_of_sides`**, immediately after
      `paired_percentile_of_derived`:

```python
def _side_content(
    item: Sequence[str], rows: Mapping[str, Mapping[str, float]]
) -> tuple[tuple[tuple[str, float], ...], ...]:
    """What a drawable thing contributes to ONE side's draw, as a comparable value.

    `_drawable_content`'s single-sided counterpart: the row each of its keys
    carries, sorted, so two things with the same rows in a different key order are
    the same contribution. The keys are deliberately not in the value, for the
    reason that function gives — a draw that replaces one key with another carrying
    an identical row produces an identical table.

    Separate rather than a parameter on `_drawable_content`, because the unpaired
    draw's two sides hold DIFFERENT key sets and a signature taking both mappings
    could only be given one side's keys with the other's rows.
    """
    return tuple(sorted(tuple(sorted(rows[key].items())) for key in item))


def unpaired_percentile_of_sides(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    of_keys: list[str],
    against_keys: list[str],
    compute_of: "Callable[[UnitTable], float | None]",
    compute_against: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    strata: dict[str, str] | None = None,
    method: str = "unpaired_percentile_over_units",
    of_clusters: dict[str, str] | None = None,
    against_clusters: dict[str, str] | None = None,
) -> PairedResample:
    """Percentiles of the difference, resampling within each side independently.

    `reference.md` § Statistical reporting: "The percentiles of the difference,
    resampling within each side independently. The unpaired counterpart of the
    second."

    **This is a separate construction from `paired_percentile_of_derived` and not a
    `method` string over it.** That function draws ONE key list and applies it to
    both sides, and its docstring argues at length that drawing each side
    independently "would resample the two conditions apart and destroy the
    pairing" — which is exactly the arrangement this function's own definition
    requires, because the two sides here hold disjoint units and there is no
    pairing to destroy. Two spellings of two different constructions, not one
    construction serving two names.

    Two computes, not one, for `paired_percentile_of_derived`'s own reason: a
    contrast's two sides can hold their `cfg` fixed on every axis except the one
    being compared, and `aggregate(units, cfg)` is evaluated once per side with
    that side's own `cfg`.

    `method` names the `Interval` the caller gets back rather than being derived
    from a parameter here: one construction serves the plain and the `_clustered`
    spelling, and the arithmetic that picks between them lives in the caller.

    `strata` resamples within each stratum, per side. `of_clusters`/
    `against_clusters` make the drawable thing a whole cluster within its own side
    — `reference.md` § Statistical reporting: "the percentile forms resample whole
    clusters", the "jointly across both sides" qualifier being the paired case's.
    Two mappings rather than one, because the two sides' key sets are disjoint and
    a single mapping would be indexed with keys it does not hold. Both compose with
    `strata` through `_draw_pools`, which is where every one of those rules lives.

    **The degenerate refusal is per side and it is AND.** Where every drawable thing
    in every stratum of BOTH sides carries the same row, every replicate reproduces
    the same difference, both percentile ranks land on it, and the interval has zero
    width while looking exactly like a narrow one — which § Statistical reporting
    refuses in those terms. Where only one side cannot vary the difference still
    can, so there is a real interval to report and refusing it would be the same
    defect in the opposite direction. Content, not count: two clusters per stratum
    carrying identical rows clear any count floor and are still degenerate.

    `PairedResample(interval=None, draws_used=0, pool=[])` below two keys on either
    side, the floor every construction here shares. The pool is sorted on both
    return paths, because `interval_at` reads fixed ranks off it and does not sort.
    """
    if len(of_keys) < 2 or len(against_keys) < 2:
        return PairedResample(interval=None, draws_used=0, pool=[])
    rng = random.Random(seed)
    of_pools = _draw_pools(of_keys, strata, of_clusters)
    against_pools = _draw_pools(against_keys, strata, against_clusters)
    if all(
        len({_side_content(item, of) for item in group}) <= 1 for group in of_pools
    ) and all(
        len({_side_content(item, against) for item in group}) <= 1
        for group in against_pools
    ):
        return PairedResample(interval=None, draws_used=0, pool=[])
    values: list[float] = []
    for _ in range(draws):
        # TWO draws per replicate, `of` first and `against` second, each over its
        # own side's pools — which is what "resampling within each side
        # independently" means, and the one thing this construction does that
        # `paired_percentile_of_derived` refuses to do.
        drawn_of = [
            key
            for group in of_pools
            for _ in range(len(group))
            for key in group[rng.randrange(len(group))]
        ]
        drawn_against = [
            key
            for group in against_pools
            for _ in range(len(group))
            for key in group[rng.randrange(len(group))]
        ]
        table_of = unit_table_from_rows([{"unit": k, **of[k]} for k in drawn_of])
        table_against = unit_table_from_rows(
            [{"unit": k, **against[k]} for k in drawn_against]
        )
        try:
            a = compute_of(table_of)
            b = compute_against(table_against)
        # A degenerate draw, not a fault; see `percentile_of_derived`. Also the same
        # containment for a template returning a non-numeric metric, which reaches
        # `cli.py`'s resample closure and raises `ValueError` from `float()`.
        except Exception:
            continue
        if a is None or b is None:
            continue
        diff = float(a) - float(b)
        if math.isnan(diff):
            continue
        values.append(diff)
    if len(values) < min_honest_draws(confidence):
        return PairedResample(interval=None, draws_used=len(values), pool=sorted(values))
    values.sort()
    lo, hi = _percentile_ranks(len(values), confidence)
    return PairedResample(
        interval=Interval(low=values[lo], high=values[hi], method=method),
        draws_used=len(values),
        pool=values,
    )
```

- [ ] **Step 5: capture the endpoints and paste them in.** Run
      `uv run pytest tests/test_stats.py -k unpaired_percentile` and read the actual endpoints out of
      the failure on the `CAPTURE-AND-PASTE` line. Replace `[0.0, 0.0]` with them **in this same
      commit**, and delete the `CAPTURE-AND-PASTE` comment. This is the only honest order: the
      construction did not exist when this plan was written, so a stated literal would have been
      invented rather than computed.

- [ ] **Step 6: run and see them pass.** `uv run pytest` → **2215 + 5 = 2220 passed**, 1 skipped,
      2 xfailed. Then the other three gates.

- [ ] **Step 7: mutate — four mutations.**

      **Mutation 1 — one draw for both sides.** Replace `drawn_against`'s comprehension with
      `drawn_of`. `test_the_unpaired_percentile_draws_each_side_independently` must **FAIL** on
      `set(seen_against) == {25}`, seeing `{5}` — and it fails on the SIZE rather than on the
      interval, which is the whole reason the row-count recorder exists. **Checked against the test
      body:** `drawn_of` holds 5 keys and `against` is indexed by them, so this raises `KeyError`
      inside the `try` and every replicate is dropped — `draws_used` becomes 0 and the interval
      `None`. Either failure is attributable; the size assertion is the readable one.

      **Mutation 2 — a pooled draw.** Replace both comprehensions with a single draw over
      `of_pools + against_pools` split at `len(of_keys)`. The same test must **FAIL** on the sizes.
      This is the mutant an interval assertion alone cannot see, because a pooled draw still
      produces a plausible number centred near 10.

      **Mutation 3 — the degenerate rule's connective.** Change the `and` between the two `all(...)`
      expressions to `or`. `test_the_unpaired_percentile_refuses_only_when_both_sides_cannot_vary`
      must **FAIL** on the one-flat case, which now returns `interval=None` where a real interval
      exists. **Checked against the test body:** `flat_of` is five identical rows, so its own
      `all(...)` is `True`, and `varied_against` holds three distinct values, so its own is `False` —
      the two connectives genuinely differ on this fixture, which a fixture with two varied sides
      could not show.

      **Mutation 4 — the extraction.** In `_draw_pools`, change the unclustered branch's
      `items = [[key] for key in keys]` to `items = [[key] for key in reversed(keys)]`.
      `test_the_extracted_draw_pools_leaves_the_paired_draw_where_it_was` must **FAIL** on the
      endpoints, **and** task 21's `plain_percentile` and `clustered_percentile` cells must **FAIL**
      on `ci95`. **Checked:** the draw indexes `items` by a fixed RNG sequence, so reversing the
      order draws a different multiset on nearly every replicate.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 8: Commit.**

```bash
git add src/publishable/stats.py tests/test_stats.py
git commit -m "feat: unpaired_percentile_of_sides — two independent draws, and one draw-pool construction for both percentile contrasts"
```

---

## Task 7: `stats.welch_t_over_units_clustered`, and the CR1 variance extracted from its sibling

**Runs after task 4.** Its df is Welch-Satterthwaite over the two per-side cluster-robust variances,
each side contributing `G_s` − 1 — task 1's ruling 4, and the clause task 1 added to
§ Statistical reporting is what licenses code to emit it at all.

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `stats.t_over_units_clustered(values, keys, membership, confidence=0.95)`, whose CR1
  body computes `groups = cluster_count_of(membership, keys)`, one residual sum per cluster,
  `meat = sum(s * s for s in scores.values())` and
  `variance = (groups / (groups - 1)) * meat / (n * n)` with `df = groups - 1` — read in
  `src/publishable/stats.py`; `units.cluster_count_of(membership, keys)`, the single counting
  expression; `stats._t_critical`.
- Produces:

```python
def _cr1_variance(
    values: Sequence[float], keys: Sequence[str], membership: Mapping[str, str]
) -> tuple[float, int] | None

def welch_t_over_units_clustered(
    of: Sequence[float],
    of_labels: Sequence[str],
    against: Sequence[float],
    against_labels: Sequence[str],
    confidence: float = 0.95,
) -> Interval | None
```

  `welch_t_over_units_clustered` is called by `correction._corrected_bounds` (task 12) and
  `cli._comparison_step_blocks` (task 14). `_cr1_variance` is **extracted from
  `t_over_units_clustered`**, which is rewired to call it, and is called twice here.

**A disagreement with the scoping, and it changes this task's shape.** `H4c-SCOPING.md` § 3 says
`welch_t_over_units_clustered` *"can follow `paired_t_over_units_clustered` into
`t_over_units_clustered`'s CR1 machinery rather than deriving a cluster-robust variance from
scratch"*. **It cannot, as that function stands**: `t_over_units_clustered` returns an `Interval`,
and a Welch form needs the two per-side **variances and cluster counts** — recoverable from an
`Interval` only by inverting `_t_critical`, which is not a construction anybody should write. So the
machinery is **extracted** into `_cr1_variance` first, and the scoping's intent is honoured exactly:
one CR1 expression, three callers, no second sandwich. Recorded in the spec's § Corrections against
the code.

**`labels` per side, not `keys` + `membership`.** Both callers hold a per-side value vector and a
per-side label vector and nothing else — `correction.UnpairedEvidence` carries exactly that pair
(task 11) — and `paired_t_over_units_clustered` set this precedent one axis over. The positional keys
synthesized inside are a **bijection, not a proxy**: `_cr1_variance` uses a key for exactly one thing,
looking its label up and counting the distinct labels through `units.cluster_count_of`, so distinct
synthetic keys carrying these labels are the same input digit for digit.

**A clustered interval that is merely wider proves NOTHING.** Under positive within-cluster
correlation a cluster-robust interval comes out wider whatever df it uses —
`t_over_units_clustered`'s own docstring says so. **Only the number is evidence**, and fixture B is
sized so five wrong readings give five other numbers, the tightest 4.4 % away, with the correct one
the extreme of no single dimension.

- [ ] **Step 1: write the failing tests.** Append to `tests/test_stats.py`:

```python
_CLUSTERED_OF = [0.0] * 2 + [15.0] * 3 + [30.0] * 4
_CLUSTERED_OF_LABELS = ["p"] * 2 + ["q"] * 3 + ["r"] * 4
_CLUSTERED_AGAINST = [2.0] * 2 + [4.0] * 3 + [6.0] * 3 + [8.0] * 4
_CLUSTERED_AGAINST_LABELS = ["w"] * 2 + ["x"] * 3 + ["y"] * 3 + ["z"] * 4


def test_the_unpaired_clustered_t_combines_two_per_side_cluster_dfs():
    """Fixture B: `of` is 9 units in 3 clusters of 2/3/4 constant within cluster at
    0/15/30, `against` 12 units in 4 clusters of 2/3/3/4 at 2/4/6/8. Values
    constant within a cluster make each side's variance entirely BETWEEN-cluster,
    so CR1 cannot approximate the IID form; the sizes are unequal so no count
    assertion is forced; and the two cluster counts differ, 3 against 4, so a
    construction reading one side's count writes a wrong integer.

    Per-side CR1 variances 67.0782 (G = 3) and 1.5880 (G = 4), SE 8.2865,
    Welch-Satterthwaite df over `G_s` − 1 = 2.0950, half-width 34.1481. Five wrong
    readings give five other numbers: `min(G) − 1` gives 35.6540, `G_against − 1`
    gives 26.3714, `G_total − 2` gives 21.3011, `n_of + n_against − 2` gives
    17.3439, and the IID Welch form on the identical data gives 9.6472. **The
    correct answer is above one of them and below four**, so an assertion on the
    number discriminates every failure mode, which an assertion on "is it wider"
    does not."""
    interval = welch_t_over_units_clustered(
        _CLUSTERED_OF,
        _CLUSTERED_OF_LABELS,
        _CLUSTERED_AGAINST,
        _CLUSTERED_AGAINST_LABELS,
    )
    assert interval is not None
    assert interval.method == "welch_t_over_units_clustered"
    centre = (interval.low + interval.high) / 2
    half = (interval.high - interval.low) / 2
    assert centre == pytest.approx(12.833333333333332)
    assert half == pytest.approx(34.14810237373095)


def test_the_unpaired_clustered_t_is_not_the_iid_welch_form_on_the_same_data():
    """The control that must report, and the number a membership-ignoring mutant
    lands on. The IID Welch form over the identical values gives 9.6472 — three and
    a half times narrower, at the same centre. **A test asserting the centre alone
    is blind to clustering entirely**, which is why the centre is asserted only
    beside the half-width above."""
    plain = welch_t_over_units(_CLUSTERED_OF, _CLUSTERED_AGAINST)
    assert plain is not None
    assert (plain.high - plain.low) / 2 == pytest.approx(9.647234756296374)


def test_the_unpaired_clustered_t_refuses_a_side_below_two_clusters():
    """Both floors, per side: `None` below two values and `None` below two clusters,
    where that side's df would be zero. The second is the one a singleton-cluster
    fixture can never see — one unit per cluster makes `G − 1` equal `n − 1`, so
    the clustered and IID forms coincide exactly and every assertion passes under a
    mutant ignoring membership. Hence the last case, which is correct and is
    exactly why no other test here may use that shape."""
    assert welch_t_over_units_clustered(
        _CLUSTERED_OF, ["p"] * 9, _CLUSTERED_AGAINST, _CLUSTERED_AGAINST_LABELS
    ) is None
    assert welch_t_over_units_clustered(
        _CLUSTERED_OF, _CLUSTERED_OF_LABELS, _CLUSTERED_AGAINST, ["w"] * 12
    ) is None
    singletons = welch_t_over_units_clustered(
        _CLUSTERED_OF,
        [f"p{i}" for i in range(9)],
        _CLUSTERED_AGAINST,
        [f"w{i}" for i in range(12)],
    )
    iid = welch_t_over_units(_CLUSTERED_OF, _CLUSTERED_AGAINST)
    assert singletons is not None and iid is not None
    assert (singletons.high - singletons.low) == pytest.approx(iid.high - iid.low)


def test_the_extracted_cr1_variance_leaves_the_clustered_t_where_it_was():
    """The extraction is pure code motion and this is the oracle. H4b-2's own 2/4/6
    fixture through `t_over_units_clustered` must give the half-width it gave
    before `_cr1_variance` existed — 8.763214143637903, which
    `tests/test_stats.py`'s paired clustered test already pins independently.

    The `G/(G−1)` finite-sample scaling is what a careless move drops, and dropping
    it is not a rounding difference: it is the CR0 estimator wearing CR1's name,
    biased downward by exactly the factor a small cluster count makes largest."""
    diffs = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
    labels = ["a"] * 2 + ["b"] * 4 + ["c"] * 6
    keys = [str(i) for i in range(12)]
    plain = t_over_units_clustered(diffs, keys, dict(zip(keys, labels, strict=True)))
    assert plain is not None
    assert (plain.high - plain.low) / 2 == pytest.approx(8.763214143637903)
    got = _cr1_variance(diffs, keys, dict(zip(keys, labels, strict=True)))
    assert got is not None
    variance, groups = got
    assert groups == 3
    assert variance == pytest.approx((3 / 2) * 398.22222222222223 / (12 * 12))
```

      Add `welch_t_over_units_clustered` and `_cr1_variance` to the import block;
      `t_over_units_clustered` is already imported — confirm by reading.

- [ ] **Step 2: run and see them fail.** `uv run pytest tests/test_stats.py -k "unpaired_clustered or cr1_variance"`
      → `ImportError`. The extraction oracle's first two assertions pass already; that is correct.

- [ ] **Step 3: extract `_cr1_variance`** immediately before `t_over_units_clustered`, and rewire
      that function to call it. The extracted body is verbatim today's, including every comment:

```python
def _cr1_variance(
    values: Sequence[float], keys: Sequence[str], membership: Mapping[str, str]
) -> tuple[float, int] | None:
    """The CR1 sandwich variance of the mean, and the cluster count its df reads.

    One expression for the cluster-robust variance, and three callers:
    `t_over_units_clustered` puts it in a per-condition interval,
    `paired_t_over_units_clustered` reaches it through that one, and
    `welch_t_over_units_clustered` combines two of them. A second sandwich is how a
    paired interval and a per-condition one come to disagree about what
    cluster-robust means, which is the argument `paired_t_over_units_clustered`'s
    docstring already makes for delegating rather than hand-rolling — and a Welch
    form cannot delegate to `t_over_units_clustered` itself, because it needs the
    variance and the count and that function returns an `Interval`.

    The model core fits is the mean, so the sandwich is the intercept-only case:
    with `X'X = n` and a cluster's score `S_g = Σ_{i∈g}(v_i − v̄)`, the variance of
    the mean is `Σ_g S_g² / n²` before scaling. **The finite-sample scaling is the
    `G/(G−1)` factor**, and dropping it is not a rounding difference — it is the CR0
    estimator wearing this one's name, biased downward by exactly the factor a small
    cluster count makes largest. The two literature conventions for CR1 coincide
    here, since `k` is 1 for a mean.

    `None` below two values or below two clusters: the df every caller derives from
    the count would be zero, and each caller's own floor is that same refusal
    reported in its own terms. Returning the count rather than only the variance is
    what lets a Welch caller give each side `G_s − 1` df without recounting.

    The membership mapping is `units.clusters_of`'s, passed whole rather than
    pre-resolved, and the count comes from `units.cluster_count_of` — the single
    counting expression, so no df here can disagree with the `n.clusters` printed
    beside it. Indexed rather than `.get`-ed: a key the roster doesn't hold is a
    core defect, and absorbing it into a cluster of its own would raise `G` and
    narrow the interval. `strict=True` on the zip, because a keys/values length
    mismatch is a misaligned cluster vector and would produce a plausible number
    rather than an error.
    """
    n = len(values)
    if n < 2:
        return None
    groups = cluster_count_of(membership, keys)
    if groups < 2:
        return None
    mean = sum(values) / n
    # One residual sum per cluster: what makes this robust is that the residuals
    # are added up WITHIN a cluster before being squared, so correlated units
    # reinforce each other instead of counting as independent draws.
    scores: dict[str, float] = {}
    for key, value in zip(keys, values, strict=True):
        label = membership[key]
        scores[label] = scores.get(label, 0.0) + (value - mean)
    meat = sum(s * s for s in scores.values())
    return (groups / (groups - 1)) * meat / (n * n), groups
```

      `t_over_units_clustered`'s body becomes:

```python
    n = len(values)
    if n < 2:
        return None
    got = _cr1_variance(values, keys, membership)
    if got is None:
        return None
    variance, groups = got
    mean = sum(values) / n
    half = _t_critical(groups - 1, confidence) * math.sqrt(variance)
    return Interval(low=mean - half, high=mean + half, method="t_over_units_clustered")
```

      **Re-read `t_over_units_clustered`'s whole docstring after the move**, and move the paragraphs
      that describe the sandwich, the `G/(G−1)` scaling and the two conventions **into**
      `_cr1_variance` rather than duplicating them — a claim standing in two places is how one gets
      corrected and the other does not. What stays is the df-is-the-construction paragraph, the two
      floors as this function reports them, and the membership-mapping paragraph. **Prefer deleting
      to rewriting**: anything that has genuinely moved is deleted here, not paraphrased.
      `weighted_t_over_units_clustered` is deliberately **not** rewired — its scores carry weights
      and its bread is `1/Σw`, a different expression — and its docstring's *"The sandwich is
      `t_over_units_clustered`'s with the weights in the score"* stays true.

- [ ] **Step 4: implement `welch_t_over_units_clustered`**, immediately after
      `welch_t_over_units`:

```python
def welch_t_over_units_clustered(
    of: Sequence[float],
    of_labels: Sequence[str],
    against: Sequence[float],
    against_labels: Sequence[str],
    confidence: float = 0.95,
) -> Interval | None:
    """Cluster-robust (CR1) Welch *t* on two independent condition means.

    `reference.md` § Statistical reporting's suffix rule: under a declared
    `cluster_by` each unweighted contrast construction "takes a `_clustered` suffix
    and reads the cluster as the draw", the *t* forms being cluster-robust (CR1)
    "over the differenced values when paired and over the arm-level ones when not"
    — this is the "when not" half. The design it is load-bearing for is
    § Clustered units' matched case-control: "The contrast stays unpaired, since no
    unit appears in both arms, but its interval is cluster-robust on the matched
    set — so the effective `n` is the number of sets rather than the number of
    subjects, which is the accounting a matched design needs."

    **The df is Welch-Satterthwaite over the two cluster-robust per-side variances,
    each side contributing `G_s` − 1**, which § Statistical reporting states since
    H4c and which code could not emit before it did. The substitution the suffix
    rule describes happens inside each side's own variance and its own df, and
    combining them is what the unclustered Welch form already does. Two readings
    are rejected rather than merely unused: `min(G_of, G_against) − 1` discards a
    side's information and contradicts "df = clusters − 1" on the side it discards,
    and `G_total − 2` is the **pooled** reading `welch_t_over_units` refuses by
    construction.

    **A cluster-robust interval that is merely wider is not evidence the cluster
    count reached the critical value.** Over positively correlated data it comes out
    wider whatever df it uses — `t_over_units_clustered` says so — so only the
    number is evidence, and a fixture whose two sides carry the same cluster count
    cannot see a construction reading one side's.

    `of_labels`/`against_labels` are one cluster label per value, in the same order,
    per side, rather than the `keys` + `membership` pairs the per-condition form
    takes: both callers hold two per-side vectors and nothing else, and
    `correction.UnpairedEvidence` carries exactly that pair. The positional keys
    synthesized below are a **bijection**, not a proxy — `_cr1_variance` uses a key
    only to look its label up and to count distinct labels — and the two sides get
    disjoint synthetic key spaces so neither side's count can read the other's.

    `None` below two values or below two clusters on **either** side, both inherited
    from `_cr1_variance`: that side's df would be zero. `None` also where both
    variances are zero, for the reason `welch_t_over_units` gives — the df is then
    0/0 — which a fixture with values constant within cluster but varying across
    clusters cannot reach.
    """
    of_keys = [f"of{i}" for i in range(len(of))]
    against_keys = [f"ag{i}" for i in range(len(against))]
    got_of = _cr1_variance(of, of_keys, dict(zip(of_keys, of_labels, strict=True)))
    got_against = _cr1_variance(
        against, against_keys, dict(zip(against_keys, against_labels, strict=True))
    )
    if got_of is None or got_against is None:
        return None
    var_of, groups_of = got_of
    var_against, groups_against = got_against
    total = var_of + var_against
    if total <= 0.0:
        return None
    # Welch-Satterthwaite with each side's df taken from its OWN cluster count —
    # the substitution the suffix rule makes, applied inside each side's variance
    # and its df rather than to the combination.
    df = total * total / (
        var_of * var_of / (groups_of - 1)
        + var_against * var_against / (groups_against - 1)
    )
    delta = sum(of) / len(of) - sum(against) / len(against)
    half = _t_critical(df, confidence) * math.sqrt(total)
    return Interval(
        low=delta - half, high=delta + half, method="welch_t_over_units_clustered"
    )
```

- [ ] **Step 5: run and see them pass.** `uv run pytest` → **2220 + 4 = 2224 passed**, 1 skipped,
      2 xfailed. Then the other three gates.

- [ ] **Step 6: mutate — five mutations, and one named blind.**

      **Do not prescribe reversing one side's label vector.** On fixture B the `of` side's labels
      `p p q q q r r r r` reversed become `r r r r q q q p p`, which maps a **different** partition
      onto the same values and gives a different meat — so it does discriminate. But the
      `against` side's `w w x x x y y y z z z z` reversed gives sizes 4/3/3/2 over values 8/6/4/2,
      whose per-cluster residual sums are the same multiset with signs preserved by symmetry of that
      fixture's spacing. **Verify by running before prescribing either**, and record the two numbers
      in the task report; a mutation whose two branches cannot differ is a claim, and this one is
      not settled by reading.

      **Mutation 1 — the df onto one side's count.** Change `df` to `groups_of - 1`.
      `test_the_unpaired_clustered_t_combines_two_per_side_cluster_dfs` must **FAIL** with
      35.653950021811816 — **above** the correct answer, which is what makes an assertion on the
      number rather than on width necessary.

      **Mutation 2 — the df onto the other side's count.** Change `df` to `groups_against - 1`. The
      same test must **FAIL** with 26.371354753115764, below correct. Mutations 1 and 2 fail on
      opposite sides, and fixture B's `3` against `4` is what makes them two different numbers at
      all — the documented *"both 3"* failure closed by construction.

      **Mutation 3 — the pooled df.** Change `df` to `groups_of + groups_against - 2`. The same test
      must **FAIL** with 21.301137240534675.

      **Mutation 4 — the IID variance.** Replace both `_cr1_variance` calls with
      `_sample_variance(...) / n` per side. The same test must **FAIL** with 9.647234756296374, the
      number `test_the_unpaired_clustered_t_is_not_the_iid_welch_form_on_the_same_data`
      independently pins — the pair rather than a repetition.

      **Mutation 5 — the extraction's scaling.** In `_cr1_variance`, drop the `(groups / (groups -
      1))` factor. `test_the_extracted_cr1_variance_leaves_the_clustered_t_where_it_was` must
      **FAIL** on both of its numeric assertions, **and** task 21's `clustered_t` cell must **FAIL**
      on `ci95` and `ci95_corrected` — the pair that says the extraction is watched from inside
      `stats.py` and from the record at once.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 7: Commit.**

```bash
git add src/publishable/stats.py tests/test_stats.py
git commit -m "feat: welch_t_over_units_clustered, and one CR1 variance expression for its three callers"
```

---

## Task 8: the `_clustered` percentile spelling, per side

**Runs after task 6**, whose construction this is a second `method=` spelling and a second pair of
cluster mappings over — **not a second function**. The parameters already exist from task 6; what
this task adds is the test that the clustered draw is really a clustered draw, and the `method`
string's licence.

**Files:**
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `stats.unpaired_percentile_of_sides(..., method=, of_clusters=, against_clusters=)`
  (task 6); `stats._draw_pools`' clustered branch, which groups keys by label and orders the groups
  by their own sorted contents.
- Produces: nothing new in `src/`. The spelling `unpaired_percentile_over_units_clustered` becomes
  live, and task 14 is what passes it.

**Why this is a task rather than a paragraph in task 6.** The `method` string and the draw are **two
claims**, and H4b-2's own experience is the precedent: a `method` naming a construction the draw did
not perform is the failure this slice is ordered around. Task 6 pins the plain draw's size; this task
pins that whole clusters are drawn, by the only evidence available at this level — **the row count
varies across replicates**, because a large cluster contributes more rows than a small one.

- [ ] **Step 1: write the failing tests.** Append to `tests/test_stats.py`, after task 7's:

```python
def test_the_unpaired_clustered_percentile_draws_whole_clusters_per_side():
    """Fixture B through the percentile form. `of` holds clusters of 2/3/4, so a
    replicate drawing 3 clusters with replacement pools between 6 and 12 rows; a
    mutant drawing UNITS returns a fixed 9. `against` holds 2/3/3/4 and varies
    between 8 and 16 against a fixed 12.

    **The varying row count is the assertion**, not the interval: equal cluster
    sizes would make "a replicate's pooled row count varies" invisible and a
    unit-drawing mutant would never be seen, which is why fixture B's clusters are
    unequal in size within each side as well as unequal in count between them.

    The two sides are asserted separately, because a construction passing
    `of_clusters` to both sides would give the `against` side `of`'s sizes and a
    single pooled assertion would not notice."""
    of_rows = {f"of{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_OF)}
    against_rows = {f"ag{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_AGAINST)}
    of_clusters = dict(zip(sorted(of_rows), _CLUSTERED_OF_LABELS, strict=True))
    against_clusters = dict(
        zip(sorted(against_rows), _CLUSTERED_AGAINST_LABELS, strict=True)
    )
    compute_of, seen_of = _row_count_recorder()
    compute_against, seen_against = _row_count_recorder()
    got = unpaired_percentile_of_sides(
        of_rows,
        against_rows,
        sorted(of_rows),
        sorted(against_rows),
        compute_of,
        compute_against,
        seed=7,
        draws=400,
        method="unpaired_percentile_over_units_clustered",
        of_clusters=of_clusters,
        against_clusters=against_clusters,
    )
    assert got.interval is not None
    assert got.interval.method == "unpaired_percentile_over_units_clustered"
    assert len(set(seen_of)) > 1  # a unit draw would give exactly {9}
    assert min(seen_of) >= 6 and max(seen_of) <= 12
    assert 9 not in {min(seen_of), max(seen_of)} or len(set(seen_of)) > 1
    assert len(set(seen_against)) > 1  # a unit draw would give exactly {12}
    assert min(seen_against) >= 8 and max(seen_against) <= 16
    # CAPTURE-AND-PASTE: replace with this test's first green endpoints.
    assert [got.interval.low, got.interval.high] == pytest.approx([0.0, 0.0])


def test_the_unpaired_clustered_percentile_is_not_the_unclustered_one():
    """The control that must report. The same rows drawn as units give a different
    interval, and the endpoints of both are pinned as literals rather than compared
    only for inequality — `!=` alone passes for any third wrong pair, and it is the
    weak-discriminator shape this slice bans by name."""
    of_rows = {f"of{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_OF)}
    against_rows = {f"ag{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_AGAINST)}
    compute, _ = _row_count_recorder()
    other, _ = _row_count_recorder()
    unclustered = unpaired_percentile_of_sides(
        of_rows, against_rows, sorted(of_rows), sorted(against_rows),
        compute, other, seed=7, draws=400,
    )
    assert unclustered.interval is not None
    assert unclustered.interval.method == "unpaired_percentile_over_units"
    # CAPTURE-AND-PASTE: replace with this test's first green endpoints.
    assert [unclustered.interval.low, unclustered.interval.high] == pytest.approx([0.0, 0.0])


def test_the_unpaired_clustered_percentile_is_invariant_to_relabelling():
    """`_draw_pools` orders clusters by their own sorted contents rather than by
    label, so a relabelled roster draws the identical sequence — the invariance
    `percentile_over_units_clustered` keeps and the one a `sorted(by_cluster)` over
    LABELS would silently break. Asserted on the endpoints, which is the only place
    a changed draw sequence shows."""
    of_rows = {f"of{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_OF)}
    against_rows = {f"ag{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_AGAINST)}
    renamed = {"p": "zz", "q": "aa", "r": "mm"}
    first, second = [], []
    for labels in (_CLUSTERED_OF_LABELS, [renamed[x] for x in _CLUSTERED_OF_LABELS]):
        compute, _ = _row_count_recorder()
        other, _ = _row_count_recorder()
        got = unpaired_percentile_of_sides(
            of_rows, against_rows, sorted(of_rows), sorted(against_rows),
            compute, other, seed=7, draws=400,
            method="unpaired_percentile_over_units_clustered",
            of_clusters=dict(zip(sorted(of_rows), labels, strict=True)),
            against_clusters=dict(
                zip(sorted(against_rows), _CLUSTERED_AGAINST_LABELS, strict=True)
            ),
        )
        assert got.interval is not None
        (first if labels is _CLUSTERED_OF_LABELS else second).append(
            [got.interval.low, got.interval.high]
        )
    assert first == second
```

- [ ] **Step 2: run.** The first two tests fail on their `CAPTURE-AND-PASTE` lines; the third should
      pass. Capture the endpoints from the failures and paste them in **in this same commit**, then
      delete the `CAPTURE-AND-PASTE` comments — the same order task 6's Step 5 uses, and for the same
      reason.

      **Read the third assertion of the first test before keeping it.**
      `assert 9 not in {min(seen_of), max(seen_of)} or len(set(seen_of)) > 1` is a tautology once the
      previous assertion holds — its right arm is already asserted — so **delete it** rather than
      ship an assertion that cannot fail. It is written here so the implementer deletes it
      deliberately rather than leaving it as an assertion the suite counts and nothing checks; this
      is the *"an assertion implied by another in the same test"* shape, and naming it is cheaper
      than a review round.

- [ ] **Step 3: run the gates.** `uv run pytest` → **2224 + 3 = 2227 passed**, 1 skipped,
      2 xfailed. Then the other three.

- [ ] **Step 4: mutate — three mutations.**

      **Mutation 1 — units instead of clusters.** In `stats._draw_pools`, change the clustered
      branch's `items = sorted(sorted(group) for group in by_cluster.values())` to
      `items = [[key] for key in sorted(keys)]`.
      `test_the_unpaired_clustered_percentile_draws_whole_clusters_per_side` must **FAIL** on
      `len(set(seen_of)) > 1`, seeing `{9}`. **Checked against the test body:** a unit draw takes
      exactly 9 keys every replicate, so the recorded set is a singleton and the assertion is on
      exactly that. **This mutation also breaks the paired clustered form**, so task 21's
      `clustered_percentile` cell and `tests/test_cli.py::test_a_clustered_resampled_contrast_really_drew_clusters`
      must fail too — which is the point: one draw shape, one mutation, three tests.

      **Mutation 2 — one side's mapping for both.** In `unpaired_percentile_of_sides`, change
      `_draw_pools(against_keys, strata, against_clusters)` to
      `_draw_pools(against_keys, strata, of_clusters)`. The same test must **FAIL** — `of_clusters`
      is keyed on `of`-side keys, so `_draw_pools`' indexed `clusters[key]` raises `KeyError`.
      **That is a raise rather than a wrong number, and it is worth saying so**: the two sides' key
      spaces being disjoint is what converts this class of mistake from a plausible number into an
      error, which is the property the two-mapping signature buys.

      **Mutation 3 — ordering by label.** In `stats._draw_pools`, change the clustered branch to
      `items = [sorted(by_cluster[label]) for label in sorted(by_cluster)]`.
      `test_the_unpaired_clustered_percentile_is_invariant_to_relabelling` must **FAIL** — the
      renamed labels `zz/aa/mm` sort differently from `p/q/r`, so the group order changes and the
      draw sequence with it. **Checked against the fixture:** `sorted(["p","q","r"])` is the
      insertion order while `sorted(["zz","aa","mm"])` is not, so the two arrangements genuinely
      differ. A two-cluster fixture could not show this — with two labels the reverse of insertion
      order *is* sorted order for one arrangement — which is why the `of` side has three.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 5: Commit.**

```bash
git add tests/test_stats.py
git commit -m "test: the unpaired clustered percentile spelling, its per-side draw sizes, and its relabelling invariance"
```

---
## Task 9: mint `E-DATA-WEIGHT-ALLOCATION-CONTRAST`, and the shared pairing predicate it fires through

**Runs after task 1**, whose sentence in § Statistical reporting this completes with the guard and
both rows. **Before task 18**, or the combination falls through to an unweighted number silently the
moment the allocation refusal is deleted. **This task also mints decision 7's shared pairing
predicate** — see deviation (b): its guard is the predicate's **first** caller and task 13's
derivation the second.

**Files:**
- Modify: `src/publishable/contrasts.py`
- Modify: `src/publishable/validate.py`
- Modify: `docs/reference.md`
- Test: `tests/test_contrasts.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `contrasts.differing_axes(of, against) -> list[str]`, which walks the union of both
  sides' `values` keys with a sentinel `.get`; `sweep.Condition.selectors: frozenset[str]`, the
  paths that select **units** rather than set a parameter, set by `expand` because it is the only
  place that knows which mode produced a cell; `validate._check_sweep`'s existing
  `for comp in resolved_contrasts` loop, which builds `conditions_by_index`, calls
  `differing_axes`, intersects with `of_cond.selectors | against_cond.selectors` and `continue`s on
  an empty result; `weight_by = units_here.get("weight_by")`, already bound in the same function
  above the `E-DATA-WEIGHT-CLUSTER-CONTRAST` guard — all read in `src/publishable/`.
- Produces:

```python
def crossed_group_axes(of: "Condition", against: "Condition") -> list[str]
```

  in `contrasts.py`, returning the declared group axes the two conditions disagree on, **in sweep
  declaration order**, empty exactly when the comparison is paired. Called by `validate._check_sweep`
  here, by `cli._comparison_step_blocks` in tasks 10 and 13. Plus the new error code, its § Errors
  row and its § Validation row.

**Why one function with two callers, and why `contrasts.py`.** Decision 7: *"Two spellings of one rule
drifting apart is a defect this codebase has already shipped, and here the drift would be `validate`
refusing a shape `cli` records as paired."* `contrasts.py` is the home because `cli` imports
`publishable.validate` at module scope, so `validate` importing `cli` back is a true cycle, and
`contrasts` sits below both — `differing_axes`' own docstring already makes exactly this argument,
and `Condition` is already its `TYPE_CHECKING` import. **Do not relocate it.**

**It returns the list, not a boolean.** `validate`'s message names the axes and pluralizes on their
count; `cli` reads emptiness. A boolean would force `validate` to recompute the list from a second
expression, which is the drift this function exists to prevent.

**Two calls to `differing_axes` per comparison, and that is deliberate.** `cli` needs `differs_on`
for `confounded` and this predicate needs its own intersection. A signature taking a precomputed
`differs_on` would let a caller pass a list computed from different conditions, which is the
misaligned-input class that produces a plausible answer rather than an error.

- [ ] **Step 1: write the failing tests.** In `tests/test_contrasts.py`:

```python
def test_crossed_group_axes_is_empty_for_a_within_arm_comparison():
    """The predicate `validate` refuses on and `cli` derives `paired` from, and it
    must be ONE expression: a `validate` that refused a shape `cli` recorded as
    paired is the drift this function exists to prevent.

    Two conditions differing only on a parameter axis share their arm's units, so
    the list is empty — which is what "paired" means here, whatever `allocation`
    itself is declared as. `selectors` is what distinguishes a group path from a
    parameter path, and it is carried on the condition rather than re-derived."""
    of = Condition(
        index=1,
        label="arm=control__method=spearman",
        values={"arm": "control", "analysis.method": "spearman"},
        selectors=frozenset({"arm"}),
    )
    against = Condition(
        index=0,
        label="arm=control__method=pearson",
        values={"arm": "control", "analysis.method": "pearson"},
        selectors=frozenset({"arm"}),
    )
    assert crossed_group_axes(of, against) == []
    assert differing_axes(of, against) == ["analysis.method"]  # the control


def test_crossed_group_axes_names_the_group_axes_in_declaration_order():
    """A cross-arm comparison, and the list rather than a boolean: `validate`'s
    message names the axes and pluralizes on how many, so a boolean would force a
    second expression to recompute them.

    Order is the sweep's declaration order, inherited from `differing_axes`, which
    is what makes the emitted message stable across runs rather than set-ordered."""
    of = Condition(
        index=1,
        label="arm=treatment__site=north",
        values={"arm": "treatment", "site": "north"},
        selectors=frozenset({"arm", "site"}),
    )
    against = Condition(
        index=0,
        label="arm=control__site=south",
        values={"arm": "control", "site": "south"},
        selectors=frozenset({"arm", "site"}),
    )
    assert crossed_group_axes(of, against) == ["arm", "site"]


def test_crossed_group_axes_ignores_a_parameter_axis_named_like_a_selector():
    """A path only crosses arms if it is a DECLARED group axis, which `selectors`
    is the authority on. A condition differing on a path neither side declares as a
    selector is paired, and reading `values` alone would call it unpaired — the
    "answering with a proxy" substitution one axis over.

    The asymmetric case is asserted too: `selectors` is the union of both sides', so
    a path one side declares and the other does not still counts."""
    of = Condition(index=1, values={"arm": "treatment"}, label="a", selectors=frozenset())
    against = Condition(index=0, values={"arm": "control"}, label="b", selectors=frozenset())
    assert crossed_group_axes(of, against) == []
    half = Condition(index=2, values={"arm": "treatment"}, label="c", selectors=frozenset({"arm"}))
    assert crossed_group_axes(half, against) == ["arm"]
```

      Add `crossed_group_axes` to `tests/test_contrasts.py`'s import block; `Condition` and
      `differing_axes` are already imported there — confirm by reading.

      In `tests/test_validate.py`, beside `test_a_contrast_beside_groups_and_cluster_by_draws_the_allocation_refusal`:

```python
def _groups_weight_csv() -> str:
    """`_groups_cluster_csv`'s roster with a weight column instead of a cluster one.

    A separate builder rather than a column added to that one: its own tests assert
    a documented arm/site crossing, and a roster that grew a column would be a
    second fixture wearing the first one's name."""
    rows = ["patient_id,arm,sampling_weight"]
    for arm, keys in _GROUPS_CLUSTER_ARMS.items():
        for key in keys:
            rows.append(f"{key},{arm},{2 if arm == 'control' else 3}")
    return "\n".join(rows) + "\n"


def _groups_weight_doc(**extra) -> dict:
    doc = {
        "data.units": {
            "from": "index.csv",
            "key": "patient_id",
            "attributes": ["arm", "sampling_weight"],
            "weight_by": "sampling_weight",
            "allocation": "between",
            "assign": {"arm": {"method": "by_attribute"}},
        },
        "sweep": {"groups": [{"by": "arm", "levels": ["control", "treatment"]}]},
    }
    doc.update(extra)
    return doc


def test_groups_and_weight_by_compose_with_no_comparison(write_config, tmp_path):
    """The can-fail control, and it must come first: the combination ITSELF is
    legal, so a refusal that fired here would be refusing a declaration rather than
    a combination. A `between` + `by_attribute` + `weight_by` config over a roster
    whose arms carry different weights validates fully clean."""
    (tmp_path / "input" / "index.csv").write_text(_groups_weight_csv())
    assert _error_codes(write_config(_groups_weight_doc())) == set()


def test_a_weighted_cross_arm_contrast_draws_the_weight_allocation_refusal(
    write_config, tmp_path
):
    """`E-DATA-WEIGHT-ALLOCATION-CONTRAST`. A Welch *t* on two weighted means needs
    Kish's effective size PER SIDE — two df inputs where the paired form needed one,
    on the dimension where a wrong choice hides best — so the composition is refused
    rather than approximated, on the precedent `E-DATA-WEIGHT-CLUSTER-CONTRAST` set.

    Asserted ALONGSIDE `E-DATA-ALLOCATION-CONTRAST` rather than as an exact set:
    that code is alive until this slice's retirement task, and `validate` collects
    rather than aborting, so both report. Task 18 owns the flip to a set of one."""
    (tmp_path / "input" / "index.csv").write_text(_groups_weight_csv())
    doc = _groups_weight_doc(
        statistics={
            "contrasts": [{"id": "t_vs_c", "of": "arm=treatment", "against": "arm=control"}]
        }
    )
    found = _error_codes(write_config(doc))
    assert "E-DATA-WEIGHT-ALLOCATION-CONTRAST" in found
    assert "E-DATA-ALLOCATION-CONTRAST" in found
    assert "E-DATA-ALLOCATION-WITHIN-ARMS" not in found  # attributed, not incidental
    assert "E-DATA-ALLOCATION-NO-ARMS" not in found


def test_a_weighted_within_arm_contrast_draws_neither_refusal(write_config, tmp_path):
    """The refusal is per comparison, not per config. A `groups × grid` design whose
    declared contrast stays inside one arm shares that arm's units, so it is paired
    and weightable — `weighted_paired_t_over_units` is exactly the construction it
    gets — and a guard firing on `weight_by` beside a group axis would refuse a
    design core computes correctly today.

    This is the assertion that separates the two readings, and without it a guard
    keyed on the declaration rather than on the comparison passes every other test
    in this file."""
    (tmp_path / "input" / "index.csv").write_text(_groups_weight_csv())
    doc = _groups_weight_doc(
        sweep={
            "groups": [{"by": "arm", "levels": ["control", "treatment"]}],
            "grid": {"analysis.method": ["pearson", "spearman"]},
        },
        statistics={
            "contrasts": [
                {
                    "id": "within_control",
                    "of": "arm=control__method=spearman",
                    "against": "arm=control__method=pearson",
                }
            ]
        },
    )
    found = _error_codes(write_config(doc))
    assert "E-DATA-WEIGHT-ALLOCATION-CONTRAST" not in found
    assert "E-DATA-ALLOCATION-CONTRAST" not in found


def test_a_weighted_clustered_cross_arm_contrast_draws_both_composition_refusals(
    write_config, tmp_path
):
    """Two independent compositions, both refused, and `validate` collects rather
    than aborting — so the finding set carries both plus the allocation refusal
    still alive at this task. `E-DATA-WEIGHT-CLUSTER-CONTRAST` fires on an unpaired
    comparison too, which H4c-SCOPING probed and which is why H4c inherits that
    composition as a standing refusal rather than as work."""
    (tmp_path / "input" / "index.csv").write_text(_groups_weight_csv())
    doc = _groups_weight_doc(
        statistics={
            "contrasts": [{"id": "t_vs_c", "of": "arm=treatment", "against": "arm=control"}]
        }
    )
    doc["data.units"]["cluster_by"] = "arm"
    found = _error_codes(write_config(doc))
    assert "E-DATA-WEIGHT-ALLOCATION-CONTRAST" in found
    assert "E-DATA-WEIGHT-CLUSTER-CONTRAST" in found
    assert "E-DATA-ALLOCATION-CONTRAST" in found
```

      **`cluster_by: "arm"` in the last test is deliberate and cheap** — it needs a declared cluster
      attribute and `arm` is already in `attributes`. **If `cluster_by` naming a group axis draws its
      own refusal, use a third column instead and say so in the report**; read what `validate`
      reports in full rather than assuming, because a refusal that happens to fire must be attributed
      before it is counted.

- [ ] **Step 2: run and see them fail.** `uv run pytest tests/test_contrasts.py tests/test_validate.py -k "crossed_group or weight_allocation or groups_and_weight"`
      → `ImportError` on `crossed_group_axes`, and the four validate tests failing on the missing
      code.

- [ ] **Step 3: implement the predicate.** In `src/publishable/contrasts.py`, immediately after
      `differing_axes`:

```python
def crossed_group_axes(of: "Condition", against: "Condition") -> list[str]:
    """The declared group axes two conditions disagree on — empty iff they are paired.

    `reference.md` § Allocation's pairing table: two conditions differing only on
    parameter axes share their units and are paired unit by unit (or paired within
    that arm under `between`), while two differing on *any* `groups` axis hold
    disjoint sets of units by construction. So this list being empty **is** the
    pairing test, and it answers per comparison rather than per config — in a
    `groups × grid` design, control-pearson against control-spearman is paired and
    computable while control-pearson against treatment-pearson is not.

    **One expression with two callers, deliberately.** `validate` refuses
    `weight_by` beside a non-empty answer, and `cli._comparison_step_blocks` derives
    the `paired` it records from the same answer. Two spellings of one rule drifting
    apart is a defect this codebase has already shipped, and here the drift would be
    `validate` refusing a shape `cli` records as paired.

    Returns the **list**, not a boolean: `validate`'s message names the axes and
    pluralizes on how many there are, and a boolean would force a second expression
    to recompute them.

    `Condition.selectors` is the authority on which of a condition's `values` paths
    select units rather than set a parameter — carried on the condition and set by
    `expand`, which is the only place that knows which mode produced a cell. Reading
    `values` alone would call every differing path a group axis. The **union** of
    both sides' selectors, because a path one side declares and the other does not
    still makes the two sides disjoint.

    Not gated on `allocation`: the axis being a declared `groups` axis is what makes
    the two sides disjoint, whatever `allocation` itself is declared as — a config
    missing that declaration entirely earns `E-DATA-ALLOCATION-WITHIN-ARMS`
    separately.
    """
    group_selectors = of.selectors | against.selectors
    return [axis for axis in differing_axes(of, against) if axis in group_selectors]
```

- [ ] **Step 4: rewire `validate._check_sweep`'s loop and add the new guard.** Replace the loop's
      three inlined lines with the predicate and append the new error inside the same loop:

```python
    conditions_by_index = {cond.index: cond for cond in conditions}
    for comp in resolved_contrasts:
        of_cond = conditions_by_index.get(comp.of)
        against_cond = conditions_by_index.get(comp.against)
        if of_cond is None or against_cond is None:
            continue
        group_axes = crossed_group_axes(of_cond, against_cond)
        if not group_axes:
            continue
        plural = "" if len(group_axes) == 1 else "s"
        c.error(
            "E-DATA-ALLOCATION-CONTRAST",
            ...unchanged...
        )
        # A weighted unpaired contrast has no construction and will not get one.
        # `weight_by` beside a cross-arm comparison needs Kish's effective size PER
        # SIDE — two df inputs where the paired form needed one — and the two
        # readings coincide in any fixture not built to separate them, so the wrong
        # choice would be invisible. Refused rather than approximated, on the
        # precedent `E-DATA-WEIGHT-CLUSTER-CONTRAST` set. Standing, not temporary:
        # it refuses a COMBINATION rather than a declaration, so it carries a
        # § Validation row and a § Errors row and is not one of the `NOT BUILT`
        # declarations § The one config file counts.
        #
        # Inside this loop rather than beside the `comparisons > 0` guards above,
        # because it is the same per-comparison reading its neighbour is: a
        # `groups × grid` design's within-arm comparisons are paired and weightable,
        # and a guard firing on the declaration would refuse a design core computes
        # correctly today.
        if isinstance(weight_by, str) and weight_by:
            c.error(
                "E-DATA-WEIGHT-ALLOCATION-CONTRAST",
                "data.units.weight_by",
                f"is declared beside a comparison whose two conditions "
                f"({of_cond.label!r} and {against_cond.label!r}) differ on group "
                f"axis{plural} {', '.join(group_axes)}, and no construction computes "
                "a weighted unpaired delta: a Welch *t* on two weighted means takes "
                "its df from Kish's effective size per side, two inputs where the "
                "paired form needed one, and the two readings coincide in any sample "
                "not built to separate them. Drop `weight_by` and the cross-arm delta "
                "is computed unweighted, keep it and compare within an arm, or express "
                "the weighted difference as an `Estimate` returned by a `summary` step, "
                "which core records as reported rather than recomputing",
            )
```

      **The message states the standing reason, not a build state.** No form of *"until the
      estimators exist"* appears in it — that phrasing is what makes a refusal read as temporary, and
      `CLAUDE.md` § Misreadings names *"Reading a temporary refusal as permanent, or the reverse"* as
      a repeated error here.

- [ ] **Step 5: add both `reference.md` rows.** A refusal of a **combination** carries a § Validation
      row and a § Errors row — the two ends of one check — which is what distinguishes it from a
      `-UNSUPPORTED` build-family code, and `tests/test_cli.py::test_the_weight_cluster_refusal_has_both_of_its_rows`
      is the shape of the pin that says so.

      **§ Validation's registry**, beside the *Weighted clustered deltas aren't computed* row, whose
      subject is the sibling composition:

```
| Weighted unpaired deltas aren't computed | `data.units.weight_by` is declared and a resolved comparison crosses a [group axis](#expansion-modes). A Welch *t* on two weighted means takes its df from Kish's effective size **per side**, two inputs where the paired form needs one, and the two readings coincide in any sample not built to separate them — so the composition is refused rather than approximated. Read per comparison: a `groups × grid` design's within-arm comparisons stay weighted and computed | `E-DATA-WEIGHT-ALLOCATION-CONTRAST` |
```

      **§ Errors `validate` reports**, beside the `E-DATA-WEIGHT-CLUSTER-CONTRAST` row — the row must
      end with `` | `E-DATA-WEIGHT-ALLOCATION-CONTRAST` | `` so a test can locate it by its final
      cell rather than by position:

```
| [`data.units.weight_by`](#weighted-samples) is declared beside a resolved comparison whose two conditions differ on a declared [`sweep.groups`](#expansion-modes) axis. The unweighted unpaired constructions exist — `welch_t_over_units` and `unpaired_percentile_over_units`, and their `_clustered` forms — but no weighted one does, and it is not a gap waiting to be filled: a Welch *t* on two weighted means takes its df from Kish's effective size **per side**, two df inputs where the paired form needed one, and the two candidate readings coincide in any sample not built to separate them, so a wrong choice would be invisible in every output. Read **per comparison**, the same reading its sibling composition refusal takes: a `groups × grid` design's within-arm comparisons share their arm's units, so they stay paired, weighted and computed. Drop `weight_by` for an unweighted cross-arm delta, compare within an arm to keep it, or express the weighted difference as an `Estimate` returned by a `summary` step | `E-DATA-WEIGHT-ALLOCATION-CONTRAST` |
```

      **Check every row this insertion moved**, and every count phrase near it — a positional locator
      wrong twice in this repo was falsified by exactly this kind of insertion.

- [ ] **Step 6: run and see them pass.** `uv run pytest` → **2227 + 7 = 2234 passed**, 1 skipped,
      2 xfailed. Then `uv run ruff check .`, `uv run ruff format --check .` (80 files),
      `uv run mypy`. Run the mechanical pass over `docs/reference.md`.

- [ ] **Step 7: mutate — four mutations.**

      **Mutation 1 — the predicate reads `values` instead of `selectors`.** In
      `contrasts.crossed_group_axes`, replace the comprehension with `differing_axes(of, against)`.
      `test_crossed_group_axes_ignores_a_parameter_axis_named_like_a_selector` must **FAIL** on its
      first assertion, and `test_a_weighted_within_arm_contrast_draws_neither_refusal` must **FAIL**
      too — the pair is what says the predicate is right at the unit level *and* at the config level.

      **Mutation 2 — the guard keyed on the declaration.** Move the
      `E-DATA-WEIGHT-ALLOCATION-CONTRAST` emit out of the loop and up beside the
      `E-DATA-WEIGHT-CLUSTER-CONTRAST` guard, keyed on `comparisons > 0`.
      `test_a_weighted_within_arm_contrast_draws_neither_refusal` must **FAIL** —
      that config has a comparison and a `weight_by`, and its comparison is within-arm.
      **Checked against the test body:** the two branches genuinely differ because that config's
      contrast fixes `arm=control` on both sides, so `crossed_group_axes` returns `[]` while
      `comparisons > 0` is `True`.

      **Mutation 3 — the intersection dropped from `validate`'s loop.** Change
      `group_axes = crossed_group_axes(of_cond, against_cond)` to
      `group_axes = differing_axes(of_cond, against_cond)`. The same within-arm test must **FAIL** on
      **both** of its assertions, seeing the allocation refusal fire on a parameter-only difference.

      **Mutation 4 — the union narrowed to one side.** In `crossed_group_axes`, change
      `of.selectors | against.selectors` to `of.selectors`.
      `test_crossed_group_axes_ignores_a_parameter_axis_named_like_a_selector`'s asymmetric case
      still passes (`half` is the `of` side), so **reverse the order in a second run**: call
      `crossed_group_axes(against, half)` and confirm it returns `["arm"]`. **This is a mutation
      whose two branches cannot differ on the fixture as written** — the asymmetric case puts the
      selector on the side the mutant keeps — so the test needs the reversed call to discriminate.
      **Add that reversed assertion to the test in this task's commit**; naming a seam is not testing
      it, and this repo has shipped that exact shape twice.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 8: Commit.**

```bash
git add src/publishable/contrasts.py src/publishable/validate.py docs/reference.md \
        tests/test_contrasts.py tests/test_validate.py
git commit -m "feat: E-DATA-WEIGHT-ALLOCATION-CONTRAST, and one pairing predicate for validate and cli"
```

---

## Task 10: the unpaired key path, the per-side record keys, and the weight bookkeeping guard

**Runs after task 2** (whose four keys this emits) **and after task 9** (whose predicate this reads).
**Before task 13** — see deviation (c): taking them in the other order would ship `n_paired: 0`
beside `paired: false`, which decision 5 rejects by name as *"the worst-of-both"*.

**The interim state this leaves is stated rather than hidden.** For the three commits between this
task and task 13, an unpaired entry carries `paired: true` beside `n_of`/`n_against`. That is
internally odd, it is **never published** — `validate` gates `run` until task 18, so the shape is
reachable only by direct call — and it is not a shape any decision forbids, where `n_paired: 0` is.

**Files:**
- Modify: `src/publishable/cli.py`
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `contrasts.crossed_group_axes(of, against) -> list[str]` (task 9);
  `stats.paired_keys(of, against, allowed) -> list[str]`, the sorted intersection;
  `stats.mean_of(values) -> float | None`; `units.cluster_count_of(membership, keys) -> int`, the
  single counting expression; `cli._comparison_step_blocks`' existing shape — `differs_on`,
  `confounded`, `allowed = units_matching(roster, comp.within)`, the per-step `base_keys`, the
  `is_derived` branch and the recorded-column branch, the `if weights is not None:` and
  `if clusters is not None:` blocks that both read `base_keys if is_derived else col_keys`, and the
  `weights is not None and clusters is not None` `ValueError` at the top — all read in
  `src/publishable/cli.py`.
- Produces:

```python
def unpaired_keys(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    allowed: set[str] | None,
) -> tuple[list[str], list[str]]
```

  in `stats.py`; and in `_comparison_step_blocks` a function-scope `is_paired: bool`, per-step
  `of_side_keys`/`against_side_keys`, per-metric `of_col`/`against_col`, an unpaired arm of the
  recorded-column branch writing `delta`/`n_of`/`n_against`, conditional `n_paired` /
  `n_paired_clusters` / `n_clusters_of` / `n_clusters_against`, and a `ValueError` for weights beside
  an unpaired comparison. Tasks 11, 13, 14, 15 and 16 all read `is_paired`.

**`paired_keys` does not apply and its replacement is not its sibling.** The intersection is the wrong
set for a contrast whose sides are disjoint, and the point estimate is the **difference of two side
means** rather than the mean of a difference vector — over each side's own completed units narrowed
by the contrast's `within`, which is the same narrowing `paired_keys` applies.

**Why the weight guard lands here rather than in task 13.** The `if weights is not None:` block
computes `n_paired_effective` over `base_keys if is_derived else col_keys`, and `col_keys` does not
exist on the unpaired arm — so without the guard this task's own change leaves an unbound name
reachable by direct call. Task 9's refusal makes the combination unreachable through `run`, and this
guard is the `cli`-side end of that same claim, exactly as the existing
`E-DATA-WEIGHT-CLUSTER-CONTRAST` `ValueError` is for its own composition.

- [ ] **Step 1: write the failing tests.** In `tests/test_stats.py`:

```python
def test_unpaired_keys_gives_each_side_its_own_completed_set():
    """`paired_keys` is the intersection and it is the wrong set for a contrast
    whose two sides are disjoint. Each side gets its own completed units, sorted for
    the same reason `paired_keys` sorts — a draw over these keys must be row-order
    invariant.

    The fixture is genuinely disjoint AND has one shared key, which is the case a
    naive `set(of) - set(against)` would get wrong: sharing a key is not what makes
    a comparison paired, the group axis is, and this function does not decide that."""
    of = {"a": {"m": 1.0}, "b": {"m": 2.0}, "s": {"m": 3.0}}
    against = {"c": {"m": 4.0}, "s": {"m": 5.0}}
    assert unpaired_keys(of, against, None) == (["a", "b", "s"], ["c", "s"])


def test_unpaired_keys_narrows_both_sides_by_the_stratum():
    """`within` narrows each side, the same narrowing `paired_keys` applies to the
    intersection. Asserted on both sides, because a function narrowing only `of`
    passes any test that reads one side."""
    of = {"a": {"m": 1.0}, "b": {"m": 2.0}}
    against = {"c": {"m": 3.0}, "d": {"m": 4.0}}
    assert unpaired_keys(of, against, {"a", "c"}) == (["a"], ["c"])
    assert unpaired_keys(of, against, set()) == ([], [])
```

      In `tests/test_cli.py`, add an unpaired direct-call harness beside `_clustered_contrast_call`:

```python
_UNPAIRED_OF = [17.0, 19.0, 20.0, 21.0, 23.0]
_UNPAIRED_AGAINST = [5.0] * 12 + [15.0] * 12 + [10.0]


def _unpaired_contrast_call(**extra):
    """`_comparison_step_blocks` over fixture A, two disjoint arms.

    `of` is 5 units at mean 20 with s² 5, `against` 25 units at mean 10 with s² 25 —
    so s²/n is exactly 1 on each side and both contribute comparably to the Welch
    variance, which is what keeps a `min(n) − 1` df mutant visible. Delta 10, Welch
    SE √2, df 96/7, half-width 3.039125537798091.

    The two conditions differ on `arm`, which both declare as a `selector`, so
    `crossed_group_axes` returns `["arm"]` and the comparison is unpaired. **The two
    sides' collapsed tables share no key**, which is what a group axis means."""
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.diagnostics import Collector
    from publishable.sweep import Condition
    from publishable.units import Unit, UnitList

    of_keys = [f"t{i:02d}" for i in range(len(_UNPAIRED_OF))]
    against_keys = [f"c{i:02d}" for i in range(len(_UNPAIRED_AGAINST))]
    roster = UnitList([Unit(key=k) for k in of_keys + against_keys])
    kwargs = dict(
        roster=roster,
        aggregated={1: {"s": {"m": 20.0}}, 0: {"s": {"m": 10.0}}},
        collapsed_by_key={
            (1, "s"): {k: {"m": v} for k, v in zip(of_keys, _UNPAIRED_OF, strict=True)},
            (0, "s"): {
                k: {"m": v} for k, v in zip(against_keys, _UNPAIRED_AGAINST, strict=True)
            },
        },
        derived_by_key={},
        resample_fns_by_key={},
        seed=7,
        draws=400,
        min_reported_n=None,
        findings=Collector(),
        where="contrast 'arm_effect'",
        where_id="contrast:arm_effect",
        conditions_by_index={
            0: Condition(
                index=0,
                label="arm=control",
                values={"arm": "control"},
                selectors=frozenset({"arm"}),
            ),
            1: Condition(
                index=1,
                label="arm=treatment",
                values={"arm": "treatment"},
                selectors=frozenset({"arm"}),
            ),
        },
        resample_columns=False,
    )
    kwargs.update(extra)
    return _comparison_step_blocks(
        Comparison(id="arm_effect", of=1, against=0, declared=True), **kwargs
    )


def test_an_unpaired_contrast_records_its_two_side_counts_and_no_n_paired():
    """Decision 5, and it is the first conditional write of `n_paired` in this
    codebase. § Contrasts defines `n_paired` as the intersection, and an unpaired
    contrast's intersection is empty by construction — so `n_paired: 0` would be
    arithmetically true and descriptively false, and it would spend on a design
    where pairing is not the concept the same `0` § Contrasts already spends on a
    pairing that FAILED.

    **Absent, not null**, the shape `weighted_by` and `n_paired_effective` already
    use. Asserted beside the two presences, because a control asserting only
    absences passes identically if nothing ran."""
    block, _ = _unpaired_contrast_call()
    entry = block["s"]["m"]
    assert entry["n_of"] == 5
    assert entry["n_against"] == 25
    assert "n_paired" not in entry
    assert "n_paired_effective" not in entry


def test_an_unpaired_contrasts_delta_is_a_difference_of_two_side_means():
    """`paired_keys` does not apply, so the point estimate cannot be the mean of a
    difference vector — there are no per-unit differences to take. It is the
    difference of the two sides' own means over the units each side completed.

    Asserted as a POSITIVE literal rather than `is not None`: over disjoint arms
    every construction in this module returns `None`, so a null assertion cannot
    tell a computed delta from a failed one — which is why this slice bans that
    shape. 20 − 10 = 10 exactly, and the two side means are asserted separately so a
    delta that came from the wrong side's mean is attributable."""
    block, _ = _unpaired_contrast_call()
    entry = block["s"]["m"]
    assert entry["delta"] == pytest.approx(10.0)
    assert entry["basis"] == "units"


def test_an_unpaired_contrast_narrows_both_sides_by_its_within_stratum():
    """`within` narrows each side, and it must narrow BOTH: a narrowing applied to
    one side gives a delta computed over a stratum on one side and a whole arm on
    the other, which is a number no reader could detect is wrong.

    The stratum keeps 3 of 5 `of` units and 2 of 25 `against` units, so the two
    counts move by different amounts — a fixture narrowing both sides equally could
    not tell a per-side narrowing from a shared one."""
    from publishable.contrasts import Comparison
    from publishable.units import Unit, UnitList

    of_keys = [f"t{i:02d}" for i in range(5)]
    against_keys = [f"c{i:02d}" for i in range(25)]
    keep = set(of_keys[:3]) | set(against_keys[:2])
    roster = UnitList(
        [
            Unit(key=k, attributes={"site": "north" if k in keep else "south"})
            for k in of_keys + against_keys
        ]
    )
    block, _ = _unpaired_contrast_call(
        roster=roster,
        _comparison=Comparison(
            id="arm_effect", of=1, against=0, within={"site": "north"}, declared=True
        ),
    )
    entry = block["s"]["m"]
    assert entry["n_of"] == 3
    assert entry["n_against"] == 2


def test_a_weighted_unpaired_comparison_is_a_core_defect_here_not_a_silent_choice():
    """`E-DATA-WEIGHT-ALLOCATION-CONTRAST` refuses the combination at `validate` and
    `cli` always validates before running, so reaching this function with both is a
    bookkeeping error rather than a config — the same standing the weight-cluster
    guard beside it has, and `ValueError` for the same reason `Member.__post_init__`
    gives: nothing here came from outside core.

    Raised rather than resolved by ignoring the weight: silently publishing an
    unweighted cross-arm delta beside a `weighted_by` marker is a declaration
    accepted whose effect is not delivered, and no reader of `run.yaml` could tell."""
    with pytest.raises(ValueError, match="E-DATA-WEIGHT-ALLOCATION-CONTRAST"):
        _unpaired_contrast_call(
            weights={f"t{i:02d}": 1.0 for i in range(5)}
            | {f"c{i:02d}": 1.0 for i in range(25)},
            weighted_by="sampling_weight",
        )


def test_an_unpaired_clustered_contrast_records_two_cluster_counts_and_no_paired_one():
    """§ Contrasts: `n_paired_clusters` counts the clusters the paired intersection
    falls in, so it has nothing to count here. `n_clusters_of` and
    `n_clusters_against` replace it — **two integers that cannot coincide on this
    fixture**, 3 against 4, which is what makes them the strongest discriminator
    available: a construction reading one side's count, or a pooled count of 7,
    writes a wrong integer into the record even where a float assertion might be
    argued about.

    `cluster_count_of` is the single counting expression, the one `attrition`'s
    `n.clusters` and every clustered df read; `len(set(...))` here would be a second
    authority for one number."""
    of_keys = [f"t{i:02d}" for i in range(5)]
    against_keys = [f"c{i:02d}" for i in range(25)]
    clusters = {k: f"g{i // 2}" for i, k in enumerate(of_keys)}  # 3 clusters: 2/2/1
    clusters |= {k: f"h{i // 7}" for i, k in enumerate(against_keys)}  # 4: 7/7/7/4
    block, _ = _unpaired_contrast_call(clusters=clusters)
    entry = block["s"]["m"]
    assert entry["n_clusters_of"] == 3
    assert entry["n_clusters_against"] == 4
    assert "n_paired_clusters" not in entry
```

      **`_unpaired_contrast_call` needs a `_comparison=` override** for the `within` test, since the
      `Comparison` is built inside it. Add that parameter: `comparison = extra.pop("_comparison",
      None) or Comparison(id="arm_effect", of=1, against=0, declared=True)`. **Read
      `_clustered_contrast_call` first** — it takes no such parameter, so this is a new shape and it
      belongs in the new helper rather than being retrofitted onto the old one.

- [ ] **Step 2: run and see them fail.** `uv run pytest tests/test_stats.py tests/test_cli.py -k "unpaired_keys or unpaired_contrast or weighted_unpaired"`
      → `ImportError` on `unpaired_keys`, then `KeyError: 'n_of'`.

- [ ] **Step 3: implement `stats.unpaired_keys`**, immediately after `paired_keys`:

```python
def unpaired_keys(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    allowed: set[str] | None,
) -> tuple[list[str], list[str]]:
    """Each side's own completed units, narrowed by a `within` stratum if given.

    `paired_keys`' counterpart for a contrast whose two conditions differ on a
    declared `sweep.groups` axis: the two sides hold disjoint sets of units, so
    there is no intersection to take and no per-unit difference to contribute. What
    replaces the intersection is two sets, and what replaces the mean of a
    difference vector is a difference of two means.

    **This function does not decide whether a comparison is paired** —
    `contrasts.crossed_group_axes` does — and it deliberately does not subtract the
    two sides from each other. Two sides sharing a key is not what makes a
    comparison paired, the group axis is, and a set difference here would silently
    drop a unit from a roster whose arms overlap for a reason this function cannot
    see.

    Sorted, for the reason `paired_keys` sorts: a resample over these keys must be
    row-order invariant, and `unpaired_percentile_of_sides` asserts a sorted-keys
    caller contract when `strata` is given.

    `allowed` narrows **both** sides. A narrowing applied to one would compute a
    delta over a stratum on one side and a whole arm on the other, which is exactly
    the number no reader could detect is wrong.
    """
    of_keys = set(of)
    against_keys = set(against)
    if allowed is not None:
        of_keys &= allowed
        against_keys &= allowed
    return sorted(of_keys), sorted(against_keys)
```

- [ ] **Step 4: wire `_comparison_step_blocks`.** Six edits, and **no edit to the paired arm's
      arithmetic** — task 21's six-cell pin is what says so.

      **(i) At the top, beside the existing weight-cluster guard**, after `differs_on` is computed:

```python
    differs_on = differing_axes(conditions_by_index[comp.of], conditions_by_index[comp.against])
    confounded = len(differs_on) > 1
    # Whether the two sides share their units, from the SAME expression `validate`
    # refuses on — `contrasts.crossed_group_axes`, whose docstring argues why it is
    # one function with two callers. Read once at function scope: a per-metric
    # re-derivation is how two entries in one block come to disagree about a fact
    # about their two conditions.
    is_paired = not crossed_group_axes(
        conditions_by_index[comp.of], conditions_by_index[comp.against]
    )
    # `E-DATA-WEIGHT-ALLOCATION-CONTRAST` refuses this combination at `validate`,
    # and `cli` always validates before running — so both being set is core's own
    # bookkeeping error, not a config. Raised rather than resolved by dropping the
    # weight: an unweighted cross-arm delta published beside a `weighted_by` marker
    # is a declaration accepted whose effect is not delivered, and no reader of
    # `run.yaml` could tell. `ValueError` for the reason the guard below gives.
    if weights is not None and not is_paired:
        raise ValueError(
            "a weighted unpaired comparison has no construction in this build; "
            "E-DATA-WEIGHT-ALLOCATION-CONTRAST refuses the combination at validate"
        )
```

      **(ii) Per step**, beside `base_keys`:

```python
        base_keys = paired_keys(of_collapsed, against_collapsed, allowed)
        of_side_keys, against_side_keys = unpaired_keys(
            of_collapsed, against_collapsed, allowed
        )
```

      Both are computed unconditionally. `base_keys` is empty on an unpaired comparison and the two
      side lists are the whole sides on a paired one; **neither is read by the other's arm**, and
      computing both is what keeps the two arms' key expressions independent rather than one derived
      from the other.

      **(iii) Per metric**, beside the existing `col_weights`/`col_clusters` pre-binding and for the
      identical reason it gives — *"so the name is always defined"*:

```python
            of_col: list[str] = of_side_keys
            against_col: list[str] = against_side_keys
```

      These are the side key lists **narrowed to the units carrying this metric**, and the recorded-
      column arm narrows them. A derived metric leaves them whole, which is the same asymmetry the
      existing `base_keys if is_derived else col_keys` expression encodes — written as one narrowing
      rather than a repeated ternary, so the two per-side facts cannot disagree about which set they
      are computed over.

      **(iv) The derived branch's count.** Replace `n_paired = len(base_keys)` with nothing and the
      record's `"n_paired": n_paired` with the conditional block in (vi). Keep
      `if compute_of is not None and compute_against is not None and clusters is None:` **exactly as
      it is** — task 15 adds the `is_paired` ground to it, and adding it here would leave that task
      nothing to verify. **`base_keys` being empty on an unpaired comparison is why the derived
      delta comes back `None` today, and that is an ACCIDENT this plan does not rely on**: decision 8
      calls an empty `base_keys` a **proxy**, because it is also empty when two genuinely paired
      conditions share no completed units, which is a defect to report rather than a design to
      honour. Task 15 replaces the accident with a guard.

      Rebind the resample floor in the derived branch from `n_paired >= 2` to `len(base_keys) >= 2`,
      which is the same number and removes the name this task deletes.

      **(v) The recorded-column branch gets a second arm.** Wrap today's body in `if is_paired:`
      unchanged — every line, every comment, the `resample_columns` branch, the three-way *t* choice
      and the whole `metric_block[metric_key] = {...}` literal — and add:

```python
                else:
                    of_col = [k for k in of_side_keys if metric_key in of_collapsed[k]]
                    against_col = [
                        k for k in against_side_keys if metric_key in against_collapsed[k]
                    ]
                    of_values = [of_collapsed[k][metric_key] for k in of_col]
                    against_values = [
                        against_collapsed[k][metric_key] for k in against_col
                    ]
                    resampled = None
                    # Task 14 selects the construction. Until it does, an unpaired
                    # contrast records its delta and its two counts with no interval
                    # — a point with no interval, which is the honest shape every
                    # construction in `stats.py` already returns below its floor.
                    interval = None
                    of_mean = mean_of(of_values)
                    against_mean = mean_of(against_values)
                    metric_block[metric_key] = {
                        # The difference of the two sides' own means, over the units
                        # each side completed AND recorded this column for. Never a
                        # mean of differences: there are no per-unit differences, and
                        # `n_paired`'s intersection is empty by construction.
                        "delta": (
                            None
                            if of_mean is None or against_mean is None
                            else of_mean - against_mean
                        ),
                        "basis": "units",
                        "paired": True,
                        "method": interval.method if interval else None,
                        "ci95": [interval.low, interval.high] if interval else None,
                        "cohens_d": None,
                        "correction": None,
                    }
```

      **`"paired": True` here is the literal task 13 derives**, and it is written as a literal on
      purpose: task 17a counts `'"paired": True'` in this function's source and must fail in exactly
      one commit, task 13's. **Do not derive it here.**

      **(vi) The two count blocks become conditional.** Replace the unconditional `"n_paired"` entry
      in both record literals with a shared block after them, beside the existing
      `if weights is not None:` block:

```python
            # § Contrasts: `n_paired` is the intersection, and a PAIRED contrast has
            # to record it. An unpaired contrast's intersection is empty by
            # construction, so `n_paired: 0` would be arithmetically true and
            # descriptively false — and § Contrasts already spends `0` on a different
            # meaning, a pairing that failed, which is the whole reason this key is
            # absent here rather than zero. Absent, not null, the shape `weighted_by`
            # and `n_paired_effective` already use.
            if is_paired:
                metric_block[metric_key]["n_paired"] = (
                    len(base_keys) if is_derived else len(col_keys)
                )
            else:
                metric_block[metric_key]["n_of"] = len(of_col)
                metric_block[metric_key]["n_against"] = len(against_col)
```

      and the cluster block becomes:

```python
            if clusters is not None:
                if is_paired:
                    metric_block[metric_key]["n_paired_clusters"] = cluster_count_of(
                        clusters, base_keys if is_derived else col_keys
                    )
                else:
                    # Per side once the sides are disjoint, and Welch's df reads
                    # both. Two integers that cannot coincide, which is what makes
                    # them a stronger discriminator than any float here.
                    metric_block[metric_key]["n_clusters_of"] = cluster_count_of(
                        clusters, of_col
                    )
                    metric_block[metric_key]["n_clusters_against"] = cluster_count_of(
                        clusters, against_col
                    )
```

      **The `if weights is not None:` block is left exactly as it is.** The guard in (i) makes it
      unreachable on an unpaired comparison, so `col_keys` in its expression is always bound — and
      that is the guard's whole purpose, stated in its own comment rather than left for a reader to
      reconstruct.

      **(vii) The `Member` and the thin warning.** `corrected_from_pool = is_derived or
      resample_columns` and the `Member(...)` call reference `diffs` and `col_weights`/`col_clusters`,
      none of which the unpaired arm binds. Set `diffs=tuple(diffs) if is_paired else None` — spelled
      as one conditional expression rather than pre-binding `diffs = []`, because an empty tuple would
      be a `diffs` a `Member` could carry — and leave `weights`/`clusters` as they are, since the
      unpaired arm leaves both `col_weights` and `col_clusters` at their pre-bound `None`.
      **`ci95` is `None` on the unpaired arm at this task, so `__post_init__`'s exactly-one rule is
      exempt** and task 11 is what makes the member carry real evidence. Change the
      `min_reported_n` guard's `n_paired` reference to `(len(col_keys) if is_paired else
      min(len(of_col), len(against_col)))` as a **placeholder for one commit**, and say so in the
      task report: **task 16 owns the per-side warning and its message**, and a placeholder that
      warns on the thinner side is the reading that cannot under-report in the interim.

- [ ] **Step 5: run and see them pass.** `uv run pytest` → **2234 + 8 = 2242 passed**, 1 skipped,
      2 xfailed. **Task 21's six-cell pin and `test_a_paired_contrast_entry_still_grows_no_unpaired_key`
      must both still be green** — if either fails, the paired arm moved and the fix is here, not in
      the pin. Then `uv run ruff check .`, `uv run ruff format --check .` (80 files), `uv run mypy`.

- [ ] **Step 6: mutate — five mutations.**

      **Mutation 1 — `paired_keys` for both.** In the unpaired arm, change `of_side_keys` and
      `against_side_keys` to `base_keys`. `test_an_unpaired_contrasts_delta_is_a_difference_of_two_side_means`
      must **FAIL** with `delta: None` and
      `test_an_unpaired_contrast_records_its_two_side_counts_and_no_n_paired` must **FAIL** with
      `n_of == 0`. **Checked against the fixture:** the two collapsed tables share no key, so
      `base_keys` is `[]` — the counts go to zero and the delta to `None`, and the count assertion is
      the readable failure.

      **Mutation 2 — one side's narrowing dropped.** In `stats.unpaired_keys`, remove
      `against_keys &= allowed`. `test_an_unpaired_contrast_narrows_both_sides_by_its_within_stratum`
      must **FAIL** on `n_against == 2`, seeing 25. **Checked:** the stratum keeps 2 of 25 on that
      side, so the two branches differ by 23 — which is why the fixture narrows the two sides by
      **different** amounts rather than equally.

      **Mutation 3 — `n_paired: 0` written beside the siblings.** Change the `if is_paired:` count
      block to write `n_paired` unconditionally as well as the two siblings.
      `test_an_unpaired_contrast_records_its_two_side_counts_and_no_n_paired` must **FAIL** on
      `"n_paired" not in entry`. This is the exact worst-of-both decision 5 rejects, and it is the
      mutation that says the rejection is enforced rather than merely written down.

      **Mutation 4 — a pooled cluster count.** Change `n_clusters_against`'s call to
      `cluster_count_of(clusters, of_col + against_col)`.
      `test_an_unpaired_clustered_contrast_records_two_cluster_counts_and_no_paired_one` must
      **FAIL**, seeing 7 where it expects 4. **Checked:** the fixture's per-side counts are 3 and 4,
      distinct integers, and their pooled count is 7 — three different answers, which a fixture with
      equal per-side counts could not produce. This is the documented *"both 3"* failure closed by
      construction.

      **Mutation 5 — the weight guard.** Delete the `if weights is not None and not is_paired:`
      raise. `test_a_weighted_unpaired_comparison_is_a_core_defect_here_not_a_silent_choice` must
      **FAIL**, and it must fail with `NameError`/`UnboundLocalError` on `col_keys` rather than by
      not raising — **record which in the task report**, because the two say different things about
      what the guard is protecting.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 7: Commit.**

```bash
git add src/publishable/stats.py src/publishable/cli.py tests/test_stats.py tests/test_cli.py
git commit -m "feat: the unpaired key path, n_of/n_against and the per-side cluster counts"
```

---
## Task 11: `Member`'s third evidence kind, and the exactly-one rule counted over three

**Runs after tasks 4 and 6**, whose constructions decide what evidence a member has to carry. **Before
12 and 14**: `_comparison_step_blocks` builds the `Member`s, so a `Member` that cannot represent an
unpaired interval makes the dispatch untestable end to end.

**Files:**
- Modify: `src/publishable/correction.py`
- Test: `tests/test_correction.py`

**Interfaces:**
- Consumes: `correction.Member`, a frozen dataclass with `where`, `step`, `metric`, `delta`, `ci95`,
  `pool`, `diffs`, `declaration_index`, `weights=None`, `clusters=None`, whose `__post_init__` checks
  `weights` then `clusters` (each raising when `pool is not None`, when `diffs is None` or lengths
  disagree, and `clusters` additionally when `weights is not None`), returns early on `ci95 is None`,
  and then enforces `(self.pool is None) == (self.diffs is None)` — read in
  `src/publishable/correction.py`.
- Produces:

```python
@dataclass(frozen=True)
class UnpairedEvidence:
    of: tuple[float, ...]
    against: tuple[float, ...]
    clusters: tuple[tuple[str, ...], tuple[str, ...]] | None = None
```

  and `Member.sides: UnpairedEvidence | None = None`. Task 12 branches on `member.sides`, task 14
  builds it in `cli`.

**One field, not four, and the reason is decision 2's.** Only a single field can enter the exactly-one
rule cleanly, and a modifier's length invariant belongs to the object that defines the vectors it
aligns against — a flat per-side `clusters` beside `sides` would be one field with two admissible
shapes, which is the misaligned-vector class that *"produces a plausible number rather than an
error"*. `UnpairedEvidence` validates its own internal alignment in its own `__post_init__`.

**`pool` needs no change at all.** An unpaired percentile's evidence is a pool of resampled
differences, structurally identical to a paired one's, so `interval_at` already serves it. Only the
*t* forms have evidence that is neither a pool nor differences.

**The exactly-one rule becomes COUNTED over three, not a second equality.** Today's
`(self.pool is None) == (self.diffs is None)` does not generalize, and a later reader adding a second
equality would silently admit two-set members. Counting is what makes "exactly one of three" one
expression.

**Two existing tests match on the message and this task owns editing them.** Measured at `e40a219`:
`tests/test_correction.py` has `pytest.raises(ValueError, match="both")` and
`match="neither"` over the exactly-one rule. "Neither" is wrong of three options, so their `match=`
strings change with the message — **named here so it is a deliberate edit rather than a surprise
failure**.

- [ ] **Step 1: write the failing tests.** Append to `tests/test_correction.py`:

```python
def test_unpaired_evidence_carries_two_vectors_and_validates_its_own_alignment():
    """A Welch interval's evidence is neither a pool nor a difference vector: it is
    two per-side value vectors, plus two per-side label vectors when clustered. The
    alignment invariant lives HERE rather than on `Member`, because a modifier's
    length check belongs to the object that defines the vectors it aligns against —
    a flat `clusters` pair beside `sides` would be one field with two admissible
    shapes, which is the misaligned-vector class that produces a plausible number
    rather than an error.

    Both sides are checked, because a check reading one passes any fixture whose
    other side happens to align."""
    plain = UnpairedEvidence(of=(1.0, 2.0), against=(3.0, 4.0, 5.0))
    assert plain.clusters is None
    clustered = UnpairedEvidence(
        of=(1.0, 2.0), against=(3.0, 4.0, 5.0), clusters=(("a", "b"), ("c", "c", "d"))
    )
    assert clustered.clusters == (("a", "b"), ("c", "c", "d"))
    with pytest.raises(ValueError, match="of"):
        UnpairedEvidence(of=(1.0, 2.0), against=(3.0, 4.0), clusters=(("a",), ("c", "d")))
    with pytest.raises(ValueError, match="against"):
        UnpairedEvidence(of=(1.0, 2.0), against=(3.0, 4.0), clusters=(("a", "b"), ("c",)))


def test_a_member_carries_exactly_one_of_pool_diffs_and_sides():
    """The rule counted over three rather than extended from an equality. Today's
    `(pool is None) == (diffs is None)` does not generalize, and a second equality
    beside it would admit a member carrying two kinds — which would let
    `_corrected_bounds` build a *t* corrected bound for a percentile raw interval,
    narrower or wider than the truth by construction rather than by evidence.

    All three pairs are asserted plus the empty case, because a count that tested
    `<= 1` would admit none and a count testing `>= 1` would admit all three."""
    common = dict(where="1", step="s", metric="m", delta=1.0, ci95=(0.0, 2.0), declaration_index=0)
    sides = UnpairedEvidence(of=(1.0, 2.0), against=(3.0, 4.0))
    Member(pool=None, diffs=None, sides=sides, **common)  # the control: one is fine
    with pytest.raises(ValueError, match="pool, sides"):
        Member(pool=(1.0, 2.0), diffs=None, sides=sides, **common)
    with pytest.raises(ValueError, match="diffs, sides"):
        Member(pool=None, diffs=(1.0, 2.0), sides=sides, **common)
    with pytest.raises(ValueError, match="pool, diffs"):
        Member(pool=(1.0,), diffs=(1.0,), sides=None, **common)
    with pytest.raises(ValueError, match="none of the three"):
        Member(pool=None, diffs=None, sides=None, **common)


def test_a_member_may_not_carry_a_modifier_beside_sides():
    """Both modifiers are modifiers on `diffs`, and neither composes with `sides`.
    `weights` because `E-DATA-WEIGHT-ALLOCATION-CONTRAST` refuses the weighted
    unpaired composition at `validate`, so a member carrying both is `cli`'s
    bookkeeping error exactly as `E-DATA-WEIGHT-CLUSTER-CONTRAST` makes the other
    pair's. `clusters` because unpaired membership is PER SIDE and lives inside
    `UnpairedEvidence` — a flat label vector beside `sides` could not say which
    side it belongs to, and a construction reading it would align it against
    whichever vector came first.

    Asserted with `ci95=None` as well as with an interval, because both modifier
    checks run BEFORE the exactly-one rule's early return and must not become
    reachable only through it."""
    common = dict(where="1", step="s", metric="m", delta=1.0, declaration_index=0)
    sides = UnpairedEvidence(of=(1.0, 2.0), against=(3.0, 4.0))
    with pytest.raises(ValueError, match="sides"):
        Member(pool=None, diffs=None, sides=sides, weights=(1.0, 1.0), ci95=(0.0, 2.0), **common)
    with pytest.raises(ValueError, match="sides"):
        Member(pool=None, diffs=None, sides=sides, clusters=("a", "b"), ci95=(0.0, 2.0), **common)
    with pytest.raises(ValueError, match="sides"):
        Member(pool=None, diffs=None, sides=sides, weights=(1.0, 1.0), ci95=None, **common)


def test_a_member_with_no_interval_may_carry_sides_and_is_not_corrected():
    """The exemption `pool` and `diffs` already have, read for the third kind: a
    member with no `ci95` is dropped by `family_members` before any evidence field
    is read, and it is not required to carry none — a contrast whose construction
    came back below its floor still holds the two side vectors it was computed
    from.

    `family_members` reads `ci95` and nothing else, which is why it needs no change
    for this field; that is asserted here rather than left as a claim in a task
    report."""
    common = dict(where="1", step="s", metric="m", delta=1.0, declaration_index=0)
    sides = UnpairedEvidence(of=(1.0,), against=(3.0,))
    thin = Member(pool=None, diffs=None, sides=sides, ci95=None, **common)
    assert thin.sides is sides
    assert family_members([thin]) == []
    fat = Member(pool=None, diffs=None, sides=sides, ci95=(0.0, 2.0), **common)
    assert family_members([thin, fat]) == [fat]  # the presence that must report
```

      Add `UnpairedEvidence` to `tests/test_correction.py`'s import block; `Member` and
      `family_members` are already there — confirm by reading.

- [ ] **Step 2: edit the two existing message assertions.** In `tests/test_correction.py`, the test
      raising with `match="both"` becomes `match="pool, diffs"` and the one raising with
      `match="neither"` becomes `match="none of the three"`. **Read each test's whole docstring after
      editing it**: both argue about a two-way rule, and the argument is still correct of the pair
      they build — so **do not rewrite them**, only the `match=` string and, in the second, the word
      "neither" wherever the docstring uses it as the rule's name.

- [ ] **Step 3: run and see them fail.** `uv run pytest tests/test_correction.py` →
      `ImportError` on `UnpairedEvidence`, and the two edited tests failing on the old message.

- [ ] **Step 4: implement.** In `src/publishable/correction.py`, add the import
      `welch_t_over_units, welch_t_over_units_clustered` to the `from publishable.stats import (...)`
      block **in task 12, not here** — this task adds no `stats` call — and add the type before
      `Member`:

```python
@dataclass(frozen=True)
class UnpairedEvidence:
    """Two per-side value vectors, and their two per-side cluster labels if any.

    The evidence a Welch interval is built from, and the one kind that is neither a
    draw pool nor a difference vector: `welch_t_over_units` takes two independent
    samples and `welch_t_over_units_clustered` takes two more label vectors beside
    them. A percentile unpaired interval is NOT here — its evidence is a pool of
    resampled differences, structurally identical to a paired one's, so
    `interval_at` already serves it and `Member.pool` needs no change.

    **`clusters` lives here rather than on `Member`, and that is the whole reason
    this type exists.** A modifier's length invariant belongs to the object that
    defines the vectors it aligns against: a flat per-side label pair beside
    `Member.sides` would be one field with two admissible shapes, and a
    construction reading it would align it against whichever vector came first —
    the misaligned-vector class that produces a plausible number rather than an
    error. One field on `Member` is also what lets the exactly-one rule stay one
    expression.

    Tuples so a member cannot be mutated into the record by accident, the same
    reason `pool` and `diffs` are tuples. Neither may reach `run.yaml`.
    """

    of: tuple[float, ...]
    against: tuple[float, ...]
    clusters: tuple[tuple[str, ...], tuple[str, ...]] | None = None

    def __post_init__(self) -> None:
        """One label per value, per side, in the same order.

        `cli`'s bookkeeping to get right, so `ValueError` rather than
        `ContractError`: the latter is reserved for something a user's code asked
        for or handed back, and nothing here comes from outside core.

        Both sides are checked. A check reading one side passes any input whose
        other side happens to align, and the two sides here are deliberately
        different lengths in every fixture — an unpaired contrast whose arms were
        the same size would make the pooled and Welch standard errors algebraically
        identical, so a same-length assumption is wrong about the domain as well as
        about the code.
        """
        if self.clusters is None:
            return
        of_labels, against_labels = self.clusters
        if len(of_labels) != len(self.of):
            raise ValueError(
                "UnpairedEvidence clusters must give one label per value on the of "
                f"side, not {len(of_labels)} against {len(self.of)}"
            )
        if len(against_labels) != len(self.against):
            raise ValueError(
                "UnpairedEvidence clusters must give one label per value on the "
                f"against side, not {len(against_labels)} against {len(self.against)}"
            )
```

      Add the field to `Member` after `clusters`:

```python
    sides: UnpairedEvidence | None = None
```

      Rewrite the tail of `Member.__post_init__`, and add "never beside `sides`" to both modifier
      checks:

```python
        if self.weights is not None:
            if self.sides is not None:
                raise ValueError(
                    "Member weights may not accompany sides; "
                    "E-DATA-WEIGHT-ALLOCATION-CONTRAST refuses a weighted unpaired "
                    "comparison at validate"
                )
            if self.pool is not None:
                ...unchanged...
            ...unchanged...
        if self.clusters is not None:
            if self.sides is not None:
                raise ValueError(
                    "Member clusters may not accompany sides; unpaired cluster "
                    "membership is per side and lives inside UnpairedEvidence"
                )
            ...unchanged...
        if self.ci95 is None:
            return
        # Counted over the three rather than a second equality beside the first:
        # `(pool is None) == (diffs is None)` does not generalize, and a reader
        # adding a second equality would admit a member carrying two kinds. Two set
        # would let `_corrected_bounds` take one branch and build a corrected
        # interval from evidence the raw one was not read from — narrower or wider
        # than the truth by construction rather than by evidence, which is the exact
        # failure this rule exists to prevent. None set would make
        # `_corrected_bounds` return `None` for a reason that has nothing to do with
        # a pool being too small, so `thin: True` would fire over a member that was
        # never thin.
        present = [
            name
            for name, value in (
                ("pool", self.pool),
                ("diffs", self.diffs),
                ("sides", self.sides),
            )
            if value is not None
        ]
        if len(present) != 1:
            raise ValueError(
                "Member requires exactly one of pool/diffs/sides, not "
                + (", ".join(present) if present else "none of the three")
            )
```

      **Re-read `Member`'s whole class docstring and `__post_init__`'s whole docstring after this.**
      Both argue for a two-way rule with two modifiers on one of the two kinds. Add one paragraph to
      the class docstring for `sides`, and **narrow the sentence that says "Exactly one of them is
      set"** to name three. **Prefer deleting to rewriting** anywhere a claim has become false:
      `__post_init__`'s *"**`weights` and `clusters` are both modifiers on `diffs`, not a third kind
      of evidence**, so neither enters the exactly-one rule"* is still true and stays; its *"Both set
      would let `_corrected_bounds` silently take the `diffs` branch"* is now one of three cases and
      the comment above states the general form, so **delete the docstring sentence rather than
      re-enumerate it**.

- [ ] **Step 5: run and see them pass.** `uv run pytest` → **2242 + 4 = 2246 passed**, 1 skipped,
      2 xfailed. Then the other three gates.

- [ ] **Step 6: mutate — four mutations.**

      **Mutation 1 — the count relaxed.** Change `if len(present) != 1:` to `if len(present) > 1:`.
      `test_a_member_carries_exactly_one_of_pool_diffs_and_sides` must **FAIL** on the
      `"none of the three"` case. The reverse mutation, `if len(present) < 1:`, must **FAIL** on all
      three two-kind cases — **run both**, because one arm of a count check passing is what a single
      mutation cannot tell you.

      **Mutation 2 — a modifier admitted beside `sides`.** Delete the `weights`/`sides` raise.
      `test_a_member_may_not_carry_a_modifier_beside_sides` must **FAIL** on its first and third
      assertions and **pass** its second — which is what says the two modifier checks are independent
      rather than one guard covering both.

      **Mutation 3 — the alignment check reading one side.** In `UnpairedEvidence.__post_init__`,
      delete the `against_labels` check.
      `test_unpaired_evidence_carries_two_vectors_and_validates_its_own_alignment` must **FAIL** on
      its `match="against"` case. **Checked against the fixture:** the two sides there are length 2
      and 2 with label vectors of length 2 and 1, so the `of` check passes and only the `against`
      check can catch it — the fixture is built so the two checks are separately reachable, which
      equal-length label vectors could not show.

      **Mutation 4 — the exemption removed.** Move the `if self.ci95 is None: return` below the
      `present` check. `test_a_member_with_no_interval_may_carry_sides_and_is_not_corrected` must
      **FAIL** on constructing `thin`, and several pre-existing tests must fail too — **record which**,
      because that count is the measure of how many callers rely on the exemption.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 7: Commit.**

```bash
git add src/publishable/correction.py tests/test_correction.py
git commit -m "feat: Member's third evidence kind, and the exactly-one rule counted over pool/diffs/sides"
```

---

## Task 12: `_corrected_bounds`' two unpaired arms — five *t* arms, counted rather than carried

**Runs after tasks 11 and 7.** `correction.py` is a **second production call site for the contrast *t*
family that no charter names**, and it is the **first** of the two written — exactly as H4b-1's spec
correction 2 and H4b-2's task 12 found one axis over.

**Files:**
- Modify: `src/publishable/correction.py`
- Test: `tests/test_correction.py`

**Interfaces:**
- Consumes: `stats.welch_t_over_units(of, against, confidence=0.95)` (task 4);
  `stats.welch_t_over_units_clustered(of, of_labels, against, against_labels, confidence=0.95)`
  (task 7); `correction.UnpairedEvidence` and `Member.sides` (task 11);
  `correction._corrected_bounds(member, level)`, which today tests `member.diffs is not None` and
  chooses among `paired_t_over_units_clustered` / `weighted_paired_t_over_units` /
  `paired_t_over_units`, then falls through to `interval_at(member.pool, 1.0 - level)`, then returns
  `None`; `correction._level_for(method, family_size, rank)` — read in
  `src/publishable/correction.py`.
- Produces: `_corrected_bounds` with **five *t* arms and one pool arm — six return paths.** Nothing
  else changes: `family_members`, `family_shape`, `_evidence_ratio`, `rank_family`, `_level_for`,
  `_family`, `corrected_for` and `corrected_fields` are all untouched.

**Count the arms rather than carrying a number.** Two arms under `sides` (clustered, then plain),
three under `diffs` (clusters, weights, then plain), and the `pool` fall-through unchanged. **Five *t*
arms, six return paths** — the scoping said "six-way" of the *t* family alone and decision 2 says
"five", and the two are counting different things. **An implementer writing six *t* arms leaves an arm
no input reaches; one writing four leaves a cell falling through to a wrong construction**, which is
H4b-2's decision 2 verbatim.

**`family_members` needs no change, and that is a measured answer rather than an omission.** It reads
`e.ci95` and nothing else — read at `e40a219` — so a third evidence kind is invisible to it, which is
correct: a member with no interval is not corrected whatever it carries. Task 11's
`test_a_member_with_no_interval_may_carry_sides_and_is_not_corrected` asserts exactly that, so this
task adds nothing there.

**`sides` is tested BEFORE `diffs`, and the order is not a tie-break.** `Member.__post_init__` makes
the three mutually exclusive, so the order is a preference among impossible-to-have-both fields — the
same standing today's `clusters`-before-`weights` order has, and stated in the comment for the same
reason.

- [ ] **Step 1: write the failing tests.** Append to `tests/test_correction.py`:

```python
_CB_OF = (17.0, 19.0, 20.0, 21.0, 23.0)
_CB_AGAINST = (5.0,) * 12 + (15.0,) * 12 + (10.0,)


def test_an_unpaired_members_corrected_bound_is_the_welch_form_at_a_smaller_alpha():
    """The corrected interval must be the SAME construction at a smaller α or it is
    a counterpart in name only. Fixture A: raw half-width 3.039125537798091 at df
    96/7, and Bonferroni over a family of 2 is α = 0.025, so the corrected
    half-width is that times `t(96/7, 0.9875) / t(96/7, 0.975)` =
    1.1706821500146336 — 3.5578…

    **The ratio is the assertion, at the entry's OWN df**, not the presence of a
    wider interval: a corrected bound built at an unpaired-IID df where a clustered
    one belongs, or at a paired df, is also wider. The clustered fixture below gives
    a ratio of 1.4227764722656022 at df 2.095031, and the two differ by 21 %, which
    is what makes each assertion discriminating."""
    member = Member(
        where="c",
        step="s",
        metric="m",
        delta=10.0,
        ci95=(10.0 - 3.039125537798091, 10.0 + 3.039125537798091),
        pool=None,
        diffs=None,
        sides=UnpairedEvidence(of=_CB_OF, against=_CB_AGAINST),
        declaration_index=0,
    )
    bounds = _corrected_bounds(member, 0.025)
    assert bounds is not None
    half = (bounds[1] - bounds[0]) / 2
    assert half == pytest.approx(3.039125537798091 * 1.1706821500146336)
    assert (bounds[0] + bounds[1]) / 2 == pytest.approx(10.0)


def test_an_unpaired_clustered_members_corrected_bound_reads_its_own_two_cluster_counts():
    """Fixture B: raw half-width 34.14810237373095 at df 2.0950313633473936, so the
    corrected half-width at α = 0.025 is that times 1.4227764722656022 — 48.5814…

    **The 21 % gap from the IID ratio is the point.** A corrected bound built from
    the two value vectors while ignoring the label vectors gives the IID Welch
    construction, whose own df is 8.399133841827005 and whose ratio is therefore a
    visibly different number — so this assertion catches a `clusters` field that was
    threaded onto the member and then dropped by the construction, which is the
    failure H4b-2 pinned one axis over."""
    of = (0.0,) * 2 + (15.0,) * 3 + (30.0,) * 4
    against = (2.0,) * 2 + (4.0,) * 3 + (6.0,) * 3 + (8.0,) * 4
    labels = (("p",) * 2 + ("q",) * 3 + ("r",) * 4,
              ("w",) * 2 + ("x",) * 3 + ("y",) * 3 + ("z",) * 4)
    member = Member(
        where="c",
        step="s",
        metric="m",
        delta=12.833333333333332,
        ci95=(12.833333333333332 - 34.14810237373095, 12.833333333333332 + 34.14810237373095),
        pool=None,
        diffs=None,
        sides=UnpairedEvidence(of=of, against=against, clusters=labels),
        declaration_index=0,
    )
    bounds = _corrected_bounds(member, 0.025)
    assert bounds is not None
    half = (bounds[1] - bounds[0]) / 2
    assert half == pytest.approx(34.14810237373095 * 1.4227764722656022)


def test_an_unpaired_percentile_member_reads_a_second_rank_pair_off_its_pool():
    """An unpaired percentile's evidence is a pool of resampled differences,
    structurally identical to a paired one's — so `pool` needs no change and this is
    the arm that must NOT have grown a fourth branch. Asserted as `corrected ⊇ raw`
    off the same pool, which is a property of the arithmetic rather than of two RNG
    calls agreeing."""
    pool = tuple(float(i) for i in range(400))
    member = Member(
        where="c", step="s", metric="m", delta=200.0, ci95=(10.0, 389.0),
        pool=pool, diffs=None, sides=None, declaration_index=0,
    )
    bounds = _corrected_bounds(member, 0.025)
    assert bounds is not None
    assert bounds[0] < 10.0 and bounds[1] > 389.0


def test_the_five_t_arms_are_each_reached_by_one_member_shape():
    """Five *t* arms, counted rather than carried: two under `sides` and three under
    `diffs`, plus the `pool` fall-through. **An implementer writing six leaves an arm
    no input reaches, and one writing four leaves a cell falling through to a wrong
    construction** — so every arm is asserted by the construction its `method` names,
    read off the raw interval each arm rebuilds.

    Asserted as a table rather than one arm at a time, because the failure this
    guards is a cell falling through to a NEIGHBOUR: an unpaired clustered member
    taking the plain Welch arm gives a plausible number 3.5 times too narrow, and
    every existing test still passes because nothing else builds that shape."""
    common = dict(where="c", step="s", metric="m", delta=1.0, declaration_index=0)
    diffs = (1.0, 2.0, 3.0, 4.0)
    shapes = {
        "sides_clustered": dict(
            pool=None, diffs=None,
            sides=UnpairedEvidence(
                of=(1.0, 1.0, 5.0), against=(2.0, 2.0, 8.0),
                clusters=(("a", "a", "b"), ("c", "c", "d")),
            ),
        ),
        "sides_plain": dict(
            pool=None, diffs=None, sides=UnpairedEvidence(of=(1.0, 2.0, 3.0), against=(4.0, 5.0, 7.0))
        ),
        "diffs_clustered": dict(pool=None, diffs=diffs, sides=None, clusters=("a", "a", "b", "b")),
        "diffs_weighted": dict(pool=None, diffs=diffs, sides=None, weights=(1.0, 2.0, 1.0, 2.0)),
        "diffs_plain": dict(pool=None, diffs=diffs, sides=None),
        "pool": dict(pool=tuple(float(i) for i in range(400)), diffs=None, sides=None),
    }
    got = {}
    for name, fields in shapes.items():
        member = Member(ci95=(0.0, 2.0), **common, **fields)
        got[name] = _corrected_bounds(member, 0.025)
    # Every arm returned a bound, so no shape fell through to the final `None`.
    assert all(v is not None for v in got.values()), got
    # And no two arms produced the same bound, so no shape fell through to a
    # neighbour's construction: five distinct *t* answers plus the pool's.
    assert len({tuple(v) for v in got.values() if v is not None}) == 6
```

      Add `_corrected_bounds` and `UnpairedEvidence` to the import block if not already present —
      **read the block rather than assuming**, since task 11 added one of them.

      **The last test's `== 6` is a count in a test, which is fine and is not the thing the prose
      rule forbids** — it is asserting that six inputs give six distinct answers, which is the
      property, not a count of call sites. **If two arms collide on these fixtures, change the
      FIXTURES rather than the assertion**, and record which two collided: two arms that cannot be
      told apart on any input are two arms one of which is unreachable.

- [ ] **Step 2: run and see them fail.** `uv run pytest tests/test_correction.py -k "unpaired or five_t_arms"`
      → the `sides` members return `None`, since `_corrected_bounds` falls through.

- [ ] **Step 3: implement.** Add to `correction.py`'s `from publishable.stats import (...)` block:
      `welch_t_over_units`, `welch_t_over_units_clustered`. Then in `_corrected_bounds`, insert the
      `sides` branch **above** the `diffs` branch:

```python
    if member.sides is not None:
        # WHICH Welch construction rebuilds the bound is decided by whether the
        # evidence carries per-side cluster labels — the same evidence at a smaller α
        # either way. An unpaired clustered raw interval with an unclustered
        # corrected counterpart is narrower by construction rather than by evidence
        # and no reader of `run.yaml` could detect it, which is the fault the
        # exactly-one rule refuses one axis over.
        if member.sides.clusters is not None:
            of_labels, against_labels = member.sides.clusters
            got = welch_t_over_units_clustered(
                member.sides.of,
                of_labels,
                member.sides.against,
                against_labels,
                confidence=1.0 - level,
            )
        else:
            got = welch_t_over_units(
                member.sides.of, member.sides.against, confidence=1.0 - level
            )
        return None if got is None else (got.low, got.high)
```

      **Re-read `_corrected_bounds`' whole docstring after this.** Its opening sentence — *"**What
      decides the construction is which field the member carries, not what kind of metric it is.**"*
      — is still exactly right and gains a third field. Its *"A member carrying per-unit differences
      re-runs `paired_t_over_units`…"* sentence gains a sibling clause for `sides`. Its
      *"`Member.__post_init__` enforces exactly one of the two, so this order is a preference among
      impossible-to-have-both fields rather than a tie-break"* needs **"of the two" narrowed to name
      three** — that is the quantifier, and it is the sentence a reader uses to decide whether the
      order matters. **Do not add a count of arms to the docstring**: the prose rule is no counts, and
      a count here would go stale the next time a construction lands.

- [ ] **Step 4: run and see them pass.** `uv run pytest` → **2246 + 4 = 2250 passed**, 1 skipped,
      2 xfailed. **Task 21's six cells must all still be green** — `_corrected_bounds` gaining an arm
      above the `diffs` branch is precisely what that pin's `ci95_corrected` literals exist to catch.
      Then the other three gates.

- [ ] **Step 5: mutate — four mutations.**

      **Mutation 1 — the clustered arm dropped.** In the `sides` branch, remove the
      `if member.sides.clusters is not None:` test and always call `welch_t_over_units`.
      `test_an_unpaired_clustered_members_corrected_bound_reads_its_own_two_cluster_counts` must
      **FAIL** — the ratio becomes 1.2276 at df 8.399 instead of 1.4228 at df 2.095, and the
      half-width lands near 41.9 instead of 48.6. **Checked against the fixture:** the two dfs differ
      by a factor of four because the fixture's values are constant within cluster, which is
      constraint 4 of § The two discriminating fixtures — on a fixture with within-cluster variation
      CR1 would approximate the IID form and this mutation could hide.

      **Mutation 2 — the corrected level ignored.** Change both `confidence=1.0 - level` to
      `confidence=0.95`. `test_an_unpaired_members_corrected_bound_is_the_welch_form_at_a_smaller_alpha`
      must **FAIL** with the raw half-width 3.0391 where it expects 3.5578.

      **Mutation 3 — the arm placed below `diffs`.** Move the `sides` branch below the `diffs` branch.
      **This mutation is BLIND and it is written down so nobody prescribes it later**: a member
      carrying `sides` carries no `diffs`, `__post_init__` refuses both, so the `diffs` branch is not
      entered and the `sides` branch is reached either way. **The fixture that would discriminate
      cannot be built** — it needs a member carrying two kinds, which `__post_init__` raises on — and
      the order's real protection is that refusal, pinned in task 11's
      `test_a_member_carries_exactly_one_of_pool_diffs_and_sides`. This is the same blindness task
      21's mutation 1 records for the `pool`/`diffs` order, and it has the same cause.

      **Mutation 4 — an arm falling through to a neighbour.** In the `sides` branch, swap
      `member.sides.of` and `member.sides.against` in the **clustered** call only.
      `test_the_five_t_arms_are_each_reached_by_one_member_shape` must **FAIL** on the distinctness
      assertion **only if** the swap changes the number — and **it does not change the half-width**,
      because `var_of + var_against` is symmetric; it flips the centre. **So check the test body
      before believing this mutation**: the distinctness assertion compares `tuple(v)` pairs, which
      DO move when the centre flips, so it discriminates — but for the centre rather than the
      construction. Prescribe it, and **record in the report that it is attributable to the centre
      and not to the df**, which is the honest reading.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/correction.py tests/test_correction.py
git commit -m "feat: _corrected_bounds' two unpaired arms — the Welch forms rebuilt at a smaller alpha"
```

---

## Task 13 (with task 17a): derive `paired` at both branches, and replace the source-text pin

**Runs after task 10**, whose `is_paired` this reads. **Task 17's first half lands in this commit** —
`test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch` fails the moment
either literal becomes conditional, and splitting the two leaves the branch red for a reason
unrelated to both.

**Files:**
- Modify: `src/publishable/cli.py`
- Modify: `src/publishable/contrasts.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `is_paired` at `_comparison_step_blocks`' function scope (task 10);
  `contrasts.crossed_group_axes` (task 9); `_comparison_step_blocks`' two `"paired": True` literals,
  one in the derived branch's record and one in the recorded-column paired arm's, plus the third
  task 10 added on the unpaired arm; `contrasts.differing_axes`' docstring, whose closing paragraph
  names its two callers, one of them *"the (temporarily) hard-coded `paired`"*;
  `tests/test_cli.py::test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch`,
  which asserts `inspect.getsource(_comparison_step_blocks).count('"paired": True') == 2` **and**
  `.count('"paired":') == 2` — read at `e40a219`.
- Produces: `"paired": is_paired` at all three record sites, `differing_axes`' docstring without its
  caller enumeration, and the behavioural pin that replaces the source-text one.

**Why the source-text pin is replaced and not deleted.** Its own docstring records the scope gap:
*"this reads one function's source text, so it is defeated by extracting either write into a helper —
the guarantee it protects is real, but this is not the only way to make the guarantee false and have
this test stay green."* Its replacement is the behavioural pin it could not be: **one run in which a
declared cross-arm contrast records `paired: false` beside a `welch_*`/`unpaired_*` `method` and a
within-arm comparison in the same run still records `true`.** That run needs the retirement, so **the
replacement lands in task 18** and this commit lands the **direct-call** half — the same two claims
through `_comparison_step_blocks`, which is the strongest thing available while `validate` still gates
`run`. Both halves are named in task 17's brief.

**`differing_axes`' docstring is this task's, and task 19's sweep deliberately does not touch it.**
That docstring *names its two callers*, one of them *"the (temporarily) hard-coded `paired`
`_comparison_step_blocks` records"* — a claim about the **call graph**, falsified by tasks 13 and 18
together rather than by any wording a citation sweep would match. **Delete the enumeration rather than
re-enumerate it**: after this slice `cli` calls it directly for `confounded`/`differs_on` while
`validate` reaches it only *through* `crossed_group_axes`, and a rewritten enumeration is a new
maintenance obligation and a fresh chance to be wrong. The plan's own prose rule says the same — no
call-site enumerations, state what a set *is*.

- [ ] **Step 1: write the failing tests.** In `tests/test_cli.py`, **replace the body of**
      `test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch` with the
      direct-call pin, keeping the file position and renaming it:

```python
def test_a_contrast_entrys_paired_flag_is_derived_at_every_branch():
    """Replaces `test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch`,
    which asserted `inspect.getsource` counts of `'"paired": True'` — the mutation
    its docstring said it could not be, because `paired` was a literal and there was
    no runtime state to assert against. H4c gives it that state, so this is the
    behavioural pin: **both answers in the same assertion**, because a derivation
    stuck at `True` and one stuck at `False` are two different defects and each
    passes a test asserting only the other.

    Its predecessor's scope gap is what the replacement closes: reading one
    function's source text is defeated by extracting either write into a helper.
    This reads the record.

    The `run`-through half of the same claim lands with the retirement, where a
    single run carries a cross-arm and a within-arm comparison at once."""
    unpaired, _ = _unpaired_contrast_call()
    assert unpaired["s"]["m"]["paired"] is False
    paired, _ = _clustered_contrast_call()
    assert paired["s"]["m"]["paired"] is True


def test_a_derived_metrics_unpaired_contrast_also_derives_its_flag():
    """Both metric branches, not one. `_comparison_step_blocks` wrote the literal at
    two sites and task 10 added a third, so a derivation applied to the recorded-
    column arm alone leaves the derived branch claiming `paired: true` over disjoint
    arms — the false claim this slice exists to remove, and one that no test of the
    column arm can see.

    The derived branch's other fields are asserted `None` here as the shape they
    already have; task 15 is what makes that a GUARD rather than an accident of an
    empty intersection."""
    of_keys = [f"t{i:02d}" for i in range(5)]
    against_keys = [f"c{i:02d}" for i in range(25)]
    block, _ = _unpaired_contrast_call(
        derived_by_key={(1, "s"): {"m": 20.0}, (0, "s"): {"m": 10.0}},
        resample_fns_by_key={
            (1, "s"): {"m": lambda table: 20.0},
            (0, "s"): {"m": lambda table: 10.0},
        },
    )
    entry = block["s"]["m"]
    assert entry["paired"] is False
    assert entry["n_of"] == 5 and entry["n_against"] == 25
    assert entry["delta"] is None and entry["method"] is None and entry["ci95"] is None


def test_differing_axes_docstring_names_no_caller():
    """The docstring named its two callers and one of them by a claim this slice
    falsifies — "the (temporarily) hard-coded `paired`". A call-site enumeration is
    a maintenance obligation nobody owns and a fresh chance to be wrong, so it is
    DELETED rather than rewritten: a rewrite invents, a deletion cannot.

    Asserted against the surviving text so the deletion cannot be re-seeded as a
    paraphrase, which is how a deleted claim came back three times on H4b-2 — the
    check is on the words that carried the claim, plus a control that the docstring
    still exists."""
    from publishable.contrasts import differing_axes

    doc = differing_axes.__doc__ or ""
    assert "declaration order" in doc  # the control
    assert "temporarily" not in doc
    assert "hard-coded" not in doc
    assert "_comparison_step_blocks" not in doc
```

- [ ] **Step 2: run and see them fail.** `uv run pytest tests/test_cli.py -k "paired_flag or derived_metrics_unpaired or differing_axes_docstring"`
      → the two record tests fail with `True is False`, and the docstring test fails on
      `"temporarily"`.

      **The old source-text test is gone from the run, and that is the point** — it would have failed
      in Step 3 anyway, which is why the replacement lands in this commit.

- [ ] **Step 3: implement.** In `src/publishable/cli.py`, change all three `"paired": True` literals
      to `"paired": is_paired`. **Three sites, and the count is not carried**: locate them by reading
      the function for every `metric_block[metric_key] = {` literal rather than by a grep count, and
      confirm afterwards with `grep -c '"paired": is_paired' src/publishable/cli.py` against a
      can-fail control of `grep -c '"paired": True' src/publishable/cli.py` → **0**.

      Then rewrite `_comparison_step_blocks`' docstring paragraph that begins *"`paired` stays hard
      `True` here"*. It argues at length that `E-DATA-ALLOCATION-CONTRAST` is what makes the literal a
      true claim, and closes with *"**That claim expires with `E-DATA-ALLOCATION-CONTRAST`**: the
      slice that builds the unpaired estimator family and lifts the refusal must also make `paired`
      here a derived value"*. **That whole paragraph is now describing work this commit did**, so
      replace it with the shorter true statement:

```
    `paired` is derived per comparison, from `contrasts.crossed_group_axes` — the
    same expression `validate` refuses a weighted unpaired comparison on, so the
    two cannot disagree about which comparisons share their units. Two conditions
    differing on any declared `sweep.groups` axis hold disjoint sets of units
    whatever `allocation` itself is declared as, and an unpaired entry records
    `n_of`/`n_against` in place of an `n_paired` its intersection cannot supply.
```

      **Re-read the whole docstring afterwards.** Its earlier paragraphs state that both
      constructions read `n_paired` off `stats.paired_keys`, that `W-STATS-CONTRAST-THIN` fires on
      `n_paired`, and that a recorded column *"takes `paired_t_over_units` over the per-unit
      differences"* — **all three become false for the unpaired arm**, and tasks 14 and 16 are what
      make their replacements true. Leave them for those tasks rather than fixing them here, and
      **say so in the task report**: a docstring corrected in three commits is worse than one
      corrected in the commit that finishes the behaviour, but a docstring corrected *before* the
      behaviour is a claim the code does not support.

      In `src/publishable/contrasts.py`, delete `differing_axes`' final paragraph — the one beginning
      *"Lives here, not in `cli.py` or `validate.py`, because both call it"* — and replace it with one
      sentence carrying the part that is still load-bearing and no enumeration:

```
    Lives in this module rather than in `cli.py` or `validate.py` because both read
    it, and a module either of them already imports is what removes the cross-module
    private access and the local import either alternative would need — `cli`
    imports `publishable.validate` at module scope, so `validate` importing `cli`
    back is a true cycle, and `contrasts` sits below both.
```

- [ ] **Step 4: run and see them pass.** `uv run pytest` → **2250 + 2 = 2252 passed**, 1 skipped,
      2 xfailed. **The count is +2 and not +3** because the replaced test occupied one of the three
      names — confirm that arithmetic against the actual output rather than assuming it, and if the
      number differs, find out why before committing.

      **Task 21's six cells must still be green.** They assert `paired is True` on a fixture whose two
      conditions differ only on `analysis.method` with no `selectors`, so the derivation must answer
      `True` there — and that is the half of this change a test asserting only `False` would miss.
      Then the other three gates.

- [ ] **Step 5: mutate — four mutations.**

      **Mutation 1 — the derivation inverted.** Change `is_paired = not crossed_group_axes(...)` to
      `is_paired = bool(crossed_group_axes(...))`. `test_a_contrast_entrys_paired_flag_is_derived_at_every_branch`
      must **FAIL** on **both** assertions, and task 21's six cells must fail on `paired is True`.
      **Checked:** the two fixtures answer opposite ways, which is why both are in one test.

      **Mutation 2 — one branch left literal.** Change the derived branch's `"paired": is_paired`
      back to `"paired": True`. `test_a_derived_metrics_unpaired_contrast_also_derives_its_flag` must
      **FAIL** while `test_a_contrast_entrys_paired_flag_is_derived_at_every_branch` **passes** — the
      pair is what says both branches are covered rather than one twice.

      **Mutation 3 — the unpaired arm left literal.** Change the unpaired recorded-column arm's
      `"paired": is_paired` back to `"paired": True`. The first test must **FAIL** and the derived one
      **pass** — the mirror of mutation 2, and running both is what says the three sites are
      independently covered.

      **Mutation 4 — the docstring claim re-seeded.** Add the sentence *"the (temporarily) hard-coded
      `paired`"* back into `differing_axes`' docstring. `test_differing_axes_docstring_names_no_caller`
      must **FAIL**. **This is a mutation on a comment and it is prescribed deliberately**: *"a safety
      argument in a comment is a claim, and needs a mutation like any other"*, and on H4b-2 a deleted
      claim returned as a paraphrase no literal search matched.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 6: Commit.** One commit for task 13 and task 17a, per the ordering constraint.

```bash
git add src/publishable/cli.py src/publishable/contrasts.py tests/test_cli.py
git commit -m "feat: paired derived at every contrast branch, and the source-text pin replaced by a behavioural one"
```

---

## Task 14: the `method` and `cohens_d` selection across the reachable cells

**Runs after task 13 and after every construction (4, 5, 6, 7, 8).** This is the task that gives all
four constructions a production caller in `cli`; before it they have one only in `correction.py`.
**It wires `cohens_ds` as well as the `method`** — see deviation (d): the spec builds `cohens_ds` in
task 5 and wires it nowhere, and `cohens_d` is the record's other construction-dependent field,
keyed on the same `is_paired` answer.

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `stats.welch_t_over_units(of, against)`; `stats.welch_t_over_units_clustered(of,
  of_labels, against, against_labels)`; `stats.unpaired_percentile_of_sides(of, against, of_keys,
  against_keys, compute_of, compute_against, seed, draws=, confidence=, strata=, method=,
  of_clusters=, against_clusters=)`; `stats.cohens_ds(of, against)`;
  `correction.UnpairedEvidence(of, against, clusters=)`; task 10's unpaired arm with its
  `of_values`/`against_values`/`of_col`/`against_col` and its `interval = None`;
  `_comparison_step_blocks`' `_column_mean` closure pattern and the paired arm's `method=` argument,
  which H4b-2's correction 2 established as the caller's to pass.
- Produces: the unpaired arm's interval, `method`, `cohens_d` and `Member(sides=...)`. After this
  task an unpaired contrast is complete except for the derived suppression (task 15), the thin
  warning (task 16) and the retirement (task 18).

**Four reachable unpaired cells, and no more.** `{plain, clustered} × {t, percentile}` — the weighted
cells are refused by `E-DATA-WEIGHT-ALLOCATION-CONTRAST` and unreachable by task 10's `ValueError`,
and the derived cell is suppressed. **Four, counted rather than carried**: an implementer writing six
leaves two cells no input reaches, and one writing two leaves a cell falling through to a neighbour's
`method`.

**The *t* arm's string comes from the construction and the percentile arm's from a `method=`
argument.** That asymmetry is H4b-2's correction 2 and it is deliberate: a *t* construction is one
function per spelling, while `unpaired_percentile_of_sides` is one function serving two.

**`cohens_d` is *d*s for an unpaired column contrast, and it does not read the interval.** § Statistical
reporting: *"paired contrasts report *d*z … and unpaired ones report *d*s, over the pooled
within-condition standard deviation … *d*s pools where `welch_t_over_units` deliberately doesn't."*
So the selection keys on `is_paired` and **not** on which interval arm ran — the same way `cohens_dz`
survives the resample switch today, computed from the local vectors rather than from anything the
`Member` carries.

- [ ] **Step 1: write the failing tests.** Append to `tests/test_cli.py`:

```python
_UNPAIRED_CLUSTERS = (
    {f"t{i:02d}": lbl for i, lbl in enumerate(["p"] * 2 + ["q"] * 2 + ["r"])}
    | {f"c{i:02d}": f"h{i // 7}" for i in range(25)}
)


@pytest.mark.parametrize(
    "clustered,resampled,expected",
    [
        (False, False, "welch_t_over_units"),
        (False, True, "unpaired_percentile_over_units"),
        (True, False, "welch_t_over_units_clustered"),
        (True, True, "unpaired_percentile_over_units_clustered"),
    ],
)
def test_every_reachable_unpaired_contrast_cell_writes_its_own_method(
    clustered, resampled, expected
):
    """Every reachable combination of `cluster_by` and a declared `resample` on an
    unpaired comparison, and the `method` § Statistical reporting defines or licenses
    for each. The two weighted cells are absent by construction —
    `E-DATA-WEIGHT-ALLOCATION-CONTRAST` refuses them at `validate` and
    `_comparison_step_blocks` raises on them — so this is a four-cell table over two
    independent declarations rather than a six-cell one with cells missing.

    Asserted as a table because the failure this guards is a cell FALLING THROUGH to
    a neighbour's `method`: an implementer writing two arms leaves two cells
    publishing a string naming a construction the run did not use, and every
    existing test still passes since nothing else builds those fixtures."""
    block, _ = _unpaired_contrast_call(
        resample_columns=resampled,
        clusters=_UNPAIRED_CLUSTERS if clustered else None,
    )
    assert block["s"]["m"]["method"] == expected


def test_an_unpaired_column_contrast_takes_the_welch_t():
    """Fixture A through the record. Delta 10, and the half-width 3.039125537798091
    at df 96/7 — **the number is the assertion**, because a Welch interval that
    coincides with a pooled one proves nothing, and the pooled reading on this data
    gives 4.7221 while `min(n) − 1` gives 3.9265 and the total-df reading 2.8969.

    All three facts move together, which is the obligation H4b-1 pinned after a
    per-side key passed under a hardcoded constant: the interval, the `method` and
    the two counts."""
    block, _ = _unpaired_contrast_call()
    entry = block["s"]["m"]
    assert entry["method"] == "welch_t_over_units"
    assert entry["delta"] == pytest.approx(10.0)
    assert (entry["ci95"][1] - entry["ci95"][0]) / 2 == pytest.approx(3.039125537798091)
    assert entry["n_of"] == 5 and entry["n_against"] == 25


def test_an_unpaired_column_contrast_reports_cohens_ds_not_dz():
    """§ Statistical reporting: unpaired contrasts report *d*s over the pooled
    within-condition sd, and *d*s pools where `welch_t_over_units` deliberately
    doesn't. On fixture A the pooled sd is 4.705619740571601, so *d*s is
    2.1251185925162073 — while standardizing by the interval's own Welch
    denominator would give 7.0710678118654755, a factor of 3.33.

    **The literal is the assertion, not `is not None`.** A *d* is a number readers
    compare across papers, and every wrong denominator here still returns a
    plausible float."""
    block, _ = _unpaired_contrast_call()
    assert block["s"]["m"]["cohens_d"] == pytest.approx(2.1251185925162073)


def test_an_unpaired_contrast_member_carries_two_sides_and_no_diffs():
    """The member is what the correction family rebuilds from, so an unpaired raw
    interval whose member carried no per-side vectors would get no corrected bound
    at all — `thin: True` over a member that was never thin. Asserted beside
    `diffs is None` and `pool is None`, because `_corrected_bounds` tests `sides`
    first and a member carrying two kinds is refused rather than resolved.

    Under a declared `resample` the member carries the POOL instead and `sides` is
    `None`, the same single `corrected_from_pool` decision the paired arm reads once
    for all its fields — asserted here so the two cannot disagree."""
    _, members = _unpaired_contrast_call()
    assert len(members) == 1
    assert members[0].sides is not None
    assert members[0].sides.of == tuple(_UNPAIRED_OF)
    assert members[0].sides.against == tuple(_UNPAIRED_AGAINST)
    assert members[0].sides.clusters is None
    assert members[0].diffs is None and members[0].pool is None
    _, clustered = _unpaired_contrast_call(clusters=_UNPAIRED_CLUSTERS)
    assert clustered[0].sides is not None
    assert clustered[0].sides.clusters is not None
    assert len(clustered[0].sides.clusters[0]) == 5
    assert len(clustered[0].sides.clusters[1]) == 25
    _, resampled = _unpaired_contrast_call(resample_columns=True)
    assert resampled[0].sides is None
    assert resampled[0].pool is not None


def test_an_unpaired_clustered_contrast_records_its_two_counts_and_a_cluster_robust_interval():
    """The three facts a cluster adds to an unpaired entry, moving together: the
    interval reads the cluster as the draw, the `method` says so, and the two
    counts say how many clusters each side has. **A cluster-robust interval that is
    merely wider is not evidence** — over positively correlated data it comes out
    wider whatever df it uses — so the two integer counts carry the discrimination
    a float assertion could be argued about, and they cannot coincide: 3 against 4."""
    block, _ = _unpaired_contrast_call(clusters=_UNPAIRED_CLUSTERS)
    entry = block["s"]["m"]
    assert entry["method"] == "welch_t_over_units_clustered"
    assert entry["n_clusters_of"] == 3
    assert entry["n_clusters_against"] == 4
    unclustered, _ = _unpaired_contrast_call()
    assert entry["ci95"] != unclustered["s"]["m"]["ci95"]
    # CAPTURE-AND-PASTE: the clustered half-width, from this test's first green run.
    assert (entry["ci95"][1] - entry["ci95"][0]) / 2 == pytest.approx(0.0)
```

      **`_UNPAIRED_CLUSTERS` gives the `of` side 3 clusters (2/2/1) and the `against` side 4 (7/7/7/4)
      — two integers that cannot coincide**, which is the documented *"both 3"* failure closed by
      construction. It is the same mapping task 10's cluster-count test builds; **hoist it to a module
      constant in this commit and have task 10's test use it**, or leave both — but do not let two
      spellings of one fixture drift.

- [ ] **Step 2: run and see them fail.** `uv run pytest tests/test_cli.py -k "unpaired"` → the
      parametrized table fails with `method is None` on every cell.

- [ ] **Step 3: implement.** In `_comparison_step_blocks`' unpaired recorded-column arm, replace
      `interval = None` with the selection:

```python
                    of_clusters = (
                        None if clusters is None else {k: clusters[k] for k in of_col}
                    )
                    against_clusters = (
                        None if clusters is None else {k: clusters[k] for k in against_col}
                    )
                    if resample_columns and len(of_col) >= 2 and len(against_col) >= 2:
                        # The same closure the paired arm uses, and the same
                        # argument for reusing it: both sides compute the mean of
                        # the same column, which is one formula rather than the
                        # shared-closure cancellation a swept axis produces. No
                        # weight branch, because a weighted unpaired comparison
                        # raises above.
                        def _unpaired_column_mean(
                            table: UnitTable, _name: str = metric_key
                        ) -> float:
                            column: list[float] = getattr(table, _name)
                            return float(sum(column) / len(column))

                        resampled = unpaired_percentile_of_sides(
                            of_collapsed,
                            against_collapsed,
                            of_col,
                            against_col,
                            _unpaired_column_mean,
                            _unpaired_column_mean,
                            seed,
                            draws=draws,
                            strata=strata,
                            # One spelling per declaration. The construction is ONE
                            # function serving two `method` strings, so the string is
                            # the caller's to pass — the asymmetry with the *t* arm
                            # below, where each spelling is its own function.
                            method=(
                                "unpaired_percentile_over_units_clustered"
                                if clusters is not None
                                else "unpaired_percentile_over_units"
                            ),
                            of_clusters=of_clusters,
                            against_clusters=against_clusters,
                        )
                        interval = resampled.interval
                    elif of_clusters is not None and against_clusters is not None:
                        interval = welch_t_over_units_clustered(
                            of_values,
                            [of_clusters[k] for k in of_col],
                            against_values,
                            [against_clusters[k] for k in against_col],
                        )
                    else:
                        interval = welch_t_over_units(of_values, against_values)
```

      **`of_col`/`against_col` order, not the roster's**, for the reason the paired arm's
      `col_weights` comment gives: a vector ordered differently from the values beside it aligns the
      wrong unit, and `_cr1_variance` zips the two with `strict=True` so a length mismatch raises
      rather than producing a plausible number.

      Then the record's `cohens_d`:

```python
                        "cohens_d": cohens_ds(of_values, against_values),
```

      and the `Member` call gains the third evidence field. **Read the existing `corrected_from_pool`
      comment before editing it** — it says *"the single decision, read once for all three fields, so
      `pool`, `weights` and `clusters` cannot disagree"* — and extend that single decision to four:

```python
                    sides=(
                        None
                        if corrected_from_pool or is_paired
                        else UnpairedEvidence(
                            of=tuple(of_values),
                            against=tuple(against_values),
                            clusters=(
                                None
                                if of_clusters is None or against_clusters is None
                                else (
                                    tuple(of_clusters[k] for k in of_col),
                                    tuple(against_clusters[k] for k in against_col),
                                )
                            ),
                        )
                    ),
```

      **`of_values`/`against_values`/`of_clusters`/`against_clusters` are bound only inside the
      unpaired arm**, and the `Member` is built after both arms — so **pre-bind all four at the top of
      the metric loop beside `of_col`/`against_col`**, exactly as `col_weights`/`col_clusters` are
      pre-bound and for the reason that comment gives: *"so the name is always defined … relying on
      `corrected_from_pool`'s short-circuit to keep it out of reach there would make an unrelated
      refactor of that expression silently load-bearing."*

      Add to `cli.py`'s imports: `cohens_ds`, `unpaired_percentile_of_sides`, `welch_t_over_units`,
      `welch_t_over_units_clustered` from `publishable.stats`, and `UnpairedEvidence` from
      `publishable.correction`.

      Finally, repair the `_comparison_step_blocks` docstring claims task 13 deliberately left
      standing: *"A recorded column takes `paired_t_over_units` over the per-unit differences"* and
      *"Both constructions read `n_paired` off `stats.paired_keys`"*. **Narrow the quantifier rather
      than enumerating the new cells** — that is `efa13bc`'s own repair and H4b-2's decision 5 — so
      each becomes a claim about a **paired** column and a **paired** comparison, with one sentence
      saying an unpaired one takes the Welch or the per-side percentile form over
      `stats.unpaired_keys` instead.

- [ ] **Step 4: capture the clustered half-width and paste it in**, deleting the
      `CAPTURE-AND-PASTE` comment, in this same commit. **Cross-check it against fixture B's table
      before accepting it**: the fixture here is fixture A's values with a 3/4 cluster split, not
      fixture B, so the number is new — but it must be **wider** than 3.039125537798091 and must not
      equal any of fixture A's four mutant half-widths. If it equals one of them, change the cluster
      split and say why.

- [ ] **Step 5: run and see them pass.** `uv run pytest` → **2252 + 8 = 2260 passed**, 1 skipped,
      2 xfailed. Task 21's six cells must still be green. Then the other three gates.

- [ ] **Step 6: mutate — five mutations.**

      **Mutation 1 — a cell falling through.** Remove the `elif of_clusters is not None ...` arm so
      the clustered *t* cell falls to `welch_t_over_units`.
      `test_every_reachable_unpaired_contrast_cell_writes_its_own_method[True-False-...]` must
      **FAIL** on the `method`, and
      `test_an_unpaired_clustered_contrast_records_its_two_counts_and_a_cluster_robust_interval` must
      **FAIL** on the half-width — the pair says the string and the construction are both pinned,
      which the string alone does not.

      **Mutation 2 — the percentile `method` argument dropped.** Remove the `method=` argument so the
      construction's default is used. The `[True-True-...]` cell must **FAIL**, seeing
      `unpaired_percentile_over_units`. **Checked:** the default is the plain spelling, so the
      clustered cell is the only one that moves — which is why the table has both.

      **Mutation 3 — *d*z for an unpaired contrast.** Change `cohens_ds(of_values, against_values)`
      to `cohens_dz([a - b for a, b in zip(of_values, against_values)])`.
      `test_an_unpaired_column_contrast_reports_cohens_ds_not_dz` must **FAIL**. **Checked against
      the fixture:** `zip` truncates to 5 pairs, so this returns a *d* over five arbitrary
      differences — a plausible float, and exactly the shape a reader could not detect is wrong,
      which is why the assertion is a literal.

      **Mutation 4 — the member's sides dropped.** Change `sides=` to `None`.
      `test_an_unpaired_contrast_member_carries_two_sides_and_no_diffs` must **FAIL**, and
      `Member.__post_init__` must **raise** on the non-resampled cell, since `ci95` is present and no
      evidence field is set — **record which happens first**, because a raise says the exactly-one
      rule is doing the work and a quiet `None` says only the test is.

      **Mutation 5 — one side's cluster labels for both.** Change the clustered *t* call's second
      label list to `[of_clusters[k] for k in of_col]`.
      `test_an_unpaired_clustered_contrast_records_its_two_counts_and_a_cluster_robust_interval` must
      **FAIL** — `_cr1_variance` zips 25 values against 5 labels with `strict=True`, so it raises
      rather than returning a wrong number. **That is the property the per-side signature buys**, and
      it is worth recording as a raise rather than a silent number.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 7: Commit.**

```bash
git add src/publishable/cli.py tests/test_cli.py
git commit -m "feat: the four reachable unpaired contrast cells, their methods and cohens_ds"
```

---

## Task 16: `W-STATS-CONTRAST-THIN` and `limits.min_reported_n`, per side at both emit sites

**Runs after tasks 2 and 13.** **§ Errors carries one row per code covering every emit site**, and
this code has **two**: one at `validate`, over the roster units matching the `within` stratum, and one
at `run`, over the comparison's realized denominator. **The spec's decision 6 quotes only the
run-side reading, and the validate-side message asserts something this slice makes false** — recorded
in the spec's § Corrections against the code, and this task owns both.

**Files:**
- Modify: `src/publishable/cli.py`
- Modify: `src/publishable/validate.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `_comparison_step_blocks`' warning guard
  `if comp.within is not None and min_reported_n is not None and n_paired < min_reported_n:` and its
  message `f"{where}, step {step_name!r} metric {metric_key!r}: n_paired {n_paired} is below
  limits.min_reported_n ({min_reported_n})"`, with task 10's placeholder in place of `n_paired`;
  `validate._check_stats`' per-contrast-entry warning whose message reads *"selects {stratum}, which
  {len(matched)} of {len(roster)} units match, below limits.min_reported_n ({floor}). The run counts
  `n_paired` over the two sides' completed units, which attrition can only make smaller"*; task 2's
  § Contrasts restatement — all read in `src/publishable/`.
- Produces: one warning per metric entry naming every denominator below the floor, and a validate-side
  message that no longer names a key an unpaired contrast does not record.

**Both apply per side, and fire when EITHER side is below the limit.** § Validation's row reads *"the
comparison's realized `n_paired` is below it"* and § Contrasts grounds it in *"a stratified paired
comparison is where a small denominator is easiest to miss and most disclosive"*. **The disclosive
quantity is a thin denominator anywhere**, not a thin intersection specifically: a five-unit arm
compared against a five-hundred-unit one is exactly the disclosure the limit exists to catch, and any
rule reading only one side or only a total would pass it.

**One warning per entry, not one per thin side.** The warning is about the entry's disclosure, and two
findings for one entry would double-count in any consumer that counts them. So the denominators are
collected and the message names every one below the floor.

**The paired message's wording moves, and nothing asserts it.** Measured at `e40a219`: every test
touching this code asserts the code's presence or absence, and the only message assertion is on the
**validate**-side text (`"`dx_family=rare`"` and `"2 of 12 units"`). So one expression serving both
readings is preferred to two spellings of one rule, and the paired text changes from *"n_paired 5 is
below"* to *"n_paired 5 — below"*. **Say so in the task report** rather than letting it be discovered.

- [ ] **Step 1: write the failing tests.** In `tests/test_cli.py`:

```python
def test_an_unpaired_within_contrast_warns_when_either_side_is_thin():
    """Decision 6. § Validation's row keys the warning on the comparison's realized
    denominator, and an unpaired contrast has two — so the rule reading "either" is
    the one that preserves the row's own reason: the disclosive quantity is a thin
    denominator ANYWHERE, and a five-unit arm against a five-hundred-unit one is
    exactly what the limit exists to catch.

    The fixture is asymmetric on purpose: `of` keeps 3 units and `against` keeps 20,
    with a floor of 10, so only ONE side is below it. A rule reading a total (23) or
    the larger side would not warn at all, and a fixture where both sides were thin
    could not tell those readings from this one."""
    from publishable.contrasts import Comparison
    from publishable.diagnostics import Collector
    from publishable.units import Unit, UnitList

    of_keys = [f"t{i:02d}" for i in range(5)]
    against_keys = [f"c{i:02d}" for i in range(25)]
    keep = set(of_keys[:3]) | set(against_keys[:20])
    roster = UnitList(
        [
            Unit(key=k, attributes={"site": "north" if k in keep else "south"})
            for k in of_keys + against_keys
        ]
    )
    findings = Collector()
    block, _ = _unpaired_contrast_call(
        roster=roster,
        findings=findings,
        min_reported_n=10,
        _comparison=Comparison(
            id="arm_effect", of=1, against=0, within={"site": "north"}, declared=True
        ),
    )
    assert block["s"]["m"]["n_of"] == 3 and block["s"]["m"]["n_against"] == 20
    thin = [f for f in findings.findings if f.code == "W-STATS-CONTRAST-THIN"]
    assert len(thin) == 1
    assert "n_of 3" in thin[0].message
    assert "n_against" not in thin[0].message


def test_an_unpaired_contrast_with_two_healthy_sides_does_not_warn():
    """The control that must not report, paired with a presence: a check firing on
    every unpaired contrast would pass the test above too. Both sides clear the
    floor, and the entry is asserted present so the absence is not the absence of a
    contrast."""
    from publishable.contrasts import Comparison
    from publishable.diagnostics import Collector
    from publishable.units import Unit, UnitList

    of_keys = [f"t{i:02d}" for i in range(5)]
    against_keys = [f"c{i:02d}" for i in range(25)]
    roster = UnitList([Unit(key=k, attributes={"site": "north"}) for k in of_keys + against_keys])
    findings = Collector()
    block, _ = _unpaired_contrast_call(
        roster=roster,
        findings=findings,
        min_reported_n=3,
        _comparison=Comparison(
            id="arm_effect", of=1, against=0, within={"site": "north"}, declared=True
        ),
    )
    assert block["s"]["m"]["n_of"] == 5  # the presence that must report
    assert [f for f in findings.findings if f.code == "W-STATS-CONTRAST-THIN"] == []


def test_a_paired_within_contrast_still_warns_on_its_intersection():
    """The regression half. One expression serves both readings, so the paired
    reading must be unchanged: `n_paired` against the floor, named in the message.
    A rule restructured for two sides that stopped reading the intersection would
    silence every warning this code has ever emitted."""
    from publishable.contrasts import Comparison
    from publishable.diagnostics import Collector
    from publishable.units import Unit, UnitList

    keys = [f"u{i:02d}" for i in range(12)]
    roster = UnitList([Unit(key=k, attributes={"site": "north"}) for k in keys])
    findings = Collector()
    _clustered_contrast_call(
        roster=roster,
        findings=findings,
        min_reported_n=20,
        comp_override=Comparison(id="c", of=1, against=0, within={"site": "north"}),
    )
    thin = [f for f in findings.findings if f.code == "W-STATS-CONTRAST-THIN"]
    assert len(thin) == 1
    assert "n_paired 12" in thin[0].message
```

      **`_clustered_contrast_call` builds its own `Comparison` and takes no override** — read it, and
      add the same `_comparison=` parameter task 10 added to `_unpaired_contrast_call` rather than
      duplicating the helper. Use one parameter name in both; the body above writes `comp_override`
      deliberately as a marker that **the implementer must pick one spelling and use it in both
      helpers and all three tests**.

      In `tests/test_validate.py`, beside the existing thin-stratum tests:

```python
def test_the_validate_time_thin_warning_names_no_key_it_cannot_promise(
    write_config, tmp_path
):
    """The validate-side emit's message asserted "The run counts `n_paired` over the
    two sides' completed units", which is false of an unpaired contrast — the run
    counts `n_of` and `n_against` there. This check cannot tell the two apart: it
    reads the roster units matching the stratum, before any condition exists.

    So the false half is DELETED rather than rewritten into a conditional it cannot
    evaluate — a rewrite invents and a deletion cannot — and the surviving claim,
    that attrition can only make the denominator smaller, is true of both readings.
    The stratum and the count stay asserted, because they are what the warning is
    for."""
    path = write_config(...the fixture the existing thin-stratum test uses...)
    message = messages_by_code(path)["W-STATS-CONTRAST-THIN"]
    assert "units match" in message  # the control
    assert "attrition can only make" in message
    assert "n_paired" not in message
```

      **Copy the fixture from the existing test that asserts `"2 of 12 units"` in this message** —
      read it, name it in the docstring, and do not build a second roster for the same claim.

- [ ] **Step 2: run and see them fail.** The three `cli` tests fail on the message text or on the
      finding count; the `validate` test fails on `"n_paired" not in message`.

- [ ] **Step 3: implement the run-side warning.** Replace task 10's placeholder guard with one
      expression serving both readings:

```python
            # § Validation keys this on the comparison's realized denominator, and an
            # unpaired comparison has two — so it fires where EITHER is below the
            # floor. § Contrasts grounds the row in "a stratified comparison is where
            # a small denominator is easiest to miss and most disclosive", and the
            # disclosive quantity is a thin denominator anywhere: a five-unit arm
            # against a five-hundred-unit one is exactly what the limit exists to
            # catch, and a rule reading one side or a total would pass it.
            #
            # ONE finding per metric entry, naming every denominator below the floor.
            # The warning is about this entry's disclosure, and two findings for one
            # entry would double-count in any consumer that counts them.
            #
            # Scoped to a comparison declaring a `within`, because that is the scope
            # `reference.md` gives it three times over — § Contrasts, § The one config
            # file's comment, and the § Validation row. `min_reported_n: 10` is in
            # every generated config, so warning on every comparison would fire on
            # any pilot under ten units for a comparison the document never scoped it
            # to.
            if comp.within is not None and min_reported_n is not None:
                denominators = (
                    (("n_paired", len(base_keys) if is_derived else len(col_keys)),)
                    if is_paired
                    else (("n_of", len(of_col)), ("n_against", len(against_col)))
                )
                thin = [
                    f"{name} {value}"
                    for name, value in denominators
                    if value < min_reported_n
                ]
                if thin:
                    findings.warn(
                        "W-STATS-CONTRAST-THIN",
                        "limits.min_reported_n",
                        f"{where}, step {step_name!r} metric {metric_key!r}: "
                        f"{' and '.join(thin)} — below limits.min_reported_n "
                        f"({min_reported_n})",
                    )
```

- [ ] **Step 4: repair the validate-side message, by deletion.** In `validate._check_stats`, delete
      the sentence's false clause and keep the true one:

```python
                        f"selects {stratum}, which {len(matched)} of {len(roster)} units "
                        f"match, below limits.min_reported_n ({floor}). The run counts "
                        f"this comparison's own denominator over the two sides' completed "
                        f"units, which attrition can only make smaller",
```

      **This is a deletion of the key name, not a rewrite of the sentence**: "`n_paired`" is the only
      false word, and the surviving claim is true of a paired intersection and of two per-side counts
      alike. **Re-read the whole message and the whole comment block above it** — the comment argues
      about skipping a stratum whose attribute was just refused, which is unaffected.

- [ ] **Step 5: run and see them pass.** `uv run pytest` → **2260 + 4 = 2264 passed**, 1 skipped,
      2 xfailed. **The existing validate-side test asserting `"2 of 12 units"` must still be green**,
      and every `W-STATS-CONTRAST-THIN` presence/absence test in both files must be unchanged. Then
      the other three gates.

- [ ] **Step 6: mutate — four mutations.**

      **Mutation 1 — the total instead of either side.** Change `denominators`' unpaired arm to
      `(("n_total", len(of_col) + len(against_col)),)`.
      `test_an_unpaired_within_contrast_warns_when_either_side_is_thin` must **FAIL** — 23 is above
      the floor of 10, so nothing warns. **Checked against the fixture:** 3 + 20 = 23 > 10 while
      3 < 10, so the two readings genuinely differ, which a fixture with two thin sides could not
      show.

      **Mutation 2 — the larger side only.** Change it to
      `(("n_against", len(against_col)),)`. The same test must **FAIL** — 20 clears the floor.
      Mutations 1 and 2 are different wrong readings of the same row and both are silent, which is
      why the fixture is asymmetric.

      **Mutation 3 — the paired reading lost.** Change `denominators`' paired arm to the unpaired one
      unconditionally. `test_a_paired_within_contrast_still_warns_on_its_intersection` must **FAIL**
      on `"n_paired 12" in thin[0].message`. **Checked:** on `_clustered_contrast_call`'s fixture the
      two sides hold the same 12 keys, so a per-side reading would name `n_of 12` — a different string
      at the same number, which is exactly why the assertion is on the message rather than on the
      count.

      **Mutation 4 — the `within` scope dropped.** Remove `comp.within is not None` from the guard.
      `test_an_unpaired_contrast_with_two_healthy_sides_does_not_warn` still passes (both sides clear
      the floor), so **run task 21's six cells too**: `_clustered_contrast_call` passes
      `min_reported_n=None`, so they also pass. **This mutation is BLIND on the fixtures in this
      task**, and the fixture that would discriminate is a comparison with **no** `within` and a floor
      above its `n` — **add it**, as a third `cli` test asserting no warning for a `within`-less
      comparison at `min_reported_n=20`. Naming a seam is not testing it, and the `within` scope is a
      documented rule with three sources.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 7: Commit.**

```bash
git add src/publishable/cli.py src/publishable/validate.py tests/test_cli.py tests/test_validate.py
git commit -m "fix: W-STATS-CONTRAST-THIN reads a comparison's own denominators, per side at both emit sites"
```

---
## Task 17: the two pins the scoping requires — replaced and converted, never deleted

**This task has no commit of its own.** Its two halves land inside tasks 13 and 18, by constraint:
each pin fails the moment its own change lands, and splitting either leaves the branch red for a
reason unrelated to both. **Deleting either pin is the one move H4c may not make** — they exist to
force the clustered unpaired constructions into the same slice as the retirement, which is H4b-2's
decision 2 read forward.

**Files:** `tests/test_cli.py` (17a, in task 13's commit), `tests/test_validate.py` and
`tests/test_cli.py` (17b, in task 18's commit).

### 17a — replace the source-text pin, in task 13's commit

`tests/test_cli.py::test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch`
asserts `inspect.getsource(_comparison_step_blocks)` contains `'"paired": True'` exactly **2** times
**and** `'"paired":'` exactly **2** times. Both counts, deliberately: the first alone passes under a
third branch writing `"paired": is_paired`, the second alone under two sites that both became
conditional. **It fails on both assertions the moment either site becomes conditional, which is
precisely the change task 13 makes.**

Its own docstring records the scope gap the replacement closes: *"this reads one function's source
text, so it is defeated by extracting either write into a helper — the guarantee it protects is real,
but this is not the only way to make the guarantee false and have this test stay green."*

**The replacement is in two halves and both are named here so neither is lost.** Task 13 lands the
direct-call half — `test_a_contrast_entrys_paired_flag_is_derived_at_every_branch` and
`test_a_derived_metrics_unpaired_contrast_also_derives_its_flag`, whose bodies are in task 13's Step 1.
**Task 18 lands the `run`-through half**, which the pin's own replacement description requires and
which `validate` gates until then: **one run in which a declared cross-arm contrast records
`paired: false` beside a `welch_*`/`unpaired_*` `method` AND a within-arm comparison in the same run
still records `true`.** Its body is in task 18's Step 1 as
`test_one_run_records_both_pairings_and_the_method_that_goes_with_each`.

### 17b — convert the exact-set pin, in task 18's commit

`tests/test_validate.py::test_a_contrast_beside_groups_and_cluster_by_draws_the_allocation_refusal`
asserts the **exact set** `_error_codes(write_config(doc)) == {"E-DATA-ALLOCATION-CONTRAST"}` for a
declared cross-arm contrast beside `cluster_by`. Retiring the code makes the set `{}`, so the
assertion fails — **and that failure is the tripwire working.** Its fixture is a **clustered**
cross-arm contrast, which is what forces `welch_t_over_units_clustered` and
`unpaired_percentile_over_units_clustered` into this slice: the conversion is honest only once both
exist.

**Converted, not deleted**, into two things in task 18's commit:

1. **The clean-composition control**, beside the sibling `test_groups_and_cluster_by_compose_with_no_comparison`
   that already asserts `_error_codes(...) == set()` for the same fixture **without** a comparison:
   the same fixture **with** the cross-arm contrast now also validates clean, which is the whole
   content of the retirement. Keep it as an **exact set** — `== set()` — because a filtered assertion
   here would pass under any refusal this design should not draw.
2. **The run-side assertion that the entry's `method` carries `_clustered`**, which is what says the
   clustered constructions were reached rather than merely built. It lands as task 18's
   `test_a_clustered_cross_arm_contrast_runs_and_records_a_cluster_robust_interval`.

**The renamed test keeps its position in the file and its docstring records what it replaced**, so a
reader greping for the old name finds the conversion rather than nothing.

---

## Task 15 + 17b + 18: the derived suppression guard, the converted pin, and the retirement — one commit

**Three tasks, one commit, and the reasons are two ordering constraints rather than convenience.**
Task 15's guard cannot be verified before the retirement, because `validate` gates `run` and decision
8 requires an end-to-end `run`; and landing it **after** leaves the retirement commit shipping an
unguarded derived unpaired path — a window in which a derived unpaired contrast publishes a number
from nothing with `validate` reporting zero errors. **On H4b-2 the retirement commit was exactly the
commit whose re-check was silently dropped, and only the whole-branch review found it.** Task 17b's
half fails the moment the code is deleted.

**Runs after every construction (4–8), after 9, and after 10–14 and 16.** Retiring the guard while a
construction is missing routes a declared cross-arm comparison to a *paired* construction over an
empty intersection, publishing `delta: null, paired: true, n_paired: 0` with `validate` reporting zero
errors.

**Files:**
- Modify: `src/publishable/cli.py`
- Modify: `src/publishable/validate.py`
- Modify: `docs/reference.md`
- Test: `tests/test_cli.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `_comparison_step_blocks`' derived branch guard
  `if compute_of is not None and compute_against is not None and clusters is None:`, whose comment
  block argues the clusters ground at length; `is_paired` (task 10); `validate._check_sweep`'s
  `E-DATA-ALLOCATION-CONTRAST` emit and its 40-line comment block, inside the
  `for comp in resolved_contrasts` loop task 9 rewired; `reference.md` § Validation's *Allocation
  deltas aren't computed* row and § Errors' `E-DATA-ALLOCATION-CONTRAST` row; task 2's documented
  unpaired-derived suppression sentence.
- Produces: a two-ground suppression guard, an `E-DATA-ALLOCATION-CONTRAST`-free `validate`, and the
  first end-to-end `run` of an unpaired contrast in this repo's history.

**Decision 8's guard reads the pairing derivation's own answer, not an empty `base_keys`.** An empty
`base_keys` is a **proxy**: it is also empty when two genuinely paired conditions share no completed
units, which is a defect to report rather than a design to honour — the substitution `CLAUDE.md`
§ Answering a question with a proxy is about, one axis over.

**The two grounds are ONE guard naming both, never two accreted checks.** After this slice the derived
branch carries two independent suppression conditions, a declared cluster and an unpaired comparison.
**A later reader taking one as covering the other is the *fourth* wrong ground this corner was already
given** — *"the same clusters-guarded suppression `E-DATA-CLUSTER-DERIVED` states for the
recorded-column path applies to the contrast over that key too"*, disproved by running.

**The whole-branch hazard, stated where the implementer will meet it.** On H4b-2, with the refusal
gone, a derived key colliding with a recorded column's name published an *unclustered* contrast
interval — half-width 2.0 beside per-condition cluster-robust values at 10.31, `validate` reporting
zero errors — reachable because `derived_by_key` and `resample_fns_by_key` are both built before the
`summarize_step` call whose `except ContractError` retry clears neither. **Only an end-to-end `run`
exposed it; every direct-call probe hand-built the maps and so never reached it.** Step 4 below is
that run, and it is not optional.

- [ ] **Step 1: write the failing tests.** In `tests/test_cli.py`:

```python
def test_one_run_records_both_pairings_and_the_method_that_goes_with_each():
    """Task 17a's `run`-through half, and the pin that replaces
    `test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch`'s
    source-text counts with the behaviour they stood in for. **Both answers in one
    run**: a declared cross-arm contrast records `paired: false` beside a `welch_*`
    or `unpaired_*` `method`, and a within-arm comparison in the same run still
    records `true`.

    One run rather than two, because the claim is that the derivation answers PER
    COMPARISON. Two runs would pin two configs and say nothing about a `groups ×
    grid` design, which is the design § Allocation walks through twice and the only
    one this slice makes analyzable end to end.

    This is the first end-to-end `run` of an unpaired contrast in this repository."""
    ...built in Step 4, from `run_a_project` with the roster and sweep named there...


def test_a_clustered_cross_arm_contrast_runs_and_records_a_cluster_robust_interval():
    """Task 17b's run-side half. The converted pin's fixture is a CLUSTERED cross-arm
    contrast, which is what forced `welch_t_over_units_clustered` and
    `unpaired_percentile_over_units_clustered` into this slice — so the conversion is
    honest only once the entry's `method` carries the `_clustered` suffix through a
    real run.

    The two per-side cluster counts are asserted beside it, because they are integers
    that cannot coincide on this roster and a `method` string alone does not say the
    draw happened."""
    ...built in Step 4...


def test_a_derived_metrics_unpaired_contrast_publishes_nothing_through_a_real_run():
    """Decision 8, and it is verified by `run` rather than by direct call for a
    measured reason: on H4b-2 the neighbouring corner survived four task batches and
    two direct-call pins because every probe hand-built `derived_by_key` and
    `resample_fns_by_key`, and only an end-to-end run reached the state the code
    branches on. **That corner was given four wrong grounds in four commits.**

    A derived metric's unpaired contrast has nothing to compute — no per-side derived
    draw exists among the constructions this slice builds — so `delta`, `method` and
    `ci95` are all `null` with the two side counts beside them, the shape
    `E-DATA-CLUSTER-DERIVED` already uses and § Contrasts licenses.

    **The two counts are the presences that must report.** A test asserting only the
    three nulls passes identically if the whole entry were missing, and `is None` is
    the weakest possible discriminator on this slice — a suppressed contrast, a thin
    side and a degenerate draw all produce it."""
    ...built in Step 4...
```

      In `tests/test_cli.py`, an `is_paired`-versus-`base_keys` discriminator that a `run` can reach:

```python
def test_the_derived_suppression_reads_the_pairing_answer_not_an_empty_intersection():
    """The guard's ground, and the assertion that separates it from its proxy. An
    empty `base_keys` is ALSO empty when two genuinely PAIRED conditions share no
    completed units — a defect to report, not a design to honour — so a guard keyed
    on the intersection's size would suppress both and say nothing about either.

    Two comparisons, one of each kind, through one direct call each: the unpaired one
    is suppressed and records `n_of`/`n_against`, and the paired-but-disjoint one is
    NOT suppressed and records `n_paired: 0` beside its own nulls — which is
    `test_a_derived_contrast_over_an_empty_stratum_reports_no_delta`'s documented
    shape, and the live proof that `0` means pairing FAILED.

    This is the test a `not base_keys` guard cannot pass, and no other test in this
    slice discriminates the two."""
    unpaired, _ = _unpaired_contrast_call(
        derived_by_key={(1, "s"): {"m": 20.0}, (0, "s"): {"m": 10.0}},
        resample_fns_by_key={
            (1, "s"): {"m": lambda table: 20.0},
            (0, "s"): {"m": lambda table: 10.0},
        },
    )
    entry = unpaired["s"]["m"]
    assert entry["paired"] is False
    assert entry["n_of"] == 5 and entry["n_against"] == 25
    assert "n_paired" not in entry
    # The paired-but-disjoint control: same empty intersection, opposite answer.
    paired_disjoint, _ = _unpaired_contrast_call(
        conditions_by_index={
            0: Condition(index=0, label="m=pearson", values={"analysis.method": "pearson"}),
            1: Condition(index=1, label="m=spearman", values={"analysis.method": "spearman"}),
        },
        derived_by_key={(1, "s"): {"m": 20.0}, (0, "s"): {"m": 10.0}},
        resample_fns_by_key={
            (1, "s"): {"m": lambda table: 20.0},
            (0, "s"): {"m": lambda table: 10.0},
        },
    )
    control = paired_disjoint["s"]["m"]
    assert control["paired"] is True
    assert control["n_paired"] == 0
    assert control["delta"] is None
```

      **The paired-but-disjoint control needs `Condition` imported in the test body** and
      `_unpaired_contrast_call` to accept a `conditions_by_index` override — it already does, since
      `kwargs.update(extra)` overrides. **Confirm by reading the helper** rather than assuming.

      **`test_a_derived_contrast_over_an_empty_stratum_reports_no_delta` must survive unchanged.** It
      asserts `n_paired == 0` beside a null delta for a *paired* contrast whose stratum matched
      nobody, and it is the live proof that `0` already means **pairing failed** — which is the whole
      reason an unpaired contrast may not spend it. **Do not edit it.** Verify it is green after this
      commit and record that in the task report.

- [ ] **Step 2: implement task 15's guard.** In `_comparison_step_blocks`' derived branch, replace the
      guard and rewrite its comment so **both grounds are stated in one place**:

```python
                # **Two independent suppression conditions, stated as ONE guard
                # naming both grounds.** Neither covers the other, and taking one as
                # covering the other is a wrong ground this corner has already been
                # given more than once.
                #
                # A DECLARED CLUSTER: no clustered draw exists for a recomputed
                # metric (`E-DATA-CLUSTER-DERIVED`). A derived key colliding with a
                # recorded column's name leaves `derived_by_key` AND
                # `resample_fns_by_key` populated for it — `command_run` builds a
                # closure for every key in `derived` before the raising call, and the
                # `except ContractError` retry that follows the collision clears
                # neither — so the two computes above are real callables and this
                # branch would otherwise draw an UNCLUSTERED interval for a metric
                # whose per-condition sibling is cluster-robust.
                #
                # AN UNPAIRED COMPARISON: no per-side derived draw exists either.
                # `unpaired_percentile_of_sides` serves a recorded column's own
                # closure; a recomputed metric would need `aggregate` evaluated on
                # each side's independently drawn table, which is a construction this
                # build does not have. Reached, this branch would compute
                # `paired_delta_of_derived` over an intersection that is empty by
                # construction and publish whatever `paired_percentile_of_derived`
                # returned over it.
                #
                # **The unpaired ground reads `is_paired`, never `not base_keys`.**
                # An empty intersection is a PROXY: it is also empty when two
                # genuinely paired conditions share no completed units, which is a
                # defect to report rather than a design to honour —
                # `test_a_derived_contrast_over_an_empty_stratum_reports_no_delta` is
                # that case, and it records `n_paired: 0` for exactly that reason.
                # `clusters` is likewise the roster-wide declaration and not
                # `col_clusters`, which this branch never builds.
                if (
                    compute_of is not None
                    and compute_against is not None
                    and clusters is None
                    and is_paired
                ):
```

- [ ] **Step 3: retire `E-DATA-ALLOCATION-CONTRAST`.** In `validate._check_sweep`, delete the
      `c.error("E-DATA-ALLOCATION-CONTRAST", ...)` call and its 40-line comment block. **Keep the
      loop, `crossed_group_axes`, `plural` and the `E-DATA-WEIGHT-ALLOCATION-CONTRAST` guard task 9
      put inside it** — the loop is now that guard's, and its remaining comment must say so rather
      than reading as a leftover. Then in `docs/reference.md`:

      - Delete § Validation's *Allocation deltas aren't computed* row.
      - Delete § Errors' `E-DATA-ALLOCATION-CONTRAST` row — the one ending
        `` | `E-DATA-ALLOCATION-CONTRAST` | ``.
      - **Check every row both deletions moved**, and every count phrase near them. A positional
        locator in this repo has been wrong twice, once falsified by exactly this kind of edit.

      **§ The one config file's declaration count does not move**: retiring a *combination* refusal is
      not retiring a declaration, and `_check_sweep`'s own comment makes that placement argument.

- [ ] **Step 4: build the three run-through tests, and read the record before writing the
      assertions.** All three need a roster with two arms, `assign: by_attribute`, `allocation:
      between`, a `sweep.groups` axis and a declared `statistics.contrasts` entry — plus, for the
      second, a `cluster_by` whose **per-arm cluster counts differ**.

      **Do not reuse `tests/test_validate.py`'s `_groups_cluster_csv` for the clustered run.**
      Measured at `e40a219`: its sites are A(c0,c1,t0) B(c2,c3,t1,t2) C(c4,c5,c6) D(t3,t4), so the
      `control` arm touches A, B, C and `treatment` touches A, B, D — **three clusters each.** Equal
      per-side counts are the documented *"a cluster fixture where correct and buggy cluster counts
      were both 3"* failure, and a side-swapping construction would be invisible. **Build this task's
      own roster through `run_a_project(roster_csv=..., unit_attributes=[...])`**, with per-arm
      cluster counts of **3 and 4** — and assert both integers. Leave
      `_groups_cluster_csv` untouched: its own tests assert a documented arm/site crossing.

      For the third test, use `aggregate_returns=` so the template derives a metric, exactly as task
      21's boundary test does — that is the route to a derived contrast through a real run, and
      task 21's Step 1 records that the combination was verified at `e40a219`.

      **Read the produced `run.yaml` before writing the expected values.** Every number in these three
      tests is captured from the first green run and pasted in, in this same commit. **Assert, in
      every one of them, a positive literal or an integer count** — `is not None` is a uselessly weak
      discriminator here.

      For the first test specifically, the sweep must be `groups × grid` so one run holds both kinds:

```python
        sweep={
            "groups": [{"by": "arm", "levels": ["control", "treatment"]}],
            "grid": {"analysis.method": ["pearson", "spearman"]},
        },
        statistics={
            "contrasts": [
                {"id": "across_arms", "of": "arm=treatment__method=pearson",
                 "against": "arm=control__method=pearson"},
                {"id": "within_control", "of": "arm=control__method=spearman",
                 "against": "arm=control__method=pearson"},
            ]
        },
```

      and the assertions read `run["results"]["contrasts"]` by `id`:

```python
    across = next(c for c in run["results"]["contrasts"] if c["id"] == "across_arms")
    within = next(c for c in run["results"]["contrasts"] if c["id"] == "within_control")
    across_entry = next(iter(next(iter(...the step block...)).values()))
    assert across_entry["paired"] is False
    assert across_entry["method"].startswith(("welch_", "unpaired_"))
    assert "n_paired" not in across_entry
    assert across_entry["n_of"] > 0 and across_entry["n_against"] > 0
    within_entry = ...
    assert within_entry["paired"] is True
    assert within_entry["method"].startswith("paired_")
    assert within_entry["n_paired"] > 0
```

      **`.startswith(("welch_", "unpaired_"))` rather than an equality is deliberate here and only
      here**: this test's claim is the *pairing derivation*, and the exact `method` is pinned by task
      14's four-cell table and by the clustered run beside it. **Every other assertion in this commit
      is an equality or an integer.**

- [ ] **Step 5: convert the existing assertions — enumerated by reading, then confirmed by grep.**
      These were located by reading `tests/test_validate.py` and `tests/test_cli.py` at `e40a219` and
      confirmed with `grep -rn 'E-DATA-ALLOCATION-CONTRAST' tests/`. **Re-run that grep first and
      reconcile against this list**; a name that has moved is expected, a site this list does not
      carry is a finding.

      | Test or site | What this commit does to it |
      |---|---|
      | `test_a_contrast_beside_groups_and_cluster_by_draws_the_allocation_refusal` | **Task 17b's conversion.** Rename to `test_a_contrast_beside_groups_and_cluster_by_now_validates_clean`, keep its position, assert `_error_codes(...) == set()`, and record in its docstring what it replaced and why the exact set stays exact |
      | `test_a_generated_cross_arm_comparison_is_refused_and_the_within_arm_one_is_not` | Its filtered `[f for f in c.findings if f.code == "E-DATA-ALLOCATION-CONTRAST"]` can no longer report. **Convert to the composition control it becomes**: the same config validates clean, asserted as an exact empty set — and rename it, since "is refused" is now false |
      | `test_a_declared_contrast_across_arms_is_refused` | The same, by the same route, and the same rename obligation |
      | `test_a_baseline_may_not_fix_a_group_level` | Remove `"E-DATA-ALLOCATION-CONTRAST"` from its expected sets — **three entries at `e40a219`, and the count is not to be carried**: read the test and remove every one. Its docstring's *"At two or more levels `E-DATA-ALLOCATION-CONTRAST` fires beside…"* is a claim about the old behaviour: **delete it rather than rewrite it** |
      | `test_a_baseline_may_not_fix_a_group_level_while_ablate_is_declared` | The same, one expected-set entry and one docstring claim |
      | `test_the_one_level_control_arm_baseline_reports_where_it_once_validated_clean` | Its docstring's *"at two or more levels `E-DATA-ALLOCATION-CONTRAST` masks it"* — the masking is gone. **Delete the clause**; the test's own subject is `E-SWEEP-BASELINE-GROUP` and is unaffected |
      | `test_a_group_axis_with_no_comparison_is_untouched` | Its docstring's *"a change that adds `E-DATA-ALLOCATION-CONTRAST` to it"* names a code that no longer exists. Rewrite the clause to name the guard's current subject, `E-DATA-WEIGHT-ALLOCATION-CONTRAST` — this is the one site where a **rewrite** rather than a deletion is right, because the sentence's job is to say what a regression here would look like and there is still a code that would |
      | The two `tests/test_validate.py` section comments naming the code | Read both, and repair each by naming what its section now covers. One introduces the group-axis refusal family and one the baseline-group interaction |
      | `tests/test_cli.py::test_the_allocation_refusal_row_states_its_own_reading` | Its `_row("E-DATA-ALLOCATION-CONTRAST")` raises `StopIteration` once the row is deleted. **Convert it to the same check over `E-DATA-WEIGHT-ALLOCATION-CONTRAST`'s row**, which task 9 wrote with a `per comparison` clause for exactly this reason, and rename accordingly |
      | The `tests/test_cli.py` comment reading *"either would draw `E-DATA-ALLOCATION-CONTRAST` instead of validating"* | Read the test it belongs to and repair the claim. If the config it describes now validates, say that instead — the comment exists to explain a fixture choice, and the choice may no longer need explaining |

- [ ] **Step 6: run the gates.** `uv run pytest` → **2264 + 4 = 2268 passed**, 1 skipped, 2 xfailed —
      **and check that arithmetic against the actual output**, since several tests are renamed rather
      than added and one may be merged. If the number differs, find out which test moved before
      committing. Then `uv run ruff check .`, `uv run ruff format --check .` (80 files),
      `uv run mypy`. Run the mechanical pass over `docs/reference.md`.

      **The `validate`-clean half, asserted as an exact set:** the clustered cross-arm design now
      reports `{}`. **The `run`-through half:** three real runs. **And the negative control that must
      still refuse:** the weighted cross-arm design still reports
      `{"E-DATA-WEIGHT-ALLOCATION-CONTRAST"}` as an exact set of one — task 9's test asserted it
      alongside the retiring code, so **flip that assertion to the exact set here**, which is the flip
      task 9's brief promised this task would own.

- [ ] **Step 7: mutate — four mutations.**

      **Mutation 1 — the guard's unpaired ground removed.** Delete `and is_paired` from the derived
      branch's guard. `test_a_derived_metrics_unpaired_contrast_publishes_nothing_through_a_real_run`
      must **FAIL** — a `delta` and a `method` appear where three nulls belong. **This is the mutation
      that says the guard is a guard**, and it must be run against the **`run`-through** test rather
      than only the direct-call one, because that is where the maps are real.

      **Mutation 2 — the guard's ground replaced by its proxy.** Change `and is_paired` to
      `and bool(base_keys)`. `test_the_derived_suppression_reads_the_pairing_answer_not_an_empty_intersection`
      must **FAIL** on its paired-but-disjoint control, which is now suppressed and loses its
      `n_paired: 0`. **Checked against the test body:** both comparisons have an empty `base_keys`, and
      only `is_paired` distinguishes them — which is the whole reason that control is in the test, and
      the reason no other test in this slice can catch this mutation.

      **Mutation 3 — the refusal restored.** Re-add the `c.error("E-DATA-ALLOCATION-CONTRAST", ...)`
      call. The converted clean-composition tests must **FAIL** on their exact empty sets, and the
      three run-through tests must **FAIL** with `EXIT_WRONG`. **That is the retirement's own pin**:
      it says the deletion is what made the runs possible rather than something else having changed.

      **Mutation 4 — the clustered construction not reached through the record.** In
      `_comparison_step_blocks`' unpaired arm, change the clustered *t* call's `against_clusters`
      lookup to `of_clusters`. `test_a_clustered_cross_arm_contrast_runs_and_records_a_cluster_robust_interval`
      must **FAIL** — and record whether it fails on `n_clusters_against` or by raising from
      `_cr1_variance`'s `strict=True` zip. **Both are attributable and they say different things**: a
      wrong integer means the count path is separate from the construction path, and a raise means the
      per-side signature caught it.

      Run each against the **full, unfiltered** suite in the foreground; revert by editing back.

- [ ] **Step 8: Commit.** One commit for tasks 15, 17b and 18.

```bash
git add src/publishable/cli.py src/publishable/validate.py docs/reference.md \
        tests/test_cli.py tests/test_validate.py
git commit -m "feat: E-DATA-ALLOCATION-CONTRAST retired, the derived unpaired path guarded on two named grounds, and an unpaired contrast run end to end"
```

---

## Task 19: the surviving-citation sweep

**Runs after task 18.** Every site the retirement does **not** delete, repaired **by claim** over a
named file list. **This task must not touch the development record** — `H4c-SCOPING.md`, both H4b
specs, the H4b ledgers and this slice's own spec are evidence, not text to repair. `spec-defects.md`
is task 20's.

**Files:**
- Modify: `src/publishable/validate.py`
- Modify: `src/publishable/cli.py`
- Modify: `docs/reference.md`
- Modify: `docs/experimental-designs.md`
- Modify: `docs/feasibility-llm-growth-studies.md`
- Test: `tests/test_validate.py`, `tests/test_cli.py` (assertions on the repaired strings)

**Interfaces:**
- Consumes: task 18's deletions; task 9's `E-DATA-WEIGHT-ALLOCATION-CONTRAST`, which is what several
  of these sentences are repaired **to** rather than merely away from.
- Produces: no surviving claim that core refuses a cross-arm delta.

**The enumeration, read at `e40a219` and confirmed by grep.** Run the sweep first and reconcile:

```bash
grep -rn 'E-DATA-ALLOCATION-CONTRAST' src/ docs/reference.md docs/experimental-designs.md \
  docs/design-principles.md README.md docs/feasibility-llm-growth-studies.md tests/
grep -rn 'unpaired estimator\|unpaired construction\|no unpaired\|until the unpaired' \
  src/ docs/reference.md docs/experimental-designs.md docs/design-principles.md README.md
# the can-fail control: the same sweep shape over a string that IS present
grep -rc 'E-DATA-WEIGHT-ALLOCATION-CONTRAST' src/publishable/validate.py docs/reference.md
```

**`docs/superpowers/` is excluded from the FILE LIST, never from the output.** A reviewer checking
this exact rule once lost a true hit to `grep -v superpowers`, because the matching line contained
that path.

**And read for the CLAIM, not for the wording.** The second sweep above is the claim sweep, and it
exists because on H4b-2 a deleted claim returned as a paraphrase no literal search matched.

| Site | The repair |
|---|---|
| `validate._check_assign`'s docstring | Cites the retired code as the precedent for refusing a combination while honouring both declarations. **The precedent survives under a new name**: `E-DATA-WEIGHT-ALLOCATION-CONTRAST` is that shape, minted in this slice. Re-point the citation |
| `validate._check_unimplemented`'s comment | Cites `_check_sweep` as the owner of the cross-arm contrast refusal. There is no cross-arm contrast refusal. **Delete the clause**; the comment's subject is which function owns which refusal, and `_check_sweep` still owns one |
| `validate`'s `E-SWEEP-BASELINE-GROUP` guard comment **and its emitted message** | Both promise the delta *"until the unpaired estimators exist"* — **a temporary clause inside a permanent refusal**, and the one repair in this table that is a re-wording rather than a deletion. The refusal rests on the **peers** rule (§ Expansion modes, *the arms of a group axis are peers*), and the sentence must say that a designated arm's comparison is a `statistics.contrasts` entry **which core now computes** — the baseline is still refused, and for a reason that was never about the estimators |
| `cli._comparison_step_blocks`' docstring | Tasks 13, 14 and 16 each repaired the paragraph they falsified. **Re-read the whole docstring here as the last reader**, and confirm no clause still claims a cross-arm comparison cannot reach the function, that `paired` is hard-coded, or that `n_paired` is unconditional. **Report what you found rather than asserting it was clean** |
| `reference.md` § Expansion modes' control-arm paragraph | *"**This build refuses to compute that delta** (`E-DATA-ALLOCATION-CONTRAST`, temporary …): the two sides hold disjoint units, and no unpaired construction exists yet. Until it does, the arm-versus-arm difference is an `Estimate` …"* — **the whole claim is now false.** Replace it with the positive statement: a `statistics.contrasts` entry naming both arms is computed, unpaired, by the Welch or per-side percentile construction, and the `Estimate` route remains available for anything core does not compute (an interaction, a conditional estimator) |
| `reference.md` § Errors' `E-SWEEP-BASELINE-GROUP` row | Carries the same *"whose delta this build refuses for the same disjoint-units reason"* clause. Same repair, and **check the row's column count and every row the edit moves** |
| `experimental-designs.md` § Mistakes core prevents | *"And a contrast that crosses arms is refused outright rather than reported paired over an empty intersection (`E-DATA-ALLOCATION-CONTRAST`)"*, inside a sentence that also enumerates which codes read the within-versus-arms question. **Delete the crossed-arms clause and remove the code from the enumeration** — this is § Mistakes core prevents, whose entries must be *structurally impossible*, and a computed unpaired contrast is not a mistake at all. **Re-read the whole entry afterwards**: it is one long sentence with several enumerations, and a deletion inside it can leave a dangling conjunction or a count phrase that no longer holds |
| `reference.md` § Allocation's pairing table and the paragraph task 3 repaired | **Read, do not assume.** Task 3 repaired the example and two sentences; confirm no third sentence in that section still says the unpaired delta is refused |
| `docs/feasibility-llm-growth-studies.md` | **Re-dated, never edited.** Task 20 owns the new dated section; this task confirms that no *undated* prose there claims the refusal is live, and repairs only such prose if it exists. The dated sections are measurements on their dates and must not be retro-edited |

- [ ] **Step 1: run both sweeps and the control**, and record every hit with its file and its claim in
      the task report. **Filter the file list, never the output.**

- [ ] **Step 2: repair each site**, in the order of the table. For each, **re-read the whole docstring,
      comment or paragraph** — not the matched line. Ten Majors across H4b-1's four review batches were
      stale quantifiers or claims left standing over changed material.

- [ ] **Step 3: pin the two repairs that are re-wordings rather than deletions**, since a rewrite can
      re-seed. In `tests/test_validate.py`:

```python
def test_the_baseline_group_refusal_rests_on_the_peers_rule_alone():
    """`E-SWEEP-BASELINE-GROUP` is PERMANENT and its message promised the cross-arm
    delta "until the unpaired estimators exist" — a temporary clause inside a
    permanent refusal, and one that is now simply false. The refusal rests on the
    peers rule: the arms of a group axis are peers and a baseline designating one of
    them is not a reference the expansion can give.

    Asserted on the surviving text plus the absence of the temporary clause, so a
    rewrite cannot re-seed it as a paraphrase. The control is the peers claim, which
    must be present."""
    ...the fixture from `test_a_baseline_may_not_fix_a_group_level`...
    message = messages_by_code(path)["E-SWEEP-BASELINE-GROUP"]
    assert "peers" in message  # the control
    assert "unpaired" not in message
    assert "until" not in message
```

      and in `tests/test_cli.py` a § Expansion modes text assertion using the module's existing
      `_section_text` helper — **read it before using it**:

```python
def test_expansion_modes_says_a_cross_arm_contrast_is_computed():
    """§ Expansion modes' control-arm paragraph claimed core refuses the arm-versus-arm
    delta. It computes it. Asserted on the section text with a control, because this
    is the sentence a reader deciding whether to express a control arm as a contrast
    actually reads."""
    section = _section_text("### Expansion modes")
    assert "statistics.contrasts" in section  # the control
    assert "no unpaired construction exists" not in section
    assert "E-DATA-ALLOCATION-CONTRAST" not in section
```

- [ ] **Step 4: run the gates and both passes.** `uv run pytest` → **2268 + 2 = 2270 passed**, 1
      skipped, 2 xfailed. Then `uv run ruff check .`, `uv run ruff format --check .` (80 files),
      `uv run mypy`. Then the **mechanical** pass over `docs/reference.md` and
      `docs/experimental-designs.md`, and the **cross-document** pass over all four documents —
      § Mistakes core prevents is one of its named classes, and this task edits it.

- [ ] **Step 5: mutate.** **Re-add the deleted clause to `E-SWEEP-BASELINE-GROUP`'s emitted message**
      and confirm `test_the_baseline_group_refusal_rests_on_the_peers_rule_alone` **FAILS**; then the
      same for § Expansion modes and its test. **A mutation on a comment or a document is prescribed
      deliberately here**: these two repairs are re-wordings, a rewrite invents, and this repo has
      re-seeded a deleted claim three times.

      **There is no mutation for the deletion-only sites**, and that is stated rather than left as a
      gap: a deleted comment has no behaviour to break, and the sweep in Step 1 is what says the
      deletion happened. Task 22's re-read is the second check.

- [ ] **Step 6: Commit.**

```bash
git add src/publishable/validate.py src/publishable/cli.py docs/reference.md \
        docs/experimental-designs.md tests/test_validate.py tests/test_cli.py
git commit -m "docs: every surviving claim that core refuses a cross-arm delta, repaired by claim"
```

---

## Task 20: the five inherited filings, each claimed or re-declined in writing

**Runs after task 18.** **A silent inherit is how an entry comes to read as live work nobody holds**,
and a ledger line saying "filed" is not a filing.

**Files:**
- Modify: `docs/superpowers/spec-defects.md`
- Modify: `src/publishable/stats.py` (the one filing this claims)
- Modify: `docs/feasibility-llm-growth-studies.md`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `spec-defects.md`'s five entries naming H4c — located by
  `grep -n 'H4c' docs/superpowers/spec-defects.md`, which returned hits in the sorted-pool entry, the
  column-resample finiteness entry, the contrast-disclosure entry, the `W-STATS-REPORTBY-THIN` entry
  and the `E-DATA-CLUSTER-DERIVED` entry at `e40a219`; `stats.interval_at(pool, confidence)`, whose
  docstring already states *"`pool` must already be sorted ascending — `interval_at` reads fixed ranks
  off it and does not sort"*.
- Produces: five written rulings, one assertion, and one dated re-measurement.

| Filing | Ruling |
|---|---|
| `paired_percentile_of_derived`'s sorted-pool precondition unasserted | **CLAIM IT.** `interval_at` reads fixed ranks off an unsorted pool silently, and task 6 added a **new** percentile construction returning a pool — which is the entry's own original condition, restored by H4b-2. The cost is one assertion at a seam this slice opened anyway. **Strike the entry** |
| *A column resample is only ever defined given finite inputs* | **VERIFY THE PREMISE, DO NOT INHERIT IT.** The identical prediction was made of H4b-2 and **did not come true**, which the entry itself records. H4c's unpaired *t* forms **do** sum per-side value columns and compute per-side variances, so the premise is likelier here — **but likelier is not measured.** Check, then claim or re-decline **with the measurement** |
| *The contrast path discloses nothing about its resample* — Findings 1 and 3 | **CLAIM Finding 3; re-decline Finding 1 with a named owner.** H4b-2 declined both on a "no new disclosure surface" ground that **does not transfer**: H4c adds four `method` spellings and a new record shape. Finding 3 — a resolved-`resample` echo on the contrast entry — is the same record this slice re-authored. Finding 1 needs a contrast-scope `where` and a warning-registry row, which is warning-registry work; **owner: H4d** |
| `W-STATS-REPORTBY-THIN`'s whole-roster-versus-arm gap, and `report_by`'s `resample_columns` asymmetry | **RE-DECLINE, and name a slice.** Live on C1–C3, created by neither weights, clusters nor pairing, and **the only one of the five genuinely unrelated to unpaired constructions.** Declined by three consecutive slices, so a fourth decline needs an owner that is not a description: **H4d**, the last remaining slice whose surface is the `statistics` block. **H4d is terminal for it** — after H4d there is no statistics slice, so a fifth decline must convert it into a documented limitation with a permanent § Errors or § Validation row, not pass it on again. **Write that terminality into the entry** |
| `E-DATA-CLUSTER-DERIVED` — the clustered derived draw | **RE-DECLINE, on a new ground, owner H4d.** The old ground was cost and reachability and H4b-2 used it up. The new ground is decision 8: H4c is the slice that gave the derived branch a **second** suppression condition, and building the clustered derived draw inside it would require that same guard to distinguish three states rather than two — compounding, in one commit, the exact corner that has already been given four wrong grounds in four commits. Building it after the guard is stable is strictly safer than building it while the guard is being written |

- [ ] **Step 1: claim the sorted-pool filing.** In `stats.interval_at`, add the assertion its own
      docstring already promises:

```python
    assert list(pool) == sorted(pool), (
        "interval_at reads fixed ranks off a sorted pool and does not sort; an "
        "unsorted pool gives two arbitrary positions"
    )
```

      placed **before** the `min_honest_draws` floor, so a too-short unsorted pool is still caught.
      **`assert` rather than a raise**, because every caller is core: this is `cli`'s and
      `correction.py`'s bookkeeping, the same standing `Member.__post_init__`'s `ValueError` has.

      And the test, in `tests/test_stats.py`:

```python
def test_interval_at_refuses_an_unsorted_pool_rather_than_reading_two_positions():
    """The filing H4b-2 restored and H4c claims. `interval_at` reads fixed ranks off
    a pool, so an unsorted one returns two arbitrary values that look exactly like an
    interval — and this slice added a construction returning a pool, which is the
    seam that made the precondition worth asserting rather than documenting.

    The sorted control must report, because an assertion that fires on every input
    would pass the negative case too."""
    ordered = [float(i) for i in range(400)]
    assert interval_at(ordered, 0.95) is not None  # the control
    with pytest.raises(AssertionError, match="sorted"):
        interval_at(list(reversed(ordered)), 0.95)
```

      **Run the full suite immediately after adding the assertion.** If any existing caller hands
      `interval_at` an unsorted pool, that is a **live defect this filing was about** — do not weaken
      the assertion. Record what you find; every path this plan touched sorts.

- [ ] **Step 2: measure the finiteness premise rather than inheriting it.** The claim is that a column
      resample is only ever defined given finite inputs. Probe it:

```bash
uv run python - <<'PY'
import math
from publishable.stats import welch_t_over_units, welch_t_over_units_clustered, cohens_ds
inf = float("inf")
nan = float("nan")
for name, fn, args in [
    ("welch inf", welch_t_over_units, ([1.0, inf, 3.0], [1.0, 2.0, 3.0])),
    ("welch nan", welch_t_over_units, ([1.0, nan, 3.0], [1.0, 2.0, 3.0])),
    ("ds inf", cohens_ds, ([1.0, inf, 3.0], [1.0, 2.0, 3.0])),
]:
    try:
        print(name, fn(*args))
    except Exception as exc:
        print(name, type(exc).__name__, exc)
PY
```

      **Then decide in writing.** If a non-finite column produces a plausible interval rather than
      `None` or a raise, the premise is **falsified** and the entry is claimed or re-owned with the
      measurement beside it. If every path answers `None`/`nan` in a way a reader can see, re-decline
      **with the measurement**, and name the owner. **Either way the entry carries the probe's output
      and its date** — an undated build claim reads as a spec claim a month later.

- [ ] **Step 3: write the five rulings into `spec-defects.md`.** For each: what was ruled, on what
      ground, and who owns what remains. **A closed gap is STRUCK, not deleted** — that is this file's
      one exception to the no-retro-edit rule, and the strike is what stops a closed gap from
      misleading. **A re-declined entry names a slice, never a description**: *"whichever slice does
      X"* points at a closed slice once X lands.

      **Re-read each entry before editing it.** *"A filing's claims about the code go stale like any
      other comment; when you change code a `spec-defects.md` entry describes, re-read the entry"* —
      and this slice changed `_corrected_bounds`, `_comparison_step_blocks`, `interval_at` and both
      percentile constructions, which four of the five entries describe.

- [ ] **Step 4: re-date `docs/feasibility-llm-growth-studies.md`.** Add one section on the shape
      § Executability on this build already uses — **"### Measured on 2026-08-18 against commit
      `<sha>` — after H4c"** — carrying:

      - **The counts, unmoved: six with no remaining core-side blocker, three executable.** Neither
        number changes, and the section must say so in those words rather than omitting them.
      - **The measurement, with a control that can fail**: no config declares a `sweep.groups` axis —
        `grep -c 'allocation: within'` → 3 (two config blocks plus one prose sentence),
        `grep -c 'allocation: between'` → 1, **read** and found to be a prose sentence listing fields
        no config declares, `grep -n 'groups:'` → two hits, both `groups: []`. **Re-run each and paste
        the actual numbers**, since the file has been edited since those figures were taken.
      - **The refusal row**: `E-DATA-ALLOCATION-CONTRAST` retired,
        `E-DATA-WEIGHT-ALLOCATION-CONTRAST` minted, **net zero**, and **no config hits either**.
      - **The sentence that must not be roundable**: *a retired-refusal count is not an
        executable-run count.* Both review verdicts on H4b-1 faulted that conflation, and a
        *correction* on H4b-2 inverted the same two numbers and named a **retired** refusal as live.

      **Do not edit any earlier dated section.** They are measurements on their dates.

- [ ] **Step 5: run the gates.** `uv run pytest` → **2270 + 1 = 2271 passed**, 1 skipped, 2 xfailed.
      Then the other three. Run the **mechanical** pass over `docs/feasibility-llm-growth-studies.md`
      — it is exempt from the cross-document pass and subject to the mechanical one in full,
      including `×` for multiplication and hyphens in anchors.

- [ ] **Step 6: mutate.** **Mutation — the assertion removed.** Delete `interval_at`'s `assert`.
      `test_interval_at_refuses_an_unsorted_pool_rather_than_reading_two_positions` must **FAIL** by
      not raising. **Check the two branches can differ before believing it:** a reversed 400-element
      pool is genuinely unsorted and `interval_at` would otherwise return `(pool[lo], pool[hi])` = two
      descending values, so the un-asserted branch returns a value rather than raising. It does
      discriminate.

      **Note for the report:** running Python with `-O` disables `assert`, so this claim is scoped to
      a normal interpreter. **Say so** rather than claiming the precondition is enforced
      unconditionally — that is the kind of over-claim this repo has shipped a dozen times in
      docstrings.

- [ ] **Step 7: Commit.**

```bash
git add docs/superpowers/spec-defects.md docs/feasibility-llm-growth-studies.md \
        src/publishable/stats.py tests/test_stats.py
git commit -m "docs: H4c's five inherited filings ruled, the sorted-pool precondition claimed, and the counts re-measured unmoved"
```

      **`docs/superpowers/` is gitignore-clobbered by `scripts/sdd-workspace`, which `task-brief`
      calls.** If `git add` reports the path as ignored, restore `.superpowers/sdd/.gitignore`'s
      content and use `git add -f`.

---

## Task 22: the whole-branch review, and both consistency passes

**Runs last, over the whole branch rather than task by task.** **H4b-2's whole-branch review found a
Critical no per-task review could** — a derived key colliding with a recorded column's name publishing
an *unclustered* contrast interval with `validate` reporting zero errors, reachable only through an
end-to-end `run` because every direct-call probe hand-built the maps. **This task exists because that
class of finding is invisible from inside one task.**

**Files:** whatever the review finds. No new behaviour is planned.

- [ ] **Step 1: the four gates, from a clean tree.** `uv run pytest` → the count task 20 left, 1
      skipped, 2 xfailed, **in the FOREGROUND**. `uv run ruff check .`,
      `uv run ruff format --check .` (80 files), `uv run mypy` (45 source files).

- [ ] **Step 2: the df-clause tripwire — a RE-READ, not a grep.** Task 1 added a df-provenance clause
      to § Statistical reporting **scoped to the *t* forms alone**, and this is its tripwire: **batch 1
      of H4b-2 deleted a df-provenance clause from this exact region as false of the percentile form,
      and batch 3 re-seeded it at three more sites — one of them a paraphrase no literal grep could
      find.** So **read**, in full: `unpaired_percentile_of_sides`' docstring, `_draw_pools`'
      docstring, `paired_percentile_of_derived`'s docstring, `_side_content`'s and
      `_drawable_content`'s, and § Statistical reporting's percentile rows and paragraphs. Confirm
      none of them claims a df, a degrees-of-freedom provenance, or a cluster-count-based interval
      width. **Report what you read, not that a grep was clean.**

- [ ] **Step 3: the whole-branch behavioural sweep — three corners no task owns alone.**

      **(a) An unpaired contrast whose derived key collides with a recorded column's name.** This is
      H4b-2's Critical one axis over, and task 15's guard is what should close it — but that guard was
      written and verified in the same commit as the retirement, which is exactly the arrangement that
      hid the last one. **Build it through a real `run`**: a template whose `aggregate` returns a key
      the step also records, beside a cross-arm contrast. Read the record and confirm the contrast
      over that key publishes three nulls and two counts, **and that the recorded column's own
      per-condition interval is untouched.**

      **(b) An unpaired contrast in the correction family beside a paired one.** `family_shape` counts
      comparisons × metrics and `rank_family` ranks on the point estimate over half the raw interval's
      width. A run holding both kinds ranks them together for the first time. **Confirm the ranking
      and every `ci95_corrected` by hand** at the family's own α, using the ratio method: a corrected
      half-width must equal the raw one times `t(df, 1 − level) / t(df, 0.95)` at the **entry's own
      df**. H4b-2's whole-branch review confirmed its own bound exactly this way.

      **(c) An unpaired contrast beside a `report_by` stratum and a `summary` `Estimate`.** Neither
      joins the correction family, and task 21 pins the `Estimate` boundary. **Confirm through a run
      that a `report_by` level's block grew no unpaired key** and that the family size did not move.

- [ ] **Step 4: the mechanical pass, over the four documents and the feasibility analysis.** Every
      relative link and `#anchor` resolves; no two headings in a file produce the same anchor; every
      table's rows match its header's column count and no row is empty; no line carries trailing
      whitespace, a tab, or invisible unicode; `×` not `x`; hyphens not en dashes in anything that
      becomes an anchor. **Skip fenced code blocks in all of them** — the docs contain markdown
      inside markdown, so a `##` or `|` there is content, not structure.

      Then sweep for what should no longer exist, **filtering the file list and never the output**,
      with a control that can fail:

```bash
grep -rn 'E-DATA-ALLOCATION-CONTRAST' src/ tests/ README.md docs/reference.md \
  docs/design-principles.md docs/experimental-designs.md
grep -rc 'E-DATA-WEIGHT-ALLOCATION-CONTRAST' src/publishable/validate.py docs/reference.md
```

      The first must return nothing; the second must return hits. **`docs/superpowers/` and
      `docs/feasibility-*.md`'s dated sections are excluded from the first by design** — the
      development record is evidence, and a dated measurement is a measurement.

- [ ] **Step 5: the cross-document pass, by its named classes.** **The shared worked example** —
      `cohort-pilot` declares no group axis; confirm no unpaired key or `method` reached README,
      `design-principles.md`, or `reference.md`'s worked example, and that no interval was narrowed
      back. **Config completeness** — no config field was added, so § The one config file is
      unchanged; confirm its *"One declaration above is not yet built"* still reads **one**.
      **Enum comments** — confirm no inline `# a | b | c` enumerates `method` strings. **Schema
      fields in prose** — the four new record keys are named in prose *and* appear in a fenced
      example. **Declared vs. derived** — `paired` is derived and no passage shows it as settable.
      **Versions** — unchanged. **Prevented mistakes** — `experimental-designs.md` § Mistakes core
      prevents no longer names a cross-arm contrast, and every remaining entry is still structurally
      impossible.

- [ ] **Step 6: the four-document `Status` invariants.** `tests/test_cli.py` asserts set equality
      between `reference.md`'s `NOT BUILT` command rows and `cli.NOT_BUILT_COMMANDS` — confirm green.
      Confirm `test_a_clustered_contrast_method_is_one_the_document_defines` is still green, which is
      the mechanical half of task 1's "no new rows for the clustered forms" ruling.

- [ ] **Step 7: write the review.** For every finding: what it is, what it was **verified by** (a run,
      a mutation, a probe with a positive control — **never a reading alone**), and its severity.
      **A finding whose evidence is a grep must say so**, and a grep is evidence about a spelling
      rather than about a behaviour.

- [ ] **Step 8: Commit** any fixes the review produced, each with its own message, and then the review
      record.

```bash
git add -A
git commit -m "review: H4c whole-branch — <what was found>"
```

---
## Plan self-review, run 2026-08-18 against `e40a219`

Three passes, run by this plan's author before committing it. Each records what it checked and what it
found, not that it was run.

### Spec coverage — every decision and every one of the spec's own 22 tasks

**The eight decisions.**

| Decision | Where it is carried |
|---|---|
| 1 — one slice at 22, build the plain and clustered unpaired pairs, refuse the weighted pair | Task 1 (ruled, with the free-identifier sweep and its control), task 9 (minted with both rows), tasks 4/6/7/8 (the four built). Batched dispatch rather than a cut: § Sequencing's execution order |
| 2 — `Member`'s third evidence *kind*, one field, exactly-one counted over three, both modifiers "never beside `sides`", `_corrected_bounds` to five *t* arms | Task 11 (the type, the field, the counted rule, both modifier checks), task 12 (five *t* arms plus the unchanged `pool` arm, counted; `correction.py` as the second production call site, written first) |
| 3 — four spellings, `reference.md` first, no new table rows, the df clause scoped to the *t* forms, no reuse of `paired_percentile_of_derived` | Task 1 (the ruling, the narrowing, the clause), task 6 (`unpaired_percentile_of_sides` as a new construction with the argument written into its docstring), task 8 (the second spelling through `method=`), task 22 Step 2 (the clause's re-read tripwire) |
| 4 — Welch-Satterthwaite over two cluster-robust per-side variances, each contributing `G_s` − 1 | Task 1 (the document clause), task 7 (the construction, with both rejected readings named and mutations 1–3 separating all three) |
| 5 — `n_paired` **absent**, `n_of`/`n_against` and `n_clusters_of`/`n_clusters_against` in its place, `n_paired_effective` with no counterpart | Task 2 (documented first, with the absent-not-null argument), task 10 (emitted conditionally, mutation 3 pinning the rejection of `n_paired: 0`), task 21 (`test_a_paired_contrast_entry_still_grows_no_unpaired_key` reading the obligation in the other direction) |
| 6 — `W-STATS-CONTRAST-THIN` and `limits.min_reported_n` per side, firing where **either** is below | Task 2 (§ Contrasts restated), task 16 (both emit sites, with an asymmetric fixture and two silent-reading mutations) |
| 7 — the retirement last, `paired` derived from ONE expression with two callers | Task 9 (the predicate minted, first caller), task 13 (second caller, three literals derived), task 18 (last among the code tasks, carrying the `validate`-clean and `run`-through halves) |
| 8 — suppress the derived unpaired case on a guard reading the pairing answer, two grounds in one guard, verified by `run` | Task 2 (documented), task 15 (the guard, in task 18's commit, with the proxy-discriminating control test and mutation 2), task 22 Step 3(a) (the whole-branch re-check) |

**The spec's own 22 numbered tasks map one-to-one onto this plan's 22**, deliberately keeping the
numbering so coverage is checkable by eye. Every spec task's content is present. Four additions and
one reassignment, all argued in § Four deviations: task 9 also mints the shared predicate (the spec
assigns it to no task); task 10 also owns the conditional record keys and the weight guard (the
scoping requires the first, and the second is mechanically forced); task 14 also wires `cohens_ds`
(the spec builds it in task 5 and wires it nowhere); task 21 executes fourth rather than last.

**Gaps this plan found in the spec and closed, listed rather than absorbed:**

1. **`cohens_ds` had no wiring task.** Closed in task 14, deviation (d).
2. **The `Member(...)` construction site in `cli` had no owner.** Closed in task 14, with the
   `corrected_from_pool` single-decision property extended to four fields.
3. **The `if weights is not None:` block's unpaired reachability had no owner.** Closed in task 10 by
   a `ValueError` mirroring the existing weight × cluster guard, which is also what makes `Member`'s
   "never beside `sides`" and `cli`'s bookkeeping one claim from two ends.
4. **`n_clusters_of`/`n_clusters_against`'s emit site had no owner.** Closed in task 10.
5. **`PairedResample`'s docstring reads "A **paired** percentile interval and the pool it was read
   from"** and task 6 reuses the type. **Ruled: reuse it and narrow the docstring by deleting the
   word `paired`** — task 6's Step 3 carries it. Renaming the type is a cross-cutting edit the spec
   never scoped, and reuse-plus-deletion is the lower-risk branch.
6. **The degenerate-draw rule across two independent draws was undefined.** Ruled in task 6: `None`
   only where **both** sides cannot vary, because one constant side still leaves the difference
   varying. A copied `all(...)` with an implicit "either" would null intervals that are fine, which is
   the reverse of the defect H4b-2 closed and just as invisible.
7. **`W-STATS-CONTRAST-THIN` has a second emit site at `validate` whose message asserts something
   this slice makes false.** A spec-versus-code disagreement, recorded in the spec's § Corrections
   against the code and owned by task 16.
8. **§ Allocation's example metric is `r`, which is derived** — so the spec's task 3 repair would have
   shipped a record decision 8 forbids. Closed in task 3 by moving to `abs_error`, the worked
   example's recorded column, with `delta` and `ci95` carried unchanged.
9. **`t_over_units_clustered` returns an `Interval`, so the Welch clustered form cannot "follow it
   into the CR1 machinery"** as the scoping says. Closed in task 7 by extracting `_cr1_variance`.
10. **`tests/test_validate.py`'s `_groups_cluster_*` fixture has per-arm cluster counts of 3 and 3**,
    so it cannot discriminate a side-swapping construction. Closed in task 18 Step 4 by building that
    task's own roster at 3 and 4 rather than reusing it.

**One thing this plan could not resolve, and it is stated rather than absorbed:** the **percentile
half-width literals** for the two unpaired percentile spellings, and the unpaired clustered *t*
half-width in task 14. The constructions do not exist at `e40a219`, so any literal here would be
invented rather than computed — which is the failure `CLAUDE.md` names for a regression pin captured
after the change. Tasks 6, 8 and 14 each carry a `CAPTURE-AND-PASTE` marker, the capture step, and the
constraint the captured number must satisfy. **Task 21's literals, by contrast, are all captured** —
that is what deviation (a) buys.

### Placeholder scan

No task says "similar to task N", "as above", "add appropriate error handling", "and so on", or "TODO".
Every construction task carries its full function body with its full docstring; every test task carries
full test bodies. **The four deliberate exceptions, each with the reason it cannot be a literal:**

| Where | What is deferred, and why |
|---|---|
| Task 6 Step 1, task 8 Step 1, task 14 Step 1 | Three `CAPTURE-AND-PASTE` interval literals, with the capture step in the same commit and a stated constraint each must satisfy. A literal invented here would pin the invention |
| Task 16 Step 1's validate-side test | The fixture is *"the one the existing thin-stratum test uses"*, named by the assertion it makes (`"2 of 12 units"`) rather than copied — copying a roster builder is how two spellings of one fixture drift |
| Task 18 Step 1's three run-through tests | Bodies are specified as configs and assertion shapes with the record read first, because the record shape at that commit is what three earlier tasks produce and reading it is the point |
| Task 19's site table | Each repair is stated as a claim to remove or re-point, not as replacement text, wherever the surviving sentence must be read in full first. The two that ARE re-wordings carry pins |

### Type consistency across tasks

Every signature appears identically wherever it is named.

| Name | Signature, as it appears in every task naming it |
|---|---|
| `_sample_variance` | `(values: Sequence[float], mean: float) -> float` — tasks 4, 5 |
| `welch_t_over_units` | `(of: Sequence[float], against: Sequence[float], confidence: float = 0.95) -> Interval \| None` — tasks 4, 7, 12, 14 |
| `cohens_ds` | `(of: Sequence[float], against: Sequence[float]) -> float \| None` — tasks 5, 14 |
| `_cr1_variance` | `(values: Sequence[float], keys: Sequence[str], membership: Mapping[str, str]) -> tuple[float, int] \| None` — task 7 |
| `welch_t_over_units_clustered` | `(of: Sequence[float], of_labels: Sequence[str], against: Sequence[float], against_labels: Sequence[str], confidence: float = 0.95) -> Interval \| None` — tasks 7, 12, 14 |
| `_draw_pools` | `(keys: list[str], strata: dict[str, str] \| None, clusters: dict[str, str] \| None) -> list[list[list[str]]]` — tasks 6, 8 |
| `_side_content` | `(item: Sequence[str], rows: Mapping[str, Mapping[str, float]]) -> tuple[tuple[tuple[str, float], ...], ...]` — task 6 |
| `unpaired_percentile_of_sides` | thirteen parameters, returning `PairedResample` — tasks 6, 8, 14; the full list appears in task 6's Interfaces and task 14's |
| `unpaired_keys` | `(of: dict[str, dict[str, float]], against: dict[str, dict[str, float]], allowed: set[str] \| None) -> tuple[list[str], list[str]]` — task 10 |
| `crossed_group_axes` | `(of: "Condition", against: "Condition") -> list[str]` — tasks 9, 10, 13 |
| `UnpairedEvidence` | `of: tuple[float, ...]`, `against: tuple[float, ...]`, `clusters: tuple[tuple[str, ...], tuple[str, ...]] \| None = None` — tasks 11, 12, 14 |
| `Member.sides` | `UnpairedEvidence \| None = None` — tasks 11, 12, 14 |

**Two consistency facts worth stating because a reader will check them.** `UnpairedEvidence.clusters`
is a **pair of tuples**, never a flat tuple, in all three tasks — a flat one is the shape decision 2
rejects by name. And `unpaired_percentile_of_sides` takes **two** cluster *mappings*
(`of_clusters`/`against_clusters`, keyed by unit key) while `welch_t_over_units_clustered` takes **two
label vectors** (positional, one per value) — the asymmetry is deliberate and matches the paired
family's own, where `paired_percentile_of_derived` takes a `clusters` mapping and
`paired_t_over_units_clustered` takes `labels`.

**Return-shape consistency:** both percentile constructions return `PairedResample`, both Welch forms
return `Interval | None`, and `_corrected_bounds` returns `tuple[float, float] | None` unchanged.
`family_members`, `family_shape`, `_evidence_ratio`, `rank_family`, `_level_for`, `_family`,
`corrected_for` and `corrected_fields` are **untouched by every task** — measured, not assumed:
`family_members` reads `e.ci95` and nothing else at `e40a219`.
