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
