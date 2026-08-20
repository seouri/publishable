# H7d Part A — whole-branch review

**Reviewed 2026-08-19 against `h7d-apparatus-part-a` at `48bc9e2`** (17 tasks, 5 batches, 41
commits ahead of `main`). Independent of the five batch reviews; findings already closed and
verified in `progress.md` are not re-litigated.

## Verdict: **MERGE, with three items owed at the merge commit**

No Critical. Three Major, four Minor. None of the Majors is a regression, a false test, or an
unreached check — the branch's behaviour is what the design describes and what the reports claim,
and every claim I tested by running held. All three are gaps at seams no per-batch review could
see: a fail-open predicate on `apparatus_probe` that this slice's own semantics turned into a
false record again, a credential check strictly weaker than the redaction over the same value set,
and a sentence this branch wrote pointing at a section that does not answer it. Each is a filing
or a one-line narrowing, not a rebuild.

**Owed at the merge commit, named here so they do not evaporate behind the verdict:**

1. **`progress.md`'s batch-5 entry** — the ledger stops at batch 4 and batch 5 was never reviewed
   (Minor 4). It is the tracked artifact; it must carry tasks 14/16/17 and this review's findings.
2. **`CLAUDE.md`'s H7d Part A paragraph**, plus the amendment to its H7b Part B paragraph, which
   still says *"`cli.py` writes `apparatus: null` unconditionally regardless of what a template
   declares — filed, owned by H7d"* — falsified by this branch. This repo's own pattern is a
   separate `docs: CLAUDE.md records <slice>` commit (`7fb413d` for H4d), and the H4b-1 entry
   models the amendment form.
3. **A dated § Executability entry in the feasibility analysis** — Major 3, because a sentence this
   branch authored points a reader at that section for an answer it does not contain. The content
   is my re-measurement in § 7 below.

Major 1 and Major 2 need an owner, in `spec-defects.md`, before or at merge; neither needs a code
change to merge.

## Gates, verified by running

| Gate | Result |
|---|---|
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 82 files already formatted |
| `uv run mypy` | no issues, **46 source files** |
| `uv run pytest` | **2418 passed, 1 skipped, 2 xfailed** (157 s) |

`git status` clean and `git diff` empty after every mutation below was reverted **by editing the
file back** and re-verified by re-running. `.superpowers/sdd/.gitignore` intact (not clobbered).
Zero deleted lines in every test file across the whole branch (`git diff --numstat`:
`test_cli.py` 1228/0, `test_apparatus.py` 557/0, `test_validate.py` 63/0) — no existing pin was
weakened. `cli.py` is 108/20, the 20 being the re-indented `execute_plan` call and the literal
`"apparatus": None`.

---

## What I verified by running

### 1. The call-count contract, on my own fixture

Built the design's **actual** Fixture F shape rather than the plan's reduced one, plus a summary
step: `sweep.grid` over one axis with two levels (**C = 2**), a `run`-scoped step, a
`condition`-scoped step, a `repeat`-scoped step at `n = 1`, and a `summary` step — 6 executions,
**E_c = 2 + 2 = 4**, **E_none = 2**. `C + E_c + C × E_none = 2 + 4 + 2×2 = **10**`, recomputed by
hand before the run.

Measured: **10 ledger lines**, and the ordered `(phase, condition)` list is

```
run_start 00_model=m1 · run_start 01_model=m2
pre_execution 00 · pre_execution 01          (the run-scoped execution, once per condition)
pre_execution 00 · pre_execution 00          (condition step, then repeat step, condition 0)
pre_execution 01 · pre_execution 01          (same, condition 1)
pre_execution 00 · pre_execution 01          (the summary execution, once per condition, LAST)
```

The summary execution — Decision 3's motivating case, and the one the plan's own fixture omits —
is probed once per condition and runs last. Both rejected readings are excluded by the pair list,
not by the count.

### 2. `provenance.apparatus`, the hash, and the null accounting

