# H6a batch 3 review — tasks 5 and 6, THE VALUE CHANGE

**Verdicts: task 5 PASS (three Majors, all disclosure/ownership rather than behaviour).
task 6 PASS (one Minor).**

**Nothing found here blocks the merge.** No finding is behavioural: the value change is correct end
to end, all six of the report's mutation counts reconcile exactly, and every guard-pin arm holds.
Major 1 needs an authorized one-clause deletion in a no-editor arm; Major 2 needs task 12 to file
the gap with a named owner; Major 3 needs one disclosure line in the report. Three Majors here are
three obligations, not a hold.

Reviewed at `d959b34` on `h6a-hash-definitions`. Commits `9685ae0`, `c98b24e`, `5974c93`,
`d959b34`.

**The value change is correct end to end.** Verified through the installed console script on a
project outside this repo, not by reading and not by a direct call: the same byte-identical tree
records `sha256:09a843b1…` under the pre-slice definition and `sha256:f6a935cf…` under the shipped
one, and the `run_id` and the `latest` pointer both follow.

**Suite: 2951 passed, 1 skipped, 2 xfailed** (baseline 2945 → +6, which reconciles: task 5 +4 in
`tests/test_cli.py` and +2 in `tests/test_hashes.py`, task 6 +1 −1). `ruff check` clean,
`ruff format --check` 93 files, `mypy` 52 source files. Working tree clean at the end; every
mutation reverted **by editing the file back** and each revert verified by **re-running**.

---

## 1. The entailed pin-arm edit — arm B

