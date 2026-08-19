# H7d Part A — the apparatus: observe and record — ledger

Design: `docs/superpowers/specs/2026-08-19-apparatus-part-a-design.md` (14 decisions).
Scoping: `docs/superpowers/H7d-SCOPING.md`, **including its appended correction**.
Plan: `docs/superpowers/plans/2026-08-19-apparatus-part-a.md` (18 tasks, five batches).

Baseline at `4508ea6`: **2363 passed, 1 skipped, 2 xfailed.** Four gates clean.

## What this slice is, and the figure that does not move

`statistics.null_test` closed the `statistics` family; this opens the apparatus. **Part A observes and
records; it cannot stop a run** — the gate, `EXIT_EXTERNAL`'s reader, run-stops-here and the
truncated-plan distinction are Part B's, each routed in writing rather than left implicit.

**It unblocks zero configs.** All nine configs in the feasibility analysis earn only
`W-DATA-CLUSTER-UNDECLARED`; **six with no remaining core-side blocker, three executable, both
unmoved** — and the design's sharper point is that **the only direction this slice can move a config
count is down.** The distinction worth carrying, which the old charter collapsed: *as measured* the nine
need nothing from H7d; *as designed* their template declares a probe, and such a run today **validates
clean, exits 0, records `apparatus: null`, and never calls the probe.**

## Two things settled before any code

**The scoping was wrong about exit code 5, and the design caught it within hours.** `EXIT_EXTERNAL = 5`
ships in `diagnostics.py` with **no reader anywhere** — I confirmed it. Corrected by **appending** to the
scoping, because a scoping records what was measured on its date. It is the **second time on this project
that re-measuring a scoping the same week falsified one of its claims**; `H7b-SCOPING-2.md` lost seven.

**And the documents change before the code.** § The apparatus core can only observe sites the
declared-keys check, the credential check and the null warning **at `dry-run` only — and `dry-run` does
not exist**, so taken literally Part A would call user code once per execution with **nothing checking
that a declared key came back.** Ruling: the three become **phase-independent functions in
`apparatus.py` that every caller invokes**; no check moves *off* `dry-run`, which stops being *where
they live* and becomes *one of the places they run*. **No new command.** That is task 1, it precedes
every code task, and it touches **three files** — `experimental-designs.md` carries the same siting, and
a one-file sweep is this repo's named habit.

## The plan's corrections against the code — fourteen, eight of which reshaped a task

The plan step earned its place. The eight that changed a task's shape, in short:

- **The ledger's `condition` and `facts` keys are `<nn>_<label>`, not the bare label** the design named —
  and a **no-sweep run's label is `None`**, which neither document nor design answered. Ruled
  `f"{index:02d}"`, because canonical JSON cannot sort a `None` key.
- **Neither published mapping can supply `W-APPARATUS-UNANSWERED` at the design's grain**: `unobserved`
  aggregates over conditions, and `facts` records the *answer* for a partially answered fact — so a
  `facts`-derived warning is **silent for exactly the flaky case the null rule exists for.** Task 7 keeps
  per-(condition, fact) counts. **§ Warnings core reports was in neither the design's rows task nor its
  sweep.**
- **A probe returning a non-`Apparatus` had no refusal** — it reaches `run` as a traceback.
  `E-APPARATUS-RETURN` minted; **five codes, not four**, everywhere.
- **The design's "append after the execution" mutation cannot fail**, because a failed execution never
  stops the run, so the line is written either way. Replaced with a run-scoped count: **4 against 2.**
  That is the *a mutation is a claim too* row, caught in the plan rather than by a reviewer.
- Decision 5's value contract enforced **at core's boundary, not in `Apparatus.__init__`**, or a
  probe-body raise gets mis-coded; `E-APPARATUS-FACT-TYPE` needs catch-and-re-code because `_refuse`
  hardcodes another code; `execute_plan` **cannot supply the condition list** (plan-derived, empty for a
  `run`/`summary`-only pipeline); and `main`'s handler prints a bare `{exc}` **with no collector**, which
  fixes the containment site and narrows `APPARATUS_CODES` to the five so **every member is pinned.**

## The guard pin, chosen the way the last slice's was

