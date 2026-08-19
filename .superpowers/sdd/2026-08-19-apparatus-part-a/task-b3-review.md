# H7d Part A batch 3 review — tasks 9, 10, 15

**Reviewed at `f912bce`** (branch `h7d-apparatus-part-a`), 2026-08-19. Every claim below marked
*verified by running* was produced by an end-to-end `run` through `main(["run", ...])` in a
throwaway test module built for this review, or by a mutation run against the committed suite.
Claims marked *read* were not executed.

## Verdicts

**Spec compliance: FAILS.** Decisions 2, 3, 4, 7, 9 are implemented as ruled and were verified by
running (see § What holds). What fails is the plan's § Corrections against the code, correction 10,
and the two comments task 9 wrote from it: the exclusion of `E-PLUGIN-LOAD` and
`E-PLUGIN-DECORATOR` from the containment filter rests on an explicit, falsifiable measurement
claim — *"no fixture in this plan reaches it and none easily can"* — and a three-line fixture
falsifies it. Decision 6 is why that matters rather than the rule it breaks: the consequence is a
declared credential on stderr, un-redacted, at `run`, in the slice whose design says *"This exact
class of leak has now been found twice … Part A must not make it three."* Finding **Critical 1**.

**Task quality: FAILS.** Three of the five `APPARATUS_CODES` members can be deleted with the full
suite staying green while the set's own docstring asserts *"the set stays five, every one pinned"*
(Major 2); task 10's substituted assertion does not witness the property it was substituted for
and cannot fail (Major 4); and `append_observation`'s docstring still instructs batch 3 to make a
ruling batch 3 already made (Major 3). The three tasks' *behaviour* is right; the evidence for it
is weaker than the report claims in three places.

Gates at `f912bce`, run directly: `uv run ruff check .` → All checks passed; `uv run ruff format
--check .` → 82 files already formatted; `uv run mypy` → Success, 46 source files; `uv run pytest`
→ **2402 passed, 1 skipped, 2 xfailed**. Matches the brief. **Tree left clean** (`git status
--porcelain` empty; the review's temporary test module was deleted, `src/publishable/apparatus.py`
and `tests/test_cli.py` restored from pre-mutation copies and re-verified by behaviour, never by
`git checkout`).

---

## Findings

### Critical 1 — a probe plugin's dispatch failure reaches `main` un-redacted, and leaks a declared credential

**File:** `src/publishable/cli.py:2411` (`probe=apparatus._probe_for(declared_probe)`, deliberately
outside the `try` opened at `cli.py:2419`); justified at `cli.py:2396–2405` and at
`src/publishable/apparatus.py:373–382`.

**Verified by running.** A project-local template declaring `required_env =
["PUBLISHABLE_TEST_TOKEN"]` and `apparatus_probe`, `_env_file="PUBLISHABLE_TEST_TOKEN=lab7"`, and an
installed distribution whose probe entry-point **module raises at import** carrying that value.
`validate` reports nothing (the name is registered), the run reaches the lock, `_probe_for` calls
`load_entry_point`, and stderr prints:

```
  error   E-PLUGIN-LOAD        the entry point `rev_cred_probe` in `publishable.probes`, from
  dist-revl 1.0, raised while importing and registers nothing usable:
  RuntimeError('plugin import failed near token lab7')
```

`lab7` present in stderr; exit `EXIT_WRONG`.

**The exclusion has no ground — this is the disqualifying fact.** Both `cli.py:2396–2405` and
`apparatus.py:373–382` argue the dispatch codes are outside the filter because *"reaching the
wrapper with a dispatch code would need the installed set to change between `validate` and the
lock, which no fixture in this plan reaches"* (plan § Task 9 and § Corrections, correction 10, say
"and none easily can"). **Read:** `validate._check_probe` (`src/publishable/validate.py:953`)
answers from `scan_group` metadata only and never calls `EntryPoint.load()`. So `validate` computes
**no** verdict about `E-PLUGIN-LOAD` or `E-PLUGIN-DECORATOR`, and neither needs the installed set to
change — both fire on the first `run` of an unchanged machine. **Verified by running:**
`E-PLUGIN-LOAD` as above, and `E-PLUGIN-DECORATOR` from a module registering under a different name
(that one carries no credential, but escapes to `main` the same way). The claim was answered from a
proxy — *what does `_check_probe` scan* — rather than from *what can `load_entry_point` raise*,
which is the substitution `CLAUDE.md` § Answering a question with a proxy describes.

