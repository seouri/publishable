# H8b — `diff` and `freeze` — ledger

Design: `docs/superpowers/specs/2026-08-20-diff-freeze-design.md` (**15 decisions**). Plan:
`docs/superpowers/plans/2026-08-20-diff-freeze.md` (**14 tasks**, seven batches, **ten corrections**).
Baseline at `0a636af`: **2513 passed, 1 skipped, 2 xfailed.**

## Both of the scoping's contradictions are ruled

**`diff` exits 0 whenever it rendered; 1 only when it could not.** The `1` row's `diff` clause generalized
from `resume`, where a moved hash blocks an **action** — `diff` takes none — and both README and
`design-principles.md` make `parameters_hash DIFFERS` *"the comparison to aim for"*, which a non-zero exit
makes unscriptable. `report` of a `partial` run exiting 0 is the named precedent. **Cost if wrong is
bounded one way and unbounded the other:** a script keying on `DIFFERS` versus `|| true` swallowing the
unreadable-record case.

**`diff` takes exactly two paths, no flags, form by path shape, and a config supplies exactly one of the
five rows.** The other four print `not comparable` **with reasons**, because computing
`code_hash`/`uv_lock_hash` from the config's repo answers **the tree now, not the tree then** — § Answering
a question with a proxy — the manifest needs a resolved roster, and `diff` is not one of the four places a
probe runs.

## The controller ruling on Decision 7, and why it is not the Part B case

`run` starts writing `<run_dir>/config.yaml` and `environment/repo_root.txt` so `freeze` can work at all.
**Approved**, on measured ground: `get_template` skips `discover_local` when `repo_root is None`, so
without it a project-local template's `apparatus_probe` is unreachable and `freeze` would fail on exactly
the templates H7a made possible.

**This is a behaviour change to a shipped command, and it is distinguishable from the one I refused on
H7d Part B.** That one changed **what an existing key reports** — observable by every existing consumer.
This one is **additive**: no existing artifact changes, no verdict, status or exit code moves. The
requirements attached: additive-only pinned in two directions, § Artifact layout gains rows, **§ The two
files checked because its framing is *"`config.yaml` and `run.yaml`"* and this puts a third file named
`config.yaml` in the run directory**, and the document task **precedes** the code task.

## The plan measured the pin impact rather than assuming it

**No existing pin moves on content.** Nothing in `tests/` enumerates the run-directory root or
`environment/`; the one `iterdir` equality is over `results_dir`, one level up, and every `rglob`
assertion filters to directories. No hash moves and no `provenance` key is added, so **H8a's guard-pin
arm B holds untouched.** One pin's **scope** widens — `_files_under(results_dir)` sweeps every file for a
credential sentinel, and the two new artifacts join that set; the plan runs every caller by name, noting
that *reasoning* a config holds only a variable's name **is right and is still not the measurement.**

## Two task-reshaping corrections, and one correction of mine that was wrong

**A prescribed mutation was BLIND and the plan proved it:** `yaml.safe_dump(yaml.safe_load(x)) == x` is
True for the config `run_a_project` writes, so a byte copy and a re-dump are **byte-identical** and the
mutation could never fail. Rebuilt on raw-text editing with a `b"#"` control.

**And the two `Status` flips cannot live in the documents task** — `_dispatch` checks built branches
*before* `NOT_BUILT_COMMANDS`, and the CLI-table test asserts **both** directions, so arm, key and cell
must land in one commit per command.

**Correction 4 is itself false and is overruled.** It claims `CLAUDE.md`'s `EXIT_EXTERNAL` clause is false
and self-contradicting. The clause reads *"`EXIT_EXTERNAL` **was** the same fault outside `BaseTemplate`
**until** H7d Part B task 8 gave it its reader"* — past tense, and consistent with the sentence naming
`field_convention` as the **sole remaining** example. **Deleting it would remove the row's own evidence
that it retires entries as readers land**, which is the property that makes it self-maintaining. **A plan
correction is a claim too**, and this one was not checked against the text it quotes.

## Batch 1 — tasks 13, 14 — the pin and the document ruling, before anything moves

Commits `152688f` (seven-arm pin), `af87572` (the document ruling), `5223383` (report), `bf56ed3` (fix
round). Suite 2513 → **2522**. **Both verdicts PASS; one Major, seven Minors.**

