# H6a — the two hash definitions — whole-branch review

Branch `h6a-hash-definitions`, 42 commits ahead of `main` (`main` at `6aec85a`, HEAD at `c743f31`).
Reviewed 2026-08-23. Everything below is marked **by behaviour** (a command, a probe, a mutation and
its output) or **by reading**.

## Verdict: **HOLD** — three Majors and two Minors, all closable in one same-day fix round

**Major 1 needs code** (one test; the probe body already exists in this review). **Majors 2 and 3 are
single-sentence document edits** in `reference.md`, one of them repeated in `CLAUDE.md`.

Behaviour is clean. The value change is right end to end, every moved digest is enumerated and
pinned, both new refusals are pinned in both directions with distinct failures, and all seven
guard-pin arms were proven able to fail. **What holds the merge is one missing pin and two false
normative sentences, all three on the slice's own central claim (Ruling F).** None of the three is a
behaviour defect; all three are the kind of thing that ships and then gets silently weakened.

---

## The independent measurements

### The value change, main vs HEAD, key by key — **by behaviour**

A project built outside this repo (`/tmp/h6agate/A`), committed, holding `src/pkg/step.py` = `a = 1\n`
plus three untracked files matching the scaffold's own `.gitignore` (`src/pkg/.env`,
`src/.venv/lib/site.py`, `src/pkg/loose.pyd`). The **same tree** was run twice, first through a
`main` worktree's console script, then through this branch's:

```
main : run.yaml → /tmp/h6agate/A/results/run_2026-08-23T04-13-31Z_09a843b/run.yaml
HEAD : run.yaml → /tmp/h6agate/A/results/run_2026-08-23T04-13-40Z_f6a935c/run.yaml
```

`diff` of the two `run.yaml`s with the run-directory string normalized away:

```
63c63
< code_hash: sha256:09a843b15e23fe355b389aec9ae6a1566f4a6211bf249781884f2e4c82f842cc
> code_hash: sha256:f6a935cfc29196b2a5f5a7f873096c4ab3ee077ff3152afedafeb34fb919078a
102,103c102,103   (started_at / wall_seconds)
111c111           (started_at)
```

`diff -rq` over the whole run directories: only `run.yaml` and `executions.jsonl`, and the latter
only in `started_at`/`wall_seconds`. `parameters_hash`, `input_manifest_hash`, `units_hash`,
`allocation_hash`, `uv_lock_hash`, `design_digest` and the derived seed (`seed54`, identical in both
ledgers) are unmoved. `results/latest` points at the new directory.

**Every digest that moves is one the slice enumerated** — `code_hash`, `run_id`, the directory name,
the `latest` target — and the two digest literals are exactly the ones batch 3 and `CLAUDE.md` claim
(`09a843b1…` → `f6a935cf…`), reproduced here independently.

### The four-case table, each case run through the console script — **by behaviour**

| Case built | Result |
|---|---|
| untracked files excluded by the repo's own committed `.gitignore` | dropped — `f6a935c` |
| the same rule as a **global** `core.excludesFile` only | **hashed** — `bbb597a` (Ruling F holds) |
| the same rule moved into the committed `.gitignore` | dropped — back to `f6a935c` |
| the same rule in a **repo-local** `.git/config` `core.excludesFile` | **hashed** — `bbb597a` (neutralized, correct) |
| the same rule in `.git/info/exclude` | dropped — `f6a935c` (the disclosed residue, true) |
| tracked `src/pkg/__pycache__/keep.py` **and** tracked `src/pkg/step.pyc`, `.gitignore` omitting both | both skipped — `f6a935c` (unconditional skip, true) |
| `src/pkg/` empty, no `templates/` | `E-CODE-EMPTY`, exit 1, **no run directory created** |
| every file under `src/` excluded by a committed `src/` rule, dirty gate clean | `E-CODE-EMPTY`, exit 1 |
| a committed submodule at `src/vendor` | `E-CODE-FILE-LIST`, exit 1, carrying git's own `fatal: Pathspec 'src/vendor/m.py' is in submodule 'src/vendor'` — a clean diagnostic, not a traceback |

`W-PARAM-UNSET` through the console script: warning, path `parameters`, **exit 0**.

