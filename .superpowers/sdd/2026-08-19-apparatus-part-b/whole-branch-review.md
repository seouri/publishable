# H7d Part B — whole-branch review

**Branch:** `h7d-apparatus-part-b` (13 tasks, six batches) · **Reviewed:** 2026-08-20 · **HEAD:** `600b207`

## Verdict: **MERGE**

Four Minors, no Critical and no Major. **I applied no fix** — Minors 1 and 2 are one-clause
deletions in `src/`, and a reviewer editing the branch it is gating is the move this repo has been
burned by; both are handed off, with the deletion (never a rewrite) named as the remedy. Nothing found changes a status byte, an exit code, a stop
decision, or a credential's path to a stream. Three of the four Minors are false claims in
comments/docs; the fourth is a sweep that stopped one file short. All four are the *record* being
wrong about the code, not the code being wrong — which is why none of them blocks.

**Gates, all run:** `ruff check` clean · `ruff format --check` 82 files formatted ·
`mypy` 46 source files, no issues · `pytest` **2456 passed, 1 skipped, 2 xfailed** (the expected
counts). Working tree clean; every mutation below was reverted from a saved copy and the revert
verified **by re-running the suite to 2456**, never by `git status`.

---

## First, a premise of the review brief that is false

**Batch 6 (tasks 9, 10, 11) was never reviewed.** There is no `task-b6-review.md` — five reviews
exist for six batches. And the ledger's last entry is **batch 5 pre-fix**: its final commit
(`c6a5863`) precedes both batch 5's fix round (`57a0734`) and all of batch 6. So the ledger records
neither batch 5's fix round nor tasks 9–11 at all.

Consequence: "do not re-litigate a closed finding" gave no coverage over batch 6, which owns the
no-policy-knob pin, the `batch`-independence pin, the document rows and all three filings. **I served
as batch 6's first review** and treated it at first-pass rigor rather than as a spot-check. It came
back clean — it touches **no `src/`** at all (tests and docs only), its two fixtures are
non-degenerate, and its three filings are the strongest artifacts on the branch. But that was
verified here for the first time, not confirmed.

---

## Findings

### Minor 1 — `STOP_CODES`' docstring names an exit code its own named test stopped asserting a batch ago
**`src/publishable/apparatus.py:526`**

> `task 5 added Fixture U, the unreachable-mid-plan sibling for E-APPARATUS-RAISED
> (tests/test_cli.py, `status: partial`, `EXIT_PARTIAL`)`

Fixture U asserts **`EXIT_EXTERNAL`**, not `EXIT_PARTIAL`. Task 5 (batch 4) wrote the docstring; task
8 (batch 5) moved the test's literal to `5` per Decision 6 and updated the test's own docstring to
say so — and did not touch this one. **This is a third instance of the exact cross-batch shape the
brief names twice**: batch 5's change made a batch 4 sentence false, invisible to either batch's own
review.

*Verified by:* reading `tests/test_cli.py:14556` (`expect_exit=EXIT_EXTERNAL`, `run["status"] ==
"partial"`), and by **mutation 3** below — deleting the precedence branch fails exactly that test,
confirming which literal it holds.

*Fix:* one word — `EXIT_PARTIAL` → `EXIT_EXTERNAL`. Prefer **deleting** the parenthetical to
rewriting it (`CLAUDE.md`: a rewrite invents, a deletion cannot); the status/exit pair is already
stated correctly in the test itself.

### Minor 2 — `Observations.changed`'s docstring asserts no shipped test does what a shipped test does
**`src/publishable/apparatus.py:278`**

> `reachable by a direct call that skips record first (verified by review; **no shipped test calls it
> that way**), not by any fixture that keeps the ordering`

`tests/test_apparatus.py:865`, `test_changed_asserts_when_called_without_record_first`, calls
`obs.changed("00", {"pinned": "r1"})` on a fresh `Observations` for the express purpose of tripping
that assert. Same shape as Minor 1, one batch apart: the clause landed in batch 2's fix round
(`abb04a9`), the test in batch 3's fix round (`3b62c82`).

Worth noting the direction: this is a comment claiming a thing is **unpinned** when it is pinned —
the opposite of the usual overclaim, and the more likely to send a later reader building a test that
already exists.

*Verified by:* reading both sites; `git log -S` on each string to establish the ordering.

*Fix:* delete the parenthetical, or replace it with the test's name.

### Minor 3 — the `E-APPARATUS-RAISED` § Errors row's mid-plan clause is untrue for a zero-results stop
**`docs/reference.md:1061`**

> `A mid-plan raise instead stops execute_plan's loop … and reaches the same redacted diagnostic
> through the record path: status: partial, the executions that already ran kept, exit 5 again`

