# H9a batches 6–7 review — tasks 10–14

**Reviewed 2026-08-23 at `12a9370`** (branch `h9a-re-entry-seam`, ~40 commits ahead of `main`).
Commits under review: `204fbf7` (10), `42019f5` (11), `efad33c` (12), `c925416` (13), `e133833` (14),
`66a24b4` (report), `12a9370` (its own fix round).

**Verdicts: task 10 PASS · task 11 PASS · task 12 PASS with one Major and one Minor · task 13 PASS
with one Minor · task 14 PASS with one Major.**

Suite at review time, run directly in the foreground after clearing stale dirs and `__pycache__`:
**3019 passed, 1 skipped, 2 xfailed in 215.58s.** `uv run ruff check .` → *All checks passed!* ·
`uv run ruff format --check .` → *93 files already formatted* · `uv run mypy` → *Success: no issues
found in 52 source files*.

**What was verified by behaviour and what by reading** is stated on every item below. Every mutation
count names the `-k` selection it was scoped to, per the ledger's own Minor about single-test-scoped
counts reported as though they were suite-wide.

---

## Task 10 — PASS. The `probes the apparatus` clause is TRUE, rebuilt independently

**Verified by behaviour, not by reading the report.** I built my own out-of-repo project — a
project-local template declaring `apparatus_probe = "rev_probe"` and `apparatus_facts =
["model_revision", "reagent_lot"]`, the probe supplied by a real installed distribution
(`rev_probe_dist-1.0.dist-info/` with `entry_points.txt`, on `PYTHONPATH`) — committed once, and ran
the real console script:

```
$ REV_CALLS=…/calls.txt PYTHONPATH=…/site:…/outside \
    uv run publishable dry-run …/proj/configs/probe-pilot/config.yaml
  warning W-APPARATUS-UNANSWERED apparatus
          condition `00_model=m1`'s fact `reagent_lot` came back `null` on 1 of 1 probes
  warning W-APPARATUS-UNANSWERED apparatus
          condition `01_model=m2`'s fact `reagent_lot` came back `null` on 1 of 1 probes
2 problems (0 errors, 2 warnings)
sweep: 2 conditions (grid) × 1 repeats = 2 executions
…
and 9 fixed files in that directory:
  apparatus/probes.jsonl
…
creates nothing
EXIT=0
$ cat calls.txt
m1
m2
$ ls -A …/results | wc -l
0
```

**Two calls, one per resolved condition, each under that condition's own cfg** (`m1`, `m2` — not
`m1`, `m1`); both conditions warn; `output_dir` empty; exit 0. The clause the batch 3–5 review left
open with an escalation is **true**, so it does not promote to a Major.

**Three homes, confirmed, and a fourth home of the same claim.**
`grep -rn "probes the apparatus" README.md docs/ src/ tests/ CLAUDE.md` (development record excluded
by naming the files, not by filtering output; can-fail control `zzz-absent-string` → 0) attributes
`reference.md:368` (§ Operation commands prose), `:3136` (§ Before you spend it — *"real credentials
and a reachable apparatus … for a sweep over six model deployments, all six"*, the strongest), and
`:3706` (the § CLI reference row Minor 5 named). All three are satisfied by the run above. A **fourth**
home of the claim in different words is `reference.md:3267` — *"It runs at `dry-run`, at run start,
before every execution, and at `freeze` — never at `validate`"* — also true.

**Decision 14's containment verified by behaviour, independently.** A probe raising with a credential
declared through `Param(requires_env={"m1": ["REV_SECRET"], …})` and set in `.env`:

```
exit=5
  error   E-APPARATUS-RAISED   experiment_type
          probe `rev_probe` raised RuntimeError: instrument rejected token <redacted:REV_SECRET>
leaked=0 redacted=1
```

`EXIT_EXTERNAL` for `E-APPARATUS-RAISED`, the secret absent, `<redacted:` present. **A first attempt
of mine passed vacuously** — `requires_env={"alpha": "RR_TOKEN"}` (a bare string, not a list) made
core iterate the string character by character and left `credentials` empty, so the secret printed
verbatim at all four commands *and on `main` too*. Recorded here because it is the trap Fixture W's
own note names: an undeclared credential passes the redaction assertion for the wrong reason.

**A path not exercised by the shipped fixtures, found while rebuilding:** a declared fact the probe
does not return **at all** (rather than returning as `None`) earns `E-APPARATUS-FACT-MISSING` and
`EXIT_WRONG` at `dry-run`, with the round stopping after the first condition's call (tally: `m1`
alone). That is the containment's non-`RAISED` branch doing exactly what its comment says. No finding
— stated so the next reader knows the branch was exercised.