**Task 18 runs first.** It asserts the full `provenance` key list, `provenance["apparatus"] is None`, and
**no `apparatus/` directory** — captured from a **real end-to-end run** at `4508ea6` rather than
transcribed from `cli.py`. Its mutation is `"apparatus": {"probe": None}`, **exactly the `probe: null`
spelling decision 7 rejects.** Tasks 11 and 12 replace what it covers, which is the point: the preceding
slice's batch-1 pin caught a spurious key three batches later without ever being edited.

## Batch 1 — tasks 18, 1, 2, 3 — the pin, the document change, `Apparatus`, dispatch

Commits `7568a34` (guard pin), `0113fce` (check-placement), `4c1c0ae` (`Apparatus` + export),
`d1590a4` (`_probe_for`). Branch `h7d-apparatus-part-a`. Suite 2363 → **2370** passed, 1 skipped,
2 xfailed; mypy 45 → 46 source files.

**The guard pin works, and it was captured rather than transcribed.** The reviewer applied the
prescribed mutation **and invented a second** — an unconditional `apparatus` mkdir — and **both failed
on assertions**. It confirmed the pin covers what tasks 8, 11 and 12 will move, which is the only reason
a pin built before the code has value.

### Review: both verdicts PASS with exceptions; three Majors, no Criticals

**The implementer reported ZERO disagreements between the briefs, the design, the plan and the code**,
and I asked the reviewer to treat that as a claim to test rather than a result to accept — `CLAUDE.md`
records **six of six implementers on a recent slice finding a real one**, and this slice's own plan made
fourteen. **The test was worth running.** Zero was right about the *code*, and wrong about the
*documents*: `apparatus.py`'s docstrings **assert § Errors rows that do not exist**, `E-APPARATUS-RAISED`
appearing nowhere but the docstring claiming it. Both were **carried from brief prose and never checked
against the documents** — the converse of *assuming a documented rule has code behind it*, and the exact
place a zero-disagreement report was weakest.

**Major 1 is this repo's named habit, twice in one finding.** The `dry-run` siting task 1 removed
**survives as a paraphrase** in the feasibility analysis — *"Resolved in § The apparatus core can only
observe: declaring the fact buys a `dry-run` warning"*, attributing the old siting to **the very sentence
task 1 rewrote**. Found by an unfiltered sweep across the four documents, `CLAUDE.md` and the analysis,
all 34 hits read. **The design's sweep named the feasibility analysis; task 1's brief named only the four
documents, and the sweep that ran followed the brief.** Recorded as a **plan defect**, not the
implementer's alone — a brief that under-scopes a sweep produces exactly one file's worth of miss.

**Major 3 is a fail-open the whole suite is blind to**: inserting `if name in PROBES: return PROBES[name]`
ahead of `_probe_for`'s metadata scan leaves the tests green, and **the decorator-only case its docstring
argues about has no fixture** — the *seam named in the brief and instantiated by no fixture* row.
Mitigating, and worth carrying rather than hiding: **`units._resolver_for` has the identical hole**, so
this is a **copied** gap, not a new class of one.

**Fix round 1 — all three Majors and five Minors closed** (`8521f69`). Suite **2371** passed, 1
skipped, 2 xfailed; four gates clean. Major 1's paraphrase now reads *"a warning, fired wherever a
probe runs"*; Major 2's undated build claim is **deleted and replaced by a pointer** to § Executability
on this build, with the reason stated in the file — *restating it here is exactly what leaves an undated
claim behind for the next slice to falsify* — which is the procedure's own step 10 turned into prose.
Major 3's decorator-only fixture now exists and fails under the reviewer's exact mutation. Minor 1's
phantom § Errors claims were **closed by deletion**; confirmed gone by grep over `src/` and
`reference.md`.

**And the fix round's own closing note was false, which is the entry worth keeping.** It reported that
`ruff format` had reformatted embedded Python fences in two `.md` files, and reverted them with
`git checkout --`. **`ruff format` does not process `.md`** — measured by copying `reference.md`,
running `uv run ruff format docs/`, and diffing: byte-identical, `git status` clean, and no
`extend-include` in `pyproject.toml`. **So the `git checkout --` was performed on a misdiagnosis.**

The outcome is sound — I verified both intended fixes by reading the committed diff rather than
trusting the report, and the gates pass. But `CLAUDE.md` names that command as destroying uncommitted
work *"twice mistaken for reverting a mutation"*, and **this is the third instance and the first whose
justification was itself wrong.** **Flagging it is why it was caught**, and the rule it sharpens is
narrower than *don't use it*: **a revert is verified by behaviour, never by `git status`, and least of
all by a story about what caused the change.** Keeping a copy before mutating removes the need for a
diagnosis at all.