### The guard pin — **by behaviour**

Every arm extracted at its capture commit and diffed against HEAD:

* **Arms A, C, D, N — no authorized editor.** No assertion, digest literal or test name moved. Arms A
  and D took task 3's `, None` plus docstring prose (batch 2's disclosed Major); arm C took docstring
  and comment prose only in batch 1's own fix round; **arm N is byte-identical.**
* **Arm E** moved by exactly the clause Ruling J authorized (`cb5003d`: `; \`code_hash\` still has
  exactly one in \`src/\`` deleted, nothing else) — plus task 3's `, None` and docstring, the same
  disclosed batch-2 edit.
* **Arm B** moved to the four literals its own docstring specified in advance, plus the disclosed
  fifth edit. Batch 2's self-authorization did **not** recur in batches 3–6.

Each arm proven able to fail, by mutation, with the file list read:

| Mutation | Fails |
|---|---|
| `hashes.py` fold separator `b"\0"` → `b"\1"` | arms A, B, C, D + 6 fixtures (10 failures) |
| `code_hash_of` returns a different digest for an empty list | **arm E alone** |
| `validate.py` `"but the template reports"` → `"but the template says"` | **arm F alone** |
| `diff.py` `_figure("code_hash")` → a constant | **arm N and its control** |

### Both new refusals, both directions — **by behaviour**

| Mutation | Failures |
|---|---|
| `if not hashed:` → `if False:` (guard deleted) | 2: fixtures G and H — and a run completes with `run_…_e3b0c44` |
| `if not hashed:` → `if True:` (always refuses) | 264, including every arm |
| `if result.returncode not in (0, 1):` → `if False:` | 1: Fixture I (the submodule) |
| `not in (0, 1)` → `not in (0,)` (raises on the ordinary answer) | 4, none of them Fixture I |
| `if unset:` → `if False:` | 1: Fixture K |
| `unset = list(parameter_spec)`, unconditional | 55 |
| `check-ignore -z` → `check-ignore` | 6, including Fixtures C, D, J |

Different faults produce different failures in every pair. Reverted by editing back; `git status
--porcelain` empty; full suite re-run green afterwards.

### Gates and delta

`ruff check` clean · `ruff format --check` 93 files formatted · `mypy` clean ·
**2955 passed, 1 skipped, 2 xfailed** (204 s). `main`'s own suite, run in a synced worktree:
**2931 passed, 1 skipped, 2 xfailed** → **+24**, which is exactly the ledger's per-batch arithmetic
(+8, +6, +6, +2, +2, +0).

### Records, documents, filings

* **No retro-edit.** `git diff main...HEAD` over `docs/superpowers/` and `.superpowers/` has **three
  deleted lines in total**, all three in `spec-defects.md` (the sole permitted exception) and all
  three replaced by the same heading struck with `~~…~~` and a dated CLOSED note. The design's and
  the spine's corrections are appended.
* **Mechanical pass** over the four documents + `CLAUDE.md` + the feasibility analysis: every
  relative link and `#anchor` resolves (0 problems), no duplicate heading slugs, no trailing
  whitespace/tab/invisible unicode, every table row matches its header once escaped `\|` is
  discounted. **Each checker was proven able to fail** — a bogus anchor and a bogus file link were
  injected into a copy and both were reported; a 2-vs-3-column table was fed to the table checker and
  detected. The file list was filtered, never the output.
* **Cross-document pass**: the `cohort-pilot` intervals and every hash prefix are untouched
  (occurrence counts on `main` and HEAD compared for all sixteen literals). The removed normalization
  sentence has no residue anywhere.
* **§ Errors core raises' own scope sentence** now names the two `Collector` refusals and why they sit
  in that table — batch 4's finding is properly closed at the table, not by citing the design.
* **`W-STUDY-CODE-HASH-MISMATCH`** is untouched but for one added link; `report.py` has a zero-line
  diff; the row still names three causes and no build boundary.
* **Feasibility analysis**: the four-row table is **byte-identical** to the preceding entry
  (`md5 20e8fc95513a15c376345ab966604e11` for both extractions; the comparison was proven able to fail
  by perturbing one cell), no fifth number, and § Executability's non-movement re-derived here — the
  new warning is a `c.warn` at exit 0, and neither new error is reachable from `validate`
  (`grep -c` over `validate.py` → 0, control `E-PARAM-MISSING` → 3).
