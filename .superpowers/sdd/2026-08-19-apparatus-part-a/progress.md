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

**Fix round 1 — the Major and all six Minors closed** (`e636f15`, `2ce5efa`), every one by deletion,
rename or correction with **no behaviour changed**; suite unchanged at **2417**. The false "no other test
reaches" clause is deleted rather than rewritten, the misleading test name now says what it asserts, and
the report's disagreement count is **corrected from zero to two, both named** — which is the outcome that
makes the pattern visible instead of buried.

## Batch 5 — tasks 14, 16, 17 — the guards, the rows, the filings

Commits `5fc26fa` (`validate` calls no probe, pinned by a probe that **writes a flag file and raises**,
so the guard's failure is observable on disk rather than inferred), `80c2b2c` (one row per code — the
five `E-APPARATUS-*`, `W-APPARATUS-UNANSWERED`, and `E-PROBE-UNKNOWN` restated **dual-surface** as one
row), `e15c474` (two filings struck, one amended, `EXIT_EXTERNAL` filed against Part B), report
`48bc9e2`. Suite 2417 → **2418**.

**The batch found a genuine under-description the brief did not name**, and it is the misreading
`CLAUDE.md` calls *scoping a diagnostic by the helper it calls*: the existing `E-PLUGIN-LOAD` and
`E-PLUGIN-DECORATOR` rows described their reach as only *"a resolver source's dispatch"* — but
`apparatus._probe_for` now dispatches through **the identical functions**. Both rows were extended with
the probe case's asymmetry (dispatched at `run`, never at `validate`). **That is the same asymmetry this
slice's Critical came from**, now written down where a reader will find it.

**And it caught two of its own citation errors before committing** — mis-attributing the `EXIT_EXTERNAL`
measurement to the design when it lives in the plan's § Corrections, and omitting Part B's task from the
citation — **by re-reading the cited sections rather than trusting the first draft.** Disclosed rather
than quietly fixed, which is the convention this slice has been held to throughout.

## Independent whole-branch review: MERGE with items owed — no Critical, three Majors

**I am holding the merge on Major 2 anyway**, because it is a credential in a published artifact.

**Major 2 — a fact value *containing* a declared credential is published verbatim.** `check_facts`
matches by **exact equality** while `secrets.redact`, over the **identical value set**, matches by
**substring**. Verified by running: a probe returning `"endpoint": ".../?key=" + token` gives **exit 0,
no diagnostic, and the raw token in both `run.yaml` and `probes.jsonl`** — the two artifacts the
documents call *publishable as-is*. Core credential-checks **nothing else it records**, so this block is
precisely where the stronger match belongs. **Fourth instance of this class here, and the first where the
two mechanisms disagreed with each other rather than one being absent.**

**Major 1 — a non-`str` `apparatus_probe` silently reads as "no apparatus", at BOTH surfaces.** A
template declaring `apparatus_probe = ["wbr_probe"]` — plausible, since `apparatus_facts` beside it *is*
a list — is skipped at `validate` **and** at `run`, with `validate` reporting nothing. **The fail-open
predates this branch** (H7b Part A) **but had no observable consequence until task 11 gave
`apparatus: null` a meaning** — so a latent fail-open became a silent wrong answer the moment the record
key became real. It is line for line the reproduction in **a filing this slice struck**. Two guards, two
files, two batches: **the seam class no per-batch review could reach**, which is the argument for the
whole-branch gate existing at all.

**What the gate confirmed sound, by running:** the call-count contract on its own fixture (C=2, E_c=4,
E_none=2 → **10** lines, recomputed before the run, asserted as an ordered `(phase, condition)` list);
the hash **not** a fourth hash (`hashes.py` absent from the whole diff, `HASHED_TREES` unchanged);
**Part A provably cannot stop a run** — a mid-plan raise gives exit 1, never 5, no `run.yaml`, no
`status:` byte, `latest` uncreated, the ledger's lines preserved; the null accounting and
`W-APPARATUS-UNANSWERED` printed **exactly once**; the redaction path for a probe raising **at import**;
**the guard pin byte-identical to its capture and still discriminating**; **zero deleted test lines
branch-wide**; and E1 and C1 re-measured through `validate_config` with a can-fail control —
**zero, six and three all unmoved.**

**Fix round — Majors 1-3 closed, Minors 1-2 closed, Minor 3 noted** (`06bc38d`, `0f29b8a`,
`eafb222`, plus the CLAUDE.md amendment). Suite 2418 → **2423** (five new tests, four end to end
through `main(["run", ...])`, one direct-call). Every fix verified by reverting to a saved pre-fix
copy, re-running to confirm the reproduction, then restoring and re-confirming green — never by
`git checkout -- <file>`.

**Major 2 closed.** `apparatus.check_facts`'s credential check now matches by containment
(`cred_value and cred_value in value`), the same way `secrets.redact` already matches over the
identical value set, rather than exact equality alone. Pinned direct-call
(`test_a_fact_value_containing_a_declared_credential_is_refused`,
`test_the_containment_refusal_also_names_the_variable_and_never_the_value` — the message still
names the fact key and the credential's name, never the value) and end to end
(`test_a_fact_value_containing_a_declared_credential_fails_the_command_end_to_end`): reverting the
fix reproduces the review's exact finding, a different code even (`E-APPARATUS-FACT-MISSING`, since
the fixture's probe doesn't return the declared key `model_revision` at all — the credential check
never runs before that other refusal fires, which is itself evidence the containment check is what
closes the gap rather than an unrelated fixture accident). `reference.md`'s
`E-APPARATUS-FACT-CREDENTIAL` row now says "exact value or substring containment."