A mid-plan raise on the **first** `pre_execution` round has zero results: no `run.yaml`, no `status`
byte, `latest` untouched — Decision 4's row 2, and Fixture Z arm 3's own subject. The row states the
`≥ 1`-results outcome as though it were the only mid-plan one.

**Its twin row carries exactly the missing qualifier.** The `E-APPARATUS-CHANGED` row (line 1066)
reads *"the record kept — **once there is one to keep**, per § Exit codes' `1` row"*. This is the
same asymmetry batch 1's review caught pointing the other way (the moved fact's record claim
unqualified while the unreachable twin was qualified), now inverted after task 8 fixed that half.
`CLAUDE.md`: a § Errors row carries one row per code covering **every** emit site.

Scope note: **§ Exit codes is correct** — *"That exit code holds whether or not a record was
written — a probe unreachable before the first execution leaves a run directory with no `run.yaml` to
hold a status at all, and still exits `5`."* Only the § Errors row is loose, so a reader who reaches
the exit-codes section gets the right answer — and that clause covers the shape completely rather
than by coincidence of wording: **a mid-plan raise with zero results can only be the first
`pre_execution` round**, because `results.append` is unconditional per loop iteration, so no variant
exists where execution N ≥ 1 has run and `results` is still empty.

*Verified by running:* my own fixture (row 2 below) — exit `5`, no `run.yaml`, no
`executions.jsonl`, `latest` and `latest.txt` both absent.

### Minor 4 — the consistency sweep stopped one file short of the file its own charter names
**`docs/feasibility-llm-growth-studies.md:490`**

Still reads *"each deployment is gated against its own first observation"*. The branch changed both
normative statements of that rule to **first *answered* observation** — `reference.md:3108` and
`experimental-designs.md:375` — because the design found *"two document sections give the gate two
different comparison rules"* and task 1 gained a step for it. `CLAUDE.md` § Checking consistency puts
the feasibility analysis explicitly inside the removed-string sweep, and the design's own
§ The consistency sweep lists only the four documents, which is where the omission entered.

*Verified by:* `grep -l` over the four documents + `CLAUDE.md` + the feasibility analysis, **with a
can-fail control** (`"Four things produce it"` → found in `reference.md`, proving the sweep can hit).

---

## Not a finding, but owed: no § Executability entry

**Nine consecutive slices have added a dated `### Measured on … — after <slice>` entry** to
`docs/feasibility-llm-growth-studies.md` § Executability on this build, H7d **Part A** included —
and Part A's was added *by its whole-branch review*, not by a task. Part B added none, and its design
chartered none (its consistency sweep names the four documents only).

**The entry is owed and unwritten, and this file is not it.** The analysis has nine dated
subsections and no tenth; a measurement living only in a review file is not that tenth, and Part A's
entry was written *into the analysis*. I took the measurement so its author does not have to re-run
it — the table below is the measurement, not the filing. Method: each config's `data`/`statistics` blocks transplanted verbatim onto a scaffolded config
over a 240-row synthetic roster, through `validate_config` — the same method every entry since
2026-08-16 uses.

| Config | Codes reported |
|---|---|
| E1 | `E-NAME-DIR`, `E-RESOLVER-UNKNOWN` (both harness artifacts: the config not under `configs/<name>/`, and the plugin not installed) |
| C1 | the same two |
| E1 with `holdout.frac → 0` (**can-fail control**) | the same two **plus** `E-DATA-HOLDOUT-FRAC` |

**No `E-APPARATUS-*` on either**, and none is reachable for any of the nine: `apparatus_probe` is a
**template** attribute defaulting to `None` on `BaseTemplate`, and `generic` — the template every
config here substitutes — declares none, so `command_run` never constructs an `Observer`. Also
confirmed absent: `E-DATA-RESOLVER-UNSUPPORTED` (H7b B) and `E-DATA-WEIGHT-CONTRAST` (H4b-1), both
retired.

**The remaining action:** someone writes
`### Measured on 2026-08-20 against commit 600b207 — after H7d Part B` into
`docs/feasibility-llm-growth-studies.md` § Executability on this build, from the table above. Until
that exists, "the whole-branch review measured it" must not be read as "the analysis records it" —
the same distinction between a ledger line saying *filed* and a filing.

**The counts are unmoved: zero unblocked, six with no remaining core-side blocker, three
executable.** The slice's own claim, re-measured independently rather than carried.

---

## What I verified by running

### Decision 4's four rows — my own fixtures, exit code and status byte asserted separately

Built independently of the shipped Fixtures U / G1 / Z, each on its own probe schedule. **All four
correct.**