* **Filings**: three entries struck (not deleted), two OPEN entries filed with **unassigned owners
  and reasons**, and the core-schema half of `W-PARAM-UNSET` — deferred twice before — **landed**. I
  reproduced it: deleting `limits.min_reported_n` from a real config prints `✓ config valid`, exit 0.
  The `835 ms` in that filing is a re-measurement of the plan's `875 ms`, stated as such.
* **`CLAUDE.md`'s entry**: every count checked. Ten unmoved figures enumerated (ten, counted), one
  emit site each for both new codes (grepped: `cli.py:2380`, `provenance.py:81`), seven arms, the two
  digest literals reproduced above. The order line (`H6b, H9, then H3c-3's remaining 14`) is right.
  The spine correction's own numbers check out: `grep -c '^## Task '` → **13**, and the purity grep
  over the four documents named individually → **one** hit, in `reference.md`.

---

## Findings

### Major 1 — Ruling F, the slice's central claim, is pinned by nothing

**`grep -rn "GIT_CONFIG_GLOBAL\|excludesFile\|excludesfile" tests/` → 0 hits.** No test in the suite
constructs a global or system git config, so no mutation to the neutralization can fail. This machine
has no global excludes either (`git config --global --get core.excludesFile` → rc 1), which is why the
probes in batches 1 and 3 had to build a throwaway repo to see it at all.

Confirmed by mutation — both halves of the neutralization removed:

```python
env = dict(os.environ)                                   # was: GIT_CONFIG_GLOBAL/SYSTEM=/dev/null
["git", "check-ignore", "-z", "--stdin"]                 # was: git -c core.excludesFile= …
```

```
2955 passed, 1 skipped, 2 xfailed in 206.31s
```

**Byte-identical to the unmutated run.** The one claim this slice was chartered to make — *only rules
that travel with the tree may define the tree's identity* — is a probe and a sentence, and this repo's
own § Misreadings says that is exactly how five correct fixes shipped unpinned in three slices.

**Route: fix round now.** The test already exists as a probe body: build a repo whose only exclude of
`src/pkg/notes.log` is a global `core.excludesFile`, assert the digest is the **unnarrowed** one
(`bbb597a…` on my tree), then move the identical rule into the committed `.gitignore` and assert it
returns to the narrowed one. Both branches differ, and the mutation above must fail it.

### Major 2 — `reference.md`'s `E-CODE-DIRTY` row claims a convergence the code does not have

Line 1141: *"since [the hash honours the same exclude rules](#how-the-three-are-computed) **the gate
and the hash now consider the same set of files, which they did not before**."*

**False exactly where Ruling F does its work.** The gate is `git status --porcelain -- src templates`
(`provenance.py:110`), which honours the machine's whole exclude chain; the hash asks `check-ignore`
with global and system config neutralized. Measured, with an untracked `src/pkg/notes.log` and a
global exclude of `notes.log` — **injected through the environment, because this machine has no global
excludes of its own** (`git config --global --get core.excludesFile` → rc 1), which is what a user
whose machine does have one sees:

```
$ export GIT_CONFIG_GLOBAL=/tmp/h6agate/gitconfig     # [core] excludesFile = …/globalexclude
$ git status --porcelain -- src templates        → (nothing: the GATE treats it as ignored)
$ publishable run …                              → code_hash bbb597a… (the HASH read the file)
```

Reproducing this without the env var gives "not excluded" from both sides and shows nothing; the
divergence is only visible on a machine that has a global exclude, which is the population the row's
claim is about.

Two different sets of files, in one run, on the branch whose row says otherwise. **This is the
cross-batch interaction this gate exists to find**: batch 3 wired the neutralization, batch 4 wrote a
convergence claim over it, and no per-batch review saw both.

**Route: fix round now.** The true sentence is narrower — the gate and the hash converged on the
repo's own *committed* rules, and diverge on anything that does not travel with the tree.

### Major 3 — "One residue, and it is the only machine-dependent input left" is not the only one