## Task 11 — PASS. The blind-mutation diagnosis reproduced exactly

**Verified by behaviour.** I spliced the design's prescribed mutation in for real —
`apparatus.append_observation(prepared.output_dir, phase=apparatus.PHASE_DRY_RUN, condition=…,
probe=declared_probe, facts=facts)` inside `_dry_run_probe`'s loop — and ran the four *creates
nothing* arms by name:

```
$ uv run pytest tests/test_cli.py -q -k "test_h9a_dry_run_creates_nothing_under_output_dir_on_a_never_run_project
    or test_h9a_dry_run_leaves_an_existing_output_dir_byte_identical
    or test_h9a_dry_run_against_a_live_lock_completes_and_takes_none
    or test_h9a_fixture_y_dry_run_creates_nothing_while_the_probe_round_runs"
FAILED …::test_h9a_fixture_y_dry_run_creates_nothing_while_the_probe_round_runs
E  Left contains 2 more items:
E  {'apparatus': None, 'apparatus/probes.jsonl': (276, …)}
1 failed, 3 passed, 475 deselected
```

**1 failed, 3 passed** over that four-test selection. The three shipped arms are blind because
`_h6a_t5_project`'s `generic` template has `apparatus_probe = None`; only task 11's new arm fails.
*Reporting a mutation blind is necessary and not sufficient — it owes a replacement*, and the
replacement is real and discriminating. Reverted by copying the pre-mutation file back and
**re-running** the arm (1 passed).

**Decision 12's named residue independently confirmed.** Snapshotting the whole project tree without
excluding `__pycache__` around a real `dry-run` shows exactly two added paths —
`templates/__pycache__` and `templates/__pycache__/rev_assay.cpython-313.pyc` — and **nothing** under
`output_dir`. So the scoping of *Creates nothing* to `output_dir` is the promise rather than a
weakening of it, as the docstring argues.

## Task 12 — PASS, with **Major 1** and **Minor 1**

### Major 1 — the widened `W-APPARATUS-UNANSWERED` row now contradicts itself, and the false half says `dry-run` replays a ledger

**Established by reading both versions of the row, mechanically extracted.** On `main` the row ends:

> **A second surface**: [`freeze`] fires the identical warning at the end of its own invocation …
> through its own `Collector`. **Its counts are the run's own accumulated
> `run_start`/`pre_execution` history, replayed from the ledger** as this invocation's starting point,
> **plus** the one round `freeze` itself just probed …

"Its counts" bound to **`freeze`**. Task 12 inserted the new clause **between** that sentence and the
`freeze` sentence it modifies, so at HEAD (`docs/reference.md:378`) the row reads, in sequence:

> **A third**: [`dry-run`] fires it from its own probe round, **over that round's own in-memory counts
> alone** … printed to stdout through a fresh `Collector` before the transcript … **Its counts are the
> run's own accumulated `run_start`/`pre_execution` history, replayed from the ledger** …

