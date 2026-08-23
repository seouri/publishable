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
