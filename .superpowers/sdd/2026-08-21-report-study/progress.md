# H8c — `report`, `study`, `BaseReport` — ledger

Design: `docs/superpowers/specs/2026-08-21-report-study-design.md` (**21 decisions**). Plan:
`docs/superpowers/plans/2026-08-21-report-study.md` (**17 tasks**, nine batches, **17 corrections**).
Baseline at `ebf642a`: **2636 passed, 1 skipped, 2 xfailed.**

## The design's six stale scoping claims, and the one worth carrying

**`basis: repeats` is written by nothing.** All five `"basis"` write sites write `"units"` — I verified
this myself — while `reference.md` asserts the value seven times and the shipped
`W-HYPOTHESIS-INFERENCE-BASE` names it. **A documented record value with no producer.** The prompt's third
branch therefore ships **behind a hand-synthesized record that says so**, and **no task may claim the
shape is producible.** Filed away from H8c, correctly: nothing in a read-and-bundle slice may alter a run.

Also dead: *"whether the standard sections need the run directory"* (answer: `run.yaml` alone — only an
**override** needs the directory); § A report override's *"read-only accessor a summary step gets"*, **false
of the code** and carried into the scoping unchallenged; and a filing claiming H8c owed the
`diff`-versus-gate sentence, which **H8b task 12 had already landed** — stale in a day.

## The `allocation.json` ruling

**A bundle never carries it, and no option is added.** Four grounds in binding order: `study add` takes a
`run.yaml` **path**, so the file is not reachable from the argument; it is **the one run artifact that is a
list of unit identities**, in the artifact most likely to be deposited publicly; `provenance.allocation`
plus `allocation_hash` already put a **commitment** to the split in the bundle without the split; and the
reader who wants to verify gets a named route — ship it as supplementary material, with `allocation_hash`
making the transfer checkable, which is the posture `input_manifest` already has.

## The plan's three best moves

**It found the mutation the design and the scoping both missed.** Decision 3's override discovery is this
slice's proxy risk, and the plan's **M15** — delete the `sys.modules` purge, or narrow it to the bare root
package — is caught only by **two separate projects declaring the SAME package name, rendered in sequence
in one process.** On a fresh process with one project, purge and no-purge are **byte-identical**, so no
fixture in the design's set could see it. **That is H7a's third fail-open — state read at the wrong
moment — in its actual costume here**, and `load_experiment`'s own docstring names the hazard.

**And it rejected a mutation for the right reason:** the walk-up arm would be caught by a **crash**
(`find_repo_root` raises `E-GIT-NO-REPO`) rather than by the property — which is H8a's batch-2 Major, cited
by name.

**The guard pin's arm D is built to need NO editor.** It pins the three worked `diff` blocks' rows as
**raw text**, located by the `code_hash` line they contain — and because task 16 inserts its two header
lines **above** `code_hash`, **a passing arm D is itself the proof** that no hash prefix, run ID, delta
line, row label, row order or separator moved. § The worked example is binding and its intervals were
checked numerically; this is how a pin enforces that without needing to be trusted.

## Two process errors of mine that the plan designed around

**B9 is the documents batch, alone and reviewed** — explicitly because H8b dispatched no review for its
documents task and **three of its four whole-branch Majors lived in that commit.** And correction 6 puts
**every code's § Errors row in the commit that raises it**, because *a row narrower than its code* was the
whole-branch Major on **both** preceding sub-slices — the second time in the very task that went
unreviewed.

## Batch 1 — task 17 — the guard pin, four arms

Commits `52612ed` (the pin), `2610ef4` (report). Suite 2636 → **2643**. Four gates clean.

**The implementing agent stalled waiting on a monitor** — the sixth instance across these slices, and its
instructions said in bold not to construct one. **I verified the true state rather than assuming it:**
455 insertions across three test files, **zero deletions**, so no mutation was left applied — established
from the diffstat, not from the agent's account. Gates run, work committed by me, and the agent then wrote
only its report, with the stall recorded in it. **One of the previous five stalls left a mutation applied**,
which is why the diffstat check comes before anything else.

**Arm D is the arm worth understanding, because it enforces § The worked example without being trusted.**
It pins the three worked `diff` blocks' rows as **raw text, located by the `code_hash` line each block
contains** rather than by position — and task 16 inserts its two header lines **above** `code_hash`, so
**a passing arm D is itself the proof** that no hash prefix, run ID, delta line, row label, row order or
separator moved. **It deliberately has no authorized editor**: if it fires, that is a finding. Arm B, by
contrast, names **task 1** as sole editor with the post-edit state stated in advance — the fourth clean
cycle of that mechanism.

