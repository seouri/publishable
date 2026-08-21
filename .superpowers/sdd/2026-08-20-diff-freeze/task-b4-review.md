# Batch 4 review — tasks 4, 5, 6 (`freeze.py` end to end)

Reviewed 2026-08-20 against `2675cc8` on `h8b-diff-freeze`. Every `freeze` invocation below went
through **`main(["freeze", …])`**, never `_precheck` or `command_freeze` directly — H7d Part A's
only Critical was invisible to every direct-call probe, and two of the findings here are invisible
to the shipped suite for the same reason. A throwaway harness (`tests/test_zz_review_b4.py`, 17
tests) built its own project through `run_a_project` with an installed probe distribution whose
probe answers from a JSON file the test rewrites and appends to a marker file on every call. The
harness was **deleted**; the tree is clean and every mutation was reverted by restoring a
pre-mutation copy and **re-running**, never by `git status`.

**Gates, run directly at HEAD after every revert:** `uv run pytest` → **2569 passed, 1 skipped, 2
xfailed**; `ruff check` clean; `ruff format --check` → **86 files** unchanged; `mypy` → **48 source
files**, clean. The guard pin's final arms did not fire.

## Verdicts

**Spec compliance: PASS with findings.** Decisions 7-9 and 11-13 are implemented as written, and the
two properties most easily got wrong are right and I verified both by running: Decision 9's
exclusion holds under a **second** `freeze` (attack 3 is **not** a Critical), and Decision 11's
"writes one line per condition and touches nothing else" holds byte-for-byte over the whole results
tree, `lock` included. Decision 10 is where it diverges: the two warnings its verdict table
specifies are shipped **unpinned** (Major 3), and its exit-0 **`Printed as`** cell and Decision 8's
*"the output states the count"* are both unmet, undisclosed and unfiled (Minor 1) — ranked Minor
because § Operation commands specifies no `freeze` output at all, so no document is contradicted and
no observation is lost: the ledger holds every one.

**Task quality: PASS with findings.** The report is the most candid in this slice — it discloses the
missing ordering mutation, the unverified carry-forward, and the brief disagreement, each in its own
section. That candour is why two of the three Majors were findable at all. It does not convert them
into non-findings: the ordering property Decision 10 calls load-bearing is unpinned (Major 1), and
batch 2's carried Major 3 is **still open** while the report says a grep showed it closed (Major 2).

---

## Findings

### Major 1 — Decision 10's credential-before-the-probe ordering is unpinned; the only test that sees it fails on the check's *location*

`src/publishable/freeze.py:367-368` (gate (k)); `tests/test_freeze.py:362`.

Decision 10 states the property as *"A missing credential is exit `5` … with **no probe call made**
and no ledger line written."* The report answers with *"structurally true by construction, not only
by test"* and *"tried by hand and reverted rather than kept as a persisted mutation test."*
`CLAUDE.md` is explicit that a safety argument is a claim needing a mutation, and that if a comment
says this cannot happen, you make it happen. **I ran both mutations.**

- **M-b (property genuinely broken):** gate (k)'s refusal moved into `command_freeze` **after**
  `observer.observe_round(...)`. Exactly one test fails —
  `test_f5_sibling_arm_credential_precheck_before_any_probe_call` — on
  `assert isinstance(result, _Refused)` (`tests/test_freeze.py:116`). The probe **is** called, a
  ledger line **is** written, a metered call **is** spent, and no assertion anywhere sees any of
  that.
- **M-a (property preserved):** the same block moved into `command_freeze` **before** `_probe_for`.
  **The same one test fails, on the same assertion.**

So the shipped suite cannot distinguish "the check runs before the metered call" from "the check
runs after it" — it distinguishes only "the check lives inside `_precheck`". That is precisely
`CLAUDE.md` § Answering a question with a proxy, and § Writing checks that can fail's *a mutation
applied to a proxy*.