§ How the three are computed says the excluded row is decided by *"one of the repo's own **committed**
rules"* plus `.git/info/exclude`, *"the only machine-dependent input left"*. `check-ignore` reads the
**working tree**, so an **uncommitted** `.gitignore` decides too — and the dirty gate cannot catch it,
because the gate is scoped to `src/**` and `templates/**` while the deciding file sits at the repo
root. Measured:

```
$ git status --porcelain            →  M .gitignore
$ git status --porcelain -- src templates   → (nothing — the gate is clean)
$ publishable run …                 →  run_…_f6a935c   (notes.log dropped by an uncommitted rule)
```

So a run at a given commit publishes an identity claim **no clone of that commit can reproduce** —
the precise failure § The value change argues against. The boundary that makes this narrow and
actionable: a `.gitignore` *inside* either hashed tree is caught by the dirty gate — **verified by
behaviour**, an untracked `src/.gitignore` gives `?? src/.gitignore` and `E-CODE-DIRTY` at exit 1 — so
the repo root is the only escape. `CLAUDE.md`'s H6a entry carries the same claim
(*"only rules that travel with the tree decide"*) and needs the same narrowing.

**Route: fix round now** — narrow both sentences (working-tree `.gitignore`s, committed or not), and
either file the residue with an owner or state it beside `.git/info/exclude`.

### Minor 1 — a co-occurrence claim with no fixture

`_check_versions`' new docstring: *"The duplication with `W-PARAM-UNSET` on a version-mismatched
config is deliberate, not an oversight — **both warnings render in one `Collector` output**."* No test
asserts it: `grep -rn "W-PARAM-UNSET" tests/` → five hits, all in Fixture K and its control and one
docstring. Guard-pin arm F's own config (version `0.9.0`, one defaulted parameter deleted) produces
**both** warnings and the test filters to `W-TEMPLATE-VERSION`. The claim is true — verified through
the console script, both warnings, `2 problems (0 errors, 2 warnings)`, exit 0 — and it is a seam
named in prose and instantiated by no fixture. **Route: fix round (one assertion) or file.**

### Minor 2 — `W-PARAM-UNSET`'s message does not agree with its own path

Rendered side by side:

```
warning W-PARAM-UNSET      parameters
        carries a default and is left unset here; …: analysis.confidence
warning W-TEMPLATE-VERSION template_version
        is 0.9.0 but the template reports 1.0.0; unset here and …: analysis.confidence
```

Every diagnostic in this project reads as `<path> <message>`. `template_version is 0.9.0 …` reads;
*`parameters` carries a default and is left unset here* does not — the block does not carry the
default, the enumerated paths do. The § Warnings row claims the message is *"on `W-TEMPLATE-VERSION`'s
own enumerating shape"*, which holds for the enumeration and not for the subject. **Route: fix round
(reword, e.g. *"holds a path that carries a default and is left unset here: …"*) or file.** Arm F does
not pin this message; Fixture K asserts substrings only, so a reword is cheap.

---

## What was checked and is NOT a finding

* **Repo-local `core.excludesFile`** — neutralized correctly by the command-line `-c`, measured.
* **`.git/info/exclude`** — the disclosed residue, and the disclosure is true, measured.
* **The `if not candidates: return set()` early return** — the comment calls it an optimization and
  not a correctness fix; `printf '' | git check-ignore -z --stdin` → **rc 1**, so the claim holds and
  the branch is behaviour-equivalent.
* **`E-CODE-EMPTY` leaves no run directory** — measured, the results directory stays empty.
* **`E-CODE-FILE-LIST` reaching a user** — a clean `error E-CODE-FILE-LIST …` on stderr at exit 1
  through `main`'s `PublishableError` handler, carrying git's own stderr as the row promises.
* **`draft`** — not built, so `run` is the only site that computes a `code_hash`; `diff`, `report`,
  `study`, `lineage` and `freeze` all read a recorded string (re-grepped).
* **`hashes.code_hash`'s zero production callers** — filed and closed in the same `spec-defects.md`
  entry, and the measurement is right: its body **is** the composition `command_run` calls.
