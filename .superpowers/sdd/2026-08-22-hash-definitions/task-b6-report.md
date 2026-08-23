# Batch 6 — tasks 12 and 13 — the records

**Both PASS on their own account; two disagreements with the brief found, one of which changes what a
tracked record says.** Commits `f70499f` (task 12) and `fe8ea47` (task 13). Gates at `fe8ea47`:
`ruff check` clean, `ruff format --check` 93 files already formatted, `mypy` clean over 52 source
files, `uv run pytest` **2955 passed, 1 skipped, 2 xfailed** — unmoved, as a records batch should be.
Run directly in the foreground, not backgrounded, after clearing `pytest-of-joon` and every
`__pycache__`.

---

## Disagreements with the brief, reported as a list rather than as a count

**1. The brief's step 4 says H6a "documented its own two new codes and took NONE of the nine". It took
one.** `E-CODE-DIRTY` — row 3 of the nine-undocumented-codes entry's own table — gained a § Errors core
raises row in this slice's batch-4 controller follow-up. Measured, not inferred:
`git log -S "E-CODE-DIRTY" --oneline -- docs/reference.md` → `4c79905` ("give E-CODE-DIRTY the row it
never had") and `758f8a7`. The design says the same wrong thing (§ The § Errors and § Warnings work:
*"not H6a's … H6b task 17 owns that"*), and both were written before batch 4's follow-up existed. The
appended record says eight, names the commit, and says `E-CODE-DIRTY` is no longer H6b task 17's.

**2. The brief's step 1 says the predicate "answers about git's whole exclude chain".** Under **Ruling
F**, which post-dates that sentence and wins, it does not: the call neutralizes the user's global and
system git configuration, so what answers is the repo's own committed rules plus `.git/info/exclude`.
Read at the shipped call site (`provenance.unignored_under_hashed_trees`:
`GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM=/dev/null`, `-c core.excludesFile=`). The strike says neither
`.gitignore` alone nor the whole chain, and names what it is. The plan's own *Live overrulings* item 2
carries the same over-wide phrasing and is superseded the same way.