**Verified by diff and by reading the advance state.** Arm B's own docstring, written in batch 1
and therefore before anything moved, specifies **four** literals and their post-edit values (the
plan's task 2 says "exactly two"; the arm records why it holds four — *"The plan names two because
it names one tree; this arm holds two trees"*, the base tree not being runnable). The shipped edit
moves exactly those four:

| Literal | Before | After | Shipped |
|---|---|---|---|
| `_H6A_BASE_WITH_ENV_DIGEST` | `ebc5ee53…` | `71bf339c…` | yes |
| `_H6A_RUN_WITH_ENV_DIGEST` | `a74f3d44…` | `f6a935cf…` | yes |
| run directory suffix | `_a74f3d4` | `_f6a935c` | yes |
| the recorded `code_hash` | (same constant) | unedited | yes |

**The disclosed fifth edit is sound and I would have required it.** The two direct halves called
`code_hash(tree, None)`; `None` bypasses `include` entirely, so with it literals 1 and 2 **cannot**
move and the arm's own advance specification is unsatisfiable. Both halves now take
`_h6a_live_include`, `command_run`'s own predicate. The stale sentence it falsified was **deleted**,
not rewritten. Both constant NAMES survive, which is what keeps arm C green with zero lines changed.

**Arms A, C, D, E, F and N were never opened.** Measured, not asserted: `git diff 59ba24b HEAD`
touches five files, and the four `tests/` hunks are arm B, the constants block, the two `__pycache__`
tests, and appended-at-end additions. `tests/test_diff.py` (arm N) and `tests/test_validate.py`
(arm F) are **byte-unchanged**; each arm's function body diffs identical, as do the pin's shared
helpers `_h6a_base_tree`/`_h6a_pin_project`.

**Batch 2's Major did not recur.** Task 5 is arm B's sole authorized editor and edited arm B alone.

**Every no-editor arm still passes AND can still fail** — batch 1's two mutations re-run, plus two
more for the arms those two cannot reach:

| Mutation | Arms that failed |
|---|---|
| `hashes.py` fold separator `b"\0"` → `b"\|"` | A, B, C, D (+ Fixtures C×2, D, count pin, M) — 9 failures |
| `diff.py:363` `figure_a == figure_b` → `!=` | N and N's control, both |
| `_prefixed` truncates the digest | E |
| `W-TEMPLATE-VERSION`'s unset clause reworded | F |

## 2. Every digest recomputed independently

**Recomputed by building each tree and folding it with a script written from the algorithm, not by
calling `hashes.py`.** All eight reproduce to the character:

```
base tree                    sha256:71bf339cc946…   [src/pkg/step.py, templates/t.py]
base + .env, ALL             sha256:ebc5ee53ac39…
runnable project (1 file)    sha256:f6a935cfc291…   [src/pkg/step.py]
runnable + .env, ALL         sha256:a74f3d44dc1d…
base + loose.pyd=X, ALL      sha256:eec1541edde4…
probe project + 3 excluded   sha256:09a843b15e23…
Fixture C's tree, ALL        sha256:1947d2a21da3…
base + .env, include applied sha256:71bf339cc946…
```

So `ebc5ee53→71bf339c`, `a74f3d44→f6a935cf`, `1947d2a2→71bf339c`, `eec1541e→71bf339c` (under
mutation 4) and `09a843b1→f6a935cf` are all correct. **Three of this plan's own fixtures were wrong
before; none of this batch's is.**

**The coincident digests do not weaken any fixture, and the follow-up commit's comment is true.**
`_H6A_T5_RUN_DIGEST` equals arm A's `_H6A_RUN_DIGEST` because both trees hash exactly
`src/pkg/step.py` = `a = 1\n` — computed, above. The after-value `71bf339c` likewise recurs because
narrowing those trees *lands on the base tree by construction*. Discrimination is preserved
independently of the digest at each site: arm B asserts `.env`'s contents are still on disk,
Fixture C asserts the dropped set **as an exact three-element set**, Fixture D asserts `git ls-files`
membership on both arms. Empirically confirmed by mutations 2 and 4 (below), which fail 8 and 3
tests respectively.

## 3. End to end through the installed console script

`~/src/tries/publishable/.venv/bin/publishable run configs/t5/config.yaml`, project outside this
repo, one committed `src/pkg/step.py` plus three untracked excluded files (`src/pkg/.env`,
`src/.venv/lib/site.py`, `src/pkg/loose.pyd`), exit 0. `run.yaml` read key by key:

```
top-level : schema_version run_id status draft config parameters_hash code_hash
            provenance layout execution results          (11 keys — Fixture M's literal, exactly)
schema_version : 1.0                                     (no bump, no marker — Ruling C)
run_id         : run_2026-08-23T01-23-48Z_f6a935c
status/draft   : completed / False
parameters_hash: sha256:081de4f3df68…
code_hash      : sha256:f6a935cfc291…
provenance     : git environment apparatus input_manifest input_manifest_hash
                 input_manifest_changed publishable_version plugin_versions units
                 units_hash allocation allocation_hash upstream ; upstream == []
results/latest -> run_2026-08-23T01-23-48Z_f6a935c       (symlink, read)
```

**The same tree pre-slice**, by editing `cli.py` back to `ch = code_hash(repo_root, None)` and
re-running the console script: `run_2026-08-23T01-24-12Z_09a843b`. Reverted by copying the file
back and re-running: `_f6a935c` again.

**Ruling F verified by behaviour, not by reading the flags.** There is exactly **one**
`check-ignore` invocation in `src/` (`provenance.py:70`) and it carries
`GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_SYSTEM=/dev/null` and `-c core.excludesFile=`. Probed:
with a global `core.excludesFile` excluding `*.log` and an untracked `src/pkg/machine.log` present,
the run **hashed it** — `run_…_a34ed58`, which equals the two-file digest I computed by hand
(`sha256:a34ed587dfac…`), so the machine-local rule did **not** move the digest. Committing `*.log`
into the repo's own `.gitignore` returned the run to `_f6a935c`. Note the accepted asymmetry: the
dirty gate *does* honour the global exclude (`git status` is not neutralized), so that repo runs at
all — which is Ruling F's stated cost, not a defect.

## 4. The three "unreachable as written" brief steps — both claims verified by running

* **The plan's base tree cannot be `run`.** Confirmed: `publishable validate` over the base tree
  prints `error E-TEMPLATE-LOAD experiment_type — the project-local template …/templates/t.py
  imported cleanly but called @register_template on nothing`.
* **A resolver writing into `src/**` on its FIRST call refuses with `E-CODE-DIRTY`.** Confirmed
  twice over. Structurally: `command_run` calls `validate_config` (cli.py:2010) **before** the dirty
  gate (cli.py:2025), and `resolve_units` has exactly two call sites, `validate.py:1370` and
  `cli.py:2074`. Behaviourally: flipping the shipped fixture's resolver to `>= 1` makes the run exit
  1 with `E-CODE-DIRTY`. The counter-reaches-2 assertion is therefore a real measurement of the
  window, exactly as the report claims.
* **The substituted fixtures test the same property**, split across two surfaces: the direct half
  (`tests/test_hashes.py`) carries the plan's literals **on both branches** (`1947d2a2…` for
  `include=None`, `71bf339c…` for the wired form) plus the exact dropped set; the end-to-end half
  (`tests/test_cli.py`) carries the real `run`. See Minor 3 for the one place this split costs
  something.