**Verified the gap is closable by one test.** My harness's end-to-end arm — credential unset, `.env`
deleted, a probe that appends to a marker file on every call, driven through `main` — asserts exit
`5`, `E-APPARATUS-RAISED` in stderr, **the marker absent**, and the ledger unchanged. It **passes**
at HEAD, **fails under M-b** on `assert not marker.exists()`, and **passes under M-a**. That is the
discriminating triple, and it is what makes this a fixable Major rather than a complaint.

### Major 2 — batch 2's carried Major 3 is NOT closed, and the report's grep claim about it is false

`src/publishable/apparatus.py:585` (presence-only key check) and `:593` → `Observations.record`
(`:251`).

The report says: *"grep confirms `apparatus.replay_ledger`'s guard already required
`isinstance(doc["facts"], Mapping)` and `isinstance(doc["condition"], str)` at the commit this batch
started from (task 1's own commit, `1fc05dc`), so this was already closed before task 4 began."*
**Neither guard exists — at `1fc05dc` or at HEAD.** `git show 1fc05dc:src/publishable/apparatus.py |
grep -n isinstance` returns seven hits, none of them these two; `grep -c` for either spelling at HEAD
is `0`. `replay_ledger` checks key **presence** only. The likely misread is
`isinstance(doc, Mapping)` at `:580`, which is the whole-line check.

**Measured through `main(["freeze", <run_dir>])`, one appended `run_start` line per case:**

| Appended line | What happens today |
|---|---|
| `"facts": null` | **`AttributeError: 'NoneType' object has no attribute 'items'`** — a raw traceback out of the console command, `apparatus.py:251` |
| `"facts": [1, 2]` | **`AttributeError: 'list' object has no attribute 'items'`** — same site |
| `"condition": 42` | **exit 0**, silently: an int-keyed baseline, and `freeze` reports every condition `unchanged` |
| `[1, 2, 3]` | `E-FREEZE-LEDGER-UNREADABLE`, exit 1 ✔ |
| `not json at all` | `E-FREEZE-LEDGER-UNREADABLE`, exit 1 ✔ |

This is the third pass this finding has survived: an H8a review routed it to batch 2, batch 2 carried
it into task 4's brief, and task 4 recorded it closed on a grep that does not hold.

**Scoped, so the claim matches its evidence.** `append_observation` has exactly one call site
(`apparatus.py:742`, in `Observer._observe_one`) and it always passes `condition_key(...)` — a `str`
— and `check_facts`'s return, which refuses a non-`Mapping` at `E-APPARATUS-RETURN`. So core cannot
write any of these three shapes: each needs a **hand-edited or truncated** ledger. That is exactly the
class `E-FREEZE-LEDGER-UNREADABLE` exists for, and it is still a Major on both halves: a raw
`AttributeError` traceback out of a console command is never the right answer, and the `condition:
42` arm is worse than a traceback because it reaches `freeze`'s **verdict** — exit 0, every condition
`unchanged` — over a ledger nobody should trust.

### Major 3 — both warnings Decision 10's verdict table specifies at `freeze` are unpinned

`src/publishable/freeze.py:398-427` (`_warn_lock_moved`) and `:504-507` (the `warn_unanswered`
block).

- `W-FREEZE-LOCK-MOVED` has **no occurrence anywhere in `tests/`** (grepped `tests/`, `src/`, and the
  four documents by name). Replacing `_warn_lock_moved`'s body with an immediate `return` leaves
  `tests/test_freeze.py`, `tests/test_apparatus.py` and `tests/test_cli.py` **green — 464 passed, 1
  skipped.** § Operation commands requires the report (*"a moved lockfile is reported too"*), so the
  whole warning can be deleted and nothing notices.
- Deleting the four-line `warn_unanswered` block leaves `tests/test_freeze.py` green (27 passed), so
  `W-APPARATUS-UNANSWERED` at `freeze` — Decision 10's fourth row — is unpinned too.

Both **work**: I verified `W-FREEZE-LOCK-MOVED` fires when the captured copy and the repo's lockfile
disagree, and stays silent when nothing was captured. `CLAUDE.md`'s row is *"five times in three
slices a correct fix shipped unpinned — verify by probe, then pin by mutation."* This is the sixth
and seventh.

### Minor 1 — Decision 10's exit-0 output and Decision 8's count are both unmet, and neither is disclosed or filed

`src/publishable/freeze.py:500-502`.

Decision 10's table: *"Every fact agrees with its first answered observation | **the observation**,
per condition | `0`"*. Decision 8: *"It then probes once per resolved condition — that is its whole
per-invocation cost, and **the output states the count**."* What a real exit-0 invocation prints,
captured through `main` on a three-condition sweep:

```
  00_model=m1  unchanged
  01_model=m2  unchanged
  02_model=m3  unchanged
```

No observed fact, no count. `reference.md` § Operation commands shows no worked `freeze` output, so
nothing overrides the two rulings. The report claims Decision 10's split and Decision 11's writes
verbatim and says nothing about the print shape. `CLAUDE.md`'s standing rule is that where the code
cannot follow the document, **the document changes first** and the gap is recorded in
`spec-defects.md` rather than diverged from silently; neither happened. Consequence is low — the
ledger holds every observation, so nothing is lost — but a scheduled `freeze` whose entire value is
*when you find out* now prints a verdict word where the design specified the evidence.

### Minor 2 — `replay_ledger`'s not-a-mapping guard cannot fail

`src/publishable/apparatus.py:580`; `tests/test_apparatus.py:1151-1170`, arm `not-a-mapping`.

Deleting that guard entirely leaves **all three arms green**. The `[1, 2, 3]` fixture is caught by
the *next* guard instead: `"phase" not in [1, 2, 3]` is `True`, so the missing-keys check raises the
same code. The guard is genuinely reachable (a JSON array literally containing `"phase"`,
`"condition"` and `"facts"` reaches `doc["phase"]` and raises `TypeError`), so this is an unpinned
guard rather than dead code — § Writing checks that can fail's *a fixture whose numbers agree with
the bug*. The `missing-facts` arm **does** discriminate its guard: deleting it fails that arm alone,
on a `KeyError`.

### Minor 3 — the report's "ten `NOT BUILT` rows" is eleven

`.superpowers/sdd/2026-08-20-diff-freeze/task-b4-report.md`, task 6 section. Measured through the
test's own parser: `_status_tables()["Command"]` holds **11** `NOT BUILT` rows after `freeze`'s flip,
and `NOT_BUILT_COMMANDS` holds the same 11 keys. Ten is the plan's figure for *after **both**
flips* (correction 1), carried as a measurement of the current state. The conclusion the number was
offered for — that the `{"built", "NOT BUILT"}` control does not go vacuous — holds, and I confirmed
it by running both CLI-table tests. Same shape as batch 3's three Minors: a claim broader than its
evidence.

### Minor 4 — `_warn_lock_moved`'s docstring claims a guarantee for a side the code does not guard

`src/publishable/freeze.py:406-412`: *"**Absent on either side is not a move.**"* The code checks the
captured side only (`:413`). Verified by running: captured copy present, the repo's `uv.lock`
**deleted**, `freeze` **warns** `W-FREEZE-LOCK-MOVED` — because `uv_lock_info` returns `(None, None)`
for a missing file and `None != captured_hash`. The behaviour is arguably right (a deleted lockfile
is an environment move); the sentence is not. Per *prefer deleting a claim to rewriting it*, narrow
it to the captured side.

### Minor 5 — the new `spec-defects.md` entry mis-attributes the claim it turns on

`docs/superpowers/spec-defects.md`, the `discover_local` entry: *"which would make `freeze`'s own
'resolves the template NOW' claim (`reference.md` § Operation commands) imprecise."* Grepped: the
phrase *resolves the template NOW* exists at exactly one site in the repo,
`src/publishable/freeze.py:342`, a code comment. § Operation commands says nothing of the kind. The
filing's option (b) is the one that would oblige a document correction, so the site it names is
load-bearing for its own remedy. The same paragraph's opening — *"Either (a) pass `check=False` is
not an option — the cache still gets consulted — so the fix is more likely…"* — is garbled where it
is most actionable.

### Minor 6 — the filing's owner is `unassigned`

`CLAUDE.md`: *a ledger line saying "filed" is not a filing*, and *re-owner a deferral when the slice
that filed it finishes* — an entry pointing at nobody is the shape that row warns about, and
`field_convention` "owned by nobody" is cited in `CLAUDE.md` as a live problem rather than a resting
state. `discovery.py` is H7a's and H7a merged. Either half of the filing's own remedy has an owner
available: option (b) is a `reference.md`/`freeze.py` correction this slice's task 12 could take,
and option (a) sits naturally with **H9**, which resolves the same template from the same two
artifacts for `resume`. Route it rather than leaving it unowned.

### Minor 7 — no gate for a run directory that does not exist

`src/publishable/freeze.py:132-142`. `main(["freeze", "/nope/nope"])` → `E-FREEZE-NO-CONFIG`, exit 1,
with the remedy *"the run was started by a build before this artifact existed, or the directory was
edited."* A typo'd path and a config path passed by mistake both land there. Decision 12's test for a
split is *"each row's remedy is different"*, and this input's remedy is neither of that row's. The
shipped precedent Decision 4 already cites for `diff` is `validate`'s `E-IO-FAILED` at exit 1, and I
confirmed by running that `validate` answers a missing **directory** the same way — `E-IO-FAILED`,
exit 1 — not only the missing config path the design's measurement table records.

### Minor 8 — the exit-1 and exit-5 disk claims were measured on fixtures too small to distinguish them

`tests/test_freeze.py:590` (F2) and `:615` (F5 arm one) both build **one** condition (`sweep={}`).
The report's claims are *"lines are appended for every condition up to and including the first mover,
and none after"* and *"no line for any condition after it either"* — properties a one-condition
fixture cannot see, argued from the loop's shape and reported as measured. § Writing checks that can
fail: *a fixture with too few elements to distinguish the candidate orderings.*

**Both claims are true.** I built three conditions with the **second** one moving, through `main`:
exit 1, `E-APPARATUS-CHANGED`, and exactly the `00_model=m1` and `01_model=m2` lines appended, none
for `02_model=m3`. Then three conditions with the **second** one raising: exit 5,
`E-APPARATUS-RAISED`, and only the `00_model=m1` line — none for the raising condition, none after.
In both cases the whole run directory was otherwise byte-identical. So this is an evidence gap and an
unpinned property, not a defect.

### Minor 9 — `apparatus/probes.jsonl` is read three times per invocation, and gate (i)'s baseline is discarded

`src/publishable/freeze.py:325` (gate (i)), `:345` (`_ledger_probe_names`), `:471` (a second
`replay_ledger`). The `baseline` computed at `:325` is used only for its `facts_document()`
emptiness test and then thrown away; `:471` recomputes it. Correct, and the `_ledger_probe_names`
docstring's claim that it runs only after gate (i) validated every line does hold (gate (j) follows
gate (i)) — but `_Ready` already carries seven fields and could carry the baseline as an eighth.

