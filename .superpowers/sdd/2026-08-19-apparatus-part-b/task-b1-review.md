# Batch B1 review — tasks 12, 1

**Reviewed:** `2a10c3a` (task 12), `a59ef6f` (task 1), `e1e178f` (report), against
`4abdbe2`. Branch `h7d-apparatus-part-b`.

**Gates, run in the foreground at `e1e178f` with `__pycache__` and `pytest-of-*` cleared:**
`ruff check` **All checks passed!** · `ruff format --check` **82 files already formatted** ·
`mypy` **Success: no issues found in 46 source files** · `pytest` **2426 passed, 1 skipped,
2 xfailed** (150.41 s). **Tree clean at review end**: no tracked file modified, every review mutation
reverted by editing back and confirmed by `diff` against a saved copy; the only untracked file is this
review.

## Two verdicts

**Spec compliance: PASS.** Both tasks did what the design's § Ruling from the controller and their
own briefs authorized, and no more. No behaviour changed — the suite moved only by task 12's three
tests, and `git diff 4abdbe2..e1e178f` touches exactly three files, none of them under `src/`.
`test_max_failed_fraction_is_measured_against_the_test_partition` — its assertions **and** the
docstring the ruling protects — is untouched, verified by diff. The failure-fraction clause in
`reference.md` § What `status` means is byte-identical, so nothing made that section consistent
about `max_failed_fraction`. Neither commit nor the report names a config count, and nothing claims
this slice unblocks anything (grep over the whole batch diff for *unblock*, *executable*, *no
remaining core-side*: zero hits).

**Task quality: PASS. No Major, no Critical; every finding below is Minor.** The pin is real and
discriminates on all three arms, verified by three mutations rather than by reading, and the report's
own mutation claim reproduces exactly — 1 failed, 2425 passed. Its two disclosed residuals are the
substantive ones, and its § What this task does NOT close is substantively complete with one
propagation unnamed (Minor 1). The "ZERO disagreements" claim did not survive: one brief departure
and one brief-prescribed over-claim are named below. Ranked by what a later batch needs to see,
**Minor 3 is the one to carry forward** — task 8 writes the branch it concerns.

## The circularity question (attack 1): **not circular**

Arm B is an **independent assertion**, not the shipped test. It builds its own `run_a_project(...)`
call inline with the same arguments and asserts, in its own body, `len(ledger) == 2`,
`len(sweep["execution_order"]) == 5`, the inequality between them, all-`completed`, and — the
discriminator — **`run["status"] == "completed"`**, which
`test_max_failed_fraction_is_measured_against_the_test_partition` does not assert at all (it asserts
a non-empty ledger, all-`completed`, and `len(ledger) < _planned_execution_count(doc)`). Editing or
deleting the shipped test cannot satisfy arm B; the shipped test is named only in arm B's docstring.

**Verified by running, not by reading.** Under a record-only mutation of the status byte
(`cli.py`'s `assemble_run_yaml(status=…)` flipped `completed`↔`partial`, leaving the exit mapping's
input alone) the shipped `max_failed_fraction` test **passed** while arm B **failed** on
`assert run["status"] == "completed"`. A mutation the shipped pin cannot see and arm B can is
positive proof the two are not the same test.

Two residuals, neither a finding:

- Both share the `_ALWAYS_FAILING_STEP` source string (four occurrences in `tests/test_cli.py`:
  definition, the shipped docstring, the shipped call, arm B's call). That is a shared **input**,
  not a shared assertion — a change to it breaks both, which is the direction that fails loudly.
- The ruling protects the shipped docstring's **argument**, and no test can pin a docstring. A later
  batch editing only that docstring is caught by nothing. Listed under *could not check*.

## Findings

### Minor 1 — `docs/reference.md:778`: the `failed` clause's contradiction propagates into the adjacent paragraph's exclusivity claim, and the report names only one face of it

The landed sentence reads *"A run that stops early can still be `partial`, and one thing produces
that: the apparatus becoming unreachable — not the apparatus generally, and not a fact it observed
changing…"*. Arm C (`tests/test_cli.py:14279`,
`test_a_mixed_truncation_is_partial_at_exit_3`) drives a `max_failed_fraction` stop with a mixed
status set: the plan stops at 2 of 5 and `run.yaml` records `status: partial` at exit `3`.

**This is not an independent second producer.** The paragraph's list is scoped by the paragraph before
it, which claims `max_failed_fraction` produces `failed` — so under the document's own story the
failure fraction is not a candidate for `partial` at all, and :778 is false only because that clause
is. **One contradiction with two faces**, and the ruling forbids repairing either. Task 1 was right to
leave both.

What is worth recording is that the report names one face — *"the `failed` paragraph's
`max_failed_fraction` clause is a clause the code still contradicts"* — and not that task 1
**sharpened** the other one in the same commit. The owner reconciling that clause must fix **two**
sentences, not one, and task 11's filing is written from this report. **Fix:** one clause in the
report and one in the filing. No code, no document edit.