## 5. Mutations — all six re-run against the FULL suite, counts read

| # | Mutation | Report | **Measured** | Tests that failed |
|---|---|---|---|---|
| 2 | `hashed_files` computes `include` and ignores it | 8 | **8** | arm B, arm C, Fixture C ×2, Fixture D, Fixture J, `test_code_hash_delegates_to_code_hash_of_over_hashed_files`, Fixture F |
| 4 | `check-ignore --no-index` | 3 | **3** | survivor, Fixture D, Fixture I |
| 5 | ask git before the fixed skip set | 1 | **1** | task 6's survivor **alone** |
| 7 | predicate built and called at phase 3 | 1 | **1** | the resolver fixture, discriminated by digest |
| P2 | `hashed_files(...)` then `code_hash(repo, _include)` | 1 | **1** | the count pin, reading `2` invocations |
| t6 s3 | `__pycache__` out of `_SKIP_DIRS` | 2 | **2** | survivor + guard-pin arm D |

**Zero miscounts, and the named test lists match exactly.** Five miscounts in the previous slice
family; none here.

**Mutation 5 lands on task 6's survivor alone — verified**, and that is the evidence the removed
twin did no work: the twin ran `code_hash(tmp_path, None)` in a non-repository, so `include` was
never applied and git was never asked. The survivor's tracked `git add -f`-ed
`src/pkg/__pycache__/keep.py`, whose non-exclusion is asserted as `check-ignore` returncode 1, is
the only thing in the suite that separates *skip-then-ask* from *ask-then-skip*.

---

## Findings

### Major 1 — a shipped guard-pin arm's docstring was made FALSE by this batch, unnoticed and unfiled

`tests/test_hashes.py`, guard-pin **arm E**, closing sentence:

> *"None of the four is a 15th **production** call site; `code_hash` still has exactly one in `src/`."*

That was true when batch 1 wrote it (`cli.py` held `ch = code_hash(repo_root, None)`). Task 5
replaced that call with the two-step form, so **`code_hash` now has zero production call sites**.
Established by `grep -rn "code_hash(" src/` → **one hit, the definition in `hashes.py:75`**, and
nothing else.

Arm E has **no authorized editor in this batch** (task 3 only), so task 5 was right not to edit it —
but it then owed a disclosure and a filing, and gave neither. The report's own grep bullet notices
the zero-caller fact and does not connect it to the arm asserting the opposite. This is § Corrections
8's exact shape (*"a shipped test's docstring becomes FALSE while its assertion stays green"*), at a
site nothing sweeps, inside the device whose whole value is that its text is trustworthy.

**Remedy, scoped to one clause so the fix cannot invent.** Delete exactly the clause
*"; `code_hash` still has exactly one in `src/`"* and nothing else. **The same paragraph's other
count stays**: *"the 13 `code_hash(` call sites the six named tests … already had **when task 3's
brief was written**"* is written in the past tense about a moment that has passed, so task 6's
removal of the duplicated twin does not falsify it. Saying which sentence goes is the difference
between a deletion and a rewrite, and *a rewrite invents; a deletion cannot*. The edit is one line
and touches no assertion, but arm E has **no authorized editor**, so it needs explicit
authorization rather than being folded into whatever slice notices next.

### Major 2 — `hashes.code_hash` has zero production callers and no owner