**One row, two contradictory claims about the same command**, and the false half asserts `dry-run`
reads a ledger — precisely what Decision 7 exists to deny, and what task 13 wrote into § The apparatus
files one commit later (*"`dry_run` is a reserved phase name that no build appends, because the ledger
lives inside a run directory `dry-run` never creates"*). The later `` "the one round `freeze` itself
just probed" `` lets a careful reader reconstruct the intent; that is an argument about how to fix it,
not against the finding, and a normative § Warnings row is not read that carefully.

The command that establishes it:

```
$ git show main:docs/reference.md | grep -n 'W-APPARATUS-UNANSWERED` |'
378: … **A second surface**: `freeze` … through its own `Collector`. Its counts are the run's own …
$ sed -n '378p' docs/reference.md
… **A second surface**: `freeze` … **A third**: `dry-run` … over that round's own in-memory counts
alone … Its counts are the run's own … replayed from the ledger …
```

**Routed to a document-only fix in `reference.md` § Warnings core reports**: move the `dry-run` clause
to **after** the `freeze` "Its counts" sentence, or bind that sentence explicitly (`freeze`'s counts
are …). No code moves. **This is the sibling of the fault the report's own addendum caught twice** —
*when you edit one line of a block, diff the block* — applied to the row's own following sentence.

**I swept the other twelve row edits for the same shape and found none.** Method: extract every
`§ Errors`/`§ Warnings` row by its code cell from `main` and from HEAD, word-diff each, and print
**45 words of following context** after every insertion point. Only `W-APPARATUS-UNANSWERED` has a
pronoun whose antecedent the insertion displaced; the other twelve either replace a name in place or
append at the end of a clause, and each reads coherently. Script and output kept at
`scratchpad/wk/rowdiff.txt`.

### Minor 1 — "fifteen § Errors / § Warnings rows" is thirteen, and it is now in `CLAUDE.md`

**Measured, by extracting rows by their code cell rather than by counting diff lines** (a `+| ` count
would have given the same 13, but the row-keyed extraction attributes each):

```
task 12 (efad33c) alone            → 13 rows changed
task 12 + fix round (12a9370)      → 14 rows changed
    the 14th is E-CODE-DIRTY, which the fix round WIDENED-to-narrower, i.e. a narrowing of a row
    that had gone WIDE — not one of the "narrower than their code" class at all
```

The 13: `E-APPARATUS-RAISED`, `-RETURN`, `E-PROBE-UNKNOWN`, `E-PLUGIN-DECORATOR`, `E-PLUGIN-LOAD`,
`W-APPARATUS-UNANSWERED`, `E-RESOLVER-SWEPT-PARAM`, `E-RESOLVER-RAISED`, `E-UNITS-ATTR-MISSING`,
`E-UNITS-ATTR-COLUMN`, `E-UNITS-EMPTY`, `E-UNITS-KEY-DUPLICATE`, `E-UNITS-SOURCE-UNREADABLE`.
**That is exactly what the report's own verdict table enumerates** — its prose says fifteen while its
table lists thirteen. `efad33c`'s commit message says fifteen; the addendum says *"the fourteen
narrowings in § Task 12"*, wrong twice (13 in task 12; the 14th is a widening). And **`CLAUDE.md`'s
new H9a paragraph carries "Fifteen § Errors / § Warnings rows were narrower than their code"** into a
tracked document.

Routed: correct the count in `CLAUDE.md`'s paragraph to **thirteen** (or *"thirteen, plus one that had
gone wider"*) and say so in an appended note on the report. This is the same class as the ledger's
"ninth miscount in four slices" and the report's own Minor about the amendment's count — a number
carried rather than derived.

### What I checked and found sound

- **The six roster rows did not lose their `validate` surface while being widened.** The new text
  enumerates `run`, `draft` and `dry-run` and does **not** name `validate` — but all six live in
  **§ Errors `validate` reports** (`awk` over headings: the section spans 413–652, the rows sit at
  594/631/635 and neighbours), whose own scope sentence supplies it, and each keeps its explicit
  **Dual-surface** label plus *"reports it there **too**"*. No new narrowing.
- **The widening is true of the code, verified by behaviour** rather than by reading. A resolver
  plugin raising with a **declared** credential (`Param(requires_env={"alpha": ["RR_TOKEN"]})`, value
  in `.env`), run through the real console script at all four commands:
  `validate`/`dry-run`/`draft`/`run` → exit 1, `E-RESOLVER-RAISED`, secret **absent**, `<redacted:`
  **present** at every one. So *"contains the identical raise at each of those three commands"* holds.
- **`E-APPARATUS-RAISED`'s *three* → *four* outcomes and *A fourth surface* have no contradicting home.**
  Sweep over the four documents plus `CLAUDE.md`, the feasibility analysis and `src/**`, files named
  individually: `three outcomes|four outcomes|two outcomes` → **0** other hits; the probe-surface
  enumerations at `reference.md:1157`, `:3267`, `:1025`, `:3727` and
  `experimental-designs.md:375` all say four/`dry-run`-inclusive and agree.
- **`E-PROBE-UNKNOWN`'s `dry-run` attribution is not over-claimed.** `validate._check_probe` answers
  first for `dry-run` in every ordinary case, and the row says so in its own next sentence (*"met only
  where nothing validated this config first, or where the installed set changed between the two"*).
- **The plan's amended sweep count is one short — confirmed, and it is the second wrong count in that
  lineage.** `git show 574eba7:docs/reference.md | grep -c "would write"` → **4** at the exact commit
  the amendment says it measured against, while the amendment names three (`:3094`, `:3673`, `:3756`)
  and misses `:368`. The amendment itself replaced a target with **zero** homes. The report's Minor is
  correct and correctly recorded without retro-editing the plan.
- **The worked example's statistics did not move.** `grep -o` over the four documents named
  individually: `0.581` ×2, `0.607` ×9, `0.412` ×1, `0.488, 0.661` ×2, `0.517, 0.683` ×7,
  `0.347, 0.477` ×1, `−0.007, 0.059` ×1, `−0.213, −0.125` ×1; can-fail control `0.29801` → 0. The
  branch diff of those four files contains **no** line carrying any of them.
- **The 20 is right, and the `= N executions` figure is `len(plan)` rather than conditions × repeats.**
  Reproduced independently on a 3-scope, 3-condition, 2-repeat project outside the repo:
  `sweep: 3 conditions (baseline + grid) × 2 repeats = 8 executions` with
  `would create 8 step directories` — 1 (`run`) + 6 (`repeat`) + 1 (`summary`). 3 × 2 = 6. Filing 3's
  claim is exactly right.

## Task 13 — PASS, with **Minor 2**

All three filings reproduced independently.

- **Filing 1 (seed labels).** `uv run python -c "print([f'seed{s % 100:02d}' for s in
  [17,42,137,1009,2027]])"` → `['seed17','seed42','seed37','seed09','seed27']`; `replication.py:83–85`
  is the rule with the full-value form as a **collision-only** fallback (read), and all five two-digit
  labels are distinct, so it never fires. `grep -n "seed137\|seed1009\|seed2027"` over the four
  documents plus `CLAUDE.md` and the feasibility analysis → **two homes**, `reference.md:905` and
  `:923`, both predating this slice. § Before you spend it's transcript at HEAD lists `seed17` and
  `seed42` and elides the rest, so the fix round's correction landed and the filing no longer
  contradicts itself.
- **Filing 2 (`command_run` residue).** `grep -rn "command_run" src/ tests/ | wc -l` → **195**;
  22 files; `tests/` **101** against `src/`'s **94**; `grep -c "command_run" docs/reference.md` → **1**.
  Every figure reproduces.
- **Filing 3 (the sweep header).** Reproduced above by running.
- **The struck `PHASE_DRY_RUN` entry.** `grep -rn "PHASE_DRY_RUN" src/` → 6 lines, 2 code and 4 prose,
  no call site — and the `append_observation` mutation in task 11's section is the behavioural proof
  that adding one is visible.
- **`apparatus.py` really is docstrings only.** Not read off the diff: parsed both sides with `ast`,
  removed **every bare string-constant expression statement** anywhere in the tree, and compared
  `ast.dump` — **equal**. Zero executable statements moved.

### Minor 2 — the signpost filing over-claims its own mitigation, by a proxy

The filing says: *"A reader who greps `command_run` in `cli.py` lands on it: it is inside the function
every one of those 34 hits names."* **Names ≠ sits inside.** Measured:

```
$ uv run python -c "…ast span of command_run…"
command_run span: (4123, 4148)
cli.py command_run hits: 34
hits INSIDE command_run: 2 [4123, 4134]
hits OUTSIDE: 32
```

**2 of 34.** The other 32 sit in other functions' docstrings and comments (`_resolved_group_axes`,
`_cond_beside_n`, `_make_null_fn`, `_resolved_resample`, …), and a reader grepping lands on whichever
hit matched, not on the signpost. So the docstring is landed on by **2 of 195** hits, not 34 + 1.

**Adjudicating the dispatch's question — is 195 hits a residue a docstring can carry, or does it need
an owner?** *Measured, it is not a residue a docstring carries*: the mitigation reaches 2 hits by
landing. But the filing's **routing is right and should not change** — no remaining slice has
`cli.py`'s phase split as its surface, the normative homes are all closed, and the residue is comments
and test names, which is the low-harm half. What needs correcting is the **mitigation sentence**, not
the ownership: say that the signpost is reached only by a reader who opens `command_run` itself, that
32 of `cli.py`'s 34 hits and all 101 `tests/` hits reach nothing, and keep *Owner: unassigned, with
the reason*. This is the *answering a question with a proxy* shape inside a filing whose whole subject
is a claim about the code.

## Task 14 — PASS, with **Major 2** (also a gate finding; see the whole-branch review)

- **Mechanical pass re-derived independently.** I wrote my own checker over the same seven files —
  anchors (GitHub's slugger rules, `_` **kept**), duplicate anchors, cross-file `file.md#frag`, table
  column counts splitting on **unescaped** `|` only, empty rows, trailing whitespace, tabs, invisible
  unicode, fenced blocks skipped — and got **`--- 0 problems over 7 files`**. **Proven able to fail**
  on a purpose-built bad file: 8 problems, one per class, with the fenced content ignored.
- **§ Executability's table is byte-identical, extracted independently.** A programmatic walk that
  finds the last `| Figure | Count | Visible to` header in each entry and reads forward while the line
  starts with `|`: H6b 6 lines, H9a 6 lines, **equal**. No fifth number, no ordinal.
- **Row 1's three measurements all reproduce.** `git diff --name-only main...HEAD -- src` → exactly
  `apparatus.py`, `cli.py`; `apparatus.py` AST-equal after stripping bare strings (above);
  `command_validate`'s source segment via `ast.get_source_segment` on both sides — **261 characters
  each, equal**. And `git log -1 --format=%h -- src tests` → `c925416`, so the pinned sha is still the
  last commit touching code.
- **`Status` column consistency exact.** `NOT_BUILT_COMMANDS` = `{demo, docs, list-templates,
  reproduce, resume}`; § CLI reference's `NOT BUILT` command rows, parsed = the same five;
  `OPERATION_COMMANDS` = `{draft, dry-run, freeze, report, run, validate}`; `NOT_BUILT_GENERATORS`
  empty and no `NOT BUILT` generator row.
- **Versions agree.** `CITATION.cff` `version: 0.1.0` vs `reference.md:708` `publishable_version:
  "0.1.0"`.
- **The `15`/`20` homes attributed individually.** `15 executions`: `README.md:56` (the `demo`'s
  one-step `correlation-pilot`, whose own transcript shows `5/5` per condition and no step list — a
  single `repeat`-scope step, so 15 is right), `reference.md:1651` (`scope = "repeat"  # 15
  executions`, one step's own count), `reference.md:3789` (§ What `demo` walks you through stop 4, the
  same one-step pipeline). `20 executions` / `4,800`: only § Before you spend it. No contradiction.

### Major 2 — § Executability repeats a **false** disclosure, and the exit code it says does not move, moves

The entry's item **(3)** reads: *"`publishable draft new` now reaches that arity arm rather than the
unbuilt diagnostic: **same exit code, different line**, and again no config is read."* Measured through
the real console script on both sides:

```
# main worktree
[draft new]    exit=2 :: `publishable draft` is specified but not built in this version — …
[dry-run new]  exit=2 :: `publishable dry-run` is specified but not built in this version — …
# HEAD
[draft new]    exit=1 ::   error   E-IO-FAILED          No such file or directory
[dry-run new]  exit=1 ::   error   E-IO-FAILED          No such file or directory
[draft a b]    exit=2 :: `draft` takes exactly one path and no flags
```

Three things are wrong: the **exit code does change**, 2 → 1; the line is **not** the arity message;
and **a config path IS read** (`E-IO-FAILED` is `_prepare_run` failing to open `new`). `draft a b` —
disclosure item **(2)** — is right; item (3) is not.

**Task 4's own test knew this and the records were never corrected.** Its docstring says exactly the
right thing (*"the call actually proceeds into `command_draft` rather than being refused for arity …
`_prepare_run` reports a wrong (not invocation) failure"*, `code != EXIT_INVOCATION`), and
`task-b3-report.md` says the same. But the claim was left standing in **three** places: the design's
§ 5 item 3, the plan's task 4 section (*"after this task reaches the arity arm, printing …"*), and now
this dated entry in the feasibility analysis — the one section whose whole purpose is that build claims
are dated and checkable. **Task 14's brief told it to derive each of the four rather than repeat it;
this one was repeated.**

Routed: **append** a correction to the design's § 5 and to the plan's task 4 (never retro-edit), and
correct § Executability item (3) in place — it is a *dated* entry, so the honest form is a correction
appended inside it saying what it replaces. Also worth noting: the two test **names**
(`test_h9a_draft_new_now_reaches_the_arity_arm_not_the_not_built_diagnostic` and its `dry-run` twin)
assert in their names a routing their bodies correctly disprove. Not a separate finding — the
docstrings are explicit — but a reader greps the name and stops.

---

## Concerns adjudicated

The report's six Concerns, each answered:

1. **The amended sweep count** — confirmed, correctly recorded, no retro-edit. Sustained.
2. **The fourth edit class (row widenings)** — in scope, and the widenings are true of the code
   (verified by running the resolver-raise case at all four commands). But the **count** is wrong
   (Minor 1) and one insertion broke a following sentence (Major 1).
3. **`E-APPARATUS-CHANGED` has no `dry-run` clause** — correct. `dry-run` does not call
   `check_changed` (read, and the docstring gives the measured ground). Adding a clause would document
   a non-emit-site. No finding.
4. **The seed-label filing touching the worked example** — the fix round's elision is the right answer
   and needs no ruling: the three unreachable labels keep their two pre-existing homes, the
   step-directory count and the four-component derivation are unchanged.
5. **The mechanical checker is a throwaway** — correct per the repo's own rule. I wrote my own and it
   agrees.
6. **Fixture X's prescribed mutation is not constructible** — confirmed by behaviour, and the
   substitute is discriminating. Detailed below.

### Fixture X: the prescribed mutation, and the substitute

**Prescribed mutation (hoist the probe above `_prepare_run`) — NOT CONSTRUCTIBLE, reproduced:**

```
$ uv run ruff check src/publishable/cli.py   → Found 1 error.
$ uv run pytest tests/test_cli.py -q -k "test_h9a_fixture_x_a_config_that_does_not_validate_never_reaches_the_probe"
E  UnboundLocalError: cannot access local variable 'prepared' where it is not associated with a value
1 failed, 478 deselected
```

It "fails" — through `UnboundLocalError` before any behaviour, so its two branches cannot differ on the
property X tests. The diagnosis holds.

**Substitute (probe first, from a template resolved independently of `_prepare_run` — six lines, a
plausible alternative implementation):**

```
$ uv run ruff check src/publishable/cli.py   → All checks passed!
$ uv run pytest … -k "test_h9a_fixture_x_…"
        assert main(["dry-run", str(cfg)]) == EXIT_WRONG      ← PASSED
        assert "instrument.model" in out                      ← PASSED
>       assert not entered.exists(), "the probe ran before validation refused the config"
E       AssertionError: the probe ran before validation refused the config
1 failed, 478 deselected
```

**Fails on exactly the discriminating assertion, with the exit-code assertion passing before it** — so
an exit-code-only fixture would have passed. The substitute is real. Reverted by copying the file back
and re-running (1 passed).