From the same run: `list(block) == ["probe", "ledger", "hash", "facts", "unobserved"]`, `probe`
the declared name, `ledger` the relative path, `facts` keyed by both `<nn>_<label>` condition
keys. The hash **recomputed** from the `facts` mapping parsed out of `run.yaml` with
`json.dumps(..., sort_keys=True, separators=(",",":"), ensure_ascii=False)` matched the recorded
digest exactly — never compared against a literal.

Null accounting, with a fact answered for one condition and `None` for the other over 10 calls:
`flaky_pin → {null_probes: 5, total_probes: 10}`, `model_revision → {null_probes: 0,
total_probes: 10}`, `facts[00].flaky_pin is None`, `facts[01].flaky_pin == "pinned"`, and
`W-APPARATUS-UNANSWERED` printed **exactly once** on stdout. An **undeclared** returned fact
(`undeclared_extra: 7`) is present in `facts` and in **every** ledger line and **absent** from
`unobserved` — Decision 4's fourth row, confirmed end to end.

### 3. Part A cannot stop a run (brief area 6)

A probe that raises on its **sixth** call — after the run-start round, the `run`-scoped execution
and the condition-0 condition-scoped execution had all completed:

- exit **1** (`EXIT_WRONG`), **never 5**;
- **no `run.yaml`**; run directory holds `apparatus/ conditions/ environment/ executions.jsonl
  manifest/ shared/ sweep.yaml` — the same shape any other pre-`run.yaml` failure leaves;
- **no `status:` in any byte of the run directory**, asserted over every file;
- `results/latest` **not created** — `point_latest` is skipped, as the wrapper's own comment
  claims;
- the ledger holds the **5** observations that preceded the failure, in order;
- stderr carries `E-APPARATUS-RAISED` at `experiment_type`.