Confirmed by grep (above) and by reading: `diff.py`, `report.py`, `study.py` and `lineage.py` each
read a **recorded string**; `freeze.py` names no code hash at all. So no shipped command computes one
definition while `run` records the other — the live defect this batch could have created, and did
not. Good.

But the residue is dead production code, and the report says *"Not filed here, because it is neither
task 5's nor task 6's surface."* **A gap named in a report and not filed is owned by nobody**, which
is the exact shape `CLAUDE.md` calls out (*"A ledger line saying 'filed' is not a filing"*).

**Adjudication:** it is **not** the *shipped-surface-with-no-reader* class — `code_hash` is not in
`publishable/__init__.py`'s exported surface, so no user can call it. It is plain dead internal code
with one live constraint on deleting it: `reference.md` names `hashes.code_hash` **twice**, in
`W-STUDY-CODE-HASH-MISMATCH`'s row and § Building one, both saying *"`report` never calls
`hashes.code_hash`"* — sentences that would name a nonexistent function if it were removed. So the
right answer is probably *keep it and say why*, not *delete it* — but that is a ruling somebody has
to write.

**Remedy:** task 12 (the records task, which already opens `spec-defects.md`) files it with a reason
and an owner that is a fact, not *"whichever slice next touches hashes."*

### Major 3 — mutation 14 was dropped with no disclosure, in a section headed "every one"

Task 5's brief, step 9: *"Mutation 14 (recompute the upstream's hash at ledger time) makes both
digests `71bf339c…`."* The report's mutation table lists 2, 4, 5, 7, P2 and task 6 step 3 — **six** —
under the heading *"Mutations — every one against the FULL, unfiltered suite, with the count read"*,
and the string "mutation 14" appears nowhere in the report. The report's list of disagreements with
the brief has three items and this is not among them.

**No hole exists** — I ran a proxy so the reviewer is not left guessing: replacing
`lineage.py`'s `"code_hash": record.get("code_hash")` with `None` fails
`test_h6a_fixture_m_one_record_carries_two_hash_definitions`, along with two pre-existing pins
(`test_fixture_r_…`, `test_h8b_fixture_u_…`). Fixture M genuinely pins the verbatim copy.

The finding is the **silence**, not the coverage: an undisclosed drop of a brief-mandated step, under
a completeness claim. **Remedy:** a one-line disclosure in the report saying 14 was not run and why,
or run it.

### Minor 1 — "No other test moved" is false as stated, and its stated proof cannot support it

§ *Existing tests whose expectation moved* says *"Exactly one: guard-pin arm B"* and then *"**No
other test moved.** That is measured, not claimed: the full suite went 2945 → 2951 with zero
failures."*

Task 6 rewrote an existing test — `test_code_hash_still_skips_a_genuine_pycache_dir_inside_the_tree`
— from a three-line body over `tmp_path` to a committed repository with a new literal expectation
(`eec1541e…`) and three new assertions. That is an existing test whose expectation moved. It **is**
disclosed elsewhere (§ The tests, § Mutations), so the information is in the report and only the
summary is wrong. Separately, a green suite is not evidence that no test moved: a test whose
expectation was *updated* also passes. Both halves are the kind of sentence a later reader quotes.

### Minor 2 — a new refusal reachable at `run` is disclosed only in a grep bullet

`E-CODE-FILE-LIST` is genuinely reachable from `run` today. **Measured, end to end:** a project with
`src/vendor` added as a git submodule now exits **1** with
`error E-CODE-FILE-LIST git could not answer which of …'s files are excluded: fatal: Pathspec
'src/vendor/z.py' is in submodule 'src/vendor'`. Before this batch that repo ran to completion.

So batch 3 changed more than a digest: it added a refusal for a class of repository that used to
work. That belongs in § The disclosure beside the moved hashes, not in a bullet under *claims about
other code*. The missing § Errors row is correctly deferred to task 8 by plan and the report flags
it; worth noting for task 8 that **no `E-CODE-*` code has a row today** — `grep -n "E-CODE-"
docs/reference.md` → zero hits, so `E-CODE-DIRTY` has none either.

### Minor 3 — the end-to-end half asserts an inequality where the plan asked for the pre-slice literal