* **`CLAUDE.md`'s *"merged on 2026-08-22"***. The convention was checked rather than assumed: H5b's
  and H8c's entries date the records commit that wrote them, and H6a's (`f70499f`) is dated 08-22, so
  the convention holds. If the merge lands 2026-08-23 the date reads one day stale — a bump, not a
  finding.
* **`tests/test_hashes.py:131`'s un-neutralized `check-ignore`** — asserts rc 1 for a **tracked**
  file, which `check-ignore` answers from the index, so a machine's global `__pycache__/` rule cannot
  flip it.

## Every moved digest, enumerated and pinned?

**Yes.** `code_hash` is the only moved figure, measured key by key across `main` and HEAD on one tree;
`run_id`, the run directory's name and the `latest` target follow it and are covered by arms A/B/C;
`provenance.upstream[].code_hash` is copied rather than computed and is pinned by Fixture M; the
bundled copy is a verbatim copy of a pinned record. The other ten figures are enumerated in
`reference.md` and unmoved in the measured diff.

---

# Fix round, 2026-08-23 — all three Majors and both Minors closed

Everything below is the fix round's own record; nothing above it was edited. Each finding is marked
**by behaviour** (a probe, a mutation and the failures it produced, a full suite run) or **by reading**.

**Suite: 2955 → 2962 passed, 1 skipped, 2 xfailed** — **+7**, which is exactly the seven tests this
round adds (4 in `tests/test_hashes.py`, 1 in `tests/test_acceptance.py`, 2 in `tests/test_validate.py`).
Predicted before the run and read from the unfiltered output. `ruff check` clean, `ruff format --check`
93 files already formatted, `mypy` clean. **Zero deletions in `tests/`** (`git diff --numstat`), and both test
files that carry arms are **appended to at end of file** — below arm F in `tests/test_validate.py`,
below arms D and E in `tests/test_hashes.py` — so no insertion lands inside an arm body either. Arms A,
C, D, N (no authorized editor) and B, E, F are byte-identical.

## Major 1 — Ruling F is pinned — **CLOSED**

**The claim that it was unpinned, re-verified rather than carried:** `git grep -c
"GIT_CONFIG_GLOBAL\|excludesFile\|excludesfile" d920470 -- tests/` → **no output, rc 0** (zero files).

Building the pin needed a measurement the review did not have: **which half of the neutralization
closes which route.** Measured on 2026-08-23 in a throwaway repo, `src/pkg/notes.log` untracked:

| Route the exclude rule takes | killed by `-c core.excludesFile=` | killed by `GIT_CONFIG_GLOBAL/SYSTEM=/dev/null` |
|---|---|---|
| global config `[core] excludesFile` | yes | yes |
| the XDG default `~/.config/git/ignore`, named by no config entry | yes | **no** |
| repo-local `.git/config` `core.excludesFile` | yes | **no** |
| global `[status] showUntrackedFiles = no` (the dirty gate only) | **no** | yes |

So **no exclude route pins the environment half** — the command-line override closes every one of them
on its own — and a test built only from the review's proposed probe would have left half the
neutralization exactly as unpinned as before. The environment half is pinned on the **gate**, where a
global `status.showUntrackedFiles` reaches and no `-c` about excludes does, which is the reason the two
halves are now **one shared pair of constants** (`_NEUTRALIZED_CONFIG_ARGS`, `_NEUTRALIZED_CONFIG_ENV`)
used by both call sites rather than written twice.

Four arms in `tests/test_hashes.py`, each with a **positive control** asserting the fixture's machine
rule is one git really reads, and each with a third arm proving the identical pattern **committed** to
`.gitignore` still narrows the hash (so none of them passes if excludes were merely switched off):

* `test_h6a_ruling_f_a_global_excludesfile_cannot_narrow_the_hash`
* `test_h6a_ruling_f_a_repo_local_excludesfile_cannot_narrow_the_hash`
* `test_h6a_ruling_l_a_global_excludesfile_cannot_blind_the_dirty_gate`
* `test_h6a_ruling_l_a_global_show_untracked_files_no_cannot_blind_the_gate`