---

## Adjudications the brief asked for

**Attack 3 — Decision 9's exclusion. Not a Critical; verified by running.** Two `freeze`
invocations on a three-condition mid-run directory: the first exits 0 and appends three `phase:
"freeze"` lines. Moving the fact for every condition and freezing again gives exit 1 and
`E-APPARATUS-CHANGED` — compared against the run's own `run_start` baseline, **not** against
`freeze` #1's line. Restoring the original answers and freezing a third time gives exit 0 again.
`freeze` does not pin itself. The shipped M8 test (`tests/test_freeze.py:677`) exercises the same
exclusion through a `null → rev1 → rev2` path where both calls exit 0 under the shipped filter; the
moved-from-a-real-baseline form above is the stronger discriminator and the suite does not hold it.
Separately confirmed that gate (j)'s `_ledger_probe_names` filters on the same two phases, so a
`freeze` line cannot pollute the probe-name check either.

**Attack 2 — the four disk verdicts, all four re-verified at `main`.** Exit 0: a whole-tree
`{relative path: bytes}` snapshot of the **results directory** (not just the run directory —
`latest` and its siblings included), excluding only `apparatus/probes.jsonl`, is byte-identical
before and after, with `lock` present in the snapshot on both sides; `run.yaml` still absent;
exactly one `phase: "freeze"` line per condition. Exit 1 and exit 5: the three-condition results
above, each with the same byte-identical snapshot. Every `_precheck` refusal: zero lines — all 19
refusal arms in `tests/test_freeze.py` route through `_assert_refused`, which asserts it, so
`_Refused`'s docstring claim that *Fixture F4 pins the second half for every arm* is accurate.
Decision 11's other halves: no lock is taken (the report's M10 revert holds — I re-ran it
implicitly through the snapshot), no status is touched, and a run **holding `run.yaml`** is refused
through `main` at `E-FREEZE-RUN-ENDED` with the entire tree — `run.yaml` included — byte-identical.