`test_h6a_fixture_c_a_run_records_the_narrowed_digest` asserts `code_hash(root, None) !=
_H6A_T5_RUN_DIGEST` rather than `== 09a843b1…`. The plan's step 4 wanted both branches as literals.
The literal pre-slice value **is** pinned — but in the direct half, over a *different* tree
(`1947d2a2…` on the base tree), so no test in the suite holds `09a843b1…`, the digest the real
command actually produced yesterday for the tree the real command actually runs. The inequality is
adequate for the mutations this slice ships; it is one degree weaker than what was specified.

### Minor 4 — the docstring fix is described as a deletion and is a rewrite

The report says *"closed by deletion rather than rewriting"*, then two lines later *"What replaced
it…"*. The shipped edit deletes *"not from git"* and adds two new clauses. **Both new clauses check
out** — contents genuinely come from the working tree; `command_run`'s `include` genuinely asks git;
the `#how-the-three-are-computed` anchor resolves (`docs/reference.md:3094`); the `draft` clause is
pre-existing spec-tense text and `draft` is still unbuilt (`grep -n "def command_" src/publishable/cli.py`
→ `command_validate`, `command_run` only). Nothing was invented. Only the characterization
is off, and this repo's rule is the one being characterized.

### Minor 5 — `study add` does not copy a `run.yaml` "verbatim", and the report's derivation says it does

§ Corrections 12 requires task 5's report to say which of the five carriers of the moved hash are
pinned and which are derived. The report calls the bundled copy derived, on the ground that
*"`study add` copies a run's `run.yaml` **verbatim**, so the record's own pin covers the bundled
copy."*

**Read: it does not.** `study.py::study_add` does `read_record_file(run_yaml)` →
`_redacted(record)` (a `copy.deepcopy`, then four host-identifying fields overwritten) →
`target.write_text(yaml.safe_dump(redacted, sort_keys=False))`. The file is **re-serialized**, not
copied. This repo has already shipped one defect of exactly that shape — a resolved-values echo
whose YAML aliasing a `yaml.safe_load` reader normalized away.

**The conclusion survives, the word does not.** `_REDACTED_DATA_FIELDS` and the three provenance
redactions reach `config.data.input_dir`/`output_dir`, `provenance.git.repo_root`,
`provenance.environment.hostname` and `provenance.input_manifest` — `code_hash` is a top-level
scalar and is untouched, so the bundled figure really is the record's own and the record's pin
really does cover it. The derivation should be restated on the mechanism it actually rests on
(*`code_hash` is not among the fields `study add` redacts, and a scalar survives a YAML round trip*)
rather than on a "verbatim" that is false of the code.

### Minor 6 — Fixture J's docstring states four states and its assertions instantiate two (task 6's one finding)

`test_h6a_fixture_j_the_gate_and_the_hash_agree_on_an_excluded_file` enumerates all four states of a
file under the two trees and asserts **two**: *present but excluded* (neither dirty nor hashed) and
its control *untracked and not excluded* (dirty and hashed). *Tracked and clean* and *tracked and
modified* are named in the docstring and instantiated nowhere in the test.

**Both are in fact pinned, elsewhere, and naming where is the whole remedy** — *a seam named
precisely and instantiated by no fixture* is on this repo's list, and the fix is one sentence rather
than more assertions:

* *tracked and clean → not dirty*: `tests/test_provenance.py::test_a_clean_tree_is_not_dirty`.
* *tracked and modified → dirty*: `tests/test_provenance.py::test_only_the_hashed_trees_make_it_dirty`,
  which modifies a tracked `src/placeholder.py` and asserts `code_dirty is True`.
* *tracked and clean → hashed*: every digest literal in this slice — arm A, arm D, Fixture C, Fixture
  D — is computed over a tree of tracked, clean files, so a rule that dropped them would fail all of
  them.

This is the only finding against task 6, and it is a docstring's reach exceeding its own assertions,
not a coverage hole.

---

## Claims I checked mechanically, and what each returned

Every one of these is a claim the report makes about **other** tests, rows or code — the place where
six consecutive slices' "zero disagreements" hid.

