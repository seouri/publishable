# H8a — lineage and `io.reuse_from` — ledger

Scoping: `docs/superpowers/H8-SCOPING.md` (H8 measured at **30 tasks against a one-row charter**, split
10/8/12). Design: `docs/superpowers/specs/2026-08-20-lineage-design.md` (11 decisions, **plus § Rulings
from the controller** and **§ What the record still gets wrong**). Plan:
`docs/superpowers/plans/2026-08-20-lineage.md` (**12 tasks**, six batches).

Baseline at `28e311d`: **2456 passed, 1 skipped, 2 xfailed.**

## What H8a is, and the figure it may finally move

`io.reuse_from` is **the sole named remaining core-side blocker for six of nine** configs and
`grep -rn "reuse_from" src/publishable/` returns **zero**. H8a is the first sub-slice in a long while
that can move a count — which is exactly why the counting had to be fixed first.

## Two figures were wrong, and both were mine to carry

**"Six with no remaining core-side blocker" answered no consistent question.** The contradiction is
verbatim in one cell: `C1 | No — blocked on io.reuse_from (no remaining core-side blocker either)` beside
`E3 | No — blocked on io.reuse_from`, with E3 **excluded** from the six. Strict reading three, loose
nine; **six was really the count needing `io.reuse_from`**, a useful number wearing the wrong name, which
followed C1–C3 out of the *refused* column when H4b-1 landed.

**Then "three" fell the same way, within the hour.** H8a's design measured the
`report_by`-under-`resample` gap live on **seven of nine** — E1, E2, E4, E6, C1, C2, C3 — while the
record charges it to C1–C3 alone, so **E1 and E2 sat inside the three carrying the gap E3/E4/E6 were
excluded for.** Measured twice by computing: `t_over_units` `[0.3209, 0.7791]` without
`resample_columns` against `percentile_over_units` `[0.3583, 0.7500]` with it, moving **both** recorded
columns, so the gap is **per recorded column** rather than per headline metric.

**Ruling: this analysis gets a table, not a number** — 8 of 8 validating clean (**the only figure
`validate` can see**), 6 needing `io.reuse_from`, 7 meeting the `report_by` gap, 1 free of every named
dependency. Corrected by **appending** to the dated entries and by **editing `CLAUDE.md` at the minting
site**, where all five later repetitions derive from. **Cost if wrong:** a reader must consult a table
instead of quoting a headline, which is the price of the headline having been wrong twice.

**And the shape is the finding, not the arithmetic.** Both figures were produced identically: a slice
retired one blocker, moved configs out of the *refused* column, and **carried the summary phrase forward
without re-deriving what it counted.** That is the *carried claim* failure this repo records in code,
appearing twice in a number.

## Two rulings on the design, before it reached the plan

**The artifact-name rule is containment only.** The design measured that `read_upstream` returns the
contents of `../../secret/x.json` and moved to refuse separators — but **`reference.md` § Steps and
artifacts documents a `name` as a relative path and gives `programs/gpt-4.1__seed29.json` as a worked
legal example**, so that rule would break a documented case. And `name` comes from **the user's own
step**, which can already `open()` anything, with `CLAUDE.md` explicit that **core never inspects the
body of user Python**. So: refuse `..`, an absolute name and an escaping symlink; **keep forward
separators legal**; and say in writing that a step can read any file regardless, so nobody mistakes it
for a boundary. The design carries **a positive control** where `programs/a.json` must still read, and a
mutation widening the rule **must fail that control** — a fix that overshoots is caught, not just one
that undershoots.

**An absolute locator stays legal while an absolute name does not** — a locator addresses a run, which a
config may state; a name addresses an artifact **within** a run, whose location is derived from the step
it belongs to.

## The plan refused a fifth number, which is the outcome the ruling wanted

The design's own payoff line projected *"8 of 8 transplantable"* — **a fifth figure produced by the very
standard the correction had just ruled inconsistent.** The plan declined it and instead quotes the
corrected table **with one row moved** (`io.reuse_from` 6 → 0), leaving the other three untouched. A plan
overruling its own design on a counting question, citing the correction, is the record working.