## Batch 2 — tasks 1, 2 — `BaseReport` and `ReportIO`, nothing dispatched

Commits `6b0bd04` (`BaseReport`, frozen `Section`, the one new export), `56e6dc1` (`ReportIO` and one
traversal two classes call), `0140715` (report). Suite 2643 → 2651 → **2665**; mypy 49 → **50**,
formatter 88 → **90**.

**The authorized-editor mechanism completed a fourth clean cycle**, and this one inverted a negative the
right way: arm B's `assert "BaseReport" not in publishable.__all__` is **gone**, replaced by the name
entering the **full sorted list equality** — which asserts presence *and* position, so it is strictly
stronger than the negative it replaced. Same shape as H8a's `not in` → `== []`.

**A carry-forward was made correctly and I am carrying it myself, because a report cannot reach a brief.**
Task 1's render-level mutation arm — an override reaching into a **standard** section's mapping body —
could not be written yet, because no standard section with a mapping body exists until task 5. The batch
named it forward to task 5 **explicitly citing the routing failures on H8a and H8b**. But briefs are
extracted from the plan, and **that is exactly how H8a lost a finding between a review and the brief
written from it** — so **the carry travels in B4's dispatch**, not only in the report.

**One structural note the batch disclosed rather than hid:** `ReportIO` calls `StepIO._read` and
`StepIO._contained` directly — both stateless static methods, reuse rather than inheritance — so
`ReportIO`'s module still names `StepIO`. Disclosed as a symmetry question for a later reviewer rather
than resolved unilaterally, which is the right disposition for a shape that is correct but arguably
misplaced.

## Batch 3 — task 3 alone — override discovery, the slice's proxy risk

Commits `cbd1461` (override discovery, four codes with their § Errors rows), `12f853d` (report). Suite
2665 → **2685**. **Spec compliance PASS; three Majors, three Minors.**

**Isolating this batch paid for itself: the proxy class recurred in a new costume and the review caught
it.** `sys.path` restoration was **pinned by nothing** — replacing the `finally` body with `pass` left the
full suite green — **and `pop(0)` answers *which entry did I add?* with a POSITION rather than with the
entry.** It is reachable, because **user code runs inside that window by design**: an override doing its
own `sys.path.insert(0, …)` makes the pop remove the wrong entry, and a second project's override then
rendered **from the first project's `src/`.** That is Decision 3's own cost-if-wrong by a route other
than a scan.

**And the defence cited for it is where the reasoning slipped, which is the transferable part.** The
docstring justified `pop(0)` because `load_experiment` pops by index too — **accurate about the mechanism
and wrong about the exposure**: only an *import* runs inside that window, and a whole *render* runs inside
this one. **A precedent that matches the code and not the risk is not a precedent.** Now a `CLAUDE.md`
entry: *removing by position is a fifth proxy.*

**The core of the task was certified the right way**, by showing both facts **steer** the answer rather
than merely get read: repointing only `entrypoint` yields the decoy; rewriting only `repo_root.txt` yields
the other project. And **M15 — the mutation the design and the scoping both missed — reproduced in both
forms**, with a single-project probe passing identically on shipped code **and under both mutated forms**,
which is what makes the blindness real rather than asserted.

**A decoy whose sort position agrees with the bug — twice in one task**, the second time after the first
had been caught and disclosed. M1's fixture ruled out only *first*-wins; **scan-last passed** because the
decoy sorted before the real package. **Catching it once did not immunize the next fixture.** Now a
`CLAUDE.md` row: put a decoy on **each side**.

### Two controller errors of mine, same root cause

**I ran `git add -A` while a fix-round agent held this worktree**, and committed its in-progress
`report.py` docstring fix under a message that did not describe it. Nothing was lost — I checked whether
I had captured a **fix or a live mutation** before doing anything else, and it was a fix — but that is
the second instance of one root cause: **treating the worktree as mine while an agent holds it.** The
first was running a review and an implementation concurrently, which polluted the reviewer's baseline.
**Do not stage broadly while an agent is writing; name the paths.**

**And a commit message described edits the commit did not contain.** A heredoc asserted on its second
anchor *after* replacing the first, so `write_text` never ran — and `git add -A` then committed an
untracked review file under a message written for work that had not landed. **The message was the claim
and the diffstat was the fact**, which is this project's own rule about comments, arriving in a commit
message. Corrected by a follow-up commit that says what happened rather than by rewriting a pushed
commit.

