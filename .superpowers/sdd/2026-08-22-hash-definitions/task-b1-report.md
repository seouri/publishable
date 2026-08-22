# Batch 1 — tasks 1, 2, 7, 10 — report

**Commits:** task 1 `c863e3e`, task 2 `ad59bdd`, task 7 `76efc72`, task 10 `13ae83c`, plus one
fix round closing two findings this report's own review raised (see § The fix round).
**Suite:** `2931 passed, 1 skipped, 2 xfailed` at the batch's start and after task 1 and task 10;
`2937` after task 2 (+6, one per pin arm); `2939` after task 7 (+2, arm N and its control). Every run
was in the foreground, after clearing `pytest-of-joon` and `__pycache__`. `ruff check`,
`ruff format --check` and `mypy` clean before each of the four commits.

---

## Ruling F, measured rather than adopted

In a throwaway repo with a global exclude file holding `*.log`, a committed `.gitignore` holding
`b.txt`, and `a.log`/`b.txt`/`c.txt` present:

```
printf 'a.log\0b.txt\0c.txt\0' | git check-ignore -z --stdin                 → a.log, b.txt   rc 0
printf 'a.log\0b.txt\0c.txt\0' | GIT_CONFIG_GLOBAL=/dev/null \
    GIT_CONFIG_SYSTEM=/dev/null git -c core.excludesFile= \
    check-ignore -z --stdin                                                  → b.txt          rc 0
```

Then `.git/info/exclude` gained `d.txt` and the neutralized call returned **`b.txt` and `d.txt`** — so
the ruling's two claims both hold as stated: the global and system config are genuinely neutralized,
and `.git/info/exclude` survives every flag. That is the one residue, and it is what task 1 discloses.

**Which brief text Ruling F overrode.** Task 1's step 1 table row named *"the user's `core.excludesFile`"*
as an exclude source and step 3 asked for a machine-dependence disclosure arguing *"the dirty gate already
has exactly this property today."* Ruling F rejects that framing by name — a gate answers a local
question, a hash does not — so the row names only the repo's own committed rules plus
`.git/info/exclude`, and the paragraph written in step 3's place is the much smaller one: the exclude
question is asked with global and system config neutralized, `.git/info/exclude` is the exception no flag
can disable, and a file whose hashing status must be machine-independent is a file you commit. The
"dirty gate already has this property" paragraph was **not** written.

---

## Disagreements with the brief and the plan — three, none of them zero

**1. Arms A and B's end-to-end halves are unbuildable as the brief states them, and this reshaped the
arms.** The brief's step 1 says to build the base tree — `src/pkg/step.py` = `a = 1\n`,
`templates/t.py` = `b = 2\n` — and "run the same tree end to end through `main(["run", …])`". Measured:
`templates/t.py` is discovered by path as a project-local template, imports cleanly, registers nothing,
and both `validate` and `run` refuse the config at exit 1 with

```
error   E-TEMPLATE-LOAD      experiment_type
        the project-local template …/templates/t.py imported cleanly but called
        `@register_template` on nothing — every file under `templates/` that is not
        itself a template must be `__`-prefixed
```