## Batch 2 — tasks 4-8 — every check and the ledger, and not one call site

Commits `c330c67` (invocation and the contained raise), `899f657` (the `apparatus_facts` projection —
**closing the unbuilt-reader-of-a-shipped-surface defect this attribute has carried for three slices**),
`5e45ca4` (credential refusal), `48b50c8` (null semantics and the unanswered warning), `f1be329` (the
ledger), report `6df82fe`. Suite 2371 → **2392**.

**The implementer caught two prescribed mutations that could not discriminate**, which is the
*a mutation is a claim too* discipline working before a reviewer had to supply it: task 6's
`len>=20 or (digit and isalnum)` heuristic **also flags the fixture `lab7`**, so it could not be told
from the equality check; and task 7's mutation (c) is 4-against-3 on this batch's fixture rather than
the brief's 8-against-3, a figure belonging to a fixture **not yet built**. The reviewer re-derived every
number by running and confirmed both adjudications — calling the first *"correct and understated"*.

### Review: spec compliance FAILS on one point; four Majors

**The pattern is the same in all four, and it is the entry worth keeping: the batch diagnosed correctly
and then left the falsified claim standing in the committed code.** Three tests assert "no heuristic
flags lab7", "six observations", "eight" and a fixture that does not exist — **all contradicted by the
implementer's own report, which was right.** The numbers are fixture-derived and correct; the prose
around them is false. That is *a test whose docstring claims a guarantee no assertion makes*, and **a
reader greps for exactly that claim and stops looking** — the seventh instance on this project.

**The spec failure is a brief defect first.** `warn_unanswered` fires `W-APPARATUS-UNANSWERED` for an
**undeclared** fact that came back `null`, against decision 8, decision 4's fourth row and `reference.md`
— and **task 7's brief prescribes the signature `warn_unanswered(self, c: Collector)` with no `declared`
parameter**, so the rule could not be expressed in the shape the plan handed over. No fixture separated
the readings either. **Ruling: fix the behaviour, build the separating fixture, and record the brief
defect** — a seam a brief cannot express is the plan's fault.

**And the highest-stakes check in the batch is pinned by a test whose loop body never runs.** The
credential check cannot distinguish exact-value matching from a pattern: the brief's own heuristic
mutation leaves the **full suite green**, because the one test that would separate them passes
`credentials={}` — **so the loop never executes.** The missing cell is decision 6's own ground: a
non-empty `credentials` beside a credential-shaped value that is not a declared credential. **This repo
has shipped this exact class of leak twice**, which is why it is a Major rather than a Minor.

One real escape found: comparing `value == cred_value` on the **raw** value lets a numpy-array fact out
as an **uncoded `ValueError`** — but **only when a credential is declared**, which is the worst shape for
a conditional fault, since the `credentials={}` path is correctly coded and would be what a casual test
exercises.

**Fix round 1 — all four Majors and five Minors closed** (`c04d12d`, `6dbc8c8`), each verified by
running. Suite **2395** passed, 1 skipped, 2 xfailed; four gates clean; **still no call site** —
confirmed by grep for every new name outside `apparatus.py`, and `cli.py` still writes
`"apparatus": None` unconditionally, which is what batch 4 replaces and what the guard pin covers.

**The credential pin now exists, and the proof is the number that changed.** The review's exact
heuristic mutation previously left the suite at **2392 passed with zero failures**; against the new
third cell — non-empty `credentials` beside a credential-shaped value that is *not* a declared
credential — it now gives **1 failed, 2394 passed.** That cell is decision 6's own ground, and it was
the one shape no test instantiated. **This repo has shipped this class of leak twice; this is the pin
that prevents the third.**

**Major 2's fix was verified by reproducing the original bug rather than by trusting the guard.**
Removing the `isinstance(value, str)` guard again gives `E-APPARATUS-FACT-TYPE` under `credentials={}`
and an **uncoded `ValueError`** under a declared credential — the conditional shape being the whole
finding, since the easy path is the one a casual test exercises.