**Verified by running**, so the arithmetic behind arm C is not taken from its docstring: with the
guard's `break` in `src/publishable/runner.py` replaced by a diagnostic write, the guard's own numbers
came back `failed=20 resolved=20 nres=2` — a real truncation, and `run.yaml` reports `partial`.

### Minor 2 — `docs/reference.md:778`: a positional locator and a count ordinal in one clause

*"…which is `failed`'s fourth cause above."* Both shapes `CLAUDE.md` names: locating by position
(*"the two rows above"*, wrong twice in seven instances, falsified by an insertion) and a count
phrase that goes stale when a fifth cause is inserted. **Prefer deleting a claim to rewriting it** —
*"and not a fact it observed changing, which fails the run"* keeps the whole contrast with no
pointer. Verified by reading.

### Minor 3 — `docs/reference.md:776` and `:3099`: "the record is kept" stated without the zero-results qualification the same commit gave the neighbouring case

Both new sentences state the moved-apparatus outcome unconditionally: *"the record is kept anyway
rather than discarded"* (§ What `status` means) and *"The run is marked `status: failed`, and its
record is kept rather than discarded"* (§ The apparatus core can only observe). Design **Decision 4**
rules `Moved | 0 results | none | — | 1` — no record at all. The same commit qualified the
*unreachable* case exactly this way in § Exit codes (*"whether or not a record was written"*), so
the document now carries the qualification for one fault and not for its twin. The wording is what
task 1's brief step 3 prescribed, which makes this a brief-level gap the implementer did not flag —
and the report claims zero disagreements. Verified by reading Decision 4's table against the landed
text, and by reading § Exit codes' `1` row, which names *a config that fails validation, a `diff` of
runs that don't share a hash, a `resume` whose hashes moved* — **a moved apparatus at run start is
not among them**. So the document has no home for exit `1` in that corner *and* asserts the record is
kept. Task 8 writes that branch; it should see this before it does.

### Minor 4 — `docs/experimental-designs.md:375`: correction 6's divergence is closed inside `reference.md` only

`reference.md` now says *"first **answered** observation"* in both of its sections. § Mistakes core
prevents still says *"observed to differ from its own first observation"*. The row is not wrong —
its next sentence says an unanswered fact is *"recorded as `null` and counted rather than read as a
change"*, which forecloses the reading correction 6 was about — but the cross-document pass governs
all four documents, and this is the loose phrase a reader takes the contract from. The report records
the row as *checked, needed nothing* without naming the residual. Verified by sweep over the four
documents named individually plus `CLAUDE.md` plus the feasibility analysis, with a positive control
(the feasibility analysis's own *"its own first observation"* at line 490 is exempt and correctly
left).

### Minor 5 — a brief departure the "ZERO disagreements" claim does not name

Task 12's brief lists `_planned_execution_count` under **Consumes**, and the design's Fixture T
names the truncation assertion as *"the comparison the shipped `_planned_execution_count` helper
already makes"*. The arms instead read `sweep.yaml`'s `execution_order` and hard-code `5`. That is
the better choice — it asserts the artifact a reader compares against, which is Decision 12 — but it
is a departure, and the report reports none. Verified by reading both files, and by running the
guard mutation, where both arms fail on their own `len(ledger) == 2` rather than on a helper call.

### Minor 6 — the pin's discrimination boundary is narrower than the mutation suggests, and is not written down