**Attack 5 — plan correction 6's states, and the redaction.** All four codes have named arms at HEAD
(`E-TEMPLATE-UNKNOWN`, `-INSTALLED-UNSUPPORTED`, `-LOAD`, `-COLLISION`), and all seven `E-FREEZE-*`
codes do too — the code-by-code grep is in the table below. The plan's fifth state,
**local-without-root**, folds into `E-TEMPLATE-UNKNOWN` and has no arm of its own; I reached it by
repointing `environment/repo_root.txt` at an empty directory and got `E-TEMPLATE-UNKNOWN`, exit 1,
zero ledger lines. Redaction, both new sites, verified by running with a declared credential whose
value appears in the exception text: a `_probe_for` dispatch raise (`freeze.py:461-469`) → exit 1,
value absent from stderr; and a `templates/*.py` that raises at import, routed through
`partial_templates` (`freeze.py:190-196`) → `E-TEMPLATE-LOAD`, exit 1, value absent, zero ledger
lines. The shipped F5 arm one covers the third site. No leak found.

**Attack 6 — the `Status` flip.** Arm (`cli.py:3738-3745`), key (`OPERATION_COMMANDS` at `:136`,
`freeze` gone from `NOT_BUILT_COMMANDS` at `:146`) and cell (`reference.md`'s Command table, `built`)
all moved in the one commit `6258b26`. Both CLI-table tests pass unedited. Both directions probed
through `main`: `["freeze", "a", "b"]` → *"`freeze` takes exactly one path and no flags"*, exit 2 —
**not** the specified-but-unbuilt prefix, and not `unknown command`; `["freeze", <dir>]` dispatches.
Correction 3's two quoted-literal sites are handled by **deletion** with the claim intact
(`artifacts.py`, `reference.md` § Resuming), and the literal survives nowhere outside `cli.py`
itself — swept `docs/`, `src/`, `tests/`, `CLAUDE.md`, `README.md` by name.

**Attack 7a — the brief disagreement. The reading was right and it cost nothing.** Task 4's
Interfaces section omits `sweep.expand`/`resolve_condition_cfg` while its step-11 prose describes
eleven Fixture F4 arms; the implementer followed Interfaces and split the two `PLAN-*` arms into task
5. At HEAD all eleven exist, each asserting its own code:

| Code | Arms |
|---|---|
| `E-FREEZE-RUN-ENDED` | 2 (one at `_precheck`, one at `command_freeze` — M11's discriminator) |
| `E-FREEZE-NO-CONFIG` | 4 (absent, not-a-mapping, `repo_root.txt` absent, `repo_root.txt` empty) |
| `E-FREEZE-NO-APPARATUS` | 1 |
| `E-FREEZE-LEDGER-MISSING` | 2 (absent file, no qualifying line) |
| `E-FREEZE-PROBE-MISMATCH` | 2 |
| `E-FREEZE-PLAN-MISSING` | 2 (absent, unreadable) |
| `E-FREEZE-PLAN-MISMATCH` | 2 (structural edit, `values`-only edit) |
| the four reused template codes | 1 each |

The `values`-only arm is the one plan correction 8 exists for, and its test asserts all four recorded
fields are equal across the edit **before** calling `_precheck` — the "check the two branches can
differ" instruction honoured rather than skipped.

**Attack 7b — the `discover_local` filing.** Correctly scoped and honestly measured: it names the
loader, the `(mtime, size)` key, the whole-second granularity, the reproduction with no test harness,
the `time.sleep` control, the `print()` sensitivity that makes it read as flakiness, and the
workaround this batch took in its own fixtures (a new filename rather than an in-place overwrite)
rather than claiming a fix. It is right that it bears on `E-FREEZE-PROBE-MISMATCH`'s premise, and
right not to fix `discovery.py` from a `freeze` task. Two defects, both above: the mis-attributed
citation (Minor 4) and the missing owner (Minor 5).

**Attack 8 — prose and pins.** The guard pin's final arms did not fire (full suite green). § Errors
rows: **grepped before asserting** — no `E-FREEZE-*` or `W-FREEZE-*` row exists in `reference.md`
§ Errors, which is **correct**, they are task 12's; the one `E-FREEZE-` mention in the four documents
is prose at `reference.md:846`, placed by batch 1's document task. The live disagreement between
`E-APPARATUS-CHANGED`'s § Errors row (exit `4`) and `freeze`'s exit `1` for the same code is
**explicitly task 12's**, named in the plan's B7 row, so it is not a batch-4 finding. The two lines
batch 4 changed in `reference.md` carry no positional locator, no count phrase, no `x`-for-`×`, and
no config-count claim; neither does the report. A mechanical pass over the four documents by name
(anchors, duplicate anchors, relative links, fragments, table column counts, trailing whitespace,
tabs, invisible unicode, fences skipped) surfaced nothing attributable to this batch — its 24 hits
are all my slugger's own artifacts on `&`-bearing headings and cells with escaped pipes, on lines
this batch never touched.

**One docstring claim mutated rather than read.** `Observer`'s new `observations=` keyword is pinned:
dropping `observations=baseline` at `freeze.py:480` fails `test_f2_freeze_sees_a_moved_fact` with
exit 0 where 1 is expected — which is exactly the hazard the plan's § What could not be measured
named, and it is closed.

## What I could not check

- **Fixture F3 against a live lock** — I read the test rather than rebuilding the second-process
  handshake. It does use `subprocess.Popen` with a real held lock and a `finally` that releases, and
  it blocks inside a **step** rather than the probe, which is the right shape; I did not run a
  concurrency probe of my own.
- **Whether the `condition: 42` int-keyed baseline can produce a *false unchanged* on a run whose
  fact really moved.** I confirmed the int key is accepted and that `freeze` exits 0; I did not
  construct the pair where the int-keyed entry shadows a real one.
- **The `.pyc` staleness defect itself** — I took the filing's reproduction on its face and did not
  re-run it. My own fixtures wrote each edited template under a new filename, so I never exercised
  the path.
- **`freeze` through the installed console script.** Every invocation went through `main([...])` in
  process, which is what the harness needs to install a synthetic probe distribution; the one-path
  and dispatch checks were also run through a separate `uv run python -c` process.
