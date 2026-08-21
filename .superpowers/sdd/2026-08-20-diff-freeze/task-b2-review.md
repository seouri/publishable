# H8b batch B2 (tasks 1, 2) — review

**Reviewed:** `1fc05dc` (task 1), `911fb0c` (task 2), `7c76653` (report), on branch `h8b-diff-freeze`.
The diff file spans `bf56ed3`/`6b4bcd2` as well; those are batch B1's fix round and ledger, already
reviewed, and confirmed out of scope here by `git show --stat` on the two task commits.

## Verdicts

**Spec compliance: PASS.** Decision 9's ruling is implemented as written — `replay_ledger` calls the
**shipped** `Observations.record` per qualifying line in file order, with **no** first-answered,
per-condition-scoping or `nan`-reflexivity logic re-derived (verified by reading
`apparatus.py:225-315` against `replay_ledger`, and by running the gate's own `check_changed` over a
replayed baseline: agreeing facts pass, a moved fact raises `E-APPARATUS-CHANGED`). The phase filter
admits `run_start`/`pre_execution` and excludes `freeze`/`dry_run` (verified by mutation, below).
Decision 13's constants, `PHASES`, and the assert-as-first-statement are all present with no `E-` code
and no § Errors claim; Decision 14's home (`apparatus.py`, not `freeze.py`) is honoured. **Nothing was
wired:** `grep -rn replay_ledger src/` finds no caller, the only `cli.py` change is the one-line
constant swap, `NOT_BUILT_COMMANDS` is untouched, and no `freeze`/`diff` arm exists. Gates re-run by
me: `ruff check` clean, `ruff format --check` 84 files, `mypy` 47 source files, `pytest`
**2539 passed, 1 skipped, 2 xfailed**. One qualification against the refusal's own stated scope is
Major 3 below.

**Task quality: PASS WITH FINDINGS — three Majors.** Three of the four mutations (M6, M8, M9)
reproduce exactly as the report describes, verified by re-running each by hand. **M7 does not**: its
test cannot fail for the reason the report gives, and the report's stated mechanism is falsified by
running. The report's own grep list — the thing `CLAUDE.md`'s new row asks for — contains two
inaccurate entries, both about greps rather than about the implementer's code.

## Findings