plus one end-to-end arm through the real command,
`tests/test_acceptance.py::test_run_refuses_an_untracked_file_a_global_exclude_hides`, whose two arms
use **the same file and the same pattern** and differ only in where the rule lives — committed, the run
completes at `EXIT_OK`; moved into a machine's global `core.excludesFile`, the same tree is refused with
`E-CODE-DIRTY`. That is what attributes the refusal to the rule rather than to the file.

**Each half proven able to fail, separately, full unfiltered suite each time:**

| Mutation (exact text) | Result |
|---|---|
| `_NEUTRALIZED_CONFIG_ARGS = ()` | **1 failed**, 2961 passed — `…ruling_f_a_repo_local_excludesfile_cannot_narrow_the_hash` |
| `_NEUTRALIZED_CONFIG_ENV: dict[str, str] = {}` | **1 failed**, 2961 passed — `…ruling_l_a_global_show_untracked_files_no_cannot_blind_the_gate` |
| the gate's `neutralized=True` deleted | **3 of 5 failures** in the combined run below — both Ruling L arms **and** the end-to-end acceptance arm |

Reverted by copying the pre-mutation file back and verified by **re-running** the suite, not by `git
status`.

## Major 2 — the convergence claim — **CLOSED, by CONTROLLER RULING L plus a narrower sentence**

`provenance._git` gained a `neutralized` keyword and the dirty gate passes it, so `git status
--porcelain -- src templates` is asked with the same configuration out of the way `check-ignore` already
used. `ls-files` and `rev-parse` do **not** pass it: they ask about the index and the commit graph, which
no exclude rule reaches.

**The row's sentence still had to change, and deleting "same set of files" is not deleting the
sentence.** Ruling L makes the *rules* converge and does not make the *file sets* converge, because the
hash applies the fixed skip set unconditionally and the gate does not. Measured by behaviour: a
**tracked, modified** `src/pkg/step.pyc` gives `code_dirty True` while `hashed_files` returns
`['src/pkg/step.py']` — the gate fires over a file no hash reads. The `E-CODE-DIRTY` row now says the two
honour **one exclude chain**, names the global-`core.excludesFile` case it now catches, and states the
skip-set divergence with that example. Had the sentence been left as-is under Ruling L it would have
closed a false claim with a second false claim.

**The cost is disclosed with the others**, in § How the three are computed beside the `uv.lock`
disclosure: *"The dirty gate moved with the definition, and that is a second behaviour change to `run`
(2026-08-23)"*, naming all four routes that now fail `E-CODE-DIRTY` where they used to run.

**One consequence found while writing that disclosure, disclosed and filed rather than fixed:**
`safe.directory` is read from global and system configuration only, so on a repository git considers
dubiously owned the neutralized gate gets no answer and `_git`'s `check=False`/`strip()` convention reads
it as **not dirty**. Measured with `GIT_TEST_ASSUME_DIFFERENT_OWNER=1` and a global `safe.directory`
entry: `code_dirty False`, and `hashed_files` then raises `E-CODE-FILE-LIST` from the same neutralization
two phases later, so no record is published. Filed **unassigned with the reason** — closing it means
deciding what a run does when git cannot answer the gate at all, which is `_git`'s convention and a
controller ruling, not fix-round work.

## Major 3 — "the only machine-dependent input left" — **CLOSED (deleted, not narrowed), residue filed**

§ How the three are computed now states the **mechanism** rather than an enumeration that goes stale:
`check-ignore` answers from the **working tree**, so whatever exclude rule the tree holds when the
command runs decides — a `.gitignore` edited and not committed, or never committed at all — plus
`.git/info/exclude`. The paragraph's old title (*"One residue, and it is the only machine-dependent input
left"*) is gone.

Re-measured here rather than carried, on 2026-08-23: `git status --porcelain` → ` M .gitignore`, `git
status --porcelain -- src templates` → nothing, `code_dirty` → `False`, `hashed_files` → `['src/pkg/step.py']`
with `notes.log` dropped by the uncommitted rule. The boundary was measured too: an untracked
`src/.gitignore` gives `?? src/.gitignore` and `code_dirty True`, so the repo **root** is the only escape.

