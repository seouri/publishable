# H6b — the environment record and the diagnostic debt — whole-branch review

**Run 2026-08-23 against `h6b-environment-record` at `fa54834`** (31 commits ahead of `main` at
`2b18435`), clean tree, this worktree to myself. Nothing below is carried from a report, a review or
the ledger without re-running it; where a claim is established by **reading** rather than by
**behaviour** it says so.

## Verdict: HOLD — three Majors, all closable in a same-day fix round

The slice **is** additive, measured rather than assumed (§ Additivity below), and every pin it names
can fail. The three Majors are all *claims*: two false sentences and one unpinned document change.
None is a behaviour defect, and none moves a number.

## Gates

| Gate | Result |
|---|---|
| `uv run pytest` | **2971 passed, 1 skipped, 2 xfailed** in 206 s — the expected figure |
| `uv run ruff check .` | All checks passed! |
| `uv run ruff format --check .` | 93 files already formatted |
| `uv run mypy` | Success: no issues found in 52 source files |

**Delta against `main` accounted for: 2963 → 2971, +8, and the eight are named.**
`git diff main...HEAD -- tests/ | grep -c "^+def test"` → **8**: arms A, B, C-1, C-2, D (task 3),
arm T (task 1), Fixture G (task 5), Fixture E (task 4). No test was deleted or renamed. Ledger's
2964 / 2969 / 2971 / 2971 / 2971 step sequence is consistent with that split.

The suite was re-run **after every mutation was reverted by editing back**, and the tree is
`git status --porcelain`-clean at the time of writing.

---

## Findings

### Major 1 — the new `E-GIT-NO-REPO` § Errors row is wrong about one of the three sites it enumerates, and task 8 propagated the error to a second home

The row (task 5, `9e292ea`, `docs/reference.md` § Errors core raises) reads:

> Three sites catch it **by code**, as the pass branch of a check of their own: `validate._check_data`
> returns quietly …; `validate.validate_config` catches it under a bare `except ContractError`,
> leaving `repo_root` `None` …; `study._refuse_if_in_repo` catches it as the pass branch of its own
> in-repo refusal.

The middle member is **not** a catch by code and is **not** the pass branch of any check.
Established by reading the code (`grep -n "find_repo_root" src/publishable/validate.py` → two call
sites):

```
validate.py:511   repo_root: Path | None = find_repo_root(config_path)
validate.py:512   except ContractError:            # <- no code test at all
validate.py:1221  repo_root = find_repo_root(config_path).resolve()
validate.py:1223  if exc.code == "E-GIT-NO-REPO":  # <- by code, and re-raises otherwise
```

Only **two** sites catch by code (`validate._check_data`, `study._refuse_if_in_repo`). The row's own
lead clause counts three and its own second member contradicts it in the same sentence.

**This slice knew.** Task 8 (`2a62bbe`) filed a *new* `spec-defects.md` entry —
*"OPEN — `validate_config`'s bare `except ContractError` around `find_repo_root` is wider than its
comment claims"* — whose body says outright: *"The one in `validate_config` catches
`except ContractError:` with no code test at all."* **The same commit** also propagated the false
"three that catch it **by code** as their own pass branch (`validate._check_data`,
`validate.validate_config`, `study._refuse_if_in_repo`)" phrasing into the `E-GIT-NO-REPO` entry's
2026-08-23 amendment. So the claim has **two homes** and the file it lives in contradicts it a few
hundred lines away.

Task 5's entire purpose was *one row per code, covering every emit site, not narrower or wronger than
its code* — the shape `CLAUDE.md` records as the whole-branch Major on two of H8's sub-slices.

`CLAUDE.md`'s own sentence (*"one raise and six reaches, three of them deliberate swallows"*) is
**correct** and needs no edit: `validate_config` is a swallow, it is just not a swallow *by code*.

**Route — fix round now.** Two edits, both deletions rather than rewrites: in `docs/reference.md`,
say *two* sites catch by code and move `validate.validate_config` out of that clause into the same
sentence that already carries `cli._load_experiment_for` (both catch by type); in
`spec-defects.md`'s `E-GIT-NO-REPO` amendment, the same. The reach-path **count** of six does not
change and neither does the § Errors preamble's *"Two rows in this table are not raises"* (verified: the
section still holds exactly two `no exception` `Type` cells).

### Major 2 — Ruling O's change to the shared worked example is pinned by nothing, and the slice's own guard arm was proven unable to see it

Task 2 (`2ed64da`) changed § The two files' `hardware: {gpu: "1x A100 80GB", cpu_count: 32}` to
`hardware: {cpu_count: 32}` — the one edit that makes the shared worked example agree with what
`command_run` writes, and the edit `CLAUDE.md`'s slice entry leads with.

**Mutation, run:** reinstate the old line in `docs/reference.md`.