**3. Found while filing, NOT fixed, because it is outside this task's Files list — for the whole-branch
gate.** `docs/reference.md`'s `W-PARAM-UNSET` § Warnings row (batch 5's) reads *"either
[the defaults structure `design-principles.md` forbids](#there-is-no-separate-defaults-file)"*. The
anchor is right and resolves; the **attribution is wrong** — § There is no separate defaults file is a
`reference.md` section, and `design-principles.md` has no such heading (grepped: `grep -n -i "defaults"
docs/design-principles.md` → lines 28, 153, 154, 164, none of them a section, line 164 only invoking
*"the same unanswerable question as a defaults file"* in passing). The one-word fix is
`design-principles.md` → `reference.md`. Not made here: task 12's Files list is `spec-defects.md`, the
spine design and `CLAUDE.md`, and batch 2's Major was an implementer self-authorizing an edit outside
its authorization even though it turned out clean. My own filing was written with the wrong attribution
first and corrected before commit.

**4. An observation for H6b task 18, not a finding here.** Decision 15 says § Templates' *"goes dirty at
`validate`"* "describes behaviour that does not exist". The phrase survives at one place in
`reference.md` (found by sweep, below). Read in its own sentence, whose subject is *discovery importing
every file writes `templates/__pycache__/`*, the claim is **the tree becomes dirty as a result of
running `validate`, and the subsequent `run` then fails** — which is true, and is not the claim
*`validate` reports a dirty tree*. Task 18 should re-read the sentence before assuming it must go.

---

## Task 12 — the filings, each with where it landed and its reproduce command

### Filing 1 (owned by name) — the core-schema half of `W-PARAM-UNSET`

**Landed:** `docs/superpowers/spec-defects.md`, new entry at the end of the file, *"An omitted
core-schema key validates clean and then kills every execution — **Owner: unassigned, with the
reason**"*. Batch 5 deliberately did not file it and folded the reason into a § Warnings row's prose;
this is the entry. *A ledger line saying "filed" is not a filing, and neither is a dispatch line.*

**Reproduced end to end through the installed console script**, not derived from emit sites:

```
publishable new proj
publishable generate experiment --name cohort-pilot --template generic \
    --input-dir <outside-repo> --output-dir <outside-repo>
# delete the one line `  min_reported_n: 10` from configs/cohort-pilot/config.yaml
publishable validate configs/cohort-pilot/config.yaml
    ✓ config valid · configs/cohort-pilot/config.yaml        exit 0, zero findings
# add `floor = cfg.limits.min_reported_n` to the scaffolded step's run(), git commit, then
publishable run configs/cohort-pilot/config.yaml
    run.yaml → status: failed
    error: 'E-STEP-PARAM-UNKNOWN ContractError: limits.min_reported_n is not a path this config holds'
```

**The symmetry with the `parameters` half was checked, not assumed** — the advisor's point. Read at
`config.py`'s `Node.__getattr__`: the raise is generic over any absent path with no special case for
the `parameters` subtree, so the § Warnings row's stated consequence for `cfg.parameters.<path>` is
true verbatim of `cfg.limits.<path>`. **Owner: unassigned, with the reason** — no remaining slice
(H6b, H9, H3c-3's remaining 14) has core's schema envelope as its surface, and closing it needs either
the defaults structure `reference.md` § There is no separate defaults file forbids or the greenfield
line crossed. Not *"whichever slice next touches the schema"*.

### Filing 2 (owned by name) — `git check-ignore`'s cost at scale, Ruling G

**Landed:** `spec-defects.md`, new entry at the end, *"`git check-ignore` costs 835 ms at ten thousand
paths, and the second axis is unmeasured — **Owner: unassigned, with the reason**"*.

**Re-measured on this branch rather than carried from the plan** (which measured 875 ms at `f8450f9`):
a committed tree of 10,002 files under `src/**`+`templates/**` with the scaffold's four-pattern
`.gitignore`, five runs each, minimum reported.

| Call | Measured |
|---|---|
| `git -c core.excludesFile= check-ignore -z --stdin`, config-neutralized, all 10,002 paths | **835 ms** |
| `git ls-files -z -co --exclude-standard` — the rejected shape | **16 ms** |
| `code_hash_of(hashed_files(root, None))` — the whole walk, read and fold | **370 ms** |

So ~51× the rejected shape and **~2.3× the entire hash**, which is Ruling G's *"roughly twice the whole
of `code_hash`"* confirmed on a second machine-state. **Pattern-count scaling is stated as unmeasured**
— both measurements, the 53-path one and this one, used a four-pattern `.gitignore`, and nothing here
licenses "paths are the only axis". Decision 2 is named as not reopened, and Decision 6's fallback is
recorded so a successor does not re-derive it.

### Filing 3 (conditional) — `.git/info/exclude`: **NOT filed, and here is the ground**

The dispatch says *file it only if the disclosure is not enough*. It is enough, so this is a stated
non-filing rather than an omission. `docs/reference.md` § How the three are computed carries it in the
four-case table (*"excluded by one of the repo's own committed rules — a `.gitignore` at any depth — or
by `.git/info/exclude`"*) and then in prose:

> `.git/info/exclude` is the exception no flag can disable: it lives in one clone and travels with
> nothing, so a file it excludes is unhashed here and hashed by whoever clones the repo. A file whose
> hashing status has to be the same everywhere is a file you **commit**.

That names the residue, states its consequence in both directions, and names an action. **Confirmed
live rather than read** (the residue is real, so the question was only whether it is disclosed): an
untracked `src/pkg/local_note.py` moves a committed project's digest from `sha256:19b9b39f…` to
`sha256:7c39b295…`, and writing `local_note.py` into `.git/info/exclude` returns it to
`sha256:19b9b39f…`. The reproduction is recorded inside the struck entry so a reader meets it there.

### Filing 4 — every entry this slice's code touched, re-read and re-measured

| Entry | What was re-measured | Result |
|---|---|---|
| *"`code_hash` is not `.gitignore`-aware"* | its own *"the two agree today"* sentence, one perturbation at a time against a committed base tree | **false, and false when written** — `.env`, `.venv/lib/site.py` and `loose.pyd` each MOVE the pre-slice digest; `__pycache__/x.pyc` and a loose `.pyc` do not, and that pair is `_SKIP_DIRS`/`_SKIP_SUFFIXES`, not a partial honouring. Baseline `sha256:71bf339c…` under both definitions, equal to Fixture A's |
| same | the resolution the entry itself proposed | shipped, with a corrected shape: a **batch keep-predicate**, `provenance.unignored_under_hashed_trees`, not a per-path `is_ignored` |
| same | *"or relax the purity rule"* | no such rule exists — see the spine correction below |
| *"`parameters_hash` does not normalize"* | **`hashes.covered_config`'s docstring, read before the strike** (the advisor's highest-yield item, and the design's own Disagreement 8) | **already correct** — task 10 re-pointed it to *"**Does not normalize, by decision.** … ruled against on three independent grounds (H6a, Decision 9)"*. It does not point at the entry being struck. No edit needed and none made |
| *"`code_hash` over zero files"* | `grep -rn '"E-CODE-EMPTY"' src/publishable/` | **one** hit, `cli.py:2380` |
| same | `grep -n "nonexistent_empty_repo" tests/test_hashes.py` | the two negative controls at lines 91 and 142 still call `code_hash(…, None)` for `sha256:e3b0c442…`, plus guard-pin arm E's literal at 649 — the empty return value is unchanged |
| *"`hashes.code_hash` has zero production call sites"* (Ruling K, closed by batch 3) | `grep -rn "code_hash(" src/publishable/*.py` | **one** hit, the `def` at `hashes.py:75` — the entry's claim holds |
| same | the body, and the delegation pin | body is `return code_hash_of(hashed_files(repo_root, include))`; `test_code_hash_delegates_to_code_hash_of_over_hashed_files` exists at `tests/test_hashes.py:38`. One fold, not two |
| same | its claim about `reference.md`'s **two** mentions | both present and both accurate — `W-STUDY-CODE-HASH-MISMATCH`'s row (*"`hashes.code_hash` is never called on this path"*) and § Building one (*"`report` never calls `hashes.code_hash`"*) |
| The nine-undocumented-codes entry | all nine swept against the four documents by name | see Disagreement 1. Also measured: `E-EXPERIMENT-UNKNOWN` has had its own row since **H8c task 16** (`git log -S … -- docs/reference.md` → `c794029`), which is stale for a reason that is not H6a's; `E-GIT-NO-REPO` and `E-EXPERIMENT-EXISTS` appear only inside *other* codes' prose; `E-PROJECT-EXISTS` has a § Exit codes sentence and no row, as `E-STEP-EXISTS` does; `E-GIT-NO-COMMIT`, `E-INPUT-CHANGED`, `E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED` appear nowhere in the four |
| The six-unwritten-`run.yaml`-keys entry | **not touched**, per step 6 | confirmed by `git diff` — the entry is unchanged |

**Every closed entry is STRUCK, never deleted**: three headings gained `~~…~~` plus a dated marker, in
the form the file already uses at seven other headings, and each body gained an appended dated
paragraph rather than losing anything. **Every owner is a fact with a reason.**

### Step 7 — the spine correction, appended and not edited

`docs/superpowers/specs/2026-08-08-implementation-spine-design.md` § The hardening slices, appended
after the *Second correction to this amendment* block and before § Order. Four items:

1. *"`parameters_hash` normalization against `parameter_spec`"* **rejected**, with Decision 9's three
   grounds, sharpest first.
2. *"the purity rule that forced both"* **names a rule that is in no document.** Grepped 2026-08-22,
   case-insensitive, `pur(e|ity)` over the four documents named individually: **one** hit total,
   `reference.md`'s *"`parameters_hash` is a pure function of the file"*, a claim about one function's
   inputs rather than a constraint on a module. Its real home is a plan's sentence quoted in the ledger
   entry the charter row was derived from. And `hashes.py` was never pure in that sense — it `rglob`s
   (line 39), `read_bytes()` (line 67) and carries `_SKIP_DIRS`/`_SKIP_SUFFIXES` (lines 10–11).
3. *"Independent"* **too strong in one direction — H6 before H9.**
4. **Added, and flagged here as beyond the brief's "three things":** the row never received H6's own
   split (H6a/H6b, `H6-SCOPING.md`), which is exactly what the amendment it is appended to exists to
   record, and the size moved the way every re-scoping in that file has —
   `grep -c '^## Task ' docs/superpowers/plans/2026-08-22-hash-definitions.md` → **13** against the
   scoping's 12 and the design's *"Twelve tasks"*. Added because the order line now says **H6b** and a
   reader of the table alone would find no such slice.

### Step 8 — `CLAUDE.md`

Order line: *"H6 Hashes and provenance, H9, then H3c-3's remaining 14"* → **"H6b, H9, then H3c-3's
remaining 14"**. H5 was already gone from that line, so nothing stale was left behind by the edit. The
following clause moved to the past tense and now carries the H6-before-H9 correction, since leaving
*"H6 **is** chartered as independent"* standing would have contradicted the spine correction written in
the same commit.

The slice entry sits where the newest entry goes (immediately before H5b's) and states: the value
change with both measured digests and the enumerated ten unmoved figures; the two errors and one
warning; **zero configs unblocked**, with the four-row table named; that `diff` prints
`code_hash DIFFERS` for identical code across the boundary and `uv.lock` is the carrier; and Ruling C's
sharpest cost — **one record can carry two hash definitions, its own under the new rule and a copied
upstream's under the old, with nothing marking which is which**.

---

## The per-code emit-site check, with each table's own scope sentence quoted

*Check the table's own scope sentence, not the design's instruction* — batch 4's finding. All four
codes have **one** emit site each and one row each, in a table whose scope sentence admits it.

| Code | Emit sites, grepped | Row | The table's OWN scope sentence |
|---|---|---|---|
| `E-CODE-EMPTY` | **1** — `grep -rn '"E-CODE-EMPTY"' src/publishable/` → `cli.py:2380` | `reference.md` § Errors core raises | *"**Two rows in this table are not raises, and the `Type` cell says so.** A command can also refuse through a fresh `Collector` … the dirty gate and the empty-file-list gate, both inside `command_run`. They sit here rather than in § Errors `validate` reports because **`validate` does not report them**"* — the scope was widened to admit exactly these two by batch 4's follow-up, and the row's `Type` cell reads *(no exception; a `Collector` diagnostic)* |
| `E-CODE-DIRTY` | **1** — `grep -rn "E-CODE-DIRTY" src/publishable/` → `cli.py:2028` | `reference.md` § Errors core raises | the same sentence — it is the *other* of the two |
| `E-CODE-FILE-LIST` | **1** — `grep -rn "E-CODE-FILE-LIST" src/publishable/` → `provenance.py:81` | `reference.md` § Errors core raises | *"**Each carries `.code`**, the same stable `E-` identifier a command prints beside a diagnostic"*, under the exception hierarchy — and this one **does** raise, `ContractError`, so it needs no exemption |
| `W-PARAM-UNSET` | **1** — `grep -rn "W-PARAM-UNSET" src/publishable/` → `validate.py:1108` (plus three prose mentions in docstrings at 1072, 1121, 1125) | **two** rows: `reference.md` § Warnings core reports, and § Validation's check table (*"Defaulted parameter left unset"*, line 236) | § Warnings core reports: *"A warning is a diagnostic, not an exception … **Some fire at `validate` time, from the declaration alone**; others fire at `run` time"* — this one is the first kind. § Validation: *"The table below states each check by the mistake it catches … **a row here and a code there are the same check seen from the two ends**"*, and sibling rows already carry `(warning)` |

**And the emit site is a `warn`, not an `error`** — read at `validate.py:1106`, `c.warn("W-PARAM-UNSET", …)`. That is row 1 of § Executability's whole ground and is measured again below.

---

## The sweeps — exact command, file list, and can-fail proof

**The file list is filtered; the output never is.** All sweeps are **newline-insensitive**: each file is
read whole and `re.sub(r'\s+', ' ', …)`-normalized before matching, so a wrapped phrase cannot hide —
which is how two of one false sentence's five homes hid last slice.

**File list, named rather than globbed:** `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md`,
`docs/feasibility-llm-growth-studies.md`.

Command (`/tmp/sweep.py`, thrown away rather than kept):

```python
FILES = ["README.md","docs/design-principles.md","docs/experimental-designs.md","docs/reference.md",
         "CLAUDE.md","docs/feasibility-llm-growth-studies.md"]
norm = {f: re.sub(r'\s+',' ', pathlib.Path(f).read_text()) for f in FILES}
for phrase in sys.argv[1:]:
    p = re.sub(r'\s+',' ', phrase)
    print(f"[{p!r}] -> " + (", ".join(f"{f}:{norm[f].count(p)}" for f in FILES if norm[f].count(p)) or "NO HITS"))
```

| Swept for | Result |
|---|---|
| `H6 Hashes and provenance` (the order-line token this task renamed) | **NO HITS** |
| `H6 is chartered as independent` | **NO HITS** |
| ``normalized to what `init` would have materialized`` (Ruling B's deleted claim) | **NO HITS** |
| ``an omitted `cluster_by` and an explicit `cluster_by: null` are the same declaration`` (the same claim's other half) | **NO HITS** |
| `so a defaulted parameter it omits is not reported` (the docstring clause task 11 deleted) | **NO HITS** |
| ``code_hash` still has exactly one`` (the arm-E clause Ruling J authorized deleting) | **NO HITS** |
| ``goes dirty at `validate``` | **`docs/reference.md`:1** — see Disagreement 4; left standing, and it is H6b task 18's |

**Can-fail proof, run as the same command against strings known to be present in the same file list:**

| Control | Hit |
|---|---|
| `H6b, H9, then H3c-3's remaining 14` | `CLAUDE.md`:1 |
| `H6 was chartered as independent` | `CLAUDE.md`:1 |
| `Errors core raises` | `docs/reference.md`:4 |
| `the exception no flag can disable` | `docs/reference.md`:1 |

Every control hit, so no sweep above was a sweep that could not fail. **Two of three sweeps written in
one recent batch could not fail when first run, by their authors, while checking for exactly that** —
which is why the controls are run and reported rather than asserted.

---

## The mechanical pass

Written as a throwaway script (`/tmp/mech.py`), run over **`README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `docs/feasibility-llm-growth-studies.md`,
`CLAUDE.md`** plus the two development-record files this batch edited (`spec-defects.md`, the spine
design) as a self-check on my own typing — *the passes govern the four documents and the feasibility
analysis; they do not govern the development record, and nothing was changed in it on their account.*
It skips fenced blocks throughout. **Result: 0 problems over 8 files.**

Checks and their proof of being able to fail — a copy of `reference.md` with one instance of each fault
appended reported every class:

| Check | Proven to fail on |
|---|---|
| relative links resolve | `[bad file](nope.md)` → BROKEN LINK |
| `#anchor`s resolve | `[bad anchor](#no-such-heading-anywhere)` → BROKEN ANCHOR |
| cross-file `file.md#anchor` resolve | `design-principles.md#nope` → BROKEN CROSS-ANCHOR |
| no two headings share an anchor | a second `## Errors core raises` → DUPLICATE ANCHOR 'errors-core-raises' (also line 1092) |
| table rows match the header's column count | a 1-cell and a 3-cell row under a 2-cell header → both reported |
| no trailing whitespace | reported |
| no tab | reported |
| no invisible unicode | a `U+200B` → reported |

**The checker's own first run reported 8 false positives and they were a bug in the checker, not in the
documents** — it stripped `_` as an emphasis marker, so every anchor containing `derive_seed` or
`reuse_from` looked broken. Fixed and re-run; recorded because *a mutation that changes nothing is
evidence about the test*, and so is a check that fires on nothing.

Two checks are separate greps, both with controls:

- **`×` not `x` for multiplication:** `grep -nE '[0-9] ?x ?[0-9]'` over the six files → **no hits**;
  control `grep -nE '[0-9] ?× ?[0-9]'` over the same six → hits in `docs/experimental-designs.md`
  (`2 × 2`, `3 × 2`), so the pattern shape can match.
- **no wholly empty table row:** `grep -nE '^\s*\|(\s*\|)+\s*$'` over the six files → **no hits**;
  control, the same grep against a one-line file containing `| |  |` → matched. (This one is a separate
  grep because the script's own separator-row regex swallows it.)
- **hyphens, not en dashes, in anything that becomes an anchor:** no anchor in the six files failed to
  resolve, which is the direct test rather than the proxy; existing headings use em dashes (`E1 —
  Metric calibration`) and their anchors resolve, which is settled house practice, not a new fault.

---

## The cross-document pass — the four documents only

**This batch edits none of the four**, so the pass is over what the *branch* did to `docs/reference.md`
(the only one of the four it touched, 48 insertions / 5 deletions).

| Class | Result |
|---|---|
| **The shared worked example** | **Untouched, verified rather than assumed.** `git diff main...HEAD -- docs/reference.md \| grep -oE '<every worked-example literal>'` → **no matches**: not one of `0.581`/`0.607`/`0.412`/`0.488`/`0.661`/`0.517`/`0.683`/`0.347`/`0.477`/`0.026`/`0.007`/`0.059`/`0.169`/`0.213`/`0.125`/`0.014`/`0.033`/`0.009`, `228`, `240`, `8e21`, `1a2b`, `3d8a`, `6b1f`, `2f5c8d0`, or either `run_…_8e21ab3`. Can-fail control: the same regex over the whole file finds `0.581` ×1, `0.607` ×6, `228` ×15, `8e21` ×15. **No interval was narrowed back** |
| **Config completeness** | this slice adds no config field; § The one config file is unchanged on the branch |
| **Enum comments** | no enum or its inline `# a \| b \| c` comment was touched |
| **Schema fields in prose** | the new prose names `parameters`, `src/**`, `templates/**` and `.git/info/exclude` — no new schema field is named anywhere |
| **Declared vs derived** | `code_hash` is derived everywhere it appears and is shown as a settable input nowhere; the branch adds no passage that could reverse this |
| **Versions** | `CITATION.cff` `version: 0.1.0` and README's *"v0.x"* notice, both unchanged by the branch |
| **Prevented mistakes** | `experimental-designs.md` § Mistakes core prevents is untouched by the branch; the two new errors are `run`-time refusals, not schema-expressible prevention, and are not claimed there |

---

## Task 13 — § Executability's re-derivation, and the table unchanged

**Landed:** one appended entry in `docs/feasibility-llm-growth-studies.md`, *"### Measured on
2026-08-22 against commit `f70499f` — after H6a"*, placed after the H5b correction, matching the
precedent that these dated `###` entries sit under § Cost and execution summary. The `## Contents` list
carries only `##` headings, so it needs no row — checked, not assumed. **This file is the only one task
13 touched, and only in that section.**

**The re-derivation, and the two halves of it that were measured rather than repeated:**

1. **Row 1 counts configs validating with zero *errors*, and `W-PARAM-UNSET` is a warning.** Read:
   `validate.py:1106` is `c.warn`, and `Collector` has distinct `error`/`warn`. **Run**, on a
   scaffolded `generic` project with `parameters.analysis.confidence` deleted:
   `warning W-PARAM-UNSET … 1 problem (0 errors, 1 warning)`, **exit 0**. A warning cannot move an
   error count.
2. **Neither new error is reachable from `validate`.** `grep -c "E-CODE-EMPTY\|E-CODE-FILE-LIST"
   src/publishable/validate.py` → **0**; control `grep -c "E-PARAM-MISSING"
   src/publishable/validate.py` → **3**, so the sweep can find a code `validate` does emit. Both are
   raised by `command_run`.
3. **Rows 2 and 3 name `io.reuse_from`'s plugin-side call and the `report_by`-under-`resample`
   construction**; H6a's surface is `hashes.py`, `provenance.py`, `command_run`'s hashing phase and
   `validate._check_parameters`, and is neither.
4. **Row 4 counts per-config core-side dependencies, and `code_hash` is computed for every run
   regardless of config** — no declaration opts in or out, so no config gains or loses one.

**The four rows, repeated character for character** — extracted from the immediately preceding entry
with `sed -n '1775,1781p'`, pasted, then the pasted block re-extracted and `diff`-ed against the
extraction: **diff empty over all six table lines, `md5` identical (`20e8fc95513a15c376345ab966604e11`
both sides)**. Can-fail proof: mutating `8 of 8` → `9 of 9` in the copy makes the same `diff` report a
difference. **The plan's own reproduction of this table in its opening was not used as the source.**

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**No fifth number is minted**, and the entry quotes no single figure for this analysis' executability —
it quotes the table and names the dependency.

**What newly stops and what newly warns, in prose and not as a row** (H5b's own dated correction's
shape): `E-CODE-EMPTY` and `E-CODE-FILE-LIST` **cannot fire for any of the nine**, because both are
properties of a **repository** and no config in this analysis names one, nor does either code read a
declaration. `W-PARAM-UNSET`'s effect is **unknowable, with the reason** — it depends on the
`growth_screen`/`growth_shortcut` templates' own `parameter_spec`, and **neither `growth_screen` nor
`publishable-llm` is installable in any build**, so guessing from the shown `parameters` blocks would
measure the guess. Stated rather than guessed.

**The value change's effect on this analysis is stated and mints no row:** any run of these configs
before and after this build compares as `code_hash DIFFERS` for identical code whenever the project
carries an excluded file under the two trees — the scaffolded `.gitignore`'s `.env` and `.venv/` being
the two an LLM project is most likely to carry. A fact about comparisons, not about executability.

---

## Guard pins and surface

**No guard-pin arm was opened.** Arms A, C, D and N have no authorized editor; B, E and F belong to
other tasks. `git diff main...HEAD` for this batch touches `CLAUDE.md`,
`docs/superpowers/spec-defects.md`, `docs/superpowers/specs/2026-08-08-implementation-spine-design.md`
and `docs/feasibility-llm-growth-studies.md` — **no file under `src/` or `tests/`**, so no arm could
have moved, and the suite at 2955/1/2 is the confirmation.

Task 12 touched no § Executability entry and no `spec-defects.md` entry this slice did not close, other
than the nine-undocumented-codes entry it was told to append to. Task 13 touched none of the four
documents and no row of the table.

## Concerns for the whole-branch gate

1. **Disagreement 3** — the one-word mis-attribution in `reference.md`'s `W-PARAM-UNSET` § Warnings
   row, deliberately left for an authorized editor.
2. **Disagreement 4** — Decision 15's reading of *"goes dirty at `validate`"* looks wrong against the
   sentence's own subject; H6b task 18 inherits it and should re-read rather than delete on the
   design's say-so.
3. **`diff.py`'s helper name.** § Corrections 9 says the design's `diff.py::_parameters_hash_for` does
   not exist and the real name is the `_compute_parameters_hash` alias. Confirmed still true at this
   commit. The design carries the wrong name in Decision 12 and in its own measurements table; nothing
   in `docs/` or `spec-defects.md` cites it, and a spec is not retro-edited, so it is reported rather
   than fixed. **This batch cites no helper name at all.**

---

## Correction to this report, appended the same day — concern 3 above is wrong in both of its claims

**Appended rather than edited**, the way this project corrects a published claim. Written minutes after
the commit above, on a grep run to check my own sentence — which is the point: *before repeating any
claim a brief makes about the code, grep for it*, and I repeated one without doing so, in the report
whose job was to check exactly that.

**Concern 3 said the plan's § Corrections 9 is right and that nothing in `docs/` cites the name. Both
halves are false, and the more important one is the first.**

`grep -rn "_parameters_hash_for" docs/ src/ tests/`:

```
src/publishable/diff.py:419:def _parameters_hash_for(side: _Side) -> str:
src/publishable/diff.py:457:    hash_a = _parameters_hash_for(side_a)
src/publishable/diff.py:458:    hash_b = _parameters_hash_for(side_b)
tests/test_diff.py:24,456,463,474,506  — imported and exercised by name
docs/superpowers/spec-defects.md:4599  — cites `diff._parameters_hash_for`
docs/superpowers/specs/2026-08-22-hash-definitions-design.md:49, 494  — the design's two citations
docs/superpowers/plans/2026-08-22-hash-definitions.md:1449, 1450  — the correction itself
```

**`_parameters_hash_for` exists, at `diff.py:419`, and the design's citation of it is accurate.** The
plan's § Corrections 9 — *"`diff.py`'s helper is `_compute_parameters_hash`, not
`_parameters_hash_for`"* — **confuses the helper with the aliased import it calls**: `diff.py:28` does
`from publishable.hashes import parameters_hash as _compute_parameters_hash`, and `_parameters_hash_for`
calls that alias at line 439 for a config side while returning a run side's recorded string. Both names
are real and they are two different things.

**So a correction presented as measured is itself wrong**, and it instructed *"tasks 7 and 12 cite the
real name where they cite one at all"* — which, had either task cited a name, would have made it cite
the wrong one. Neither did, so nothing shipped on it. The **behavioural** claim both documents agree on
is unaffected and still confirmed: only a config operand is recomputed, a run side reads the recorded
string.

**And the second half of concern 3 was false too:** `docs/superpowers/spec-defects.md:4599` does cite
`diff._parameters_hash_for` — correctly, as it turns out. Nothing needs correcting there.

**Nothing else in this report depends on either claim**, and no commit does: `f70499f` and `fe8ea47`
cite no helper name.

---

## Second correction to this report, same day — two counts in the `CLAUDE.md` entry, fixed at `823e569`

Found by re-reading my own entry against the ledger rather than against my memory of it. Neither is a
claim any commit rests on; both are the kind of number this project re-derives rather than carries.

1. *"batch 2 did and it was the slice's one Major"* — **wrong**. Batch 2's review recorded one Major;
   batch 3's recorded **three**. Corrected to *"that was its own batch's only Major"*.
2. *"Twice more the device caught a sentence going false under its own change"* — **undercounted**. The
   ledger's batch-5 entry says *"the third time this slice has caught a sentence going false under its
   own change"*, and the third is batch 1's Minor: `hashes.py`'s `code_hash` docstring saying it reads
   the working tree *"not from git"*, true when written and false after task 5, which task 5 then
   fixed (read at the current tree: *"**Which** files are read is `include`'s answer, and
   `command_run`'s asks git"*). Corrected to three, all three named.

`CLAUDE.md` is a live document rather than a development record, so this one is corrected in place and
the correction recorded here.

---

## Third correction to this report, same day — two additions at `<this commit>`, and one wrong sweep inside the first draft of one of them

Two gaps a re-read found, both closed in the same commit as this append.

1. **The § Executability pin did not say why `f70499f` names the tree the figures were measured
   against.** The measurements were run before that commit existed. H5b's own entry states the
   equivalent reasoning explicitly and this one did not, so a reader met a pin that looked
   measured-at-a-commit it wasn't. Added: the last commit on this branch touching `src/` or `tests/`
   is `c4dea36` (task 11), and `git diff --name-only c4dea36..HEAD -- src tests` is **empty**, so every
   commit after it carries the same executable tree. **The first draft of that sentence cited
   `git diff --stat main...HEAD` as naming only `.md` files, which is false** — that range covers the
   whole branch and names four files under `src/` and five under `tests/`. Caught by running the
   command instead of reasoning about it, before the commit; recorded because it is the same fault
   class as the `_parameters_hash_for` one above, twice in one batch, both in a *claim about what a
   command returns*.
2. **The spine correction's item 4 named three sizes for H6a and no operative one.** The two
   corrections above it in that section each name what they replace; mine listed 13, 12 and "Twelve
   tasks" and left a reader to guess. Added one clause: **the operative figure is 13**, in six
   batches, and the scoping's 12 and the design's twelve are what it replaces. H6b's 8 is the
   scoping's and is untested by anything in this slice.

**The eight-file mechanical pass was re-run at the current tip** — `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`,
`docs/feasibility-llm-growth-studies.md`, `CLAUDE.md`, `docs/superpowers/spec-defects.md`,
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md` — **0 problems over 8 files**, so
the pass is measured at the tree that ships rather than at `fe8ea47`.

**One thing to concede rather than defend if the gate presses on it.** The append to the
nine-undocumented-codes entry classifies the remaining seven codes by *document* presence — a row of
their own, a mention inside another code's row, a § Exit codes sentence, or nothing. Each statement is
measured and true as worded, but their **emit sites** were not re-greped, and the classification is
work on codes outside H6a's surface. The defensible core of that append is the `E-CODE-DIRTY`
correction with its commit and the `E-EXPERIMENT-UNKNOWN` fact with its commit; the taxonomy of the
other six is the part to drop if a reviewer wants the entry kept narrow.