**The same fixture through a resolver is redacted**, verified by running it against
`data.units.from.resolver`: `RuntimeError('plugin import failed near token
<redacted:PUBLISHABLE_TEST_TOKEN>')`. The difference is placement — `units._resolver_for` runs
inside `resolve_units`, which `command_run` already wraps in the `except BaseException` roster
block that binds `credentials` onto a fresh `Collector`. So the parity the comment claims with
"every other pre-existing core-inconsistency path" does not exist; the resolver path is redacted
and the probe path this batch added is not.

**A consequence in the record:** `docs/superpowers/spec-defects.md:6195`'s OPEN entry on `main`'s
last-resort handler says *"The demonstrated path into it is closed."* That sentence is false at
this commit — batch 3 built a new demonstrated path with a declared credential in it. The filing's
claims went stale in the batch that made them stale.

**Route, not prescribed:** either move `_probe_for` inside a redacting wrapper (the resolver path's
own shape, `except BaseException` with a fresh credential-bearing `Collector`), or admit the two
loadable dispatch codes into the filter. `E-PROBE-UNKNOWN` genuinely *is* pre-answered by
`_check_probe` and can stay outside on that ground alone.

### Major 2 — three of the five `APPARATUS_CODES` are unpinned, under a docstring asserting all five are

**File:** `src/publishable/apparatus.py:364–382`.

**Verified by mutation, full suite, foreground.** Deleted `"E-APPARATUS-RETURN"`,
`"E-APPARATUS-FACT-TYPE"` and `"E-APPARATUS-FACT-MISSING"` from the frozenset → `uv run pytest` →
**2402 passed, 1 skipped, 2 xfailed**, byte-identical to baseline. Reverted by editing back and
re-confirmed. **All three are individually unpinned, not merely one of them:** had any single
member's deletion been caught, the combined run would have gone red. It stayed green, so no test
in the suite can see any of the three memberships. The docstring's *"the set stays five, every one
pinned"* and the plan's *"every member of it is pinned by a test in this plan"* are therefore both
false for three of the five. This is the
exact shape the docstring's own preceding sentence warns about, one clause earlier.

**All three are genuinely reachable at `run`** — verified by running three separate end-to-end runs
with a probe returning, respectively, a bare `dict` (`E-APPARATUS-RETURN`), an `Apparatus` whose
fact value is a list (`E-APPARATUS-FACT-TYPE`), and an `Apparatus` omitting a declared fact
(`E-APPARATUS-FACT-MISSING`). So nothing unreachable was included; what is missing is any test that
can see the *membership*. The reason nothing catches it: `main`'s handler also returns `EXIT_WRONG`,
so the only observable differences are the diagnostic's rendered shape and **whether it is
redacted** — and the three existing tests for these codes are direct calls to `check_facts` in
`tests/test_apparatus.py`, which never reach the filter at all. A direct-call test of a call site is
a test of a proxy, which is what this batch's review was scoped to catch.

This interlocks with Minor 5: the redaction of `E-APPARATUS-FACT-TYPE` is the only thing that keeps
the credential-as-fact-key case from being a live leak, and that redaction is unfailable.

### Major 3 — `append_observation`'s docstring still asks batch 3 to make a ruling batch 3 made

**File:** `src/publishable/apparatus.py:344–349`. **Read at HEAD**, both texts present in the same
module: `append_observation` says *"**No ordering is ruled here against `check_facts`.** … Batch 3,
which owns the first call site, must either call `check_facts` before this function or the gap is
`spec-defects.md`'s to carry with batch 3 as owner"*, while `Observer` (`apparatus.py:396–404`)
rules exactly that and `spec-defects.md:7012` records it as CLOSED. A reader of
`append_observation` alone is told an open question is open.

`CLAUDE.md`: *prefer deleting a claim to rewriting it.* The paragraph should be **deleted**, not
reworded — the ordering now has a ruling, a call site and a pin, and none of them lives in this
docstring.

### Major 4 — task 10's substituted assertion cannot fail, and will not start failing when task 11 lands

**File:** `tests/test_cli.py:13213–13220`, inside
`test_a_condition_less_execution_is_probed_once_per_condition`.