```
python3 -c "p='docs/reference.md';s=open(p).read();open(p,'w').write(
  s.replace('hardware: {cpu_count: 32}','hardware: {gpu: \"1x A100 80GB\", cpu_count: 32}'))"
uv run pytest tests/test_cli.py tests/test_diff.py tests/test_report.py tests/test_provenance.py -q
→ 626 passed, 1 skipped in 98.63s
```

**Nothing fails.** Ruling O can be silently reverted in the document while the code writes
`{cpu_count}` only and the new prose two hundred lines below says a GPU is an apparatus fact.

The design named guard-pin **arm R** as the proof this edit was safe, and *measured that arm R cannot
scan the line* (`_H5A_ARM_D_LITERALS` carries no substring of it). Confirmed here independently:
changing `cpu_count: 32` → `64` also leaves arm R green (`3 passed`). Both halves of that measurement
are right; the conclusion drawn from them is the gap — **arm R proving it cannot move is not the same
as the line being pinned**, and the plan's own correction 19 (*"No test extracts § The two files'
`run.yaml` fenced block"*) recorded the absence and asked for nothing.

This is the shape the gate brief names: *a slice's own central claim pinned by nothing.*

**Route — fix round now.** One test extracting § The two files' `provenance.environment` fenced block
and asserting its key set equals `command_run`'s written key set (both ends read, as Fixture G already
does for § Errors) — which pins Ruling O, pins Decision 9's order claim at the document end, and
would have caught the pre-existing six-unwritten-keys drift this slice closed by hand.

### Major 3 — the FIFTH sentence gone false under this slice's own later change, in the file Decision 13 swept, eight lines below the third home it found

`tests/test_study.py`:

```python
def test_study_add_redacts_hostname_when_present_on_a_synthesized_record():
    """Fixture Y: the one row exercised only over a hand-built record,
    because nothing in this build writes `provenance.environment.hostname`
    today (it is H6's).
```

Three claims, all false at HEAD: this build **does** write it (task 3); it is **not** the one row
exercised only over a hand-built record (task 4's Fixture E exercises it over a real bundled record —
`grep -n "hostname" tests/test_study.py` shows both); and *"it is H6's"* points at **this slice**, so
the deferral reads as live work when it has landed.

Decision 13's table listed **three** homes of this claim and task 7 fixed all three
(`secrets.py` deleted, `study.py::_redact` superseded, `_fixture_y_record` deleted). Batch 4's review
then swept for a fourth home and the ledger records *"The fourth home the reviewer swept for did not
exist, checked newline-insensitively across `src/`, `tests/`, the four documents and `CLAUDE.md` with
a can-fail control."* **It exists, in the same file, eight lines below the third.** The sweep almost
certainly keyed on `ebf642a` / the exact `study.py` phrasing; this home says the same thing in other
words.

Re-swept here for the **claim** rather than the spelling, newline-insensitively, over `src/**/*.py`,
`tests/**/*.py` and the four documents plus `CLAUDE.md` plus the feasibility analysis, patterns
`nothing in this build writes|never written|is never written|no code has ever written`, `ebf642a`,
`it is H6`; can-fail control `provenance.environment.hostname` → **4 hits**. Exactly one false
survivor, this one. (The `report.py` and `cli.py` hits are about other fields and are true; the
`study.py` hit is the superseded-and-dated one, which is correct.)

Aggravating: this docstring **was edited after task 3**, by the batch-2 controller ruling that appended
the arm-S editor note to it — so a hand was on the file with the false sentence three lines above.

**Route — fix round now.** Delete the first paragraph's causal clause (prefer deletion to rewriting);
the arm-S note below it stands unchanged, and arm S's body must not move.

### Minor 1 — the ledger cites two commit SHAs that exist nowhere in this repository

`.superpowers/sdd/2026-08-23-environment-record/progress.md` cites batch 4's follow-up as `2a9c05b`
and batches 5/6's as `1b5f0cd`.

```
git cat-file -t 2a9c05b → fatal: Not a valid object name 2a9c05b
git cat-file -t 1b5f0cd → fatal: Not a valid object name 1b5f0cd
```