**Filed: OPEN — an uncommitted root `.gitignore` decides what `code_hash` covers, and the dirty gate
cannot see it — Owner: H6b**, with the controller's reason recorded: closing it means the gate covering a
file **outside** the two hashed trees, a scope change deserving its own decision, and H6b already holds
the `validate` tree-state ruling, which is the same question at the other surface. The entry states
explicitly that **Ruling L does not close it** — the deciding file is outside the gate's *pathspec*, not
outside its exclude chain.

**The sweep, newline-insensitive, and proven able to fail.** Four patterns (`only.{0,40}rules that travel
with the tree`, `only machine-dependent input`, `the gate and the hash now consider the same set`, `one
residue`) run over whitespace-collapsed text across `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md`, `docs/superpowers/spec-defects.md` and
every `src/publishable/*.py` — the **file list** was filtered, never the output. Three hits, all fixed:
`CLAUDE.md`'s H6a entry (both the *"only rules that travel with the tree decide"* claim **and** its now
reversed *"the dirty gate's machine-dependence was rejected as a precedent"*), and `spec-defects.md`'s
Ruling F filing, which is a live entry and so carries an **appended AMENDED note** rather than a rewrite.
The sweep was proven able to fail by re-running it for `travel with the tree`, a string known present:
`docs/reference.md` 1, `CLAUDE.md` 2, `src/publishable/provenance.py` 1.

## Minor 1 — the co-occurrence seam — **CLOSED, with a fixture**

`tests/test_validate.py::test_h6a_both_warnings_render_in_one_collector_output` — arm F's own config,
asserting **both codes in emission order**, both paths, the warning **count** (two, so a third
diagnostic is visible rather than absorbed) and exit 0. Written as a **new test below arm F**, not as a
widening of arm F, which has a single authorized editor and it is not this round.

## Minor 2 — `W-PARAM-UNSET`'s message — **CLOSED and pinned whole**

`parameters carries a default and is left unset here` → `parameters holds paths that carry a default and
are left unset here; a step reading one as cfg.parameters.<path> raises E-STEP-PARAM-UNKNOWN: …`. Pinned
as a **whole string** in `test_h6a_w_param_unset_message_agrees_with_the_path_it_carries`, because a
reword is exactly what Fixture K's substring assertions could not see. The § Warnings row was re-read:
its claim is *"one diagnostic at path `parameters` naming every such path, on `W-TEMPLATE-VERSION`'s own
enumerating shape"* — about the enumeration, which is unchanged — so it needed no edit. Arm F's docstring
was re-read too and asserts nothing about this message.