Every repair — a registering template, a `__`-prefixed helper, an experiment package under `src/` — is
a different path or different bytes, and the digest is a function of exactly those, so `71bf339c…` is
not a runnable tree. **Each of arms A and B therefore holds its two halves over two trees**, each
asserting its own tree's digest beside its own consequence: the plan's tree for the direct call (keeping
the plan's literals, which tasks 3, 5 and 8 also build against) and a runnable project for the `run_id`
half, whose experiment package is imported from a directory outside both hashed trees — the route the
H6 scoping's own zero-file probe used. Written out in the arms' own docstrings, because a reader diffing
against the plan will otherwise read it as a silent shrinkage.

**Consequence for task 5, stated in advance:** arm B's moving set is **four** literals, not two. They are
listed in its docstring — `ebc5ee53…`→`71bf339c…`, `a74f3d44…`→`f6a935cf…`, the run-directory suffix
`_a74f3d4`→`_f6a935c`, and the recorded `code_hash`, which is the same constant as the second.

**2. `input_manifest_hash` is not a literal unless the input's mtime is one.** `manifest.build_manifest`
records `st_mtime_ns` per file and `manifest_hash` canonicalizes the whole manifest, so arm C's figure
moves on every run. Arm C's project fixes the roster's mtime with `os.utime(..., ns=…)` rather than
recomputing the figure from the record — a recomputation would assert the function equals itself.

**3. `allocation_hash` is `null` under the plan's implied project.** A `within` allocation with no group
axis writes no `allocation.json`, so the figure the brief lists among the *seven present* values would
have been an absence — the thing arm C exists not to be. Arm C's project declares
`allocation: between` with `assign: {arm: {method: by_attribute}}` and a `sweep.groups` axis, which
gives the arm a real digest and no RNG.

Two smaller notes, neither a disagreement: `run_a_project` was deliberately not the driver (§ Corrections
11 — its `_env_file` writes at the project root, in neither hashed tree), and the pin project's config is
hand-written rather than materialized, because `materialize_config`'s text is a generator's output and
`parameters_hash` is pinned as a literal with no authorized editor.

---

## Every pinned literal, and how it was computed

Nothing below is transcribed from the plan. Each was produced here by building the tree and calling the
shipped `code_hash`, or by reading a real run's own artifacts back.

| Literal | Arm | How |
|---|---|---|
| `sha256:71bf339cc9463f4c776c711f3d65ccf9b3bc1e18d383b78ae7d4e5170b526c2b` | A, N | `code_hash` over the base tree (`src/pkg/step.py` = `a = 1\n`, `templates/t.py` = `b = 2\n`), committed |
| `sha256:ebc5ee53ac39bbab63d5270475271068dc67e6f34ead9db648bad114845b1cce` | B, N | the same tree plus untracked `src/pkg/.env` = `OPENAI_API_KEY=sk-live-1\n` |
| `sha256:f6a935cfc29196b2a5f5a7f873096c4ab3ee077ff3152afedafeb34fb919078a` | A | `code_hash` over the runnable project (one hashed file, `src/pkg/step.py`); its real run's directory is `run_…_f6a935c` |
| `sha256:a74f3d44dc1dd9e905550b5a7b59220da26c95db2e96f235c3cd3c3743eb17bc` | B | the runnable project plus untracked `src/pkg/.env`; its real run's directory is `run_…_a74f3d4` |
| `sha256:0e55a047167d30e2caa3acefe8cff398e391a19d801add5932f95b1e2eb7232e` | C | `parameters_hash`, read off arm B's project's real `run.yaml` |
| `sha256:15d29dcab933c4824f78ff18c7ed7a3b2b83fe693c2faaa405cd54e92bdc3dc1` | C | `input_manifest_hash`, same record, with the roster's mtime fixed |
| `sha256:c0b8db057b9b36718982fea80396ba000fd75dd36ff2262bbbca881af07e341e` | C | `uv_lock_hash`, over the hand-written two-line `uv.lock` |
| `sha256:29c8190c878f0ef063976719429b96a0811c255dd7d4d9d25c14cf43e02e2ec2` | C | `units_hash`, same record |
| `sha256:27924889ef569abc53b382bfa5698e64f6fffd5693ed6f50b33e647b4789c093` | C | `allocation_hash`, same record |
| `1eda4dffe5d97175b61dbccc3b56c314fe5c760fd808f78cd5a2b953c3e3e269` | C | the one per-file digest in `manifest/input.json` |
| `sha256:73966ce7e98da4d01daf38263842f7751f9db17d2c82e0c349f94a9ad5d99d8e` | C | `design_digest`, read off the run's own `sweep.yaml` |
| `sha256:eec1541edde45c11c395e788000f719a48965a8f6fd2b3772a56de92cca18dc2` | D | the base tree plus a **tracked** `src/pkg/loose.pyd` = `X`; unmoved by a tracked `src/pkg/__pycache__/keep.py` on top |
| `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | E | `code_hash` of a directory that does not exist, and of one holding an empty `src/` |
| `is 0.9.0 but the template reports 1.0.0; unset here and left to the template's default: analysis.confidence` | F | `validate_config` through a `Collector`, whole message |

**The plan's `6ddb8634…` appears nowhere** — § Corrections 5 measured it unreproducible, and arm D
carries `eec1541e…` for the bytes fixed at `X`, which reproduced exactly.

**One literal in this batch was wrong before it was pinned, and the fixture caught it.** The first
measurement of arm C's `parameters_hash` was `13f87e1f…`, taken from a scratchpad probe whose config
carried different `replication.rationale` text from the one the test ships. `rationale` is inside the
hash; `metadata` is not. The test failed on the literal, which is the evidence that the figure
discriminates rather than merely being present.

**The console-script cross-check the controller asked for.** Arms A and B's runnable projects were also
driven through the installed console script — `uv run publishable run <cfg>` with the outside package on
`PYTHONPATH`, from the project directory — at exit 0, producing `run_…_a74f3d4` and `run_…_f6a935c`. The
in-process `main` the tests use and the shipped command agree on both digests, so no second finding.

---

## Which arms have no authorized editor

| Arm | Editor | Where |
|---|---|---|
| A — the ordinary path does not move | **NONE** | `tests/test_cli.py` |
| B — an excluded `.env` moves the hash today | **task 5 only**, four literals, all named in the docstring | `tests/test_cli.py` |
| C — the seven other present figures are unmoved | **NONE** | `tests/test_cli.py` |
| D — a tracked excluded file is hashed, a tracked `__pycache__` one is not | **NONE** | `tests/test_hashes.py` |
| E — the empty digest, and the guard did not migrate into `hashes.py` | **task 3 only**, adding the literal `None` and changing no assertion | `tests/test_hashes.py` |
| F — `W-TEMPLATE-VERSION`'s whole message | **task 11 only**, zero characters | `tests/test_validate.py` |
| N — `diff` prints `code_hash DIFFERS` for identical code | **NONE** (Ruling I) | `tests/test_diff.py` |

Four of the seven have no editor at all, so a passing arm is the proof.

**Every arm was proven able to fail, by mutation, and restored by editing the file back and re-running
— never by `git checkout`.** `_H6A_BASE_STEP` `a = 1\n`→`a = 2\n` failed arms A, B, C and D; Fixture D's
`.pyd` bytes `X`→`Y` failed arm D; one word of arm F's message failed arm F; making arm E's second tree
non-empty failed arm E; and two mutations to `diff.py`'s figure comparison (`if True:` and
`figure_a != figure_b`) each failed **both** arm N and its control. `src/publishable/diff.py` is
byte-identical to its committed state, verified by `git diff` reporting nothing **and** by re-running the
arms green.

