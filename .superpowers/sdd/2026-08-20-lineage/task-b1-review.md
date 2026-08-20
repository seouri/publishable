# Review — batch B1 (task 11, the guard pin; task 1, `read_run_record`)

Branch `h8a-lineage`, reviewed at `3ddf13a` against `main` at `28e311d`.
Everything below marked **verified by running** was run in the foreground in this session and its
output read. Nothing was inferred from a `git status`; every revert was verified by `diff` against a
pre-mutation copy in the scratchpad and by re-running the suite to 2470.

## Verdicts

**Spec compliance: PASS.** Both tasks build what the design's Decision 3 and the plan's task 11
specify, and nothing outside them. `read_run_record` imports `run_record.SCHEMA_VERSION` rather than
restating it; the three record refusals carry the three prescribed codes; a `partial`/`failed` record
is not refused and no comment claims that case unreachable; the module docstring states the import
direction and the measured cycle; `errors.py` is untouched, so the `ArtifactError` gloss is neither
fixed nor repeated (task 9's), and `lineage.py` raises only `ContractError`, so the false gloss is
not even adjacent. No sentence anywhere in the batch claims a config count moved. The four guard-pin
arms were captured from real runs, not transcribed — arm C in particular reads the generated step's
name **back** from the produced record and asserts it is *not* `step09_publish`, which is the plan's
correction 8 confirmed empirically rather than trusted.

**Task quality: PASS with findings.** Six Minors, no Major, none blocking. The most consequential is
that **one of the three `-UNREADABLE` faults the docstring enumerates is blind to the suite** — the
not-a-mapping guard can be deleted with all 2470 tests still green. The second is a gap in the
authorized-editor mechanism: the twelve-key `provenance` list is pinned in a **second** place carrying
no authorization clause. Three of the four arms turn out to have shipped predecessors, which the report
does not mention. The blind `SCHEMA_VERSION` mutation was reported honestly and the property behind it
is in fact pinned — better than the report claims.

## On the authorized-editor mechanism (attack 1)

**Sound as a mechanism, not a loophole** — on four checkable properties rather than an opinion: the
post-edit state is specified *in advance* (`upstream` appended after `allocation_hash`, nothing
reordered), the editor is **one named task** rather than a class of tasks, a post-hoc verification
obligation is stated (task 7's report must show the diff is exactly that one key), and the clause sits
on **arm B only**, so it cannot spread. Remove any one of those and it becomes a licence. Its only
enforcement is prose — nothing stops another task editing arm B and asserting authorization — but that
residual risk is strictly smaller than the alternative it replaces, which is a change detector the
slice must weaken silently. See finding **m2** for the one place it does not reach.

### All four arms, discriminated by running

Every mutation below was applied to `src/`, run against the **full unfiltered** suite, and reverted.

| Arm | Mutation | Result |
|---|---|---|
| A | spurious top-level key in `assemble_run_yaml`'s returned dict (`run_record.py`) | **arm A FAILED**, arm B passed. 3 failed, 2467 passed |
| B | the prescribed `"stopped_at": None,` in `cli.py`'s `provenance` dict | **arm B FAILED**, arm A passed — the required asymmetry. 2 failed, 2468 passed |
| C | `_execution_block`'s `elif e.scope == "summary"` routed into `shared` | **arm C FAILED**. 4 failed, 2466 passed. Decision 4's foundation is defended — something *can* break it |
| D | `read_upstream`'s `run`-scope base renamed from `shared` | **arm D FAILED**, together with 11 shipped tests including its immediate neighbour. 12 failed, 2458 passed |

## Findings

### Minor — ranked most consequential first

**m1. One of the three `-UNREADABLE` faults is blind: the not-a-mapping guard can be deleted with the
full suite green.** `src/publishable/lineage.py:61`, `if not isinstance(doc, dict):`.
*Verified by running,* against the **full unfiltered** suite: **2470 passed, 1 skipped, 2 xfailed** with
that branch neutered. The not-a-mapping fixture writes `- just\n- a\n- list\n`, which parses to a
`list`; with the guard gone, control falls to `if "run_id" not in doc`, which is **list membership**,
`True`, and raises `E-UPSTREAM-RECORD-UNREADABLE` from a different site with a different message.
`test_a_yaml_document_that_is_not_a_mapping_is_record_unreadable` (`tests/test_lineage.py:48`) asserts
`e.value.code` only, so it passes against a mutant that never executed the guard it exists to cover.
The **code** `-UNREADABLE` is pinned three ways over; the *not-a-mapping* **fault** is pinned by nothing.
This is `CLAUDE.md`'s *a seam named in the brief and instantiated by no fixture*, one level below where
the brief drew the line — and the slice's own stated lesson is H4d's, that one code returning for
several distinct faults cannot be told apart. The code is correct; the pin is partial, which is why
this is a Minor by consequence and first by importance.
*Remedy:* assert on message text in the two `-UNREADABLE` arms that share the code — `"did not parse to
a mapping"` versus `"has no \`run_id\`"`. One line in each of two tests, and the docstring's three-way
split becomes true. **Not fixed here** — this is a review, and the fix belongs to a task with a report.

**m2. The twelve-key `provenance` list is pinned twice, and only one of the two pins names an
authorized editor — so task 7 must edit an unnamed shipped assertion.**
`tests/test_cli.py:12898`, inside
`test_a_run_with_no_declared_probe_records_a_null_apparatus_block_and_no_ledger` (H7d Part A's),
asserts `list(run["provenance"]) == [...]` over the **same twelve keys**, and its own docstring says
the full list is asserted deliberately: *"a sub-key or a sibling … an assertion on `apparatus` alone
would not see it."* Task 11's arm B (`tests/test_cli.py:15340`) carries the authorization clause; that
test carries none.
*Verified by running:* the prescribed arm B mutation failed **both** tests
(`test_a_run_with_no_declared_probe_records_a_null_apparatus_block_and_no_ledger` and
`test_h8a_arm_b_the_provenance_key_list_and_no_upstream_key`), and by reading the shipped test's
assertion and docstring.
*Why it matters, and why it is a Minor:* task 7 appends `upstream` unconditionally, so that shipped
assertion fails too, and task 7 will edit a pin whose docstring argues for the whole list with no clause
authorizing it. What is missing is a **clause**, not a guard — the unnamed pin hard-fails, and a pin that
fails loudly is not the quiet weakening the mechanism exists to prevent. B1 also could not have fixed it:
adding a clause there means editing a shipped H7d assertion, which is exactly what this batch was told
not to do. The mechanism is sound but **not total**: it bounds one of the two places the key list lives.
*Remedy, cheapest first:* the batch that reaches task 7 should extend arm B's clause to name the
shipped assertion as the second authorized edit (same one key appended, nothing reordered), and task
7's report must show **both** diffs. This is a finding to carry forward, not a defect in what shipped.

**m3. Three of the four arms restate a shipped pin, and the report does not say so.**
Arm A (`tests/test_cli.py:15311`) asserts the same three things as the shipped
`test_a_clean_run_completes_with_the_full_run_yaml_shape` (`tests/test_cli.py:14232`): `status ==
"completed"`, the identical eleven-key top-level list *as a list*, and `len(executions.jsonl) ==
len(execution_order)`. Arm B duplicates the provenance list per **m2**. Arm D is a restatement of its
own immediate neighbour, `test_a_narrower_step_reads_a_wider_one_normally`, differing only in step name
and payload.
*Verified by running:* the arm A mutation failed both arm A and the shipped test; the arm B mutation
failed both arm B and the shipped provenance test; the arm D mutation failed arm D together with 11
shipped tests including that neighbour, so **no mutation isolates arm D**. *Verified by reading:* all
three shipped tests' assertion bodies.
**Arm C is the one arm carrying genuinely new discriminating power** — it is the only named pin of the
`shared`/`summary` routing Decision 4 rests on, and B2–B6 should watch it above the other three. Not a
defect: the brief prescribed all four and re-capturing by running was the point. But the report's "how
each literal was captured" section should have recorded which arms had shipped predecessors, because a
reviewer weighing the pin's marginal value cannot see it otherwise.

**m4. Arm A's docstring claims a guarantee it does not provide.** `tests/test_cli.py:15313`: *"a key
added by accident **anywhere in this slice** is exactly what a full-list assertion catches."* It is
blind to a key written only on a stop path — the shipped predecessor's own docstring
(`tests/test_cli.py:14244`) records exactly that boundary in writing (*"blind to a key written only on
a STOP path"*) and arm A's does not carry it forward. This is `CLAUDE.md`'s *docstring claiming a
guarantee the code does not provide*. *Verified by reading both docstrings.* **Prefer deletion:** cut
the words "anywhere in this slice" rather than importing a boundary paragraph.

**m5. A shipped test file cites an untracked, regenerable file.** `tests/test_artifacts.py:954` (arm
D's docstring) cites `.superpowers/sdd/2026-08-20-lineage/task-11-brief.md`.
*Verified by running:* `git ls-files .superpowers/sdd/2026-08-20-lineage/` returns only `progress.md`
and `task-b1-report.md`; `.superpowers/sdd/.gitignore` ignores `task-*-brief.md` as *"extracted
mechanically from the plan"*. So a shipped source file points at something git does not hold. The plan
citation beside it is the durable one — **delete the brief citation, do not rewrite it.** The sweep named
`tests/` as a whole rather than spot-checking one file: `grep -rn "\.superpowers/sdd" tests/` returns this
one hit, so the three arms in `tests/test_cli.py` are clean.

**m6. `lineage.py`'s module docstring closes with a clause that concedes its own argument.**
`src/publishable/lineage.py:10`: *"`run_record.py` itself is refused as the reader's home on the
same grounds … and on that identical cycle, **since a reader living there would need no import of
itself**."* The subordinate clause states the cycle does not bite in that case, while the sentence
cites the cycle as grounds. The docstring's real ground for refusing `run_record.py` is the one it
already gave — *assembles only, computes nothing* — which stands on its own. Per `CLAUDE.md`, **delete
the cycle half of that sentence** rather than rewriting it. *Verified by reading.*

**m7. First cross-test-module import in the suite.** `tests/test_lineage.py:11` does `from
tests.test_cli import run_a_project`; it is the only file in `tests/` that imports a helper from
another test module (`test_acceptance.py`, which also drives real runs, builds its own scaffold).
*Verified by running:* `grep -rn "run_a_project" tests/*.py | grep -v test_cli.py` returns only
`test_lineage.py`. Sanctioned by the design (Fixture R is *"produced by `run_a_project`"*) and it
passes, so this is informational: a rename or module-level state in a 15k-line test module now breaks
a second file for a reason unrelated to lineage. Worth a conftest-level home if later batches import
it too.

## Attack-by-attack

**2 — schema drift is NOT unpinned; the report understates what it has.** The prescribed mutation
(`SCHEMA_VERSION` → the literal `"1.0"`) is value-preserving, so *by definition* it is not drift and
could not discriminate; reporting it blind was correct. Drift requires two edits, and it **is caught**.
*Verified by running,* two file-scoped runs:
- writer bumped to `"1.1"` in `run_record.py`, reader's import intact → `tests/test_lineage.py` **10
  passed** (the reader tracked the writer);
- writer at `"1.1"` **and** `lineage.py` restating the literal `"1.0"` → **4 failed**, including
  `test_fixture_r_a_real_run_yaml_reads_back_what_the_writer_wrote` with
  `ContractError: … declares schema_version '1.1', which this build does not read (it reads '1.0')`.

Fixture R is the drift pin, and it is the one that holds independently of any import: the three
synthesized fixtures fail too, but only because the *test file* also imports `SCHEMA_VERSION`. So the
report's justification (*"no assertion in this slice hard-codes a version string"*) is true but weaker
than the actual state — **upgrade the claim, do not file a hole.** Note that `from publishable.run_record
import SCHEMA_VERSION` copies the binding, so a monkeypatch-based pin is impossible by construction;
that is not a defect, because the design's argument is about one literal in `src/`, which the
from-import delivers completely.

**3 — three refusals: all three codes individually reachable and individually pinned; one *sub-fault*
within `-UNREADABLE` is BLIND.** Each branch neutered in turn against the **full unfiltered** suite:

| Branch deleted | Full-suite result |
|---|---|
| `-RECORD-MISSING` (`lineage.py:49`) | **2 failed**, 2468 passed — both `-MISSING` tests |
| all three `-UNREADABLE` branches | **3 failed**, 2467 passed |
| `-RECORD-VERSION` (`lineage.py:72`) | **1 failed**, 2469 passed |
| **`if not isinstance(doc, dict)` alone** (`lineage.py:61`) | **2470 passed, 1 skipped, 2 xfailed — BLIND** |

So each of the three **codes** is individually reachable and individually pinned against the full suite,
which is what H4d's lesson asks for at the code level. The blind sub-fault is finding **m1** above,
with its mechanism, its evidence and its remedy.

**4 — arm C is measured, and it reads the name back.** `tests/test_cli.py:15401` builds
`generated_name = shared_names[0]` from the produced `run.yaml`'s own `execution.shared`, then asserts
`generated_name != "step09_publish"` with a message citing correction 8. No step-name literal is
assumed anywhere in the arm; both on-disk paths are built from the read-back name, and
`programs/gpt-4.1__seed29.json` is asserted among the summary artifacts. *Verified by running* (the arm
passes, so the prefixing is real, and the mutation above shows the routing assertion is live).

**5 — gate arithmetic confirmed, nothing deleted.** *Verified by running:* `uv run pytest -q` →
**2470 passed, 1 skipped, 2 xfailed**; `uv run mypy` → **47 source files**; `uv run ruff format
--check .` → **84 files**; `uv run ruff check .` → clean. `git diff --stat 28e311d..HEAD` shows
**1903 insertions, 0 deletions** across 7 files — nothing was silently removed. +14 tests decomposes
exactly: 10 in `tests/test_lineage.py` (8 functions, one parametrized ×2), 3 arms in `tests/test_cli.py`,
1 arm in `tests/test_artifacts.py`. The two gate literals move by exactly the two new files (46+1=47
source, 82+2=84 formatted), matching plan correction 7.

**6 — brief claims about existing code, checked myself.** Five verified, four by running:
- `run_record → runner → artifacts` — **true**: `run_record.py:10` imports `runner.ExecutionResult`,
  `runner.py:13` imports `artifacts.StepIO`, and `artifacts.py` does not import `lineage`. So
  `lineage → run_record` is acyclic and the reverse would not be. Decision 2/3's load-bearing literal.
- *"`read_upstream` and `read_condition` enforce no name rule"* — **true** by reading: both end in a
  bare `self._read(base / step / name)` (`artifacts.py:860`), with no `_resolve` on the path.
- `_nest_repeat`'s quoted docstring — **true verbatim** at `artifacts.py:802`: *"Writing it twice is
  how the two drift — which is exactly what had happened."* The argument `lineage.py` cites really is
  there.
- `run_a_project` prefixes a generated step's name — **true**, and it is arm C's own assertion.
- *"`grep -rn "reuse_from" src/publishable/` returns zero"* — **true for the pre-branch tree**; today
  the single hit is `lineage.py`'s own docstring, i.e. this branch's. Not a defect.
- One imprecision, not a defect: the brief's *"`grep -rn run_record src/publishable/` finds one hit
  outside the module"* is true of **imports** (`cli.py:58`) but not of the grep, which also matches
  three comments in `runner.py`. The conclusion it supports — no reader exists — is correct.

**7 — prose.** No docstring in the batch claims a § Errors row: `grep -rn "E-UPSTREAM" docs/reference.md`
returns **nothing**, and nothing in the batch says otherwise (task 9's). `errors.py` is absent from the
diff and `docs/reference.md:1031`'s `# core will not write this` is unchanged, so the false
`ArtifactError` gloss (plan correction 6) is neither fixed nor repeated. No counts and no positional
locators in the new prose; no `x`-for-`×`; `grep -nP "[ \t]+$|\t"` over both new files returns nothing.
Findings **m3**, **m4** and **m5** are the prose exceptions, all remediable by deletion.
One live document/code contradiction, **owned and scheduled, not this batch's**:
`docs/reference.md:3985` still reads `lineage.py … — not yet built` while the module now ships, and
`lineage.py:1` cites that very section. The plan assigns the marker to **task 9** (batch B6), so it is
contradictory for the duration of B1–B5 by design; naming it here so B6 cannot lose it.

**8 — no count claim.** *Verified by reading* the whole diff: no sentence in the report, the two source
docstrings or any new test asserts a config count. The report's only config statement is
`grep -rn "reuse_from" src/publishable/` being zero, which is a build fact about `src/`, not a count.
The four-figure table stays where the plan put it, and nothing in B1 quotes a headline number.

## What I could not check

- **The `28e311d` baseline literals (2456 / 46 / 82) directly.** I measured the post-batch endpoints by
  running and confirmed the arithmetic from a diff with 0 deletions and exactly two new files; I did not
  check out the parent commit to re-measure the three baseline numbers themselves.
- **Whether task 7 will honour the authorized-edit clause**, which is the mechanism's only real risk and
  is unobservable until B5.
- **Anything downstream of the reader.** Nothing in this batch is reachable from a step — no
  `reuse_from`, no resolver, no `StepIO` change — so no end-to-end lineage behaviour existed to review,
  which is the seam B1 was cut on.

## Tree state

**No tracked file modified.** `git status --short` shows exactly one entry, and it is this review file,
untracked — the deliverable itself. Four source files were mutated during this review
(`lineage.py`, `run_record.py`, `cli.py`, `artifacts.py`); each was copied to the scratchpad first,
reverted by rewriting the original bytes, and confirmed byte-identical by `diff -q` against its copy —
never by `git checkout`. The full suite was re-run **after** the last revert: **2470 passed, 1 skipped, 2
xfailed**, with `ruff check`, `ruff format --check` (84) and `mypy` (47) all clean. The only edits since
that run are to this review file.