So Part A refuses at command level and neither truncates a plan nor writes a `status`. Decision 12
holds. Read the code as well: `observer.observe_round(...)` sits at the **top** of
`execute_plan`'s loop, outside the per-execution `except Exception  # a failed execution never
stops the run` (runner.py:589 vs runner.py:719) — so a probe raise cannot be swallowed as a failed
execution, which would have made the redaction path unreachable.

### 4. The credential story, both mechanisms, at both reachable commands

- **Returned credential** (ordinary-looking value `lab7`, a declared `required_env`):
  exit 1, `E-APPARATUS-FACT-CREDENTIAL` at `experiment_type`, **no `run.yaml`**, and `b"lab7"` in
  **no byte** of the run directory, asserted on raw bytes of every file.
- **Probe entry point raising at import** with the credential in its message: exit 1,
  `E-PLUGIN-LOAD`, `lab7` absent from stdout and stderr, `<redacted:WBR_TOKEN>` present in the
  diagnostic. This is batch 3's Critical, independently reproduced on my own template, credential
  and module through the real `main(["run", ...])`.
- **Enumerated by reading, grep after**, per `CLAUDE.md`: the streams a probe exception can reach
  are (a) `apparatus._probe_for`'s dispatch — wrapped in `command_run`'s own redacting
  `except BaseException`; (b) `observe_once` at the run-start round and (c) inside `execute_plan`
  — both inside the single `except ContractError` filtered on `apparatus.APPARATUS_CODES` and
  redacted through a fresh credential-bearing `Collector`; (d) `KeyboardInterrupt`, deliberately
  re-raised fresh and argument-less so it carries no message; (e) `append_observation`'s `OSError`
  and `Observer.block()`/`apparatus_hash`, neither of which touches user code or a credential.
  `main`'s bare `{exc}` `PublishableError` handler is reachable only by codes outside
  `APPARATUS_CODES`, which are core's own (`E-RUN-CFG-MISSING`, `E-RUN-SEED-MISSING`) and unchanged
  by this slice.
- **Mutation, whole-branch:** replacing the `APPARATUS_CODES` filter with `if True: raise` — i.e.
  removing the containment entirely — fails **5** tests in `test_cli.py`, including the credential
  and raise tests and all three `..._is_individually_pinned_through_the_wrapper` tests. So every
  one of the five members is reached from a real `run` and pinned, which is what batch 3's fix
  round claimed. Reverted by editing back; `diff` against the pre-mutation copy byte-identical;
  re-ran green.

### 5. The guard pin's whole life (brief area 4) — both claims true

`git show 7568a34:tests/test_cli.py` sliced to the pin's body versus HEAD lines 12851–12884:
**byte-identical**, `diff` empty. Still discriminating: mutating `cli.py` to
`"apparatus": observer.block() if observer is not None else {"probe": None}` — the exact `probe:
null` spelling Decision 7 rejects — fails the pin on
`AssertionError: assert {'probe': None} is None`. Reverted by editing back (byte-identical to a
saved copy), re-ran, passes.

### 6. Two further whole-branch mutations, both caught

- `Observations.record`'s **first-answered-wins** → last-answered-wins: fails
  `test_the_first_answered_observation_wins_and_a_never_answered_fact_stays_null` on `r1` vs `r2`.
  The semantic is grounded: `reference.md` § The apparatus files says in so many words
  *"`provenance.apparatus.facts` in `run.yaml` is the first **answered** observation of each
  fact"* — the code did not mint an undocumented record semantic.
- Removing the **declared-facts narrowing** from `Observations.unobserved` *and*
  `warn_unanswered` together: fails 3 tests across both files, including the undeclared-fact
  absence assertion paired with its presence assertion. The seam batch 2's review found is pinned
  in both projections.

Both reverted from a saved copy; `git status` clean; suite re-run at 2418.

### 7. The figures (brief area 8) — re-measured, unmoved

Re-measured **E1** and **C1** myself through `validate_config` on a synthetic 450-row table
carrying every attribute both configs declare, transplanting each config's `data.units` and
`statistics` blocks verbatim (`weight_by: sampling_weight`, `resample.stratify_by`, `report_by`,
`holdout`, `null_test: null`):

| Config | Codes reported |
|---|---|
| E1 | `E-NAME-DIR`, `W-DATA-CLUSTER-UNDECLARED`, `W-TEMPLATE-VERSION` |
| C1 | `E-NAME-DIR`, `W-DATA-CLUSTER-UNDECLARED`, `W-TEMPLATE-VERSION` |
| E1 with `holdout.frac → 0` (**can-fail control**) | the same **plus** `E-DATA-HOLDOUT-FRAC` |

`E-NAME-DIR` and `W-TEMPLATE-VERSION` are artifacts of my harness (the config not living under
`configs/<name>/`, and a stand-in `template_version`), not of the designs. **No `E-APPARATUS-*`
and no `E-PROBE-UNKNOWN` on either**, and none is reachable for any of the nine: `generic`
declares no `apparatus_probe`, so `command_run` never constructs an `Observer`. **Zero configs
unblocked; six with no remaining core-side blocker; three executable — all three unmoved**, and
the only direction available is down. Swept the four documents, `CLAUDE.md` and the feasibility
analysis for a sentence converting the six into an execution count: none exists.

### 8. Invariants (brief area 5)

- **Three hashes, split on purpose.** `hashes.py` is **absent from the branch diff entirely**;
  `HASHED_TREES` is unchanged (`("src", "templates")`); `apparatus_hash` lives in `apparatus.py`
  beside the builder of the mapping it hashes, on `manifest_hash`'s and `allocation_hash`'s
  precedent. Not a fourth hash.
- **`batch` and the apparatus stay independent.** `validate.py:3805` derives `W-REPL-DETERMINISTIC`
  from `getattr(s, "nondeterministic", False)` over the step classes; `replication.py` and
  `sweep.py`'s `batch` handling name nothing in `apparatus.py`, and `apparatus.py` names nothing in
  either. Still independent in code, as the scoping measured. (The *test* asserting it is Part B's,
  correctly.)
- **Operation commands take paths and nothing else.** No parser or argv change in the branch diff;
  `run` and `validate` are the only built commands (`grep '^def command_'` → two), so
  `execute_plan` has exactly **one** production caller and there is no second, unwrapped executing
  path. Confirmed by grep after reading.
- **Core never inspects the body of user Python.** `apparatus.py` resolves an entry point, calls
  it, and type-checks what came back; no `inspect`, no source read.
- **Greenfield only.** No `adopt`, no config-field addition — every declaration here is a template
  attribute, so § The one config file needed no change, exactly as the design predicted.

### 9. Interfaces across the five batches (brief area 1)

- **Every emitted code has exactly one § Errors / § Warnings row.** Swept `README.md`,
  `design-principles.md`, `experimental-designs.md`, `reference.md`, `CLAUDE.md` and the
  feasibility analysis for each of `E-APPARATUS-RAISED`, `-RETURN`, `-FACT-TYPE`, `-FACT-MISSING`,
  `-FACT-CREDENTIAL`, `W-APPARATUS-UNANSWERED`, `E-PROBE-UNKNOWN`: **one hit each** in
  `reference.md` and nowhere else (`W-APPARATUS-UNANSWERED` twice — its own row plus the
  cross-reference in `E-APPARATUS-FACT-MISSING`'s). Can-fail control on the same file list:
  `register_probe` → 4 hits in `reference.md`. `E-APPARATUS-RETURN`'s single row covers all
  three of its raise sites, which is what one-row-per-code means. The reverse direction holds too:
  no documented apparatus code is unemitted.
- **Every record key code writes is named by a document**, both directions: `block()`'s five
  sub-keys and `unobserved`'s `null_probes`/`total_probes` against § The apparatus core can only
  observe's fenced example; `append_observation`'s five keys (`at`, `phase`, `condition`, `probe`,
  `facts`) against § The apparatus files' fenced example; `condition` as `<nn>_<label>` against
  both. One exception, below as Minor 1.
- **`Observer` has exactly one caller** (`cli.command_run`), constructed only when the resolved
  template declares a truthy string `apparatus_probe`; `self.cfgs[condition.index]` cannot
  `KeyError`, because `cfgs` is built as `{c.index: … for c in conditions}` from the *same*
  `conditions` list handed to `Observer`. No new shipped-but-unread surface: every public name in
  `apparatus.py` (`_probe_for`, `observe_once`, `check_facts`, `Observations`, `condition_key`,
  `append_observation`, `APPARATUS_CODES`, `Observer`, `apparatus_hash`, `Apparatus`) has a
  production reader, which is Decision 14 honoured rather than asserted.
- **Batch 5 was never task-reviewed** — see Minor 4; areas 7 and 9 below are therefore a first-pass
  review of tasks 14, 16 and 17 rather than a seam check.

### 10. Documents, both consistency passes

**Mechanical.** Scripted over the four documents plus `CLAUDE.md` and the analysis, fences skipped:
zero duplicate heading anchors, zero trailing whitespace, zero tabs, zero table rows whose cell
count differs from their header's (escaped `\|` handled), every relative link resolving. The 24
"dead anchor" hits my checker reported are all of the form `…--…` (`#secrets--credentials`,
`#allocationjson--who-went-where`) — GitHub's slugger deletes `&` and `.` and leaves the two
hyphens, which my `\s+ → -` collapse does not reproduce. All 24 are checker artifacts; no real
dead link or anchor.