The deviation itself is **correctly reasoned** — `provenance.apparatus.facts` is task 11's and
`cli.py` still writes `"apparatus": None`, so the brief's assertion would fail on task 11's absence.
The substitute is what fails. `facts_first_answered` is built by iterating **the whole ledger**,
`run_start` lines included, and those already carry both condition keys with a non-null
`model_revision`. So the final `for condition_key in expected_keys: assert (condition_key,
"model_revision") in facts_first_answered` is implied by task 9's behaviour and says nothing about
task 10's.

**Verified by mutation:** restricting the reconstruction loop to `phase == "run_start"` — i.e.
discarding every `pre_execution` line the test exists to check — leaves the test **passing**.
Reverted by editing back and re-confirmed. It is also not the substitution the docstring claims:
because it never reads `run.yaml`, it will keep passing after task 11 lands whatever `block()`
writes, so it does not stand in for the assertion it replaced.

The property is in fact pinned, by `assert pre_execution_conditions == expected_keys` on the line
above — an assertion implied by another in the same test, `CLAUDE.md`'s named shape. Either delete
the reconstruction, or make it read only `pre_execution` lines (which would then discriminate).

### Minor 5 — the OPEN filing minted in this batch describes a leak that this batch's own wrapper redacts

**File:** `docs/superpowers/spec-defects.md:7034` ("a fact **key** equal to a credential value …
reaches a diagnostic via `coerce_scalars`'s `{key!r}`").

**Verified by running.** A probe returning `Apparatus(facts={os.environ["PUBLISHABLE_TEST_TOKEN"]:
[1, 2]})` under a declared credential produces:

```
  error   E-APPARATUS-FACT-TYPE experiment_type
          probe `rev_cred_probe` gave '<redacted:PUBLISHABLE_TEST_TOKEN>' a list; …
```

`lab7` appears in no byte of stdout, stderr, or any file under the results directory. The entry's
sentence *"reaches a diagnostic with that credential in the message"* is true of the exception
object and false of the diagnostic, because `E-APPARATUS-FACT-TYPE` is inside `APPARATUS_CODES` and
`probe_c.credentials` redacts at render. The filing's *substance* — that Decision 6 checks values
and not keys — stands and is worth keeping; the leak claim should be corrected to say the value is
redacted at `run`, **and that the redaction rests on a set membership no test can see** (Major 2).

### Minor 6 — Decision 3's motivating case, a `summary`-scoped execution, is witnessed by no fixture

Decision 3's whole argument is that *"a `summary`-scoped execution runs after every
condition-bearing execution, so under any narrowing the most recent observation preceding it can be
hours old."* Every fixture in this batch uses `run` scope for its condition-less execution.

**Verified by running that the rule does hold there**, off the one tested point in two directions at
once: `sweep.grid` over three levels (`C = 3`), `replication.repeats` `[{kind: seed, n: 2}]` with
the scaffolded `repeat`-scoped step (`E_c = 6`), and one extra step whose `extra_step_source`
declares `scope = "summary"` (`E_none = 1`). Recomputed expectation `C + E_c + C × E_none = 3 + 6 +
3 = 12`; observed **12** ledger lines, the summary execution's `condition` is `None` in
`executions.jsonl`, it runs last, and it is probed once under each of the three conditions with each
condition's own swept value. A second shape (three levels × two repeats × three `repeat`-scoped
steps, `E_none = 0`) gave the predicted 21. The contract is right; it is the fixture set that stops
one case short of the case the decision argues from.

**On the reduced-fixture deviation the report raises: it does not mask the mixed case.** Task 15's
test uses a genuinely mixed plan (a `repeat`-scoped starter plus a `run`-scoped extra) and asserts
the ordered pair list, which separates "condition-less once per condition" (6) from the skip
narrowing (4) and from the wide-cfg reading (5, with a `null` condition). The reduction is a
reasonable choice for task 10's two tests. Two configs would have removed the need for it entirely,
and either is worth adopting for task 11's Fixture N: a **`summary`**-scoped extra step, whose
lines land last and are positionally attributable; or a probe keeping a call counter in a file
beside its module and returning it as a fact, which makes **every** ledger line distinguishable
from every other — used throughout this review and it works.

### Minor 7 — `Observer.warn_unanswered` ships with no caller and no test

`src/publishable/apparatus.py:461–465`. Grepped `src/` and `tests/`: the only reference is its own
definition; every test exercises `Observations.warn_unanswered` directly. Its call site is task 11's
step 2. Harmless and scheduled, but it is one more member of the shipped-but-unread set the same
module's `APPARATUS_CODES` docstring files against.

### Minor 8 — positional locators in new prose, which the plan's Global Constraints forbid