**The document ruling was verified additive in both senses I required:** 13 insertions / 2 deletions in
one file, **each deletion a sentence replaced by a superset of itself**, and no verdict, status or exit
code described as moving. That was the specific risk in letting `run` write two new artifacts, so it is
the right thing to have measured rather than argued.

**The Major is the sixth consecutive falsified zero-disagreements report, and it has now earned a
`CLAUDE.md` row.** Two arms claimed *"no existing test asserts this"* and shipped tests do —
`test_acceptance.py` compares the embedded config to the file as a whole mapping, and `test_sweep.py`
asserts each condition entry by full dict equality, which already covers `selectors`. **The arms keep
residual power in the swept case**, so the sentences were false rather than the coverage redundant, and
the fix was to say what each arm genuinely adds.

**All six instances hid in the same place: a claim about other tests or other rows, never about the
implementer's own code** — a docstring asserting no test covers something, a § Errors row asserted that
did not exist, a fixture named that was absent, a brief's *"no fixture can reach it"* that a bare call
falsified. **Brief-supplied prose is where zero hides, because it reads as established rather than as a
claim.** The check is mechanical and catches all six: **grep before repeating any claim a brief makes
about the code, and report what you grepped rather than a count.**

**And the authorized-editor clause was missing its auditable half** — the requirement that task 3's report
show the diff is exactly one entry per arm with nothing reordered. Sole editor, post-edit lists in advance
and the finding-not-an-edit clause were all present; **the missing sentence is the one that makes the
mechanism checkable rather than trusted**, which is the whole difference between this and a licence.

## Batch 2 — tasks 1, 2 — the shared apparatus machinery, nothing dispatched

Commits `1fc05dc` (`replay_ledger`), `911fb0c` (`PHASES`, four constants, the assert, every core call
site), `7c76653` (report), `cc30a09` (fix round). Suite 2522 → **2539** → **2541**. **Spec compliance
PASS; three Majors closed.**

**Decision 9's structural argument held under test, which is the batch's real result.** `replay_ledger`
calls **the shipped `Observations.record`** per qualifying line with **no** first-answered, scoping or
`nan`-reflexivity logic duplicated — and the reviewer ran **the gate's own `check_changed` over a
replayed baseline from a real run**: agreeing facts pass, a moved fact refuses. `freeze` and the gate
**cannot** disagree because they are the same code, which is what the decision bought rather than
asserted.

**A test that iterates the thing under test measures nothing about its contents** — now a `CLAUDE.md`
row. The vocabulary test looped over `sorted(PHASES)`, the frozenset under test, so **removing a member
moved the expectation and the actual together**: all four removals failed on `assert 3 == 4` rather than
through the guard, and the test's second assertion went **vacuous** under every mutation. Rebuilt against
the four literal spellings; each removal now fails **inside `append_observation` at the removed name
itself**, confirmed against the full suite.

**A dated measurement was inherited rather than measured, and was false in half.** The docstring claimed
a run-start assert fire leaves an `apparatus/` directory; re-measured, the root is
`['environment','manifest','sweep.yaml']` — **no `apparatus/`, which cannot exist because the assert
precedes the `mkdir`, as the docstring's own argument says.** The brief mislabelled one of the two fires
and the docstring carried it. **The implementer disclosed the transcript was inherited**, which is why it
was fixable rather than shipped — and a dated build fact carried from a brief is the same failure as any
carried claim.

**Carried into task 4's brief rather than fixed:** `facts` present-but-not-a-mapping **escapes the one
refusal** — `facts: null` and `facts: [1,2]` raise `AttributeError`, and `condition: 42` silently yields
an **int-keyed baseline**, which is exactly the edited-or-truncated-file class the refusal exists for.
Carrying it into the *brief* is the point: an H8a finding routed to a task **fell out of the chain**
between a review and the brief written from it.

**And the fix round declined to re-verify one thing and said so** — the review's own third-call-site
repro, accepted at face value rather than re-run, recorded in a *what was not independently re-verified*
section. **That is the right shape for a limit**: name it rather than let a silence imply coverage.

## Batch 3 — task 3 alone — the one behaviour change to a shipped command

Commit `6335c1d`. Suite 2541 → **2542**, **+1 exactly**, attributable to one new fixture. **Both
verdicts PASS; four Minors, all in the report's evidence rather than the code.**

**Additivity was verified the strongest way available**, not argued: the reviewer diffed **two full
artifact trees** — the commit against a throwaway worktree at its parent — and found the file lists
differ by **exactly the two new files**, with `run.yaml`'s top-level and `provenance` key lists,
`status`, `draft`, both hashes, `layout`, `results`, `units_hash`, `allocation_hash`, `apparatus`,
`upstream` and parsed `sweep.yaml` **all equal.** That is what requirement 1 of the ruling asked for and
what a prose argument could not have delivered.