Two Minors were **filed rather than fixed**, both deliberately. A fact **key** equal to a credential
value is a real narrowing question on decision 6's scope, filed **unassigned with the reason** rather
than the forbidden vague-owner form. And the ordering between `append_observation` and `check_facts`
is **hand-forwarded to batch 3 in both a docstring and a filing** — batch 3 being the first caller of
both, so it is the first position from which the question can be answered rather than guessed.

## Batch 3 — tasks 9, 10, 15 — the first batch where a real `run` calls user code

Commits `d645b0d` (the run-start round and a probe failure as a redacted diagnostic), `64f343f` (a probe
before every execution), `6d828e7` (the call-count contract), report `f912bce`. Suite 2395 → **2402**.

**The ordering handed forward from batch 2 was ruled and closed:** `check_facts` runs **before**
`append_observation`, so a credential-carrying fact is refused **before a byte reaches the ledger** —
verified by running, with the first condition's line on disk and the second refused.

### Review: BOTH verdicts FAIL, on a Critical — a credential leak at `run`, the third of its class here

**`_probe_for` sat OUTSIDE the containment `try`.** A probe entry-point module raising at import with a
declared credential in its message printed it **straight to stderr**, verified by running. Reachable on
**the first run of an unchanged machine**, because `validate._check_probe` reads metadata only and never
loads — so `E-PLUGIN-LOAD`/`E-PLUGIN-DECORATOR` get **no verdict from `validate` at all**.

**The tell is that the identical fixture through a resolver IS redacted**, because `_resolver_for` sits
inside `command_run`'s roster wrapper. Same shape, one line's difference in placement — which is the
whole reason this class keeps recurring.

**And the reasoning failure is the entry worth keeping.** The exclusion rests on **the plan's own
correction 10**, whose ground is *"no fixture in this plan reaches it and none easily can"* — **a
three-line fixture falsifies it**, and the batch wrote **two comments** from that claim without testing
it. `CLAUDE.md`: *a safety argument in a comment is a claim needing a mutation.* **So the plan asserted
unreachability, the implementer inherited it, and neither made it happen** — the same division of labour
that produced the previous two leaks. It also makes a `spec-defects.md` sentence — *"the demonstrated
path into it is closed"* — **false**.

**Major 2 is the unpinned-membership shape:** deleting **three of five** `APPARATUS_CODES` members
together leaves the full suite at **2402 passed, unchanged**, under a docstring asserting all five are
pinned. All three *are* reachable at `run` — the reviewer built three end-to-end runs — so the narrowing
was correct and only the pinning was absent. **Minor 5's redaction rests on that membership**, which is
why an unpinned enumeration is not a cosmetic finding.

**Major 4: the substituted assertion cannot fail.** Restricting the reconstruction to `run_start` lines
leaves the test passing, because it iterates the whole ledger and those lines already carry both keys —
**and it never reads `run.yaml`, so it will not begin failing when task 11 lands**, which was the exact
risk the deviation was accepted against.

**Deviation 2 is vindicated, and recorded as such:** the reduced fixture does **not** mask the mixed
case, because task 15's test uses a mixed plan. But decision 3's *motivating* case — a `summary`-scoped
execution — **is in no fixture**; the reviewer built it (`C=3, E_c=6, E_none=1` → **12** lines, summary
probed once per condition, last) and the rule holds.

**Fix round 1 — the Critical is closed and PINNED** (`f98ff7f`, `5cec0c3`), confirmed by an independent
rebuild rather than by trusting the report: a fresh reviewer built its **own** template, credential and
raising probe module and drove them through the real `main(["run", ...])`. The credential appears
**nowhere** on stdout, stderr, or any file under the project tree, and the diagnostic prints
`RuntimeError('cannot reach vault, secret=<redacted:PUBLISHABLE_RR_TOKEN>')` under `E-PLUGIN-LOAD`.
**It also covered a `SystemExit`-at-import shape the fix's own tests do not** — also redacted. Reverting
the containment fails a named test on its assertion. Dispatch sites were enumerated **by reading first,
grep after**: `_probe_for` has exactly one caller, the unbuilt commands exit before anything, and
`command_validate` never loads. Suite **2409**.

**Major 4's rebuild was proven to discriminate the right way**, which is worth recording as a method: the
reviewer mutated `_observe_one` and confirmed the new assertion fails, **then re-ran the same mutation
against the pre-fix reconstruction and watched it pass vacuously.** A rebuilt assertion is only witnessed
by showing the old one would not have caught it.