`src/publishable/runner.py:529` ("`conditions_list` **below**"), `src/publishable/cli.py:2397,2401`
("the run-start round just below", "the `try` below"), `src/publishable/apparatus.py:404`
("`_observe_one` below"). Each names an identifier, so none is as brittle as a table-row locator,
but the plan's rule is stated without that exemption. Naming what the sibling *does* costs nothing
here.

---

## What holds — verified by running, not read

- **Decision 2, run start is one call per resolved condition, under `resolve_condition_cfg`.** A
  three-condition run produced exactly three `run_start` lines, one per condition key, each
  carrying its own swept `instrument.model` value. `cfgs[-1]` is read nowhere in `apparatus.py`.
- **Decision 3, the call-count contract `C + E_c + C × E_none`.** Recomputed by hand and confirmed
  on three configurations beyond the suite's — `(C=3, E_c=18, E_none=0) → 21`, `(C=3, E_c=6,
  E_none=1 summary) → 12`, and the suite's own `(2, 2, 1) → 6`. Every candidate reading in the plan's
  table is separated by the observed ordered `(phase, condition)` pair list on the summary fixture
  as well.
- **The ordering ruling, `check_facts` before `append_observation`.** A two-condition run whose probe
  returns the credential **only under the second condition** left `probes.jsonl` holding exactly the
  first condition's line, no `run.yaml`, and `lab7` in no byte of any file. Pinned, too: reversing
  the two calls in `_observe_one` makes
  `test_a_probe_returning_a_declared_credential_fails_the_command_and_writes_no_run_yaml` fail on
  the ledger's raw text. The `spec-defects.md` filing is struck in the house form
  (`## CLOSED by …`, with a **Ruled:**/**Closed by:** line), matching the other CLOSED entries.
- **Redaction of a probe that raises, at every phase the wrapper covers.** Redacted at the run-start
  round (the committed K2 test) and — verified separately here — at a `pre_execution` round
  **mid-plan**, inside `execute_plan`: `probe … raised RuntimeError: instrument unreachable, token
  <redacted:PUBLISHABLE_TEST_TOKEN>`, with `lab7` absent from stdout, stderr and every artifact.
- **Enumeration of the sites a probe exception can reach a stream, by reading first:**
  `Observer._observe_one` → `observe_once` (builds the message, does not print) → `execute_plan` or
  the run-start round → `command_run`'s wrapper (redacts) → `main`'s `PublishableError` handler
  (does not, `cli.py:3698`) → `main`'s `OSError` handler (irrelevant here) → an uncaught
  `KeyboardInterrupt`, re-raised fresh and argument-less. Confirming greps ran after that reading,
  not before. The one site the reading turns up as reachable-and-unredacting is Critical 1.
- **No count moved.** Grepped the whole batch diff for `unblock`, `executable`, and the
  zero/six/three figures: no occurrence. `CLAUDE.md` and the four documents are untouched by this
  batch.
- **Mechanical pass on the one document touched** (`spec-defects.md`, development record): no added
  line carries trailing whitespace, a tab, or a bare `x` where `×` is meant; the two new headings
  are unique.

## What I could not check

- **Whether `validate` can reach Critical 1's leak — answered, not left implied.** Grepped every
  `load_entry_point` call site in `src/publishable/`: exactly two, `units._resolver_for` and
  `apparatus._probe_for`, and `_probe_for`'s only caller is `command_run`. So no `validate` path
  loads a probe entry point and the leak is `run`-only. Decision 13's guarantee — *"`validate` is
  the command you run in a loop while editing YAML"* — holds, which is what keeps Critical 1 at one
  command rather than every keystroke.
- **`E-PROBE-UNKNOWN` at the dispatch site.** It really is pre-answered by `_check_probe` from the
  same metadata scan, so I could not construct a run reaching `_probe_for` with an unknown name
  without changing the installed set mid-command. Its exclusion from `APPARATUS_CODES` stands on
  its own ground; the other two dispatch codes do not (Critical 1).
- **Whether the six-line Fixture F is minimal.** Not searched for, same as the plan's own note.
- **Anything about `dry-run`, `freeze`, `resume`.** Unbuilt; `Observer.observe_round`'s
  phase-independence is a design claim, read and not executed.
- **`Observer.block()` and `provenance.apparatus`.** Task 11's; `cli.py` still writes
  `"apparatus": None` unconditionally, and task 18's guard pin still passes. Correct for this batch.