| Claim | Command | Result |
|---|---|---|
| arm C reads arm B's constant by name; nothing else does | `grep -rn "_H6A_BASE_WITH_ENV_DIGEST\|_H6A_RUN_WITH_ENV_DIGEST" tests/` | true — arm B's definitions and uses, one arm C reference |
| arm D calls `code_hash(…, None)`, so git is never asked | `grep -n "code_hash(e_tree, None)\|code_hash(d_tree, None)" tests/test_hashes.py` | true — lines 587, 613 |
| no live reference to the removed test | `grep -rn "test_code_hash_ignores_pycache" tests/ src/ docs/ README.md CLAUDE.md` | true — one hit in `tests/`, the survivor's docstring; the other five are the development record, which must not be retro-edited |
| `E-CODE-FILE-LIST` has one emit site, no § Errors row | `grep -rn "E-CODE-FILE-LIST" src/ tests/ docs/*.md` | true — one `raise` at `provenance.py:81` |
| no other command computes a `code_hash` | `grep -rn "code_hash(\|code_hash_of(\|hashed_files(" src/` | true — and it is also how Major 2 was established |
| Fixture M's eleven-key literal | read against my own real run's `run.yaml` | true, in order |
| `_build_fixture_f_upstream` reads its step name from its own `run.yaml` | read `tests/test_cli.py:15961` | true |
| `study add` copies a run's `run.yaml` verbatim | read `study.py::study_add` and `_redacted` | **false as worded** — see Minor 5; the conclusion holds, the mechanism is a redact-and-re-dump |
| Fixture J's four states are all instantiated by it | read the test body | **two of four** — see Minor 6; the other two are pinned in `tests/test_provenance.py` |
| arm N untouched and passing | `git diff 59ba24b HEAD -- tests/test_diff.py` empty; both arm-N tests pass and both fail under the `diff.py` mutation | true |

**The two-case sweep, re-run rather than trusted, and proven able to fail.** A newline-insensitive
sentence regex pairing *hash/hashed* with *exclud/ignor/.gitignore*, over `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md`,
`docs/superpowers/spec-defects.md`, `hashes.py`, `provenance.py` and `cli.py` — **files named, output
never filtered**. Positive control on the same file list for a string known present (*"How the three
are computed"*): **14 hits**, so the sweep can fire. Result: **no two-case version of the
which-files-are-hashed rule exists.** Every site either links to § How the three are computed or
names one case and links to *"the other three cases"* / *"the first of its four cases"*.

One expected-and-planned staleness the sweep surfaced: `spec-defects.md`'s entry *"`code_hash` is
not `.gitignore`-aware (S1 deviation, not a spec defect)"* is false as of `9685ae0`. **Task 12 step 1
strikes it by name**, so this is a scheduled deferral rather than a finding — recorded here so the
next reader does not re-derive it.

**Mechanical pass on the one `*.md` this batch wrote** (`task-b3-report.md`): zero trailing
whitespace, zero tabs, zero invisible unicode, every table row matching its header's column count.

---

## What was verified by behaviour versus by reading

**By behaviour** (a command run, a mutation applied, a digest recomputed): the whole value change end
to end through the console script, on both sides of the slice; the `latest` pointer; Ruling F's
neutralization, with a positive control and a repo-rule control; all eight digests, recomputed from
the algorithm rather than by calling `hashes.py`; all six of the report's mutations against the full
suite with counts read; four extra mutations proving arms A/B/C/D/E/F/N can still fail; `E-TEMPLATE-LOAD`
on the base tree; `E-CODE-DIRTY` on a first-call resolver write; `E-CODE-FILE-LIST` from `run` via a
real submodule; the mutation-14 proxy against Fixture M; all four gates; and every revert.

**By reading** (with a grep behind it): `command_run`'s phase order; `resolve_units`' two call sites;
the arm-B advance specification against the shipped diff; arm E's false sentence; the docstring's
replacement clauses; every claim in the table above.

**Not verified:** `check-ignore`'s cost as a function of pattern count (unmeasured by the plan too,
and filed by Ruling G); the 875 ms figure, which I did not re-time.