**Cross-document.** The **shared worked example is untouched** — no `cohort-pilot` value, interval,
hash prefix or run ID appears in the branch's `reference.md` diff, whose hunks are confined to
§ Warnings core reports, § Errors `validate` reports, § The importable surface, § Errors core
raises, § Artifact layout, § The apparatus core can only observe, § The apparatus files and
§ Package layout. Task 1's re-siting is **complete in the two `reference.md` sentences and
`experimental-designs.md`'s row**, and the paraphrase batch 1 found in the feasibility analysis is
fixed in both of its occurrences (lines 820 and 937) — I re-swept and found no third. § Package
layout's `— not yet built` marker on `apparatus.py` is retired; § The importable surface's
`Apparatus` row is `built`; § Artifact layout carries `apparatus/probes.jsonl`. § Validation's
"Probe is installed" row correctly left alone.

---

## Findings

### Major 1 — a non-`str` `apparatus_probe` silently reads as "no apparatus": the run validates clean, exits 0, and records `apparatus: null` — the closed filing's defect in a new spelling

**`src/publishable/cli.py:2402`** and **`src/publishable/validate.py:972-974`**, the same predicate
in two files written by two batches.

Both guards are `if not isinstance(declared, str) or not declared: return` / `if isinstance(
declared_probe, str) and declared_probe:`. A template whose `apparatus_probe` is not a `str` —
`["llm_deployment"]` being the plausible mistake, since `apparatus_facts` sits on the next line and
*is* a list — is **silently skipped at both surfaces**. `validate` reports nothing, `command_run`
constructs no `Observer`, the probe is never called, and `run.yaml` records
`provenance.apparatus: null`, which `reference.md` defines as *"An experiment whose measurements
never leave the machine declares nothing."*

