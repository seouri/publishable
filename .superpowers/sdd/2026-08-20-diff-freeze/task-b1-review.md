# H8b batch B1 (tasks 13, 14) — review

**Reviewed at `5223383`** on branch `h8b-diff-freeze`. Diff read:
`review-b1.diff` (commits `152688f`, `af87572`, `5223383`).

## Verdicts

**Spec compliance: PASS.** Task 13's seven arms match the plan's task-13 arm list value for
value, all seven captured from a real run rather than from `cli.py`. Task 14's document changes
are additive in both senses the controller's ruling required: `af87572` is 13 insertions and 2
deletions in one file, and each deletion is a sentence replaced by a **superset** of itself (the
§ The other files intro, which gained two artifact names to its settled-before-first-execution
list, and § Run identity's `environment/{…}` brace, which gained `repo_root.txt`). No verdict,
status word or exit code is described as moving anywhere in the diff — verified by reading every
changed line. § CLI reference's `resume` sentence is **unchanged**, as step 4 required: it still
reads *"that run directory already contains the config it used,"* and `git log -S` on that string
shows it dates to the initial docs commit `b0e4070`, not to `af87572`.

**Task quality: PASS with one Major.** Both mutations the report claims are reproducible, and
each isolates exactly the arm the report says it does. The Major is a coverage-honesty defect of
exactly the class H8a's equivalent batch was made to fix: **two arms assert something false about
the shipped suite**, and the report repeats one of them. Neither is a behaviour defect and
neither blocks merge; both are one-sentence corrections.

**Gates, all run here on the reverted tree:** `ruff check .` clean · `ruff format --check .` → 84
files unchanged · `mypy` → 47 source files, no issues · `pytest` → **2522 passed, 1 skipped, 2
xfailed**. Tree clean (`git status --short` empty).

---

## Findings

### Major 1 — Two arms claim coverage the shipped suite already has, and one claim is in the tracked report too

**(a) Arm F.** `tests/test_cli.py:15995` states *"No existing test asserts this equality directly
— the nearest is each pin's own read of `run_doc["config"]` for a sub-field, never a
whole-mapping comparison against the file on disk."* The tracked report repeats it as *"New
coverage (existing tests read sub-fields of `config`, never a whole-mapping comparison against
the file on disk)"* (`task-b1-report.md:20`).

`tests/test_acceptance.py:56` is that exact comparison:
`assert doc["config"] == yaml.safe_load(cfg.read_text())  # embedded verbatim`.

**Verified by running**, not only by grep. Mutating `run_record.py:284` to
`{**config, "sweep": None}` failed **both** arm F and
`tests/test_acceptance.py::test_scaffold_then_run_produces_a_real_record`. Narrowing the same
mutation to fire only when the config declares a `sweep.grid` then failed, across the **full**
suite, only `test_h8b_arm_f_...` and `test_h8b_arm_g_parameters_hash_agrees_...` (2 failed, 2520
passed). So the arm does carry residual discriminating power — a *swept* run's embedded config
diverging from the file is caught nowhere else — and the verdict "new coverage" survives in that
narrowed form. What does not survive is the sentence: the named nearest neighbour is wrong, and
this repo's own habit list says a reader greps for exactly such a sentence and stops looking.

**(b) Arm E.** `tests/test_cli.py:15961` states *"No existing test asserts `sweep.yaml`'s
top-level key list **or that no condition entry carries `selectors`**."* The second half is
false. `tests/test_sweep.py:248-261` asserts `doc["conditions"] == [...]` by **full dict
equality**, which pins the entry key set exactly.

**Verified by running.** Adding `"selectors": {}` to each entry in `sweep.py`'s `sweep_document`
failed arm E **and** `tests/test_sweep.py::test_the_sweep_document_records_the_resolved_plan` (2
failed, 2520 passed). The top-level key list half of the claim is correct and new — no shipped
test asserts it, and no shipped test reads `sweep.yaml` as a file for its shape.

**Remedy for both:** name the real neighbour and narrow the claim — arm F to *the swept case*,
arm E to *the top-level key list*. **This also falsifies the report's § Brief/design/plan vs.
code — disagreements found: "None."** Both false claims are claims about existing code that the
task made and did not check, which is the category that section exists to hold.

### Minor 1 — The authorized-editor clause is missing its auditable half

Step 3 of task 13 required: *"Both clauses add: **task 3's report must show the diff is exactly
one entry per arm with nothing reordered.**"* Neither docstring carries it. `grep -n "task 3"
tests/test_cli.py` returns the module comment (`:15813`, sole-editor naming), Arm A's
`:15820`/`:15832` (editor + post-edit list) and Arm B's `:15856`/`:15864` (same) — and nothing
about task 3's report obligation.

Everything else the clause needed **is** present and correct, verified by reading: task 3 is
named as sole authorized editor of arms A and B in three places; each post-edit list is stated in
advance and is the shipped list plus exactly one sorted insertion; and the module comment at
`:15814` carries *"Every other task that finds any arm here failing has found a finding to report,
not an assertion to edit."* The missing sentence is the one that makes the edit checkable after
the fact rather than at the moment it is made.

### Minor 2 — The cross-document sweep was run for three spellings, not for the claim

`task-b1-report.md:61` concludes no other document enumerates run-directory contents, having
grepped `environment/{uv.lock,pyproject.toml}`, `sweep.yaml` and `manifest/input.json`. None of
those three strings can match `README.md:139-148`, which **is** a run-directory tree
(`~/results/cohort-pilot/` → `run.yaml`, `conditions/`, `summary/`).

**Verified by running my own sweep**, over the four documents named individually plus `CLAUDE.md`
and `docs/feasibility-llm-growth-studies.md`, with `run.yaml` as the positive control (present in
all six: 8/5/1/75/4/3 hits) and `environment/` as the claim (**zero hits outside
`reference.md`**). The conclusion holds — README's tree is deliberately abbreviated and already
omits `environment/`, `manifest/`, `sweep.yaml` and `executions.jsonl`, so it owes nothing — but
it holds by luck of the abbreviation rather than by the sweep having looked. `CLAUDE.md`'s rule
is *sweep for the claim, not for the file the claim was first noticed in*; the claim here is "a
run-directory listing", and README has one.

### Minor 3 — `E-FREEZE-NO-CONFIG` is named before it has a row or an emit site

`docs/reference.md:846` names `E-FREEZE-NO-CONFIG`. There is no § Errors row for it and no emit
site; `freeze` is still `NOT BUILT`. Task 12 owns the § Errors rows, so this closes on its own —
but for the length of the branch the document names a code a reader cannot look up, which is the
*"assuming a documented rule has code behind it"* trap pointed the other way.

Not a rule breach: I measured the precedent. Six codes are already prose-only in `reference.md`
with no table row anywhere in it — `E-EXPERIMENT-EXISTS`, `E-IO-FAILED`, `E-PROJECT-EXISTS`,
`E-STEP-EXISTS`, `E-TEMPLATE-EXISTS`, `E-TEMPLATE-INSTALLED-UNSUPPORTED` — computed by scanning
every `E-` token against every table line. And no test cross-checks § Errors against a code
registry, so nothing was silently relaxed. Recorded so task 12 does not have to rediscover which
code it owes a row.

### Minor 4 — A positional locator, in new text

`tests/test_hashes.py:350` — *"the two below"* — locates
`test_h8b_arm_g_metadata_only_change_is_identical` and
`test_h8b_arm_g_max_failed_fraction_change_differs` by position. Name them; a later insertion
moves them. Arm C's *"…and `test_h8a_arm_b_…` above"* (`tests/test_cli.py:15882`) is fine by
contrast: it names both tests and uses position only as a hint.

### Minor 5 — Three citations to a git-ignored artifact, in a tracked file

`task-b1-report.md` cites "the brief" as its source three times (the arms matching *"the brief's
stated values"*; *"per the brief's own instruction"*; *"the brief doesn't ask for a strike
there"*). `git check-ignore -v` confirms `task-*-brief.md` is ignored by
`.superpowers/sdd/.gitignore:20`, so a reader of the tracked record cannot check any of the
three. Weak finding — the plan holds the identical content and **is** tracked (§ Task 13 / § Task
14), and ~20 shipped test docstrings already cite briefs — but the fix is free: cite the plan's
section.

### Minor 6 — Two wording slips in the new § The two files paragraph

`docs/reference.md:627`: *"written at run start and never modified since"* — "since" has no
referent; the shipped parallel sentence for `run.yaml` reads "never modified". And the same
sentence argues *"naming it here would make this 'the two files' plus an asterisk"* while the
paragraph is itself naming it. The intent (the section is not **renamed**, and the file is not a
third thing to **edit**) is right and is stated correctly in the clause after; only these two
phrasings misfire.

---

## Attack-by-attack, with what each was verified by

**1. Every arm discriminates, and which are new.** I found and ran a mutation for six of the
seven arms, and read the seventh. Full-suite results:

| Arm | Mutation | Result | New coverage? |
|---|---|---|---|
| A (run-dir root) | `(run_dir / "stray.txt").write_text("x")` in `cli.py` | **only arm A** failed (1 failed, 2521 passed) | **Yes** — nothing else in the suite sees a stray file at the root |
| B (`environment/`) | same write into `environment/` | **only arm B** failed | **Yes** |
| C (key lists, status, draft) | extra `"zzz"` key in `run_record.py`'s doc | arm C **plus three shipped tests** (`test_a_clean_run_completes_with_the_full_run_yaml_shape`, `test_g1_ordering_chain_…`, `test_h8a_arm_a_…`) | **No**, as the docstring and report both say. `draft is False` is also shipped at `test_acceptance.py:51` and `test_runner.py:243` |
| D (five figures) | `"manager": "uv"` → `"uvx"` in `cli.py` | **only arm D** failed | **Yes** — stronger than the report's hedge; no shipped test asserts `provenance.environment["manager"]` at all |
| E (`sweep.yaml` plan) | `"selectors": {}` per condition entry | arm E **and** `test_sweep.py::test_the_sweep_document_records_the_resolved_plan` | **Partly** — see Major 1(b) |
| F (embedded config) | sweep-gated `{**config, "sweep": None}` | arm F **and** arm G-1 only | **Partly** — see Major 1(a) |
| G-1 (hash vs. embedded config) | same as F | isolated to F and G-1 | **Yes** |
| G-2 (metadata identical) | not run | — | **No**, as stated; `test_parameters_hash_excludes_metadata_and_the_two_paths:47` is the same claim |
| G-3 (`limits` differs) | `"limits"` added to `parameters_hash`'s exclusion set | **only arm G-3** failed | **Yes**, exactly as claimed |

**2. Arms A and B read genuinely different directories — reproduced, both directions.** Mutation
1 (`environment/stray.txt`): arm B failed on the list assertion, arm A passed. Mutation 2
(`run_dir/stray.txt`): arm A failed, arm B passed, and the **full** suite showed 1 failed / 2521
passed — so arm A is the only reader of the run-directory root anywhere in the suite. Neither arm
is redundant against the other. Reverted by editing the line out; `diff` against a pre-mutation
copy of `cli.py` byte-identical, and the arms re-run green.

**3. The authorized-editor clause** — present, correct, and incomplete by one sentence. See Minor
1.

**4. The document ruling** — § The two files now says what a run-start config copy is, in the
role-vs-file terms the brief demanded (`reference.md:627`); § The other files a run writes gained
the artifacts to its settled-before-first-execution list (`:840`) and a subsection of its own
(`:842-848`) with a reader, a remedy and the boundary sentence; § Run identity's tree gained
`config.yaml` on its own line and `repo_root.txt` inside the brace (`:803`, `:805`).
**Displacement checked:** the tree's `└──` is still on `summary/…` and no other marker moved; the
sentence right below the tree — *"Everything beside `run.yaml` there has a shape something reads
back"* — is strengthened rather than falsified; the § Contents entry for § The other files
(`:26`) is an already-partial summary ("`sweep.yaml`, `allocation.json`, manifests, unit tables"
— it omits `executions.jsonl` and the apparatus files) so it needed no edit; the TOC lists only
`##` headings, so the new `###` owes no entry; and the § The two files TOC line (`:25`, *"—
`config.yaml` and `run.yaml`"*) still names roles and stays true. No count phrase and no
positional locator near any of the three insertion points was made false — I read each. **One
naming note, no action:** the ledger's requirement reads *"§ Artifact layout gains rows"* and
`reference.md` has no heading by that name; § Run identity's tree and § The other files a run
writes are the artifact-layout surfaces, and Decision 7 itself names those two. Both gained
content, so the requirement is met.

**5. The sweep** — run myself, four documents named individually plus `CLAUDE.md` and the
feasibility analysis, with `run.yaml` as the proven-to-fire control. `environment/`: zero hits
outside `reference.md`. `repo_root`: only `reference.md`, and the pre-existing
`provenance.git.repo_root` rows. `"two files"`: only `reference.md`, at `:25`, `:619`, `:627` and
two unrelated uses. Mechanical pass re-run over all six, fenced blocks skipped, each check proven
able to fail with an injected control: no trailing whitespace, no tab, no invisible unicode, no
duplicate heading anchor in `reference.md`, and every `](#…)` in `reference.md` resolves (an
injected `#no-such-anchor-zzz` was the only hit when I seeded one). Method gap at Minor 2.

**6. The "no disagreements" claim** — falsified; see Major 1. Three brief/plan claims about
existing code that I verified myself: *nothing in `tests/` enumerates the run-directory root or
`environment/`* — grep for every `iterdir`/`rglob`/`glob("*")` in `tests/`, and independently
confirmed by mutation 2 failing exactly one test suite-wide; *arm C's key lists are already
asserted in this exact order by H8a's arms A and B* — read at `tests/test_cli.py:15330-15342` and
`:15364-15377`, then confirmed by the extra-key mutation; and Decision 7's grounding claim that
`get_template` skips local discovery when `repo_root is None` — `templates/registry.py:82`,
`local = discover_local(repo_root) if repo_root is not None else {}`, reached from
`get_template` → `_merged` → `_claims`. I also checked the ledger's overruling of plan correction
4: `CLAUDE.md:353` does read the past-tense *"`EXIT_EXTERNAL` **was** the same fault … **until**
H7d Part B task 8 gave it its reader"*, so the report's claim there is accurate and the
correction is rightly overruled.

**7. Prose** — no § Errors row was written (task 12's), `×` is used for the fixture's
`2 conditions × 2 seed repeats` with no bare `x` anywhere in the new text, **no config-count
claim appears** (`grep` for "executable", "no remaining core-side", "8 of 8" in the report: no
hits; `docs/feasibility-llm-growth-studies.md` untouched by both commits, so the table stays
8 of 8 / 0 / 7 / 1). Two prose findings stand: Minor 4 (positional locator) and Minor 5 (brief
citations), plus Minor 6's wording.

---

## Not checked

- **`E-FREEZE-NO-CONFIG`'s eventual § Errors row and remedy wording.** Task 12's, and there is
  nothing to compare against yet.
- **Whether the seven arms will still hold after task 3.** By construction they will not — arms A
  and B are authorized to move by one entry each — and I verified the stated post-edit lists are
  the shipped lists plus one sorted insertion, but I did not build task 3's artifacts to confirm
  the lists empirically.
- **`_files_under(results_dir)`'s credential sweep gaining two files.** The plan assigns that
  measurement to task 3 step 4; nothing in this batch touches it.
- **Arm G-2's mutation.** Read rather than run: it is self-declared as not-new-coverage and its
  shipped twin is `test_parameters_hash_excludes_metadata_and_the_two_paths:47`.

**Tree left clean.** Every mutation reverted by editing the line back out, each revert confirmed
byte-identical against a pre-mutation copy **and** by re-running the affected tests, and the
final gates above were run on the reverted tree with `git status --short` empty.