The real commits are `6497284` (*"H6b batch 4 follow-up: fixture Y's docstring gets the deletion its
brief asked for"*) and `912c57d` (*"H6b follow-up: the root-`.gitignore` entry's heading now agrees
with its own amendment"*), both of which existed **before** the ledger sections citing them were
written. The ledger is what later slices read as authority and an unresolvable SHA is worse than none.

**Route — fix round now, by appending a correction** (the ledger is a dated record; the two lines are
not rewritten in place).

### Minor 2 — `secrets.py`'s surviving structural claim is a safety argument pinned by nothing

The claim after task 7's deletion: *"nothing in this module imports `publishable.provenance` or writes
into the document it builds."* It is **true at HEAD** — established by reading
(`grep -n "provenance" src/publishable/secrets.py` → only the docstring itself). It is pinned by
nothing:

```
# added to secrets.py: import publishable.provenance
uv run pytest tests/test_secrets.py tests/test_study.py tests/test_apparatus.py -q → 119 passed
```

A safety argument in a comment needs a mutation like any other. This is a **pin gap, not a false
claim**, which is why it is a Minor.

**One observation attached, not a finding.** The deleted enumeration was doing a sliver of work the
structural sentence does not do: *"secrets.py never writes provenance"* is not *"provenance never
carries a secret"*, and `hostname` now enters the record through a literal with **no** credential
check — where the apparatus path refuses a fact merely *containing* a declared credential
(`E-APPARATUS-FACT-CREDENTIAL`, H7d's Major). A hostname equal to or containing a declared credential
value is far-fetched and I am **not** filing it; recorded so the next reader of that paragraph knows
which claim it is and is not making.

**Route — filed, owner unassigned with the reason:** no remaining chartered slice has `secrets.py` as
its surface (H9 is `reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`; H3c-3's remaining 14 are
folds and holdouts inside cells).

---

## Additivity — the charter's ground, tested rather than assumed

**Method: one real config run on `main` and on HEAD, and the two `run.yaml`s diffed leaf by leaf.**
A `main` worktree at `2b18435`, the same driver script under both (`PYTHONPATH=<wt-main>/src` proven
to win over the editable `.pth`: `import publishable` resolved into the worktree), a project scaffolded
**outside** this repo, `run` at exit 0 under both.

```
ADDED keys (HEAD only):
  + .provenance.environment.os              = 'Darwin-25.5.0-arm64'
  + .provenance.environment.hostname        = 'macbookair.lan'
  + .provenance.environment.hardware.cpu_count = 8
REMOVED keys (main only):                   (none)
CHANGED values on shared keys:
  ~ .run_id, .config.data.input_dir, .config.data.output_dir,
    .provenance.git.repo_root, .provenance.git.commit,
    .provenance.input_manifest_hash, two started_at/wall_seconds
```

Every changed value is an artefact of the two probes being two different directories and two different
project repositories (different tmp paths → different manifest hash; separate `git init` → different
commit) — **not one of them is a value H6b moved.** `code_hash` and `parameters_hash` are byte-equal.
`run.yaml`'s eleven top-level keys and `provenance`'s thirteen are identical lists. The three
insertions preserve every shipped key's relative order (`manager`, `python_version`, **os**,
**hostname**, `uv_lock`, `uv_lock_hash`, **hardware**).

**And the run directory earns nothing new:** `diff <(cd A && find .|sort) <(cd B && find .|sort)` →
identical file lists. There is exactly **one** construction of these facts and one writer of
`run.yaml` (`grep -rn "python_version\|platform\.\|socket\.gethostname\|cpu_count" src/publishable/`
→ `cli.py`'s single literal plus `run_identity.py`'s pre-existing lock host; `grep -rn
"git_provenance" src/` → one call site, inside `command_run`). **`freeze` builds no environment block**
— checked, because a second constructor would have made this two spellings of one fact.

**The backward half, which the charter implies and no test covers:** `study new` / `study add` /
`report` / `diff` all run at exit 0 over a **`main`-produced** record that lacks all three keys.
`study add` bundled it unchanged (`{manager, python_version, uv_lock, uv_lock_hash}`), `report` on both
the run and the bundle exited 0, and `diff` between the two records printed its usual rows with **no
sixth row** for `os`/`hardware` (Decision 14 confirmed by behaviour).

**Verdict: the slice is genuinely additive.** No disclosure is owed.

## The activation — verified end to end, and the pin proven able to fail

A real bundle built **outside any repository** (`study new` then `study add`, exit 0 both):

```
legacy (main-produced) {'manager':'uv','python_version':'3.13.7','uv_lock':None,'uv_lock_hash':None}
fresh  (HEAD-produced) {..., 'os':'Darwin-25.5.0-arm64',
                        'hostname':'<redacted by study add>', ...,
                        'hardware':{'cpu_count':8}}
```

`hostname` redacted, `os` and `hardware` verbatim. **Then the mutations, each run:**

| Mutation | Result | Expected |
|---|---|---|
| `_redact` also redacts `os` | `FAILED …redacts_hostname_but_leaves_os_and_hardware_end_to_end` (1 failed, 42 passed) | Fixture E's verbatim half — ✔ |
| `_redact` stops redacting `hostname` | **two** failures: arm S's synthesized-record test **and** Fixture E | ✔ (design mutation 8) |
| `_redact` redacts `hostname` **unconditionally** | `FAILED …leaves_hostname_untouched_when_absent_from_the_source` | the mutation arm S exists to catch — ✔ |

**Arm S survives its own slice's falsified premise.** The batch-2 controller ruling replaced
"absent by accident" with an explicit `del record["provenance"]["environment"]["hostname"]` and left
the assertion byte-identical. Attacked directly: the invent-the-key mutation still fails arm S and
nothing else. **The ruling preserved the property, not only the assertion.**

## The guard pin — six arms, no unauthorized movement, every arm proven able to fail

`git log -p main..HEAD -- tests/` and the branch diff: arm **P** gained exactly three `.pop(...)` calls
and three assertions with the `==` literal byte-identical (its authorized edit, task 3, matching the
advance spec); arms **Q, R, U** gained docstring-only lines; arm **S** gained the ruling's `del` plus
docstring; arm **T** is new. **No arm's assertions moved except P's authorized three.**

| Arm | Mutation run | Result |
|---|---|---|
| **P** | `"manager": "uv"` → `"uvx"` | `FAILED test_h8b_arm_d_the_five_figures_diff_reads` |
| **P**, A, D | delete the `"os"` line | 3 failed (arm P `KeyError`, Fixture A, Fixture D) |
| **Q** | add a new top-level `provenance` key (`"gpu": None`) | `FAILED test_h8b_arm_c_the_records_key_lists_status_and_exit` |
| **R** | reinstate `gpu` in § The two files | **PASSES** — as the design measured; see **Major 2** |
| **S** | unconditional redaction | `FAILED …leaves_hostname_untouched…` |
| **T** | `E-GIT-NO-COMMIT` raise → silent `commit = "unknown"` | `FAILED test_h6b_arm_t_…` |
| **T** | `E-GIT-NO-REPO` renamed to `E-GIT-NOPE` | `FAILED test_h6b_arm_t_…` |
| **U** | a shipped `environment` value moved (`manager`) | **passes** — arm U asserts `uv_lock_hash` only; arm P is what catches it. Arm U's own added docstring says exactly this and is accurate; the design's *"the arm that would catch an H6b change that was not additive"* is loose — arm U covers the **hashes**, which is the additive argument's actual subject. Not a finding |

Fixture C arm 2 and Fixture D each earn their place, by their own prescribed mutations:
`os.cpu_count() or 1` → **only** `…arm_c_hardware_carries_cpu_count_arm_2_none` fails (arm 1 passes,
as designed); swapping `os`/`hostname` insertion order → **only** `…arm_d_environment_key_order`
fails, arm P passes. Fixture G fails both ways it must: deleting `E-GIT-NO-REPO`'s row, and giving
`E-GIT-NO-COMMIT` a second row.

## Ruling P — rebuilt from scratch, and the sentence is TRUE

A hand-assembled repo **outside this one**: scaffold, generate, strip `__pycache__/` and `*.py[cod]`
from `.gitignore`, add a project-local `templates/local_probe.py`, commit, delete every `__pycache__`.

```
git status --porcelain BEFORE validate → (clean)
publishable validate → ✓ config valid, exit 0
git status --porcelain AFTER  validate → ?? src/cohort_pilot/__pycache__/
                                         ?? src/cohort_pilot/steps/__pycache__/
                                         ?? templates/__pycache__/
publishable run → error E-CODE-DIRTY, exit 1
```

**§ Templates' *"goes dirty at `validate`"* is true as written, Ruling P is right, and batch 4
confirmed something true.** The neighbouring clause Ruling F was expected to have falsified —
*"applied before git is asked anything, so no ignore file could have done that for it"* — reads
correctly against H6a's code: the claim is about the **unconditional fixed skip set**, not about the
exclude chain. Task 6's no-op is correct.

## § Errors — one row per code, and the table's own scope

Preamble's *"Two rows in this table are not raises"* still true: the section holds exactly two
`no exception` `Type` cells (`E-CODE-DIRTY`, `E-CODE-EMPTY`), programmatically counted. Both new rows
carry `ContractError` and sit beside the dirty-gate row, named by what it does. Each code has exactly
one raise site in `src/publishable/` and exactly one row (Fixture G's two independently-read ends,
re-verified by mutation). `E-GIT-NO-COMMIT`'s *"one reach path, `cli.command_run`"* verified:
`git_provenance` has one call site and its enclosing `def` is `command_run` (line 2009).
**The row-insertion collateral is clean**: `grep` over `docs/reference.md` for
`row above|rows above|row below|the two rows|further up|next row|previous row` returns ten hits, none
of them in or adjacent to § Errors core raises. The one substantive row defect is **Major 1**.

## The filings

| Entry | Checked |
|---|---|
| Six-unwritten-keys — **STRUCK, closed** | Correct. All three routed key groups are written; verified in a real record above. The reproduce recipe in the entry runs and prints the keys. The key-order note it preserves is genuinely untouched (`provenance`'s top-level order is byte-identical between main and HEAD) |
| Nine → **five** undocumented codes | **Count re-derived, and it is five.** Swept over the four documents named individually: `E-INPUT-CHANGED`, `E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED` → **0 hits each**; `E-PROJECT-EXISTS` → 1 hit, no row; `E-EXPERIMENT-EXISTS` → 2 hits, no row of its own (one is inside `E-EXPERIMENT-UNKNOWN`'s row). Control `grep -c E-PARAM-MISSING docs/reference.md` → 1. `E-STEP-EXISTS` correctly excluded (1 hit, no row) |
| **NEW OPEN** — `validate_config`'s bare `except ContractError` | **Reproduces**, by reading the two call sites side by side exactly as the entry says. Owner unassigned with a reason that is a fact. *And it is the entry that convicts Major 1* |
| Root-`.gitignore` — **DECLINED, re-owned unassigned** | Amended, not struck; heading now agrees with the body (`912c57d`); the underlying gap is real and untouched by this branch |
| § Templates `W-` seat | Amended with the measurement; matches what I reproduced above |
| `E-GIT-NO-REPO` prose-only entry — **PARTLY CLOSED** | Correct in scope; carries **Major 1**'s false clause |
| `diff` sixth row | Recorded as a stated non-gap; confirmed by behaviour — `diff` printed no `os`/`hardware` row |

## § Executability and the feasibility analysis — re-derived, not read

- **Four-row table byte-identical, ×7.** Programmatic extraction of every
  `| Figure | Count | Visible to \`validate\`? |` header plus five following lines: **eight** blocks,
  **seven identical**, the eighth being the pre-H8a *"Correction to the correction"* entry — exactly
  the divergence point the H6b entry claims. So H8a established it and **H6b is the sixth entry to
  repeat it**: the ordinal is right.
- **No fifth number.** Four rows; the prose quotes the dependency, not a figure.
- **The non-movement re-derived by me.** `grep -c "E-GIT-NO-REPO\|E-GIT-NO-COMMIT"
  src/publishable/validate.py` → **1**, and that one hit is `_check_data`'s catch, not an emit;
  control `grep -c "E-PARAM-MISSING" src/publishable/validate.py` → **3**. `provenance.environment` is
  written unconditionally with no declaration opting in or out, so no config gains or loses a
  dependency. Rows 2 and 3 name `io.reuse_from`'s plugin-side call and `summarize_step`'s construction,
  neither of which this branch touches (the whole `src/` diff is `cli.py`'s literal plus two
  docstrings). **§ Executability does not move.**
- **The entry's own load-bearing claim holds:** `git diff --name-only 6497284..HEAD -- src tests` is
  **empty**, so `9b7cc54` names the same executable tree.
- **The pre-existing wrapped-row fix is real and isolated.** My mechanical checker finds a
  `table-cols` defect on the *Class-ratio* row on `main` and **not** on HEAD; nothing else in that
  table moved (the branch's only other change to the file is the appended entry).

## Consistency passes

**Mechanical**, over a **named** file list (`README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md`,
`docs/feasibility-llm-growth-studies.md`), fences skipped, output **unfiltered**, run identically
against `main` and HEAD and the two problem sets diffed: **HEAD is strictly better than main** — main
10 problems, HEAD 9, the difference being the *Class-ratio* wrap. The nine survivors are all my own
slugger's double-hyphen false positives (`Secrets & credentials` → `secrets--credentials`) and are
present on `main` unchanged. **Checker proven able to fail**: appending `"x \t"` to `README.md`
produced both a `trailing-ws` and a `TAB` finding.

**Cross-document.** The one change to the shared worked example is Ruling O's, and I re-swept for it
across all six files with the output unfiltered: `grep -n -i "gpu\|A100"` returns **7 hits, all
correct** — five in `CLAUDE.md`'s own account of the ruling, `hostname: "hms-gpu-node-04"` (an
unrelated node name), and § The two files' new prose sentence. Control `grep -c "cohort-pilot"
docs/reference.md` → 22. **`cohort-pilot`'s intervals are not narrowed**: arm R green, and arm R is
precisely the raw-text pin over every worked-example literal in all three documents. Config
completeness, enum comments, declared-vs-derived and versions are untouched by this branch. The
*pinning* of the worked-example change is **Major 2**.

## The development record

**Not retro-edited, with one disclosed exception that is correct.** `e2f38cc` edits the design's
Decision 1 and § What this slice refuses **in place** — but it lands **before task 1's first commit**,
and the design carries an appended `## Correction, 2026-08-23, made before dispatch` that quotes the
superseded wording and says which sections it changed. Evidence preserved; no finding. Every later
record file has exactly one commit, except `progress.md` (appended per batch) and `task-b5-report.md`
(one in-place follow-up before its own review). `spec-defects.md` — the live list — strikes closed
entries rather than deleting them, as it must.

**`CLAUDE.md`** (read from disk, not from a stale context copy): the order line correctly reads
*"H9, then H3c-3's remaining 14 — the H4, H5, H6, H7 and H8 families are all complete, H6a and H6b
both having merged on 2026-08-23."* Its two greppable claims re-run and both hold: `grep -n
"hash(provenance\|hash(run_doc\|hash(record" src/publishable/*.py` → **nothing**; two readers of
`provenance.environment` and neither iterates it. The `E-GIT-NO-REPO` *"six reaches, three of them
deliberate swallows"* sentence is **true** and needs no edit (see Major 1). **No third asserted
ordinal found**: the *"sixth entry"* ordinal is derived and correct, and the *"last of H6's two"* is
a fact.

## What I verified by behaviour vs. by reading

**By behaviour** (a real command or a real mutation, output read): additivity both directions; the
run-directory file lists; the bundle activation and its three mutations; arm S's own mutation; arms
P/Q/T's mutations; Fixtures A/C-1/C-2/D/G's mutations; Ruling P's rebuild; `diff`/`report`/`study add`
over a `main`-produced record; the four gates; the suite before and after every mutation; the
mechanical checker on both branches with a can-fail control; every sweep with a can-fail control.

**By reading** (grep or file, no behaviour): Major 1's two catch sites and the contradiction between
the row and the new filing; Major 3's fourth home (found by sweep, established by reading the
docstring against task 3's and task 4's diffs); the single construction site of the three facts; the
§ Errors preamble count; the ledger's two dead SHAs (established by `git cat-file`, which is
behaviour, but their intended referents by reading commit subjects); Minor 2's structural claim being
true today.

## Routing summary

| # | Finding | Route |
|---|---|---|
| Major 1 | `E-GIT-NO-REPO`'s row says three sites catch by code; one catches by type, and the slice's own new filing says so — propagated to a second home in `spec-defects.md` | **Fix round now** — two deletions |
| Major 2 | Ruling O's worked-example edit is pinned by nothing; reinstating `gpu` leaves the suite green | **Fix round now** — one both-ends fixture |
| Major 3 | `test_study_add_redacts_hostname_when_present_on_a_synthesized_record`'s docstring — the fifth sentence gone false under this slice's own change, and the fourth home batch 4 swept for and did not find | **Fix round now** — delete the clause |
| Minor 1 | Two ledger commit SHAs (`2a9c05b`, `1b5f0cd`) exist nowhere in the repository | **Fix round now** — append a correction |
| Minor 2 | `secrets.py`'s structural safety claim is unpinned (true today) | **Filed, owner unassigned with the reason** |

---

# Fix round — 2026-08-23, run against `daa7df5`, this worktree to myself

Appended, not edited into what is above. Commits `5c2ed66` (Major 1), `0775af4` (Major 2), `94b4512`
(Major 3 + Minor 2). Gates after the last of them: `ruff check` **All checks passed!**,
`ruff format --check` **93 files unchanged**, `mypy` **Success, 52 source files**, full suite
**2973 passed, 1 skipped, 2 xfailed** in 209 s — **2971 + 2**, the two being this round's own new
tests (Major 2's both-ends pin, Minor 2's structural pin). No test was deleted or renamed and no
existing assertion moved.

## Major 1 — CLOSED, by deletion at both homes, plus a defect the finding did not name

The clause is deleted at both homes rather than rewritten. `docs/reference.md` § Errors core raises
now reads **two** sites catching **by code** (`validate._check_data`, `study._refuse_if_in_repo`) and
**two more catching by type, testing no code** (`validate.validate_config`'s bare
`except ContractError`, `cli._preloaded_experiment`'s `except Exception`). `spec-defects.md`'s
`E-GIT-NO-REPO` amendment carries the same two-and-two split. The row's cell count (2), its
`Type · code` cell and the § Errors preamble's *"Two rows in this table are not raises"* are untouched.

**The word *swallow* is deliberately NOT used for the by-type pair**, and that is what keeps
`CLAUDE.md`'s *"one raise and six reaches, three of them deliberate swallows"* true: the three are
`_check_data`, `validate_config` and `_refuse_if_in_repo`; `_preloaded_experiment` is excluded because
it converts the fault into `E-ENTRYPOINT-IMPORT` rather than swallowing it — which is what the row
says at its own source. Had the fix called the by-type pair *swallows*, the row would have shipped
four against `CLAUDE.md`'s three: a new inconsistency in the commit that closed one.

**A second defect in the same row, found by re-deriving rather than by reading the finding.** The row
named **`cli._load_experiment_for`** — a function that exists nowhere in `src/`. The real name is
`cli._preloaded_experiment` (the enclosing `def` of the `find_repo_root` call at `cli.py`'s entrypoint
preload, established by walking backwards from the call site). Corrected. `grep -rn
"_load_experiment_for" README.md docs/ CLAUDE.md src/ tests/` now returns **nothing** outside
`docs/superpowers/`, where this slice's plan and design carry it — **development record, deliberately
not retro-edited.** The review itself repeated the wrong name, which is the expected shape: it read
the name out of the row it was convicting.

**The six re-derived, and the 7-vs-6 collapse stated so the next reader does not re-grep it.**
`grep -rn "find_repo_root" src/publishable/` gives **seven** call sites: `cli.py` 206
(`_preloaded_experiment`), 2020 (`command_run`), 4153 (`_dispatch_generate`), `provenance.py` 171
(inside `git_provenance`), `validate.py` 511 (`validate_config`), 1221 (`_check_data`), `study.py` 54
(`_refuse_if_in_repo`). `grep -rn "git_provenance" src/publishable/` shows **one** call site,
`cli.py:2027`, whose enclosing `def` is `command_run` — the same function that already reaches
`find_repo_root` directly at 2020. Seven call sites, **six reaching functions.** The row's "six" is
right.

**The claim sweep, newline-insensitive (whitespace flattened before matching), over the four documents
named individually plus `CLAUDE.md`, the feasibility analysis, `src/**/*.py`, `tests/**/*.py` and
`docs/superpowers/**/*.md`.** Patterns `three sites catch`, `three that catch`,
`pass branch of a check of their own`, `by code.{0,40}pass branch`, `catch it \*\*by code\*\*`.
Can-fail control `E-GIT-NO-REPO` → **95 hits**. Result: exactly **two** live homes, both fixed; four
hits in the plan and the design, which are development record. The feasibility analysis — the file the
review's own Major-1 sweep omitted — carries three `E-GIT-NO-REPO` hits and **none** of the false
clause.

## Major 2 — CLOSED, pinned at both ends, and the (b) proof run

`tests/test_cli.py::test_h6b_fix_round_the_two_files_environment_block_is_what_run_writes`, beside
Fixture D. Document side: `_the_two_files_environment_block()` locates the **named** heading
`## The two files`, takes the first fenced `yaml` block under it, asserts there is **exactly one**
`environment:` line inside it before slicing, strips trailing `#` comments and parses. Code side: a
real `run` through `run_a_project`, `provenance.environment` read out of `run.yaml`. Neither end is
derived from the other. Three assertions: the key **lists** equal (order included), `hardware`'s key
lists equal, and `hardware`'s keys are the literal `["cpu_count"]` so neither extraction can go
vacuous and agree with itself.

**Not `_section_text`, and this is worth carrying.** That helper cuts the section at the first line
matching `^#{1,6} ` — and § The two files' fenced block **opens** with
`# <output_dir>/run_.../run.yaml`, so the slice it returns ends *above* the mapping. First attempt
failed with an empty body, which is why the one-`environment:`-line assertion is in there: a silent
wrong-mapping pin is the failure mode. Fences are skipped in every mechanical pass over these
documents for exactly this reason, and a doc-reading **test** inherits the same trap.

**Mutation (a), run:** reinstate `hardware: {gpu: "1x A100 80GB", cpu_count: 32}` →
`FAILED test_h6b_fix_round_the_two_files_environment_block_is_what_run_writes` (1 failed, 432
deselected). A second mutation, swapping the documented `os`/`hostname` lines → the same single
failure, so the order half is live too.

**Mutation (b), the one that gets skipped, run in full:** `gpu` reinstated **and** all three of the
new test's assertions neutered to self-comparisons → **full unfiltered suite 2973 passed, 1 skipped,
2 xfailed.** Zero failures. Nothing else in the suite catches Ruling O being reverted in the document.
Both counts are read from the unfiltered runs, and the tree was restored by editing back and verified
by **behaviour** (the pin passes again; `grep` shows `hardware: {cpu_count: 32}` and no `MUTATION`
marker survives).

**Does the pin belong to the worked example generally? Decided: no, and arm R is deliberately not
extended.** Arm R (`test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text`) is a raw-text golden
selected by `_H5A_ARM_D_LITERALS` over the worked example's **numbers** across three documents, and
its sole authorized editor is NONE — this round may not open it. More than that, it is the wrong
instrument: `gpu: "1x A100 80GB"` is not one of the shared statistics whose values must not be
narrowed, and the reason it must not come back is **that the code does not write it** — a fact no
single-document golden can see. A both-ends structural pin is the right shape, and it now also covers
Decision 9's order and any future documented-but-unwritten key.
**One observation, not a filing:** the same doc-vs-code gap remains for § The two files' *other*
`provenance` sub-blocks (`git`, `units`, `upstream`, `allocation`), which are pinned at the code end
by arms P and Q and against no document. Measuring that across every sub-block is more than this round
should take on; recorded here so the controller can decide whether it earns an entry.

## Major 3 — CLOSED, and a SIXTH home found and deleted in the same file

Arm S's docstring opened with three claims, all false at HEAD. **All three deleted**, not rewritten;
the docstring now says only what the test does. Arm S's **body is byte-identical** and the arm-S
editor note below it is untouched.

**The sixth home is this slice's own new Fixture E docstring** — *"Fixture Y exercises every redacted
field at once **on a record nothing in this build yet writes**"* — added by task 4 while the fifth home
was still live. Checked rather than reasoned about: a real record now carries `hostname`, `input_dir`,
`output_dir` **and** `repo_root`, so the clause is true only of that exact hand-built document, and
*"yet"* implies a future task 3 already delivered. **Deleted, not narrowed.** Adding a sixth home in
the commit that closes the fifth is what the next gate would have raised.

**Why two sweeps of that exact file missed a clause eight lines from one they found — measured, not
guessed.** At `6497284^`, `grep -n "provenance.environment.hostname" tests/test_study.py` returns
**exactly one hit: the surviving false line itself.** Home 3 (`_fixture_y_record`'s docstring) spelled
its claim with `ebf642a` and the `{manager, python_version, uv_lock, uv_lock_hash}` enumeration and
contains the dotted path **nowhere**. So the sweep did not fail to find it — **a plain grep pointed
straight at it, and the triage discarded the hit.** The shape: the hit list was checked against
Decision 13's table of three known homes rather than against the code, and a hit in a file whose homes
were already ticked off reads as one of them. Two homes in one file, eight lines apart, return two
hits and get counted as one. **A sweep's output must be attributed hit by hit, not reconciled with the
list of homes you expected** — the same fault as *a refusal that happens to fire must be attributed
before it is counted*, in the currency of a grep.

**Re-swept for the claim, newline-insensitively (whitespace flattened first), over `src/**/*.py`,
`tests/**/*.py`, the four documents named individually and `CLAUDE.md`** — patterns
`nothing in this build (yet )?writes`, `nothing (in|on) this build`,
`no(thing)? .{0,30}writes .{0,40}hostname`, `never carr(y|ies|ied) .{0,30}hostname`,
`hostname.{0,60}(not written|never written|nobody wrote|nobody writes)`, `it is H6`, `is H6's`,
`today's real records`, `yet writes`. Can-fail control `provenance\.environment\.hostname` → **4
hits**. Every survivor attributed individually: `study.py`'s is the **dated** *"was never written as of
`ebf642a`"*; `CLAUDE.md`'s two are its dated account of the ruling; `report.py`'s, `study.py`'s second
and `test_study.py`'s third are about `nondeterministic`, the `repeat_spread` shape and
`basis: "repeats"` — different fields, all true; `reference.md`'s two are `limits.min_units_per_cell`
and the `design` cell, both true. **No false survivor.**

## Minor 1 — CONFIRMED, and not touched

`git cat-file -t 2a9c05b` → *fatal: Not a valid object name*; same for `1b5f0cd`. The intended
referents, by commit subject: `6497284` *"H6b batch 4 follow-up: fixture Y's docstring gets the
deletion its brief asked for"* (batch 4's *"a follow-up deletion"*, `progress.md` line in the Batch 4
paragraph) and `912c57d` *"H6b follow-up: the root-`.gitignore` entry's heading now agrees with its own
amendment"* (batches 5/6's *"follow-up"*). **The ledger is the controller's and was not edited by this
round.**

## Minor 2 — CLOSED, split rather than pinned whole

`tests/test_secrets.py::test_h6b_fix_round_secrets_never_reaches_provenance` pins the **import** half
by parsing `secrets.py`'s own AST (an `import publishable.provenance` binds `publishable`, nothing new
on `secrets`, so a namespace check would not see it) plus a source scan below the module docstring for
the dynamic `import_module` form. **Mutation run:** adding `import publishable.provenance` to
`secrets.py` → `FAILED test_h6b_fix_round_secrets_never_reaches_provenance`, 10 passed. Restored by
editing back, verified by the test passing again.

The trailing clause *"or writes into the document it builds"* is **DELETED rather than pinned**: an
import check answers it only by proxy, which is this repo's signature failure, and no cheap structural
assertion answers it directly. The new test's docstring is deliberately no broader than its
assertions, and the module docstring now says which half is pinned and why the other was deleted. The
review's attached observation — that `hostname` enters the record through a literal with no credential
check, unlike the apparatus path — is **not** filed here either, on the review's own reasoning; it
stays recorded in the section above.

## Nothing regressed

Additivity, `hostname` redaction, Ruling P and § Executability are all untouched by this round: the
only `src/` change is `secrets.py`'s **docstring**, and the only document changes are the § Errors
row's prose and `spec-defects.md`'s amendment. `docs/reference.md` § Executability is in the
feasibility analysis, which this round did not open at all (`git diff --stat` names
`docs/reference.md`, `docs/superpowers/spec-defects.md`, `src/publishable/secrets.py`,
`tests/test_cli.py`, `tests/test_secrets.py`, `tests/test_study.py` and nothing else). **No guard-pin
arm was opened**: arm S gained a docstring change only, its body byte-identical, and arms P, Q, R, T,
U were not touched. Whitespace, tabs and invisible unicode checked at zero on every edited file; the
edited § Errors row still has two cells and no newline inside them.

## Claims I grepped rather than asserted

Every claim this section makes about other tests, rows or code was greppable and was grepped:
`_load_experiment_for`'s absence from `src/` (and its presence in the plan and design);
`find_repo_root`'s seven call sites and `git_provenance`'s one; the two live homes of the by-code
clause with a 95-hit control; the four surviving hits of the hostname claim, attributed one by one,
with a 4-hit control; `provenance.environment.hostname`'s single pre-fix occurrence in
`tests/test_study.py` at `6497284^`; `_section_text`'s cut rule read out of its own body after the
extraction failed. **Not a count of zero disagreements: two disagreements with the review are named
above** — the wrong function name in the row it convicted, and the sixth home it did not reach.