| Row | Result |
|---|---|
| Unreachable, ≥ 1 results | exit **5**, `status: partial`, `run.yaml` written |
| Unreachable, 0 results | exit **5**, **no** `run.yaml`, **no** `executions.jsonl`, `latest`/`latest.txt` absent |
| Moved, ≥ 1 results | exit **4**, `status: failed`, `run.yaml` written |
| Moved, 0 results | exit **1**, **no** `run.yaml`, `latest`/`latest.txt` absent |

The row batch 5's fix round repaired (unreachable + 0 results → 5, not 1) is correct at HEAD.

### No false stops — seven runs, zero false stops

A constant fact across every execution; `null → value`; `value → null`; an **absent undeclared key**
on later calls; a constant **`nan`**; **two conditions holding different values of the same fact**
(driven by the swept parameter); and a **`batch`** repeat. Every one completed at exit 0 with
`status: completed`. Batch 2's `nan` reflexivity fix survives the wiring and does not over-suppress.

### The credential story, end to end, with a working positive control

| Shape | Result |
|---|---|
| `int` credential that **moves** (`E-APPARATUS-CHANGED` stop) | nothing on stdout or stderr; `<redacted:…>` rendered |
| Credential as a **substring** of a `str` fact | never reaches a stop — Part A's `check_facts` refuses it first (`E-APPARATUS-FACT-CREDENTIAL`, exit 1), nothing leaked |
| Credential **inside the raise message** (`E-APPARATUS-RAISED` stop) | nothing on stdout or stderr |
| **Positive control** — `Collector.credentials` neutered on the stop path | **leaked the plaintext**, so the three fixtures above can see a leak |

`run.yaml` **does** carry the plaintext `int` credential in `provenance.apparatus.facts`. This is
**already filed and correctly scoped** — the non-`str` carve-out entry was widened to name `run.yaml`
explicitly by batch 5's review (appended 2026-08-20), stating it is the same carve-out reaching a
second artifact and pre-existing rather than created here. I re-measured it; the filing is accurate.

### The controller's ruling — four mutations

| Mutation | Outcome |
|---|---|
| Drop `and stop is None` from `run_status`'s truncation assert | **4 tests fail**, including the protected `test_max_failed_fraction_is_measured_against_the_test_partition` and both truncation arms — the third stop reason is **genuinely read**, not an unread enum member |
| Add `"stopped_at": None` to `run.yaml` (the shape Decision 3 refuses) | **2 tests fail** — batch 1's arm A *and* Fixture G1's own whole-key-list assertion on a **stop** path, which closes the blindness arm A's docstring admits |
| Delete the `EXIT_EXTERNAL` precedence branch (5 over 3) | Fixture U fails — the precedence is pinned |
| `apparatus_unreachable → "completed"`, leaving exit 5 intact via precedence | **2 tests fail** — so the **status byte and the exit code are pinned separately**, which is exactly what Decision 6 requires and what a status-only or exit-only assertion could not see |

`max_failed_fraction` keeps `completed`: the protected test's assertion **and** docstring are
byte-identical to `main`, `tests/test_runner.py` has **140 insertions and zero deletions** across the
whole branch, and the only 7 deletions in `tests/test_cli.py` are an import widening, the `run_dir`
helper widening, and the **one** documented literal change (Fixture K2, `EXIT_WRONG → EXIT_EXTERNAL`).
No assertion was removed anywhere on this branch.

### The `run_status` assert cannot fire on a healthy run

The design argues this structurally; I enumerated it. Inside `execute_plan`'s loop there are exactly
**two** `break`s — the apparatus gate and `max_failed_fraction` — and **both** set `stop.reason` when
a signal is given; there is no `continue` and no early `return`, and `results.append` is
unconditional per iteration. The assert is also **one-sided** (`len(results) >= planned`), so a
`results` list *longer* than `execution_order` cannot trip it either. `limits.max_executions` is not
a loop-level truncation. Confirmed empirically across every run I built, including a plan whose
`results` (4) exceed `sweep.yaml`'s `execution_order` (3).

### `CLAUDE.md` § Invariants

- **No policy knob.** No `limits` field exists; task 9's arm (a) pins the closed-key refusal
  differentially against a clean control, arm (b) pins that the most permissive `limits` still stops.
- **Three hashes, not four.** `HASHED_TREES = ("src", "templates")`; `hashes.py` and
  `provenance.py` name the apparatus nowhere. `reference.md` says *"This is not a fourth hash"*
  and the code agrees.
- **`batch` independent of the apparatus.** `apparatus.py` names the repeat kind nowhere (its only
  `batch` hits are prose about slice batches); `replication.py` names the apparatus nowhere. Fixture B
  is non-degenerate — its schedule *moves*, so a gate keyed on the repeat label would be visible.
- **Operation commands take paths and nothing else** — no flag, no env var, no mode added.
- **Core never inspects user Python's body**; **units stay the inference base** — untouched.

### The record on a stop