**Verified by running.** A project-local template with `apparatus_probe = ["wbr_probe"]` and
`apparatus_facts = ["model_revision"]`, driven through the real `main(["run", ...])`: stdout carries
`W-ENV-UNLOCKED` and nothing else, exit **0**, `provenance["apparatus"] is None`, and no
`apparatus/` directory exists. That is, line for line, the reproduction in the filing this slice
struck — *"a run whose template declares an installed probe records a false `apparatus: null`"* —
reached by a different route.

**Why it is this slice's finding even though the predicate is copied.** `validate._check_probe`'s
fail-open predates this branch (H7b Part A), and until task 11 it had **no observable
consequence**: `cli.py` wrote `apparatus: null` for every run regardless, so a malformed
declaration and a correct one produced the same record. This slice is what gave
`apparatus: null` a *meaning* — "no probe declared" — and so is what turns the pre-existing
fail-open into a record that under-claims. `CLAUDE.md` § Answering a question with a proxy is the
shape: the predicate answers *"is this a usable probe name"* with *"is this a non-empty `str`"*,
and when it fails open it fails toward silence. It is also the seam class no per-batch review could
reach: two guards on one attribute, in two files, batch 3 and batch 4.

**Not Critical**, because nothing leaks and no data is corrupted — the record under-claims rather
than over-claims, and `apparatus_probe` is written by a plugin author rather than in a config, so a
misspelled *name* is still caught (`E-PROBE-UNKNOWN`) and only a wrong *type* is not.

**What closes it.** One `E-PROBE-UNKNOWN`-family error at `experiment_type` from
`validate._check_probe` when `apparatus_probe` is present and not a `str` — which also makes
`cli.py`'s `isinstance` the belt-and-braces it reads as. Or a filing with an owner, since the
predicate is inherited. Either way the `E-PROBE-UNKNOWN` § Errors row would need the type case
added, or a new narrow code minted; that is a design call, not a review call.

### Major 2 — a fact value that *contains* a declared credential is published verbatim, while the terminal redacting the same value set matches by containment

**`src/publishable/apparatus.py:170-183`** (`check_facts` step 2) versus
**`src/publishable/secrets.py:115-131`** (`redact`).

`check_facts` refuses a fact value only on **exact equality** with a declared credential's value.
`secrets.redact`, answering from the **identical** value set
(`credential_values(declared_credential_names(...))`), matches by **substring replacement**. So a
probe returning `{"endpoint": "https://api.example.com/v1?key=" + token}` sails through, and the
credential is written into `provenance.apparatus.facts` in `run.yaml` **and** into every
`apparatus/probes.jsonl` line — the two artifacts § The apparatus core can only observe says are
*"publishable as-is"* and that `study add` *"has nothing to redact from"*. There is no redaction
layer on the record at all, by design (Decision 6 refuses instead), so exact equality is the
**sole** guard on the published block.