## The guard pin, and one arm with a named editor

**Task 11 runs first**, four arms captured by running: the `run.yaml` key list, the **twelve-key**
`provenance` list ending at `allocation_hash` with `upstream` **absent**, the `execution` block's scope
routing measured from a real run (**Decision 4's entire foundation**), and the shipped positive
`read_upstream` read.

**Arm B is the one arm H8a will move, so its docstring names task 7 as its only authorized editor** —
append `upstream`, reorder nothing. That converts a change detector the slice would otherwise have to
weaken quietly into **a bounded, reviewed edit**, which is the thing five previous slices got wrong by
editing a pin to accommodate new work.

## Batch 1 — tasks 11, 1 — the guard pin and the `run.yaml` reader

Commits `1f55711` (pin), `00bf45f` (`lineage.py`, `read_run_record`), `3ddf13a` (report), `5d54e94`
(fix round), `c068ea2`. Suite 2456 → **2470**; mypy 46 → **47**, formatter 82 → **84**, both predicted by
the plan. **Both verdicts PASS; six Minors, no Major.**

**The named-authorized-editor mechanism was judged sound rather than a loophole**, on four checkable
properties: the post-edit state is specified in advance, the editor is **one named task**, a post-hoc
verification obligation is stated, and the clause sits on **arm B alone** so it cannot spread. Its only
enforcement is prose — but that is strictly better than a change detector weakened silently, which is
what five earlier slices did. **Ruling: keep it, and use the same shape whenever a pin must move.**

**Two results were better than the batch reported, and correcting upward matters as much as down.** The
`SCHEMA_VERSION` mutation was reported blind; the reviewer's point is that **a value-preserving edit is
not drift by definition.** Built properly — writer bumped with the import intact (correctly passes), then
writer bumped **plus** a stale literal — it fails four tests including the batch's own Fixture R raising
`E-UPSTREAM-RECORD-VERSION`. **Fixture R is the drift pin**, so Decision 3's whole reason for importing
`SCHEMA_VERSION` is pinned, and the batch had filed a hole that does not exist.

**The blind fault is H4d's lesson one level down.** Decomposing a code into three was not enough: the
not-a-mapping fixture parses to a **list**, falls through to the `"run_id" not in doc` check where list
membership is `True`, and **raises the same code from a different site** — while the test asserted only
`e.value.code`. Three *codes* pinned, one *fault* pinned by nothing. **Two faults reaching one assertion
is the same defect as one code covering two faults**, and only a message assertion separates them.

**And a four-arm pin whose value lives in one arm now says so.** Arm A duplicates a shipped pin, arm B is
duplicated by a shipped H7d test, and **no mutation isolates arm D** — it falls with eleven other tests.
**Arm C alone carries new discriminating power**, and it *can* be broken (routing `summary` into `shared`
fails it), which matters because it is Decision 4's foundation. Recorded so later batches watch the right
arm.

**Carried to task 7 by name:** the twelve-key `provenance` list is pinned **twice**, and only arm B names
an editor — so task 7 must edit **a shipped H7d assertion too**, with the same one-key diff, and show
both. Minor rather than Major only because the unnamed pin **hard-fails** rather than weakening quietly.
**Carried to task 9:** `reference.md` still reads `lineage.py … — not yet built` while the module ships.

## Batch 2 — tasks 2, 4 — the resolution mechanism, and not one call site

Commits `3002508` (`resolve_run`), `f33e0b8` (`resolve_step`), `559167e` (report). Suite 2470 → **2482**.
**Both verdicts PASS; one Major, eight Minors.** Nothing wired, confirmed by diffstat **and** grep.

**The property designed to die silently does not.** Decision 1's `latest` asymmetry survives only if the
relative form compares **the locator as given** — `point_latest` symlinks `latest` to the run directory's
name, which *is* the `run_id`, so a resolved-basename comparison makes the relative form **silently
accept `latest` with every arm green.** The mutation was run in its strong form and failed one named test
on an assertion; the reviewer then **checked the converse in the same run** — the absolute form still
accepts `latest` — because *a rule refusing both forms would pass the same mutation.* That converse check
is the part worth copying.

**The Major is the proxy row again, and the reviewer closed it by building rather than naming.** The repo
guard is **correct** but its only available fixture **crashes** (`E-GIT-NO-REPO`) rather than
misclassifying, so the prescribed mutation was caught by accident rather than by the property. The
reviewer built what the property needs — **the upstream inside its own `git init`'d sibling repo** — where
the correct code reads and the mutant **refuses with `E-UPSTREAM-REPO-CONTAINED`, an assertion failure.**
**A guard whose only fixture crashes is a guard tested by accident**, and both H7a fail-opens came from
exactly this move.

**Batch 1's fall-through trap is structurally impossible here**, and the reviewer established that rather
than assuming it: **each of the six new codes has exactly one raise site**, all six guard deletions were
caught on assertions, and the wrong-code cases are distinguishable. That is the right answer to *two
faults reaching one assertion* — make it unreachable by construction, then verify the construction.

**One Minor touches an invariant and is filed rather than fixed.** The relative form **skips
containment**, so a symlink under `output_dir` can read an in-repo run — against `CLAUDE.md`'s
*`input_dir`/`output_dir` may never resolve inside the git repo*. **The code matches Decision 1; the
decision's grounds are incomplete**, which makes it a filing owned by tasks 3/5 rather than a
behaviour change to smuggle in here. The related fact travels with it: the relative form returns an
**unresolved** path where the absolute form returns a resolved one.

**And a narrowing done the right way, recorded as precedent.** The reviewer ran five of six guard
deletions against one test file rather than the full suite, having **first measured** that a `lineage.py`
mutation produces failures only there and that no other importer exists. **Measure that nothing else can
be affected, then say you narrowed and why** — that is different in kind from narrowing on an assumption,
which is what *never filter the output of a sweep* exists to prevent.

## Batch 3 — tasks 3, 5 — the resolver wired, and `io.reuse_from` exists

Commits `569113f` (`UpstreamResolver` injected into `StepIO`, containment filing closed), `e21d795`
(`io.reuse_from`, `_contained`, `-NAME`, `-ARTIFACT-MISSING`), `db41b5a` (report). Suite 2484 → **2494**.
**Spec compliance PASS with one Major; quality PASS.**

**`io.reuse_from` now exists** — the method that had zero occurrences in `src/` before this branch and is
the sole named remaining core-side blocker for six of nine configs. **The table row does not move until
task 10**, deliberately.

**The risk I flagged first held, and the reviewer checked it the right way.** Closing the containment
filing meant resolving in the relative form — which batch 2 had proved is exactly what kills Decision 1's
`latest` asymmetry. **It survives, because only the *path* is resolved while the comparison stays
locator-as-given.** Four arms plus batch 2's converse verified in one process, and — the part worth
copying — the reviewer **separately checked that the reorder does not mask the loss** rather than
inferring it from the arms passing.

**The Major is a cache that misses one branch, and the reproduction is exact.** The cache is consulted
only on the non-absolute branch, so Decision 6's *one answer per run* fails for the absolute form: three
identical absolute locators produce **three** record reads where relative produces one, and with **one**
resolver, editing the upstream's `run.yaml` between two identical absolute calls returned `code_hash`
**`AAAA` then `BBBB`** — the two-answers-in-one-record state the cache exists to prevent. **The brief
prescribed a per-`run_id` cache and that is what shipped, so the behaviour is the plan's; the docstring
claiming the guarantee is the batch's.** **Ruling: key the cache by locator**, which closes the Major and
a Minor together — a **warm** cache also let a relative locator resolve a run *outside* `output_dir`.

**The batch's own concern was right and its diagnosis was wrong**, which is worth separating: it flagged
the cache as *built to spec but unpinned*, when it was **unpinned and also wrong**. A concern that smells
something and mis-names it still earns its place — it is what pointed the review at the branch.

**And an arm that cannot fail, for a reason worth remembering.** Fixture N's absolute-`name` arm survives
deleting `Path(name).is_absolute()` entirely, because the arm's target sits **outside the base** and
`startswith` already refuses it. The distinguishing config — **an absolute name pointing *inside* the
step dir** — is refused by shipped code and instantiated by nothing. **A refusal that fires for the wrong
reason is not a pin**, and the `..` and symlink arms each discriminate alone, so only this arm carried no
weight.

**A closed filing asserting a pin that does not exist** is also being fixed: keeping containment on a
resolved probe while returning the **unresolved** path leaves 142 tests green, so the containment half is
pinned and the *returns-a-resolved-path* half is not.

**Fix round 1 — all four findings closed** (`292c236`, `d3d143d`). Suite **2499**. The cache is keyed by
locator, closing the Major and the warm-cache Minor together; Fixture N gained the arm that actually
discriminates (an absolute name pointing **inside** the step dir); the closed filing's unpinned half is
addressed; and the `resolves_inside_repo` fail-open is **filed rather than fixed**, correctly — it is not
this batch's code, and a guard that fails open for an unresolved argument is worth a named owner rather
than a drive-by change.

## Batch 4 — task 12 alone — the containment rule on the two shipped readers

Commits `406a86a`, `68a1726`. Suite 2499 → **2503**, **+4 exactly with zero deletions** in `tests/`
(`git show --numstat` → `140 0`). **Both verdicts PASS; four Minors, all prose.**

**The isolation earned its seam.** Task 12 was put in a batch alone so a suite-count change would be
attributable to it and nothing else — and the +4-with-zero-deletions result **answers the plan's own
unmeasurable question**: nothing in this repo reads through a `..` segment, so a behaviour change to two
shipped readers moved no existing test.

**The rule does not overshoot, verified in both directions.** Widening `_contained` to refuse any
separator fails **all three** positive controls including the pre-existing `reuse_from` one, and **each of
the three grounds discriminates alone** — the reviewer ran three separate mutations and read each at its
failing `pytest.raises` line. **Batch 3's finding is not repeated:** the absolute arm's fixture is an
absolute name pointing **inside** the step dir, so `Path(name).is_absolute()` is the only clause that can
refuse it.

**A split ownership worth recording:** the stale design claim (task 5 "closed" the wiring) is confirmed,
but its sites split — the § Errors row half is task 9's and the `spec-defects.md` half is task 10's — and
**the design is development record, which neither consistency pass governs and which is not
retro-edited.** So the right disposition is *not to edit those rows at all*, which is different from
fixing them late.

## Batch 5 — tasks 6, 7 — the ledger and the record key

Commits `ea8174e` (accumulation), `d6e65ed` (`provenance.upstream`, **both pin edits**), `63439cb`
(report). Suite 2503 → **2510**.

**The named-authorized-editor mechanism completed its cycle and worked.** Batch 1 captured arm B with
task 7 named as its sole editor and the post-edit state specified in advance; batch 1's review then found
the twelve-key list was pinned **twice**, the second being a shipped H7d test, and carried it; **task 7
edited both with the same one-key diff and showed both.** A pin that had to move, moved once, by the
named task, with no assertion weakened. **That is the answer to five earlier slices editing a pin to
accommodate new work.**

**Two mutation-quality catches the batch made before shipping, both of the kind reviewers have had to
supply here.** A "record an entry when the read raised" mutation **caught nothing** because the fixture's
raise came from the **wrong call site** — upstream of the accumulation line — and was retargeted to the
exact site. And `used` was originally a **`set`**, so the delete-`sorted()` mutation would have rested on
**Python's randomized hash order** rather than a deterministic insertion order; storing a deduplicated
list made the mutation mean something, re-verified across three runs. **A mutation over an unordered
container is not a sort pin.**

### A controller error worth recording

**I ran batch 4's review and batch 5's implementation concurrently in the same worktree**, and the review
measured a moving tree: collection went 2506 → 2513 mid-review, and it **could not re-run the baseline**
because the attempt measured polluted state. It handled that correctly — it did **not** revert another
session's work, established `+4` from `git show --numstat` instead of a suite diff, and noted that the
concurrent delta sat entirely **after** `_contained` returns so its mutation matrix was unaffected. **The
mutation matrix being immune was luck, not design.** Reviews and implementations do not share a worktree;
either serialize them or give one its own.