- `executions.jsonl` short of the plan; the ledger's last line holds the **moving** observation while
  `provenance.apparatus.facts` holds the **first-answered** one — the asymmetry Decision 1 rests on,
  observed on disk.
- A zero-results stop writes **neither** `run.yaml` **nor** `latest`, on **both** reasons.
- Decision 9's filing re-measured independently: a declared fact missing on call 3 gives exit **1**,
  `E-APPARATUS-FACT-MISSING`, **no `run.yaml`**, **one execution paid for** — exactly as filed.

### The interaction the brief asked me to hunt for

The apparatus `break` sits at the **top** of `execute_plan`'s loop, before `started =
datetime.now(UTC)`, whereas `max_failed_fraction`'s sits at the **bottom** at a step boundary. So an
apparatus stop can truncate **mid-step-sequence** and then run the whole record phase — a shape
`max_failed_fraction` is not precedent for. Two runs built for it:

- A multi-step plan whose tail is a `summary`-scope step, stopped before it: `run.yaml` written,
  `status: failed`, `results.summary` an empty dict, `latest` repointed, no crash.
- The sharper form — a declared **hypothesis** whose metric is that unrun `summary` step's reported
  `Estimate`: the verdict is recorded as `observed: null, supported: null, verdict_rests_on:
  reported`, one diagnostic printed, no crash, no `KeyError`.

Coherent, not merely non-crashing. **No finding.**

### Documents

Both passes run. **Mechanical:** every relative link, `#anchor` and cross-file anchor in the four
documents resolves; no colliding headings; every table row matches its header's column count; no
trailing whitespace, tab or invisible unicode; fenced blocks skipped. **Can-fail controls**: the
slugger was validated against a known-good anchor (`secrets--credentials`) and a known-bad one.
The four em-dash headings flagged are **pre-existing** (`33d6d32`), internally consistent, and
untouched by this branch. **Cross-document:** the shared worked example is untouched — `README.md`
and `design-principles.md` are not in the branch diff at all. Every `E-` code raised in `src/` has a
`reference.md` row except seven pre-existing ones this branch does not touch;
`E-APPARATUS-CHANGED` has its row, and its two sites (the raise in `check_changed`, the report
through task 7's fresh `Collector`) are one row, correctly.

`§ What status means` and `§ Exit codes` are true against the code on every clause I could drive —
`failed`'s count phrase moved to **four** producers with the apparatus named; `partial`'s *"one
thing"* narrowed to unreachability; the `1` row extended to a change caught before the first
execution; the `5` paragraph extended to hold whether or not a record was written. The remainder the
design said **cannot** be closed without further code change is **filed, not quietly closed** — see
below.

### The filings

All three are in `spec-defects.md` and each states the check its owner must make.

- **`EXIT_EXTERNAL` ships and is read by nothing** — struck as CLOSED, and genuinely closed: three
  readers in `cli.py`, both pinned.
- **The four fact-contract refusals lose the run record mid-plan** — unassigned **with the reason**
  (no `reference.md` sentence sites a fact-contract failure at run time, so no section has an owner),
  and its measurement re-verified by me end to end.
- **`max_failed_fraction`'s truncation** — unassigned with the reason, and **check 1 is exactly the
  controller's requirement**: *"that the current behaviour is pinned with a written justification, to
  be argued against rather than discovered."* Both faces are recorded, including the second one
  (`partial`'s *"one thing"* still false for a mixed truncation) that batch 1's review found and its
  report had missed.
- Batch 4's stale *"Verified by running"* sentence was corrected **by dated append**, twice, rather
  than rewritten — the right form.

---

## What I could not check

1. **Anything about `dry-run`, `draft`, `resume`, `freeze`, `diff`, `reproduce`.** All print
   *specified but not built*, so the gate's composition with `resume`'s restart is a spec claim, read
   and not run — as the design already states.
2. **A real metered probe**, and the hosted-deployment behaviour the `null` rule exists for. Every
   fixture uses a local fake, deliberately, per § Cost and risk.
3. **The nine configs' actual plugin.** `generic` is a documented substitution, not the thing; my
   re-measurement inherits that limitation exactly as the nine preceding entries do.
4. **Whether any *future* knob could be added.** Arm (a) pins today's schema, arm (b) pins today's
   most permissive config. Neither can pin the absence of a field nobody has written — the design
   says so and I confirm no test claims otherwise.
5. **Batch 6's own prescribed mutations as its implementer ran them.** I reviewed its work fresh and
   built my own checks, but its report's mutation outcomes are read, not reproduced.

## Tree state

**Clean.** `git status` empty; no uncommitted or untracked files; all five mutations reverted from
saved copies and verified by re-running the full suite to **2456 passed, 1 skipped, 2 xfailed**.