## Batch 4 — tasks 4-7 — record in, text out

Commits `556565b` (`report_form`, `read_record_file`), `9a3202c` (Conditions, Deltas), `6c642b0`
(Verdicts, Attrition, the `nondeterministic` filing), `eebbe2a` (both renderers), `ca4e47a`, `2092594`,
`d73303f` (fix round). Suite 2689 → 2737 → **2738**. **Spec compliance PASS; three Majors, eleven
Minors.**

**The carried mutation was routed correctly and was still vacuous, which is the lesson.** M14's whole
history is routing: it could not be built when task 1 ran, batch 2 named it forward, and **I carried it in
the dispatch myself** because a report cannot reach a brief. It got built — and the test named
`..._reaches_the_page` **rendered nothing**, mutating a dict and asserting the same dict. Gutting
`render_markdown` to `return "GUTTED"` left it green. **Getting a mutation routed to the right task is
necessary and not sufficient; it then has to test the thing.** Rebuilt to render through both renderers
and assert on emitted text, with the gutted-renderer mutation confirmed failing.

**A design defect, and the fifth instance of one move.** A recorded column named `by` was **silently
dropped from the render**, because the Conditions filter excluded a `report_by` stratum by **the string
`by`.** Decision 5's ground — *"the record `report` reads can never hold a metric called `by`"* — is
**false against a real run**, where that column is a genuine metric entry with value, `ci95`, method and
`repeat_spread`, and `cli.py` says in writing the column *"keeps its value"*. **Ruling: exclude by
structure, not by name** — a stratum is identifiable by **where it sits in the record**, not by what it is
called. Now `_is_metric_entry`/`_is_strata_block`, with *"never identified by name"* in the docstring, and
`stats.RESERVED_METRIC_NAMES` left alone because its own site guards a **derived-key collision**, a
different question.

**The tally of that move on this project is now: a module-name prefix, a class marker, state read at the
wrong moment, a one-spelling grep, `pop(0)`, and a reserved name.** Six.

**And the third Major was the same shape one level down** — two of three `execution` nesting branches were
exercised by nothing, because **Fixture R's `shared` block was empty while the test's own name claimed
it.** A fixture that does not instantiate the branch its name claims is a name standing in for a fact.

## Batch 5 — tasks 8, 9 — `report` becomes a real command

Commits `65207c1` (task 8), `f54c3e7` (task 9), `96b7060` (report), `fd3f843` (fix round). Suite 2738 →
2746 → **2753**. **Both verdicts FAILED on review: one Critical, three Majors, six Minors — all closed.**

**The Critical is the sixth credential leak of this class, and its cause is the most transferable yet.**
`get_template` and `declared_credential_names_for` ran **outside every `try`** and **before `credentials`
existed**, so a project-local template raising at import escaped to `main`'s un-redacted printer.
Verified with a positive control: **`validate` over the identical project prints `<redacted:…>` while
`report` printed the sentinel** — and § Secrets explicitly promises redaction for a post-registration
raise.

**`freeze` — the recipe cited as the precedent — already had it right.** The calls were lifted; **the
`try` they sit inside was not.** Now a `CLAUDE.md` entry: **a recipe is its calls PLUS where they sit.**
The fix mirrors `freeze._precheck`'s own `except BaseException`, with the reasoning written beside it and
the reason `command_run` gets away with an unguarded call (it validates first; `command_report` does not).

**My scrutiny question about the placeholder was the right one to ask.** `report <study.yaml>` printed
*"specified but not built"* and **exited 2** — false as of the commit that flipped the `Status` cell to
`built`, and **Decision 6 reserves 2 for invocation faults.** The CLI-table test forbids that sentence for
a built row **and cannot reach it**, while the batch's own test **pinned the sentence as present.** **A
placeholder that lies about build state is not a placeholder**; it is now a coded refusal at a permitted
exit code.

**A judgement I endorsed rather than overruled.** A credential an override renders **into a body** reaches
stdout, and the reviewer **declined to grade it Critical** because § Secrets' documented limit covers only
an execution's `error` and a diagnostic's message. That is correct — the specification permits it, and
grading it Critical against a blanket instruction would have been wrong. **The remedy is the sentence, not
the behaviour:** the limit now names a rendered report body, so the next reader need not re-derive it.

**And a fix that was correct and unpinned, again.** Mutating `raise KeyboardInterrupt from None` to a bare
`raise` left the **full suite unchanged** while the probe leaked the sentinel — the row `CLAUDE.md` counts
five times in three slices, now six.