**Verified by running.** Direct call: `check_facts(Apparatus(facts={"endpoint":
"https://api.example.com/v1?key=lab7"}), [], credentials={"WBR_TOKEN": "lab7"})` returns the value
untouched. End to end through `main(["run", ...])` with `required_env = ["WBR_TOKEN"]` and
`WBR_TOKEN=lab7`: **exit 0**, no diagnostic, and `b"lab7"` present in **`run.yaml` and
`probes.jsonl`**. The complementary case — the whole value equal to the credential — refuses
correctly, so this is a strength gap in one check, not a broken check.

**What makes the gap specific rather than sweeping, and it is the fact that keeps the fix small.**
`grep -rn "credentials" src/publishable/artifacts.py` returns **nothing**, and in `runner.py` the
name appears only to feed `redact` on an exception (runner.py:732). So **core credential-checks
nothing else it records** — an `io.record`'d column equal to a credential is written without a
murmur. `provenance.apparatus` is the *only* block the four documents promise is *"publishable
as-is"* and that `study add` *"has nothing to redact from"*, which is exactly why exact equality is
insufficient **here** in a way it is not elsewhere, and why the remedy is a narrowing of this one
check rather than a new obligation on every recorded value.

**Why it is not Critical.** The probe author constructs the leak, and § The apparatus core can only
observe already instructs a probe to emit a *hash* of an endpoint rather than the value — so this
is the user mistake the check exists to catch rather than a leak core creates. And the
implementation followed the design: Decision 6 rules *"by **exact value**, never by pattern."* But
that sentence's contrast is with **heuristics** (name patterns, entropy) whose fault is guessing;
containment of a value core actually read is the same kind of fact equality is, which is exactly
why `redact` is allowed to use it. Two strengths over one value set, and the weaker one guards the
published artifact.

**What I recommend, and it is not a merge blocker.** Either narrow `check_facts` to containment
(`cred_value in value`), or file it in `spec-defects.md` with an owner and a stated reason — the
repo's own rule is that a gap deliberately not closed gets a filing, and no existing filing covers
it: the neighbouring OPEN entry is about a fact **key** equal to a credential value, a different
shape. Whichever is chosen, `reference.md`'s § Errors row for `E-APPARATUS-FACT-CREDENTIAL`
currently says *"Checked by **exact value**, never by pattern"*, which is true of the code and
should move with it.

### Major 3 — a sentence this branch wrote points a reader at § Executability for an answer that section does not contain

**`docs/feasibility-llm-growth-studies.md:825`**, rewritten by batch 1's fix round, now reads:

> whether core's apparatus mechanism is built, and how much of it, is a build fact that moves — see
> [§ Executability on this build](#executability-on-this-build) for what is true today rather than
> restating it here, since restating it here is exactly what leaves an undated claim behind for the
> next slice to falsify.

That rewrite was the right move — it replaced a now-false undated build claim (*"there is no
`Apparatus` type, no `register_probe`, and no probe execution anywhere in the package"*) with a
pointer. But **§ Executability on this build says nothing about the apparatus mechanism at any
date.** Its last entry is `### Measured on 2026-08-19 against commit d0e9345 — after H4d`
(`grep -n '^### Measured on'` → eight entries, none for H7d), and no entry mentions a probe, a
ledger, or `provenance.apparatus`. So the one sentence in the analysis that a reader is now
directed to follow leads nowhere: the branch closed an undated claim by creating a dangling one.
The same rewrite at line 937 has the same target.

This is a live defect in a file the branch touched, not a convention lapse — which is why it is
Major and why it is the branch's rather than the merge commit's. The content the appended entry
needs is exactly my re-measurement in § 7 above: zero configs unblocked, six with no remaining
core-side blocker, three executable, all three unmoved, with the `holdout.frac → 0` can-fail
control; plus the honest statement of what *did* change (a probe-declaring run now records five
real sub-keys where it recorded a false `null`, and five new error codes are reachable, so the only
direction a config count can move is down). `CLAUDE.md` § Feasibility analyses step 10 is the
governing rule: a build claim is *"dated and pinned to a commit where it is made, and kept in a
section of its own."*

**Verified by reading**, and by re-measuring the figures myself so the appended entry has content
rather than an assertion. No *false* claim is introduced anywhere — the analysis's newest
measurement honestly reads "after H4d" — which is why this is Major rather than Critical.

### Minor 1 — the no-sweep condition key `"00"` is a record value no document names and no filing holds

**`src/publishable/apparatus.py:293-318`** (`condition_key`).

A run declaring no `sweep` has one condition whose label is `None`, and the plan (§ Corrections
against the code, correction 2) rules the key `f"{index:02d}"` on the sound ground that canonical
JSON cannot sort a `None` key beside `str` keys. **Verified by running:** a probe-declaring
template with no `sweep` block records `facts: {"00": {...}}` in `run.yaml` and `"condition": "00"`
in the ledger, and the run completes at exit 0. But `reference.md` documents only the
`<nn>_<label>` form (`00_baseline`) at both sites, `grep` over `spec-defects.md` finds no filing,
and this is the **ordinary** shape for any single-condition experiment with an apparatus. The
repo's rule is the document changes first; here the code minted a record spelling ahead of it.
One sentence in § The apparatus files, or a filing, closes it.

### Minor 2 — `experimental-designs.md`'s apparatus row still enumerates three probe placements where `reference.md` now names four

**`docs/experimental-designs.md:375`**: *"recorded per condition at `dry-run`, at run start, and
before every execution"*. Task 1 changed the sibling sentence in `reference.md` § The apparatus
core can only observe to *"at `dry-run`, at run start, before every execution, and at `freeze`"*,
and § The apparatus files already said four. This is the enum-completeness class in `CLAUDE.md`'s
cross-document table: one enumeration, two documents, two lengths. `condition_key`'s four-phase
vocabulary in code agrees with `reference.md`. Found by an **unfiltered** sweep of `dry-run` hits
across all six files (the `grep` filtered the file list, never its output). The same three-place
enumeration at `docs/feasibility-llm-growth-studies.md:825` is exempt from the cross-document pass
and correctly left.

### Minor 3 — the branch ships no `E-APPARATUS-*` §Validation row, which is right, but nothing records that it is right

Task 16's report says § Validation's "Probe is installed" row was *"read, confirmed unchanged"* and
the design's sweep names § Validation. Correct — every check this slice adds needs a call, and
§ Validation is `validate`'s own table. Noting it only so a later reader does not re-file it as a
missing row; the design's task 16 wording ("§ Validation … row") reads as though one were owed.

### Minor 4 — batch 5 has a report, no review, and no ledger entry

`.superpowers/sdd/2026-08-19-apparatus-part-a/` holds `task-b5-report.md` and **no
`task-b5-review.md`**, and `progress.md` stops at *"## Batch 4"*. So tasks 14, 16 and 17 — the
`validate` guard, all six documented rows, and all four filings — had one pair of eyes before mine,
and one ruling task 17's own report describes (its initial mis-citation of the `EXIT_EXTERNAL`
filing's owner-task, corrected in the same edit pass) has no ledger line, against `CLAUDE.md`'s
*"every ruling, its reason, and what it costs if wrong."* I reviewed all three tasks directly
rather than as a seam check, and found them sound: task 14's pin fails under a probe call inserted
into `_check_probe`'s success branch (the report's own mutation, and the flag-file-plus-raise shape
means a call cannot be silent), and every documented row and filing checks out as recorded above
and below. The gap is in the record, not in the work — and `progress.md`'s batch-5 entry is item 1 of the
three named under the verdict above, since the ledger is the tracked artifact.

---

## Filings (brief area 9) — checked entry by entry

- **`a run whose template declares an installed probe records a false `apparatus: null``** — struck,
  and struck against the code: I re-confirmed `cli.py` writes
  `"apparatus": observer.block() if observer is not None else None`. Original text kept below the
  closure note, as the convention requires.
- **`PROBES`/`RESOLVERS`, `PROBES` half** — struck, and the reader is real: `_probe_for` calls
  `declared_names(PROBE_GROUP, fn)`, which `plugins._registry_for` resolves to `PROBES`. The
  `RESOLVERS` half correctly untouched.
- **`BaseTemplate.field_convention`** — amended to name `field_convention` alone, still
  **unassigned**, and the amendment states why this slice does not adopt it. `CLAUDE.md`'s
  misreading row moved with it and now names `field_convention` as the sole example, with
  `EXIT_EXTERNAL` named separately as the same fault outside `BaseTemplate`. Consistent.
- **`EXIT_EXTERNAL = 5` ships and is read by nothing — Owner Part B** — **filed, not fixed**, which
  is correct: I re-confirmed by grep that `diagnostics.py` holds the one definition and nothing in
  `src/` or `tests/` reads it, and the entry narrows what is owed to a *reader* plus the documented
  5-wins-over-3-and-4 precedence rather than the constant. It names the check its owner must make
  and the two sibling Part B tasks it depends on.
- **`append_observation` ordering** — handed forward from batch 2 to batch 3 and **closed there
  with the ruling in the entry**: `check_facts` before `append_observation`, every time. Verified
  by reading `Observer._observe_one` and by the credential run above, where nothing reached the
  ledger.
- **A fact *key* equal to a credential value** — OPEN, **`unassigned` with a stated reason**, not
  the forbidden *"whichever slice does X"* form, and its earlier over-claim ("reaches a diagnostic
  with that credential in the message") is corrected in place with the redaction that actually
  applies and the test that now pins it. This is the one entry adjacent to Major 2 and it does
  **not** cover it; nor does any entry cover Major 1.
- **No filing this slice created has gone stale**, and no apparatus filing points at a closed slice
  for unbuilt work.

---

## What I could not check

1. **A real metered probe.** Every fixture is a local fake, deliberately — quota constrains
   placement, not testability. The one behaviour no fixture stands in for is a hosted deployment
   answering a fact on most calls and omitting it on some, which is why `null` is legal; my
   `flaky_pin` fixture simulates it per condition rather than per call.
2. **`dry-run`, `freeze`, `diff`, `reproduce`, `resume`, `draft`, `study add`.** All unbuilt. Every
   claim about where their checks live — including the `dry_run` and `freeze` members of the phase
   vocabulary and the "publishable as-is / nothing to redact" property Major 1 is measured against
   — is a **spec** claim I read, never a build fact I ran.
3. **Part B's own seam.** The gate, `EXIT_EXTERNAL`'s reader, run-stops-here, the truncated-plan
   `run_status` contract and the `batch`-independence *test* are out of scope here; I verified only
   that Part A creates none of them and that `batch` and the apparatus remain independent in code.
4. **The nine configs' actual plugin.** `publishable-llm`, `llm_screen` and `llm_deployment` are
   designs, not code; my E1/C1 re-measurement used the same `generic`-template substitution every
   § Executability entry has used since 2026-08-16, and it is a substitution.
5. **Fixture H's second assertion.** I recomputed the hash from the recorded `facts` mapping, but
   did not independently run two runs with identical facts and compare digests — batch 4's review
   covered `sort_keys`' non-blindness (its fixture inserts `zeta_field` before `alpha_field`), so I
   did not re-litigate it.
6. **Whether containment is the right strength for `check_facts`** (Major 2). I established that
   the current check is strictly weaker than `redact` over the same value set and that the gap is
   reachable and silent; whether the fix is a narrowing or a filing is a design call for the owner,
   and a containment check has its own false-positive shape (a two-character credential value)
   that I did not evaluate.
7. **Whether `_check_probe`'s type guard should refuse or warn** (Major 1). I established that it
   fails open silently at both surfaces and that the resulting record is the struck filing's
   defect; whether the remedy widens `E-PROBE-UNKNOWN` or mints a narrow code is a design call.