**Major 1 closed at the one place both surfaces share.** `validate._check_probe` now reports
`E-PROBE-UNKNOWN` for any `apparatus_probe` that is not `None` and not a usable non-empty `str` —
`None` stays the sole spelling of "no probe declared." Since `command_run` calls `validate_config`
first and returns before ever inspecting `apparatus_probe` when `c.has_errors`, this closes `run`'s
copy of the same silent skip without touching `cli.py`'s own guard, which becomes the harmless
belt-and-braces the review says it reads as. Pinned direct-call
(`test_a_non_str_apparatus_probe_is_reported_rather_than_silently_skipped`) and end to end
(`test_a_non_str_apparatus_probe_fails_the_command_before_any_run_directory_exists` — reverting the
fix reproduces the review's exact finding: exit 0, `run.yaml` written, `apparatus: null`).

**Major 3 closed.** A dated entry, "Measured on 2026-08-19 against commit `06bc38d` — after H7d
Part A," added to `feasibility-llm-growth-studies.md` § Executability on this build — the section
batch 1's rewrite pointed at and that said nothing about the apparatus at any date. States the
zero/six/three figures (re-cited from this review's own re-measurement rather than re-run a third
time on an identical fixture) and the honest statement of what changed: a probe-declaring run would
now record five real sub-keys and could newly earn one of five codes or one warning, none of it
exercised by these nine configs since none declares a probe a real plugin backs.

**Minor 1 closed.** One sentence in § The apparatus files: a no-sweep run's condition key is `"00"`,
the same `<nn>_<label>` scheme with an empty label — a record value the code already produced and no
document had named.

**Minor 2 closed.** `experimental-designs.md`'s apparatus row named three probe placements
(`dry-run`, run start, before every execution); `reference.md` names four, `freeze` included, since
task 1's re-siting. Fourth added. The identical three-place enumeration in the feasibility analysis
is correctly left — that file is exempt from the cross-document pass.

**Minor 3 noted, not fixed, because there is nothing to fix.** Task 16's report read § Validation's
"Probe is installed" row, confirmed it unchanged, and said so — correctly: every check this slice
adds needs a call, and § Validation is the table of checks that don't. `reference.md`'s own "Six
things deliberately absent from that table" paragraph already states this for the apparatus
generally ("whether the apparatus is reachable is checked by `dry-run`" / "a probe is metered by
somebody else"). Recorded here so a later reader does not re-file "no `E-APPARATUS-*` § Validation
row" as a missing row: **none is owed**, and this is the fact, not a filing.

**Minor 4 (batch 5 unreviewed) is closed by the whole-branch review itself**, which reviewed all
three of batch 5's tasks directly rather than as a seam check and found them sound.

Four gates clean at every commit in this round. Full `uv run pytest`: **2423 passed, 1 skipped, 2
xfailed.**

**Whole-branch fix round — both Majors fixed, and then I found one of the fixes unpinned.**

Commits `06bc38d` (Majors 1 and 2, Minors 1-2), `0f29b8a` (the dated § Executability entry),
`eafb222` (`CLAUDE.md`), `69c7ced`, `edd2244`. Suite **2423**.

Major 2's fix matches **the way `redact` already matches** rather than inventing a third rule, which was
the constraint that mattered: two mechanisms over the same value set disagreeing is what produced the
leak. Major 1 is fixed at `validate._check_probe`.

**Then, checking a claim rather than accepting it, I mutated Major 1's guard away and the full suite
stayed green at 2423.** Replacing `if not isinstance(declared, str) or not declared:` with `if False:`
changed **nothing** — so the behaviour was right and **the protection was asserted by nothing.** Reverted
by editing the line back, confirmed byte-identical against a pre-mutation copy.

**What prompted the check is worth recording, because it generalizes.** The `CLAUDE.md` paragraph the
same round wrote says the fix lands *"at the one place both surfaces share … which is also what closes
`run`'s copy of the same guard without touching it, since `command_run` validates first."* **That is a
safety argument in prose**, and this repo's rule is that such a claim needs a mutation. The claim may
well be true; it was **argued rather than asserted**, and the argued form is what this branch's Critical
came from. **Ruling: pin both surfaces separately — `validate` and a real `run` — and if the `run`-level
assertion cannot be made to fail, delete the sentence rather than rewrite it.**

**This is the fourth correct-but-unpinned fix on this branch alone** — batch 3's `KeyboardInterrupt`
carve-out, three `APPARATUS_CODES` members, and now this — **every one found by mutation after being
reported closed, and none by reading.** `CLAUDE.md` already counts five such across three prior slices.
The rule earns its place: **verify by probe, then pin by mutation**, and a report saying "closed" is the
beginning of that sentence rather than the end.