---

## § Errors / § Warnings — every emit site, for every code these four tasks touched

No code is minted by this batch and no diagnostic's behaviour changes, so the check is over the codes
these tasks' prose names.

| Code | Emit sites, grepped | Rows in `reference.md` | Work here |
|---|---|---|---|
| `W-STUDY-CODE-HASH-MISMATCH` | **one** — `grep -rn '"W-STUDY-CODE-HASH-MISMATCH"' src/` → `report.py` only | one row in § Warnings core reports (the other three mentions are `W-STUDY-COMMIT-MISMATCH`'s row citing it, § Building one's prose, and § How the three are computed's new paragraph) | its row gains **one link and nothing else**; its three candidate causes stay three |
| `W-TEMPLATE-VERSION` | **one** — `grep -rn '"W-TEMPLATE-VERSION"' src/` → `validate.py` only | one row, unchanged | pinned whole by arm F; no row edit |
| `E-TEMPLATE-LOAD` | not touched | unchanged | named only in a test docstring, as the refusal that made the plan's base tree unrunnable |
| `E-CODE-DIRTY` | not touched | still has **no** row — H6b task 17's, named so its absence is not read as this batch's omission | none |
| `E-STEP-PARAM-UNKNOWN` | not touched | unchanged | named in `covered_config`'s new docstring as Ruling B's third ground |

---

## What was grepped, rather than a count

- **`run.yaml`'s key lists are already pinned and are NOT duplicated.** `grep -rn "set(run_yaml)|list(run_yaml)|top-level key" tests/*.py` found
  `test_h8a_arm_a_a_clean_run_top_level_shape_status_and_exit` (the whole top-level list, in order) and
  `test_h8a_arm_b_the_provenance_key_list_and_upstream_empty` (the whole `provenance` list), both in
  `tests/test_cli.py`. Arm C cites them and asserts neither.
- **No existing test asserts `W-TEMPLATE-VERSION`'s message.**
  `grep -rn "but the template reports|unset here and left to" tests/ src/ docs/*.md` → the two f-strings
  in `validate.py` and **nothing in `tests/`**. The nearest test,
  `test_a_moved_template_version_names_a_parameter_the_config_leaves_unset`, asserts two substrings,
  neither of which can see the wording between them.
- **Arm E's negative controls.** `grep -n "nonexistent_empty_repo" tests/test_hashes.py` → the two tests
  the design names and nothing else; neither states the digest as a literal.
- **The narrow "`.gitignore`" form of the hashing rule has no other home.** Newline-insensitive sweep for
  `gitignore`, `an ignore file`, `rather than git`, `from the working tree`, `no ignore file` over the
  four documents, `CLAUDE.md`, the feasibility analysis, `spec-defects.md`, `src/**` and `tests/**`: the
  only prose statements of the rule are the two `reference.md` sites this batch edited. **`hashes.py`'s
  `code_hash` docstring says *"Read from the working tree, not from git"*** — true today and false after
  task 5. It is **not** this batch's to edit (task 1 is documents-only) and Decision 3 already assigns
  `hashes.py`'s docstring the link to the four-case table; flagged here so task 3 or 5 closes it.
- **What the mechanical pass actually checked, and what it did not.** The throwaway checker covers
  every relative link and `#anchor` resolving, duplicate heading anchors, table rows against their
  header's column count, empty rows, trailing whitespace, tabs and invisible unicode, with fenced blocks
  skipped — clean. `×`-versus-`x` and en dashes were checked **separately, over this batch's added lines
  only**: `git diff 6aec85a..HEAD -- docs/reference.md | grep '^+'` carries **no** en dash and no
  `<digit> x <digit>`, and no anchor this batch writes or links to contains one. The table checker
  reports **four** `COLS` mismatches, all pre-existing and all caused by an escaped `\|` inside a cell
  which the checker does not parse; their line numbers were compared before and after each insertion and
  none sits in a table this batch touched.
- **Task 10's sweep, newline-insensitive and proven able to fail.** Needles `normalized to what`,
  `would have materialized`, `a difference with nothing to print`,
  `hashes identically to one that spells it out`, `an omitted \`cluster_by\``, `normaliz` — each file's
  whitespace collapsed to single spaces before matching, and the **file list** filtered, never the
  output. Before: `docs/reference.md` and `src/publishable/hashes.py` (two hits, both inside
  `covered_config`'s docstring paragraph) plus `docs/superpowers/spec-defects.md`. After: **only
  `spec-defects.md`**, which is task 12's to strike — and this batch's docstring edit is what makes that
  strike safe. The sweep was proven able to fail by running it against `Does not normalize`, a string
  known present, which it found. The feasibility analysis's six `normaliz` hits are the word
  *abnormalizing* in a domain hypothesis and are untouched, as is the whole file (task 13's).

---

## The fix round — two findings, both in the pin, both closed

**1. Arm N's control had a test whose NAME claimed the guarantee its assertion denied.** Its first block
built a pair from the same digest twice, diffed one of them against the *original* run — a genuinely
differing pair — and asserted `DIFFERS`, inside a test named
`..._control_two_records_agreeing_on_code_hash_print_identical`. It also carried
`assert same_a == same_b`, an assertion satisfied by construction rather than a check. That block is
**deleted** rather than rewritten; the control now copies the run once, carrying the run's **own**
`code_hash`, and asserts `identical` plus the printed digest. `_h6a_record_pair` was split so the
control takes a single-copy helper rather than a pair helper it half-used.

Its docstring's mutation claim was then measured rather than asserted, and it had been wrong: inverting
`_render_row`'s `figure_a == figure_b` fails **both** arm N tests, while forcing it to `True` fails the
`DIFFERS` arm and **passes** the control. The docstring now states that asymmetry, which is what makes
the pair rather than either test the pin.

**2. Arm C's `code_hash` assertion reads arm B's constant, and "zero lines change" needed saying
precisely.** Arm C asserts `_H6A_RUN_WITH_ENV_DIGEST` — arm B's module-level constant by **name**, not a
second copy of the digest string — so task 5's authorized edit to that constant carries into arm C with
zero lines of arm C changing. Without that sentence a reviewer would see a no-editor arm's value move and
read the pin as broken. Arm C's docstring now says it, and says why the moving figure is asserted there
at all.

---

## Concerns for the controller and for later tasks

1. **Task 5's brief will name two moving literals in arm B and the arm names four.** The extra pair is
   the runnable project's, created by finding 1. Task 5 must be told, or it will read the arm as having
   drifted.
2. **`hashes.py`'s `code_hash` docstring** claims it reads the working tree *"not from git"*. Task 3 or
   task 5 owns it; unclosed here by scope.
3. **Arm C's literals are hostage to the config's bytes**, which is deliberate (hand-written rather than
   materialized) but means a future slice adding a required config key breaks the arm. That is the normal
   cost of a no-editor arm and is recorded rather than mitigated.
4. **Arm A and B each run a real project twice** (direct half plus end-to-end half); arm C runs a third.
   Batch cost is about 12 s of the suite's ~3 min, measured.
5. **`.superpowers/sdd/.gitignore` was found clobbered to a bare `*`** at the batch's start, restored
   from `HEAD` before the first commit, and this report is added with `git add -f`.