**Three items stayed open after round 1, and all three are the repo's own recurring shape — a correct
fix shipped unpinned.** The `KeyboardInterrupt` branch added by the Critical's own fix propagates
correctly (`args == ()`, no message) but **deleting it leaves the suite green**, because the existing KI
tests cover the *resolver* path and `observe_once`'s, **not this new dispatch site**.
`E-APPARATUS-FACT-CREDENTIAL` is an unpinned member of `APPARATUS_CODES` — not a latent leak, since its
message carries the credential's *name* and the fact *key* and never the value, but an enumeration with
one free member is exactly what Major 2 was about. And the decorator test **passes with the containment
fully reverted**: its docstring claims it proves routing, while it pins only the `exc.code` passthrough —
*a test whose name claims the guarantee*, with a one-line fix available using **a helper the same commit
already added.**

**One regression introduced while closing a Minor:** the round that removed four positional locators
**added four more**, one of them in shipped source prose. Locators have been wrong twice here in rows no
diff touched, which is why the rule is to name what a sibling *does*.

**Fix round 2 — all three unpinned items closed** (`f67cbfd`, `1ed3cd8`), each by a mutation that failed
before and passed after, plus the four positional locators round 1 had introduced. Suite **2410**
passed, 1 skipped, 2 xfailed; four gates clean. **Batch 3 complete** — the first batch where a real
`run` calls user code, and the batch that produced this slice's only Critical so far.

## Batch 4 — tasks 11, 12, 13 — the record

Commits `e833070` (`provenance.apparatus`'s five sub-keys, **replacing `cli.py`'s unconditional
`"apparatus": None`** — the OPEN filing this slice was named to close), `e36b5b3` (the fingerprint),
`c8ecd83` (publishable-as-is), report `ec16254`. Suite 2410 → **2417**.

**The guard pin held, and held without being touched.** `tests/test_cli.py` has **zero deleted lines**
across the batch and `cli.py` exactly **one** — the literal `None` this slice existed to remove — and the
pin's body is **byte-identical to its capture at `7568a34`.** It stayed green because template `generic`
declares no probe, which is the state it was built to hold, so tasks 11 and 12 **added a second state
beside it rather than replacing it.** Re-verified still discriminating under the rejected `probe: null`
spelling. That outcome is the argument for capturing a pin from a real run before the code exists: the
one I expected to have to argue about updating needed no update at all.

**Ruling on the task 11/12 split, which the reviewer correctly said was owed a ledger line.**
`apparatus_hash` was written in **task 11's** commit, because `Observer.block()` cannot produce a `hash`
key without it, leaving **task 12's commit tests-only** (confirmed: `e36b5b3` adds no production code).
**That is the right split and it was disclosed rather than hidden.** The alternative — a `block()` that
omits `hash` for one commit — would have shipped a record shape no decision describes, and the guard pin
asserts a **key list**, so an intermediate shape would have had to be pinned and then unpinned. **Cost if
wrong:** a task boundary that does not match a commit boundary, which the report states plainly.

### Review: spec compliance PASS, task quality PASS with findings — all prose, none behavioural

Decisions 7, 8 and 10 verified **by running**: the three record shapes (no probe → whole block `null`; a
probe returning nothing → five sub-keys with `unobserved: {}`; a raise → no `run.yaml`), no new
absent-vs-`null` convention minted, **the hash is not a fourth hash** (`hashes.py` untouched slice-wide,
`HASHED_TREES` unchanged), `sort_keys` genuinely load-bearing **and non-blind** because the fixture
inserts `zeta_field` before `alpha_field`, and `warn_unanswered`'s new caller correct on all four
properties — the **fresh** `Collector` proven by a second render printing "3 problems" rather than 4.

**The Major is the third instance of one pattern on this project: a "zero disagreements" report falsified
by a claim carried from a brief and never checked.** A docstring asserted its row was one "which no other
test reaches" — three tests in `test_apparatus.py` reach it, dated by `git log -S` to tasks 5 and 7. The
transferable form: **a brief's prose about other tests is a claim about the code, and it is checkable by
grep.** A second, milder divergence went unreported in the same batch — a docstring claiming a sweep was
"sliced out of `run.yaml`" where the body sweeps the whole file, which is the harmless direction and
still a divergence.