**Combined mutation run** (the two `validate` fixes plus the gate's `neutralized=True`), full unfiltered
suite, **5 failed, 2957 passed** — each attributable and disjoint:

| Mutation | Failed |
|---|---|
| message reverted to `"carries a default and is left unset here; a step "` | `…w_param_unset_message_agrees_with_the_path_it_carries` |
| `W-PARAM-UNSET` suppressed when `template_version` mismatches (the de-duplication `_check_versions`' docstring denies) | `…both_warnings_render_in_one_collector_output` — and **not** arm F |
| the gate's `neutralized=True` deleted | both Ruling L arms + the end-to-end acceptance arm |

## What was grepped, and the disagreements found

Not a count of zero.

* **`git grep … d920470 -- tests/`** for the neutralization strings — zero files, confirming Major 1's
  premise rather than repeating it.
* **The review's *"this machine has no global excludes either (`git config --global --get
  core.excludesFile` → rc 1)"*** — **incomplete**. `ls -l ~/.config/git/ignore` → the file exists
  (31 bytes, `**/.claude/settings.local.json`), and that default path is **not** reached by
  `GIT_CONFIG_GLOBAL=/dev/null`. It changes none of the review's conclusions (no fixture holds a
  `.claude/` path under the two hashed trees, and the suite delta is exactly the +7 this round adds), but
  the check named in the review does not establish what it was used for.
* **`grep -rn "W-PARAM-UNSET" tests/ src/ docs/reference.md`** before rewording — five test hits, all in
  Fixture K, its control, and one docstring, exactly as the review reported; plus the § Warnings row and
  the two `validate.py` sites.
* **`grep -n "dirty gate\|status --porcelain"` over the four documents** — one further passage worth
  reading, § Templates' *"A hand-assembled repo whose `.gitignore` omits that line goes dirty at
  `validate` and fails `run`"*. It is **unaffected** by Ruling L (the fixed skip set decides those files,
  not git), and its *"goes dirty at `validate`"* clause is a pre-existing overstatement of what `validate`
  checks (Decision 15's territory), left alone deliberately.
* **Mechanical pass** over the four documents, `CLAUDE.md`, the feasibility analysis and
  `spec-defects.md`: links, `#anchor`s, duplicate heading slugs, table column counts, trailing
  whitespace/tabs. Clean except **one pre-existing defect not this branch's**: a table row in
  `docs/feasibility-llm-growth-studies.md` § What core refuses is split across two source lines and
  carries a duplicated `([§ Executability on this build](#executability-on-this-build))` parenthetical —
  introduced by `8521f69` (H7d Part A's fix round), already on `main`, so it is reported and not touched
  here. The checker was proven able to fail: its first version's slugger mishandled ` — ` in headings and
  reported 26 false anchors, which is how its rule was corrected.
* **§ Executability's four-row table** — `docs/feasibility-llm-growth-studies.md` is not in this round's
  `git diff --name-only`, so it is byte-identical and carries no fifth number.
* **`.superpowers/sdd/.gitignore`** — checked before committing, content intact, not clobbered.

* **`grep -rn "git_provenance\|code_dirty" src/`** — the scope of Ruling L's behaviour change, checked
  rather than assumed. Both names reach exactly one command: `git_provenance` is called at
  `cli.py:2024` and nowhere else in `src/` (`validate`, `freeze`, `diff`, `report`, `study` and
  `lineage` do not call it), and `command_run` is the only definition-and-call pair. `GitInfo.code_dirty`
  **is** written into `run.yaml` (`provenance.git.code_dirty`, `cli.py:3807`), but the phase-3 gate
  refuses unconditionally when it is true, so a `run.yaml` `run` writes always records `false` and
  **Ruling L cannot move a recorded figure** — it can only turn a run into a refusal. The disclosure's
  scope word, `run`, is therefore right, and the ten-unmoved-figures claim is untouched.
* **A global setting that decides *how* a file is compared, not which files are considered** — found by
  asking what else the neutralization discards, not by grep, and it **reproduces**: with the repo's own
  `core.filemode` unset and a global `core.fileMode = false`, a `chmod +x` on a tracked file is clean
  under the machine's config and **dirty** under the neutralized question. `core.autocrlf` is the same
  class and Git for Windows writes it to the *system* config. This is a false-dirty on a tree whose
  content nobody touched — a worse class than the four routes the disclosure already named, all of which
  are "you relied on a machine rule to hide a file" — so § How the three are computed now names it, with
  the mitigating fact that `git init` writes `core.filemode` into the repo's own `.git/config`, which
  outranks the global one.

## Two concerns carried to the merge

**1. A surgical alternative to Ruling L's "the same way" exists, and it is a controller's call, not this
round's.** Ruling L said to neutralize the gate *the same way* the hash is neutralized, and that is what
shipped. But the ruling's own ground — a rule that does not travel with the tree may not decide — is
about settings that choose **which files the gate considers**, and exactly two do:
`-c core.excludesFile=` and `-c status.showUntrackedFiles=normal`, with the environment variables
dropped **for the gate only**. Measured on 2026-08-23: that pair alone defeats a global config carrying
both `showUntrackedFiles = no` and a `core.excludesFile`, printing both untracked files. It would leave
content and mode comparison alone (retiring the `core.fileMode`/`core.autocrlf` class above) and leave
`safe.directory` alone (retiring the fail-open filed under Major 2). What it costs: the environment half
of the shared constants would no longer be pinned by the gate arm — the pin would move onto
`-c status.showUntrackedFiles=normal` — and the hash and the gate would stop sharing one pair of
constants, which is the property that keeps them from drifting. **Not implemented here**: swapping it in
is a change to what Ruling L decided.

**2.** `CLAUDE.md`'s H6a entry still opens *"merged on 2026-08-22"*, which the review flagged as a bump rather
than a finding. This round did not change it: the date names the records commit by the convention H5b and
H8c set, and re-dating it would ripple through the entry's other dated claims. If the merge lands today
it reads one day stale.