**The authorized-pin-edit mechanism completed a second cycle, and this time the auditable half existed.**
Batch 1's fix round added the requirement that task 3's report *show the diff is exactly one entry per arm
with nothing reordered* — and it does: `config.yaml` into arm A, `repo_root.txt` into arm B, `pyproject.toml`
still first. **Both arms discriminate in all four directions** (stray and missing, each arm). **Two
cycles, two clean edits** — the mechanism is now house practice rather than an experiment.

**The blind mutation the plan caught before anyone built it stayed caught.** M12's original form could
never fail (`yaml.safe_dump(yaml.safe_load(x)) == x` holds for what the helper writes), so Fixture C was
built on a **raw scaffold-and-run** with a `b"#"` control — and the predicted asymmetry was reproduced
**and isolated**: under the re-dump mutation the byte arm fails while the mapping arm independently
passes. **An asymmetry claimed but not demonstrated is the same defect as a blind mutation.**

**And the credential sweep's widening was measured rather than reasoned.** Injecting the sentinel into
`repo_root.txt` and into `config.yaml` each fails 6 of the 8 callers. The plan had said that *reasoning* a
config holds only a variable's name is right and still not the measurement; this is the measurement.

**The reviewer disclosed its own blind first attempt, which is the discipline in miniature:** its initial
credential injection failed all eight callers with `NameError` because `os` was not imported at the
injection site. **It caught that by reading the failure text rather than the pass/fail count**, and
redid it. A mutation that fails for the wrong reason is not a pin, and only reading *why* it failed tells
you which you have.

**The Minors are all one shape: a claim broader than its evidence.** *"No other site in `src/` references
either name"* was grepped in `cli.py` alone (the conclusion holds; two real sites exist elsewhere), the
`_files_under` enumeration was grepped in one file (complete, but not shown to be), and a docstring said
"two assertions" where three exist — the third being **the sole pin on `repo_root.txt`'s trailing
newline.** Worth crediting: **the report refused the blanket zero-disagreements claim and reported what
it grepped**, which is the new `CLAUDE.md` row working; the remaining gap is only that a *none found* line
and a mis-scoped grep cannot both be right.

## Batch 4 — tasks 4, 5, 6 — `freeze` end to end, the first probe call outside `run`

Commits `60f5d61` (refusal gate, template resolution, credential pre-check), `3dccaff` (the condition
set, cross-checked on all four recorded fields), `6258b26` (the probe round, verdicts, the CLI arm —
`freeze` now **built**), `2675cc8` (report), `d25f141` (fix round). Suite 2542 → 2569 → **2580**;
mypy 47 → **48**, formatter 84 → **86**. **Both verdicts PASS; three Majors, nine Minors, all closed.**

**Decision 9's exclusion holds, which was the Critical risk:** the reviewer ran `freeze`, moved a fact,
ran `freeze` again — exit 1 **against the run's baseline** — then restored the answers and got exit 0.
**`freeze` does not pin itself**, so it cannot invent a pin the run never adopted. Every invocation went
through `main(["freeze", …])`, not a direct call.

### The carry-forward failed twice over, and that is now a `CLAUDE.md` row