### Major 1 — M7's test cannot fail for the reason claimed; the report's mechanism is falsified
`tests/test_apparatus.py:1291-1310` (`test_append_observation_accepts_each_of_the_four_named_phases`),
report § Task 2 ("All four removals **FAILED** the same way … because the removed name's own call now
raises `AssertionError` before writing its line").

**Verified by running** all four removals (`PHASE_RUN_START`, `PHASE_PRE_EXECUTION`, `PHASE_DRY_RUN`,
`PHASE_FREEZE` each dropped from the frozenset in turn, reverted by editing back each time, tree
confirmed clean by `git diff --quiet`): every one failed on `assert len(lines) == 4` →
`AssertionError: assert 3 == 4`, and **no `AssertionError` was ever raised inside
`append_observation`**. The loop at line 1301 iterates `sorted(PHASES)` — the very set under test — so
a removed name is never passed to the function, and the follow-up assertion
`{line["phase"] for line in lines} == set(PHASES)` compares the written phases against the *mutated*
set and is therefore vacuous under the mutation. This is `CLAUDE.md`'s "a test whose **name** claims
the guarantee": the docstring promises each of the four *named constants* is accepted; the assertions
deliver only `len(PHASES) == 4`.

Attack #4's question answered directly: **no, the four removals do not fail for their own reasons** —
all four fail identically, through one arithmetic assertion, and none through the mechanism claimed.
The mutation is still *detected* (that count, plus `test_phases_is_exactly_the_four_named_constants`
at line 1278, which pins membership against the literal strings independently), so no code property
is left unguarded — the defect is the false mechanism in a shipped docstring and in the report.
Repair: iterate the four constants (or four literals) rather than `sorted(PHASES)`, which makes each
removal fail at the removed name's own `append_observation` call.

### Major 2 — the docstring's dated measurement is false in its run-start half, and was not re-taken
`src/publishable/apparatus.py:466-482` (the `PHASES` docstring's "**Measured cost when
`append_observation`'s assert fires**, 2026-08-20, by patching it to raise and driving a real `run`
through `main(["run", …])` twice").

**Verified by running.** I patched `append_observation` to raise `AssertionError` and drove a real
`run` through `main(["run", …])` on a Fixture-P-shaped project (installed probe distribution,
project-local template declaring `apparatus_probe`/`apparatus_facts`, two swept conditions):

- fired on the **run-start** observation: uncaught `AssertionError`; run-directory root is
  `['environment', 'manifest', 'sweep.yaml']`; `run.yaml`, `executions.jsonl`, `apparatus/` and `lock`
  all **absent** (I did not measure `latest`: no such path existed in the results tree at that point,
  which is consistent with the docstring's "latest never repointed" rather than a check of it). The
  docstring says the root "holds `apparatus/`, `environment/`, `manifest/`,
  `sweep.yaml`" — **`apparatus/` does not exist**, and cannot, because the assert is the function's
  first statement, which is the very argument the same docstring makes two paragraphs earlier.
- fired on a **later `pre_execution`** observation (call 4, after two run-start calls and one
  execution): uncaught `AssertionError`; root
  `['apparatus', 'conditions', 'environment', 'executions.jsonl', 'manifest', 'sweep.yaml']`;
  `executions.jsonl` holds **1** line; `run.yaml` absent; `lock` removed. This half is accurate.

The report says the transcript was "not independently re-measured against a live `run` in this batch,
since the brief supplies the exact transcript" — and the brief's transcript labels **both** fires
`pre_execution`, while the docstring relabels the first as "the run-start round (before any
execution)". Relabelling an inherited measurement is what produced the false line. This is
`CLAUDE.md`'s "a fix that carries its own justification is not thereby verified", one level up: a
dated first-person measurement shipped in source for a run that was never made. Repair, preferring
deletion to rewriting: drop the enumerated survivor list from the run-start sentence (or drop
`apparatus/` from it) and keep the claims that were measured — uncaught, no `run.yaml`, lock released.

**The cost itself, adjudicated (attack #2).** Reproduced exactly as `CLAUDE.md` phrases it: one
execution paid for, `run.yaml` lost, and the traceback escapes because `execute_plan` wraps the
observation round in `except ContractError` and `AssertionError` is deliberately not one. I judge the
cost **acceptable and not worth filing**: no config, plugin, CLI argument or artifact can reach it
(Decision 13's own ground, which I confirmed by enumerating the call sites), and the constants make a
typo unreachable. Two things worth stating rather than filing: **no test asserts the surviving shape**
— the cost lives only in this docstring, which is exactly the sentence that turned out to be false —
and under `python -O` the assert is gone, which the docstring correctly says.

### Major 3 — a corrupt ledger line whose `facts` is present but not a mapping escapes the one refusal
`src/publishable/apparatus.py:586-594` (the `missing` key-presence guard, then
`observations.record(doc["condition"], doc["facts"])`).

**Verified by running** `replay_ledger` against hand-written single-line ledgers:

- `{"phase":"run_start","condition":"00_x","facts":null}` → `AttributeError: 'NoneType' object has no
  attribute 'items'`
- `{"phase":"run_start","condition":"00_x","facts":[1,2]}` → `AttributeError: 'list' object has no
  attribute 'items'`
- `{"phase":"run_start","condition":42,"facts":{"f":"x"}}` → returns quietly, with an **int** baseline
  key: `{42: {'f': 'x'}}`

The guard checks key *presence* only, so all three pass it. The docstring's own scope for
`E-FREEZE-LEDGER-UNREADABLE` is a line that is "not valid JSON, not a JSON object, or missing `phase`,
`condition` or `facts`", and the § Errors row task 12 is prescribed to write gives the cause as "the
file was edited or truncated" — a hand-edited or truncated ledger is precisely this input class. Once
task 6 wires `freeze`, `main` catches only `PublishableError` and `OSError`, so these become
tracebacks rather than diagnostics; the int-keyed condition is a quieter fail-open, since a baseline
key that matches no condition reads as "never answered" and lets `freeze` adopt a pin. Repair: extend
the same guard to require `isinstance(doc["facts"], Mapping)` and `isinstance(doc["condition"], str)`,
under the code that already exists.

### Minor 1 — the report's `probes.jsonl` grep result does not match the grep as written
Report § Task 1: "`grep -rn "probes.jsonl" src/publishable/` — two hits". **Verified by running** it
at the pre-task-1 commit `6b4bcd2`: **five** hits — `append_observation`'s write, `Observer.block`'s
recorded path string, and three docstring mentions (`apparatus.py:419`, `:447`, `:553`). The
substantive conclusion is right (one writer, one recorded string, no reader), and the brief made the
same two-hit claim; the reported number is what is wrong.

### Minor 2 — the report mislocates the third `phase=` hit
Report § Task 2: "`apparatus.py`'s own `phase=phase` inside `append_observation`". **Verified by
reading and by grep**: that hit is `apparatus.py:733`, inside `Observer._observe_one`'s **call to**
`append_observation`. `append_observation` receives `phase`; it passes it nowhere. The enumeration
itself is correct — see below.

### Minor 3 — the call-site enumeration is unpinned; a *third* literal site would ship green
`tests/test_apparatus.py:1334` (`test_cli_and_runner_call_sites_pass_the_named_constants`) inspects
only `command_run` and `execute_plan`. **Verified by running**: adding an unrelated function to
`cli.py` that calls `observer.observe_round(phase="run_start", …)` as a bare literal, leaving both
existing sites converted, left `tests/test_apparatus.py` fully green (63 passed). Relocating an
existing site *is* caught (I ran that too: moving `command_run`'s call into a helper fails the test on
its positive assertion). So the pin guards the two known sites, not the enumeration.

**My own enumeration (attack #3), read first, grepped second.** `append_observation`'s only caller is
`Observer._observe_one` (`apparatus.py:731`), which passes `phase` straight through; `observe_round`'s
only callers are `cli.command_run:2462` and `runner.execute_plan:640`; `observe_once` takes no phase,
and neither `observe_round` nor `_observe_one` carries a default for it, so no phase can originate
anywhere else. Confirming greps: `observe_round|append_observation` across `src/publishable/` and
`"run_start"|"pre_execution"|"dry_run"|"freeze"|phase=` across `src/publishable/*.py` — three `phase=`
hits, the four constant definitions, and `cli.py:152`'s `"freeze": "Operation commands"` section map,
which is not a phase. **Both core call sites were converted; there is no third.** And the vocabulary
is now enforced: `phase="BOGUS_FIFTH_SPELLING"` raises before the `mkdir` and leaves no file
(re-verified by running the shipped test, and by M6 showing the disk-content assertion is what
distinguishes the placement).

### Minor 4 (nit) — a cross-function positional locator in a docstring
`src/publishable/apparatus.py:452-458`: the `PHASES` docstring says "the assert **below**", which sits
~60 lines away inside another function. It names what it is, so it is findable, but "the assert in
`append_observation`" is the self-maintaining spelling `CLAUDE.md` § Habits asks for.

## The mutations I reproduced

| Mutation | What I ran | Result |
|---|---|---|
| M6 | assert moved below the `fh.write` | `test_append_observation_refuses_a_fifth_spelling_before_writing_anything` fails on `assert not …exists()` — as reported |
| M7 | each of the four names dropped in turn | fails on `assert 3 == 4` every time, never at the removed name — **Major 1** |
| M8 | `PHASE_FREEZE` admitted to `replay_ledger`'s filter | `test_replay_ledger_excludes_freeze_and_dry_run_lines_from_the_baseline` and `test_m8_fixture_…` both fail, the second with `assert ('pinned', 'a', 'b') is None` — as reported, on a named assertion |
| M9 | first-answered replaced by an unconditional `_first_answered[pair] = value` walk | `test_m9_fixture_the_baseline_is_first_answered_not_most_recent` fails with `assert ('pinned', 'r2', 'r1') is None`, plus two neighbours. **3 failed where the report says 7** — my variant also maintained `_total_counts`/`_facts_by_condition`/`_conditions`, so `facts_document()` kept working; the report's bare assignment blanks those projections and takes out the real-run and two-condition arms too. The report's figure is not falsified; my mutation was the weaker one, and the named test failed under both |

Every mutation was applied to a copy-backed file and reverted by editing back, then verified by
re-running (`git diff --quiet` clean, `tests/test_apparatus.py` green) — never by `git status` alone
and never with `git checkout --`.

## Adjudication of attack #5 — the half-pinned M8

**The split is right and the internal pin is sufficient until task 6.** No `freeze` command exists, so
an exit-code assertion is unwritable in this batch, and the internal pin discriminates for the right
reason: under the mutation `record` finds the pair already answered `"a"` from the `freeze` line and
`changed` returns a triple. The obligation is **durably filed where its owner will read it** — plan
task 6 **step 11** prescribes re-running task 1's fixture as an exit-code assertion ("two `0`s under
the shipped filter … then apply M8 and assert the second `freeze` becomes exit `1` with
`E-APPARATUS-CHANGED`"), so this is not the "a ledger line saying filed is not a filing" shape. The
report's statement of which half is pinned where is accurate.

## Prose checks (attack #7)

Verified by grepping both commits' added lines: **no § Errors row claims**, no citation of a
git-ignored brief (the two references are to "the task report", which is tracked, and to plan task 6),
**no config-count claim** anywhere — the 8 of 8 / 0 / 7 / 1 table is untouched — no `x`-for-`×`, and
no "no existing test asserts …"-style claim about other tests, which is where the last six
zero-disagreement failures hid. Brief step 1's prohibition ("do not write a sentence claiming any of
this is unreachable") is honoured: the filter's docstring says what is filtered and why. **The guard
pin's arms are untouched by this batch** — `git show --stat` on both commits shows only
`apparatus.py`, `tests/test_apparatus.py`, and the two one-line call-site swaps; the `test_cli.py` /
`test_hashes.py` docstring edits in the diff file belong to B1's fix round `bf56ed3`.

## What I could not check

- The report's **baseline** figures (2522 passed at `6b4bcd2`, and the intermediate 2535 after task 1)
  were not re-derived — that needs checking out two earlier commits. The +13 / +4 test deltas *were*
  verified from the commits themselves (11 new test functions plus a 3-id parametrize in `1fc05dc`;
  4 in `911fb0c`), and the final 2539 / 1 / 2 was re-run by me.
- Whether `spec-defects.md` should already carry the `dry_run`-phase contradiction: the docstring's
  "filed to H9" traces to the design's § Refusals row, and plan task 12 step 7 owns the filing, so no
  finding is raised against this batch — but the entry does not exist yet, and task 12's reviewer
  should check it lands.
- The `python -O` behaviour was not exercised; the docstring's claim about it is a language property,
  not a repo one.

## Disposition

**Majors 1 and 2 should close before B3 starts** — both are false claims in shipped text about this
batch's own code, and both are small: Major 1 is a two-line test edit (iterate the four constants),
Major 2 is a **deletion** of the enumerated survivor list rather than a rewrite, per `CLAUDE.md`'s
*prefer deleting a claim to rewriting it*. **Major 3 is task 4's to close**, not a fix-round item here:
it is the refusal `freeze` surfaces, task 4 owns `E-FREEZE-LEDGER-MISSING`/the refusal set and task 12
owns the § Errors row whose stated cause ("the file was edited or truncated") this batch cannot
currently honour — so it is named here **and** must be carried into task 4's brief, or it is unowned.
Minors 1-2 are report corrections; Minors 3-4 are optional.

**Tree state.** All four mutations were reverted and verified by **re-running** — full suite
2539 passed, 1 skipped, 2 xfailed; `ruff check` clean; `ruff format --check` 84 files; `mypy` 47
source files — and `git diff` against the committed tree is empty. The only working-tree entry is
this review file itself, untracked at the time of writing (`git add -f` is required for it, per
`CLAUDE.md`'s note about `.superpowers/sdd/.gitignore`).