Arm A is the only arm asserting `run.yaml`'s key list, and arm A is a **clean** run. It therefore
catches an **unconditionally** added key — which is what its docstring claims and what the report's
mutation proves — and is blind to a key written **only on the stop path**, which is exactly what
tasks 7 and 8 could add. Arms B and C assert no key list. Verified by running the report's own
mutation (`"stopped_at": None` added unconditionally in `run_record.assemble_run_yaml`: **1 failed,
2425 passed** — arm A alone, reproducing the report's claim exactly) and by reading arms B/C. Worth
one line in B5's brief so a reviewer there does not read arm A as covering the conditional shape.

### Minor 7 — the report's own framing undersells the property it is certifying

*"re-ran the shipped `max_failed_fraction` fixture's own shape rather than duplicating it"* — arm B
does duplicate the arguments inline, and **the duplication is precisely what makes the pin
non-circular**. As written the sentence describes the circular design the ruling forbids.

## Attack 2 — all three arms discriminate, and none is an absence-only control (verified by running)

| Mutation | Arm A | Arm B | Arm C | Shipped `max_failed_fraction` test |
|---|---|---|---|---|
| `runner.py`'s truncation `break` → `pass` | passes (unaffected) | **FAILS** `assert len(ledger) == 2` (5 == 2) | **FAILS** `assert len(ledger) == 2` (5 == 2) | FAILS `5 < 5` |
| `cli.py` record-only status flip (`assemble_run_yaml(status=…)`, exit mapping untouched) | **FAILS** `run["status"] == "completed"` | **FAILS** `run["status"] == "completed"` | **FAILS** `run["status"] == "partial"` | passes |
| `cli.py` exit mapping `{completed: 3, partial: 0}` | **FAILS** helper's `main(...) == expect_exit` | **FAILS** same | **FAILS** same | FAILS |
| report's own `"stopped_at": None`, unconditional | **FAILS** key list, index 8 | passes | passes | passes |

Every failure is on an assertion, and the status byte and the exit code are pinned **separately** for
all three arms — the property B5's review needs. Neither B nor C is an absence-only control: arm B's
`all(r["status"] == "completed" …)` is vacuous over an empty ledger, but `len(ledger) == 2` defeats
that; arm C asserts an explicit `["completed", "failed"]` list. Each mutation was applied over a
saved copy, reverted by editing back, and the revert verified by `diff` against the copy (three times
**REVERTED IDENTICAL**) — never `git checkout --`.

## Attack 3 — the document, both directions

`git diff 2a10c3a a59ef6f --numstat` is **5 insertions, 5 deletions**, and `docs/reference.md` is
4018 lines before and after: every edit is a one-for-one sentence replacement, so **no table row and
no paragraph moved**, and there is nothing displaced to re-check. Verified landed: `failed`'s count
phrase three → four with the moved-fact case added; `partial`'s *"one thing"* now naming the
unreachable case; § The apparatus core can only observe stating `status: failed`; § Exit codes
gaining *"whether or not a record was written"*, which matches Decision 4's table exactly
(unreachable, 0 results → no record, exit 5); and *"first **answered** observation"*. Verified
untouched: the `completed` and `partial` table rows, the `max_failed_fraction` clause (byte-identical),
the exit-`5`-wins sentence, § The apparatus files' *"first answered observation"*, the `resume`/ledger
sentence, and every file under `src/`. One forced change outside the five: the input-manifest
sentence's leading *"And"* was dropped so the new sentence could take it — no semantic drift.

## Attack 4 — the "ZERO disagreements" claim, tested on six specific brief/report claims

| Claim | Source | Verdict |
|---|---|---|
| Exit `5`'s row is the only one of `3`/`4`/`5` not marked *"`run`, `draft`, `resume` only"* | task 1 brief step 4 | **TRUE**, read from the § Exit codes table |
| Arm C is 20 of 20 unresolved, past `0.5` | task 12 brief step 2, arm C's docstring | **TRUE, verified by running** an instrumented guard: `failed=20 resolved=20 nres=2` (arm B: `failed=4 resolved=4`, the narrowed partition) |
| Default replication is `seed n=5` | report | **TRUE** — `materialize.INIT_REPEATS = 5` |
| The `stopped_at` mutation fails exactly one test | report | **TRUE, reproduced**: 1 failed, 2425 passed, 1 skipped, 2 xfailed |
| The `failed` paragraph named three producers | task 1 brief step 1 | **TRUE** |
| `_planned_execution_count` is consumed | task 12 brief *Interfaces* | **FALSE** — Minor 5 |

## Attack 5 — both passes

**Mechanical**, over the four documents named individually plus `CLAUDE.md` plus the feasibility
analysis, fenced blocks skipped: every relative link and `#anchor` resolves, no two headings collide,
every table row matches its header's column count, no empty rows, no trailing whitespace, no tab, no
invisible unicode, no `[0-9] x [0-9]`. **Clean.** The report's "four pre-existing missing anchors" do
not reproduce under a slugger that strips punctuation — they were its slugger's artifacts, and
nothing there is owed.

**Cross-document**, filtering the file list and never the sweep's output, with a positive control
(*"means there is nothing to report"* → 1 hit in `reference.md`, 0 in the other three, so the sweep
can fail): *"Three things produce it"* → 0, *"core losing the ability to certify"* → 0, *"Four things
produce it"* → 1 in `reference.md`. `design-principles.md` (the pinning bullet, § Not bit-identical
reruns) and `experimental-designs.md`'s apparatus row say a changed fact fails the run and needed
nothing, confirming the report — except for the wording in Minor 4.

## Could not check

- **The docstring the ruling protects.** Arm B pins the *behaviour*; nothing can pin
  `test_max_failed_fraction_is_measured_against_the_test_partition`'s *argument*. A later batch
  editing only that docstring is caught by no test — only by a reviewer diffing it, which this review
  did.
- **A key added on the stop path only.** No arm can see it (Minor 6). It becomes checkable at task 7.
- **Whether Minor 3's zero-results corner is reachable at all.** The plan's § What could not be
  measured says no fixture at `814eadd` can produce a stop with zero results, and that is still true
  at `e1e178f`; the claim is a spec claim on both sides.
- **`dry-run`, `freeze`, `diff`, `reproduce`, `resume`.** All print *specified but not built*, so the
  § Exit codes sentences about them are read, never run.