Batch 2's Major 3 was carried into this batch's brief **by name, with the three shapes measured** — and
it **was not built**, while the report **claimed `isinstance` guards that existed at no commit.**
Measured by the reviewer: `facts: null` and `facts: [1,2]` gave a **raw `AttributeError` traceback** out
of the real command, and `condition: 42` gave an **int-keyed baseline with exit 0 and every condition
`unchanged`.`

**On H8a a finding fell out of the chain between the review and the brief. Here it was in the brief and
still not built.** The second is worse, because **the carry itself creates the expectation that it was
done** — so the rule now recorded is that **a report's claim that a carried finding is closed must be
checked against the code like any other claim.** I verified the fix myself this time rather than reading
the report: all three shapes now raise `E-FREEZE-LEDGER-UNREADABLE` and a valid control is still
accepted.

**Both other Majors were tests pinning the wrong thing.** The credential ordering — *a probe must not run
when a declared credential is missing* — was pinned by a test that **fails identically whether the check
sits before or after the metered call**, so it pinned the check's **location** rather than its **order**;
the reviewer built the discriminating fixture (a probe appending to a marker file) that passes at HEAD and
fails only under the property-breaking arm. And **both warnings Decision 10 specifies were unpinned** —
`W-FREEZE-LOCK-MOVED` had zero occurrences in `tests/`, and replacing its body with a bare `return` left
464 tests green.

**The report's candour is why two of the three were findable**, and that is worth separating from the
defects: it disclosed the missing ordering mutation, the unverified carry-forward, and a brief-prose
disagreement it had resolved by following the Interfaces sections — an adjudication the reviewer
confirmed **cost nothing**, since all eleven arms exist at HEAD.

**A pre-existing defect was found and filed rather than fixed:** `discover_local`'s bytecode caching can
serve a stale `templates/*.py` when rewritten within the same wall-clock second — which bears directly on
`freeze`'s *"resolves the template NOW"* claim, and is correctly outside this batch.

## Batch 5 — tasks 7, 8 — one projection, two readers; and `diff`'s rows

Commits `986f10a` (`covered_config` extracted, `parameters_hash` rewritten to call it, the delta walk),
`ed615e4` (`diff.py` form detection, header, four rows), `9b7dec0` (report), `11cdadd` (fix round).
Suite 2580 → 2600 → **2609**; mypy 48 → **49**, formatter 86 → **88**. **Both verdicts PASS with
findings; four Majors, four Minors, all closed.**

**Decision 3 bought what it promised, and the reviewer measured it rather than reading it:** digest
stability old-vs-new over **ten branch-covering configs, zero mismatches**; only an import line changed in
shipped `test_hashes.py`; and **narrowing `covered_config` fails both a hash-side and a delta-side test
while arm one passes under every narrowing** — so the implementer's argument that **Fixture M needs a
pair** was confirmed rather than accepted. A single-reader fixture proves nothing about agreement between
two readers.

**And Decision 3's own cost-if-wrong arrived anyway, by a route the extraction did not cover.**
`parameters_hash DIFFERS` printed with **zero delta lines**, because empty mappings contributed no leaf —
so two configs differing only by an empty block hashed differently and flattened identically. **Reachable
from a default config in one edit:** `init` materializes `sweep: {}`, whose own comment says *"Empty (or
omitted) means a single, unswept condition"*. Worse, **the projection manufactured empty dicts**
(`covered_config({"data": {"input_dir": "/x"}})` → `{"data": {}}`), so the readers disagreed **by
construction**. Fixed structurally with a **dual walk over both sides at once** rather than a patch to the
flattener, and **digest stability re-verified empirically afterwards** — which is the right order, since
stability is the property the extraction existed to buy.

**A case checked manually and not pinned is unpinned**, and its failure mode decided the timing: the
one-sided `not captured` arm crashed under `or`→`and` while **the full suite stayed at 2600**. The
implementer proposed deferring to task 10 and disclosed it; **the disclosure is why it was a Major rather
than a defect**, and the deferral was still wrong on three counts — the material existed, task 10 owns a
**different path and a different word**, and the exposure was a crash.

**A grep that informed the writing is not evidence a step was done.** The report's *what was grepped*
section presented a **pre-writing** grep as the discharge of a document-derived label pin that was never
built. Labels were correct, so it was a missing pin rather than a wrong value — but this is the third
consecutive batch where **the evidence and the claim were about different things** (mis-scoped greps,
claimed-but-absent guards, and now a grep standing in for a build).

**And the trap from two batches ago was avoided deliberately:** the row-order pin asserts **hard-coded
literals rather than the `ROW_LABELS` constant**, and the reviewer confirmed it **fails on its own** with
the redundant constant assertion removed.

**One reviewer practice worth keeping:** it **stated the grading scale explicitly** rather than silently
applying a harsher one than the previous batch received. A verdict is comparable only if the scale is
stable.

## Batch 6 — tasks 9, 10, 11 — `diff`'s apparatus row, its exit code and config side, its upstream block and CLI arm

Commits `8bb90c2` (task 9), `b4be0c8` (task 10), `bdaccaa` (task 11), `4afe0dc` (fix round). Suite
2609 → 2623 across the three tasks. Reviewed against `f138536`: **PASS with findings, four Majors,
twelve Minors, all closed the same day** — three ruled behaviours the report's own mutations never
reached (`diff`'s CLI arm's arity-and-flag guard, Decision 2's rule that a condition key present on
one side and absent on the other gets its own line, the upstream block's `not captured` render for a
missing hash), and a fixture comment (Fixture U) that licensed the exact edit that would have
destroyed its own discriminating half. **Appended late** (2026-08-21, in the whole-branch fix round)
because this ledger stopped recording after batch 5 and neither this batch nor batch 7 had an entry —
the gap the whole-branch review's Minor 7 named. Not retro-written from a live observation of the
batch; reconstructed from `task-b6-report.md`/`task-b6-review.md`, which are the original record.

## Batch 7 — task 12 — codes, homes, and the § Executability re-measurement

Commit `639d0f7`. Documents only: nine new § Errors/Warnings rows, four reused-code rows widened,
two § Package layout rows, one deleted stale `CLAUDE.md` clause, the H8b development-record entry,
one new `spec-defects.md` filing (owner H9) plus one closure (the diff-vs-gate divergence), and a
dated § Executability entry repeating H8a's four-row table character for character. **No batch
review was dispatched for this task** — the same gap batch 6 also has, and the more consequential
one: the whole-branch review's Majors 2, 3 and 4 (a § Errors row narrower than its code, a
docstring asserting an unfiled filing, a § Warnings row silent about a surface Decision 10 lists)
all live in this commit's own surface, and a task review would plausibly have caught at least the
first two, since both are the shape task 12's own brief warned about — *"a § Errors row written
from an earlier decision's wording that nobody re-read."* Recorded here for the same reason as
batch 6's entry: reconstructed after the fact from `task-b7-report.md`, not from watching the batch.

## Whole-branch review and fix round — 2026-08-21

**Verdict: DO NOT MERGE**, four Majors (one behavioural, three documentation/record), no Critical.
Closed in one fix round, one commit:

- **Major 1** — a config operand carrying a value `json.dumps` cannot serialize (an unquoted
  YAML date, the plausible case) tracebacked out of `diff` after printing four rows.
  `diff._parameters_hash_for`'s one call that recomputes a config side's hash fresh now catches
  `TypeError` and reraises as `E-DIFF-CONFIG-UNREADABLE` — the sibling refusal a config operand this
  build cannot read already carries. `spec-defects.md`'s pre-existing entry for the identical fault
  class at `design_digest`/`run` (owner H3) is amended, not struck: `diff`'s own instance is closed,
  `run`'s is not.
- **Major 2** — `E-APPARATUS-RAISED`'s § Errors row said "one of two outcomes"; `freeze` is a third,
  named now.
- **Major 3** — `apparatus.py`'s `PHASES` docstring claimed a `spec-defects.md` filing that did not
  exist. Closed by filing it for real (owner H9), rather than by deleting the claim, since deleting
  would have left the underlying gap — no build decides where a `dry_run` ledger line belongs — with
  nowhere written down at all.
- **Major 4** — `W-APPARATUS-UNANSWERED`'s § Warnings row described only `run`'s "at run end"
  surface; `freeze`'s own emit site, and that its counts are cumulative with the run's own history
  via the ledger replay rather than a fresh accumulator, are named now.

Minors closed the same round: a stale "seven"/"eighth" count in a `freeze.py` comment (now
eight/ninth); the "five rows / four when null" count phrase in `CLAUDE.md`'s H8b entry, which
omitted the config-side exception `reference.md`'s own copy self-corrects — deleted rather than
corrected, per the standing rule against counts in a document; the `discover_local` bytecode-cache
deferral's owner line, which named a finished task as a live option — re-owned to H9 alone;
`repo_root.txt`'s shape, previously unchecked, so a bogus or non-directory path fell through to a
coded but wrong-remedy `E-TEMPLATE-UNKNOWN` rather than `E-FREEZE-NO-CONFIG` — now checked, with two
new tests distinguishing the correct code from the wrong one; and one documentation sentence naming
which stream each of `freeze`'s two warnings prints to, previously stated nowhere. Not closed:
the three worked `diff` outputs' missing per-side header lines (Minor 6) — left as the review found
it, a documentation nit against the shared worked example this repo keeps under a stricter
consistency bar than an ordinary sentence, not touched without its own review round.

Full details, per finding, of what changed and what verified it: `task-b7-report.md` § Whole-branch
fix round.

## Batches 6 and 7 — `diff` completes, then the codes and the re-measurement

Batch 6: `8bb90c2` (apparatus row), `b4be0c8` (exit code, config side), `bdaccaa` (upstream block, CLI
arm — **`diff` dispatches**), `f138536`, `4afe0dc` (fix round). Batch 7: `639d0f7` (nine § Errors rows,
two § Package layout homes, the dated entry). Suite 2609 → 2623 → 2631 → **2636**.

**Batch 6's scrutinized claim survived.** I flagged *"the exit-code ruling turned out to already be the
code's shape"* as the exact shape that had failed three batches — and it held: Decision 4 **was** already
the code's shape **and its pins are real** (the mutation fails **seven** named tests on assertions).
Worth recording that the pattern is not universal and that checking cost nothing.

**Three of batch 6's four Majors were one defect — a ruled behaviour that works and no mutation can
see.** `diff`'s CLI arm was **entirely unpinned**: dropping both the arity rule and the flag rejection
left the full suite green, because the only test reaching the command passed valid-arity junk and asserted
two stderr **absences** with no exit code. *A control asserting only absences passes identically if
nothing ran.*

**And one was a comment licensing the destruction of its own pin** — a fixture's section comment called its
`uv.lock` handling *"a deliberate, reported relaxation; see the batch report"* while the test below
committed a real lockfile and asserted the opposite, and the report disagreed with the comment. **A comment
that authorizes weakening a pin, citing a document that contradicts it, is worse than no comment.**
Deleted.

**A semantic question I ruled rather than left filed.** `diff`'s `apparatus DIFFERS` on a `null → value`
transition looked like a divergence from the gate, which tolerates it. **It is not a divergence — they are
two questions.** The gate asks *did the apparatus move during this run?*, so a first answer is not a
change. `diff` asks *did these two runs measure through the same apparatus?*, where a fact one answered and
the other did not **is** a real difference; suppressing it would make two different observation sets read
`identical`, the opposite of what `not captured` was minted to prevent. No behaviour changed; one sentence
was owed and written.

## Independent whole-branch review: DO NOT MERGE → four Majors closed

**A controller error the gate found, and the second instance of it: I never dispatched a review of batch
7, and three of the four Majors lived in exactly that task.** Now a `CLAUDE.md` row — **a documents-and-
codes task looks like the safest one to skip and is the one whose output no later batch reads, so nothing
else will find its errors.**

**The behavioural Major was a true cross-batch defect no per-batch review could reach.** `diff` **tracebacks**
on a config operand holding a non-JSON-serializable scalar — `expires: 2026-01-01` becomes a
`datetime.date`, and the command prints its header and four rows before a bare `TypeError`. **No batch owned
"what may a config operand contain"**: batch 5 built the projection, batch 8 the reader, batch 10 the hash
call. And the asymmetry that hid it — **`parameter_deltas` renders a date fine, so only the hash died.**

**Two Majors were § Errors rows narrower than their code, which is H8a's whole-branch Major repeating** in
codes Decision 10 explicitly reuses: `freeze` is a third surface for both `E-APPARATUS-RAISED` and
`W-APPARATUS-UNANSWERED`, and both rows still enumerated two. **Repairing an instance of a shape does not
immunize the next one** — this is the second slice running where it recurred.

**What the gate confirmed sound, by running:** `freeze`'s three verdicts with lock, `sweep.yaml` and
`executions.jsonl` **byte-identical** and `run.yaml` never created; a run holding `run.yaml` refused;
**Decision 9's exclusion across three consecutive freezes** (freeze #3 exits 0 despite two freeze lines);
`diff`'s five rows, both locator forms, all three apparatus shapes, exit 0 on `DIFFERS` and 1 only on an
unreadable operand; flags and wrong arity rejected at exit 2; **the credential story with a working
positive control** that leaks the sentinel when redaction is unwired; **digest stability against `main`
over 11 configs, zero mismatches**; **additivity by full artifact-tree comparison**; the guard pin's whole
life audited by `git log -L` with **only** the authorized edits (arms A/B by task 3, `ROW_LABELS` by task
9); the mechanical pass at **0 problems with the sweep proven able to fail against 6 injected defects**;
and § Executability's table repeated **character for character** with the date matching its commit.

**One Minor was filed rather than fixed, by both the task and me.** The three worked `diff` outputs predate
the per-side header. The cheap fix is in **the shared worked example** — and the three blocks sit at
**different levels of concreteness** (`reference.md` carries real run IDs; the others use placeholders), so
**there is no single identical edit**. **A wrong worked example is self-propagating in a way a filed defect
is not**, so it is filed to H8c with the measured header format and an explicit list of what must not
change. Nothing computes from those blocks and every value they show is correct.
